#!/bin/bash
# ============================================================
# VIO 83 — AUTOPILOT PERMANENTE (Installa tutto in 1 comando)
# Configura ottimizzazione automatica Mac per sempre.
#
# ESEGUI UNA SOLA VOLTA:
#   bash ~/Projects/vio83-ai-orchestra/scripts/mac-autopilot-permanent.sh
# ============================================================

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

PROJECT="$HOME/Projects/vio83-ai-orchestra"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
LOGS="$PROJECT/automation/logs"

log()  { echo -e "${GREEN}✅ $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
sep()  { echo -e "${BOLD}────────────────────────────────────────${NC}"; }

mkdir -p "$LOGS" "$LAUNCH_AGENTS"

echo -e "${BOLD}${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   VIO 83 — AUTOPILOT PERMANENTE INSTALLER                ║"
echo "║   $(date '+%Y-%m-%d %H:%M:%S')                                 ║"
echo "╚══════════════════════════════════════════════════════════╝${NC}"

# ─── Rendi eseguibili tutti gli script ───
chmod +x "$PROJECT/scripts/"*.sh 2>/dev/null
log "Script resi eseguibili"
sep

# ─── LaunchAgent 1: Cleanup notturno (03:00 ogni notte) ───
cat > "$LAUNCH_AGENTS/com.vio83.mac-cleanup.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.vio83.mac-cleanup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/padronavio/Projects/vio83-ai-orchestra/scripts/mac-cleanup.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict><key>Hour</key><integer>3</integer><key>Minute</key><integer>0</integer></dict>
    <key>StandardOutPath</key>
    <string>/Users/padronavio/Projects/vio83-ai-orchestra/automation/logs/mac-cleanup.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/padronavio/Projects/vio83-ai-orchestra/automation/logs/mac-cleanup-error.log</string>
    <key>RunAtLoad</key><false/>
    <key>KeepAlive</key><false/>
</dict>
</plist>
PLIST
launchctl unload "$LAUNCH_AGENTS/com.vio83.mac-cleanup.plist" 2>/dev/null || true
launchctl load -w "$LAUNCH_AGENTS/com.vio83.mac-cleanup.plist" 2>/dev/null
log "LaunchAgent 1: mac-cleanup → ogni notte 03:00"

# ─── LaunchAgent 2: Cargo/Rust cleanup settimanale (domenica 04:00) ───
cat > "$LAUNCH_AGENTS/com.vio83.cargo-cleanup.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.vio83.cargo-cleanup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>
rm -rf /Users/padronavio/Projects/vio83-ai-orchestra/src-tauri/target/debug 2>/dev/null;
rm -rf /Users/padronavio/.cargo/registry/src 2>/dev/null;
rm -rf /Users/padronavio/.cargo/git/checkouts 2>/dev/null;
find /Users/padronavio/Projects -name "target" -type d -maxdepth 5 2>/dev/null | while read d; do
  if [ -f "$(dirname "$d")/Cargo.toml" ]; then rm -rf "$d/debug" 2>/dev/null; fi
done;
echo "[$(date -u)] Cargo cleanup done" >> /Users/padronavio/Projects/vio83-ai-orchestra/automation/logs/cargo-cleanup.log
        </string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key><integer>0</integer>
        <key>Hour</key><integer>4</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/padronavio/Projects/vio83-ai-orchestra/automation/logs/cargo-cleanup.log</string>
    <key>RunAtLoad</key><false/>
    <key>KeepAlive</key><false/>
</dict>
</plist>
PLIST
launchctl unload "$LAUNCH_AGENTS/com.vio83.cargo-cleanup.plist" 2>/dev/null || true
launchctl load -w "$LAUNCH_AGENTS/com.vio83.cargo-cleanup.plist" 2>/dev/null
log "LaunchAgent 2: cargo-cleanup → ogni domenica 04:00"

# ─── LaunchAgent 3: Health monitor (ogni 5 minuti) ───
cat > "$LAUNCH_AGENTS/com.vio83.health-monitor.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.vio83.health-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>
# Health check ogni 5 minuti — PM2 + Backend + Disk space
LOG=/Users/padronavio/Projects/vio83-ai-orchestra/automation/logs/health-monitor.log
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
DISK_FREE=$(df -g / | awk 'NR==2{print $4}')
MIN_DISK_GB=45
PM2_COUNT=$(pm2 jlist 2>/dev/null | python3 -c "import sys,json; p=json.load(sys.stdin); print(sum(1 for x in p if x.get('pm2_env',{}).get('status')=='online'))" 2>/dev/null || echo "0")
BACKEND=$(curl -sf http://127.0.0.1:4000/health 2>/dev/null && echo "ok" || echo "down")

# Auto-restart se backend down
if [ "$BACKEND" = "down" ]; then
  cd /Users/padronavio/Projects/vio83-ai-orchestra && pm2 restart vio-backend 2>/dev/null || true
  echo "[$TS] RESTART: backend was down" >> "$LOG"
fi

# Alert + recovery se disco sotto soglia 45GB
if [ "$DISK_FREE" -lt "$MIN_DISK_GB" ]; then
    bash /Users/padronavio/Projects/vio83-ai-orchestra/scripts/mac-free-space-NOW.sh >/dev/null 2>&1 || true
    osascript -e "display notification \"⚠️ Mac: ${DISK_FREE}GB liberi (<${MIN_DISK_GB}GB). Cleanup automatico eseguito.\" with title \"VIO 83 Disk Guard\"" 2>/dev/null || true
fi

echo "[$TS] disk:${DISK_FREE}GB min:${MIN_DISK_GB}GB pm2:${PM2_COUNT} backend:${BACKEND}" >> "$LOG"
# Rotazione log 200KB
if [ $(wc -c < "$LOG") -gt 200000 ]; then tail -c 100000 "$LOG" > /tmp/hm_tmp && mv /tmp/hm_tmp "$LOG"; fi
        </string>
    </array>
    <key>StartInterval</key><integer>300</integer>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><false/>
</dict>
</plist>
PLIST
launchctl unload "$LAUNCH_AGENTS/com.vio83.health-monitor.plist" 2>/dev/null || true
launchctl load -w "$LAUNCH_AGENTS/com.vio83.health-monitor.plist" 2>/dev/null
log "LaunchAgent 3: health-monitor → ogni 5 min, auto-restart se backend down"

# ─── LaunchAgent 4: VS Code + npm cache cleanup (ogni settimana lunedì 02:00) ───
cat > "$LAUNCH_AGENTS/com.vio83.vscode-npm-cleanup.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.vio83.vscode-npm-cleanup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>
# VS Code e npm cache settimanale
npm cache clean --force 2>/dev/null;
pip3 cache purge 2>/dev/null;
rm -rf "$HOME/Library/Application Support/Code/Cache"/* 2>/dev/null;
rm -rf "$HOME/Library/Application Support/Code/Backups"/* 2>/dev/null;
find "$HOME/Projects" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true;
brew cleanup --prune=7 2>/dev/null || true;
echo "[$(date -u)] VSCode+npm cleanup done" >> /Users/padronavio/Projects/vio83-ai-orchestra/automation/logs/vscode-npm-cleanup.log
        </string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key><integer>1</integer>
        <key>Hour</key><integer>2</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
    <key>RunAtLoad</key><false/>
    <key>KeepAlive</key><false/>
</dict>
</plist>
PLIST
launchctl unload "$LAUNCH_AGENTS/com.vio83.vscode-npm-cleanup.plist" 2>/dev/null || true
launchctl load -w "$LAUNCH_AGENTS/com.vio83.vscode-npm-cleanup.plist" 2>/dev/null
log "LaunchAgent 4: vscode-npm-cleanup → ogni lunedì 02:00"

# ─── LaunchAgent 5: GitHub failed-runs autopilot (ogni 60s) ───
cat > "$LAUNCH_AGENTS/com.vio83.github-failed-runs-autopilot.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.vio83.github-failed-runs-autopilot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/padronavio/Projects/vio83-ai-orchestra/scripts/ci/github-failed-runs-autopilot.sh</string>
        <string>--owner</string>
        <string>vio83</string>
        <string>--lookback-hours</string>
        <string>24</string>
        <string>--max-runs-per-repo</string>
        <string>3</string>
    </array>
    <key>StartInterval</key><integer>60</integer>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><false/>
    <key>StandardOutPath</key>
    <string>/Users/padronavio/Projects/vio83-ai-orchestra/automation/logs/github-failed-runs-autopilot.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/padronavio/Projects/vio83-ai-orchestra/automation/logs/github-failed-runs-autopilot-error.log</string>
</dict>
</plist>
PLIST
launchctl unload "$LAUNCH_AGENTS/com.vio83.github-failed-runs-autopilot.plist" 2>/dev/null || true
launchctl load -w "$LAUNCH_AGENTS/com.vio83.github-failed-runs-autopilot.plist" 2>/dev/null
log "LaunchAgent 5: github-failed-runs-autopilot → ogni 60s"

sep
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════╗"
echo "║   AUTOPILOT PERMANENTE ATTIVATO ✅                       ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  LaunchAgent 1: mac-cleanup       → ogni notte 03:00    ║"
echo "║  LaunchAgent 2: cargo-cleanup     → domenica 04:00      ║"
echo "║  LaunchAgent 3: health-monitor    → ogni 5 minuti       ║"
echo "║  LaunchAgent 4: vscode-npm-clean  → lunedì 02:00        ║"
echo "║  LaunchAgent 5: gh failed-runs    → ogni 60 secondi     ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Log: ~/Projects/vio83-ai-orchestra/automation/logs/    ║"
echo "╚══════════════════════════════════════════════════════════╝${NC}"

echo ""
info "Per verificare che i LaunchAgent siano attivi:"
echo "   launchctl list | grep vio83"
echo ""
info "Per lo stato disco in tempo reale:"
echo "   watch -n 5 'df -h /'"
echo ""
info "ADESSO libera subito spazio (esegui questo):"
echo -e "${BOLD}   bash ~/Projects/vio83-ai-orchestra/scripts/mac-free-space-NOW.sh${NC}"
