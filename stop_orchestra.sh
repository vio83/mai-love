#!/bin/bash
# VIO 83 AI ORCHESTRA — STOP
echo "Arresto VIO 83 AI Orchestra..."
PID_FILE="$HOME/Projects/vio83-ai-orchestra/.logs/orchestra.pids"
if [ -f "$PID_FILE" ]; then
    while read -r pid; do
        kill "$pid" 2>/dev/null && echo "Processo $pid terminato"
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi
lsof -ti:4000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || true
echo "✓ Orchestra fermata."
osascript -e 'display notification "Tutti i servizi fermati" with title "VIO 83 AI Orchestra" subtitle "Orchestra spenta"'
