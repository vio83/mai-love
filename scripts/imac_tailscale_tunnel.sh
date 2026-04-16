#!/bin/bash
set -euo pipefail

LOG="$HOME/.vio83/imac_tunnel.log"
IMAC_TS_IP="100.116.120.3"
IMAC_LAN_IP="172.20.10.5"
IMAC_USER="vio"
IMAC_KEY="$HOME/.ssh/id_ed25519_archimede"

L4000=14000
L5173=15173
L11434=21434

mkdir -p "$HOME/.vio83"

ts() { date '+%F %T'; }

pick_host() {
  if ping -c 1 -W 2 "$IMAC_TS_IP" >/dev/null 2>&1; then
    echo "$IMAC_TS_IP"
    return 0
  fi
  if ping -c 1 -W 2 "$IMAC_LAN_IP" >/dev/null 2>&1; then
    echo "$IMAC_LAN_IP"
    return 0
  fi
  return 1
}

# Se i listener locali esistono già su tutte le porte, non fare nulla.
if lsof -nP -iTCP:${L4000} -sTCP:LISTEN >/dev/null 2>&1 && \
   lsof -nP -iTCP:${L5173} -sTCP:LISTEN >/dev/null 2>&1 && \
   lsof -nP -iTCP:${L11434} -sTCP:LISTEN >/dev/null 2>&1; then
  echo "$(ts) | tunnel already up" >> "$LOG"
  exit 0
fi

# Pulisce eventuali vecchi processi ssh tunnel incompleti.
pkill -f "ssh -fN .* -L ${L4000}:127.0.0.1:4000" >/dev/null 2>&1 || true

if ! HOST=$(pick_host); then
  echo "$(ts) | imac offline tailscale+lan" >> "$LOG"
  exit 0
fi

# Avvia tunnel multiporta.
if ssh -fN \
  -o ExitOnForwardFailure=yes \
  -o ConnectTimeout=8 \
  -o ServerAliveInterval=15 \
  -o ServerAliveCountMax=3 \
  -i "$IMAC_KEY" \
  "${IMAC_USER}@${HOST}" \
  -L ${L4000}:127.0.0.1:4000 \
  -L ${L5173}:127.0.0.1:5173 \
  -L ${L11434}:127.0.0.1:11434; then
  echo "$(ts) | tunnel up via ${HOST}: localhost:${L4000},${L5173},${L11434}" >> "$LOG"
else
  echo "$(ts) | tunnel start failed" >> "$LOG"
fi
