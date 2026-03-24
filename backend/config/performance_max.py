"""
VIO 83 AI ORCHESTRA — Performance MAX Configuration
Versione: 2.1 (16 Marzo 2026)

Configurazione globale per massima potenza, intelligenza e ottimizzazione
Tutti i parametri sono ottimizzati per performance WORLD-CLASS
"""

import json
from enum import Enum

# ═══════════════════════════════════════════════════════════
# PERFORMANCE MODES
# ═══════════════════════════════════════════════════════════

class PerformanceMode(Enum):
    """Modalità di performance disponibili"""
    ULTRA_RESPONSIVE = "ultra_responsive"    # Speed > Quality
    BALANCED = "balanced"                    # Speed = Quality
    QUALITY_FIRST = "quality_first"          # Quality > Speed
    REASONING_DEEP = "reasoning_deep"        # Deep reasoning, ignori velocità
    COST_OPTIMIZED = "cost_optimized"        # Minimizza costo
    HYBRID_INTELLIGENT = "hybrid_intelligent"  # Auto-switch basato sul task


# ═══════════════════════════════════════════════════════════
# GLOBAL PERFORMANCE PARAMETERS
# ═══════════════════════════════════════════════════════════

PERFORMANCE_CONFIG = {
    "mode": PerformanceMode.HYBRID_INTELLIGENT.value,

    "orchestration": {
        "enable_auto_fallback": True,
        "max_fallback_retries": 3,
        "fallback_backoff_ms": 500,
        "enable_parallel_calls": True,  # Chiama più provr in parallelo e usa il più veloce
        "parallel_timeout_ms": 5000,
    },

    "caching": {
        "enable": True,
        "ttl_seconds": 3600,
        "max_cache_size_gb": 2,
        "cache_strategy": "lru",  # least-recently-used
    },

    "health_monitoring": {
        "check_interval_seconds": 300,  # Ogni 5 minuti
        "provr_timeout_seconds": 10,
        "enable_auto_disable_unhealthy": True,
        "unhealthy_threshold": 3,  # 3 fallback consecutivi = disabilita
    },

    "costs": {
        "enable_cost_tracking": True,
        "max_budget_per_day_usd": 100.0,
        "max_cost_per_request_usd": 5.0,
        "warn_if_exceeds_percent": 80.0,
    },

    "request_optimization": {
        "enable_compression": True,
        "enable_request_batching": True,
        "batch_size": 10,
        "timeout_ms": 30000,
        "retry_on_timeout": True,
        "max_retries": 3,
    },

    "response_optimization": {
        "enable_streaming": True,
        "enable_output_caching": True,
        "cache_similar_responses": True,
        "similarity_threshold": 0.95,
    },

    "model_selection": {
        "prefer_local_when_possible": False,  # Locale è lento, usa cloud
        "prefer_cheap_when_quality_sufficient": True,
        "enable_dynamic_routing": True,
        "update_routing_every_hours": 6,
    },

    "updates": {
        "enable_auto_model_discovery": True,
        "update_models_interval_hours": 1,
        "update_pricing_interval_hours": 2,
        "enable_auto_config_optimization": True,
    },

    "monitoring": {
        "enable_detailed_logging": True,
        "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
        "enable_metrics_collection": True,
        "metrics_retention_days": 30,
    },
}


# ═══════════════════════════════════════════════════════════
# PROVR PREFERENCES
# ═══════════════════════════════════════════════════════════

PROVR_PREFERENCES = {
    "preferred_by_task": {
        "code": ["qwen2.5-coder:3b", "claude-sonnet", "deepseek-reasoner"],
        "legal": ["claude-opus", "mistral-large", "llama3"],
        "medical": ["claude-opus", "gemini-2.5-pro", "mistral-large"],
        "writing": ["gpt-5.4", "claude-sonnet", "llama3"],
        "research": ["deep-research", "claude-opus", "pro-search"],
        "realtime": ["grok-4", "gemini-2.5-flash", "llama3.2"],
        "reasoning": ["deepseek-reasoner", "claude-opus", "gpt-5.4"],
    },

    "tier_preference_order": [
        "local",        # Gratis, veloce offline
        "free_cloud",   # Gratis, ottima qualità
        "cheap_cloud",  # Pochi centesimi
        "premium_cloud",  # Dollari ma il meglio
    ],

    "enable_tier_mixing": True,  # Usa più tier per lo stesso task se sensato
}


# ═══════════════════════════════════════════════════════════
# TASK-SPECIFIC OPTIMIZATIONS
# ═══════════════════════════════════════════════════════════

TASK_OPTIMIZATIONS = {
    "code": {
        "context_required_tokens": 8000,
        "max_latency_ms": 5000,
        "min_code_quality_score": 85,
        "enable_code_validation": True,
    },
    "legal": {
        "context_required_tokens": 32000,
        "max_latency_ms": 10000,
        "min_reasoning_score": 90,
        "enable_citation_tracking": True,
    },
    "reasoning": {
        "context_required_tokens": 16000,
        "max_latency_ms": 30000,  # Può essere lento, è ok
        "min_reasoning_score": 95,
        "prefer_slow_high_quality": True,
    },
    "realtime": {
        "context_required_tokens": 4000,
        "max_latency_ms": 2000,  # MUST be fast
        "prefer_speed_over_quality": True,
    },
}


# ═══════════════════════════════════════════════════════════
# AUTO-SCALING RULES
# ═══════════════════════════════════════════════════════════

AUTO_SCALING = {
    "enable": True,

    "cpu_threshold_percent": 80,  # Se CPU > 80%, scalea a provr più leggero
    "memory_threshold_percent": 75,
    "latency_threshold_ms": 5000,

    "scale_down_to": {
        "high_cpu": "qwen2.5-coder:3b",  # Leggero locale
        "high_memory": "gemma2:2b",       # Ultra-leggero
        "high_latency": "groq",           # Cloud veloce
    },

    "scale_up_to": {
        "low_quality": "claude-opus",     # Migliore assoluto
        "complex_task": "deepseek-reasoner",
    },
}


# ═══════════════════════════════════════════════════════════
# FALLBACK STRATEGY
# ═══════════════════════════════════════════════════════════

FALLBACK_CHAINS = {
    "code_primary": [
        "qwen2.5-coder:3b",           # Locale, veloce, buono per code
        "claude-sonnet",              # Premium, ottimo
        "deepseek-reasoner",          # Cheap, eccellente reasoning
        "groq llama-3.3-70b",         # Free cloud, veloce
    ],

    "code_quality_max": [
        "claude-opus",                # Migliore assoluto
        "deepseek-reasoner",          # Secondo topolino
        "gpt-5.4",                    # Terzo
        "mistral-large",              # Cheap alternative
    ],

    "reasoning_max": [
        "deepseek-reasoner",          # BEST reasoning
        "claude-opus",                # Secondo
        "gpt-5.4",                    # Terzo
    ],

    "speed_max": [
        "gemma2:2b",                  # VELOCISSIMO locale
        "groq gemma2-9b-it",          # Veloce cloud
        "mistral-small",              # Cheap + veloce
    ],

    "cost_optimized": [
        "ollama llama3",              # Gratis
        "groq",                       # Free cloud
        "deepseek-chat",              # $0.27/1M
        "mistral-small",              # $0.20/1M
    ],
}


# ═══════════════════════════════════════════════════════════
# BATCH PROCESSING RULES
# ═══════════════════════════════════════════════════════════

BATCH_PROCESSING = {
    "enable": True,
    "optimal_batch_size": 10,
    "max_batch_size": 100,
    "batch_timeout_seconds": 60,

    "smart_batching": {
        "group_by_provr": True,
        "group_by_task_type": True,
        "sort_by_cost": True,
    },
}


# ═══════════════════════════════════════════════════════════
# MONITORING DASHBOARD ENDPOINTS
# ═══════════════════════════════════════════════════════════

MONITORING_ENDPOINTS = {
    "health": "/api/v2/health",
    "provrs": "/api/v2/provrs",
    "models": "/api/v2/models",
    "costs": "/api/v2/costs",
    "performance": "/api/v2/performance",
    "routing": "/api/v2/routing",
    "logs": "/api/v2/logs",
}


# ═══════════════════════════════════════════════════════════
# DEFAULT PERFORMANCE PROFILE
# ═══════════════════════════════════════════════════════════

DEFAULT_PROFILE = {
    "name": "Production Max",
    "mode": PerformanceMode.HYBRID_INTELLIGENT.value,
    "optimized_for": ["speed", "quality", "cost", "availability"],
    "config": PERFORMANCE_CONFIG,
    "provr_preferences": PROVR_PREFERENCES,
    "fallback_chains": FALLBACK_CHAINS,
    "auto_scaling": AUTO_SCALING,
}


def get_config(mode: str = "default") -> dict:
    """Ritorna la configurazione per il mode specificato"""
    if mode == "default":
        return DEFAULT_PROFILE
    elif mode == "ultra_responsive":
        config = DEFAULT_PROFILE.copy()
        config["preference"] = FALLBACK_CHAINS["speed_max"]
        return config
    elif mode == "quality_first":
        config = DEFAULT_PROFILE.copy()
        config["preference"] = FALLBACK_CHAINS["code_quality_max"]
        return config
    elif mode == "cost_optimized":
        config = DEFAULT_PROFILE.copy()
        config["preference"] = FALLBACK_CHAINS["cost_optimized"]
        return config
    else:
        return DEFAULT_PROFILE


if __name__ == "__main__":
    print("\n🔥 VIO 83 AI ORCHESTRA — Performance MAX Config\n")
    print(json.dumps(DEFAULT_PROFILE, indent=2, default=str))
