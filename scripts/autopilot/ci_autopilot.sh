#!/usr/bin/env bash
# =============================================================================
# CI Autopilot — Daemon persistente 24/7
# Monitora GitHub Actions (vio83/mai-love) e Apple Mail per fallimenti CI.
# Ri-esegue automaticamente i job falliti e invia notifiche macOS.
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null \
             || echo "/Users/padronavio/Projects/vio83-ai-orchestra")"
LOG_DIR="${LOG_DIR:-$REPO_ROOT/automation/logs}"
STATUS_FILE="$REPO_ROOT/data/autonomous_runtime/ci_autopilot_status.json"

mkdir -p "$LOG_DIR" "$(dirname "$STATUS_FILE")"

REPO="vio83/mai-love"
POLL_INTERVAL=60          # secondi tra i controlli GitHub
MAIL_CHECK_INTERVAL=120   # secondi tra i controlli Apple Mail

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log() {
  local log_file="$LOG_DIR/ci-autopilot-$(date +%Y%m%d).log"
  echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $*" | tee -a "$log_file"
}

# ---------------------------------------------------------------------------
# Notifiche macOS
# ---------------------------------------------------------------------------
notify() {
  local title="$1" body="$2"
  osascript -e "display notification \"${body}\" with title \"${title}\" sound name \"Basso\"" 2>/dev/null || true
}

alarm() {
  # Allarme sonoro più insistente per errori critici
  local title="$1" body="$2"
  for i in 1 2 3; do
    osascript -e "display notification \"${body}\" with title \"🚨 ${title}\" sound name \"Basso\"" 2>/dev/null || true
    sleep 2
  done
}

# ---------------------------------------------------------------------------
# Stato JSON (leggibile dal backend API)
# ---------------------------------------------------------------------------
write_status() {
  local state="$1" last_action="$2" fixed_count="${3:-0}"
  cat > "$STATUS_FILE" << JSONEOF
{
  "state": "${state}",
  "repo": "${REPO}",
  "last_check": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "last_action": "${last_action}",
  "total_fixed_this_session": ${fixed_count},
  "poll_interval_seconds": ${POLL_INTERVAL},
  "pid": $$
}
JSONEOF
}

# ---------------------------------------------------------------------------
# Verifica prerequisiti
# ---------------------------------------------------------------------------
check_deps() {
  local missing=()
  for cmd in gh jq osascript; do
    command -v "$cmd" &>/dev/null || missing+=("$cmd")
  done
  if (( ${#missing[@]} > 0 )); then
    log "ERRORE: comandi mancanti: ${missing[*]}"
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# Controllo e fix GitHub Actions
# ---------------------------------------------------------------------------
TOTAL_FIXED=0

check_and_fix_github() {
  local failed_runs
  failed_runs=$(GH_PAGER=cat gh run list \
    -R "$REPO" \
    --status failure \
    --limit 10 \
    --json databaseId,workflowName,createdAt,headBranch \
    2>/dev/null || echo "[]")

  if [ "$failed_runs" = "[]" ] || [ -z "$failed_runs" ]; then
    write_status "ok" "nessun fallimento rilevato" "$TOTAL_FIXED"
    return 0
  fi

  local count
  count=$(echo "$failed_runs" | jq 'length')
  log "⚠️  $count run fallite trovate — avvio auto-fix..."

  while IFS=$'\t' read -r rid wname branch; do
    [ -z "$rid" ] && continue
    log "AUTO-FIX: gh run rerun $rid ($wname, branch: $branch)"

    if GH_PAGER=cat gh run rerun "$rid" -R "$REPO" --failed 2>/dev/null; then
      TOTAL_FIXED=$(( TOTAL_FIXED + 1 ))
      log "✅ Rerun avviato: $wname #$rid"
      notify "CI Autopilot ✅" "Auto-fixed: $wname (branch: $branch)"
      write_status "fixed" "rerun $wname #$rid" "$TOTAL_FIXED"
    else
      log "❌ Impossibile riavviare: $wname #$rid"
      alarm "CI Autopilot FAIL" "Fix manuale necessario: $wname (branch: $branch)"
      write_status "error" "rerun fallito: $wname #$rid" "$TOTAL_FIXED"
    fi
  done < <(echo "$failed_runs" | jq -r '.[] | [.databaseId, .workflowName, .headBranch] | @tsv')
}

# ---------------------------------------------------------------------------
# Monitoraggio Apple Mail
# ---------------------------------------------------------------------------
check_apple_mail() {
  local mail_subjects
  mail_subjects=$(osascript 2>/dev/null << 'APPLESCRIPT'
tell application "Mail"
  set result_lines to {}
  try
    set unreadMsgs to (messages of inbox whose read status is false)
    repeat with aMsg in unreadMsgs
      set s to subject of aMsg
      if s contains "workflow run failed" or s contains "Run failed" or s contains "Check failure" then
        set end of result_lines to s
      end if
    end repeat
  end try
  return result_lines as string
end tell
APPLESCRIPT
) || true

  if [ -n "$mail_subjects" ] && [ "$mail_subjects" != "missing value" ]; then
    log "📧 Mail trigger ricevuto: $mail_subjects"
    log "→ Avvio check immediato GitHub..."
    check_and_fix_github
  fi
}

# ---------------------------------------------------------------------------
# Pulizia log vecchi (conserva 14 giorni)
# ---------------------------------------------------------------------------
cleanup_old_logs() {
  find "$LOG_DIR" -name "ci-autopilot-*.log" -mtime +14 -delete 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Handler segnali (SIGTERM/SIGINT)
# ---------------------------------------------------------------------------
on_exit() {
  log "CI Autopilot arrestato (PID $$)"
  write_status "stopped" "daemon arrestato" "$TOTAL_FIXED"
  notify "CI Autopilot" "Daemon arrestato — monitoraggio CI sospeso"
}
trap on_exit EXIT TERM INT

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
check_deps

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "CI Autopilot avviato — Repo: $REPO | PID: $$"
log "Poll GitHub ogni ${POLL_INTERVAL}s | Mail ogni ${MAIL_CHECK_INTERVAL}s"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
notify "CI Autopilot" "Monitoraggio $REPO attivo 24/7"
write_status "running" "avvio daemon" "0"

LAST_MAIL_CHECK=0
LAST_LOG_CLEANUP=0
ITERATIONS=0

while true; do
  ITERATIONS=$(( ITERATIONS + 1 ))
  NOW=$(date +%s)

  # --- Check GitHub ---
  check_and_fix_github || log "WARN: check_and_fix_github ha restituito errore"

  # --- Check Apple Mail ogni MAIL_CHECK_INTERVAL secondi ---
  if (( NOW - LAST_MAIL_CHECK >= MAIL_CHECK_INTERVAL )); then
    check_apple_mail || true
    LAST_MAIL_CHECK=$NOW
  fi

  # --- Pulizia log ogni 24h (ogni 1440 iterazioni a 60s) ---
  if (( NOW - LAST_LOG_CLEANUP >= 86400 )); then
    cleanup_old_logs
    LAST_LOG_CLEANUP=$NOW
    log "🧹 Log vecchi rimossi"
  fi

  sleep "$POLL_INTERVAL"
done
