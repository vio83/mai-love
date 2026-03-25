#!/bin/bash
# ============================================================
# VIO 83 — DISK SPACE WATCHDOG (ogni minuto)
# Target: mantenere ≥45 GB liberi su /
# Agisce SOLO se lo spazio scende sotto soglia
# Azioni sicure e non distruttive — mai cancella dati utente
# ============================================================

set -uo pipefail

PROJECT_DIR="/Users/padronavio/Projects/vio83-ai-orchestra"
LOG_FILE="$PROJECT_DIR/automation/logs/disk-watchdog.log"
STATE_FILE="/tmp/vio83-disk-watchdog-state"
FULL_SWEEP_STAMP="/tmp/vio83-disk-watchdog-full-sweep.ts"
mkdir -p "$(dirname "$LOG_FILE")"

# ─── SOGLIE (GB) ───
# MacBook Air M1 228GB: priorità massima alla salute dell'ambiente di sviluppo.
# Soglie rialzate per mantenere headroom stabile per VS Code, build, cache e modelli locali.
TARGET_FREE_GB=45       # Obiettivo: tenere almeno 45 GB liberi
WARN_FREE_GB=35         # Soglia warning: scatta pulizia estesa
CRITICAL_FREE_GB=25     # Soglia critica: scatta pulizia aggressiva + full sweep

log() {
    echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $1" >> "$LOG_FILE"
}

# Spazio libero in GB (intero)
free_gb() {
    df -k / | awk 'NR==2{printf "%d", $4/1048576}'
}

FREE=$(free_gb)

# ─── Scrivi stato in /tmp per monitoring esterno ───
echo "{\"free_gb\": $FREE, \"target_gb\": $TARGET_FREE_GB, \"ts\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$STATE_FILE"

# ─── Se spazio è OK, log silenzioso ogni 10 minuti e usci ───
MINUTE=$(date +%M | sed 's/^0//')
if [[ $FREE -ge $TARGET_FREE_GB ]]; then
    # Log solo ogni 10 minuti per non spammare
    if [[ $(( ${MINUTE:-0} % 10 )) -eq 0 ]]; then
        log "✅ Spazio OK: ${FREE} GB liberi (target: ≥${TARGET_FREE_GB} GB)"
    fi
    exit 0
fi

# ─── SPAZIO SOTTO SOGLIA — AZIONE ───
log "⚠️  Spazio sotto soglia: ${FREE} GB liberi (target: ${TARGET_FREE_GB} GB) — pulizia in corso..."

cleaned=0

# ─── LIVELLO 1: Sempre sicuro — cache temporanee e log vecchi ───
# Python __pycache__ nel progetto
find "$PROJECT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_DIR" -name "*.pyc" -delete 2>/dev/null || true

# Log progetto > 3 giorni
find "$PROJECT_DIR/automation/logs" -name "*.log" -mtime +3 -size +5M -delete 2>/dev/null || true

# macOS temp files
rm -rf /tmp/vio83-* 2>/dev/null || true
find ~/Library/Logs -name "*.log" -mtime +7 -size +2M -delete 2>/dev/null || true

log "  ✔ Livello 1: __pycache__, log vecchi, temp"
cleaned=1

# ─── LIVELLO 2: WARNING — cache applicazioni ───
if [[ $FREE -lt $WARN_FREE_GB ]]; then
    log "  ⚡ Livello 2 (warning <${WARN_FREE_GB} GB)"

    # npm cache
    command -v npm &>/dev/null && npm cache clean --force 2>/dev/null && log "  ✔ npm cache" || true

    # pip cache
    command -v pip3 &>/dev/null && pip3 cache purge 2>/dev/null && log "  ✔ pip3 cache" || true

    # Homebrew cache > 14 giorni
    command -v brew &>/dev/null && brew cleanup --prune=14 2>/dev/null && log "  ✔ brew cleanup" || true

    # VS Code extension host caches
    find ~/Library/Application\ Support/Code/User/workspaceStorage -maxdepth 1 \
        -type d -name "*.old" -exec rm -rf {} + 2>/dev/null || true

    # Cargo incremental build cache (sicuro da ricostruire)
    find "$PROJECT_DIR/src-tauri/target" -name "incremental" -type d \
        -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_DIR/src-tauri/target" -name "*.d" -delete 2>/dev/null || true

    log "  ✔ Livello 2: npm/pip/brew cache, cargo incremental"
fi

# ─── LIVELLO 3: CRITICO — misure più aggressive (mai dati utente) ───
if [[ $FREE -lt $CRITICAL_FREE_GB ]]; then
    log "  🚨 Livello 3 CRITICO (<${CRITICAL_FREE_GB} GB)"

    # Vite build cache (si rigenera con npm run build)
    rm -rf "$PROJECT_DIR/node_modules/.vite" 2>/dev/null || true
    rm -rf "$PROJECT_DIR/dist" 2>/dev/null || true

    # Homebrew download cache completo
    command -v brew &>/dev/null && brew cleanup --prune=0 2>/dev/null || true

    # macOS system caches (non sistema, solo utente — sicuro)
    rm -rf ~/Library/Caches/com.apple.dt.Xcode 2>/dev/null || true
    rm -rf ~/Library/Developer/Xcode/DerivedData 2>/dev/null || true
    rm -rf ~/Library/Caches/pip 2>/dev/null || true

    # Svuota Trash via rm (sicuro da daemon senza GUI)
    find ~/.Trash -mindepth 1 -delete 2>/dev/null || true

    # Sweep completo rate-limited: al massimo ogni 6 ore
    NOW_EPOCH=$(date +%s)
    LAST_SWEEP=$(cat "$FULL_SWEEP_STAMP" 2>/dev/null || echo 0)
    if [[ $((NOW_EPOCH - LAST_SWEEP)) -ge 21600 ]]; then
        bash "$PROJECT_DIR/scripts/mac-free-space-NOW.sh" >/dev/null 2>&1 || true
        echo "$NOW_EPOCH" > "$FULL_SWEEP_STAMP"
        log "  ✔ Livello 3+: eseguito mac-free-space-NOW (rate-limited 6h)"
    else
        log "  ↷ Livello 3+: full sweep saltato (già eseguito nelle ultime 6h)"
    fi

    log "  ✔ Livello 3: vite cache, dist, xcode, trash"
fi

FREE_AFTER=$(free_gb)
GAINED=$(( FREE_AFTER - FREE ))
log "✅ Pulizia completata: ${FREE} GB → ${FREE_AFTER} GB (+${GAINED} GB recuperati)"

# ─── Notifica macOS (solo se nel contesto GUI) ───
if [[ $FREE_AFTER -lt $CRITICAL_FREE_GB ]] && [[ -n "${DISPLAY:-}" || "$(uname)" == "Darwin" ]]; then
    osascript -e "display notification \"⚠️ Disco: solo ${FREE_AFTER} GB liberi!\" with title \"VIO83 Disk Alert\" sound name \"Basso\"" 2>/dev/null || true
    log "🔔 Notifica: ${FREE_AFTER} GB liberi"
fi

exit 0
