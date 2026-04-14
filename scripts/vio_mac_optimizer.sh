#!/bin/bash
# === VIO83 Mac Air Optimizer — Cron ogni 5 minuti ===
# Non tocca: Ollama, .env, .git, codice sorgente
# Tocca: cache, logs, temp, diagnostici, buffer

LOG="$HOME/.vio_optimizer.log"
TS=$(date '+%Y-%m-%d %H:%M:%S')

# Limita log a 1000 righe
tail -900 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG" 2>/dev/null

BEFORE=$(df -k / | tail -1 | awk '{print $4}')

# --- PULIZIA CACHE ---
find ~/Library/Caches -mindepth 1 -maxdepth 1 -not -name "com.apple.*" -not -name "Metadata" -exec rm -r {} + 2>/dev/null
find ~/Library/Logs -type f -mtime +1 -delete 2>/dev/null
rm -r ~/Library/Application\ Support/Code/Cache ~/Library/Application\ Support/Code/CachedData ~/Library/Application\ Support/Code/Code\ Cache ~/Library/Application\ Support/Code/GPUCache 2>/dev/null
rm -r ~/Library/Application\ Support/Claude/Cache ~/Library/Application\ Support/Claude/Code\ Cache ~/Library/Application\ Support/Claude/GPUCache 2>/dev/null
rm -r ~/Library/Logs/DiagnosticReports 2>/dev/null

# --- TEMP ---
find /tmp -user $(whoami) -type f -mtime +1 -delete 2>/dev/null

# --- NPM/PIP ---
npm cache clean --force 2>/dev/null
pip3 cache purge 2>/dev/null

# --- ICLOUD EVICTION (se file già uploaded) ---
find ~/Library/Mobile\ Documents/com~apple~CloudDocs/mac-archive-downloads -type f -size +50M 2>/dev/null | while read f; do
    brctl evict "$f" 2>/dev/null
done

# --- RAM: purge inactive pages (solo se disponibile) ---
# sudo purge richiede sudo — skip se non disponibile
purge 2>/dev/null

AFTER=$(df -k / | tail -1 | awk '{print $4}')
FREED=$(( (AFTER - BEFORE) / 1024 ))

echo "$TS | freed: ${FREED}MB | avail: $((AFTER/1024))MB" >> "$LOG"
