#!/bin/bash
# ============================================================
# 🌐 VIO 83 — APRI TUTTE LE PAGINE DI SETUP
# Apre direttamente le sezioni giuste su Orion/Safari
# ============================================================
# Uso: bash APRI-SETUP.sh
# ============================================================

echo ""
echo "🌐 Apro tutte le pagine di configurazione..."
echo ""

# =============================================
# 1. GITHUB PAGES — Settings (sezione Pages)
# =============================================
echo "1️⃣  GitHub Pages Settings..."
open "https://github.com/vio83/vio83-ai-orchestra/settings/pages"
sleep 2

# =============================================
# 2. GITHUB REPO — Settings generali (description, topics, social preview)
# =============================================
echo "2️⃣  GitHub Repo Settings..."
open "https://github.com/vio83/vio83-ai-orchestra/settings"
sleep 2

# =============================================
# 3. GITHUB SPONSORS — Setup profilo sponsor
# =============================================
echo "3️⃣  GitHub Sponsors Dashboard..."
open "https://github.com/sponsors/vio83/dashboard"
sleep 2

# =============================================
# 4. GOOGLE SEARCH CONSOLE — Pagina di benvenuto
#    → Clicca "Prefisso URL"
#    → Incolla: https://vio83.github.io/vio83-ai-orchestra/
#    → Clicca "Continua"
# =============================================
echo "4️⃣  Google Search Console..."
open "https://search.google.com/search-console/welcome"
sleep 2

# =============================================
# 5. BING WEBMASTER TOOLS — Pagina di accesso
#    → Accedi con Google (porcu.v.83@gmail.com)
#    → Poi aggiungi sito
# =============================================
echo "5️⃣  Bing Webmaster Tools..."
open "https://www.bing.com/webmasters/home"
sleep 2

# =============================================
# 6. KO-FI — Pagina impostazioni
# =============================================
echo "6️⃣  Ko-fi Settings..."
open "https://ko-fi.com/manage/supportreceived"
sleep 2

# =============================================
# 7. LINKEDIN — Il tuo profilo (per editare headline/about)
# =============================================
echo "7️⃣  LinkedIn Profile Edit..."
open "https://www.linkedin.com/in/viorica-porcu/edit/forms/intro/new/"
sleep 2

# =============================================
# 8. VERIFICA che GitHub Pages sia LIVE
# =============================================
echo "8️⃣  Pagina Live VIO 83..."
open "https://vio83.github.io/vio83-ai-orchestra/"
sleep 1

echo ""
echo "============================================"
echo "✅ Tutte le pagine aperte!"
echo "============================================"
echo ""
echo "📋 COSA FARE SU OGNI PAGINA:"
echo ""
echo "TAB 1 — GITHUB PAGES:"
echo "   → Source: 'Deploy from a branch'"
echo "   → Branch: main"
echo "   → Folder: /docs"
echo "   → Click SAVE"
echo ""
echo "TAB 2 — GITHUB SETTINGS:"
echo "   → Description: 'Multi-AI Desktop Orchestrator — 7 AI providers in one app'"
echo "   → Website: https://vio83.github.io/vio83-ai-orchestra/"
echo "   → Topics: ai, chatgpt, claude, gemini, grok, mistral, deepseek, ollama, tauri, desktop-app, multi-ai, orchestrator"
echo "   → Social Preview: carica docs/assets/social-preview.png"
echo ""
echo "TAB 3 — GITHUB SPONSORS:"
echo "   → Se non è attivo: clicca 'Join the waitlist' o 'Set up sponsors profile'"
echo "   → I testi sono pronti in .github/SPONSOR_PROFILE.md"
echo ""
echo "TAB 4 — GOOGLE SEARCH CONSOLE:"
echo "   → Scegli 'Prefisso URL' (colonna destra)"
echo "   → Incolla: https://vio83.github.io/vio83-ai-orchestra/"
echo "   → Clicca 'Continua'"
echo "   → Per verifica: scegli 'Tag HTML'"
echo "   → Copia il meta tag e incollalo qui in chat"
echo "   → (Lo aggiungo io al codice)"
echo ""
echo "TAB 5 — BING WEBMASTER TOOLS:"
echo "   → Accedi con 'Sign in with Google'"
echo "   → Usa porcu.v.83@gmail.com"
echo "   → Aggiungi sito: https://vio83.github.io/vio83-ai-orchestra/"
echo "   → Metodo verifica: 'Importa da Google Search Console' (il più veloce)"
echo "   → Oppure 'XML Sitemap' e incolla: https://vio83.github.io/vio83-ai-orchestra/sitemap.xml"
echo ""
echo "TAB 6 — KO-FI:"
echo "   → I testi sono pronti in docs/KOFI_PAGE_CONTENT.md"
echo "   → Copia-incolla About, Tiers, Goals da quel file"
echo ""
echo "TAB 7 — LINKEDIN:"
echo "   → Headline: 'AI Engineer & Multi-AI Orchestrator Creator | Building VIO 83 AI Orchestra | 7 AI in One Desktop App'"
echo "   → I testi completi sono in docs/LINKEDIN_SPONSOR_CONTENT.md"
echo ""
echo "TAB 8 — VERIFICA che la landing page sia visibile"
echo ""
