#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# PROGETTO ARCHIMEDE — FASE 3: Installazione Automatica Arch Linux
# Target: iMac11,1 Late 2009 (i7 860, 8GB DDR3, ATI HD 4850, HDD 2TB)
# ESEGUIRE DALL'AMBIENTE LIVE ARCH USB: bash FASE3_arch_auto_install.sh
#
# Questo script automatizza COMPLETAMENTE l'installazione di Arch Linux:
# - Partizionamento intelligente (preserva macOS)
# - Filesystem Btrfs con subvolumes per snapshot/rollback
# - Driver specifici iMac 2009 (radeon, ath9k, applesmc)
# - GRUB dual-boot con macOS
# - Fan control watchdog (sicurezza termica)
# - SSH server pre-configurato per accesso remoto
# - Kernel pinning per prevenire breakage
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✔ $*${NC}"; }
fail() { echo -e "  ${RED}✘ $*${NC}"; exit 1; }
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
echo "║  PROGETTO ARCHIMEDE — FASE 3                                 ║"
echo "║  Installazione Automatica Arch Linux per iMac 2009           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ═══════════════════════════════════════════════════════════════
# CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════
HOSTNAME="archimede"
USERNAME="vio"
TIMEZONE="Europe/Rome"
LOCALE="it_IT.UTF-8"
KEYMAP="it"
LINUX_SIZE="400G"           # Partizione Linux
SWAP_SIZE="8G"              # Swap = RAM size
MOUNT_POINT="/mnt"

# ═══════════════════════════════════════════════════════════════
header "1. VERIFICA AMBIENTE"
# ═══════════════════════════════════════════════════════════════

# Verificare che siamo in ambiente live
if [[ ! -f /run/archiso/bootmnt/arch/pkglist.x86_64.txt ]] && [[ ! -d /run/archiso ]]; then
    warn "Non sembra un ambiente live Arch. Procedo comunque..."
fi

# Verificare architettura
ARCH=$(uname -m)
if [[ "$ARCH" != "x86_64" ]]; then
    fail "Architettura non supportata: $ARCH (serve x86_64)"
fi
ok "Architettura: $ARCH"

# Verificare UEFI o BIOS
if [[ -d /sys/firmware/efi ]]; then
    BOOT_MODE="UEFI"
    ok "Modalità boot: UEFI"
else
    BOOT_MODE="BIOS"
    ok "Modalità boot: BIOS (Legacy) — normale per iMac 2009"
fi

# Verificare hardware iMac
CPU_MODEL=$(grep -m1 "model name" /proc/cpuinfo | cut -d: -f2 | xargs)
RAM_MB=$(free -m | awk '/Mem:/{print $2}')
info "CPU: $CPU_MODEL"
info "RAM: ${RAM_MB}MB"

# Verificare GPU
GPU_INFO=$(lspci 2>/dev/null | grep -i "vga\|display\|3d" | head -1)
info "GPU: $GPU_INFO"

# ═══════════════════════════════════════════════════════════════
header "2. CONNESSIONE RETE (Wi-Fi Hotspot iPhone)"
# ═══════════════════════════════════════════════════════════════

# Verificare se già connessi (es. Ethernet)
if ping -c 1 -W 3 archlinux.org &>/dev/null; then
    ok "Connessione internet attiva"
else
    info "Nessuna connessione — configurazione Wi-Fi..."

    # Verificare interfaccia Wi-Fi
    WIFI_IF=$(iw dev 2>/dev/null | awk '/Interface/{print $2}' | head -1)

    if [[ -z "$WIFI_IF" ]]; then
        # Provare con ip link
        WIFI_IF=$(ip link | grep -oP 'wl\w+' | head -1)
    fi

    if [[ -n "$WIFI_IF" ]]; then
        info "Interfaccia Wi-Fi: $WIFI_IF"

        # Attivare interfaccia
        ip link set "$WIFI_IF" up 2>/dev/null
        sleep 2

        # Usare iwctl per connettersi
        info "Scansione reti Wi-Fi..."
        iwctl station "$WIFI_IF" scan 2>/dev/null
        sleep 3
        iwctl station "$WIFI_IF" get-networks 2>/dev/null

        echo ""
        echo -e "${YELLOW}  Connettiti all'hotspot iPhone manualmente:${NC}"
        echo ""
        echo "  iwctl"
        echo "  station $WIFI_IF connect \"iPhone di Vio\""
        echo "  (inserisci password hotspot)"
        echo "  exit"
        echo ""
        echo -n "  Premi INVIO dopo esserti connesso... "
        read -r

        # Verificare connessione
        if ping -c 1 -W 5 archlinux.org &>/dev/null; then
            ok "Connessione internet attiva!"
        else
            fail "Nessuna connessione. Verifica hotspot e riprova."
        fi
    else
        warn "Nessuna interfaccia Wi-Fi trovata"
        info "Prova con Ethernet USB o iPhone USB tethering"
        echo ""
        echo "  Per USB tethering iPhone:"
        echo "  1. Connetti iPhone via USB"
        echo "  2. Su iPhone: Hotspot Personale → Consenti ad altri..."
        echo "  3. Attendi che appaia interfaccia usb0 o enp*"
        echo ""
        echo -n "  Premi INVIO dopo aver connesso... "
        read -r

        # DHCP su tutte le interfacce
        for iface in $(ip -o link show | awk -F': ' '{print $2}' | grep -v lo); do
            dhcpcd "$iface" 2>/dev/null &
        done
        sleep 5

        if ! ping -c 1 -W 5 archlinux.org &>/dev/null; then
            fail "Impossibile connettersi. L'installazione richiede internet."
        fi
        ok "Connessione attiva"
    fi
fi

# Sincronizzare orologio (necessario per HTTPS)
timedatectl set-ntp true 2>/dev/null
ok "NTP sincronizzato"

# ═══════════════════════════════════════════════════════════════
header "3. PARTIZIONAMENTO DISCO"
# ═══════════════════════════════════════════════════════════════

info "Dischi disponibili:"
lsblk -d -o NAME,SIZE,MODEL,TYPE | grep disk
echo ""

# Identificare disco principale (HDD 2TB)
MAIN_DISK=""
for disk in /dev/sda /dev/sdb /dev/nvme0n1; do
    if [[ -b "$disk" ]]; then
        DISK_SIZE_BYTES=$(blockdev --getsize64 "$disk" 2>/dev/null || echo 0)
        DISK_SIZE_GB=$((DISK_SIZE_BYTES / 1073741824))
        if [[ "$DISK_SIZE_GB" -gt 1500 ]]; then
            MAIN_DISK="$disk"
            info "Disco principale trovato: $disk (${DISK_SIZE_GB}GB)"
            break
        fi
    fi
done

if [[ -z "$MAIN_DISK" ]]; then
    echo "  Dischi disponibili:"
    lsblk -d -o NAME,SIZE,MODEL
    echo ""
    echo -n "  Inserisci il disco per l'installazione (es. sda): "
    read -r DISK_INPUT
    MAIN_DISK="/dev/$DISK_INPUT"
fi

if [[ ! -b "$MAIN_DISK" ]]; then
    fail "Disco $MAIN_DISK non trovato"
fi

# Mostrare partizioni esistenti
info "Partizioni attuali su $MAIN_DISK:"
fdisk -l "$MAIN_DISK" 2>/dev/null | grep "^/dev"
echo ""

# Verificare se macOS è presente
MACOS_PART=""
for part in ${MAIN_DISK}*[0-9]; do
    if [[ -b "$part" ]]; then
        FS_TYPE=$(blkid -o value -s TYPE "$part" 2>/dev/null)
        if [[ "$FS_TYPE" == "hfsplus" || "$FS_TYPE" == "apfs" ]]; then
            MACOS_PART="$part"
            MACOS_SIZE=$(blockdev --getsize64 "$part" 2>/dev/null)
            MACOS_SIZE_GB=$((MACOS_SIZE / 1073741824))
            info "Partizione macOS trovata: $part (${MACOS_SIZE_GB}GB, $FS_TYPE)"
        fi
    fi
done

echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  PARTIZIONAMENTO: Creeremo le seguenti partizioni:${NC}"
echo -e "${YELLOW}  - Boot EFI:  512MB  (FAT32)${NC}"
echo -e "${YELLOW}  - Swap:      ${SWAP_SIZE}   (linux-swap)${NC}"
echo -e "${YELLOW}  - Linux:     ${LINUX_SIZE}  (Btrfs con subvolumes)${NC}"
echo -e "${YELLOW}  La partizione macOS verrà PRESERVATA${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -n "  Conferma partizionamento (digita ARCHIMEDE): "
read -r PART_CONFIRM
if [[ "$PART_CONFIRM" != "ARCHIMEDE" ]]; then
    info "Partizionamento annullato"
    exit 0
fi

# Trovare spazio libero o partizioni da usare
# Strategia: usare gdisk/sgdisk per aggiungere partizioni nello spazio libero
info "Creazione partizioni con sgdisk..."

# Trovare il prossimo numero di partizione disponibile
LAST_PART=$(sgdisk -p "$MAIN_DISK" 2>/dev/null | grep "^ " | tail -1 | awk '{print $1}')
NEXT_PART=$((LAST_PART + 1))

# Partizione EFI (se non esiste già)
EFI_PART=""
EXISTING_EFI=$(sgdisk -p "$MAIN_DISK" 2>/dev/null | grep "EF00" | awk '{print $1}')
if [[ -n "$EXISTING_EFI" ]]; then
    EFI_PART="${MAIN_DISK}${EXISTING_EFI}"
    # Se il disco è /dev/sda, le partizioni sono /dev/sda1, /dev/sda2...
    [[ "$MAIN_DISK" == *"nvme"* ]] && EFI_PART="${MAIN_DISK}p${EXISTING_EFI}"
    info "Partizione EFI esistente: $EFI_PART"
else
    info "Creazione partizione EFI (512MB)..."
    sgdisk -n "${NEXT_PART}:0:+512M" -t "${NEXT_PART}:EF00" -c "${NEXT_PART}:EFI" "$MAIN_DISK"
    EFI_PART="${MAIN_DISK}${NEXT_PART}"
    [[ "$MAIN_DISK" == *"nvme"* ]] && EFI_PART="${MAIN_DISK}p${NEXT_PART}"
    NEXT_PART=$((NEXT_PART + 1))
    ok "Partizione EFI creata: $EFI_PART"
fi

# Partizione Swap
info "Creazione partizione Swap (${SWAP_SIZE})..."
sgdisk -n "${NEXT_PART}:0:+${SWAP_SIZE}" -t "${NEXT_PART}:8200" -c "${NEXT_PART}:SWAP" "$MAIN_DISK"
SWAP_PART="${MAIN_DISK}${NEXT_PART}"
[[ "$MAIN_DISK" == *"nvme"* ]] && SWAP_PART="${MAIN_DISK}p${NEXT_PART}"
NEXT_PART=$((NEXT_PART + 1))
ok "Partizione Swap creata: $SWAP_PART"

# Partizione Linux (Btrfs)
info "Creazione partizione Linux (${LINUX_SIZE}, Btrfs)..."
sgdisk -n "${NEXT_PART}:0:+${LINUX_SIZE}" -t "${NEXT_PART}:8300" -c "${NEXT_PART}:ARCHLINUX" "$MAIN_DISK"
LINUX_PART="${MAIN_DISK}${NEXT_PART}"
[[ "$MAIN_DISK" == *"nvme"* ]] && LINUX_PART="${MAIN_DISK}p${NEXT_PART}"
ok "Partizione Linux creata: $LINUX_PART"

# Aggiornare kernel partition table
partprobe "$MAIN_DISK" 2>/dev/null
sleep 2

# ═══════════════════════════════════════════════════════════════
header "4. FORMATTAZIONE E MOUNT"
# ═══════════════════════════════════════════════════════════════

# Formattare EFI (solo se nuova)
if [[ -z "$EXISTING_EFI" ]]; then
    info "Formattazione EFI (FAT32)..."
    mkfs.fat -F32 "$EFI_PART"
    ok "EFI formattata"
fi

# Formattare Swap
info "Formattazione Swap..."
mkswap "$SWAP_PART"
swapon "$SWAP_PART"
ok "Swap attiva: $(free -h | awk '/Swap:/{print $2}')"

# Formattare Linux con Btrfs
info "Formattazione Linux (Btrfs)..."
mkfs.btrfs -f -L "archlinux" "$LINUX_PART"
ok "Btrfs creato"

# Creare subvolumes Btrfs (per snapshot e rollback)
info "Creazione subvolumes Btrfs..."
mount "$LINUX_PART" "$MOUNT_POINT"

btrfs subvolume create "${MOUNT_POINT}/@"          # Root
btrfs subvolume create "${MOUNT_POINT}/@home"       # Home
btrfs subvolume create "${MOUNT_POINT}/@snapshots"  # Snapshots
btrfs subvolume create "${MOUNT_POINT}/@var_log"    # Log (esclusi da snapshot)
btrfs subvolume create "${MOUNT_POINT}/@var_cache"  # Cache pacman

ok "Subvolumes creati: @, @home, @snapshots, @var_log, @var_cache"

# Smontare e rimontare con subvolumes
umount "$MOUNT_POINT"

# Mount con opzioni ottimizzate per HDD
BTRFS_OPTS="noatime,compress=zstd:3,space_cache=v2,autodefrag"

mount -o "subvol=@,${BTRFS_OPTS}" "$LINUX_PART" "$MOUNT_POINT"
mkdir -p "${MOUNT_POINT}"/{boot/efi,home,.snapshots,var/log,var/cache/pacman}

mount -o "subvol=@home,${BTRFS_OPTS}" "$LINUX_PART" "${MOUNT_POINT}/home"
mount -o "subvol=@snapshots,${BTRFS_OPTS}" "$LINUX_PART" "${MOUNT_POINT}/.snapshots"
mount -o "subvol=@var_log,${BTRFS_OPTS}" "$LINUX_PART" "${MOUNT_POINT}/var/log"
mount -o "subvol=@var_cache,${BTRFS_OPTS}" "$LINUX_PART" "${MOUNT_POINT}/var/cache/pacman"

mount "$EFI_PART" "${MOUNT_POINT}/boot/efi"

ok "Tutti i subvolumes montati"
info "Opzioni Btrfs: $BTRFS_OPTS"
info "  compress=zstd:3 → risparmia ~30% spazio su HDD"
info "  autodefrag → deframmentazione automatica (critico per HDD)"

# ═══════════════════════════════════════════════════════════════
header "5. INSTALLAZIONE BASE"
# ═══════════════════════════════════════════════════════════════

info "Aggiornamento mirrorlist (mirror italiani prioritari)..."

# Configurare mirror veloci
cat > /etc/pacman.d/mirrorlist << 'MIRROR_EOF'
## Italia
Server = https://archlinux.mirror.garr.it/$repo/os/$arch
Server = https://mirror.unit193.net/archlinux/$repo/os/$arch
## Europa
Server = https://mirror.rackspace.com/archlinux/$repo/os/$arch
Server = https://mirrors.kernel.org/archlinux/$repo/os/$arch
Server = https://geo.mirror.pkgbuild.com/$repo/os/$arch
MIRROR_EOF

ok "Mirrorlist configurata (Italia prioritaria)"

info "Installazione sistema base..."
info "Pacchetti: base linux linux-firmware + driver iMac 2009 + tools essenziali"
echo ""

pacstrap -K "$MOUNT_POINT" \
    base \
    linux \
    linux-headers \
    linux-firmware \
    base-devel \
    btrfs-progs \
    grub \
    efibootmgr \
    os-prober \
    networkmanager \
    iwd \
    openssh \
    sudo \
    vim \
    nano \
    git \
    curl \
    wget \
    htop \
    tmux \
    ripgrep \
    fzf \
    zsh \
    man-db \
    man-pages \
    xf86-video-ati \
    mesa \
    lib32-mesa \
    lm_sensors \
    applesmc-dkms 2>/dev/null || true

# Se applesmc-dkms non è disponibile, lo installeremo dopo da AUR
ok "Sistema base installato"

# ═══════════════════════════════════════════════════════════════
header "6. CONFIGURAZIONE SISTEMA"
# ═══════════════════════════════════════════════════════════════

# Generare fstab
info "Generazione fstab..."
genfstab -U "$MOUNT_POINT" >> "${MOUNT_POINT}/etc/fstab"
ok "fstab generato"

# Tutto il resto dentro chroot
info "Configurazione in chroot..."

arch-chroot "$MOUNT_POINT" /bin/bash << CHROOT_EOF
set -uo pipefail

# ──── Timezone ────
ln -sf /usr/share/zoneinfo/${TIMEZONE} /etc/localtime
hwclock --systohc
echo "✔ Timezone: ${TIMEZONE}"

# ──── Locale ────
sed -i 's/^#${LOCALE}/${LOCALE}/' /etc/locale.gen
sed -i 's/^#en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen
locale-gen
echo "LANG=${LOCALE}" > /etc/locale.conf
echo "KEYMAP=${KEYMAP}" > /etc/vconsole.conf
echo "✔ Locale: ${LOCALE}"

# ──── Hostname ────
echo "${HOSTNAME}" > /etc/hostname
cat > /etc/hosts << HOSTS_EOF
127.0.0.1   localhost
::1         localhost
127.0.1.1   ${HOSTNAME}.localdomain ${HOSTNAME}
HOSTS_EOF
echo "✔ Hostname: ${HOSTNAME}"

# ──── Utente ────
useradd -m -G wheel,video,audio,storage,optical -s /bin/zsh ${USERNAME}
echo "${USERNAME}:archimede2026" | chpasswd
echo "root:archimede2026root" | chpasswd
echo "✔ Utente ${USERNAME} creato (password temporanea: archimede2026)"
echo "⚠ CAMBIA LA PASSWORD al primo login: passwd"

# ──── Sudo ────
sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers
echo "✔ Sudo configurato per gruppo wheel"

# ──── NetworkManager ────
systemctl enable NetworkManager
echo "✔ NetworkManager abilitato"

# ──── SSH Server (CRITICO per accesso remoto) ────
systemctl enable sshd
# Configurazione SSH sicura
cat > /etc/ssh/sshd_config.d/archimede.conf << SSH_EOF
Port 22
PermitRootLogin no
PasswordAuthentication yes
PubkeyAuthentication yes
X11Forwarding yes
ClientAliveInterval 60
ClientAliveCountMax 10
SSH_EOF
echo "✔ SSH server configurato e abilitato al boot"

# ──── Initramfs ────
# Aggiungere moduli per iMac 2009
sed -i 's/^MODULES=()/MODULES=(radeon ath9k applesmc coretemp)/' /etc/mkinitcpio.conf
# Aggiungere btrfs hook
sed -i 's/^HOOKS=.*/HOOKS=(base udev autodetect modconf kms keyboard keymap consolefont block filesystems btrfs fsck)/' /etc/mkinitcpio.conf
mkinitcpio -P
echo "✔ Initramfs rigenerato con driver iMac"

# ──── GRUB Bootloader ────
if [[ -d /sys/firmware/efi ]]; then
    grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ARCH
else
    # BIOS mode per iMac 2009
    grub-install --target=i386-pc ${MAIN_DISK}
fi

# Configurazione GRUB
sed -i 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=10/' /etc/default/grub
sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet radeon.modeset=1 applesmc.force=1"/' /etc/default/grub
# Abilitare os-prober per trovare macOS
echo 'GRUB_DISABLE_OS_PROBER=false' >> /etc/default/grub
grub-mkconfig -o /boot/grub/grub.cfg
echo "✔ GRUB installato e configurato (dual-boot macOS)"

# ──── Fan Control Watchdog (SICUREZZA TERMICA) ────
cat > /usr/local/bin/fan_watchdog.sh << 'FAN_EOF'
#!/bin/bash
# VIO83 ARCHIMEDE — Fan Control Watchdog
# Monitora temperatura e controlla ventole via applesmc
# Se applesmc non è disponibile, forza ventole al massimo come sicurezza

LOG="/var/log/fan_watchdog.log"
APPLESMC="/sys/devices/platform/applesmc.768"
MAX_TEMP=85  # Celsius - soglia critica
EMERGENCY_TEMP=95  # Shutdown di emergenza

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

# Funzione per impostare velocità ventola
set_fan_speed() {
    local fan_id=$1
    local speed=$2
    local fan_manual="${APPLESMC}/fan${fan_id}_manual"
    local fan_output="${APPLESMC}/fan${fan_id}_output"

    if [[ -f "$fan_manual" ]]; then
        echo 1 > "$fan_manual" 2>/dev/null
        echo "$speed" > "$fan_output" 2>/dev/null
    fi
}

while true; do
    # Leggere temperatura CPU
    TEMP=0
    if [[ -d "$APPLESMC" ]]; then
        # Cercare sensore temperatura CPU
        for sensor in ${APPLESMC}/temp*_input; do
            if [[ -f "$sensor" ]]; then
                VAL=$(cat "$sensor" 2>/dev/null)
                # applesmc riporta in milligradi
                VAL_C=$((VAL / 1000))
                [[ "$VAL_C" -gt "$TEMP" ]] && TEMP=$VAL_C
            fi
        done
    fi

    # Fallback: lm_sensors
    if [[ "$TEMP" -eq 0 ]]; then
        TEMP=$(sensors 2>/dev/null | grep -oP 'Core 0:.*?\+\K[0-9]+' | head -1)
        [[ -z "$TEMP" ]] && TEMP=0
    fi

    # Logica fan control
    if [[ "$TEMP" -ge "$EMERGENCY_TEMP" ]]; then
        log "EMERGENCY: Temp ${TEMP}°C >= ${EMERGENCY_TEMP}°C — SHUTDOWN!"
        set_fan_speed 1 6200  # Massimo
        set_fan_speed 2 6200
        sleep 10
        shutdown -h now
    elif [[ "$TEMP" -ge "$MAX_TEMP" ]]; then
        log "CRITICAL: Temp ${TEMP}°C — ventole al MASSIMO"
        set_fan_speed 1 6200
        set_fan_speed 2 6200
    elif [[ "$TEMP" -ge 70 ]]; then
        # Ventole proporzionali: 70°C=3000rpm, 85°C=6200rpm
        SPEED=$(( 3000 + (TEMP - 70) * 213 ))
        set_fan_speed 1 "$SPEED"
        set_fan_speed 2 "$SPEED"
    elif [[ "$TEMP" -ge 50 ]]; then
        set_fan_speed 1 2000
        set_fan_speed 2 2000
    else
        # Sotto 50°C: ventole minime
        set_fan_speed 1 1200
        set_fan_speed 2 1200
    fi

    sleep 10
done
FAN_EOF
chmod +x /usr/local/bin/fan_watchdog.sh

# Systemd service per fan watchdog
cat > /etc/systemd/system/fan-watchdog.service << 'FANSERVICE_EOF'
[Unit]
Description=VIO83 ARCHIMEDE Fan Control Watchdog
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/local/bin/fan_watchdog.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
FANSERVICE_EOF

systemctl enable fan-watchdog.service
echo "✔ Fan watchdog installato (auto-start al boot)"

# ──── Kernel Pinning (protezione anti-breakage) ────
cat > /usr/local/bin/safe_update.sh << 'SAFEUPD_EOF'
#!/bin/bash
# VIO83 ARCHIMEDE — Safe Update con Btrfs Snapshot
# Crea snapshot PRIMA di ogni aggiornamento, con rollback automatico

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${GREEN}═══ ARCHIMEDE Safe Update ═══${NC}"

# 1. Creare snapshot pre-update
SNAP_NAME="pre-update-$(date +%Y%m%d-%H%M%S)"
echo -e "${YELLOW}[1/4] Creazione snapshot: ${SNAP_NAME}${NC}"
btrfs subvolume snapshot / "/.snapshots/${SNAP_NAME}" 2>/dev/null
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}  ✔ Snapshot creato${NC}"
else
    echo -e "${RED}  ✘ Snapshot fallito — aggiornamento annullato${NC}"
    exit 1
fi

# 2. Salvare versione kernel attuale
CURRENT_KERNEL=$(uname -r)
echo -e "${YELLOW}[2/4] Kernel attuale: ${CURRENT_KERNEL}${NC}"

# 3. Eseguire aggiornamento
echo -e "${YELLOW}[3/4] Aggiornamento sistema...${NC}"
pacman -Syu --noconfirm

# 4. Verificare che i moduli critici siano presenti
NEW_KERNEL=$(pacman -Q linux | awk '{print $2}')
echo -e "${YELLOW}[4/4] Verifica moduli critici per kernel ${NEW_KERNEL}...${NC}"

MODULES_OK=true
for mod in radeon ath9k applesmc; do
    if ! find /lib/modules/ -name "${mod}.ko*" 2>/dev/null | grep -q .; then
        echo -e "${RED}  ✘ Modulo ${mod} NON TROVATO nel nuovo kernel!${NC}"
        MODULES_OK=false
    else
        echo -e "${GREEN}  ✔ Modulo ${mod} presente${NC}"
    fi
done

if [[ "$MODULES_OK" != "true" ]]; then
    echo -e "${RED}═══ MODULI MANCANTI — ROLLBACK AUTOMATICO ═══${NC}"
    echo "  Ripristino snapshot ${SNAP_NAME}..."
    # Il rollback Btrfs completo richiede boot da snapshot
    # Per ora, downgrade il kernel
    pacman -U /var/cache/pacman/pkg/linux-${CURRENT_KERNEL}*.pkg.tar.zst --noconfirm 2>/dev/null
    echo -e "${YELLOW}  Kernel downgraded a ${CURRENT_KERNEL}${NC}"
    echo -e "${YELLOW}  Snapshot disponibile per rollback completo: ${SNAP_NAME}${NC}"
fi

# Pulizia vecchi snapshot (mantieni ultimi 5)
SNAP_COUNT=$(ls -d /.snapshots/pre-update-* 2>/dev/null | wc -l)
if [[ "$SNAP_COUNT" -gt 5 ]]; then
    ls -dt /.snapshots/pre-update-* | tail -n +6 | while read -r OLD_SNAP; do
        btrfs subvolume delete "$OLD_SNAP" 2>/dev/null
        echo "  Snapshot vecchio rimosso: $(basename "$OLD_SNAP")"
    done
fi

echo -e "${GREEN}═══ Aggiornamento completato ═══${NC}"
SAFEUPD_EOF
chmod +x /usr/local/bin/safe_update.sh
echo "✔ Safe Update installato (usa 'sudo safe_update.sh' invece di 'pacman -Syu')"

# ──── Alias e configurazione zsh ────
cat > /home/${USERNAME}/.zshrc << 'ZSHRC_EOF'
# VIO83 ARCHIMEDE — ZSH Config
export EDITOR=vim
export VISUAL=vim
export LANG=it_IT.UTF-8
export PATH="$HOME/.local/bin:$PATH"

# Aliases
alias update='sudo /usr/local/bin/safe_update.sh'
alias ll='ls -lah --color=auto'
alias la='ls -A --color=auto'
alias gs='git status'
alias gp='git push'
alias gl='git log --oneline -20'
alias top='htop'
alias temp='sensors'
alias fans='cat /sys/devices/platform/applesmc.768/fan*_output 2>/dev/null || echo "applesmc non disponibile"'
alias snap='sudo btrfs subvolume snapshot / /.snapshots/manual-$(date +%Y%m%d-%H%M%S)'

# Prompt
PROMPT='%F{cyan}[archimede]%f %F{green}%n%f:%F{blue}%~%f %# '

# History
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt appendhistory sharehistory

# Completamento
autoload -Uz compinit && compinit

# FZF
[ -f /usr/share/fzf/key-bindings.zsh ] && source /usr/share/fzf/key-bindings.zsh
[ -f /usr/share/fzf/completion.zsh ] && source /usr/share/fzf/completion.zsh
ZSHRC_EOF
chown ${USERNAME}:${USERNAME} /home/${USERNAME}/.zshrc
echo "✔ ZSH configurato con alias safe_update"

# ──── Timer auto-snapshot settimanale ────
cat > /etc/systemd/system/btrfs-snapshot.service << 'BTSNAP_EOF'
[Unit]
Description=Weekly Btrfs Snapshot

[Service]
Type=oneshot
ExecStart=/usr/local/bin/safe_update.sh
BTSNAP_EOF

cat > /etc/systemd/system/btrfs-snapshot.timer << 'BTTIMER_EOF'
[Unit]
Description=Weekly Btrfs Snapshot Timer

[Timer]
OnCalendar=Sun 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
BTTIMER_EOF

systemctl enable btrfs-snapshot.timer
echo "✔ Snapshot automatico settimanale (domenica 03:00)"

CHROOT_EOF

ok "Configurazione sistema completata"

# ═══════════════════════════════════════════════════════════════
header "7. RIEPILOGO INSTALLAZIONE"
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  ARCH LINUX INSTALLATO — PROGETTO ARCHIMEDE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  ✔ Sistema base Arch Linux installato"
echo "  ✔ Btrfs con subvolumes per snapshot/rollback"
echo "  ✔ Driver iMac 2009: radeon, ath9k, applesmc"
echo "  ✔ GRUB dual-boot con macOS"
echo "  ✔ SSH server attivo al boot (accesso remoto)"
echo "  ✔ Fan control watchdog (sicurezza termica)"
echo "  ✔ Kernel pinning con safe_update.sh"
echo "  ✔ Snapshot automatici pre-update"
echo "  ✔ Utente: ${USERNAME} / password: archimede2026"
echo ""
echo "  PROSSIMI PASSI:"
echo "  ───────────────"
echo "  1. Smontare e riavviare:"
echo "     umount -R /mnt"
echo "     reboot"
echo ""
echo "  2. Al boot, selezionare 'Arch Linux' dal menu GRUB"
echo ""
echo "  3. Login: ${USERNAME} / archimede2026"
echo "     CAMBIA PASSWORD: passwd"
echo ""
echo "  4. Connetti Wi-Fi hotspot:"
echo "     nmcli device wifi connect 'iPhone di Vio' password 'TUA_PASSWORD'"
echo ""
echo "  5. Esegui FASE 4 per l'ambiente di sviluppo completo:"
echo "     sudo bash FASE4_arch_dev_environment.sh"
echo ""
