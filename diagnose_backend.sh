#!/bin/bash
# ============================================================
# VIO 83 AI ORCHESTRA — DIAGNOSI BACKEND
# Trova e mostra ESATTAMENTE perché il backend crasha
# ============================================================

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
GOLD='\033[0;33m'
NC='\033[0m'

cd "$HOME/Projects/vio83-ai-orchestra" || exit 1

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
echo -e "${GOLD}  DIAGNOSI BACKEND — VIO 83 AI ORCHESTRA${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
echo ""

# === 1. Versione Python ===
echo -e "${GOLD}[1/6] Versione Python:${NC}"
python3 --version
echo ""

# === 2. Test import FastAPI ===
echo -e "${GOLD}[2/6] Test import FastAPI:${NC}"
python3 -c "import fastapi; print(f'  FastAPI {fastapi.__version__} ✓')" 2>&1 || echo -e "${RED}  FastAPI NON installato!${NC}"
python3 -c "import uvicorn; print(f'  Uvicorn ✓')" 2>&1 || echo -e "${RED}  Uvicorn NON installato!${NC}"
python3 -c "import dotenv; print(f'  python-dotenv ✓')" 2>&1 || echo -e "${RED}  python-dotenv NON installato!${NC}"
echo ""

# === 3. Test import moduli backend ===
echo -e "${GOLD}[3/6] Test import moduli backend (uno per uno):${NC}"

python3 -c "from backend.models.schemas import ChatRequest; print('  backend.models.schemas ✓')" 2>&1
python3 -c "from backend.config.providers import CLOUD_PROVIDERS; print('  backend.config.providers ✓')" 2>&1
python3 -c "from backend.database.db import init_database; print('  backend.database.db ✓')" 2>&1
python3 -c "from backend.orchestrator.direct_router import orchestrate; print('  backend.orchestrator.direct_router ✓')" 2>&1
echo ""

# === 4. Test import core modules ===
echo -e "${GOLD}[4/6] Test import CORE modules (nuovi):${NC}"

python3 -c "from backend.core.cache import get_cache; print('  backend.core.cache ✓')" 2>&1
python3 -c "from backend.core.network import get_connection_pool; print('  backend.core.network ✓')" 2>&1
python3 -c "from backend.core.parallel import TaskPool; print('  backend.core.parallel ✓')" 2>&1
python3 -c "from backend.core.errors import get_error_handler; print('  backend.core.errors ✓')" 2>&1
python3 -c "from backend.core.security import get_vault; print('  backend.core.security ✓')" 2>&1
echo ""

# === 5. Test import completo server ===
echo -e "${GOLD}[5/6] Test import COMPLETO server.py:${NC}"
python3 -c "
import sys
try:
    from backend.api.server import app
    print('  server.py import COMPLETO ✓')
except Exception as e:
    print(f'  ERRORE: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
" 2>&1
echo ""

# === 6. Test avvio diretto (mostra errore in tempo reale) ===
echo -e "${GOLD}[6/6] Test avvio diretto backend (5 secondi, poi stop):${NC}"
echo -e "  Avvio python3 -m backend.api.server ..."
echo ""

# Avvia il server in foreground per 5 secondi e cattura tutto l'output
# Mac non ha timeout built-in, usiamo perl come alternativa
perl -e 'alarm 8; exec @ARGV' python3 -m backend.api.server 2>&1 || true

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
echo -e "${GOLD}  DIAGNOSI COMPLETATA${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
echo ""

# === Log esistenti ===
if [ -f ".logs/backend.log" ]; then
    echo -e "${GOLD}Ultime 30 righe di .logs/backend.log:${NC}"
    tail -30 .logs/backend.log
fi
