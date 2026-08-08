from __future__ import annotations

import json
import re
from typing import Any, Callable

from .models import Classification, Shape

MIN_CONFIDENCE = 0.80
SYSTEM_PROMPT = """Classify one user request for Hermes orchestration.
Return one JSON object only with: shape (DIRECT|LOOP|GRAPH|LOOP+GRAPH), confidence
(0..1), reason, goal, max_turns, contract (outcome, verification, constraints,
boundaries, stop_when), and optional graph metadata. Never propose shell commands.
LOOP means repeated bounded work. GRAPH means genuinely independent/specialized
reasoning branches. LOOP+GRAPH requires both. Prefer DIRECT when uncertain."""
_JSON_RE = re.compile(r"\{.*\}", re.S)


def _default_call_llm(**kwargs):
    from agent.auxiliary_client import call_llm

    return call_llm(**kwargs)


def classify_ambiguous(
    prompt: str,
    *,
    call_llm: Callable[..., Any] | None = None,
    minimum_confidence: float = MIN_CONFIDENCE,
) -> Classification | None:
    caller = call_llm or _default_call_llm
    try:
        response = caller(
            task="triage_specifier",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (prompt or "")[:4000]},
            ],
            temperature=0,
            max_tokens=1000,
            timeout=20,
        )
        raw = str(response.choices[0].message.content or "").strip()
        match = _JSON_RE.search(raw)
        if not match:
            return None
        result = Classification.from_dict(json.loads(match.group(0)))
    except Exception:
        return None
    if result.confidence < minimum_confidence or result.shape is Shape.DIRECT:
        return None
    return result
