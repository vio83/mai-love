#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OPEN_DRAFTS=false
FORCE=false
FORCE_TARGET=""

for arg in "$@"; do
  case "$arg" in
    --open-drafts)
      OPEN_DRAFTS=true
      ;;
    --force)
      FORCE=true
      ;;
    --force-target=*)
      FORCE_TARGET="${arg#*=}"
      ;;
  esac
done

mkdir -p "$ROOT_DIR/data/weekly-content" "$ROOT_DIR/automation/logs"

TODAY="$(date +%F)"
WEEKDAY="$(date +%u)" # 1=Mon ... 7=Sun
STATE_FILE="$ROOT_DIR/data/weekly-content/autopilot-state.json"
LATEST_JSON="$ROOT_DIR/data/weekly-content/latest.json"

STARS=0
FORKS=0
VIEWS=0

if command -v gh >/dev/null 2>&1; then
  STARS="$(gh api repos/vio83/vio83-ai-orchestra --jq '.stargazers_count' 2>/dev/null || echo 0)"
  FORKS="$(gh api repos/vio83/vio83-ai-orchestra --jq '.forks_count' 2>/dev/null || echo 0)"
  VIEWS="$(gh api repos/vio83/vio83-ai-orchestra/traffic/views --jq '.count' 2>/dev/null || echo 0)"
fi

JSON_OUTPUT="$(python3 "$ROOT_DIR/scripts/sponsor/generate_weekly_content.py" --stars "$STARS" --forks "$FORKS" --views "$VIEWS" --json)"
echo "$JSON_OUTPUT" > "$LATEST_JSON"

TARGET_KEY=""
TARGET_LABEL=""

resolve_label() {
  case "$1" in
    linkedin_post_1) echo "LinkedIn Post #1" ;;
    linkedin_post_2) echo "LinkedIn Post #2" ;;
    kofi_post) echo "Ko-fi Weekly Post" ;;
    github_weekly_post) echo "GitHub Weekly Post" ;;
    *) echo "" ;;
  esac
}

if [[ -n "$FORCE_TARGET" ]]; then
  TARGET_KEY="$FORCE_TARGET"
  TARGET_LABEL="$(resolve_label "$TARGET_KEY")"
  if [[ -z "$TARGET_LABEL" ]]; then
    echo "❌ force-target non valido: $FORCE_TARGET"
    echo "Valori ammessi: linkedin_post_1, linkedin_post_2, kofi_post, github_weekly_post"
    exit 1
  fi
else
  case "$WEEKDAY" in
    1)
      TARGET_KEY="linkedin_post_1"
      TARGET_LABEL="LinkedIn Post #1"
      ;;
    3)
      TARGET_KEY="kofi_post"
      TARGET_LABEL="Ko-fi Weekly Post"
      ;;
    4)
      TARGET_KEY="linkedin_post_2"
      TARGET_LABEL="LinkedIn Post #2"
      ;;
    5)
      TARGET_KEY="github_weekly_post"
      TARGET_LABEL="GitHub Weekly Post"
      ;;
    *)
      echo "ℹ️ Oggi ($TODAY) non è un giorno di pubblicazione calendario."
      echo "✅ Bundle aggiornato in: $LATEST_JSON"
      exit 0
      ;;
  esac
fi

RESULT_JSON="$(python3 - "$TARGET_KEY" "$TARGET_LABEL" "$TODAY" "$STATE_FILE" "$FORCE" <<'PY'
import json
import pathlib
import sys

target_key, target_label, today, state_file_raw, force_raw = sys.argv[1:6]
force = force_raw.lower() == "true"

latest_path = pathlib.Path("data/weekly-content/latest.json")
state_path = pathlib.Path(state_file_raw)

bundle = json.loads(latest_path.read_text(encoding="utf-8"))

if state_path.exists():
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        state = {"done": {}}
else:
    state = {"done": {}}

state.setdefault("done", {})
done_today = state["done"].setdefault(today, [])

if target_key in done_today and not force:
    print(json.dumps({
        "status": "already_done",
        "target": target_key,
        "label": target_label,
        "message": "Contenuto già preparato oggi. Usa --force per rigenerare.",
    }, ensure_ascii=False))
    raise SystemExit(0)

it_text = bundle.get(f"{target_key}_it", bundle.get(target_key, ""))
en_text = bundle.get(f"{target_key}_en", "")

publish_links = bundle.get("publish_links", {})
open_links = []
if target_key == "linkedin_post_1":
    open_links.extend([
        publish_links.get("linkedin_post_1_it", ""),
        publish_links.get("linkedin_post_1_en", ""),
    ])
elif target_key == "linkedin_post_2":
    open_links.extend([
        publish_links.get("linkedin_post_2_it", ""),
        publish_links.get("linkedin_post_2_en", ""),
    ])
elif target_key == "kofi_post":
    open_links.append(publish_links.get("kofi", ""))
elif target_key == "github_weekly_post":
    open_links.append(publish_links.get("github", ""))

open_links = [u for u in open_links if u]

payload = {
    "date": today,
    "target": target_key,
    "target_label": target_label,
    "it": it_text,
    "en": en_text,
    "approval_checklist": [
        "Verifica tono umano e trasparente",
        "Verifica link sponsor e support hub",
        "Verifica coerenza metriche e data",
        "Approvazione manuale finale prima della pubblicazione",
    ],
    "open_links": open_links,
}

out_dir = pathlib.Path("data/weekly-content")
out_dir.mkdir(parents=True, exist_ok=True)
json_path = out_dir / f"daily-{today}-{target_key}.json"
md_path = out_dir / f"daily-{today}-{target_key}.md"

json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

md = [
    f"# Daily Draft — {target_label} ({today})",
    "",
    "## IT",
    it_text,
    "",
    "## EN",
    en_text,
    "",
    "## Approval Checklist",
    "\n".join([f"- {x}" for x in payload["approval_checklist"]]),
    "",
    "## Links",
    "\n".join([f"- {x}" for x in open_links]) if open_links else "- (n/a)",
    "",
]
md_path.write_text("\n".join(md), encoding="utf-8")

if target_key not in done_today:
    done_today.append(target_key)
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({
    "status": "ready",
    "target": target_key,
    "label": target_label,
    "daily_json": str(json_path),
    "daily_md": str(md_path),
    "open_links": open_links,
}, ensure_ascii=False))
PY
)"

echo "$RESULT_JSON" > "$ROOT_DIR/data/weekly-content/daily-latest.json"

STATUS="$(python3 - <<'PY' "$RESULT_JSON"
import json, sys
obj = json.loads(sys.argv[1])
print(obj.get('status', 'unknown'))
PY
)"

if [[ "$STATUS" == "already_done" ]]; then
  python3 - <<'PY' "$RESULT_JSON"
import json, sys
obj = json.loads(sys.argv[1])
print('ℹ️', obj.get('message',''))
PY
  exit 0
fi

if [[ "$OPEN_DRAFTS" == "true" ]]; then
  python3 - <<'PY' "$RESULT_JSON"
import json, sys
obj = json.loads(sys.argv[1])
for url in obj.get('open_links', []):
    print(url)
PY
fi | while IFS= read -r url; do
  if [[ -n "$url" ]] && command -v open >/dev/null 2>&1; then
    open "$url"
  fi
done

python3 - <<'PY' "$RESULT_JSON"
import json, sys
obj = json.loads(sys.argv[1])
print('✅ Daily autopilot ready')
print('Target:', obj.get('label'))
print('Draft JSON:', obj.get('daily_json'))
print('Draft MD:', obj.get('daily_md'))
print('Links:', len(obj.get('open_links', [])))
PY
