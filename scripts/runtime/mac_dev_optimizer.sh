#!/usr/bin/env bash
# VIO 83 — Mac Development Environment Optimizer
# Runs every 4 hours via LaunchAgent to keep Mac at peak dev performance.
# Targets: disk space, RAM pressure, cache hygiene, log rotation.
set -euo pipefail

LOG_DIR="$HOME/Projects/vio83-ai-orchestra/data/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/mac_optimizer.log"
MAX_LOG_SIZE=1048576  # 1 MB

# Rotate log if too large
if [ -f "$LOG" ] && [ "$(stat -f%z "$LOG" 2>/dev/null || echo 0)" -gt "$MAX_LOG_SIZE" ]; then
  mv "$LOG" "$LOG.old"
fi

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

log "=== Mac Optimizer run start ==="

FREED=0

# 1. Ollama partial downloads (corrupt/incomplete)
PARTIALS=$(find "$HOME/.ollama/models/blobs/" -name "*-partial" 2>/dev/null || true)
if [ -n "$PARTIALS" ]; then
  SIZE_BEFORE=$(du -sk "$HOME/.ollama/models/" 2>/dev/null | cut -f1 || echo 0)
  rm -f "$HOME/.ollama/models/blobs/"*-partial 2>/dev/null || true
  SIZE_AFTER=$(du -sk "$HOME/.ollama/models/" 2>/dev/null | cut -f1 || echo 0)
  DIFF=$(( (SIZE_BEFORE - SIZE_AFTER) / 1024 ))
  FREED=$((FREED + DIFF))
  log "Ollama partials: freed ${DIFF} MB"
fi

# 2. Homebrew cache
if command -v brew &>/dev/null; then
  BREW_BEFORE=$(du -sk "$(brew --cache 2>/dev/null)" 2>/dev/null | cut -f1 || echo 0)
  brew cleanup --prune=3 -q 2>/dev/null || true
  BREW_AFTER=$(du -sk "$(brew --cache 2>/dev/null)" 2>/dev/null | cut -f1 || echo 0)
  DIFF=$(( (BREW_BEFORE - BREW_AFTER) / 1024 ))
  FREED=$((FREED + DIFF))
  log "Brew cache: freed ${DIFF} MB"
fi

# 3. npm cache
if command -v npm &>/dev/null; then
  npm cache clean --force 2>/dev/null || true
  log "npm cache: cleaned"
fi

# 4. pip cache
if command -v pip3 &>/dev/null; then
  pip3 cache purge 2>/dev/null || true
  log "pip3 cache: purged"
fi

# 5. Python __pycache__ in project
PROJECT="$HOME/Projects/vio83-ai-orchestra"
if [ -d "$PROJECT" ]; then
  find "$PROJECT" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
  find "$PROJECT" -name "*.pyc" -delete 2>/dev/null || true
  log "Project pycache: cleaned"
fi

# 6. Old logs (>7 days) in project
if [ -d "$PROJECT/data/logs" ]; then
  find "$PROJECT/data/logs" -name "*.log.old" -mtime +7 -delete 2>/dev/null || true
  find "$PROJECT/logs" -name "*.log" -mtime +14 -delete 2>/dev/null || true
  log "Old project logs: cleaned"
fi

# 7. Xcode DerivedData (if not actively building)
if [ -d "$HOME/Library/Developer/Xcode/DerivedData" ]; then
  # Only clean if Xcode is not running
  if ! pgrep -x Xcode &>/dev/null; then
    XCODE_SIZE=$(du -sk "$HOME/Library/Developer/Xcode/DerivedData" 2>/dev/null | cut -f1 || echo 0)
    rm -rf "$HOME/Library/Developer/Xcode/DerivedData" 2>/dev/null || true
    DIFF=$((XCODE_SIZE / 1024))
    FREED=$((FREED + DIFF))
    log "Xcode DerivedData: freed ${DIFF} MB"
  fi
fi

# 8. System log cleanup (user-level)
find "$HOME/Library/Logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
log "User logs >7d: cleaned"

# 9. RAM: purge inactive memory (requires no sudo on recent macOS)
# Only if memory pressure is high
VM_STAT=$(vm_stat 2>/dev/null || true)
if [ -n "$VM_STAT" ]; then
  PAGES_FREE=$(echo "$VM_STAT" | awk '/Pages free/ {gsub(/\./, "", $3); print $3}')
  PAGES_INACTIVE=$(echo "$VM_STAT" | awk '/Pages inactive/ {gsub(/\./, "", $3); print $3}')
  # Each page = 16384 bytes on Apple Silicon
  FREE_MB=$(( (PAGES_FREE * 16384) / 1048576 ))
  INACTIVE_MB=$(( (PAGES_INACTIVE * 16384) / 1048576 ))
  log "RAM: free=${FREE_MB}MB inactive=${INACTIVE_MB}MB"
fi

# 10. Flush DNS cache (network performance)
dscacheutil -flushcache 2>/dev/null || true

# Report
DISK_AVAIL=$(df -h / | tail -1 | awk '{print $4}')
log "Disk available: ${DISK_AVAIL}"
log "Total freed this run: ~${FREED} MB"
log "=== Mac Optimizer run complete ==="
