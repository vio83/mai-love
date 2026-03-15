#!/bin/bash
# ============================================================
# VIO 83 AI ORCHESTRA — Setup Mac Automation
# Run this ONCE to install all cron/launchd jobs
# ============================================================

echo "🎵 VIO 83 — Setting up Mac automation..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
PLIST_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$PROJECT_DIR/automation/logs"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$PLIST_DIR"

# Make scripts executable
chmod +x "$SCRIPT_DIR/seo-ping.sh"
echo "✅ Scripts made executable"

# 1. Install SEO Ping launchd job (every 6 hours)
cp "$SCRIPT_DIR/com.vio83.seo-ping.plist" "$PLIST_DIR/"
launchctl unload "$PLIST_DIR/com.vio83.seo-ping.plist" 2>/dev/null
launchctl load "$PLIST_DIR/com.vio83.seo-ping.plist"
echo "✅ SEO Ping automation installed (every 6 hours)"

# 2. Run first ping immediately
bash "$SCRIPT_DIR/seo-ping.sh"
echo "✅ First SEO ping executed"

# 3. Install n8n (if not present)
if ! command -v n8n &> /dev/null; then
    echo "📦 Installing n8n globally..."
    npm install -g n8n
    echo "✅ n8n installed"
else
    echo "✅ n8n already installed ($(n8n --version))"
fi

# 4. Print status
echo ""
echo "============================================"
echo "🎵 VIO 83 Automation Setup Complete!"
echo "============================================"
echo ""
echo "Active automations:"
echo "  ⏰ SEO Ping → every 6 hours (launchd)"
echo "  📊 GitHub Actions → daily SEO + weekly report"
echo "  🔄 n8n → 3 workflows ready to import"
echo ""
echo "Logs directory: $LOG_DIR"
echo ""
echo "To check launchd status:"
echo "  launchctl list | grep vio83"
echo ""
echo "To import n8n workflows:"
echo "  1. Run: n8n start"
echo "  2. Open: http://localhost:5678"
echo "  3. Import files from: $PROJECT_DIR/automation/n8n-workflows/"
echo ""
echo "To uninstall:"
echo "  launchctl unload ~/Library/LaunchAgents/com.vio83.seo-ping.plist"
echo ""
