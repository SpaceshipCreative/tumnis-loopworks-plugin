#!/usr/bin/env python3
"""Pure planning helpers bridging static Tumnis DAGs to Hermes delegation.

This module builds native ``delegate_task(tasks=[...])`` payloads. It does not
pretend to invoke Hermes tools from a standalone process; the parent Hermes
agent owns tool invocation, wave joins, and retries.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

_VALID_KINDS = {"worker", "verifier", "reduce"}


@dataclass(frozen=True)
class WavePlan:
    node_names: tuple[str, ...]
    tasks: tuple[dict[str, Any], ...]
    reduce_nodes: tuple[str, ...]


def _node_kind(config: Mapping[str, Any]) -> str:
    kind = str(config.get("kind", "worker")).strip().lower()
    if kind not in _VALID_KINDS:
        raise ValueError(f"invalid node kind: {kind}")
    return kind


def _safe_output(value: Any, node_name: str) -> str:
    path = Path(str(value))
    if path.is_absolute() or ".." in path.parts or str(path) in {"", "."}:
        raise ValueError(f"node {node_name} has unsafe output path: {value!r}")
    return str(path)


def build_wave(
    workflow: str,
    nodes: Mapping[str, Mapping[str, Any]],
    node_names: Sequence[str],
    output_dir: str | Path,
) -> WavePlan:
    """Build one deterministic dependency wave for a parent delegate_task call."""
    root = Path(output_dir)
    tasks: list[dict[str, Any]] = []
    delegated: list[str] = []
    reducers: list[str] = []

    for name in node_names:
        if name not in nodes:
            raise ValueError(f"unknown node in wave: {name}")
        config = nodes[name]
        missing = [key for key in ("task", "output") if not config.get(key)]
        if missing:
            raise ValueError(f"node {name} missing required fields: {', '.join(missing)}")
        kind = _node_kind(config)
        if kind == "reduce":
            reducers.append(name)
            continue
        deps = tuple(str(dep) for dep in config.get("depends_on", []))
        unknown = [dep for dep in deps if dep not in nodes]
        if unknown:
            raise ValueError(f"node {name} has unknown dependency: {', '.join(unknown)}")
        if kind == "verifier" and not deps:
            raise ValueError(f"verifier node {name} must depend on artifacts it reviews")
        output = root / _safe_output(config["output"], name)
        inputs = [
            root / _safe_output(nodes[dep]["output"], dep)
            for dep in deps
        ]
        output_contract = str(config.get("output_contract") or "A complete non-empty handoff")
        role = "Fresh-context verifier" if kind == "verifier" else "Worker"
        context = [
            f"You are {role.lower()} node '{name}' in workflow '{workflow}'.",
            "Do only this bounded job; children have no parent conversation context.",
            f"TASK: {config['task']}",
            f"OUTPUT CONTRACT: {output_contract}",
            f"Return the complete handoff in your final message for the parent to write to the declared artifact: {output}",
            "Do not claim external writes or side effects without a verifiable handle.",
        ]
        if inputs:
            context.append("READ-ONLY DEPENDENCY ARTIFACTS: " + ", ".join(map(str, inputs)))
        task: dict[str, Any] = {
            "goal": f"{role} '{name}' for workflow '{workflow}'",
            "context": "\n".join(context),
        }
        if isinstance(config.get("output_schema"), dict):
            task["output_schema"] = config["output_schema"]
        tasks.append(task)
        delegated.append(name)

    return WavePlan(tuple(delegated), tuple(tasks), tuple(reducers))


def result_text(result: Any) -> str:
    if isinstance(result, Mapping):
        for key in ("result", "summary", "output"):
            value = result.get(key)
            if value is not None:
                return str(value)
        return ""
    return str(result)


def validate_node_result(node_name: str, result: Any, output_path: str | Path) -> str:
    """Validate a child handoff before the parent persists its declared artifact."""
    text = result_text(result).strip()
    if not text:
        raise ValueError(f"node {node_name} returned empty output for {output_path}")
    return text
