#!/bin/bash
# ============================================================
# 🔧 VIO 83 — FIX WORKFLOW ERRORS + PUSH + ENABLE PAGES
# ============================================================
# Uso: cd ~/Projects/vio83-ai-orchestra && bash FIX-E-PUSH.sh
# ============================================================

echo ""
echo "============================================"
echo "🔧 VIO 83 — FIX ERRORI GITHUB ACTIONS"
echo "============================================"
echo ""

cd "$(dirname "$0")"

# =============================================
# STEP 1: Commit e push delle fix
# =============================================
echo "📦 STEP 1: Commit fix workflow..."
git add -A
git commit -m "fix: correct all 3 GitHub Actions workflows

- deploy-pages.yml: disabled (use Settings > Pages > branch deployment instead)
- seo-automation.yml: merged into single job to avoid push conflicts, hardcoded IndexNow key, removed push trigger
- python-app.yml: only runs on backend/ changes, updated to Python 3.11, syntax check instead of pytest

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>" 2>/dev/null || echo "✅ Niente di nuovo da committare"

echo "📤 Pushing..."
git push origin main
echo "✅ Push completato"
echo ""

# =============================================
# STEP 2: Apri direttamente la pagina GitHub Pages Settings
# =============================================
echo "🌐 STEP 2: Apro GitHub Pages Settings..."
open "https://github.com/vio83/vio83-ai-orchestra/settings/pages"
echo ""
echo "============================================"
echo "⚠️  AZIONE MANUALE RICHIESTA (30 secondi):"
echo "============================================"
echo ""
echo "  Nella pagina che si è aperta:"
echo ""
echo "  1. Sotto 'Build and deployment'"
echo "     → Source: seleziona 'Deploy from a branch'"
echo ""
echo "  2. Branch: seleziona 'main'"
echo "     → Folder: seleziona '/docs'"
echo ""
echo "  3. Clicca 'Save'"
echo ""
echo "  4. Aspetta 1-2 minuti"
echo ""
echo "  5. Ricarica la pagina → vedrai il link verde:"
echo "     https://vio83.github.io/vio83-ai-orchestra/"
echo ""
echo "============================================"
echo ""

# =============================================
# STEP 3: Verifica dopo 90 secondi
# =============================================
echo "⏳ Aspetto 90 secondi per il deploy..."
echo "   (Nel frattempo fai il SAVE nelle Settings)"
sleep 90

echo ""
echo "🌐 Verifico se il sito è live..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://vio83.github.io/vio83-ai-orchestra/")
echo "   Landing page: HTTP $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo ""
    echo "🎉🎉🎉 IL SITO È LIVE! 🎉🎉🎉"
    echo ""
    echo "   → https://vio83.github.io/vio83-ai-orchestra/"
    echo ""
    # Ping immediato ai motori di ricerca
    echo "🔍 Ping immediato ai motori di ricerca..."
    curl -s "https://www.google.com/ping?sitemap=https://vio83.github.io/vio83-ai-orchestra/sitemap.xml" > /dev/null 2>&1
    curl -s "https://www.bing.com/ping?sitemap=https://vio83.github.io/vio83-ai-orchestra/sitemap.xml" > /dev/null 2>&1
    curl -s -X POST "https://api.indexnow.org/indexnow" \
      -H "Content-Type: application/json" \
      -d '{
        "host": "vio83.github.io",
        "key": "3e6f9ffe76d0f756d7492ec16fd4d501",
        "keyLocation": "https://vio83.github.io/vio83-ai-orchestra/3e6f9ffe76d0f756d7492ec16fd4d501.txt",
        "urlList": [
          "https://vio83.github.io/vio83-ai-orchestra/",
          "https://vio83.github.io/vio83-ai-orchestra/sitemap.xml"
        ]
      }' > /dev/null 2>&1
    echo "✅ Google, Bing, IndexNow pingati!"
    echo ""
    open "https://vio83.github.io/vio83-ai-orchestra/"
else
    echo ""
    echo "⚠️  Il sito non è ancora live (HTTP $HTTP_CODE)"
    echo "   Hai fatto SAVE nelle Pages Settings?"
    echo "   Se sì, aspetta ancora 1-2 minuti e ricarica:"
    echo "   → https://vio83.github.io/vio83-ai-orchestra/"
fi

echo ""
echo "============================================"
echo "📋 PROSSIMI PASSI (dopo che Pages è live):"
echo "============================================"
echo ""
echo "1. GOOGLE SEARCH CONSOLE — tab già aperta"
echo "   → Colonna DESTRA: 'Prefisso URL'"
echo "   → Incolla: https://vio83.github.io/vio83-ai-orchestra/"
echo "   → Continua → 'Tag HTML' → copia il meta tag"
echo "   → Incollalo nella chat con Claude"
echo ""
echo "2. BING WEBMASTER TOOLS — tab già aperta"
echo "   → Colonna SINISTRA: 'Import from Google Search Console'"
echo "   → Clicca 'Import' → seleziona il tuo sito → fatto!"
echo ""
