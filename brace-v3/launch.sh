#!/usr/bin/env bash
# GIU-L_IA v3.1 launcher for demo and prototype

set -euo pipefail

BRACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$BRACE_DIR/.run_logs"
mkdir -p "$LOG_DIR"

echo "[GIU-L_IA] Avvio servizi da: $BRACE_DIR"

# Kill stale listeners on known ports to avoid silent launch failures
for p in 9000 9001; do
  pids="$(lsof -tiTCP:"$p" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "[GIU-L_IA] Porta $p occupata, stop PID: $pids"
    kill -15 $pids || true
    sleep 1
    for pid in $pids; do
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid" || true
    done
  fi
done

nohup python3 "$BRACE_DIR/prototipo_web_advanced.py" > "$LOG_DIR/prototype.log" 2>&1 &
PROTO_PID=$!
echo "$PROTO_PID" > "$LOG_DIR/prototype.pid"

sleep 1

echo "[GIU-L_IA] Prototipo web avviato (PID: $PROTO_PID)"
echo "[GIU-L_IA] URL: https://127.0.0.1:9001"
echo "[GIU-L_IA] Log: $LOG_DIR/prototype.log"
echo "[GIU-L_IA] Demo terminale: python3 $BRACE_DIR/demo_terminal_optimized.py"
