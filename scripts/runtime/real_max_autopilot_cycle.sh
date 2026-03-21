#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-hourly}"
LOG_DIR="$ROOT_DIR/automation/logs"
mkdir -p "$LOG_DIR"

LOCK_DIR="/tmp/vio83-real-max-autopilot.lock"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
CYCLE_LOG="$LOG_DIR/real-max-autopilot-cycle.log"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[$TS] [${MODE}] lock-active: ciclo precedente ancora in esecuzione" >> "$CYCLE_LOG"
  exit 0
fi

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

{
  echo "[$TS] [${MODE}] cycle-start"

  # Fast local housekeeping for VS Code + Claude + macOS runtime.
  bash "$ROOT_DIR/scripts/runtime/macos_ultra_optimizer.sh" "normal" || true

  # Allinea sempre il profilo locale-only prima della manutenzione.
  bash "$ROOT_DIR/scripts/runtime/activate_real_max_global_mode.sh" >/dev/null 2>&1 || true

  # Manutenzione pesante: sempre su ciclo hourly.
  bash "$ROOT_DIR/scripts/runtime/run_real_max_maintenance.sh" || true

  # VS Code autofix: ESLint, TSC, Python compile, cache cleanup
  bash "$ROOT_DIR/scripts/runtime/vscode_autofix_cycle.sh" || true

  # Rinforzo quotidiano: doppio passaggio maintenance per autotune più aggressivo.
  if [[ "$MODE" == "daily" ]]; then
    sleep 5
    bash "$ROOT_DIR/scripts/runtime/run_real_max_maintenance.sh" || true
    # Daily hard cap for Ollama footprint.
    bash "$ROOT_DIR/scripts/runtime/ollama_aggressive_controlled_cleanup.sh" || true
  fi

  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [${MODE}] cycle-done"
} >> "$CYCLE_LOG" 2>&1
