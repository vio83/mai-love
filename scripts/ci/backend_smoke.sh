#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PORT="${VIO_SMOKE_PORT:-4010}"
LOG_FILE="${PROJECT_ROOT}/.logs/backend-smoke.log"
PID_FILE="${PROJECT_ROOT}/.pids/backend-smoke.pid"

mkdir -p "${PROJECT_ROOT}/.logs" "${PROJECT_ROOT}/.pids"

cleanup() {
  if [[ -f "${PID_FILE}" ]]; then
    PID="$(cat "${PID_FILE}")"
    if kill -0 "${PID}" >/dev/null 2>&1; then
      kill "${PID}" >/dev/null 2>&1 || true
      wait "${PID}" 2>/dev/null || true
    fi
    rm -f "${PID_FILE}"
  fi
}
trap cleanup EXIT

cd "${PROJECT_ROOT}"
PYTHONPATH="${PROJECT_ROOT}" python3 -m uvicorn backend.api.server:app --host 127.0.0.1 --port "${PORT}" >"${LOG_FILE}" 2>&1 &
echo $! > "${PID_FILE}"

for _ in {1..60}; do
  if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
 done

curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/knowledge/registry" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/knowledge/domain-scores" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/kb/stats" >/dev/null

echo "Backend smoke OK on port ${PORT}"
