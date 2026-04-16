#!/usr/bin/env bash
set -euo pipefail

BRACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$BRACE_DIR/.run_logs"
PORT="${GIULIA_PROTO_PORT:-9011}"
SUP_PID_FILE="$RUN_DIR/mvp_supervisor.pid"
LOG_FILE="$RUN_DIR/mvp_permanent.log"

if [[ -f "$SUP_PID_FILE" ]]; then
  sup_pid="$(cat "$SUP_PID_FILE" 2>/dev/null || true)"
  if [[ -n "$sup_pid" ]] && kill -0 "$sup_pid" 2>/dev/null; then
    echo "[MVP] Supervisore: ATTIVO (PID: $sup_pid)"
  else
    echo "[MVP] Supervisore: NON ATTIVO (pid file stale)"
  fi
else
  echo "[MVP] Supervisore: NON ATTIVO"
fi

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[MVP] App: ATTIVA su https://127.0.0.1:$PORT/"
else
  echo "[MVP] App: NON ATTIVA su porta $PORT"
fi

if [[ -f "$LOG_FILE" ]]; then
  echo "[MVP] Ultime righe log:"
  tail -n 10 "$LOG_FILE"
else
  echo "[MVP] Log non presente"
fi
