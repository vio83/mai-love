# ============================================================
# VIO 83 AI ORCHESTRA — SEO & Growth Automation Engine
# Copyright (c) 2026 Viorica Porcu (vio83)
# ============================================================
"""
Automated SEO, visibility, and sponsor growth engine.
Runs as part of the FastAPI backend with scheduled tasks.

Features:
- Search engine ping (Google, Bing, IndexNow)
- GitHub stats tracking
- Sitemap auto-update
- Growth metrics logging
"""

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

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
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"https://www.google.com/ping?sitemap={SITEMAP_URL}")
            _log(f"Google ping: {r.status_code}")
            return r.status_code == 200
    except Exception as e:
        _log(f"Google ping error: {e}")
        return False


async def ping_bing() -> bool:
    """Ping Bing with sitemap URL."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
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
        async with httpx.AsyncClient(timeout=10) as client:
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
        async with httpx.AsyncClient(timeout=10) as client:
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
