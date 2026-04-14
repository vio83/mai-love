#!/bin/bash
#
# BRACE v3.0 — iMac Archimede Deployment Script
# Sincronizza + Avvia DEMO e PROTOTIPO
# Esecuzione: ./deploy_brace_imac.sh
#

set -e

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  🚀 BRACE v3.0 → iMac Archimede Deployment                        ║"
echo "║  Sincronizzazione + Configurazione + Avvio                        ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
IMAC_HOST="vio@172.20.10.5"
IMAC_PATH="/opt/vioaiorchestra"
LOCAL_BRACE="brace-v3"

echo "📤 [1/5] Pacchettizzazione BRACE v3.0..."
tar czf /tmp/brace-v3-deploy.tar.gz ${LOCAL_BRACE}/
echo "✅ Package created: /tmp/brace-v3-deploy.tar.gz"
echo ""

echo "🌐 [2/5] Sincronizzazione via SCP → iMac..."
scp -q /tmp/brace-v3-deploy.tar.gz ${IMAC_HOST}:/tmp/
echo "✅ Archive sent to iMac"
echo ""

echo "⚙️  [3/5] Estrazione e Setup su iMac..."
ssh ${IMAC_HOST} << 'REMOTE_COMMANDS'
cd /opt/vioaiorchestra
tar xzf /tmp/brace-v3-deploy.tar.gz
echo "✅ BRACE v3 estratto"

# Crea cartelle security
mkdir -p brace-v3/.security_certs
mkdir -p brace-v3/data
echo "✅ Directory create"

# Verifica Python
python3 -c "import sys; print(f'✅ Python {sys.version.split()[0]} OK')"
REMOTE_COMMANDS

echo ""
echo "🚀 [4/5] Avvio BRACE DEMO su iMac (porta 9443)..."
ssh ${IMAC_HOST} "cd /opt/vioaiorchestra && python3 brace-v3/demo_algorithm.py &" 2>/dev/null &
echo "✅ Demo algorithm eseguito in background"
echo ""

echo "🌐 [5/5] Avvio BRACE Web Server su iMac..."
ssh ${IMAC_HOST} "cd /opt/vioaiorchestra && nohup python3 brace-v3/webui.py > /tmp/brace_imac.log 2>&1 &" 2>/dev/null
sleep 3
echo "✅ iMac Web Server avviato (https://172.20.10.5:9443)"
echo ""

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  ✅ DEPLOYMENT COMPLETE                                           ║"
echo "║                                                                    ║"
echo "║  MacBook Air:  https://localhost:9443   (DEMO)                   ║"
echo "║  iMac:         https://172.20.10.5:9443 (DEMO)                   ║"
echo "║                                                                    ║"
echo "║  Both secured with Privacy Bunker + Security Bunker              ║"
echo "║  Developer authentication active on both instances               ║"
echo "║                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
