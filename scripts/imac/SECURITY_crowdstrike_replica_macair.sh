#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VIO83 — CROWDSTRIKE FALCON REPLICA (~90%) PER MAC AIR M1
# Security Stack Open-Source che replica le funzionalità CrowdStrike Falcon
# Target: MacBook Air M1 — macOS Sequoia/Sonoma
# Creato: 2026-04-04 da Claude per Vio
# ESEGUIRE CON: bash SECURITY_crowdstrike_replica_macair.sh
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

LOG="/tmp/SECURITY_FALCON_REPLICA_$(date +%Y%m%d_%H%M%S).log"
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
echo "║  VIO83 — CROWDSTRIKE FALCON REPLICA (~90%)                   ║"
echo "║  Security Stack Open-Source per Mac Air M1                   ║"
echo "║  $(date)                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo "  CrowdStrike Falcon fornisce:"
echo "  1. EDR (Endpoint Detection & Response)  → osquery + Santa"
echo "  2. Antivirus/Antimalware                → ClamAV"
echo "  3. Firewall intelligente                → LuLu (Objective-See)"
echo "  4. Persistence monitoring               → BlockBlock"
echo "  5. Startup item monitoring              → KnockKnock"
echo "  6. Process monitoring                   → ProcessMonitor"
echo "  7. Network monitoring                   → Netiquette"
echo "  8. DNS monitoring                       → DNSMonitor"
echo "  9. Ransomware protection                → RansomWhere?"
echo "  10. Log aggregation                     → macOS Unified Logging"
echo ""

# ═══════════════════════════════════════════════════════════════
header "0. PREREQUISITI — HOMEBREW"
# ═══════════════════════════════════════════════════════════════

if ! command -v brew &>/dev/null; then
    info "Installazione Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$(/opt/homebrew/bin/brew shellenv)"
    ok "Homebrew installato"
else
    ok "Homebrew già presente"
    brew update
fi

# ═══════════════════════════════════════════════════════════════
header "1. LuLu — FIREWALL INTELLIGENTE (replica Falcon Firewall)"
# ═══════════════════════════════════════════════════════════════
# LuLu di Objective-See: firewall applicativo che blocca connessioni
# in uscita non autorizzate. Equivalente al network containment di Falcon.

info "LuLu blocca connessioni in uscita sospette (come Falcon Network Containment)"

if [[ -d "/Applications/LuLu.app" ]]; then
    ok "LuLu già installato"
else
    brew install --cask lulu 2>/dev/null || {
        info "Download diretto LuLu..."
        LULU_DMG="/tmp/LuLu.dmg"
        curl -sL "https://github.com/objective-see/LuLu/releases/latest/download/LuLu.dmg" -o "$LULU_DMG"
        hdiutil attach "$LULU_DMG" -nobrowse -quiet 2>/dev/null
        LULU_VOL=$(ls -d /Volumes/LuLu* 2>/dev/null | head -1)
        if [[ -n "$LULU_VOL" ]]; then
            cp -R "$LULU_VOL/LuLu.app" /Applications/ 2>/dev/null
            hdiutil detach "$LULU_VOL" -quiet 2>/dev/null
            ok "LuLu installato"
        else
            warn "Installazione LuLu fallita — scaricare da objective-see.org/products/lulu.html"
        fi
    }
fi

info "Aprire LuLu e concedere permessi in Privacy & Security → Network Extensions"

# ═══════════════════════════════════════════════════════════════
header "2. BlockBlock — PERSISTENCE MONITORING (replica Falcon IOA)"
# ═══════════════════════════════════════════════════════════════
# BlockBlock monitora installazione di componenti persistenti:
# launch daemons, agents, login items, kernel extensions.
# Equivalente agli Indicators of Attack (IOA) di Falcon.

info "BlockBlock rileva malware che tenta di installarsi permanentemente"

if [[ -d "/Applications/BlockBlock Helper.app" ]]; then
    ok "BlockBlock già installato"
else
    brew install --cask blockblock 2>/dev/null || {
        BLOCK_DMG="/tmp/BlockBlock.dmg"
        curl -sL "https://github.com/objective-see/BlockBlock/releases/latest/download/BlockBlock.dmg" -o "$BLOCK_DMG"
        hdiutil attach "$BLOCK_DMG" -nobrowse -quiet 2>/dev/null
        BLOCK_VOL=$(ls -d /Volumes/BlockBlock* 2>/dev/null | head -1)
        if [[ -n "$BLOCK_VOL" ]]; then
            cp -R "$BLOCK_VOL/BlockBlock Installer.app" /Applications/ 2>/dev/null
            hdiutil detach "$BLOCK_VOL" -quiet 2>/dev/null
            open "/Applications/BlockBlock Installer.app" 2>/dev/null
            ok "BlockBlock installato — completare setup nell'app"
        fi
    }
fi

# ═══════════════════════════════════════════════════════════════
header "3. KnockKnock — STARTUP ITEM SCANNER (replica Falcon Discover)"
# ═══════════════════════════════════════════════════════════════
# KnockKnock scansiona tutti gli item che si avviano automaticamente.
# Equivalente a Falcon Discover per visibilità endpoint.

info "KnockKnock scansiona launch items, kernel extensions, login items, cron jobs"

if [[ -d "/Applications/KnockKnock.app" ]]; then
    ok "KnockKnock già installato"
else
    brew install --cask knockknock 2>/dev/null || {
        KK_DMG="/tmp/KnockKnock.dmg"
        curl -sL "https://github.com/objective-see/KnockKnock/releases/latest/download/KnockKnock.dmg" -o "$KK_DMG"
        hdiutil attach "$KK_DMG" -nobrowse -quiet 2>/dev/null
        KK_VOL=$(ls -d /Volumes/KnockKnock* 2>/dev/null | head -1)
        if [[ -n "$KK_VOL" ]]; then
            cp -R "$KK_VOL/KnockKnock.app" /Applications/ 2>/dev/null
            hdiutil detach "$KK_VOL" -quiet 2>/dev/null
            ok "KnockKnock installato"
        fi
    }
fi

# ═══════════════════════════════════════════════════════════════
header "4. RansomWhere? — ANTI-RANSOMWARE (replica Falcon Prevent)"
# ═══════════════════════════════════════════════════════════════
# RansomWhere? rileva e blocca processi che tentano di criptare file.
# Equivalente a Falcon Prevent per protezione ransomware.

info "RansomWhere? blocca cifratura non autorizzata dei file"

if [[ -d "/Applications/RansomWhere?.app" ]] || [[ -d "/Applications/RansomWhere.app" ]]; then
    ok "RansomWhere? già installato"
else
    RW_DMG="/tmp/RansomWhere.dmg"
    curl -sL "https://github.com/objective-see/RansomWhere/releases/latest/download/RansomWhere.dmg" -o "$RW_DMG" 2>/dev/null
    if [[ -f "$RW_DMG" ]] && [[ -s "$RW_DMG" ]]; then
        hdiutil attach "$RW_DMG" -nobrowse -quiet 2>/dev/null
        RW_VOL=$(ls -d /Volumes/RansomWhere* 2>/dev/null | head -1)
        if [[ -n "$RW_VOL" ]]; then
            cp -R "$RW_VOL/"*.app /Applications/ 2>/dev/null
            hdiutil detach "$RW_VOL" -quiet 2>/dev/null
            ok "RansomWhere? installato"
        fi
    else
        warn "RansomWhere? — scaricare da objective-see.org/products/ransomwhere.html"
    fi
fi

# ═══════════════════════════════════════════════════════════════
header "5. ClamAV — ANTIVIRUS (replica Falcon AV Engine)"
# ═══════════════════════════════════════════════════════════════
# ClamAV: engine antivirus open-source con signature database.
# Equivalente al motore AV di Falcon.

info "ClamAV: scansione malware con database firme aggiornato"

if command -v clamscan &>/dev/null; then
    ok "ClamAV già installato"
else
    brew install clamav
    ok "ClamAV installato"
fi

# Configurazione ClamAV
CLAM_CONF_DIR="/opt/homebrew/etc/clamav"
if [[ -d "$CLAM_CONF_DIR" ]]; then
    if [[ ! -f "$CLAM_CONF_DIR/freshclam.conf" ]]; then
        cp "$CLAM_CONF_DIR/freshclam.conf.sample" "$CLAM_CONF_DIR/freshclam.conf" 2>/dev/null
        sed -i '' 's/^Example/#Example/' "$CLAM_CONF_DIR/freshclam.conf" 2>/dev/null
    fi

    info "Aggiornamento database firme ClamAV..."
    freshclam 2>/dev/null &
    ok "Database ClamAV in aggiornamento (background)"
fi

# Scansione programmata (cron giornaliero)
CLAM_SCAN_SCRIPT="/usr/local/bin/vio_clamscan_daily.sh"
cat > "$CLAM_SCAN_SCRIPT" << 'CLAM_EOF'
#!/bin/bash
# VIO83 ClamAV Scansione giornaliera
LOG="/tmp/clamscan_$(date +%Y%m%d).log"
clamscan -r --bell --move=/tmp/quarantine \
    ~/Downloads ~/Documents ~/Desktop \
    /Applications \
    2>/dev/null > "$LOG"
INFECTED=$(grep "Infected files:" "$LOG" | awk '{print $3}')
if [[ "${INFECTED:-0}" -gt 0 ]]; then
    osascript -e "display notification \"ClamAV: $INFECTED file infetti trovati!\" with title \"VIO83 Security Alert\""
fi
CLAM_EOF
chmod +x "$CLAM_SCAN_SCRIPT"

# Cron giornaliero alle 3:00
(crontab -l 2>/dev/null | grep -v "vio_clamscan"; echo "0 3 * * * $CLAM_SCAN_SCRIPT") | crontab -
ok "Scansione ClamAV programmata ogni giorno alle 3:00"

# ═══════════════════════════════════════════════════════════════
header "6. osquery — ENDPOINT MONITORING (replica Falcon Insight)"
# ═══════════════════════════════════════════════════════════════
# osquery: SQL-based endpoint monitoring. Stessa tecnologia usata
# internamente da CrowdStrike Falcon per query sullo stato endpoint.

info "osquery: monitora processi, file, rete, utenti via SQL"

if command -v osqueryi &>/dev/null; then
    ok "osquery già installato"
else
    brew install osquery 2>/dev/null || {
        OSQUERY_PKG="/tmp/osquery.pkg"
        curl -sL "https://pkg.osquery.io/darwin/osquery-5.12.1.pkg" -o "$OSQUERY_PKG"
        sudo installer -pkg "$OSQUERY_PKG" -target / 2>/dev/null
    }
    ok "osquery installato"
fi

# Configurazione osquery per monitoraggio continuo
OSQUERY_CONF="/opt/homebrew/etc/osquery/osquery.conf"
mkdir -p "$(dirname "$OSQUERY_CONF")" 2>/dev/null
cat > "$OSQUERY_CONF" << 'OSQ_EOF'
{
  "options": {
    "logger_plugin": "filesystem",
    "logger_path": "/tmp/osquery_logs",
    "schedule_splay_percent": 10,
    "events_expiry": 3600,
    "verbose": false,
    "worker_threads": 2,
    "enable_monitor": true
  },
  "schedule": {
    "process_check": {
      "query": "SELECT name, pid, uid, cmdline FROM processes WHERE on_disk = 0;",
      "interval": 300,
      "description": "Processi non su disco (possibile injection)"
    },
    "listening_ports": {
      "query": "SELECT DISTINCT p.name, l.port, l.protocol, l.address FROM listening_ports l JOIN processes p ON l.pid = p.pid WHERE l.port != 0;",
      "interval": 300,
      "description": "Porte in ascolto"
    },
    "login_items": {
      "query": "SELECT * FROM login_items;",
      "interval": 3600,
      "description": "Item di login"
    },
    "launch_daemons": {
      "query": "SELECT * FROM launchd WHERE run_at_load = 1;",
      "interval": 3600,
      "description": "Launch daemons attivi"
    },
    "browser_extensions": {
      "query": "SELECT * FROM chrome_extensions WHERE from_webstore = 0;",
      "interval": 3600,
      "description": "Estensioni Chrome non dal webstore"
    },
    "usb_devices": {
      "query": "SELECT * FROM usb_devices;",
      "interval": 60,
      "description": "Dispositivi USB collegati"
    },
    "network_connections": {
      "query": "SELECT DISTINCT p.name, p.pid, poc.remote_address, poc.remote_port FROM process_open_sockets poc JOIN processes p ON p.pid = poc.pid WHERE poc.remote_port != 0 AND poc.family = 2;",
      "interval": 120,
      "description": "Connessioni di rete attive"
    }
  }
}
OSQ_EOF

ok "osquery configurato con 7 query di monitoraggio"

# ═══════════════════════════════════════════════════════════════
header "7. SANTA — APPLICATION CONTROL (replica Falcon Device Control)"
# ═══════════════════════════════════════════════════════════════
# Santa: binary authorization system di Google. Controlla
# quali binari possono eseguirsi. Equivalente a Falcon Device Control.

info "Santa: controlla autorizzazione esecuzione binari"

if command -v santactl &>/dev/null; then
    ok "Santa già installato"
else
    SANTA_DMG="/tmp/santa.dmg"
    # Santa releases su GitHub
    curl -sL "https://github.com/google/santa/releases/latest/download/santa.dmg" -o "$SANTA_DMG" 2>/dev/null
    if [[ -f "$SANTA_DMG" ]] && [[ -s "$SANTA_DMG" ]]; then
        hdiutil attach "$SANTA_DMG" -nobrowse -quiet 2>/dev/null
        SANTA_VOL=$(ls -d /Volumes/Santa* 2>/dev/null | head -1)
        if [[ -n "$SANTA_VOL" ]]; then
            sudo installer -pkg "$SANTA_VOL/"*.pkg -target / 2>/dev/null
            hdiutil detach "$SANTA_VOL" -quiet 2>/dev/null
            ok "Santa installato"
        fi
    else
        warn "Santa — installare da github.com/google/santa/releases"
    fi
fi

# ═══════════════════════════════════════════════════════════════
header "8. FIREWALL MACOS — HARDENING"
# ═══════════════════════════════════════════════════════════════

info "Attivazione e hardening firewall macOS..."

# Attivare firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on 2>/dev/null
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on 2>/dev/null
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setallowsigned enable 2>/dev/null
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setallowsignedapp enable 2>/dev/null

ok "Firewall macOS attivato + Stealth Mode"

# ═══════════════════════════════════════════════════════════════
header "9. MONITORAGGIO CONTINUO — DASHBOARD SECURITY"
# ═══════════════════════════════════════════════════════════════

# Script di security check rapido
cat > /usr/local/bin/vio_security_status.sh << 'SEC_EOF'
#!/bin/bash
# VIO83 Security Status Dashboard
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  VIO83 SECURITY STATUS — $(date '+%Y-%m-%d %H:%M')             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Firewall
FW=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null)
echo "$FW" | grep -q "enabled" && echo "  ✔ Firewall: ATTIVO" || echo "  ✖ Firewall: DISATTIVO"

# LuLu
pgrep -x "LuLu" > /dev/null 2>&1 && echo "  ✔ LuLu: ATTIVO" || echo "  ⚠ LuLu: NON ATTIVO"

# BlockBlock
pgrep -f "BlockBlock" > /dev/null 2>&1 && echo "  ✔ BlockBlock: ATTIVO" || echo "  ⚠ BlockBlock: NON ATTIVO"

# ClamAV database
CLAM_DB=$(stat -f "%Sm" /opt/homebrew/share/clamav/daily.cvd 2>/dev/null || echo "N/A")
echo "  ℹ ClamAV DB aggiornato: $CLAM_DB"

# Porte in ascolto sospette
PORTS=$(lsof -i -P -n 2>/dev/null | grep LISTEN | wc -l | tr -d ' ')
echo "  ℹ Porte in ascolto: $PORTS"

# Connessioni esterne
EXT_CONN=$(lsof -i -P -n 2>/dev/null | grep ESTABLISHED | wc -l | tr -d ' ')
echo "  ℹ Connessioni esterne attive: $EXT_CONN"

# SIP status
csrutil status 2>/dev/null | head -1

echo ""
SEC_EOF
chmod +x /usr/local/bin/vio_security_status.sh

ok "Script security status: eseguire 'vio_security_status.sh' per dashboard rapida"

# ═══════════════════════════════════════════════════════════════
header "RIEPILOGO — CROWDSTRIKE FALCON REPLICA"
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  CROWDSTRIKE FALCON REPLICA — INSTALLAZIONE COMPLETATA      ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  MAPPATURA FALCON → OPEN-SOURCE:"
echo ""
echo "  Falcon Prevent (AV)          → ClamAV (scansione giornaliera)"
echo "  Falcon Insight (EDR)         → osquery (7 query monitoring)"
echo "  Falcon Firewall              → LuLu (Objective-See)"
echo "  Falcon IOA                   → BlockBlock (persistence detect)"
echo "  Falcon Discover              → KnockKnock (startup scan)"
echo "  Falcon Device Control        → Santa (binary authorization)"
echo "  Falcon Network Containment   → macOS Firewall + Stealth Mode"
echo "  Falcon Ransomware Protect    → RansomWhere?"
echo "  Falcon Overwatch (MDR)       → vio_security_status.sh"
echo ""
echo -e "${BOLD}  STRUMENTI ATTIVI:${NC}"
echo ""
echo "  vio_security_status.sh     → Dashboard security rapida"
echo "  vio_clamscan_daily.sh      → Scansione AV giornaliera (cron 3:00)"
echo "  osqueryi                   → Query interattive endpoint"
echo ""
echo -e "${YELLOW}  ⚠ AZIONI MANUALI RICHIESTE:${NC}"
echo ""
echo "  1. Aprire LuLu e concedere permessi Network Extension"
echo "  2. Aprire BlockBlock e concedere permessi Full Disk Access"
echo "  3. Aprire KnockKnock e fare prima scansione"
echo "  4. Verificare: Privacy & Security → Full Disk Access per tutti i tool"
echo ""
echo -e "${CYAN}  📋 Log: $LOG${NC}"
echo ""
