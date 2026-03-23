<p align="center">
  <img src="https://img.shields.io/badge/VIO_83-AI_ORCHESTRA-00ff00?style=for-the-badge&logo=music&logoColor=black" alt="VIO 83 AI ORCHESTRA" />
</p>

<h1 align="center">🎵 VIO 83 AI ORCHESTRA</h1>

<p align="center">
  <strong>Desktop AI platform — local-first, offline, private</strong><br>
  <em>Ollama routing. Streaming chat. Knowledge base. Tauri desktop app.</em>
</p>

<p align="center">
  <a href="https://github.com/vio83/vio83-ai-orchestra/stargazers"><img src="https://img.shields.io/github/stars/vio83/vio83-ai-orchestra?style=flat-square&color=00ff00" alt="GitHub Stars" /></a>
  <a href="https://github.com/vio83/vio83-ai-orchestra/network/members"><img src="https://img.shields.io/github/forks/vio83/vio83-ai-orchestra?style=flat-square&color=cyan" alt="GitHub Forks" /></a>
  <a href="https://github.com/vio83/vio83-ai-orchestra/issues"><img src="https://img.shields.io/github/issues/vio83/vio83-ai-orchestra?style=flat-square&color=yellow" alt="GitHub Issues" /></a>
  <a href="https://github.com/vio83/vio83-ai-orchestra/blob/main/LICENSE"><img src="https://img.shields.io/github/license/vio83/vio83-ai-orchestra?style=flat-square" alt="License" /></a>
  <a href="https://github.com/vio83/vio83-ai-orchestra/commits/main"><img src="https://img.shields.io/github/last-commit/vio83/vio83-ai-orchestra?style=flat-square&color=00ff00" alt="Last Commit" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Ollama-Local_AI-00ff00?style=flat-square" />
  <img src="https://img.shields.io/badge/Runtime-No--Hybrid_%2F_Local--Only-00ff00?style=flat-square" />
  <img src="https://img.shields.io/badge/Privacy-Zero_Data_Leaves_Mac-00ff00?style=flat-square" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Tauri_2.0-Rust_+_WebView-FFC131?style=flat-square&logo=tauri" />
  <img src="https://img.shields.io/badge/React_18-TypeScript-61DAFB?style=flat-square&logo=react" />
  <img src="https://img.shields.io/badge/FastAPI-Python-009688?style=flat-square&logo=fastapi" />
  <img src="https://img.shields.io/badge/Zustand-State_Management-brown?style=flat-square" />
  <img src="https://img.shields.io/badge/SQLite_FTS5-Knowledge_Base-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/License-Proprietary_+_AGPL--3.0-red?style=flat-square" />
</p>

<p align="center">
  <a href="#-what-it-does">What It Does</a> •
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-local-models">Local Models</a> •
  <a href="#-sponsor-this-project">Sponsor</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## 🎯 What It Does

VIO 83 AI Orchestra is a **local-first desktop AI app** for macOS.

**Runtime policy: no-hybrid / local-only.** All AI calls go to [Ollama](https://ollama.ai) running on your machine. No data leaves your Mac at runtime.

> Cloud API keys (Claude, GPT-4, Gemini, etc.) are configurable in Settings for future cloud mode, but the current runtime enforces Ollama-only routing. Cloud routing is not active.

### What It Includes Today

| Component                                          | Status                                                    |
| -------------------------------------------------- | --------------------------------------------------------- |
| Streaming chat (Ollama)                            | ✅ Active                                                  |
| Smart request routing (local)                      | ✅ Active — classifies code/medical/reasoning/etc.         |
| Cross-check verification (local)                   | ✅ Active — second Ollama model verifies first             |
| Knowledge base (SQLite FTS5)                       | ✅ Active — ChromaDB optional, disabled on Python 3.14     |
| Command Center dashboard                           | ✅ Active — real usage metrics                             |
| AI Models registry                                 | ✅ Active — shows installed Ollama models                  |
| Analytics page                                     | ✅ Active                                                  |
| Tauri 2 desktop shell                              | ✅ Builds on macOS                                         |
| Cloud API routing                                  | ⚠️ Keys configurable, routing locked local-only at runtime |
| **VirtualPartnerAI (emotion/memory/relationship)** | ✅ **NEW** — 4 engines integrated + bridge                 |
| **Stripe Billing Webhooks**                        | ✅ **NEW** — subscription management ready                 |
| **IP Protection Certificate**                      | ✅ **NEW** — prior art timestamps + AGPL-3.0 enforcement   |

---

## ✨ Features

### 🧠 Local AI Routing
The orchestrator classifies each request before calling a model:

- **Code questions** → `qwen2.5-coder:3b` (best local code model)
- **Reasoning / deep analysis** → `deepseek-r1:latest`
- **Legal / medical** → `mistral:latest`
- **General conversation** → configured model (default `llama3.2:3b`)
- **Quick tasks** → `gemma2:2b` or `llama3.2:3b`

### 🔍 Cross-Check Verification
For critical answers, a **second local Ollama model** independently verifies the first response. Both responses are compared for concordance (%). All inference stays on your Mac.

### 📊 Command Center Dashboard
Real-time monitoring of local AI usage — requests per model, token usage, cost ($0.00 for local), latency analysis, and model distribution.

### 📚 Knowledge Base (SQLite FTS5)
Every answer can be checked against a local knowledge base using **SQLite FTS5 full-text search**. ChromaDB/semantic search is optional and disabled on Python 3.14.

Quality badges on every response:
- 🥇 **Gold** — Verified by 3+ sources
- 🥈 **Silver** — Partially corroborated
- 🥉 **Bronze** — Low confidence
- ⚪ **Unverified** — No matching sources found

### 🤖 AI Models Registry
Browse and configure installed Ollama models. Shows quality scores, speed benchmarks, specialties per task type.

### 🔒 Privacy First
- All inference runs locally via Ollama — zero API calls at runtime
- No telemetry, no tracking, no data collection
- API keys stored encrypted (configurable for future cloud mode)
- Open source = fully auditable

### 🎨 Vio Dark Fluorescent Theme
Custom dark theme with Framer Motion animations:
- Pure black background (#000000)
- Fluorescent green accents (#00FF00)
- Magenta (#FF00FF), Cyan (#00FFFF), Yellow (#FFFF00)
- JetBrains Mono for code, Inter for UI

---

## 📸 UI Pages

| Page                 | Description                                                       |
| -------------------- | ----------------------------------------------------------------- |
| 🏠 **Dashboard**      | Command Center with live stats, model distribution, activity feed |
| 💬 **AI Chat**        | Local streaming chat with markdown rendering + cross-check        |
| 🛡️ **Cross-Check**    | Multi-model local verification with concordance scoring           |
| 📈 **Analytics**      | Usage tracking per model                                          |
| 📚 **Knowledge Base** | FTS5 knowledge base manager with quality badges                   |
| 🤖 **AI Models**      | Ollama model registry with benchmarks and configuration           |

---

## 🚀 Quick Start

> **⚡ TL;DR — Start in 3 commands:**
> ```bash
> git clone https://github.com/vio83/vio83-ai-orchestra.git && cd vio83-ai-orchestra
> npm install && pip3 install fastapi uvicorn httpx && ollama pull qwen2.5-coder:3b
> ./orchestra.sh
> ```
> Open **http://localhost:5173** — Orchestra is running. 🎵

### Prerequisites
- **macOS** (Apple Silicon recommended)
- **Node.js** 20+ (`nvm install 20`)
- **Rust** (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
- **Python** 3.11–3.13 (note: ChromaDB is incompatible with Python 3.14)
- **Ollama** (`brew install ollama`)

### Install

```bash
# Clone
git clone https://github.com/vio83/vio83-ai-orchestra.git
cd vio83-ai-orchestra

# Frontend
npm install

# Backend
pip3 install fastapi uvicorn httpx

# Download local models
ollama pull qwen2.5-coder:3b
ollama pull llama3.2:3b
```

### Run

```bash
# Start everything (recommended)
./orchestra.sh

# Or individually:
# Terminal 1: Ollama
ollama serve

# Terminal 2: Backend API
PYTHONPATH=. python3 -m uvicorn backend.api.server:app --reload --port 4000

# Terminal 3: Frontend
npm run dev
```

Open `http://localhost:5173` — your Orchestra is ready. 🎵

### Local Runtime Services Autostart (OpenClaw / LegalRoom / n8n)

To keep Runtime 360 Health panel stable, run the local supervisor and install launchd autostart:

```bash
# 1) Configure real service start commands in .env
#    OPENCLAW_START_CMD=...
#    LEGALROOM_START_CMD=...
#    N8N_START_CMD=... (optional: empty = automatic fallback)

# 2) Start supervisor now
bash scripts/runtime/start_runtime_services.sh

# 3) Install macOS LaunchAgents (login autostart + KeepAlive)
bash install_autostart.sh
```

Logs and state:

- `.logs/runtime-supervisor.log`
- `.logs/runtime-openclaw.log`
- `.logs/runtime-legalroom.log`
- `.logs/runtime-n8n.log`
- `.pids/runtime-supervisor-state.json`

Note: OpenClaw and LegalRoom require real local start commands; no fake health service is used.

---

## 🏗 Architecture

```
USER types a question
        ↓
┌─────────────────────────┐
│  Frontend (React/Tauri)  │  ← Dashboard, Chat, Analytics, Models, KB, Settings
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  Request Classifier      │  ← Classifies: code/medical/legal/reasoning/etc.
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  Local Model Router      │  ← Picks best Ollama model for request type
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  Ollama (local only)     │  ← llama3.2, qwen2.5-coder, deepseek-r1, mistral...
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  Cross-Check (optional)  │  ← Second Ollama model verifies first response
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  KB Verification (FTS5)  │  ← SQLite FTS5 full-text search
└───────────┬─────────────┘
            ↓
   Response + Quality Badge + Analytics Event
            ↓
      USER gets answer — all local, zero cloud calls ✓
```

### Tech Stack

| Layer        | Technology                   | Why                                      |
| ------------ | ---------------------------- | ---------------------------------------- |
| Desktop      | **Tauri 2.0**                | Lightweight native shell vs Electron.    |
| Frontend     | **React 18 + TypeScript**    | Type-safe, fast, large ecosystem.        |
| Styling      | **CSS Variables + Tailwind** | Custom dark theme.                       |
| Animations   | **Framer Motion**            | Smooth page transitions.                 |
| State        | **Zustand**                  | Lightweight persistent store.            |
| Icons        | **Lucide React**             | Tree-shakeable SVG icons.                |
| Local AI     | **Ollama**                   | Run any model locally. Zero cloud calls. |
| Backend      | **FastAPI**                  | Async Python, SSE streaming.             |
| Knowledge DB | **SQLite FTS5**              | Full-text search, no external service.   |
| Bundler      | **Vite 7**                   | Fast HMR, optimized builds.              |

---

## 🤖 Local Models

All inference uses **Ollama** running locally. Pull models with `ollama pull <name>`:

| Model                | Size   | RAM    | Best For                  |
| -------------------- | ------ | ------ | ------------------------- |
| `qwen2.5-coder:3b`   | 2.0 GB | 2.5 GB | Code generation           |
| `llama3.2:3b`        | 2.0 GB | 2.5 GB | General assistant         |
| `mistral:latest`     | 4.1 GB | 5.0 GB | Reasoning, legal, medical |
| `deepseek-r1:latest` | varies | 5+ GB  | Deep reasoning            |
| `gemma2:2b`          | 1.6 GB | 2.0 GB | Ultra-fast responses      |

> Cloud model routing (Claude, GPT-4, Gemini, etc.) is configurable in Settings but **not active at runtime**. Runtime enforces local-only.

---

## 🗺 Roadmap

- [x] **Phase 1** — Core architecture (Tauri + React + TypeScript + Zustand)
- [x] **Phase 2** — AI orchestrator with smart routing + 7 providers
- [x] **Phase 3** — RAG engine with verified sources (ChromaDB + FTS5)
- [x] **Phase 4** — Multi-page UI: Dashboard, Analytics, Workflow, CrossCheck, Models, RAG
- [x] **Phase 5** — Framer Motion animations + Vio Dark Theme
- [ ] **Phase 6** — GitHub Pages landing page + global SEO indexing
- [ ] **Phase 7** — VS Code extension
- [ ] **Phase 8** — iPhone companion app (iCloud sync)
- [ ] **Phase 9** — Marketplace for custom AI workflows
- [ ] **Phase 10** — Enterprise features (team management, SSO)

---

## 💚 Sponsor This Project

Official links:
- GitHub Repo: https://github.com/vio83/vio83-ai-orchestra
- GitHub Sponsors: https://github.com/sponsors/vio83
- Ko-fi: https://ko-fi.com/vio83_ai_orchestra_
- LinkedIn: https://www.linkedin.com/in/viorica-porcu-637735139
- Support Hub: https://vio83.github.io/vio83-ai-orchestra/support.html
- Legal Proof Bundle: https://github.com/vio83/vio83-ai-orchestra/blob/main/docs/LEGAL_PROOF_BUNDLE_2026-03-21.md

<p align="center">
  <a href="https://github.com/sponsors/vio83">
    <img src="https://img.shields.io/badge/GitHub_Sponsors-💚_Become_a_Sponsor-ea4aaa?style=for-the-badge&logo=github-sponsors" />
  </a>
  &nbsp;&nbsp;
  <a href="https://ko-fi.com/vio83_ai_orchestra_">
    <img src="https://img.shields.io/badge/Ko--fi-☕_Support_on_Ko--fi-FF5E5B?style=for-the-badge&logo=ko-fi" />
  </a>
  &nbsp;&nbsp;
  <a href="https://www.linkedin.com/in/viorica-porcu-637735139">
    <img src="https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin" />
  </a>
  &nbsp;&nbsp;
  <a href="https://vio83.github.io/vio83-ai-orchestra/support.html">
    <img src="https://img.shields.io/badge/Support_Hub-🌍_All_Options-8B5CF6?style=for-the-badge" />
  </a>
</p>

### The Story

I'm **Viorica**, a solo developer from Italy building this on a **MacBook Air M1 with 8GB RAM**. No VC funding. No team. No salary. Just pure determination and 16-hour coding sessions.

I'm building VIO 83 because I believe access to intelligent AI should not require 5 separate subscriptions, and that **verified, trustworthy answers** matter more than fast, unverified ones.

### What Your Sponsorship Funds

| Priority              | Need                              | Why It Matters                                |
| --------------------- | --------------------------------- | --------------------------------------------- |
| **#1 Hardware**       | Mac Studio M4 Ultra (192GB)       | Current M1 8GB limits large local models      |
| **#2 Time**           | Full-time development             | More hours = faster features, better quality  |
| **#3 Infrastructure** | Server for the Knowledge Base     | Scaling FTS5/vector index to millions of docs |
| **#4 Optional cloud** | API credits for future cloud mode | Testing optional multi-provider routing       |

### Current Progress (Live — 21 March 2026)

```
Backend Engine:       ████████████████░░░░  85%  (15 modules, all tested)
Frontend UI:          ██████████████░░░░░░  70%  (7 full pages + settings)
Knowledge Base:       ██░░░░░░░░░░░░░░░░░░  10%  (10K docs, target 10M+)
API Connectors:       ████████░░░░░░░░░░░░  40%  (7/11 providers active)
42-Category System:   ████████████████████  100% (1,082 sub-disciplines)
Cross-Check Engine:   ████████████████░░░░  80%  (multi-model concordance)
Visual Workflows:     ████████░░░░░░░░░░░░  40%  (pipeline builder MVP)
Analytics Dashboard:  ████████████████░░░░  80%  (real-time tracking)
```

### Sponsor Tiers

| Tier             | Monthly | What You Get                                           |
| ---------------- | ------- | ------------------------------------------------------ |
| ☕ **Supporter**  | $5      | Name in SPONSORS.md + early access to all releases     |
| 🎵 **Musician**   | $15     | Above + priority on feature requests + private Discord |
| 🎼 **Conductor**  | $50     | Above + monthly video call + custom AI routing rules   |
| 🏆 **Patron**     | $100    | Above + your logo in the app UI + dedicated support    |
| 🏢 **Enterprise** | $500    | Commercial license + custom deployment + 1:1 support   |

> **Target:** first 10 founding sponsors by **17 April 2026**. This is a public goal, not a guaranteed outcome.

> **Early sponsors get lifetime perks** at launch-era prices. When VIO 83 ships v1.0, these tiers will increase.

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) before getting started.

```bash
git checkout -b feature/your-feature
# Make changes, test thoroughly
git push origin feature/your-feature
# Submit PR with clear description
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines, code standards, and how to set up your development environment.

---

## 📄 License

**Dual Licensed:**

| Use Case        | License                            | What It Means                                              |
| --------------- | ---------------------------------- | ---------------------------------------------------------- |
| **Commercial**  | [Proprietary](LICENSE-PROPRIETARY) | All Rights Reserved. Contact for licensing.                |
| **Open Source** | [AGPL-3.0](LICENSE-AGPL-3.0)       | Free to use, must share source, network use = distribution |

See [LICENSE](LICENSE) for full details. Copyright (c) 2026 Viorica Porcu (vio83).

---

## 🌐 Keywords & Topics

`ai-orchestration` `multi-ai` `llm-router` `ai-platform` `tauri-app` `desktop-ai` `claude-api` `gpt4` `gemini-api` `grok-api` `ollama` `rag-engine` `cross-check` `knowledge-base` `chromadb` `react-typescript` `fastapi` `ai-workflow` `multi-model` `verified-answers` `ai-verification` `smart-routing` `ai-desktop-app` `open-source-ai` `privacy-first-ai`

---

<p align="center">
  <strong>Built with determination by Viorica (vio83) — Italy 🇮🇹</strong><br>
  <em>One developer. One vision. The entire AI world in one app.</em><br>
  <em>Copyright (c) 2026 Viorica Porcu. All Rights Reserved.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made_in-Italy_🇮🇹-008C45?style=flat-square" />
  <img src="https://img.shields.io/badge/Status-Active_Development-00ff00?style=flat-square" />
  <img src="https://img.shields.io/badge/Pages-7_Full_UI-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/AI_Providers-7+-purple?style=flat-square" />
</p>
