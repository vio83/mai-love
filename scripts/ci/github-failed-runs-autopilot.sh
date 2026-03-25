#!/bin/bash
# ============================================================
# VIO 83 — GitHub Failed Runs Autopilot
# Scansiona i run failed e rilancia automaticamente i failed jobs.
# Supporta repo corrente o tutti i repository dell'owner autenticato.
# ============================================================
set -uo pipefail

OWNER=""
ALL_REPOS=true
REPO=""
LOOKBACK_HOURS=24
MAX_RUNS_PER_REPO=3
INTERVAL_SEC=60
WATCH=false
DRY_RUN=false

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/automation/logs"
LOG_FILE="$LOG_DIR/github-failed-runs-autopilot.log"

mkdir -p "$LOG_DIR"

now_iso() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

log() {
  local msg="$1"
  echo "[$(now_iso)] $msg" | tee -a "$LOG_FILE"
}

usage() {
  cat <<EOF
Uso:
  $0 [opzioni]

Opzioni:
  --owner <github-owner>       Owner da scansionare (default: utente autenticato)
  --repo <owner/repo>          Solo un repository specifico
  --lookback-hours <n>         Considera solo failure recenti (default: 24)
  --max-runs-per-repo <n>      Max run failed da processare per repo (default: 3)
  --interval-sec <n>           Intervallo watch in secondi (default: 60)
  --watch                      Modalita continua
  --dry-run                    Simulazione senza rerun
  --help                       Mostra aiuto

Esempi:
  $0 --repo vio83/vio83-ai-orchestra
  $0 --owner vio83 --watch --interval-sec 60
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner)
      OWNER="$2"; shift 2 ;;
    --repo)
      REPO="$2"; ALL_REPOS=false; shift 2 ;;
    --lookback-hours)
      LOOKBACK_HOURS="$2"; shift 2 ;;
    --max-runs-per-repo)
      MAX_RUNS_PER_REPO="$2"; shift 2 ;;
    --interval-sec)
      INTERVAL_SEC="$2"; shift 2 ;;
    --watch)
      WATCH=true; shift ;;
    --dry-run)
      DRY_RUN=true; shift ;;
    --help|-h)
      usage; exit 0 ;;
    *)
      echo "Argomento sconosciuto: $1"; usage; exit 1 ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "gh non trovato. Installa GitHub CLI." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "gh non autenticato. Esegui: gh auth login" >&2
  exit 1
fi

if ! [[ "$LOOKBACK_HOURS" =~ ^[0-9]+$ ]]; then
  echo "lookback-hours non valido: $LOOKBACK_HOURS" >&2
  exit 1
fi

if ! [[ "$MAX_RUNS_PER_REPO" =~ ^[0-9]+$ ]]; then
  echo "max-runs-per-repo non valido: $MAX_RUNS_PER_REPO" >&2
  exit 1
fi

if ! [[ "$INTERVAL_SEC" =~ ^[0-9]+$ ]]; then
  echo "interval-sec non valido: $INTERVAL_SEC" >&2
  exit 1
fi

if [[ -z "$OWNER" ]]; then
  OWNER="$(gh api user --jq .login 2>/dev/null || true)"
fi

if [[ -z "$OWNER" ]]; then
  echo "Impossibile determinare owner GitHub autenticato." >&2
  exit 1
fi

iso_age_hours() {
  local iso="$1"
  python3 - "$iso" <<'PY'
import sys
from datetime import datetime, timezone
iso = sys.argv[1]
try:
    dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    print((now - dt).total_seconds() / 3600)
except Exception:
    print(999999)
PY
}

list_repos() {
  if [[ "$ALL_REPOS" == false && -n "$REPO" ]]; then
    echo "$REPO"
    return 0
  fi
  gh repo list "$OWNER" --limit 1000 --json nameWithOwner,isArchived,isFork --jq '.[] | select(.isArchived==false and .isFork==false) | .nameWithOwner' 2>/dev/null
}

process_repo() {
  local repo="$1"
  local processed=0
  local rerun_count=0

  local lines
  lines="$(gh run list -R "$repo" --status failure -L "$MAX_RUNS_PER_REPO" --json databaseId,workflowName,headBranch,event,createdAt,url,displayTitle --jq '.[] | "\(.databaseId)|\(.workflowName)|\(.headBranch)|\(.event)|\(.createdAt)|\(.url)|\(.displayTitle)"' 2>/dev/null || true)"

  if [[ -z "$lines" ]]; then
    log "[$repo] nessun failed recente"
    return 0
  fi

  while IFS='|' read -r run_id wf_name branch event created_at run_url run_title; do
    [[ -z "$run_id" ]] && continue

    local age_h
    age_h="$(iso_age_hours "$created_at")"
    local too_old
    too_old="$(python3 - "$age_h" "$LOOKBACK_HOURS" <<'PY'
import sys
age=float(sys.argv[1]); lim=float(sys.argv[2])
print('1' if age > lim else '0')
PY
)"

    if [[ "$too_old" == "1" ]]; then
      log "[$repo] skip run $run_id (age ${age_h}h > ${LOOKBACK_HOURS}h)"
      continue
    fi

    if [[ "$branch" != "main" && "$branch" != "master" ]]; then
      log "[$repo] skip run $run_id branch=$branch"
      continue
    fi

    processed=$((processed + 1))

    if [[ "$DRY_RUN" == true ]]; then
      log "[$repo] DRY-RUN rerun-failed run_id=$run_id wf=$wf_name title=$run_title url=$run_url"
      continue
    fi

    rerun_err=""
    if gh run rerun-failed -R "$repo" "$run_id" >/dev/null 2>"$LOG_DIR/.gh-rerun.err"; then
      rerun_count=$((rerun_count + 1))
      log "[$repo] RERUN_OK run_id=$run_id wf=$wf_name url=$run_url"
    else
      rerun_err="$(cat "$LOG_DIR/.gh-rerun.err" 2>/dev/null || true)"
      # Fallback API diretto: /actions/runs/{run_id}/rerun-failed-jobs
      if gh api -X POST "repos/$repo/actions/runs/$run_id/rerun-failed-jobs" >/dev/null 2>>"$LOG_DIR/.gh-rerun.err"; then
        rerun_count=$((rerun_count + 1))
        log "[$repo] RERUN_OK_FALLBACK run_id=$run_id wf=$wf_name url=$run_url"
      else
        rerun_err="$(cat "$LOG_DIR/.gh-rerun.err" 2>/dev/null || true)"
        rerun_err="${rerun_err//$'\n'/ | }"
        log "[$repo] RERUN_FAIL run_id=$run_id wf=$wf_name url=$run_url err=$rerun_err"
      fi
    fi
  done <<< "$lines"

  log "[$repo] processed=$processed rerun_ok=$rerun_count"
}

run_once() {
  local repos
  repos="$(list_repos)"
  if [[ -z "$repos" ]]; then
    log "Nessun repository trovato per owner=$OWNER"
    return 0
  fi

  local repo_count=0
  while IFS= read -r r; do
    [[ -z "$r" ]] && continue
    repo_count=$((repo_count + 1))
    process_repo "$r"
  done <<< "$repos"

  log "Ciclo completato: owner=$OWNER repos=$repo_count"
}

log "Autopilot avviato owner=$OWNER all_repos=$ALL_REPOS lookback_h=$LOOKBACK_HOURS max_runs_per_repo=$MAX_RUNS_PER_REPO watch=$WATCH dry_run=$DRY_RUN"

if [[ "$WATCH" == true ]]; then
  while true; do
    run_once
    sleep "$INTERVAL_SEC"
  done
else
  run_once
fi
