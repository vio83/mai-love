#!/usr/bin/env bash
# Bootstrap/check VS Code extensions and optional macOS developer tools.
set -euo pipefail

MODE="${1:-check}" # check | install

REQUIRED_EXT=(
  "ms-python.python"
  "ms-python.vscode-pylance"
  "dbaeumer.vscode-eslint"
  "esbenp.prettier-vscode"
  "github.vscode-github-actions"
  "github.copilot-chat"
  "eamodio.gitlens"
  "usernamehw.errorlens"
)

OPTIONAL_BREW=(
  "gh"
  "jq"
  "ripgrep"
  "ollama"
)

info() { echo "[INFO] $*"; }
warn() { echo "[WARN] $*"; }

has_cmd() { command -v "$1" >/dev/null 2>&1; }

ensure_code_cli() {
  if has_cmd code; then
    return 0
  fi
  warn "'code' CLI non trovato. In VS Code: Command Palette -> 'Shell Command: Install code command in PATH'"
  return 1
}

check_extensions() {
  ensure_code_cli || return 1
  local installed
  installed=$(code --list-extensions 2>/dev/null || true)
  for ext in "${REQUIRED_EXT[@]}"; do
    if echo "$installed" | grep -Fxq "$ext"; then
      info "OK extension: $ext"
    else
      warn "MISSING extension: $ext"
      if [ "$MODE" = "install" ]; then
        code --install-extension "$ext" || warn "Install fallita: $ext"
      fi
    fi
  done
}

check_brew_tools() {
  if ! has_cmd brew; then
    warn "Homebrew non trovato. Installa da https://brew.sh"
    return 0
  fi

  for t in "${OPTIONAL_BREW[@]}"; do
    if has_cmd "$t"; then
      info "OK tool: $t"
    else
      warn "MISSING tool: $t"
      if [ "$MODE" = "install" ]; then
        brew install "$t" || warn "Install fallita: $t"
      fi
    fi
  done
}

info "Bootstrap mode: $MODE"
check_extensions
check_brew_tools

info "Completato"
