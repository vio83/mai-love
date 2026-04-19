#!/usr/bin/env bash
set -euo pipefail

VSCODE_DIR="$HOME/Library/Application Support/Code"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$HOME/Desktop/vscode-recovery-backup-$STAMP"
mkdir -p "$BACKUP_DIR"

log() { echo "[recovery] $*"; }

log "Backing up VS Code user state"
mkdir -p "$BACKUP_DIR"
cp -R "$VSCODE_DIR/User" "$BACKUP_DIR/User" 2>/dev/null || true

log "Stopping heavy local AI and cleanup agents"
for label in \
  com.vio83.mac-dev-optimizer \
  com.vio83.vscode-autofix-hourly \
  com.vio83.health-monitor \
  com.vio83.github-failed-runs-autopilot \
  com.vio83.real-max-hourly \
  com.vio83.real-max-daily \
  com.vio83.ai-orchestra \
  com.vio83.runtime-services
  do
    launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  done

pkill -f 'ollama serve' 2>/dev/null || true
pkill -f 'code-server' 2>/dev/null || true

log "Cleaning non-critical VS Code caches"
rm -rf "$VSCODE_DIR/Cache"/* 2>/dev/null || true
rm -rf "$VSCODE_DIR/CachedData"/* 2>/dev/null || true
rm -rf "$VSCODE_DIR/Crashpad/completed"/* 2>/dev/null || true

log "Writing minimal emergency settings"
mkdir -p "$VSCODE_DIR/User"
cat > "$VSCODE_DIR/User/settings.json" <<'EOF'
{
  "update.mode": "none",
  "extensions.autoUpdate": false,
  "extensions.autoCheckUpdates": false,
  "telemetry.telemetryLevel": "off",
  "workbench.startupEditor": "none",
  "files.hotExit": "off",
  "editor.minimap.enabled": false,
  "editor.inlineSuggest.enabled": false,
  "github.copilot.enable": {
    "*": false
  }
}
EOF

log "Done. Next start recommendation:"
log "1) Start VS Code once with extensions disabled"
log "2) Re-enable only GitHub Copilot and Python/TypeScript essentials"
log "Backup created at: $BACKUP_DIR"
