#!/usr/bin/env bash
# ============================================================
# VIO 83 — RIATTIVA VS CODE + APP ORCHESTRA
# Esegui: chmod +x RIATTIVA-TUTTO.sh && ./RIATTIVA-TUTTO.sh
# ============================================================
set -uo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  🎵 VIO 83 AI ORCHESTRA — RIATTIVAZIONE COMPLETA v2       ${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ═══════════════════════════════════════════════
# FASE 0: Fix proxy fantasma (se presente)
# ═══════════════════════════════════════════════
echo -e "${CYAN}═══ FASE 0: Pulizia proxy ═══${NC}"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy no_proxy NO_PROXY 2>/dev/null || true
git config --global --unset http.proxy 2>/dev/null || true
git config --global --unset https.proxy 2>/dev/null || true
echo -e "${GREEN}  ✅ Variabili proxy ripulite${NC}"
echo ""

# ═══════════════════════════════════════════════
# FASE 1: Riattiva VS Code
# ═══════════════════════════════════════════════
echo -e "${CYAN}═══ FASE 1: VS Code ═══${NC}"

# Cerca VS Code in tutti i posti possibili
VSCODE_BIN=""
if command -v code &>/dev/null; then
  VSCODE_BIN="code"
elif [ -f "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" ]; then
  VSCODE_BIN="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
elif [ -f "/usr/local/bin/code" ]; then
  VSCODE_BIN="/usr/local/bin/code"
fi

if [ -n "$VSCODE_BIN" ]; then
  echo -e "  Apro VS Code con il progetto..."
  "$VSCODE_BIN" "$ROOT_DIR" 2>/dev/null &
  echo -e "${GREEN}  ✅ VS Code aperto${NC}"
elif [ -d "/Applications/Visual Studio Code.app" ]; then
  echo -e "  Apro VS Code tramite open..."
  open -a "Visual Studio Code" "$ROOT_DIR"
  echo -e "${GREEN}  ✅ VS Code aperto${NC}"
  echo -e "${YELLOW}  TIP: In VS Code → Cmd+Shift+P → 'Shell Command: Install code command in PATH'${NC}"
else
  echo -e "${RED}  ❌ VS Code non trovato!${NC}"
  echo -e "  Installa: brew install --cask visual-studio-code"
fi

echo ""

# ═══════════════════════════════════════════════
# FASE 2: Fix + Ricostruisci venv Python
# ═══════════════════════════════════════════════
echo -e "${CYAN}═══ FASE 2: Python Environment ═══${NC}"

# Trova il Python di sistema migliore
SYS_PYTHON=""
for P in python3.12 python3.13 python3.11 python3; do
  if command -v "$P" &>/dev/null; then
    SYS_PYTHON="$(command -v "$P")"
    break
  fi
done

if [ -z "$SYS_PYTHON" ]; then
  echo -e "${RED}  ❌ Python3 non trovato sul sistema!${NC}"
  echo -e "  Installa: brew install python@3.12"
  echo -e "  Poi ri-esegui questo script."
  exit 1
fi

PYVER=$($SYS_PYTHON --version 2>&1)
echo -e "  Python di sistema: ${CYAN}$SYS_PYTHON ($PYVER)${NC}"

# Verifica se il venv è funzionante
VENV_OK=false
if [ -f "$ROOT_DIR/venv/bin/python3" ] && "$ROOT_DIR/venv/bin/python3" --version &>/dev/null; then
  VENV_OK=true
  echo -e "${GREEN}  ✅ venv esistente funzionante${NC}"
fi

if [ "$VENV_OK" = false ]; then
  echo -e "${YELLOW}  ⚠️  venv rotto o mancante — lo ricreo da zero...${NC}"

  # Backup del vecchio venv (se esiste)
  if [ -d "$ROOT_DIR/venv" ]; then
    rm -rf "$ROOT_DIR/venv.broken" 2>/dev/null || true
    mv "$ROOT_DIR/venv" "$ROOT_DIR/venv.broken" 2>/dev/null || true
    echo -e "  Vecchio venv spostato in venv.broken/"
  fi

  # Crea nuovo venv
  echo -e "  Creo nuovo venv con $SYS_PYTHON..."
  $SYS_PYTHON -m venv "$ROOT_DIR/venv"

  if [ -f "$ROOT_DIR/venv/bin/python3" ] && "$ROOT_DIR/venv/bin/python3" --version &>/dev/null; then
    echo -e "${GREEN}  ✅ Nuovo venv creato${NC}"
  else
    echo -e "${RED}  ❌ Errore nella creazione del venv!${NC}"
    exit 1
  fi
fi

# Usa il Python del venv
PYTHON="$ROOT_DIR/venv/bin/python3"
PIP="$ROOT_DIR/venv/bin/pip"

# Aggiorna pip
echo -e "  Aggiorno pip..."
$PYTHON -m pip install --upgrade pip --quiet 2>/dev/null

# Installa dipendenze
echo -e "  Installo dipendenze da requirements.txt..."
$PIP install -r "$ROOT_DIR/requirements.txt" --quiet 2>&1 | tail -5

# Verifica moduli critici
echo -e "  Verifica moduli critici:"
for MOD in fastapi uvicorn pydantic httpx; do
  if $PYTHON -c "import $MOD" 2>/dev/null; then
    echo -e "    ${GREEN}✓${NC} $MOD"
  else
    echo -e "    ${RED}✗${NC} $MOD — installo..."
    $PIP install "$MOD" --quiet 2>/dev/null
  fi
done

echo ""

# ═══════════════════════════════════════════════
# FASE 3: Avvia Ollama
# ═══════════════════════════════════════════════
echo -e "${CYAN}═══ FASE 3: Ollama ═══${NC}"

if command -v ollama &>/dev/null; then
  if curl -sf http://localhost:11434/api/tags &>/dev/null; then
    echo -e "${GREEN}  ✅ Ollama già attivo${NC}"
  else
    echo -e "  Avvio Ollama..."
    # Su macOS, Ollama potrebbe essere un'app
    if [ -d "/Applications/Ollama.app" ]; then
      open -a Ollama 2>/dev/null || true
    else
      ollama serve &>/dev/null &
    fi
    sleep 4
    if curl -sf http://localhost:11434/api/tags &>/dev/null; then
      echo -e "${GREEN}  ✅ Ollama avviato${NC}"
    else
      echo -e "${YELLOW}  ⏳ Ollama in avvio — attendi qualche secondo${NC}"
    fi
  fi
  echo -e "  Modelli disponibili:"
  ollama list 2>/dev/null | head -10 || echo "  (nessuno — scarica con: ollama pull qwen2.5-coder:3b)"
else
  echo -e "${YELLOW}  ⚠️  Ollama non installato${NC}"
  echo -e "  Installa: brew install ollama"
  echo -e "  Oppure: https://ollama.com/download"
fi

echo ""

# ═══════════════════════════════════════════════
# FASE 4: Avvia Backend FastAPI
# ═══════════════════════════════════════════════
echo -e "${CYAN}═══ FASE 4: Backend FastAPI ═══${NC}"

PORT="${VIO_BACKEND_PORT:-4000}"

# Uccidi processi stale sulla porta
PIDS="$(lsof -ti tcp:${PORT} 2>/dev/null || true)"
if [[ -n "$PIDS" ]]; then
  echo -e "  ${YELLOW}Porta ${PORT} occupata — chiudo processi stale${NC}"
  kill -9 $PIDS 2>/dev/null || true
  sleep 1
fi

export PYTHONPATH="$ROOT_DIR"
export VIO_EXECUTION_PROFILE="real-max-local"
export VIO_SPEED_MODE="true"
export VIO_LOCAL_MODEL_PREFERENCE="${VIO_LOCAL_MODEL_PREFERENCE:-qwen2.5-coder:3b}"

mkdir -p "$ROOT_DIR/logs"

echo -e "  Avvio backend su porta ${PORT}..."
nohup "$PYTHON" -m uvicorn backend.api.server:app \
  --reload --host 127.0.0.1 --port "$PORT" \
  > "$ROOT_DIR/logs/backend-out.log" 2> "$ROOT_DIR/logs/backend-error.log" &
BACKEND_PID=$!
echo -e "  PID backend: $BACKEND_PID"

# Attendi che il server parta
for i in 1 2 3 4 5 6 7 8; do
  sleep 1
  if curl -sf "http://localhost:${PORT}/healthz" &>/dev/null 2>&1 || \
     curl -sf "http://localhost:${PORT}/api/health" &>/dev/null 2>&1 || \
     curl -sf "http://localhost:${PORT}/" &>/dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Backend attivo → http://localhost:${PORT}${NC}"
    break
  fi
  if [ "$i" = "8" ]; then
    # Mostra gli ultimi errori dal log
    echo -e "${YELLOW}  ⏳ Backend ancora in avvio...${NC}"
    if [ -f "$ROOT_DIR/logs/backend-error.log" ]; then
      LAST_ERR=$(tail -5 "$ROOT_DIR/logs/backend-error.log" 2>/dev/null || true)
      if [ -n "$LAST_ERR" ]; then
        echo -e "${RED}  Ultimi errori:${NC}"
        echo "$LAST_ERR" | head -5
      fi
    fi
    if [ -f "$ROOT_DIR/logs/backend-out.log" ]; then
      LAST_OUT=$(tail -3 "$ROOT_DIR/logs/backend-out.log" 2>/dev/null || true)
      if [ -n "$LAST_OUT" ]; then
        echo "$LAST_OUT"
      fi
    fi
  fi
done

echo ""

# ═══════════════════════════════════════════════
# FASE 5: Avvia Frontend Vite
# ═══════════════════════════════════════════════
echo -e "${CYAN}═══ FASE 5: Frontend React (Vite) ═══${NC}"

# Uccidi processi stale sulla porta 5173
FPIDS="$(lsof -ti tcp:5173 2>/dev/null || true)"
if [[ -n "$FPIDS" ]]; then
  echo -e "  ${YELLOW}Porta 5173 occupata — chiudo processi stale${NC}"
  kill -9 $FPIDS 2>/dev/null || true
  sleep 1
fi

# Verifica node_modules
if [ ! -d "$ROOT_DIR/node_modules" ]; then
  echo -e "${YELLOW}  node_modules mancante — eseguo npm install...${NC}"
  npm install 2>&1 | tail -3
fi

if [ -d "$ROOT_DIR/node_modules" ]; then
  echo -e "  Avvio Vite dev server..."
  nohup npx vite --host 127.0.0.1 --port 5173 \
    > "$ROOT_DIR/logs/frontend-out.log" 2>&1 &
  FRONTEND_PID=$!
  echo -e "  PID frontend: $FRONTEND_PID"

  for i in 1 2 3 4 5; do
    sleep 1
    if curl -sf "http://localhost:5173" &>/dev/null; then
      echo -e "${GREEN}  ✅ Frontend attivo → http://localhost:5173${NC}"
      break
    fi
    if [ "$i" = "5" ]; then
      echo -e "${YELLOW}  ⏳ Frontend in avvio — controlla logs/frontend-out.log${NC}"
    fi
  done
else
  echo -e "${RED}  ❌ npm install fallito — controlla la rete e il proxy${NC}"
fi

echo ""

# ═══════════════════════════════════════════════
# RIEPILOGO FINALE
# ═══════════════════════════════════════════════
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  🎵 VIO AI ORCHESTRA — STATO SERVIZI${NC}"
echo -e ""

# Verifica stato finale di ogni servizio
if command -v code &>/dev/null || [ -d "/Applications/Visual Studio Code.app" ]; then
  echo -e "  VS Code:    ${GREEN}APERTO${NC}"
else
  echo -e "  VS Code:    ${RED}NON TROVATO${NC}"
fi

if curl -sf "http://localhost:11434/api/tags" &>/dev/null; then
  echo -e "  Ollama:     ${GREEN}ATTIVO${NC}  → http://localhost:11434"
else
  echo -e "  Ollama:     ${YELLOW}NON ATTIVO${NC}"
fi

if curl -sf "http://localhost:${PORT}/" &>/dev/null 2>&1 || \
   curl -sf "http://localhost:${PORT}/healthz" &>/dev/null 2>&1; then
  echo -e "  Backend:    ${GREEN}ATTIVO${NC}  → http://localhost:${PORT}"
else
  echo -e "  Backend:    ${YELLOW}IN AVVIO${NC} → http://localhost:${PORT}"
fi

if curl -sf "http://localhost:5173" &>/dev/null; then
  echo -e "  Frontend:   ${GREEN}ATTIVO${NC}  → http://localhost:5173"
else
  echo -e "  Frontend:   ${YELLOW}IN AVVIO${NC} → http://localhost:5173"
fi

echo -e ""
echo -e "  Logs:       $ROOT_DIR/logs/"
echo -e ""
echo -e "  ${CYAN}Per fermare tutto:${NC}"
echo -e "  kill \$(lsof -ti tcp:4000,5173) 2>/dev/null"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Apri il browser sulla app dopo che tutto è pronto
sleep 2
if command -v open &>/dev/null; then
  open "http://localhost:5173" 2>/dev/null || true
fi
