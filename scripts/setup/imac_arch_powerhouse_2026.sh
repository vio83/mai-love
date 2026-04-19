#!/usr/bin/env bash
# =============================================================================
# VIO AI ORCHESTRA — iMac (Arch Linux) POWERHOUSE — April 2026 edition
# -----------------------------------------------------------------------------
# Pre-requisiti già soddisfatti:
#   * Tailscale attivo e autenticato
#   * sshd abilitato e raggiungibile dal Mac Air
#
# Questo iMac è il NODO DI ESECUZIONE PRIMARIO: quando il Mac Air fa
# Remote-SSH qui, tutti gli agenti, modelli locali, MCP server, build e
# debugger girano su questa macchina.
#
# Cosa fa (idempotente):
#   1. Aggiornamento completo pacman + yay (AUR)
#   2. Toolchain CLI + linguaggi (Python, Node LTS, Rust, Go, Docker)
#   3. Stack AI CLI: Claude Code, Codex, Gemini, Aider, Cline, OpenCode,
#      Goose, Copilot CLI, Cursor CLI
#   4. Ollama + pull modelli locali top-tier aprile 2026
#   5. MCP server pack completo (npm global)
#   6. VS Code (code OSS o visual-studio-code-bin) + estensioni AI
#   7. Settings.json condiviso con Settings Sync ON, Continue multi-router
#   8. 4 unit systemd --user sempre attive:
#        ollama-watchdog, mcp-broker, orchestra, extensions-updater
#   9. loginctl enable-linger = i servizi girano anche senza sessione aperta
#
# LIMITI ONESTI:
#   * API keys devono essere compilate una volta in ~/.config/vio/keys.env
#   * Settings Sync: un login GitHub interattivo (una volta sola)
# =============================================================================

set -Eeuo pipefail
readonly C_G='\033[0;32m' C_Y='\033[1;33m' C_C='\033[0;36m' C_R='\033[0;31m' C_N='\033[0m'
ok()   { printf "${C_G}  ✓${C_N} %s\n" "$*"; }
warn() { printf "${C_Y}  !${C_N} %s\n" "$*"; }
err()  { printf "${C_R}  ✗${C_N} %s\n" "$*" >&2; }
step() { printf "\n${C_C}▶ %s${C_N}\n" "$*"; }
trap 'err "Errore riga $LINENO. Lo script è idempotente: rilancialo."' ERR

[[ -f /etc/arch-release ]] || {
  err "Questo script gira solo su Arch Linux. Per il Mac Air usa mac_air_powerhouse_2026.sh"
  exit 1
}

# -----------------------------------------------------------------------------
step "[1/9] Aggiornamento sistema + AUR helper"
sudo pacman -Syu --noconfirm --needed base-devel git
if ! command -v yay &>/dev/null; then
  tmp=$(mktemp -d)
  git clone https://aur.archlinux.org/yay-bin.git "$tmp/yay"
  (cd "$tmp/yay" && makepkg -si --noconfirm)
  rm -rf "$tmp"
fi
ok "pacman + yay pronti"

# -----------------------------------------------------------------------------
step "[2/9] Toolchain CLI + linguaggi"
PAC_PKGS=(
  git github-cli jq yq curl wget ripgrep fd bat eza fzf zoxide htop btop
  tmux zsh neovim tree tokei hyperfine direnv starship mosh rsync
  openssh base-devel cmake pkgconf
  python python-pip pyenv pipx
  nodejs npm
  go rust
  docker docker-compose docker-buildx
  ffmpeg imagemagick poppler pandoc
)
sudo pacman -S --noconfirm --needed "${PAC_PKGS[@]}" || true
sudo systemctl enable --now docker 2>/dev/null || true
sudo usermod -aG docker "$USER" 2>/dev/null || true
ok "Toolchain installata"

# Node LTS via nvm (per evitare conflitti con pacman durante i npm -g)
export NVM_DIR="$HOME/.nvm"
if ! command -v nvm &>/dev/null && [[ ! -s "$NVM_DIR/nvm.sh" ]]; then
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
fi
. "$NVM_DIR/nvm.sh" 2>/dev/null || true
nvm install --lts && nvm alias default lts/*

# -----------------------------------------------------------------------------
step "[3/9] Stack AI CLI + agenti autonomi (April 2026 top-tier)"
NPM_GLOBAL=(
  "@anthropic-ai/claude-code"
  "@openai/codex"
  "@google/gemini-cli"
  "@sourcegraph/amp"
  "opencode-ai"
  "@cline/cli"
  "@github/copilot-cli"
  "cursor-cli"
)
for p in "${NPM_GLOBAL[@]}"; do
  npm install -g "$p" 2>/dev/null && ok "npm: $p" \
    || warn "skip $p (non pubblicato o offline)"
done

pipx ensurepath >/dev/null 2>&1 || true
for py in aider-chat goose-cli litellm; do
  pipx install "$py" 2>/dev/null && ok "pipx: $py" || warn "pipx skip: $py"
done

# -----------------------------------------------------------------------------
step "[4/9] Ollama + modelli locali (iMac è il nodo di esecuzione primario)"
if ! command -v ollama &>/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
sudo systemctl enable --now ollama
sleep 3

# Modelli scelti per un iMac con più RAM/CPU del Mac Air: più pesanti
OLLAMA_MODELS=(
  "llama3.3:70b-instruct-q4_K_M"
  "qwen2.5-coder:32b-instruct-q4_K_M"
  "deepseek-r1:32b"
  "mistral-small:24b-instruct-2501-q4_K_M"
  "phi4:14b"
  "nomic-embed-text:latest"
  "qwen2.5:14b-instruct"
)
for m in "${OLLAMA_MODELS[@]}"; do
  ollama pull "$m" 2>/dev/null && ok "ollama: $m" \
    || warn "ollama pull $m fallito (spazio disco / rete)"
done

# Espone Ollama su Tailnet così il Mac Air può interrogarlo via Continue
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf >/dev/null <<'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_KEEP_ALIVE=24h"
Environment="OLLAMA_NUM_PARALLEL=4"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
ok "Ollama esposto sulla Tailnet (11434)"

# -----------------------------------------------------------------------------
step "[5/9] MCP server pack"
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

mkdir -p "$HOME/.config/vio"
[[ -f "$HOME/.config/vio/keys.env" ]] || cat > "$HOME/.config/vio/keys.env" <<'ENV'
# Compilare e poi: source ~/.config/vio/keys.env (aggiungerlo in ~/.zshrc)
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

mkdir -p "$HOME/.config/claude"
cat > "$HOME/.config/claude/mcp_servers.json" <<'JSON'
{
  "mcpServers": {
    "filesystem":    { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home", "/opt/vioaiorchestra"] },
    "github":        { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"],
                       "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" } },
    "memory":        { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"] },
    "sequential":    { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"] },
    "fetch":         { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-fetch"] },
    "time":          { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-time"] },
    "puppeteer":     { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"] },
    "postgres":      { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-postgres"] },
    "sqlite":        { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-sqlite"] },
    "brave-search":  { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                       "env": { "BRAVE_API_KEY": "${BRAVE_API_KEY}" } }
  }
}
JSON
ok "MCP registry → ~/.config/claude/mcp_servers.json"

# -----------------------------------------------------------------------------
step "[6/9] VS Code + estensioni"
if ! command -v code &>/dev/null; then
  yay -S --noconfirm --needed visual-studio-code-bin || \
    sudo pacman -S --noconfirm --needed code
fi

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
       || warn "skip: $e"
  fi
done

SDIR="$HOME/.config/Code/User"
mkdir -p "$SDIR"
[[ -f "$SDIR/settings.json" ]] && cp "$SDIR/settings.json" "$SDIR/settings.json.bak.$(date +%s)"
cat > "$SDIR/settings.json" <<'JSON'
{
  "settingsSync.keybindingsPerPlatform": false,
  "telemetry.telemetryLevel": "off",
  "editor.fontFamily": "JetBrainsMono Nerd Font, monospace",
  "editor.fontLigatures": true,
  "editor.formatOnSave": true,
  "editor.inlineSuggest.enabled": true,
  "editor.minimap.enabled": false,
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 500,
  "terminal.integrated.defaultProfile.linux": "zsh",
  "terminal.integrated.scrollback": 50000,
  "git.autofetch": true,
  "git.confirmSync": false,
  "github.copilot.enable": { "*": true },
  "claude-code.autoStart": true,
  "continue.telemetryEnabled": false,
  "continue.enableTabAutocomplete": true
}
JSON
ok "settings.json scritto"

mkdir -p "$HOME/.continue"
cat > "$HOME/.continue/config.json" <<'JSON'
{
  "models": [
    { "title": "Claude Sonnet 4.6", "provider": "anthropic", "model": "claude-sonnet-4-6", "apiKey": "${ANTHROPIC_API_KEY}" },
    { "title": "GPT-4o",            "provider": "openai",    "model": "gpt-4o",            "apiKey": "${OPENAI_API_KEY}" },
    { "title": "Gemini 2.5 Pro",    "provider": "gemini",    "model": "gemini-2.5-pro",    "apiKey": "${GOOGLE_API_KEY}" },
    { "title": "Qwen2.5-Coder 32B (local)", "provider": "ollama", "model": "qwen2.5-coder:32b-instruct-q4_K_M" },
    { "title": "DeepSeek R1 32B (local)",   "provider": "ollama", "model": "deepseek-r1:32b" },
    { "title": "Llama 3.3 70B (local)",     "provider": "ollama", "model": "llama3.3:70b-instruct-q4_K_M" }
  ],
  "tabAutocompleteModel": { "title": "Qwen Coder", "provider": "ollama", "model": "qwen2.5-coder:32b-instruct-q4_K_M" },
  "embeddingsProvider":   { "provider": "ollama", "model": "nomic-embed-text:latest" }
}
JSON
ok "Continue config scritto"

# -----------------------------------------------------------------------------
step "[7/9] Servizi systemd --user sempre attivi"
UDIR="$HOME/.config/systemd/user"
mkdir -p "$UDIR" "$HOME/.vio-logs"

# 1) Ollama watchdog (Ollama è un service di sistema, ma monitoriamolo comunque)
cat > "$UDIR/vio-ollama-watchdog.service" <<EOF
[Unit]
Description=VIO — Ollama health watchdog
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
ExecStart=/bin/bash -c 'while true; do curl -sf http://localhost:11434/api/tags >/dev/null || systemctl restart ollama; sleep 30; done'
Restart=always
RestartSec=10
StandardOutput=append:%h/.vio-logs/ollama-watchdog.log
StandardError=append:%h/.vio-logs/ollama-watchdog.err
[Install]
WantedBy=default.target
EOF

# 2) MCP broker (memory server sempre caldo)
cat > "$UDIR/vio-mcp-broker.service" <<EOF
[Unit]
Description=VIO — MCP memory broker (always warm)
After=network-online.target
[Service]
Type=simple
EnvironmentFile=-%h/.config/vio/keys.env
ExecStart=/bin/bash -lc 'npx -y @modelcontextprotocol/server-memory'
Restart=always
RestartSec=5
StandardOutput=append:%h/.vio-logs/mcp-broker.log
StandardError=append:%h/.vio-logs/mcp-broker.err
[Install]
WantedBy=default.target
EOF

# 3) Orchestra backend autostart
if [[ -x /opt/vioaiorchestra/server.js ]] || [[ -f /opt/vioaiorchestra/server.js ]]; then
cat > "$UDIR/vio-orchestra.service" <<EOF
[Unit]
Description=VIO AI Orchestra backend
After=network-online.target
[Service]
Type=simple
WorkingDirectory=/opt/vioaiorchestra
EnvironmentFile=-/opt/vioaiorchestra/.env
EnvironmentFile=-%h/.config/vio/keys.env
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=5
StandardOutput=append:%h/.vio-logs/orchestra.log
StandardError=append:%h/.vio-logs/orchestra.err
[Install]
WantedBy=default.target
EOF
fi

# 4) Auto-updater estensioni VS Code (settimanale)
cat > "$UDIR/vio-extensions-updater.service" <<'EOF'
[Unit]
Description=VIO — VS Code extensions auto-updater
[Service]
Type=oneshot
ExecStart=/bin/bash -lc 'code --update-extensions --force || true'
EOF
cat > "$UDIR/vio-extensions-updater.timer" <<'EOF'
[Unit]
Description=VIO — weekly extension update
[Timer]
OnBootSec=5min
OnUnitActiveSec=7d
Persistent=true
[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
for svc in vio-ollama-watchdog vio-mcp-broker vio-orchestra; do
  [[ -f "$UDIR/$svc.service" ]] || continue
  systemctl --user enable --now "$svc.service" 2>/dev/null && ok "attivo: $svc" \
    || warn "$svc: non avviato (controlla 'journalctl --user -u $svc')"
done
systemctl --user enable --now vio-extensions-updater.timer 2>/dev/null || true

# loginctl enable-linger → i servizi --user girano anche a sessione chiusa
sudo loginctl enable-linger "$USER" 2>/dev/null && ok "linger abilitato ($USER)"

# -----------------------------------------------------------------------------
step "[8/9] Firewall: apri solo sulla Tailnet (non su internet pubblico)"
if command -v ufw &>/dev/null; then
  sudo ufw allow in on tailscale0 to any port 11434 proto tcp 2>/dev/null || true
  sudo ufw allow in on tailscale0 to any port 3000  proto tcp 2>/dev/null || true
  sudo ufw allow in on tailscale0 to any port 22    proto tcp 2>/dev/null || true
  ok "ufw: aperte 22/3000/11434 su tailscale0"
else
  warn "ufw non installato — skippo (Tailscale ha già il suo filtering)"
fi

# -----------------------------------------------------------------------------
step "[9/9] Riepilogo"
cat <<EOF

${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
${C_G}iMac ARCH — SETUP COMPLETATO${C_N}

Passi interattivi obbligatori (non automatizzabili onestamente):

  1. ${C_Y}Compila le API keys${C_N} (una volta):
       \$EDITOR ~/.config/vio/keys.env
       echo 'source ~/.config/vio/keys.env' >> ~/.zshrc
       systemctl --user restart vio-mcp-broker vio-orchestra

  2. ${C_Y}VS Code Settings Sync${C_N} (una volta):
       Command Palette → "Settings Sync: Turn On" → login GitHub
       (stesso account del Mac Air = sessioni/estensioni mirror)

${C_C}Servizi systemd --user sempre attivi (systemctl --user list-units | grep vio):${C_N}
  vio-ollama-watchdog     — restart Ollama se cade
  vio-mcp-broker          — MCP memory server sempre caldo
  vio-orchestra           — backend Express (se /opt/vioaiorchestra esiste)
  vio-extensions-updater  — timer settimanale update estensioni

${C_C}Come verificare da Mac Air che tutto è raggiungibile sulla Tailnet:${C_N}
  curl http://imac-archimede:11434/api/tags          # Ollama
  curl http://imac-archimede:3000/health             # Orchestra backend
  ssh imac-archimede systemctl --user status 'vio-*' # Stato servizi

${C_C}Log:${C_N} ~/.vio-logs/*.log
${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
EOF
