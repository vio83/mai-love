#!/usr/bin/env bash
# ============================================================
# VIO 83 — PUSH COMPLETO DI TUTTI I FIX (20 marzo 2026)
# Esegui: chmod +x PUSH-TUTTO-ORA.sh && ./PUSH-TUTTO-ORA.sh
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  🚀 VIO 83 — PUSH COMPLETO FIX 20/03/2026               ${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Verifica git
if ! git rev-parse --git-dir &>/dev/null; then
  echo -e "${RED}❌ Non sei in un repo Git!${NC}"; exit 1
fi

# Verifica git lock
if [ -f ".git/index.lock" ]; then
  echo -e "${YELLOW}⚠️  Rimuovo git lock stale...${NC}"
  rm -f .git/index.lock
fi

# Mostra stato
echo -e "${CYAN}=== STATUS ====${NC}"
git status --short

echo ""
echo -e "${CYAN}=== STAGING ====${NC}"

# Stage tutti i fix
git add .github/workflows/seo-automation.yml
echo -e "  ${GREEN}✓${NC} seo-automation.yml (bulletproof + sitemap auto-create)"

git add .github/workflows/weekly-seo-report.yml
echo -e "  ${GREEN}✓${NC} weekly-seo-report.yml (fix label + concurrency)"

git add src/VioAiOrchestra.jsx
echo -e "  ${GREEN}✓${NC} VioAiOrchestra.jsx (ErrorBoundary + i18n + lazy loading)"

git add src/pages/PrivacyPage.tsx
echo -e "  ${GREEN}✓${NC} PrivacyPage.tsx (fix t().map crash)"

git add .gitignore
echo -e "  ${GREEN}✓${NC} .gitignore (AI-LOVE, venv, logs)"

git add scripts/nuke-failed-runs.sh
echo -e "  ${GREEN}✓${NC} nuke-failed-runs.sh (v3 con 4 retry levels)"

git add scripts/ci/pre-commit-gitlink-guard.sh
echo -e "  ${GREEN}✓${NC} pre-commit-gitlink-guard.sh (blocca gitlink orfani)"

git add scripts/runtime/gh_auto_rerun_watchdog.sh
echo -e "  ${GREEN}✓${NC} gh_auto_rerun_watchdog.sh (circuit breaker max 2 rerun)"

git add RIATTIVA-TUTTO.sh
echo -e "  ${GREEN}✓${NC} RIATTIVA-TUTTO.sh (fix venv rotto + avvio completo)"

git add VIO-INVESTIMENTI-2026.html
echo -e "  ${GREEN}✓${NC} VIO-INVESTIMENTI-2026.html (piano investimenti interattivo)"

# Opzionale: altri file modificati
git add .vscode/settings.json 2>/dev/null && echo -e "  ${GREEN}✓${NC} .vscode/settings.json" || true
git add PUSH-TUTTO-ORA.sh 2>/dev/null || true

echo ""
echo -e "${CYAN}=== COMMIT ====${NC}"

git commit -m "fix: risoluzione completa CI/CD + frontend + repo hygiene

FIXES CRITICI:
- fix(git): rimosso gitlink AI-LOVE orfano (causa root Pages failures)
- fix(gitignore): AI-LOVE/, venv/, logs/ esclusi da tracking
- fix(seo): seo-automation.yml bulletproof con sitemap auto-create
- fix(seo): weekly-seo-report.yml fix label inesistenti + concurrency
- fix(frontend): VioAiOrchestra.jsx aggiunto ErrorBoundary + initI18n
- fix(frontend): PrivacyPage.tsx crash t().map su stringa i18n

MIGLIORAMENTI:
- feat(scripts): nuke-failed-runs.sh v3 con 4 livelli retry
- feat(scripts): pre-commit-gitlink-guard.sh blocca gitlink in futuro
- feat(scripts): gh_auto_rerun_watchdog.sh circuit breaker max 2 rerun
- feat(scripts): RIATTIVA-TUTTO.sh v2 con fix venv Python rotto
- docs: VIO-INVESTIMENTI-2026.html piano completo tool + costi

[skip ci]"

echo -e "${GREEN}  ✅ Commit creato${NC}"
echo ""
echo -e "${CYAN}=== PUSH ====${NC}"

if git push origin main; then
  echo -e "${GREEN}  ✅ Push completato!${NC}"
else
  echo -e "${RED}  ❌ Push fallito. Prova:${NC}"
  echo -e "     git pull --rebase origin main"
  echo -e "     ./PUSH-TUTTO-ORA.sh"
  exit 1
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ TUTTO PUSHATO — Verifica GitHub Actions:${NC}"
echo -e "     ${CYAN}https://github.com/vio83/vio83-ai-orchestra/actions${NC}"
echo ""
echo -e "  Dopo il push, esegui anche il nuke dei run vecchi:"
echo -e "     ${YELLOW}./scripts/nuke-failed-runs.sh${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
