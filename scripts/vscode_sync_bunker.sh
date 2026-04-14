#!/bin/bash
# === VS Code Session Sync — BUNKER MODE ===
# Sincronizza sessioni VS Code tra Mac Air e iMac Arch Linux
# Trasporto: SSH diretto (LAN) con fallback Tailscale
# Zero terze parti, zero metadata leak, cifratura Ed25519 end-to-end
# Autore: VIO83 — 2026-04-14

set -euo pipefail

# ─── Configurazione ──────────────────────────────────────────
IMAC_USER="vio"
IMAC_LAN="172.20.10.5"
IMAC_TS="100.116.120.3"
IMAC_KEY="$HOME/.ssh/id_ed25519_archimede"
LOG="$HOME/.vio83/vscode_sync.log"

# Percorsi VS Code locali (macOS)
LOCAL_VSCODE="$HOME/Library/Application Support/Code/User"
# Percorsi VS Code remoti (Arch Linux)
REMOTE_VSCODE=".config/Code/User"

mkdir -p "$HOME/.vio83"

# ─── SSH options hardened ────────────────────────────────────
SSH_OPTS=(
    -o "IdentityFile=$IMAC_KEY"
    -o "ConnectTimeout=10"
    -o "ServerAliveInterval=15"
    -o "ServerAliveCountMax=3"
    -o "BatchMode=yes"
    -o "StrictHostKeyChecking=accept-new"
    -o "PasswordAuthentication=no"
    -o "PubkeyAuthentication=yes"
    -o "ControlMaster=auto"
    -o "ControlPath=$HOME/.ssh/control-imac-%C"
    -o "ControlPersist=300"
)

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

# ─── 1. Selezione host (LAN prioritario, Tailscale fallback) ─
pick_host() {
    if ping -c 1 -W 2 "$IMAC_LAN" >/dev/null 2>&1; then
        echo "$IMAC_LAN"
        return 0
    fi
    if ping -c 1 -W 2 "$IMAC_TS" >/dev/null 2>&1; then
        echo "$IMAC_TS"
        return 0
    fi
    return 1
}

log "=== VS Code Sync Bunker — avvio ==="

if ! HOST=$(pick_host); then
    log "[ERRORE] iMac non raggiungibile (LAN né Tailscale). Abort."
    exit 1
fi

TRANSPORT="LAN"
[[ "$HOST" == "$IMAC_TS" ]] && TRANSPORT="Tailscale"
log "[OK] iMac raggiungibile via $TRANSPORT ($HOST)"

# ─── 2. Verifica SSH ─────────────────────────────────────────
if ! ssh "${SSH_OPTS[@]}" "$IMAC_USER@$HOST" 'echo SSH_OK' >/dev/null 2>&1; then
    log "[ERRORE] SSH non risponde su $HOST. Verifica sshd e chiave."
    exit 2
fi
log "[OK] SSH connesso"

# ─── 3. Verifica key (non procedere senza la key corretta) ───
if [[ ! -f "$IMAC_KEY" ]]; then
    log "[ERRORE] Chiave SSH non trovata: $IMAC_KEY"
    exit 3
fi

# ─── 4. Prepara directory remota ─────────────────────────────
ssh "${SSH_OPTS[@]}" "$IMAC_USER@$HOST" "mkdir -p ~/$REMOTE_VSCODE/snippets"
log "[OK] Directory VS Code remota pronta"

# ─── 5. Sync settings.json ───────────────────────────────────
if [[ -f "$LOCAL_VSCODE/settings.json" ]]; then
    rsync -az -e "ssh ${SSH_OPTS[*]}" \
        "$LOCAL_VSCODE/settings.json" \
        "$IMAC_USER@$HOST:~/$REMOTE_VSCODE/settings.json"
    log "[SYNC] settings.json"
else
    log "[SKIP] settings.json non trovato localmente"
fi

# ─── 6. Sync keybindings.json ────────────────────────────────
if [[ -f "$LOCAL_VSCODE/keybindings.json" ]]; then
    rsync -az -e "ssh ${SSH_OPTS[*]}" \
        "$LOCAL_VSCODE/keybindings.json" \
        "$IMAC_USER@$HOST:~/$REMOTE_VSCODE/keybindings.json"
    log "[SYNC] keybindings.json"
fi

# ─── 7. Sync snippets ────────────────────────────────────────
if [[ -d "$LOCAL_VSCODE/snippets" ]]; then
    rsync -az --delete -e "ssh ${SSH_OPTS[*]}" \
        "$LOCAL_VSCODE/snippets/" \
        "$IMAC_USER@$HOST:~/$REMOTE_VSCODE/snippets/"
    log "[SYNC] snippets/"
fi

# ─── 8. Sync estensioni (lista → install remoto) ─────────────
log "[SYNC] Estensioni VS Code..."
EXT_LIST=$(code --list-extensions 2>/dev/null || true)

if [[ -n "$EXT_LIST" ]]; then
    # Salva lista locale per riferimento
    echo "$EXT_LIST" > "$HOME/.vio83/vscode_extensions_macair.txt"

    # Ottieni lista estensioni su iMac (se code è installato)
    REMOTE_EXT=$(ssh "${SSH_OPTS[@]}" "$IMAC_USER@$HOST" \
        'command -v code >/dev/null 2>&1 && code --list-extensions 2>/dev/null || true')

    INSTALLED=0
    SKIPPED=0
    while IFS= read -r ext; do
        [[ -z "$ext" ]] && continue
        if echo "$REMOTE_EXT" | grep -qxF "$ext"; then
            ((SKIPPED++))
        else
            ssh "${SSH_OPTS[@]}" "$IMAC_USER@$HOST" \
                "code --install-extension '$ext' --force 2>/dev/null" && ((INSTALLED++)) || true
        fi
    done <<< "$EXT_LIST"
    log "[SYNC] Estensioni: $INSTALLED installate, $SKIPPED già presenti"
else
    log "[SKIP] Impossibile listare estensioni locali"
fi

# ─── 9. Sync workspace folders (progetti) ────────────────────
log "[SYNC] Workspace progetto principale..."
if [[ -d "$HOME/Projects/vio83-ai-orchestra" ]]; then
    rsync -az --delete \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='dist' \
        --exclude='__pycache__' \
        --exclude='.venv' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='data/*.db' \
        -e "ssh ${SSH_OPTS[*]}" \
        "$HOME/Projects/vio83-ai-orchestra/" \
        "$IMAC_USER@$HOST:~/Projects/vio83-ai-orchestra/"
    log "[SYNC] vio83-ai-orchestra → iMac"
fi

if [[ -d "$HOME/ai-scripts-elite" ]]; then
    rsync -az --delete \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='.env' \
        -e "ssh ${SSH_OPTS[*]}" \
        "$HOME/ai-scripts-elite/" \
        "$IMAC_USER@$HOST:~/ai-scripts-elite/"
    log "[SYNC] ai-scripts-elite → iMac"
fi

# ─── 10. Configura SSH config locale (idempotente) ───────────
SSH_CONFIG="$HOME/.ssh/config"
if ! grep -q "Host imac-archimede" "$SSH_CONFIG" 2>/dev/null; then
    cat >> "$SSH_CONFIG" << EOF

# === iMac Archimede — Bunker Mode ===
Host imac-archimede
    HostName $IMAC_LAN
    User $IMAC_USER
    IdentityFile $IMAC_KEY
    StrictHostKeyChecking accept-new
    PasswordAuthentication no
    PubkeyAuthentication yes
    ForwardAgent no
    ControlMaster auto
    ControlPath ~/.ssh/control-imac-%C
    ControlPersist 300
    ServerAliveInterval 15
    ServerAliveCountMax 3

Host imac-tailscale
    HostName $IMAC_TS
    User $IMAC_USER
    IdentityFile $IMAC_KEY
    StrictHostKeyChecking accept-new
    PasswordAuthentication no
    PubkeyAuthentication yes
    ForwardAgent no
    ControlMaster auto
    ControlPath ~/.ssh/control-imacts-%C
    ControlPersist 300
    ServerAliveInterval 15
    ServerAliveCountMax 3
EOF
    chmod 600 "$SSH_CONFIG"
    log "[CONFIG] SSH config aggiornato con host imac-archimede + imac-tailscale"
else
    log "[SKIP] SSH config già contiene imac-archimede"
fi

# ─── 11. Riepilogo ───────────────────────────────────────────
echo ""
log "═══════════════════════════════════════════"
log "  SYNC COMPLETATO via $TRANSPORT ($HOST)"
log "═══════════════════════════════════════════"
log ""
log "Per aprire VS Code remoto su iMac:"
log "  code --remote ssh-remote+imac-archimede ~/Projects/vio83-ai-orchestra"
log ""
log "Per connessione da VS Code GUI:"
log "  Cmd+Shift+P → Remote-SSH: Connect to Host → imac-archimede"
log ""
log "Log completo: $LOG"
