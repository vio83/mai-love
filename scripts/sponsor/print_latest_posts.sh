#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

python3 - <<'PY'
import json
from pathlib import Path
p = Path('data/weekly-content/latest.json')
if not p.exists():
    raise SystemExit('❌ latest.json non trovato. Esegui prima: bash scripts/sponsor/boost_20x.sh')
obj = json.loads(p.read_text(encoding='utf-8'))

def show(title: str, key_it: str, key_en: str):
    print(f"\n=== {title} IT ===\n")
    print(obj.get(key_it, ''))
    print(f"\n=== {title} EN ===\n")
    print(obj.get(key_en, ''))

show('LinkedIn #1', 'linkedin_post_1_it', 'linkedin_post_1_en')
show('LinkedIn #2', 'linkedin_post_2_it', 'linkedin_post_2_en')
show('Ko-fi', 'kofi_post_it', 'kofi_post_en')
show('GitHub Weekly', 'github_weekly_post_it', 'github_weekly_post_en')
PY
