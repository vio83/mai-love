#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PORT="${VIO_BACKEND_PORT:-4000}"

PIDS="$(lsof -ti tcp:${PORT} || true)"
if [[ -n "$PIDS" ]]; then
  echo "⚠️ Porta ${PORT} occupata. Chiudo processi stale: $PIDS"
  kill -9 $PIDS || true
  sleep 1
fi

export PYTHONPATH="$ROOT_DIR"
export VIO_EXECUTION_PROFILE="real-max-local"
export VIO_NO_HYBRID="${VIO_NO_HYBRID:-true}"
export VIO_SPEED_MODE="true"
export VIO_SERVER_MAX_TOKENS="512"
export VIO_SERVER_MAX_TOKENS_HARD="768"
export VIO_TURBO_MAX_TOKENS="320"
export VIO_OLLAMA_TIMEOUT_SEC="45"
export VIO_OLLAMA_STREAM_TIMEOUT_SEC="90"

if [[ -z "${VIO_LOCAL_MODEL_PREFERENCE:-}" ]]; then
  export VIO_LOCAL_MODEL_PREFERENCE="qwen2.5-coder:3b"
fi

echo "🚀 Avvio backend su porta ${PORT} (safe mode)"
exec python3 -m uvicorn backend.api.server:app --reload --host 0.0.0.0 --port "$PORT"
