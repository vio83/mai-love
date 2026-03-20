# ============================================================
# VIO 83 AI ORCHESTRA — SEO & Growth Automation Engine
# Copyright (c) 2026 Viorica Porcu (vio83)
# ============================================================
"""
Automated SEO, visibility, and sponsor growth engine.
Runs as part of the FastAPI backend with scheduled tasks.

Features:
- Search engine ping (Google, Bing, IndexNow)
- GitHub stats tracking + analytics
- Sitemap auto-update
- Growth metrics logging + trend analysis
- Sponsor funnel tracking (visitor → subscriber → paid)
- AI insights + recommendations
- Real-time webhook notifications
- Dashboard metrics API
"""

import asyncio
import json
import os
import time
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from collections import defaultdict

import httpx

# Configuration
GITHUB_REPO = "vio83/vio83-ai-orchestra"
SITE_URL = "https://vio83.github.io/vio83-ai-orchestra/"
SITEMAP_URL = f"{SITE_URL}sitemap.xml"
INDEXNOW_KEY = "3e6f9ffe76d0f756d7492ec16fd4d501"
INDEXNOW_KEY_URL = f"{SITE_URL}{INDEXNOW_KEY}.txt"

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
STATS_FILE = DATA_DIR / "growth-stats.jsonl"
LOG_FILE = DATA_DIR / "seo-automation.log"


def _log(msg: str):
    """Append to log file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} — {msg}\n")


async def ping_google() -> bool:
    """Ping Google with sitemap URL."""
    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            r = await client.get(f"https://www.google.com/ping?sitemap={SITEMAP_URL}")
            _log(f"Google ping: {r.status_code}")
            return r.status_code == 200
    except Exception as e:
        _log(f"Google ping error: {e}")
        return False


async def ping_bing() -> bool:
    """Ping Bing with sitemap URL."""
    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            r = await client.get(f"https://www.bing.com/ping?sitemap={SITEMAP_URL}")
            _log(f"Bing ping: {r.status_code}")
            return r.status_code == 200
    except Exception as e:
        _log(f"Bing ping error: {e}")
        return False


async def ping_indexnow() -> bool:
    """Ping IndexNow API (Bing, Yandex, DuckDuckGo, Seznam)."""
    payload = {
        "host": "vio83.github.io",
        "key": INDEXNOW_KEY,
        "keyLocation": INDEXNOW_KEY_URL,
        "urlList": [
            SITE_URL,
            SITEMAP_URL,
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            r = await client.post(
                "https://api.indexnow.org/indexnow",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            _log(f"IndexNow ping: {r.status_code}")
            return r.status_code in (200, 202)
    except Exception as e:
        _log(f"IndexNow ping error: {e}")
        return False


async def get_github_stats() -> dict:
    """Fetch current GitHub repository stats."""
    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            r = await client.get(f"https://api.github.com/repos/{GITHUB_REPO}")
            if r.status_code == 200:
                data = r.json()
                stats = {
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "watchers": data.get("subscribers_count", 0),
                    "open_issues": data.get("open_issues_count", 0),
                    "size_kb": data.get("size", 0),
                }
                _log(f"GitHub stats: stars={stats['stars']} forks={stats['forks']}")
                return stats
    except Exception as e:
        _log(f"GitHub stats error: {e}")
    return {}


async def log_growth_stats():
    """Fetch and log daily growth stats to JSONL file."""
    stats = await get_github_stats()
    if stats:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATS_FILE, "a") as f:
            f.write(json.dumps(stats) + "\n")
        _log(f"Growth stats logged: {stats}")
    return stats


async def run_seo_cycle():
    """Run a complete SEO ping cycle."""
    _log("=== SEO Cycle Starting ===")
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "google": await ping_google(),
        "bing": await ping_bing(),
        "indexnow": await ping_indexnow(),
    }
    stats = await log_growth_stats()
    results["github_stats"] = stats
    _log(f"=== SEO Cycle Complete: {results} ===")
    return results


# Background task for scheduled execution
_seo_task: Optional[asyncio.Task] = None


async def _seo_loop(interval_hours: int = 6):
    """Background loop that runs SEO cycle every N hours."""
    interval_seconds = interval_hours * 3600
    _log(f"SEO background loop started (interval: {interval_hours}h)")
    while True:
        try:
            await run_seo_cycle()
        except Exception as e:
            _log(f"SEO loop error: {e}")
        await asyncio.sleep(interval_seconds)


def start_seo_background(interval_hours: int = 6):
    """Start the SEO background task."""
    global _seo_task
    if _seo_task is None or _seo_task.done():
        _seo_task = asyncio.create_task(_seo_loop(interval_hours))
        _log("SEO background task created")
    return True


def stop_seo_background():
    """Stop the SEO background task."""
    global _seo_task
    if _seo_task and not _seo_task.done():
        _seo_task.cancel()
        _log("SEO background task cancelled")
    _seo_task = None


# ============ GROWTH ANALYTICS ENGINE ============

def _load_growth_history(days: int = 90) -> List[dict]:
    """Load growth stats from JSONL file for last N days."""
    if not STATS_FILE.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    history = []

    try:
        with open(STATS_FILE, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_date = datetime.fromisoformat(entry["date"])
                    if entry_date >= cutoff:
                        history.append(entry)
                except:
                    continue
    except:
        pass

    return history


def calculate_growth_metrics(days: int = 30) -> Dict[str, Any]:
    """Calculate growth metrics: velocity, acceleration, trends."""
    history = _load_growth_history(days + 30)
    if not history:
        return {"error": "Insufficient data"}

    # Sort by date
    history = sorted(history, key=lambda x: x["date"])

    # Extract series
    stars_series = [h.get("stars", 0) for h in history]
    forks_series = [h.get("forks", 0) for h in history]

    if len(stars_series) < 2:
        return {"error": "Insufficient data"}

    # Calculate metrics
    stars_today = stars_series[-1]
    stars_30d_ago = stars_series[0] if len(stars_series) > 30 else stars_series[0]
    stars_growth = stars_today - stars_30d_ago
    stars_velocity = stars_growth / max(1, len(stars_series) - 1)  # stars/day

    # Acceleration (rate of change of velocity)
    if len(stars_series) >= 3:
        v1 = stars_series[-2] - stars_series[-3]
        v2 = stars_series[-1] - stars_series[-2]
        acceleration = v2 - v1
    else:
        acceleration = 0

    # Trend direction
    trend = "📈 Accelerating" if acceleration > 0 else "📉 Decelerating" if acceleration < 0 else "➡️ Stable"

    return {
        "period_days": len(stars_series) - 1,
        "stars_today": stars_today,
        "stars_30d_growth": stars_growth,
        "stars_velocity_per_day": round(stars_velocity, 2),
        "acceleration": round(acceleration, 2),
        "trend": trend,
        "forks_today": forks_series[-1] if forks_series else 0,
        "last_updated": history[-1].get("date") if history else None,
    }


def calculate_sponsor_funnel() -> Dict[str, Any]:
    """Estimate sponsor conversion funnel based on GitHub stats."""
    history = _load_growth_history(90)
    if not history:
        return {"error": "No data"}

    latest = history[-1]
    stars = latest.get("stars", 1)
    watchers = latest.get("watchers", 1)

    # Assumptions: 1 sponsor per ~200 active users (visitors)
    # Conversion: watchers → active interest, stars → engaged users
    estimated_visitors_monthly = stars * 3  # rough estimate
    estimated_subscribers = max(1, stars // 100)  # rough estimate
    estimated_paying = max(1, stars // 500)  # rough estimate

    conversion_rate_sub = round((estimated_subscribers / max(1, estimated_visitors_monthly)) * 100, 2)
    conversion_rate_paid = round((estimated_paying / max(1, estimated_subscribers)) * 100, 2)

    return {
        "estimated_visitors_monthly": estimated_visitors_monthly,
        "estimated_email_subscribers": estimated_subscribers,
        "estimated_paying_sponsors": estimated_paying,
        "visitor_to_subscriber_rate": f"{conversion_rate_sub}%",
        "subscriber_to_paid_rate": f"{conversion_rate_paid}%",
        "monthly_recurring_revenue_estimate": max(1, estimated_paying) * 5,  # assume $5/sponsor
        "forecast_6m": {
            "projected_subscribers": estimated_subscribers * 1.3,
            "projected_paying": estimated_paying * 1.5,
        }
    }


def get_dashboard_metrics() -> Dict[str, Any]:
    """Complete dashboard metrics for visualization."""
    growth = calculate_growth_metrics()
    funnel = calculate_sponsor_funnel()
    history = _load_growth_history(30)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "growth_analytics": growth,
        "sponsor_funnel": funnel,
        "recent_30d": {
            "snapshots": len(history),
            "stars_gained": history[-1]["stars"] - history[0]["stars"] if history else 0,
            "forks_gained": history[-1]["forks"] - history[0]["forks"] if history else 0,
        }
    }


async def generate_ai_insights() -> str:
    """Generate AI-powered insights using local LLM (Ollama)."""
    metrics = get_dashboard_metrics()

    prompt = f"""
Analizza questi metriche di crescita del progetto vio83-ai-orchestra e fornisci 3-4 insights brevi e actionable:

Dati:
- Growth Analytics: {json.dumps(metrics['growth_analytics'], indent=2)}
- Sponsor Funnel: {json.dumps(metrics['sponsor_funnel'], indent=2)}

Fornisci insights in formato Markdown, include raccomandazioni concrete.
"""

    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            r = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:3b",
                    "prompt": prompt,
                    "stream": False,
                },
            )
            if r.status_code == 200:
                response_data = r.json()
                insights = response_data.get("response", "No insights generated")
                _log(f"AI insights generated: {len(insights)} chars")
                return insights
    except Exception as e:
        _log(f"AI insights error: {e}")

    return "AI insights unavailable (Ollama not responding)"


async def webhook_notify_growth(webhook_url: str, metrics: Dict[str, Any]) -> bool:
    """Send growth metrics to webhook (e.g., n8n, Discord, Slack)."""
    payload = {
        "type": "growth_update",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    }

    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            r = await client.post(webhook_url, json=payload)
            success = r.status_code in (200, 201, 202)
            _log(f"Webhook notify ({webhook_url[:40]}...): {r.status_code}")
            return success
    except Exception as e:
        _log(f"Webhook error: {e}")
        return False


async def run_full_growth_cycle() -> Dict[str, Any]:
    """Run complete growth cycle: SEO + analytics + insights + notifications."""
    _log("=== FULL GROWTH CYCLE STARTING ===")

    # 1. SEO ping
    seo_results = await run_seo_cycle()

    # 2. Metrics calculation
    metrics = get_dashboard_metrics()

    # 3. AI insights (async, non-blocking)
    insights = await asyncio.create_task(generate_ai_insights())
    metrics["ai_insights"] = insights

    # 4. Webhook notifications (if configured)
    webhook_urls = os.getenv("GROWTH_WEBHOOK_URLS", "").split(",")
    webhook_results = {}
    for url in webhook_urls:
        if url.strip():
            success = await webhook_notify_growth(url.strip(), metrics)
            webhook_results[url.strip()] = success

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seo_ping_results": seo_results,
        "metrics": metrics,
        "webhook_notifications": webhook_results,
        "status": "complete"
    }

    _log(f"=== FULL GROWTH CYCLE COMPLETE ===")
    return result
