#!/usr/bin/env bash
# ============================================================
# VIO 83 AI Orchestra — Bump Version
# Aggiorna la versione in tutti i file in un'unica operazione.
# Uso: ./scripts/bump-version.sh 1.0.0
# ============================================================
set -euo pipefail

NEW_VERSION="${1:-}"
if [[ -z "$NEW_VERSION" ]]; then
    echo "❌ Usa: $0 <versione> (es. $0 1.0.0)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "🔢 Bump versione → v${NEW_VERSION}"
echo "========================================"

# Verifica che jq sia disponibile
if ! command -v jq &>/dev/null; then
    echo "❌ jq non trovato. Installa con: brew install jq"
    exit 1
fi

# 1. package.json
echo "📦 package.json..."
jq --arg v "$NEW_VERSION" '.version = $v' package.json > package.json.tmp
mv package.json.tmp package.json

# 2. src-tauri/tauri.conf.json
echo "🦀 tauri.conf.json..."
jq --arg v "$NEW_VERSION" '.version = $v' src-tauri/tauri.conf.json > tauri.conf.json.tmp
mv tauri.conf.json.tmp src-tauri/tauri.conf.json

# 3. src-tauri/Cargo.toml
echo "⚙️  Cargo.toml..."
sed -i.bak "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" src-tauri/Cargo.toml
rm -f src-tauri/Cargo.toml.bak

# 4. backend/api/server.py — aggiorna VERSION_APP
if grep -q "VERSION_APP\|version.*=.*\"0\." backend/api/server.py 2>/dev/null; then
    echo "🐍 server.py..."
    sed -i.bak "s/VERSION_APP = \"[^\"]*\"/VERSION_APP = \"${NEW_VERSION}\"/" backend/api/server.py
    rm -f backend/api/server.py.bak
fi

# 5. CHANGELOG.md — sostituisce [Unreleased] con la nuova versione
TODAY=$(date +%Y-%m-%d)
if grep -q "\[Unreleased\]" CHANGELOG.md 2>/dev/null; then
    echo "📝 CHANGELOG.md (Unreleased → ${NEW_VERSION})..."
    sed -i.bak "s/\[Unreleased\]/[${NEW_VERSION}] — ${TODAY}/" CHANGELOG.md
    rm -f CHANGELOG.md.bak
fi

echo ""
echo "✅ Versione aggiornata a v${NEW_VERSION} in:"
echo "   - package.json"
echo "   - src-tauri/tauri.conf.json"
echo "   - src-tauri/Cargo.toml"
echo "   - backend/api/server.py (se presente VERSION_APP)"
echo "   - CHANGELOG.md (se presente [Unreleased])"
echo ""
echo "📌 Prossimi step:"
echo "   git add -A && git commit -m 'chore(release): v${NEW_VERSION}'"
echo "   git tag v${NEW_VERSION}"
echo "   git push origin main --tags"
