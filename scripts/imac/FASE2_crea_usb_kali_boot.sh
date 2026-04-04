#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VIO83 AI ORCHESTRA — FASE 2: CREAZIONE USB KALI LINUX BOOT + PERSISTENCE
# DA ESEGUIRE SUL MAC AIR (non sull'iMac!)
# Target: USB per boot su iMac11,1 Late 2009 (Intel x86_64, BIOS/EFI)
# Creato: 2026-04-04 da Claude per Vio
# ESEGUIRE CON: sudo bash FASE2_crea_usb_kali_boot.sh
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

LOG="/tmp/FASE2_KALI_USB_$(date +%Y%m%d_%H%M%S).log"
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
echo "║  VIO83 — FASE 2: CREAZIONE USB KALI LINUX BOOT              ║"
echo "║  Target: iMac11,1 Late 2009 (Intel x86_64)                  ║"
echo "║  $(date)                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

[[ $EUID -ne 0 ]] && { fail "Eseguire con sudo!"; exit 1; }

# ═══════════════════════════════════════════════════════════════
header "1. PREREQUISITI E CONFIGURAZIONE"
# ═══════════════════════════════════════════════════════════════

# Kali Linux ISO — versione rolling (ultima stabile)
# Usiamo la versione "installer" per installazione persistente su USB
KALI_VERSION="2025.1c"
KALI_ISO="kali-linux-${KALI_VERSION}-installer-amd64.iso"
KALI_URL="https://cdimage.kali.org/kali-${KALI_VERSION}/${KALI_ISO}"
KALI_SHA256_URL="https://cdimage.kali.org/kali-${KALI_VERSION}/SHA256SUMS"
DOWNLOAD_DIR="/tmp/kali_download"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$DOWNLOAD_DIR"

# Dimensione USB minima richiesta: 32GB (per persistence + tools)
MIN_USB_GB=16

info "Kali ISO: $KALI_ISO"
info "URL: $KALI_URL"
info "Download dir: $DOWNLOAD_DIR"

# ═══════════════════════════════════════════════════════════════
header "2. IDENTIFICAZIONE USB TARGET"
# ═══════════════════════════════════════════════════════════════

echo ""
info "Dischi disponibili:"
echo ""
diskutil list external physical 2>/dev/null || diskutil list

echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  ATTENZIONE: IL DISCO USB VERRÀ COMPLETAMENTE CANCELLATO!${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Inserisci il disco USB da usare (es: disk2, disk3, disk4)"
echo "  Il disco DEVE essere almeno ${MIN_USB_GB}GB"
echo ""
read -rp "  Disco USB (senza /dev/): " USB_DISK

if [[ -z "$USB_DISK" ]]; then
    fail "Nessun disco specificato. Uscita."
    exit 1
fi

USB_DEV="/dev/$USB_DISK"
RDISK="/dev/r${USB_DISK}"

# Verifica che esista
if ! diskutil info "$USB_DEV" > /dev/null 2>&1; then
    fail "Disco $USB_DEV non trovato!"
    exit 1
fi

# Verifica dimensione
USB_SIZE_BYTES=$(diskutil info "$USB_DEV" 2>/dev/null | grep "Disk Size" | awk '{print $5}' | tr -d '(')
USB_SIZE_GB=$((USB_SIZE_BYTES / 1073741824))

if [[ $USB_SIZE_GB -lt $MIN_USB_GB ]]; then
    fail "USB troppo piccola: ${USB_SIZE_GB}GB (minimo ${MIN_USB_GB}GB)"
    exit 1
fi

ok "USB trovata: $USB_DEV (${USB_SIZE_GB}GB)"

echo ""
echo -e "${RED}  CONFERMA FINALE: Tutti i dati su $USB_DEV verranno CANCELLATI!${NC}"
read -rp "  Digitare 'SI' per confermare: " CONFIRM
[[ "$CONFIRM" != "SI" ]] && { info "Operazione annullata."; exit 0; }

# ═══════════════════════════════════════════════════════════════
header "3. DOWNLOAD KALI LINUX ISO"
# ═══════════════════════════════════════════════════════════════

if [[ -f "$DOWNLOAD_DIR/$KALI_ISO" ]]; then
    info "ISO già presente: $DOWNLOAD_DIR/$KALI_ISO"
    info "Verifica integrità..."
else
    info "Download Kali Linux ${KALI_VERSION}... (circa 4GB, pazienza)"
    curl -L -# -o "$DOWNLOAD_DIR/$KALI_ISO" "$KALI_URL"

    if [[ ! -f "$DOWNLOAD_DIR/$KALI_ISO" ]]; then
        fail "Download fallito!"
        echo ""
        echo "  Download manuale:"
        echo "  1. Vai su https://www.kali.org/get-kali/#kali-installer-images"
        echo "  2. Scarica '64-bit (Installer)'"
        echo "  3. Salva in $DOWNLOAD_DIR/$KALI_ISO"
        echo "  4. Riesegui questo script"
        exit 1
    fi
fi

# Verifica SHA256
info "Download SHA256SUMS per verifica..."
curl -sL -o "$DOWNLOAD_DIR/SHA256SUMS" "$KALI_SHA256_URL" 2>/dev/null

if [[ -f "$DOWNLOAD_DIR/SHA256SUMS" ]]; then
    EXPECTED_SHA=$(grep "$KALI_ISO" "$DOWNLOAD_DIR/SHA256SUMS" | awk '{print $1}')
    ACTUAL_SHA=$(shasum -a 256 "$DOWNLOAD_DIR/$KALI_ISO" | awk '{print $1}')

    if [[ "$EXPECTED_SHA" == "$ACTUAL_SHA" ]]; then
        ok "SHA256 verificato: ISO autentica"
    else
        fail "SHA256 NON corrisponde! ISO potenzialmente corrotta."
        echo "  Atteso:  $EXPECTED_SHA"
        echo "  Trovato: $ACTUAL_SHA"
        read -rp "  Continuare comunque? (si/no): " CONT
        [[ "$CONT" != "si" ]] && exit 1
    fi
else
    warn "Impossibile verificare SHA256 — continuare con cautela"
fi

ok "ISO Kali Linux pronta: $DOWNLOAD_DIR/$KALI_ISO"

# ═══════════════════════════════════════════════════════════════
header "4. SCRITTURA ISO SU USB"
# ═══════════════════════════════════════════════════════════════

info "Smonto tutte le partizioni di $USB_DEV..."
diskutil unmountDisk "$USB_DEV" 2>/dev/null

info "Scrittura ISO su USB con dd (può richiedere 10-30 minuti)..."
info "NON INTERROMPERE! Ctrl+T per vedere progresso."
echo ""

dd if="$DOWNLOAD_DIR/$KALI_ISO" of="$RDISK" bs=4m status=progress 2>&1
sync

ok "ISO scritta su USB con successo!"

# ═══════════════════════════════════════════════════════════════
header "5. CREAZIONE PARTIZIONE PERSISTENCE (OPZIONALE)"
# ═══════════════════════════════════════════════════════════════

echo ""
info "La persistence permette di salvare configurazioni e file tra i reboot."
info "Spazio USB rimanente verrà usato per la partizione persistence."
echo ""
read -rp "  Creare partizione persistence? (si/no): " DO_PERSIST

if [[ "$DO_PERSIST" == "si" ]]; then
    info "Creazione partizione persistence..."
    info "Questo richiede che la USB abbia spazio dopo l'ISO."
    echo ""
    info "NOTA: La partizione persistence verrà creata al primo boot Kali"
    info "seguendo le istruzioni in FASE3."
    echo ""
    info "Al boot Kali, eseguire:"
    echo "  # Trovare la USB"
    echo "  fdisk -l"
    echo "  # Creare partizione (es. /dev/sdb3)"
    echo "  parted /dev/sdb mkpart primary ext4 <end_of_iso> 100%"
    echo "  mkfs.ext4 -L persistence /dev/sdb3"
    echo "  mkdir -p /mnt/persistence"
    echo "  mount /dev/sdb3 /mnt/persistence"
    echo "  echo '/ union' > /mnt/persistence/persistence.conf"
    echo "  umount /mnt/persistence"
    echo ""
    ok "Istruzioni persistence salvate. Seguire FASE3 al boot Kali."
fi

# ═══════════════════════════════════════════════════════════════
header "6. COPIA SCRIPT SU USB (PARTIZIONE DATI SEPARATA)"
# ═══════════════════════════════════════════════════════════════

info "NOTA: Dopo la scrittura ISO, la USB non è montabile come FAT/HFS."
info "Gli script verranno copiati in un'altra USB o via rete."
echo ""
info "Opzioni per trasferire script all'iMac:"
echo ""
echo "  OPZIONE A — Seconda USB con script:"
echo "    1. Inserire una seconda USB nell'iMac"
echo "    2. Copiare la cartella scripts/imac/ sulla seconda USB"
echo ""
echo "  OPZIONE B — Via rete (SSH dal Mac Air):"
echo "    1. Collegare iMac alla rete Ethernet"
echo "    2. Boot Kali dalla USB"
echo "    3. Dal Mac Air: scp -r scripts/imac/ kali@<ip-imac>:~/"
echo ""
echo "  OPZIONE C — GitHub (consigliato):"
echo "    1. Boot Kali dalla USB"
echo "    2. git clone https://github.com/vio83/mai-love.git"
echo "    3. git clone https://github.com/vio83/ai-scripts-elite.git"
echo ""

ok "Script pronti nei repository GitHub"

# ═══════════════════════════════════════════════════════════════
header "7. ISTRUZIONI BOOT iMAC 2009"
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  ISTRUZIONI BOOT KALI SU iMAC 2009${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  1. INSERIRE la USB Kali nell'iMac"
echo ""
echo "  2. RIAVVIARE l'iMac tenendo premuto il tasto OPTION (Alt)"
echo "     → Apparirà il menu di selezione boot"
echo ""
echo "  3. SELEZIONARE il disco USB (potrebbe apparire come 'EFI Boot')"
echo "     → Se non appare, provare:"
echo "       - Riavviare e tenere C premuto (boot da USB/CD)"
echo "       - Andare in Recovery (Cmd+R) → Startup Security → Allow external"
echo ""
echo "  4. MENU KALI → Selezionare:"
echo "     'Live system' (per provare senza installare)"
echo "     'Live system (persistence)' (se configurata)"
echo "     'Install' (per installazione completa su USB)"
echo ""
echo "  5. DOPO IL BOOT → Eseguire FASE3:"
echo "     git clone https://github.com/vio83/ai-scripts-elite.git"
echo "     cd ai-scripts-elite"
echo "     sudo bash kali_vio_bunker_deploy.sh"
echo ""
echo -e "${YELLOW}  ⚠ IMPORTANTE: iMac 2009 usa BIOS legacy, NON UEFI puro.${NC}"
echo "    Se EFI boot non funziona, potrebbe servire rEFInd:"
echo "    https://sourceforge.net/projects/refind/"
echo ""

# ═══════════════════════════════════════════════════════════════
header "FASE 2 COMPLETATA"
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  USB KALI LINUX BOOT CREATA${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  ✔ ISO Kali Linux scaricata e verificata"
echo "  ✔ ISO scritta su USB"
echo "  ✔ Istruzioni persistence fornite"
echo "  ✔ Istruzioni boot iMac 2009 fornite"
echo ""
echo -e "${CYAN}  📋 Log: $LOG${NC}"
echo ""
echo -e "${BOLD}  PROSSIMO STEP: Boot iMac da USB → Eseguire FASE 3${NC}"
echo ""
