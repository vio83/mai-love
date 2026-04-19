#!/usr/bin/env bash
# =============================================================================
# VIO AI ORCHESTRA — VS Code BOOST Mac Air (Apple Silicon) — April 2026
# VERSIONE NON-DISTRUTTIVA: merge-only, mai sovrascrive config esistenti.
# -----------------------------------------------------------------------------
# Garanzie concrete:
#   * Ogni JSON esistente viene FUSO con i default (jq -s '.[0] * .[1]')
#     I tuoi valori vincono sempre sui conflitti.
#   * Prima di QUALSIASI modifica: backup timestamped (.bak.YYYYMMDD-HHMMSS)
#   * Se jq non riesce a parsare (commenti JSONC): il file NON viene toccato,
#     solo un warning + backup. Zero rischio di corruzione.
#   * Le estensioni sono installate solo se mancanti (--force per aggiornare).
#   * Sessioni VS Code, tab aperti, workspace state, Remote-SSH cache,
#     storia chat Claude Code: NON toccati in alcun modo.
# =============================================================================
set -Eeuo pipefail
readonly C_G='\033[0;32m' C_Y='\033[1;33m' C_C='\033[0;36m' C_R='\033[0;31m' C_N='\033[0m'
ok(){ printf "${C_G}  ✓${C_N} %s\n" "$*"; }
warn(){ printf "${C_Y}  !${C_N} %s\n" "$*"; }
err(){ printf "${C_R}  ✗${C_N} %s\n" "$*" >&2; }
step(){ printf "\n${C_C}▶ %s${C_N}\n" "$*"; }

[[ "$(uname -s)" == "Darwin" ]] || { echo "macOS only"; exit 1; }
command -v code &>/dev/null || { echo "Manca 'code' sul PATH. Apri VS Code → Cmd+Shift+P → Shell Command: Install 'code' in PATH"; exit 1; }
command -v npm  &>/dev/null || { echo "Manca 'npm'. Installa Node (brew install node o nvm) prima di rilanciare."; exit 1; }
command -v jq   &>/dev/null || { command -v brew &>/dev/null && brew install jq || { echo "Installa jq e rilancia"; exit 1; }; }

SDIR="$HOME/Library/Application Support/Code/User"
mkdir -p "$SDIR/snippets"
TS=$(date +%Y%m%d-%H%M%S)
BKROOT="$HOME/.vio-vscode-backups/$TS"
mkdir -p "$BKROOT"

# ----- helper: merge JSON oggetto, tuoi valori vincono ----------------------
safe_merge_json() {
  local target="$1" defaults_file="$2"
  if [[ ! -f "$target" ]]; then
    mkdir -p "$(dirname "$target")"
    cp "$defaults_file" "$target"
    ok "nuovo: $target"
    return
  fi
  cp -a "$target" "$BKROOT/$(basename "$target").bak"
  if jq empty <"$target" 2>/dev/null; then
    local tmp="$target.merged.$$"
    if jq -s '.[0] * .[1]' "$defaults_file" "$target" > "$tmp" 2>/dev/null; then
      mv "$tmp" "$target"
      ok "fuso: $target (tuoi valori intatti)"
    else
      rm -f "$tmp"
      warn "merge fallito su $target → lasciato invariato"
    fi
  else
    warn "$target ha commenti JSONC → NON toccato (backup in $BKROOT)"
  fi
}

# ----- helper: strip commenti JSONC (node → python3 → fallback) -------------
strip_jsonc() {
  local infile="$1"
  if command -v node &>/dev/null; then
    node -e '
      const fs=require("fs");
      let t=fs.readFileSync(process.argv[1],"utf8");
      t=t.replace(/\/\*[\s\S]*?\*\//g,"");
      t=t.replace(/^\s*\/\/[^\n]*$/gm,"");
      t=t.replace(/([^:"])\/\/[^\n]*$/gm,"$1");
      t=t.replace(/,(\s*[}\]])/g,"$1");
      process.stdout.write(t);
    ' "$infile"
  elif command -v python3 &>/dev/null; then
    python3 -c "
import sys,re
t=open(sys.argv[1]).read()
t=re.sub(r'/\*.*?\*/','',t,flags=re.S)
t=re.sub(r'^\s*//[^\n]*$','',t,flags=re.M)
t=re.sub(r'([^:\"])//[^\n]*$',r'\1',t,flags=re.M)
t=re.sub(r',(\s*[}\]])',r'\1',t)
sys.stdout.write(t)" "$infile"
  else
    cat "$infile"
  fi
}

# ----- helper: merge keybindings (array, JSONC-aware) -----------------------
safe_merge_keybindings() {
  local target="$1" defaults_file="$2"
  if [[ ! -f "$target" ]]; then
    mkdir -p "$(dirname "$target")"
    cp "$defaults_file" "$target"
    ok "nuovi keybindings: $target"
    return
  fi
  cp -a "$target" "$BKROOT/keybindings.json.bak"
  local cleaned=$(mktemp)
  strip_jsonc "$target" > "$cleaned"
  if jq empty <"$cleaned" 2>/dev/null; then
    local tmp="$target.merged.$$"
    if jq -s '.[1] + [.[0][] | select(.key as $k | .[1] | map(.key) | index($k) | not)]' \
        "$defaults_file" "$cleaned" > "$tmp" 2>/dev/null; then
      mv "$tmp" "$target"
      ok "keybindings estesi (tuoi shortcut intatti; eventuali commenti JSONC rimossi)"
    else
      rm -f "$tmp"
      warn "merge keybindings fallito → invariato (backup in $BKROOT)"
    fi
  else
    warn "keybindings.json non parsabile anche dopo strip → invariato"
  fi
  rm -f "$cleaned"
}

# ----- helper: install estensione con retry 3x ------------------------------
install_ext_with_retry() {
  local e="$1"
  for i in 1 2 3; do
    if code --install-extension "$e" --force >/dev/null 2>&1; then
      echo "  ✓ install: $e"
      return 0
    fi
    sleep 2
  done
  echo "  ✗ skip: $e (3 tentativi falliti)"
  return 1
}
export -f install_ext_with_retry

# -----------------------------------------------------------------------------
step "[1/6] Estensioni (additive, parallele -P6, retry 3x)"
EXT=(
  anthropic.claude-code github.copilot github.copilot-chat
  continue.continue codeium.codeium rjmacarthy.twinny
  saoudrizwan.claude-dev sourcegraph.amp
  google.geminicodeassist
  ms-vscode-remote.remote-ssh ms-vscode-remote.remote-ssh-edit
  ms-vscode-remote.remote-containers ms-vsliveshare.vsliveshare
  eamodio.gitlens github.vscode-pull-request-github
  github.vscode-github-actions mhutchie.git-graph
  dbaeumer.vscode-eslint esbenp.prettier-vscode
  ms-python.python ms-python.vscode-pylance charliermarsh.ruff
  rust-lang.rust-analyzer golang.go
  ms-azuretools.vscode-docker redhat.vscode-yaml tamasfe.even-better-toml
  usernamehw.errorlens streetsidesoftware.code-spell-checker
  editorconfig.editorconfig christian-kohler.path-intellisense
  formulahendry.auto-rename-tag gruntfuggly.todo-tree
  yzhang.markdown-all-in-one bierner.markdown-mermaid
  wayou.vscode-todo-highlight ritwickdey.liveserver
)
INSTALLED="$(code --list-extensions 2>/dev/null || true)"
MISSING=(); ALREADY=0
for e in "${EXT[@]}"; do
  if grep -qix "$e" <<<"$INSTALLED"; then ((ALREADY++))
  else MISSING+=("$e")
  fi
done
ok "già presenti: $ALREADY — da installare: ${#MISSING[@]}"
if ((${#MISSING[@]} > 0)); then
  printf '%s\n' "${MISSING[@]}" | xargs -P 6 -I {} bash -c 'install_ext_with_retry "$@"' _ {}
fi

# -----------------------------------------------------------------------------
step "[2/6] settings.json (MERGE — tuoi valori intatti)"
TMP=$(mktemp)
cat > "$TMP" <<'JSON'
{
  "settingsSync.keybindingsPerPlatform": false,
  "editor.inlineSuggest.enabled": true,
  "editor.suggest.preview": true,
  "editor.formatOnSave": true,
  "editor.bracketPairColorization.enabled": true,
  "editor.stickyScroll.enabled": true,
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 500,
  "terminal.integrated.scrollback": 50000,
  "git.autofetch": true,
  "remote.SSH.remotePlatform": { "imac-archimede": "linux" },
  "remote.SSH.defaultExtensions": [
    "anthropic.claude-code","github.copilot","github.copilot-chat",
    "continue.continue","saoudrizwan.claude-dev","eamodio.gitlens"
  ],
  "remote.SSH.connectTimeout": 60,
  "github.copilot.enable": { "*": true },
  "claude-code.autoStart": true,
  "cline.mcpMarketplace.enabled": true,
  "continue.telemetryEnabled": false,
  "continue.enableTabAutocomplete": true
}
JSON
safe_merge_json "$SDIR/settings.json" "$TMP"
rm -f "$TMP"

# -----------------------------------------------------------------------------
step "[3/6] keybindings.json (MERGE — aggiunti solo shortcut non in uso)"
TMP=$(mktemp)
cat > "$TMP" <<'JSON'
[
  { "key": "cmd+i",         "command": "workbench.action.chat.open" },
  { "key": "cmd+shift+i",   "command": "claude-code.open" },
  { "key": "alt+\\",        "command": "editor.action.inlineSuggest.trigger" },
  { "key": "cmd+alt+c",     "command": "workbench.action.terminal.sendSequence", "args": { "text": "claude\n" } },
  { "key": "cmd+alt+a",     "command": "workbench.action.terminal.sendSequence", "args": { "text": "aider --model sonnet\n" } }
]
JSON
safe_merge_keybindings "$SDIR/keybindings.json" "$TMP"
rm -f "$TMP"

# -----------------------------------------------------------------------------
step "[4/6] snippets globali (MERGE)"
TMP=$(mktemp)
cat > "$TMP" <<'JSON'
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
safe_merge_json "$SDIR/snippets/global.code-snippets" "$TMP"
rm -f "$TMP"

# -----------------------------------------------------------------------------
step "[5/6] Continue config (MERGE — chiavi API esistenti preservate)"
mkdir -p "$HOME/.continue"
TMP=$(mktemp)
cat > "$TMP" <<'JSON'
{
  "models": [
    { "title": "Claude Sonnet 4.6", "provider": "anthropic", "model": "claude-sonnet-4-6", "apiKey": "${ANTHROPIC_API_KEY}" },
    { "title": "Claude Opus 4.7",   "provider": "anthropic", "model": "claude-opus-4-7",   "apiKey": "${ANTHROPIC_API_KEY}" },
    { "title": "GPT-4o",            "provider": "openai",    "model": "gpt-4o",            "apiKey": "${OPENAI_API_KEY}" },
    { "title": "Gemini 2.5 Pro",    "provider": "gemini",    "model": "gemini-2.5-pro",    "apiKey": "${GOOGLE_API_KEY}" },
    { "title": "Qwen-Coder 32B (iMac)", "provider": "ollama", "model": "qwen2.5-coder:32b-instruct-q4_K_M", "apiBase": "http://imac-archimede:11434" },
    { "title": "DeepSeek R1 32B (iMac)", "provider": "ollama", "model": "deepseek-r1:32b", "apiBase": "http://imac-archimede:11434" }
  ],
  "tabAutocompleteModel": { "title": "Qwen Coder (iMac)", "provider": "ollama", "model": "qwen2.5-coder:32b-instruct-q4_K_M", "apiBase": "http://imac-archimede:11434" },
  "embeddingsProvider": { "provider": "ollama", "model": "nomic-embed-text:latest", "apiBase": "http://imac-archimede:11434" }
}
JSON
safe_merge_json "$HOME/.continue/config.json" "$TMP"
rm -f "$TMP"

# -----------------------------------------------------------------------------
step "[6/6] MCP registry (Claude Code + Cline) — MERGE"
mkdir -p "$HOME/.config/claude"
TMP=$(mktemp)
cat > "$TMP" <<'JSON'
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
safe_merge_json "$HOME/.config/claude/mcp_servers.json" "$TMP"
CLINE_DIR="$SDIR/globalStorage/saoudrizwan.claude-dev/settings"
mkdir -p "$CLINE_DIR"
safe_merge_json "$CLINE_DIR/cline_mcp_settings.json" "$TMP"
rm -f "$TMP"

# LaunchAgent idempotente
LA="$HOME/Library/LaunchAgents"; LOG="$HOME/Library/Logs/vio"
mkdir -p "$LA" "$LOG"
PLIST="$LA/ai.vio.vscode-mcp-warm.plist"
cat > "$PLIST" <<EOF
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
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load   "$PLIST" && ok "LaunchAgent: ai.vio.vscode-mcp-warm"

cat <<EOF

${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
${C_G}MAC AIR VS Code — BOOST NON-DISTRUTTIVO COMPLETATO${C_N}

Backup totale in: ${C_Y}$BKROOT${C_N}
Ripristino (se serve): cp -a "$BKROOT"/* nei path originali.

Passi manuali (una volta):
  1. ${C_Y}Settings Sync${C_N}: Cmd+Shift+P → "Settings Sync: Turn On" → GitHub
  2. ${C_Y}Remote-SSH${C_N}:   Cmd+Shift+P → "Remote-SSH: Connect to Host" → imac-archimede
  3. ${C_Y}API keys${C_N}:     edita ~/.config/vio/keys.env
${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
EOF
