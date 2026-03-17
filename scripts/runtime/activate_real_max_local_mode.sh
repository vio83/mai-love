#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="$ROOT_DIR/.env"
mkdir -p "$ROOT_DIR/data/config"
mkdir -p "$ROOT_DIR/automation/logs"

PLIST_SRC="$ROOT_DIR/automation/mac-scripts/com.vio83.real-max-maintenance.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.vio83.real-max-maintenance.plist"

if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" <<'EOF'
VIO_EXECUTION_PROFILE=real-max-local
VIO_NO_HYBRID=true
VIO_LOCAL_MODEL_PREFERENCE=qwen2.5-coder:3b
EOF
fi

python3 - <<'PY'
from pathlib import Path
import json
import time

env_path = Path('.env')
lines = env_path.read_text(encoding='utf-8').splitlines() if env_path.exists() else []
updates = {
    'VIO_EXECUTION_PROFILE': 'real-max-local',
    'VIO_NO_HYBRID': 'true',
    'VIO_LOCAL_MODEL_PREFERENCE': 'qwen2.5-coder:3b',
  'VIO_REAL_MAX_AUTOTUNE': 'true',
}

out = []
seen = set()
for line in lines:
    s = line.strip()
    if s and not s.startswith('#') and '=' in line:
        k = line.split('=', 1)[0].strip()
        if k in updates:
            out.append(f"{k}={updates[k]}")
            seen.add(k)
            continue
    out.append(line)

if out and out[-1].strip() != '':
    out.append('')

for k, v in updates.items():
    if k not in seen:
        out.append(f"{k}={v}")

env_path.write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')

snapshot = {
    'updated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'profile': updates['VIO_EXECUTION_PROFILE'],
    'no_hybrid': True,
    'local_model_preference': updates['VIO_LOCAL_MODEL_PREFERENCE'],
  'real_max_autotune': True,
}
Path('data/config/orchestration-profile.json').write_text(
    json.dumps(snapshot, ensure_ascii=False, indent=2),
    encoding='utf-8',
)
print('✅ .env aggiornato in modalità REAL MAX LOCAL')
print('✅ Snapshot scritto in data/config/orchestration-profile.json')
PY

if command -v curl >/dev/null 2>&1; then
  curl -sS -X PUT "http://127.0.0.1:4000/orchestration/profile?profile=real-max-local&no_hybrid=true&local_model_preference=qwen2.5-coder:3b" >/tmp/vio-real-max-profile.json 2>/dev/null || true
fi

if [[ -s /tmp/vio-real-max-profile.json ]]; then
  echo "✅ Profilo applicato live via API backend"
  cat /tmp/vio-real-max-profile.json
else
  echo "ℹ️ Backend non raggiungibile ora: profilo comunque persistente in .env"
fi

chmod +x "$ROOT_DIR/scripts/runtime/run_real_max_maintenance.sh"

if [[ -f "$PLIST_SRC" ]]; then
  mkdir -p "$HOME/Library/LaunchAgents"
  cp "$PLIST_SRC" "$PLIST_DST"
  launchctl unload "$PLIST_DST" 2>/dev/null || true
  launchctl load "$PLIST_DST"
  echo "✅ Scheduler auto-ottimizzazione installato (launchd)"
else
  echo "⚠️ Plist non trovato: $PLIST_SRC"
fi

bash "$ROOT_DIR/scripts/runtime/run_real_max_maintenance.sh" || true

echo "✅ Modalità REAL MAX LOCAL pronta"
