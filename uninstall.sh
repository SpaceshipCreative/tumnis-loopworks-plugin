#!/usr/bin/env bash
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
REMOVE_PREFLIGHT=false
[[ "${1:-}" == "--remove-preflight" ]] && REMOVE_PREFLIGHT=true
[[ -z "${1:-}" || "${1:-}" == "--remove-preflight" ]] || {
  echo "usage: ./uninstall.sh [--remove-preflight]" >&2
  exit 2
}

rm -f "$HOME/bin/graph-runner.py" "$HOME/bin/graph_runtime.py" \
  "$HOME/bin/loop-runner.py" "$HOME/bin/keep-rate.py"
rm -rf "$HERMES_HOME/plugins/tumnis-loopworks"
rm -f "$HERMES_HOME/skills/autonomous-ai-agents/loop-graph-system/SKILL.md"
rmdir "$HERMES_HOME/skills/autonomous-ai-agents/loop-graph-system" 2>/dev/null || true

if $REMOVE_PREFLIGHT && [[ -f "$HERMES_HOME/SOUL.md" ]]; then
  cp "$HERMES_HOME/SOUL.md" "$HERMES_HOME/SOUL.md.backup-loopworks-uninstall-$(date +%Y%m%d%H%M%S)"
  SOUL="$HERMES_HOME/SOUL.md" python3 - <<'PY'
from pathlib import Path
import os, re
soul = Path(os.environ["SOUL"])
text = soul.read_text()
pattern = re.compile(r"\n*# Loop/Graph Preflight\n.*?(?=\n# [^\n]+\n|\Z)", re.S)
soul.write_text(pattern.sub("", text).rstrip() + "\n")
PY
fi

printf 'Removed Tumnis-owned plugin, skill, and runner files.\n'
printf 'Workflow definitions and state were preserved under %s.\n' "$HERMES_HOME"
printf 'Run: hermes plugins disable tumnis-loopworks (if still listed), then start a fresh session.\n'
