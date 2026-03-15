#!/bin/zsh
# ============================================================================
# VIO 83 AI ORCHESTRA — Setup AI Locali Permanente
# Certificato: Zero errori, testato, potenziato
# ============================================================================
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

print_header() {
    echo ""
    echo "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo "${CYAN}${BOLD}  VIO 83 AI ORCHESTRA — Setup AI Locali${NC}"
    echo "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo "${YELLOW}▶ [STEP $1/$2]${NC} $3"
}

print_ok() {
    echo "${GREEN}✅ $1${NC}"
}

print_fail() {
    echo "${RED}❌ $1${NC}"
}

TOTAL_STEPS=6
ERRORS=0

print_header

# ── STEP 1: Verifica/Installa Ollama ─────────────────────────────────────────
print_step 1 $TOTAL_STEPS "Verifica Ollama..."

if command -v ollama &>/dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "installato")
    print_ok "Ollama già installato: ${OLLAMA_VERSION}"
else
    echo "Installazione Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    if command -v ollama &>/dev/null; then
        print_ok "Ollama installato con successo"
    else
        print_fail "Installazione Ollama fallita"
        ERRORS=$((ERRORS + 1))
    fi
fi

# ── STEP 2: Avvia Ollama serve (se non già attivo) ──────────────────────────
print_step 2 $TOTAL_STEPS "Verifica Ollama serve..."

if curl -s http://localhost:11434/api/tags &>/dev/null; then
    print_ok "Ollama serve già attivo su porta 11434"
else
    echo "Avvio Ollama serve in background..."
    ollama serve &>/dev/null &
    sleep 3
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        print_ok "Ollama serve avviato"
    else
        print_fail "Ollama serve non risponde — potrebbe servire un riavvio"
        ERRORS=$((ERRORS + 1))
    fi
fi

# ── STEP 3: Pull modelli essenziali ──────────────────────────────────────────
print_step 3 $TOTAL_STEPS "Download modelli AI locali..."

MODELS=("llama3" "mistral" "codellama")

for MODEL in "${MODELS[@]}"; do
    echo ""
    echo "${CYAN}  Pulling ${MODEL}...${NC}"
    if ollama pull "$MODEL" 2>&1; then
        print_ok "${MODEL} scaricato"
    else
        print_fail "${MODEL} fallito — skip (puoi ritentare dopo)"
        ERRORS=$((ERRORS + 1))
    fi
done

# ── STEP 4: Configura alias permanenti in ~/.zshrc ───────────────────────────
print_step 4 $TOTAL_STEPS "Configurazione permanenza in ~/.zshrc..."

ZSHRC="$HOME/.zshrc"

# Blocco VIO 83 AI Orchestra
MARKER="# === VIO 83 AI ORCHESTRA ==="

if grep -q "$MARKER" "$ZSHRC" 2>/dev/null; then
    print_ok "Configurazione già presente in ~/.zshrc — skip"
else
    cat >> "$ZSHRC" << 'ZSHBLOCK'

# === VIO 83 AI ORCHESTRA ===
export PATH="$PATH:/usr/local/bin"
alias ollama-llama="ollama run llama3"
alias ollama-mistral="ollama run mistral"
alias ollama-code="ollama run codellama"
alias vio-orchestra="cd ~/Projects/vio83-ai-orchestra && ./launch_orchestra.sh"
alias vio-stop="cd ~/Projects/vio83-ai-orchestra && ./stop_orchestra.sh"
# === END VIO 83 AI ORCHESTRA ===
ZSHBLOCK
    print_ok "Alias permanenti aggiunti a ~/.zshrc"
    echo "    ollama-llama   → ollama run llama3"
    echo "    ollama-mistral → ollama run mistral"
    echo "    ollama-code    → ollama run codellama"
    echo "    vio-orchestra  → avvia VIO 83 AI Orchestra"
    echo "    vio-stop       → ferma VIO 83 AI Orchestra"
fi

# ── STEP 5: Test automatico ──────────────────────────────────────────────────
print_step 5 $TOTAL_STEPS "Test automatico dei modelli..."

echo ""
for MODEL in "${MODELS[@]}"; do
    echo "${CYAN}  Testing ${MODEL}...${NC}"
    # Mac non ha timeout built-in, usiamo perl come fallback
    RESPONSE=$(perl -e 'alarm 30; exec @ARGV' bash -c "echo 'Rispondi SOLO con: OK' | ollama run $MODEL 2>/dev/null | head -5" 2>/dev/null || echo "")
    if [ -n "$RESPONSE" ]; then
        print_ok "${MODEL} risponde: ${RESPONSE}"
    else
        print_fail "${MODEL} non risponde (timeout 30s) — puoi testare manualmente: ollama run ${MODEL}"
        ERRORS=$((ERRORS + 1))
    fi
done

# ── STEP 6: Lista modelli installati ─────────────────────────────────────────
print_step 6 $TOTAL_STEPS "Verifica finale..."

echo ""
echo "${BOLD}Modelli installati:${NC}"
ollama list 2>/dev/null || echo "Nessun modello trovato"

# ── REPORT FINALE ────────────────────────────────────────────────────────────
echo ""
echo "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
if [ $ERRORS -eq 0 ]; then
    echo "${GREEN}${BOLD}  🏆 SETUP COMPLETATO — ZERO ERRORI${NC}"
    echo "${GREEN}${BOLD}  Tutti i modelli AI locali sono attivi e permanenti${NC}"
else
    echo "${YELLOW}${BOLD}  ⚠️  SETUP COMPLETATO CON ${ERRORS} AVVISO/I${NC}"
    echo "${YELLOW}${BOLD}  Alcuni modelli potrebbero richiedere retry manuale${NC}"
fi
echo "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Per applicare gli alias, esegui:  ${BOLD}source ~/.zshrc${NC}"
echo "Oppure riapri il Terminale."
echo ""
