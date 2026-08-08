from __future__ import annotations

import re

from .models import Classification, Shape

_CONTINUATION = "[continuing toward your standing goal]"
_INTERNAL_PREFIXES = ("[async delegation batch complete", "[background process complete")
_TRIVIAL = {"ok", "okay", "thanks", "thank you", "got it", "yes", "no"}
_LOOP_RE = re.compile(r"\b(until|iterate|retries?|retry|keep trying|every\s+\w+|monitor|stop after|attempts?)\b", re.I)
_GRAPH_RE = re.compile(r"\b(in parallel|parallel|independent|fan[- ]?out|sub-?agents?|specialists?|compare\s+.+\s+and\s+|reviewer|verifier)\b", re.I)
_DIRECT_RE = re.compile(r"\b(summarize|define|explain|what is|who is|one sentence|translate)\b", re.I)
_ATTEMPT_RE = re.compile(
    r"(?:stop after|after|max(?:imum)? of?)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"(?:attempts?|tries|turns?)",
    re.I,
)
_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


def classify_prompt(prompt: str) -> Classification | None:
    text = (prompt or "").strip()
    low = text.lower()
    if not text or low in _TRIVIAL or text.startswith("/"):
        return None
    if low.startswith(_CONTINUATION) or low.startswith(_INTERNAL_PREFIXES):
        return None

    loop = bool(_LOOP_RE.search(text))
    graph = bool(_GRAPH_RE.search(text))
    attempts = _ATTEMPT_RE.search(text)
    if attempts:
        raw_attempts = attempts.group(1).lower()
        max_turns = int(raw_attempts) if raw_attempts.isdigit() else _NUMBER_WORDS[raw_attempts]
    else:
        max_turns = 6
    verification = "Satisfy the requested acceptance criteria and show concrete evidence."

    if loop and graph:
        shape, reason = Shape.LOOP_GRAPH, "loop_and_graph_signals"
    elif graph:
        shape, reason = Shape.GRAPH, "graph_signal"
    elif loop:
        shape, reason = Shape.LOOP, "loop_signal"
    elif _DIRECT_RE.search(text) or len(text.split()) <= 8:
        shape, reason = Shape.DIRECT, "direct_signal"
    else:
        return None

    return Classification.from_dict(
        {
            "shape": shape.value,
            "confidence": 0.95,
            "reason": reason,
            "goal": text,
            "max_turns": max_turns,
            "contract": {
                "outcome": text,
                "verification": verification,
                "constraints": "Do not exceed the attempt budget or claim success without evidence.",
                "stop_when": "Stop and ask for input when blocked by a consequential decision or missing access.",
            },
        }
    )
