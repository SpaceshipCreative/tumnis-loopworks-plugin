# Migration from v0.4

v0.4 used a SOUL preflight and manual runners as the primary orchestration surface. v0.5 makes the standalone plugin primary and delegates loop execution and evaluation to Hermes native goals.

## Upgrade

```bash
./install.sh
hermes plugins enable tumnis-loopworks
```

Start a fresh session or run `/reset`.

The default installer no longer modifies `SOUL.md`. Existing marked preflight sections are left untouched during install; run `./uninstall.sh --remove-preflight` if you intentionally want to remove the legacy section.

## Modes

- `./install.sh` — plugin + skill + manual utilities; no SOUL modification.
- `./install.sh --with-preflight` — also install the legacy SOUL fallback.
- `./install.sh --no-plugin` — skill + utilities, optionally combined with `--with-preflight`.
- `./install.sh --manual-only` — skill + manual utilities only.

Manual loop YAML, graph YAML, state, checkpoints, and keep-rate logs remain compatible. `graph-runner.py run` now emits a `tumnis.graph/v1` native-delegation manifest instead of broken Python that assumed delegation was available inside `execute_code`.
