#!/usr/bin/env bash
# VIO83 Runtime Autopilot 360 — Tick ogni 2 minuti (launchd)
# Monitora, analizza e auto-ottimizza backend + Ollama + runtime
set -euo pipefail

PROJECT="/Users/padronavio/Projects/vio83-ai-orchestra"
LOG_DIR="$PROJECT/automation/logs"
LOG_FILE="$LOG_DIR/autopilot-360.log"
JSONL="$PROJECT/data/logs/autopilot-360.jsonl"
BACKEND="http://127.0.0.1:4000"
OLLAMA="http://127.0.0.1:11434"

mkdir -p "$LOG_DIR" "$(dirname "$JSONL")"

ts() { date '+%Y-%m-%dT%H:%M:%S'; }

# ── 1. Health check backend ──
backend_ok=false
health_json=""
if health_json=$(curl -sS --max-time 6 "$BACKEND/health" 2>/dev/null); then
  if echo "$health_json" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status')=='ok' else 1)" 2>/dev/null; then
    backend_ok=true
  fi
fi

# ── 2. Ollama check ──
ollama_ok=false
if curl -sS --max-time 4 "$OLLAMA/api/tags" >/dev/null 2>&1; then
  ollama_ok=true
fi

# ── 3. Auto-restart se necessario ──
if [ "$backend_ok" = false ]; then
  echo "[$(ts)] WARN: Backend non raggiungibile, tentativo restart..." >> "$LOG_FILE"
  cd "$PROJECT"
  PID=$(lsof -ti tcp:4000 2>/dev/null || true)
  if [ -n "$PID" ]; then
    kill "$PID" 2>/dev/null || true
    sleep 2
  fi
  PYTHONPATH="$PROJECT" VIO_NO_HYBRID="${VIO_NO_HYBRID:-false}" nohup python3 -m uvicorn backend.api.server:app --port 4000 --log-level warning >> "$LOG_DIR/backend-autorestart.log" 2>&1 &
  sleep 4
  if curl -sS --max-time 5 "$BACKEND/health" >/dev/null 2>&1; then
    backend_ok=true
    echo "[$(ts)] OK: Backend riavviato con successo" >> "$LOG_FILE"
  else
    echo "[$(ts)] FAIL: Backend non risponde dopo restart" >> "$LOG_FILE"
  fi
fi

if [ "$ollama_ok" = false ]; then
  echo "[$(ts)] WARN: Ollama non raggiungibile, tentativo avvio..." >> "$LOG_FILE"
  if command -v ollama >/dev/null 2>&1; then
    nohup ollama serve >> "$LOG_DIR/ollama-autorestart.log" 2>&1 &
    sleep 3
    if curl -sS --max-time 4 "$OLLAMA/api/tags" >/dev/null 2>&1; then
      ollama_ok=true
      echo "[$(ts)] OK: Ollama avviato con successo" >> "$LOG_FILE"
    fi
  fi
fi

# ── 4. Score calcolo ──
score=0
[ "$backend_ok" = true ] && score=$((score + 35))
[ "$ollama_ok" = true ] && score=$((score + 35))

# Cache cleanup se backend ok
if [ "$backend_ok" = true ]; then
  cache_resp=$(curl -sS --max-time 5 "$BACKEND/core/cache/stats" 2>/dev/null || echo "{}")
  cache_size=$(echo "$cache_resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('size',0))" 2>/dev/null || echo 0)
  if [ "$cache_size" -gt 400 ] 2>/dev/null; then
    curl -sS --max-time 5 -X POST "$BACKEND/core/cache/cleanup" >/dev/null 2>&1 || true
    echo "[$(ts)] AUTO: Cache cleanup eseguito (size=$cache_size)" >> "$LOG_FILE"
  fi
  score=$((score + 15))

  # Error check
  error_resp=$(curl -sS --max-time 5 "$BACKEND/core/errors/stats" 2>/dev/null || echo "{}")
  error_count=$(echo "$error_resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_tracked',0))" 2>/dev/null || echo 0)
  [ "$error_count" -lt 30 ] 2>/dev/null && score=$((score + 15))
fi

# ── 5. Log JSONL persistente ──
entry=$(python3 -c "
import json, sys
print(json.dumps({
    'ts': '$(ts)',
    'score': $score,
    'backend': $( [ \"$backend_ok\" = true ] && echo true || echo false ),
    'ollama': $( [ \"$ollama_ok\" = true ] && echo true || echo false ),
    'type': 'tick'
}))
" 2>/dev/null || echo '{"ts":"'"$(ts)"'","score":'"$score"',"type":"tick"}')

echo "$entry" >> "$JSONL"

# ── 6. Rotazione log (max 5000 righe) ──
if [ -f "$JSONL" ]; then
  lines=$(wc -l < "$JSONL")
  if [ "$lines" -gt 5000 ]; then
    tail -n 3000 "$JSONL" > "$JSONL.tmp" && mv "$JSONL.tmp" "$JSONL"
  fi
fi
if [ -f "$LOG_FILE" ]; then
  loglines=$(wc -l < "$LOG_FILE")
  if [ "$loglines" -gt 2000 ]; then
    tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
  fi
fi

echo "[$(ts)] TICK score=$score backend=$backend_ok ollama=$ollama_ok" >> "$LOG_FILE"
