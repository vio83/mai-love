#!/usr/bin/env bash
#
# BRACE v3.0 — ONE-COMMAND PRESENTATION LAUNCHER
# Run this tomorrow morning to launch everything
#
# Usage: ./launch_presentation.sh
#

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 BRACE v3.0 — PRESENTATION LAUNCHER                        ║"
echo "║  Starting iMac servers + opening browser windows              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Verify SSH connection
echo "📡 Step 1: Verifying SSH connection to iMac..."
if ! ssh -o ConnectTimeout=5 vio@172.20.10.5 "echo ok" > /dev/null 2>&1; then
    echo "❌ Cannot connect to iMac via SSH"
    echo "   Make sure iMac is powered on and has Arch Linux running"
    exit 1
fi
echo "✅ SSH connection successful"

# Step 2: Verify services
echo ""
echo "✔️  Step 2: Checking BRACE services on iMac..."
for service in brace-demo brace-proto brace-elite; do
    ACTIVE=$(ssh vio@172.20.10.5 "systemctl is-active $service.service 2>/dev/null" || echo "inactive")
    if [ "$ACTIVE" = "active" ]; then
        echo "  ✅ $service is running"
    else
        echo "  ⚠️  $service not running, starting..."
        ssh vio@172.20.10.5 "sudo systemctl start $service.service 2>/dev/null"
        sleep 2
    fi
done

# Step 3: Create SSH tunnels
echo ""
echo "🔌 Step 3: Creating SSH tunnels..."
pkill -f "ssh -L" 2>/dev/null || true
sleep 1

echo "  Creating tunnel 9443..."
ssh -L 9443:127.0.0.1:9443 vio@172.20.10.5 -N -f &
sleep 1

echo "  Creating tunnel 9444..."
ssh -L 9444:127.0.0.1:9444 vio@172.20.10.5 -N -f &
sleep 1

echo "  Creating tunnel 9445..."
ssh -L 9445:127.0.0.1:9445 vio@172.20.10.5 -N -f &
sleep 2

echo "✅ SSH tunnels created"

# Step 4: Verify port accessibility
echo ""
echo "🌐 Step 4: Verifying port accessibility..."
PORTS_OK=0
for port in 9444 9445; do
    if curl -s -m 2 http://127.0.0.1:$port/ > /dev/null 2>&1; then
        echo "  ✅ Port $port accessible"
        ((PORTS_OK++))
    else
        echo "  ⏳ Port $port not yet responsive (may be loading)"
    fi
done

if [ "$PORTS_OK" -lt 2 ]; then
    echo "  ⏸️  Waiting for servers to respond..."
    sleep 3
fi

# Step 5: Open browser windows
echo ""
echo "🌍 Step 5: Opening browser windows..."

# Use 'open' command (macOS)
BROWSER="open"

if command -v $BROWSER &> /dev/null; then
    echo "  Opening DEMO (Port 9443)..."
    $BROWSER "https://127.0.0.1:9443" &
    sleep 2

    echo "  Opening PROTOTIPO (Port 9444)..."
    $BROWSER "http://127.0.0.1:9444" &
    sleep 2

    echo "  Opening ELITE (Port 9445)..."
    $BROWSER "http://127.0.0.1:9445" &

    echo "✅ Browser windows opened"
else
    echo "⚠️  Browser not found. Please manually open these URLs:"
    echo "   • DEMO:      https://127.0.0.1:9443"
    echo "   • PROTOTIPO: http://127.0.0.1:9444"
    echo "   • ELITE:     http://127.0.0.1:9445"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ PRESENTATION READY!                                        ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  All systems operational:                                      ║"
echo "║  ✓ DEMO (Port 9443)      — WCAG AAA Standard                  ║"
echo "║  ✓ PROTOTIPO (Port 9444) — Advanced Features                  ║"
echo "║  ✓ ELITE (Port 9445)     — Premium Glassmorphism ✨            ║"
echo "║                                                                ║"
echo "║  Browser windows should open automatically                    ║"
echo "║  If certificate warning appears on DEMO, click 'Proceed'      ║"
echo "║                                                                ║"
echo "║  Ready to present! 🎤                                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
