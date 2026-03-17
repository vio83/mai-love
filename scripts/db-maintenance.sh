#!/bin/bash
# VIO 83 — Database Maintenance
# Rotazione e vacuum automatico dei database SQLite
# Esegui: cron settimanale o da n8n

PROJECT="/Users/padronavio/Projects/vio83-ai-orchestra"
DATA="$PROJECT/data"
LOG="$PROJECT/automation/logs/db-maintenance.log"
mkdir -p "$(dirname "$LOG")"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "$LOG"; }
MAX_KB_KNOWLEDGE=512000  # 500MB max per knowledge_distilled.db
MAX_KB_PROCESS=10240     # 10MB max per process_log.db

log "=== DB Maintenance START ==="

# ─── 1. Process log rotation ───
PROC_LOG="$DATA/process_log.db"
if [ -f "$PROC_LOG" ]; then
    SIZE_KB=$(du -k "$PROC_LOG" | cut -f1)
    if [ "$SIZE_KB" -gt "$MAX_KB_PROCESS" ]; then
        log "process_log.db: ${SIZE_KB}KB > ${MAX_KB_PROCESS}KB — eseguo vacuum + truncate"
        python3 -c "
import sqlite3, os
db = '$PROC_LOG'
conn = sqlite3.connect(db)
# Elimina snapshot vecchi (mantieni ultimi 7 giorni)
cutoff_epoch = __import__('time').time() - (7 * 24 * 3600)
try:
    conn.execute(\"DELETE FROM process_snapshots WHERE timestamp < ?\", (cutoff_epoch,))
except Exception:
    pass
try:
    conn.execute(\"DELETE FROM app_sessions WHERE started_at > 0 AND started_at < ?\", (cutoff_epoch,))
except Exception:
    pass

# Hard cap: conserva i più recenti
try:
    conn.execute(\"DELETE FROM process_snapshots WHERE id NOT IN (SELECT id FROM process_snapshots ORDER BY timestamp DESC LIMIT 50000)\")
except Exception:
    pass

conn.execute('VACUUM')
conn.commit()
conn.close()
print('process_log vacuum OK')
" 2>&1 | tee -a "$LOG"
    else
        log "process_log.db: ${SIZE_KB}KB — OK"
    fi
fi

# ─── 2. Knowledge distilled DB ───
KNOW_DB="$DATA/knowledge_distilled.db"
if [ -f "$KNOW_DB" ]; then
    SIZE_KB=$(du -k "$KNOW_DB" | cut -f1)
    log "knowledge_distilled.db: ${SIZE_KB}KB"
    if [ "$SIZE_KB" -gt "$MAX_KB_KNOWLEDGE" ]; then
        log "AVVISO: knowledge_distilled.db supera 500MB — pruning + vacuum"
        python3 -c "
import sqlite3
import os
conn = sqlite3.connect('$KNOW_DB')

size_kb = os.path.getsize('$KNOW_DB') // 1024
max_kb = $MAX_KB_KNOWLEDGE

if size_kb > max_kb:
    over_kb = size_kb - max_kb
    total_docs = conn.execute('SELECT COUNT(*) FROM l1_metadata').fetchone()[0]
    if total_docs > 0:
        avg_kb = max(1, size_kb // total_docs)
        to_delete = max(250, int((over_kb / avg_kb) * 1.25))

        rows = conn.execute('SELECT doc_id FROM l1_metadata ORDER BY data_distillazione ASC LIMIT ?', (to_delete,)).fetchall()
        ids = [r[0] for r in rows]
        if ids:
            placeholders = ','.join(['?'] * len(ids))
            conn.execute(f'DELETE FROM l2_embeddings WHERE doc_id IN ({placeholders})', ids)
            conn.execute(f'DELETE FROM l3_summaries WHERE doc_id IN ({placeholders})', ids)
            conn.execute(f'DELETE FROM l4_knowledge_graph WHERE doc_id IN ({placeholders})', ids)
            conn.execute(f'DELETE FROM l5_fulltext WHERE doc_id IN ({placeholders})', ids)
            conn.execute(f'DELETE FROM distilled_fts WHERE doc_id IN ({placeholders})', ids)
            conn.execute(f'DELETE FROM l1_metadata WHERE doc_id IN ({placeholders})', ids)

conn.execute('VACUUM')
conn.commit()
conn.close()
print('knowledge prune+vacuum OK')
" 2>&1 | tee -a "$LOG"
        # Dopo vacuum, controlla di nuovo
        SIZE_AFTER=$(du -k "$KNOW_DB" | cut -f1)
        log "knowledge_distilled.db dopo vacuum: ${SIZE_AFTER}KB"
    fi
fi

# ─── 3. WAL checkpoint per tutti i db ───
for DB in "$DATA"/*.db; do
    python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$DB', timeout=3)
    conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    conn.close()
except Exception as e:
    print(f'Skip $DB: {e}')
" 2>/dev/null
done
log "WAL checkpoint completato per tutti i database"

# ─── 4. Elimina .db-journal orfani ───
find "$DATA" -name "*.db-journal" -mtime +1 -delete 2>/dev/null
log "Journal orfani rimossi"

log "=== DB Maintenance DONE | disk: $(df -h "$DATA" | awk 'NR==2{print $4}') liberi ==="
