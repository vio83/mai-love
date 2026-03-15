# VIO 83 AI ORCHESTRA — Automation Module
from backend.automation.seo_engine import (
    run_seo_cycle,
    start_seo_background,
    stop_seo_background,
    get_github_stats,
    ping_google,
    ping_bing,
    ping_indexnow,
    log_growth_stats,
)

__all__ = [
    "run_seo_cycle",
    "start_seo_background",
    "stop_seo_background",
    "get_github_stats",
    "ping_google",
    "ping_bing",
    "ping_indexnow",
    "log_growth_stats",
]
