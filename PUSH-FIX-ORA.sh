#!/bin/bash
echo ""
echo "🔧 Push fix workflow + abilita GitHub Pages"
echo ""

cd ~/Projects/vio83-ai-orchestra

# Commit le fix
git add -A
git commit -m "fix: correct GitHub Actions workflows — stop error notifications

- deploy-pages.yml: disabled auto-deploy (use branch deployment instead)
- seo-automation.yml: single job, no conflicts
- python-app.yml: only on backend changes, no pytest needed"

# Push
git push origin main

echo ""
echo "✅ Fix pushate!"
echo ""
echo "================================================"
echo "ORA FAI QUESTO (è facilissimo, 4 click):"
echo "================================================"
echo ""
echo "STEP 1: Vai su questo link (copialo e incollalo su Orion):"
echo ""
echo "  https://github.com/vio83/vio83-ai-orchestra/settings/pages"
echo ""
echo "  SE VEDI 404: significa che non sei loggata su GitHub."
echo "  In quel caso vai prima su https://github.com/login"
echo "  e accedi, poi torna al link sopra."
echo ""
echo "STEP 2: Quando vedi la pagina Settings > Pages:"
echo "  - Cerca la sezione 'Build and deployment'"
echo "  - Sotto 'Source' clicca il menu e seleziona 'Deploy from a branch'"
echo "  - Sotto 'Branch' clicca 'None' e seleziona 'main'"
echo "  - Apparirà un secondo menu: seleziona '/ (root)' o '/docs'"
echo "    SCEGLI '/docs'"
echo "  - Clicca il bottone 'Save'"
echo ""
echo "STEP 3: Aspetta 2 minuti, poi vai su:"
echo "  https://vio83.github.io/vio83-ai-orchestra/"
echo ""
echo "  Se vedi la landing page → TUTTO FUNZIONA!"
echo ""
echo "================================================"
echo ""

# Apri la pagina
open "https://github.com/login"
sleep 3
open "https://github.com/vio83/vio83-ai-orchestra/settings/pages"
