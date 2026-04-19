#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/automation/logs"
STATE_DIR="$ROOT_DIR/data/config"
mkdir -p "$LOG_DIR" "$STATE_DIR" "$ROOT_DIR/.pids"

STACK_LOG="$LOG_DIR/imac-permanent-stack.log"
BACKEND_LOG="$LOG_DIR/imac-backend-forever.log"
FRONTEND_LOG="$LOG_DIR/imac-frontend-forever.log"
OLLAMA_LOG="$LOG_DIR/imac-ollama-forever.log"
STATE_FILE="$STATE_DIR/imac-permanent-stack-state.json"

TICK_SEC="${STACK_TICK_SEC:-5}"
BACKEND_PORT="${VIO_BACKEND_PORT:-4000}"
FRONTEND_PORT="${VIO_FRONTEND_PORT:-5173}"
OLLAMA_URL="${OLLAMA_HOST:-http://127.0.0.1:11434}"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set +u
  set -a
  source "$ROOT_DIR/.env"
  set +a
  set -u
fi

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$STACK_LOG"
}

is_http_ok() {
  local url="$1"
  curl -fsS --max-time 4 "$url" >/dev/null 2>&1
}

start_ollama() {
  if is_http_ok "$OLLAMA_URL/api/tags"; then
    return 0
  fi
  if command -v ollama >/dev/null 2>&1; then
    log "ollama-down -> start"
    nohup ollama serve >> "$OLLAMA_LOG" 2>&1 &
  else
    log "ollama-missing"
  fi
}

start_backend() {
  if is_http_ok "http://127.0.0.1:${BACKEND_PORT}/health"; then
    return 0
  fi
  log "backend-down -> start"
  nohup bash "$ROOT_DIR/scripts/runtime/start_backend_dev_safe.sh" >> "$BACKEND_LOG" 2>&1 &
}

start_frontend() {
  if is_http_ok "http://127.0.0.1:${FRONTEND_PORT}"; then
    return 0
  fi
  if command -v npm >/dev/null 2>&1; then
    log "frontend-down -> start"
    nohup npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" >> "$FRONTEND_LOG" 2>&1 &
  else
    log "npm-missing"
  fi
}

start_supervisor() {
  bash "$ROOT_DIR/scripts/runtime/start_runtime_services.sh" >> "$STACK_LOG" 2>&1 || true
}

write_state() {
  python3 - "$STATE_FILE" <<'PY'
import json, sys, time
path = sys.argv[1]
payload = {
    'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'status': 'running',
    'service': 'vio83-imac-stack',
}
with open(path, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
PY
}

log "imac-permanent-stack-start"
while true; do
  start_ollama
  start_backend
  start_frontend
  start_supervisor
  write_state
  sleep "$TICK_SEC"
done
