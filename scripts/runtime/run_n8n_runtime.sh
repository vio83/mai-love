#!/usr/bin/env bash
# Runtime runner robusto per n8n (ordine: custom cmd -> docker -> nvm node22 -> npx)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

sanitize_n8n_encryption_env() {
  if [[ "${N8N_STRICT_ENCRYPTION:-0}" == "1" ]]; then
    echo "[n8n-runner] N8N_STRICT_ENCRYPTION=1: nessuna sanitizzazione chiave"
    return 0
  fi

  if [[ -z "${N8N_ENCRYPTION_KEY:-}" ]]; then
    return 0
  fi

  local config_file="$HOME/.n8n/config"
  if [[ ! -f "$config_file" ]]; then
    return 0
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    return 0
  fi

  local compare_rc=0
  if python3 - "$config_file" <<'PY'
import json
import os
import sys

cfg_path = sys.argv[1]
env_key = os.environ.get("N8N_ENCRYPTION_KEY")

try:
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
except Exception:
    sys.exit(2)

cfg_key = cfg.get("encryptionKey") if isinstance(cfg, dict) else None
if not env_key or not cfg_key:
    sys.exit(3)

sys.exit(0 if env_key == cfg_key else 1)
PY
  then
    compare_rc=0
  else
    compare_rc=$?
  fi

  if [[ $compare_rc -eq 1 ]]; then
    echo "[n8n-runner] mismatch N8N_ENCRYPTION_KEY vs ~/.n8n/config: unset automatico per avvio locale"
    unset N8N_ENCRYPTION_KEY
  fi
}

sanitize_n8n_encryption_env

# 1) comando custom esplicito
if [[ -n "${N8N_START_CMD:-}" ]]; then
  echo "[n8n-runner] uso N8N_START_CMD custom"
  if /bin/bash -lc "$N8N_START_CMD"; then
    exit 0
  else
    echo "[n8n-runner] N8N_START_CMD fallito: provo fallback automatici"
  fi
fi

# 2) Docker fallback (consigliato se Node locale non compatibile)
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    echo "[n8n-runner] avvio n8n via Docker"
    docker rm -f vio83-n8n >/dev/null 2>&1 || true
    exec docker run --rm \
      --name vio83-n8n \
      -p 5678:5678 \
      -e N8N_HOST=127.0.0.1 \
      -e N8N_PORT=5678 \
      -e N8N_PROTOCOL=http \
      -e N8N_SECURE_COOKIE=false \
      -e WEBHOOK_URL=http://127.0.0.1:5678/ \
      -v "$PROJECT_DIR/.n8n:/home/node/.n8n" \
      n8nio/n8n:latest
  else
    echo "[n8n-runner] docker installato ma daemon non attivo: passo al fallback"
  fi
fi

# 3) nvm + Node (22/20/18 se disponibile)
if [[ -s "$HOME/.nvm/nvm.sh" ]]; then
  # shellcheck source=/dev/null
  source "$HOME/.nvm/nvm.sh"

  N8N_NODE_VERSION=""
  for v in 22 20 18; do
    if nvm ls "$v" >/dev/null 2>&1; then
      N8N_NODE_VERSION="$v"
      break
    fi
  done

  if [[ -n "$N8N_NODE_VERSION" ]]; then
    echo "[n8n-runner] avvio n8n via nvm Node $N8N_NODE_VERSION"
    exec bash -lc 'source "$HOME/.nvm/nvm.sh" && nvm use "'$N8N_NODE_VERSION'" >/dev/null && export N8N_HOST=127.0.0.1 N8N_PORT=5678 N8N_PROTOCOL=http N8N_SECURE_COOKIE=false WEBHOOK_URL=http://127.0.0.1:5678/ && npx n8n start'
  fi
fi

# 4) fallback npx standard
echo "[n8n-runner] fallback npx n8n (richiede Node 18/20/22)"
export N8N_HOST=127.0.0.1
export N8N_PORT=5678
export N8N_PROTOCOL=http
export N8N_SECURE_COOKIE=false
export WEBHOOK_URL=http://127.0.0.1:5678/
exec npx n8n start
