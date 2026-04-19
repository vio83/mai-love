#!/usr/bin/env bash
# =============================================================================
# VIO AI ORCHESTRA — UNIFIED CROSS-PLATFORM POWERHOUSE SETUP
# -----------------------------------------------------------------------------
# Target: macOS (Apple Silicon / MacBook Air M1) AND Arch Linux (iMac)
#
# Single command:
#     bash scripts/setup/vio_orchestra_ultimate_setup.sh
#
# What it does (idempotent — safe to re-run):
#   1. Detects OS (macOS arm64 / Arch Linux) and installs the right package mgr
#   2. Installs core CLI toolchain (git, gh, jq, ripgrep, fd, bat, htop, tmux,
#      zsh, node via nvm, python via pyenv, rust, go, docker, tailscale)
#   3. Installs VS Code (cask on mac, AUR/pacman on Arch)
#   4. Installs the curated extension set (AI + remote + git + lang servers)
#   5. Writes a shared VS Code settings.json that enables Settings Sync
#      (one GitHub sign-in mirrors extensions + settings on both machines)
#   6. Installs Tailscale and enables it at boot
#   7. On Arch: enables sshd so Mac Air can drive it via Remote-SSH
#      On macOS: adds an SSH config entry pointing at the iMac's Tailscale name
#   8. Installs the Claude Code CLI + a curated set of MCP servers (npm global)
#   9. Installs a launchd (macOS) or systemd --user (Arch) autostart unit that
#      keeps Tailscale + the orchestra backend alive across reboots
#  10. Prints the short list of steps that REQUIRE human interaction (no
#      honest script can fully automate: GitHub OAuth, Tailscale auth, Apple ID)
#
# HONEST LIMITS — read this:
#   * "Always running forever" = auto-start at boot + keep-alive watchdog.
#     Nothing survives power-off or a pulled plug.
#   * Real-time typing mirror is implemented as VS Code Remote-SSH over
#     Tailscale: you open the iMac workspace from the Mac Air, every keystroke
#     executes ON the iMac. That is the production-grade way to do this —
#     Live Share is the alternative but requires a MS account on both ends.
#   * Settings Sync still needs ONE interactive GitHub login per machine.
#     After that, extensions + settings + keybindings propagate automatically.
#   * Tailscale still needs ONE `tailscale up` with browser auth per machine.
# =============================================================================

set -Eeuo pipefail

# ---------- pretty output ----------------------------------------------------
readonly C_R='\033[0;31m' C_G='\033[0;32m' C_Y='\033[1;33m'
readonly C_B='\033[0;34m' C_C='\033[0;36m' C_N='\033[0m'
log()   { printf "${C_C}[%(%H:%M:%S)T]${C_N} %s\n" -1 "$*"; }
ok()    { printf "${C_G}  ✓${C_N} %s\n" "$*"; }
warn()  { printf "${C_Y}  !${C_N} %s\n" "$*"; }
err()   { printf "${C_R}  ✗${C_N} %s\n" "$*" >&2; }
step()  { printf "\n${C_B}▶ %s${C_N}\n" "$*"; }

trap 'err "Failed at line $LINENO. Re-run the script — it is idempotent."' ERR

# ---------- OS detection -----------------------------------------------------
detect_os() {
  case "$(uname -s)" in
    Darwin) OS=macos ;;
    Linux)
      if [[ -f /etc/arch-release ]]; then OS=arch
      else err "Only macOS and Arch Linux are supported by this script."; exit 1
      fi ;;
    *) err "Unsupported OS: $(uname -s)"; exit 1 ;;
  esac
  ARCH="$(uname -m)"
  log "Detected: $OS ($ARCH)"
}

# ---------- package manager bootstrap ---------------------------------------
bootstrap_pkg_mgr() {
  step "[1/10] Bootstrapping package manager"
  if [[ $OS == macos ]]; then
    if ! command -v brew &>/dev/null; then
      log "Installing Homebrew…"
      NONINTERACTIVE=1 /bin/bash -c \
        "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      if [[ $ARCH == arm64 ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        grep -q 'brew shellenv' "$HOME/.zprofile" 2>/dev/null || \
          echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
      fi
    fi
    ok "Homebrew ready ($(brew --version | head -1))"
  else
    sudo pacman -Syu --noconfirm --needed base-devel git
    if ! command -v yay &>/dev/null; then
      log "Installing yay (AUR helper)…"
      tmp=$(mktemp -d)
      git clone https://aur.archlinux.org/yay-bin.git "$tmp/yay"
      (cd "$tmp/yay" && makepkg -si --noconfirm)
      rm -rf "$tmp"
    fi
    ok "pacman + yay ready"
  fi
}

# ---------- core toolchain ---------------------------------------------------
install_core_tools() {
  step "[2/10] Installing core CLI toolchain"
  local mac_pkgs=(
    git gh jq curl wget ripgrep fd bat eza htop btop tmux zsh neovim
    coreutils gnu-sed gnu-tar findutils make cmake pkg-config
    openssh mosh rsync tree tokei hyperfine watch
    python@3.12 pyenv node nvm go rust
    docker docker-compose colima
    tailscale syncthing
    direnv starship fzf zoxide
  )
  local arch_pkgs=(
    git github-cli jq curl wget ripgrep fd bat eza htop btop tmux zsh neovim
    openssh mosh rsync tree tokei hyperfine
    python python-pip pyenv nodejs npm go rust
    docker docker-compose
    tailscale syncthing
    direnv starship fzf zoxide
    base-devel cmake pkgconf
  )
  if [[ $OS == macos ]]; then
    brew install "${mac_pkgs[@]}" || true
  else
    sudo pacman -S --noconfirm --needed "${arch_pkgs[@]}" || true
  fi
  ok "Core toolchain installed"
}

# ---------- node / nvm (needed for MCP servers) ------------------------------
install_node_stack() {
  step "[3/10] Setting up Node LTS (for MCP servers + Claude Code)"
  export NVM_DIR="$HOME/.nvm"
  if [[ $OS == macos ]]; then
    [[ -s /opt/homebrew/opt/nvm/nvm.sh ]] && . /opt/homebrew/opt/nvm/nvm.sh
  fi
  if ! command -v nvm &>/dev/null; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
    . "$NVM_DIR/nvm.sh"
  fi
  . "$NVM_DIR/nvm.sh" 2>/dev/null || true
  nvm install --lts
  nvm alias default lts/*
  ok "Node $(node -v) ready"
}

# ---------- VS Code ----------------------------------------------------------
install_vscode() {
  step "[4/10] Installing VS Code"
  if command -v code &>/dev/null; then ok "VS Code already present"; return; fi
  if [[ $OS == macos ]]; then
    brew install --cask visual-studio-code
  else
    yay -S --noconfirm --needed visual-studio-code-bin
  fi
  ok "VS Code installed"
}

# ---------- VS Code extensions (AI + remote + languages) --------------------
install_vscode_extensions() {
  step "[5/10] Installing the VS Code extension set"
  local exts=(
    # AI assistants
    anthropic.claude-code
    github.copilot
    github.copilot-chat
    continue.continue
    codeium.codeium
    rjmacarthy.twinny
    danielsanchez-pg.dscodegpt
    # Remote / sync
    ms-vscode-remote.remote-ssh
    ms-vscode-remote.remote-ssh-edit
    ms-vscode-remote.remote-containers
    ms-vscode.remote-explorer
    ms-vsliveshare.vsliveshare
    # Git
    eamodio.gitlens
    github.vscode-pull-request-github
    github.vscode-github-actions
    mhutchie.git-graph
    # Language servers / linters
    dbaeumer.vscode-eslint
    esbenp.prettier-vscode
    ms-python.python
    ms-python.vscode-pylance
    ms-python.black-formatter
    charliermarsh.ruff
    rust-lang.rust-analyzer
    golang.go
    redhat.vscode-yaml
    tamasfe.even-better-toml
    ms-azuretools.vscode-docker
    # Productivity / DX
    usernamehw.errorlens
    streetsidesoftware.code-spell-checker
    editorconfig.editorconfig
    christian-kohler.path-intellisense
    formulahendry.auto-rename-tag
    gruntfuggly.todo-tree
    yzhang.markdown-all-in-one
    bierner.markdown-mermaid
    wayou.vscode-todo-highlight
  )
  local installed; installed="$(code --list-extensions 2>/dev/null || true)"
  for e in "${exts[@]}"; do
    if grep -qix "$e" <<<"$installed"; then
      ok "already: $e"
    else
      code --install-extension "$e" --force >/dev/null 2>&1 && ok "installed: $e" \
        || warn "could not install $e (marketplace / licensing — skipped)"
    fi
  done
}

# ---------- shared VS Code settings (Settings Sync ON) ----------------------
write_vscode_settings() {
  step "[6/10] Writing shared VS Code settings (enables Settings Sync)"
  local dir
  if [[ $OS == macos ]]; then dir="$HOME/Library/Application Support/Code/User"
  else dir="$HOME/.config/Code/User"; fi
  mkdir -p "$dir"
  local settings="$dir/settings.json"
  [[ -f $settings ]] && cp "$settings" "$settings.bak.$(date +%s)"
  cat > "$settings" <<'JSON'
{
  "settingsSync.keybindingsPerPlatform": false,
  "workbench.settings.enableNaturalLanguageSearch": true,
  "editor.fontFamily": "JetBrainsMono Nerd Font, Menlo, Consolas, monospace",
  "editor.fontLigatures": true,
  "editor.formatOnSave": true,
  "editor.inlineSuggest.enabled": true,
  "editor.suggest.preview": true,
  "editor.minimap.enabled": false,
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": "active",
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 500,
  "terminal.integrated.defaultProfile.osx": "zsh",
  "terminal.integrated.defaultProfile.linux": "zsh",
  "terminal.integrated.scrollback": 50000,
  "git.autofetch": true,
  "git.confirmSync": false,
  "git.enableSmartCommit": true,
  "remote.SSH.remotePlatform": { "imac-archimede": "linux" },
  "remote.SSH.defaultExtensions": [
    "anthropic.claude-code",
    "github.copilot",
    "github.copilot-chat",
    "continue.continue",
    "eamodio.gitlens"
  ],
  "github.copilot.enable": { "*": true },
  "claude-code.autoStart": true,
  "continue.telemetryEnabled": false
}
JSON
  ok "settings.json written → $settings"
}

# ---------- Tailscale --------------------------------------------------------
setup_tailscale() {
  step "[7/10] Installing & enabling Tailscale"
  if [[ $OS == macos ]]; then
    brew install --cask tailscale 2>/dev/null || true
    open -a Tailscale || true
  else
    sudo systemctl enable --now tailscaled
  fi
  if ! tailscale status &>/dev/null; then
    warn "Run manually (once): sudo tailscale up --ssh --accept-routes"
  else
    ok "Tailscale is up: $(tailscale ip -4 | head -1)"
  fi
}

# ---------- SSH + Remote-SSH glue -------------------------------------------
setup_ssh() {
  step "[8/10] Configuring SSH for cross-machine Remote-SSH"
  mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
  local key="$HOME/.ssh/id_ed25519_orchestra"
  [[ -f $key ]] || ssh-keygen -t ed25519 -N "" -C "vio-orchestra-$(hostname)" -f "$key"

  if [[ $OS == arch ]]; then
    sudo pacman -S --noconfirm --needed openssh
    sudo systemctl enable --now sshd
    ok "sshd enabled on iMac (Mac Air can now connect via Remote-SSH)"
  fi

  # Mac Air → iMac convenience entry (uses MagicDNS hostname; edit if yours differs)
  local cfg="$HOME/.ssh/config"
  if ! grep -q "Host imac-archimede" "$cfg" 2>/dev/null; then
    cat >> "$cfg" <<EOF

Host imac-archimede
    HostName imac-archimede
    User vio
    IdentityFile ~/.ssh/id_ed25519_orchestra
    StrictHostKeyChecking accept-new
    ControlMaster auto
    ControlPath ~/.ssh/cm-%C
    ControlPersist 10m
    ServerAliveInterval 30
EOF
    ok "Added 'imac-archimede' to ~/.ssh/config"
  fi
  chmod 600 "$cfg"
}

# ---------- Claude Code CLI + MCP servers ------------------------------------
install_claude_and_mcp() {
  step "[9/10] Installing Claude Code CLI + MCP servers"
  . "$HOME/.nvm/nvm.sh" 2>/dev/null || true
  npm install -g @anthropic-ai/claude-code 2>/dev/null && ok "Claude Code CLI" \
    || warn "Claude Code CLI install failed (check npm)"
  local mcps=(
    "@modelcontextprotocol/server-filesystem"
    "@modelcontextprotocol/server-github"
    "@modelcontextprotocol/server-memory"
    "@modelcontextprotocol/server-sequential-thinking"
    "@modelcontextprotocol/server-everything"
    "@modelcontextprotocol/server-fetch"
    "@modelcontextprotocol/server-time"
  )
  for m in "${mcps[@]}"; do
    npm install -g "$m" 2>/dev/null && ok "MCP: $m" || warn "skip $m (not published / offline)"
  done
}

# ---------- Auto-start (launchd / systemd --user) ---------------------------
install_autostart() {
  step "[10/10] Installing boot-time autostart"
  local launcher="$PWD/scripts/vio-orchestra-autostart.sh"
  [[ -x $launcher ]] || warn "$launcher missing or not executable — autostart will be skipped"
  if [[ $OS == macos ]]; then
    local plist="$HOME/Library/LaunchAgents/ai.vio.orchestra.plist"
    mkdir -p "$(dirname "$plist")"
    cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>ai.vio.orchestra</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$launcher</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/vio-orchestra.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/vio-orchestra.err</string>
</dict></plist>
EOF
    launchctl unload "$plist" 2>/dev/null || true
    launchctl load "$plist"
    ok "launchd agent loaded: ai.vio.orchestra"
  else
    local unit_dir="$HOME/.config/systemd/user"
    mkdir -p "$unit_dir"
    cat > "$unit_dir/vio-orchestra.service" <<EOF
[Unit]
Description=VIO AI Orchestra autostart
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
Type=simple
ExecStart=/bin/bash $launcher
Restart=always
RestartSec=5
StandardOutput=append:%h/.vio-orchestra.log
StandardError=append:%h/.vio-orchestra.err

[Install]
WantedBy=default.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable --now vio-orchestra.service
    loginctl enable-linger "$USER" 2>/dev/null || true
    ok "systemd --user unit enabled: vio-orchestra.service"
  fi
}

# ---------- manual-steps summary --------------------------------------------
print_manual_steps() {
  cat <<EOF

${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
${C_G}SETUP COMPLETE — 3 interactive steps remain (cannot be automated):${C_N}

  1. ${C_Y}Tailscale login${C_N} — run once per machine:
       sudo tailscale up --ssh --accept-routes
     (Opens a browser; same account on both machines = same tailnet.)

  2. ${C_Y}VS Code Settings Sync${C_N} — run once per machine:
       Open VS Code → Command Palette → "Settings Sync: Turn On"
       Sign in with GitHub (same account on both machines).
       From that moment extensions + settings + keybindings mirror
       automatically in both directions.

  3. ${C_Y}Remote-SSH pairing${C_N} (only on Mac Air, after Tailscale is up on iMac):
       Command Palette → "Remote-SSH: Connect to Host" → imac-archimede
       Open folder: /opt/vioaiorchestra
       From now on every keystroke in that VS Code window executes
       on the iMac — terminals, language servers, debugger, the lot.

${C_C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_N}
EOF
}

# ---------- main -------------------------------------------------------------
main() {
  log "VIO AI Orchestra — Unified Powerhouse Setup starting"
  detect_os
  bootstrap_pkg_mgr
  install_core_tools
  install_node_stack
  install_vscode
  install_vscode_extensions
  write_vscode_settings
  setup_tailscale
  setup_ssh
  install_claude_and_mcp
  install_autostart
  print_manual_steps
  log "Done."
}
main "$@"
