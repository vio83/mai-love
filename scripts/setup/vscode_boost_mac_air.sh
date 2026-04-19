#!/usr/bin/env bash
# =============================================================================
# VIO AI ORCHESTRA — VS Code BOOST per Mac Air (Apple Silicon) — April 2026
# -----------------------------------------------------------------------------
# Scope: SOLO VS Code. Niente package manager, niente Ollama, niente systemd.
# Presume che mac_air_powerhouse_2026.sh sia già stato eseguito (oppure che
# 'code' e 'npm' siano già disponibili sul PATH).
#
# Cosa fa (idempotente):
#   1. Installa il pack completo estensioni AI + Remote + lang + DX
#   2. Scrive settings.json / keybindings.json / snippets globali
#   3. Scrive Continue config multi-router (cloud + Ollama locale)
#   4. Registra MCP server sia per Claude Code sia per Cline
#   5. Task/launch templates pronti per il progetto VIO Orchestra
#   6. LaunchAgent che tiene sempre caldo npx per i MCP più usati
# =============================================================================
set -Eeuo pipefail
readonly C_G='\033[0;32m' C_Y='\033[1;33m' C_C='\033[0;36m' C_N='\033[0m'
ok(){ printf "${C_G}  ✓${C_N} %s\n" "$*"; }
warn(){ printf "${C_Y}  !${C_N} %s\n" "$*"; }
step(){ printf "\n${C_C}▶ %s${C_N}\n" "$*"; }

[[ "$(uname -s)" == "Darwin" ]] || { echo "macOS only"; exit 1; }
command -v code &>/dev/null || { echo "Manca 'code' sul PATH. Apri VS Code → Shell Command: Install 'code' in PATH"; exit 1; }
command -v npm  &>/dev/null || { echo "Manca 'npm'. Installa Node (nvm o brew) prima di rilanciare."; exit 1; }

SDIR="$HOME/Library/Application Support/Code/User"
mkdir -p "$SDIR/snippets"

# -----------------------------------------------------------------------------
step "[1/6] Estensioni (AI top-tier aprile 2026 + Remote + lang + DX)"
EXT=(
  # AI assistants & agenti autonomi
  anthropic.claude-code github.copilot github.copilot-chat
  continue.continue codeium.codeium rjmacarthy.twinny
  saoudrizwan.claude-dev sourcegraph.amp
  google.gemini-cli-vscode openai.chatgpt
  # Remote + pairing
  ms-vscode-remote.remote-ssh ms-vscode-remote.remote-ssh-edit
  ms-vscode-remote.remote-containers ms-vscode-remote.remote-wsl
  ms-vscode.remote-explorer ms-vsliveshare.vsliveshare
  # Git / GitHub
  eamodio.gitlens github.vscode-pull-request-github
  github.vscode-github-actions mhutchie.git-graph
  # Lang servers
  dbaeumer.vscode-eslint esbenp.prettier-vscode
  ms-python.python ms-python.vscode-pylance ms-python.black-formatter charliermarsh.ruff
  rust-lang.rust-analyzer golang.go
  redhat.vscode-yaml tamasfe.even-better-toml
  ms-azuretools.vscode-docker
  # DX / produttività
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
       || warn "skip: $e (marketplace/licensing)"
  fi
done

# -----------------------------------------------------------------------------
step "[2/6] settings.json (Settings Sync ON + AI tunato)"
[[ -f "$SDIR/settings.json" ]] && cp "$SDIR/settings.json" "$SDIR/settings.json.bak.$(date +%s)"
cat > "$SDIR/settings.json" <<'JSON'
{
  "settingsSync.keybindingsPerPlatform": false,
  "telemetry.telemetryLevel": "off",
  "workbench.settings.enableNaturalLanguageSearch": true,
  "workbench.colorTheme": "Default Dark Modern",
  "editor.fontFamily": "JetBrainsMono Nerd Font, Menlo, Consolas, monospace",
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
  "terminal.integrated.defaultProfile.osx": "zsh",
  "terminal.integrated.scrollback": 50000,
  "terminal.integrated.enableMultiLinePasteWarning": "never",
  "git.autofetch": true,
  "git.confirmSync": false,
  "git.enableSmartCommit": true,
  "remote.SSH.remotePlatform": { "imac-archimede": "linux" },
  "remote.SSH.defaultExtensions": [
    "anthropic.claude-code","github.copilot","github.copilot-chat",
    "continue.continue","saoudrizwan.claude-dev","eamodio.gitlens"
  ],
  "remote.SSH.connectTimeout": 60,
  "github.copilot.enable": { "*": true, "markdown": true, "plaintext": true },
  "github.copilot.advanced": { "length": 500 },
  "claude-code.autoStart": true,
  "cline.mcpMarketplace.enabled": true,
  "continue.telemetryEnabled": false,
  "continue.enableTabAutocomplete": true,
  "workbench.editor.enablePreview": false,
  "explorer.confirmDelete": false
}
JSON
ok "settings.json scritto"

# -----------------------------------------------------------------------------
step "[3/6] keybindings.json + snippet globale VIO"
cat > "$SDIR/keybindings.json" <<'JSON'
[
  { "key": "cmd+i",          "command": "workbench.action.chat.open" },
  { "key": "cmd+shift+i",    "command": "claude-code.open" },
  { "key": "alt+\\",         "command": "editor.action.inlineSuggest.trigger" },
  { "key": "cmd+alt+c",      "command": "workbench.action.terminal.sendSequence",
                             "args": { "text": "claude\n" } },
  { "key": "cmd+alt+a",      "command": "workbench.action.terminal.sendSequence",
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
step "[4/6] Continue config (multi-router cloud + Ollama)"
mkdir -p "$HOME/.continue"
cat > "$HOME/.continue/config.json" <<'JSON'
{
  "models": [
    { "title": "Claude Sonnet 4.6", "provider": "anthropic", "model": "claude-sonnet-4-6", "apiKey": "${ANTHROPIC_API_KEY}" },
    { "title": "Claude Opus 4.7",   "provider": "anthropic", "model": "claude-opus-4-7",   "apiKey": "${ANTHROPIC_API_KEY}" },
    { "title": "GPT-4o",            "provider": "openai",    "model": "gpt-4o",            "apiKey": "${OPENAI_API_KEY}" },
    { "title": "Gemini 2.5 Pro",    "provider": "gemini",    "model": "gemini-2.5-pro",    "apiKey": "${GOOGLE_API_KEY}" },
    { "title": "Qwen-Coder 32B (iMac)", "provider": "ollama", "model": "qwen2.5-coder:32b-instruct-q4_K_M",
      "apiBase": "http://imac-archimede:11434" },
    { "title": "DeepSeek R1 32B (iMac)", "provider": "ollama", "model": "deepseek-r1:32b",
      "apiBase": "http://imac-archimede:11434" },
    { "title": "Qwen-Coder 32B (locale)", "provider": "ollama", "model": "qwen2.5-coder:32b-instruct-q4_K_M" }
  ],
  "tabAutocompleteModel": { "title": "Qwen Coder (iMac)", "provider": "ollama",
    "model": "qwen2.5-coder:32b-instruct-q4_K_M", "apiBase": "http://imac-archimede:11434" },
  "embeddingsProvider": { "provider": "ollama", "model": "nomic-embed-text:latest",
    "apiBase": "http://imac-archimede:11434" }
}
JSON
ok "Continue: cloud + Ollama remoto su iMac via Tailnet"

# -----------------------------------------------------------------------------
step "[5/6] MCP registry (Claude Code + Cline)"
mkdir -p "$HOME/.config/claude"
cat > "$HOME/.config/claude/mcp_servers.json" <<'JSON'
{
  "mcpServers": {
    "filesystem":   { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users"] },
    "github":       { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"], "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" } },
    "memory":       { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"] },
    "sequential":   { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"] },
    "fetch":        { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-fetch"] },
    "time":         { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-time"] },
    "puppeteer":    { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"] },
    "brave-search": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"], "env": { "BRAVE_API_KEY": "${BRAVE_API_KEY}" } }
  }
}
JSON

# Cline (VS Code) legge da una location sua
CLINE_DIR="$SDIR/globalStorage/saoudrizwan.claude-dev/settings"
mkdir -p "$CLINE_DIR"
cp "$HOME/.config/claude/mcp_servers.json" "$CLINE_DIR/cline_mcp_settings.json"
ok "MCP registrati per Claude Code + Cline"

# -----------------------------------------------------------------------------
step "[6/6] LaunchAgent: mantiene caldo MCP memory + pre-cache npx"
LA="$HOME/Library/LaunchAgents"
LOG="$HOME/Library/Logs/vio"
mkdir -p "$LA" "$LOG"
cat > "$LA/ai.vio.vscode-mcp-warm.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>ai.vio.vscode-mcp-warm</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>-lc</string>
    <string>source \$HOME/.config/vio/keys.env 2>/dev/null; npx -y @modelcontextprotocol/server-memory</string>
  </array>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$LOG/vscode-mcp-warm.log</string>
  <key>StandardErrorPath</key><string>$LOG/vscode-mcp-warm.err</string>
</dict></plist>
EOF
launchctl unload "$LA/ai.vio.vscode-mcp-warm.plist" 2>/dev/null || true
launchctl load   "$LA/ai.vio.vscode-mcp-warm.plist"
ok "LaunchAgent attivo: ai.vio.vscode-mcp-warm"

cat <<EOF

${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
${C_G}VS Code Mac Air — BOOST COMPLETATO${C_N}

Passi manuali (onestamente obbligati):
  1. ${C_Y}Settings Sync${C_N}: Command Palette → "Settings Sync: Turn On" → GitHub
  2. ${C_Y}Remote-SSH${C_N}:   Command Palette → "Remote-SSH: Connect to Host" → imac-archimede
  3. ${C_Y}API keys${C_N}:     compila ~/.config/vio/keys.env (già creato)

Continue userà in automatico:
  • Cloud: Claude Sonnet/Opus, GPT-4o, Gemini 2.5 Pro
  • Locale: Ollama remoto su imac-archimede:11434 (Qwen-Coder 32B, DeepSeek R1 32B)

Log: ~/Library/Logs/vio/
${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
EOF
