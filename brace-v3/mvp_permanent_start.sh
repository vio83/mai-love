#!/usr/bin/env bash
set -euo pipefail

BRACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$BRACE_DIR/.run_logs"
mkdir -p "$RUN_DIR"

PORT="${GIULIA_PROTO_PORT:-9011}"
SUP_PID_FILE="$RUN_DIR/mvp_supervisor.pid"
LOG_FILE="$RUN_DIR/mvp_permanent.log"

if [[ -f "$SUP_PID_FILE" ]]; then
  old_pid="$(cat "$SUP_PID_FILE" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "[MVP] Supervisore gia attivo (PID: $old_pid)"
    echo "[MVP] URL: https://127.0.0.1:$PORT/"
    open "https://127.0.0.1:$PORT/" || true
    exit 0
  fi
fi

# Libera solo la porta dedicata MVP.
pids="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$pids" ]]; then
  kill -15 $pids || true
  sleep 1
  for pid in $pids; do
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" || true
  done
fi

cat > "$RUN_DIR/mvp_port.txt" <<EOF
$PORT
EOF

nohup bash -lc '
  set -euo pipefail
  while true; do
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] START prototipo_web_advanced.py" >> "'"$LOG_FILE"'"
    GIULIA_PROTO_PORT="'"$PORT"'" python3 "'"$BRACE_DIR"'"/prototipo_web_advanced.py >> "'"$LOG_FILE"'" 2>&1 || true
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] RESTART in 2s" >> "'"$LOG_FILE"'"
    sleep 2
  done
' >/dev/null 2>&1 &

echo $! > "$SUP_PID_FILE"
sleep 1

echo "[MVP] Supervisore avviato (PID: $(cat "$SUP_PID_FILE"))"
echo "[MVP] Porta dedicata: $PORT"
echo "[MVP] URL: https://127.0.0.1:$PORT/"
echo "[MVP] Log: $LOG_FILE"
open "https://127.0.0.1:$PORT/" || true
