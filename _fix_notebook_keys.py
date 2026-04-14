#!/usr/bin/env python3
"""Corregge gaming_detected -> window_gaming nel notebook BRACE v3.0."""
import json
import pathlib

nb_path = pathlib.Path("brace-v3/PROGETTI FA/Untitled-WEBUI-1.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))

fixed = 0
for cell in nb.get("cells", []):
    if cell.get("cell_type") != "code":
        continue
    new_src = []
    for line in cell.get("source", []):
        if 'pil_result["gaming_detected"]' in line:
            line = line.replace('pil_result["gaming_detected"]', 'pil_result["window_gaming"]')
            fixed += 1
        new_src.append(line)
    cell["source"] = new_src

nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=4), encoding="utf-8")
print(f"✅ Fix completato: {fixed} occorrenze corrette")
