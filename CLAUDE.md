# VIO AI Orchestra — Istruzioni Master Claude

## Identità progetto

- Utente: Viorica Porcu (vio83)
- Mac: MacBook Air M1, username padronavio
- GitHub: <https://github.com/vio83> (repo: mai-love)
- Email: <porcu.v.83@gmail.com>

## Architettura sistema (verificata 25/03/2026)

- Frontend: React 18 + TypeScript + Vite 6 → porta 5173
- Backend: FastAPI + Uvicorn (Python >=3.12, dev 3.14.3) → porta 4000
- AI locale: Ollama → porta 11434 (6 modelli: qwen2.5-coder:3b, llama3.2:3b, qwen2.5:3b, gemma2:2b, phi3:mini, nomic-embed-text)
- Desktop: Tauri 2.0 (Rust) — build nativo macOS
- DB: SQLite (conversazioni + FTS5 + vector engine custom)
- Path locale: /Users/padronavio/Projects/vio83-ai-orchestra

## Metriche codebase

- ~53.000 LOC su 114 file sorgente
- 80 file Python backend, 34 file TS/TSX frontend
- 28 moduli core, 12 plugin (30 tool), 139 endpoint REST
- 410 test automatizzati (pytest, 100% pass)
- 10 provider cloud: Claude, GPT-4, Grok, Gemini, Mistral, DeepSeek, Groq, OpenRouter, Together, Perplexity
- 9 motori core: Direct Router, JetEngine, SelfOptimizer, AutoLearner, ReasoningEngine, WorldKnowledge, FeatherMemory, HyperCompressor, VectorEngine

## Comandi

```bash
./orchestra.sh          # Avvia tutto
npm run dev             # Frontend dev → 5173
PYTHONPATH=. python3 -m uvicorn backend.api.server:app --reload --port 4000  # Backend
npx tsc --noEmit        # TypeScript check
python3 -m pytest tests/backend/ -q   # Test backend
flake8 backend/ --select=E9,F63,F7,F82,F401,F841,F541 --max-line-length=120 --exclude=backend/__pycache__,backend/rag/
```

## Task attivi

Vedi cartella: vio-tasks/

## Regole comportamento

1. Leggi sempre CLAUDE.md e vio-tasks/ all'inizio di ogni sessione
2. Git commit + push dopo ogni modifica completata
3. Zero TypeScript errors (npx tsc --noEmit)
4. Zero Python syntax errors (py_compile + flake8)
5. API keys solo in .env, MAI in source
6. Commit atomici: feat:|fix:|chore:|refactor:|docs:

## Dispositivi sincronizzati

- Mac: Claude Desktop Cowork (task lunghi e complessi)
- VS Code: Copilot Chat (sviluppo in-IDE)
- Web: claude.ai Progetti (consultazione e pianificazione)

## Ultimo aggiornamento

25/03/2026 07:05 — Sync post-fix CI + ottimizzazione ambienti
