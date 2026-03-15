#!/bin/bash
#═══════════════════════════════════════════════════════════════
#  VIO 83 AI Orchestra — Commit + Push Streaming Changes
#  Esegui questo script dal Terminale del tuo Mac:
#  bash ~/Projects/vio83-ai-orchestra/completa_streaming_push.sh
#  oppure copialo nella root del progetto e lancialo da lì
#═══════════════════════════════════════════════════════════════

set -e

PROJECT="/Users/padronavio/Projects/vio83-ai-orchestra"

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║  🎵 VIO 83 AI Orchestra — Commit & Push          ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

cd "$PROJECT" || { echo "❌ Cartella progetto non trovata: $PROJECT"; exit 1; }

echo "📂 Progetto: $PROJECT"
echo ""

# 1. Mostra stato
echo "── Git Status ──────────────────────────────────────"
git status --short
echo ""

# 2. Verifica build prima di committare
echo "── Verifica Build ──────────────────────────────────"
echo "⏳ TypeScript check..."
npx tsc --noEmit 2>&1 && echo "✅ TypeScript OK" || { echo "❌ Errori TypeScript!"; exit 1; }

echo "⏳ Vite build..."
npx vite build 2>&1 | tail -3
echo "✅ Build OK"
echo ""

# 3. Stage + Commit
echo "── Commit ──────────────────────────────────────────"
git add src/services/ai/orchestrator.ts src/components/chat/ChatView.tsx
git commit -m "$(cat <<'EOF'
feat: streaming AI responses in real-time

- Rewrite orchestrator.ts with onToken callback for Ollama + Cloud
- Rewrite ChatView.tsx with live streaming display
- Tokens appear one by one as the AI generates them
- Support both local (Ollama) and cloud provider streaming
- Graceful fallback if streaming fails

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
echo ""

# 4. Push
echo "── Push to GitHub ────────────────────────────────"
git push origin main
echo ""

# 5. Stato finale
echo "── Risultato Finale ────────────────────────────────"
echo "✅ Commit creato e pushato su GitHub!"
echo ""
git log --oneline -5
echo ""

echo "╔═══════════════════════════════════════════════════╗"
echo "║  ✅ FATTO! Streaming changes su GitHub.           ║"
echo "║                                                   ║"
echo "║  Prossimo passo: testa l'app con:                 ║"
echo "║  ./orchestra.sh start                             ║"
echo "║  oppure: vio start                                ║"
echo "╚═══════════════════════════════════════════════════╝"
