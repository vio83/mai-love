# Contributing to VIO 83 AI Orchestra

Thank you for your interest in contributing to **VIO 83 AI Orchestra** — the world's first intelligent multi-AI orchestration platform! Every contribution helps make AI more accessible, verified, and intelligent.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Sponsor the Project](#sponsor-the-project)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code. Be respectful, inclusive, and constructive.

---

## How Can I Contribute?

### 🐛 Report Bugs
Found a bug? Open an [issue](https://github.com/vio83/vio83-ai-orchestra/issues/new?template=bug_report.md) with steps to reproduce it.

### 💡 Suggest Features
Have an idea? Open a [feature request](https://github.com/vio83/vio83-ai-orchestra/issues/new?template=feature_request.md) and describe your use case.

### 🔧 Fix Issues
Browse our [open issues](https://github.com/vio83/vio83-ai-orchestra/issues) — issues labeled `good first issue` are great starting points.

### 📖 Improve Documentation
Better docs help everyone. Fix typos, add examples, or improve explanations.

### 🌍 Translations
Help translate the interface and documentation into other languages.

### ⭐ Star & Share
The simplest way to help: star the repository and share it with others who might benefit.

---

## Development Setup

### Prerequisites
- **macOS** (Apple Silicon recommended)
- **Node.js** 20+ (`nvm install 20`)
- **Python** 3.11+ (`brew install python`)
- **Rust** (for Tauri desktop builds): `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- **Ollama** (for local AI testing): `brew install ollama`

### Quick Setup

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/vio83-ai-orchestra.git
cd vio83-ai-orchestra

# 3. Install frontend dependencies
npm install

# 4. Install backend dependencies
pip3 install litellm fastapi uvicorn chromadb anthropic openai httpx

# 5. Copy environment template
cp .env.example .env
# Edit .env with your API keys (optional for local-only development)

# 6. Start development
npm run dev          # Frontend at http://localhost:5173
python -m backend.api.server  # Backend API at http://localhost:8000
```

---

## Project Structure

```
vio83-ai-orchestra/
├── src/                          # Frontend (React + TypeScript)
│   ├── components/               # Reusable UI components
│   │   ├── chat/                 # ChatView, ChatInput, ChatMessage
│   │   ├── sidebar/              # Sidebar navigation
│   │   └── settings/             # SettingsPanel
│   ├── pages/                    # Full-page views
│   │   ├── DashboardPage.tsx     # Command Center
│   │   ├── AnalyticsPage.tsx     # Performance analytics
│   │   ├── WorkflowPage.tsx      # Visual pipeline builder
│   │   ├── CrossCheckPage.tsx    # Multi-model verification
│   │   ├── RagPage.tsx           # RAG knowledge base
│   │   └── ModelsPage.tsx        # AI models registry
│   ├── services/ai/              # AI orchestration logic
│   ├── stores/                   # Zustand state management
│   ├── styles/                   # CSS (vio-dark.css theme)
│   ├── types/                    # TypeScript type definitions
│   └── App.tsx                   # Root component + routing
├── backend/                      # Backend (Python + FastAPI)
│   ├── api/server.py             # FastAPI server (800+ lines)
│   ├── orchestrator/             # AI routing + Ollama integration
│   └── models/                   # Data models
├── src-tauri/                    # Tauri 2.0 desktop wrapper (Rust)
├── data/                         # Knowledge base data
├── docs/                         # GitHub Pages landing page
├── .github/                      # GitHub Actions, issue templates, funding
└── package.json                  # Node.js dependencies + scripts
```

---

## Coding Standards

### TypeScript / React
- Use **functional components** with hooks
- Use **Zustand** for global state (not Context API for complex state)
- Use **lucide-react** for icons
- Use **framer-motion** for animations
- Follow existing CSS variable pattern (`var(--vio-green)`, etc.)
- Use **inline styles** for component-specific styles (consistent with existing codebase)
- Export pages as `export default function PageName()`

### Python / Backend
- Use **FastAPI** with async endpoints
- Use **type hints** everywhere
- Follow **PEP 8** style guide
- Use `httpx` for async HTTP calls

### General
- Write meaningful commit messages
- Keep PRs focused — one feature or fix per PR
- Test your changes before submitting

---

## Pull Request Process

1. **Fork** the repository and create a new branch: `git checkout -b feature/your-feature`
2. **Make** your changes following the coding standards above
3. **Test** thoroughly — ensure `npm run build` succeeds and `npm run lint` passes
4. **Commit** with a clear message: `git commit -m "Add: brief description of change"`
5. **Push** to your fork: `git push origin feature/your-feature`
6. **Open a PR** against the `main` branch with a clear description:
   - What does this PR do?
   - Why is this change needed?
   - How was it tested?

### PR Review
- The maintainer (Viorica) reviews all PRs personally
- Please be patient — this is a solo project
- Address review comments promptly

---

## Reporting Issues

### Bug Reports
Include:
- **OS and version** (e.g., macOS 15.3, Apple M1)
- **Node.js version** (`node -v`)
- **Steps to reproduce** the bug
- **Expected behavior** vs **actual behavior**
- **Screenshots** if applicable
- **Console logs** if relevant

### Feature Requests
Include:
- **Use case** — what problem does this solve?
- **Proposed solution** — how should it work?
- **Alternatives considered** — what other approaches did you think of?

---

## License

By contributing to VIO 83 AI Orchestra, you agree that your contributions will be licensed under the same **dual license** (AGPL-3.0 + Proprietary) as the project.

---

## Sponsor the Project

Love VIO 83? Consider [sponsoring the development](https://github.com/sponsors/vio83). Your support directly funds API costs, hardware, and full-time development.

<p align="center">
  <a href="https://github.com/sponsors/vio83">
    <img src="https://img.shields.io/badge/Sponsor-💚-ea4aaa?style=for-the-badge&logo=github-sponsors" />
  </a>
</p>

---

**Thank you for contributing!** Every PR, issue, star, and share helps build a better AI future. 🎵
