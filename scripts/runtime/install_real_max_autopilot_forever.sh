#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR" "$ROOT_DIR/automation/logs"

chmod +x "$ROOT_DIR/scripts/runtime/real_max_autopilot_cycle.sh"
chmod +x "$ROOT_DIR/scripts/runtime/activate_real_max_global_mode.sh"
chmod +x "$ROOT_DIR/scripts/runtime/run_real_max_maintenance.sh"
chmod +x "$ROOT_DIR/scripts/runtime/macos_ultra_optimizer.sh"

cp "$ROOT_DIR/automation/mac-scripts/com.vio83.real-max-hourly.plist" "$LAUNCH_AGENTS_DIR/com.vio83.real-max-hourly.plist"
cp "$ROOT_DIR/automation/mac-scripts/com.vio83.real-max-daily.plist" "$LAUNCH_AGENTS_DIR/com.vio83.real-max-daily.plist"

UID_VAL="$(id -u)"

for label in com.vio83.real-max-hourly com.vio83.real-max-daily; do
  launchctl bootout "gui/${UID_VAL}/${label}" 2>/dev/null || true
  launchctl bootstrap "gui/${UID_VAL}" "$LAUNCH_AGENTS_DIR/${label}.plist"
  launchctl kickstart -k "gui/${UID_VAL}/${label}" || true
done

# Prima esecuzione immediata per iniziare subito l'ottimizzazione.
bash "$ROOT_DIR/scripts/runtime/real_max_autopilot_cycle.sh" hourly || true

echo "✅ REAL MAX autopilot installato"
echo "   - hourly: com.vio83.real-max-hourly (ogni 3600s)"
echo "   - daily:  com.vio83.real-max-daily (06:10 locali)"
echo "   - logs:   $ROOT_DIR/automation/logs"
