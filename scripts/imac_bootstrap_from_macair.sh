#!/bin/bash
# Mac Air -> iMac bootstrap orchestrator
# Runs safely when iMac is reachable; no destructive operations.

set -euo pipefail

IMAC_USER="vio"
IMAC_LAN="172.20.10.5"
IMAC_TS="100.116.120.3"
IMAC_KEY="$HOME/.ssh/id_ed25519_archimede"
PROJECT_ROOT="$HOME/Projects/vio83-ai-orchestra"
STATE_DIR="$HOME/.vio83"
STATE_FILE="$STATE_DIR/imac_bootstrap.done"
LOG="$STATE_DIR/imac_bootstrap.log"

mkdir -p "$STATE_DIR"
exec > >(tee -a "$LOG") 2>&1

if [[ -f "$STATE_FILE" ]]; then
  echo "[SKIP] Bootstrap already completed at $(cat "$STATE_FILE")"
  exit 0
fi

echo "=== iMac bootstrap attempt $(date) ==="

pick_host() {
  if ping -c 1 -W 2 "$IMAC_LAN" >/dev/null 2>&1; then
    echo "$IMAC_LAN"
    return 0
  fi
  if ping -c 1 -W 2 "$IMAC_TS" >/dev/null 2>&1; then
    echo "$IMAC_TS"
    return 0
  fi
  return 1
}

if ! HOST=$(pick_host); then
  echo "[WAIT] iMac offline (LAN+Tailscale)."
  exit 2
fi

echo "[INFO] Using host: $HOST"
SSH_OPTS=( -o IdentityFile="$IMAC_KEY" -o ConnectTimeout=12 -o BatchMode=yes )

if ! ssh "${SSH_OPTS[@]}" "$IMAC_USER@$HOST" 'echo SSH_OK' >/dev/null 2>&1; then
  echo "[WAIT] iMac reachable by ping but SSH not ready."
  exit 3
fi

echo "[INFO] SSH OK. Preparing remote directories..."
ssh "${SSH_OPTS[@]}" "$IMAC_USER@$HOST" 'mkdir -p ~/.vio83-bootstrap ~/mac-archive/downloads'

echo "[INFO] Uploading scripts..."
scp "${SSH_OPTS[@]}" "$PROJECT_ROOT/scripts/imac_remote_devstack_arch.sh" "$IMAC_USER@$HOST:~/.vio83-bootstrap/"
scp "${SSH_OPTS[@]}" "$PROJECT_ROOT/scripts/imac_ollama_install_all.sh" "$IMAC_USER@$HOST:~/.vio83-bootstrap/"
scp "${SSH_OPTS[@]}" "$PROJECT_ROOT/scripts/imac_transfer_and_cleanup.sh" "$IMAC_USER@$HOST:~/.vio83-bootstrap/"

echo "[INFO] Running remote dev stack bootstrap..."
ssh "${SSH_OPTS[@]}" "$IMAC_USER@$HOST" 'chmod +x ~/.vio83-bootstrap/*.sh && bash ~/.vio83-bootstrap/imac_remote_devstack_arch.sh'

echo "[INFO] Running remote Ollama model installer in background..."
ssh "${SSH_OPTS[@]}" "$IMAC_USER@$HOST" 'nohup bash ~/.vio83-bootstrap/imac_ollama_install_all.sh >/tmp/imac_ollama_install_all.log 2>&1 &'

# Optional transfer script execution (safe no-op if local files not present)
echo "[INFO] Triggering transfer job from Mac side..."
bash "$PROJECT_ROOT/scripts/imac_transfer_and_cleanup.sh" || true

date -Iseconds > "$STATE_FILE"
echo "[DONE] iMac bootstrap completed at $(cat "$STATE_FILE")"
