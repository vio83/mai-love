#!/bin/bash
# ============================================================
# VIO 83 AI ORCHESTRA — LAUNCHER v3 (FIXED)
# Copyright (c) 2026 Viorica Porcu (vio83). All Rights Reserved.
# Avvia Backend + Frontend e apre SEMPRE in Orion
# ============================================================

# FIX: RIMOSSO "set -e" — causava uscita prematura dello script
#      quando wait_for_port o npm install fallivano, triggerando
#      il trap cleanup che uccideva ANCHE il backend funzionante.

# === CONFIGURAZIONE ===
PROJECT_DIR="$HOME/Projects/vio83-ai-orchestra"
BACKEND_PORT=4000
FRONTEND_PORT=5173
LOG_DIR="$PROJECT_DIR/.logs"
PID_FILE="$LOG_DIR/orchestra.pids"
MAX_RETRIES=3
RUNTIME_START_SCRIPT="$PROJECT_DIR/scripts/runtime/start_runtime_services.sh"
RUNTIME_STOP_SCRIPT="$PROJECT_DIR/scripts/runtime/stop_runtime_services.sh"

# === COLORI TERMINALE ===
CYAN='\033[0;36m'
GOLD='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# === FUNZIONI ===
log_info()  { echo -e "${CYAN}[VIO83]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[✓]${NC} $1"; }
log_err()   { echo -e "${RED}[✗]${NC} $1"; }
log_gold()  { echo -e "${GOLD}[★]${NC} $1"; }

cleanup() {
    log_info "Arresto VIO 83 AI Orchestra..."
    if [ -f "$RUNTIME_STOP_SCRIPT" ]; then
        bash "$RUNTIME_STOP_SCRIPT" >/dev/null 2>&1 || true
    fi
    if [ -f "$PID_FILE" ]; then
        while read -r pid; do
            kill "$pid" 2>/dev/null && log_info "Processo $pid terminato"
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    lsof -ti:$BACKEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:$FRONTEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
    log_ok "Orchestra fermata."
    exit 0
}

trap cleanup SIGINT SIGTERM

check_dependencies() {
    log_info "Controllo dipendenze..."
    if ! command -v python3 &>/dev/null; then
        log_err "Python3 non trovato! Installalo con: brew install python3"
        return 1
    fi
    log_ok "Python3: $(python3 --version)"

    if ! command -v node &>/dev/null; then
        log_err "Node.js non trovato! Installalo con: brew install node"
        return 1
    fi
    log_ok "Node.js: $(node --version)"

    if ! command -v npm &>/dev/null; then
        log_err "npm non trovato!"
        return 1
    fi
    log_ok "npm: $(npm --version)"

    # Controlla e installa dipendenze Python mancanti
    log_info "Controllo dipendenze Python..."
    if ! python3 -c "import sentence_transformers" 2>/dev/null; then
        log_gold "Installazione sentence_transformers..."
        pip3 install sentence_transformers --quiet || log_err "Impossibile installare sentence_transformers"
    else
        log_ok "sentence_transformers già installato"
    fi

    return 0
}

kill_existing() {
    log_info "Pulizia processi esistenti sulle porte $BACKEND_PORT e $FRONTEND_PORT..."
    lsof -ti:$BACKEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:$FRONTEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
    sleep 1
}

wait_for_port() {
    local port=$1
    local name=$2
    local max_wait=${3:-45}
    local waited=0

    while ! lsof -ti:$port &>/dev/null; do
        sleep 1
        waited=$((waited + 1))
        if [ $waited -ge $max_wait ]; then
            log_err "$name non si è avviato entro ${max_wait}s!"
            return 1
        fi
    done
    log_ok "$name attivo sulla porta $port (${waited}s)"
    return 0
}

open_in_orion() {
    local url=$1
    if [ -d "/Applications/Orion.app" ]; then
        open -a "/Applications/Orion.app" "$url"
    elif [ -d "/Applications/Orion RC.app" ]; then
        open -a "/Applications/Orion RC.app" "$url"
    else
        log_info "Orion non trovato, uso browser predefinito"
        open "$url"
    fi
}

# === BANNER ===
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}  ${GOLD}★  VIO 83 AI ORCHESTRA  ★${NC}                          ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  Multi-Provider AI Orchestration Platform             ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  Copyright (c) 2026 Viorica Porcu                    ${CYAN}║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# === CONTROLLI ===
if [ ! -d "$PROJECT_DIR" ]; then
    log_err "Directory progetto non trovata: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"
mkdir -p "$LOG_DIR"

check_dependencies || exit 1
kill_existing

# === FIX: INSTALLA DIPENDENZE NODE SE MANCANTI ===
if [ ! -d "$PROJECT_DIR/node_modules" ]; then
    log_gold "node_modules non trovato — installazione dipendenze npm..."
    npm install --legacy-peer-deps > "$LOG_DIR/npm_install.log" 2>&1
    if [ $? -eq 0 ]; then
        log_ok "Dipendenze npm installate con successo"
    else
        log_err "npm install fallito! Log: $LOG_DIR/npm_install.log"
        tail -10 "$LOG_DIR/npm_install.log"
        log_err "Il frontend non potrà partire."
    fi
else
    log_ok "node_modules presente"
fi

# === TEST RAPIDO: il backend importa correttamente? ===
log_gold "Test rapido import backend..."
if python3 -c "from backend.api.server import app; print('Import OK')" 2>"$LOG_DIR/import_test.log"; then
    log_ok "Backend import test superato"
else
    log_err "Backend NON riesce ad importare! Errore:"
    cat "$LOG_DIR/import_test.log"
    echo ""
    log_err "Correggi l'errore sopra prima di avviare."
    exit 1
fi

# === AVVIO BACKEND (FastAPI con uvicorn) ===
log_gold "Avvio Backend FastAPI sulla porta $BACKEND_PORT..."
uvicorn backend.api.server:app --host 0.0.0.0 --port $BACKEND_PORT --log-level info --timeout-keep-alive 120 > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$PID_FILE"
log_info "Backend PID: $BACKEND_PID"

# === AVVIO FRONTEND (Vite) ===
log_gold "Avvio Frontend Vite sulla porta $FRONTEND_PORT..."
npx vite --host > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" >> "$PID_FILE"
log_info "Frontend PID: $FRONTEND_PID"

# === ATTESA PORTE ===
log_info "Attendo avvio servizi..."
wait_for_port $BACKEND_PORT "Backend FastAPI" 45 || true
wait_for_port $FRONTEND_PORT "Frontend Vite" 45 || true

# === AVVIO SUPERVISOR RUNTIME SERVICES (OpenClaw / LegalRoom / n8n) ===
if [ -f "$RUNTIME_START_SCRIPT" ]; then
    log_gold "Avvio Runtime Services Supervisor..."
    if bash "$RUNTIME_START_SCRIPT" >> "$LOG_DIR/runtime-supervisor-launch.log" 2>&1; then
        log_ok "Runtime Services Supervisor attivo"
    else
        log_err "Runtime Services Supervisor non avviato (controlla $LOG_DIR/runtime-supervisor.log)"
    fi
fi

# === APRI ORION ===
sleep 2
log_gold "Apertura Orion su http://localhost:$FRONTEND_PORT ..."
open_in_orion "http://localhost:$FRONTEND_PORT"

# === NOTIFICA macOS ===
osascript -e 'display notification "Frontend: localhost:5173 | Backend: localhost:4000" with title "VIO 83 AI Orchestra" subtitle "Orchestra attiva! ★"' 2>/dev/null || true

# === STATUS FINALE ===
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}  ${GOLD}VIO 83 AI ORCHESTRA — ATTIVA!${NC}                       ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                      ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Frontend: ${CYAN}http://localhost:$FRONTEND_PORT${NC}                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Backend:  ${CYAN}http://localhost:$BACKEND_PORT${NC}                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Browser:  ${CYAN}Orion${NC}                                    ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Logs:     ${CYAN}$LOG_DIR/${NC}              ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                      ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Premi ${RED}Ctrl+C${NC} per fermare l'orchestra                ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# === MANTIENI ATTIVO CON LIMITE RETRY ===
BACKEND_RETRIES=0
FRONTEND_RETRIES=0

log_info "Orchestra in esecuzione. Monitoraggio processi (max $MAX_RETRIES retry)..."
while true; do
    # Verifica backend
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        BACKEND_RETRIES=$((BACKEND_RETRIES + 1))
        if [ $BACKEND_RETRIES -gt $MAX_RETRIES ]; then
            log_err "Backend crashato $MAX_RETRIES volte! Stop retry automatico."
            log_err "Ultimo errore in: $LOG_DIR/backend.log"
            echo -e "${RED}=== ULTIME 20 RIGHE DEL LOG BACKEND ===${NC}"
            tail -20 "$LOG_DIR/backend.log" 2>/dev/null || echo "(log vuoto)"
            log_info "Per diagnostica: python3 -m backend.api.server"
            log_info "Il frontend resta attivo su http://localhost:$FRONTEND_PORT"
            while true; do
                if ! kill -0 $FRONTEND_PID 2>/dev/null; then
                    log_err "Anche il frontend si è fermato. Uscita."
                    exit 1
                fi
                sleep 10
            done
        fi
        log_err "Backend crashato! (tentativo $BACKEND_RETRIES/$MAX_RETRIES)"
        tail -5 "$LOG_DIR/backend.log" 2>/dev/null
        log_info "Riavvio backend..."
        uvicorn backend.api.server:app --host 0.0.0.0 --port $BACKEND_PORT --log-level info --timeout-keep-alive 120 > "$LOG_DIR/backend.log" 2>&1 &
        BACKEND_PID=$!
        echo "$BACKEND_PID" > "$PID_FILE"
        echo "$FRONTEND_PID" >> "$PID_FILE"
        log_ok "Backend riavviato con PID: $BACKEND_PID"
        sleep 5
    fi

    # Verifica frontend
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        FRONTEND_RETRIES=$((FRONTEND_RETRIES + 1))
        if [ $FRONTEND_RETRIES -gt $MAX_RETRIES ]; then
            log_err "Frontend crashato $MAX_RETRIES volte!"
            tail -10 "$LOG_DIR/frontend.log" 2>/dev/null
            exit 1
        fi
        log_err "Frontend crashato! (tentativo $FRONTEND_RETRIES/$MAX_RETRIES)"
        log_info "Riavvio frontend..."
        npx vite --host > "$LOG_DIR/frontend.log" 2>&1 &
        FRONTEND_PID=$!
        echo "$BACKEND_PID" > "$PID_FILE"
        echo "$FRONTEND_PID" >> "$PID_FILE"
        log_ok "Frontend riavviato con PID: $FRONTEND_PID"
        sleep 5
    fi

    sleep 5
done
