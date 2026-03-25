#!/usr/bin/env bash
# ============================================================
# VIO 83 AI ORCHESTRA — VS Code AI Powerhouse Setup
#
# Installa e configura TUTTE le estensioni AI per VS Code
# con Ollama come backend locale + multi-model routing.
#
# Estensioni AI installate:
#   1. Continue          — Chat + Autocomplete + Context (principale)
#   2. Twinny            — Copilot-like gratuito, autocomplete locale
#   3. Ollama Agent      — Agente autonomo (crea/modifica file)
#   4. CodeGPT           — Multi-provider chat panel
#   5. GitHub Copilot    — Cloud AI (già installato)
#
# Eseguire: bash scripts/setup/vscode_ai_powerhouse.sh
# ============================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  VIO 83 — VS Code AI Powerhouse Setup                  ║${NC}"
echo -e "${CYAN}║  Multi-AI, Multi-Model, Multi-Session Development      ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================
# STEP 1: Verifica prerequisiti
# ============================================================
echo -e "${BLUE}[STEP 1/5]${NC} Verifica prerequisiti..."

if ! command -v code &>/dev/null; then
    echo -e "${RED}  ✗ Comando 'code' non trovato. Installa Shell Command da VS Code:${NC}"
    echo "    Cmd+Shift+P → 'Shell Command: Install code command in PATH'"
    exit 1
fi
echo -e "${GREEN}  ✓ VS Code CLI disponibile${NC}"

if ! command -v ollama &>/dev/null; then
    echo -e "${RED}  ✗ Ollama non installato. Installa da https://ollama.ai${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Ollama installato${NC}"

if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo -e "${YELLOW}  Avvio Ollama...${NC}"
    ollama serve &>/dev/null &
    sleep 3
fi
echo -e "${GREEN}  ✓ Ollama in esecuzione${NC}"

echo ""

# ============================================================
# STEP 2: Installa estensioni AI
# ============================================================
echo -e "${BLUE}[STEP 2/5]${NC} Installazione estensioni AI..."

AI_EXTENSIONS=(
    # AI Chat & Autocomplete
    "continue.continue"                          # Continue — principal AI chat + autocomplete
    "rjmacarthy.twinny"                          # Twinny — Copilot-like locale, gratis
    "NishantUnavane.Ollama-Ai-agent"             # Ollama Agent — agente autonomo
    "danielsanchez-pg.dscodegpt"                 # CodeGPT — multi-provider chat

    # Già installate (verifica)
    "github.copilot"                             # GitHub Copilot
    "github.copilot-chat"                        # GitHub Copilot Chat
)

INSTALLED_EXT=$(code --list-extensions 2>/dev/null)

for ext in "${AI_EXTENSIONS[@]}"; do
    if echo "$INSTALLED_EXT" | grep -qi "$ext"; then
        echo -e "${GREEN}  ✓ $ext — già installata${NC}"
    else
        echo -e "${YELLOW}  ↓ $ext — installazione...${NC}"
        if code --install-extension "$ext" --force 2>/dev/null; then
            echo -e "${GREEN}  ✓ $ext — installata${NC}"
        else
            echo -e "${RED}  ✗ $ext — installazione fallita (installa manualmente)${NC}"
        fi
    fi
done

echo ""

# ============================================================
# STEP 3: Configura Continue con Smart Routing
# ============================================================
echo -e "${BLUE}[STEP 3/5]${NC} Configurazione Continue Smart Routing..."

CONTINUE_DIR="$HOME/.continue"
mkdir -p "$CONTINUE_DIR"

# Backup
if [ -f "$CONTINUE_DIR/config.json" ]; then
    cp "$CONTINUE_DIR/config.json" "$CONTINUE_DIR/config.json.backup-$(date +%Y%m%d_%H%M%S)"
fi

cat > "$CONTINUE_DIR/config.json" << 'CONFIGEOF'
{
  "models": [
    {
      "title": "DeepSeek-R1 — Reasoning",
      "provider": "ollama",
      "model": "deepseek-r1",
      "apiBase": "http://localhost:11434",
      "systemMessage": "You are a senior software architect. Reason step by step. Be precise and thorough."
    },
    {
      "title": "CodeLlama — Code Expert",
      "provider": "ollama",
      "model": "codellama",
      "apiBase": "http://localhost:11434",
      "systemMessage": "You are an expert code assistant. Write clean, production-ready code with types and error handling."
    },
    {
      "title": "Mistral 7B — Multilingual",
      "provider": "ollama",
      "model": "mistral",
      "apiBase": "http://localhost:11434",
      "systemMessage": "You are a multilingual technical assistant. Respond in the user's language. Be professional and precise."
    },
    {
      "title": "Qwen 2.5 Coder — Fast Code",
      "provider": "ollama",
      "model": "qwen2.5-coder:3b",
      "apiBase": "http://localhost:11434",
      "systemMessage": "You are a fast code assistant. Provide concise, working solutions."
    },
    {
      "title": "Llama 3 8B — General",
      "provider": "ollama",
      "model": "llama3",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Llama 3.2 3B — Quick Chat",
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
  "contextProviders": [
    {"name": "code", "params": {}},
    {"name": "docs", "params": {}},
    {"name": "diff", "params": {}},
    {"name": "terminal", "params": {}},
    {"name": "problems", "params": {}},
    {"name": "folder", "params": {}},
    {"name": "codebase", "params": {}}
  ],
  "slashCommands": [
    {"name": "edit", "description": "Edit selected code"},
    {"name": "comment", "description": "Add comments to code"},
    {"name": "share", "description": "Export to markdown"},
    {"name": "cmd", "description": "Generate terminal command"},
    {"name": "commit", "description": "Generate commit message"}
  ],
  "customCommands": [
    {"name": "test", "prompt": "Write comprehensive unit tests for the selected code. Cover edge cases.", "description": "Generate unit tests"},
    {"name": "fix", "prompt": "Identify and fix all bugs in the selected code. Explain what was wrong.", "description": "Fix bugs"},
    {"name": "optimize", "prompt": "Optimize the selected code for performance and readability.", "description": "Optimize code"},
    {"name": "refactor", "prompt": "Refactor following SOLID principles. Maintain same behavior.", "description": "Refactor code"},
    {"name": "security", "prompt": "Security audit: check OWASP top 10 vulnerabilities.", "description": "Security audit"},
    {"name": "doc", "prompt": "Generate comprehensive documentation with JSDoc/docstrings.", "description": "Generate docs"},
    {"name": "vio", "prompt": "Analyze current context and suggest next best action for VIO AI Orchestra.", "description": "VIO assistant"}
  ],
  "allowAnonymousTelemetry": false,
  "docs": []
}
CONFIGEOF

echo -e "${GREEN}  ✓ Continue config.json — 6 modelli + 7 comandi custom${NC}"
echo ""

# ============================================================
# STEP 4: Configura Twinny per autocomplete parallelo
# ============================================================
echo -e "${BLUE}[STEP 4/5]${NC} Configurazione Twinny autocomplete..."

# Twinny si configura via VS Code settings
# Aggiungiamo le impostazioni al workspace settings
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VSCODE_SETTINGS="$PROJECT_ROOT/.vscode/settings.json"

if [ -f "$VSCODE_SETTINGS" ]; then
    # Verifica se le impostazioni Twinny sono già presenti
    if ! grep -q "twinny" "$VSCODE_SETTINGS" 2>/dev/null; then
        # Aggiungi le impostazioni Twinny prima dell'ultima }
        python3 -c "
import json

with open('$VSCODE_SETTINGS', 'r') as f:
    content = f.read()
    # Remove trailing comments for JSON parsing
    lines = content.split('\n')
    clean_lines = [l for l in lines if not l.strip().startswith('//')]
    clean_content = '\n'.join(clean_lines)

try:
    settings = json.loads(clean_content)
except:
    # If JSON parsing fails, just report
    print('  ⚠ Cannot auto-edit settings.json (comments in JSON)')
    exit(0)

# Add Twinny settings
settings['twinny.fimModelName'] = 'qwen2.5-coder:3b'
settings['twinny.chatModelName'] = 'codellama'
settings['twinny.apiHostname'] = 'localhost'
settings['twinny.apiPort'] = 11434
settings['twinny.apiProvider'] = 'ollama'
settings['twinny.enabled'] = True
settings['twinny.autoSuggestEnabled'] = True

with open('$VSCODE_SETTINGS', 'w') as f:
    json.dump(settings, f, indent=2)

print('  ✓ Twinny settings aggiunte a .vscode/settings.json')
" 2>/dev/null || echo -e "${YELLOW}  ⚠ Impostazioni Twinny: aggiungi manualmente in VS Code Settings${NC}"
    else
        echo -e "${GREEN}  ✓ Twinny settings già presenti${NC}"
    fi
fi

echo ""

# ============================================================
# STEP 5: Verifica modelli Ollama e riepilogo
# ============================================================
echo -e "${BLUE}[STEP 5/5]${NC} Verifica modelli Ollama..."

REQUIRED_MODELS=("qwen2.5-coder:3b" "codellama" "deepseek-r1" "mistral" "llama3" "llama3.2:3b" "nomic-embed-text")
INSTALLED=$(ollama list 2>/dev/null | awk 'NR>1 {print $1}' | sed 's/:latest$//')

for model in "${REQUIRED_MODELS[@]}"; do
    base="${model%:latest}"
    if echo "$INSTALLED" | grep -qF "$base"; then
        echo -e "${GREEN}  ✓ $model${NC}"
    else
        echo -e "${YELLOW}  ↓ $model — installazione...${NC}"
        ollama pull "$model" 2>/dev/null && echo -e "${GREEN}  ✓ $model installato${NC}" || echo -e "${RED}  ✗ $model — riprova: ollama pull $model${NC}"
    fi
done

echo ""

# ============================================================
# RIEPILOGO FINALE
# ============================================================
echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║            SETUP COMPLETATO                            ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}ESTENSIONI AI ATTIVE:${NC}"
echo "  1. Continue      → Cmd+L     — Chat principale, 6 modelli, 7 comandi"
echo "  2. Twinny        → Auto      — Autocomplete inline (come Copilot)"
echo "  3. Ollama Agent  → Sidebar   — Agente autonomo (crea/modifica file)"
echo "  4. CodeGPT       → Sidebar   — Chat multi-provider alternativa"
echo "  5. Copilot       → Tab       — Cloud AI (quando online)"
echo "  6. Copilot Chat  → Ctrl+Cmd+I — Chat cloud AI"
echo ""
echo -e "${BLUE}COME USARLI IN PARALLELO:${NC}"
echo "  • Apri Continue:     Cmd+L"
echo "  • Apri Copilot Chat: Ctrl+Cmd+I"
echo "  • Apri Ollama Agent: Click icona nella Sidebar sinistra"
echo "  • Apri CodeGPT:      Click icona nella Sidebar sinistra"
echo "  • Twinny:            Autocomplete automatico mentre digiti"
echo ""
echo -e "${BLUE}MODELLI E SPECIALIZZAZIONI:${NC}"
echo "  DeepSeek-R1  (5.2GB) → Ragionamento, analisi, debugging complesso"
echo "  CodeLlama    (3.8GB) → Code generation, refactoring, review"
echo "  Mistral      (4.4GB) → Multilingue, documentazione, italiano"
echo "  Qwen Coder   (1.9GB) → Autocomplete veloce, code rapido"
echo "  Llama 3      (4.7GB) → General purpose, chat completa"
echo "  Llama 3.2    (2.0GB) → Chat veloce, risposte brevi"
echo ""
echo -e "${YELLOW}NOTA IMPORTANTE:${NC}"
echo "  Con 7 modelli caricati, Ollama usa ~22GB RAM."
echo "  Su MacBook Air M1 (8GB RAM): carica max 2-3 modelli alla volta."
echo "  Ollama gestisce automaticamente lo swap dei modelli in RAM."
echo ""
echo -e "${GREEN}Riavvia VS Code per attivare tutte le estensioni.${NC}"
