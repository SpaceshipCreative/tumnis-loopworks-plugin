import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugin"))

from tumnis.classifier import classify_prompt
from tumnis.hook import TumnisHook
from tumnis.models import Classification, Shape


class EmptyManager:
    def __init__(self, session_id, default_max_turns=20):
        self.session_id = session_id

    def has_goal(self):
        return False

    def set(self, goal, max_turns=None, contract=None):
        return {"goal": goal}


class Contract:
    def __init__(self, **kwargs):
        self.values = kwargs


def test_plan_and_advice_requests_do_not_activate_automatic_work():
    for prompt in (
        "Create a plan to implement this feature. Do not make changes.",
        "Advise me on the best architecture, but only explain it.",
        "Review this design and tell me what you think without executing anything.",
    ):
        result = classify_prompt(prompt)
        assert result is not None
        assert result.shape is Shape.DIRECT


def test_approved_plan_execution_is_not_misclassified_as_advice():
    result = classify_prompt("Implement the approved plan and run tests until they pass")
    assert result is not None
    assert result.shape is Shape.LOOP


def test_plan_then_execute_phrases_are_not_misclassified_as_advice():
    prompts = (
        "Prepare a plan for the migration and then run it",
        "Create a plan for the refactor, then execute the plan",
        "Write a plan for the Q3 migration and then execute it step by step",
        "Give me a plan and run it",
    )
    for prompt in prompts:
        result = classify_prompt(prompt)
        assert result is None or result.shape is not Shape.DIRECT


def test_durable_graph_routes_to_kanban_goal_mode():
    hook = TumnisHook(manager_cls=EmptyManager, contract_cls=Contract)
    result = hook(
        user_message="Run independent research branches as a durable workflow that survives restarts",
        session_id="durable",
    )
    assert result is not None
    assert "Kanban" in result["context"]
    assert "goal_mode=True" in result["context"]


def test_auxiliary_classifier_exception_fails_open():
    hook = TumnisHook(
        manager_cls=EmptyManager,
        contract_cls=Contract,
        ambiguous_classifier=lambda _: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    assert hook(
        user_message="Handle this substantial request with multiple unclear requirements today",
        session_id="s",
    ) is None


def test_cron_and_goal_mode_kanban_workers_are_excluded(monkeypatch):
    hook = TumnisHook(manager_cls=EmptyManager, contract_cls=Contract)
    monkeypatch.setenv("HERMES_CRON_SESSION", "1")
    assert hook(user_message="Monitor every hour", session_id="cron") is None
    monkeypatch.delenv("HERMES_CRON_SESSION")
    monkeypatch.setenv("HERMES_KANBAN_TASK", "task-1")
    monkeypatch.setenv("HERMES_KANBAN_GOAL_MODE", "1")
    assert hook(user_message="Iterate until done", session_id="kanban") is None


def test_low_confidence_classification_cannot_start_goal():
    weak = Classification.from_dict(
        {
            "shape": "LOOP",
            "confidence": 0.2,
            "goal": "maybe loop",
            "reason": "weak",
            "contract": {"outcome": "maybe"},
        }
    )
    hook = TumnisHook(
        manager_cls=EmptyManager,
        contract_cls=Contract,
        ambiguous_classifier=lambda _: weak,
    )
    assert hook(
        user_message="Handle this substantial request with multiple unclear requirements today",
        session_id="weak",
    ) is None
