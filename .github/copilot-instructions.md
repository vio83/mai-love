# Project Guidelines

## Code Style
- TypeScript in `src/` is strict: keep types explicit, avoid `any` unless justified.
- Python in `backend/` uses type hints and Pydantic models for API contracts.
- Python imports use the `backend.` prefix with project-root `PYTHONPATH=.`.
- Keep source code/comments in English; Italian is acceptable in operational docs/scripts.
- Never commit secrets: API keys stay only in `.env`.

## Architecture
- Frontend: React 18 + TypeScript + Vite (`src/`).
- Backend: FastAPI + Uvicorn + Pydantic (`backend/api/server.py`, `backend/models/schemas.py`).
- Orchestration logic: `backend/orchestrator/` and frontend bridge in `src/services/ai/orchestrator.ts`.
- Desktop shell: Tauri 2 (`src-tauri/`).
- Data layer: SQLite for conversations, optional ChromaDB for vector workflows.

## Build And Test
Run from repository root unless noted.

```bash
# Frontend development
npm run dev

# Type and lint gates
npm run typecheck
npm run lint

# Tests
npm run test:frontend
npm run test:backend

# Backend syntax/compile smoke
npm run backend:compile

# Production builds
npm run build
npm run tauri:build

# Full release gate
npm run release:gate

# Unified local launcher
./orchestra.sh
```

## Conventions
- Keep API endpoints centralized in `backend/api/server.py` unless a refactor is explicitly requested.
- Put request/response schema changes in `backend/models/schemas.py` first, then update handlers.
- Reuse existing orchestrator pathways before adding new routing layers.
- Prefer existing UI patterns from `src/components/` and existing state management (Zustand stores).
- Keep changes focused and atomic; avoid unrelated refactors in the same patch.

## Pitfalls
- Required runtimes: Node >= 20, npm >= 10, Python >= 3.12.
- Repository contains multiple virtual environments (`.venv`, `.venv-1`, `venv`): prefer one active env consistently per session.
- ChromaDB support may be constrained by Python version; if unavailable, keep SQLite-based fallback behavior intact.
- `orchestra.sh` can include machine-specific assumptions: validate paths and local services before changing startup logic.

## Exemplar Files
- `backend/api/server.py`
- `backend/models/schemas.py`
- `backend/orchestrator/direct_router.py`
- `src/services/ai/orchestrator.ts`
- `src/services/ai/systemPrompt.ts`
- `tests/backend/test_router.py`
- `tests/frontend/orchestrator.test.ts`

## Operating Principle
Apply Protocollo di Aderenza Totale 100x style for delivery quality: concrete, verifiable, professional, and no fluff.
