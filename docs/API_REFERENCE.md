# API Reference — VIO 83 AI Orchestra

**Versione:** 0.9.0 | **Base URL:** `http://127.0.0.1:4000` | **Data:** 18 Marzo 2026

Il backend FastAPI è accessibile **solo da localhost** per ragioni di sicurezza.
Tutti gli endpoint restituiscono JSON. Gli errori seguono lo schema `ErrorResponse`.

---

## Autenticazione Admin

Alcuni endpoint distruttivi richiedono il PIN admin (se configurato nel `.env`):

```
VIO_ADMIN_PIN=il-tuo-pin-segreto
```

Header richiesto:
```
x-vio-admin-pin: il-tuo-pin-segreto
```

Se `VIO_ADMIN_PIN` non è impostato, gli endpoint admin funzionano senza autenticazione (uso locale).

---

## Rate Limiting

- `/chat` e `/chat/stream`: **30 richieste/minuto per IP** (finestra scorrevole 60s)
- Risposta su limite: `HTTP 429` + header `Retry-After: 60`

---

## Schema comune di errore

```json
{
  "error": "Descrizione errore",
  "detail": "Dettaglio opzionale",
  "code": 422
}
```

Codici errore interni:
- `1xxx` — errori provider AI
- `2xxx` — errori di rete
- `3xxx` — errori database
- `9xxx` — errori di sistema

---

## Endpoints

### Health

#### `GET /health`

Stato del sistema completo.

**Risposta 200:**
```json
{
  "status": "ok",
  "version": "0.9.0",
  "uptime_seconds": 3600.5,
  "mode": "local",
  "ollama_available": true,
  "ollama_model": "qwen2.5-coder:3b",
  "cloud_providers_configured": 2,
  "cache_status": "active",
  "kb_available": true,
  "rate_limit_chat": 30
}
```

---

### Auth

#### `GET /auth/status`

Stato chiavi API configurate.

**Risposta 200:**
```json
{
  "providers_configured": ["claude", "groq"],
  "providers_valid": ["groq"],
  "ollama_available": true
}
```

---

### Chat

#### `POST /chat`

Chat non-streaming — risposta completa in un'unica chiamata.

**Rate limited:** 30 req/min

**Request body:**
```json
{
  "message": "Spiega la teoria della relatività",
  "conversation_id": "conv_abc123",
  "provider": "auto",
  "model": null,
  "deep_mode": false,
  "system_prompt": null
}
```

| Campo | Tipo | Obbligatorio | Default |
|-------|------|-------------|---------|
| `message` | string | ✅ Sì | — |
| `conversation_id` | string | No | auto-generato |
| `provider` | string | No | `"auto"` |
| `model` | string | No | `null` (usa default provider) |
| `deep_mode` | boolean | No | `false` |
| `system_prompt` | string | No | `null` |

**Provider validi:** `auto`, `ollama`, `claude`, `openai`, `gemini`, `groq`, `mistral`, `deepseek`, `grok`, `openrouter`, `together`, `perplexity`

**Risposta 200:**
```json
{
  "response": "La teoria della relatività...",
  "provider": "groq",
  "model": "llama3-70b-8192",
  "intent": "reasoning",
  "conversation_id": "conv_abc123",
  "tokens_used": 342,
  "latency_ms": 1250.3,
  "cached": false
}
```

**Errori:**
- `400` — messaggio vuoto o provider non valido
- `429` — rate limit superato
- `503` — nessun provider disponibile

---

#### `POST /chat/stream`

Chat streaming via **Server-Sent Events (SSE)**.

**Rate limited:** 30 req/min

**Request body:** identico a `POST /chat`

**Response:** `Content-Type: text/event-stream`

```
data: {"chunk": "La teoria", "done": false}
data: {"chunk": " della", "done": false}
data: {"chunk": " relatività...", "done": false}
data: {"chunk": "", "done": true, "provider": "groq", "latency_ms": 980.2}
```

Ogni evento SSE è una riga `data: <json>\n\n`.
Il campo `done: true` nell'ultimo evento indica il completamento.

---

### Conversazioni

#### `GET /conversations`

Lista tutte le conversazioni.

**Query params:**
- `limit` (int, default: 50) — numero max di risultati
- `offset` (int, default: 0) — paginazione

**Risposta 200:**
```json
[
  {
    "id": "conv_abc123",
    "title": "Teoria della relatività",
    "created_at": 1742300000,
    "updated_at": 1742301000,
    "message_count": 4,
    "archived": false
  }
]
```

---

#### `POST /conversations`

Crea nuova conversazione.

**Request body:**
```json
{
  "title": "Nuova conversazione"
}
```

**Risposta 201:**
```json
{
  "id": "conv_xyz789",
  "title": "Nuova conversazione",
  "created_at": 1742300000
}
```

---

#### `GET /conversations/{conv_id}`

Dettaglio conversazione con messaggi.

**Risposta 200:**
```json
{
  "id": "conv_abc123",
  "title": "Teoria della relatività",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "Spiega la teoria della relatività",
      "timestamp": 1742300000
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "La teoria della relatività...",
      "timestamp": 1742300100,
      "provider": "groq",
      "model": "llama3-70b-8192"
    }
  ]
}
```

---

#### `PUT /conversations/{conv_id}/title`

Rinomina conversazione.

**Request body:**
```json
{
  "title": "Nuovo titolo"
}
```

**Risposta 200:** `{ "ok": true }`

---

#### `DELETE /conversations/{conv_id}`

Elimina conversazione. **Richiede admin PIN se configurato.**

**Risposta 200:** `{ "ok": true }`

---

#### `POST /conversations/{conv_id}/archive`

Archivia/ripristina conversazione.

**Risposta 200:** `{ "ok": true, "archived": true }`

---

### Classificazione Intent

#### `POST /classify`

Classifica l'intent di un messaggio senza eseguire la chat.

**Request body:**
```json
{
  "message": "Scrivi una funzione Python per ordinare una lista"
}
```

**Risposta 200:**
```json
{
  "intent": "code",
  "confidence": 0.95,
  "suggested_provider": "claude",
  "categories": ["code", "reasoning"]
}
```

**Intent disponibili:** `code`, `legal`, `medical`, `creative`, `reasoning`, `analysis`, `writing`, `automation`, `realtime`, `research`, `conversation`

---

### Ollama

#### `GET /ollama/status`

Stato del daemon Ollama locale.

**Risposta 200:**
```json
{
  "available": true,
  "version": "0.3.12",
  "models_loaded": ["qwen2.5-coder:3b", "llama3.2:3b"]
}
```

---

#### `GET /ollama/models`

Lista modelli Ollama installati.

**Risposta 200:**
```json
{
  "models": [
    {
      "name": "qwen2.5-coder:3b",
      "size_gb": 2.3,
      "modified": "2026-03-10T12:00:00Z"
    }
  ]
}
```

---

### Provider

#### `GET /providers`

Lista tutti i provider configurati e disponibili.

**Risposta 200:**
```json
{
  "cloud": ["claude", "groq", "openai"],
  "local": ["ollama"],
  "available": ["groq", "ollama"],
  "free_tier": ["groq", "openrouter"],
  "recommended": "groq"
}
```

---

### Orchestration

#### `GET /orchestration/profile`

Profilo di orchestrazione attivo.

#### `PUT /orchestration/profile` ⚙️ Admin

Aggiorna profilo di orchestrazione.

**Request body:**
```json
{
  "mode": "cloud",
  "primary_provider": "claude",
  "fallback_providers": ["groq", "ollama"],
  "auto_routing": true
}
```

#### `GET /orchestration/elite-stacks`

Configurazioni elite per task specializzati (legal, medical, code, creative).

---

### Metriche

#### `GET /metrics`

Sommario metriche di utilizzo (ultimi 90 giorni).

**Risposta 200:**
```json
{
  "total_requests": 1250,
  "total_tokens": 450000,
  "avg_latency_ms": 1100.5,
  "provider_breakdown": {
    "groq": 800,
    "ollama": 400,
    "claude": 50
  },
  "intent_breakdown": {
    "code": 400,
    "conversation": 350
  },
  "cache_hit_rate": 0.23
}
```

---

### Settings

#### `GET /settings`

Tutte le impostazioni app salvate nel database locale.

#### `PUT /settings/{key}`

Aggiorna un'impostazione.

**Request body:**
```json
{
  "value": "nuovo_valore"
}
```

---

### Knowledge Base (RAG)

#### `GET /kb/stats`

Statistiche Knowledge Base.

#### `POST /kb/ingest/text`

Aggiungi testo alla Knowledge Base.

**Request body:**
```json
{
  "text": "Contenuto da indicizzare...",
  "title": "Documento esempio",
  "source": "manuale"
}
```

#### `POST /kb/ingest/file`

Aggiungi file (PDF, DOCX, TXT) alla Knowledge Base via path locale.

#### `POST /kb/query`

Query semantica sulla Knowledge Base.

**Request body:**
```json
{
  "query": "Come funziona il rate limiting?",
  "top_k": 5
}
```

---

### Core System

#### `GET /core/cache/stats`

Statistiche cache L1 (memoria) + L2 (SQLite).

#### `POST /core/cache/clear` ⚙️ Admin

Svuota completamente la cache.

#### `POST /core/cache/cleanup` ⚙️ Admin

Pulizia voci cache scadute.

#### `GET /core/network/stats`

Statistiche connection pool per provider.

#### `GET /core/network/health/{provider}`

Health check network per un provider specifico.

#### `GET /core/errors/stats`

Statistiche errori per categoria (1xxx/2xxx/3xxx/9xxx).

#### `GET /core/security/stats`

Statistiche validazione API keys.

#### `GET /core/security/validate`

Validazione chiave API attiva.

#### `GET /core/status`

Stato completo dei moduli core (cache, network, security, errors).

---

## Esempi cURL

```bash
# Health check
curl http://127.0.0.1:4000/health

# Chat semplice
curl -X POST http://127.0.0.1:4000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Ciao, chi sei?"}'

# Chat con provider specifico
curl -X POST http://127.0.0.1:4000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Scrivi un test pytest", "provider": "claude"}'

# Streaming
curl -N -X POST http://127.0.0.1:4000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Racconta una storia breve"}'

# Classifica intent
curl -X POST http://127.0.0.1:4000/classify \
  -H "Content-Type: application/json" \
  -d '{"message": "Analizza questa sentenza penale"}'

# Admin: svuota cache (con PIN)
curl -X POST http://127.0.0.1:4000/core/cache/clear \
  -H "x-vio-admin-pin: tuo-pin"

# Lista conversazioni
curl http://127.0.0.1:4000/conversations

# Elimina conversazione (admin)
curl -X DELETE http://127.0.0.1:4000/conversations/conv_abc123 \
  -H "x-vio-admin-pin: tuo-pin"
```

---

## OpenAPI / Swagger

Con il server in esecuzione, la documentazione interattiva è disponibile su:

- **Swagger UI:** http://127.0.0.1:4000/docs
- **ReDoc:** http://127.0.0.1:4000/redoc
- **OpenAPI JSON:** http://127.0.0.1:4000/openapi.json

---

_Repository: https://github.com/vio83/vio83-ai-orchestra_
_Maintainer: Viorica Porcu — porcu.v.83@gmail.com_
