#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/automation/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/imac-sync-forever.log"

SYNC_ENV_FILE="${SYNC_ENV_FILE:-$HOME/.config/vio83-sync.env}"
if [[ -f "$SYNC_ENV_FILE" ]]; then
  set +u
  source "$SYNC_ENV_FILE"
  set -u
fi

PEER_HOST="${PEER_HOST:-}"
PEER_USER="${PEER_USER:-padronavio}"
PEER_REPO_DIR="${PEER_REPO_DIR:-/Users/padronavio/Projects/vio83-ai-orchestra}"

auto_detect_peer_host() {
  if ! command -v tailscale >/dev/null 2>&1; then
    return 1
  fi
  python3 - <<'PY'
import json, subprocess
try:
    out = subprocess.check_output(['tailscale', 'status', '--json'], text=True)
    peers = json.loads(out).get('Peer', {})
    for peer in peers.values():
        if not peer.get('Online'):
            continue
        name = (peer.get('DNSName') or '').rstrip('.')
        ips = peer.get('TailscaleIPs') or []
        if any(tag in name.lower() for tag in ['macbook', 'macbook-air', 'mac-air']):
            print(ips[0] if ips else name)
            raise SystemExit(0)
except SystemExit:
    raise
except Exception:
    pass
raise SystemExit(1)
PY
}

if [[ -z "$PEER_HOST" ]]; then
  PEER_HOST="$(auto_detect_peer_host 2>/dev/null || true)"
fi
PEER_SSH_TARGET="${PEER_SSH_TARGET:-${PEER_USER}@${PEER_HOST}}"

PEER_VSCODE_DIR="${PEER_VSCODE_DIR:-/Users/vio/Library/Application Support/Code/User}"
PEER_VSCODE_DIR="${PEER_VSCODE_DIR:-/Users/vio/Library/Application Support/Code/User}"
LOCAL_REPO_DIR="${LOCAL_REPO_DIR:-$ROOT_DIR}"
LOCAL_VSCODE_DIR="${LOCAL_VSCODE_DIR:-$HOME/.config/Code/User}"
IMAC_SYNC_INTERVAL_SEC="${IMAC_SYNC_INTERVAL_SEC:-5}"

mkdir -p "$LOCAL_VSCODE_DIR/snippets"

RSYNC_SSH="ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 -o ServerAliveInterval=15 -o ServerAliveCountMax=3"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

wait_for_peer() {
  if [[ -z "$PEER_HOST" ]]; then
    log "peer-host-not-configured"
    sleep "$IMAC_SYNC_INTERVAL_SEC"
    return 1
  fi
  if ! ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 "$PEER_SSH_TARGET" 'echo ok' >/dev/null 2>&1; then
    log "peer-unreachable:$PEER_SSH_TARGET"
    sleep "$IMAC_SYNC_INTERVAL_SEC"
    return 1
  fi
  return 0
}

sync_vscode_file() {
  local remote_path="$1"
  local local_path="$2"
  mkdir -p "$(dirname "$local_path")"
  rsync -az -e "$RSYNC_SSH" "$PEER_SSH_TARGET:$remote_path" "$local_path" >/dev/null 2>&1 || true
}

sync_repo() {
  rsync -az --delete \
    --exclude '.git/' \
    --exclude 'node_modules/' \
    --exclude 'dist/' \
    --exclude '.venv/' \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '.mypy_cache/' \
    --exclude '.pytest_cache/' \
    --exclude '.logs/' \
    --exclude 'logs/' \
    --exclude '.pids/' \
    --exclude 'data/*.db' \
    --exclude '.env' \
    --exclude '.env.*' \
    -e "$RSYNC_SSH" \
    "$PEER_SSH_TARGET:$PEER_REPO_DIR/" "$LOCAL_REPO_DIR/" >/dev/null 2>&1 || true
}

log "imac-sync-forever-start"
while true; do
  if wait_for_peer; then
    sync_vscode_file "$PEER_VSCODE_DIR/settings.json" "$LOCAL_VSCODE_DIR/settings.json"
    sync_vscode_file "$PEER_VSCODE_DIR/keybindings.json" "$LOCAL_VSCODE_DIR/keybindings.json"
    rsync -az --delete -e "$RSYNC_SSH" "$PEER_SSH_TARGET:$PEER_VSCODE_DIR/snippets/" "$LOCAL_VSCODE_DIR/snippets/" >/dev/null 2>&1 || true
    sync_repo
    log "sync-ok:$PEER_SSH_TARGET"
  fi
  sleep "$IMAC_SYNC_INTERVAL_SEC"
done
