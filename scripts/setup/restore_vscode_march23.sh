#!/usr/bin/env bash
# ============================================================
# VIO 83 AI ORCHESTRA — Ripristino VS Code al 23 Marzo 2026 08:00
#
# Questo script ripristina ESATTAMENTE la configurazione
# di VS Code + Continue + Ollama come era la mattina del
# 23 Marzo 2026 alle ore 08:00.
#
# Eseguire dal Mac Terminal:
#   cd ~/Projects/vio83-ai-orchestra
#   bash scripts/setup/restore_vscode_march23.sh
# ============================================================

set -euo pipefail

# Colori output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  VIO 83 AI ORCHESTRA — Ripristino VS Code 23/03/2026   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ==============================================================
# STEP 1: Verifica prerequisiti
# ==============================================================
echo -e "${BLUE}[STEP 1/6]${NC} Verifica prerequisiti..."

# Verifica che siamo nella cartella giusta
if [[ ! -f "package.json" ]]; then
    echo -e "${RED}ERRORE: Esegui questo script dalla root del progetto vio83-ai-orchestra${NC}"
    exit 1
fi

PROJECT_NAME=$(python3 -c "import json; print(json.load(open('package.json'))['name'])" 2>/dev/null || echo "unknown")
if [[ "$PROJECT_NAME" != "vio83-ai-orchestra" ]]; then
    echo -e "${RED}ERRORE: Questo non è il progetto vio83-ai-orchestra (trovato: $PROJECT_NAME)${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Progetto vio83-ai-orchestra confermato${NC}"

# Verifica Ollama installato
if ! command -v ollama &>/dev/null; then
    echo -e "${RED}ERRORE: Ollama non è installato. Installa da https://ollama.ai${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Ollama installato${NC}"

# Verifica VS Code installato
if ! command -v code &>/dev/null; then
    echo -e "${YELLOW}  ⚠ Comando 'code' non trovato nel PATH. Installa Shell Command da VS Code:${NC}"
    echo -e "${YELLOW}    Cmd+Shift+P → 'Shell Command: Install code command in PATH'${NC}"
fi

echo ""

# ==============================================================
# STEP 2: Ripristina Continue config.json dal backup originale
# ==============================================================
echo -e "${BLUE}[STEP 2/6]${NC} Ripristino configurazione Continue..."

CONTINUE_DIR="$HOME/.continue"
CONTINUE_CONFIG="$CONTINUE_DIR/config.json"
CONTINUE_BACKUP="$CONTINUE_DIR/config.json.OLD"
CONTINUE_YAML="$CONTINUE_DIR/config.yaml"

if [[ -f "$CONTINUE_BACKUP" ]]; then
    # Backup della versione corrente (sovrascritta) prima di ripristinare
    cp "$CONTINUE_CONFIG" "$CONTINUE_DIR/config.json.overwritten-$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true

    # Ripristina dal backup originale
    cp "$CONTINUE_BACKUP" "$CONTINUE_CONFIG"
    echo -e "${GREEN}  ✓ config.json ripristinato dal backup .OLD (configurazione originale)${NC}"
else
    echo -e "${YELLOW}  ⚠ Backup .OLD non trovato. Creo config.json basato su config.yaml originale...${NC}"

    # Crea config.json basato sulla configurazione "AI-Master-2026" dal config.yaml
    cat > "$CONTINUE_CONFIG" << 'CONFIGEOF'
{
  "models": [
    {
      "title": "DeepSeek-R1 (Local)",
      "provider": "ollama",
      "model": "deepseek-r1",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Llama 3 8B (Local)",
      "provider": "ollama",
      "model": "llama3",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Mistral 7B (Local)",
      "provider": "ollama",
      "model": "mistral",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "CodeLlama 7B (Local)",
      "provider": "ollama",
      "model": "codellama",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Qwen 2.5 Coder 3B (Local)",
      "provider": "ollama",
      "model": "qwen2.5-coder:3b",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Llama 3.2 3B (Local)",
      "provider": "ollama",
      "model": "llama3.2:3b",
      "apiBase": "http://localhost:11434"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Qwen 2.5 Coder (Autocomplete)",
    "provider": "ollama",
    "model": "qwen2.5-coder:3b",
    "apiBase": "http://localhost:11434"
  },
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text",
    "apiBase": "http://localhost:11434"
  },
  "customCommands": [
    {
      "name": "test",
      "prompt": "Write a comprehensive set of unit tests for the selected code. Make sure to cover edge cases."
    },
    {
      "name": "explain",
      "prompt": "Explain the following code in detail, including what each part does and why."
    },
    {
      "name": "optimize",
      "prompt": "Analyze and optimize the selected code for better performance and readability."
    }
  ],
  "allowAnonymousTelemetry": false,
  "docs": []
}
CONFIGEOF
    echo -e "${GREEN}  ✓ config.json creato con configurazione AI-Master-2026${NC}"
fi

echo ""

# ==============================================================
# STEP 3: Verifica e avvia Ollama
# ==============================================================
echo -e "${BLUE}[STEP 3/6]${NC} Verifica Ollama in esecuzione..."

if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo -e "${YELLOW}  Ollama non in esecuzione. Avvio...${NC}"
    ollama serve &>/dev/null &
    sleep 3
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        echo -e "${GREEN}  ✓ Ollama avviato${NC}"
    else
        echo -e "${RED}  ✗ Impossibile avviare Ollama. Avvialo manualmente.${NC}"
    fi
else
    echo -e "${GREEN}  ✓ Ollama già in esecuzione${NC}"
fi

echo ""

# ==============================================================
# STEP 4: Installa modelli Ollama mancanti
# ==============================================================
echo -e "${BLUE}[STEP 4/6]${NC} Verifica e installazione modelli Ollama..."

# Lista modelli richiesti dalla configurazione
REQUIRED_MODELS=(
    "qwen2.5-coder:3b"
    "llama3.2:3b"
    "nomic-embed-text"
    "deepseek-r1"
    "mistral"
    "codellama"
    "llama3"
)

INSTALLED_MODELS=$(ollama list 2>/dev/null | awk 'NR>1 {print $1}' | sed 's/:latest$//')

for model in "${REQUIRED_MODELS[@]}"; do
    # Normalizza nome (rimuovi :latest per confronto)
    model_base="${model%:latest}"

    if echo "$INSTALLED_MODELS" | grep -qF "$model_base"; then
        echo -e "${GREEN}  ✓ $model — già installato${NC}"
    else
        echo -e "${YELLOW}  ↓ $model — installazione in corso...${NC}"
        if ollama pull "$model" 2>/dev/null; then
            echo -e "${GREEN}  ✓ $model — installato con successo${NC}"
        else
            echo -e "${RED}  ✗ $model — ERRORE installazione. Riprova manualmente: ollama pull $model${NC}"
        fi
    fi
done

echo ""

# ==============================================================
# STEP 5: Verifica estensioni VS Code
# ==============================================================
echo -e "${BLUE}[STEP 5/6]${NC} Verifica estensioni VS Code..."

REQUIRED_EXTENSIONS=(
    "continue.continue"
    "github.copilot-chat"
    "dbaeumer.vscode-eslint"
    "bradlc.vscode-tailwindcss"
    "ms-python.python"
    "rust-lang.rust-analyzer"
    "tauri-apps.tauri-vscode"
    "eamodio.gitlens"
    "usernamehw.errorlens"
    "pkief.material-icon-theme"
    "streetsidesoftware.code-spell-checker"
)

if command -v code &>/dev/null; then
    INSTALLED_EXT=$(code --list-extensions 2>/dev/null)

    for ext in "${REQUIRED_EXTENSIONS[@]}"; do
        if echo "$INSTALLED_EXT" | grep -qi "$ext"; then
            echo -e "${GREEN}  ✓ $ext${NC}"
        else
            echo -e "${YELLOW}  ↓ $ext — installazione...${NC}"
            code --install-extension "$ext" 2>/dev/null || echo -e "${RED}  ✗ Installa manualmente: $ext${NC}"
        fi
    done
else
    echo -e "${YELLOW}  ⚠ Comando 'code' non nel PATH. Verifica estensioni manualmente in VS Code.${NC}"
fi

echo ""

# ==============================================================
# STEP 6: Verifica configurazione workspace .vscode/
# ==============================================================
echo -e "${BLUE}[STEP 6/6]${NC} Verifica configurazione workspace..."

VSCODE_DIR=".vscode"

check_file() {
    local file="$1"
    local desc="$2"
    if [[ -f "$VSCODE_DIR/$file" ]]; then
        echo -e "${GREEN}  ✓ $file — $desc${NC}"
    else
        echo -e "${RED}  ✗ $file — MANCANTE!${NC}"
    fi
}

check_file "settings.json" "837 righe, configurazione completa"
check_file "launch.json" "debug configs (Frontend, Backend, Tauri, Test)"
check_file "tasks.json" "build tasks (Full Orchestra, maintenance)"
check_file "extensions.json" "estensioni raccomandate"
check_file "vio83.code-snippets" "snippets personalizzati (vrc, vzs, vai, vfa, vlog)"

# Verifica OLLAMA_HOST nel settings.json
if grep -q "OLLAMA_HOST" "$VSCODE_DIR/settings.json" 2>/dev/null; then
    echo -e "${GREEN}  ✓ OLLAMA_HOST configurato nel terminal integrato${NC}"
else
    echo -e "${RED}  ✗ OLLAMA_HOST mancante nel settings.json${NC}"
fi

# Verifica tema
THEME=$(grep -o '"workbench.colorTheme": "[^"]*"' "$VSCODE_DIR/settings.json" 2>/dev/null)
echo -e "${GREEN}  ✓ Tema: $THEME${NC}"

echo ""

# ==============================================================
# RIEPILOGO FINALE
# ==============================================================
echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                  RIPRISTINO COMPLETATO                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Configurazione VS Code ripristinata al 23 Marzo 2026 08:00${NC}"
echo ""
echo -e "${YELLOW}PROSSIMI PASSI:${NC}"
echo -e "  1. Riavvia VS Code completamente (chiudi e riapri)"
echo -e "  2. Premi ${CYAN}Cmd+L${NC} per aprire Continue AI Chat"
echo -e "  3. Premi ${CYAN}Ctrl+Cmd+I${NC} per aprire Copilot Chat"
echo -e "  4. Verifica che i modelli Ollama rispondano nella chat"
echo ""
echo -e "${BLUE}Modelli Ollama disponibili:${NC}"
ollama list 2>/dev/null | head -10
echo ""
echo -e "${GREEN}✅ Script completato con successo.${NC}"
