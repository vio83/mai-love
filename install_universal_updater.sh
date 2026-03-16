#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
# VIO 83 AI ORCHESTRA — Universal AI Updater Installer
# Versione: 4.0 (16 Marzo 2026)
#
# INSTALLA E ATTIVA PERMANENTEMENTE:
# ✅ com.vio83.universal-ai-updater   → ogni giorno alle 03:00 UTC
# ✅ com.vio83.ollama-model-sync       → ogni giorno alle 04:00 UTC
# ✅ com.vio83.provider-updater        → ogni ora (discovery cloud)
# ✅ com.vio83.daily-auto-update       → ogni giorno alle 02:00 UTC
#
# ESEGUIRE UNA SOLA VOLTA (poi tutto è automatico per sempre)
# ═══════════════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$HOME/Projects/vio83-ai-orchestra"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PYTHON3="$(which python3)"
LOG_DIR="$PROJECT_ROOT/data/logs"

mkdir -p "$LOG_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║    VIO 83 AI ORCHESTRA — UNIVERSAL AI UPDATER INSTALLER     ║"
echo "║    Versione 4.0 — Installazione Permanente                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ─── Helper functions ───────────────────────────────────────────────

install_launchagent() {
    local label="$1"
    local plist_path="$LAUNCH_AGENTS/$label.plist"
    local plist_content="$2"

    echo "  📋 Installazione: $label"

    # Rimuovi se già caricato
    launchctl unload "$plist_path" 2>/dev/null || true

    # Scrivi plist
    echo "$plist_content" > "$plist_path"
    chmod 644 "$plist_path"

    # Carica
    if launchctl load "$plist_path" 2>/dev/null; then
        echo "  ✅ $label → ATTIVO"
    else
        echo "  ⚠️  $label → errore load (potrebbe non avere permessi su macOS 13+)"
        # Prova bootstrap
        launchctl bootstrap gui/$(id -u) "$plist_path" 2>/dev/null || true
    fi
}

# ─── 1. Universal AI Updater (MASTER — ogni giorno 03:00 UTC) ───────

PLIST_UNIVERSAL=$(cat << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vio83.universal-ai-updater</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON3</string>
        <string>-m</string>
        <string>backend.orchestrator.universal_ai_updater</string>
        <string>run</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_ROOT</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>$PROJECT_ROOT</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>$LOG_DIR/universal_updater_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/universal_updater_stderr.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>StartInterval</key>
    <integer>86400</integer>

    <key>TimeOut</key>
    <integer>3600</integer>

    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF
)

install_launchagent "com.vio83.universal-ai-updater" "$PLIST_UNIVERSAL"


# ─── 2. Ollama Model Sync (ogni giorno 04:00 UTC) ────────────────────

PLIST_OLLAMA=$(cat << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vio83.ollama-model-sync</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON3</string>
        <string>-m</string>
        <string>backend.orchestrator.ollama_model_sync</string>
        <string>full</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_ROOT</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>$PROJECT_ROOT</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>4</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>$LOG_DIR/ollama_sync_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/ollama_sync_stderr.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>TimeOut</key>
    <integer>7200</integer>

    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF
)

install_launchagent "com.vio83.ollama-model-sync" "$PLIST_OLLAMA"


# ─── 3. Provider Updater (ogni ora) — già esistente, ricarica ────────

echo "  🔄 Ricarica: com.vio83.provider-updater"
launchctl unload "$LAUNCH_AGENTS/com.vio83.provider-updater.plist" 2>/dev/null || true
launchctl load   "$LAUNCH_AGENTS/com.vio83.provider-updater.plist" 2>/dev/null && \
    echo "  ✅ com.vio83.provider-updater → RICARICATO" || \
    echo "  ⚠️  com.vio83.provider-updater → non trovato (skip)"


# ─── 4. Daily Auto-Update — già esistente, ricarica ──────────────────

echo "  🔄 Ricarica: com.vio83.daily-auto-update"
launchctl unload "$LAUNCH_AGENTS/com.vio83.daily-auto-update.plist" 2>/dev/null || true
launchctl load   "$LAUNCH_AGENTS/com.vio83.daily-auto-update.plist" 2>/dev/null && \
    echo "  ✅ com.vio83.daily-auto-update → RICARICATO" || \
    echo "  ⚠️  com.vio83.daily-auto-update → non trovato (skip)"


# ─── Verifica finale ──────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "STATO LAUNCHAGENTS VIO 83:"
echo "═══════════════════════════════════════════════════════════════"

for label in \
    com.vio83.universal-ai-updater \
    com.vio83.ollama-model-sync \
    com.vio83.provider-updater \
    com.vio83.daily-auto-update \
    com.vio83.ai-orchestra; do

    if launchctl list "$label" 2>/dev/null | grep -q "$label"; then
        echo "  ✅ $label"
    elif [ -f "$LAUNCH_AGENTS/$label.plist" ]; then
        echo "  📋 $label (plist installato, caricato al prossimo login)"
    else
        echo "  ⭕ $label (non installato)"
    fi
done

echo ""
echo "SCHEDULE AGGIORNAMENTI:"
echo "  02:00 UTC → daily-auto-update      (certificato)"
echo "  03:00 UTC → universal-ai-updater   (master, 8 fasi)"
echo "  04:00 UTC → ollama-model-sync       (pull modelli locali)"
echo "  Ogni ora  → provider-updater        (discovery cloud)"
echo ""
echo "✅ INSTALLAZIONE COMPLETATA"
echo "   Tutti gli aggiornamenti ora avvengono in automatico"
echo "   per sempre, ogni giorno, senza intervento manuale."
echo ""
