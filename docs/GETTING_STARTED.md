# VIO 83 AI Orchestra — Getting Started

> **Versione:** 0.9.0-beta · **Autrice:** Viorica Porcu (vio83) · **Piattaforma:** macOS (Apple Silicon + Intel)

---

## Cos'è VIO 83 AI Orchestra?

VIO 83 AI Orchestra è una **desktop app locale-first** che orchestra intelligentemente più modelli AI — locali e cloud — da un'unica interfaccia. Il tuo Mac esegue i modelli, il tuo backend gestisce le conversazioni, i tuoi dati non lasciano mai il tuo computer senza il tuo consenso esplicito.

In breve:
- **Parli con Claude, GPT-4, Gemini, Mistral, DeepSeek, Perplexity** dallo stesso posto
- **I modelli locali via Ollama** funzionano completamente offline
- **Il router AI** smista ogni domanda al modello più adatto automaticamente
- **La knowledge base** permette di caricare PDF, DOCX e fare ricerche semantiche
- **Dashboard e Analytics** mostrano statistiche di utilizzo in tempo reale

---

## Requisiti di sistema

| Componente | Minimo | Raccomandato |
|------------|--------|--------------|
| macOS | 12 Monterey | 14 Sonoma / 15 Sequoia |
| RAM | 8 GB | 16 GB (per modelli locali 7B+) |
| Spazio disco | 4 GB | 20 GB (con modelli Ollama) |
| Python | 3.11 | 3.12 |
| Node.js | 18 | 20 LTS |
| Rust | 1.75 | latest (per Tauri build) |

---

## Installazione rapida (5 minuti)

### 1. Clona il repository

```bash
git clone https://github.com/vio83/vio83-ai-orchestra.git
cd vio83-ai-orchestra
```

### 2. Installa le dipendenze Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Nota:** Se vuoi abilitare il RAG Engine con ricerca semantica vettoriale (richiede Python 3.11/3.12):
> ```bash
> pip install -r requirements-rag.txt
> ```

### 3. Installa le dipendenze Node.js

```bash
npm install
```

### 4. Configura le API Keys

Crea il file `.env` dalla template:

```bash
cp .env.example .env
```

Poi apri `.env` con un editor di testo e imposta le chiavi che vuoi usare:

```env
# Almeno una delle seguenti chiavi è necessaria per usare modelli cloud
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
MISTRAL_API_KEY=...
DEEPSEEK_API_KEY=...

# Modalità orchestratore (cloud = modelli cloud, local = solo Ollama)
VIO_NO_HYBRID=false
VIO_EXECUTION_PROFILE=real-max-local
```

> **Privacy:** Le chiavi sono lette localmente dal file `.env` e non vengono mai inviate a server esterni se non per autenticarsi con il provider corrispondente.

### 5. (Opzionale) Installa Ollama per i modelli locali

Ollama permette di eseguire modelli AI direttamente sul Mac, senza internet.

```bash
# Installa Ollama
brew install ollama
# oppure scarica da https://ollama.ai

# Avvia il servizio
ollama serve

# In un altro terminale, scarica un modello (es. Llama 3.2 3B, ~2GB)
ollama pull llama3.2:3b

# Per un modello più capace (7B, ~4.7GB)
ollama pull qwen2.5-coder:7b
```

---

## Avvio dell'applicazione

### Modalità sviluppo (backend + frontend separati)

**Terminale 1 — Avvia il backend FastAPI:**
```bash
source .venv/bin/activate
uvicorn backend.api.server:app --host 127.0.0.1 --port 4000 --reload
```

Il backend sarà disponibile su `http://127.0.0.1:4000`
- Interfaccia API Docs: `http://127.0.0.1:4000/docs`
- Health check: `http://127.0.0.1:4000/health`

**Terminale 2 — Avvia il frontend React:**
```bash
npm run dev
```

Il frontend sarà disponibile su `http://localhost:1420`

### Modalità desktop Tauri (app nativa macOS)

```bash
npm run tauri:dev
```

Questo compila e avvia l'app come finestra nativa macOS. Il backend viene avviato automaticamente.

### Con PM2 (autopilot 24/7)

```bash
# Installa PM2 globalmente
npm install -g pm2

# Avvia tutti i servizi
pm2 start ecosystem.config.cjs

# Verifica stato
pm2 status

# Imposta avvio automatico al boot
pm2 startup
pm2 save
```

---

## Prima chat

Una volta avviata l'app:

1. Apri la sezione **AI Chat** dalla sidebar sinistra
2. Seleziona la modalità in alto a destra: **☁️ Cloud** o **💻 Locale**
3. Scrivi il tuo messaggio e premi **Invio**
4. Il router AI analizzerà la tua richiesta e la invierà al modello più adatto

### Esempi per iniziare

| Cosa vuoi fare | Messaggio di esempio |
|---------------|---------------------|
| Scrivere codice | `Scrivi una funzione Python che ordina una lista per frequenza` |
| Spiegare un concetto | `Spiega la differenza tra RAM e SSD in parole semplici` |
| Revisione legale | `Analizza questa clausola contrattuale GDPR` |
| Aiuto medico | `Quali sono i sintomi del diabete tipo 2?` |
| Scrittura creativa | `Scrivi un haiku sulla tecnologia AI` |

---

## Gestione dei modelli AI

Vai alla sezione **AI Models** per:
- Vedere quali modelli cloud hai configurato (richiede API key valida)
- Vedere i modelli Ollama installati localmente
- Scaricare nuovi modelli Ollama direttamente dall'interfaccia

### Modelli cloud supportati

| Provider | Modello | Chiave necessaria |
|----------|---------|------------------|
| Anthropic | Claude 3.5 Sonnet | `ANTHROPIC_API_KEY` |
| OpenAI | GPT-4o | `OPENAI_API_KEY` |
| Google | Gemini 1.5 Pro | `GEMINI_API_KEY` |
| Mistral | Mistral Large | `MISTRAL_API_KEY` |
| DeepSeek | DeepSeek Chat | `DEEPSEEK_API_KEY` |
| xAI | Grok | `XAI_API_KEY` |
| Groq | Llama 3.1 70B (fast) | `GROQ_API_KEY` |
| Together AI | Mixtral 8x7B | `TOGETHER_API_KEY` |
| OpenRouter | Multi-model | `OPENROUTER_API_KEY` |

---

## Workflow Builder

Il **Workflow Builder** permette di creare pipeline AI multi-step:

1. Apri la sezione **Workflow Builder**
2. Aggiungi nodi trascinando dal pannello a sinistra
3. Collega i nodi con frecce per definire il flusso
4. Esegui il workflow con il pulsante **▶ Esegui**

Esempi di workflow:
- **Ricerca + Sintesi**: cerca informazioni online, poi le sintetizza con Claude
- **Cross-Check**: stessa domanda a 3 modelli diversi, confronta le risposte
- **RAG + Chat**: cerca nella knowledge base, poi risponde in base ai documenti trovati

---

## RAG Knowledge Base

La sezione **RAG Knowledge** permette di caricare documenti e fare ricerche semantiche:

1. Carica un PDF, DOCX o file di testo
2. Il sistema indicizza automaticamente il contenuto
3. Nelle chat successive, usa `@kb` per cercare nella knowledge base

> **Nota:** Il RAG Engine completo con vector search richiede `requirements-rag.txt` e Python 3.11/3.12. La versione base funziona con SQLite FTS5 (incluso in Python).

---

## Risoluzione problemi comuni

### Il backend non si avvia

```bash
# Controlla che la porta 4000 sia libera
lsof -i :4000

# Verifica l'ambiente virtuale Python
source .venv/bin/activate
python3 -c "import fastapi; print(fastapi.__version__)"

# Controlla i log
uvicorn backend.api.server:app --host 127.0.0.1 --port 4000 --log-level debug
```

### Ollama non risponde

```bash
# Verifica che Ollama sia in esecuzione
curl http://localhost:11434/api/tags

# Riavvia il servizio
pkill ollama && ollama serve

# Controlla i modelli installati
ollama list
```

### Errore API Key non valida

1. Vai su **Impostazioni → API Keys**
2. Controlla che la chiave sia nel formato corretto:
   - Anthropic: `sk-ant-api03-...`
   - OpenAI: `sk-...`
   - Groq: `gsk_...`
3. Verifica che la chiave abbia credito disponibile sul dashboard del provider

### Poco spazio su disco

```bash
# Pulizia aggressiva (esegui dallo script dedicato)
bash scripts/mac-free-space-NOW.sh

# Oppure solo per i target Rust (tipicamente 2GB+)
cargo clean
```

### Rate limit superato (429)

L'app limita le richieste a `/chat` a **30 richieste al minuto per IP** per default. Se stai sviluppando e hai bisogno di più, puoi aumentare il limite in `.env`:

```env
VIO_RATE_LIMIT_CHAT_PER_MIN=100
```

---

## Backup e sicurezza

### File importanti da conservare

| File/Cartella | Contenuto | Dove salvarlo |
|---------------|-----------|---------------|
| `.env` | API Keys e configurazione | Password manager o 1Password |
| `data/conversations.db` | Storico conversazioni | iCloud / backup locale |
| `data/knowledge_distilled.db` | Knowledge base | Disco esterno |

### Non committare mai

Il `.gitignore` è già configurato per escludere:
- `.env` (API Keys)
- `data/*.db` (database locali)
- `*.log` (log files)
- `.venv/` (ambiente virtuale)

---

## Aggiornamenti

```bash
# Aggiorna il codice
git pull origin main

# Aggiorna dipendenze Python
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# Aggiorna dipendenze Node
npm install

# Riavvia l'app
pm2 restart all  # se usi PM2
```

---

## Supporto e community

- **Bug reports:** [GitHub Issues](https://github.com/vio83/vio83-ai-orchestra/issues)
- **Discussioni:** [GitHub Discussions](https://github.com/vio83/vio83-ai-orchestra/discussions)
- **Supporta il progetto:** [Ko-fi](https://ko-fi.com/vio83) | [GitHub Sponsors](https://github.com/sponsors/vio83)
- **Email:** porcu.v.83@gmail.com

---

## Licenza

VIO 83 AI Orchestra è distribuito con **doppia licenza**:
- **AGPL-3.0** per uso personale e open source
- **Licenza commerciale proprietaria** per uso commerciale

Per dettagli, consulta i file `LICENSE` e `LICENSE-COMMERCIAL.md`.

---

*VIO 83 AI Orchestra — Fatto con ❤️ da Viorica Porcu in Sardegna, Italia.*
