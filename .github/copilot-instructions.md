# VIO 83 AI Orchestra — GitHub Copilot Instructions

> Progetto di Viorica Porcu (vio83). Desktop AI orchestration platform.
> Path locale: `/Users/padronavio/Projects/vio83-ai-orchestra`
> GitHub: https://github.com/vio83/vio83-ai-orchestra

---

## Architettura

```
Frontend:  React 18 + TypeScript + Vite 7 → porta 5173
Backend:   FastAPI (Python 3.14) + Uvicorn  → porta 4000
Local AI:  Ollama                           → porta 11434
Desktop:   Tauri 2.0 (Rust) — per build desktop
DB:        SQLite (conversazioni), ChromaDB (vettori, opzionale)
```

### Struttura directory chiave
```
src/           React frontend (TypeScript)
backend/       FastAPI server Python
  api/         server.py — entry point
  config/      providers.py — configurazione AI providers
  core/        cache, network, parallel, errors, security
  database/    db.py — SQLite + conversazioni
  models/      schemas.py — Pydantic models
  orchestrator/ direct_router.py — routing AI
  rag/         Knowledge base (disabilitato su Python 3.14)
src-tauri/     Rust/Tauri — build desktop app
docs/          Documentazione e profili LinkedIn
automation/    n8n workflows
```

---

## Comandi principali

```bash
# Avvia TUTTO (frontend + backend + ollama + browser)
./orchestra.sh

# Solo frontend
npm run dev           # http://localhost:5173

# Solo backend
cd /Users/padronavio/Projects/vio83-ai-orchestra
PYTHONPATH=. python3 -m uvicorn backend.api.server:app --reload --port 4000

# Status servizi
./orchestra.sh status

# Ferma tutto
./orchestra.sh stop

# Build produzione
npm run build

# Build Tauri desktop
npx tauri build
```

---

## Convenzioni codice

- **TypeScript**: strict mode, no `any` salvo casi eccezionali
- **Python**: type hints sempre, Pydantic per tutti i modelli API
- **Imports Python**: da `backend.` prefix (PYTHONPATH=project root)
- **API endpoints**: tutti in `backend/api/server.py`
- **Providers AI**: configurazione in `backend/config/providers.py`
- **Schema Pydantic**: in `backend/models/schemas.py`
- **React components**: in `src/` con Zustand per stato globale
- **Stile UI**: Framer Motion per animazioni, Tailwind per CSS

---

## Note critiche

- **RAG disabilitato**: ChromaDB non compatibile con Python 3.14. Usare SQLite FTS5 come fallback.
- **Ollama**: 7 modelli locali installati (deepseek-r1, llama3, codellama, mistral, gemma2, llama3.2, qwen2.5-coder)
- **Cloud providers**: richiedono API keys nel file `.env` (non committare!)
- **CORS**: configurato per localhost:5173 e localhost:4000
- **Database**: SQLite in `data/` — non eliminare mai

---

## Provider AI configurati

| Provider | Tipo | Costo | Stato |
|----------|------|-------|-------|
| Ollama | Locale | Gratis | ✅ Attivo |
| Groq | Cloud | Gratis | Richiede GROQ_API_KEY |
| OpenRouter | Cloud | Gratis/Paid | Richiede OPENROUTER_API_KEY |
| DeepSeek | Cloud | Economico | Richiede DEEPSEEK_API_KEY |
| Mistral | Cloud | Economico | Richiede MISTRAL_API_KEY |
| Claude | Cloud | Standard | Richiede ANTHROPIC_API_KEY |
| GPT-4 | Cloud | Standard | Richiede OPENAI_API_KEY |
| Grok | Cloud | Standard | Richiede XAI_API_KEY |
| Gemini | Cloud | Standard | Richiede GEMINI_API_KEY |

---

## Git workflow

```bash
git pull                          # Prima di iniziare
git add -A && git commit -m "..."  # Dopo ogni feature
git push                          # Push immediato
```

Regola: commit atomici, messaggi in inglese con prefix `feat:`, `fix:`, `docs:`, `refactor:`.

---

## Contatti progetto
- **Autrice**: Viorica Porcu — porcu.v.83@gmail.com
- **GitHub**: https://github.com/vio83
- **Sponsor**: https://github.com/sponsors/vio83
- **Ko-fi**: https://ko-fi.com/vio83_ai_orchestra_
