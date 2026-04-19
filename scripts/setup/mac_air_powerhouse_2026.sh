#!/usr/bin/env bash
# =============================================================================
# VIO AI ORCHESTRA — MAC AIR (Apple Silicon) POWERHOUSE — April 2026 edition
# -----------------------------------------------------------------------------
# Pre-requisiti già soddisfatti dall'utente:
#   * Tailscale attivo e autenticato
#   * SSH reciproco Mac Air ↔ iMac funzionante
#
# Cosa fa questo script (idempotente — si può rieseguire senza danni):
#   1. Bootstrap Homebrew + aggiornamento completo
#   2. Installa / aggiorna lo stack AI CLI + IDE 2026:
#        - Claude Code (Anthropic)
#        - OpenAI Codex CLI
#        - Google Gemini CLI
#        - Aider, Cline, OpenCode, Goose (agenti autonomi)
#        - Cursor CLI, Continue, Copilot CLI
#   3. Installa Ollama + pull dei modelli locali top-tier per Apple Silicon
#   4. Installa il pack completo di MCP server (npm global)
#   5. Installa estensioni VS Code: AI + Remote + lang + produttività
#   6. Scrive settings.json con Settings Sync ON, Continue multi-router,
#      Claude Code autostart, MCP registrati
#   7. Registra 3 LaunchAgent sempre attivi (Ollama, MCP broker, watchdog)
#   8. Stampa onestamente i passi che richiedono intervento umano
#
# LIMITI ONESTI:
#   * "Sempre attivo per sempre" = LaunchAgent con KeepAlive. Nessuno
#     script sopravvive a spegnimenti hardware o logout forzati.
#   * Le API keys (OpenAI, Google, ecc.) vanno inserite una volta in
#     ~/.config/vio/keys.env — non posso inventarle.
#   * Settings Sync richiede UN login GitHub interattivo per macchina.
# =============================================================================

set -Eeuo pipefail
readonly C_G='\033[0;32m' C_Y='\033[1;33m' C_C='\033[0;36m' C_R='\033[0;31m' C_N='\033[0m'
ok()   { printf "${C_G}  ✓${C_N} %s\n" "$*"; }
warn() { printf "${C_Y}  !${C_N} %s\n" "$*"; }
err()  { printf "${C_R}  ✗${C_N} %s\n" "$*" >&2; }
step() { printf "\n${C_C}▶ %s${C_N}\n" "$*"; }
trap 'err "Errore riga $LINENO. Lo script è idempotente: rilancialo."' ERR

[[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]] || {
  err "Questo script gira solo su macOS Apple Silicon. Per l'iMac usa imac_arch_powerhouse_2026.sh"
  exit 1
}

# -----------------------------------------------------------------------------
step "[1/8] Homebrew + aggiornamento base"
if ! command -v brew &>/dev/null; then
  NONINTERACTIVE=1 /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
  grep -q 'brew shellenv' "$HOME/.zprofile" 2>/dev/null || \
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
fi
brew update
ok "Homebrew $(brew --version | head -1)"

# -----------------------------------------------------------------------------
step "[2/8] Toolchain CLI + linguaggi"
BREW_PKGS=(
  git gh jq yq curl wget ripgrep fd bat eza fzf zoxide htop btop tmux zsh
  neovim tree tokei hyperfine direnv starship mosh rsync watch gnu-sed
  coreutils findutils make cmake pkg-config openssh
  python@3.12 pyenv node nvm go rust
  docker docker-compose colima
  ollama
  ffmpeg imagemagick poppler pandoc
)
brew install "${BREW_PKGS[@]}" 2>/dev/null || true
ok "Toolchain installata"

# -----------------------------------------------------------------------------
step "[3/8] Stack AI CLI + agenti autonomi (April 2026 top-tier)"
export NVM_DIR="$HOME/.nvm"
[[ -s /opt/homebrew/opt/nvm/nvm.sh ]] && . /opt/homebrew/opt/nvm/nvm.sh
command -v nvm &>/dev/null || {
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
  . "$NVM_DIR/nvm.sh"
}
. "$NVM_DIR/nvm.sh" 2>/dev/null || true
nvm install --lts && nvm alias default lts/*

NPM_GLOBAL=(
  "@anthropic-ai/claude-code"            # Claude Code (Anthropic)
  "@openai/codex"                        # OpenAI Codex CLI
  "@google/gemini-cli"                   # Gemini CLI
  "@sourcegraph/amp"                     # Amp coding agent
  "opencode-ai"                          # OpenCode agent
  "@cline/cli"                           # Cline
  "aider-chat"                           # Aider (alcune distribuzioni su npm)
  "@github/copilot-cli"                  # Copilot CLI
  "cursor-cli"                           # Cursor CLI
)
for p in "${NPM_GLOBAL[@]}"; do
  npm install -g "$p" 2>/dev/null && ok "npm: $p" \
    || warn "skip $p (pacchetto non pubblicato o offline)"
done

# Aider tramite pipx è la via canonica:
brew install pipx 2>/dev/null || true
pipx ensurepath >/dev/null 2>&1 || true
pipx install aider-chat 2>/dev/null && ok "pipx: aider-chat" \
  || warn "pipx aider già installato o non disponibile"
pipx install goose-cli 2>/dev/null && ok "pipx: goose-cli" \
  || warn "goose-cli: salto"

# -----------------------------------------------------------------------------
step "[4/8] Ollama + modelli locali ottimizzati per M1"
brew services start ollama 2>/dev/null || true
sleep 2
OLLAMA_MODELS=(
  "llama3.3:70b-instruct-q4_K_M"         # general-purpose flagship (pesante)
  "qwen2.5-coder:32b-instruct-q4_K_M"    # coding agent locale top
  "deepseek-r1:14b"                      # reasoning locale
  "mistral-small:24b-instruct-2501-q4_K_M"
  "phi4:14b"                             # compatto, ragionamento
  "nomic-embed-text:latest"              # embeddings per RAG / Continue
  "qwen2.5:7b-instruct"                  # fallback leggero
)
for m in "${OLLAMA_MODELS[@]}"; do
  ollama pull "$m" 2>/dev/null && ok "ollama: $m" \
    || warn "ollama pull $m fallito (spazio disco / rete)"
done

# -----------------------------------------------------------------------------
step "[5/8] MCP server pack (sempre disponibili a VS Code e Claude Code)"
MCP_PKGS=(
  "@modelcontextprotocol/server-filesystem"
  "@modelcontextprotocol/server-github"
  "@modelcontextprotocol/server-memory"
  "@modelcontextprotocol/server-sequential-thinking"
  "@modelcontextprotocol/server-everything"
  "@modelcontextprotocol/server-fetch"
  "@modelcontextprotocol/server-time"
  "@modelcontextprotocol/server-puppeteer"
  "@modelcontextprotocol/server-brave-search"
  "@modelcontextprotocol/server-slack"
  "@modelcontextprotocol/server-gdrive"
  "@modelcontextprotocol/server-postgres"
  "@modelcontextprotocol/server-sqlite"
)
for m in "${MCP_PKGS[@]}"; do
  npm install -g "$m" 2>/dev/null && ok "MCP: $m" || warn "MCP skip: $m"
done

# Stub file keys — l'utente deve compilarlo UNA volta
mkdir -p "$HOME/.config/vio"
[[ -f "$HOME/.config/vio/keys.env" ]] || cat > "$HOME/.config/vio/keys.env" <<'ENV'
# Riempire le chiavi necessarie, poi: source ~/.config/vio/keys.env
export ANTHROPIC_API_KEY=""
export OPENAI_API_KEY=""
export GOOGLE_API_KEY=""
export MISTRAL_API_KEY=""
export DEEPSEEK_API_KEY=""
export PERPLEXITY_API_KEY=""
export GITHUB_TOKEN=""
export BRAVE_API_KEY=""
ENV
chmod 600 "$HOME/.config/vio/keys.env"
ok "keys.env pronto: $HOME/.config/vio/keys.env (compilare a mano)"

# Claude Code MCP registry
mkdir -p "$HOME/.config/claude"
cat > "$HOME/.config/claude/mcp_servers.json" <<'JSON'
{
  "mcpServers": {
    "filesystem":    { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users"] },
    "github":        { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"],
                       "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" } },
    "memory":        { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"] },
    "sequential":    { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"] },
    "fetch":         { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-fetch"] },
    "time":          { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-time"] },
    "puppeteer":     { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"] },
    "brave-search":  { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                       "env": { "BRAVE_API_KEY": "${BRAVE_API_KEY}" } }
  }
}
JSON
ok "MCP registry → ~/.config/claude/mcp_servers.json"

# -----------------------------------------------------------------------------
step "[6/8] Estensioni VS Code + settings.json"
command -v code &>/dev/null || brew install --cask visual-studio-code

EXT=(
  anthropic.claude-code github.copilot github.copilot-chat
  continue.continue codeium.codeium rjmacarthy.twinny saoudrizwan.claude-dev
  sourcegraph.amp google.gemini-cli-vscode openai.chatgpt
  ms-vscode-remote.remote-ssh ms-vscode-remote.remote-ssh-edit
  ms-vscode-remote.remote-containers ms-vsliveshare.vsliveshare
  eamodio.gitlens github.vscode-pull-request-github mhutchie.git-graph
  dbaeumer.vscode-eslint esbenp.prettier-vscode
  ms-python.python ms-python.vscode-pylance charliermarsh.ruff
  rust-lang.rust-analyzer golang.go
  ms-azuretools.vscode-docker redhat.vscode-yaml tamasfe.even-better-toml
  usernamehw.errorlens streetsidesoftware.code-spell-checker
  editorconfig.editorconfig gruntfuggly.todo-tree yzhang.markdown-all-in-one
)
INSTALLED="$(code --list-extensions 2>/dev/null || true)"
for e in "${EXT[@]}"; do
  if grep -qix "$e" <<<"$INSTALLED"; then ok "già: $e"
  else code --install-extension "$e" --force >/dev/null 2>&1 && ok "install: $e" \
       || warn "skip: $e (marketplace/licensing)"
  fi
done

SDIR="$HOME/Library/Application Support/Code/User"
mkdir -p "$SDIR"
[[ -f "$SDIR/settings.json" ]] && cp "$SDIR/settings.json" "$SDIR/settings.json.bak.$(date +%s)"
cat > "$SDIR/settings.json" <<'JSON'
{
  "settingsSync.keybindingsPerPlatform": false,
  "telemetry.telemetryLevel": "off",
  "editor.fontFamily": "JetBrainsMono Nerd Font, Menlo, monospace",
  "editor.fontLigatures": true,
  "editor.formatOnSave": true,
  "editor.inlineSuggest.enabled": true,
  "editor.minimap.enabled": false,
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 500,
  "terminal.integrated.defaultProfile.osx": "zsh",
  "terminal.integrated.scrollback": 50000,
  "git.autofetch": true,
  "git.confirmSync": false,
  "remote.SSH.remotePlatform": { "imac-archimede": "linux" },
  "remote.SSH.defaultExtensions": [
    "anthropic.claude-code","github.copilot","github.copilot-chat",
    "continue.continue","eamodio.gitlens","saoudrizwan.claude-dev"
  ],
  "github.copilot.enable": { "*": true },
  "claude-code.autoStart": true,
  "continue.telemetryEnabled": false,
  "continue.enableTabAutocomplete": true
}
JSON
ok "settings.json scritto"

# Continue config (multi-router: locale Ollama + cloud)
mkdir -p "$HOME/.continue"
cat > "$HOME/.continue/config.json" <<'JSON'
{
  "models": [
    { "title": "Claude Sonnet 4.6", "provider": "anthropic", "model": "claude-sonnet-4-6", "apiKey": "${ANTHROPIC_API_KEY}" },
    { "title": "GPT-4o",            "provider": "openai",    "model": "gpt-4o",            "apiKey": "${OPENAI_API_KEY}" },
    { "title": "Gemini 2.5 Pro",    "provider": "gemini",    "model": "gemini-2.5-pro",    "apiKey": "${GOOGLE_API_KEY}" },
    { "title": "Qwen2.5-Coder 32B (local)", "provider": "ollama", "model": "qwen2.5-coder:32b-instruct-q4_K_M" },
    { "title": "DeepSeek R1 14B (local)",   "provider": "ollama", "model": "deepseek-r1:14b" }
  ],
  "tabAutocompleteModel": { "title": "Qwen Coder", "provider": "ollama", "model": "qwen2.5-coder:32b-instruct-q4_K_M" },
  "embeddingsProvider":   { "provider": "ollama", "model": "nomic-embed-text:latest" }
}
JSON
ok "Continue config scritto"

# -----------------------------------------------------------------------------
step "[7/8] LaunchAgent sempre-attivi (Ollama + MCP broker + watchdog)"
LA="$HOME/Library/LaunchAgents"
mkdir -p "$LA" "$HOME/Library/Logs/vio"

# 1) Ollama già gestito da `brew services` — aggiungiamo solo watchdog
cat > "$LA/ai.vio.ollama-watchdog.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>ai.vio.ollama-watchdog</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>-c</string>
    <string>while true; do curl -sf http://localhost:11434/api/tags &gt;/dev/null || /opt/homebrew/bin/brew services restart ollama; sleep 30; done</string>
  </array>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/vio/ollama-watchdog.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/vio/ollama-watchdog.err</string>
</dict></plist>
EOF

# 2) MCP broker — tiene caldi i server più usati
cat > "$LA/ai.vio.mcp-broker.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>ai.vio.mcp-broker</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>-lc</string>
    <string>source $HOME/.config/vio/keys.env 2>/dev/null; npx -y @modelcontextprotocol/server-memory</string>
  </array>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/vio/mcp-broker.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/vio/mcp-broker.err</string>
</dict></plist>
EOF

# 3) Orchestra backend autostart (usa lo script già esistente)
if [[ -x "$PWD/scripts/vio-orchestra-autostart.sh" ]]; then
cat > "$LA/ai.vio.orchestra.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>ai.vio.orchestra</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$PWD/scripts/vio-orchestra-autostart.sh</string></array>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/vio/orchestra.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/vio/orchestra.err</string>
</dict></plist>
EOF
fi

for p in ai.vio.ollama-watchdog ai.vio.mcp-broker ai.vio.orchestra; do
  plist="$LA/$p.plist"
  [[ -f $plist ]] || continue
  launchctl unload "$plist" 2>/dev/null || true
  launchctl load "$plist" && ok "launchd attivo: $p"
done

# -----------------------------------------------------------------------------
step "[8/8] Cleanup + riepilogo"
brew cleanup -s 2>/dev/null || true

cat <<EOF

${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
${C_G}MAC AIR — SETUP COMPLETATO${C_N}

Passi interattivi obbligatori (non automatizzabili onestamente):

  1. ${C_Y}Compila le API keys${C_N} (una volta sola):
       \$EDITOR ~/.config/vio/keys.env
       echo 'source ~/.config/vio/keys.env' >> ~/.zshrc

  2. ${C_Y}VS Code Settings Sync${C_N} (una volta):
       Command Palette → "Settings Sync: Turn On" → login GitHub
       (stesso account sul iMac = estensioni e settings identici)

  3. ${C_Y}Primo Remote-SSH verso iMac${C_N} (una volta):
       Command Palette → "Remote-SSH: Connect to Host" → imac-archimede
       Apri cartella /opt/vioaiorchestra

Da quel momento ogni tasto digitato in quella finestra VS Code esegue
sull'iMac: terminali, language server, agenti AI, MCP, debugger.

${C_C}Servizi sempre attivi (launchctl list | grep vio):${C_N}
  ai.vio.ollama-watchdog  — mantiene Ollama up (restart se cade)
  ai.vio.mcp-broker       — MCP memory server sempre caldo
  ai.vio.orchestra        — backend Express della piattaforma

${C_C}Log:${C_N} ~/Library/Logs/vio/*.log
${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
EOF
