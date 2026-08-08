from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

MAX_GOAL_CHARS = 4000
MAX_FIELD_CHARS = 2000
MAX_REASON_CHARS = 240
MAX_TURNS = 20
CONTRACT_FIELDS = ("outcome", "verification", "constraints", "boundaries", "stop_when")


class Shape(str, Enum):
    DIRECT = "DIRECT"
    LOOP = "LOOP"
    GRAPH = "GRAPH"
    LOOP_GRAPH = "LOOP+GRAPH"


@dataclass(frozen=True)
class Classification:
    shape: Shape
    confidence: float
    reason: str
    goal: str
    max_turns: int = 6
    contract: dict[str, str] = field(default_factory=dict)
    graph: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Classification":
        shape = Shape(str(raw.get("shape", "DIRECT")).upper())
        try:
            confidence = min(1.0, max(0.0, float(raw.get("confidence", 0))))
        except (TypeError, ValueError):
            confidence = 0.0
        try:
            turns = min(MAX_TURNS, max(1, int(raw.get("max_turns", 6))))
        except (TypeError, ValueError):
            turns = 6
        source = raw.get("contract") if isinstance(raw.get("contract"), Mapping) else {}
        contract = {
            key: str(source[key]).strip()[:MAX_FIELD_CHARS]
            for key in CONTRACT_FIELDS
            if source.get(key)
        }
        graph = dict(raw["graph"]) if isinstance(raw.get("graph"), Mapping) else None
        return cls(
            shape=shape,
            confidence=confidence,
            reason=str(raw.get("reason", "unspecified")).strip()[:MAX_REASON_CHARS],
            goal=str(raw.get("goal", "")).strip()[:MAX_GOAL_CHARS],
            max_turns=turns,
            contract=contract,
            graph=graph,
        )

    @classmethod
    def loop(cls, goal: str, *, verification: str = "", max_turns: int = 6) -> "Classification":
        return cls.from_dict(
            {
                "shape": "LOOP",
                "confidence": 1,
                "reason": "explicit_loop_signal",
                "goal": goal,
                "max_turns": max_turns,
                "contract": {"outcome": goal, "verification": verification},
            }
        )
