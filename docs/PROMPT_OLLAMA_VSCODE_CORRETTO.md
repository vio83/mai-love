 # PROMPT_OLLAMA_VSCODE — VIO 83 AI ORCHESTRA (CORRETTO)

> Prompt unificato per sessioni Ollama agent in VS Code.
> Allineato al progetto REALE — aggiornato al commit dc4eec3.

---

## Identità progetto

| Campo | Valore |
|---|---|
| **Nome** | VIO 83 AI Orchestra |
| **Path** | `~/Projects/vio83-ai-orchestra` |
| **GitHub** | `https://github.com/vio83/mai-love.git` (branch: `main`) |
| **Utente** | Viorica Porcu (vio83) — Mac: `padronavio` |
| **Licenza** | Dual: Proprietary + AGPL-3.0 |

---

## Stack tecnico REALE

| Layer | Tecnologia | Porta | Entry point |
|---|---|---|---|
| **Frontend** | React 18 + TypeScript + Vite 7 | `5173` | `src/main.tsx` |
| **Backend** | FastAPI + Uvicorn (Python 3.14) | `4000` | `backend/api/server.py` |
| **Desktop** | Tauri 2.0 (Rust) | — | `src-tauri/` |
| **AI locale** | Ollama | `11434` | 6 modelli |
| **Database** | SQLite (embedded) | — | `backend/database/db.py` |

### Modelli Ollama disponibili
- `phi3:mini` — reasoning leggero
- `gemma2:2b` — multiuso veloce
- `qwen2.5:3b` — coding + italiano
- `llama3.2:3b` — chat generale
- `qwen2.5-coder:3b` — coding specialist
- `nomic-embed-text` — embeddings per RAG

---

## Struttura directory

```
vio83-ai-orchestra/
├── src/                    # React 18 + TypeScript frontend
│   ├── App.tsx
│   ├── main.tsx
│   ├── components/         # chat/, settings/, sidebar/, layout/, onboarding/, updater/
│   ├── pages/              # AuthPage, DashboardPage, ChatView, ModelsPage, RagPage...
│   ├── services/           # ai/orchestrator, metrics/
│   ├── stores/             # appStore (Zustand)
│   ├── hooks/              # useI18n
│   ├── i18n/               # internazionalizzazione
│   ├── runtime/            # runtimeAutopilot
│   └── types/              # index.ts (Message, Conversation, etc.)
├── backend/                # FastAPI Python
│   ├── api/                # server.py (2400+ righe), websocket_stream.py
│   ├── core/               # jet_engine, security, cache, tracing, vector_engine...
│   ├── orchestrator/       # direct_router, router, parallel_race, system_prompt...
│   ├── openclaw/           # agent.py (tool calling)
│   ├── rag/                # engine, ingestion, search, knowledge_base...
│   ├── database/           # db.py, migrations.py
│   ├── models/             # schemas.py
│   ├── plugins/            # registry.py
│   ├── automation/         # autonomous_runtime, seo_engine, sponsor_growth...
│   ├── config/             # providers.py, performance_max.py
│   ├── utils/
│   └── virtualpartner/     # bridge.py
├── src-tauri/              # Tauri 2.0 desktop (Rust)
│   ├── Cargo.toml
│   └── tauri.conf.json
├── tests/                  # test suite
├── scripts/                # maintenance, nuke-failed-runs, generate_spec...
├── automation/             # circuit breaker, logs
├── docs/                   # documentazione
├── data/                   # logs, dati runtime
├── vio-tasks/              # task tracking tra sessioni
├── public/                 # asset statici
├── venv/                   # Python virtual environment
├── node_modules/           # dipendenze Node
├── CLAUDE.md               # istruzioni continuità sessioni Claude
├── package.json            # config npm + Vite + Vitest
├── pyproject.toml          # config Python
├── requirements.txt        # dipendenze Python
├── .gitignore
└── .vscode/                # settings, extensions, launch configs
```

---

## Comandi operativi

### Avvio servizi
```bash
# Backend FastAPI
cd ~/Projects/vio83-ai-orchestra
source venv/bin/activate
uvicorn backend.api.server:app --host 0.0.0.0 --port 4000 --reload

# Frontend Vite
npm run dev          # → http://localhost:5173

# Ollama (se non auto-started)
ollama serve

# Tauri dev
npm run tauri dev
```

### Verifiche codice (pre-push gates)
```bash
# TypeScript — ZERO errori obbligatorio
npx tsc --noEmit

# Python — ZERO errori obbligatorio
find backend/ -name "*.py" -exec python3 -m py_compile {} \;

# Flake8 critical
flake8 backend/ --select=E9,F63,F7,F82 --statistics

# Lint frontend
npx eslint src/ --ext .ts,.tsx

# Build completa
npm run build
```

### Health check
```bash
# Backend
curl -s http://localhost:4000/health | python3 -m json.tool

# Ollama
curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data['models']:
    print(f\"  {m['name']}: {m['size']//1024//1024}MB\")
"

# Porte attive
lsof -iTCP:4000,5173,11434 -sTCP:LISTEN -P
```

---

## Regole per l'agente Ollama in VS Code

### Non fare MAI
1. **Non creare directory** `src/frontend`, `src/backend`, `src/desktop` — la struttura è `src/`, `backend/`, `src-tauri/`
2. **Non usare Next.js** — il frontend è React + Vite
3. **Non usare porta 3000 o 8000** — le porte sono 5173 (frontend) e 4000 (backend)
4. **Non creare un nuovo `main.py`** — il server è `backend/api/server.py`
5. **Non inventare dati, test results, o metriche**
6. **Non committare segreti** — API keys solo in `.env`

### Fare SEMPRE
1. **Leggere `CLAUDE.md`** all'inizio della sessione
2. **Verificare TypeScript** dopo ogni modifica a `src/`: `npx tsc --noEmit`
3. **Verificare Python** dopo ogni modifica a `backend/`: `python3 -m py_compile <file>`
4. **Commit atomici** con prefix: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`
5. **Push** dopo ogni gruppo logico di modifiche
6. **Aggiornare `vio-tasks/`** con il progresso

### Protocollo verità
- Se non puoi verificare qualcosa → dichiaralo
- Se non puoi completare → consegna il massimo + indica il delta
- Distingui sempre: fatti verificati vs assunzioni vs raccomandazioni

---

## LaunchAgent attivo

```
com.vio83.orchestra-unified
Script: scripts/vio-orchestra-autostart.sh
Frequenza: login + ogni 10 minuti
Score attuale: 100/100
```

---

## Metriche sistema (snapshot)

| Metrica | Valore |
|---|---|
| Disco libero | 14 GB / 228 GB |
| Node | v24.13.0 |
| Python | 3.14.3 |
| npm | 11.6.2 |
| Modelli Ollama | 6 |
| Backend uptime | 24h+ |
| Git commit | `dc4eec3` |
| Pre-push gates | 8/8 pass |
| TypeScript errors | 0 |
| Python errors | 0 |
