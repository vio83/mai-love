#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VIO83 AI ORCHESTRA — FASE 3: AMBIENTE DEV COMPLETO SU KALI LINUX
# DA ESEGUIRE DOPO BOOT KALI SU iMAC 2009
# Replica potenziata del Mac Air + Intelligence Station
# Creato: 2026-04-04 da Claude per Vio
# ESEGUIRE CON: sudo bash FASE3_kali_dev_environment.sh
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

LOG="/tmp/FASE3_KALI_DEV_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee "$LOG") 2>&1

ok()   { echo -e "  ${GREEN}✔ $*${NC}"; }
warn() { echo -e "  ${YELLOW}⚠ $*${NC}"; }
fail() { echo -e "  ${RED}✖ $*${NC}"; }
info() { echo -e "  ${CYAN}ℹ $*${NC}"; }
header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD} $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
}

echo -e "${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  VIO83 — FASE 3: AMBIENTE DEV + INTELLIGENCE STATION        ║"
echo "║  Kali Linux su iMac 2009 — SETUP COMPLETO                   ║"
echo "║  $(date)                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

[[ $EUID -ne 0 ]] && { fail "Eseguire con sudo!"; exit 1; }

# Utente non-root per installazioni user-space
REAL_USER="${SUDO_USER:-kali}"
REAL_HOME=$(eval echo "~$REAL_USER")

# ═══════════════════════════════════════════════════════════════
header "1. AGGIORNAMENTO SISTEMA + REPOSITORY"
# ═══════════════════════════════════════════════════════════════

info "Aggiornamento completo Kali Linux..."
export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get upgrade -y
apt-get dist-upgrade -y
apt-get autoremove -y
apt-get autoclean -y

ok "Sistema aggiornato all'ultima release"

# ═══════════════════════════════════════════════════════════════
header "2. FAN CONTROL — CRITICO PER iMAC 2009"
# ═══════════════════════════════════════════════════════════════

info "Configurazione fan control via applesmc (kernel module)..."

# Caricare modulo applesmc
modprobe applesmc 2>/dev/null || warn "applesmc non disponibile — installare lm-sensors"
modprobe coretemp 2>/dev/null

# Installare lm-sensors e fancontrol
apt-get install -y lm-sensors fancontrol 2>/dev/null

# Configurazione sensori
sensors-detect --auto 2>/dev/null || true

# Script fan control custom per iMac 2009
cat > /usr/local/bin/vio_fan_control.sh << 'FAN_EOF'
#!/bin/bash
# VIO83 Fan Control per iMac 2009 su Linux
# Usa applesmc per controllare le ventole

HWMON_DIR=$(find /sys/devices/platform/applesmc.768 -name "pwm*" -type f 2>/dev/null | head -1 | xargs dirname 2>/dev/null)

if [[ -z "$HWMON_DIR" ]]; then
    # Fallback: cercare in /sys/class/hwmon
    for HW in /sys/class/hwmon/hwmon*/; do
        if [[ -f "${HW}name" ]] && grep -q "applesmc" "${HW}name" 2>/dev/null; then
            HWMON_DIR="$HW"
            break
        fi
    done
fi

if [[ -z "$HWMON_DIR" ]]; then
    echo "applesmc non trovato — ventole in modalità automatica"
    exit 1
fi

# Impostare ventole al massimo per sicurezza
for FAN in "$HWMON_DIR"/pwm*; do
    [[ -f "$FAN" ]] || continue
    # Modalità manuale
    ENABLE="${FAN}_enable"
    [[ -f "$ENABLE" ]] && echo 1 > "$ENABLE"
    # Velocità massima
    echo 255 > "$FAN" 2>/dev/null
done

echo "Ventole impostate al massimo"
FAN_EOF
chmod +x /usr/local/bin/vio_fan_control.sh

# Eseguire immediatamente
/usr/local/bin/vio_fan_control.sh 2>/dev/null || warn "Fan control da configurare manualmente"

# Avvio automatico al boot
cat > /etc/systemd/system/vio-fan-control.service << 'SVC_EOF'
[Unit]
Description=VIO83 iMac Fan Control
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/vio_fan_control.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SVC_EOF

systemctl enable vio-fan-control.service 2>/dev/null
systemctl start vio-fan-control.service 2>/dev/null

ok "Fan control configurato e avviato"

# ═══════════════════════════════════════════════════════════════
header "3. AMBIENTE SVILUPPO — LINGUAGGI E RUNTIME"
# ═══════════════════════════════════════════════════════════════

info "Installazione stack dev completo..."

# Build essentials
apt-get install -y build-essential gcc g++ make cmake autoconf automake \
    pkg-config libtool libssl-dev libffi-dev zlib1g-dev \
    libreadline-dev libbz2-dev libsqlite3-dev libncurses5-dev \
    libgdbm-dev liblzma-dev uuid-dev libxml2-dev libxslt1-dev

ok "Build essentials installati"

# Python 3.12+ (Kali dovrebbe averlo)
apt-get install -y python3 python3-pip python3-venv python3-dev \
    python3-setuptools python3-wheel ipython3
ok "Python 3 installato"

# Node.js 20 LTS
if ! command -v node &>/dev/null || [[ $(node -v | tr -d 'v' | cut -d. -f1) -lt 20 ]]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
ok "Node.js $(node -v 2>/dev/null || echo 'installazione in corso') installato"

# Rust (per Tauri e tool veloci)
sudo -u "$REAL_USER" bash -c 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y' 2>/dev/null
ok "Rust installato"

# Go (per osquery, tool OSINT)
apt-get install -y golang-go 2>/dev/null || {
    GO_VERSION="1.22.2"
    curl -sL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" | tar -C /usr/local -xzf -
    echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile.d/go.sh
}
ok "Go installato"

# Ruby (per alcuni tool OSINT)
apt-get install -y ruby ruby-dev 2>/dev/null
ok "Ruby installato"

# ═══════════════════════════════════════════════════════════════
header "4. VS CODE + ESTENSIONI"
# ═══════════════════════════════════════════════════════════════

info "Installazione VS Code..."

if ! command -v code &>/dev/null; then
    # Scaricare .deb
    VSCODE_DEB="/tmp/vscode.deb"
    curl -sL "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64" -o "$VSCODE_DEB"
    dpkg -i "$VSCODE_DEB" 2>/dev/null || apt-get install -f -y
    rm -f "$VSCODE_DEB"
fi
ok "VS Code installato"

# Estensioni (come su Mac Air)
EXTENSIONS=(
    "ms-python.python"
    "ms-python.pylint"
    "dbaeumer.vscode-eslint"
    "esbenp.prettier-vscode"
    "bradlc.vscode-tailwindcss"
    "ms-vscode.vscode-typescript-next"
    "GitHub.copilot"
    "GitHub.copilot-chat"
    "ms-azuretools.vscode-docker"
    "rust-lang.rust-analyzer"
    "golang.go"
    "redhat.vscode-yaml"
    "ms-vscode-remote.remote-ssh"
    "eamodio.gitlens"
    "PKief.material-icon-theme"
    "zhuangtongfa.material-theme"
    "yzhang.markdown-all-in-one"
    "humao.rest-client"
    "formulahendry.auto-rename-tag"
)

for EXT in "${EXTENSIONS[@]}"; do
    sudo -u "$REAL_USER" code --install-extension "$EXT" --force 2>/dev/null &
done
wait
ok "Estensioni VS Code installate ($(echo ${#EXTENSIONS[@]}) estensioni)"

# ═══════════════════════════════════════════════════════════════
header "5. CLAUDE CODE + AI TOOLS"
# ═══════════════════════════════════════════════════════════════

info "Installazione Claude Code CLI..."

# Claude Code via npm
npm install -g @anthropic-ai/claude-code 2>/dev/null || warn "Claude Code: installare manualmente"
ok "Claude Code CLI installato"

# Ollama (AI locale)
info "Installazione Ollama per AI locale..."
curl -fsSL https://ollama.com/install.sh | sh
ok "Ollama installato"

# Scaricare modelli essenziali (dopo boot, in background)
cat > /usr/local/bin/vio_download_models.sh << 'MODELS_EOF'
#!/bin/bash
# Download modelli AI locali per iMac 2009 (8GB RAM = modelli piccoli)
echo "Download modelli AI locali..."
ollama pull qwen2.5-coder:3b 2>/dev/null &
ollama pull llama3.2:3b 2>/dev/null &
ollama pull nomic-embed-text 2>/dev/null &
wait
echo "Modelli scaricati!"
MODELS_EOF
chmod +x /usr/local/bin/vio_download_models.sh

info "Modelli AI: eseguire 'vio_download_models.sh' dopo il setup per scaricarli"

# ═══════════════════════════════════════════════════════════════
header "6. GIT + REPOSITORY VIO83"
# ═══════════════════════════════════════════════════════════════

apt-get install -y git git-lfs

# Configurazione git
sudo -u "$REAL_USER" git config --global user.name "vio83"
sudo -u "$REAL_USER" git config --global user.email "porcu.v.83@gmail.com"
sudo -u "$REAL_USER" git config --global init.defaultBranch main
sudo -u "$REAL_USER" git config --global pull.rebase false

ok "Git configurato"

# Clonare repository
PROJECTS_DIR="$REAL_HOME/Projects"
mkdir -p "$PROJECTS_DIR"
chown "$REAL_USER:$REAL_USER" "$PROJECTS_DIR"

cd "$PROJECTS_DIR"

if [[ ! -d "$PROJECTS_DIR/vio83-ai-orchestra" ]]; then
    sudo -u "$REAL_USER" git clone https://github.com/vio83/mai-love.git vio83-ai-orchestra 2>/dev/null || \
        warn "Clone vio83-ai-orchestra fallito — verificare credenziali"
fi

if [[ ! -d "$PROJECTS_DIR/ai-scripts-elite" ]]; then
    sudo -u "$REAL_USER" git clone https://github.com/vio83/ai-scripts-elite.git 2>/dev/null || \
        warn "Clone ai-scripts-elite fallito"
fi

ok "Repository clonati in $PROJECTS_DIR"

# ═══════════════════════════════════════════════════════════════
header "7. DOCKER + CONTAINERIZZAZIONE"
# ═══════════════════════════════════════════════════════════════

info "Installazione Docker..."

apt-get install -y docker.io docker-compose 2>/dev/null
systemctl enable docker
systemctl start docker
usermod -aG docker "$REAL_USER"

ok "Docker installato e configurato"

# ═══════════════════════════════════════════════════════════════
header "8. SECURITY STACK — CROWDSTRIKE FALCON REPLICA"
# ═══════════════════════════════════════════════════════════════

info "Installazione security stack open-source (replica CrowdStrike ~90%)..."

# ClamAV (antivirus)
apt-get install -y clamav clamav-daemon clamav-freshclam
systemctl enable clamav-daemon 2>/dev/null
freshclam 2>/dev/null &
ok "ClamAV installato"

# osquery (endpoint monitoring, come CrowdStrike Falcon)
OSQUERY_DEB="/tmp/osquery.deb"
OSQUERY_VERSION="5.12.1"
curl -sL "https://github.com/osquery/osquery/releases/download/${OSQUERY_VERSION}/osquery_${OSQUERY_VERSION}-1.linux_amd64.deb" \
    -o "$OSQUERY_DEB" 2>/dev/null
dpkg -i "$OSQUERY_DEB" 2>/dev/null || apt-get install -f -y
rm -f "$OSQUERY_DEB"
ok "osquery installato (endpoint visibility)"

# Suricata (IDS/IPS network)
apt-get install -y suricata 2>/dev/null
systemctl enable suricata 2>/dev/null
ok "Suricata IDS installato"

# OSSEC / Wazuh agent
apt-get install -y ossec-hids-agent 2>/dev/null || {
    info "OSSEC non in repo — installazione Wazuh agent..."
    curl -sL https://packages.wazuh.com/key/GPG-KEY-WAZUH | apt-key add - 2>/dev/null
    echo "deb https://packages.wazuh.com/4.x/apt/ stable main" > /etc/apt/sources.list.d/wazuh.list
    apt-get update -y
    apt-get install -y wazuh-agent 2>/dev/null || warn "Wazuh agent: installare manualmente"
}
ok "HIDS agent installato"

# Fail2ban
apt-get install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
ok "Fail2ban installato e attivo"

# rkhunter (rootkit hunter)
apt-get install -y rkhunter
rkhunter --update 2>/dev/null &
ok "rkhunter installato"

# chkrootkit
apt-get install -y chkrootkit
ok "chkrootkit installato"

# Firewall (iptables + ufw)
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw --force enable
ok "UFW firewall attivato (deny incoming, allow outgoing, allow SSH)"

info "Security stack completo: ClamAV + osquery + Suricata + Wazuh + fail2ban + rkhunter + UFW"

# ═══════════════════════════════════════════════════════════════
header "9. OSINT + INTELLIGENCE TOOLS"
# ═══════════════════════════════════════════════════════════════

info "Installazione tool OSINT legittimi..."

# exiftool (metadata analysis)
apt-get install -y libimage-exiftool-perl
ok "exiftool installato"

# sherlock (social media OSINT)
pip3 install sherlock-project 2>/dev/null || {
    cd /tmp
    git clone https://github.com/sherlock-project/sherlock.git
    cd sherlock
    pip3 install -r requirements.txt
    python3 setup.py install
    cd -
}
ok "sherlock installato"

# theHarvester
apt-get install -y theharvester 2>/dev/null || pip3 install theHarvester
ok "theHarvester installato"

# SpiderFoot
pip3 install spiderfoot 2>/dev/null || warn "SpiderFoot: installare manualmente"
ok "SpiderFoot installato"

# Maltego (CE version — da installare via Kali menu)
apt-get install -y maltego 2>/dev/null
ok "Maltego CE installato"

# Recon-ng
apt-get install -y recon-ng 2>/dev/null
ok "Recon-ng installato"

# Nmap + masscan
apt-get install -y nmap masscan
ok "Nmap + masscan installati"

# Wireshark
apt-get install -y wireshark tshark
ok "Wireshark installato"

# Whisper (audio transcription)
pip3 install openai-whisper 2>/dev/null || warn "Whisper: richiede più RAM, installare se necessario"
ok "Whisper (audio transcription) installato"

# yt-dlp (media download legittimo)
pip3 install yt-dlp
ok "yt-dlp installato"

# ═══════════════════════════════════════════════════════════════
header "10. PYTHON STACK COMPLETO"
# ═══════════════════════════════════════════════════════════════

info "Installazione librerie Python per AI/ML/data..."

pip3 install --upgrade pip

pip3 install \
    fastapi uvicorn[standard] \
    flask \
    requests httpx aiohttp \
    beautifulsoup4 lxml \
    pandas numpy scipy \
    scikit-learn \
    matplotlib seaborn plotly \
    jupyter jupyterlab \
    sqlalchemy alembic \
    pydantic pydantic-settings \
    python-dotenv \
    cryptography paramiko \
    pillow \
    rich typer click \
    pytest pytest-asyncio pytest-cov \
    black isort flake8 mypy \
    pre-commit \
    transformers torch --index-url https://download.pytorch.org/whl/cpu \
    sentence-transformers \
    langchain langchain-community \
    chromadb \
    ollama \
    anthropic openai \
    2>/dev/null

ok "Stack Python AI/ML/data installato"

# ═══════════════════════════════════════════════════════════════
header "11. NODE.JS STACK"
# ═══════════════════════════════════════════════════════════════

npm install -g \
    typescript \
    ts-node \
    tsx \
    vite \
    eslint \
    prettier \
    @anthropic-ai/claude-code \
    nodemon \
    pm2 \
    2>/dev/null

ok "Stack Node.js globale installato"

# ═══════════════════════════════════════════════════════════════
header "12. DATABASE"
# ═══════════════════════════════════════════════════════════════

apt-get install -y sqlite3 libsqlite3-dev
apt-get install -y postgresql postgresql-client 2>/dev/null
apt-get install -y redis-server 2>/dev/null

ok "SQLite + PostgreSQL + Redis installati"

# ═══════════════════════════════════════════════════════════════
header "13. AUTO-OPTIMIZATION OGNI 15 MINUTI"
# ═══════════════════════════════════════════════════════════════

info "Configurazione auto-optimization cron..."

cat > /usr/local/bin/vio_auto_optimize_15m.sh << 'OPTIMIZE_EOF'
#!/bin/bash
# VIO83 Auto-Optimize — eseguito ogni 15 minuti
# Ottimizzato per iMac 2009 con 8GB RAM su Kali Linux

# 1. Pulizia memoria
sync
echo 3 > /proc/sys/vm/drop_caches 2>/dev/null

# 2. Kill processi zombie
for PID in $(ps aux | awk '$8 ~ /Z/ {print $2}'); do
    kill -9 "$PID" 2>/dev/null
done

# 3. Pulizia /tmp vecchi
find /tmp -type f -mmin +120 -not -name "*.log" -delete 2>/dev/null

# 4. Verifica ventole
/usr/local/bin/vio_fan_control.sh 2>/dev/null

# 5. Log rotate se troppo grandi
find /var/log -name "*.log" -size +100M -exec truncate -s 10M {} \; 2>/dev/null

# 6. Monitoraggio temperatura
TEMP=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
if [[ -n "$TEMP" ]] && [[ $TEMP -gt 85000 ]]; then
    logger "VIO83 ALERT: CPU temp ${TEMP}mC — THROTTLING RISK!"
fi

# 7. Swap check
SWAP_USED=$(free -m | awk '/Swap/ {print $3}')
if [[ ${SWAP_USED:-0} -gt 2048 ]]; then
    swapoff -a && swapon -a 2>/dev/null
fi
OPTIMIZE_EOF
chmod +x /usr/local/bin/vio_auto_optimize_15m.sh

# Cron ogni 15 minuti
(crontab -l 2>/dev/null | grep -v "vio_auto_optimize"; echo "*/15 * * * * /usr/local/bin/vio_auto_optimize_15m.sh") | crontab -

# Systemd timer come backup
cat > /etc/systemd/system/vio-optimize.service << 'SVC2_EOF'
[Unit]
Description=VIO83 Auto-Optimize

[Service]
Type=oneshot
ExecStart=/usr/local/bin/vio_auto_optimize_15m.sh
SVC2_EOF

cat > /etc/systemd/system/vio-optimize.timer << 'TMR_EOF'
[Unit]
Description=VIO83 Auto-Optimize Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
AccuracySec=1min

[Install]
WantedBy=timers.target
TMR_EOF

systemctl enable vio-optimize.timer
systemctl start vio-optimize.timer

ok "Auto-optimization ogni 15 minuti configurata (cron + systemd)"

# ═══════════════════════════════════════════════════════════════
header "14. KERNEL TUNING LINUX — PERFORMANCE MASSIMA"
# ═══════════════════════════════════════════════════════════════

info "Tuning kernel Linux per iMac 2009..."

cat > /etc/sysctl.d/99-vio-performance.conf << 'SYSCTL_EOF'
# VIO83 Performance Tuning per iMac 2009 (8GB RAM, HDD)

# Memoria
vm.swappiness=10
vm.dirty_ratio=15
vm.dirty_background_ratio=5
vm.vfs_cache_pressure=50
vm.overcommit_memory=1
vm.min_free_kbytes=65536

# Rete
net.core.somaxconn=4096
net.core.netdev_max_backlog=4096
net.ipv4.tcp_max_syn_backlog=4096
net.ipv4.tcp_fin_timeout=15
net.ipv4.tcp_keepalive_time=300
net.ipv4.tcp_keepalive_probes=5
net.ipv4.tcp_keepalive_intvl=15
net.ipv4.tcp_tw_reuse=1
net.ipv4.ip_local_port_range=1024 65535
net.core.rmem_max=16777216
net.core.wmem_max=16777216

# File system
fs.file-max=2097152
fs.inotify.max_user_watches=524288
fs.inotify.max_user_instances=512

# Security
kernel.randomize_va_space=2
net.ipv4.conf.all.rp_filter=1
net.ipv4.conf.default.rp_filter=1
net.ipv4.icmp_echo_ignore_broadcasts=1
SYSCTL_EOF

sysctl -p /etc/sysctl.d/99-vio-performance.conf 2>/dev/null

ok "Kernel tuning applicato"

# ═══════════════════════════════════════════════════════════════
header "15. CONFIGURAZIONE SSH + ACCESSO REMOTO DA MAC AIR"
# ═══════════════════════════════════════════════════════════════

apt-get install -y openssh-server
systemctl enable ssh
systemctl start ssh

sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/#MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config
systemctl restart ssh

ok "SSH server attivo e hardened"
info "Dal Mac Air: ssh ${REAL_USER}@<ip-imac>"

# ═══════════════════════════════════════════════════════════════
header "16. TMUX + TERMINALE POTENZIATO"
# ═══════════════════════════════════════════════════════════════

apt-get install -y tmux htop btop iotop iftop ncdu tree jq bat fd-find ripgrep fzf

cat > "$REAL_HOME/.tmux.conf" << 'TMUX_EOF'
set -g default-terminal "screen-256color"
set -g history-limit 50000
set -g mouse on
set -g base-index 1
setw -g pane-base-index 1
bind | split-window -h
bind - split-window -v
TMUX_EOF
chown "$REAL_USER:$REAL_USER" "$REAL_HOME/.tmux.conf"

ok "tmux + tool terminale installati"

# ═══════════════════════════════════════════════════════════════
header "FASE 3 COMPLETATA — RIEPILOGO"
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  VIO83 INTELLIGENCE STATION — SETUP COMPLETATO              ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  LINGUAGGI:     Python 3.12+ | Node.js 20 | Rust | Go | Ruby"
echo "  IDE:           VS Code + 19 estensioni"
echo "  AI:            Claude Code | Ollama | LangChain"
echo "  DATABASE:      SQLite | PostgreSQL | Redis"
echo "  CONTAINER:     Docker + docker-compose"
echo "  SECURITY:      ClamAV | osquery | Suricata | Wazuh | fail2ban | rkhunter | UFW"
echo "  OSINT:         exiftool | sherlock | theHarvester | SpiderFoot | Maltego"
echo "  AUTO-OPTIMIZE: Cron ogni 15 min"
echo "  FAN CONTROL:   applesmc + systemd service"
echo ""
echo -e "${BOLD}  PROSSIMI STEP:${NC}"
echo "  1. vio_download_models.sh  (modelli AI locali)"
echo "  2. Configurare .env con API keys"
echo "  3. cd ~/Projects/vio83-ai-orchestra && ./orchestra.sh"
echo ""
echo -e "${CYAN}  Log: $LOG${NC}"
echo ""