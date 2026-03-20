#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-normal}"
LOG_DIR="$ROOT_DIR/automation/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/macos-ultra-optimizer.log"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

safe_rm_dir() {
  local p="$1"
  [ -d "$p" ] && /bin/rm -rf "$p" 2>/dev/null || true
}

safe_cleanup_common() {
  safe_rm_dir "$HOME/Library/Application Support/Code/CachedData"
  safe_rm_dir "$HOME/Library/Application Support/Code/CachedExtensionVSIXs"
  safe_rm_dir "$HOME/Library/Application Support/Code/logs"
  safe_rm_dir "$HOME/Library/Application Support/Claude/Cache"
  safe_rm_dir "$HOME/Library/Application Support/Claude/Code Cache"
  safe_rm_dir "$HOME/Library/Application Support/Claude/GPUCache"
  safe_rm_dir "$HOME/Library/Application Support/Claude/DawnWebGPUCache"
  safe_rm_dir "$HOME/Library/Application Support/Claude/DawnGraphiteCache"
  safe_rm_dir "$HOME/Library/Logs/DiagnosticReports"
}

trim_project_logs() {
  find "$LOG_DIR" -type f -mtime +14 -delete 2>/dev/null || true
}

run_emergency_extras() {
  # Keep local model storage within validated essentials.
  bash "$ROOT_DIR/scripts/runtime/ollama_aggressive_controlled_cleanup.sh" >/dev/null 2>&1 || true

  # Clean npm cache non-interactively when in emergency mode.
  if command -v npm >/dev/null 2>&1; then
    npm cache clean --force >/dev/null 2>&1 || true
  fi
}

before_free_gb="$(df -g / | awk 'NR==2 {print $4}')"
{
  echo "[$TS] mode=$MODE before_free_gb=$before_free_gb"
  safe_cleanup_common
  trim_project_logs

  if [[ "$MODE" == "emergency" ]]; then
    run_emergency_extras
  fi

  after_free_gb="$(df -g / | awk 'NR==2 {print $4}')"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] mode=$MODE after_free_gb=$after_free_gb"
} >> "$LOG_FILE" 2>&1
