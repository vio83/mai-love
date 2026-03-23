#!/usr/bin/env bash
# VIO 83 — CI Pre-Push Gate
# Runs locally BEFORE git push to catch everything that would fail on GitHub Actions.
# Mirrors: ci.yml guardrails + frontend + backend, python-app.yml, policy gates.
# Usage: bash scripts/ci/pre_push_gate.sh
#   or install as git hook: cp scripts/ci/pre_push_gate.sh .git/hooks/pre-push && chmod +x .git/hooks/pre-push
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

pass() { echo -e "${GREEN}✔ $*${NC}"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}✖ $*${NC}"; FAIL=$((FAIL+1)); }
warn() { echo -e "${YELLOW}⚠ $*${NC}"; WARN=$((WARN+1)); }

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "═══════════════════════════════════════════"
echo " VIO 83 — CI Pre-Push Gate"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════"
echo ""

# ─── 1. Guardrails ───
echo "── Guardrails ──"
if bash scripts/ci/check_no_orphan_gitlinks.sh 2>&1 >/dev/null; then
  pass "No orphan gitlinks"
else
  fail "Orphan gitlinks detected"
fi

if bash scripts/ci/policy_failure_gates.sh 2>&1 >/dev/null; then
  pass "Policy gates passed"
else
  fail "Policy gates failed — run: bash scripts/ci/policy_failure_gates.sh"
fi

# ─── 2. Frontend ───
echo ""
echo "── Frontend ──"
if npx tsc --noEmit 2>&1 >/dev/null; then
  pass "TypeScript check"
else
  fail "TypeScript errors — run: npx tsc --noEmit"
fi

if npm run build 2>&1 >/dev/null; then
  pass "Vite production build"
else
  fail "Build failed — run: npm run build"
fi

# Lint (non-blocking, like CI)
if npm run lint 2>&1 >/dev/null; then
  pass "ESLint"
else
  warn "ESLint warnings (non-blocking)"
fi

# ─── 3. Backend ───
echo ""
echo "── Backend ──"
if python3 -m compileall -q backend/ 2>&1 >/dev/null; then
  pass "Python compile check"
else
  fail "Python compile error — run: python3 -m compileall -q backend/"
fi

# Flake8 critical errors (if available)
if command -v flake8 &>/dev/null || python3 -m flake8 --version &>/dev/null 2>&1; then
  if python3 -m flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics 2>&1 >/dev/null; then
    pass "Flake8 critical errors"
  else
    fail "Flake8 critical errors — run: python3 -m flake8 backend/ --select=E9,F63,F7,F82"
  fi
else
  warn "Flake8 not installed — skipping (CI will still check)"
fi

# Syntax verification (mirrors python-app.yml)
SYNTAX_ERRORS=$(cd backend && python3 -c "
import pathlib
errors = 0
for f in pathlib.Path('.').rglob('*.py'):
    if f.name == '__init__.py':
        continue
    try:
        compile(open(f).read(), f, 'exec')
    except SyntaxError as e:
        print(f'  {f}: {e}')
        errors += 1
print(f'ERRORS={errors}')
" 2>&1 | grep "^ERRORS=" | cut -d= -f2)

if [ "${SYNTAX_ERRORS:-0}" = "0" ]; then
  pass "Backend syntax verification"
else
  fail "Backend syntax errors: $SYNTAX_ERRORS files"
fi

# ─── Summary ───
echo ""
echo "═══════════════════════════════════════════"
echo -e " Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}, ${YELLOW}${WARN} warnings${NC}"
echo "═══════════════════════════════════════════"

if [ "$FAIL" -gt 0 ]; then
  echo -e "${RED}BLOCKED: Fix $FAIL failure(s) before pushing.${NC}"
  exit 1
else
  echo -e "${GREEN}ALL CLEAR: Safe to push.${NC}"
  exit 0
fi
