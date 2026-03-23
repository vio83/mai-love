#!/usr/bin/env bash
# Installs the VIO 83 CI Pre-Push Gate as a git hook.
# After this, every 'git push' runs the full CI check locally FIRST.
# If any check fails, the push is blocked — preventing GitHub run failures.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

HOOK_SRC="scripts/ci/pre_push_gate.sh"
HOOK_DST=".git/hooks/pre-push"

if [ ! -f "$HOOK_SRC" ]; then
  echo "ERROR: $HOOK_SRC not found"
  exit 1
fi

chmod +x "$HOOK_SRC"
cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"

echo "✔ Git pre-push hook installed: $HOOK_DST"
echo "  Every 'git push' will now run CI checks locally first."
echo "  To bypass (emergency): git push --no-verify"
