#!/usr/bin/env bash
# Arresta il supervisor locale runtime e i child process gestiti

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="$PROJECT_DIR/.pids/runtime-supervisor.pid"

stop_pid() {
  local pid="$1"
  if [[ -z "$pid" ]]; then
    return
  fi

  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true

    for _ in {1..20}; do
      if ! kill -0 "$pid" 2>/dev/null; then
        break
      fi
      sleep 0.2
    done

    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi
}

if [[ -f "$PID_FILE" ]]; then
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  stop_pid "$pid"
  rm -f "$PID_FILE"
  echo "[runtime] Supervisor fermato${pid:+ (PID $pid)}"
else
  echo "[runtime] Nessun PID file supervisor trovato"
fi

# Fallback sicurezza: termina eventuali processi orfani del supervisor
pkill -f "scripts/runtime/local_runtime_supervisor.py" 2>/dev/null || true
