#!/usr/bin/env bash
# ============================================================
# VIO 83 — LEGAL GUARDIAN GATE
# Verifica automatica che la protezione legale sia intatta:
#   1. File licenza esistono (LICENSE, LICENSE-PROPRIETARY, NOTICE)
#   2. AppFooter importato in App.tsx
#   3. i18n keys footerDisclaimer/footerJurisdiction in it.json + en.json
#   4. "Tribunale di Cagliari" in README.md + LICENSE-PROPRIETARY
# ============================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
FAIL=0

# Risolvi project root (funziona sia in locale che in CI)
if [ -n "${GITHUB_WORKSPACE:-}" ]; then
  ROOT="$GITHUB_WORKSPACE"
elif [ -d "$(git rev-parse --show-toplevel 2>/dev/null)" ]; then
  ROOT="$(git rev-parse --show-toplevel)"
else
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi

check() {
  if [ "$1" -eq 0 ]; then
    echo -e "${GREEN}✔ $2${NC}"
  else
    echo -e "${RED}✖ $2${NC}"
    FAIL=1
  fi
}

# ── 1. File licenza critici ──────────────────
for f in LICENSE LICENSE-PROPRIETARY NOTICE; do
  if [ -f "$ROOT/$f" ]; then
    check 0 "$f presente"
  else
    check 1 "$f MANCANTE — protezione legale compromessa"
  fi
done

# ── 2. AppFooter importato in App.tsx ────────
if grep -q "AppFooter" "$ROOT/src/App.tsx" 2>/dev/null; then
  check 0 "AppFooter presente in App.tsx"
else
  check 1 "AppFooter NON trovato in App.tsx — footer legale rimosso"
fi

# ── 3. i18n keys protezione ─────────────────
for locale in it en; do
  LOCALE_FILE="$ROOT/src/i18n/locales/${locale}.json"
  if [ -f "$LOCALE_FILE" ]; then
    MISSING_KEYS=""
    for key in footerDisclaimer footerJurisdiction; do
      if ! grep -q "$key" "$LOCALE_FILE" 2>/dev/null; then
        MISSING_KEYS="$MISSING_KEYS $key"
      fi
    done
    if [ -z "$MISSING_KEYS" ]; then
      check 0 "i18n ${locale}.json: chiavi legali presenti"
    else
      check 1 "i18n ${locale}.json: chiavi mancanti:$MISSING_KEYS"
    fi
  else
    check 1 "i18n ${locale}.json: file non trovato"
  fi
done

# ── 4. Giurisdizione nei documenti chiave ────
for f in README.md LICENSE-PROPRIETARY; do
  if grep -qi "Tribunale di Cagliari" "$ROOT/$f" 2>/dev/null; then
    check 0 "$f: giurisdizione Tribunale di Cagliari presente"
  else
    check 1 "$f: giurisdizione Tribunale di Cagliari ASSENTE"
  fi
done

# ── ESITO ────────────────────────────────────
if [ $FAIL -ne 0 ]; then
  echo -e "${RED}━━━ LEGAL GUARDIAN: PROTEZIONE LEGALE COMPROMESSA ━━━${NC}"
  exit 1
fi
echo -e "${GREEN}✔ Legal Guardian: protezione legale intatta${NC}"
