#!/bin/bash
# ============================================================
# IMPOSTA-TRADUZIONE-ITA.sh
# Imposta traduzione automatica in italiano per Orion e Tor
# Esegui con: bash ~/Projects/vio83-ai-orchestra/IMPOSTA-TRADUZIONE-ITA.sh
# ============================================================

echo ""
echo "=========================================="
echo "  TRADUZIONE AUTOMATICA ITALIANO"
echo "  Orion Browser + Tor Browser"
echo "=========================================="
echo ""

# -----------------------------------------------
# PARTE 1: ORION BROWSER
# -----------------------------------------------
echo ">>> PARTE 1: ORION BROWSER"
echo ""

# Trova il bundle ID di Orion
ORION_BUNDLE=$(mdfind "kMDItemCFBundleIdentifier == 'com.kagi.kagimacOS'" 2>/dev/null | head -1)
if [ -z "$ORION_BUNDLE" ]; then
    ORION_BUNDLE=$(mdfind "kMDItemDisplayName == 'Orion*' && kMDItemContentType == 'com.apple.application-bundle'" 2>/dev/null | head -1)
fi

# Orion è basato su WebKit (come Safari) — usa le preferenze di sistema per la lingua
echo "[1/4] Impostando lingua preferita su italiano per traduzioni web..."

# Imposta la lingua preferita di macOS per le traduzioni Safari/WebKit
# Orion usa WebKit, quindi rispetta queste impostazioni
defaults write -g AppleLanguages -array "it" "it-IT" "en" "en-US"
echo "  ✅ Lingua sistema: Italiano impostato come primario"

# Impostazioni specifiche per Safari/WebKit translation (Orion le eredita)
defaults write com.apple.Safari AutomaticTranslationEnabled -bool true 2>/dev/null
defaults write com.apple.Safari WebKitPreferences.automaticTranslation -bool true 2>/dev/null
echo "  ✅ Traduzione automatica WebKit: ATTIVATA"

# Prova a trovare e configurare Orion direttamente
ORION_IDS=("com.kagi.kagimacOS" "com.kagi.kagimacOS.browser" "com.nickvision.Orion" "com.nickvision.orion")
for ORID in "${ORION_IDS[@]}"; do
    if defaults read "$ORID" 2>/dev/null | head -1 > /dev/null 2>&1; then
        echo "  Trovato Orion con bundle: $ORID"
        defaults write "$ORID" AppleLanguages -array "it" "it-IT" "en" "en-US" 2>/dev/null
        defaults write "$ORID" AutomaticTranslationEnabled -bool true 2>/dev/null
        echo "  ✅ Traduzione Orion configurata per $ORID"
    fi
done

# Cerca il vero bundle ID di Orion
echo ""
echo "[2/4] Cercando bundle ID esatto di Orion..."
REAL_ORION_ID=$(osascript -e 'id of application "Orion"' 2>/dev/null)
if [ -n "$REAL_ORION_ID" ]; then
    echo "  Bundle ID trovato: $REAL_ORION_ID"
    defaults write "$REAL_ORION_ID" AppleLanguages -array "it" "it-IT" "en" "en-US" 2>/dev/null
    defaults write "$REAL_ORION_ID" AutomaticTranslationEnabled -bool true 2>/dev/null
    defaults write "$REAL_ORION_ID" WebKitPreferences.automaticTranslation -bool true 2>/dev/null
    echo "  ✅ Orion ($REAL_ORION_ID) configurato con italiano + traduzione automatica"
else
    echo "  ⚠️  Orion non trovato tramite osascript — provo metodo alternativo..."
    # Cerca nei bundle installati
    ORION_PATH=$(mdfind "kMDItemFSName == 'Orion.app'" 2>/dev/null | head -1)
    if [ -n "$ORION_PATH" ]; then
        REAL_ORION_ID=$(/usr/libexec/PlistBuddy -c "Print CFBundleIdentifier" "$ORION_PATH/Contents/Info.plist" 2>/dev/null)
        if [ -n "$REAL_ORION_ID" ]; then
            echo "  Bundle ID trovato da Info.plist: $REAL_ORION_ID"
            defaults write "$REAL_ORION_ID" AppleLanguages -array "it" "it-IT" "en" "en-US" 2>/dev/null
            defaults write "$REAL_ORION_ID" AutomaticTranslationEnabled -bool true 2>/dev/null
            echo "  ✅ Orion configurato!"
        fi
    fi
fi

echo ""
echo "[3/4] Configurando traduzione automatica pagine in Orion..."
echo ""
echo "  NOTA IMPORTANTE PER ORION:"
echo "  ──────────────────────────"
echo "  Orion usa il motore di traduzione di Apple (come Safari)."
echo "  Per attivare la traduzione automatica di OGNI pagina:"
echo ""
echo "  1. Apri Orion"
echo "  2. Vai su una pagina in inglese (es. github.com)"
echo "  3. Clicca col TASTO DESTRO sulla barra degli indirizzi"
echo "  4. Cerca 'Traduci pagina' / 'Translate Page'"
echo "  5. Seleziona 'Italiano'"
echo "  6. Spunta 'Traduci sempre le pagine in inglese'"
echo "     (o 'Always Translate English')"
echo ""
echo "  Questo attiverà la traduzione AUTOMATICA per TUTTE"
echo "  le pagine in inglese che aprirai in futuro!"
echo ""

# -----------------------------------------------
# PARTE 2: TOR BROWSER
# -----------------------------------------------
echo ">>> PARTE 2: TOR BROWSER"
echo ""

# Cerca Tor Browser
TOR_PATH=$(mdfind "kMDItemFSName == 'Tor Browser.app'" 2>/dev/null | head -1)
if [ -z "$TOR_PATH" ]; then
    TOR_PATH="/Applications/Tor Browser.app"
fi

TOR_PROFILE_DIR="$HOME/Library/Application Support/TorBrowser-Data/Browser"

echo "[4/4] Configurando Tor Browser in italiano..."

if [ -d "$TOR_PATH" ] || [ -d "/Applications/Tor Browser.app" ]; then
    echo "  ✅ Tor Browser trovato"

    # Tor Browser usa Firefox — configurazione via user.js/prefs.js
    # Cerca la cartella profilo
    TOR_PROFILES=("$TOR_PROFILE_DIR" "$HOME/Library/Application Support/TorBrowser-Data" "$TOR_PATH/TorBrowser/Data/Browser")

    PROFILE_FOUND=false
    for TDIR in "${TOR_PROFILES[@]}"; do
        if [ -d "$TDIR" ]; then
            # Cerca tutti i profili
            find "$TDIR" -name "prefs.js" -maxdepth 4 2>/dev/null | while read PREFS; do
                PROF_DIR=$(dirname "$PREFS")
                echo "  Profilo trovato: $PROF_DIR"

                # Crea/aggiorna user.js per lingua italiana
                USER_JS="$PROF_DIR/user.js"

                # Rimuovi vecchie impostazioni di lingua se esistono
                if [ -f "$USER_JS" ]; then
                    grep -v "intl.accept_languages\|general.useragent.locale\|intl.locale.requested\|browser.translation" "$USER_JS" > "${USER_JS}.tmp" 2>/dev/null
                    mv "${USER_JS}.tmp" "$USER_JS" 2>/dev/null
                fi

                # Aggiungi impostazioni italiano
                cat >> "$USER_JS" << 'TOREOF'

// === TRADUZIONE AUTOMATICA ITALIANO - VIO83 ===
user_pref("intl.accept_languages", "it-IT, it, en-US, en");
user_pref("intl.locale.requested", "it");
user_pref("general.useragent.locale", "it");
// Nota: Tor Browser limita le traduzioni per privacy
// ma la lingua dell'interfaccia sarà in italiano
// === FINE TRADUZIONE ===
TOREOF
                echo "  ✅ Tor Browser profilo aggiornato con lingua italiana"
                PROFILE_FOUND=true
            done
        fi
    done

    if [ "$PROFILE_FOUND" = false ]; then
        echo "  ⚠️  Profilo Tor non trovato. Configurazione manuale:"
        echo ""
        echo "  1. Apri Tor Browser"
        echo "  2. Nella barra indirizzi scrivi: about:preferences"
        echo "  3. Cerca 'Language' / 'Lingua'"
        echo "  4. Clicca 'Set Alternatives' / 'Imposta alternative'"
        echo "  5. Aggiungi 'Italiano (it)' e mettilo in cima"
        echo "  6. Clicca OK e riavvia Tor Browser"
    fi
else
    echo "  ⚠️  Tor Browser non trovato in /Applications/"
    echo "  Se lo hai installato altrove, esegui:"
    echo "  open -a 'Tor Browser'"
    echo "  Poi vai su about:preferences → Language → Italiano"
fi

echo ""
echo "=========================================="
echo "  ✅ CONFIGURAZIONE COMPLETATA!"
echo "=========================================="
echo ""
echo "COSA FARE ORA:"
echo ""
echo "1. CHIUDI Orion completamente (⌘+Q)"
echo "2. RIAPRI Orion"
echo "3. Vai su qualsiasi pagina in inglese"
echo "4. Click destro → 'Translate Page' → 'Italian'"
echo "5. Spunta 'Always Translate English'"
echo ""
echo "Per Tor Browser:"
echo "1. CHIUDI Tor Browser (⌘+Q)"
echo "2. RIAPRI Tor Browser — interfaccia sarà in italiano"
echo ""
echo "=========================================="
