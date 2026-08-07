# Tumnis Loopworks

*A quiet guide through branching systems, turning uncertain paths into verified outcomes.*

Verified loops and graph orchestration for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

Tumnis Loopworks gives Hermes three small, inspectable building blocks:

- **Loop runner** — bounded iterations, deterministic gates, checkpoints, `NO_CHANGE`, and hard attempt limits.
- **Graph runner** — validated YAML DAGs, parallel execution waves, typed file handoffs, and fresh-context reviewers.
- **Keep-rate gate** — measures whether automation outputs are actually worth keeping and flags workflows below 50%.

No orchestration theater: simple prompts stay simple. Use a loop for repeated checkable work and a graph only when real specialization, parallelism, convergence, or failure isolation earns it.

## Requirements

- Linux or macOS
- Python 3.10+
- [Hermes Agent](https://hermes-agent.nousresearch.com/docs)
- PyYAML (`python3 -m pip install pyyaml`)

## Install

```bash
git clone https://github.com/SpaceshipCreative/tumnis-loopworks.git
cd tumnis-loopworks
./install.sh
```

The installer:

- copies runners to `~/bin/`
- installs the skill under `$HERMES_HOME/skills/autonomous-ai-agents/loop-graph-system/`
- creates loop, graph, and state directories
- optionally installs the always-on prompt classifier with `./install.sh --with-preflight`

Start a fresh Hermes session or run `/reset` after installation.

## Quick start: loop

```bash
cp examples/verified-brief.yaml ~/.hermes/loops/
loop-runner.py tick verified-brief
# Do one bounded pass, then:
loop-runner.py pass verified-brief
loop-runner.py status verified-brief
keep-rate.py --strict
```

`pass` runs every command in the YAML `checks:` list. A failed command rejects the pass and leaves the loop pending.

## Quick start: graph

```bash
graph-runner.py plan examples/research-diamond.yaml
graph-runner.py run examples/research-diamond.yaml > /tmp/research-driver.py
```

`run` emits Python for Hermes `execute_code`; it does not call delegates itself. The driver executes one parallel batch per wave, writes declared artifacts, rejects empty outputs, runs handoff checks, and logs successful completion.

## Architecture

```text
request
  |
  +-- DIRECT: one bounded action
  +-- LOOP: goal -> act -> deterministic check -> pass/retry/stop
  +-- GRAPH: fan-out workers -> artifact checks -> fresh reviewer -> synthesis
  +-- LOOP+GRAPH: scheduled/repeated graph with an outer keep-rate gate
```

State is stored under `~/.hermes/state/`; workflow definitions live in `~/.hermes/loops/` and `~/.hermes/graphs/`.

## Honest boundaries

- The graph runner executes static DAG edges.
- Conditional reject-routing is performed by Hermes after reading a router/checker artifact.
- Failed-node retry is orchestrator-driven; successful waves are not rerun.
- The preflight is a compact decision rule, not a second orchestration engine.

## Test

```bash
python3 tests/test_loopworks.py
python3 -m py_compile scripts/*.py
```

The suite uses a temporary HOME and does not modify your Hermes state.

## Security

- YAML `checks:` execute shell commands. Only run workflow files you trust.
- Output paths must be safe, unique, and relative to the graph state directory.
- Shared graph inputs are read-only by contract; each node receives one writable artifact.
- Keep credentials, logs, profile identities, and runtime state out of repositories.

## License

Apache License 2.0. See [LICENSE](LICENSE).
