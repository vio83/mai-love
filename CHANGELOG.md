# Changelog — VIO 83 AI Orchestra

Tutte le modifiche notevoli sono documentate in questo file.
Formato basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/).
Versioning: [Semantic Versioning](https://semver.org/lang/it/).

---

## [0.9.0-beta] — 2026-03-18

### Aggiunto
- **OnboardingWizard** — guida step-by-step alla prima configurazione (scelta modalità, API key, test, prima chat)
- **React ErrorBoundary globale** — crash recovery con error ID univoco, stack trace in DEV mode
- **i18n foundation** — react-i18next con traduzione completa IT + EN, auto-detect lingua browser
- **Privacy Policy** — GDPR-compliant, docs/PRIVACY_POLICY.md
- **Terms of Service** — docs/TERMS_OF_SERVICE.md
- **GETTING_STARTED.md** — documentazione utente completa (installazione, setup, troubleshooting)
- **DB maintenance script** — scripts/db-maintenance.sh (vacuum, rotazione, WAL checkpoint)
- **Mac autopilot** — 4 LaunchAgents macOS + n8n workflows per manutenzione automatica
- **requirements-rag.txt** — dipendenze RAG separate (chromadb, sentence-transformers per Python ≤3.13)
- **49 nuovi test backend** — test_security, test_errors, test_schemas, test_router, test_providers

### Corretto
- `server.py` — versione allineata da `0.2.0` a `0.9.0`
- `Cargo.toml` — metadati reali (autore, licenza AGPL-3.0, repository)
- `tauri.conf.json` — versione allineata a `0.9.0`
- `direct_router.py` — `trust_env=False` su tutti i `httpx.AsyncClient` (fix SOCKS proxy warning al boot)
- `cache.py` — fallback automatico a `/tmp` quando il filesystem non supporta SQLite locking (es. VirtioFS)
- `App.tsx` — `OnboardingWizard.onComplete` correttamente collega a `updateSettings({ onboardingCompleted: true })`
- `App.tsx` — aggiunta 404 fallback page (era `default: return <ChatView />`)

### Migliorato
- `requirements.txt` — chromadb + sentence-transformers con marker `python_version < "3.14"`
- `package.json` — aggiunto react-i18next, i18next, i18next-browser-languagedetector

---

## [0.8.0-beta] — 2026-03-16

### Aggiunto
- Autonomous Runtime con heartbeat e cron self-management
- OrchestraRuntimePage — pannello di monitoraggio runtime a 360°
- CrossCheckPage — verifica incrociata tra modelli AI
- WorkflowPage — workflow builder con nodi drag-and-drop
- AnalyticsPage — metriche di utilizzo con grafici
- Sistema di metriche SQLite (`log_metric`, `get_metrics_summary`)
- Orchestration profile endpoint (`/orchestration/profile`)
- Provider pool con connection pooling e circuit breaker
- Multi-layer cache L1 (memory LRU) + L2 (SQLite disk)
- SEO Engine per contenuti automatici
- Universal AI Updater — aggiornamento modelli automatico

### Corretto
- Ollama fallback chain (6 modelli in ordine di preferenza)
- SOCKS proxy warning al boot (parziale — completato in v0.9.0)

---

## [0.7.0-beta] — 2026-03-10

### Aggiunto
- Knowledge Base v2 con SQLite FTS5 (fallback senza chromadb)
- RagPage — interfaccia per caricare e interrogare documenti
- Sistema di ingestion PDF/DOCX (pypdf + python-docx)
- Advanced compression per knowledge base
- NLP engine per preprocessing testo
- Mac Auto-Distiller — indicizzazione automatica documenti Mac

---

## [0.6.0-beta] — 2026-03-05

### Aggiunto
- Sistema di autenticazione API keys (APIKeyVault) con regex validation per 9 provider
- Error handling strutturato — ErrorCode (1xxx provider, 2xxx network, 3xxx database, 9xxx system)
- EnvironmentValidator — validazione dipendenze al boot
- ModelsPage — gestione modelli Ollama con download in-app
- Ollama model sync daemon

---

## [0.5.0-beta] — 2026-02-28

### Aggiunto
- Streaming SSE (Server-Sent Events) per risposte in tempo reale
- Conversazioni persistenti in SQLite (`data/vio83_orchestra.db`)
- DashboardPage con statistiche real-time
- SettingsPanel con gestione completa configurazione
- GitHub Actions CI/CD pipeline

---

## [0.4.0-beta] — 2026-02-24

### Aggiunto
- Intent-based routing — 11 categorie (code, legal, medical, creative, reasoning, analysis, writing, automation, realtime, research, conversation)
- Provider routing map (code→claude, research→perplexity, creative→gpt4, realtime→grok)
- Token budget scaling (normale vs deep mode)
- Rate limiting — 30 req/min per IP su `/chat`

---

## [0.3.0-alpha] — 2026-02-22

### Aggiunto
- FastAPI backend con Pydantic v2 validation
- Chat endpoint con supporto multi-provider
- Direct router Ollama (senza LiteLLM — compatibile Python 3.14)
- 9 provider cloud configurati (Anthropic, OpenAI, Gemini, Mistral, DeepSeek, Groq, Together, OpenRouter, xAI)

---

## [0.2.0-alpha] — 2026-02-20

### Aggiunto
- React frontend con Tauri 2.0 desktop wrapper
- Zustand state management
- ChatView + ChatInput + ChatMessage components
- Sidebar navigation
- VIO Dark theme CSS

---

## [0.1.0-alpha] — 2026-02-19

### Iniziale
- Prima commit del progetto
- Struttura base: Tauri 2.0 + React 18 + TypeScript + FastAPI + SQLite
- GitHub repository: https://github.com/vio83/vio83-ai-orchestra
