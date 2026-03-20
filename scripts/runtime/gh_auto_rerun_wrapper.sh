#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# gh_auto_rerun_wrapper.sh
#
# Portable wrapper for gh_auto_rerun_watchdog.sh
# Resolves paths dynamically using $HOME and git root instead of hardcoding
# This allows LaunchAgent plist to work across different macOS setups
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# Resolve repo root dynamically, independent of current working directory.
if command -v git &>/dev/null; then
  SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  if REPO_ROOT="$(git -C "${SCRIPT_DIR}/../.." rev-parse --show-toplevel 2>/dev/null)"; then
    :
  elif REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    :
  else
    REPO_ROOT="${HOME}/Projects/vio83-ai-orchestra"
  fi
else
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

# Provide portable defaults to downstream scripts.
if [ -z "${LOG_DIR:-}" ]; then
  LOG_DIR="${REPO_ROOT}/automation/logs"
fi

export REPO_ROOT LOG_DIR
exec bash "$WATCHDOG_SCRIPT" "$@"
