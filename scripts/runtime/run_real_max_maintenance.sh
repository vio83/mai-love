#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/automation/logs"
mkdir -p "$LOG_DIR" "$ROOT_DIR/data/config"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE="$LOG_DIR/real-max-maintenance.log"

{
  echo "[$TS] 🚀 REAL MAX maintenance start"

  FREE_GB="$(df -g "$ROOT_DIR" | awk 'NR==2 {print $4}')"
  echo "[$TS] 💽 Free space: ${FREE_GB}GB"

  # Pulizia sicura: solo log vecchi (non tocca database o dati core)
  find "$ROOT_DIR/automation/logs" -type f -mtime +21 -delete 2>/dev/null || true
  find "$ROOT_DIR/data/logs" -type f -mtime +21 -delete 2>/dev/null || true

  if [[ "${FREE_GB:-0}" =~ ^[0-9]+$ ]] && [[ "$FREE_GB" -lt 20 ]]; then
    echo "[$TS] ⚠️ Free space sotto soglia (20GB). Eseguire clean manuale consigliato."
  fi

  if ! python3 "$ROOT_DIR/scripts/runtime/real_max_optimizer.py" --write-env --request-timeout 12 --max-tokens 180 --out "$ROOT_DIR/data/config/real-max-optimizer-report.json"; then
    echo "[$TS] ⚠️ Optimizer returned non-zero (continuo con fallback report)"
    python3 - <<'PY'
import json, time
from pathlib import Path
p = Path('data/config/real-max-optimizer-report.json')
if not p.exists():
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'status': 'degraded',
        'note': 'optimizer timeout/failure; keeping existing local preference',
    }, ensure_ascii=False, indent=2), encoding='utf-8')
PY
  fi

  if command -v curl >/dev/null 2>&1; then
    ORCH_PROFILE="$(python3 - <<'PY'
from pathlib import Path
env = Path('.env')
profile = 'real-max-local'
if env.exists():
    for raw in env.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        if k.strip() == 'VIO_EXECUTION_PROFILE':
            profile = (v.strip().strip('"').strip("'")) or 'real-max-local'
            break
if profile in {'balanced', 'real-max'}:
    profile = 'real-max-local'
print(profile)
PY
)"

    ORCH_NO_HYBRID="$(python3 - <<'PY'
print('true')
PY
)"

    curl -sS -X PUT "http://127.0.0.1:4000/orchestration/profile?profile=${ORCH_PROFILE}&no_hybrid=${ORCH_NO_HYBRID}&local_model_preference=$(python3 - <<'PY'
import json
from pathlib import Path
p = Path('data/config/real-max-optimizer-report.json')
if p.exists():
    d = json.loads(p.read_text(encoding='utf-8'))
    print(d.get('best_model','qwen2.5-coder:3b'))
else:
    print('qwen2.5-coder:3b')
PY
)" >/tmp/vio-real-max-maintenance-api.json 2>/dev/null || true
  fi

  if [[ -s /tmp/vio-real-max-maintenance-api.json ]]; then
    echo "[$TS] ✅ Backend profile sync ok"
  else
    echo "[$TS] ℹ️ Backend profile sync skipped (backend offline)"
  fi

  python3 - <<'PY'
import json
import time
from pathlib import Path

env_path = Path('.env')
env = {}
if env_path.exists():
    for raw in env_path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

profile = (env.get('VIO_EXECUTION_PROFILE') or 'real-max-local').strip().lower()
if profile in {'balanced', 'real-max', 'hybrid'}:
    profile = 'real-max-local'

model_pref = env.get('VIO_LOCAL_MODEL_PREFERENCE') or 'qwen2.5-coder:3b'

snapshot = {
    'updated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'profile': profile,
    'no_hybrid': True,
    'effective_mode': 'local-only',
    'local_model_preference': model_pref,
    'real_max_autotune': True,
}

out = Path('data/config/orchestration-profile.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
print('snapshot-updated')
PY

  echo "[$TS] ✅ REAL MAX maintenance done"
} >> "$LOG_FILE" 2>&1
