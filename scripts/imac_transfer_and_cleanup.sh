#!/bin/bash
# === Trasferimento Downloads → iMac Archimede + Pulizia Mac Air ===
# Eseguire quando l'iMac è raggiungibile via LAN (172.20.10.5)
# REGOLA: NON modifica NULLA di esistente su iMac, SOLO aggiunge file.
# Autore: VIO83 — $(date -I)

set -euo pipefail

IMAC_USER="vio"
IMAC_LAN="172.20.10.5"
IMAC_KEY="$HOME/.ssh/id_ed25519_archimede"
REMOTE_DIR="mac-archive/downloads"
LOG="$HOME/imac_transfer.log"

SSH_OPTS=(
    -o "IdentityFile=$IMAC_KEY"
    -o ConnectTimeout=15
    -o ServerAliveInterval=10
    -o ServerAliveCountMax=3
    -o BatchMode=yes
)

echo "=== Trasferimento avviato $(date) ===" | tee "$LOG"

# 1. Verifica raggiungibilità
echo "[CHECK] Ping iMac..." | tee -a "$LOG"
if ! ping -c 2 -W 5 "$IMAC_LAN" > /dev/null 2>&1; then
    echo "[ERRORE] iMac non raggiungibile su $IMAC_LAN. Riprova più tardi." | tee -a "$LOG"
    exit 1
fi

echo "[CHECK] SSH iMac..." | tee -a "$LOG"
if ! ssh "${SSH_OPTS[@]}" "$IMAC_USER@$IMAC_LAN" 'echo SSH_OK' 2>/dev/null; then
    echo "[ERRORE] SSH non funziona. Controlla sshd su iMac." | tee -a "$LOG"
    exit 1
fi

# 2. Assicura directory remota
ssh "${SSH_OPTS[@]}" "$IMAC_USER@$IMAC_LAN" "mkdir -p ~/$REMOTE_DIR" 2>/dev/null

# 3. Trasferisci file grossi uno alla volta (con verifica dimensione)
FILES=(
    "$HOME/Downloads/kali-bootable.dmg"
    "$HOME/Downloads/kali-linux-2026.1-live-amd64.iso"
    "$HOME/Downloads/archlinux.iso"
    "$HOME/Downloads/lexroom-app"
    "$HOME/Downloads/ai-assistant-2026"
    "$HOME/Downloads/datasets"
)

for f in "${FILES[@]}"; do
    if [[ -e "$f" ]]; then
        LOCAL_SIZE=$(du -sk "$f" 2>/dev/null | awk '{print $1}')
        BASENAME=$(basename "$f")
        echo "[TRASF] $BASENAME ($LOCAL_SIZE KB)..." | tee -a "$LOG"
        
        if scp -r "${SSH_OPTS[@]}" "$f" "$IMAC_USER@$IMAC_LAN:~/$REMOTE_DIR/" >> "$LOG" 2>&1; then
            # Verifica dimensione remota
            REMOTE_SIZE=$(ssh "${SSH_OPTS[@]}" "$IMAC_USER@$IMAC_LAN" "du -sk ~/'$REMOTE_DIR/$BASENAME' 2>/dev/null | awk '{print \$1}'" 2>/dev/null || echo "0")
            if [[ "$REMOTE_SIZE" -ge "$LOCAL_SIZE" ]]; then
                echo "[OK] $BASENAME trasferito e verificato ($REMOTE_SIZE KB)" | tee -a "$LOG"
            else
                echo "[WARN] $BASENAME dimensione non corrisponde (locale=$LOCAL_SIZE remoto=$REMOTE_SIZE)" | tee -a "$LOG"
            fi
        else
            echo "[ERRORE] Trasferimento fallito per $BASENAME" | tee -a "$LOG"
        fi
    fi
done

# 4. Trasferisci foto/screenshot/PDF
echo "[TRASF] Foto, screenshot, PDF..." | tee -a "$LOG"
for ext in jpeg png PNG pdf; do
    for f in "$HOME/Downloads/"*."$ext"; do
        if [[ -e "$f" ]]; then
            scp "${SSH_OPTS[@]}" "$f" "$IMAC_USER@$IMAC_LAN:~/$REMOTE_DIR/" >> "$LOG" 2>&1
        fi
    done
done
echo "[OK] Media files trasferiti" | tee -a "$LOG"

# 5. Riepilogo remoto
echo "[VERIFICA] Contenuto remoto:" | tee -a "$LOG"
ssh "${SSH_OPTS[@]}" "$IMAC_USER@$IMAC_LAN" "ls -lhS ~/$REMOTE_DIR/" 2>/dev/null | tee -a "$LOG"
REMOTE_TOTAL=$(ssh "${SSH_OPTS[@]}" "$IMAC_USER@$IMAC_LAN" "du -sh ~/$REMOTE_DIR/ 2>/dev/null | awk '{print \$1}'" 2>/dev/null || echo "?")
echo "[TOTALE REMOTO] $REMOTE_TOTAL" | tee -a "$LOG"

echo ""
echo "=== Trasferimento completato $(date) ===" | tee -a "$LOG"
echo ""
echo "Per cancellare i file da Mac Air (dopo verifica manuale):"
echo "  rm -r ~/Downloads/kali-bootable.dmg ~/Downloads/kali-linux-2026.1-live-amd64.iso ~/Downloads/archlinux.iso"
echo "  rm -r ~/Downloads/lexroom-app ~/Downloads/ai-assistant-2026 ~/Downloads/datasets"
echo "  rm ~/Downloads/*.jpeg ~/Downloads/*.png ~/Downloads/*.PNG ~/Downloads/*.pdf"
echo ""
echo "Spazio stimato recuperabile: ~12.5 GB"
