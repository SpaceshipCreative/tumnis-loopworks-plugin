# Compatibility

Tumnis Loopworks Plugin is tested against the Hermes goal surface containing:

- `hermes_cli.goals.GoalManager(session_id, default_max_turns=...)`
- `GoalManager.has_goal()`
- `GoalManager.set(goal, max_turns=..., contract=...)`
- `hermes_cli.goals.GoalContract(outcome, verification, constraints, boundaries, stop_when)`
- `pre_llm_call` plugin context injection

`plugin/tumnis/compat.py` probes this surface at runtime. If imports or signatures are unavailable, automatic goal activation fails open: the original prompt proceeds as an ordinary Hermes turn. Existing active or paused goals are never replaced.

The current compatibility canary was verified against Hermes Agent commit `b3aa561fa` (2026-08-08 checkout), which includes native completion contracts and deterministic goal quality gates. Treat that commit as the minimum tested baseline until release-tag compatibility is established. Pin deployments to a tested Hermes release/commit and run the real integration tests after upgrades:

```bash
HERMES_SOURCE=/path/to/hermes-agent python3 -m pytest tests/integration -q
```

Known limitations:

- The goal classes are internal APIs rather than a documented stable plugin service.
- One-shot `hermes chat -q` may not execute continuation turns.
- Cron and goal-mode Kanban workers are excluded from automatic activation by default.
- In-session delegation is non-durable; use Kanban for restart-safe graphs.
