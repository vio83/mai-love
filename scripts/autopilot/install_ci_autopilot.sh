#!/usr/bin/env bash
# =============================================================================
# Installa e avvia il CI Autopilot come LaunchAgent macOS (KeepAlive)
# Utilizzo: bash scripts/autopilot/install_ci_autopilot.sh
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
PLIST_SRC="$REPO_ROOT/automation/mac-scripts/com.vio83.ci-autopilot.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.vio83.ci-autopilot.plist"
DAEMON="$REPO_ROOT/scripts/autopilot/ci_autopilot.sh"
LOG_DIR="$REPO_ROOT/automation/logs"
LABEL="com.vio83.ci-autopilot"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CI Autopilot — Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# --- Prerequisiti ---
echo "→ Verifica prerequisiti..."
MISSING=()
for cmd in gh jq osascript; do
  command -v "$cmd" &>/dev/null || MISSING+=("$cmd")
done
if (( ${#MISSING[@]} > 0 )); then
  echo "❌ Comandi mancanti: ${MISSING[*]}"
  echo "   Installa con: brew install ${MISSING[*]}"
  exit 1
fi
echo "   ✅ gh, jq, osascript — OK"

# --- Permessi script ---
chmod +x "$DAEMON"
echo "   ✅ Permessi eseguibili su ci_autopilot.sh"

# --- Sintassi script ---
bash -n "$DAEMON"
echo "   ✅ Nessun errore sintassi in ci_autopilot.sh"

# --- Verifica plist ---
plutil -lint "$PLIST_SRC"
echo "   ✅ Plist valido"

# --- Crea directory log ---
mkdir -p "$LOG_DIR"
echo "   ✅ Log dir: $LOG_DIR"

# --- Copia plist in LaunchAgents ---
cp "$PLIST_SRC" "$PLIST_DEST"
echo "   ✅ Plist copiato in ~/Library/LaunchAgents/"

# --- Scarica se già caricato ---
if launchctl list | grep -q "$LABEL" 2>/dev/null; then
  echo "→ Scarico versione precedente..."
  launchctl unload "$PLIST_DEST" 2>/dev/null || true
  sleep 1
fi

# --- Carica LaunchAgent ---
echo "→ Carico LaunchAgent..."
launchctl load -w "$PLIST_DEST"

# --- Verifica ---
sleep 2
if launchctl list | grep -q "$LABEL"; then
  PID=$(launchctl list | awk "/$LABEL/"'{print $1}')
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  ✅ CI Autopilot ATTIVO — PID: ${PID}"
  echo "  → Repo monitorata: vio83/mai-love"
  echo "  → Log: $LOG_DIR/ci-autopilot-YYYYMMDD.log"
  echo "  → Status: data/autonomous_runtime/ci_autopilot_status.json"
  echo "  → Avvio automatico al login: SÌ (KeepAlive)"
  echo ""
  echo "  Comandi utili:"
  echo "    Stato:  launchctl list | grep ci-autopilot"
  echo "    Stop:   launchctl unload ~/Library/LaunchAgents/${LABEL}.plist"
  echo "    Start:  launchctl load -w ~/Library/LaunchAgents/${LABEL}.plist"
  echo "    Log:    tail -f $LOG_DIR/ci-autopilot-\$(date +%Y%m%d).log"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
  echo "❌ Caricamento fallito. Verifica:"
  echo "   tail $LOG_DIR/ci-autopilot-launchd.err"
  exit 1
fi
