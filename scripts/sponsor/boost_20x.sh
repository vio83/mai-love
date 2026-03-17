#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OPEN_DRAFTS=false
for arg in "$@"; do
  case "$arg" in
    --open-drafts)
      OPEN_DRAFTS=true
      ;;
  esac
done

mkdir -p "$ROOT_DIR/automation/logs" "$ROOT_DIR/data/weekly-content"

# 1) Generate fresh bilingual weekly bundle
bash "$ROOT_DIR/scripts/sponsor/run_weekly_content_engine.sh" >/dev/null 2>&1 || true

# 2) Force all 4 targets now (regardless weekday)
TARGETS=("linkedin_post_1" "kofi_post" "linkedin_post_2" "github_weekly_post")
for target in "${TARGETS[@]}"; do
  if [[ "$OPEN_DRAFTS" == "true" ]]; then
    bash "$ROOT_DIR/scripts/sponsor/run_daily_autopilot.sh" --force --force-target="$target" --open-drafts >/dev/null 2>&1 || true
  else
    bash "$ROOT_DIR/scripts/sponsor/run_daily_autopilot.sh" --force --force-target="$target" >/dev/null 2>&1 || true
  fi
done

# 3) Write summary snapshot
python3 - <<'PY'
import json
from pathlib import Path
root = Path('.')
latest = root / 'data/weekly-content/latest.json'
out = root / 'data/weekly-content/turbo-20x-summary.json'

obj = json.loads(latest.read_text(encoding='utf-8')) if latest.exists() else {}
summary = {
    'generated_on': obj.get('generated_on'),
    'iso_week': obj.get('iso_week'),
    'optimization': obj.get('optimization', {}),
    'targets': [
        'linkedin_post_1_it/en',
        'kofi_post_it/en',
        'linkedin_post_2_it/en',
        'github_weekly_post_it/en'
    ],
    'latest_json': str(latest),
}
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print('✅ Turbo 20X completed')
print('Summary:', out)
print('Latest:', latest)
PY
