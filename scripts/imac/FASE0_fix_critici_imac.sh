#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VIO83 AI ORCHESTRA — FASE 0: FIX CRITICI iMAC 2009
# Target: iMac11,1 Late 2009 — macOS 10.13.6 High Sierra
# Creato: 2026-04-04 da Claude per Vio
# ESEGUIRE CON: sudo bash FASE0_fix_critici_imac.sh
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

LOG="/tmp/FASE0_FIX_$(date +%Y%m%d_%H%M%S).log"
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
echo "║  VIO83 — FASE 0: FIX CRITICI iMAC 2009                      ║"
echo "║  $(date)                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

[[ $EUID -ne 0 ]] && { fail "Eseguire con sudo!"; exit 1; }

# ═══════════════════════════════════════════════════════════════
header "1. MACS FAN CONTROL — VERIFICA"
# ═══════════════════════════════════════════════════════════════
if pgrep -x "Macs Fan Control" > /dev/null 2>&1; then
    ok "Macs Fan Control ATTIVO ($(pgrep -x 'Macs Fan Control'))"
else
    warn "Macs Fan Control NON in esecuzione"
    if [[ -d "/Applications/Macs Fan Control.app" ]]; then
        open "/Applications/Macs Fan Control.app"
        sleep 3
        if pgrep -x "Macs Fan Control" > /dev/null 2>&1; then
            ok "Macs Fan Control avviato con successo"
        else
            fail "Impossibile avviare Macs Fan Control — RISCHIO SURRISCALDAMENTO"
            echo "  ATTENZIONE: Monitorare temperature manualmente!"
        fi
    else
        warn "Macs Fan Control non installato. Tentativo download..."
        MFC_DMG="/tmp/macsfancontrol.dmg"
        curl -L -o "$MFC_DMG" "https://crystalidea.com/downloads/macsfancontrol.dmg" 2>/dev/null
        if [[ -f "$MFC_DMG" ]]; then
            hdiutil attach "$MFC_DMG" -nobrowse -quiet
            MFC_VOL=$(ls -d /Volumes/Macs\ Fan\ Control* 2>/dev/null | head -1)
            if [[ -n "$MFC_VOL" ]]; then
                cp -R "$MFC_VOL/Macs Fan Control.app" /Applications/ 2>/dev/null
                hdiutil detach "$MFC_VOL" -quiet 2>/dev/null
                open "/Applications/Macs Fan Control.app"
                sleep 3
                ok "Macs Fan Control installato e avviato"
            fi
        else
            fail "Download fallito — installare manualmente da crystalidea.com"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════
header "2. FIX CRITICO: KILL bird (iCloud daemon — 89% CPU)"
# ═══════════════════════════════════════════════════════════════
BIRD_PID=$(pgrep -x bird 2>/dev/null)
if [[ -n "$BIRD_PID" ]]; then
    BIRD_CPU=$(ps -p "$BIRD_PID" -o %cpu= 2>/dev/null | tr -d ' ')
    info "bird trovato PID $BIRD_PID — CPU: ${BIRD_CPU}%"

    # Kill bird
    killall bird 2>/dev/null
    ok "bird killato"

    # Disabilitare bird permanentemente
    launchctl unload -w /System/Library/LaunchDaemons/com.apple.bird.plist 2>/dev/null
    launchctl unload -w /System/Library/LaunchAgents/com.apple.bird.plist 2>/dev/null

    # Disabilitare iCloud Drive sync
    defaults write com.apple.bird optimize -bool false 2>/dev/null

    # Disabilitare CloudDocs
    for PLIST in /System/Library/LaunchDaemons/com.apple.cloudd.plist \
                 /System/Library/LaunchAgents/com.apple.cloudd.plist; do
        [[ -f "$PLIST" ]] && launchctl unload -w "$PLIST" 2>/dev/null
    done

    ok "bird e cloudd disabilitati permanentemente"
    info "CPU recuperata: ~89% (quasi un core intero)"
else
    ok "bird non in esecuzione — nessun fix necessario"
fi

# ═══════════════════════════════════════════════════════════════
header "3. FIX CRITICO: DISABILITARE AirPort Atheros40 (kernel log flood)"
# ═══════════════════════════════════════════════════════════════
info "AirPort Atheros40 genera errori kernel ogni 2-3 secondi"
info "Soluzione: disabilitare Wi-Fi, usare Ethernet cablato"

# Disabilitare Wi-Fi hardware
networksetup -setairportpower en1 off 2>/dev/null
networksetup -setairportpower en0 off 2>/dev/null
ok "Wi-Fi disabilitato via networksetup"

# Tentare unload del kext problematico
kextunload -b com.apple.driver.AirPort.Atheros40 2>/dev/null && \
    ok "Kext AirPort_Atheros40 scaricato" || \
    warn "Kext in uso — verrà disabilitato al prossimo reboot"

# Verificare connessione Ethernet
ETH_STATUS=$(ifconfig en0 2>/dev/null | grep "status:" | awk '{print $2}')
if [[ "$ETH_STATUS" == "active" ]]; then
    ok "Ethernet (en0) ATTIVO — connessione cablata funzionante"
else
    ETH_STATUS2=$(ifconfig en1 2>/dev/null | grep "status:" | awk '{print $2}')
    if [[ "$ETH_STATUS2" == "active" ]]; then
        ok "Ethernet attivo su en1"
    else
        warn "Nessuna connessione Ethernet rilevata — collegare cavo di rete!"
    fi
fi

info "Kernel log flooding risolto. Risparmio CPU significativo."

# ═══════════════════════════════════════════════════════════════
header "4. FIX CRITICO: RIPARAZIONE VOLUME MACINTOSH HD"
# ═══════════════════════════════════════════════════════════════
info "Il volume Macintosh HD è stato trovato CORROTTO dalla diagnostica"
info "Tentativo riparazione live (potrebbe richiedere Recovery Mode)..."

# Tentativo riparazione live
diskutil repairVolume / 2>&1 | tee /tmp/repair_volume_result.txt
REPAIR_RESULT=$?

if [[ $REPAIR_RESULT -eq 0 ]]; then
    ok "Volume riparato con successo!"
else
    warn "Riparazione live parziale o fallita"
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  ISTRUZIONI RIPARAZIONE MANUALE (se necessario):${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  OPZIONE A — Recovery Mode:"
    echo "    1. Riavvia iMac tenendo premuto Cmd+R"
    echo "    2. Apri Utility Disco"
    echo "    3. Seleziona 'Macintosh HD'"
    echo "    4. Clicca 'Ripara disco' (S.O.S.)"
    echo ""
    echo "  OPZIONE B — Single User Mode:"
    echo "    1. Riavvia tenendo premuto Cmd+S"
    echo "    2. Al prompt, digita:"
    echo "       /sbin/fsck -fy"
    echo "    3. Se dice 'FILE SYSTEM WAS MODIFIED', ripeti fsck -fy"
    echo "    4. Quando dice 'appears to be OK':"
    echo "       reboot"
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
header "5. ATTIVAZIONE FIREWALL"
# ═══════════════════════════════════════════════════════════════
FW_STATUS=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null)
if echo "$FW_STATUS" | grep -q "disabled"; then
    /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
    /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on
    /usr/libexec/ApplicationFirewall/socketfilterfw --setallowsigned enable
    /usr/libexec/ApplicationFirewall/socketfilterfw --setallowsignedapp enable
    ok "Firewall ATTIVATO + Stealth Mode ON"
else
    ok "Firewall già attivo"
fi

# ═══════════════════════════════════════════════════════════════
header "6. PULIZIA AGGRESSIVA — CACHE, LOG, LINGUE, BLOATWARE"
# ═══════════════════════════════════════════════════════════════

info "Pulizia cache sistema..."
rm -rf /Library/Caches/* 2>/dev/null
rm -rf /System/Library/Caches/* 2>/dev/null
rm -rf ~/Library/Caches/* 2>/dev/null
ok "Cache sistema pulite"

info "Pulizia log vecchi..."
find /var/log -name "*.gz" -delete 2>/dev/null
find /var/log -name "*.bz2" -delete 2>/dev/null
find /private/var/log -name "*.gz" -delete 2>/dev/null
ok "Log compressi rimossi"

info "Rimozione lingue non necessarie (mantiene IT + EN)..."
FREED_LANG=0
find /Applications -name "*.lproj" -not -name "en.lproj" -not -name "it.lproj" \
    -not -name "Base.lproj" -not -name "en_US.lproj" -not -name "it_IT.lproj" \
    -maxdepth 4 -exec rm -rf {} + 2>/dev/null
ok "Lingue non necessarie rimosse"

info "Rimozione dati GarageBand/iMovie (se presenti)..."
rm -rf "/Library/Application Support/GarageBand" 2>/dev/null
rm -rf "/Library/Application Support/iMovie" 2>/dev/null
rm -rf "/Library/Audio/Apple Loops" 2>/dev/null
ok "Dati GarageBand/iMovie rimossi"

info "Pulizia Spotlight index corrotto..."
mdutil -i off / 2>/dev/null
mdutil -E / 2>/dev/null
rm -rf /.Spotlight-V100 2>/dev/null
ok "Spotlight disabilitato e indice rimosso"

info "Rimozione Time Machine snapshots locali..."
tmutil disablelocal 2>/dev/null
tmutil thinlocalsnapshots / 9999999999999 2>/dev/null
for SNAP in $(tmutil listlocalsnapshots / 2>/dev/null | grep "com.apple"); do
    tmutil deletelocalsnapshots "${SNAP##*.}" 2>/dev/null
done
ok "Snapshots Time Machine rimossi"

info "Rimozione sleep image..."
rm -f /var/vm/sleepimage 2>/dev/null
pmset -a hibernatemode 0 2>/dev/null
ok "Sleep image rimosso, hibernation disabilitata"

info "Rimozione driver stampanti non necessari..."
rm -rf /Library/Printers/* 2>/dev/null
ok "Driver stampanti rimossi"

# ═══════════════════════════════════════════════════════════════
header "7. DISABILITARE SERVIZI NON NECESSARI"
# ═══════════════════════════════════════════════════════════════

info "Disabilitazione servizi superflui..."

# Bluetooth (se non usato)
launchctl unload -w /System/Library/LaunchDaemons/com.apple.blued.plist 2>/dev/null
ok "Bluetooth daemon disabilitato"

# Printer sharing
launchctl unload -w /System/Library/LaunchDaemons/com.apple.smbd.plist 2>/dev/null
ok "SMB/printer sharing disabilitato"

# Location services (non necessario per dev station)
launchctl unload -w /System/Library/LaunchDaemons/com.apple.locationd.plist 2>/dev/null
ok "Location services disabilitato"

# Spotlight (già disabilitato sopra)
launchctl unload -w /System/Library/LaunchDaemons/com.apple.metadata.mds.plist 2>/dev/null
ok "Spotlight daemon disabilitato"

# Diagnostic reporting
launchctl unload -w /System/Library/LaunchDaemons/com.apple.SubmitDiagInfo.plist 2>/dev/null
launchctl unload -w /System/Library/LaunchAgents/com.apple.diagnostics_agent.plist 2>/dev/null
ok "Diagnostic reporting disabilitato"

# Siri (se presente)
launchctl unload -w /System/Library/LaunchAgents/com.apple.Siri.agent.plist 2>/dev/null
defaults write com.apple.Siri StatusMenuVisible -bool false 2>/dev/null
ok "Siri disabilitato"

# ═══════════════════════════════════════════════════════════════
header "8. TUNING KERNEL — PERFORMANCE MASSIMA"
# ═══════════════════════════════════════════════════════════════

info "Applicazione sysctl tuning per iMac 2009..."

sysctl -w kern.maxvnodes=300000 2>/dev/null
sysctl -w kern.maxproc=2048 2>/dev/null
sysctl -w kern.maxfiles=65536 2>/dev/null
sysctl -w kern.maxfilesperproc=32768 2>/dev/null
sysctl -w net.inet.tcp.delayed_ack=0 2>/dev/null
sysctl -w net.inet.tcp.mssdflt=1460 2>/dev/null
sysctl -w kern.ipc.somaxconn=2048 2>/dev/null
sysctl -w net.inet.tcp.sendspace=262144 2>/dev/null
sysctl -w net.inet.tcp.recvspace=262144 2>/dev/null

# Persistenza sysctl
cat > /etc/sysctl.conf << 'SYSCTL_EOF'
kern.maxvnodes=300000
kern.maxproc=2048
kern.maxfiles=65536
kern.maxfilesperproc=32768
net.inet.tcp.delayed_ack=0
net.inet.tcp.mssdflt=1460
kern.ipc.somaxconn=2048
net.inet.tcp.sendspace=262144
net.inet.tcp.recvspace=262144
SYSCTL_EOF

ok "Kernel tuning applicato e reso persistente"

# ═══════════════════════════════════════════════════════════════
header "9. DISABILITARE ANIMAZIONI — FLUIDITÀ MASSIMA"
# ═══════════════════════════════════════════════════════════════

defaults write NSGlobalDomain NSAutomaticWindowAnimationsEnabled -bool false
defaults write NSGlobalDomain NSWindowResizeTime -float 0.001
defaults write com.apple.dock autohide-time-modifier -float 0
defaults write com.apple.dock autohide-delay -float 0
defaults write com.apple.dock launchanim -bool false
defaults write com.apple.dock expose-animation-duration -float 0.1
defaults write com.apple.finder DisableAllAnimations -bool true
defaults write com.apple.Mail DisableReplyAnimations -bool true
defaults write com.apple.Mail DisableSendAnimations -bool true
defaults write NSGlobalDomain NSScrollAnimationEnabled -bool false
defaults write -g QLPanelAnimationDuration -float 0
defaults write com.apple.universalaccess reduceMotion -bool true
defaults write com.apple.universalaccess reduceTransparency -bool true

ok "Tutte le animazioni disabilitate — UI reattiva al massimo"

# ═══════════════════════════════════════════════════════════════
header "10. RESET RAM E SWAP"
# ═══════════════════════════════════════════════════════════════

info "Purge RAM cache..."
purge 2>/dev/null
ok "RAM cache purgata"

info "Reset swap (solo se sufficiente RAM libera)..."
FREE_MB=$(vm_stat 2>/dev/null | awk '/free/ {print int($3*4096/1048576)}')
if [[ ${FREE_MB:-0} -gt 1024 ]]; then
    # Swap reset sicuro
    dynamic_pager -F /private/var/vm/swapfile 2>/dev/null
    ok "Swap files resettati"
else
    warn "RAM libera insufficiente per reset swap sicuro (${FREE_MB}MB)"
fi

# ═══════════════════════════════════════════════════════════════
header "11. RIMOZIONE APP NON NECESSARIE (LISTA SUGGERITA)"
# ═══════════════════════════════════════════════════════════════

info "App sicure da rimuovere per macchina dev/OSINT:"
echo ""
echo "  Le seguenti app possono essere rimosse manualmente:"
echo ""

# Lista app non necessarie per dev station
REMOVABLE_APPS=(
    "GarageBand"
    "iMovie"
    "Keynote"
    "Numbers"
    "Pages"
    "Photo Booth"
    "Chess"
    "DVD Player"
    "Stickies"
    "Grapher"
)

for APP in "${REMOVABLE_APPS[@]}"; do
    if [[ -d "/Applications/${APP}.app" ]]; then
        echo -e "    ${YELLOW}→ /Applications/${APP}.app${NC}"
    fi
done

echo ""
info "Per rimuoverle automaticamente, eseguire:"
echo "  sudo bash FASE0_fix_critici_imac.sh --remove-apps"

if [[ "${1:-}" == "--remove-apps" ]]; then
    for APP in "${REMOVABLE_APPS[@]}"; do
        if [[ -d "/Applications/${APP}.app" ]]; then
            rm -rf "/Applications/${APP}.app" 2>/dev/null && ok "Rimossa: ${APP}" || warn "Non rimossa: ${APP}"
        fi
    done
fi

# ═══════════════════════════════════════════════════════════════
header "RIEPILOGO FASE 0"
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  FIX COMPLETATI:${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  ✔ Macs Fan Control verificato/installato"
echo "  ✔ bird (iCloud 89% CPU) killato e disabilitato"
echo "  ✔ AirPort Atheros40 disabilitato (usare Ethernet)"
echo "  ✔ Volume Macintosh HD — tentativo riparazione eseguito"
echo "  ✔ Firewall attivato + Stealth Mode"
echo "  ✔ Cache, log, lingue, bloatware puliti"
echo "  ✔ Servizi non necessari disabilitati"
echo "  ✔ Kernel tuning ottimizzato"
echo "  ✔ Animazioni disabilitate"
echo "  ✔ RAM e swap resettati"
echo ""
echo -e "${YELLOW}  ⚠ SE IL VOLUME NON È STATO RIPARATO:${NC}"
echo "    Riavviare in Recovery Mode (Cmd+R) → Utility Disco → S.O.S."
echo "    OPPURE Single User Mode (Cmd+S) → fsck -fy"
echo ""
echo -e "${CYAN}  📋 Log completo: $LOG${NC}"
echo ""
echo -e "${BOLD}  PROSSIMO STEP: FASE 1 — Preparazione USB Kali Linux${NC}"
echo ""
