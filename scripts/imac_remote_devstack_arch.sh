#!/bin/bash
# Bootstrap dev stack on iMac Arch Linux
# Safe mode: install/enable only, no destructive actions.

set -euo pipefail

LOG="$HOME/imac_remote_devstack.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== iMac Arch Dev Stack Bootstrap $(date) ==="

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "[ERROR] This script must run on Linux"
  exit 1
fi

if ! command -v pacman >/dev/null 2>&1; then
  echo "[ERROR] pacman not found; expected Arch Linux"
  exit 1
fi

# Core development stack
PKGS=(
  git
  openssh
  rsync
  curl
  wget
  zip
  unzip
  base-devel
  python
  python-pip
  python-virtualenv
  nodejs
  npm
  go
  jdk17-openjdk
  docker
  podman
  code
  ripgrep
  fd
  tmux
  htop
)

echo "[INFO] Installing packages..."
sudo pacman -Syu --noconfirm
sudo pacman -S --needed --noconfirm "${PKGS[@]}"

# Rust toolchain (skip if rust already installed via system package)
if command -v rustup >/dev/null 2>&1; then
  rustup default stable || true
elif ! command -v rustc >/dev/null 2>&1; then
  echo "[INFO] Neither rustup nor rustc found, installing rustup via pacman..."
  sudo pacman -S --needed --noconfirm rustup || true
  rustup default stable || true
else
  echo "[INFO] rustc already installed via system package, skipping rustup"
fi

# Docker service
sudo systemctl enable --now docker || true
sudo usermod -aG docker "$USER" || true

# Workspace folders
mkdir -p "$HOME/work" "$HOME/.config/Code/User" "$HOME/.vio83"

# Python toolchain quick sanity
python3 --version || true
pip3 --version || true
node --version || true
npm --version || true
go version || true
rustc --version || true
code --version || true

echo "[INFO] Installing essential VS Code extensions..."
EXTS=(
  ms-python.python
  ms-python.vscode-pylance
  charliermarsh.ruff
  esbenp.prettier-vscode
  dbaeumer.vscode-eslint
  github.copilot
  github.copilot-chat
  eamodio.gitlens
  ms-vscode-remote.remote-ssh
  ms-vscode.remote-explorer
  ms-azuretools.vscode-docker
  redhat.vscode-yaml
)

for ext in "${EXTS[@]}"; do
  code --install-extension "$ext" --force || true
done

echo "[INFO] Creating user systemd task: vio-imac-health.timer"
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/vio-imac-health.service" <<'EOF'
[Unit]
Description=VIO iMac health snapshot

[Service]
Type=oneshot
ExecStart=/bin/bash -lc 'echo "$(date)" >> ~/.vio83/health.log; uptime >> ~/.vio83/health.log; df -h / >> ~/.vio83/health.log; free -h >> ~/.vio83/health.log; echo "---" >> ~/.vio83/health.log'
EOF

cat > "$HOME/.config/systemd/user/vio-imac-health.timer" <<'EOF'
[Unit]
Description=Run VIO iMac health snapshot every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Unit=vio-imac-health.service

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now vio-imac-health.timer || true

echo "=== iMac Arch Dev Stack Bootstrap COMPLETED $(date) ==="
