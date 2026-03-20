#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR" "$ROOT_DIR/automation/logs"

chmod +x "$ROOT_DIR/scripts/runtime/real_max_watchdog.sh"
chmod +x "$ROOT_DIR/scripts/runtime/install_real_max_autopilot_forever.sh"
chmod +x "$ROOT_DIR/scripts/runtime/macos_ultra_optimizer.sh"

# Ensure hourly+daily autopilot is installed first.
bash "$ROOT_DIR/scripts/runtime/install_real_max_autopilot_forever.sh" >/dev/null 2>&1 || true

cp "$ROOT_DIR/automation/mac-scripts/com.vio83.real-max-watchdog.plist" "$LAUNCH_AGENTS_DIR/com.vio83.real-max-watchdog.plist"

UID_VAL="$(id -u)"
label="com.vio83.real-max-watchdog"
launchctl bootout "gui/${UID_VAL}/${label}" 2>/dev/null || true
launchctl bootstrap "gui/${UID_VAL}" "$LAUNCH_AGENTS_DIR/${label}.plist"
launchctl kickstart -k "gui/${UID_VAL}/${label}" || true

# Immediate run
bash "$ROOT_DIR/scripts/runtime/real_max_watchdog.sh" || true

echo "✅ REAL MAX watchdog installato"
echo "   - label: ${label}"
echo "   - check interval: 900s"
echo "   - threshold default: 6GB"
echo "   - model-sync kill switch: enabled"
echo "   - log: $ROOT_DIR/automation/logs/real-max-watchdog.log"
