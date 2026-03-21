#!/usr/bin/env bash
# ============================================================
# VIO 83 — Installa VS Code Autofix Autopilot (permanente)
# Registra il LaunchAgent macOS per esecuzione oraria automatica
# ============================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR" "$ROOT_DIR/automation/logs"

LABEL="com.vio83.vscode-autofix-hourly"
PLIST_SRC="$ROOT_DIR/automation/mac-scripts/${LABEL}.plist"
PLIST_DST="$LAUNCH_AGENTS_DIR/${LABEL}.plist"

# Rendi eseguibile lo script
chmod +x "$ROOT_DIR/scripts/runtime/vscode_autofix_cycle.sh"

# Copia plist in LaunchAgents
cp "$PLIST_SRC" "$PLIST_DST"

# Disinstalla versione precedente se esiste
UID_VAL="$(id -u)"
launchctl bootout "gui/${UID_VAL}/${LABEL}" 2>/dev/null || true

# Installa e avvia
launchctl bootstrap "gui/${UID_VAL}" "$PLIST_DST"
launchctl kickstart -k "gui/${UID_VAL}/${LABEL}" || true

# Prima esecuzione immediata
echo "🔧 Esecuzione immediata primo ciclo autofix..."
bash "$ROOT_DIR/scripts/runtime/vscode_autofix_cycle.sh" || true

echo ""
echo "✅ VS Code Autofix Autopilot INSTALLATO"
echo "   - Label:     $LABEL"
echo "   - Frequenza: ogni 3600s (1 ora)"
echo "   - RunAtLoad: sì (parte all'avvio Mac)"
echo "   - Log:       $ROOT_DIR/automation/logs/vscode-autofix-cycle.log"
echo "   - Correzioni: ESLint, TSC, Python compile, cache, log rotation"
echo ""
echo "🔄 Per verificare stato:"
echo "   launchctl list | grep vio83"
echo ""
echo "🛑 Per disinstallare:"
echo "   launchctl bootout gui/$(id -u)/$LABEL"
echo "   rm $PLIST_DST"
