#!/bin/zsh
# ============================================================================
# VIO 83 AI ORCHESTRA — Setup Orion Browser come Default
# Copyright (c) 2026 Viorica Porcu (vio83). All Rights Reserved.
# ============================================================================
# Cosa fa questo script:
# 1. Verifica che Orion sia installato
# 2. Imposta Orion come browser predefinito
# 3. Esporta segnalibri e impostazioni base da Safari
# 4. Aggiorna launch_orchestra.sh per usare Orion
# ============================================================================
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

PROJECT_DIR="$HOME/Projects/vio83-ai-orchestra"
ERRORS=0
TOTAL_STEPS=5

print_header() {
    echo ""
    echo "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo "${CYAN}${BOLD}  VIO 83 AI ORCHESTRA — Setup Orion Browser${NC}"
    echo "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo "${YELLOW}▶ [STEP $1/$TOTAL_STEPS]${NC} $2"
}

print_ok() {
    echo "${GREEN}✅ $1${NC}"
}

print_fail() {
    echo "${RED}❌ $1${NC}"
}

print_warn() {
    echo "${YELLOW}⚠️  $1${NC}"
}

print_header

# ── STEP 1: Verifica che Orion sia installato ─────────────────────────────
print_step 1 "Verifica installazione Orion..."

ORION_APP=""
if [ -d "/Applications/Orion.app" ]; then
    ORION_APP="/Applications/Orion.app"
    print_ok "Orion trovato: /Applications/Orion.app"
elif [ -d "$HOME/Applications/Orion.app" ]; then
    ORION_APP="$HOME/Applications/Orion.app"
    print_ok "Orion trovato: ~/Applications/Orion.app"
elif [ -d "/Applications/Orion RC.app" ]; then
    ORION_APP="/Applications/Orion RC.app"
    print_ok "Orion RC trovato: /Applications/Orion RC.app"
else
    print_fail "Orion NON trovato!"
    echo ""
    echo "  Per installare Orion:"
    echo "  1. Visita https://browser.kagi.com/"
    echo "  2. Scarica e installa Orion"
    echo "  3. Riesegui questo script"
    echo ""
    echo "  Oppure installa via Homebrew:"
    echo "    brew install --cask orion"
    echo ""
    exit 1
fi

# Ottieni il Bundle ID di Orion
ORION_BUNDLE_ID=$(defaults read "${ORION_APP}/Contents/Info.plist" CFBundleIdentifier 2>/dev/null || echo "com.kagi.kagimacOS")
print_ok "Bundle ID Orion: $ORION_BUNDLE_ID"
echo ""

# ── STEP 2: Imposta Orion come browser predefinito ────────────────────────
print_step 2 "Impostazione Orion come browser predefinito..."

# macOS non ha un comando semplice per impostare il browser predefinito da CLI.
# Il modo più affidabile è usare lo strumento Swift/AppleScript oppure
# aprire le preferenze di sistema.
# Usiamo il metodo AppleScript che funziona su macOS.

# Metodo 1: Prova con defaultbrowser (se installato)
if command -v defaultbrowser &>/dev/null; then
    defaultbrowser orion 2>/dev/null && print_ok "Browser predefinito impostato con defaultbrowser" || true
else
    # Metodo 2: Apri Orion — quando Orion si apre per la prima volta,
    # chiede di diventare il browser predefinito
    echo "  Apertura Orion per impostazione browser predefinito..."
    echo "  ${BOLD}IMPORTANTE: Quando Orion ti chiede 'Vuoi impostare Orion come browser predefinito?'${NC}"
    echo "  ${BOLD}Clicca SÌ / YES${NC}"
    echo ""

    # Apri Orion
    open -a "${ORION_APP}"
    sleep 3

    # Prova anche via AppleScript
    osascript -e '
    tell application "System Events"
        try
            tell application process "Orion"
                -- Se c'è un dialog per impostare come default, accettalo
                if exists (button "Use Orion" of window 1) then
                    click button "Use Orion" of window 1
                end if
            end tell
        end try
    end tell
    ' 2>/dev/null || true

    print_warn "Se Orion non è ancora il browser predefinito:"
    echo "    1. Apri Preferenze di Sistema → Generali → Browser web predefinito"
    echo "    2. Seleziona Orion dalla lista"
    echo "    OPPURE: brew install defaultbrowser && defaultbrowser orion"
fi
echo ""

# ── STEP 3: Esporta segnalibri da Safari ──────────────────────────────────
print_step 3 "Migrazione segnalibri da Safari a Orion..."

BOOKMARKS_DIR="$HOME/Desktop/safari_export"
mkdir -p "$BOOKMARKS_DIR"

# Esporta segnalibri Safari in formato HTML
SAFARI_BOOKMARKS="$HOME/Library/Safari/Bookmarks.plist"
if [ -f "$SAFARI_BOOKMARKS" ]; then
    # Copia i segnalibri Safari
    cp "$SAFARI_BOOKMARKS" "$BOOKMARKS_DIR/Safari_Bookmarks.plist" 2>/dev/null || true

    # Converti in HTML per importazione
    python3 -c "
import plistlib
import html
import sys

try:
    with open('$SAFARI_BOOKMARKS', 'rb') as f:
        plist = plistlib.load(f)

    output = ['<!DOCTYPE NETSCAPE-Bookmark-file-1>',
              '<META HTTP-EQUIV=\"Content-Type\" CONTENT=\"text/html; charset=UTF-8\">',
              '<TITLE>Bookmarks</TITLE>',
              '<H1>Bookmarks Safari Export</H1>',
              '<DL><p>']

    def process_children(children, indent=1):
        for item in children:
            prefix = '    ' * indent
            item_type = item.get('WebBookmarkType', '')
            if item_type == 'WebBookmarkTypeList':
                title = html.escape(item.get('Title', 'Folder'))
                output.append(f'{prefix}<DT><H3>{title}</H3>')
                output.append(f'{prefix}<DL><p>')
                process_children(item.get('Children', []), indent + 1)
                output.append(f'{prefix}</DL><p>')
            elif item_type == 'WebBookmarkTypeLeaf':
                url_dict = item.get('URIDictionary', {})
                title = html.escape(url_dict.get('title', ''))
                url = item.get('URLString', '')
                if url and not url.startswith('bookmarklet:'):
                    output.append(f'{prefix}<DT><A HREF=\"{url}\">{title}</A>')

    children = plist.get('Children', [])
    process_children(children)
    output.append('</DL><p>')

    with open('$BOOKMARKS_DIR/Safari_Bookmarks.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    print('Esportati')
except Exception as e:
    print(f'Errore: {e}')
" 2>/dev/null

    if [ -f "$BOOKMARKS_DIR/Safari_Bookmarks.html" ]; then
        print_ok "Segnalibri Safari esportati in: $BOOKMARKS_DIR/Safari_Bookmarks.html"
        echo "    Per importarli in Orion: File → Import Bookmarks → seleziona il file HTML"
    else
        print_warn "Esportazione segnalibri automatica non riuscita"
        echo "    Puoi esportare manualmente: Safari → File → Esporta Segnalibri"
    fi
else
    print_warn "File segnalibri Safari non trovato"
fi
echo ""

# ── STEP 4: Configura traduzione automatica in Orion ──────────────────────
print_step 4 "Nota sulla traduzione automatica..."

echo "  Orion ha traduzione integrata come Safari (basata su Apple Translate)."
echo "  Per attivarla:"
echo "    1. Apri Orion"
echo "    2. Vai su una pagina in inglese"
echo "    3. Clicca l'icona di traduzione nella barra degli indirizzi (aA)"
echo "    4. Seleziona 'Traduci in Italiano'"
echo ""
echo "  Per traduzione AUTOMATICA di tutti i siti:"
echo "    1. Orion → Preferences → Websites → Page Translation"
echo "    2. Imposta 'When visiting a page in English' → 'Always translate to Italian'"
echo ""
print_ok "Nota traduzione documentata"
echo ""

# ── STEP 5: Aggiorna launch_orchestra.sh per usare Orion ─────────────────
print_step 5 "Aggiornamento launcher VIO 83 AI Orchestra per Orion..."

LAUNCHER="$PROJECT_DIR/launch_orchestra.sh"
if [ -f "$LAUNCHER" ]; then
    # Sostituisci 'open "http://...' con 'open -a "ORION_APP" "http://...'
    if grep -q 'open "http://localhost' "$LAUNCHER"; then
        sed -i '' "s|open \"http://localhost:\$FRONTEND_PORT\"|open -a \"${ORION_APP}\" \"http://localhost:\$FRONTEND_PORT\"|" "$LAUNCHER"
        print_ok "launch_orchestra.sh aggiornato — ora apre con Orion"
    elif grep -q 'open -a' "$LAUNCHER"; then
        print_ok "launch_orchestra.sh già configurato per un browser specifico"
    else
        print_warn "Formato comando open non riconosciuto in launch_orchestra.sh"
    fi
else
    print_warn "launch_orchestra.sh non trovato in $PROJECT_DIR"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# ── NOTA SU SAFARI ────────────────────────────────────────────────────────
echo "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
echo "${YELLOW}${BOLD}  NOTA IMPORTANTE SU SAFARI${NC}"
echo "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "  Safari NON può essere disabilitato o rimosso da macOS."
echo "  Apple lo protegge con System Integrity Protection (SIP)."
echo "  Questo è un limite di sicurezza di Apple, non un bug."
echo ""
echo "  Quello che puoi fare:"
echo "  ${GREEN}✓${NC} Impostare Orion come browser predefinito (fatto sopra)"
echo "  ${GREEN}✓${NC} Rimuovere Safari dal Dock: trascina l'icona fuori dal Dock"
echo "  ${GREEN}✓${NC} Usare Orion per tutto: naviga, cerca, traduci"
echo "  ${RED}✗${NC} Disinstallare Safari (protetto da SIP)"
echo "  ${RED}✗${NC} Disabilitare Safari completamente (protetto da SIP)"
echo ""

# ── REPORT FINALE ─────────────────────────────────────────────────────────
echo "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
if [ $ERRORS -eq 0 ]; then
    echo "${GREEN}${BOLD}  🏆 SETUP ORION COMPLETATO${NC}"
else
    echo "${YELLOW}${BOLD}  ⚠️  SETUP COMPLETATO CON $ERRORS AVVISO/I${NC}"
fi
echo "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "  Prossimi passi:"
echo "  1. Conferma Orion come browser predefinito nelle Preferenze di Sistema"
echo "  2. Importa i segnalibri Safari: File → Import in Orion"
echo "  3. Configura traduzione automatica in Orion (vedi sopra)"
echo "  4. Rimuovi Safari dal Dock (trascina fuori)"
echo ""
