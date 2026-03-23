#!/usr/bin/env bash
# Install VIO 83 Mac Dev Optimizer as a permanent LaunchAgent.
# Runs every 4 hours + at login. Keeps disk, RAM, caches clean.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$SCRIPT_DIR/com.vio83.mac-dev-optimizer.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.vio83.mac-dev-optimizer.plist"
OPTIMIZER="$SCRIPT_DIR/mac_dev_optimizer.sh"

echo "=== VIO 83 Mac Dev Optimizer — Install ==="

# Make optimizer executable
chmod +x "$OPTIMIZER"

# Unload old version if exists
if launchctl list | grep -q "com.vio83.mac-dev-optimizer" 2>/dev/null; then
  launchctl unload "$PLIST_DST" 2>/dev/null || true
  echo "Old LaunchAgent unloaded."
fi

# Copy plist
cp "$PLIST_SRC" "$PLIST_DST"
echo "Plist installed: $PLIST_DST"

# Load
launchctl load "$PLIST_DST"
echo "LaunchAgent loaded."

# Verify
if launchctl list | grep -q "com.vio83.mac-dev-optimizer"; then
  echo "✔ com.vio83.mac-dev-optimizer is ACTIVE"
else
  echo "✖ Failed to activate. Check: launchctl list | grep vio83"
  exit 1
fi

# Run immediately
echo "Running first optimization now..."
bash "$OPTIMIZER"
echo "=== Installation complete. Runs every 4 hours + at login. ==="
