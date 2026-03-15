#!/usr/bin/env python3
"""
VIO 83 AI ORCHESTRA — Dock Icon Setup
Salva l'immagine cyberpunk come dock-icon.png nel progetto.

ISTRUZIONI:
1. Salva l'immagine cyberpunk che hai inviato nella chat come:
   ~/Projects/vio83-ai-orchestra/dock-icon.png

   Oppure esegui questo script con il path dell'immagine:
   python3 setup_dock_icon.py /path/to/immagine.png

2. Poi esegui: ./install_dock_app.sh
"""

import sys
import os
import shutil

PROJECT_DIR = os.path.expanduser("~/Projects/vio83-ai-orchestra")
DOCK_ICON = os.path.join(PROJECT_DIR, "dock-icon.png")
FALLBACK = os.path.join(PROJECT_DIR, "src-tauri", "icons", "icon.png")

def setup_icon(source_path=None):
    if source_path and os.path.exists(source_path):
        shutil.copy2(source_path, DOCK_ICON)
        print(f"✓ Icona copiata da: {source_path}")
        print(f"  → Salvata come: {DOCK_ICON}")
    elif os.path.exists(DOCK_ICON):
        print(f"✓ Icona già presente: {DOCK_ICON}")
    elif os.path.exists(FALLBACK):
        shutil.copy2(FALLBACK, DOCK_ICON)
        print(f"✓ Icona progetto usata come fallback: {FALLBACK}")
        print(f"  → Copiata in: {DOCK_ICON}")
    else:
        print("✗ Nessuna immagine trovata!")
        print(f"  Salva l'immagine cyberpunk come: {DOCK_ICON}")
        sys.exit(1)

    # Verifica dimensioni
    size = os.path.getsize(DOCK_ICON)
    print(f"  Dimensione: {size:,} bytes")
    print()
    print("Ora esegui:")
    print("  ./install_dock_app.sh")

if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else None
    setup_icon(source)
