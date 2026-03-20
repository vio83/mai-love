#!/usr/bin/env python3
"""
investor_outreach.py — VIO AI Orchestra Investor Outreach Engine
Genera email personalizzate pronte all'invio per ogni investitore nel CRM.
Uso: python3 scripts/investor/investor_outreach.py [--investor IT-001] [--dry-run]
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CRM_FILE = PROJECT_ROOT / "docs" / "investors" / "investor_crm.json"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "investors" / "outreach"

FOUNDER_NAME = "Viorica Porcu"
FOUNDER_EMAIL = "porcu.v.83@gmail.com"
PROJECT_NAME = "VIO AI Orchestra"
GITHUB_URL = "https://github.com/vio83/mai-love"
WEBSITE_URL = "https://vio83.github.io/vio83-ai-orchestra/"
CALENDAR_URL = "https://calendly.com/vio83"  # da creare su calendly.com

EMAIL_TEMPLATES = {
    "VC": """\
Oggetto: VIO AI Orchestra — Pre-Seed Round da €50K | AI Local-First Open Source | {name}

Gentile Team {name},

Mi chiamo Viorica Porcu, sviluppatrice software indipendente e fondatrice di VIO AI Orchestra.

In 12 mesi ho costruito da zero la prima piattaforma desktop open source (AGPL-3.0) che orchestra 9+ modelli AI — locali (Ollama: Llama3, DeepSeek, Mistral, Gemma) e cloud (GPT-4, Claude, Gemini, Groq) — in un'unica app cross-platform (macOS, Windows, Linux).

DATI CONCRETI:
• Codice pubblico su GitHub: {github_url}
• Stack certificato: FastAPI + React/Vite + Tauri + SQLite
• Privacy-first: i dati NON lasciano il device in modalità local
• Traction attuale: community developer in crescita organica
• Licenza duale AGPL-3.0 + Commercial per revenue enterprise

PERCHÉ ADESSO:
Il mercato AI desktop è esploso. Microsoft spende $13B su OpenAI. Apple integra LLM on-device. VIO AI Orchestra è già funzionante, già deployato, già open: vantaggio competitivo di 18-24 mesi su qualsiasi competitor che parte da zero.

RICHIESTA:
€50.000 Pre-Seed per 10-15% equity su valutazione €350K pre-money.
Uso dei fondi: 50% stipendio fondatrice (sviluppo full-time 12 mesi), 20% infrastruttura, 20% marketing, 10% legale.

NEXT STEP:
30 minuti di chiamata? {calendar_url}

Con stima,
{founder_name}
{founder_email}
GitHub: {github_url}
Web: {website_url}
""",
    "Grant": """\
Oggetto: Application: VIO AI Orchestra — Privacy-First Local AI Orchestrator | {name}

Dear {name} Team,

My name is Viorica Porcu, independent software developer from Italy.

I am applying for a grant to fund the continued development of VIO AI Orchestra, a fully open source (AGPL-3.0) desktop AI orchestration platform.

PROJECT OVERVIEW:
VIO AI Orchestra allows anyone — individuals, NGOs, journalists, SMEs — to run powerful AI (9+ models including local LLMs via Ollama) WITHOUT sending data to the cloud. Privacy is enforced architecturally: all processing runs on-device by default.

TECHNICAL PROOF:
• Public code: {github_url}
• Stack: FastAPI (Python), React/TypeScript, Tauri (Rust), SQLite
• Local models: LLaMA 3, Mistral, DeepSeek, Gemma, Qwen
• Zero external dependencies in local mode
• Dual license: AGPL-3.0 (community) + Commercial (enterprise)

FIT WITH YOUR MISSION:
This project directly advances open internet, privacy-preserving AI, and digital sovereignty — making cutting-edge AI tools accessible without vendor lock-in or surveillance.

REQUESTED AMOUNT:
{ticket_min} – {ticket_max} EUR for 6-12 months of full-time development.

APPLICATION: {apply_url}

Thank you for your consideration.

Viorica Porcu
{founder_email}
{github_url}
""",
    "Accelerator": """\
Oggetto: VIO AI Orchestra — Solo Founder AI Platform | Application {name}

Hi {name} Team,

I'm Viorica Porcu, solo founder building VIO AI Orchestra — the open source desktop app that makes running 9+ AI models locally as simple as opening Spotify.

ONE-LINER:
"The VSCode for AI models" — runs everything local, beats any SaaS on privacy and cost.

TRACTION:
• Working product: {github_url}
• AGPL-3.0 + Commercial dual license
• 9 AI providers integrated (local + cloud)
• Built by 1 person in 12 months from scratch

WHY ACCELERATOR:
I need mentorship on GTM, distribution, and pricing — not more code. The code works. I need the network.

Target raise: €50K-€120K depending on program structure.

Can we find 15 minutes? {calendar_url}

Viorica Porcu
{founder_email}
""",
    "default": """\
Oggetto: VIO AI Orchestra — Local-First AI Platform | Investment Opportunity

Hi,

I'm Viorica Porcu, founder of VIO AI Orchestra — open source AI orchestration platform.

See: {github_url} | {website_url}

Happy to share more details.

Viorica Porcu
{founder_email}
"""
}


def load_crm() -> dict:
    if not CRM_FILE.exists():
        print(f"[ERRORE] CRM non trovato: {CRM_FILE}", file=sys.stderr)
        sys.exit(1)
    return json.loads(CRM_FILE.read_text(encoding="utf-8"))


def get_template(inv_type: str) -> str:
    return EMAIL_TEMPLATES.get(inv_type, EMAIL_TEMPLATES["default"])


def generate_email(inv: dict) -> str:
    template = get_template(inv.get("type", "default"))
    ticket_min = f"€{inv.get('ticket_min_eur', 5000):,}".replace(",", ".")
    ticket_max = f"€{inv.get('ticket_max_eur', 50000):,}".replace(",", ".")
    return template.format(
        name=inv.get("name", "Team"),
        type=inv.get("type", ""),
        github_url=GITHUB_URL,
        website_url=WEBSITE_URL,
        calendar_url=CALENDAR_URL,
        founder_name=FOUNDER_NAME,
        founder_email=FOUNDER_EMAIL,
        apply_url=inv.get("apply_url", ""),
        ticket_min=ticket_min,
        ticket_max=ticket_max,
        today=date.today().isoformat(),
    )


def main():
    parser = argparse.ArgumentParser(description="VIO AI Orchestra Investor Outreach Generator")
    parser.add_argument("--investor", help="ID specifico investitore (es. IT-001). Ometti per tutti.")
    parser.add_argument("--dry-run", action="store_true", help="Stampa a schermo senza salvare file")
    parser.add_argument("--status-filter", default="to_contact", help="Filtra per status (default: to_contact)")
    args = parser.parse_args()

    crm = load_crm()
    pipeline = crm.get("pipeline", [])

    if args.investor:
        pipeline = [p for p in pipeline if p["id"] == args.investor]
        if not pipeline:
            print(f"[ERRORE] Investitore {args.investor} non trovato nel CRM", file=sys.stderr)
            sys.exit(1)
    else:
        pipeline = [p for p in pipeline if p.get("status") == args.status_filter]

    if not pipeline:
        print(f"[INFO] Nessun investitore con status='{args.status_filter}' trovato.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = 0

    for inv in pipeline:
        email_text = generate_email(inv)
        filename = f"{inv['id']}_{inv['name'].replace(' ', '_').replace('/', '-')}.txt"

        if args.dry_run:
            print(f"\n{'='*60}")
            print(f"INVESTITORE: {inv['id']} — {inv['name']} ({inv['type']}, {inv['country']})")
            print(f"INVIA A: {inv.get('contact_email') or 'Vedi apply_url: ' + inv.get('apply_url','N/A')}")
            print(f"{'='*60}")
            print(email_text)
        else:
            out_path = OUTPUT_DIR / filename
            out_path.write_text(email_text, encoding="utf-8")
            print(f"[OK] {inv['id']} — {inv['name']} → {out_path}")
            generated += 1

    if not args.dry_run:
        print(f"\n✅ {generated} email generate in {OUTPUT_DIR}")
        print(f"   Apri la cartella: open {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
