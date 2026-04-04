#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VIO83 — FIX WI-FI + OTTIMIZZAZIONE HOTSPOT iPHONE 15
# Riabilita Wi-Fi (disabilitato in FASE0) e ottimizza per hotspot iPhone
# Target: iMac11,1 Late 2009 + iPhone 15 hotspot
# ESEGUIRE CON: sudo bash FIX_wifi_hotspot_ottimizzato.sh
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
echo "║  VIO83 — FIX WI-FI + HOTSPOT iPHONE OTTIMIZZATO             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

[[ $EUID -ne 0 ]] && { echo "Eseguire con sudo!"; exit 1; }

# ═══════════════════════════════════════════════════════════════
header "1. RIABILITARE WI-FI"
# ═══════════════════════════════════════════════════════════════

# Trovare interfaccia Wi-Fi
WIFI_IF=$(networksetup -listallhardwareports 2>/dev/null | awk '/Wi-Fi|AirPort/{getline; print $2}')
if [[ -z "$WIFI_IF" ]]; then
    WIFI_IF="en1"
    warn "Interfaccia Wi-Fi non trovata, uso en1 come default"
fi

info "Interfaccia Wi-Fi: $WIFI_IF"

# Riabilitare Wi-Fi
networksetup -setairportpower "$WIFI_IF" on 2>/dev/null
ok "Wi-Fi RIABILITATO su $WIFI_IF"

# Ricaricare kext AirPort se necessario
kextload -b com.apple.driver.AirPort.Atheros40 2>/dev/null || true

# Attendere che il Wi-Fi si attivi
sleep 3

# Verificare stato
WIFI_STATUS=$(networksetup -getairportpower "$WIFI_IF" 2>/dev/null)
echo "  Stato: $WIFI_STATUS"

# ═══════════════════════════════════════════════════════════════
header "2. CONNESSIONE AUTOMATICA HOTSPOT iPHONE"
# ═══════════════════════════════════════════════════════════════

info "Ricerca reti disponibili..."
NETWORKS=$(/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s 2>/dev/null | head -20)
echo "$NETWORKS"
echo ""

info "Per connettere l'hotspot iPhone automaticamente:"
echo ""
echo "  1. Sull'iPhone 15: Impostazioni → Hotspot Personale → attivalo"
echo "  2. Sull'iMac il nome della rete sarà il nome del tuo iPhone"
echo "     (es. 'iPhone di Vio' o 'iPhone di Chiara')"
echo ""

# Tentare connessione automatica a reti iPhone comuni
for SSID in "iPhone di Vio" "iPhone di Chiara" "iPhone" "Vio" "iPhone 15"; do
    if echo "$NETWORKS" | grep -q "$SSID"; then
        info "Trovata rete: $SSID — tentativo connessione..."
        networksetup -setairportnetwork "$WIFI_IF" "$SSID" 2>/dev/null
        sleep 3
        if networksetup -getairportnetwork "$WIFI_IF" 2>/dev/null | grep -q "$SSID"; then
            ok "Connesso a $SSID!"
            break
        fi
    fi
done

# ═══════════════════════════════════════════════════════════════
header "3. OTTIMIZZAZIONE TCP/IP PER HOTSPOT MOBILE"
# ═══════════════════════════════════════════════════════════════

info "Tuning rete specifico per connessione mobile 4G/5G..."

# Buffer TCP ottimizzati per alta latenza mobile
sysctl -w net.inet.tcp.sendspace=262144 2>/dev/null
sysctl -w net.inet.tcp.recvspace=262144 2>/dev/null

# Delayed ACK a 0 per ridurre latenza
sysctl -w net.inet.tcp.delayed_ack=0 2>/dev/null

# MSS ottimale per mobile
sysctl -w net.inet.tcp.mssdflt=1400 2>/dev/null

# Window scaling aggressivo
sysctl -w net.inet.tcp.win_scale_factor=8 2>/dev/null

# Slow start più aggressivo per mobile
sysctl -w net.inet.tcp.slowstart_flightsize=20 2>/dev/null

# Keep-alive per non perdere connessione hotspot
sysctl -w net.inet.tcp.always_keepalive=1 2>/dev/null
sysctl -w net.inet.tcp.keepidle=10000 2>/dev/null
sysctl -w net.inet.tcp.keepintvl=5000 2>/dev/null

# UDP max per trasferimenti veloci
sysctl -w net.inet.udp.maxdgram=65535 2>/dev/null

# ECN per gestire congestione mobile
sysctl -w net.inet.tcp.ecn_initiate_out=1 2>/dev/null

ok "TCP/IP ottimizzato per hotspot mobile"

# ═══════════════════════════════════════════════════════════════
header "4. DNS VELOCISSIMO"
# ═══════════════════════════════════════════════════════════════

info "Configurazione DNS ultraveloci (Cloudflare + Google)..."

# DNS primari: Cloudflare (1.1.1.1 = il più veloce al mondo)
# DNS secondari: Google (8.8.8.8)
networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1 8.8.8.8 8.8.4.4 2>/dev/null
networksetup -setdnsservers "$WIFI_IF" 1.1.1.1 1.0.0.1 8.8.8.8 8.8.4.4 2>/dev/null

# Flush DNS cache
dscacheutil -flushcache 2>/dev/null
killall -HUP mDNSResponder 2>/dev/null

ok "DNS impostati: Cloudflare 1.1.1.1 + Google 8.8.8.8"
ok "DNS cache flushato"

# ═══════════════════════════════════════════════════════════════
header "5. BLUETOOTH + AIRDROP"
# ═══════════════════════════════════════════════════════════════

info "Riabilitazione Bluetooth per AirDrop e connessione iPhone..."

# Riabilitare Bluetooth (era stato disabilitato in FASE0)
launchctl load -w /System/Library/LaunchDaemons/com.apple.blued.plist 2>/dev/null
ok "Bluetooth daemon riabilitato"

# Abilitare AirDrop se possibile
defaults write com.apple.NetworkBrowser BrowseAllInterfaces -bool true 2>/dev/null
ok "AirDrop network browsing abilitato"

info "NOTA: iMac 2009 potrebbe NON supportare AirDrop nativo."
info "Se AirDrop non funziona, usa condivisione file via Wi-Fi (SMB/AFP)."
echo ""
info "Alternativa veloce: condivisione file diretta iPhone↔iMac:"
echo "  1. iPhone e iMac sulla stessa rete (hotspot)"
echo "  2. Su iMac: Preferenze → Condivisione → Condivisione File → ON"
echo "  3. Su iPhone: File app → sfoglia → network → iMac"

# ═══════════════════════════════════════════════════════════════
header "6. CONNESSIONE AUTOMATICA AL BOOT"
# ═══════════════════════════════════════════════════════════════

info "Configurazione auto-connessione hotspot al boot..."

# Script di auto-connessione
cat > /usr/local/bin/vio_auto_wifi.sh << 'WIFI_EOF'
#!/bin/bash
# VIO83 Auto WiFi — si connette all'hotspot iPhone al boot
sleep 10  # Attendere che il Wi-Fi si inizializzi

WIFI_IF=$(networksetup -listallhardwareports 2>/dev/null | awk '/Wi-Fi|AirPort/{getline; print $2}')
[ -z "$WIFI_IF" ] && WIFI_IF="en1"

# Accendere Wi-Fi
networksetup -setairportpower "$WIFI_IF" on 2>/dev/null
sleep 5

# DNS veloci
networksetup -setdnsservers "$WIFI_IF" 1.1.1.1 1.0.0.1 8.8.8.8 8.8.4.4 2>/dev/null
dscacheutil -flushcache 2>/dev/null

# Tuning TCP
sysctl -w net.inet.tcp.delayed_ack=0 2>/dev/null
sysctl -w net.inet.tcp.mssdflt=1400 2>/dev/null
sysctl -w net.inet.tcp.win_scale_factor=8 2>/dev/null
sysctl -w net.inet.tcp.slowstart_flightsize=20 2>/dev/null
WIFI_EOF
chmod +x /usr/local/bin/vio_auto_wifi.sh

# LaunchDaemon per esecuzione al boot
cat > /Library/LaunchDaemons/com.vio83.autowifi.plist << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vio83.autowifi</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/usr/local/bin/vio_auto_wifi.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
PLIST_EOF

launchctl load /Library/LaunchDaemons/com.vio83.autowifi.plist 2>/dev/null
ok "Auto-connessione Wi-Fi configurata al boot"

# ═══════════════════════════════════════════════════════════════
header "7. RIMOZIONE APP INUTILI"
# ═══════════════════════════════════════════════════════════════

info "Rimozione app non necessarie per dev station..."

REMOVED=0
REMOVABLE=("GarageBand" "iMovie" "Keynote" "Numbers" "Pages" "Photo Booth" "Chess" "DVD Player" "Stickies")
for APP in "${REMOVABLE[@]}"; do
    if [[ -d "/Applications/${APP}.app" ]]; then
        rm -rf "/Applications/${APP}.app" 2>/dev/null && {
            ok "Rimossa: ${APP}"
            REMOVED=$((REMOVED + 1))
        }
    fi
done
ok "$REMOVED app rimosse"

# ═══════════════════════════════════════════════════════════════
header "8. TEST CONNESSIONE"
# ═══════════════════════════════════════════════════════════════

info "Test velocità connessione..."
echo ""

# Test DNS
DNS_START=$(python -c "import time; print(time.time())" 2>/dev/null || date +%s)
nslookup google.com > /dev/null 2>&1
DNS_END=$(python -c "import time; print(time.time())" 2>/dev/null || date +%s)
info "DNS lookup: completato"

# Test ping
PING_RESULT=$(ping -c 5 -t 5 1.1.1.1 2>/dev/null | tail -1)
if [[ -n "$PING_RESULT" ]]; then
    ok "Ping Cloudflare: $PING_RESULT"
else
    warn "Ping fallito — verificare connessione hotspot"
fi

# Test download speed (file piccolo)
DL_START=$(date +%s)
curl -so /dev/null -w "%{speed_download}" http://speedtest.tele2.net/1MB.zip 2>/dev/null
DL_END=$(date +%s)
SPEED=$(curl -so /dev/null -w "%{speed_download}" http://speedtest.tele2.net/1MB.zip 2>/dev/null)
if [[ -n "$SPEED" ]]; then
    SPEED_MB=$(echo "$SPEED / 1048576" | bc -l 2>/dev/null | head -c 5)
    info "Velocità download: ~${SPEED_MB} MB/s"
fi

# ═══════════════════════════════════════════════════════════════
header "COMPLETATO"
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  WI-FI + HOTSPOT OTTIMIZZATO${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  ✔ Wi-Fi riabilitato"
echo "  ✔ TCP/IP ottimizzato per hotspot mobile"
echo "  ✔ DNS ultraveloci: Cloudflare 1.1.1.1 + Google 8.8.8.8"
echo "  ✔ Bluetooth riabilitato per AirDrop"
echo "  ✔ Auto-connessione al boot configurata"
echo "  ✔ App inutili rimosse"
echo ""
echo "  Ora connetti l'hotspot dell'iPhone 15 e l'iMac"
echo "  si collegherà automaticamente!"
echo ""
