#!/bin/bash
# ============================================================
# VIO 83 AI ORCHESTRA — Provider Update Daemon Installer
# Installa il daemon Auto-Update come LaunchAgent macOS
# Versione: 1.0 (16 Marzo 2026)
# ============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAEMON_SCRIPT="$PROJECT_ROOT/backend/orchestrator/provider_update_daemon.py"
LAUNCHAGENT_DIR="$HOME/Library/LaunchAgents"
LAUNCHAGENT_PATH="$LAUNCHAGENT_DIR/com.vio83.provider-updater.plist"
LOG_DIR="$PROJECT_ROOT/data/logs"
PID_FILE="$PROJECT_ROOT/.pids/provider-updater.pid"

mkdir -p "$LOG_DIR" "$PROJECT_ROOT/.pids" "$LAUNCHAGENT_DIR"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  VIO 83 AI ORCHESTRA — Provider Update Daemon           ║"
echo "║  Installazione per Esecuzione Permanente macOS         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# ───────────────────────────────────────────────────────────
# 1. Crea il plist LaunchAgent
# ───────────────────────────────────────────────────────────

cat > "$LAUNCHAGENT_PATH" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vio83.provider-updater</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/env</string>
        <string>python3</string>
        <string>PROJECT_ROOT_PLACEHOLDER/backend/orchestrator/provider_update_daemon.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>PROJECT_ROOT_PLACEHOLDER</string>

    <key>StandardOutPath</key>
    <string>PROJECT_ROOT_PLACEHOLDER/data/logs/provider-updater.log</string>

    <key>StandardErrorPath</key>
    <string>PROJECT_ROOT_PLACEHOLDER/data/logs/provider-updater.error.log</string>

    <!-- Esegui il daemon ogni ora (3600 secondi) -->
    <key>StartInterval</key>
    <integer>3600</integer>

    <!-- Riavvia automaticamente se crash -->
    <key>KeepAlive</key>
    <false/>

    <!-- Carica l'ambiente .env -->
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>PYTHONPATH</key>
        <string>PROJECT_ROOT_PLACEHOLDER</string>
    </dict>

    <!-- Non carica user-specific stuff (headless) -->
    <key>SessionType</key>
    <string>Background</string>
</dict>
</plist>
EOF

# Sostituisci placeholder
sed -i '' "s|PROJECT_ROOT_PLACEHOLDER|$PROJECT_ROOT|g" "$LAUNCHAGENT_PATH"

echo "✅ LaunchAgent creato: $LAUNCHAGENT_PATH"
echo ""

# ───────────────────────────────────────────────────────────
# 2. Carica il LaunchAgent
# ───────────────────────────────────────────────────────────

echo "📋 Caricamento LaunchAgent in macOS..."
launchctl load -w "$LAUNCHAGENT_PATH" 2>/dev/null || {
    echo "⚠️  LaunchAgent potrebbe essere già caricato"
    launchctl unload "$LAUNCHAGENT_PATH" 2>/dev/null
    launchctl load -w "$LAUNCHAGENT_PATH"
}

echo "✅ LaunchAgent caricato"
echo ""

# ───────────────────────────────────────────────────────────
# 3. Testa il daemon
# ───────────────────────────────────────────────────────────

echo "🧪 Testo il daemon (esecuzione singola)..."
cd "$PROJECT_ROOT"
python3 "$DAEMON_SCRIPT" once

echo ""
echo "✅ Test completato!"
echo ""

# ───────────────────────────────────────────────────────────
# 4. Mostra stato
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 STATO DAEMON"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Label:        com.vio83.provider-updater"
echo "LaunchAgent:  $LAUNCHAGENT_PATH"
echo "Log:          $LOG_DIR/provider-updater.log"
echo "Interval:     Ogni 1 ora (3600 secondi)"
echo "Auto-start:   ✅ Si (al login di macOS)"
echo ""

# Mostra lo stato
echo "🔍 Status macOS:"
launchctl list | grep "com.vio83.provider-updater" || echo "   (non ancora avviato)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 COMANDI UTILI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "# Vedi log in tempo reale:"
echo "tail -f $LOG_DIR/provider-updater.log"
echo ""
echo "# Esegui manualmente subito:"
echo "cd $PROJECT_ROOT && python3 -m backend.orchestrator.provider_update_daemon once"
echo ""
echo "# Vedi stato LaunchAgent:"
echo "launchctl list com.vio83.provider-updater"
echo ""
echo "# Disabilita il daemon:"
echo "launchctl unload $LAUNCHAGENT_PATH"
echo ""
echo "# Abilita il daemon:"
echo "launchctl load -w $LAUNCHAGENT_PATH"
echo ""
echo "# Disinstalla completamente:"
echo "launchctl unload $LAUNCHAGENT_PATH"
echo "rm $LAUNCHAGENT_PATH"
echo ""

echo "✅ INSTALLAZIONE COMPLETATA!"
echo ""
