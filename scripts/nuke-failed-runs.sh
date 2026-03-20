#!/bin/bash
# ============================================================
# VIO 83 — CANCELLA TUTTI I RUN FAILED/CANCELLED DA GITHUB
# Versione 3.0 — Cancella TUTTO: vecchi, nuovi, Attempt #2, rinominati
#
# Requisiti: gh auth login (GitHub CLI autenticato)
# Esegui: chmod +x scripts/nuke-failed-runs.sh && ./scripts/nuke-failed-runs.sh
# ============================================================
set -uo pipefail

REPO="vio83/vio83-ai-orchestra"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🗑️  VIO 83 — PULIZIA TOTALE GITHUB ACTIONS v3.0             ${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if ! gh auth status &>/dev/null; then
  echo -e "${RED}❌ GitHub CLI non autenticato! Esegui: gh auth login${NC}"
  exit 1
fi
echo -e "${GREEN}✅ GitHub CLI autenticato${NC}"
echo ""

DELETED=0
ERRORS=0

# ═══════════════════════════════════════════════
# FUNZIONE: Cancella run per status
# ═══════════════════════════════════════════════
delete_runs_by_status() {
  local STATUS="$1"
  local LABEL="$2"

  echo -e "${YELLOW}Cercando run con status: ${LABEL}...${NC}"

  # Prende fino a 100 run per pagina, massimo 5 pagine (500 run)
  for PAGE in 1 2 3 4 5; do
    IDS=$(gh api "repos/${REPO}/actions/runs?status=${STATUS}&per_page=100&page=${PAGE}" \
      --jq '.workflow_runs[].id' 2>/dev/null || echo "")

    if [ -z "$IDS" ]; then
      break
    fi

    for RUN_ID in $IDS; do
      RUN_INFO=$(gh api "repos/${REPO}/actions/runs/${RUN_ID}" \
        --jq '"[\(.name // "unknown")] — \(.head_sha[0:7]) — \(.created_at[0:10])"' 2>/dev/null || echo "ID: ${RUN_ID}")

      # Tentativo 1: DELETE diretto
      if gh api "repos/${REPO}/actions/runs/${RUN_ID}" -X DELETE 2>/dev/null; then
        DELETED=$((DELETED + 1))
        echo -e "  ${GREEN}✅ #${DELETED}: ${RUN_INFO}${NC}"
      else
        # Tentativo 2: Cancella logs prima, poi il run
        gh api "repos/${REPO}/actions/runs/${RUN_ID}/logs" -X DELETE 2>/dev/null || true
        sleep 0.5
        if gh api "repos/${REPO}/actions/runs/${RUN_ID}" -X DELETE 2>/dev/null; then
          DELETED=$((DELETED + 1))
          echo -e "  ${GREEN}✅ #${DELETED}: ${RUN_INFO} (retry OK)${NC}"
        else
          # Tentativo 3: Force cancel + delete
          gh api "repos/${REPO}/actions/runs/${RUN_ID}/cancel" -X POST 2>/dev/null || true
          sleep 1
          if gh api "repos/${REPO}/actions/runs/${RUN_ID}" -X DELETE 2>/dev/null; then
            DELETED=$((DELETED + 1))
            echo -e "  ${GREEN}✅ #${DELETED}: ${RUN_INFO} (force OK)${NC}"
          else
            # Tentativo 4: Force rerun poi cancel poi delete
            gh api "repos/${REPO}/actions/runs/${RUN_ID}/rerun-failed-jobs" -X POST 2>/dev/null || true
            sleep 2
            gh api "repos/${REPO}/actions/runs/${RUN_ID}/cancel" -X POST 2>/dev/null || true
            sleep 1
            if gh api "repos/${REPO}/actions/runs/${RUN_ID}" -X DELETE 2>/dev/null; then
              DELETED=$((DELETED + 1))
              echo -e "  ${GREEN}✅ #${DELETED}: ${RUN_INFO} (rerun+cancel OK)${NC}"
            else
              ERRORS=$((ERRORS + 1))
              echo -e "  ${RED}⚠️  Non cancellabile: ${RUN_INFO}${NC}"
            fi
          fi
        fi
      fi
      sleep 0.2
    done
  done
}

# ═══════════════════════════════════════════════
# FASE 1: Cancella per status
# ═══════════════════════════════════════════════
echo -e "${CYAN}═══ FASE 1: Cancellazione per status ═══${NC}"
echo ""

delete_runs_by_status "failure" "FAILED"
echo ""
delete_runs_by_status "cancelled" "CANCELLED"
echo ""
delete_runs_by_status "action_required" "ACTION_REQUIRED"
echo ""
delete_runs_by_status "stale" "STALE"
echo ""
delete_runs_by_status "timed_out" "TIMED_OUT"
echo ""
delete_runs_by_status "startup_failure" "STARTUP_FAILURE"
echo ""

# ═══════════════════════════════════════════════
# FASE 2: Cancella TUTTI i run di workflow obsoleti/rinominati
# (workflow che non esistono più nei file .yml)
# ═══════════════════════════════════════════════
echo -e "${CYAN}═══ FASE 2: Pulizia workflow obsoleti ═══${NC}"
echo ""

# Prende TUTTI i run e filtra quelli con conclusion != success e status != in_progress
echo -e "${YELLOW}Cercando run non-success da workflow rinominati...${NC}"

for PAGE in 1 2 3 4 5; do
  ALL_RUNS=$(gh api "repos/${REPO}/actions/runs?per_page=100&page=${PAGE}" \
    --jq '.workflow_runs[] | select(.conclusion != "success" and .conclusion != null and .status != "in_progress" and .status != "queued") | .id' 2>/dev/null || echo "")

  if [ -z "$ALL_RUNS" ]; then
    break
  fi

  for RUN_ID in $ALL_RUNS; do
    RUN_INFO=$(gh api "repos/${REPO}/actions/runs/${RUN_ID}" \
      --jq '"[\(.name // "unknown")] — \(.conclusion // "?") — \(.created_at[0:10])"' 2>/dev/null || echo "ID: ${RUN_ID}")

    if gh api "repos/${REPO}/actions/runs/${RUN_ID}" -X DELETE 2>/dev/null; then
      DELETED=$((DELETED + 1))
      echo -e "  ${GREEN}✅ #${DELETED}: ${RUN_INFO}${NC}"
    else
      gh api "repos/${REPO}/actions/runs/${RUN_ID}/logs" -X DELETE 2>/dev/null || true
      sleep 0.5
      if gh api "repos/${REPO}/actions/runs/${RUN_ID}" -X DELETE 2>/dev/null; then
        DELETED=$((DELETED + 1))
        echo -e "  ${GREEN}✅ #${DELETED}: ${RUN_INFO} (retry OK)${NC}"
      fi
    fi
    sleep 0.2
  done
done

# ═══════════════════════════════════════════════
# VERIFICA FINALE
# ═══════════════════════════════════════════════
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

REMAINING_FAIL=$(gh api "repos/${REPO}/actions/runs?status=failure&per_page=1" \
  --jq '.total_count' 2>/dev/null || echo "?")
REMAINING_CANCEL=$(gh api "repos/${REPO}/actions/runs?status=cancelled&per_page=1" \
  --jq '.total_count' 2>/dev/null || echo "?")

# Validate numeric values before arithmetic. Do not mask API failures as zero.
COUNTS_KNOWN=true
if ! [[ "$REMAINING_FAIL" =~ ^[0-9]+$ ]]; then
  COUNTS_KNOWN=false
fi
if ! [[ "$REMAINING_CANCEL" =~ ^[0-9]+$ ]]; then
  COUNTS_KNOWN=false
fi

echo -e "  Cancellati:        ${GREEN}${DELETED}${NC}"
echo -e "  Non cancellabili:  ${ERRORS}"
echo -e "  Rimasti (failed):  ${REMAINING_FAIL}"
echo -e "  Rimasti (cancel):  ${REMAINING_CANCEL}"
echo ""

if [ "$COUNTS_KNOWN" = false ]; then
  echo -e "${RED}❌ Impossibile calcolare il totale residuo: API GitHub non raggiungibile o auth scaduta.${NC}"
  echo -e "${YELLOW}Verifica: gh auth status && riprova.${NC}"
  exit 2
fi

TOTAL_REMAINING=$((REMAINING_FAIL + REMAINING_CANCEL))

if [ "$TOTAL_REMAINING" -eq 0 ]; then
  echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}║  🎉 ZERO RUN FAILED SU GITHUB — PULIZIA TOTALE!        ║${NC}"
  echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
else
  echo -e "${YELLOW}Rimangono run. Ri-esegui tra 1 minuto: ./scripts/nuke-failed-runs.sh${NC}"
fi
echo ""
echo -e "Verifica: ${CYAN}https://github.com/${REPO}/actions${NC}"
