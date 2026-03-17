#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

STARS=0
FORKS=0
VIEWS=0

if command -v gh >/dev/null 2>&1; then
  STARS="$(gh api repos/vio83/vio83-ai-orchestra --jq '.stargazers_count' 2>/dev/null || echo 0)"
  FORKS="$(gh api repos/vio83/vio83-ai-orchestra --jq '.forks_count' 2>/dev/null || echo 0)"
  VIEWS="$(gh api repos/vio83/vio83-ai-orchestra/traffic/views --jq '.count' 2>/dev/null || echo 0)"
fi

if [[ $# -ge 1 ]]; then STARS="$1"; fi
if [[ $# -ge 2 ]]; then FORKS="$2"; fi
if [[ $# -ge 3 ]]; then VIEWS="$3"; fi

JSON_OUTPUT="$(python3 "$ROOT_DIR/scripts/sponsor/generate_weekly_content.py" --stars "$STARS" --forks "$FORKS" --views "$VIEWS" --json)"

echo "$JSON_OUTPUT" > "$ROOT_DIR/data/weekly-content/latest.json"

if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY'
import json
from pathlib import Path
p = Path('data/weekly-content/latest.json')
obj = json.loads(p.read_text(encoding='utf-8'))
print('✅ Weekly copy generated')
print('MD:', obj.get('md_path'))
print('JSON:', obj.get('json_path'))
print('Optimization:', obj.get('optimization', {}))
print('\n--- LinkedIn #1 ---\n')
print('IT:\n' + obj.get('linkedin_post_1_it',''))
print('\nEN:\n' + obj.get('linkedin_post_1_en',''))
print('\n--- LinkedIn #2 ---\n')
print('IT:\n' + obj.get('linkedin_post_2_it',''))
print('\nEN:\n' + obj.get('linkedin_post_2_en',''))
print('\n--- Ko-fi ---\n')
print('IT:\n' + obj.get('kofi_post_it',''))
print('\nEN:\n' + obj.get('kofi_post_en',''))
print('\n--- GitHub Weekly ---\n')
print('IT:\n' + obj.get('github_weekly_post_it',''))
print('\nEN:\n' + obj.get('github_weekly_post_en',''))
PY
fi
