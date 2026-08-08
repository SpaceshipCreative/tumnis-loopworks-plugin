from __future__ import annotations

import os
from typing import Any, Callable

from .aux_classifier import classify_ambiguous
from .classifier import classify_prompt
from .compat import load_goal_api
from .graph_contract import render_graph_contract
from .models import Shape
from .native_goal import activate_native_goal


class TumnisHook:
    def __init__(
        self,
        *,
        manager_cls: type | None = None,
        contract_cls: type | None = None,
        ambiguous_classifier: Callable[[str], Any] = classify_ambiguous,
    ):
        self.manager_cls = manager_cls
        self.contract_cls = contract_cls
        self.ambiguous_classifier = ambiguous_classifier

    def _has_existing_goal(self, session_id: str) -> bool:
        manager_cls = self.manager_cls
        if manager_cls is None:
            api = load_goal_api()
            if api is None:
                return False
            manager_cls = api.manager_cls
        try:
            return bool(manager_cls(session_id=session_id).has_goal())
        except Exception:
            return False

    def __call__(self, **kwargs: Any) -> dict[str, str] | None:
        prompt = str(kwargs.get("user_message") or "")
        session_id = str(kwargs.get("session_id") or "")
        parent_session_id = str(kwargs.get("parent_session_id") or "")
        platform = str(kwargs.get("platform") or "").lower()

        if not session_id or parent_session_id:
            return None
        if os.getenv("HERMES_KANBAN_TASK") and os.getenv("HERMES_KANBAN_GOAL_MODE"):
            return None
        if (platform in {"cron", "internal"} or os.getenv("HERMES_CRON_SESSION")) and not os.getenv(
            "TUMNIS_ENABLE_CRON"
        ):
            return None
        if self._has_existing_goal(session_id):
            return None

        classification = classify_prompt(prompt)
        if classification is None:
            classification = self.ambiguous_classifier(prompt)
        if classification is None or classification.shape is Shape.DIRECT:
            return None

        if classification.shape in {Shape.LOOP, Shape.LOOP_GRAPH}:
            activated = activate_native_goal(
                session_id,
                classification,
                manager_cls=self.manager_cls,
                contract_cls=self.contract_cls,
            )
            if not activated:
                return None

        if classification.shape in {Shape.GRAPH, Shape.LOOP_GRAPH}:
            context = render_graph_contract(
                loop=classification.shape is Shape.LOOP_GRAPH,
                durable=False,
            )
        else:
            context = (
                "[TUMNIS SHAPE: LOOP]\n"
                "A native Hermes goal is active for this request. Work toward the completion "
                "contract, show concrete verification evidence, and respect the bounded turn budget."
            )
        return {"context": context}


_DEFAULT_HOOK: TumnisHook | None = None


def get_default_hook() -> TumnisHook:
    global _DEFAULT_HOOK
    if _DEFAULT_HOOK is None:
        _DEFAULT_HOOK = TumnisHook()
    return _DEFAULT_HOOK
