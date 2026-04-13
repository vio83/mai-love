#!/bin/bash
# rebuild_env.sh — Ricostruzione rapida venv + node_modules
# Da usare dopo pulizia disco per ricreare gli ambienti di sviluppo
# Autrice: Viorica Porcu (vio83)
# Data: 2026-04-13

set -euo pipefail

ORCHESTRA_DIR="$HOME/Projects/vio83-ai-orchestra"
ELITE_DIR="$HOME/ai-scripts-elite"

echo "=== Ricostruzione ambiente VIO AI Orchestra ==="

# 1. Python venv orchestra
if [ ! -d "$ORCHESTRA_DIR/.venv" ]; then
    echo "[1/4] Creazione Python venv orchestra..."
    cd "$ORCHESTRA_DIR"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    echo "✅ venv orchestra creato"
else
    echo "⏭  venv orchestra già presente"
fi

# 2. node_modules orchestra
if [ ! -d "$ORCHESTRA_DIR/node_modules" ]; then
    echo "[2/4] Installazione node_modules orchestra..."
    cd "$ORCHESTRA_DIR"
    npm ci
    echo "✅ node_modules orchestra installati"
else
    echo "⏭  node_modules orchestra già presenti"
fi

# 3. Python venv ai-scripts-elite
if [ ! -d "$ELITE_DIR/.venv" ]; then
    echo "[3/4] Creazione Python venv ai-scripts-elite..."
    cd "$ELITE_DIR"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    [ -f requirements.txt ] && pip install -r requirements.txt
    deactivate
    echo "✅ venv ai-scripts-elite creato"
else
    echo "⏭  venv ai-scripts-elite già presente"
fi

# 4. node_modules ai-scripts-elite/vio-ai
if [ -d "$ELITE_DIR/vio-ai" ] && [ ! -d "$ELITE_DIR/vio-ai/node_modules" ]; then
    echo "[4/4] Installazione node_modules vio-ai..."
    cd "$ELITE_DIR/vio-ai"
    npm ci 2>/dev/null || npm install
    echo "✅ node_modules vio-ai installati"
else
    echo "⏭  node_modules vio-ai già presenti o directory non esiste"
fi

echo ""
echo "=== Ricostruzione completata ==="
echo "Spazio disco: $(df -h / | tail -1 | awk '{print $4}') liberi"
