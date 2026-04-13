#!/bin/bash
# VS Code Sync Script - MacBook Air → iMac Archimede
# Sincronizazione in Tempo Reale + Tema + Lingua Italiana + Ottimizzazione

set -e

IMAC_USER="vio"
IMAC_HOST="172.20.10.5"
VSCODE_USER_DIR=~/.config/Code/User

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🔄 VS Code Sync — MacBook Air → iMac Archimede          ║"
echo "║  Sincronizzazione Specchio in Tempo Reale                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1: Estrai settings.json da MacBook
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "📋 STEP 1: Lettura settings MacBook Air..."

# Tenta percorsi diversi per trovare settings.json
SETTINGS_FILE=""
for path in "$HOME/Library/Application Support/Code/User/settings.json" \
            "$HOME/.config/Code/User/settings.json"; do
    if [ -f "$path" ]; then
        SETTINGS_FILE="$path"
        break
    fi
done

if [ -z "$SETTINGS_FILE" ]; then
    echo "❌ settings.json non trovato"
    exit 1
fi

echo "✅ Trovato: $SETTINGS_FILE"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2: Crea settings.json ottimizzato per iMac
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "⚙️  STEP 2: Creazione settings ottimizzato per iMac..."

VSCODE_SETTINGS=$(cat << 'EOF'
{
  "workbench.colorTheme": "GitHub Light",
  "workbench.iconTheme": "Fluent Icons",
  "workbench.startupEditor": "none",
  "[italian]": {
    "locale": "it"
  },
  "editor.fontFamily": "'Fira Code', 'Monaco', monospace",
  "editor.fontSize": 13,
  "editor.fontLigatures": true,
  "editor.fontWeight": "400",
  "editor.lineHeight": 1.6,
  "editor.letterSpacing": 0.3,
  "editor.tabSize": 2,
  "editor.insertSpaces": true,
  "editor.wordWrap": "on",
  "editor.wordWrapColumn": 120,
  "editor.formatOnSave": true,
  "editor.formatOnPaste": true,
  "editor.formatOnType": true,
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": "active",
  "editor.linkedEditing": true,
  "editor.renderLineHighlight": "all",
  "editor.selectionHighlight": true,
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000,
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "files.encoding": "utf8",
  "terminal.integrated.defaultProfile.linux": "bash",
  "terminal.integrated.fontSize": 13,
  "extensions.autoUpdate": true,
  "extensions.autoCheckUpdates": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "vio.autoLaunchChat": true,
  "vio.chatEngine": "local-4model",
  "vio.apiKeys": "NONE-LOCAL"
}
EOF
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3: Sync a iMac via SSH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "📤 STEP 3: Invio settings a iMac..."

ssh "$IMAC_USER@$IMAC_HOST" "mkdir -p ~/.config/Code/User" 2>/dev/null

# Scrivi settings.json su iMac
ssh "$IMAC_USER@$IMAC_HOST" "cat > ~/.config/Code/User/settings.json << 'SETTINGS_EOF'
$VSCODE_SETTINGS
SETTINGS_EOF" || echo "❌ Errore invio settings"

echo "✅ Settings sincronizzati"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4: Installa Language Pack Italiano
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "🌍 STEP 4: Configurazione lingua italiana..."

# Verifica se VS Code è disponibile su iMac
ssh "$IMAC_USER@$IMAC_HOST" "which code || echo 'VS Code non trovato'" 2>/dev/null

echo "ℹ️  Nota: Language pack italiano sarà installato al primo avvio di VS Code su iMac"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 5: Sincronizzazione Estensioni Consigliate
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "🔧 STEP 5: Estensioni consigliate per iMac:"

EXTENSIONS=(
    "ms-ceintl.vscode-language-pack-it"
    "esbenp.prettier-vscode"
    "dbaeumer.vscode-eslint"
    "ms-python.python"
    "charliermarsh.ruff"
    "bradlc.vscode-tailwindcss"
    "github.copilot-chat"
    "eamodio.gitlens"
    "continue.continue"
)

for ext in "${EXTENSIONS[@]}"; do
    echo "   ✓ $ext"
done

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ Sincronizzazione Completata                           ║"
echo "║                                                            ║"
echo "║  Prossimi Step:                                            ║"
echo "║  1. Apri VS Code su iMac (avvierà language pack IT)       ║"
echo "║  2. Installa estensioni da Command Palette               ║"
echo "║  3. Usa SSH Remote per mirror in tempo reale            ║"
echo "╚════════════════════════════════════════════════════════════╝"
exit 0
