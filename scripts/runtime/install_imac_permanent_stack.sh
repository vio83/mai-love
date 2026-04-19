#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
SYNC_ENV_TARGET="$HOME/.config/vio83-sync.env"
mkdir -p "$USER_SYSTEMD_DIR" "$HOME/.config" "$ROOT_DIR/automation/logs"

chmod +x \
  "$ROOT_DIR/scripts/runtime/imac_permanent_stack.sh" \
  "$ROOT_DIR/scripts/runtime/imac_sync_forever.sh" \
  "$ROOT_DIR/scripts/runtime/certify_imac_runtime_99_9.sh"

if [[ ! -f "$SYNC_ENV_TARGET" ]]; then
  cp "$ROOT_DIR/.env.sync-imac.example" "$SYNC_ENV_TARGET"
fi

AUTO_PEER_HOST="$(python3 - <<'PY'
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
print('')
PY
)"

if [[ -n "$AUTO_PEER_HOST" ]]; then
  python3 - "$SYNC_ENV_TARGET" "$AUTO_PEER_HOST" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
peer = sys.argv[2]
lines = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
updates = {
    'PEER_HOST': peer,
    'PEER_USER': 'padronavio',
    'PEER_SSH_TARGET': f'padronavio@{peer}',
    'PEER_REPO_DIR': '"/Users/padronavio/Projects/vio83-ai-orchestra"',
    'PEER_VSCODE_DIR': '"/Users/padronavio/Library/Application Support/Code/User"',
}
out = []
seen = set()
for line in lines:
    if line.strip() and not line.lstrip().startswith('#') and '=' in line:
        key = line.split('=', 1)[0].strip()
        if key in updates:
            out.append(f'{key}={updates[key]}')
            seen.add(key)
            continue
    out.append(line)
for k, v in updates.items():
    if k not in seen:
        out.append(f'{k}={v}')
path.write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')
PY
fi

cat > "$USER_SYSTEMD_DIR/vio83-imac-stack.service" <<EOF
[Unit]
Description=VIO83 iMac permanent stack
After=default.target network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT_DIR
Environment=PYTHONPATH=$ROOT_DIR
Environment=VIO_NO_HYBRID=true
ExecStart=$ROOT_DIR/scripts/runtime/imac_permanent_stack.sh
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

cat > "$USER_SYSTEMD_DIR/vio83-imac-sync.service" <<EOF
[Unit]
Description=VIO83 iMac continuous mirror sync
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT_DIR
ExecStart=$ROOT_DIR/scripts/runtime/imac_sync_forever.sh
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

cat > "$USER_SYSTEMD_DIR/vio83-imac-certify.service" <<EOF
[Unit]
Description=VIO83 iMac 99.9 certification audit
After=vio83-imac-stack.service

[Service]
Type=oneshot
WorkingDirectory=$ROOT_DIR
Environment=PYTHONPATH=$ROOT_DIR
ExecStart=$ROOT_DIR/scripts/runtime/certify_imac_runtime_99_9.sh
EOF

cat > "$USER_SYSTEMD_DIR/vio83-imac-certify.timer" <<EOF
[Unit]
Description=Run VIO83 iMac certification every 15 minutes

[Timer]
OnBootSec=90
OnUnitActiveSec=15m
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now vio83-imac-stack.service
systemctl --user enable --now vio83-imac-sync.service
systemctl --user enable --now vio83-imac-certify.timer

loginctl enable-linger "$USER" 2>/dev/null || true

printf '\n✅ Permanent iMac stack installed\n'
printf '   - stack: vio83-imac-stack.service\n'
printf '   - sync:  vio83-imac-sync.service\n'
printf '   - cert:  vio83-imac-certify.timer\n'
printf '   - sync env template: %s\n' "$SYNC_ENV_TARGET"

bash "$ROOT_DIR/scripts/runtime/certify_imac_runtime_99_9.sh" || true
