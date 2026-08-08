#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
WITH_PREFLIGHT=false
WITH_PLUGIN=true

for arg in "$@"; do
  case "$arg" in
    --with-preflight) WITH_PREFLIGHT=true ;;
    --no-preflight) WITH_PREFLIGHT=false ;; # v0.4 compatibility alias
    --no-plugin) WITH_PLUGIN=false ;;
    --manual-only) WITH_PLUGIN=false; WITH_PREFLIGHT=false ;;
    *)
      echo "usage: ./install.sh [--with-preflight] [--no-plugin] [--manual-only]" >&2
      exit 2
      ;;
  esac
done

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
python3 -c 'import yaml' 2>/dev/null || {
  echo "PyYAML is required: python3 -m pip install pyyaml" >&2
  exit 1
}

mkdir -p "$HOME/bin" \
  "$HERMES_HOME/skills/autonomous-ai-agents/loop-graph-system" \
  "$HERMES_HOME/loops" "$HERMES_HOME/graphs" \
  "$HERMES_HOME/state/loops" "$HERMES_HOME/state/graphs"
$WITH_PLUGIN && mkdir -p "$HERMES_HOME/plugins/tumnis-loopworks"

install -m 0755 "$ROOT/scripts/graph-runner.py" "$HOME/bin/graph-runner.py"
install -m 0644 "$ROOT/scripts/graph_runtime.py" "$HOME/bin/graph_runtime.py"
install -m 0755 "$ROOT/scripts/loop-runner.py" "$HOME/bin/loop-runner.py"
install -m 0755 "$ROOT/scripts/keep-rate.py" "$HOME/bin/keep-rate.py"
install -m 0644 "$ROOT/skill/SKILL.md" "$HERMES_HOME/skills/autonomous-ai-agents/loop-graph-system/SKILL.md"
$WITH_PLUGIN && cp -R "$ROOT/plugin/." "$HERMES_HOME/plugins/tumnis-loopworks/"

if $WITH_PREFLIGHT; then
  soul="$HERMES_HOME/SOUL.md"
  [[ -f "$soul" ]] || : > "$soul"
  cp "$soul" "$soul.backup-loopworks-$(date +%Y%m%d%H%M%S)"
  ROOT="$ROOT" SOUL="$soul" python3 - <<'PY'
from pathlib import Path
import os, re
soul = Path(os.environ["SOUL"])
section = Path(os.environ["ROOT"], "templates", "preflight.md").read_text().strip()
text = soul.read_text() if soul.exists() else ""
pattern = re.compile(r"\n*# Loop/Graph Preflight\n.*?(?=\n# [^\n]+\n|\Z)", re.S)
text = pattern.sub("", text).rstrip()
soul.write_text(text + "\n\n" + section + "\n")
PY
fi

printf 'Installed Tumnis Loopworks\n'
printf '  runners: %s/bin\n' "$HOME"
printf '  skill:   %s/skills/autonomous-ai-agents/loop-graph-system/SKILL.md\n' "$HERMES_HOME"
$WITH_PLUGIN && printf '  plugin:  %s/plugins/tumnis-loopworks\n' "$HERMES_HOME"
$WITH_PREFLIGHT && printf '  legacy preflight: %s/SOUL.md\n' "$HERMES_HOME"
$WITH_PLUGIN && printf 'Enable once with: hermes plugins enable tumnis-loopworks\n'
printf 'Start a fresh Hermes session or run /reset.\n'
