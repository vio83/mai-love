# VIO 83 AI Orchestra — GitHub Copilot Instructions

> Progetto di Viorica Porcu (vio83). Desktop AI orchestration platform.
> Path locale: `/Users/padronavio/Projects/vio83-ai-orchestra`
> GitHub: https://github.com/vio83/vio83-ai-orchestra

---

## Architettura

```
Frontend:  React 18 + TypeScript + Vite 6 → porta 5173
Backend:   FastAPI (Python >=3.12) + Uvicorn  → porta 4000
Local AI:  Ollama (6 modelli)               → porta 11434
Desktop:   Tauri 2.0 (Rust) — build nativo macOS
DB:        SQLite (conversazioni + FTS5 + VectorEngine custom)
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

- **RAG**: ChromaDB non compatibile con Python 3.14. VectorEngine custom (SQLite + NumPy) come sostituto.
- **Ollama**: 6 modelli locali installati (qwen2.5-coder:3b, llama3.2:3b, qwen2.5:3b, gemma2:2b, phi3:mini, nomic-embed-text)
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

---

## Protocollo di Aderenza Totale 100× — PERMANENTE

> File autoritativo: `.github/instructions/100x-total-adherence-protocol.instructions.md` (applyTo: `**`)
> Questo file è caricato automaticamente da Copilot per tutte le chat, modelli e agenti nel workspace.

**Ogni output di Copilot su questo progetto deve rispettare queste regole in modo permanente e automatico:**

### Mandato operativo
Produci codice gemello al 100% all'obiettivo dichiarato: concreto, verificabile, professionale, zero fronzoli. Se mancano dati, **BLOCCA**, elenca lacune e chiedi solo le 3–5 informazioni indispensabili per chiuderla.

### Criteri non negoziabili
1. **Zero TypeScript errors** — ogni modifica a `src/` deve passare `npx tsc --noEmit`
2. **Zero Python syntax errors** — ogni modifica a `backend/` deve passare `python3 -m py_compile`
3. **Nessun segreto in source** — API keys solo in `.env`, mai in `.py/.ts/.json`
4. **SPONSORS.md sempre pulito** — nessun template raw visibile pubblicamente
5. **Commit atomici** — un commit = una funzionalità o fix con messaggio `feat:|fix:|chore:|refactor:`
6. **KPI tracciabili** — ogni feature impatta almeno 1 metrica misurabile
7. **Auto-maintain attivo** — `scripts/maintenance/auto_maintain.sh` passa sempre

### Struttura output obbligatoria (per task complessi)
- Executive summary ≤ 120 parole
- Sezioni numerate con KPI (valore/unità/target/data)
- Rischi + mitigazioni concrete
- Prossimi passi: chi / cosa / quando (data ISO)
- Checklist di verifica finale ✔/✖

### Truth Policy (non derogabile)
- Non inventare dati, citazioni, link o numeri di performance.
- Se non puoi verificare qualcosa: dichiararlo esplicitamente.
- Requisito ambiguo o conflittuale → BLOCCA → lista lacune → chiedi 3–5 risposte minime → consegna.
- Conflitto tra requisiti → proponi **variante A** e **variante B** con raccomandazione motivata da criteri misurabili.

### Auto-maintenance permanente
- **GitHub Actions**: `auto-maintenance.yml` esegue daily alle 06:00 UTC
- **Locale**: `scripts/maintenance/auto_maintain.sh` (3x/giorno via launchd)
- **Pre-commit hook**: gitlink guard + Python syntax + secrets scan
- **Issue auto-open**: `ci-issue-on-failure.yml` su failure permanente (attempt ≥ 2)
