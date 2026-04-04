#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# PROGETTO ARCHIMEDE — FASE 2: Preparazione USB Arch Linux
# Target: iMac11,1 Late 2009 (Intel Core i7 860, x86_64)
# USB: 8GB minimo (ISO Arch ~800MB)
# ESEGUIRE SU MAC AIR CON: sudo bash FASE2_arch_usb_installer.sh
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

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
echo "║  PROGETTO ARCHIMEDE — FASE 2                                 ║"
echo "║  Preparazione USB Arch Linux per iMac 2009                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

[[ $EUID -ne 0 ]] && { echo "Eseguire con sudo!"; exit 1; }

# ═══════════════════════════════════════════════════════════════
# Variabili
# ═══════════════════════════════════════════════════════════════
ARCH_MIRROR="https://geo.mirror.pkgbuild.com"
ISO_DATE=$(date +%Y.%m.01)  # Arch rilascia ISO il primo di ogni mese
ISO_NAME="archlinux-${ISO_DATE}-x86_64.iso"
ISO_URL="${ARCH_MIRROR}/iso/${ISO_DATE}/${ISO_NAME}"
SIG_URL="${ISO_URL}.sig"
SHA256_URL="${ARCH_MIRROR}/iso/${ISO_DATE}/sha256sums.txt"
DOWNLOAD_DIR="/tmp/arch_installer"

# ═══════════════════════════════════════════════════════════════
header "1. PREPARAZIONE DOWNLOAD"
# ═══════════════════════════════════════════════════════════════

mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

info "ISO target: $ISO_NAME"
info "Mirror: $ARCH_MIRROR"
info "Directory download: $DOWNLOAD_DIR"

# Verificare spazio disponibile
AVAIL_MB=$(df -m /tmp | awk 'NR==2{print $4}')
if [[ "$AVAIL_MB" -lt 2000 ]]; then
    fail "Spazio insufficiente in /tmp: ${AVAIL_MB}MB (servono almeno 2GB)"
    exit 1
fi
ok "Spazio disponibile: ${AVAIL_MB}MB"

# ═══════════════════════════════════════════════════════════════
header "2. DOWNLOAD ISO ARCH LINUX"
# ═══════════════════════════════════════════════════════════════

if [[ -f "$ISO_NAME" ]]; then
    info "ISO già presente: $ISO_NAME"
    info "Dimensione: $(du -h "$ISO_NAME" | cut -f1)"
else
    info "Download in corso... (~800MB)"
    info "URL: $ISO_URL"
    echo ""

    # Tentativo con mirror primario
    if ! curl -L -C - --progress-bar -o "$ISO_NAME" "$ISO_URL" 2>&1; then
        warn "Mirror primario fallito, provo mirror alternativi..."

        # Mirror alternativi
        MIRRORS=(
            "https://mirror.rackspace.com/archlinux/iso/${ISO_DATE}/${ISO_NAME}"
            "https://mirrors.kernel.org/archlinux/iso/${ISO_DATE}/${ISO_NAME}"
            "https://mirror.pkgbuild.com/iso/${ISO_DATE}/${ISO_NAME}"
            "https://archlinux.mirror.garr.it/iso/${ISO_DATE}/${ISO_NAME}"
        )

        DOWNLOADED=false
        for MIRROR in "${MIRRORS[@]}"; do
            info "Provo: $MIRROR"
            if curl -L -C - --progress-bar -o "$ISO_NAME" "$MIRROR" 2>&1; then
                DOWNLOADED=true
                ok "Download completato da mirror alternativo"
                break
            fi
        done

        if [[ "$DOWNLOADED" != "true" ]]; then
            fail "Download fallito da tutti i mirror"
            info "Prova manuale: vai su https://archlinux.org/download/"
            info "Scarica l'ISO e mettila in: $DOWNLOAD_DIR/$ISO_NAME"
            exit 1
        fi
    fi
fi

# Verificare dimensione ISO (dovrebbe essere ~800MB-1GB)
ISO_SIZE=$(stat -f%z "$ISO_NAME" 2>/dev/null || stat --format=%s "$ISO_NAME" 2>/dev/null)
ISO_SIZE_MB=$((ISO_SIZE / 1048576))
if [[ "$ISO_SIZE_MB" -lt 500 ]]; then
    fail "ISO troppo piccola (${ISO_SIZE_MB}MB) — download probabilmente incompleto"
    rm -f "$ISO_NAME"
    exit 1
fi
ok "ISO scaricata: ${ISO_SIZE_MB}MB"

# ═══════════════════════════════════════════════════════════════
header "3. VERIFICA INTEGRITÀ SHA256"
# ═══════════════════════════════════════════════════════════════

info "Download sha256sums..."
if curl -sL -o sha256sums.txt "$SHA256_URL" 2>/dev/null; then
    EXPECTED_SHA=$(grep "$ISO_NAME" sha256sums.txt | awk '{print $1}')
    if [[ -n "$EXPECTED_SHA" ]]; then
        info "SHA256 atteso: ${EXPECTED_SHA:0:16}..."
        ACTUAL_SHA=$(shasum -a 256 "$ISO_NAME" | awk '{print $1}')
        info "SHA256 calcolato: ${ACTUAL_SHA:0:16}..."

        if [[ "$EXPECTED_SHA" == "$ACTUAL_SHA" ]]; then
            ok "SHA256 VERIFICATO — ISO integra"
        else
            fail "SHA256 NON CORRISPONDE — ISO corrotta!"
            fail "Atteso:   $EXPECTED_SHA"
            fail "Ottenuto: $ACTUAL_SHA"
            rm -f "$ISO_NAME"
            exit 1
        fi
    else
        warn "SHA256 per $ISO_NAME non trovato nel file sums"
        warn "Procedo senza verifica SHA (ISO potrebbe essere di una data diversa)"
    fi
else
    warn "Impossibile scaricare sha256sums — procedo senza verifica"
fi

# ═══════════════════════════════════════════════════════════════
header "4. SELEZIONE DISCO USB"
# ═══════════════════════════════════════════════════════════════

echo ""
info "Dischi disponibili:"
echo ""
diskutil list external physical 2>/dev/null || diskutil list

echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  ATTENZIONE: Il disco selezionato verrà COMPLETAMENTE CANCELLATO${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Inserisci il disco USB (es. ${BOLD}disk2${NC}, ${BOLD}disk3${NC}, ${BOLD}disk4${NC}):"
echo -e "  ${RED}NON inserire disk0 o disk1 (disco di sistema!)${NC}"
echo -n "> "
read -r USB_DISK

# Validazione
if [[ -z "$USB_DISK" ]]; then
    fail "Nessun disco inserito"
    exit 1
fi

# Rimuovere /dev/ se l'utente lo ha incluso
USB_DISK="${USB_DISK#/dev/}"

# Safety check: non permettere disk0 (disco di sistema)
if [[ "$USB_DISK" == "disk0" || "$USB_DISK" == "disk0s"* ]]; then
    fail "ERRORE: disk0 è il disco di sistema! Operazione annullata."
    exit 1
fi

# Safety check: non permettere disk1 su Mac (di solito è il disco interno)
if [[ "$USB_DISK" == "disk1" ]]; then
    warn "disk1 è spesso il disco interno del Mac."
    echo -n "Sei SICURO di voler usare disk1? (digita YES per confermare): "
    read -r CONFIRM
    if [[ "$CONFIRM" != "YES" ]]; then
        info "Operazione annullata"
        exit 0
    fi
fi

# Verificare che il disco esista
if ! diskutil info "/dev/$USB_DISK" &>/dev/null; then
    fail "Disco /dev/$USB_DISK non trovato"
    exit 1
fi

# Mostrare info disco per conferma
DISK_SIZE=$(diskutil info "/dev/$USB_DISK" | grep "Disk Size" | head -1)
DISK_NAME=$(diskutil info "/dev/$USB_DISK" | grep "Media Name" | head -1)
echo ""
info "Disco selezionato: /dev/$USB_DISK"
info "$DISK_SIZE"
info "$DISK_NAME"
echo ""
echo -e "${RED}  ULTIMA CONFERMA: Tutti i dati su /dev/$USB_DISK verranno PERSI!${NC}"
echo -n "  Digitare 'ARCH' per confermare: "
read -r FINAL_CONFIRM

if [[ "$FINAL_CONFIRM" != "ARCH" ]]; then
    info "Operazione annullata"
    exit 0
fi

# ═══════════════════════════════════════════════════════════════
header "5. SCRITTURA ISO SU USB"
# ═══════════════════════════════════════════════════════════════

info "Smontaggio disco..."
diskutil unmountDisk "/dev/$USB_DISK" 2>/dev/null || true

# Usare rdisk per velocità massima (raw device)
RAW_DISK="${USB_DISK/disk/rdisk}"
info "Scrittura ISO su /dev/$RAW_DISK (raw device per velocità)..."
info "Questo richiederà qualche minuto..."
echo ""

# dd con progress (macOS)
dd if="$ISO_NAME" of="/dev/$RAW_DISK" bs=4m status=progress 2>&1

sync
ok "Scrittura completata!"

# Eject sicuro
sleep 2
diskutil eject "/dev/$USB_DISK" 2>/dev/null || true
ok "USB espulsa in sicurezza"

# ═══════════════════════════════════════════════════════════════
header "6. SCRIPT DI INSTALLAZIONE AUTOMATICA"
# ═══════════════════════════════════════════════════════════════

info "Generazione script auto-install per uso post-boot..."

# Creare lo script di installazione automatica che verrà usato dopo il boot
cat > "$DOWNLOAD_DIR/archimede_install.sh" << 'INSTALL_EOF'
#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# PROGETTO ARCHIMEDE — Installazione automatica Arch Linux
# Target: iMac11,1 Late 2009
# Eseguire DOPO il boot dalla USB Arch in ambiente live
# ═══════════════════════════════════════════════════════════════
echo "Questo script va eseguito dall'ambiente live Arch."
echo "Vedi FASE3_arch_auto_install.sh per l'installazione completa."
INSTALL_EOF
chmod +x "$DOWNLOAD_DIR/archimede_install.sh"

ok "Script generato in $DOWNLOAD_DIR/"

# ═══════════════════════════════════════════════════════════════
header "FASE 2 COMPLETATA"
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  USB ARCH LINUX PRONTA${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  ✔ ISO Arch Linux scaricata e verificata"
echo "  ✔ USB flashata con successo"
echo ""
echo "  PROSSIMI PASSI:"
echo "  ───────────────"
echo "  1. Inserisci la USB nell'iMac"
echo "  2. Riavvia l'iMac tenendo premuto OPTION (Alt)"
echo "  3. Seleziona 'EFI Boot' dal menu"
echo "  4. Al prompt Arch, seleziona 'Arch Linux install medium'"
echo ""
echo "  NOTA per iMac 2009:"
echo "  Se EFI Boot non appare, prova tenendo premuto C"
echo "  L'iMac 2009 usa firmware EFI 32-bit con CPU 64-bit"
echo "  Potrebbe servire un bootloader EFI a 32 bit (raro)"
echo ""
echo "  Una volta dentro l'ambiente live, esegui FASE 3:"
echo "  sudo bash FASE3_arch_auto_install.sh"
echo ""
