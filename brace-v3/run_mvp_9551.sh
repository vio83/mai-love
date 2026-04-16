#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/.run_logs"
PID_FILE="$LOG_DIR/mvp_9551.pid"
PORT=9551
mkdir -p "$LOG_DIR"

start() {
  if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "MVP gia attivo (PID $(cat "$PID_FILE")) su https://127.0.0.1:${PORT}"
    return 0
  fi

  local pids
  pids="$(lsof -tiTCP:${PORT} -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "Porta ${PORT} occupata, stop PID: $pids"
    kill -15 $pids || true
    sleep 1
    for pid in $pids; do
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid" || true
    done
  fi

  nohup env GIULIA_PROTO_PORT="$PORT" python3 "$ROOT_DIR/prototipo_web_advanced.py" > "$LOG_DIR/mvp_9551.log" 2>&1 &
  local pid=$!
  echo "$pid" > "$PID_FILE"
  sleep 1

  if kill -0 "$pid" 2>/dev/null; then
    echo "MVP avviato (PID $pid) su https://127.0.0.1:${PORT}"
  else
    echo "Errore avvio MVP. Log: $LOG_DIR/mvp_9551.log"
    return 1
  fi
}

stop() {
  if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    kill -15 "$(cat "$PID_FILE")" || true
    sleep 1
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      kill -9 "$(cat "$PID_FILE")" || true
    fi
    rm -f "$PID_FILE"
    echo "MVP fermato"
    return 0
  fi

  local pids
  pids="$(lsof -tiTCP:${PORT} -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    kill -15 $pids || true
    sleep 1
    for pid in $pids; do
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid" || true
    done
    echo "MVP fermato su porta ${PORT}"
  else
    echo "MVP non attivo"
  fi
}

status() {
  if lsof -nP -iTCP:${PORT} -sTCP:LISTEN >/dev/null 2>&1; then
    echo "MVP attivo su https://127.0.0.1:${PORT}"
    return 0
  fi
  echo "MVP non attivo"
  return 1
}

case "${1:-start}" in
  start) start ;;
  stop) stop ;;
  restart) stop || true; start ;;
  status) status ;;
  *)
    echo "Uso: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
