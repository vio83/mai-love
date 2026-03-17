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
chmod +x "$PROJECT_DIR/scripts/sponsor/run_daily_autopilot.sh"
chmod +x "$PROJECT_DIR/scripts/sponsor/run_weekly_content_engine.sh"
chmod +x "$PROJECT_DIR/scripts/sponsor/install_autopilot_forever.sh"
chmod +x "$PROJECT_DIR/scripts/runtime/activate_real_max_local_mode.sh"
chmod +x "$PROJECT_DIR/scripts/runtime/activate_real_max_global_mode.sh"
chmod +x "$PROJECT_DIR/scripts/runtime/run_real_max_maintenance.sh"
echo "✅ Scripts made executable"

# 1. Install SEO Ping launchd job (every 6 hours)
cp "$SCRIPT_DIR/com.vio83.seo-ping.plist" "$PLIST_DIR/"
launchctl unload "$PLIST_DIR/com.vio83.seo-ping.plist" 2>/dev/null
launchctl load "$PLIST_DIR/com.vio83.seo-ping.plist"
echo "✅ SEO Ping automation installed (every 6 hours)"

# 1b. Install Sponsor Autopilot launchd job (Mon/Wed/Thu/Fri)
cp "$PROJECT_DIR/automation/mac-scripts/com.vio83.sponsor-autopilot.plist" "$PLIST_DIR/"
launchctl unload "$PLIST_DIR/com.vio83.sponsor-autopilot.plist" 2>/dev/null
launchctl load "$PLIST_DIR/com.vio83.sponsor-autopilot.plist"
echo "✅ Sponsor autopilot installed (Mon/Wed/Thu/Fri)"

# 1c. Install Real Max maintenance job (daily + weekly deep check)
cp "$PROJECT_DIR/automation/mac-scripts/com.vio83.real-max-maintenance.plist" "$PLIST_DIR/"
launchctl unload "$PLIST_DIR/com.vio83.real-max-maintenance.plist" 2>/dev/null
launchctl load "$PLIST_DIR/com.vio83.real-max-maintenance.plist"
echo "✅ Real Max maintenance installed (daily + weekly)"

# 2. Run first ping immediately
bash "$SCRIPT_DIR/seo-ping.sh"
echo "✅ First SEO ping executed"

# 2b. Run first sponsor autopilot immediately
bash "$PROJECT_DIR/scripts/sponsor/run_daily_autopilot.sh" --force
echo "✅ First sponsor autopilot run executed"

# 2c. Run first real-max maintenance immediately
bash "$PROJECT_DIR/scripts/runtime/run_real_max_maintenance.sh"
echo "✅ First real-max maintenance run executed"

# 2d. Enforce local-only no-hybrid profile permanently
bash "$PROJECT_DIR/scripts/runtime/activate_real_max_local_mode.sh"
echo "✅ Real-max local-only no-hybrid profile activated"

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
echo "  🚀 Sponsor Autopilot → Mon/Wed/Thu/Fri (launchd)"
echo "  🧠 Real Max Optimizer → daily + weekly (launchd)"
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
echo "  launchctl unload ~/Library/LaunchAgents/com.vio83.sponsor-autopilot.plist"
echo "  launchctl unload ~/Library/LaunchAgents/com.vio83.real-max-maintenance.plist"
echo ""
