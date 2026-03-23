#!/usr/bin/env bash
# ============================================================
# VIO 83 — Pulizia spazio Mac per aggiornamento macOS
# Libera ≥34 GB eliminando cache, partial downloads, temp files
# ============================================================
set -euo pipefail

echo "🔍 Spazio attuale:"
df -h / | tail -1

echo ""
echo "=== [1/6] Pulizia Ollama download parziali ==="
PARTIAL_SIZE=$(du -sh ~/.ollama/models/blobs/*-partial 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
if find ~/.ollama/models/blobs/ -name "*-partial" -print -quit 2>/dev/null | grep -q .; then
  find ~/.ollama/models/blobs/ -name "*-partial" -print -delete 2>/dev/null && echo "✅ Partial files rimossi" || echo "⚠️ Errore permessi — prova manualmente: rm ~/.ollama/models/blobs/*-partial"
else
  echo "  Nessun file partial trovato"
fi

echo ""
echo "=== [2/6] Pulizia cache sistema ==="
# Homebrew cache
if command -v brew &>/dev/null; then
  brew cleanup --prune=all 2>/dev/null && echo "✅ Homebrew cache pulita" || true
fi

# npm cache
if command -v npm &>/dev/null; then
  npm cache clean --force 2>/dev/null && echo "✅ npm cache pulita" || true
fi

# pip cache
if command -v pip3 &>/dev/null; then
  pip3 cache purge 2>/dev/null && echo "✅ pip cache pulita" || true
fi

echo ""
echo "=== [3/6] Log vecchi ==="
find ~/Library/Logs -type f -mtime +7 -delete 2>/dev/null && echo "✅ Log >7gg rimossi" || true
find /tmp -maxdepth 1 -type f -mtime +3 -delete 2>/dev/null || true

echo ""
echo "=== [4/6] Xcode DerivedData ==="
if [ -d ~/Library/Developer/Xcode/DerivedData ]; then
  rm -rf ~/Library/Developer/Xcode/DerivedData
  echo "✅ DerivedData rimossa"
fi

echo ""
echo "=== [5/6] Cache Rust/Cargo ==="
if [ -d ~/.cargo/registry/cache ]; then
  rm -rf ~/.cargo/registry/cache
  echo "✅ Cargo cache pulita"
fi

echo ""
echo "=== [6/6] Pulizia progetto VIO ==="
cd /Users/padronavio/Projects/vio83-ai-orchestra
# __pycache__
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find backend -name "*.pyc" -delete 2>/dev/null || true
# Vite cache
rm -rf node_modules/.cache 2>/dev/null || true
echo "✅ Cache progetto pulite"

echo ""
echo "========================================="
echo "🔍 Spazio dopo pulizia:"
df -h / | tail -1
AVAIL=$(df -h / | tail -1 | awk '{print $4}')
echo ""
echo "📊 Spazio disponibile: $AVAIL"
echo ""
if [[ $(df / | tail -1 | awk '{print $4}') -gt 70000000 ]]; then
  echo "✅ HAI ABBASTANZA SPAZIO per l'aggiornamento macOS (>34 GB)"
else
  echo "⚠️ Potrebbe servire più spazio. Controlla in Impostazioni > Generali > Spazio"
fi
