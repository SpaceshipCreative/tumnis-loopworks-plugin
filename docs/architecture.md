# Architecture

## Runtime path

```text
ordinary user prompt
  -> Tumnis pre_llm_call hook
  -> deterministic exclusions and fast-path rules
  -> bounded auxiliary classifier only when ambiguous
  -> DIRECT: ordinary Hermes turn
  -> LOOP: native GoalManager + GoalContract
  -> GRAPH: ephemeral native-delegation contract
  -> LOOP+GRAPH: native outer goal + delegation contract
```

Hermes owns loop persistence, quality gates, the independent goal judge, WAIT barriers, pause/resume, continuation turns, delegation isolation, and Kanban durability. Tumnis owns automatic shape policy, static artifact DAG contracts, `NO_CHANGE`, and privacy-safe keep-rate signals.

## Graph execution

Independent reasoning nodes in the same dependency wave are sent in one `delegate_task(tasks=[...])` batch. Every child receives complete context and one bounded handoff because children start fresh. Verifier nodes consume prior artifacts in a separate fresh context. Mechanical reducers use `execute_code`, not model workers. The parent verifies schemas, result counts, artifact handles, and trusted deterministic checks before advancing.

Static YAML `run` emits a `tumnis.graph/v1` manifest. Standalone Python cannot call Hermes model tools; the parent Hermes agent consumes the manifest and performs native tool calls.

Restart-durable workflows use Kanban dependencies and goal-mode workers instead of in-process delegation.

## Compatibility boundary

The plugin imports `GoalManager` and `GoalContract` through `plugin/tumnis/compat.py`. These are version-gated internal interfaces, never vendored or monkeypatched. Missing or incompatible APIs disable automatic goal activation while preserving the ordinary Hermes turn.
