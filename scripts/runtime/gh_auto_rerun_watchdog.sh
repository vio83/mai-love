#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# gh_auto_rerun_watchdog.sh
# Auto-rerun CI failed jobs across all vio83 repos.
# Designed to be run hourly by a macOS LaunchAgent.
# Skips runs older than 30 days (GitHub rerun limit).
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# Allow wrapper/environment to provide portable paths.
LOG_DIR="${LOG_DIR:-${REPO_ROOT:-$HOME/Projects/vio83-ai-orchestra}/automation/logs}"
LOG_FILE="$LOG_DIR/gh-auto-rerun-$(date +%Y%m%d).log"
CUTOFF_HOURS=720   # 30 days in hours

mkdir -p "$LOG_DIR"
exec >> "$LOG_FILE" 2>&1

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "▶ gh_auto_rerun_watchdog — $(date '+%Y-%m-%d %H:%M:%S')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Repos da monitorare
REPOS=(
  "vio83/vio83-ai-orchestra"
)

RERUN_COUNT=0
SKIP_COUNT=0
ERROR_COUNT=0

NOW_TS=$(date +%s)

if ! command -v jq >/dev/null 2>&1; then
  echo "    ❌ jq non trovato nel PATH: impossibile processare i run"
  exit 1
fi

for REPO in "${REPOS[@]}"; do
  echo "  [REPO] $REPO"

  # Recupera i run failed recenti
  RUNS=$(GH_PAGER=cat PAGER=cat gh run list \
    -R "$REPO" \
    --status failure \
    --limit 20 \
    --json databaseId,createdAt,workflowName,conclusion 2>/dev/null || true)

  if [ -z "$RUNS" ] || [ "$RUNS" = "[]" ]; then
    echo "    ✅ Nessun run failed"
    continue
  fi

  # Processa ogni run senza file temporanei e senza subshell state loss.
  while IFS=$'\t' read -r RUN_ID CREATED_AT WF_NAME; do
    [ -z "$RUN_ID" ] && continue

    # Calcola età del run
    if [[ "$OSTYPE" == "darwin"* ]]; then
      RUN_TS=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$CREATED_AT" +%s 2>/dev/null || echo "0")
    else
      RUN_TS=$(date -d "$CREATED_AT" +%s 2>/dev/null || echo "0")
    fi

    AGE_HOURS=$(( (NOW_TS - RUN_TS) / 3600 ))

    if [ "$AGE_HOURS" -ge "$CUTOFF_HOURS" ]; then
      echo "    ⏭  Skip (${AGE_HOURS}h fa): $WF_NAME #$RUN_ID"
      SKIP_COUNT=$((SKIP_COUNT + 1))
      continue
    fi

    # Tenta rerun solo dei job falliti
    if RESULT=$(GH_PAGER=cat gh run rerun "$RUN_ID" -R "$REPO" --failed 2>&1); then
      echo "    🔄 Rerun OK: $WF_NAME #$RUN_ID (${AGE_HOURS}h fa)"
      RERUN_COUNT=$((RERUN_COUNT + 1))
    else
      echo "    ❌ Rerun FAIL: $WF_NAME #$RUN_ID — $RESULT"
      ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
  done < <(echo "$RUNS" | jq -r '.[] | [.databaseId, .createdAt, .workflowName] | @tsv')
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Rerun: $RERUN_COUNT | Skip: $SKIP_COUNT | Errori: $ERROR_COUNT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
