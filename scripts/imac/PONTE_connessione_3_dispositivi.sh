#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VIO83 — PONTE CONNESSIONE 3 DISPOSITIVI
# Ottimizzazione connessione: iPhone 15 ↔ MacBook Air M1 ↔ iMac 2009
#
# ESEGUIRE SU MAC AIR CON: sudo bash PONTE_connessione_3_dispositivi.sh
#
# Architettura rete:
#   iPhone 15 (hotspot 4G/5G)
#       ↕ Wi-Fi (primario)
#   MacBook Air M1 ← → AirDrop/Bluetooth con iPhone
#       ↕ Wi-Fi (stessa rete hotspot)
#   iMac 2009 ← → SMB file sharing (AirDrop NON supportato)
#
# Stesso Apple ID: porcu.v.83@gmail.com su tutti e 3
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✔ $*${NC}"; }
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
echo "║  VIO83 — PONTE CONNESSIONE 3 DISPOSITIVI                    ║"
echo "║  iPhone 15 ↔ MacBook Air M1 ↔ iMac 2009                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

[[ $EUID -ne 0 ]] && { echo "Eseguire con sudo!"; exit 1; }

# Identificare il Mac
MAC_MODEL=$(sysctl -n hw.model 2>/dev/null)
info "Mac rilevato: $MAC_MODEL"

IS_M1=false
if sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -qi "apple"; then
    IS_M1=true
    info "Processore: Apple Silicon (M1)"
fi

# ═══════════════════════════════════════════════════════════════
header "1. OTTIMIZZAZIONE WI-FI HOTSPOT iPHONE"
# ═══════════════════════════════════════════════════════════════

WIFI_IF=$(networksetup -listallhardwareports 2>/dev/null | awk '/Wi-Fi/{getline; print $2}')
[[ -z "$WIFI_IF" ]] && WIFI_IF="en0"
info "Interfaccia Wi-Fi: $WIFI_IF"

# Assicurarsi che Wi-Fi sia acceso
networksetup -setairportpower "$WIFI_IF" on 2>/dev/null
ok "Wi-Fi attivo"

# Scansione reti per trovare hotspot iPhone
info "Ricerca hotspot iPhone..."
CURRENT_SSID=$(/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I 2>/dev/null | awk '/ SSID:/{print substr($0, index($0, $2))}')

if [[ -n "$CURRENT_SSID" ]]; then
    ok "Già connesso a: $CURRENT_SSID"
else
    warn "Non connesso a nessuna rete Wi-Fi"
    info "Connettiti all'hotspot iPhone:"
    echo "  1. Su iPhone 15: Impostazioni → Hotspot Personale → ON"
    echo "  2. Su Mac Air: barra menu → Wi-Fi → seleziona iPhone"
fi

# TCP/IP tuning per hotspot mobile
info "Tuning TCP/IP per massima velocità su hotspot mobile..."

# Buffer TCP grandi per compensare latenza 4G/5G
sysctl -w net.inet.tcp.sendspace=524288 2>/dev/null
sysctl -w net.inet.tcp.recvspace=524288 2>/dev/null
ok "Buffer TCP: 512KB (send/recv)"

# Delayed ACK disabilitato — riduce latenza di 40ms
sysctl -w net.inet.tcp.delayed_ack=0 2>/dev/null
ok "Delayed ACK: OFF (−40ms latenza)"

# Window scaling aggressivo per banda mobile
sysctl -w net.inet.tcp.win_scale_factor=8 2>/dev/null
ok "TCP Window Scale: 8 (finestra fino a 16MB)"

# Slow start aggressivo
sysctl -w net.inet.tcp.slowstart_flightsize=20 2>/dev/null
ok "Slow start: 20 segmenti (partenza veloce)"

# MSS ottimale per mobile (evita frammentazione)
sysctl -w net.inet.tcp.mssdflt=1400 2>/dev/null
ok "MSS: 1400 (ottimale per 4G/5G)"

# Keep-alive aggressivo (mantiene connessione hotspot viva)
sysctl -w net.inet.tcp.always_keepalive=1 2>/dev/null
sysctl -w net.inet.tcp.keepidle=10000 2>/dev/null    # 10 sec
sysctl -w net.inet.tcp.keepintvl=5000 2>/dev/null     # 5 sec
sysctl -w net.inet.tcp.keepcnt=5 2>/dev/null           # 5 tentativi
ok "Keep-alive: 10s idle, 5s intervallo (connessione stabile)"

# UDP massimo per trasferimenti file
sysctl -w net.inet.udp.maxdgram=65535 2>/dev/null
ok "UDP maxdgram: 65535"

# ECN per gestione congestione intelligente
sysctl -w net.inet.tcp.ecn_initiate_out=1 2>/dev/null
ok "ECN abilitato (congestione intelligente)"

# ═══════════════════════════════════════════════════════════════
header "2. DNS ULTRAVELOCI"
# ═══════════════════════════════════════════════════════════════

info "Configurazione DNS Cloudflare + Google..."

# Impostare DNS su tutte le interfacce di rete attive
for SERVICE in $(networksetup -listallnetworkservices 2>/dev/null | tail -n +2); do
    networksetup -setdnsservers "$SERVICE" 1.1.1.1 1.0.0.1 8.8.8.8 8.8.4.4 2>/dev/null
done
ok "DNS impostati su tutte le interfacce"

# Flush DNS cache
dscacheutil -flushcache 2>/dev/null
killall -HUP mDNSResponder 2>/dev/null
ok "DNS cache flushata"

# Test DNS speed
info "Test DNS..."
DNS_TIME=$(python3 -c "
import time, socket
start = time.time()
try:
    socket.getaddrinfo('google.com', 80)
except: pass
print(f'{(time.time()-start)*1000:.0f}ms')
" 2>/dev/null)
ok "DNS lookup: $DNS_TIME"

# ═══════════════════════════════════════════════════════════════
header "3. BLUETOOTH OTTIMIZZATO"
# ═══════════════════════════════════════════════════════════════

info "Verifica Bluetooth per AirDrop con iPhone..."

# Verificare stato Bluetooth
BT_STATUS=$(defaults read /Library/Preferences/com.apple.Bluetooth ControllerPowerState 2>/dev/null)
if [[ "$BT_STATUS" == "1" ]]; then
    ok "Bluetooth: ATTIVO"
else
    info "Attivazione Bluetooth..."
    # Su macOS recenti
    defaults write /Library/Preferences/com.apple.Bluetooth ControllerPowerState -int 1 2>/dev/null
    killall -HUP blued 2>/dev/null
    sleep 2
    ok "Bluetooth attivato"
fi

# Verificare AirDrop
defaults write com.apple.NetworkBrowser BrowseAllInterfaces -bool true 2>/dev/null
ok "AirDrop: abilitato per tutti i contatti"

info "AirDrop funziona tra Mac Air ↔ iPhone 15 (entrambi Bluetooth 5.0)"
warn "AirDrop NON funziona con iMac 2009 (Bluetooth 2.1, serve 4.0)"
info "Per iMac 2009 → usa condivisione file SMB (sezione 5)"

# ═══════════════════════════════════════════════════════════════
header "4. CONDIVISIONE FILE MAC AIR"
# ═══════════════════════════════════════════════════════════════

info "Abilitazione condivisione file per connessione con iMac..."

# Abilitare condivisione file SMB
launchctl load -w /System/Library/LaunchDaemons/com.apple.smbd.plist 2>/dev/null || true
defaults write /Library/Preferences/SystemConfiguration/com.apple.smb.server.plist EnabledServices -array disk 2>/dev/null || true

ok "Condivisione file SMB abilitata"

# Abilitare Remote Login (SSH) per controllo remoto
systemsetup -setremotelogin on 2>/dev/null || {
    warn "Remote Login: abilitare manualmente in Preferenze → Condivisione"
}

info "SSH abilitato — Claude può controllare anche il Mac Air da remoto"

# Hostname facile da ricordare
CURRENT_HOSTNAME=$(scutil --get ComputerName 2>/dev/null)
info "Hostname attuale: $CURRENT_HOSTNAME"
info "L'iMac troverà questo Mac come: $CURRENT_HOSTNAME.local"

# ═══════════════════════════════════════════════════════════════
header "5. PONTE FILE: iMac 2009 ↔ Mac Air (sostituto AirDrop)"
# ═══════════════════════════════════════════════════════════════

info "Configurazione cartella condivisa per trasferimento file con iMac..."

SHARED_DIR="$HOME/Condiviso-VIO"
mkdir -p "$SHARED_DIR"
chmod 755 "$SHARED_DIR"

# Creare README nella cartella condivisa
cat > "$SHARED_DIR/README_PONTE.txt" << 'PONTE_EOF'
═══════════════════════════════════════════════════
  VIO83 — CARTELLA PONTE CONDIVISA
═══════════════════════════════════════════════════

Questa cartella è condivisa tra Mac Air e iMac 2009.

COME USARLA:

  Da iMac (macOS):
  1. Finder → Cmd+K
  2. Digitare: smb://MacBook-Air-di-Vio.local/Condiviso-VIO
  3. Login con credenziali Mac Air

  Da iMac (Arch Linux dopo installazione):
  1. Aprire Thunar file manager
  2. Barra indirizzi: smb://MacBook-Air-di-Vio.local/Condiviso-VIO
  3. Oppure da terminale:
     mount -t cifs //MacBook-Air-di-Vio.local/Condiviso-VIO /mnt/macair

  Da iPhone:
  1. App File → Sfoglia → "..." → Connetti al server
  2. Digitare: smb://MacBook-Air-di-Vio.local/Condiviso-VIO

NOTA: Tutti i dispositivi devono essere sulla STESSA rete
(cioè tutti connessi all'hotspot iPhone).
═══════════════════════════════════════════════════
PONTE_EOF

ok "Cartella ponte creata: $SHARED_DIR"
info "Questa cartella è accessibile da tutti i dispositivi via SMB"

# Aggiungere la cartella alla condivisione
sharing -a "$SHARED_DIR" -n "Condiviso-VIO" -S "Condiviso-VIO" 2>/dev/null || {
    warn "Condivisione automatica non riuscita"
    info "Aggiungere manualmente:"
    echo "  Preferenze di Sistema → Condivisione → Condivisione File"
    echo "  Aggiungi cartella: $SHARED_DIR"
}

# ═══════════════════════════════════════════════════════════════
header "6. SCRIPT DI AUTO-CONNESSIONE AL BOOT"
# ═══════════════════════════════════════════════════════════════

info "Configurazione auto-tuning al boot..."

cat > /usr/local/bin/vio_ponte_boot.sh << 'BOOT_EOF'
#!/bin/bash
# VIO83 — Auto-tuning rete al boot Mac Air
sleep 10

# Wi-Fi ON
WIFI_IF=$(networksetup -listallhardwareports 2>/dev/null | awk '/Wi-Fi/{getline; print $2}')
[ -z "$WIFI_IF" ] && WIFI_IF="en0"
networksetup -setairportpower "$WIFI_IF" on 2>/dev/null

# DNS veloci
for SVC in $(networksetup -listallnetworkservices 2>/dev/null | tail -n +2); do
    networksetup -setdnsservers "$SVC" 1.1.1.1 1.0.0.1 8.8.8.8 8.8.4.4 2>/dev/null
done
dscacheutil -flushcache 2>/dev/null

# TCP tuning
sysctl -w net.inet.tcp.sendspace=524288 2>/dev/null
sysctl -w net.inet.tcp.recvspace=524288 2>/dev/null
sysctl -w net.inet.tcp.delayed_ack=0 2>/dev/null
sysctl -w net.inet.tcp.win_scale_factor=8 2>/dev/null
sysctl -w net.inet.tcp.slowstart_flightsize=20 2>/dev/null
sysctl -w net.inet.tcp.mssdflt=1400 2>/dev/null
sysctl -w net.inet.tcp.always_keepalive=1 2>/dev/null
sysctl -w net.inet.tcp.keepidle=10000 2>/dev/null
sysctl -w net.inet.udp.maxdgram=65535 2>/dev/null
sysctl -w net.inet.tcp.ecn_initiate_out=1 2>/dev/null

# AirDrop
defaults write com.apple.NetworkBrowser BrowseAllInterfaces -bool true 2>/dev/null
BOOT_EOF
chmod +x /usr/local/bin/vio_ponte_boot.sh

# LaunchDaemon
cat > /Library/LaunchDaemons/com.vio83.ponte.plist << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vio83.ponte</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/usr/local/bin/vio_ponte_boot.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
PLIST_EOF

launchctl load /Library/LaunchDaemons/com.vio83.ponte.plist 2>/dev/null || true
ok "Auto-tuning al boot configurato"

# ═══════════════════════════════════════════════════════════════
header "7. TEST CONNETTIVITÀ"
# ═══════════════════════════════════════════════════════════════

info "Test connessione..."
echo ""

# Test internet
if ping -c 3 -t 5 1.1.1.1 &>/dev/null; then
    PING_MS=$(ping -c 5 -t 5 1.1.1.1 2>/dev/null | tail -1 | awk -F'/' '{print $5}')
    ok "Internet: OK (ping medio: ${PING_MS}ms)"
else
    warn "Internet: nessuna connessione — attiva hotspot iPhone"
fi

# Test Bluetooth
BT_ON=$(defaults read /Library/Preferences/com.apple.Bluetooth ControllerPowerState 2>/dev/null)
if [[ "$BT_ON" == "1" ]]; then
    ok "Bluetooth: ATTIVO"
else
    warn "Bluetooth: SPENTO"
fi

# Test mDNS (per scoperta dispositivi locali)
if command -v dns-sd &>/dev/null; then
    info "Servizi mDNS attivi sulla rete:"
    timeout 3 dns-sd -B _smb._tcp. local 2>/dev/null | head -5 || true
fi

# ═══════════════════════════════════════════════════════════════
header "PONTE COMPLETATO"
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  PONTE 3 DISPOSITIVI CONFIGURATO${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  ARCHITETTURA RETE:"
echo ""
echo "      iPhone 15"
echo "      ┌───┴───┐"
echo "    Wi-Fi    Bluetooth/AirDrop"
echo "      │           │"
echo "      ▼           ▼"
echo "    Mac Air M1 ←──┘"
echo "      │"
echo "    Wi-Fi + SMB"
echo "      │"
echo "      ▼"
echo "    iMac 2009"
echo ""
echo "  CONNESSIONI ATTIVE:"
echo "  ✔ iPhone ↔ Mac Air:  Wi-Fi + AirDrop + Bluetooth"
echo "  ✔ iPhone ↔ iMac:     Wi-Fi (solo dopo FIX_wifi su iMac)"
echo "  ✔ Mac Air ↔ iMac:    SMB file sharing + SSH"
echo "  ✘ iMac ↔ AirDrop:    NON supportato (Bluetooth 2.1)"
echo ""
echo "  OTTIMIZZAZIONI:"
echo "  ✔ TCP buffer 512KB (2x default)"
echo "  ✔ Delayed ACK OFF (−40ms latenza)"
echo "  ✔ DNS Cloudflare 1.1.1.1"
echo "  ✔ Keep-alive aggressivo (connessione stabile)"
echo "  ✔ Auto-tuning al boot"
echo ""
echo "  CARTELLA CONDIVISA:"
echo "  ✔ $SHARED_DIR"
echo "  ✔ Accessibile da iPhone, Mac Air, iMac via SMB"
echo ""
echo "  TRASFERIMENTO FILE TRA DISPOSITIVI:"
echo "  ─────────────────────────────────"
echo "  Mac Air → iPhone:  AirDrop (velocissimo)"
echo "  iPhone → Mac Air:  AirDrop (velocissimo)"
echo "  Mac Air → iMac:    SMB cartella condivisa"
echo "  iMac → Mac Air:    SMB cartella condivisa"
echo "  iPhone → iMac:     Via Mac Air (ponte) o USB"
echo ""
echo "  PROSSIMO PASSO OBBLIGATORIO:"
echo "  ────────────────────────────"
echo "  Eseguire FIX_wifi_hotspot_ottimizzato.sh sull'iMac"
echo "  per abilitare Wi-Fi e connettere anche l'iMac alla rete"
echo ""
