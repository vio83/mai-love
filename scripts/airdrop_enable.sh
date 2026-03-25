#!/usr/bin/env bash
set -euo pipefail
echo "Enabling Wi-Fi, Bluetooth and Handoff (where possible)."

# Enable Wi-Fi
WIFI_DEVICE=$(networksetup -listallhardwareports | awk '/Wi-Fi/{getline; print $2}') || true
if [ -n "$WIFI_DEVICE" ]; then
  echo "Turning on Wi-Fi interface: $WIFI_DEVICE"
  sudo networksetup -setairportpower "$WIFI_DEVICE" on || true
else
  echo "Wi-Fi device not found via networksetup; ensure Wi-Fi is enabled in System Settings."
fi

# Enable Bluetooth (requires blueutil)
if command -v blueutil >/dev/null 2>&1; then
  echo "Turning on Bluetooth via blueutil"
  blueutil --power 1 || true
else
  echo "blueutil not found. Install via Homebrew: brew install blueutil"
fi

# Enable Handoff (may require logout/login)
echo "Enabling Handoff (may require logout/login to take effect)"
defaults write com.apple.coreservices.useractivityd ActivityAdvertisingAllowed -bool true || true
defaults write com.apple.coreservices.useractivityd ActivityReceivingAllowed -bool true || true

# Open AirDrop window
echo "Opening AirDrop window in Finder..."
open /System/Library/CoreServices/Finder.app/Contents/Applications/AirDrop.app || echo "Open Finder → Go → AirDrop manually"

echo "AirDrop/Handoff enable script completed."
