#!/bin/bash
# VIO 83 — Health Monitor (ogni 5 minuti via LaunchAgent)
# Controlla: Backend, Ollama, Disco, Log rotation
set -euo pipefail

LOG="/Users/padronavio/Projects/vio83-ai-orchestra/automation/logs/health-monitor.log"
mkdir -p "$(dirname "$LOG")"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
DISK_FREE=$(df -g / | awk 'NR==2{print $4}')

# Backend check
BACKEND=$(curl -sf http://127.0.0.1:4000/health 2>/dev/null && echo "ok" || echo "down")

# Ollama check
OLLAMA=$(curl -sf http://127.0.0.1:11434/api/tags 2>/dev/null && echo "ok" || echo "down")

# Auto-restart backend se down (via uvicorn diretto, non pm2)
if [ "$BACKEND" = "down" ]; then
  cd /Users/padronavio/Projects/vio83-ai-orchestra
  if [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null || true
  fi
  nohup python3 -m uvicorn backend.api.server:app --host 0.0.0.0 --port 4000 > /dev/null 2>&1 &
  echo "[$TS] RESTART: backend was down, restarted" >> "$LOG"
fi

# Alert se disco sotto 5GB
if [ "$DISK_FREE" -lt 5 ]; then
  osascript -e "display notification \"Solo ${DISK_FREE}GB liberi! Esegui mac-free-space-NOW.sh\" with title \"VIO 83 Disk Alert\"" 2>/dev/null || true
fi

echo "[$TS] disk:${DISK_FREE}GB backend:${BACKEND} ollama:${OLLAMA}" >> "$LOG"

# Rotazione log se > 200KB
if [ -f "$LOG" ]; then
  LOG_SIZE=$(wc -c < "$LOG" | tr -d ' ')
  if [ "$LOG_SIZE" -gt 200000 ]; then
    tail -c 100000 "$LOG" > /tmp/hm_tmp && mv /tmp/hm_tmp "$LOG"
  fi
fi
