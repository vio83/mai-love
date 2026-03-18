# Guida ai Contributi — VIO 83 AI Orchestra

**Versione:** 1.0.0 | **Data:** 18 Marzo 2026

Grazie per voler contribuire a VIO 83 AI Orchestra! Questo documento descrive il processo per contribuire in modo ordinato e professionale.

---

## Indice

1. [Codice di Condotta](#codice-di-condotta)
2. [Come contribuire](#come-contribuire)
3. [Setup ambiente di sviluppo](#setup-ambiente-di-sviluppo)
4. [Struttura del progetto](#struttura-del-progetto)
5. [Standard di codice](#standard-di-codice)
6. [Testing](#testing)
7. [Pull Request](#pull-request)
8. [Versioning e CHANGELOG](#versioning-e-changelog)

---

## Codice di Condotta

Questo progetto adotta il [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). In sintesi:

- Usa un linguaggio inclusivo e rispettoso
- Accetta critiche costruttive con apertura
- Concentrati su ciò che è meglio per la community
- Segnala comportamenti inaccettabili a: **porcu.v.83@gmail.com**

---

## Come contribuire

### Bug report

1. Verifica che il bug non sia già segnalato nelle [Issues](https://github.com/vio83/vio83-ai-orchestra/issues)
2. Apri una nuova Issue con il template **Bug Report**
3. Includi: versione app, OS, passi per riprodurre, comportamento atteso vs osservato, log rilevanti

### Feature request

1. Controlla che la feature non sia già proposta o in sviluppo
2. Apri una Issue con il template **Feature Request**
3. Descrivi il problema che la feature risolve (non solo "cosa vuoi")

### Vulnerabilità di sicurezza

**NON aprire una Issue pubblica.** Vedi [SECURITY.md](SECURITY.md).

---

## Setup ambiente di sviluppo

### Prerequisiti

| Tool | Versione minima | Note |
|------|----------------|-------|
| Node.js | 20.x LTS | frontend React + Tauri |
| Python | 3.11+ | backend FastAPI |
| Rust | stable (1.75+) | Tauri 2.0 |
| Ollama | 0.3.x | modelli locali (opzionale) |

### Installazione

```bash
# 1. Fork + clone
git clone https://github.com/TUO-USERNAME/vio83-ai-orchestra.git
cd vio83-ai-orchestra

# 2. Frontend
npm install

# 3. Backend Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Copia configurazione
cp .env.example .env
# Edita .env con le tue API key (opzionale per sviluppo locale)

# 5. Avvia in sviluppo
npm run tauri dev        # frontend + Tauri
# In altro terminale:
uvicorn backend.server:app --reload --port 4000
```

### Struttura del progetto

```
vio83-ai-orchestra/
├── src/                    # Frontend React + TypeScript
│   ├── components/         # Componenti riutilizzabili
│   ├── pages/              # Pagine (DashboardPage, ChatView, etc.)
│   ├── stores/             # Zustand state management
│   ├── i18n/               # Internazionalizzazione (IT + EN)
│   └── styles/             # CSS temi VIO Dark
├── backend/                # FastAPI Python
│   ├── server.py           # Entry point + endpoint
│   ├── orchestrator/       # Routing intelligente multi-provider
│   ├── core/               # Cache, metriche, knowledge base
│   └── auth/               # Validazione API keys
├── tests/
│   ├── backend/            # Test pytest (52+ unit test)
│   └── e2e/                # Test E2E Playwright
├── docs/                   # Documentazione
├── scripts/                # Script manutenzione
└── src-tauri/              # Configurazione Tauri/Rust
```

---

## Standard di codice

### TypeScript / React

```bash
# Linting
npm run lint

# Formatting (Prettier)
npm run format

# Type check
npm run typecheck
```

Regole principali:
- Componenti: `PascalCase`, file `.tsx`
- Hook custom: `useXxx`, file `use-xxx.ts`
- Stores Zustand: `use<Name>Store`
- Evita `any` — usa tipi espliciti o `unknown`
- Preferisci `const` a `let`, mai `var`

### Python / FastAPI

```bash
# Formatting
black backend/ tests/

# Linting
ruff check backend/ tests/

# Type check
mypy backend/
```

Regole principali:
- PEP 8 + Black formatting (line length 100)
- Type hints su tutte le funzioni pubbliche
- Docstring Google-style per funzioni complesse
- Pydantic v2 per tutti i modelli request/response

### Commit messages

Formato: [Conventional Commits](https://www.conventionalcommits.org/)

```
<tipo>(<scope>): <descrizione breve in italiano o inglese>

[corpo opzionale]

[footer opzionale: BREAKING CHANGE, Closes #issue]
```

Tipi: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`

Esempi:
```
feat(router): aggiunge supporto provider xAI Grok
fix(cache): fallback /tmp su filesystem VirtioFS
docs(api): aggiorna riferimenti endpoint /orchestration
test(backend): aggiungi test integrazione provider pool
chore(deps): aggiorna react-i18next a 16.3.5
```

---

## Testing

### Eseguire i test

```bash
# Backend unit test (pytest)
cd tests/backend
python -m pytest -v

# E2E tests (Playwright)
npm run test:e2e

# Solo backend test rapidi
python -m pytest tests/backend/ -v --tb=short
```

### Requisiti per il merge

- ✅ Tutti i test esistenti devono passare
- ✅ I nuovi feature devono avere copertura test ≥ 80%
- ✅ Nessun errore TypeScript (`npm run typecheck`)
- ✅ Nessun errore linting (`npm run lint`, `ruff check backend/`)

### Aggiungere test

Test backend in `tests/backend/test_<modulo>.py`:

```python
import pytest
from backend.modulo import funzione

def test_descrizione_comportamento():
    # Arrange
    input_data = ...
    # Act
    result = funzione(input_data)
    # Assert
    assert result == expected
```

---

## Pull Request

### Processo

1. Crea un branch da `main`:
   ```bash
   git checkout -b feat/nome-feature
   # oppure
   git checkout -b fix/descrizione-bug
   ```

2. Sviluppa e committa con messaggi Conventional Commits

3. Prima di aprire la PR:
   ```bash
   npm run lint && npm run typecheck
   python -m pytest tests/backend/ -v
   ```

4. Apri la PR su GitHub con:
   - Titolo chiaro (stesso formato commit)
   - Descrizione: cosa cambia, perché, come testarlo
   - Screenshot per cambiamenti UI
   - Link all'Issue correlata (se esiste)

5. Aspetta la review — rispondi ai commenti in modo costruttivo

### Review checklist

Il maintainer verificherà:
- [ ] Funzionalità funziona come descritto
- [ ] Test presenti e passanti
- [ ] Nessuna regressione su test esistenti
- [ ] Codice leggibile e ben commentato dove necessario
- [ ] CHANGELOG.md aggiornato (per feature significative)
- [ ] Documentazione aggiornata se necessario

---

## Versioning e CHANGELOG

Usiamo [Semantic Versioning](https://semver.org/lang/it/):

- `MAJOR.MINOR.PATCH`
- **MAJOR**: breaking changes
- **MINOR**: nuove feature retrocompatibili
- **PATCH**: bug fix

Il CHANGELOG.md viene aggiornato dal maintainer ad ogni release.
I contribuenti sono citati nel CHANGELOG come `grazie a @username`.

---

## Contatti

- **Maintainer:** Viorica Porcu — porcu.v.83@gmail.com
- **GitHub:** https://github.com/vio83
- **Repository:** https://github.com/vio83/vio83-ai-orchestra

Grazie per contribuire! 🎶
