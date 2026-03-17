#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PORT="${VIO_BACKEND_PORT:-4000}"

echo "🧯 BACKEND PANIC RESET — stop/clean/start"
echo "📍 Root: $ROOT_DIR"
echo "🔌 Porta target: $PORT"

# 1) STOP hard + soft (listener + pattern backend uvicorn)
LISTENER_PIDS="$(lsof -ti tcp:${PORT} || true)"
if [[ -n "$LISTENER_PIDS" ]]; then
  echo "⛔ Stop listener su :${PORT} -> $LISTENER_PIDS"
  kill $LISTENER_PIDS 2>/dev/null || true
  sleep 1
  STILL_LISTENING="$(lsof -ti tcp:${PORT} || true)"
  if [[ -n "$STILL_LISTENING" ]]; then
    echo "💥 Force kill listener persistenti -> $STILL_LISTENING"
    kill -9 $STILL_LISTENING 2>/dev/null || true
  fi
else
  echo "ℹ️ Nessun listener attivo su :${PORT}"
fi

pkill -f "uvicorn backend.api.server:app" 2>/dev/null || true
pkill -f "python3 -m uvicorn backend.api.server:app" 2>/dev/null || true

# 2) CLEAN mirata (solo cache/runtime temporanei)
echo "🧹 Pulizia cache Python backend/runtime"
find "$ROOT_DIR/backend" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find "$ROOT_DIR/scripts/runtime" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find "$ROOT_DIR/backend" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

rm -f /tmp/vio-real-max-*.json /tmp/vio_realmax_exit_code.txt 2>/dev/null || true

echo "✅ Stop/Clean completati. Riavvio backend safe..."

# 3) START (safe launcher)
exec bash "$ROOT_DIR/scripts/runtime/start_backend_dev_safe.sh"
