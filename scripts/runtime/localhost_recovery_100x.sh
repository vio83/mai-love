#!/usr/bin/env bash
# Localhost Recovery 100x
# Ripristino rapido stack locale: stop, cleanup porte, start, health checks.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

HOST_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"

log() {
  printf "%s\n" "$*"
}

http_code() {
  local url="$1"
  curl --noproxy '*' -s -o /dev/null -w "%{http_code}" -m 12 "$url" || true
}

wait_http_200() {
  local url="$1"
  local label="$2"
  local attempts="${3:-20}"
  local sleep_sec="${4:-1}"
  local code="000"

  for _ in $(seq 1 "$attempts"); do
    code="$(http_code "$url")"
    if [[ "$code" == "200" ]]; then
      log "  ✅ $label -> 200"
      return 0
    fi
    sleep "$sleep_sec"
  done

  log "  ❌ $label -> $code"
  return 1
}

kill_stale_ports() {
  for p in 4000 5173 9443; do
    local pids
    pids="$(lsof -tiTCP:"$p" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      log "  ⚠️ Porta $p occupata, termino PID: $pids"
      kill -15 $pids 2>/dev/null || true
      sleep 1
      for pid in $pids; do
        kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
      done
    fi
  done
}

log "╔══════════════════════════════════════════════════════════╗"
log "║  🔧 LOCALHOST RECOVERY 100x                              ║"
log "╚══════════════════════════════════════════════════════════╝"

log "[1/5] Stop orchestra"
./orchestra.sh stop >/dev/null 2>&1 || true

log "[2/5] Cleanup porte stale"
kill_stale_ports

log "[3/5] Start orchestra"
./orchestra.sh >/dev/null 2>&1 || true

log "[4/5] Health checks localhost"
wait_http_200 "http://127.0.0.1:5173" "Frontend localhost"
wait_http_200 "http://127.0.0.1:4000/health" "Backend localhost"
wait_http_200 "http://127.0.0.1:9443" "GIU-L_IA localhost"

if [[ -n "$HOST_IP" ]]; then
  log "[5/5] Health checks LAN ($HOST_IP)"
  wait_http_200 "http://$HOST_IP:5173" "Frontend LAN"
  wait_http_200 "http://$HOST_IP:4000/health" "Backend LAN"
  wait_http_200 "http://$HOST_IP:9443" "GIU-L_IA LAN"
else
  log "[5/5] IP LAN non rilevato: salto check LAN"
fi

log "✅ Recovery completato: localhost e LAN operativi"
