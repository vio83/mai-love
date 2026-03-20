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
CIRCUIT_BREAK_COUNT=0

NOW_TS=$(date +%s)

# ── CIRCUIT BREAKER ──────────────────────────────────────────
# Max 2 rerun per combinazione workflow+sha nelle ultime 2 ore.
# Previene loop infiniti di rerun sullo stesso commit.
CB_FILE="${LOG_DIR}/.circuit-breaker-state"
touch "$CB_FILE"
# Pulisci entry più vecchie di 2 ore
if [ -f "$CB_FILE" ]; then
  CB_CUTOFF=$((NOW_TS - 7200))
  awk -F'|' -v cutoff="$CB_CUTOFF" '$1 >= cutoff' "$CB_FILE" > "${CB_FILE}.tmp" 2>/dev/null || true
  mv "${CB_FILE}.tmp" "$CB_FILE" 2>/dev/null || true
fi

circuit_breaker_check() {
  local wf_name="$1"
  local run_id="$2"
  local key="${wf_name}|${run_id}"
  local count
  count=$(grep -c "|${key}$" "$CB_FILE" 2>/dev/null || echo "0")
  if [ "$count" -ge 2 ]; then
    return 1  # BLOCCATO
  fi
  echo "${NOW_TS}|${key}" >> "$CB_FILE"
  return 0    # OK
}

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

    # Circuit breaker — max 2 rerun per stesso workflow+run
    if ! circuit_breaker_check "$WF_NAME" "$RUN_ID"; then
      echo "    🛑 Circuit break: $WF_NAME #$RUN_ID (già 2+ tentativi)"
      CIRCUIT_BREAK_COUNT=$((CIRCUIT_BREAK_COUNT + 1))
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
echo "  Rerun: $RERUN_COUNT | Skip: $SKIP_COUNT | Errori: $ERROR_COUNT | Circuit Break: $CIRCUIT_BREAK_COUNT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
