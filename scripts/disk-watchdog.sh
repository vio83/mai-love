#!/bin/bash
# ============================================================
# VIO 83 — DISK SPACE WATCHDOG (ogni minuto)
# Auto-ottimizzazione continua spazio disco per ambiente sviluppo
# ============================================================

set -uo pipefail

PROJECT_DIR="/Users/padronavio/Projects/vio83-ai-orchestra"
LOG_FILE="$PROJECT_DIR/automation/logs/disk-watchdog.log"
STATE_FILE="/tmp/vio83-disk-watchdog-state"
FULL_SWEEP_STAMP="/tmp/vio83-disk-watchdog-full-sweep.ts"
LEVEL2_STAMP="/tmp/vio83-disk-watchdog-level2.ts"
LEVEL3_STAMP="/tmp/vio83-disk-watchdog-level3.ts"

mkdir -p "$(dirname "$LOG_FILE")"

# Soglie realistiche per disco 228GB
TARGET_FREE_GB=25
WARN_FREE_GB=18
CRITICAL_FREE_GB=12

log() {
    echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $1" >> "$LOG_FILE"
}

free_gb() {
    df -k /System/Volumes/Data | awk 'NR==2{printf "%d", $4/1048576}'
}

should_run_step() {
    local stamp_file="$1"
    local min_interval_sec="$2"
    local now_epoch
    local last_epoch

    now_epoch=$(date +%s)
    last_epoch=$(cat "$stamp_file" 2>/dev/null || echo 0)

    if [[ $((now_epoch - last_epoch)) -ge $min_interval_sec ]]; then
        echo "$now_epoch" > "$stamp_file"
        return 0
    fi

    return 1
}

FREE=$(free_gb)
echo "{\"free_gb\": $FREE, \"target_gb\": $TARGET_FREE_GB, \"ts\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$STATE_FILE"

MINUTE=$(date +%M | sed 's/^0//')
if [[ $FREE -ge $TARGET_FREE_GB ]]; then
    if [[ $(( ${MINUTE:-0} % 10 )) -eq 0 ]]; then
        log "OK spazio: ${FREE} GB liberi (target >= ${TARGET_FREE_GB} GB)"
    fi
    exit 0
fi

log "WARN spazio basso: ${FREE} GB liberi (target ${TARGET_FREE_GB} GB)"

# Livello 1: sempre sicuro
find "$PROJECT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$PROJECT_DIR/automation/logs" -name "*.log" -mtime +3 -size +5M -delete 2>/dev/null || true
find ~/Library/Logs -name "*.log" -mtime +7 -size +2M -delete 2>/dev/null || true
rm -rf /tmp/vio83-* 2>/dev/null || true
log "L1 completato: pycache/log vecchi/temp"

# Livello 2: rate-limited 30 min
if [[ $FREE -lt $WARN_FREE_GB ]]; then
    if should_run_step "$LEVEL2_STAMP" 1800; then
        command -v npm &>/dev/null && npm cache clean --force 2>/dev/null && log "L2 npm cache"
        command -v pip3 &>/dev/null && pip3 cache purge 2>/dev/null && log "L2 pip cache"
        command -v brew &>/dev/null && brew cleanup --prune=14 2>/dev/null && log "L2 brew cleanup"
        find ~/Library/Application\ Support/Code/User/workspaceStorage -maxdepth 1 -type d -name "*.old" -exec rm -rf {} + 2>/dev/null || true
        find "$PROJECT_DIR/src-tauri/target" -name "incremental" -type d -exec rm -rf {} + 2>/dev/null || true
        find "$PROJECT_DIR/src-tauri/target" -name "*.d" -delete 2>/dev/null || true
        log "L2 completato: cache npm/pip/brew + cargo incremental"
    else
        log "L2 saltato: rate-limit 30m"
    fi
fi

# Livello 3: critico, rate-limited 2h
if [[ $FREE -lt $CRITICAL_FREE_GB ]]; then
    if should_run_step "$LEVEL3_STAMP" 7200; then
        rm -rf "$PROJECT_DIR/node_modules/.vite" 2>/dev/null || true
        rm -rf "$PROJECT_DIR/dist" 2>/dev/null || true
        command -v brew &>/dev/null && brew cleanup --prune=0 2>/dev/null || true
        rm -rf ~/Library/Caches/com.apple.dt.Xcode 2>/dev/null || true
        rm -rf ~/Library/Developer/Xcode/DerivedData 2>/dev/null || true
        rm -rf ~/Library/Caches/pip 2>/dev/null || true
        rm -rf ~/Library/Application\ Support/Code/Cache 2>/dev/null || true
        rm -rf ~/Library/Application\ Support/Code/CachedData 2>/dev/null || true
        find ~/Library/Application\ Support/Code/logs -mindepth 1 -maxdepth 1 -type d -mtime +2 -exec rm -rf {} + 2>/dev/null || true
        find ~/.Trash -mindepth 1 -delete 2>/dev/null || true

        # Reclaim mirato per sviluppo VIO: artefatti rigenerabili
        if [[ -f ~/Library/Application\ Support/Claude/vm_bundles/claudevm.bundle/sessiondata.img ]]; then
            rm -f ~/Library/Application\ Support/Claude/vm_bundles/claudevm.bundle/sessiondata.img 2>/dev/null || true
            log "L3 Claude sessiondata.img rimosso"
        fi
        if [[ -f ~/Library/Application\ Support/Claude/vm_bundles/claudevm.bundle/rootfs.img.zst ]]; then
            rm -f ~/Library/Application\ Support/Claude/vm_bundles/claudevm.bundle/rootfs.img.zst 2>/dev/null || true
            log "L3 Claude rootfs.img.zst rimosso"
        fi
        if [[ -d ~/Library/Application\ Support/Jan/data/llamacpp/models ]]; then
            rm -rf ~/Library/Application\ Support/Jan/data/llamacpp/models/* 2>/dev/null || true
            log "L3 Jan models rimossi"
        fi

        # Sweep completo al massimo ogni 6h
        NOW_EPOCH=$(date +%s)
        LAST_SWEEP=$(cat "$FULL_SWEEP_STAMP" 2>/dev/null || echo 0)
        if [[ $((NOW_EPOCH - LAST_SWEEP)) -ge 21600 ]]; then
            bash "$PROJECT_DIR/scripts/mac-free-space-NOW.sh" >/dev/null 2>&1 || true
            echo "$NOW_EPOCH" > "$FULL_SWEEP_STAMP"
            log "L3+ eseguito mac-free-space-NOW (rate-limit 6h)"
        else
            log "L3+ saltato: rate-limit 6h"
        fi

        log "L3 completato"
    else
        log "L3 saltato: rate-limit 2h"
    fi
fi

FREE_AFTER=$(free_gb)
GAINED=$(( FREE_AFTER - FREE ))
log "DONE pulizia: ${FREE} GB -> ${FREE_AFTER} GB (+${GAINED} GB)"

if [[ $FREE_AFTER -lt $CRITICAL_FREE_GB ]]; then
    osascript -e "display notification \"Disco critico: ${FREE_AFTER} GB liberi\" with title \"VIO83 Disk Alert\"" 2>/dev/null || true
fi

exit 0
