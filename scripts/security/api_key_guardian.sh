#!/usr/bin/env bash
# ============================================================
# VIO 83 AI ORCHESTRA — API Key Guardian
# Scansione automatica, alerting e protezione API keys
#
# Eseguire: bash scripts/security/api_key_guardian.sh [scan|watch|report]
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_FILE="$PROJECT_ROOT/.logs/security-scan-$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$PROJECT_ROOT/.logs"

# ============================================================
# API KEY PATTERNS — tutti i pattern noti a Marzo 2026
# ============================================================
declare -A KEY_PATTERNS=(
  ["OpenAI"]='sk-proj-[a-zA-Z0-9_-]{20,}'
  ["OpenAI_Legacy"]='sk-[a-zA-Z0-9]{40,}'
  ["Anthropic"]='sk-ant-[a-zA-Z0-9_-]{20,}'
  ["Groq"]='gsk_[a-zA-Z0-9]{20,}'
  ["xAI_Grok"]='xai-[a-zA-Z0-9]{20,}'
  ["Google_Gemini"]='AIza[a-zA-Z0-9_-]{35}'
  ["GitHub_PAT"]='ghp_[a-zA-Z0-9]{36}'
  ["GitHub_OAuth"]='gho_[a-zA-Z0-9]{36}'
  ["Stripe_Secret"]='sk_live_[a-zA-Z0-9]{20,}'
  ["Stripe_Test"]='sk_test_[a-zA-Z0-9]{20,}'
  ["Stripe_Publishable"]='pk_live_[a-zA-Z0-9]{20,}'
  ["Stripe_Webhook"]='whsec_[a-zA-Z0-9]{20,}'
  ["Snyk"]='snyk-[a-zA-Z0-9]{20,}'
  ["SendGrid"]='SG\.[a-zA-Z0-9_-]{22,}'
  ["Slack_Bot"]='xoxb-[a-zA-Z0-9-]{20,}'
  ["Slack_User"]='xoxp-[a-zA-Z0-9-]{20,}'
  ["AWS_Access"]='AKIA[0-9A-Z]{16}'
  ["Private_Key"]='-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'
  ["DeepSeek"]='sk-[a-f0-9]{32}'
  ["OpenRouter"]='sk-or-v1-[a-zA-Z0-9]{40,}'
  ["Perplexity"]='pplx_[a-zA-Z0-9]{40,}'
  ["Tavily"]='tvly-[a-zA-Z0-9]{20,}'
)

# Files to EXCLUDE from scanning (they legitimately contain patterns)
EXCLUDE_DIRS="node_modules,.git,dist,__pycache__,target,.venv,.venv-1,venv"
EXCLUDE_FILES="api_key_guardian.sh,policy_failure_gates.sh,auto-maintenance.yml,.env.example"

scan_tracked_files() {
  echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║     VIO 83 — API Key Guardian — Security Scan           ║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${BLUE}Scansione:${NC} $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  echo ""

  local FOUND=0
  local TOTAL_CHECKED=0

  # 1. Scan GIT-TRACKED files (these would be exposed on GitHub)
  echo -e "${BLUE}[FASE 1]${NC} Scansione file tracciati da Git (esposti su GitHub)..."

  cd "$PROJECT_ROOT"

  local TRACKED_FILES
  TRACKED_FILES=$(git ls-files 2>/dev/null)

  for pattern_name in "${!KEY_PATTERNS[@]}"; do
    local pattern="${KEY_PATTERNS[$pattern_name]}"
    local matches
    matches=$(echo "$TRACKED_FILES" | xargs grep -lE "$pattern" 2>/dev/null | grep -v -E "(\.env\.example|$EXCLUDE_FILES)" || true)

    if [ -n "$matches" ]; then
      echo -e "${RED}  ✗ CRITICO: Pattern $pattern_name trovato in file tracciati:${NC}"
      echo "$matches" | while read -r file; do
        echo -e "${RED}    → $file${NC}"
        FOUND=$((FOUND + 1))
      done
    fi
  done

  if [ "$FOUND" -eq 0 ]; then
    echo -e "${GREEN}  ✓ Nessuna API key reale nei file tracciati da Git${NC}"
  fi

  echo ""

  # 2. Check .gitignore covers sensitive files
  echo -e "${BLUE}[FASE 2]${NC} Verifica .gitignore protegge file sensibili..."

  local SENSITIVE_FILES=(".env" ".env.local" ".env.production" ".env.release" ".tauri-keys/")
  for sf in "${SENSITIVE_FILES[@]}"; do
    if git check-ignore -q "$sf" 2>/dev/null; then
      echo -e "${GREEN}  ✓ $sf — protetto da .gitignore${NC}"
    else
      echo -e "${RED}  ✗ $sf — NON protetto da .gitignore!${NC}"
      FOUND=$((FOUND + 1))
    fi
  done

  echo ""

  # 3. Check .env exists locally with real keys
  echo -e "${BLUE}[FASE 3]${NC} Verifica .env locale..."

  if [ -f "$PROJECT_ROOT/.env" ]; then
    local ENV_KEYS=0
    for pattern_name in "${!KEY_PATTERNS[@]}"; do
      local pattern="${KEY_PATTERNS[$pattern_name]}"
      if grep -qE "$pattern" "$PROJECT_ROOT/.env" 2>/dev/null; then
        # Check it's not a placeholder
        if ! grep -E "$pattern" "$PROJECT_ROOT/.env" 2>/dev/null | grep -qE "xxxx|XXXX|your_|example|placeholder"; then
          echo -e "${YELLOW}  ⚠ $pattern_name — chiave REALE presente in .env locale${NC}"
          ENV_KEYS=$((ENV_KEYS + 1))
        fi
      fi
    done

    if [ "$ENV_KEYS" -gt 0 ]; then
      echo -e "${YELLOW}  Trovate $ENV_KEYS chiavi reali nel .env locale (OK se non committato)${NC}"
    else
      echo -e "${GREEN}  ✓ .env contiene solo placeholder${NC}"
    fi
  else
    echo -e "${GREEN}  ✓ Nessun .env locale (sicuro)${NC}"
  fi

  echo ""

  # 4. Check git history for accidentally committed keys
  echo -e "${BLUE}[FASE 4]${NC} Scansione cronologia Git per chiavi accidentalmente committate..."

  local HISTORY_LEAK=0
  # Check if .env was ever tracked
  if git log --all --diff-filter=A --name-only --pretty=format: -- .env 2>/dev/null | grep -q ".env"; then
    echo -e "${RED}  ✗ CRITICO: .env è stato committato nella cronologia Git!${NC}"
    echo -e "${RED}    Azione: Esegui 'git filter-branch' o 'BFG Repo Cleaner' per rimuoverlo${NC}"
    HISTORY_LEAK=1
  else
    echo -e "${GREEN}  ✓ .env mai committato nella cronologia Git${NC}"
  fi

  echo ""

  # Final report
  echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
  if [ "$FOUND" -eq 0 ] && [ "$HISTORY_LEAK" -eq 0 ]; then
    echo -e "${GREEN}RISULTATO: SICURO — Nessuna API key esposta su GitHub${NC}"
  else
    echo -e "${RED}RISULTATO: ATTENZIONE — $FOUND problemi trovati${NC}"
  fi
  echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
}

show_rotation_links() {
  echo ""
  echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║     Link diretti per ruotare le API Keys                ║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${BLUE}OpenAI:${NC}      https://platform.openai.com/api-keys"
  echo -e "${BLUE}Anthropic:${NC}   https://console.anthropic.com/settings/keys"
  echo -e "${BLUE}Groq:${NC}        https://console.groq.com/keys"
  echo -e "${BLUE}DeepSeek:${NC}    https://platform.deepseek.com/api_keys"
  echo -e "${BLUE}Mistral:${NC}     https://console.mistral.ai/api-keys/"
  echo -e "${BLUE}Google AI:${NC}   https://aistudio.google.com/apikey"
  echo -e "${BLUE}xAI (Grok):${NC}  https://console.x.ai/team/api-keys"
  echo -e "${BLUE}Perplexity:${NC}  https://www.perplexity.ai/settings/api"
  echo -e "${BLUE}OpenRouter:${NC}  https://openrouter.ai/settings/keys"
  echo -e "${BLUE}Stripe:${NC}      https://dashboard.stripe.com/apikeys"
  echo -e "${BLUE}GitHub PAT:${NC}  https://github.com/settings/tokens"
  echo -e "${BLUE}Snyk:${NC}        https://app.snyk.io/account"
  echo ""
}

pre_commit_check() {
  # Usato come pre-commit hook
  echo "API Key Guardian — Pre-commit check..."

  local STAGED_FILES
  STAGED_FILES=$(git diff --cached --name-only 2>/dev/null)

  if [ -z "$STAGED_FILES" ]; then
    exit 0
  fi

  local BLOCKED=0

  for pattern_name in "${!KEY_PATTERNS[@]}"; do
    local pattern="${KEY_PATTERNS[$pattern_name]}"
    local matches
    matches=$(echo "$STAGED_FILES" | xargs grep -lE "$pattern" 2>/dev/null | grep -v -E "(\.env\.example|$EXCLUDE_FILES)" || true)

    if [ -n "$matches" ]; then
      echo -e "${RED}BLOCCATO: API key pattern ($pattern_name) trovato nei file staged:${NC}"
      echo "$matches"
      BLOCKED=1
    fi
  done

  if [ "$BLOCKED" -eq 1 ]; then
    echo -e "${RED}Commit BLOCCATO per protezione API keys.${NC}"
    echo "Rimuovi le chiavi dai file prima di committare."
    exit 1
  fi

  echo -e "${GREEN}✓ Nessuna API key nei file staged${NC}"
}

# ============================================================
# MAIN
# ============================================================
case "${1:-scan}" in
  scan)
    scan_tracked_files
    show_rotation_links
    ;;
  links)
    show_rotation_links
    ;;
  pre-commit)
    pre_commit_check
    ;;
  *)
    echo "Uso: $0 [scan|links|pre-commit]"
    exit 1
    ;;
esac
