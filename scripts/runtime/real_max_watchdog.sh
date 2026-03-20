#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/automation/logs"
mkdir -p "$LOG_DIR" "$HOME/Library/LaunchAgents"
LOG_FILE="$LOG_DIR/real-max-watchdog.log"
ALERT_LOG="$LOG_DIR/real-max-alerts.log"
LOCK_DIR="/tmp/vio83-real-max-watchdog.lock"

THRESHOLD_GB="${VIO_DISK_ALERT_THRESHOLD_GB:-6}"
HIGH_LOAD_THRESHOLD="${VIO_HIGH_LOAD_THRESHOLD:-14}"
HIGH_MEM_PRESSURE_PAGES="${VIO_HIGH_MEM_PRESSURE_PAGES:-120000}"
DISABLE_OLLAMA_MODEL_SYNC="${VIO_DISABLE_OLLAMA_MODEL_SYNC:-1}"
UID_VAL="$(id -u)"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[$TS] watchdog-lock-active" >> "$LOG_FILE"
  exit 0
fi

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

ensure_agent() {
  local label="$1"
  local src="$2"
  local dst="$HOME/Library/LaunchAgents/${label}.plist"

  if [[ -f "$src" ]]; then
    cp "$src" "$dst"
  fi

  if ! launchctl print "gui/${UID_VAL}/${label}" >/dev/null 2>&1; then
    launchctl bootstrap "gui/${UID_VAL}" "$dst" >/dev/null 2>&1 || true
    launchctl kickstart -k "gui/${UID_VAL}/${label}" >/dev/null 2>&1 || true
    echo "[$TS] restored ${label}" >> "$LOG_FILE"
  fi
}

{
  echo "[$TS] watchdog-start"

  ensure_agent "com.vio83.real-max-hourly" "$ROOT_DIR/automation/mac-scripts/com.vio83.real-max-hourly.plist"
  ensure_agent "com.vio83.real-max-daily" "$ROOT_DIR/automation/mac-scripts/com.vio83.real-max-daily.plist"

  if [[ "$DISABLE_OLLAMA_MODEL_SYNC" == "1" ]]; then
    if launchctl print "gui/${UID_VAL}/com.vio83.ollama-model-sync" >/dev/null 2>&1; then
      launchctl bootout "gui/${UID_VAL}/com.vio83.ollama-model-sync" >/dev/null 2>&1 || true
      echo "[$TS] disabled com.vio83.ollama-model-sync" >> "$LOG_FILE"
    fi
  fi

  FREE_GB="$(df -g / | awk 'NR==2 {print $4}')"
  LOAD_1M="$(sysctl -n vm.loadavg 2>/dev/null | awk '{gsub(/[{}]/,""); print int($1)}')"
  MEM_PRESSURE_PAGES="$(vm_stat 2>/dev/null | awk '/Pages occupied by compressor/ {gsub("\\.","",$5); print $5+0}')"
  echo "[$TS] free_gb=${FREE_GB} load_1m=${LOAD_1M:-0} mem_pressure_pages=${MEM_PRESSURE_PAGES:-0}" >> "$LOG_FILE"

  if [[ "$LOAD_1M" =~ ^[0-9]+$ ]] && [[ "$LOAD_1M" -ge "$HIGH_LOAD_THRESHOLD" ]]; then
    echo "[$TS] high-load detected -> run maintenance" >> "$LOG_FILE"
    bash "$ROOT_DIR/scripts/runtime/run_real_max_maintenance.sh" >/dev/null 2>&1 || true
  fi

  if [[ "$MEM_PRESSURE_PAGES" =~ ^[0-9]+$ ]] && [[ "$MEM_PRESSURE_PAGES" -ge "$HIGH_MEM_PRESSURE_PAGES" ]]; then
    echo "[$TS] high-memory-pressure detected -> run optimizer normal" >> "$LOG_FILE"
    bash "$ROOT_DIR/scripts/runtime/macos_ultra_optimizer.sh" "normal" >/dev/null 2>&1 || true
  fi

  if [[ "$FREE_GB" =~ ^[0-9]+$ ]] && [[ "$FREE_GB" -le "$THRESHOLD_GB" ]]; then
    MSG="[VIO83] Spazio critico: ${FREE_GB}GB liberi (soglia ${THRESHOLD_GB}GB). Watchdog ha avviato maintenance."
    echo "[$TS] ALERT ${MSG}" >> "$ALERT_LOG"

    # Trigger maintenance when low space is detected.
    bash "$ROOT_DIR/scripts/runtime/run_real_max_maintenance.sh" >/dev/null 2>&1 || true
    bash "$ROOT_DIR/scripts/runtime/macos_ultra_optimizer.sh" "emergency" >/dev/null 2>&1 || true

    if command -v osascript >/dev/null 2>&1; then
      osascript -e "display notification \"${MSG}\" with title \"VIO83 Real-Max Watchdog\" sound name \"Submarine\"" >/dev/null 2>&1 || true
    fi
  fi

  echo "[$TS] watchdog-done"
} >> "$LOG_FILE" 2>&1
