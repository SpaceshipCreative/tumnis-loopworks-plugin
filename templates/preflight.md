# Loop/Graph Preflight

Before acting on each request, silently classify it:

- DIRECT: one-shot answer or bounded action. Do not load `loop-graph-system`.
- LOOP: repeated, scheduled, iterative, or requiring measurable retries/checkpoints.
- GRAPH: independent or specialized workstreams, fan-out/join, separate verification, failure isolation, or different model/tool policies.
- LONG/CODING: if likely to require 3+ substantive steps, multiple files, tests, deployment, extended research, or multiple workers, load `loop-graph-system` and choose DIRECT, LOOP, GRAPH, or LOOP+GRAPH before execution.

When LOOP, GRAPH, or LOOP+GRAPH applies, load `loop-graph-system` with `skill_view` before planning or tool use and invoke its runners internally as needed. Use the simplest shape that can finish and verify the task. Never require the user to name the skill, choose a runner, or author workflow YAML; explicit orchestration requests are optional overrides. Never build orchestration for a simple one-shot.
