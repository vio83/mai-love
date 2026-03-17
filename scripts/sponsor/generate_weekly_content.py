#!/usr/bin/env python3
"""Generate weekly sponsor-ready copy (2 LinkedIn + 1 Ko-fi + 1 GitHub).

Features:
- bilingual outputs (IT + EN)
- date-aligned content calendar
- adaptive strategy hints based on recent generated bundles
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import random
import urllib.parse


def monday_of_week(day: dt.date) -> dt.date:
    return day - dt.timedelta(days=day.weekday())


def choose(rng: random.Random, items: list[str]) -> str:
    return items[rng.randrange(len(items))]


def load_recent_bundles(out_dir: pathlib.Path, limit: int = 8) -> list[dict]:
    if not out_dir.exists():
        return []
    bundles: list[dict] = []
    for path in sorted(out_dir.glob("*.json"))[-limit:]:
        try:
            bundles.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return bundles


def strategy_from_history(history: list[dict], stars: int, views: int) -> dict:
    if not history:
        return {
            "mode": "bootstrap",
            "cta_strength": "medium",
            "focus": "awareness_and_trust",
            "innovation_angle": "product_progress",
        }

    recent_views = []
    recent_stars = []
    for item in history:
        metrics = item.get("metrics", {})
        if isinstance(metrics.get("views"), int):
            recent_views.append(metrics["views"])
        if isinstance(metrics.get("stars"), int):
            recent_stars.append(metrics["stars"])

    avg_views = sum(recent_views) / len(recent_views) if recent_views else 0
    last_stars = recent_stars[-1] if recent_stars else stars

    cta_strength = "strong" if views < avg_views else "medium"
    focus = "conversion_push" if views < avg_views else "trust_compound"
    innovation_angle = "proof_and_metrics" if stars >= last_stars else "vision_and_story"

    return {
        "mode": "adaptive",
        "cta_strength": cta_strength,
        "focus": focus,
        "innovation_angle": innovation_angle,
        "avg_recent_views": round(avg_views, 2),
    }


def build_content(stars: int, forks: int, views: int, today: dt.date, out_dir: pathlib.Path) -> dict:
    iso_year, iso_week, _ = today.isocalendar()
    week_key = iso_year * 100 + iso_week
    rng = random.Random(week_key + stars * 3 + forks * 5 + views * 7)
    history = load_recent_bundles(out_dir)
    strategy = strategy_from_history(history, stars, views)

    support_hub = "https://vio83.github.io/vio83-ai-orchestra/support.html"
    gh_sponsor = "https://github.com/sponsors/vio83"
    kofi = "https://ko-fi.com/vio83_ai_orchestra_"

    li1_hooks_it = [
        "🎵 Build log settimanale: VIO 83 AI Orchestra",
        "🚀 Settimana di shipping concreto su VIO 83 AI Orchestra",
        "🛠️ Weekly engineering update: qualità + velocità + affidabilità",
        "📈 Questa settimana ho migliorato affidabilità locale e flusso sponsor",
    ]
    li1_hooks_en = [
        "🎵 Weekly build log: VIO 83 AI Orchestra",
        "🚀 Shipping week on VIO 83 AI Orchestra",
        "🛠️ Weekly engineering update: quality + speed + reliability",
        "📈 This week I improved local reliability and sponsor flow",
    ]
    li1_focus_it = [
        "più stabilità nel flusso locale, meno attrito nell'esperienza utente",
        "orchestrazione più robusta e risposta più fluida lato chat",
        "pipeline più affidabile per generazione output e fallback",
        "operatività reale: meno blocchi, più continuità, più valore pratico",
    ]
    li1_focus_en = [
        "more stability in local flow, less friction in user experience",
        "more robust orchestration and smoother chat responses",
        "more reliable pipeline for output generation and fallback",
        "real execution: fewer blocks, more continuity, more practical value",
    ]

    li2_hooks_it = [
        "🧠 AI utile = precisione + velocità + verifica",
        "⚖️ Il punto non è solo rispondere: è rispondere bene e in tempo",
        "🔍 Tra hype e realtà: io scelgo AI verificabile e concreta",
        "🎯 Product note: meno promesse, più risultati misurabili",
    ]
    li2_hooks_en = [
        "🧠 Useful AI = precision + speed + verification",
        "⚖️ It is not only about responding, but responding well and on time",
        "🔍 Between hype and reality, I choose verifiable AI",
        "🎯 Product note: fewer promises, more measurable outcomes",
    ]
    li2_angles_it = [
        "Sto costruendo un sistema che riduce la frammentazione tra modelli AI.",
        "L'obiettivo è una UX che unisca qualità tecnica e tempi pratici.",
        "Ogni settimana ottimizzo affidabilità, funnel e deploy operativo.",
        "Build in public, con numeri reali e iterazione continua.",
    ]
    li2_angles_en = [
        "I am building a system that reduces fragmentation across AI models.",
        "The goal is a UX that combines technical quality with practical speed.",
        "Every week I optimize reliability, funnel and operational deployment.",
        "Build in public, with real numbers and continuous iteration.",
    ]

    kofi_openers_it = [
        "☕ Ko-fi Weekly Update — grazie per il supporto reale",
        "💚 Weekly Ko-fi update — progressi concreti, non teoria",
        "🔧 Ko-fi update della settimana — shipping e ottimizzazione",
    ]
    kofi_openers_en = [
        "☕ Ko-fi Weekly Update — thanks for real support",
        "💚 Weekly Ko-fi update — concrete progress, not theory",
        "🔧 This week on Ko-fi — shipping and optimization",
    ]

    gh_openers_en = [
        "## Weekly Progress — VIO 83 AI Orchestra",
        "## Weekly Engineering Update — VIO 83 AI Orchestra",
        "## Weekly Build Report — VIO 83 AI Orchestra",
    ]
    gh_openers_it = [
        "## Progresso Settimanale — VIO 83 AI Orchestra",
        "## Aggiornamento Engineering Settimanale — VIO 83 AI Orchestra",
        "## Report Build Settimanale — VIO 83 AI Orchestra",
    ]

    cta_it = "Sostieni qui" if strategy["cta_strength"] == "strong" else "Se vuoi supportare il progetto"
    cta_en = "Support here" if strategy["cta_strength"] == "strong" else "If you want to support the project"

    monday = monday_of_week(today)
    wednesday = monday + dt.timedelta(days=2)
    thursday = monday + dt.timedelta(days=3)
    friday = monday + dt.timedelta(days=4)

    linkedin_post_1_it = (
        f"{choose(rng, li1_hooks_it)}\n\n"
        f"Questa settimana focus su {choose(rng, li1_focus_it)}.\n\n"
        f"📊 Snapshot aggiornato ({today.isoformat()}):\n"
        f"⭐ {stars} stelle\n"
        f"🔀 {forks} fork\n"
        f"👀 {views} views settimanali\n\n"
        f"{cta_it} open source:\n"
        f"💚 {gh_sponsor}\n"
        f"☕ {kofi}\n"
        f"🌍 {support_hub}\n\n"
        "#AI #OpenSource #BuildInPublic #IndieDev #MadeInItaly"
    )

    linkedin_post_1_en = (
        f"{choose(rng, li1_hooks_en)}\n\n"
        f"This week focus: {choose(rng, li1_focus_en)}.\n\n"
        f"📊 Updated snapshot ({today.isoformat()}):\n"
        f"⭐ {stars} stars\n"
        f"🔀 {forks} forks\n"
        f"👀 {views} weekly views\n\n"
        f"{cta_en}:\n"
        f"💚 {gh_sponsor}\n"
        f"☕ {kofi}\n"
        f"🌍 {support_hub}\n\n"
        "#AI #OpenSource #BuildInPublic #IndieDev"
    )

    linkedin_post_2_it = (
        f"{choose(rng, li2_hooks_it)}\n\n"
        f"{choose(rng, li2_angles_it)}\n"
        "Punto chiave: meno rumore, più output utile e verificabile.\n\n"
        "Obiettivo mese: 10 sponsor per accelerare qualità, QA e release.\n\n"
        f"{cta_it}:\n💚 {gh_sponsor}\n☕ {kofi}\n🌍 {support_hub}\n\n"
        "#AIEngineering #OpenSource #SoloFounder #LLM #Tech"
    )

    linkedin_post_2_en = (
        f"{choose(rng, li2_hooks_en)}\n\n"
        f"{choose(rng, li2_angles_en)}\n"
        "Key point: less noise, more useful and verifiable output.\n\n"
        "Monthly target: 10 sponsors to accelerate quality, QA and releases.\n\n"
        f"{cta_en}:\n💚 {gh_sponsor}\n☕ {kofi}\n🌍 {support_hub}\n\n"
        "#AIEngineering #OpenSource #SoloFounder #LLM #Tech"
    )

    kofi_post_it = (
        f"{choose(rng, kofi_openers_it)}\n\n"
        f"Settimana {iso_week} — metriche:\n"
        f"⭐ {stars} stars\n"
        f"🔀 {forks} forks\n"
        f"👀 {views} views\n\n"
        "Sto continuando a migliorare stabilità locale, qualità output e automazioni sponsor.\n"
        "Ogni supporto qui su Ko-fi finanzia test, sviluppo e release.\n\n"
        f"Support Hub: {support_hub}\n"
        "Grazie di cuore 💚"
    )

    kofi_post_en = (
        f"{choose(rng, kofi_openers_en)}\n\n"
        f"Week {iso_week} — metrics:\n"
        f"⭐ {stars} stars\n"
        f"🔀 {forks} forks\n"
        f"👀 {views} views\n\n"
        "I keep improving local reliability, output quality and sponsor operations.\n"
        "Every Ko-fi support directly funds testing, development and releases.\n\n"
        f"Support Hub: {support_hub}\n"
        "Thank you so much 💚"
    )

    github_weekly_post_en = (
        f"{choose(rng, gh_openers_en)}\n\n"
        "This week focused on reliability, speed, and sponsor growth execution.\n\n"
        "### Metrics\n"
        f"- Stars: {stars}\n"
        f"- Forks: {forks}\n"
        f"- Weekly Views: {views}\n\n"
        "### Weekly focus\n"
        "- Local reliability and fallback quality\n"
        "- Faster visible output and cleaner chat UX\n"
        "- Sponsor funnel and content operations\n\n"
        "### Support\n"
        f"- GitHub Sponsors: {gh_sponsor}\n"
        f"- Ko-fi: {kofi}\n"
        f"- Support Hub: {support_hub}\n"
    )

    github_weekly_post_it = (
        f"{choose(rng, gh_openers_it)}\n\n"
        "Questa settimana il focus è stato su affidabilità, velocità e crescita sponsor.\n\n"
        "### Metriche\n"
        f"- Stars: {stars}\n"
        f"- Forks: {forks}\n"
        f"- Weekly Views: {views}\n\n"
        "### Focus settimanale\n"
        "- Affidabilità locale e qualità fallback\n"
        "- Output visibile più rapido e UX chat più pulita\n"
        "- Funnel sponsor e operatività contenuti\n\n"
        "### Supporto\n"
        f"- GitHub Sponsors: {gh_sponsor}\n"
        f"- Ko-fi: {kofi}\n"
        f"- Support Hub: {support_hub}\n"
    )

    action_items_it = (
        f"📋 WEEKLY CONTENT CALENDAR — {today.isoformat()}\n\n"
        f"Lunedì ({monday.isoformat()}): LinkedIn Post #1\n"
        f"Mercoledì ({wednesday.isoformat()}): Ko-fi update\n"
        f"Giovedì ({thursday.isoformat()}): LinkedIn Post #2\n"
        f"Venerdì ({friday.isoformat()}): GitHub weekly post\n\n"
        "Outreach: 3–5 DM mirati/settimana\n"
        "Target pratico:\n"
        "- CTR support hub >= 2.5%\n"
        "- Conversione visita→sponsor 1–3%\n"
        "- Review KPI ogni domenica\n"
    )

    action_items_en = (
        f"📋 WEEKLY CONTENT CALENDAR — {today.isoformat()}\n\n"
        f"Monday ({monday.isoformat()}): LinkedIn Post #1\n"
        f"Wednesday ({wednesday.isoformat()}): Ko-fi update\n"
        f"Thursday ({thursday.isoformat()}): LinkedIn Post #2\n"
        f"Friday ({friday.isoformat()}): GitHub weekly post\n\n"
        "Outreach: 3–5 targeted DMs per week\n"
        "Practical targets:\n"
        "- Support hub CTR >= 2.5%\n"
        "- Visit→sponsor conversion 1–3%\n"
        "- KPI review every Sunday\n"
    )

    dm_template_it = (
        "Ciao [Nome], seguo con interesse il tuo lavoro su [tema].\n"
        "Sto costruendo VIO 83 AI Orchestra (multi-AI orchestration, open source, build in public).\n"
        f"Se vuoi dare un'occhiata: {support_hub}\n"
        "Se ti va, apprezzo feedback o supporto. Grazie davvero 🙏"
    )

    dm_template_en = (
        "Hi [Name], I really appreciate your work on [topic].\n"
        "I am building VIO 83 AI Orchestra (multi-AI orchestration, open source, build in public).\n"
        f"If you want to take a look: {support_hub}\n"
        "If you like it, I would value feedback or support. Thank you 🙏"
    )

    linkedin_share_1_it = (
        "https://www.linkedin.com/feed/?shareActive=true&text="
        + urllib.parse.quote(linkedin_post_1_it)
    )
    linkedin_share_1_en = (
        "https://www.linkedin.com/feed/?shareActive=true&text="
        + urllib.parse.quote(linkedin_post_1_en)
    )
    linkedin_share_2_it = (
        "https://www.linkedin.com/feed/?shareActive=true&text="
        + urllib.parse.quote(linkedin_post_2_it)
    )
    linkedin_share_2_en = (
        "https://www.linkedin.com/feed/?shareActive=true&text="
        + urllib.parse.quote(linkedin_post_2_en)
    )

    return {
        "generated_on": today.isoformat(),
        "iso_week": iso_week,
        "metrics": {
            "stars": stars,
            "forks": forks,
            "views": views,
        },
        "optimization": strategy,
        "linkedin_post_1_it": linkedin_post_1_it,
        "linkedin_post_1_en": linkedin_post_1_en,
        "linkedin_post_2_it": linkedin_post_2_it,
        "linkedin_post_2_en": linkedin_post_2_en,
        "kofi_post_it": kofi_post_it,
        "kofi_post_en": kofi_post_en,
        "github_weekly_post_it": github_weekly_post_it,
        "github_weekly_post_en": github_weekly_post_en,
        "action_items_it": action_items_it,
        "action_items_en": action_items_en,
        "dm_template_it": dm_template_it,
        "dm_template_en": dm_template_en,
        "publish_links": {
            "linkedin_post_1_it": linkedin_share_1_it,
            "linkedin_post_1_en": linkedin_share_1_en,
            "linkedin_post_2_it": linkedin_share_2_it,
            "linkedin_post_2_en": linkedin_share_2_en,
            "kofi": "https://ko-fi.com/manage/posts",
            "github": "https://github.com/vio83/vio83-ai-orchestra/discussions/new",
        },
        "linkedin_post_1": f"{linkedin_post_1_it}\n\n--- EN ---\n\n{linkedin_post_1_en}",
        "linkedin_post_2": f"{linkedin_post_2_it}\n\n--- EN ---\n\n{linkedin_post_2_en}",
        "kofi_post": f"{kofi_post_it}\n\n--- EN ---\n\n{kofi_post_en}",
        "github_weekly_post": f"{github_weekly_post_it}\n\n--- EN ---\n\n{github_weekly_post_en}",
        "action_items": f"{action_items_it}\n\n--- EN ---\n\n{action_items_en}",
        "dm_template": f"{dm_template_it}\n\n--- EN ---\n\n{dm_template_en}",
    }


def persist_bundle(bundle: dict, out_dir: pathlib.Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{bundle['generated_on']}-W{bundle['iso_week']}"
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"

    json_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        f"# Weekly Sponsor Copy — {bundle['generated_on']} (W{bundle['iso_week']})",
        "",
        "## Optimization Strategy",
        json.dumps(bundle.get("optimization", {}), ensure_ascii=False, indent=2),
        "",
        "## LinkedIn Post 1 (IT)",
        bundle["linkedin_post_1_it"],
        "",
        "## LinkedIn Post 1 (EN)",
        bundle["linkedin_post_1_en"],
        "",
        "## LinkedIn Post 2 (IT)",
        bundle["linkedin_post_2_it"],
        "",
        "## LinkedIn Post 2 (EN)",
        bundle["linkedin_post_2_en"],
        "",
        "## Ko-fi Post (IT)",
        bundle["kofi_post_it"],
        "",
        "## Ko-fi Post (EN)",
        bundle["kofi_post_en"],
        "",
        "## GitHub Weekly Post (IT)",
        bundle["github_weekly_post_it"],
        "",
        "## GitHub Weekly Post (EN)",
        bundle["github_weekly_post_en"],
        "",
        "## Action Items (IT)",
        bundle["action_items_it"],
        "",
        "## Action Items (EN)",
        bundle["action_items_en"],
        "",
        "## DM Template (IT)",
        bundle["dm_template_it"],
        "",
        "## DM Template (EN)",
        bundle["dm_template_en"],
        "",
    ]
    md_path.write_text("\n".join(md), encoding="utf-8")

    return {"json_path": str(json_path), "md_path": str(md_path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stars", type=int, default=0)
    parser.add_argument("--forks", type=int, default=0)
    parser.add_argument("--views", type=int, default=0)
    parser.add_argument("--date", type=str, default="")
    parser.add_argument("--out-dir", type=str, default="data/weekly-content")
    parser.add_argument("--json", action="store_true", help="print JSON to stdout")
    args = parser.parse_args()

    today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    out_dir = pathlib.Path(args.out_dir)
    bundle = build_content(args.stars, args.forks, args.views, today, out_dir)
    paths = persist_bundle(bundle, out_dir)
    bundle.update(paths)

    if args.json:
        print(json.dumps(bundle, ensure_ascii=False))
    else:
        print(f"Generated weekly content: {paths['md_path']}")


if __name__ == "__main__":
    main()
