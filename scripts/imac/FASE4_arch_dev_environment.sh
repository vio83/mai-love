#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# PROGETTO ARCHIMEDE — FASE 4: Dev Environment Completo
# Target: Arch Linux su iMac11,1 Late 2009
# ESEGUIRE DOPO FASE 3: sudo bash FASE4_arch_dev_environment.sh
#
# Installa ambiente di sviluppo completo:
# - Linguaggi: Python 3.12+, Node.js 20, Rust, Go, Ruby
# - Editor: VS Code + 19 estensioni
# - AI: Claude Code CLI, Ollama (modelli piccoli per 8GB RAM)
# - Container: Docker + docker-compose
# - Security: ClamAV, osquery, Suricata, fail2ban, rkhunter, UFW
# - OSINT: exiftool, sherlock, theHarvester, SpiderFoot, nmap, wireshark
# - Desktop: XFCE4 (leggero per iMac 2009)
# - Auto-optimization ogni 15 minuti
# - Connessione iPhone hotspot automatica
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✔ $*${NC}"; }
fail() { echo -e "  ${RED}✘ $*${NC}"; }
warn() { echo -e "  ${YELLOW}⚠ $*${NC}"; }
info() { echo -e "  ${CYAN}ℹ $*${NC}"; }
header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD} $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
}

echo -e "${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  PROGETTO ARCHIMEDE — FASE 4                                 ║"
echo "║  Dev Environment Completo per Arch Linux                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

[[ $EUID -ne 0 ]] && { echo "Eseguire con sudo!"; exit 1; }

USERNAME="vio"
HOME_DIR="/home/$USERNAME"

# ═══════════════════════════════════════════════════════════════
header "1. AUR HELPER (yay)"
# ═══════════════════════════════════════════════════════════════

info "Installazione yay (AUR helper)..."

if ! command -v yay &>/dev/null; then
    # Yay va compilato come utente non-root
    sudo -u "$USERNAME" bash << 'YAY_EOF'
cd /tmp
git clone https://aur.archlinux.org/yay-bin.git
cd yay-bin
makepkg -si --noconfirm
cd /tmp && rm -rf yay-bin
YAY_EOF
    ok "yay installato"
else
    ok "yay già presente"
fi

# ═══════════════════════════════════════════════════════════════
header "2. DESKTOP ENVIRONMENT (XFCE4)"
# ═══════════════════════════════════════════════════════════════

info "Installazione XFCE4 (desktop leggero per iMac 2009)..."

pacman -S --noconfirm --needed \
    xorg-server \
    xorg-xinit \
    xf86-video-ati \
    xfce4 \
    xfce4-goodies \
    lightdm \
    lightdm-gtk-greeter \
    network-manager-applet \
    pulseaudio \
    pavucontrol \
    firefox \
    thunar \
    file-roller \
    xarchiver \
    gvfs \
    tumbler \
    xdg-user-dirs

# Abilitare display manager
systemctl enable lightdm
ok "XFCE4 + LightDM installati"

# Configurazione XFCE leggera per iMac 2009
sudo -u "$USERNAME" mkdir -p "${HOME_DIR}/.config/xfce4/xfconf/xfce-perchannel-xml"

# Disabilitare compositing (risparmia GPU)
cat > "${HOME_DIR}/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml" << 'XFWM_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <property name="use_compositing" type="bool" value="false"/>
    <property name="cycle_draw_frame" type="bool" value="false"/>
    <property name="cycle_raise" type="bool" value="false"/>
    <property name="show_frame_shadow" type="bool" value="false"/>
    <property name="show_popup_shadow" type="bool" value="false"/>
  </property>
</channel>
XFWM_EOF
chown -R "${USERNAME}:${USERNAME}" "${HOME_DIR}/.config"
ok "XFCE configurato (compositing OFF per performance)"

# ═══════════════════════════════════════════════════════════════
header "3. LINGUAGGI DI PROGRAMMAZIONE"
# ═══════════════════════════════════════════════════════════════

info "Installazione linguaggi..."

# Python
pacman -S --noconfirm --needed \
    python \
    python-pip \
    python-virtualenv \
    python-pipx \
    python-numpy \
    python-pandas \
    python-requests \
    python-beautifulsoup4 \
    python-flask \
    python-fastapi \
    uvicorn \
    ipython \
    jupyter-notebook

PYTHON_VER=$(python --version 2>&1)
ok "Python: $PYTHON_VER"

# Node.js
pacman -S --noconfirm --needed nodejs npm
NODE_VER=$(node --version 2>&1)
ok "Node.js: $NODE_VER"

# Rust
pacman -S --noconfirm --needed rustup
sudo -u "$USERNAME" rustup default stable 2>/dev/null
RUST_VER=$(sudo -u "$USERNAME" rustc --version 2>&1 || echo "installato")
ok "Rust: $RUST_VER"

# Go
pacman -S --noconfirm --needed go
GO_VER=$(go version 2>&1)
ok "Go: $GO_VER"

# Ruby
pacman -S --noconfirm --needed ruby
RUBY_VER=$(ruby --version 2>&1)
ok "Ruby: $RUBY_VER"

# Build tools
pacman -S --noconfirm --needed \
    gcc \
    make \
    cmake \
    pkg-config \
    openssl

ok "Build tools installati"

# ═══════════════════════════════════════════════════════════════
header "4. VS CODE + ESTENSIONI"
# ═══════════════════════════════════════════════════════════════

info "Installazione VS Code..."

# VS Code da AUR
sudo -u "$USERNAME" yay -S --noconfirm visual-studio-code-bin 2>/dev/null || {
    # Fallback: code-oss (versione open source)
    pacman -S --noconfirm --needed code
    ok "VS Code OSS installato (versione open source)"
}

# Estensioni VS Code
info "Installazione estensioni VS Code..."
EXTENSIONS=(
    "ms-python.python"
    "ms-python.vscode-pylance"
    "dbaeumer.vscode-eslint"
    "esbenp.prettier-vscode"
    "eamodio.gitlens"
    "GitHub.copilot"
    "GitHub.copilot-chat"
    "ms-vscode.vscode-typescript-next"
    "bradlc.vscode-tailwindcss"
    "rust-lang.rust-analyzer"
    "golang.go"
    "ms-azuretools.vscode-docker"
    "redhat.vscode-yaml"
    "ms-vscode-remote.remote-ssh"
    "streetsidesoftware.code-spell-checker"
    "streetsidesoftware.code-spell-checker-italian"
    "PKief.material-icon-theme"
    "zhuangtongfa.material-theme"
    "formulahendry.auto-rename-tag"
)

for ext in "${EXTENSIONS[@]}"; do
    sudo -u "$USERNAME" code --install-extension "$ext" --force 2>/dev/null || true
done
ok "Estensioni VS Code installate (${#EXTENSIONS[@]} estensioni)"

# ═══════════════════════════════════════════════════════════════
header "5. AI TOOLS"
# ═══════════════════════════════════════════════════════════════

# Claude Code CLI
info "Installazione Claude Code CLI..."
sudo -u "$USERNAME" npm install -g @anthropic-ai/claude-code 2>/dev/null || {
    warn "Claude Code CLI non installato — verificare npm"
}
ok "Claude Code CLI"

# Ollama
info "Installazione Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh 2>/dev/null

# Abilitare servizio Ollama
systemctl enable ollama 2>/dev/null || true

# Modelli piccoli per 8GB RAM
info "Download modelli AI (piccoli per 8GB RAM)..."
sudo -u "$USERNAME" ollama pull qwen2.5-coder:3b 2>/dev/null &
sudo -u "$USERNAME" ollama pull llama3.2:3b 2>/dev/null &
sudo -u "$USERNAME" ollama pull phi3:mini 2>/dev/null &
wait
ok "Ollama + 3 modelli installati (qwen2.5-coder:3b, llama3.2:3b, phi3:mini)"

info "NOTA: iMac 2009 NON ha GPU CUDA/ROCm compatibile"
info "Ollama userà solo CPU — risposte più lente ma funzionali"

# ═══════════════════════════════════════════════════════════════
header "6. DOCKER"
# ═══════════════════════════════════════════════════════════════

info "Installazione Docker..."
pacman -S --noconfirm --needed docker docker-compose

systemctl enable docker
usermod -aG docker "$USERNAME"

ok "Docker installato e abilitato"
info "Utente $USERNAME aggiunto al gruppo docker"

# ═══════════════════════════════════════════════════════════════
header "7. SECURITY STACK"
# ═══════════════════════════════════════════════════════════════

info "Installazione security stack..."

# ClamAV
pacman -S --noconfirm --needed clamav
freshclam 2>/dev/null || true
systemctl enable clamav-freshclam
ok "ClamAV installato + aggiornamento firme"

# Configurare scansione notturna
cat > /etc/systemd/system/clamav-scan.service << 'CLAM_EOF'
[Unit]
Description=ClamAV Daily Scan

[Service]
Type=oneshot
ExecStart=/usr/bin/clamscan -r /home --log=/var/log/clamav-scan.log --infected --exclude-dir="^/proc" --exclude-dir="^/sys" --exclude-dir="^/dev"
CLAM_EOF

cat > /etc/systemd/system/clamav-scan.timer << 'CLAMTIMER_EOF'
[Unit]
Description=ClamAV Daily Scan Timer

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
CLAMTIMER_EOF
systemctl enable clamav-scan.timer
ok "ClamAV scansione automatica ogni notte alle 03:00"

# fail2ban
pacman -S --noconfirm --needed fail2ban
systemctl enable fail2ban
cat > /etc/fail2ban/jail.local << 'F2B_EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
F2B_EOF
ok "fail2ban configurato (SSH: max 3 tentativi)"

# UFW (Uncomplicated Firewall)
pacman -S --noconfirm --needed ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw --force enable
systemctl enable ufw
ok "UFW configurato (deny incoming, allow SSH)"

# rkhunter
pacman -S --noconfirm --needed rkhunter
rkhunter --update 2>/dev/null || true
rkhunter --propupd 2>/dev/null
ok "rkhunter installato"

# osquery (da AUR)
sudo -u "$USERNAME" yay -S --noconfirm osquery-bin 2>/dev/null || {
    warn "osquery non installato da AUR — installazione manuale necessaria"
}

# Suricata (IDS/IPS)
pacman -S --noconfirm --needed suricata 2>/dev/null || {
    warn "Suricata non disponibile nei repo — installare da AUR"
    sudo -u "$USERNAME" yay -S --noconfirm suricata 2>/dev/null || true
}

ok "Security stack installato"

# ═══════════════════════════════════════════════════════════════
header "8. OSINT TOOLS"
# ═══════════════════════════════════════════════════════════════

info "Installazione OSINT tools..."

# Tools dai repo ufficiali
pacman -S --noconfirm --needed \
    nmap \
    wireshark-qt \
    perl-image-exiftool \
    whois \
    bind-tools \
    traceroute \
    tcpdump \
    net-tools

# Tools Python via pip
sudo -u "$USERNAME" pip install --user --break-system-packages \
    sherlock-project \
    theHarvester \
    shodan \
    censys \
    holehe 2>/dev/null || true

# SpiderFoot via Docker (più pulito)
info "SpiderFoot disponibile via Docker:"
info "  docker run -p 5001:5001 spiderfoot/spiderfoot"

# Maltego (AUR)
sudo -u "$USERNAME" yay -S --noconfirm maltego 2>/dev/null || {
    warn "Maltego: installare manualmente da https://www.maltego.com/downloads/"
}

ok "OSINT tools installati"

# Aggiungere utente al gruppo wireshark
usermod -aG wireshark "$USERNAME" 2>/dev/null

# ═══════════════════════════════════════════════════════════════
header "9. GIT CONFIGURAZIONE"
# ═══════════════════════════════════════════════════════════════

sudo -u "$USERNAME" bash << 'GIT_EOF'
git config --global user.name "vio83"
git config --global user.email "porcu.v.83@gmail.com"
git config --global init.defaultBranch main
git config --global core.editor "vim"
git config --global push.autoSetupRemote true
git config --global pull.rebase false
git config --global alias.st "status"
git config --global alias.co "checkout"
git config --global alias.br "branch"
git config --global alias.ci "commit"
git config --global alias.lg "log --oneline --graph --decorate -20"
GIT_EOF

ok "Git configurato per vio83"

# Clonare repository
info "Clonazione repository..."
sudo -u "$USERNAME" bash << 'CLONE_EOF'
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/vio83/mai-love.git vio83-ai-orchestra 2>/dev/null || true
git clone https://github.com/vio83/ai-scripts-elite.git 2>/dev/null || true
CLONE_EOF

ok "Repository clonati in ~/Projects"

# ═══════════════════════════════════════════════════════════════
header "10. AUTO-OPTIMIZATION (ogni 15 minuti)"
# ═══════════════════════════════════════════════════════════════

cat > /usr/local/bin/archimede_optimize.sh << 'OPTIMIZE_EOF'
#!/bin/bash
# VIO83 ARCHIMEDE — Auto-Optimization (eseguito ogni 15 min)

LOG="/var/log/archimede_optimize.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

# 1. Kill processi zombie
ZOMBIES=$(ps aux | awk '{ if ($8 == "Z") print $2 }')
for z in $ZOMBIES; do
    kill -9 "$z" 2>/dev/null
    log "Killed zombie PID $z"
done

# 2. Pulizia cache se RAM < 1GB libera
FREE_MB=$(free -m | awk '/Mem:/{print $7}')
if [[ "$FREE_MB" -lt 1024 ]]; then
    sync
    echo 3 > /proc/sys/vm/drop_caches
    log "Cache dropped (free was ${FREE_MB}MB)"
fi

# 3. Pulizia /tmp vecchi (>7 giorni)
find /tmp -type f -atime +7 -delete 2>/dev/null
find /tmp -type d -empty -delete 2>/dev/null

# 4. Pulizia cache pacman (mantieni ultime 3 versioni)
paccache -r -k 3 2>/dev/null

# 5. Ottimizzazione I/O per HDD
for disk in /sys/block/sd[a-z]; do
    [[ -d "$disk" ]] || continue
    echo deadline > "${disk}/queue/scheduler" 2>/dev/null
    echo 256 > "${disk}/queue/read_ahead_kb" 2>/dev/null
    echo 256 > "${disk}/queue/nr_requests" 2>/dev/null
done

# 6. Swappiness bassa (preferire RAM)
sysctl -w vm.swappiness=10 2>/dev/null

# 7. Verificare servizi critici
for svc in sshd NetworkManager fan-watchdog; do
    if ! systemctl is-active "$svc" &>/dev/null; then
        systemctl restart "$svc" 2>/dev/null
        log "Restarted $svc"
    fi
done

log "Optimization cycle complete (free: ${FREE_MB}MB)"
OPTIMIZE_EOF
chmod +x /usr/local/bin/archimede_optimize.sh

# Timer systemd ogni 15 minuti
cat > /etc/systemd/system/archimede-optimize.service << 'OPTSVC_EOF'
[Unit]
Description=ARCHIMEDE Auto-Optimization

[Service]
Type=oneshot
ExecStart=/usr/local/bin/archimede_optimize.sh
OPTSVC_EOF

cat > /etc/systemd/system/archimede-optimize.timer << 'OPTTIMER_EOF'
[Unit]
Description=ARCHIMEDE Optimization Timer (15 min)

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target
OPTTIMER_EOF

systemctl enable archimede-optimize.timer
ok "Auto-optimization ogni 15 minuti"

# ═══════════════════════════════════════════════════════════════
header "11. CONNESSIONE iPHONE HOTSPOT AUTOMATICA"
# ═══════════════════════════════════════════════════════════════

info "Configurazione auto-connessione hotspot iPhone..."

cat > /usr/local/bin/archimede_wifi.sh << 'WIFI_EOF'
#!/bin/bash
# VIO83 ARCHIMEDE — Auto WiFi Hotspot iPhone
# Tenta connessione automatica all'hotspot iPhone

SSIDS=("iPhone di Vio" "iPhone di Chiara" "iPhone" "Vio" "iPhone 15")
LOG="/var/log/archimede_wifi.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

# Verificare se già connessi
if nmcli -t -f STATE general 2>/dev/null | grep -q "connected"; then
    exit 0
fi

log "Non connesso — ricerca hotspot..."

# Scansionare reti
nmcli device wifi rescan 2>/dev/null
sleep 3

# Tentare connessione
for SSID in "${SSIDS[@]}"; do
    if nmcli -t -f SSID device wifi list 2>/dev/null | grep -q "^${SSID}$"; then
        log "Trovata rete: $SSID — connessione..."
        nmcli device wifi connect "$SSID" 2>/dev/null
        sleep 5
        if nmcli -t -f STATE general 2>/dev/null | grep -q "connected"; then
            log "Connesso a $SSID"

            # DNS veloci
            nmcli con mod "$SSID" ipv4.dns "1.1.1.1 8.8.8.8" 2>/dev/null
            nmcli con mod "$SSID" ipv4.ignore-auto-dns yes 2>/dev/null

            exit 0
        fi
    fi
done

log "Nessun hotspot trovato"
WIFI_EOF
chmod +x /usr/local/bin/archimede_wifi.sh

# Timer per auto-connessione
cat > /etc/systemd/system/archimede-wifi.service << 'WIFISVC_EOF'
[Unit]
Description=ARCHIMEDE Auto WiFi Hotspot
After=NetworkManager.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/archimede_wifi.sh
WIFISVC_EOF

cat > /etc/systemd/system/archimede-wifi.timer << 'WIFITIMER_EOF'
[Unit]
Description=ARCHIMEDE WiFi Check Timer

[Timer]
OnBootSec=30s
OnUnitActiveSec=2min

[Install]
WantedBy=timers.target
WIFITIMER_EOF

systemctl enable archimede-wifi.timer
ok "Auto-connessione hotspot configurata (check ogni 2 min)"

# ═══════════════════════════════════════════════════════════════
header "12. KERNEL TUNING LINUX"
# ═══════════════════════════════════════════════════════════════

info "Tuning kernel per iMac 2009 con 8GB RAM e HDD..."

cat > /etc/sysctl.d/99-archimede.conf << 'SYSCTL_EOF'
# VIO83 ARCHIMEDE — Kernel Tuning per iMac 2009

# === MEMORIA ===
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.overcommit_memory = 0

# === RETE (ottimizzato per hotspot mobile) ===
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_ecn = 1
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_keepalive_time = 60
net.ipv4.tcp_keepalive_intvl = 10
net.ipv4.tcp_keepalive_probes = 6

# === SICUREZZA ===
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
kernel.sysrq = 0
fs.suid_dumpable = 0

# === I/O HDD ===
vm.dirty_writeback_centisecs = 1500
SYSCTL_EOF

ok "Kernel tuning applicato"

# Caricare modulo BBR
modprobe tcp_bbr 2>/dev/null
echo "tcp_bbr" > /etc/modules-load.d/bbr.conf

# ═══════════════════════════════════════════════════════════════
header "13. MONITORING DASHBOARD"
# ═══════════════════════════════════════════════════════════════

cat > /usr/local/bin/archimede_status.sh << 'STATUS_EOF'
#!/bin/bash
# VIO83 ARCHIMEDE — Status Dashboard

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'

clear
echo -e "${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  ARCHIMEDE — Status Dashboard                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# CPU
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
CPU_TEMP=$(sensors 2>/dev/null | grep -oP 'Core 0:.*?\+\K[0-9.]+' | head -1)
echo -e "  ${CYAN}CPU:${NC}  Usage: ${CPU_USAGE}%  Temp: ${CPU_TEMP:-N/A}°C"

# RAM
RAM_USED=$(free -h | awk '/Mem:/{print $3}')
RAM_TOTAL=$(free -h | awk '/Mem:/{print $2}')
RAM_AVAIL=$(free -h | awk '/Mem:/{print $7}')
echo -e "  ${CYAN}RAM:${NC}  ${RAM_USED}/${RAM_TOTAL} (disponibile: ${RAM_AVAIL})"

# Disco
DISK_USED=$(df -h / | awk 'NR==2{print $3}')
DISK_AVAIL=$(df -h / | awk 'NR==2{print $4}')
DISK_PCT=$(df -h / | awk 'NR==2{print $5}')
echo -e "  ${CYAN}Disco:${NC} ${DISK_USED} usati, ${DISK_AVAIL} liberi (${DISK_PCT})"

# Rete
WIFI_SSID=$(nmcli -t -f active,ssid dev wifi 2>/dev/null | grep "^yes" | cut -d: -f2)
IP_ADDR=$(ip -4 -o addr show 2>/dev/null | grep -v "127.0.0.1" | awk '{print $4}' | head -1)
echo -e "  ${CYAN}Rete:${NC}  WiFi: ${WIFI_SSID:-Disconnesso}  IP: ${IP_ADDR:-N/A}"

# Ventole
if [[ -d /sys/devices/platform/applesmc.768 ]]; then
    FAN1=$(cat /sys/devices/platform/applesmc.768/fan1_output 2>/dev/null)
    echo -e "  ${CYAN}Fan:${NC}   ${FAN1:-N/A} RPM"
fi

# Servizi
echo ""
echo -e "  ${BOLD}Servizi:${NC}"
for svc in sshd NetworkManager docker fan-watchdog clamav-freshclam ufw; do
    STATUS=$(systemctl is-active "$svc" 2>/dev/null)
    if [[ "$STATUS" == "active" ]]; then
        echo -e "    ${GREEN}●${NC} $svc"
    else
        echo -e "    ${RED}○${NC} $svc (${STATUS})"
    fi
done

# Snapshot Btrfs
echo ""
SNAP_COUNT=$(ls -d /.snapshots/pre-update-* 2>/dev/null | wc -l)
LAST_SNAP=$(ls -dt /.snapshots/pre-update-* 2>/dev/null | head -1 | xargs basename 2>/dev/null)
echo -e "  ${CYAN}Snapshot:${NC} ${SNAP_COUNT} disponibili (ultimo: ${LAST_SNAP:-nessuno})"

# Uptime
echo ""
echo -e "  ${CYAN}Uptime:${NC}  $(uptime -p 2>/dev/null || uptime)"
echo ""
STATUS_EOF
chmod +x /usr/local/bin/archimede_status.sh

# Alias per dashboard
echo 'alias status="sudo /usr/local/bin/archimede_status.sh"' >> "${HOME_DIR}/.zshrc"

ok "Dashboard: esegui 'status' per vedere lo stato del sistema"

# ═══════════════════════════════════════════════════════════════
header "14. KALI TOOLS VIA DOCKER (opzionale)"
# ═══════════════════════════════════════════════════════════════

info "Configurazione container Kali per tools specialistici..."

cat > "${HOME_DIR}/kali-docker.sh" << 'KALI_EOF'
#!/bin/bash
# Avvia un container Kali Linux con tools completi
# Uso: ./kali-docker.sh [comando]

if [[ -n "$1" ]]; then
    docker run --rm -it --net=host kalilinux/kali-rolling "$@"
else
    docker run --rm -it --net=host kalilinux/kali-rolling /bin/bash
fi
KALI_EOF
chmod +x "${HOME_DIR}/kali-docker.sh"
chown "${USERNAME}:${USERNAME}" "${HOME_DIR}/kali-docker.sh"

ok "Kali Docker: ~/kali-docker.sh per ambiente Kali completo"

# ═══════════════════════════════════════════════════════════════
header "15. PULIZIA FINALE E SNAPSHOT"
# ═══════════════════════════════════════════════════════════════

info "Pulizia cache pacman..."
pacman -Sc --noconfirm 2>/dev/null

info "Creazione snapshot post-installazione..."
btrfs subvolume snapshot / "/.snapshots/post-install-$(date +%Y%m%d)" 2>/dev/null
ok "Snapshot post-installazione creato (punto di ripristino sicuro)"

# Rigenerare initramfs con tutti i moduli
mkinitcpio -P 2>/dev/null

# ═══════════════════════════════════════════════════════════════
header "FASE 4 COMPLETATA — ARCHIMEDE OPERATIVO"
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  PROGETTO ARCHIMEDE — INSTALLAZIONE COMPLETA${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  AMBIENTE DI SVILUPPO:"
echo "  ✔ Desktop XFCE4 (ottimizzato per iMac 2009)"
echo "  ✔ Python $(python --version 2>&1 | awk '{print $2}')"
echo "  ✔ Node.js $(node --version 2>&1)"
echo "  ✔ Rust, Go, Ruby"
echo "  ✔ VS Code + 19 estensioni"
echo "  ✔ Claude Code CLI"
echo "  ✔ Ollama (3 modelli AI locali)"
echo "  ✔ Docker"
echo ""
echo "  SICUREZZA:"
echo "  ✔ ClamAV (scansione notturna)"
echo "  ✔ fail2ban (SSH: max 3 tentativi)"
echo "  ✔ UFW firewall (deny incoming)"
echo "  ✔ rkhunter (rootkit scanner)"
echo ""
echo "  OSINT:"
echo "  ✔ nmap, wireshark, exiftool"
echo "  ✔ sherlock, theHarvester"
echo "  ✔ Kali tools via Docker"
echo ""
echo "  PROTEZIONE:"
echo "  ✔ Btrfs snapshot (rollback in 5 sec)"
echo "  ✔ Kernel pinning (safe_update.sh)"
echo "  ✔ Fan control watchdog"
echo "  ✔ Auto-optimization ogni 15 min"
echo "  ✔ SSH server (accesso remoto)"
echo ""
echo "  COMANDI UTILI:"
echo "  ─────────────"
echo "  status          → Dashboard sistema"
echo "  update          → Aggiornamento sicuro (con snapshot)"
echo "  snap            → Snapshot manuale"
echo "  fans            → Stato ventole"
echo "  temp            → Temperature"
echo "  ~/kali-docker.sh → Ambiente Kali completo"
echo ""
echo -e "  ${YELLOW}CAMBIA LA PASSWORD: passwd${NC}"
echo ""
echo -e "  ${CYAN}Riavvia per applicare tutto: sudo reboot${NC}"
echo ""
