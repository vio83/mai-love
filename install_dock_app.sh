#!/bin/bash
# ============================================================
# VIO 83 AI ORCHESTRA — DOCK APP INSTALLER
# Copyright (c) 2026 Viorica Porcu (vio83). All Rights Reserved.
# Crea un .app bundle con icona personalizzata e lo aggiunge al Dock
# ============================================================

set -e

# === CONFIGURAZIONE ===
PROJECT_DIR="$HOME/Projects/vio83-ai-orchestra"
APP_NAME="VIO 83 AI Orchestra"
APP_DIR="$HOME/Applications"
APP_PATH="$APP_DIR/$APP_NAME.app"
ICON_SOURCE="$PROJECT_DIR/dock-icon.png"
ICON_FALLBACK="$PROJECT_DIR/src-tauri/icons/icon.png"

CYAN='\033[0;36m'
GOLD='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[VIO83]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[✓]${NC} $1"; }
log_err()   { echo -e "${RED}[✗]${NC} $1"; }
log_gold()  { echo -e "${GOLD}[★]${NC} $1"; }

echo ""
echo -e "${GOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GOLD}║  ★  VIO 83 AI ORCHESTRA — DOCK INSTALLER  ★        ║${NC}"
echo -e "${GOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# === VERIFICA PROGETTO ===
if [ ! -d "$PROJECT_DIR" ]; then
    log_err "Directory progetto non trovata: $PROJECT_DIR"
    exit 1
fi

# === CREA DIRECTORY APPLICAZIONI UTENTE ===
mkdir -p "$APP_DIR"

# === RIMUOVI APP PRECEDENTE ===
if [ -d "$APP_PATH" ]; then
    log_info "Rimozione versione precedente..."
    rm -rf "$APP_PATH"
fi

# === CREA STRUTTURA .APP ===
log_gold "Creazione bundle $APP_NAME.app..."

mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# === Info.plist ===
cat > "$APP_PATH/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>VIO 83 AI Orchestra</string>
    <key>CFBundleDisplayName</key>
    <string>VIO 83 AI Orchestra</string>
    <key>CFBundleIdentifier</key>
    <string>com.vio83.ai-orchestra</string>
    <key>CFBundleVersion</key>
    <string>0.1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>VIO8</string>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2026 Viorica Porcu (vio83). All Rights Reserved.</string>
</dict>
</plist>
PLIST
log_ok "Info.plist creato"

# === SCRIPT ESEGUIBILE ===
cat > "$APP_PATH/Contents/MacOS/launch" << 'LAUNCHER'
#!/bin/bash
# VIO 83 AI ORCHESTRA — App Launcher v3 (FIXED)
PROJECT_DIR="$HOME/Projects/vio83-ai-orchestra"
BACKEND_PORT=4000
FRONTEND_PORT=5173
LOG_DIR="$PROJECT_DIR/.logs"
PID_FILE="$LOG_DIR/orchestra.pids"
mkdir -p "$LOG_DIR"

cleanup() {
    if [ -f "$PID_FILE" ]; then
        while read -r pid; do kill "$pid" 2>/dev/null; done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    lsof -ti:$BACKEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:$FRONTEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
}
trap cleanup EXIT

lsof -ti:$BACKEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:$FRONTEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1
cd "$PROJECT_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.nvm/versions/node/$(ls $HOME/.nvm/versions/node/ 2>/dev/null | sort -V | tail -1)/bin:$PATH"
[ -s "$HOME/.nvm/nvm.sh" ] && source "$HOME/.nvm/nvm.sh"

# FIX: Installa node_modules se mancanti
[ ! -d "$PROJECT_DIR/node_modules" ] && npm install --legacy-peer-deps > "$LOG_DIR/npm_install.log" 2>&1

# FIX: Backend con uvicorn diretto (stabile con Python 3.14)
python3 -c "
import uvicorn
uvicorn.run('backend.api.server:app', host='0.0.0.0', port=$BACKEND_PORT, log_level='info', timeout_keep_alive=120)
" > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$PID_FILE"

# FIX: Frontend con npx vite diretto
npx vite --host > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" >> "$PID_FILE"

WAITED=0
while ! lsof -ti:$FRONTEND_PORT &>/dev/null; do
    sleep 1; WAITED=$((WAITED + 1))
    [ $WAITED -ge 45 ] && break
done
sleep 2

if [ -d "/Applications/Orion.app" ]; then
    open -a "/Applications/Orion.app" "http://localhost:$FRONTEND_PORT"
elif [ -d "/Applications/Orion RC.app" ]; then
    open -a "/Applications/Orion RC.app" "http://localhost:$FRONTEND_PORT"
else
    open "http://localhost:$FRONTEND_PORT"
fi
osascript -e 'display notification "Orchestra attiva!" with title "VIO 83 AI Orchestra"'

while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        python3 -c "import uvicorn; uvicorn.run('backend.api.server:app', host='0.0.0.0', port=$BACKEND_PORT, log_level='info', timeout_keep_alive=120)" > "$LOG_DIR/backend.log" 2>&1 &
        BACKEND_PID=$!; echo "$BACKEND_PID" > "$PID_FILE"; echo "$FRONTEND_PID" >> "$PID_FILE"
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        npx vite --host > "$LOG_DIR/frontend.log" 2>&1 &
        FRONTEND_PID=$!; echo "$BACKEND_PID" > "$PID_FILE"; echo "$FRONTEND_PID" >> "$PID_FILE"
    fi
    sleep 5
done
LAUNCHER

chmod +x "$APP_PATH/Contents/MacOS/launch"
log_ok "Eseguibile launcher creato"

# === CREA ICONA .icns ===
log_gold "Generazione icona macOS (.icns)..."

# Usa l'immagine cyberpunk se presente, altrimenti l'icona del progetto
if [ -f "$ICON_SOURCE" ]; then
    SOURCE_IMG="$ICON_SOURCE"
    log_info "Uso immagine cyberpunk: $ICON_SOURCE"
elif [ -f "$ICON_FALLBACK" ]; then
    SOURCE_IMG="$ICON_FALLBACK"
    log_info "Uso icona progetto: $ICON_FALLBACK"
else
    log_err "Nessuna icona trovata!"
    log_info "Posiziona l'immagine come: $ICON_SOURCE"
    SOURCE_IMG=""
fi

if [ -n "$SOURCE_IMG" ]; then
    ICONSET_DIR="$PROJECT_DIR/.tmp_iconset.iconset"
    mkdir -p "$ICONSET_DIR"

    # Genera tutte le dimensioni richieste per .icns
    sips -z 16 16     "$SOURCE_IMG" --out "$ICONSET_DIR/icon_16x16.png"      2>/dev/null
    sips -z 32 32     "$SOURCE_IMG" --out "$ICONSET_DIR/icon_16x16@2x.png"   2>/dev/null
    sips -z 32 32     "$SOURCE_IMG" --out "$ICONSET_DIR/icon_32x32.png"      2>/dev/null
    sips -z 64 64     "$SOURCE_IMG" --out "$ICONSET_DIR/icon_32x32@2x.png"   2>/dev/null
    sips -z 128 128   "$SOURCE_IMG" --out "$ICONSET_DIR/icon_128x128.png"    2>/dev/null
    sips -z 256 256   "$SOURCE_IMG" --out "$ICONSET_DIR/icon_128x128@2x.png" 2>/dev/null
    sips -z 256 256   "$SOURCE_IMG" --out "$ICONSET_DIR/icon_256x256.png"    2>/dev/null
    sips -z 512 512   "$SOURCE_IMG" --out "$ICONSET_DIR/icon_256x256@2x.png" 2>/dev/null
    sips -z 512 512   "$SOURCE_IMG" --out "$ICONSET_DIR/icon_512x512.png"    2>/dev/null
    sips -z 1024 1024 "$SOURCE_IMG" --out "$ICONSET_DIR/icon_512x512@2x.png" 2>/dev/null

    # Converti in .icns
    iconutil -c icns "$ICONSET_DIR" -o "$APP_PATH/Contents/Resources/AppIcon.icns"

    # Pulisci
    rm -rf "$ICONSET_DIR"
    log_ok "Icona .icns generata con successo"
else
    log_info "App creata senza icona personalizzata"
fi

# === REGISTRA APP CON LAUNCH SERVICES ===
log_info "Registrazione app con macOS Launch Services..."
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP_PATH" 2>/dev/null || true
log_ok "App registrata"

# === AGGIUNGI AL DOCK ===
log_gold "Aggiunta al Dock macOS..."

# Verifica se già presente nel Dock
DOCK_CHECK=$(defaults read com.apple.dock persistent-apps 2>/dev/null | grep -c "ai-orchestra" || true)

if [ "$DOCK_CHECK" -gt 0 ]; then
    log_info "App già presente nel Dock, aggiornamento..."
    # Rimuovi vecchia entry
    DOCK_APPS=$(defaults read com.apple.dock persistent-apps 2>/dev/null)
fi

# Aggiungi al Dock usando defaults
defaults write com.apple.dock persistent-apps -array-add "<dict>
    <key>tile-data</key>
    <dict>
        <key>file-data</key>
        <dict>
            <key>_CFURLString</key>
            <string>file://$APP_PATH/</string>
            <key>_CFURLStringType</key>
            <integer>15</integer>
        </dict>
        <key>file-label</key>
        <string>VIO 83 AI Orchestra</string>
        <key>file-type</key>
        <integer>41</integer>
    </dict>
    <key>tile-type</key>
    <string>file-tile</string>
</dict>"

# Riavvia il Dock per applicare le modifiche
killall Dock

log_ok "App aggiunta al Dock!"

# === CREA ANCHE SCRIPT DI STOP ===
cat > "$PROJECT_DIR/stop_orchestra.sh" << 'STOP'
#!/bin/bash
# VIO 83 AI ORCHESTRA — STOP
echo "Arresto VIO 83 AI Orchestra..."
PID_FILE="$HOME/Projects/vio83-ai-orchestra/.logs/orchestra.pids"
if [ -f "$PID_FILE" ]; then
    while read -r pid; do
        kill "$pid" 2>/dev/null && echo "Processo $pid terminato"
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi
lsof -ti:4000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || true
echo "✓ Orchestra fermata."
osascript -e 'display notification "Tutti i servizi fermati" with title "VIO 83 AI Orchestra" subtitle "Orchestra spenta"'
STOP
chmod +x "$PROJECT_DIR/stop_orchestra.sh"

# === RISULTATO FINALE ===
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}  ${GOLD}★  INSTALLAZIONE COMPLETATA CON SUCCESSO!  ★${NC}           ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  App:      ${CYAN}$APP_PATH${NC}    ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Dock:     ${CYAN}Icona aggiunta al Dock${NC}                        ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Frontend: ${CYAN}http://localhost:5173${NC}                         ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Backend:  ${CYAN}http://localhost:4000${NC}                         ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${GOLD}Clicca l'icona nel Dock per avviare!${NC}                   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${GOLD}Per fermare: ./stop_orchestra.sh${NC}                        ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Notifica finale
osascript -e 'display notification "Clicca l'\''icona nel Dock per avviare!" with title "VIO 83 AI Orchestra" subtitle "Installazione completata ★"'
