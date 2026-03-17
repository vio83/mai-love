#!/bin/bash
# ============================================================
# Installa LaunchAgent per Mac Disk Cleanup automatico
# Esegui UNA VOLTA sul Mac:
#   bash ~/Projects/vio83-ai-orchestra/scripts/install-mac-cleanup-agent.sh
# ============================================================

PLIST_SRC="$HOME/Projects/vio83-ai-orchestra/automation/mac-scripts/com.vio83.mac-cleanup.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.vio83.mac-cleanup.plist"
LOGS_DIR="$HOME/Projects/vio83-ai-orchestra/automation/logs"

echo "🔧 Installazione VIO83 Mac Cleanup Agent..."

mkdir -p "$LOGS_DIR"

if [ ! -f "$PLIST_SRC" ]; then
    echo "❌ File plist non trovato: $PLIST_SRC"
    exit 1
fi

cp "$PLIST_SRC" "$PLIST_DEST"

# Disinstalla versione vecchia se presente
launchctl unload "$PLIST_DEST" 2>/dev/null || true

# Installa e avvia
launchctl load -w "$PLIST_DEST"

echo "✅ LaunchAgent installato: com.vio83.mac-cleanup"
echo "   → Esecuzione: ogni notte alle 03:00"
echo "   → Log: $LOGS_DIR/mac-cleanup.log"
echo ""
echo "💡 Per eseguire subito il cleanup manualmente:"
echo "   bash ~/Projects/vio83-ai-orchestra/scripts/mac-cleanup.sh"
echo ""
echo "💡 Per disinstallare:"
echo "   launchctl unload ~/Library/LaunchAgents/com.vio83.mac-cleanup.plist"
