# ============================================================
# VIO 83 AI ORCHESTRA — Sponsor Growth Funnel Tracker
# Copyright (c) 2026 Viorica Porcu (vio83)
# ============================================================
"""
Sponsor lifecycle and funnel tracking:
- Visitor → Subscriber → Paying sponsor
- Churn tracking and retention
- LTV (Lifetime Value) calculation
- Cohort analysis
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
SPONSOR_FUNNEL_FILE = DATA_DIR / "sponsor-funnel.jsonl"
SPONSOR_COHORTS_FILE = DATA_DIR / "sponsor-cohorts.json"


def _ensure_dirs():
    """Ensure data directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _track_event(event_type: str, user_id: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Log sponsor lifecycle event."""
    _ensure_dirs()

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,  # visitor, subscriber, paying, churned, reactivated
        "user_id": user_id,
        "metadata": metadata or {},
    }

    with open(SPONSOR_FUNNEL_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

    return event


def track_visitor(user_id: str, source: str = "organic", utm_params: Dict = None):
    """Track new visitor."""
    return _track_event("visitor", user_id, {
        "source": source,
        "utm": utm_params or {},
    })


def track_subscriber(user_id: str, email: str):
    """Track email subscriber."""
    return _track_event("subscriber", user_id, {
        "email": email,
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
    })


def track_paying_sponsor(user_id: str, tier: str, amount: float, interval: str = "monthly"):
    """Track paying sponsor."""
    return _track_event("paying", user_id, {
        "tier": tier,  # bronze, silver, gold
        "amount": amount,
        "interval": interval,
        "started_at": datetime.now(timezone.utc).isoformat(),
    })


def track_churn(user_id: str, reason: str = "unknown"):
    """Track churned sponsor."""
    return _track_event("churned", user_id, {
        "reason": reason,
        "churned_at": datetime.now(timezone.utc).isoformat(),
    })


def track_reactivation(user_id: str, previous_tier: str = None):
    """Track sponsor reactivation."""
    return _track_event("reactivated", user_id, {
        "previous_tier": previous_tier,
        "reactivated_at": datetime.now(timezone.utc).isoformat(),
    })


def get_funnel_metrics(days: int = 90) -> Dict[str, Any]:
    """Calculate current funnel metrics."""
    if not SPONSOR_FUNNEL_FILE.exists():
        return {"status": "no_data"}

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    users_by_stage = {
        "visitors": set(),
        "subscribers": set(),
        "paying": set(),
        "churned": set(),
        "reactivated": set(),
    }

    try:
        with open(SPONSOR_FUNNEL_FILE, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    event_time = datetime.fromisoformat(event["timestamp"])

                    if event_time < cutoff:
                        continue

                    user_id = event["user_id"]
                    event_type = event["event_type"]

                    if event_type == "visitor":
                        users_by_stage["visitors"].add(user_id)
                    elif event_type == "subscriber":
                        users_by_stage["subscribers"].add(user_id)
                        users_by_stage["visitors"].discard(user_id)  # move up funnel
                    elif event_type == "paying":
                        users_by_stage["paying"].add(user_id)
                        users_by_stage["subscribers"].discard(user_id)
                    elif event_type == "churned":
                        users_by_stage["churned"].add(user_id)
                        users_by_stage["paying"].discard(user_id)
                    elif event_type == "reactivated":
                        users_by_stage["reactivated"].add(user_id)
                        users_by_stage["churned"].discard(user_id)
                except:
                    continue
    except:
        pass

    # Convert to counts
    counts = {stage: len(users) for stage, users in users_by_stage.items()}

    # Calculate conversion rates
    total_ever = sum(counts.values())
    visitor_to_sub = (counts["subscribers"] / max(1, counts["visitors"])) * 100 if counts["visitors"] > 0 else 0
    sub_to_paying = (counts["paying"] / max(1, counts["subscribers"])) * 100 if counts["subscribers"] > 0 else 0
    paying_churn_rate = (counts["churned"] / max(1, counts["paying"] + counts["churned"])) * 100 if counts["paying"] + counts["churned"] > 0 else 0
    reactivation_rate = (counts["reactivated"] / max(1, counts["churned"])) * 100 if counts["churned"] > 0 else 0

    return {
        "period_days": days,
        "funnel_stages": counts,
        "total_historical": total_ever,
        "conversion_rates": {
            "visitor_to_subscriber": round(visitor_to_sub, 2),
            "subscriber_to_paying": round(sub_to_paying, 2),
            "paying_churn_rate": round(paying_churn_rate, 2),
            "reactivation_rate": round(reactivation_rate, 2),
        },
        "quality_score": round((visitor_to_sub + sub_to_paying) / 2, 2),  # simple quality metric
    }


def get_cohort_analysis() -> Dict[str, Any]:
    """Analyze user cohorts by signup month."""
    if not SPONSOR_FUNNEL_FILE.exists():
        return {"status": "no_data"}

    cohorts = {}  # cohort_month -> {subscribers, paying, churned}

    try:
        with open(SPONSOR_FUNNEL_FILE, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    event_time = datetime.fromisoformat(event["timestamp"])
                    cohort_month = event_time.strftime("%Y-%m")

                    if cohort_month not in cohorts:
                        cohorts[cohort_month] = {"visitors": 0, "paying": 0, "churned": 0}

                    if event["event_type"] == "visitor":
                        cohorts[cohort_month]["visitors"] += 1
                    elif event["event_type"] == "paying":
                        cohorts[cohort_month]["paying"] += 1
                    elif event["event_type"] == "churned":
                        cohorts[cohort_month]["churned"] += 1
                except:
                    continue
    except:
        pass

    # Calculate retention for each cohort
    retention = {}
    for cohort_month in sorted(cohorts.keys()):
        data = cohorts[cohort_month]
        visitor_count = data["visitors"]
        paying_count = data["paying"]

        if visitor_count > 0:
            retention[cohort_month] = {
                "visitors": visitor_count,
                "conversion_to_paying": round((paying_count / visitor_count) * 100, 2),
                "churn_count": data["churned"],
            }

    return {
        "cohort_analysis": retention,
        "best_performing_cohort": max(retention.items(), key=lambda x: x[1]["conversion_to_paying"])[0] if retention else None,
    }


def estimate_ltv(avg_monthly_payment: float = 5.0, avg_customer_lifespan_months: int = 12) -> Dict[str, Any]:
    """Estimate Lifetime Value of sponsors."""
    metrics = get_funnel_metrics()

    paying_sponsors = metrics["funnel_stages"]["paying"]
    churn_rate = metrics["conversion_rates"]["paying_churn_rate"] / 100

    # LTV = (avg monthly payment) / (monthly churn rate)
    # Simplified: LTV = avg_monthly * lifespan
    ltv = avg_monthly_payment * avg_customer_lifespan_months

    # Adjust based on actual churn
    if churn_rate > 0:
        adjusted_lifespan = 1 / churn_rate / 30  # months
        adjusted_ltv = avg_monthly_payment * adjusted_lifespan
    else:
        adjusted_ltv = ltv

    total_mrr = paying_sponsors * avg_monthly_payment

    return {
        "ltv_per_sponsor": round(ltv, 2),
        "ltv_adjusted_for_churn": round(adjusted_ltv, 2),
        "current_paying_sponsors": paying_sponsors,
        "monthly_recurring_revenue": round(total_mrr, 2),
        "projected_annual_revenue": round(total_mrr * 12, 2),
        "assumptions": {
            "avg_monthly_payment": avg_monthly_payment,
            "avg_customer_lifespan_months": avg_customer_lifespan_months,
            "actual_churn_rate": round(churn_rate * 100, 2),
        }
    }


def get_health_dashboard() -> Dict[str, Any]:
    """Complete health dashboard for sponsor growth."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "funnel": get_funnel_metrics(),
        "cohorts": get_cohort_analysis(),
        "ltv": estimate_ltv(),
        "status": "healthy" if get_funnel_metrics()["funnel_stages"]["paying"] > 0 else "early_stage",
    }
