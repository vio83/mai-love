#!/bin/bash
# ============================================================
# VIO 83 AI ORCHESTRA — AUTOSTART INSTALLER
# Copyright (c) 2026 Viorica Porcu (vio83). All Rights Reserved.
# Installa LaunchAgent per avvio automatico al login del Mac
# Apre SEMPRE in Orion browser
# ============================================================

set -e

CYAN='\033[0;36m'
GOLD='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[VIO83]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[✓]${NC} $1"; }
log_gold()  { echo -e "${GOLD}[★]${NC} $1"; }

PROJECT_DIR="$HOME/Projects/vio83-ai-orchestra"
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.vio83.ai-orchestra.plist"
PLIST_PATH="$LAUNCH_AGENT_DIR/$PLIST_NAME"

echo ""
echo -e "${GOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GOLD}║  ★  VIO 83 AI ORCHESTRA — AUTOSTART SETUP  ★       ║${NC}"
echo -e "${GOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# === CREA DIRECTORY LaunchAgents SE NON ESISTE ===
mkdir -p "$LAUNCH_AGENT_DIR"

# === RIMUOVI VECCHIO AGENT SE PRESENTE ===
if [ -f "$PLIST_PATH" ]; then
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm -f "$PLIST_PATH"
    log_info "Vecchio LaunchAgent rimosso"
fi

# === CREA LaunchAgent PLIST ===
log_gold "Creazione LaunchAgent per avvio automatico..."

cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vio83.ai-orchestra</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${PROJECT_DIR}/launch_orchestra.sh</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <false/>

    <key>StandardOutPath</key>
    <string>${PROJECT_DIR}/.logs/launchagent-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>${PROJECT_DIR}/.logs/launchagent-stderr.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
</dict>
</plist>
PLIST

log_ok "LaunchAgent creato: $PLIST_PATH"

# === CARICA IL LAUNCH AGENT ===
log_gold "Attivazione LaunchAgent..."
launchctl load "$PLIST_PATH"
log_ok "LaunchAgent caricato e attivo!"

# === VERIFICA ===
log_info "Verifica stato..."
if launchctl list | grep -q "com.vio83.ai-orchestra"; then
    log_ok "LaunchAgent registrato e in esecuzione!"
else
    log_info "LaunchAgent registrato — si attiverà al prossimo login"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}  ${GOLD}★  AUTOSTART CONFIGURATO CON SUCCESSO!  ★${NC}               ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  L'app si avvierà automaticamente ad ogni login          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  e aprirà Orion su http://localhost:5173                 ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Per DISATTIVARE l'autostart:                            ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  launchctl unload ~/Library/LaunchAgents/$PLIST_NAME     ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Per RIATTIVARE:                                         ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  launchctl load ~/Library/LaunchAgents/$PLIST_NAME       ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

osascript -e 'display notification "L'\''app si avvierà automaticamente ad ogni login!" with title "VIO 83 AI Orchestra" subtitle "Autostart configurato ★"'
