#!/bin/bash
# ============================================================
# VIO 83 AI ORCHESTRA — SETUP COMPLETO MAC
# Eseguire su Mac con: chmod +x scripts/setup-vio-complete.sh && ./scripts/setup-vio-complete.sh
# ============================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_DIR="$HOME/Projects/vio83-ai-orchestra"

log_ok()   { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_err()  { echo -e "${RED}❌ $1${NC}"; }
log_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
log_step() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BLUE}🔧 $1${NC}"; echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ============================================================
# FASE 1: HOMEBREW + STRUMENTI BASE
# ============================================================
log_step "FASE 1/8: Homebrew + Strumenti Base Mac"

if ! command -v brew &>/dev/null; then
  log_info "Installando Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
  log_ok "Homebrew installato"
else
  log_ok "Homebrew già presente"
  brew update
fi

BREW_PACKAGES=(
  "git"           # Version control
  "gh"            # GitHub CLI — per PR, issues, releases da terminale
  "node"          # Node.js LTS (per frontend React + Tauri CLI)
  "python@3.12"   # Python stabile (3.14 è troppo nuovo per alcune deps)
  "rust"          # Rust toolchain (per compilare Tauri)
  "ollama"        # AI locale — modelli LLM
  "pm2"           # Process manager per backend
  "jq"            # JSON processor CLI
  "ripgrep"       # Ricerca veloce nel codice
  "fd"            # File finder veloce
  "bat"           # cat con syntax highlighting
  "fzf"           # Fuzzy finder
  "lazygit"       # Git TUI interattivo
  "wget"          # HTTP downloads
  "htop"          # Monitor processi
  "tree"          # Visualizza directory
  "sqlite"        # CLI per database SQLite
)

for pkg in "${BREW_PACKAGES[@]}"; do
  if brew list "$pkg" &>/dev/null; then
    log_ok "$pkg già installato"
  else
    log_info "Installando $pkg..."
    brew install "$pkg" || log_warn "Fallito: $pkg (continuo)"
  fi
done

# ============================================================
# FASE 2: RUST + TAURI PREREQUISITES
# ============================================================
log_step "FASE 2/8: Rust + Tauri Build Prerequisites"

if ! command -v rustc &>/dev/null; then
  log_info "Installando Rust via rustup..."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  source "$HOME/.cargo/env"
  log_ok "Rust installato"
else
  log_ok "Rust già presente: $(rustc --version)"
  rustup update stable
fi

# Tauri richiede Xcode Command Line Tools su macOS
if ! xcode-select -p &>/dev/null; then
  log_info "Installando Xcode Command Line Tools..."
  xcode-select --install
  log_warn "Attendi il completamento dell'installazione Xcode, poi ri-esegui lo script"
else
  log_ok "Xcode CLI Tools presenti"
fi

# ============================================================
# FASE 3: NODE.JS + DIPENDENZE FRONTEND
# ============================================================
log_step "FASE 3/8: Node.js + Frontend Dependencies"

cd "$PROJECT_DIR"

# Verifica Node.js versione
NODE_VER=$(node --version 2>/dev/null || echo "none")
log_info "Node.js: $NODE_VER"

if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-lock.json" ]; then
  log_info "Installando dipendenze npm..."
  npm install
  log_ok "npm install completato"
else
  log_ok "node_modules aggiornato"
fi

# Installa Tauri CLI globale
if ! npx tauri --version &>/dev/null 2>&1; then
  log_info "Tauri CLI sarà disponibile via npx (già in devDependencies)"
fi
log_ok "Tauri CLI: $(npx tauri --version 2>/dev/null || echo 'via npx')"

# ============================================================
# FASE 4: PYTHON + DIPENDENZE BACKEND
# ============================================================
log_step "FASE 4/8: Python + Backend Dependencies"

# Usa Python 3.12 per compatibilità massima (ChromaDB, scikit-optimize)
PYTHON_CMD="python3.12"
if ! command -v $PYTHON_CMD &>/dev/null; then
  PYTHON_CMD="python3"
fi
log_info "Python: $($PYTHON_CMD --version)"

# Crea virtual environment se non esiste
if [ ! -d ".venv-prod" ]; then
  log_info "Creando virtual environment con $PYTHON_CMD..."
  $PYTHON_CMD -m venv .venv-prod
  log_ok "Virtual environment creato: .venv-prod"
fi

source .venv-prod/bin/activate
log_info "Attivato venv: $(python --version)"

# Installa tutte le dipendenze
pip install --upgrade pip
pip install -r requirements.txt
log_ok "Tutte le dipendenze Python installate"

# Verifica moduli critici
python -c "import fastapi; print(f'  FastAPI: {fastapi.__version__}')"
python -c "import numpy; print(f'  NumPy: {numpy.__version__}')"
python -c "import argon2; print(f'  Argon2: OK')"
python -c "import httpx; print(f'  HTTPX: {httpx.__version__}')"
log_ok "Tutti i moduli critici verificati"

# ============================================================
# FASE 5: OLLAMA + MODELLI AI LOCALI
# ============================================================
log_step "FASE 5/8: Ollama + Modelli AI Locali"

# Avvia Ollama se non gira
if ! pgrep -x ollama &>/dev/null; then
  log_info "Avviando Ollama..."
  ollama serve &>/dev/null &
  sleep 3
fi

# Modelli essenziali per VIO AI Orchestra
OLLAMA_MODELS=(
  "gemma2:2b"          # Chat veloce, default locale
  "nomic-embed-text"   # Embeddings per VectorEngine (CRITICO!)
  "llama3.2:3b"        # Alternativa performante
  "qwen2.5:3b"         # Ottimo per code
  "phi3:mini"          # Ultra-leggero per classificazione
)

for model in "${OLLAMA_MODELS[@]}"; do
  if ollama list 2>/dev/null | grep -q "$(echo $model | cut -d: -f1)"; then
    log_ok "Modello $model già presente"
  else
    log_info "Scaricando $model..."
    ollama pull "$model" || log_warn "Fallito: $model"
  fi
done

# ============================================================
# FASE 6: GITHUB CLI + AUTENTICAZIONE
# ============================================================
log_step "FASE 6/8: GitHub CLI + Autenticazione"

if ! gh auth status &>/dev/null 2>&1; then
  log_warn "GitHub CLI non autenticato!"
  log_info "Esegui: gh auth login"
  log_info "  → Seleziona GitHub.com"
  log_info "  → Seleziona HTTPS"
  log_info "  → Autenticati con browser"
  echo ""
  read -p "Vuoi autenticarti ora? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    gh auth login
  fi
else
  log_ok "GitHub CLI autenticato: $(gh auth status 2>&1 | grep 'Logged in' | head -1)"
fi

# ============================================================
# FASE 7: VS CODE ESTENSIONI
# ============================================================
log_step "FASE 7/8: VS Code Estensioni Essenziali"

if command -v code &>/dev/null; then
  VSCODE_EXTENSIONS=(
    # === LINGUAGGI ===
    "ms-python.python"                    # Python IntelliSense
    "ms-python.vscode-pylance"            # Python type checker
    "ms-python.debugpy"                   # Python debugger
    "dbaeumer.vscode-eslint"              # ESLint per TypeScript
    "esbenp.prettier-vscode"              # Formatter universale
    "bradlc.vscode-tailwindcss"           # Tailwind CSS IntelliSense
    "rust-lang.rust-analyzer"             # Rust IntelliSense (per Tauri)

    # === TAURI ===
    "tauri-apps.tauri-vscode"             # Tauri dev tools

    # === AI ASSISTENTI ===
    "anthropic.claude-code"               # Claude Code per VS Code
    "github.copilot"                      # GitHub Copilot
    "github.copilot-chat"                 # Copilot Chat
    "continue.continue"                   # Continue.dev (Ollama locale)

    # === GIT ===
    "eamodio.gitlens"                     # Git supercharged
    "mhutchie.git-graph"                  # Git graph visuale

    # === DATABASE ===
    "alexcvzz.vscode-sqlite"             # SQLite viewer
    "qwtel.sqlite-viewer"                # SQLite file viewer

    # === PRODUTTIVITA ===
    "christian-kohler.path-intellisense"  # Path autocomplete
    "usernamehw.errorlens"               # Errori inline
    "ms-vscode.vscode-json"              # JSON tools
    "redhat.vscode-yaml"                 # YAML support
    "DotJoshJohnson.xml"                 # XML tools
    "streetsidesoftware.code-spell-checker" # Spell check
    "pkief.material-icon-theme"          # Icone

    # === API TESTING ===
    "humao.rest-client"                  # REST client in VS Code
    "rangav.vscode-thunder-client"       # Thunder Client (Postman alternativa)

    # === DOCKER (opzionale) ===
    "ms-azuretools.vscode-docker"        # Docker support
  )

  for ext in "${VSCODE_EXTENSIONS[@]}"; do
    if code --list-extensions 2>/dev/null | grep -qi "$(echo $ext | cut -d. -f2-)"; then
      log_ok "VS Code: $ext"
    else
      log_info "Installando VS Code ext: $ext"
      code --install-extension "$ext" --force 2>/dev/null || log_warn "Fallito: $ext"
    fi
  done

  # VS Code settings per il progetto
  mkdir -p .vscode
  cat > .vscode/settings.json << 'SETTINGS'
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv-prod/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "python.linting.enabled": true,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  },
  "[rust]": {
    "editor.defaultFormatter": "rust-lang.rust-analyzer"
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "eslint.validate": ["javascript", "typescript", "typescriptreact"],
  "tailwindCSS.includeLanguages": { "typescriptreact": "html" },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.DS_Store": true,
    "**/node_modules": true,
    "**/.venv*": true,
    "**/target": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/.venv*": true,
    "**/target": true,
    "**/dist": true
  },
  "editor.rulers": [100],
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true
}
SETTINGS
  log_ok "VS Code settings creati: .vscode/settings.json"

  # Launch config per debug
  cat > .vscode/launch.json << 'LAUNCH'
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Backend FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["backend.api.server:app", "--host", "0.0.0.0", "--port", "4000", "--reload"],
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env",
      "console": "integratedTerminal"
    },
    {
      "name": "Python: Run Tests",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v", "--tb=short"],
      "cwd": "${workspaceFolder}"
    },
    {
      "name": "Tauri: Dev",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "npx",
      "runtimeArgs": ["tauri", "dev"],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal"
    }
  ]
}
LAUNCH
  log_ok "VS Code launch.json creato"

  # Tasks per build veloce
  cat > .vscode/tasks.json << 'TASKS'
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Backend: Start",
      "type": "shell",
      "command": "source .venv-prod/bin/activate && uvicorn backend.api.server:app --host 0.0.0.0 --port 4000 --reload",
      "group": "build",
      "isBackground": true,
      "problemMatcher": []
    },
    {
      "label": "Frontend: Dev",
      "type": "shell",
      "command": "npm run dev",
      "group": "build",
      "isBackground": true
    },
    {
      "label": "Tauri: Dev",
      "type": "shell",
      "command": "npm run tauri:dev",
      "group": "build",
      "isBackground": true
    },
    {
      "label": "Tests: All",
      "type": "shell",
      "command": "source .venv-prod/bin/activate && python -m pytest tests/ -v && npm run test:frontend",
      "group": "test"
    },
    {
      "label": "Build: Release",
      "type": "shell",
      "command": "npm run release:gate",
      "group": "build"
    }
  ]
}
TASKS
  log_ok "VS Code tasks.json creato"
else
  log_warn "VS Code non trovato nel PATH"
  log_info "Installa: brew install --cask visual-studio-code"
  log_info "Poi aggiungi al PATH: Shell Command > Install 'code' in PATH"
fi

# ============================================================
# FASE 8: PM2 + AVVIO SERVIZI
# ============================================================
log_step "FASE 8/8: PM2 Ecosystem + Avvio Servizi"

# Installa PM2 globalmente
if ! command -v pm2 &>/dev/null; then
  npm install -g pm2
fi

# Crea ecosystem file per PM2
cat > ecosystem.config.cjs << 'PM2CONFIG'
module.exports = {
  apps: [
    {
      name: "vio-backend",
      script: ".venv-prod/bin/uvicorn",
      args: "backend.api.server:app --host 0.0.0.0 --port 4000 --workers 2",
      cwd: process.env.HOME + "/Projects/vio83-ai-orchestra",
      interpreter: "none",
      env: {
        PYTHONPATH: ".",
        PYTHONUNBUFFERED: "1",
      },
      watch: false,
      max_memory_restart: "500M",
      error_file: ".logs/pm2-backend-error.log",
      out_file: ".logs/pm2-backend-out.log",
      merge_logs: true,
      time: true,
    },
    {
      name: "vio-frontend",
      script: "npx",
      args: "vite --host 0.0.0.0 --port 5173",
      cwd: process.env.HOME + "/Projects/vio83-ai-orchestra",
      interpreter: "none",
      watch: false,
      error_file: ".logs/pm2-frontend-error.log",
      out_file: ".logs/pm2-frontend-out.log",
      merge_logs: true,
      time: true,
    },
  ],
};
PM2CONFIG
log_ok "PM2 ecosystem.config.cjs creato"

# ============================================================
# REPORT FINALE
# ============================================================
log_step "REPORT SETUP COMPLETO"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   VIO 83 AI ORCHESTRA — SETUP COMPLETATO            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Comandi rapidi:${NC}"
echo "  cd $PROJECT_DIR"
echo ""
echo "  # Avvia tutto con PM2:"
echo "  pm2 start ecosystem.config.cjs"
echo ""
echo "  # Oppure manualmente:"
echo "  source .venv-prod/bin/activate"
echo "  uvicorn backend.api.server:app --port 4000 --reload  # Backend"
echo "  npm run dev                                          # Frontend"
echo "  npm run tauri:dev                                    # App Desktop"
echo ""
echo "  # Test:"
echo "  npm run test:frontend      # Vitest"
echo "  python -m pytest tests/ -v # Pytest"
echo ""
echo "  # Build release:"
echo "  npm run release:gate       # TypeCheck + Lint + Test + Build + Tauri"
echo ""
echo -e "${YELLOW}⚠️  AZIONI MANUALI RICHIESTE:${NC}"
echo "  1. gh auth login              → Autenticazione GitHub"
echo "  2. Configurare API keys in .env (vedi sotto)"
echo "  3. Apple Developer account per firmare l'app (release.yml)"
echo ""
echo -e "${CYAN}API Keys da configurare in .env:${NC}"
echo "  GROQ_API_KEY        → https://console.groq.com/keys (GRATIS)"
echo "  OPENROUTER_API_KEY  → https://openrouter.ai/keys (GRATIS)"
echo "  TOGETHER_API_KEY    → https://api.together.xyz/settings/api-keys"
echo "  DEEPSEEK_API_KEY    → https://platform.deepseek.com/api_keys"
echo "  MISTRAL_API_KEY     → https://console.mistral.ai/api-keys/"
echo "  ANTHROPIC_API_KEY   → https://console.anthropic.com/settings/keys"
echo "  OPENAI_API_KEY      → https://platform.openai.com/api-keys"
echo "  GEMINI_API_KEY      → https://aistudio.google.com/app/apikey"
echo ""
log_ok "Setup completo! 🚀"
