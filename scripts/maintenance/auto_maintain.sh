#!/usr/bin/env bash
# ============================================================
# VIO 83 AI ORCHESTRA — AUTO-MAINTAIN HEALTH CHECK 100x
# Protocollo di Aderenza Totale — Esecuzione locale permanente
#
# USO:
#   ./scripts/maintenance/auto_maintain.sh           # check completo
#   ./scripts/maintenance/auto_maintain.sh --fix     # fix automatico dove possibile
#   ./scripts/maintenance/auto_maintain.sh --watch   # loop continuo ogni 30 min
#
# INSTALLAZIONE AUTOSTART (launchd):
#   bash scripts/maintenance/auto_maintain.sh --install-autostart
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/data/logs/auto_maintain.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'

FIX_MODE=false
WATCH_MODE=false
INSTALL_MODE=false
PASS=0; FAIL=0; WARN=0

for arg in "$@"; do
  case $arg in
    --fix) FIX_MODE=true ;;
    --watch) WATCH_MODE=true ;;
    --install-autostart) INSTALL_MODE=true ;;
  esac
done

log() { echo -e "$*" | tee -a "$LOG_FILE" 2>/dev/null || echo -e "$*"; }
pass() { log "${GREEN}  ✔ $1${NC}"; ((PASS++)) || true; }
fail() { log "${RED}  ✖ $1${NC}"; ((FAIL++)) || true; }
warn() { log "${YELLOW}  ⚠ $1${NC}"; ((WARN++)) || true; }
info() { log "${BLUE}  → $1${NC}"; }

# ─────────────────────────────────────────────
install_autostart() {
  PLIST_PATH="$HOME/Library/LaunchAgents/com.vio83.auto-maintain.plist"
  cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.vio83.auto-maintain</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$PROJECT_ROOT/scripts/maintenance/auto_maintain.sh</string>
    <string>--fix</string>
  </array>
  <key>WorkingDirectory</key><string>$PROJECT_ROOT</string>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>14</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>20</integer><key>Minute</key><integer>0</integer></dict>
  </array>
  <key>StandardOutPath</key><string>$PROJECT_ROOT/data/logs/auto_maintain.log</string>
  <key>StandardErrorPath</key><string>$PROJECT_ROOT/data/logs/auto_maintain_err.log</string>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
PLIST
  launchctl unload "$PLIST_PATH" 2>/dev/null || true
  launchctl load "$PLIST_PATH"
  echo -e "${GREEN}✅ Auto-maintain installato: esecuzione 3x/giorno (08:00, 14:00, 20:00)${NC}"
  echo "   Plist: $PLIST_PATH"
  echo "   Log: $PROJECT_ROOT/data/logs/auto_maintain.log"
}

# ─────────────────────────────────────────────
run_check() {
  mkdir -p "$PROJECT_ROOT/data/logs"
  cd "$PROJECT_ROOT"

  log ""
  log "${BOLD}══════════════════════════════════════════════════════════${NC}"
  log "${BOLD}🎵 VIO 83 — AUTO-MAINTAIN 100x | $DATE${NC}"
  log "${BOLD}══════════════════════════════════════════════════════════${NC}"

  # ── 1. TypeScript zero-error check ──────────
  log "\n${BLUE}[1/7] TypeScript Zero-Error Gate${NC}"
  if command -v npx &>/dev/null; then
    if npx tsc --noEmit 2>&1 | tee -a "$LOG_FILE" | grep -q "error TS"; then
      fail "TypeScript: errori rilevati"
      if $FIX_MODE; then
        info "FIX: Esegui 'npx tsc --noEmit' per dettagli"
      fi
    else
      pass "TypeScript: zero errori"
    fi
  else
    warn "npx non trovato — skip TypeScript check"
  fi

  # ── 2. Python syntax check ───────────────────
  log "\n${BLUE}[2/7] Python Backend Syntax Gate${NC}"
  PYTHON_FILES=(
    backend/api/server.py
    backend/config/providers.py
    backend/database/db.py
    backend/orchestrator/direct_router.py
  )
  PY_ERRORS=0
  for f in "${PYTHON_FILES[@]}"; do
    if [ -f "$f" ]; then
      if ! python3 -m py_compile "$f" 2>>"$LOG_FILE"; then
        fail "Python syntax error: $f"
        ((PY_ERRORS++)) || true
      fi
    fi
  done
  [ $PY_ERRORS -eq 0 ] && pass "Python: tutti i file core compilano correttamente"

  # ── 3. Flake8 backend ───────────────────────
  log "\n${BLUE}[3/7] Python Linting (E/F codes)${NC}"
  # Cerca flake8: PATH di sistema, poi venv locale
  FLAKE8_BIN=$(command -v flake8 2>/dev/null \
    || echo "${SCRIPT_DIR}/../../.venv-1/bin/flake8" 2>/dev/null)
  [ -x "$FLAKE8_BIN" ] || FLAKE8_BIN=""
  if [ -n "$FLAKE8_BIN" ]; then
    FLAKE_OUT=$("$FLAKE8_BIN" backend/ --select=E,F --max-line-length=120 \
      --exclude=backend/__pycache__,backend/rag/ 2>&1 | head -20 || true)
    if [ -n "$FLAKE_OUT" ]; then
      warn "Flake8: errori presenti (vedi log)"
      echo "$FLAKE_OUT" >> "$LOG_FILE"
    else
      pass "Flake8: nessun errore E/F"
    fi
  else
    warn "flake8 non trovato — skip Python lint"
  fi

  # ── 4. Git integrity check ───────────────────
  log "\n${BLUE}[4/7] Git Integrity (no orphan gitlinks)${NC}"
  GITLINKS=$(git ls-files --stage 2>/dev/null | grep "^160000" || true)
  if [ -n "$GITLINKS" ]; then
    fail "Gitlink 160000 orfano rilevato: $GITLINKS"
  else
    pass "Git: nessun gitlink orfano"
  fi

  # ── 5. Security: no API keys in source ──────
  log "\n${BLUE}[5/7] Security Scan (no secrets in source)${NC}"
  SECRET_PATTERN='sk-[a-zA-Z0-9]{20,}|AIza[a-zA-Z0-9_-]{35}|gsk_[a-zA-Z0-9]{40,}'
  FOUND_SECRETS=$(grep -rE "$SECRET_PATTERN" --include="*.py" --include="*.ts" \
    --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist \
    . 2>/dev/null | grep -v ".env.example" | grep -v "test_stripe" || true)
  if [ -n "$FOUND_SECRETS" ]; then
    fail "API key rilevata nel source! Rimuovere immediatamente."
    echo "$FOUND_SECRETS" >> "$LOG_FILE"
  else
    pass "Security: nessuna API key in source"
  fi

  # ── 6. SPONSORS.md integrity ─────────────────
  log "\n${BLUE}[6/7] SPONSORS.md Integrity${NC}"
  if grep -q "\[Nome\]" SPONSORS.md 2>/dev/null; then
    fail "SPONSORS.md contiene template raw — file pubblico inquinato"
    if $FIX_MODE; then
      info "FIX: esegui 'bash scripts/maintenance/auto_maintain.sh' per dettagli"
    fi
  else
    pass "SPONSORS.md clean: nessun template grezzo"
  fi

  # ── 7. Sponsor stats check ───────────────────
  log "\n${BLUE}[7/7] Sponsor Campaign Tracker${NC}"
  if [ -f "data/sponsor-stats.json" ]; then
    SPONSORS=$(python3 -c "import json; d=json.load(open('data/sponsor-stats.json')); print(f\"{d['sponsors_active']}/{d['target_30d']} (target: {d['target_date']})\")" 2>/dev/null || echo "parse error")
    pass "sponsor-stats.json: $SPONSORS"
  else
    warn "data/sponsor-stats.json non trovato"
    if $FIX_MODE; then
      info "FIX: creato sponsor-stats.json baseline"
      python3 -c "
import json
from datetime import date
data = {
  'baseline_date': str(date.today()),
  'sponsors_active': 0,
  'ticket_medio_eur': 5,
  'target_30d': 100,
  'target_date': '2026-04-22',
  'channels': {'github_sponsors': 0, 'kofi': 0, 'other': 0},
  'daily_log': []
}
open('data/sponsor-stats.json', 'w').write(json.dumps(data, indent=2))
"
    fi
  fi

  # ── REPORT FINALE ────────────────────────────
  TOTAL=$((PASS + FAIL + WARN))
  log ""
  log "${BOLD}══════════════════════════════════════════════════════════${NC}"
  if [ $FAIL -eq 0 ]; then
    log "${GREEN}${BOLD}✅ AUTO-MAINTAIN: VERDE — $PASS/$TOTAL check passati${NC}"
  else
    log "${RED}${BOLD}🔴 AUTO-MAINTAIN: CRITICO — $FAIL errori su $TOTAL check${NC}"
  fi
  [ $WARN -gt 0 ] && log "${YELLOW}  ⚠ $WARN warning — non bloccanti ma da risolvere${NC}"
  log "${BOLD}══════════════════════════════════════════════════════════${NC}"
  log ""

  return $FAIL
}

# ─────────────────────────────────────────────
if $INSTALL_MODE; then
  install_autostart
  exit 0
fi

if $WATCH_MODE; then
  echo -e "${BOLD}🔄 Watch mode: check ogni 30 minuti (Ctrl+C per terminare)${NC}"
  while true; do
    run_check || true
    echo -e "${BLUE}⏰ Prossimo check tra 30 minuti...${NC}"
    sleep 1800
  done
else
  run_check
fi
