#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# gh_auto_rerun_wrapper.sh
#
# Portable wrapper for gh_auto_rerun_watchdog.sh
# Resolves paths dynamically using $HOME and git root instead of hardcoding
# This allows LaunchAgent plist to work across different macOS setups
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# Resolve repo root dynamically (works if script is in a git repo)
if command -v git &>/dev/null && git rev-parse --show-toplevel &>/dev/null 2>&1; then
  REPO_ROOT=$(git rev-parse --show-toplevel)
else
  # Fallback: assume standard path relative to $HOME
  REPO_ROOT="${HOME}/Projects/vio83-ai-orchestra"
fi

# Validate that the repo root exists
if [ ! -d "$REPO_ROOT" ]; then
  echo "ERROR: Repo root not found at: $REPO_ROOT" >&2
  exit 1
fi

# Path to the actual watchdog script
WATCHDOG_SCRIPT="$REPO_ROOT/scripts/runtime/gh_auto_rerun_watchdog.sh"

if [ ! -f "$WATCHDOG_SCRIPT" ]; then
  echo "ERROR: Watchdog script not found at: $WATCHDOG_SCRIPT" >&2
  exit 1
fi

# Pass through to actual watchdog with resolved paths
export REPO_ROOT
exec bash "$WATCHDOG_SCRIPT" "$@"
