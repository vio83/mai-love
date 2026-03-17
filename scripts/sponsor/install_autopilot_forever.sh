#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/com.vio83.sponsor-autopilot.plist"
LOG_DIR="$ROOT_DIR/automation/logs"

mkdir -p "$PLIST_DIR" "$LOG_DIR"

chmod +x "$ROOT_DIR/scripts/sponsor/run_weekly_content_engine.sh"
chmod +x "$ROOT_DIR/scripts/sponsor/run_daily_autopilot.sh"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.vio83.sponsor-autopilot</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$ROOT_DIR/scripts/sponsor/run_daily_autopilot.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>5</integer></dict>
    <dict><key>Weekday</key><integer>3</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>5</integer></dict>
    <dict><key>Weekday</key><integer>4</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>5</integer></dict>
    <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>5</integer></dict>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/sponsor-autopilot.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/sponsor-autopilot-error.log</string>
  <key>KeepAlive</key>
  <false/>
</dict>
</plist>
EOF

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

bash "$ROOT_DIR/scripts/sponsor/run_daily_autopilot.sh" --force

echo "✅ Sponsor autopilot installato e avviato"
echo "Plist: $PLIST_PATH"
echo "Log: $LOG_DIR/sponsor-autopilot.log"
echo "Status: launchctl list | grep sponsor-autopilot"
