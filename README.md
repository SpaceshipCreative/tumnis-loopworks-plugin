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
- copies the loop, graph, graph-runtime, and keep-rate utilities to `~/bin/`
- creates the required workflow and state directories
- does **not** modify `SOUL.md` by default

Enable the plugin once with `hermes plugins enable tumnis-loopworks`, then start a fresh Hermes session or run `/reset`.

For legacy SOUL-based preflight fallback:

```bash
./install.sh --with-preflight
```

For only the skill and manual runners, with no plugin or SOUL changes:

```bash
./install.sh --manual-only
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

## What the integration owns

1. The Tumnis `pre_llm_call` plugin classifies ordinary prompts as DIRECT, LOOP, GRAPH, or LOOP+GRAPH.
2. LOOP and LOOP+GRAPH activate Hermes native `GoalManager` with a bounded completion contract.
3. Hermes owns persistence, deterministic quality gates, the independent goal judge, WAIT barriers, and continuation turns.
4. GRAPH and LOOP+GRAPH require real Hermes `delegate_task` subagents for independent reasoning branches.
5. Hermes Kanban owns durable dependency workflows that must survive restarts.
6. Tumnis retains static DAG contracts, safe paths, validated handoffs, `NO_CHANGE`, and keep-rate telemetry. Manual workflows emit complete keep-rate outcomes; native goal verdict telemetry remains limited until Hermes exposes stable goal-lifecycle hooks.

## Components

- **Plugin classifier** — deterministic fast paths plus bounded auxiliary classification for ambiguous prompts.
- **Native goal adapter** — activates Hermes loops without `/goal` and never replaces an active or paused goal.
- **Graph contract/runtime** — batches native subagent work by dependency wave and isolates deterministic reducers.
- **Manual loop runner** — portable bounded loops, deterministic gates, checkpoints, and `NO_CHANGE`.
- **Keep-rate gate** — measures whether automation outputs are worth keeping and flags workflows below 50%.
- **Legacy preflight** — optional fallback only; it is not an independent evaluator.

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

`graph-runner.py run` emits a `tumnis.graph/v1` manifest. The parent Hermes agent executes reasoning nodes with native `delegate_task`, runs deterministic reducers with `execute_code`, validates handoffs, and advances dependency waves.

## Honest boundaries

- The plugin uses a version-gated internal Hermes goal API until Hermes exposes a stable public goal service.
- In-session `delegate_task` graphs are not restart-durable; use Kanban dependencies and goal-mode workers when durability matters.
- One-shot `hermes chat -q` may exit after its first response and does not promise hidden continuation turns.
- Cron jobs retain their own bounded execution model and are excluded from automatic activation unless explicitly opted in.
- The static graph runner plans DAG edges and emits execution contracts; the parent Hermes agent performs model-tool calls.
- Tumnis does not replace Hermes' independent goal judge.
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
