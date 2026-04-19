#!/usr/bin/env bash
# =============================================================================
# VIO AI ORCHESTRA — VS Code BOOST per iMac (Arch Linux) — April 2026
# -----------------------------------------------------------------------------
# Scope: SOLO VS Code. Niente pacman, niente Ollama, niente docker.
# Presume che imac_arch_powerhouse_2026.sh sia già stato eseguito (o che
# 'code' e 'npm' siano già sul PATH).
#
# Cosa fa (idempotente):
#   1. Installa pack completo estensioni AI + Remote + lang + DX
#   2. Scrive settings.json / keybindings.json / snippets
#   3. Continue config con Ollama LOCALE (l'iMac è il nodo di esecuzione)
#   4. MCP registry per Claude Code + Cline
#   5. Task VS Code pronti per il progetto VIO Orchestra
#   6. Unit systemd --user che tiene caldo MCP memory + timer update ext
# =============================================================================
set -Eeuo pipefail
readonly C_G='\033[0;32m' C_Y='\033[1;33m' C_C='\033[0;36m' C_N='\033[0m'
ok(){ printf "${C_G}  ✓${C_N} %s\n" "$*"; }
warn(){ printf "${C_Y}  !${C_N} %s\n" "$*"; }
step(){ printf "\n${C_C}▶ %s${C_N}\n" "$*"; }

[[ -f /etc/arch-release ]] || { echo "Arch Linux only"; exit 1; }
command -v code &>/dev/null || { echo "Manca 'code'. Installa visual-studio-code-bin (AUR) prima."; exit 1; }
command -v npm  &>/dev/null || { echo "Manca 'npm'. Installa nodejs+npm prima."; exit 1; }

SDIR="$HOME/.config/Code/User"
mkdir -p "$SDIR/snippets"

# -----------------------------------------------------------------------------
step "[1/6] Estensioni (AI top-tier aprile 2026 + Remote + lang + DX)"
EXT=(
  anthropic.claude-code github.copilot github.copilot-chat
  continue.continue codeium.codeium rjmacarthy.twinny
  saoudrizwan.claude-dev sourcegraph.amp
  google.gemini-cli-vscode openai.chatgpt
  ms-vscode-remote.remote-ssh ms-vscode-remote.remote-ssh-edit
  ms-vscode-remote.remote-containers ms-vsliveshare.vsliveshare
  eamodio.gitlens github.vscode-pull-request-github
  github.vscode-github-actions mhutchie.git-graph
  dbaeumer.vscode-eslint esbenp.prettier-vscode
  ms-python.python ms-python.vscode-pylance ms-python.black-formatter charliermarsh.ruff
  rust-lang.rust-analyzer golang.go
  redhat.vscode-yaml tamasfe.even-better-toml
  ms-azuretools.vscode-docker
  usernamehw.errorlens streetsidesoftware.code-spell-checker
  editorconfig.editorconfig christian-kohler.path-intellisense
  formulahendry.auto-rename-tag gruntfuggly.todo-tree
  yzhang.markdown-all-in-one bierner.markdown-mermaid
  wayou.vscode-todo-highlight ritwickdey.liveserver
)
INSTALLED="$(code --list-extensions 2>/dev/null || true)"
for e in "${EXT[@]}"; do
  if grep -qix "$e" <<<"$INSTALLED"; then ok "già: $e"
  else code --install-extension "$e" --force >/dev/null 2>&1 && ok "install: $e" \
       || warn "skip: $e"
  fi
done

# -----------------------------------------------------------------------------
step "[2/6] settings.json"
[[ -f "$SDIR/settings.json" ]] && cp "$SDIR/settings.json" "$SDIR/settings.json.bak.$(date +%s)"
cat > "$SDIR/settings.json" <<'JSON'
{
  "settingsSync.keybindingsPerPlatform": false,
  "telemetry.telemetryLevel": "off",
  "workbench.settings.enableNaturalLanguageSearch": true,
  "workbench.colorTheme": "Default Dark Modern",
  "editor.fontFamily": "JetBrainsMono Nerd Font, monospace",
  "editor.fontLigatures": true,
  "editor.formatOnSave": true,
  "editor.inlineSuggest.enabled": true,
  "editor.suggest.preview": true,
  "editor.minimap.enabled": false,
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": "active",
  "editor.stickyScroll.enabled": true,
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 500,
  "terminal.integrated.defaultProfile.linux": "zsh",
  "terminal.integrated.scrollback": 50000,
  "terminal.integrated.enableMultiLinePasteWarning": "never",
  "git.autofetch": true,
  "git.confirmSync": false,
  "git.enableSmartCommit": true,
  "github.copilot.enable": { "*": true, "markdown": true, "plaintext": true },
  "claude-code.autoStart": true,
  "cline.mcpMarketplace.enabled": true,
  "continue.telemetryEnabled": false,
  "continue.enableTabAutocomplete": true,
  "workbench.editor.enablePreview": false
}
JSON
ok "settings.json scritto"

# -----------------------------------------------------------------------------
step "[3/6] keybindings.json + snippet globale"
cat > "$SDIR/keybindings.json" <<'JSON'
[
  { "key": "ctrl+i",         "command": "workbench.action.chat.open" },
  { "key": "ctrl+shift+i",   "command": "claude-code.open" },
  { "key": "alt+\\",         "command": "editor.action.inlineSuggest.trigger" },
  { "key": "ctrl+alt+c",     "command": "workbench.action.terminal.sendSequence",
                             "args": { "text": "claude\n" } },
  { "key": "ctrl+alt+a",     "command": "workbench.action.terminal.sendSequence",
                             "args": { "text": "aider --model sonnet\n" } }
]
JSON
cat > "$SDIR/snippets/global.code-snippets" <<'JSON'
{
  "VIO header": {
    "scope": "javascript,typescript,python,go,rust,sh",
    "prefix": "vio-hdr",
    "body": [
      "// VIO AI Orchestra — $TM_FILENAME",
      "// Autore: Viorica Porcu (Vio) — https://github.com/vio83/vio83-ai-orchestra",
      ""
    ]
  }
}
JSON
ok "keybindings + snippet globale"

# -----------------------------------------------------------------------------
step "[4/6] Continue config (Ollama LOCALE = esecuzione primaria su iMac)"
mkdir -p "$HOME/.continue"
cat > "$HOME/.continue/config.json" <<'JSON'
{
  "models": [
    { "title": "Claude Sonnet 4.6", "provider": "anthropic", "model": "claude-sonnet-4-6", "apiKey": "${ANTHROPIC_API_KEY}" },
    { "title": "Claude Opus 4.7",   "provider": "anthropic", "model": "claude-opus-4-7",   "apiKey": "${ANTHROPIC_API_KEY}" },
    { "title": "GPT-4o",            "provider": "openai",    "model": "gpt-4o",            "apiKey": "${OPENAI_API_KEY}" },
    { "title": "Gemini 2.5 Pro",    "provider": "gemini",    "model": "gemini-2.5-pro",    "apiKey": "${GOOGLE_API_KEY}" },
    { "title": "Qwen-Coder 32B (local)", "provider": "ollama", "model": "qwen2.5-coder:32b-instruct-q4_K_M" },
    { "title": "DeepSeek R1 32B (local)","provider": "ollama", "model": "deepseek-r1:32b" },
    { "title": "Llama 3.3 70B (local)",  "provider": "ollama", "model": "llama3.3:70b-instruct-q4_K_M" }
  ],
  "tabAutocompleteModel": { "title": "Qwen Coder", "provider": "ollama", "model": "qwen2.5-coder:32b-instruct-q4_K_M" },
  "embeddingsProvider":   { "provider": "ollama", "model": "nomic-embed-text:latest" }
}
JSON
ok "Continue: modelli locali dell'iMac in prima linea"

# -----------------------------------------------------------------------------
step "[5/6] MCP registry (Claude Code + Cline)"
mkdir -p "$HOME/.config/claude"
cat > "$HOME/.config/claude/mcp_servers.json" <<'JSON'
{
  "mcpServers": {
    "filesystem":   { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home", "/opt/vioaiorchestra"] },
    "github":       { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"], "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" } },
    "memory":       { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"] },
    "sequential":   { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"] },
    "fetch":        { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-fetch"] },
    "time":         { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-time"] },
    "puppeteer":    { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"] },
    "postgres":     { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-postgres"] },
    "sqlite":       { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-sqlite"] },
    "brave-search": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"], "env": { "BRAVE_API_KEY": "${BRAVE_API_KEY}" } }
  }
}
JSON

CLINE_DIR="$SDIR/globalStorage/saoudrizwan.claude-dev/settings"
mkdir -p "$CLINE_DIR"
cp "$HOME/.config/claude/mcp_servers.json" "$CLINE_DIR/cline_mcp_settings.json"
ok "MCP registrati per Claude Code + Cline"

# -----------------------------------------------------------------------------
step "[6/6] systemd --user: MCP memory warm + timer update estensioni"
UDIR="$HOME/.config/systemd/user"
mkdir -p "$UDIR" "$HOME/.vio-logs"

cat > "$UDIR/vio-vscode-mcp-warm.service" <<EOF
[Unit]
Description=VIO — MCP memory server always warm for VS Code
After=network-online.target
[Service]
Type=simple
EnvironmentFile=-%h/.config/vio/keys.env
ExecStart=/bin/bash -lc 'npx -y @modelcontextprotocol/server-memory'
Restart=always
RestartSec=5
StandardOutput=append:%h/.vio-logs/vscode-mcp-warm.log
StandardError=append:%h/.vio-logs/vscode-mcp-warm.err
[Install]
WantedBy=default.target
EOF

cat > "$UDIR/vio-vscode-ext-updater.service" <<'EOF'
[Unit]
Description=VIO — VS Code extensions auto-update
[Service]
Type=oneshot
ExecStart=/bin/bash -lc 'code --update-extensions --force || true'
EOF
cat > "$UDIR/vio-vscode-ext-updater.timer" <<'EOF'
[Unit]
Description=VIO — weekly VS Code extensions update
[Timer]
OnBootSec=5min
OnUnitActiveSec=7d
Persistent=true
[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now vio-vscode-mcp-warm.service 2>/dev/null && ok "attivo: vio-vscode-mcp-warm"
systemctl --user enable --now vio-vscode-ext-updater.timer 2>/dev/null && ok "attivo: vio-vscode-ext-updater.timer"
sudo loginctl enable-linger "$USER" 2>/dev/null && ok "linger abilitato (servizi vivi anche a sessione chiusa)"

cat <<EOF

${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
${C_G}VS Code iMac Arch — BOOST COMPLETATO${C_N}

Passi manuali (onestamente obbligati):
  1. ${C_Y}Settings Sync${C_N}: Command Palette → "Settings Sync: Turn On" → GitHub
                  (stesso account del Mac Air → estensioni/settings mirror)
  2. ${C_Y}API keys${C_N}:     compila ~/.config/vio/keys.env
                  poi: systemctl --user restart vio-vscode-mcp-warm

Questo iMac è il nodo di ESECUZIONE: quando il Mac Air fa Remote-SSH qui,
agenti, Ollama, MCP e debugger girano su questa macchina.

Log: ~/.vio-logs/
${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
EOF
