#!/usr/bin/env bash
# ============================================================
# VIO 83 AI ORCHESTRA — PEC ZIP DATA CERTA
# Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: AGPL-3.0 / Proprietary — See LICENSE files
# ============================================================
#
# Genera un archivio ZIP firmato SHA256 del codice sorgente
# per prova di data certa (invio PEC / deposito SIAE).
#
# Uso: bash scripts/pec_zip_data_certa.sh
# Output: data/pec/ con ZIP + SHA256 + manifesto
# ============================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S_UTC")
DATE_HUMAN=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
PEC_DIR="$PROJECT_ROOT/data/pec"
ZIP_NAME="vio83-ai-orchestra_source_${TIMESTAMP}.zip"
ZIP_PATH="$PEC_DIR/$ZIP_NAME"
SHA_PATH="$PEC_DIR/${ZIP_NAME}.sha256"
MANIFEST_PATH="$PEC_DIR/MANIFESTO_DATA_CERTA_${TIMESTAMP}.txt"

echo "═══════════════════════════════════════════════════════"
echo "  VIO 83 AI ORCHESTRA — PEC ZIP DATA CERTA"
echo "  Timestamp: $DATE_HUMAN"
echo "═══════════════════════════════════════════════════════"

# Crea directory output
mkdir -p "$PEC_DIR"

echo ""
echo "📦 Creazione archivio ZIP del codice sorgente..."
echo "   Esclude: node_modules, .git, __pycache__, venv, dist, data/, .env"

# Crea ZIP escludendo file non necessari e sensibili
zip -r "$ZIP_PATH" . \
  -x "node_modules/*" \
  -x ".git/*" \
  -x "__pycache__/*" \
  -x "*/__pycache__/*" \
  -x "venv/*" \
  -x ".venv/*" \
  -x "dist/*" \
  -x "data/*" \
  -x ".env" \
  -x ".env.*" \
  -x "*.pyc" \
  -x ".DS_Store" \
  -x "target/*" \
  -x "src-tauri/target/*" \
  -x ".pids/*" \
  -x "data/pec/*" \
  > /dev/null 2>&1

ZIP_SIZE=$(stat -f%z "$ZIP_PATH" 2>/dev/null || stat --printf="%s" "$ZIP_PATH" 2>/dev/null)
ZIP_SIZE_MB=$(echo "scale=2; $ZIP_SIZE / 1048576" | bc)

echo "   ✅ ZIP creato: $ZIP_NAME ($ZIP_SIZE_MB MB)"

# Calcola SHA256
echo ""
echo "🔐 Calcolo hash SHA256..."
SHA256=$(shasum -a 256 "$ZIP_PATH" | awk '{print $1}')
echo "$SHA256  $ZIP_NAME" > "$SHA_PATH"
echo "   ✅ SHA256: $SHA256"

# Conta file nel progetto
FILE_COUNT=$(zip -sf "$ZIP_PATH" 2>/dev/null | tail -1 | grep -o '[0-9]*' | head -1 || echo "N/A")

# Git info
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "N/A")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "N/A")

# Genera manifesto legale
cat > "$MANIFEST_PATH" << MANIFESTO
═══════════════════════════════════════════════════════════════════
  MANIFESTO DI DATA CERTA — DEPOSITO CODICE SORGENTE
  VIO 83 AI ORCHESTRA
═══════════════════════════════════════════════════════════════════

TITOLO OPERA:        VIO 83 AI Orchestra
AUTRICE:             Viorica Porcu (vio83)
EMAIL:               porcu.v.83@gmail.com
GITHUB:              https://github.com/vio83/vio83-ai-orchestra
LICENZA:             AGPL-3.0 / Licenza Commerciale Proprietaria

DATA GENERAZIONE:    $DATE_HUMAN
TIMESTAMP UNIX:      $(date +%s)

ARCHIVIO:            $ZIP_NAME
DIMENSIONE:          $ZIP_SIZE_MB MB ($ZIP_SIZE bytes)
FILE INCLUSI:        $FILE_COUNT
SHA-256:             $SHA256

GIT COMMIT:          $GIT_COMMIT
GIT BRANCH:          $GIT_BRANCH

───────────────────────────────────────────────────────────────────
ISTRUZIONI PER PEC CON VALORE LEGALE:
───────────────────────────────────────────────────────────────────

1. Inviare via PEC i seguenti file come allegati:
   - $ZIP_NAME (archivio codice sorgente)
   - ${ZIP_NAME}.sha256 (hash di verifica)
   - Questo manifesto

2. Destinatario PEC consigliato:
   - La propria PEC personale/aziendale
   - Oppure: depositi@pec.it (se disponibile)

3. Oggetto PEC suggerito:
   "Deposito codice sorgente — VIO 83 AI Orchestra — $DATE_HUMAN"

4. La ricevuta PEC con marca temporale costituisce prova di
   data certa ai sensi del Codice dell'Amministrazione Digitale
   (D.Lgs. 82/2005, art. 20-21) e del Regolamento eIDAS
   (Regolamento UE 910/2014).

───────────────────────────────────────────────────────────────────
VERIFICA INTEGRITÀ:
───────────────────────────────────────────────────────────────────

Per verificare che l'archivio non sia stato alterato:

  shasum -a 256 $ZIP_NAME

Il risultato deve corrispondere a:
  $SHA256

───────────────────────────────────────────────────────────────────
NOTE LEGALI:
───────────────────────────────────────────────────────────────────

- Questo deposito attesta l'esistenza del codice sorgente alla
  data indicata, ma NON sostituisce la registrazione presso
  SIAE/Ufficio Brevetti per la tutela del diritto d'autore.
- Il codice è protetto dalla Legge 633/1941 (Diritto d'autore)
  e dalla Direttiva UE 2009/24/CE (tutela giuridica dei
  programmi per elaboratore).
- La licenza AGPL-3.0 è pubblicata nel repository GitHub.
- La licenza commerciale proprietaria è riservata a Viorica Porcu.

© 2026 Viorica Porcu — Tutti i diritti riservati
Giurisdizione: Tribunale di Cagliari, Italia

═══════════════════════════════════════════════════════════════════
MANIFESTO

echo ""
echo "📄 Manifesto legale generato: MANIFESTO_DATA_CERTA_${TIMESTAMP}.txt"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ PEC ZIP COMPLETATO"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "  File pronti in: $PEC_DIR/"
echo ""
echo "  1️⃣  $ZIP_NAME ($ZIP_SIZE_MB MB)"
echo "  2️⃣  ${ZIP_NAME}.sha256"
echo "  3️⃣  MANIFESTO_DATA_CERTA_${TIMESTAMP}.txt"
echo ""
echo "  SHA-256: $SHA256"
echo ""
echo "  📬 Invia tutti e 3 i file via PEC per data certa legale."
echo "═══════════════════════════════════════════════════════"
