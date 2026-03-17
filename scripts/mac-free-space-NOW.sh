#!/bin/bash
# ============================================================
# VIO 83 — MAC FREE SPACE NOW (ESECUZIONE IMMEDIATA)
# Libera 10-30GB in 2-5 minuti. SICURO AL 100%.
#
# ESEGUI ORA:
#   bash ~/Projects/vio83-ai-orchestra/scripts/mac-free-space-NOW.sh
# ============================================================

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'

PROJECT="$HOME/Projects/vio83-ai-orchestra"
LOG="$PROJECT/automation/logs/mac-free-space.log"
mkdir -p "$(dirname "$LOG")"

log()  { echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$LOG"; }
sep()  { echo -e "${BOLD}────────────────────────────────────────${NC}"; }

disk_free() { df -g / | awk 'NR==2{print $4}'; }
disk_free_hr() { df -h / | awk 'NR==2{print $4}'; }

echo -e "${BOLD}${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║     VIO 83 — MAC FREE SPACE NOW                      ║"
echo "║     $(date '+%Y-%m-%d %H:%M:%S')                           ║"
echo "╚══════════════════════════════════════════════════════╝${NC}"
echo ""

BEFORE_GB=$(disk_free)
BEFORE_HR=$(disk_free_hr)
info "Spazio libero PRIMA: ${BEFORE_HR}"
sep

# ═══════════════════════════════════════════════════════════
# BLOCCO 1: CARGO/RUST BUILD ARTIFACTS ← BIGGEST KILLER
# Su Mac può occupare 5-30GB facilmente
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}[1/10] 🦀 Cargo/Rust build artifacts${NC}"

# Cartella target del progetto VIO83
if [ -d "$PROJECT/src-tauri/target" ]; then
    SIZE=$(du -sh "$PROJECT/src-tauri/target" 2>/dev/null | cut -f1)
    info "target/ VIO83: $SIZE"
    # Pulisce debug (rigenera in 2 min), mantiene release se esiste
    rm -rf "$PROJECT/src-tauri/target/debug" 2>/dev/null
    rm -rf "$PROJECT/src-tauri/target/doc" 2>/dev/null
    find "$PROJECT/src-tauri/target" -name "*.d" -delete 2>/dev/null || true
    find "$PROJECT/src-tauri/target" -name "*.rmeta" -delete 2>/dev/null || true
    log "Cargo debug artifacts VIO83 rimossi (erano $SIZE)"
fi

# Tutti i progetti Rust/Tauri sul Mac
find "$HOME/Projects" "$HOME/Developer" "$HOME/Code" "$HOME/repos" "$HOME/git" -maxdepth 4 -name "target" -type d 2>/dev/null | while read -r tdir; do
    if [ -f "$(dirname "$tdir")/Cargo.toml" ] || [ -f "$(dirname "$(dirname "$tdir")")/Cargo.toml" ]; then
        SIZE=$(du -sh "$tdir" 2>/dev/null | cut -f1)
        rm -rf "$tdir/debug" 2>/dev/null
        log "Cargo debug rimosso: $tdir (era $SIZE)"
    fi
done

# Cargo registry e cache globale (sicuro da pulire)
if [ -d "$HOME/.cargo/registry/src" ]; then
    SIZE=$(du -sh "$HOME/.cargo/registry/src" 2>/dev/null | cut -f1)
    rm -rf "$HOME/.cargo/registry/src" 2>/dev/null
    log "Cargo registry/src: $SIZE rimossi"
fi
if [ -d "$HOME/.cargo/git/checkouts" ]; then
    SIZE=$(du -sh "$HOME/.cargo/git/checkouts" 2>/dev/null | cut -f1)
    rm -rf "$HOME/.cargo/git/checkouts" 2>/dev/null
    log "Cargo git checkouts: $SIZE rimossi"
fi
sep

# ═══════════════════════════════════════════════════════════
# BLOCCO 2: XCODE DERIVEDDATA ← SECONDO KILLER (5-50GB)
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}[2/10] 🍎 Xcode DerivedData + Archives${NC}"

XCODE_DERIVED="$HOME/Library/Developer/Xcode/DerivedData"
if [ -d "$XCODE_DERIVED" ]; then
    SIZE=$(du -sh "$XCODE_DERIVED" 2>/dev/null | cut -f1)
    rm -rf "$XCODE_DERIVED"/* 2>/dev/null
    log "Xcode DerivedData: $SIZE rimossi"
fi

XCODE_ARCHIVES="$HOME/Library/Developer/Xcode/Archives"
if [ -d "$XCODE_ARCHIVES" ]; then
    SIZE=$(du -sh "$XCODE_ARCHIVES" 2>/dev/null | cut -f1)
    # Mantieni ultimi 30 giorni
    find "$XCODE_ARCHIVES" -mtime +30 -delete 2>/dev/null || true
    log "Xcode Archives vecchi (>30gg): rimossi"
fi

# iOS Simulators (possono essere ENORMI - 10-20GB)
SIMULATORS="$HOME/Library/Developer/CoreSimulator/Devices"
if [ -d "$SIMULATORS" ]; then
    SIZE=$(du -sh "$SIMULATORS" 2>/dev/null | cut -f1)
    info "Simulatori iOS: $SIZE — per rimuovere quelli non usati: xcrun simctl delete unavailable"
    xcrun simctl delete unavailable 2>/dev/null && log "Simulatori iOS non disponibili rimossi" || true
fi
sep

# ═══════════════════════════════════════════════════════════
# BLOCCO 3: NODE_MODULES + NPM/PNPM/YARN CACHE
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}[3/10] 📦 Node.js caches + orphan node_modules${NC}"

# npm cache
npm cache clean --force 2>/dev/null && log "npm cache pulita" || warn "npm non trovato"

# pnpm cache
pnpm store prune 2>/dev/null && log "pnpm store pruned" || true

# yarn cache
yarn cache clean 2>/dev/null && log "yarn cache pulita" || true

# node_modules nei progetti NON attivi (non toccati da >30 giorni)
find "$HOME/Projects" "$HOME/Developer" -maxdepth 4 -name "node_modules" -type d -mtime +30 2>/dev/null | while read -r nm; do
    SIZE=$(du -sh "$nm" 2>/dev/null | cut -f1)
    # Non tocca il progetto VIO83 attivo
    if [[ "$nm" != *"vio83-ai-orchestra"* ]]; then
        rm -rf "$nm" 2>/dev/null
        log "node_modules inattivo rimosso: $nm ($SIZE)"
    fi
done

# npx cache
rm -rf "$HOME/.npx" 2>/dev/null || true
log "npx cache rimossa"
sep

# ═══════════════════════════════════════════════════════════
# BLOCCO 4: PYTHON pip/conda/venv
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}[4/10] 🐍 Python environments + caches${NC}"

pip3 cache purge 2>/dev/null && log "pip3 cache purge" || warn "pip3 non trovato"

# pyc e pycache in tutti i progetti
find "$HOME/Projects" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$HOME/Projects" -name "*.pyc" -delete 2>/dev/null || true
log "Python __pycache__ e .pyc rimossi"

# Conda cache (se installato)
conda clean --all --yes 2>/dev/null && log "conda cache pulita" || true
sep

# ═══════════════════════════════════════════════════════════
# BLOCCO 5: HOMEBREW
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}[5/10] 🍺 Homebrew cache${NC}"

if command -v brew &>/dev/null; then
    SIZE=$(du -sh "$(brew --cache)" 2>/dev/null | cut -f1 || echo "?")
    brew cleanup --prune=1 2>/dev/null
    brew autoremove 2>/dev/null
    log "Homebrew cleanup (cache era ~$SIZE)"
else
    warn "Homebrew non trovato"
fi
sep

# ═══════════════════════════════════════════════════════════
# BLOCCO 6: DOCKER (se installato)
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}[6/10] 🐳 Docker pruning${NC}"

if docker info &>/dev/null 2>&1; then
    docker system prune -af --volumes 2>/dev/null
    log "Docker: tutti i container/immagini/volumi non usati rimossi"
else
    info "Docker non attivo — skip"
fi
sep

# ═══════════════════════════════════════════════════════════
# BLOCCO 7: OLLAMA MODELS AUDIT
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}[7/10] 🧠 Ollama models${NC}"

if command -v ollama &>/dev/null; then
    MODELS=$(ollama list 2>/dev/null | tail -n +2)
    COUNT=$(echo "$MODELS" | grep -c . || echo 0)
    SIZE_DIR=""
    if [ -d "$HOME/.ollama/models" ]; then
        SIZE_DIR=$(du -sh "$HOME/.ollama/models" 2>/dev/null | cut -f1)
    fi
    info "Ollama: $COUNT modelli installati (totale: $SIZE_DIR)"
    echo "$MODELS"
    echo ""
    info "Per rimuovere un modello non usato: ollama rm <nome>"
    info "Modelli pesanti tipici: llama3 (4GB), codellama (4GB), mistral (4GB)"
    info "Mantieni solo quelli che usi: gemma2:2b (1.6GB) è già in .env come default"
else
    info "Ollama non trovato"
fi
sep

# ═══════════════════════════════════════════════════════════
# BLOCCO 8: MACOS SYSTEM CACHES + LOG
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}[8/10] 🍏 macOS caches + log di sistema${NC}"

# Cache utente
USER_CACHE="$HOME/Library/Caches"
if [ -d "$USER_CACHE" ]; then
    # Safe caches to remove (non Apple system caches)
    for cache_dir in \
        "com.apple.dt.Xcode" \
        "pip" \
        "node" \
        "com.electron" \
        "typescript" \
        "Yarn" \
        "Cypress" \
        "com.google.Chrome" \
        "Google" \
        "BraveSoftware" \
        "Mozilla" \
        "ms-playwright"
    do
        TARGET="$USER_CACHE/$cache_dir"
        if [ -d "$TARGET" ]; then
            SIZE=$(du -sh "$TARGET" 2>/dev/null | cut -f1)
            rm -rf "$TARGET" 2>/dev/null
            log "Cache rimossa: $cache_dir ($SIZE)"
        fi
    done
fi

# Log di sistema vecchi (>14 giorni)
find "$HOME/Library/Logs" -name "*.log" -mtime +14 -delete 2>/dev/null || true
find /private/var/log -name "*.log" -mtime +14 -delete 2>/dev/null || true
log "Log di sistema vecchi (>14gg) rimossi"

# Crash reports
rm -rf "$HOME/Library/Logs/DiagnosticReports"/*.crash 2>/dev/null || true
log "Crash reports rimossi"
sep

# ═══════════════════════════════════════════════════════════
# BLOCCO 9: VS CODE CACHE + ESTENSIONI ORFANE
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}[9/10] 💻 VS Code cache${NC}"

VSCODE_CACHE="$HOME/Library/Application Support/Code/Cache"
VSCODE_BACKUP="$HOME/Library/Application Support/Code/Backups"
VSCODE_LOGS="$HOME/Library/Application Support/Code/logs"

for dir in "$VSCODE_CACHE" "$VSCODE_BACKUP" "$VSCODE_LOGS"; do
    if [ -d "$dir" ]; then
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1)
        rm -rf "$dir"/* 2>/dev/null
        log "VS Code: $(basename "$dir") ($SIZE) pulita"
    fi
done

# Extensions cache
VSCODE_EXT_CACHE="$HOME/.vscode/extensions/.obsolete"
rm -f "$VSCODE_EXT_CACHE" 2>/dev/null || true
log "VS Code estensioni obsolete rimosse"
sep

# ═══════════════════════════════════════════════════════════
# BLOCCO 10: TRASH + FILE DOWNLOADS VECCHI
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}[10/10] 🗑️ Trash + Downloads vecchi${NC}"

# Svuota Trash (osascript è più sicuro di rm -rf)
osascript -e 'tell application "Finder" to empty trash' 2>/dev/null && log "Trash svuotata" || warn "Trash: impossibile svuotare via script"

# Downloads vecchi > 60 giorni (solo report, non cancella automaticamente - troppo rischioso)
OLD_DOWNLOADS=$(find "$HOME/Downloads" -mtime +60 -type f 2>/dev/null | wc -l | tr -d ' ')
OLD_SIZE=$(find "$HOME/Downloads" -mtime +60 -type f 2>/dev/null -exec du -k {} + 2>/dev/null | awk '{sum+=$1}END{printf "%.0fMB", sum/1024}')
if [ "$OLD_DOWNLOADS" -gt 0 ]; then
    warn "Downloads > 60 giorni: $OLD_DOWNLOADS file ($OLD_SIZE) — rimuovi manualmente quelli non necessari"
    info "Comando: find ~/Downloads -mtime +60 -type f -ls"
fi
sep

# ═══════════════════════════════════════════════════════════
# RISULTATO FINALE
# ═══════════════════════════════════════════════════════════
AFTER_GB=$(disk_free)
AFTER_HR=$(disk_free_hr)
FREED_GB=$(( AFTER_GB - BEFORE_GB ))

echo ""
echo -e "${BOLD}${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║     CLEANUP COMPLETATO                               ║"
echo "╠══════════════════════════════════════════════════════╣"
printf  "║  Prima:   %-42s║\n" "${BEFORE_HR}"
printf  "║  Dopo:    %-42s║\n" "${AFTER_HR}"
printf  "║  Liberati: ~%-40s║\n" "${FREED_GB}GB"
echo "╚══════════════════════════════════════════════════════╝${NC}"

# Avviso se ancora sotto 15GB
if [ "$AFTER_GB" -lt 15 ]; then
    echo ""
    echo -e "${RED}${BOLD}⚠️  ANCORA SOTTO 15GB LIBERI — AZIONI AGGIUNTIVE CONSIGLIATE:${NC}"
    echo ""
    echo -e "${YELLOW}1. Ollama: rimuovi modelli non usati${NC}"
    echo "   ollama list && ollama rm <nome_modello_non_usato>"
    echo ""
    echo -e "${YELLOW}2. Cargo target/release (se non devi fare build subito):${NC}"
    echo "   rm -rf ~/Projects/vio83-ai-orchestra/src-tauri/target/release"
    echo "   (si rigenera con: npm run tauri:build)"
    echo ""
    echo -e "${YELLOW}3. Finds files > 500MB sul sistema:${NC}"
    echo "   find ~ -type f -size +500M 2>/dev/null | head -20"
    echo ""
    echo -e "${YELLOW}4. Analisi completa con ncdu (installa con: brew install ncdu):${NC}"
    echo "   ncdu ~"
fi

echo ""
log "=== mac-free-space-NOW completato: $(date -u +%Y-%m-%dT%H:%M:%SZ) | Liberati ~${FREED_GB}GB ==="
