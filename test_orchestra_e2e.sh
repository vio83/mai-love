#!/bin/bash
#═══════════════════════════════════════════════════════════════
#  VIO 83 AI Orchestra — Test End-to-End
#  Verifica che tutto funzioni: Ollama, Frontend, Backend, Chat
#
#  Esegui dal Terminale Mac:
#  bash test_orchestra_e2e.sh
#═══════════════════════════════════════════════════════════════

PROJECT="/Users/padronavio/Projects/vio83-ai-orchestra"
PASS=0
FAIL=0
WARN=0

green()  { echo -e "\033[32m✅ $1\033[0m"; ((PASS++)); }
red()    { echo -e "\033[31m❌ $1\033[0m"; ((FAIL++)); }
yellow() { echo -e "\033[33m⚠️  $1\033[0m"; ((WARN++)); }

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  🧪 VIO 83 AI Orchestra — Test End-to-End            ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

cd "$PROJECT" 2>/dev/null || { red "Cartella progetto non trovata: $PROJECT"; exit 1; }

# ─── 1. Struttura Progetto ───────────────────────────────────
echo "── 1. Struttura Progetto ─────────────────────────────"
[ -f "package.json" ]                          && green "package.json esiste" || red "package.json mancante"
[ -f "src/App.tsx" ]                           && green "src/App.tsx esiste" || red "src/App.tsx mancante"
[ -f "src/services/ai/orchestrator.ts" ]       && green "orchestrator.ts esiste" || red "orchestrator.ts mancante"
[ -f "src/components/chat/ChatView.tsx" ]      && green "ChatView.tsx esiste" || red "ChatView.tsx mancante"
[ -f "src/components/settings/SettingsPanel.tsx" ] && green "SettingsPanel.tsx esiste" || red "SettingsPanel.tsx mancante"
[ -f "backend/api/server.py" ]                 && green "backend/api/server.py esiste" || red "backend/api/server.py mancante"
[ -f "backend/rag/engine.py" ]                 && green "backend/rag/engine.py esiste" || red "backend/rag/engine.py mancante"
[ -f "orchestra.sh" ]                          && green "orchestra.sh esiste" || red "orchestra.sh mancante"
[ -x "orchestra.sh" ]                          && green "orchestra.sh è eseguibile" || red "orchestra.sh non è eseguibile"
echo ""

# ─── 2. Dipendenze ──────────────────────────────────────────
echo "── 2. Dipendenze ─────────────────────────────────────"
[ -d "node_modules" ]  && green "node_modules installati" || { yellow "node_modules mancanti — esegui: npm install"; }
command -v node &>/dev/null && green "Node.js: $(node -v)" || red "Node.js non installato"
command -v python3 &>/dev/null && green "Python: $(python3 --version 2>&1)" || red "Python3 non installato"
command -v ollama &>/dev/null && green "Ollama: installato" || red "Ollama non installato"
echo ""

# ─── 3. Ollama ───────────────────────────────────────────────
echo "── 3. Ollama ─────────────────────────────────────────"
if curl -s http://localhost:11434/api/tags &>/dev/null; then
    green "Ollama server attivo su :11434"

    MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "
import json, sys
data = json.load(sys.stdin)
models = [m['name'] for m in data.get('models', [])]
print('\n'.join(models))
" 2>/dev/null)

    if [ -n "$MODELS" ]; then
        echo "   Modelli disponibili:"
        echo "$MODELS" | while read m; do echo "   • $m"; done

        # Cerca modello per chat
        if echo "$MODELS" | grep -qi "qwen\|llama\|gemma\|mistral\|phi"; then
            green "Modello chat disponibile"
        else
            yellow "Nessun modello chat riconosciuto — scarica con: ollama pull qwen2.5-coder:3b"
        fi
    else
        yellow "Nessun modello installato"
    fi
else
    red "Ollama non attivo — avvia con: ollama serve"
fi
echo ""

# ─── 4. Test Chat Ollama (Quick) ─────────────────────────────
echo "── 4. Test Chat Ollama (risposta rapida) ─────────────"
if curl -s http://localhost:11434/api/tags &>/dev/null; then
    # Prendi il primo modello disponibile
    MODEL=$(curl -s http://localhost:11434/api/tags | python3 -c "
import json, sys
data = json.load(sys.stdin)
models = data.get('models', [])
if models: print(models[0]['name'])
" 2>/dev/null)

    if [ -n "$MODEL" ]; then
        echo "   Invio messaggio test a: $MODEL"
        RESPONSE=$(curl -s --max-time 30 http://localhost:11434/api/chat \
            -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Rispondi solo: OK FUNZIONA\"}],\"stream\":false}" \
            2>/dev/null)

        if echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['message']['content'])" 2>/dev/null | grep -qi "ok\|funziona\|work"; then
            green "Ollama risponde correttamente!"
            echo "   Risposta: $(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['message']['content'][:100])" 2>/dev/null)"
        else
            CONTENT=$(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('message',{}).get('content','VUOTA')[:150])" 2>/dev/null)
            if [ -n "$CONTENT" ] && [ "$CONTENT" != "VUOTA" ]; then
                green "Ollama risponde (contenuto diverso dal previsto)"
                echo "   Risposta: $CONTENT"
            else
                red "Ollama non ha risposto correttamente"
            fi
        fi
    else
        yellow "Nessun modello per test chat"
    fi
else
    yellow "Skipping test chat — Ollama non attivo"
fi
echo ""

# ─── 5. Test Streaming Ollama ────────────────────────────────
echo "── 5. Test Streaming Ollama ──────────────────────────"
if curl -s http://localhost:11434/api/tags &>/dev/null && [ -n "$MODEL" ]; then
    echo "   Test streaming con: $MODEL"
    TOKENS=0
    while IFS= read -r line; do
        TOKEN=$(echo "$line" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('message',{}).get('content',''))" 2>/dev/null)
        if [ -n "$TOKEN" ]; then
            ((TOKENS++))
        fi
        if [ $TOKENS -ge 5 ]; then break; fi
    done < <(curl -s --max-time 15 http://localhost:11434/api/chat \
        -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Conta da 1 a 5\"}],\"stream\":true}" 2>/dev/null)

    if [ $TOKENS -ge 3 ]; then
        green "Streaming funziona! ($TOKENS token ricevuti)"
    else
        yellow "Streaming ha prodotto pochi token ($TOKENS)"
    fi
else
    yellow "Skipping test streaming"
fi
echo ""

# ─── 6. Build TypeScript + Vite ──────────────────────────────
echo "── 6. Build ──────────────────────────────────────────"
echo "   ⏳ TypeScript check..."
if npx tsc --noEmit 2>&1; then
    green "TypeScript compilation OK"
else
    red "Errori TypeScript"
fi

echo "   ⏳ Vite build..."
if npx vite build 2>&1 | tail -1 | grep -q "built in"; then
    green "Vite build OK"
else
    red "Vite build fallito"
fi
echo ""

# ─── 7. Git Status ───────────────────────────────────────────
echo "── 7. Git ────────────────────────────────────────────"
BRANCH=$(git branch --show-current 2>/dev/null)
[ -n "$BRANCH" ] && green "Branch: $BRANCH" || red "Non in un repo git"

COMMITS=$(git log --oneline 2>/dev/null | wc -l | tr -d ' ')
green "Commits totali: $COMMITS"

DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$DIRTY" -eq 0 ]; then
    green "Working tree pulito"
else
    yellow "$DIRTY file non committati"
    git status --short 2>/dev/null | head -10
fi

REMOTE=$(git remote get-url origin 2>/dev/null)
[ -n "$REMOTE" ] && green "Remote: $REMOTE" || yellow "Nessun remote configurato"
echo ""

# ─── Risultati ───────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════"
echo ""
echo "  📊 RISULTATI TEST"
echo "  ─────────────────"
echo "  ✅ Passati:    $PASS"
echo "  ❌ Falliti:    $FAIL"
echo "  ⚠️  Warning:   $WARN"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "  🎵 TUTTO FUNZIONA! L'Orchestra è pronta!"
    echo ""
    echo "  Avvia l'app con:"
    echo "  ./orchestra.sh start"
    echo "  oppure: vio start"
else
    echo "  ⚠️  Ci sono $FAIL problemi da risolvere."
    echo "  Correggi gli errori sopra e rilancia il test."
fi
echo ""
echo "═══════════════════════════════════════════════════════"
