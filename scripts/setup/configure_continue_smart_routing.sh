#!/usr/bin/env bash
# ============================================================
# VIO 83 AI ORCHESTRA — Continue Smart Model Routing
#
# Configura Continue per selezionare automaticamente il modello
# Ollama migliore in base al tipo di task.
#
# Modelli installati e loro specializzazioni:
#   - qwen2.5-coder:3b  → Code completion, autocomplete (veloce)
#   - codellama:latest   → Code generation, debugging, refactoring
#   - deepseek-r1:latest → Reasoning, analisi, problem solving
#   - mistral:latest     → Multilingue, writing, documentazione
#   - llama3.2:3b        → General purpose, chat veloce
#   - llama3:latest      → General purpose, chat (8B, più potente)
#   - nomic-embed-text   → Embeddings per ricerca semantica
#
# Eseguire: bash scripts/setup/configure_continue_smart_routing.sh
# ============================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

CONTINUE_DIR="$HOME/.continue"
CONFIG_FILE="$CONTINUE_DIR/config.json"

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  VIO 83 — Continue Smart Model Routing Configuration   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Backup config attuale
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup-$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}  ✓ Backup config attuale creato${NC}"
fi

# Scrivi nuova configurazione con routing intelligente
cat > "$CONFIG_FILE" << 'CONFIGEOF'
{
  "models": [
    {
      "title": "DeepSeek-R1 — Reasoning & Analysis",
      "provider": "ollama",
      "model": "deepseek-r1",
      "apiBase": "http://localhost:11434",
      "systemMessage": "You are a senior software architect. Reason step by step. Be precise, thorough, and professional. When analyzing code, identify root causes, not symptoms."
    },
    {
      "title": "CodeLlama — Code Expert",
      "provider": "ollama",
      "model": "codellama",
      "apiBase": "http://localhost:11434",
      "systemMessage": "You are an expert code assistant. Write clean, production-ready code. Follow best practices for the language being used. Include types, error handling, and edge cases."
    },
    {
      "title": "Mistral 7B — Multilingual & Docs",
      "provider": "ollama",
      "model": "mistral",
      "apiBase": "http://localhost:11434",
      "systemMessage": "You are a multilingual technical writer and developer assistant. Respond in the same language as the user. Be clear, professional, and precise."
    },
    {
      "title": "Qwen 2.5 Coder — Fast Code",
      "provider": "ollama",
      "model": "qwen2.5-coder:3b",
      "apiBase": "http://localhost:11434",
      "systemMessage": "You are a fast, efficient code assistant. Provide concise, working code solutions. Prioritize correctness and performance."
    },
    {
      "title": "Llama 3 8B — General",
      "provider": "ollama",
      "model": "llama3",
      "apiBase": "http://localhost:11434",
      "systemMessage": "You are a helpful, knowledgeable assistant. Be direct and thorough in your responses."
    },
    {
      "title": "Llama 3.2 3B — Quick Chat",
      "provider": "ollama",
      "model": "llama3.2:3b",
      "apiBase": "http://localhost:11434",
      "systemMessage": "You are a fast, helpful assistant. Keep responses concise but complete."
    }
  ],
  "tabAutocompleteModel": {
    "title": "Qwen 2.5 Coder (Autocomplete)",
    "provider": "ollama",
    "model": "qwen2.5-coder:3b",
    "apiBase": "http://localhost:11434"
  },
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text",
    "apiBase": "http://localhost:11434"
  },
  "reranker": {
    "name": "llm",
    "params": {
      "modelTitle": "Llama 3.2 3B — Quick Chat"
    }
  },
  "contextProviders": [
    {
      "name": "code",
      "params": {}
    },
    {
      "name": "docs",
      "params": {}
    },
    {
      "name": "diff",
      "params": {}
    },
    {
      "name": "terminal",
      "params": {}
    },
    {
      "name": "problems",
      "params": {}
    },
    {
      "name": "folder",
      "params": {}
    },
    {
      "name": "codebase",
      "params": {}
    }
  ],
  "slashCommands": [
    {
      "name": "edit",
      "description": "Edit selected code"
    },
    {
      "name": "comment",
      "description": "Add comments to code"
    },
    {
      "name": "share",
      "description": "Export conversation to markdown"
    },
    {
      "name": "cmd",
      "description": "Generate terminal command"
    },
    {
      "name": "commit",
      "description": "Generate a commit message"
    }
  ],
  "customCommands": [
    {
      "name": "test",
      "prompt": "Write comprehensive unit tests for the selected code using the appropriate testing framework (pytest for Python, vitest for TypeScript). Cover edge cases, error paths, and boundary conditions.",
      "description": "Generate unit tests"
    },
    {
      "name": "explain",
      "prompt": "Explain the selected code in detail. Describe what each part does, why design decisions were made, and identify any potential issues or improvements.",
      "description": "Explain code in detail"
    },
    {
      "name": "optimize",
      "prompt": "Analyze the selected code for performance, readability, and maintainability. Suggest specific improvements with before/after examples.",
      "description": "Optimize code"
    },
    {
      "name": "fix",
      "prompt": "Identify and fix all bugs, errors, and issues in the selected code. Explain what was wrong and why the fix works.",
      "description": "Fix bugs in code"
    },
    {
      "name": "refactor",
      "prompt": "Refactor the selected code following SOLID principles, clean code practices, and the project's coding standards. Maintain the same behavior.",
      "description": "Refactor code"
    },
    {
      "name": "security",
      "prompt": "Perform a security audit on the selected code. Check for OWASP top 10 vulnerabilities, injection risks, authentication issues, and data exposure.",
      "description": "Security audit"
    },
    {
      "name": "doc",
      "prompt": "Generate comprehensive documentation for the selected code including JSDoc/docstrings, parameter descriptions, return values, and usage examples.",
      "description": "Generate documentation"
    },
    {
      "name": "vio",
      "prompt": "You are the VIO 83 AI Orchestra assistant. Analyze the current project context and suggest the next best action to improve code quality, performance, or architecture. Be specific and actionable.",
      "description": "VIO 83 project assistant"
    }
  ],
  "allowAnonymousTelemetry": false,
  "docs": []
}
CONFIGEOF

echo -e "${GREEN}  ✓ config.json scritto con Smart Model Routing${NC}"
echo ""

echo -e "${BLUE}Modelli configurati:${NC}"
echo "  1. DeepSeek-R1     → Reasoning, analisi, problem solving"
echo "  2. CodeLlama       → Code generation, debugging, refactoring"
echo "  3. Mistral 7B      → Multilingue, documentazione, writing"
echo "  4. Qwen 2.5 Coder  → Autocomplete + fast code (DEFAULT)"
echo "  5. Llama 3 8B      → General purpose"
echo "  6. Llama 3.2 3B    → Chat veloce"
echo ""
echo -e "${BLUE}Autocomplete:${NC} Qwen 2.5 Coder (veloce, 3B)"
echo -e "${BLUE}Embeddings:${NC}   nomic-embed-text (ricerca semantica)"
echo ""
echo -e "${BLUE}Comandi custom disponibili in chat:${NC}"
echo "  /test     → Genera unit test"
echo "  /explain  → Spiega il codice"
echo "  /optimize → Ottimizza performance"
echo "  /fix      → Trova e correggi bug"
echo "  /refactor → Refactoring SOLID"
echo "  /security → Audit sicurezza OWASP"
echo "  /doc      → Genera documentazione"
echo "  /vio      → Assistente progetto VIO 83"
echo ""
echo -e "${BLUE}Context providers attivi:${NC}"
echo "  @code, @docs, @diff, @terminal, @problems, @folder, @codebase"
echo ""
echo -e "${GREEN}✅ Configurazione completata. Riavvia VS Code e premi Cmd+L.${NC}"
