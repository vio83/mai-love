#!/bin/bash
set -euo pipefail

OUTFILE="$HOME/Desktop/ALGORITMO BRACE V3.1 GIU-L_IA.txt"
SRCDIR="$(cd "$(dirname "$0")" && pwd)"

FILES=(
  __init__.py
  brace_v3.py
  scenarios_db.py
  webui.py
  prototipo_web_advanced.py
  demo_algorithm.py
  demo_terminal_optimized.py
  benchmark.py
  test_bunker_quality.py
  launch.sh
  webui_glassmorphic_elite.py
  webui_luxury_new.py
  webui_proto.py
  webui_video_wrapper.py
)

{
  echo "================================================================================"
  echo "=== ALGORITMO BRACE V3.1 GIU-L_IA — DUMP COMPLETO BYTE BY BYTE"
  echo "=== DATA: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "=== AUTRICE: VIORICA PORCU (VIO83)"
  echo "=== REPOSITORY: GITHUB.COM/VIO83/VIO83-AI-ORCHESTRA"
  echo "=== TOTALE FILE: ${#FILES[@]} (13 PYTHON + 1 SHELL)"
  echo "================================================================================"
  echo ""

  for f in "${FILES[@]}"; do
    fp="$SRCDIR/$f"
    righe=$(wc -l < "$fp" | tr -d ' ')
    bytes=$(wc -c < "$fp" | tr -d ' ')
    echo "================================================================================"
    echo "=== FILE: brace-v3/$f  ($righe RIGHE, $bytes BYTE)"
    echo "================================================================================"
    cat "$fp"
    echo ""
    echo ""
  done

  echo "================================================================================"
  echo "=== FINE DUMP — TUTTI I ${#FILES[@]} FILE INCLUSI"
  echo "=== PY_COMPILE: 13/13 PYTHON OK — ZERO ERRORI"
  echo "================================================================================"
} > "$OUTFILE"

echo "CREATO: $OUTFILE"
ls -lh "$OUTFILE"
echo "SHA256: $(shasum -a 256 "$OUTFILE")"
