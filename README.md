# Tumnis Loopworks Plugin

*Automatic native loop and graph orchestration for Hermes Agent.*

Tumnis Loopworks Plugin is the Hermes-native integration layer for [Tumnis Loopworks](https://github.com/SpaceshipCreative/tumnis-loopworks). It classifies ordinary prompts as DIRECT, LOOP, GRAPH, or LOOP+GRAPH without requiring `/goal`, then combines Tumnis policy with Hermes' existing strengths:

- Hermes `GoalManager`, completion contracts, deterministic gates, and independent goal judge for loops
- Hermes `delegate_task` subagents for in-session graph fan-out and fresh-context verification
- Hermes Kanban for durable dependency workflows
- Tumnis `NO_CHANGE`, keep-rate telemetry, static DAG contracts, safe artifact paths, and validated handoffs

No Hermes Core patch or fork is required.

The plugin chooses the simplest execution shape that can finish and verify the request:

- **DIRECT** — one bounded action
- **LOOP** — repeated or iterative work with measurable gates and a hard stop
- **GRAPH** — independent or specialized workstreams with validated handoffs
- **LOOP+GRAPH** — repeated graph execution with an outer quality gate

Simple requests stay simple. Orchestration is applied only when it earns its keep.

## Install

### Requirements

- Linux or macOS
- Python 3.10+
- [Hermes Agent](https://hermes-agent.nousresearch.com/docs)
- PyYAML (`python3 -m pip install pyyaml`)

### One-time setup

```bash
git clone https://github.com/SpaceshipCreative/tumnis-loopworks-plugin.git
cd tumnis-loopworks-plugin
./install.sh
```

The installer:

- installs the standalone Hermes plugin under `$HERMES_HOME/plugins/tumnis-loopworks/`
- installs the Loopworks policy skill for fallback and advanced/manual workflows
- optionally installs the legacy SOUL preflight block
- copies the loop, graph, and keep-rate runners to `~/bin/`
- creates the required workflow and state directories
- backs up an existing `SOUL.md` before changing it

Enable the plugin once with `hermes plugins enable tumnis-loopworks`, then start a fresh Hermes session or run `/reset`.

To install only the skill and runners without automatic prompt evaluation:

```bash
./install.sh --no-preflight
```

## Quick start

Ask Hermes normally. That is the primary interface.

```text
Research n8n, Zapier, and Make. Verify the important claims and recommend one for a technical team.
```

Hermes can recognize the independent research branches, use a graph with a fresh-context verifier, validate the handoffs, and synthesize the result.

```text
Improve this implementation until the tests pass, but stop after three attempts and report any remaining gaps.
```

Hermes can recognize the measurable retries, use a bounded loop, run deterministic checks, checkpoint progress, and stop at the declared limit.

```text
Summarize this paragraph in one sentence.
```

Hermes handles it directly. No loop. No graph. No theater.

Users may explicitly request a loop, graph, attempt cap, reviewer, or checkpoint when they want tighter control, but explicit invocation is optional.

## What Hermes does

For every request, the installed preflight tells Hermes to:

1. Silently classify the work as DIRECT, LOOP, GRAPH, or LOOP+GRAPH.
2. Load the Loopworks skill only when orchestration applies.
3. Choose the smallest viable topology.
4. Define hard completion criteria and attempt limits for loops.
5. Validate graph artifacts before dependent work advances.
6. Retry only failed work instead of replaying successful branches.
7. Report the verified result—not the internal ceremony.

## Components

- **Loop runner** — bounded iterations, deterministic gates, checkpoints, `NO_CHANGE`, and hard attempt limits.
- **Graph runner** — validated YAML DAGs, parallel execution waves, typed file handoffs, and fresh-context reviewers.
- **Keep-rate gate** — measures whether automation outputs are worth keeping and flags workflows below 50%.
- **Preflight** — gives Hermes the automatic per-prompt decision rule.

State is stored under `~/.hermes/state/`. Workflow definitions live under `~/.hermes/loops/` and `~/.hermes/graphs/`.

## Advanced: manual control

Most users do not need these commands. They are available for debugging, reusable workflow authoring, and explicit operator control.

```bash
loop-runner.py tick <name>
loop-runner.py pass|fail|nochange|status|reset <name>
graph-runner.py plan|run <workflow.yaml>
keep-rate.py [--strict|--json]
```

Example definitions are available in [`examples/`](examples/).

`graph-runner.py run` emits a Hermes `execute_code` driver; it does not directly call delegates. Hermes executes that driver as part of orchestration.

## Honest boundaries

- The graph runner executes static DAG edges.
- Hermes performs conditional routing after reading router or checker artifacts.
- Hermes orchestrates failed-node retry; successful waves are not rerun.
- The preflight is a decision rule, not a second orchestration engine.
- YAML `checks:` execute shell commands; use only trusted workflow definitions.

## Security

- Output paths must be safe, unique, and relative to the graph state directory.
- Shared graph inputs are read-only by contract; each node receives one writable artifact.
- Keep credentials, logs, profile identities, and runtime state out of repositories.

## Test

```bash
python3 tests/test_loopworks.py
python3 -m py_compile scripts/*.py
```

The suite uses temporary directories and does not modify your Hermes state.

## License

Apache License 2.0. See [LICENSE](LICENSE).
