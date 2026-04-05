# VIO AI ORCHESTRA — Contesto Progetto

## Identità Progetto
- **Nome:** VIO AI Orchestra
- **Autore:** Viorica Porcu (Vio)
- **Repository:** github.com/vio83/vio83-ai-orchestra
- **Licenza:** Dual License — Proprietaria (All Rights Reserved) + AGPL-3.0
- **Stato:** In sviluppo attivo

## Descrizione
VIO AI Orchestra è una piattaforma di orchestrazione AI che unifica provider multipli
(Claude, GPT-4, Gemini, Mistral, DeepSeek, Perplexity) attraverso un'interfaccia singola.
Il sistema permette di inviare prompt a provider diversi simultaneamente, confrontare
risposte, e gestire il routing intelligente delle richieste.

## Stack Tecnologico

### Backend (operativo)
- Runtime: Node.js con Express.js
- Comunicazione real-time: WebSocket
- Process Manager: PM2
- Percorso installazione: /opt/vioaiorchestra/
- Porta: 3000 (HTTP e WebSocket)
- File principale: server.js
- Configurazione: .env (API keys provider)

### Frontend (in sviluppo)
- Framework: React 18+ con Suspense
- Build tool: Vite
- State management: Zustand
- Styling: Tailwind CSS con CSS Variables
- Real-time: WebSocket (gia nel backend)
- Streaming: SSE per risposte AI
- Charts: Recharts (analytics)
- Animation: Framer Motion
- Testing: Vitest + Testing Library
- PWA: Service Worker + Workbox

### Provider AI integrati
1. Claude (Anthropic) — API ufficiale
2. GPT-4 (OpenAI) — API ufficiale
3. Gemini (Google) — API ufficiale
4. Mistral — API ufficiale
5. DeepSeek — API ufficiale + modelli locali via Ollama
6. Perplexity — API ufficiale

### Modelli locali (via Ollama su MacBook Air M1)
- DeepSeek R1 (8B)
- Mistral (7B)
- Altri modelli compatibili con architettura ARM64

## Endpoints API

| Endpoint | Metodo | Funzione |
|----------|--------|----------|
| /health | GET | Health check |
| /api/providers | GET | Lista provider AI |
| /api/chat | POST | Invia messaggio |
| /api/compare | POST | Confronta provider |

## Ambiente di Sviluppo
- Macchina principale: MacBook Air M1 (macOS)
- Macchina secondaria: iMac 2009 (iMac11,1) — in fase di setup con Kali Linux
- Editor: VS Code con estensioni AI (Copilot, Tabnine, Continue.dev)
- Versioning: Git + GitHub
- Device mobile: iPhone 15 (per accesso remoto e testing)

## Comandi di gestione server

```bash
# Avviare il server
cd /opt/vioaiorchestra && pm2 start server.js --name vioaiorchestra

# Riavviare
pm2 restart vioaiorchestra

# Log
pm2 logs vioaiorchestra

# Stato
pm2 status
```

## Sponsorship
- Ko-fi: ko-fi.com/vio83_ai_orchestra_
- GitHub Sponsors: github.com/sponsors/vio83
- Obiettivo: 30 Founding Sponsors

## Roadmap 2026

### Aprile-Giugno: Architettura frontend stabile
- React 18+, Vite, Zustand, Tailwind CSS
- Interfaccia unificata multi-provider operativa
- Streaming parallelo delle risposte

### Luglio-Settembre: Connettori AI completi
- Tutti i provider integrati e testati
- Sistema di caching intelligente
- Analytics di utilizzo

### Ottobre-Dicembre: Versione pubblica beta
- Deployment pubblico
- Documentazione completa
- Community GitHub attiva
- Licenza AGPL-3.0 per versione open source

## Task attivi

### TASK-01: Ottimizzazione ambiente Mac
- Setup completo VS Code con estensioni AI
- Configurazione Git e GitHub SSH
- Ambiente Python venv per SDK AI

### TASK-02: Sviluppo VIO AI Orchestra
- Completare frontend React
- Integrare tutti i provider API
- Testing e ottimizzazione performance

### TASK-03: Privacy e Sicurezza
- Configurazione rete sicura
- Gestione API keys con dotenv
- Protezione IP del progetto

## Note operative
- Il server Express gira su porta 3000 gestito da PM2
- Le API keys sono in /opt/vioaiorchestra/.env
- Il frontend va costruito in /opt/vioaiorchestra/public/ o in directory separata
- Ogni modifica deve essere committata su GitHub
- Workflow: modifica locale, test, git add, commit, push
