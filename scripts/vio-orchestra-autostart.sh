#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  VIO 83 AI ORCHESTRA — AUTO-START + AUTO-OTTIMIZZAZIONE 10x UNIFICATO     ║
# ║  Eseguito automaticamente al login Mac via LaunchAgent                     ║
# ║  Sincronizza: Mac ↔ VS Code ↔ Claude Desktop Cowork                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
set -uo pipefail

PROJECT="/Users/padronavio/Projects/vio83-ai-orchestra"
LOG_DIR="$PROJECT/.logs"
LOG_FILE="$LOG_DIR/autostart-unified.log"
DATA_LOG="$PROJECT/data/logs/autostart-optimization.jsonl"
VENV="$PROJECT/venv"
BACKEND_PORT=4000
FRONTEND_PORT=5173
OLLAMA_PORT=11434

export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

mkdir -p "$LOG_DIR" "$(dirname "$DATA_LOG")"

ts() { date '+%Y-%m-%dT%H:%M:%S'; }
log() { echo "[$(ts)] $1" >> "$LOG_FILE"; }

log "═══ VIO ORCHESTRA AUTO-START UNIFICATO ═══"
log "Avvio ciclo auto-ottimizzazione 10x integrale"

SCORE=0
MAX_SCORE=100
OPTIMIZATIONS=0

# ─── 1. PULIZIA PROXY ───
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy 2>/dev/null || true
log "OK: Proxy ripuliti"

# ─── 2. GIT SYNC ───
cd "$PROJECT"
if git rev-parse --is-inside-work-tree &>/dev/null; then
  git stash --include-untracked 2>/dev/null || true
  if git pull --rebase origin main 2>/dev/null; then
    log "OK: Git pull completato"
    SCORE=$((SCORE + 10))
  else
    git pull origin main 2>/dev/null || log "WARN: Git pull fallito"
  fi
  git stash pop 2>/dev/null || true
  OPTIMIZATIONS=$((OPTIMIZATIONS + 1))
fi

# ─── 3. OLLAMA ───
if ! curl -sS --max-time 4 "http://127.0.0.1:$OLLAMA_PORT/api/tags" >/dev/null 2>&1; then
  if command -v ollama >/dev/null 2>&1; then
    log "Avvio Ollama..."
    nohup ollama serve >> "$LOG_DIR/ollama-autostart.log" 2>&1 &
    sleep 4
    if curl -sS --max-time 4 "http://127.0.0.1:$OLLAMA_PORT/api/tags" >/dev/null 2>&1; then
      log "OK: Ollama avviato"
      SCORE=$((SCORE + 15))
    else
      log "WARN: Ollama non risponde dopo avvio"
    fi
  fi
else
  log "OK: Ollama già attivo"
  SCORE=$((SCORE + 15))
fi
OPTIMIZATIONS=$((OPTIMIZATIONS + 1))

# ─── 4. BACKEND PYTHON ───
if ! curl -sS --max-time 5 "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1; then
  log "Avvio Backend FastAPI..."
  # Kill orfani
  lsof -ti tcp:$BACKEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
  sleep 1

  cd "$PROJECT"
  if [ -f "$VENV/bin/python3" ]; then
    PYTHONPATH="$PROJECT" nohup "$VENV/bin/python3" -m uvicorn backend.api.server:app \
      --port $BACKEND_PORT --log-level warning \
      >> "$LOG_DIR/backend-autostart.log" 2>&1 &
  else
    PYTHONPATH="$PROJECT" nohup python3 -m uvicorn backend.api.server:app \
      --port $BACKEND_PORT --log-level warning \
      >> "$LOG_DIR/backend-autostart.log" 2>&1 &
  fi
  sleep 5

  if curl -sS --max-time 5 "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1; then
    log "OK: Backend avviato porta $BACKEND_PORT"
    SCORE=$((SCORE + 25))
  else
    log "FAIL: Backend non risponde dopo avvio"
  fi
else
  log "OK: Backend già attivo"
  SCORE=$((SCORE + 25))
fi
OPTIMIZATIONS=$((OPTIMIZATIONS + 1))

# ─── 5. VS CODE ───
VSCODE_BIN=""
if command -v code &>/dev/null; then
  VSCODE_BIN="code"
elif [ -f "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" ]; then
  VSCODE_BIN="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
fi

if [ -n "$VSCODE_BIN" ]; then
  # Apri VS Code sul progetto solo se non è già aperto
  if ! pgrep -f "Visual Studio Code" >/dev/null 2>&1; then
    "$VSCODE_BIN" "$PROJECT" 2>/dev/null &
    log "OK: VS Code aperto su progetto"
  else
    log "OK: VS Code già in esecuzione"
  fi
  SCORE=$((SCORE + 10))
else
  if [ -d "/Applications/Visual Studio Code.app" ]; then
    open -a "Visual Studio Code" "$PROJECT" 2>/dev/null || true
    log "OK: VS Code aperto via open"
    SCORE=$((SCORE + 10))
  else
    log "WARN: VS Code non trovato"
  fi
fi
OPTIMIZATIONS=$((OPTIMIZATIONS + 1))

# ─── 6. CACHE CLEANUP (se backend attivo) ───
if curl -sS --max-time 5 "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1; then
  cache_resp=$(curl -sS --max-time 5 "http://127.0.0.1:$BACKEND_PORT/core/cache/stats" 2>/dev/null || echo "{}")
  cache_size=$(echo "$cache_resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('size',0))" 2>/dev/null || echo 0)
  if [ "${cache_size:-0}" -gt 300 ] 2>/dev/null; then
    curl -sS --max-time 5 -X POST "http://127.0.0.1:$BACKEND_PORT/core/cache/cleanup" >/dev/null 2>&1 || true
    log "AUTO-OPT: Cache cleanup (size=$cache_size)"
    OPTIMIZATIONS=$((OPTIMIZATIONS + 1))
  fi
  SCORE=$((SCORE + 10))
fi

# ─── 7. LOG ROTATION ───
find "$LOG_DIR" -name "*.log" -size +5M -exec sh -c 'mv "$1" "$1.old" && touch "$1"' _ {} \; 2>/dev/null || true
find "$LOG_DIR" -name "*.old" -mtime +7 -delete 2>/dev/null || true
log "AUTO-OPT: Log rotation completata"
OPTIMIZATIONS=$((OPTIMIZATIONS + 1))
SCORE=$((SCORE + 5))

# ─── 8. NODE_MODULES HEALTH CHECK ───
cd "$PROJECT"
if [ -f "package.json" ] && [ -d "node_modules" ]; then
  if [ "package.json" -nt "node_modules/.package-lock.json" ] 2>/dev/null; then
    log "AUTO-OPT: npm install (package.json aggiornato)"
    npm install --prefer-offline --no-audit --no-fund >> "$LOG_DIR/npm-autofix.log" 2>&1 || true
    OPTIMIZATIONS=$((OPTIMIZATIONS + 1))
  fi
fi
SCORE=$((SCORE + 5))

# ─── 9. PYTHON DEPS CHECK ───
if [ -f "$VENV/bin/python3" ] && [ -f "$PROJECT/requirements.txt" ]; then
  "$VENV/bin/pip" check >> "$LOG_DIR/pip-check.log" 2>&1 || {
    log "AUTO-OPT: pip install requirements (dipendenze rotte)"
    "$VENV/bin/pip" install -r "$PROJECT/requirements.txt" --quiet >> "$LOG_DIR/pip-autofix.log" 2>&1 || true
    OPTIMIZATIONS=$((OPTIMIZATIONS + 1))
  }
fi
SCORE=$((SCORE + 5))

# ─── 10. PYCOMPILE CHECK (backend integrity) ───
SYNTAX_OK=true
for pyfile in $(find "$PROJECT/backend" -name "*.py" -not -path "*__pycache__*" 2>/dev/null | head -50); do
  if ! python3 -m py_compile "$pyfile" 2>/dev/null; then
    log "WARN: Errore sintassi in $pyfile"
    SYNTAX_OK=false
  fi
done
if [ "$SYNTAX_OK" = true ]; then
  log "OK: Backend Python syntax check passato"
  SCORE=$((SCORE + 10))
fi
OPTIMIZATIONS=$((OPTIMIZATIONS + 1))

# ─── 11. __PYCACHE__ CLEANUP ───
find "$PROJECT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT" -name "*.pyc" -delete 2>/dev/null || true
log "AUTO-OPT: __pycache__ pulito"
OPTIMIZATIONS=$((OPTIMIZATIONS + 1))

# ─── 12. DISK SPACE CHECK ───
DISK_FREE_GB=$(df -g "$HOME" 2>/dev/null | awk 'NR==2{print $4}' || echo 0)
if [ "${DISK_FREE_GB:-0}" -lt 10 ] 2>/dev/null; then
  log "WARN: Spazio disco basso: ${DISK_FREE_GB}GB"
  # Pulizia sicura
  rm -rf "$HOME/Library/Caches/pip" 2>/dev/null || true
  rm -rf "$PROJECT/.pytest_cache" 2>/dev/null || true
  OPTIMIZATIONS=$((OPTIMIZATIONS + 1))
fi
SCORE=$((SCORE + 5))

# ─── REPORT FINALE ───
SCORE_PCT=$((SCORE * 100 / MAX_SCORE))
log "═══ REPORT AUTO-OTTIMIZZAZIONE ═══"
log "Score: $SCORE/$MAX_SCORE ($SCORE_PCT%)"
log "Ottimizzazioni eseguite: $OPTIMIZATIONS"
log "═══ FINE CICLO ═══"

# JSON log per tracking storico
echo "{\"ts\":\"$(ts)\",\"score\":$SCORE,\"max\":$MAX_SCORE,\"pct\":$SCORE_PCT,\"optimizations\":$OPTIMIZATIONS,\"disk_free_gb\":${DISK_FREE_GB:-0}}" >> "$DATA_LOG"

exit 0
