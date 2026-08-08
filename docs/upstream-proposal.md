# Upstream Hermes Extension Proposal

Tumnis can ship without Hermes Core changes, but long-term compatibility would improve with four stable public surfaces:

1. `activate_goal(session_id, goal, contract, max_turns)` as a documented service.
2. Goal lifecycle hooks: `goal_started`, `goal_verdict`, `goal_waiting`, `goal_paused`, and `goal_done`.
3. Typed continuation metadata exposed to plugins.
4. Optional native automatic-goal classification configuration.

The service should preserve existing-goal preemption semantics, persistence, prompt caching, CLI/gateway parity, and deterministic quality gates. Lifecycle hooks should expose verdict categories and reason codes without requiring plugins to scrape the session database.

This document is a proposal only. The Tumnis repository does not patch or fork Hermes Core, and no upstream submission should occur without explicit operator approval.
