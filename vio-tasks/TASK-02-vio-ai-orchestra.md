# TASK 02 — VIO AI Orchestra - Sviluppo Continuo

## Obiettivo
Riprendere e continuare lo sviluppo del progetto VIO AI Orchestra.

## Repository
- Percorso locale: /Users/padronavio/Projects/vio83-ai-orchestra
- GitHub: https://github.com/vio83/mai-love
- Sessione precedente: ~/.claude/projects/-Users-padronavio-Projects-vio83-ai-orchestra--claude-worktrees-festive-chatterjee/

## Stack tecnologico
- React 18 + TypeScript + Vite (frontend, porta 5173)
- FastAPI Python 3.14.3 (backend, porta 4000)
- Ollama (AI locale, porta 11434)
- Tauri 2.0 (desktop shell)
- Zustand v8 (state management)
- SQLite (database conversazioni)

## Stato attuale (2026-03-25, commit bc3779c)
### Completati
- CI/CD: 10 workflow GitHub Actions, tutti green
- Cloud streaming SSE: Claude, GPT-4, Grok, Gemini, Mistral, DeepSeek, Groq, Perplexity, OpenRouter, Together
- Extended thinking: Claude reasoning blocks visibili in UI
- JetEngine 5-layer: TurboCache + ComplexityScorer + LocalFirstRouter + StreamGateway + ParallelSprint
- Knowledge Taxonomy: 12 macro-domini, get_optimal_config()
- ModelBar UI: 17 modelli (5 Ollama + 12 cloud) come pill cliccabili
- Frontend rewire backend-first: POST /chat/stream con SSE, fallback diretto
- JetEngine integrato in /chat/stream (cache hit istantaneo + routing)
- Persistenza conversazioni: sync frontend-backend, loadConversationsFromBackend()
- 414 test backend passati, TypeScript 0 errori, build pulita

### Prossimi step (priorita)
1. P3: Settings sync frontend-backend (API keys, config)
2. P4: RAG/Vector Engine riattivazione (disabilitato per incompatibilita chromadb/Python 3.14)
3. P5: WebSocket/SSE unificazione endpoint
4. Tauri build e distribuzione desktop
5. Conversazione multi-turn: sync conversation_id tra frontend e backend
