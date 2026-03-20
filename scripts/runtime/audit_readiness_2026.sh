#!/usr/bin/env bash
# ============================================================================
# VIO / AI LOVE Readiness Audit 2026
# Esegue un audit tecnico locale e produce report JSON + testo.
# ============================================================================
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$REPO_ROOT/data/autonomous_runtime"
JSON_OUT="$OUT_DIR/readiness-audit-$(date +%Y%m%d-%H%M%S).json"
TXT_OUT="$OUT_DIR/readiness-audit-latest.txt"

mkdir -p "$OUT_DIR"

has_cmd() {
  command -v "$1" >/dev/null 2>&1 && echo true || echo false
}

cmd_ver() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    "$cmd" --version 2>/dev/null | head -1 || echo "installed"
  else
    echo "missing"
  fi
}

GITLINK_COUNT=$(git -C "$REPO_ROOT" ls-files --stage | awk '$1=="160000"{c++} END{print c+0}')
AUTOPILOT_STATUS="stopped"
if launchctl list | grep -q "com.vio83.ci-autopilot"; then
  AUTOPILOT_STATUS="running"
fi

TYPECHECK_STATUS="unknown"
if npx tsc --noEmit >/dev/null 2>&1; then
  TYPECHECK_STATUS="pass"
else
  TYPECHECK_STATUS="fail"
fi

cat > "$JSON_OUT" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repo_root": "$REPO_ROOT",
  "ci": {
    "gitlink_count": $GITLINK_COUNT,
    "autopilot_status": "$AUTOPILOT_STATUS",
    "gh_installed": $(has_cmd gh),
    "jq_installed": $(has_cmd jq)
  },
  "toolchain": {
    "node": "$(node -v 2>/dev/null || echo missing)",
    "npm": "$(npm -v 2>/dev/null || echo missing)",
    "python3": "$(python3 --version 2>/dev/null || echo missing)",
    "git": "$(git --version 2>/dev/null || echo missing)",
    "rustc": "$(cmd_ver rustc)",
    "cargo": "$(cmd_ver cargo)",
    "ollama": "$(ollama --version 2>/dev/null | head -1 || echo missing)",
    "docker": "$(docker --version 2>/dev/null | head -1 || echo missing)"
  },
  "quality": {
    "typecheck": "$TYPECHECK_STATUS"
  }
}
EOF

{
  echo "VIO / AI LOVE READINESS AUDIT"
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  echo "CI"
  echo "- Gitlink count: $GITLINK_COUNT (expected 0)"
  echo "- CI autopilot: $AUTOPILOT_STATUS"
  echo ""
  echo "Toolchain"
  echo "- Node: $(node -v 2>/dev/null || echo missing)"
  echo "- npm: $(npm -v 2>/dev/null || echo missing)"
  echo "- Python: $(python3 --version 2>/dev/null || echo missing)"
  echo "- Rust: $(cmd_ver rustc)"
  echo "- Cargo: $(cmd_ver cargo)"
  echo "- Ollama: $(ollama --version 2>/dev/null | head -1 || echo missing)"
  echo "- Docker: $(docker --version 2>/dev/null | head -1 || echo missing)"
  echo ""
  echo "Quality"
  echo "- Typecheck: $TYPECHECK_STATUS"
  echo ""
  echo "JSON report: $JSON_OUT"
} > "$TXT_OUT"

echo "Audit completato"
echo "- Report testo: $TXT_OUT"
echo "- Report JSON:  $JSON_OUT"
