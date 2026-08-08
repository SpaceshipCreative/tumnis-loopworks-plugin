# Security

- Classifier output cannot create shell quality gates.
- Goal, reason, and contract fields are length-capped before persistence or injection.
- Auxiliary classification uses temperature zero, bounded output, a timeout, and fail-open DIRECT behavior.
- Confidence below 0.80 cannot activate loops or graphs.
- Active or paused native goals are never overwritten.
- Slash commands, standing-goal continuations, delegation completions, child sessions, cron runs, and goal-mode Kanban workers are excluded.
- Plan/advice/review-only requests remain DIRECT unless autonomous execution is explicitly requested.
- Static graph outputs must be safe, unique relative paths; cycles, unknown dependencies, malformed schemas, and verifier nodes without inputs are rejected.
- YAML `checks:` are trusted operator configuration. Prompt or auxiliary-classifier text is never promoted into executable checks.
- Child self-reports are not proof of external side effects. Parents must verify files, URLs, IDs, or live state directly.
- Keep-rate logs store timestamps, workflow identifiers, kept flags, and outcome categories—never raw prompts, credentials, or artifact contents.
- Tumnis never patches, forks, vendors, or monkeypatches Hermes Core.
