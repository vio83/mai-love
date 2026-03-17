#!/bin/bash
# ============================================================
# VIO 83 — MAC DISK CLEANUP SCRIPT
# Libera spazio su MacBook Air M1 in modo sicuro
# Eseguito da: n8n autopilot + LaunchAgent giornaliero
# Data: 17 Marzo 2026
# ============================================================

set -euo pipefail

PROJECT_DIR="/Users/padronavio/Projects/vio83-ai-orchestra"
LOG_FILE="$PROJECT_DIR/automation/logs/mac-cleanup.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "$LOG_FILE"
}

freed=0
before=$(df -k / | awk 'NR==2{print $4}')

log "=== VIO83 Mac Cleanup START ==="

# ─── 1. npm/pnpm cache ───
if command -v npm &>/dev/null; then
    npm cache clean --force 2>/dev/null && log "✅ npm cache pulita" || log "⚠️ npm cache skip"
fi

# ─── 2. pip cache ───
if command -v pip3 &>/dev/null; then
    pip3 cache purge 2>/dev/null && log "✅ pip3 cache pulita" || log "⚠️ pip3 cache skip"
fi

# ─── 3. Homebrew cache ───
if command -v brew &>/dev/null; then
    brew cleanup --prune=7 2>/dev/null && log "✅ Homebrew cleanup" || log "⚠️ brew skip"
fi

# ─── 4. Rust/Cargo build artifacts (SOLO debug, non release) ───
CARGO_DEBUG="$PROJECT_DIR/src-tauri/target/debug"
if [ -d "$CARGO_DEBUG" ]; then
    SIZE_BEFORE=$(du -sk "$CARGO_DEBUG" 2>/dev/null | cut -f1)
    find "$CARGO_DEBUG" -name "*.d" -delete 2>/dev/null
    find "$CARGO_DEBUG" -name "incremental" -type d -exec rm -rf {} + 2>/dev/null || true
    SIZE_AFTER=$(du -sk "$CARGO_DEBUG" 2>/dev/null | cut -f1 || echo "$SIZE_BEFORE")
    SAVED=$(( (SIZE_BEFORE - SIZE_AFTER) / 1024 ))
    log "✅ Cargo debug artifacts: liberati ~${SAVED}MB"
fi

# ─── 5. Python __pycache__ nel progetto ───
find "$PROJECT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_DIR" -name "*.pyc" -delete 2>/dev/null || true
log "✅ Python __pycache__ rimossi"

# ─── 6. Log vecchi > 7 giorni ───
find "$PROJECT_DIR/automation/logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
log "✅ Log vecchi (>7 giorni) rimossi"

# ─── 7. macOS system caches (safe) ───
rm -rf ~/Library/Caches/com.apple.dt.Xcode 2>/dev/null || true
rm -rf ~/Library/Developer/Xcode/DerivedData/* 2>/dev/null || true
rm -rf ~/Library/Caches/pip 2>/dev/null || true
# Trash system log snippets (safe)
find ~/Library/Logs -name "*.log" -mtime +14 -delete 2>/dev/null || true
log "✅ macOS caches di sistema pulite"

# ─── 8. Docker (se installato) ───
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    docker system prune -f --filter "until=168h" 2>/dev/null && log "✅ Docker prune (>7 giorni)" || true
fi

# ─── 9. Ollama models audit (NON cancella, solo lista) ───
if command -v ollama &>/dev/null; then
    OLLAMA_MODELS=$(ollama list 2>/dev/null | tail -n +2)
    log "📋 Ollama modelli attivi:"
    echo "$OLLAMA_MODELS" | while read -r line; do
        log "   $line"
    done
    # Conta modelli non usati di recente (solo report, non cancella)
    COUNT=$(echo "$OLLAMA_MODELS" | wc -l | tr -d ' ')
    log "   Totale: $COUNT modelli. Rimuovi manualmente quelli non usati con: ollama rm <nome>"
fi

# ─── 10. Calcolo spazio liberato ───
after=$(df -k / | awk 'NR==2{print $4}')
freed_mb=$(( (after - before) / 1024 ))
log "=== CLEANUP COMPLETATO ==="
log "💾 Spazio liberato questa esecuzione: ~${freed_mb}MB"
log "💾 Spazio disponibile ora: $(df -h / | awk 'NR==2{print $4}')"

# ─── Output strutturato per n8n ───
echo "{\"freed_mb\": ${freed_mb}, \"available\": \"$(df -h / | awk 'NR==2{print $4}')\", \"status\": \"ok\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
