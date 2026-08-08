from __future__ import annotations

from typing import Any

from .compat import load_goal_api
from .models import Classification


def activate_native_goal(
    session_id: str,
    classification: Classification,
    *,
    manager_cls: type | None = None,
    contract_cls: type | None = None,
) -> bool:
    """Activate one native goal, never replacing active or paused state."""
    if not session_id:
        return False
    if manager_cls is None or contract_cls is None:
        api = load_goal_api()
        if api is None:
            return False
        manager_cls, contract_cls = api.manager_cls, api.contract_cls
    manager = manager_cls(session_id=session_id, default_max_turns=classification.max_turns)
    if manager.has_goal():
        return False
    contract = contract_cls(**classification.contract)
    manager.set(
        classification.goal,
        max_turns=classification.max_turns,
        contract=contract,
    )
    return True
