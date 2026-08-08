---
name: loop-graph-system
description: Use for self-checking loops or parallel worker graph runs.
version: 0.5.0
author: Hermes
license: Apache-2.0
metadata:
  hermes:
    tags: [Loops, Graphs, Delegation, Verification]
---

# Loop & Graph System

## Operating Contract

Hermes owns classification and invocation. The user should ask for an outcome normally; never require them to name this skill, select a runner, or author YAML. Explicit loop or graph requests are optional operator overrides.

Before execution, silently choose DIRECT, LOOP, GRAPH, or LOOP+GRAPH. For DIRECT work, do not load or expose orchestration. For the other shapes, apply this skill internally and report the verified result rather than runner ceremony.

Use Hermes native goals for repeated work with measurable completion. The plugin activates `GoalManager` and supplies a completion contract; Hermes owns persistence, deterministic gates, the independent goal judge, WAIT barriers, continuations, and bounded turns. Preserve the manual loop runner only for portable/offline workflows and `NO_CHANGE` monitoring.

Use native `delegate_task(tasks=[...])` for independent or specialized reasoning branches. Batch nodes in the same dependency wave, give each fresh child complete context, validate every handoff, and add a fresh-context verifier when deterministic checks cannot prove correctness. Use Kanban goal-mode tasks instead when the graph must survive restarts. Static Tumnis YAML remains the advanced contract surface for reusable artifact DAGs.

## Prerequisites

- `~/bin/loop-runner.py`
- `~/bin/graph-runner.py`
- `~/bin/keep-rate.py`
- PyYAML
- Hermes tools: `skill_view`, `delegate_task`, and `execute_code`

Definitions live in `~/.hermes/{loops,graphs}/`. State lives in `~/.hermes/state/`.

## Internal Runner Interface

These commands are for Hermes orchestration and optional advanced operator control—not the normal user quick start.

```bash
loop-runner.py tick <name>
loop-runner.py pass|fail|nochange|status|reset <name>
graph-runner.py plan|run <workflow.yaml>
keep-rate.py [--strict|--json]
```

## Quick Reference

- Deterministic gate > independent review > self-review.
- Closed loop: explicit criteria, `max_attempts`, and checkpoint.
- `NO_CHANGE` is success; never manufacture work.
- Add `depends_on` only when predecessor output is consumed.
- Validate every handoff before the next node runs.
- Retry only the failed node.
- Below 50% keep-rate: stop or redesign the automation.

## Procedure

### Loop

1. For ordinary LOOP and LOOP+GRAPH requests, let the plugin activate Hermes native `GoalManager`; do not create a parallel Tumnis state machine.
2. Work toward the native completion contract and provide concrete verification evidence for the Hermes goal judge.
3. Respect native max turns, WAIT barriers, pause/resume, user preemption, and existing goals.
4. For monitoring where nothing changed is a legitimate success, preserve Tumnis `NO_CHANGE` telemetry.
5. Use the manual YAML loop runner only for portable/offline operation: `tick`, then one bounded pass, then `pass`, `fail`, or `nochange`.

### Graph

1. For ordinary GRAPH requests, call `delegate_task(tasks=[...])` with all independent reasoning nodes in one batch.
2. Give each child one bounded goal, complete context, and one declared handoff. Children start fresh and know no parent history.
3. Validate returned count, schema validity, claims, artifact handles, and deterministic checks before advancing.
4. Add a fresh-context verifier child only when deterministic verification is insufficient or review is explicitly required.
5. Preserve successful handoffs and retry only failed or rejected nodes.
6. Use `execute_code` for deterministic reduce work such as dedupe, filter, merge, and counts.
7. For reusable static DAGs, define `kind: worker | verifier | reduce`, `task`, unique safe `output`, optional `output_contract`, `depends_on`, `output_schema`, and trusted `checks`.
8. `graph-runner.py run` emits a `tumnis.graph/v1` delegation manifest. The parent executes each wave using native tools; standalone Python cannot invoke Hermes model tools.
9. Use Kanban dependencies and goal-mode workers for durable or restart-safe graphs.

## Pitfalls

- `graph-runner.py run` emits a native delegation manifest; the parent Hermes agent performs actual `delegate_task` calls.
- YAML checks execute shell commands; trust the workflow source and never derive checks from classifier output.
- Sequence is not dependency. Fake edges serialize work and increase failure surface.
- Workers can write off-path; verify declared artifacts before dependent waves.
- Stale delegation batches can still report completion; confirm the live ID.
- Keep loops short. Context and cost grow on every pass.

## Verification

- Loop `pass` is rejected when any deterministic check fails.
- Checkpoints update on every state change.
- `done:no_change` remains terminal.
- Graph planning rejects cycles, unknown dependencies, unsafe/duplicate outputs, invalid checks, invalid node kinds, and verifier nodes without dependencies.
- Delegation manifests batch same-wave workers, isolate reducer nodes, and carry declared output contracts.
- `keep-rate.py --strict` exits 2 when any workflow falls below 50%.
