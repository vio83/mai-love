#!/usr/bin/env bash
# Avvia il supervisor locale per OpenClaw / LegalRoom / n8n

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SUPERVISOR="$PROJECT_DIR/scripts/runtime/local_runtime_supervisor.py"
PID_FILE="$PROJECT_DIR/.pids/runtime-supervisor.pid"
LOG_FILE="$PROJECT_DIR/.logs/runtime-supervisor.log"

mkdir -p "$PROJECT_DIR/.pids" "$PROJECT_DIR/.logs"

if [[ -f "$PID_FILE" ]]; then
  existing_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${existing_pid}" ]] && kill -0 "$existing_pid" 2>/dev/null; then
    echo "[runtime] Supervisor già attivo (PID $existing_pid)"
    exit 0
  fi
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[runtime] python3 non trovato: impossibile avviare supervisor" >&2
  exit 1
fi

nohup python3 "$SUPERVISOR" >> "$LOG_FILE" 2>&1 &
new_pid=$!
echo "$new_pid" > "$PID_FILE"

sleep 1
if kill -0 "$new_pid" 2>/dev/null; then
  echo "[runtime] Supervisor avviato (PID $new_pid)"
  exit 0
fi

echo "[runtime] Avvio supervisor fallito. Controlla: $LOG_FILE" >&2
exit 1
