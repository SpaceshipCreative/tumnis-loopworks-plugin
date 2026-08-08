#!/usr/bin/env python3
"""Validate a static workflow DAG and emit a Hermes execution driver.

YAML node keys:
  task: required string
  output: required relative file path
  depends_on: optional list of node names
  checks: optional shell commands; supports {output}; exit 0 = valid handoff
  kind: optional worker | verifier | reduce (default worker)
  output_contract: optional non-executable handoff description
  output_schema: optional JSON Schema for delegated structured summaries

Commands:
  plan workflow.yaml   # validate schema/DAG and print waves
  run workflow.yaml    # emit a native Hermes delegation manifest

The emitted manifest is consumed by the parent Hermes agent, which calls
``delegate_task(tasks=[...])`` for reasoning nodes in each wave. Standalone
Python cannot invoke Hermes model tools. Conditional reject-routing and retries
remain parent-orchestrated.
"""
import json
import os
import pathlib
import sys
import yaml

from graph_runtime import build_wave

STATE_DIR = os.path.expanduser("~/.hermes/state/graphs")


def safe_relative(value, field):
    p = pathlib.PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or str(p) in ("", "."):
        raise SystemExit(f"unsafe {field}: {value!r}")
    return str(p)


def load(path):
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}
    nodes = doc.get("nodes")
    if not isinstance(nodes, dict) or not nodes:
        raise SystemExit("workflow needs a non-empty 'nodes' mapping")
    name = doc.get("workflow", os.path.basename(path).split(".")[0])
    safe_relative(name, "workflow name")
    outputs = set()
    for node, cfg in nodes.items():
        if not isinstance(cfg, dict):
            raise SystemExit(f"node {node}: config must be a mapping")
        if not isinstance(cfg.get("task"), str) or not cfg["task"].strip():
            raise SystemExit(f"node {node}: task must be a non-empty string")
        if "output" not in cfg:
            raise SystemExit(f"node {node}: output is required (typed artifact contract)")
        cfg["output"] = safe_relative(str(cfg["output"]), f"node {node} output")
        if cfg["output"] in outputs:
            raise SystemExit(f"duplicate output path: {cfg['output']}")
        outputs.add(cfg["output"])
        deps = cfg.get("depends_on", [])
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            raise SystemExit(f"node {node}: depends_on must be a list of node names")
        unknown = [d for d in deps if d not in nodes]
        if unknown:
            raise SystemExit(f"node {node}: unknown dependencies: {', '.join(unknown)}")
        if node in deps:
            raise SystemExit(f"node {node}: self-dependency is invalid")
        checks = cfg.get("checks", [])
        if not isinstance(checks, list) or not all(isinstance(c, str) for c in checks):
            raise SystemExit(f"node {node}: checks must be a list of shell commands")
        kind = str(cfg.get("kind", "worker")).strip().lower()
        if kind not in {"worker", "verifier", "reduce"}:
            raise SystemExit(f"node {node}: kind must be worker, verifier, or reduce")
        cfg["kind"] = kind
        if kind == "verifier" and not deps:
            raise SystemExit(f"node {node}: verifier must depend on artifacts it reviews")
        if "output_contract" in cfg and not isinstance(cfg["output_contract"], str):
            raise SystemExit(f"node {node}: output_contract must be a string")
        if "output_schema" in cfg and not isinstance(cfg["output_schema"], dict):
            raise SystemExit(f"node {node}: output_schema must be a mapping")
    return name, nodes


def waves(nodes):
    done, order, remaining = set(), [], dict(nodes)
    while remaining:
        ready = sorted(n for n, cfg in remaining.items() if set(cfg.get("depends_on", [])) <= done)
        if not ready:
            raise SystemExit("dependency cycle among: " + ", ".join(sorted(remaining)))
        order.append(ready)
        for node in ready:
            done.add(node)
            del remaining[node]
    return order


def plan(path):
    name, nodes = load(path)
    order = waves(nodes)
    print(f"workflow: {name} ({len(nodes)} nodes, {len(order)} waves)")
    for idx, wave in enumerate(order, 1):
        for node in wave:
            cfg = nodes[node]
            deps = ",".join(cfg.get("depends_on", [])) or "-"
            checks = len(cfg.get("checks", []))
            print(f"  wave {idx}: {node:20s} deps={deps:30s} checks={checks} -> {cfg['output']}")
    return order


def emit_runner(path):
    """Emit a parent-consumable manifest for native Hermes graph execution."""
    name, nodes = load(path)
    order = waves(nodes)
    outdir = os.path.join(STATE_DIR, name)
    manifest = {
        "contract": "tumnis.graph/v1",
        "workflow": name,
        "output_dir": outdir,
        "execution": {
            "reasoning_nodes": "Parent MUST call delegate_task(tasks=[...]) once per dependency wave.",
            "reduce_nodes": "Parent MUST use execute_code for deterministic reductions.",
            "verification": "Validate result count, declared artifacts, non-empty handoffs, schemas, and checks before advancing.",
            "retry": "Preserve successful nodes and retry only failed or rejected nodes.",
        },
        "waves": [],
    }
    for idx, wave in enumerate(order, 1):
        wave_plan = build_wave(name, nodes, wave, outdir)
        manifest["waves"].append(
            {
                "index": idx,
                "nodes": list(wave),
                "delegated_nodes": list(wave_plan.node_names),
                "delegate_tasks": list(wave_plan.tasks),
                "reduce_nodes": list(wave_plan.reduce_nodes),
                "outputs": {
                    node: os.path.join(outdir, nodes[node]["output"])
                    for node in wave
                },
                "checks": {
                    node: nodes[node].get("checks", [])
                    for node in wave
                },
                "check_commands": {
                    node: [
                        command.replace(
                            "{output}", os.path.join(outdir, nodes[node]["output"])
                        )
                        for command in nodes[node].get("checks", [])
                    ]
                    for node in wave
                },
            }
        )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: graph-runner.py plan|run <workflow.yaml>")
    command, workflow = sys.argv[1:]
    if command == "plan": plan(workflow)
    elif command == "run": emit_runner(workflow)
    else: raise SystemExit("usage: graph-runner.py plan|run <workflow.yaml>")
