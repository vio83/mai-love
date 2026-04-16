#!/usr/bin/env bash
set -euo pipefail

BRACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$BRACE_DIR/.run_logs"
PORT="${GIULIA_PROTO_PORT:-9011}"
SUP_PID_FILE="$RUN_DIR/mvp_supervisor.pid"

if [[ -f "$SUP_PID_FILE" ]]; then
  sup_pid="$(cat "$SUP_PID_FILE" 2>/dev/null || true)"
  if [[ -n "$sup_pid" ]] && kill -0 "$sup_pid" 2>/dev/null; then
    kill -15 "$sup_pid" || true
    sleep 1
    kill -0 "$sup_pid" 2>/dev/null && kill -9 "$sup_pid" || true
    echo "[MVP] Supervisore fermato (PID: $sup_pid)"
  fi
  rm -f "$SUP_PID_FILE"
fi

pids="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$pids" ]]; then
  kill -15 $pids || true
  sleep 1
  for pid in $pids; do
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" || true
  done
  echo "[MVP] Processo applicativo su porta $PORT fermato"
fi

echo "[MVP] Stop completato"
