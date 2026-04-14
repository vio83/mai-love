#!/bin/bash
# === Installa TUTTI i modelli Ollama su iMac Archimede ===
# Eseguire localmente sull'iMac, OR via SSH dal Mac Air.
# NON tocca i modelli già installati (phi4-mini:latest, llama3.2:1b).
# Autore: VIO83

set -euo pipefail

LOG="$HOME/ollama_install_all.log"
echo "=== Ollama Model Install $(date) ===" | tee "$LOG"

# Verifica Ollama attivo
if ! ollama list > /dev/null 2>&1; then
    echo "[ERRORE] Ollama non risponde. Verifica: systemctl status ollama" | tee -a "$LOG"
    exit 1
fi

echo "[INFO] Modelli già presenti:" | tee -a "$LOG"
ollama list 2>/dev/null | tee -a "$LOG"
echo "---" | tee -a "$LOG"

# Lista modelli da installare
MODELS=(
    "qwen2.5-coder:3b"
    "qwen2.5:3b"
    "llama3.2:3b"
    "nomic-embed-text"
    "deepseek-r1:1.5b"
    "smollm2:1.7b"
    "llama3.1:8b"
    "mxbai-embed-large"
    "all-minilm"
)

SUCCESS=0
FAIL=0

for model in "${MODELS[@]}"; do
    # Skip se già presente
    if ollama list 2>/dev/null | grep -q "^${model}"; then
        echo "[SKIP] $model già presente" | tee -a "$LOG"
        ((SUCCESS++))
        continue
    fi
    
    echo "[PULL] $model..." | tee -a "$LOG"
    for attempt in 1 2 3; do
        if ollama pull "$model" >> "$LOG" 2>&1; then
            echo "[OK] $model installato (tentativo $attempt)" | tee -a "$LOG"
            ((SUCCESS++))
            break
        else
            echo "[RETRY] $model fallito tentativo $attempt/3" | tee -a "$LOG"
            if [[ $attempt -eq 3 ]]; then
                echo "[FAIL] $model NON installato dopo 3 tentativi" | tee -a "$LOG"
                ((FAIL++))
            fi
            sleep 10
        fi
    done
done

echo "---" | tee -a "$LOG"
echo "[RISULTATO] Successi: $SUCCESS | Fallimenti: $FAIL" | tee -a "$LOG"
echo "[MODELLI FINALI]:" | tee -a "$LOG"
ollama list 2>/dev/null | tee -a "$LOG"
echo "=== Completato $(date) ===" | tee -a "$LOG"
