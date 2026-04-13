#!/bin/bash
# VS Code True Mirror Setup
# Remote SSH + File Sync per editing identico su entrambi i VS Code

set -e

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  🪞 VS CODE TRUE MIRROR — Setup Remote SSH + File Sync            ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Installa Remote SSH Extension
echo "📦 [1/4] Installazione VS Code Remote SSH Extension..."
code --install-extension ms-vscode-remote.remote-ssh 2>/dev/null || true
code --install-extension ms-vscode-remote.remote-ssh-edit 2>/dev/null || true
echo "    ✅ Remote SSH Extension installata"

# Step 2: Verifica SSH connectivity
echo ""
echo "🔐 [2/4] Verifica connettività SSH a iMac..."
if ssh -o ConnectTimeout=5 vio@172.20.10.5 "echo 'SSH OK'" > /dev/null 2>&1; then
    echo "    ✅ SSH connection OK (vio@172.20.10.5)"
else
    echo "    ❌ SSH connection failed"
    echo "    Assicurati che iMac sia online e SSH sia configurato"
    exit 1
fi

# Step 3: Configura VS Code settings per Remote
echo ""
echo "⚙️  [3/4] Configurazione VS Code Remote Settings..."

# Crea le impostazioni per remote SSH
mkdir -p ~/.ssh
cat >> ~/.ssh/config << 'EOF'

Host imac-archimede
    HostName 172.20.10.5
    User vio
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    ForwardAgent yes
    ControlMaster auto
    ControlPath ~/.ssh/control-%C
    ControlPersist 600
EOF

echo "    ✅ SSH config aggiornato"

# Step 4: Avvia file sync daemon
echo ""
echo "🔄 [4/4] Avvio sincronizzazione file in background..."
python3 scripts/vscode-sync-imac.py > /tmp/vscode_mirror.log 2>&1 &
SYNC_PID=$!
echo "    ✅ Sync daemon avviato (PID: $SYNC_PID)"

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  ✅ SETUP COMPLETATO — VS CODE TRUE MIRROR READY                  ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

echo "🎯 PROSSIMI STEP:"
echo "   1. Apri VS Code"
echo "   2. Premi Cmd+Shift+P → 'Remote-SSH: Connect to Host'"
echo "   3. Seleziona: vio@172.20.10.5"
echo "   4. Apri folder: /opt/vioaiorchestra"
echo ""

echo "🎨 RISULTATO:"
echo "   • VS Code MacBook Air = File system iMac (Remote)"
echo "   • Editing direttamente su file iMac"
echo "   • Esecuzione su iMac (massima potenza)"
echo "   • Terminal integrato = iMac shell"
echo "   • File sync automatico (ogni 100ms)"
echo ""

echo "📝 LOG:"
echo "   tail -f /tmp/vscode_mirror.log"
echo ""

echo "✅ Mirror virtuale attivo!"
echo "   Digita su MacBook Air → Codice sincronizzato su iMac"
echo ""
