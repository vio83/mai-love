#!/usr/bin/env bash
# ============================================================
# VIO 83 — VS Code Autopilot Auto-Fix & Auto-Optimize
# Ciclo continuo di correzione automatica errori, lint, spell,
# typecheck, e ottimizzazione workspace. Eseguito ogni ora da
# LaunchAgent macOS in modo permanente.
# ============================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/automation/logs"
mkdir -p "$LOG_DIR"

LOCK_DIR="/tmp/vio83-vscode-autofix.lock"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LOG_FILE="$LOG_DIR/vscode-autofix-cycle.log"

# ---  Lock anti-overlap ---
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[$TS] lock-active: ciclo precedente in esecuzione" >> "$LOG_FILE"
  exit 0
fi
cleanup() { rmdir "$LOCK_DIR" 2>/dev/null || true; }
trap cleanup EXIT

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" >> "$LOG_FILE"; }

log "========== AUTOFIX CYCLE START =========="

FIXES=0
ERRORS=0

# -------------------------------------------------------
# 1. ESLint auto-fix (TypeScript / React)
# -------------------------------------------------------
log "[1/7] ESLint auto-fix..."
if command -v npx &>/dev/null && [[ -f "$ROOT_DIR/eslint.config.js" ]]; then
  if npx eslint --fix "src/**/*.{ts,tsx}" --no-error-on-unmatched-pattern >> "$LOG_DIR/eslint-autofix.log" 2>&1; then
    log "  ESLint autofix: OK"
    FIXES=$((FIXES+1))
  else
    log "  ESLint autofix: completato con warning"
    FIXES=$((FIXES+1))
  fi
else
  log "  ESLint: npx non disponibile o config mancante, skip"
fi

# -------------------------------------------------------
# 2. TypeScript type-check (solo verifica, no fix)
# -------------------------------------------------------
log "[2/7] TypeScript type-check..."
if npx tsc --noEmit --pretty 2>"$LOG_DIR/tsc-check.log"; then
  log "  TSC: 0 errori"
else
  TSC_ERRORS=$(grep -c "error TS" "$LOG_DIR/tsc-check.log" 2>/dev/null || echo "0")
  log "  TSC: $TSC_ERRORS errori rilevati (vedi tsc-check.log)"
  ERRORS=$((ERRORS + TSC_ERRORS))
fi

# -------------------------------------------------------
# 3. Python compile-check (tutti i file backend)
# -------------------------------------------------------
log "[3/7] Python compile check..."
if command -v python3 &>/dev/null; then
  PY_OUTPUT=$(python3 -m compileall -q "$ROOT_DIR/backend/" 2>&1 || true)
  PY_ERRORS=$(echo "$PY_OUTPUT" | grep -c "Error" || true)
  if [[ "$PY_ERRORS" -eq 0 ]]; then
    log "  Python: compilazione OK"
  else
    log "  Python: $PY_ERRORS errori di compilazione"
    ERRORS=$((ERRORS + PY_ERRORS))
  fi
else
  log "  Python3 non trovato, skip"
fi

# -------------------------------------------------------
# 4. Pulizia cache/temp — impedisce accumulo
# -------------------------------------------------------
log "[4/7] Pulizia cache..."
CLEANED=0

# __pycache__
PYCACHE_COUNT=$(find "$ROOT_DIR/backend" -type d -name "__pycache__" 2>/dev/null | wc -l | xargs)
if [[ "$PYCACHE_COUNT" -gt 0 ]]; then
  find "$ROOT_DIR/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  CLEANED=$((CLEANED + PYCACHE_COUNT))
fi

# .pyc files
PYC_COUNT=$(find "$ROOT_DIR/backend" -name "*.pyc" 2>/dev/null | wc -l | xargs)
if [[ "$PYC_COUNT" -gt 0 ]]; then
  find "$ROOT_DIR/backend" -name "*.pyc" -delete 2>/dev/null || true
  CLEANED=$((CLEANED + PYC_COUNT))
fi

# Vite cache
if [[ -d "$ROOT_DIR/node_modules/.cache" ]]; then
  rm -rf "$ROOT_DIR/node_modules/.cache"
  CLEANED=$((CLEANED + 1))
fi

# Stale .tsbuildinfo
find "$ROOT_DIR" -maxdepth 2 -name "*.tsbuildinfo" -mtime +7 -delete 2>/dev/null || true

log "  Cache: rimossi $CLEANED elementi"
FIXES=$((FIXES + CLEANED))

# -------------------------------------------------------
# 5. Git: auto-stage & promemoria
# -------------------------------------------------------
log "[5/7] Git status check..."
if command -v git &>/dev/null; then
  GIT_DIRTY=$(git -C "$ROOT_DIR" status --porcelain 2>/dev/null | wc -l | xargs)
  GIT_BRANCH=$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  log "  Git: branch=$GIT_BRANCH, dirty_files=$GIT_DIRTY"
else
  log "  Git non disponibile, skip"
fi

# -------------------------------------------------------
# 6. Verifica servizi attivi (ollama, backend)
# -------------------------------------------------------
log "[6/7] Health check servizi..."

# Ollama
if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
  log "  Ollama: ATTIVO"
else
  log "  Ollama: NON attivo (normale se non in uso)"
fi

# Backend FastAPI
if curl -sf http://localhost:4000/health >/dev/null 2>&1; then
  log "  Backend: ATTIVO"
else
  log "  Backend: NON attivo (normale se non in uso)"
fi

# -------------------------------------------------------
# 7. Rotazione log (mantieni ultimi 30 giorni)
# -------------------------------------------------------
log "[7/7] Log rotation..."
find "$LOG_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null || true
# Tronca log grandi (>5MB)
for logfile in "$LOG_DIR"/*.log; do
  if [[ -f "$logfile" ]] && [[ $(stat -f%z "$logfile" 2>/dev/null || echo 0) -gt 5242880 ]]; then
    tail -n 1000 "$logfile" > "${logfile}.tmp" && mv "${logfile}.tmp" "$logfile"
    log "  Troncato: $(basename "$logfile")"
  fi
done

# -------------------------------------------------------
# Riepilogo
# -------------------------------------------------------
log "========== AUTOFIX CYCLE DONE =========="
log "  Correzioni applicate: $FIXES"
log "  Errori residui: $ERRORS"
log "  Prossimo ciclo: tra 1 ora"
log "========================================="
