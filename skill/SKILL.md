---
name: loop-graph-system
description: Use for self-checking loops or parallel worker graph runs.
version: 0.4.0
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

Use a loop for repeated work with measurable completion. Use a static graph for specialized or parallel work with artifact handoffs. Escalate to a graph only for a real need: distinct specialties, fan-out/join, different model or tool policies, auditable branching, an overloaded verifier, or failure isolation. Add one node per need, never a mesh.

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

1. Create `~/.hermes/loops/<name>.yaml` with `goal`, non-empty `criteria`, optional `checks`, and `max_attempts`.
2. Run `loop-runner.py tick <name>` and perform one bounded pass.
3. Call `pass`, `fail "gap 1; gap 2"`, or `nochange`.
4. `pass` executes all checks; failures return nonzero and leave the loop pending.
5. Terminal states require explicit `reset`. Review `status`, checkpoint, and `keep-rate.py --strict`.
6. Put a cheap deterministic trigger before scheduled agent work whenever possible.

### Graph

1. Define nodes with required `task`, unique safe relative `output`, optional `depends_on`, and optional `checks`. `{output}` expands to the artifact path.
2. Run `graph-runner.py plan <workflow.yaml>` and inspect the waves.
3. Run `graph-runner.py run <workflow.yaml>` and execute the emitted code with Hermes `execute_code`.
4. Each node receives read-only dependency artifact paths and one declared writable artifact.
5. The driver rejects missing/empty artifacts and failed checks before advancing.
6. Use plain code for deterministic reduce work such as dedupe, filter, merge, and counts.

The runner handles static DAG edges only. For conditional routing, read the checker/router artifact and dispatch only its named next node. If this becomes common, implement and test routing in the runner before calling it automatic.

## Pitfalls

- `graph-runner.py run` emits code; it does not directly call delegates.
- YAML checks execute shell commands; trust the workflow source.
- Sequence is not dependency. Fake edges serialize work and increase failure surface.
- Workers can write off-path; verify declared artifacts before dependent waves.
- Stale delegation batches can still report completion; confirm the live ID.
- Keep loops short. Context and cost grow on every pass.

## Verification

- Loop `pass` is rejected when any deterministic check fails.
- Checkpoints update on every state change.
- `done:no_change` remains terminal.
- Graph planning rejects cycles, unknown dependencies, unsafe/duplicate outputs, and invalid checks.
- Emitted drivers reject empty handoffs and failed checks.
- `keep-rate.py --strict` exits 2 when any workflow falls below 50%.
