#!/usr/bin/env python3
"""
Build VC visibility assets from investor CRM.
Genera una coda prioritaria VC e un piano operativo di contatto.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CRM = ROOT / "docs" / "investors" / "investor_crm.json"
OUT_CSV = ROOT / "docs" / "investors" / "vc_priority_queue.csv"
OUT_JSON = ROOT / "docs" / "investors" / "vc_priority_queue.json"


def score(inv: dict) -> int:
    s = 0
    inv_type = inv.get("type", "")
    focus = (inv.get("focus") or "").lower()
    notes = (inv.get("notes") or "").lower()
    if inv_type == "VC":
        s += 40
    if inv_type == "Accelerator":
        s += 30
    if "open source" in focus or "open source" in notes:
        s += 30
    if "ai" in focus:
        s += 20
    if "dev tools" in focus:
        s += 20
    if inv.get("country") in {"IT", "EU"}:
        s += 10
    if inv.get("contact_email"):
        s += 10
    if inv.get("apply_url"):
        s += 5
    if inv.get("interest_level") == "high":
        s += 20
    return s


def build() -> None:
    data = json.loads(CRM.read_text(encoding="utf-8"))
    pipeline = data.get("pipeline", [])
    targets = []
    for inv in pipeline:
        inv_type = inv.get("type", "")
        if inv_type not in {"VC", "Accelerator", "Angel Platform", "Grant"}:
            continue
        row = {
            "id": inv.get("id"),
            "name": inv.get("name"),
            "type": inv_type,
            "country": inv.get("country"),
            "focus": inv.get("focus"),
            "status": inv.get("status"),
            "contact_email": inv.get("contact_email"),
            "apply_url": inv.get("apply_url"),
            "linkedin": inv.get("linkedin"),
            "score": score(inv),
            "action": "send_email_and_linkedin" if inv.get("contact_email") else "apply_form",
        }
        targets.append(row)

    targets.sort(key=lambda x: x["score"], reverse=True)

    OUT_JSON.write_text(json.dumps(targets, ensure_ascii=False, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "name",
                "type",
                "country",
                "score",
                "status",
                "action",
                "contact_email",
                "apply_url",
                "linkedin",
                "focus",
            ],
        )
        writer.writeheader()
        writer.writerows(targets)

    print(f"[OK] Generated: {OUT_CSV}")
    print(f"[OK] Generated: {OUT_JSON}")
    print(f"[OK] Targets: {len(targets)}")


if __name__ == "__main__":
    build()
