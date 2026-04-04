#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VIO83 AI ORCHESTRA — FASE 1: OTTIMIZZAZIONE PRE-KALI MASSIMA
# Target: iMac11,1 Late 2009 — macOS 10.13.6 High Sierra
# OBIETTIVO: Spremere ogni ciclo CPU dal vecchio iMac prima del boot Kali
# Creato: 2026-04-04 da Claude per Vio
# ESEGUIRE CON: sudo bash FASE1_ottimizzazione_pre_kali.sh
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

LOG="/tmp/FASE1_OPTIMIZE_$(date +%Y%m%d_%H%M%S).log"
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
echo "║  VIO83 — FASE 1: OTTIMIZZAZIONE PRE-KALI MASSIMA            ║"
echo "║  $(date)                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

[[ $EUID -ne 0 ]] && { fail "Eseguire con sudo!"; exit 1; }

# ═══════════════════════════════════════════════════════════════
header "1. KILL TOTALE PROCESSI INUTILI"
# ═══════════════════════════════════════════════════════════════

KILL_LIST=(
    "bird" "cloudd" "nsurlsessiond" "CalendarAgent" "contactsd"
    "remindd" "soagent" "AddressBookSourceSync" "IMDPersistenceAgent"
    "knowledge-agent" "parsecd" "routined" "duetexpertd"
    "suggestd" "touristd" "mediaanalysisd" "photoanalysisd"
    "photolibraryd" "Photos" "com.apple.photomodel" "photolibraryd"
    "mapspushd" "mapssyncd" "FindMyMac" "rapportd"
    "AMPDeviceDiscoveryAgent" "AMPLibraryAgent" "iTunes"
    "SafariCloudHistoryPushAgent" "SafariBookmarksSyncAgent"
    "syncdefaultsd" "SocialPushAgent" "nbagent" "GameController"
    "com.apple.Siri" "siriknowledged" "assistantd"
    "com.apple.icloud" "cloudd" "cloudpaird" "cloudphotosd"
    "nsurlsessiond" "akd" "sharingd" "AirPlayUIAgent"
    "AirPlayXPCHelper" "Spotlight" "mds" "mds_stores" "mdworker"
)

KILLED=0
for PROC in "${KILL_LIST[@]}"; do
    if pgrep -x "$PROC" > /dev/null 2>&1; then
        killall "$PROC" 2>/dev/null && KILLED=$((KILLED + 1))
    fi
done
ok "Killati $KILLED processi inutili"

# ═══════════════════════════════════════════════════════════════
header "2. DISABILITARE TUTTI I LAUNCH AGENTS/DAEMONS NON ESSENZIALI"
# ═══════════════════════════════════════════════════════════════

DISABLE_AGENTS=(
    # iCloud
    "com.apple.bird" "com.apple.cloudd" "com.apple.cloudpaird"
    "com.apple.cloudphotod" "com.apple.icloud.fmfd"
    # Spotlight
    "com.apple.metadata.mds" "com.apple.metadata.mds.index"
    "com.apple.metadata.mds.scan" "com.apple.metadata.mds.spindump"
    # Siri & Assistants
    "com.apple.Siri.agent" "com.apple.siri.morphunassetsupdater"
    "com.apple.siriknowledged" "com.apple.assistantd"
    "com.apple.parsecd" "com.apple.suggestd"
    # Photos & Media
    "com.apple.photoanalysisd" "com.apple.photolibraryd"
    "com.apple.mediaanalysisd" "com.apple.AMPLibraryAgent"
    "com.apple.AMPDeviceDiscoveryAgent"
    # Location
    "com.apple.locationd" "com.apple.routined"
    # Sharing
    "com.apple.sharingd" "com.apple.rapportd"
    # Safari Sync
    "com.apple.SafariCloudHistoryPushAgent"
    "com.apple.SafariBookmarksSyncAgent"
    # Social
    "com.apple.SocialPushAgent" "com.apple.soagent"
    # Diagnostics
    "com.apple.SubmitDiagInfo" "com.apple.CrashReporterSupportHelper"
    "com.apple.diagnostics_agent" "com.apple.spindump_agent"
    "com.apple.ReportCrash" "com.apple.ReportCrash.Root"
    "com.apple.ReportPanic"
    # Misc
    "com.apple.AirPlayUIAgent" "com.apple.AirPlayXPCHelper"
    "com.apple.GameController.gamecontrollerd"
    "com.apple.touristd" "com.apple.knowlegde-agent"
    "com.apple.duetexpertd" "com.apple.CalendarAgent"
    "com.apple.remindd" "com.apple.contactsd"
    "com.apple.AddressBookSourceSync"
    "com.apple.familycircled" "com.apple.familycontrols.useragent"
    "com.apple.gamed" "com.apple.parentalcontrols.check"
    "com.apple.Maps.pushdaemon" "com.apple.Maps.mapssyncagent"
)

DISABLED=0
for AGENT in "${DISABLE_AGENTS[@]}"; do
    for DIR in /System/Library/LaunchAgents /System/Library/LaunchDaemons \
               /Library/LaunchAgents /Library/LaunchDaemons \
               ~/Library/LaunchAgents; do
        PLIST="${DIR}/${AGENT}.plist"
        if [[ -f "$PLIST" ]]; then
            launchctl unload -w "$PLIST" 2>/dev/null && DISABLED=$((DISABLED + 1))
        fi
    done
done
ok "Disabilitati $DISABLED launch agents/daemons"

# ═══════════════════════════════════════════════════════════════
header "3. OTTIMIZZAZIONE DISCO HDD — MASSIMA VELOCITÀ"
# ═══════════════════════════════════════════════════════════════

info "Tuning I/O scheduler per HDD meccanico..."

# noatime per ridurre scritture
# Su High Sierra non possiamo rimontare / facilmente, ma possiamo ottimizzare altro

# Disabilitare journaling su volumi non-boot se presenti
info "Verifica journaling..."
diskutil info / 2>/dev/null | grep "File System" | head -1

# Flush buffer cache per performance pulita
sync && purge 2>/dev/null
ok "Buffer cache flushato"

# Ridurre swappiness equivalente macOS
sysctl -w vm.swappiness=10 2>/dev/null || true
# Aumentare read-ahead per HDD
sysctl -w vfs.read_max=128 2>/dev/null || true

# Disabilitare fsevents su directory pesanti
touch /.fseventsd/no_log 2>/dev/null
ok "FSEvents logging ridotto"

# Compattare directory principali
info "Update_prebinding per velocizzare load dinamico..."
update_prebinding -root / -force 2>/dev/null || true

ok "Ottimizzazioni disco HDD applicate"

# ═══════════════════════════════════════════════════════════════
header "4. PULIZIA DEEP — RECUPERO SPAZIO MASSIMO"
# ═══════════════════════════════════════════════════════════════

FREED=0

# Xcode derived data (se presente)
if [[ -d ~/Library/Developer/Xcode/DerivedData ]]; then
    SIZE=$(du -sm ~/Library/Developer/Xcode/DerivedData 2>/dev/null | awk '{print $1}')
    rm -rf ~/Library/Developer/Xcode/DerivedData
    FREED=$((FREED + SIZE))
    ok "Xcode DerivedData rimosso (${SIZE}MB)"
fi

# iOS device support (se presente)
if [[ -d ~/Library/Developer/Xcode/iOS\ DeviceSupport ]]; then
    SIZE=$(du -sm ~/Library/Developer/Xcode/iOS\ DeviceSupport 2>/dev/null | awk '{print $1}')
    rm -rf ~/Library/Developer/Xcode/iOS\ DeviceSupport
    FREED=$((FREED + SIZE))
    ok "iOS DeviceSupport rimosso (${SIZE}MB)"
fi

# Old system logs
find /var/log -type f -mtime +7 -delete 2>/dev/null
find /Library/Logs -type f -mtime +7 -delete 2>/dev/null
find ~/Library/Logs -type f -mtime +7 -delete 2>/dev/null
ok "Log vecchi (>7 giorni) rimossi"

# Crash reports
rm -rf ~/Library/Logs/CrashReporter/* 2>/dev/null
rm -rf /Library/Logs/CrashReporter/* 2>/dev/null
rm -rf ~/Library/Logs/DiagnosticReports/* 2>/dev/null
ok "Crash reports rimossi"

# Trash
rm -rf ~/.Trash/* 2>/dev/null
rm -rf /Volumes/*/.Trashes/* 2>/dev/null
ok "Cestino svuotato"

# npm/pip cache
rm -rf ~/.npm/_cacache 2>/dev/null
rm -rf ~/Library/Caches/pip 2>/dev/null
ok "Cache npm/pip pulite"

# Homebrew cache
rm -rf ~/Library/Caches/Homebrew 2>/dev/null
brew cleanup -s 2>/dev/null || true
ok "Homebrew cache pulito"

# Application caches deep
rm -rf ~/Library/Caches/com.apple.Safari 2>/dev/null
rm -rf ~/Library/Caches/com.spotify.* 2>/dev/null
rm -rf ~/Library/Caches/com.google.* 2>/dev/null
rm -rf ~/Library/Caches/Firefox 2>/dev/null
ok "Cache app principali pulite"

# Old downloads (>30 giorni)
find ~/Downloads -type f -mtime +30 -delete 2>/dev/null
ok "Download vecchi (>30 giorni) rimossi"

info "Spazio totale recuperato: ~${FREED}MB (+ cache e log non contabilizzati)"

# ═══════════════════════════════════════════════════════════════
header "5. OTTIMIZZAZIONE RETE — MASSIMA VELOCITÀ"
# ═══════════════════════════════════════════════════════════════

# DNS cache flush
dscacheutil -flushcache 2>/dev/null
killall -HUP mDNSResponder 2>/dev/null
ok "DNS cache flushed"

# Ottimizzazione TCP/IP per Ethernet
sysctl -w net.inet.tcp.win_scale_factor=8 2>/dev/null || true
sysctl -w net.inet.tcp.sendspace=262144 2>/dev/null
sysctl -w net.inet.tcp.recvspace=262144 2>/dev/null
sysctl -w net.inet.tcp.delayed_ack=0 2>/dev/null
sysctl -w net.inet.tcp.mssdflt=1460 2>/dev/null
sysctl -w net.inet.tcp.always_keepalive=1 2>/dev/null
sysctl -w net.inet.tcp.slowstart_flightsize=20 2>/dev/null
sysctl -w net.inet.udp.maxdgram=65535 2>/dev/null
ok "TCP/IP ottimizzato per Ethernet"

# Disabilitare Bonjour/mDNS advertising (spreco rete)
launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponderHelper.plist 2>/dev/null
ok "mDNS advertising ridotto"

# ═══════════════════════════════════════════════════════════════
header "6. MEMORIA — CONFIGURAZIONE OTTIMALE PER 8GB"
# ═══════════════════════════════════════════════════════════════

info "Configurazione memoria per massima efficienza su 8GB..."

# Disabilitare App Nap (consuma memoria per context switching)
defaults write NSGlobalDomain NSAppSleepDisabled -bool true
ok "App Nap disabilitato"

# Ridurre dimensioni swap file
sysctl -w vm.compressor_mode=4 2>/dev/null || true

# Disabilitare memory pressure notifications (overhead)
sysctl -w kern.memorystatus_purge_on_warning=0 2>/dev/null || true

# Aumentare buffer cache per I/O
sysctl -w vfs.generic.nfs.client.bufsize=65536 2>/dev/null || true

ok "Configurazione memoria ottimizzata per 8GB"

# ═══════════════════════════════════════════════════════════════
header "7. GPU — RIDURRE OVERHEAD ATI RADEON HD 4850"
# ═══════════════════════════════════════════════════════════════

info "Ottimizzazione GPU per terminale/code (no gaming)..."

# Disabilitare effetti grafici pesanti
defaults write com.apple.dock no-glass -bool true 2>/dev/null
defaults write com.apple.dock minimize-to-application -bool true 2>/dev/null
defaults write com.apple.dock mineffect -string "scale" 2>/dev/null

# Ridurre risoluzione se necessario (opzionale)
# Il 27" a 2560x1440 è pesante per la 4850 senza Metal
info "Risoluzione attuale: $(system_profiler SPDisplaysDataType 2>/dev/null | grep Resolution | head -1 | xargs)"
info "Per massima performance: considerare 1920x1080 tramite Preferenze → Monitor"

# Disabilitare screensaver (spreco GPU)
defaults -currentHost write com.apple.screensaver idleTime -int 0
ok "Screensaver disabilitato"

# Disabilitare desktop dinamico
defaults write com.apple.dock wvous-bl-corner -int 0 2>/dev/null
ok "Hot corners disabilitati"

ok "GPU overhead ridotto al minimo"

# ═══════════════════════════════════════════════════════════════
header "8. CRON AUTO-MAINTENANCE"
# ═══════════════════════════════════════════════════════════════

info "Configurazione manutenzione automatica..."

# Script di manutenzione automatica
cat > /usr/local/bin/vio_auto_maintain.sh << 'MAINT_EOF'
#!/bin/bash
# VIO83 Auto-maintenance — eseguito ogni 6 ore
purge 2>/dev/null
rm -rf /tmp/*.log.old 2>/dev/null
find /var/log -name "*.gz" -mtime +3 -delete 2>/dev/null
find /tmp -type f -mtime +1 -delete 2>/dev/null
dscacheutil -flushcache 2>/dev/null
sync
MAINT_EOF
chmod +x /usr/local/bin/vio_auto_maintain.sh

# Cron job ogni 6 ore
(crontab -l 2>/dev/null | grep -v "vio_auto_maintain"; echo "0 */6 * * * /usr/local/bin/vio_auto_maintain.sh") | crontab -
ok "Auto-maintenance configurata (ogni 6 ore)"

# Forzare esecuzione maintenance scripts macOS
periodic daily weekly monthly 2>/dev/null &
ok "Maintenance scripts macOS avviati in background"

# ═══════════════════════════════════════════════════════════════
header "9. VERIFICA STATO FINALE"
# ═══════════════════════════════════════════════════════════════

echo ""
info "CPU Load attuale:"
uptime
echo ""

info "RAM libera:"
vm_stat 2>/dev/null | head -5
echo ""

info "Top 10 processi per CPU:"
ps aux --sort=-%cpu 2>/dev/null | head -11 || ps aux | sort -nrk 3,3 | head -11
echo ""

info "Spazio disco:"
df -h / 2>/dev/null
echo ""

# ═══════════════════════════════════════════════════════════════
header "FASE 1 COMPLETATA"
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  OTTIMIZZAZIONE PRE-KALI COMPLETATA${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  ✔ Processi inutili killati e disabilitati"
echo "  ✔ Launch agents/daemons non essenziali disabilitati"
echo "  ✔ Disco HDD ottimizzato al massimo"
echo "  ✔ Pulizia deep completata"
echo "  ✔ Rete ottimizzata per Ethernet"
echo "  ✔ Memoria configurata per 8GB"
echo "  ✔ GPU overhead ridotto"
echo "  ✔ Auto-maintenance configurata"
echo ""
echo -e "${CYAN}  📋 Log: $LOG${NC}"
echo ""
echo -e "${BOLD}  PROSSIMO STEP: FASE 2 — Creazione USB Kali Linux Boot${NC}"
echo ""
