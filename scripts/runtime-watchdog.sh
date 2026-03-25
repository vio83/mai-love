#!/bin/bash
# ============================================================
# VIO 83 — RUNTIME WATCHDOG (RAM/CPU friendly)
# Esecuzione periodica per mantenere ambiente sviluppo stabile
# ============================================================

set -uo pipefail

PROJECT_DIR="/Users/padronavio/Projects/vio83-ai-orchestra"
LOG_FILE="$PROJECT_DIR/automation/logs/runtime-watchdog.log"
STATE_FILE="/tmp/vio83-runtime-watchdog-state"
MEM_SWEEP_STAMP="/tmp/vio83-runtime-watchdog-mem.ts"

mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $1" >> "$LOG_FILE"
}

get_mem_free_pct() {
    memory_pressure -Q 2>/dev/null | awk -F': ' '/System-wide memory free percentage/ {gsub(/%/,"",$2); print int($2)}'
}

get_swap_used_mb() {
    /usr/sbin/sysctl vm.swapusage 2>/dev/null | awk -F'[ =M]' '{for(i=1;i<=NF;i++){if($i=="used"){print int($(i+1)); exit}}}'
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

MEM_FREE_PCT=$(get_mem_free_pct)
SWAP_USED_MB=$(get_swap_used_mb)

if [[ -z "${MEM_FREE_PCT:-}" ]]; then MEM_FREE_PCT=0; fi
if [[ -z "${SWAP_USED_MB:-}" ]]; then SWAP_USED_MB=0; fi

echo "{\"mem_free_pct\": $MEM_FREE_PCT, \"swap_used_mb\": $SWAP_USED_MB, \"ts\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$STATE_FILE"

# Re-applica guardrail Ollama ad ogni ciclo (safe/no-op se già impostate)
launchctl setenv OLLAMA_FLASH_ATTENTION 1 >/dev/null 2>&1 || true
launchctl setenv OLLAMA_MAX_LOADED_MODELS 1 >/dev/null 2>&1 || true
launchctl setenv OLLAMA_NUM_PARALLEL 1 >/dev/null 2>&1 || true
launchctl setenv OLLAMA_KEEP_ALIVE 5m >/dev/null 2>&1 || true
launchctl setenv VIO_OLLAMA_NUM_CTX 2048 >/dev/null 2>&1 || true

if [[ $MEM_FREE_PCT -lt 20 || $SWAP_USED_MB -gt 6000 ]]; then
    log "WARN memoria: free=${MEM_FREE_PCT}% swap=${SWAP_USED_MB}MB"

    # Pulizia leggera cache non critiche
    rm -rf ~/Library/Caches/pip 2>/dev/null || true
    rm -rf ~/Library/Application\ Support/Code/Cache 2>/dev/null || true

    # In stato critico esegue purge al massimo ogni 30 minuti
    if [[ $MEM_FREE_PCT -lt 14 || $SWAP_USED_MB -gt 9000 ]]; then
        if should_run_step "$MEM_SWEEP_STAMP" 1800; then
            if command -v purge >/dev/null 2>&1; then
                purge >/dev/null 2>&1 || true
                log "Azione: purge eseguito"
            fi

            # Se non ci sono connessioni attive a Ollama, scarica modelli in RAM
            if command -v ollama >/dev/null 2>&1; then
                if ! lsof -iTCP:11434 -sTCP:ESTABLISHED 2>/dev/null | grep -q ESTABLISHED; then
                    ollama ps 2>/dev/null | awk 'NR>1 {print $1}' | while read -r model; do
                        [[ -n "$model" ]] && ollama stop "$model" >/dev/null 2>&1 || true
                    done
                    log "Azione: scarico modelli Ollama in RAM (nessuna connessione attiva)"
                fi
            fi
        else
            log "Azione critica saltata: rate-limit 30m"
        fi
    fi
else
    log "OK memoria: free=${MEM_FREE_PCT}% swap=${SWAP_USED_MB}MB"
fi

exit 0
