#!/bin/bash
set -euo pipefail

LOG="$HOME/.vio83/imac_project_sync.log"
LOCKDIR="$HOME/.vio83/imac_project_sync.lock"
REMOTE="archimede-vio"
REMOTE_ROOT="/home/vio/work"
SRC1="$HOME/Projects/vio83-ai-orchestra/"
SRC2="$HOME/ai-scripts-elite/"
LOCK_MAX_AGE_SEC=1800
BWLIMIT_KB=3500

mkdir -p "$HOME/.vio83"

if [[ -d "$LOCKDIR" ]]; then
  now_ts=$(date +%s)
  lock_ts=$(stat -f %m "$LOCKDIR" 2>/dev/null || echo 0)
  age=$((now_ts - lock_ts))
  if [[ "$age" -gt "$LOCK_MAX_AGE_SEC" ]]; then
    rmdir "$LOCKDIR" 2>/dev/null || true
    echo "$(date '+%F %T') | stale lock removed (age=${age}s)" >> "$LOG"
  fi
fi

if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "$(date '+%F %T') | sync skipped (lock active)" >> "$LOG"
  exit 0
fi
trap 'rmdir "$LOCKDIR" >/dev/null 2>&1 || true' EXIT

if ! ping -c 1 -W 2 172.20.10.5 >/dev/null 2>&1 && ! ping -c 1 -W 2 100.116.120.3 >/dev/null 2>&1; then
  echo "$(date '+%F %T') | iMac offline, skip" >> "$LOG"
  exit 0
fi

if ! ssh -o ConnectTimeout=8 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 "$REMOTE" 'echo ok' >/dev/null 2>&1; then
  echo "$(date '+%F %T') | iMac ssh unavailable, skip" >> "$LOG"
  exit 0
fi

ssh "$REMOTE" "mkdir -p '$REMOTE_ROOT/vio83-ai-orchestra' '$REMOTE_ROOT/ai-scripts-elite'"

RSYNC_SSH="ssh -o ConnectTimeout=8 -o ServerAliveInterval=15 -o ServerAliveCountMax=4"
COMMON_EXCLUDES=(
  --exclude '.git/'
  --exclude '.DS_Store'
  --exclude 'node_modules/'
  --exclude '.venv/'
  --exclude 'venv/'
  --exclude '__pycache__/'
  --exclude '.pytest_cache/'
  --exclude '.mypy_cache/'
  --exclude 'dist/'
  --exclude 'build/'
  --exclude '.next/'
  --exclude '.cache/'
)

START=$(date +%s)
echo "$(date '+%F %T') | sync start" >> "$LOG"

rsync -az --delete --partial --partial-dir=.rsync-partial --timeout=120 --bwlimit="$BWLIMIT_KB" -e "$RSYNC_SSH" "${COMMON_EXCLUDES[@]}" \
  "$SRC1" "$REMOTE:$REMOTE_ROOT/vio83-ai-orchestra/"

rsync -az --delete --partial --partial-dir=.rsync-partial --timeout=120 --bwlimit="$BWLIMIT_KB" -e "$RSYNC_SSH" "${COMMON_EXCLUDES[@]}" \
  "$SRC2" "$REMOTE:$REMOTE_ROOT/ai-scripts-elite/"

END=$(date +%s)
ELAPSED=$((END - START))

echo "$(date '+%F %T') | sync ok elapsed=${ELAPSED}s" >> "$LOG"
