from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Any


@dataclass(frozen=True)
class GoalAPI:
    manager_cls: type
    contract_cls: type


def load_goal_api() -> GoalAPI | None:
    """Load the narrow native-goal API without changing Hermes Core."""
    try:
        from hermes_cli.goals import GoalContract, GoalManager
    except Exception:
        return None
    try:
        params = inspect.signature(GoalManager.set).parameters
        if not {"goal", "max_turns", "contract"}.issubset(params):
            return None
    except (TypeError, ValueError):
        return None
    return GoalAPI(GoalManager, GoalContract)
