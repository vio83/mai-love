#!/usr/bin/env bash
# Policy gates that must pass before expensive CI jobs run.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

fail() {
  echo -e "${RED}FAIL: $*${NC}"
  exit 1
}

pass() {
  echo -e "${GREEN}OK: $*${NC}"
}

# Gate 1: required files for legal/release hygiene.
for f in README.md LICENSE package.json .github/workflows/ci.yml; do
  [ -f "$f" ] || fail "required file missing: $f"
done
pass "required repository files present"

# Gate 2: package-lock must exist for deterministic frontend builds.
[ -f "package-lock.json" ] || fail "package-lock.json missing"
pass "lockfile present"

# Gate 3: release workflow must use pinned major versions for critical actions.
for action in actions/checkout@v4 actions/setup-node@v4 actions/setup-python@v5; do
  grep -R --line-number "$action" .github/workflows >/dev/null || fail "missing recommended action pin: $action"
done
pass "workflow action pins found"

# Gate 4: disallow obvious leaked API keys in tracked files.
MATCHES=$(git grep -nE '(sk-live-|sk_test_|AKIA[0-9A-Z]{16}|-----BEGIN PRIVATE KEY-----)' -- . ':(exclude)data/**' ':(exclude)scripts/ci/policy_failure_gates.sh' || true)
if [ -n "$MATCHES" ]; then
  echo "$MATCHES"
  fail "potential credential leak pattern found"
fi
pass "no obvious credential leak patterns"
