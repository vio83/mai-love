#!/usr/bin/env bash
# ============================================================
# VIO 83 — PRE-COMMIT HOOK: Blocca gitlink 160000 orfani
# Previene il push di submodule senza .gitmodules
#
# Installazione automatica:
#   cp scripts/ci/pre-commit-gitlink-guard.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
# ============================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Cerca gitlink 160000 nell'index staged
GITLINKS=$(git diff --cached --diff-filter=A --raw 2>/dev/null | grep "^:000000 160000" || true)

if [ -n "$GITLINKS" ]; then
  echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${RED}  BLOCCATO: Gitlink 160000 rilevato nello staging!${NC}"
  echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  echo "$GITLINKS"
  echo ""
  echo "Questo causerebbe un fallimento di GitHub Actions checkout."
  echo ""
  echo "Per risolvere:"
  echo "  git rm --cached <nome-cartella>"
  echo "  echo '<nome-cartella>/' >> .gitignore"
  echo "  git add .gitignore && git commit"
  echo ""
  exit 1
fi

# Verifica anche gitlink già presenti nell'index
EXISTING=$(git ls-files --stage 2>/dev/null | grep "^160000" || true)

if [ -n "$EXISTING" ]; then
  # Verifica se .gitmodules esiste e contiene i path
  if [ ! -f ".gitmodules" ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  AVVISO: Gitlink 160000 senza .gitmodules!       ${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "$EXISTING"
    echo ""
    echo "Rimuovi con: git rm --cached <path>"
    exit 1
  fi
fi

echo -e "${GREEN}✓ Nessun gitlink orfano rilevato${NC}"
exit 0
