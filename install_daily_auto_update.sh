#!/bin/bash
# ============================================================
# VIO 83 AI ORCHESTRA — Daily Auto-Update Daemon Installer
# Installazione per Esecuzione Permanente GIORNALIERA su macOS
# Sincerità 100% Brutale — Certificazione Totale
# Data: 16 Marzo 2026
# ============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAEMON_SCRIPT="$PROJECT_ROOT/backend/orchestrator/daily_auto_update_certified.py"
LAUNCHAGENT_DIR="$HOME/Library/LaunchAgents"
LAUNCHAGENT_PATH="$LAUNCHAGENT_DIR/com.vio83.daily-auto-update.plist"
LOG_DIR="$PROJECT_ROOT/data/logs"
DATA_DIR="$PROJECT_ROOT/data"
PID_FILE="$PROJECT_ROOT/.pids/daily-auto-update.pid"
CERT_DIR="$DATA_DIR/updates/certificates"

mkdir -p "$LOG_DIR" "$CERT_DIR" "$PROJECT_ROOT/.pids" "$LAUNCHAGENT_DIR"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  VIO 83 AI ORCHESTRA — Daily Auto-Update Daemon        ║"
echo "║  Installazione PERMANENTE GIORNALIERA — Certificazione ║"
echo "║  Eccellenza Assoluta — Sincerità 100% Brutale          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# ───────────────────────────────────────────────────────────
# 1. Backup del LaunchAgent precedente (se esiste)
# ───────────────────────────────────────────────────────────

if [ -f "$LAUNCHAGENT_PATH" ]; then
    echo "📋 Backup LaunchAgent precedente..."
    cp "$LAUNCHAGENT_PATH" "${LAUNCHAGENT_PATH}.backup.$(date +%s)"
    echo "   ✅ Backup creato"

    # Unload precedente
    launchctl unload "$LAUNCHAGENT_PATH" 2>/dev/null || true
fi

echo ""

# ───────────────────────────────────────────────────────────
# 2. Crea il plist LaunchAgent (esecuzione giornaliera)
# ───────────────────────────────────────────────────────────

cat > "$LAUNCHAGENT_PATH" << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vio83.daily-auto-update</string>

    <key>Program</key>
    <string>/usr/bin/env</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/env</string>
        <string>python3</string>
        <string>PROJECT_ROOT_PLACEHOLDER/backend/orchestrator/daily_auto_update_certified.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>PROJECT_ROOT_PLACEHOLDER</string>

    <!-- OGNI GIORNO alle 02:00 UTC (00:00 CET in inverno, 01:00 CEST in estate) -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <!-- Output logging -->
    <key>StandardOutPath</key>
    <string>PROJECT_ROOT_PLACEHOLDER/data/logs/daily-auto-update.log</string>

    <key>StandardErrorPath</key>
    <string>PROJECT_ROOT_PLACEHOLDER/data/logs/daily-auto-update.error.log</string>

    <!-- Non riavviare automaticamente (esegui solo al tempo specificato) -->
    <key>KeepAlive</key>
    <false/>

    <!-- Ambiente -->
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>PYTHONPATH</key>
        <string>PROJECT_ROOT_PLACEHOLDER</string>
        <key>LC_ALL</key>
        <string>en_US.UTF-8</string>
    </dict>

    <!-- Headless mode -->
    <key>SessionType</key>
    <string>Background</string>

    <!-- Timeout: max 30 minuti per ciclo (se impiccato, uccidi) -->
    <key>TimeOut</key>
    <integer>1800</integer>

    <!-- Usa umask stretto per file creati -->
    <key>Umask</key>
    <integer>077</integer>
</dict>
</plist>
PLIST_EOF

# Sostituisci placeholder
sed -i '' "s|PROJECT_ROOT_PLACEHOLDER|$PROJECT_ROOT|g" "$LAUNCHAGENT_PATH"

echo "✅ LaunchAgent creato: $LAUNCHAGENT_PATH"
echo "   📅 Esecuzione: OGNI GIORNO alle 02:00 UTC"
echo ""

# ───────────────────────────────────────────────────────────
# 3. Carica il LaunchAgent
# ───────────────────────────────────────────────────────────

echo "📋 Caricamento LaunchAgent in macOS..."
launchctl load -w "$LAUNCHAGENT_PATH"

echo "✅ LaunchAgent caricato"
echo ""

# ───────────────────────────────────────────────────────────
# 4. Testa il daemon (esecuzione immediata)
# ───────────────────────────────────────────────────────────

echo "🧪 Test: Esecuzione immediata del daemon..."
echo ""

cd "$PROJECT_ROOT"
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')

from backend.orchestrator.daily_auto_update_certified import auto_updater

result = asyncio.run(auto_updater.run_daily_update())

print()
print('='*60)
print('TEST RESULT:', result['status'].upper())
print('='*60)
" | tee "$LOG_DIR/daily-auto-update-initial-test.log"

echo ""
echo "✅ Test completato!"
echo ""

# ───────────────────────────────────────────────────────────
# 5. Mostra configurazione finale
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 CONFIGURAZIONE DAEMON"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Label:               com.vio83.daily-auto-update"
echo "LaunchAgent Path:    $LAUNCHAGENT_PATH"
echo "Daemon Script:       $DAEMON_SCRIPT"
echo "Log File:            $LOG_DIR/daily-auto-update.log"
echo "Error Log:           $LOG_DIR/daily-auto-update.error.log"
echo "Certificates Dir:    $CERT_DIR"
echo "Database:            $DATA_DIR/daily_updates.db"
echo ""
echo "Execution Schedule:  OGNI GIORNO alle 02:00 UTC"
echo "Timeout:             30 minuti (auto-kill se impiccato)"
echo "Auto-restart:        ❌ No (esegui solo al tempo programmato)"
echo "Persistence:         ✅ Si (si riavvia automaticamente post-reboot)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 FUNZIONALITÀ ATTIVE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Scoperta automatica nuovi modelli (Ollama, Groq, etc)"
echo "✅ Scoperta automatica nuovi provider"
echo "✅ Scoperta automatica nuove dipendenze"
echo "✅ Download artefatti verificato"
echo "✅ Verifica integrità (checksum SHA256)"
echo "✅ Test funzionalità completo"
echo "✅ Installazione automatica"
echo "✅ Certificazione ufficiale"
echo "✅ Auto-rollback su errore"
echo "✅ Audit log permanente e verificabile"
echo "✅ Sincerità 100% Brutale"
echo ""

# ───────────────────────────────────────────────────────────
# 6. Comandi di gestione
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 COMANDI DI GESTIONE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "# Vedi lo stato del daemon:"
echo "launchctl list com.vio83.daily-auto-update"
echo ""
echo "# Vedi i log in tempo reale:"
echo "tail -f $LOG_DIR/daily-auto-update.log"
echo ""
echo "# Esegui subito manualmente (senza aspettare 24h):"
echo "cd $PROJECT_ROOT && python3 -m backend.orchestrator.daily_auto_update_certified"
echo ""
echo "# Vedi tutti i certificati installati:"
echo "ls -lh $CERT_DIR/"
echo ""
echo "# Vedi audit log completo:"
echo "sqlite3 $DATA_DIR/daily_updates.db 'SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 50;'"
echo ""
echo "# Disabilita il daemon (non lo rimuove):"
echo "launchctl unload $LAUNCHAGENT_PATH"
echo ""
echo "# Abilita il daemon:"
echo "launchctl load -w $LAUNCHAGENT_PATH"
echo ""
echo "# Disinstalla completamente il daemon:"
echo "launchctl unload $LAUNCHAGENT_PATH && rm $LAUNCHAGENT_PATH"
echo ""

# ───────────────────────────────────────────────────────────
# 7. Test finale status
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ STATUS FINALE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

launchctl list | grep "com.vio83.daily-auto-update" && \
    echo "✅ Daemon ATTIVO e CARICATO in macOS" || \
    echo "⚠️  Daemon non ancora attivo (verrà eseguito domani alle 02:00 UTC)"

echo ""
echo "🚀 VIO 83 AI ORCHESTRA — Daily Auto-Update Daemon INSTALLATO!"
echo "💪 Eccellenza Permanente — Sincerità 100% — Certificazione TOTALE"
echo ""
