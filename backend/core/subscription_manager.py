# ============================================================
# VIO 83 AI ORCHESTRA — Subscription & Plan Manager
# Copyright © 2026 Viorica Porcu (vio83) — All rights reserved
# ============================================================
"""
Gestione piani di abbonamento e accesso AI.

Ogni piano definisce:
- Quali AI provider l'utente può usare
- Quante richieste al giorno/mese
- Quali funzionalità sono attive
- Il prezzo corrispondente

Come un hotel con diverse tipologie di camera:
- Economy (free): solo stanza base (Ollama locale)
- Standard: stanza + colazione (AI locali + cloud free)
- Premium: suite (tutte le AI)
- Enterprise: piano intero (tutto + priorità + custom)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─── Definizione piani ──────────────────────────────────────────────

@dataclass(frozen=True)
class SubscriptionPlan:
    """Definizione di un piano di abbonamento."""
    plan_id: str
    name: str
    name_it: str
    description: str
    description_it: str
    price_monthly_eur: float
    price_yearly_eur: float
    providers: list[str]          # Provider AI inclusi
    max_requests_day: int         # Limite giornaliero
    max_requests_month: int       # Limite mensile
    features: list[str]           # Funzionalità incluse
    max_tokens_per_request: int   # Max token per singola richiesta
    priority: int                 # 1=base, 10=massima priorità


# Catalogo piani VIO 83 AI Orchestra
PLANS: dict[str, SubscriptionPlan] = {
    # ── Piano gratuito: solo AI locale ──
    "free_local": SubscriptionPlan(
        plan_id="free_local",
        name="Local Free",
        name_it="Locale Gratuito",
        description="Local AI only — Ollama models on your machine",
        description_it="Solo AI locale — modelli Ollama sulla tua macchina",
        price_monthly_eur=0.0,
        price_yearly_eur=0.0,
        providers=["ollama"],
        max_requests_day=100,
        max_requests_month=3000,
        features=["local_ai", "conversations", "history"],
        max_tokens_per_request=2048,
        priority=1,
    ),

    # ── Starter: locale + cloud gratuiti ──
    "starter": SubscriptionPlan(
        plan_id="starter",
        name="Starter",
        name_it="Starter",
        description="Local AI + free cloud providers (Groq, OpenRouter)",
        description_it="AI locale + provider cloud gratuiti (Groq, OpenRouter)",
        price_monthly_eur=4.99,
        price_yearly_eur=49.90,
        providers=["ollama", "groq", "together", "openrouter"],
        max_requests_day=200,
        max_requests_month=6000,
        features=["local_ai", "cloud_free", "conversations", "history", "analytics"],
        max_tokens_per_request=4096,
        priority=3,
    ),

    # ── Pro: tutti i provider economici ──
    "pro": SubscriptionPlan(
        plan_id="pro",
        name="Pro",
        name_it="Pro",
        description="All local + free + affordable cloud AI (DeepSeek, Mistral)",
        description_it="Tutte le AI locali + gratuite + cloud economiche (DeepSeek, Mistral)",
        price_monthly_eur=14.99,
        price_yearly_eur=149.90,
        providers=["ollama", "groq", "together", "openrouter", "deepseek", "mistral"],
        max_requests_day=500,
        max_requests_month=15000,
        features=[
            "local_ai", "cloud_free", "cloud_paid", "conversations", "history",
            "analytics", "cross_check", "rag", "auto_routing",
        ],
        max_tokens_per_request=8192,
        priority=5,
    ),

    # ── Premium: tutti i provider ──
    "premium": SubscriptionPlan(
        plan_id="premium",
        name="Premium",
        name_it="Premium",
        description="ALL AI providers — Claude, GPT-4, Gemini, Grok, Perplexity + everything",
        description_it="TUTTI i provider AI — Claude, GPT-4, Gemini, Grok, Perplexity + tutto",
        price_monthly_eur=29.99,
        price_yearly_eur=299.90,
        providers=[
            "ollama", "groq", "together", "openrouter",
            "deepseek", "mistral", "anthropic", "openai",
            "xai", "gemini", "perplexity",
        ],
        max_requests_day=1000,
        max_requests_month=30000,
        features=[
            "local_ai", "cloud_free", "cloud_paid", "cloud_premium",
            "conversations", "history", "analytics", "cross_check",
            "rag", "auto_routing", "workflow", "plugins",
            "priority_routing", "reasoning_amplifier",
        ],
        max_tokens_per_request=16384,
        priority=8,
    ),

    # ── Enterprise: tutto illimitato ──
    "enterprise": SubscriptionPlan(
        plan_id="enterprise",
        name="Enterprise",
        name_it="Enterprise",
        description="Unlimited — all AI, max performance, priority support, custom routing",
        description_it="Illimitato — tutte le AI, massime prestazioni, supporto prioritario",
        price_monthly_eur=99.99,
        price_yearly_eur=999.90,
        providers=[
            "ollama", "groq", "together", "openrouter",
            "deepseek", "mistral", "anthropic", "openai",
            "xai", "gemini", "perplexity",
        ],
        max_requests_day=999999,
        max_requests_month=999999,
        features=[
            "local_ai", "cloud_free", "cloud_paid", "cloud_premium",
            "conversations", "history", "analytics", "cross_check",
            "rag", "auto_routing", "workflow", "plugins",
            "priority_routing", "reasoning_amplifier",
            "omega_orchestrator", "world_data", "custom_models",
            "api_access", "white_label",
        ],
        max_tokens_per_request=32768,
        priority=10,
    ),
}


# ─── Subscription Manager ──────────────────────────────────────────

class SubscriptionManager:
    """
    Gestisce abbonamenti, limiti di utilizzo e accesso AI per utente.

    Controlla:
    - L'utente può usare questo provider? (piano lo include?)
    - Ha superato il limite giornaliero/mensile?
    - Quale max_tokens può usare?
    - Quali funzionalità ha attive?
    """

    def __init__(self):
        self._usage_cache: dict[str, dict] = {}  # user_id → {"day": count, "month": count}

    def get_plan(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Ottieni un piano per ID."""
        return PLANS.get(plan_id)

    def get_all_plans(self) -> list[dict]:
        """Lista tutti i piani disponibili per il frontend."""
        return [
            {
                "plan_id": p.plan_id,
                "name": p.name,
                "name_it": p.name_it,
                "description": p.description,
                "description_it": p.description_it,
                "price_monthly_eur": p.price_monthly_eur,
                "price_yearly_eur": p.price_yearly_eur,
                "providers": p.providers,
                "provider_count": len(p.providers),
                "max_requests_day": p.max_requests_day,
                "max_requests_month": p.max_requests_month,
                "features": p.features,
                "max_tokens_per_request": p.max_tokens_per_request,
            }
            for p in PLANS.values()
        ]

    def can_use_provider(self, plan_id: str, provider: str) -> bool:
        """L'utente con questo piano può usare questo provider?"""
        plan = PLANS.get(plan_id)
        if not plan:
            return False
        return provider in plan.providers

    def get_allowed_providers(self, plan_id: str) -> list[str]:
        """Lista provider consentiti per un piano."""
        plan = PLANS.get(plan_id)
        if not plan:
            return ["ollama"]  # Fallback sempre locale
        return list(plan.providers)

    def check_rate_limit(self, user_id: str, plan_id: str) -> dict:
        """
        Verifica se l'utente ha ancora richieste disponibili.
        Returns: {"allowed": bool, "remaining_day": int, "remaining_month": int}
        """
        plan = PLANS.get(plan_id)
        if not plan:
            return {"allowed": False, "remaining_day": 0, "remaining_month": 0, "reason": "Piano non valido"}

        usage = self._get_usage(user_id)
        day_remaining = plan.max_requests_day - usage.get("day", 0)
        month_remaining = plan.max_requests_month - usage.get("month", 0)

        if day_remaining <= 0:
            return {
                "allowed": False,
                "remaining_day": 0,
                "remaining_month": month_remaining,
                "reason": "Limite giornaliero raggiunto",
            }
        if month_remaining <= 0:
            return {
                "allowed": False,
                "remaining_day": day_remaining,
                "remaining_month": 0,
                "reason": "Limite mensile raggiunto",
            }

        return {
            "allowed": True,
            "remaining_day": day_remaining,
            "remaining_month": month_remaining,
        }

    def record_usage(self, user_id: str) -> None:
        """Registra un utilizzo per l'utente."""
        usage = self._get_usage(user_id)
        usage["day"] = usage.get("day", 0) + 1
        usage["month"] = usage.get("month", 0) + 1
        usage["last_used"] = time.time()
        self._usage_cache[user_id] = usage

    def get_max_tokens(self, plan_id: str) -> int:
        """Max token per richiesta per questo piano."""
        plan = PLANS.get(plan_id)
        return plan.max_tokens_per_request if plan else 2048

    def has_feature(self, plan_id: str, feature: str) -> bool:
        """L'utente ha questa funzionalità nel suo piano?"""
        plan = PLANS.get(plan_id)
        if not plan:
            return False
        return feature in plan.features

    def get_plan_for_provider(self, provider: str) -> str:
        """Quale piano minimo serve per questo provider?"""
        for plan_id, plan in sorted(PLANS.items(), key=lambda x: x[1].priority):
            if provider in plan.providers:
                return plan_id
        return "enterprise"

    def _get_usage(self, user_id: str) -> dict:
        """Ottieni o inizializza contatore utilizzo."""
        if user_id not in self._usage_cache:
            self._usage_cache[user_id] = {"day": 0, "month": 0, "last_reset_day": 0, "last_reset_month": 0}

        usage = self._usage_cache[user_id]
        now = time.time()
        day_start = now - (now % 86400)
        month_start = now - (now % (86400 * 30))

        # Reset giornaliero
        if usage.get("last_reset_day", 0) < day_start:
            usage["day"] = 0
            usage["last_reset_day"] = day_start

        # Reset mensile
        if usage.get("last_reset_month", 0) < month_start:
            usage["month"] = 0
            usage["last_reset_month"] = month_start

        return usage


# ─── Singleton ──────────────────────────────────────────────────────

_INSTANCE: Optional[SubscriptionManager] = None


def get_subscription_manager() -> SubscriptionManager:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = SubscriptionManager()
    return _INSTANCE
