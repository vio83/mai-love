#!/bin/bash
# VIO 83 AI ORCHESTRA — Fix & Launch
# Risolve porta occupata, copia icona fallback, installa sul Dock

set -e
cd "$HOME/Projects/vio83-ai-orchestra"

echo "★ Fix porta 5173..."
lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1
echo "✓ Porta 5173 libera"

echo "★ Setup icona Dock..."
if [ ! -f dock-icon.png ]; then
    cp src-tauri/icons/icon.png dock-icon.png
    echo "✓ Icona progetto copiata come dock-icon.png"
fi

echo "★ Installazione Dock app..."
./install_dock_app.sh

echo ""
echo "★ Avvio frontend..."
npm run dev &
sleep 3
open "http://localhost:5173"
echo "✓ TUTTO ATTIVO!"
