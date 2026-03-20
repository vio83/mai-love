#!/usr/bin/env bash
# Fail CI if orphan gitlinks (mode 160000) are present without valid .gitmodules entries.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

GITLINKS=$(git ls-files --stage | awk '$1=="160000" {print $4}')

if [ -z "$GITLINKS" ]; then
  echo -e "${GREEN}OK: no gitlinks present${NC}"
  exit 0
fi

if [ ! -f ".gitmodules" ]; then
  echo -e "${RED}FAIL: gitlinks found but .gitmodules is missing${NC}"
  echo "$GITLINKS"
  exit 1
fi

MISSING=0
while IFS= read -r path; do
  [ -z "$path" ] && continue
  if ! git config -f .gitmodules --get-regexp '^submodule\..*\.path$' | awk '{print $2}' | grep -Fxq "$path"; then
    echo -e "${RED}FAIL: gitlink path '$path' not declared in .gitmodules${NC}"
    MISSING=1
  fi
done <<< "$GITLINKS"

if [ "$MISSING" -ne 0 ]; then
  exit 1
fi

echo -e "${GREEN}OK: gitlinks are consistent with .gitmodules${NC}"
