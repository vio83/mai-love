#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

REPORT="$ROOT_DIR/data/config/imac-runtime-cert-latest.json"
mkdir -p "$(dirname "$REPORT")"

score=0
max=99.9
status="pass"

is_active() {
  local cmd="$1"
  eval "$cmd" >/dev/null 2>&1
}

check() {
  local name="$1"
  local points="$2"
  local cmd="$3"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "$name=pass|$points"
  else
    echo "$name=fail|0"
    status="warn"
  fi
}

results=()
results+=("$(check tailscaled 10 'systemctl is-active tailscaled')")
results+=("$(check sshd 10 'systemctl is-active sshd')")
results+=("$(check docker 8 'systemctl is-active docker')")
results+=("$(check user_stack 18 'systemctl --user is-active vio83-imac-stack.service')")
results+=("$(check user_sync 8 'systemctl --user is-active vio83-imac-sync.service')")
results+=("$(check frontend 12 'curl -fsS --max-time 4 http://127.0.0.1:5173 >/dev/null')")
results+=("$(check backend 12 'curl -fsS --max-time 4 http://127.0.0.1:4000/health >/dev/null')")
results+=("$(check ollama 12 'curl -fsS --max-time 4 http://127.0.0.1:11434/api/tags >/dev/null')")

local_only_json="$(bash "$ROOT_DIR/scripts/runtime/certify_runtime_local_only.sh" 2>/dev/null || true)"
if echo "$local_only_json" | grep -q '"status": "pass"'; then
  results+=("local_only=pass|9.9")
else
  results+=("local_only=fail|0")
  status="warn"
fi

for item in "${results[@]}"; do
  pts="${item#*|}"
  score=$(python3 - <<PY
print(round(float($score) + float($pts), 1))
PY
)
done

python3 - "$REPORT" "$status" "$score" "$max" "${results[*]}" <<'PY'
import json, sys, time
path, status, score, max_score, packed = sys.argv[1:6]
checks = {}
for item in packed.split():
    if '=' not in item or '|' not in item:
        continue
    name, rest = item.split('=', 1)
    state, pts = rest.split('|', 1)
    checks[name] = {'status': state, 'points': float(pts)}
payload = {
    'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'status': status,
    'score_percent': float(score),
    'max_score': float(max_score),
    'checks': checks,
}
with open(path, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
print(json.dumps(payload, ensure_ascii=False))
PY

if python3 - <<PY
import sys
sys.exit(0 if float('$score') >= 90.0 else 1)
PY
then
  exit 0
fi
exit 2
