#!/usr/bin/env bash
# ============================================================
# VIO 83 AI Orchestra — Genera chiavi Tauri Updater
# Esegui UNA VOLTA sul tuo Mac prima del primo release.
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
KEYS_DIR="$PROJECT_ROOT/.tauri-keys"

echo "🔐 VIO 83 — Generazione chiavi Tauri Updater"
echo "============================================"
echo ""

# Verifica che tauri CLI sia installato
if ! command -v cargo &>/dev/null; then
    echo "❌ Cargo/Rust non trovato. Installa: https://rustup.rs"
    exit 1
fi

if ! command -v npx &>/dev/null; then
    echo "❌ npx non trovato. Installa Node.js."
    exit 1
fi

# Crea directory sicura per le chiavi
mkdir -p "$KEYS_DIR"
chmod 700 "$KEYS_DIR"

echo "📁 Directory chiavi: $KEYS_DIR"
echo ""

# Genera coppia di chiavi
echo "🔑 Generazione coppia chiavi minisign..."
npx @tauri-apps/cli@latest signer generate \
    --output "$KEYS_DIR/vio83-updater" \
    --force

echo ""
echo "✅ Chiavi generate:"
echo "   Privata: $KEYS_DIR/vio83-updater"
echo "   Pubblica: $KEYS_DIR/vio83-updater.pub"
echo ""

# Leggi la chiave pubblica
PUBKEY=$(cat "$KEYS_DIR/vio83-updater.pub")
echo "📋 CHIAVE PUBBLICA (copia in tauri.conf.json → plugins.updater.pubkey):"
echo ""
echo "$PUBKEY"
echo ""

# Aggiorna automaticamente tauri.conf.json
TAURI_CONF="$PROJECT_ROOT/src-tauri/tauri.conf.json"
if command -v jq &>/dev/null; then
    echo "🔧 Aggiorno tauri.conf.json automaticamente..."
    PUBKEY_B64=$(cat "$KEYS_DIR/vio83-updater.pub" | base64 | tr -d '\n')
    jq --arg pk "$PUBKEY_B64" '.plugins.updater.pubkey = $pk' "$TAURI_CONF" > "$TAURI_CONF.tmp"
    mv "$TAURI_CONF.tmp" "$TAURI_CONF"
    echo "✅ tauri.conf.json aggiornato con la chiave pubblica reale."
else
    echo "⚠️  jq non trovato. Aggiorna manualmente tauri.conf.json:"
    echo "   plugins.updater.pubkey = $(cat "$KEYS_DIR/vio83-updater.pub")"
fi

# Istruzioni per GitHub Actions
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 PASSAGGI SUCCESSIVI:"
echo ""
echo "1. Aggiungi la chiave privata come GitHub Secret:"
echo "   Nome secret: TAURI_PRIVATE_KEY"
echo "   Valore: $(cat "$KEYS_DIR/vio83-updater")"
echo ""
echo "2. Aggiungi la password come GitHub Secret:"
echo "   Nome secret: TAURI_KEY_PASSWORD"
echo "   Valore: (la password inserita durante la generazione)"
echo ""
echo "3. Per fare un release:"
echo "   git tag v0.9.0 && git push origin v0.9.0"
echo "   → GitHub Actions costruirà e firmerà automaticamente il .dmg"
echo ""
echo "⚠️  SICUREZZA: Non committare mai $KEYS_DIR/ su Git!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Aggiungi le chiavi al .gitignore
GITIGNORE="$PROJECT_ROOT/.gitignore"
if ! grep -q ".tauri-keys" "$GITIGNORE" 2>/dev/null; then
    echo "" >> "$GITIGNORE"
    echo "# Tauri updater private keys — MAI su Git" >> "$GITIGNORE"
    echo ".tauri-keys/" >> "$GITIGNORE"
    echo "✅ .tauri-keys/ aggiunto a .gitignore"
fi
