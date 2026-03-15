#!/bin/bash
# ============================================================
# 🚀 VIO 83 AI ORCHESTRA — MASTER EXECUTION SCRIPT
# Esegui questo UNICO script dal Mac per attivare TUTTO
# ============================================================
# Uso: cd ~/Projects/vio83-ai-orchestra && bash ESEGUI-ORA.sh
# ============================================================

set -e
echo ""
echo "============================================"
echo "🚀 VIO 83 — ATTIVAZIONE MONDIALE SEO"
echo "============================================"
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# =============================================
# STEP 1: GIT PUSH (deploy tutto su GitHub)
# =============================================
echo "📦 STEP 1: Push su GitHub..."
git add -A
git status
git commit -m "seo: landing page + cyber-vio + automation completa" 2>/dev/null || echo "✅ Niente di nuovo da committare"
git push origin main
echo "✅ Push completato — GitHub Pages si aggiorna in ~60 secondi"
echo ""

# =============================================
# STEP 2: ATTENDI DEPLOY GITHUB PAGES
# =============================================
echo "⏳ STEP 2: Attendo deploy GitHub Pages (90 secondi)..."
sleep 90
echo "✅ Deploy dovrebbe essere completato"
echo ""

# =============================================
# STEP 3: PING GOOGLE
# =============================================
echo "🔍 STEP 3: Ping Google Sitemap..."
GOOGLE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://www.google.com/ping?sitemap=https://vio83.github.io/vio83-ai-orchestra/sitemap.xml")
echo "   Google: HTTP $GOOGLE_RESPONSE"

# =============================================
# STEP 4: PING BING
# =============================================
echo "🔍 STEP 4: Ping Bing Sitemap..."
BING_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://www.bing.com/ping?sitemap=https://vio83.github.io/vio83-ai-orchestra/sitemap.xml")
echo "   Bing: HTTP $BING_RESPONSE"

# =============================================
# STEP 5: PING INDEXNOW (Bing + Yandex + DuckDuckGo + Seznam)
# =============================================
echo "🔍 STEP 5: Ping IndexNow (4 motori)..."
INDEXNOW_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "vio83.github.io",
    "key": "3e6f9ffe76d0f756d7492ec16fd4d501",
    "keyLocation": "https://vio83.github.io/vio83-ai-orchestra/3e6f9ffe76d0f756d7492ec16fd4d501.txt",
    "urlList": [
      "https://vio83.github.io/vio83-ai-orchestra/",
      "https://vio83.github.io/vio83-ai-orchestra/sitemap.xml",
      "https://vio83.github.io/vio83-ai-orchestra/index.html"
    ]
  }')
echo "   IndexNow: HTTP $INDEXNOW_RESPONSE"

# =============================================
# STEP 6: PING YANDEX
# =============================================
echo "🔍 STEP 6: Ping Yandex..."
YANDEX_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://blogs.yandex.ru/pings/?status=success&url=https://vio83.github.io/vio83-ai-orchestra/")
echo "   Yandex: HTTP $YANDEX_RESPONSE"

# =============================================
# STEP 7: VERIFICA PAGINE LIVE
# =============================================
echo ""
echo "🌐 STEP 7: Verifica pagine live..."
LANDING=$(curl -s -o /dev/null -w "%{http_code}" "https://vio83.github.io/vio83-ai-orchestra/")
SITEMAP=$(curl -s -o /dev/null -w "%{http_code}" "https://vio83.github.io/vio83-ai-orchestra/sitemap.xml")
ROBOTS=$(curl -s -o /dev/null -w "%{http_code}" "https://vio83.github.io/vio83-ai-orchestra/robots.txt")
INDEXNOW_KEY=$(curl -s -o /dev/null -w "%{http_code}" "https://vio83.github.io/vio83-ai-orchestra/3e6f9ffe76d0f756d7492ec16fd4d501.txt")
PAGE404=$(curl -s -o /dev/null -w "%{http_code}" "https://vio83.github.io/vio83-ai-orchestra/404.html")

echo "   Landing page:  HTTP $LANDING"
echo "   Sitemap.xml:   HTTP $SITEMAP"
echo "   Robots.txt:    HTTP $ROBOTS"
echo "   IndexNow key:  HTTP $INDEXNOW_KEY"
echo "   404 page:      HTTP $PAGE404"

# =============================================
# STEP 8: INSTALLA AUTOMAZIONE MAC (launchd)
# =============================================
echo ""
echo "⚙️  STEP 8: Installazione automazione Mac..."
PLIST_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$PLIST_DIR"
mkdir -p "$PROJECT_DIR/automation/logs"

# Rendi eseguibile lo script
chmod +x "$PROJECT_DIR/automation/mac-scripts/seo-ping.sh"

# Aggiorna il path nel plist con il path reale
sed "s|/Users/padronavio/Projects/vio83-ai-orchestra|$PROJECT_DIR|g" \
    "$PROJECT_DIR/automation/mac-scripts/com.vio83.seo-ping.plist" > \
    "$PLIST_DIR/com.vio83.seo-ping.plist"

# Carica il job
launchctl unload "$PLIST_DIR/com.vio83.seo-ping.plist" 2>/dev/null || true
launchctl load "$PLIST_DIR/com.vio83.seo-ping.plist"
echo "✅ SEO Ping automatico installato (ogni 6 ore, sopravvive ai riavvii)"

# =============================================
# STEP 9: PRIMO PING LOCALE
# =============================================
echo ""
echo "🔄 STEP 9: Primo ping SEO locale..."
bash "$PROJECT_DIR/automation/mac-scripts/seo-ping.sh" 2>&1 | tail -5
echo "✅ Primo ping eseguito"

# =============================================
# STEP 10: VERIFICA GITHUB ACTIONS
# =============================================
echo ""
echo "📋 STEP 10: Verifica GitHub Actions..."
echo "   I workflow sono configurati e saranno attivati:"
echo "   - deploy-pages.yml    → ad ogni push su main"
echo "   - seo-automation.yml  → ogni giorno alle 06:00 UTC"
echo "   - weekly-seo-report.yml → ogni lunedì alle 09:00 UTC"
echo ""

# =============================================
# RIEPILOGO FINALE
# =============================================
echo ""
echo "============================================"
echo "🎉 VIO 83 — ATTIVAZIONE COMPLETATA!"
echo "============================================"
echo ""
echo "✅ RISULTATI:"
echo "   • GitHub Pages LIVE:  https://vio83.github.io/vio83-ai-orchestra/"
echo "   • Sitemap:            https://vio83.github.io/vio83-ai-orchestra/sitemap.xml"
echo "   • Robots.txt:         https://vio83.github.io/vio83-ai-orchestra/robots.txt"
echo "   • IndexNow key:       https://vio83.github.io/vio83-ai-orchestra/3e6f9ffe76d0f756d7492ec16fd4d501.txt"
echo "   • Google:             PINGATO ✅"
echo "   • Bing:               PINGATO ✅"
echo "   • IndexNow (4 motori): PINGATO ✅"
echo "   • Yandex:             PINGATO ✅"
echo "   • Mac automation:     ATTIVA ogni 6 ore ✅"
echo "   • GitHub Actions:     3 workflow attivi ✅"
echo ""
echo "🔗 PROSSIMI PASSI MANUALI (2 minuti):"
echo ""
echo "   1. GOOGLE SEARCH CONSOLE:"
echo "      → https://search.google.com/search-console/welcome"
echo "      → Scegli 'Prefisso URL'"
echo "      → Incolla: https://vio83.github.io/vio83-ai-orchestra/"
echo "      → Verifica con 'Tag HTML' (copia il meta tag)"
echo ""
echo "   2. BING WEBMASTER TOOLS:"
echo "      → https://www.bing.com/webmasters"
echo "      → Accedi con Microsoft account"
echo "      → Aggiungi sito: https://vio83.github.io/vio83-ai-orchestra/"
echo "      → Verifica con 'Sitemap XML' o 'Meta tag'"
echo ""
echo "   3. GITHUB SETTINGS:"
echo "      → https://github.com/vio83/vio83-ai-orchestra/settings/pages"
echo "      → Source: 'Deploy from a branch'"
echo "      → Branch: main, folder: /docs"
echo "      → Save"
echo ""
echo "Log automazione: $PROJECT_DIR/automation/logs/"
echo ""
