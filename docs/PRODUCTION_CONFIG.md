# VIO 83 AI Orchestra — Configurazione Produzione
## Architettura a 3 Livelli + Checklist Completa
### Data: 17 Marzo 2026 | Versione: 1.0.0-prod

---

## LIVELLO 1 — INTERFACCIA (Ingresso messaggi/eventi)

### Sicurezza Ingresso
```
✅ HTTPS obbligatorio via reverse proxy (nginx/Caddy)
✅ Firma webhook verificata (HMAC-SHA256)
✅ Rate limiting: 100 req/min per IP, 1000 req/ora per utente
✅ Whitelist IP per endpoint admin (/admin/*, /metrics/*)
✅ CORS configurato solo per origini autorizzate
✅ Timeout webhook: 30s (no attese infinite)
```

### nginx Configurazione Base
```nginx
# /usr/local/etc/nginx/vio83.conf
server {
    listen 443 ssl http2;
    server_name vio83.local;

    ssl_certificate     /etc/ssl/vio83/cert.pem;
    ssl_certificate_key /etc/ssl/vio83/key.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req zone=api burst=20 nodelay;

    location /api/ {
        proxy_pass         http://127.0.0.1:4000;
        proxy_read_timeout 30s;
        proxy_send_timeout 30s;
        proxy_set_header   X-Request-ID $request_id;
    }

    location /admin/ {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://127.0.0.1:4000;
    }
}
```

---

## LIVELLO 2 — AGENTE (Routing, Strumenti, Memoria, Policy)

### Intent-Based Routing
```python
# backend/core/router.py

ROUTING_RULES = {
    "faq": {
        "model": "llama3:8b",        # locale, gratuito, veloce
        "max_tokens": 512,
        "timeout": 10,
        "patterns": ["cos'è", "come si", "dove trovo", "quando"]
    },
    "reasoning": {
        "model": "claude-sonnet-4-6",  # cloud, potente
        "max_tokens": 4096,
        "timeout": 60,
        "patterns": ["analizza", "confronta", "spiega perché", "piano"]
    },
    "code": {
        "model": "deepseek-coder",     # economico per codice
        "max_tokens": 8192,
        "timeout": 120,
        "patterns": ["scrivi codice", "debug", "refactor", "test"]
    },
    "fallback": {
        "model": "gemma2:2b",          # locale, sempre disponibile
        "max_tokens": 256,
        "action": "ask_clarification"
    }
}

TOKEN_BUDGET = {
    "per_request": 8192,
    "context_window": 16384,
    "max_history_messages": 20
}
```

### Gestione Errori — Zero Errori Silenziosi
```python
# backend/core/tool_executor.py

import logging
import uuid
from datetime import datetime

logger = logging.getLogger("vio83.tools")

async def execute_tool(tool_name: str, params: dict) -> dict:
    request_id = str(uuid.uuid4())[:8]
    start_time = datetime.utcnow()

    try:
        result = await _run_tool(tool_name, params)
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        logger.info(json.dumps({
            "event": "tool_success",
            "request_id": request_id,
            "tool": tool_name,
            "duration_ms": duration_ms,
            "timestamp": start_time.isoformat()
        }))
        return {"ok": True, "result": result, "request_id": request_id}

    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        logger.error(json.dumps({
            "event": "tool_failure",
            "request_id": request_id,
            "tool": tool_name,
            "error": str(e),
            "error_type": type(e).__name__,
            "duration_ms": duration_ms,
            "params_keys": list(params.keys()),  # keys solo, mai valori (sicurezza)
            "timestamp": start_time.isoformat()
        }))
        return {"ok": False, "error": str(e), "context": tool_name, "request_id": request_id}
```

### Cache Risposte Frequenti
```python
# backend/core/cache.py

from functools import lru_cache
import hashlib

# Cache LRU in memoria per FAQ (no token extra)
@lru_cache(maxsize=256)
def get_cached_faq(query_hash: str) -> str | None:
    return _faq_store.get(query_hash)

def cache_response(query: str, response: str, ttl_seconds: int = 3600):
    key = hashlib.sha256(query.lower().strip().encode()).hexdigest()[:16]
    _faq_store[key] = {"response": response, "expires": time.time() + ttl_seconds}

# Cache metadata Ollama (modelli disponibili) — aggiornamento ogni 5 min
_ollama_models_cache = {"data": None, "expires": 0}

def get_ollama_models_cached() -> list:
    if time.time() < _ollama_models_cache["expires"]:
        return _ollama_models_cache["data"]
    models = fetch_ollama_models()  # chiamata reale solo se cache scaduta
    _ollama_models_cache.update({"data": models, "expires": time.time() + 300})
    return models
```

### Credenziali Separate per Ambiente
```bash
# .env.dev   → solo mock APIs, nessuna chiave reale
# .env.staging → chiavi con limiti di budget bassi
# .env.prod  → chiavi reali, rotazione ogni 90 giorni

# Mai credenziali in codice. Mai un token che sblocca tutto.
# Ogni provider ha la sua chiave separata.
ANTHROPIC_API_KEY=sk-ant-...   # solo Claude
OPENAI_API_KEY=sk-...          # solo OpenAI
GROQ_API_KEY=gsk_...           # solo Groq
# Admin API separata con permessi minimi necessari
```

---

## LIVELLO 3 — OPERATIVO (Deployment, Osservabilità, Backup)

### Process Supervisor — PM2 con Policy di Riavvio
```javascript
// ecosystem.config.js — già presente nel progetto
module.exports = {
  apps: [
    {
      name: "vio-backend",
      script: "backend/main.py",
      interpreter: "python3",
      watch: false,
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
      restart_delay: 3000,
      env_file: ".env",
      error_file: "automation/logs/backend-error.log",
      out_file: "automation/logs/backend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z"
    }
  ]
};
```

### Health Check Endpoint
```python
# backend/api/health.py

@router.get("/health")
async def health_check():
    checks = {
        "backend": "ok",
        "ollama": await check_ollama(),
        "database": await check_db(),
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
    status = 200 if all(v == "ok" for k, v in checks.items() if k != "timestamp" and k != "version") else 503
    return JSONResponse(content=checks, status_code=status)
```

### Dashboard Log — Latenza p50/p95
```python
# In backend/api/metrics.py — endpoint /metrics (solo localhost)

import statistics

def compute_latency_percentiles(samples: list[float]) -> dict:
    if not samples:
        return {"p50": 0, "p95": 0, "count": 0}
    s = sorted(samples)
    return {
        "p50": s[int(len(s) * 0.50)],
        "p95": s[int(len(s) * 0.95)],
        "count": len(s),
        "error_rate": f"{(error_count / total_requests * 100):.1f}%"
    }
```

### Backup — Ripristino in 10 Minuti
```bash
#!/bin/bash
# scripts/backup.sh — eseguito da cron ogni notte a 02:00

PROJECT=/Users/padronavio/Projects/vio83-ai-orchestra
BACKUP_DIR=~/Backups/vio83
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# 1. Database SQLite (< 1 secondo)
cp "$PROJECT/data/vio83.db" "$BACKUP_DIR/vio83_$DATE.db"

# 2. Configurazione (esclusi segreti)
tar czf "$BACKUP_DIR/config_$DATE.tar.gz" \
  "$PROJECT/data/config/" \
  "$PROJECT/docs/" \
  --exclude="*.key" --exclude=".env*"

# 3. Mantieni solo ultimi 7 backup
ls -t "$BACKUP_DIR"/*.db | tail -n +8 | xargs rm -f 2>/dev/null
ls -t "$BACKUP_DIR"/*.tar.gz | tail -n +8 | xargs rm -f 2>/dev/null

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Backup completato: $DATE"
```

---

## AGENTI ATTIVI IN VIO 83 AI ORCHESTRA

### Agenti Attualmente Configurati

| Agente | Framework | Ruolo | Trigger |
|--------|-----------|-------|---------|
| **RoutingAgent** | Custom Python | Analizza intent → seleziona modello | Ogni richiesta |
| **CrossCheckAgent** | LangChain | Verifica risposta con secondo AI | Richieste critiche |
| **RAGAgent** | LangChain + ChromaDB | Recupera documenti rilevanti | Query knowledge base |
| **OrchestratorAgent** | LangGraph | Coordina multi-step task complessi | Task lunghi |
| **RuntimeSupervisorAgent** | n8n | Monitora health PM2/Backend/Ollama | Ogni 2 min |
| **AutoUpdateAgent** | n8n + shell | Controlla aggiornamenti provider | Ogni 6 ore |
| **SEOPingAgent** | n8n | Notifica motori di ricerca | Su ogni push |

### Agenti Autonomi 24/7 — Attivazione
```bash
# 1. Avvia tutti gli agenti via PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # installa come servizio macOS (LaunchAgent)

# 2. Importa workflow n8n
# Apri http://localhost:5678 → Import → seleziona i file in automation/n8n-workflows/

# 3. Verifica stato completo
pm2 status
curl http://localhost:4000/health
curl http://localhost:11434/api/tags
```

---

## FIX API ERROR 500 — CLAUDE CODE COWORK

### Causa Reale (brutalmente onesta)
```
HTTP 500 Internal Server Error = ERRORE LATO SERVER ANTHROPIC
NON è un bug nel tuo codice VIO 83.
NON puoi "fixarlo" tu.
```

### Cosa Succede
```
request_id: req_011CZ9DcTgpA1XFQTBNqXY72
→ Questo ID appartiene ai server Anthropic
→ Significa che la richiesta è arrivata ad Anthropic ma ha fallito internamente

Cause più comuni:
1. Contesto troppo lungo (Opus 4.6 su conversazioni lunghe)
2. Carico elevato sui server Anthropic
3. Rate limit di account raggiunto
4. Bug temporaneo Anthropic (si risolve da solo in minuti)
```

### Soluzione Immediata (3 passi)
```
PASSO 1: Cambia modello
  → Da: Opus 4.6  (costoso, limite più veloce)
  → A:  Sonnet 4.6 (stesso Claude, più veloce, meno costoso)
  Il messaggio di errore STESSO suggerisce questo!

PASSO 2: Nuova conversazione
  → Apri una nuova chat in Claude Code Cowork
  → Il contesto si azzera e il 500 sparisce

PASSO 3: Se persiste (raro)
  → Controlla https://status.anthropic.com
  → Aspetta 5-10 minuti
  → Riprova
```

### Prevenzione nel Tuo Workflow
```
• Non usare Opus 4.6 per conversazioni lunghe > 30 messaggi
• Usa Sonnet per la maggior parte dei task
• Usa Opus solo per ragionamento complesso su sessioni fresche
• Imposta /claude clear ogni 20-25 messaggi nelle sessioni lunghe
```

---

## CHECKLIST PRODUZIONE FINALE

```
SICUREZZA:
□ HTTPS terminato da nginx/Caddy
□ Admin interface su localhost only
□ Rate limiting attivo (100 req/min)
□ Credenziali separate per ogni provider
□ Nessun segreto nel codice (solo .env)
□ .env escluso da git (.gitignore ✅)
□ Campi sensibili oscurati nei log

AFFIDABILITÀ:
□ PM2 con autorestart e pm2 save
□ Health check endpoint /health
□ n8n autopilot ogni 2 minuti
□ Log strutturati con request_id
□ Timeout su tutte le chiamate HTTP
□ Retry con backoff esponenziale

BACKUP:
□ Script backup.sh configurato
□ Cron notturno alle 02:00
□ Backup testato (ripristino < 10 min)
□ Ultimi 7 backup mantenuti

OSSERVABILITÀ:
□ Log in automation/logs/
□ Metriche latenza p50/p95 su /metrics
□ Error rate monitorato
□ n8n dashboard per workflow
```

---
*Documento creato 17 Marzo 2026 — VIO 83 AI Orchestra v1.0.0-prod*
