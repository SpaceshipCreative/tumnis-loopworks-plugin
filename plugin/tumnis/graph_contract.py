from __future__ import annotations


def render_graph_contract(*, loop: bool, durable: bool = False) -> str:
    mode = "LOOP+GRAPH" if loop else "GRAPH"
    durability = (
        "This work must survive restarts: use Hermes Kanban dependencies with goal_mode=True."
        if durable
        else "Use native delegate_task(tasks=[...]) for independent reasoning-heavy nodes in the same wave."
    )
    return f"""[TUMNIS SHAPE: {mode}]
{durability}
Graph contract:
- Deploy real Hermes subagents for independent or specialized reasoning branches.
- Give every child a bounded goal and complete context; children know no parent history.
- Batch only nodes in the same dependency wave.
- Use output_schema for structured handoffs when the parent consumes fields.
- Validate every handoff and verify external side effects directly.
- Add a fresh-context verifier when deterministic checks cannot prove correctness.
- Retry only failed or rejected nodes; preserve successful results.
- Use execute_code, not a subagent, for mechanical dedupe, sort, merge, and counts.
- Synthesize only after all required handoffs pass.
"""
