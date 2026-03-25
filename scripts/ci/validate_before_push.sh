#!/usr/bin/env bash
# ============================================================
# VIO 83 AI ORCHESTRA — Anti-Run-Failed Validation System
# Esegue TUTTI i check CI localmente PRIMA del push.
# Replica esattamente: ci.yml + python-app.yml + auto-maintenance.yml
# ============================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

pass()  { echo -e "${GREEN}✅ $*${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $*${NC}"; WARNINGS=$((WARNINGS + 1)); }
fail()  { echo -e "${RED}❌ $*${NC}"; ERRORS=$((ERRORS + 1)); }
header(){ echo -e "\n${CYAN}━━━ $* ━━━${NC}"; }

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   VIO AI ORCHESTRA — Anti-Run-Failed Validation v1.0   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"

# ─── GATE 1: Guardrails ───
header "GATE 1: Guardrails (Policy + Gitlinks)"

if [ -f scripts/ci/check_no_orphan_gitlinks.sh ]; then
  bash scripts/ci/check_no_orphan_gitlinks.sh && pass "No orphan gitlinks" || fail "Orphan gitlinks trovati"
else
  fail "scripts/ci/check_no_orphan_gitlinks.sh mancante"
fi

if [ -f scripts/ci/policy_failure_gates.sh ]; then
  bash scripts/ci/policy_failure_gates.sh && pass "Policy gates passati" || fail "Policy gates falliti"
else
  fail "scripts/ci/policy_failure_gates.sh mancante"
fi

# ─── GATE 2: TypeScript ───
header "GATE 2: Frontend (TypeScript + ESLint)"

if command -v npx &> /dev/null && [ -f tsconfig.json ]; then
  npx tsc --noEmit 2>&1 && pass "TypeScript: 0 errori" || fail "TypeScript: errori trovati"
else
  warn "npx/tsconfig non trovati — skip TypeScript check"
fi

# ESLint (non-blocking: warn only)
if command -v npx &> /dev/null && [ -f eslint.config.js ]; then
  npx eslint src/ --max-warnings=0 2>&1 || warn "ESLint: warnings presenti"
fi

# ─── GATE 3: Python Backend ───
header "GATE 3: Python Backend (Syntax + Flake8 + Import)"

# Python compile check
python3 -c "
import py_compile, sys, os
errors = 0
for root, dirs, files in os.walk('backend'):
    dirs[:] = [d for d in dirs if d != '__pycache__' and d != 'venv']
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                print(f'  FAIL: {e}')
                errors += 1
if errors:
    sys.exit(1)
" && pass "Python: 0 syntax errors" || fail "Python: syntax errors trovati"

# Flake8 — critical errors only (same as CI)
if command -v flake8 &> /dev/null; then
  flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics 2>&1 \
    && pass "Flake8: 0 critical errors" || fail "Flake8: errori critici"
else
  warn "flake8 non installato — skip"
fi

# Import sanity check
python3 -c "
import sys, os
os.chdir('$(pwd)')
sys.path.insert(0, '.')
try:
    from backend.models.schemas import ChatRequest, HealthResponse
    from backend.config.providers import get_all_providers_ordered
    from backend.database.db import init_database
    print('Import check OK')
except ImportError as e:
    print(f'Import FAIL: {e}')
    sys.exit(1)
" && pass "Python import check OK" || fail "Python import fallito"

# ─── GATE 4: File Integrity ───
header "GATE 4: File Integrity & Security"

# Required files
for f in README.md LICENSE package.json package-lock.json .github/workflows/ci.yml; do
  [ -f "$f" ] || fail "File mancante: $f"
done
pass "File richiesti presenti"

# No API keys in source
PATTERN='(sk-live-|sk_test_|AKIA[0-9A-Z]{16}|-----BEGIN PRIVATE KEY-----)'
if grep -rE "$PATTERN" --include="*.py" --include="*.ts" --include="*.json" \
   --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist . 2>/dev/null | \
   grep -v ".env.example" | grep -v "test_stripe" | grep -v "policy_failure_gates" | grep -v "api_key_guardian"; then
  fail "Potenziale API key trovata nel codice!"
else
  pass "Nessuna API key esposta"
fi

# ─── GATE 5: Tests ───
header "GATE 5: Backend Tests"

if command -v pytest &> /dev/null; then
  PYTHONPATH=. python3 -m pytest tests/backend/ -q --tb=short \
    --ignore=tests/backend/test_integration.py 2>&1 | tail -5 \
    && pass "Backend tests passati" || fail "Backend tests falliti"
else
  warn "pytest non installato — skip"
fi

# ─── REPORT FINALE ───
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ "$ERRORS" -gt 0 ]; then
  echo -e "${RED}🔴 VALIDATION FAILED: $ERRORS errori, $WARNINGS warnings${NC}"
  echo -e "${RED}   NON fare push — fixa prima gli errori sopra.${NC}"
  exit 1
elif [ "$WARNINGS" -gt 0 ]; then
  echo -e "${YELLOW}🟡 VALIDATION PASSED con $WARNINGS warning(s)${NC}"
  echo -e "${YELLOW}   Push consentito, ma valuta i warnings.${NC}"
  exit 0
else
  echo -e "${GREEN}🟢 VALIDATION PASSED — Tutti i gate superati!${NC}"
  echo -e "${GREEN}   Push sicuro — CI non fallirà.${NC}"
  exit 0
fi
