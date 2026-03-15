# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA - Configurazione Provider AI
Mappa completa dei provider supportati con modelli e endpoint.

ORDINE PRIORITÀ:
1. LOCALI (Ollama) — Gratis, nessuna API key, sempre disponibili
2. CLOUD GRATUITI — API key gratis con limiti generosi
3. CLOUD A PAGAMENTO — API key con crediti a pagamento
"""

import os
from typing import Optional


# ═══════════════════════════════════════════════════════════
# PROVIDER LOCALI (Ollama) — PRIORITÀ 1: Gratis, sempre attivi
# ═══════════════════════════════════════════════════════════

LOCAL_PROVIDERS = {
    "ollama": {
        "name": "Ollama (Locale)",
        "host": "http://localhost:11434",
        "priority": 1,  # Massima priorità
        "cost": "free",
        "models": {
            # === Modelli installati sul Mac ===
            "llama3:latest": {
                "name": "Llama 3 8B",
                "ram_required_gb": 4.7,
                "strengths": ["general", "conversation", "reasoning", "multilingual"],
                "installed": True,
            },
            "mistral:latest": {
                "name": "Mistral 7B",
                "ram_required_gb": 4.4,
                "strengths": ["reasoning", "multilingual", "code"],
                "installed": True,
            },
            "codellama:latest": {
                "name": "Code Llama 7B",
                "ram_required_gb": 3.8,
                "strengths": ["code", "debugging", "programming"],
                "installed": True,
            },
            "gemma2:2b": {
                "name": "Gemma 2 2B",
                "ram_required_gb": 1.6,
                "strengths": ["lightweight", "fast", "simple_tasks"],
                "installed": True,
            },
            "llama3.2:3b": {
                "name": "Llama 3.2 3B",
                "ram_required_gb": 2.0,
                "strengths": ["general", "conversation", "fast"],
                "installed": True,
            },
            "qwen2.5-coder:3b": {
                "name": "Qwen 2.5 Coder 3B",
                "ram_required_gb": 1.9,
                "strengths": ["code", "fast", "efficient"],
                "installed": True,
            },
            # === Modelli scaricabili (non ancora installati) ===
            "phi3:3.8b": {
                "name": "Phi-3 3.8B",
                "ram_required_gb": 3.0,
                "strengths": ["reasoning", "efficient"],
                "installed": False,
            },
            "deepseek-coder-v2:lite": {
                "name": "DeepSeek Coder V2 Lite",
                "ram_required_gb": 3.5,
                "strengths": ["code", "debugging"],
                "installed": False,
            },
        },
        "default_model": "llama3:latest",
    }
}


# ═══════════════════════════════════════════════════════════
# PROVIDER CLOUD CON API KEY GRATUITA — PRIORITÀ 2
# Funzionano con piano free (limiti generosi)
# ═══════════════════════════════════════════════════════════

FREE_CLOUD_PROVIDERS = {
    "groq": {
        "name": "Groq (Gratis)",
        "litellm_prefix": "groq",
        "priority": 2,
        "cost": "free",
        "free_tier": "14,400 richieste/giorno, rate limit generoso",
        "signup_url": "https://console.groq.com/keys",
        "models": {
            "llama-3.3-70b-versatile": {
                "name": "Llama 3.3 70B (via Groq)",
                "context_window": 128000,
                "max_output": 8192,
                "strengths": ["general", "reasoning", "fast"],
                "cost_per_1m_input": 0.0,
                "cost_per_1m_output": 0.0,
            },
            "mixtral-8x7b-32768": {
                "name": "Mixtral 8x7B (via Groq)",
                "context_window": 32768,
                "max_output": 8192,
                "strengths": ["multilingual", "reasoning", "code"],
                "cost_per_1m_input": 0.0,
                "cost_per_1m_output": 0.0,
            },
            "gemma2-9b-it": {
                "name": "Gemma 2 9B (via Groq)",
                "context_window": 8192,
                "max_output": 8192,
                "strengths": ["fast", "efficient"],
                "cost_per_1m_input": 0.0,
                "cost_per_1m_output": 0.0,
            },
        },
        "env_key": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "together": {
        "name": "Together AI (Gratis)",
        "litellm_prefix": "together_ai",
        "priority": 2,
        "cost": "free",
        "free_tier": "$1 credito gratis alla registrazione",
        "signup_url": "https://api.together.xyz/settings/api-keys",
        "models": {
            "meta-llama/Llama-3.3-70B-Instruct-Turbo": {
                "name": "Llama 3.3 70B Turbo",
                "context_window": 131072,
                "max_output": 8192,
                "strengths": ["general", "reasoning", "multilingual"],
                "cost_per_1m_input": 0.88,
                "cost_per_1m_output": 0.88,
            },
            "deepseek-ai/DeepSeek-R1-Distill-Llama-70B": {
                "name": "DeepSeek R1 Distill 70B",
                "context_window": 131072,
                "max_output": 8192,
                "strengths": ["deep_reasoning", "math", "science"],
                "cost_per_1m_input": 0.88,
                "cost_per_1m_output": 0.88,
            },
        },
        "env_key": "TOGETHER_API_KEY",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    },
    "openrouter": {
        "name": "OpenRouter (Gratis)",
        "litellm_prefix": "openrouter",
        "priority": 2,
        "cost": "free",
        "free_tier": "Modelli gratuiti illimitati + $1 credito",
        "signup_url": "https://openrouter.ai/keys",
        "models": {
            "meta-llama/llama-3.3-70b-instruct:free": {
                "name": "Llama 3.3 70B (gratis)",
                "context_window": 131072,
                "max_output": 8192,
                "strengths": ["general", "reasoning"],
                "cost_per_1m_input": 0.0,
                "cost_per_1m_output": 0.0,
            },
            "deepseek/deepseek-r1:free": {
                "name": "DeepSeek R1 (gratis)",
                "context_window": 64000,
                "max_output": 8192,
                "strengths": ["deep_reasoning", "math", "code"],
                "cost_per_1m_input": 0.0,
                "cost_per_1m_output": 0.0,
            },
            "google/gemma-2-9b-it:free": {
                "name": "Gemma 2 9B (gratis)",
                "context_window": 8192,
                "max_output": 8192,
                "strengths": ["fast", "efficient"],
                "cost_per_1m_input": 0.0,
                "cost_per_1m_output": 0.0,
            },
        },
        "env_key": "OPENROUTER_API_KEY",
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
    },
}


# ═══════════════════════════════════════════════════════════
# PROVIDER CLOUD A PAGAMENTO — PRIORITÀ 3
# Richiedono API key con crediti a pagamento
# Ordinati: dal più economico al più costoso
# ═══════════════════════════════════════════════════════════

CLOUD_PROVIDERS = {
    # --- TIER 1: Economici (< $1/1M token) ---
    "deepseek": {
        "name": "DeepSeek",
        "litellm_prefix": "deepseek",
        "priority": 3,
        "cost": "paid_cheap",
        "models": {
            "deepseek-chat": {
                "name": "DeepSeek Chat V3",
                "context_window": 64000,
                "max_output": 8192,
                "strengths": ["code", "math", "reasoning"],
                "cost_per_1m_input": 0.27,
                "cost_per_1m_output": 1.10,
            },
            "deepseek-reasoner": {
                "name": "DeepSeek R1",
                "context_window": 64000,
                "max_output": 8192,
                "strengths": ["deep_reasoning", "math", "science"],
                "cost_per_1m_input": 0.55,
                "cost_per_1m_output": 2.19,
            },
        },
        "env_key": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
    },
    "mistral": {
        "name": "Mistral AI",
        "litellm_prefix": "mistral",
        "priority": 3,
        "cost": "paid_cheap",
        "models": {
            "mistral-small-latest": {
                "name": "Mistral Small",
                "context_window": 128000,
                "max_output": 8192,
                "strengths": ["speed", "cost_effective", "multilingual"],
                "cost_per_1m_input": 0.2,
                "cost_per_1m_output": 0.6,
            },
            "mistral-large-latest": {
                "name": "Mistral Large",
                "context_window": 128000,
                "max_output": 8192,
                "strengths": ["multilingual", "reasoning", "code"],
                "cost_per_1m_input": 2.0,
                "cost_per_1m_output": 6.0,
            },
        },
        "env_key": "MISTRAL_API_KEY",
        "default_model": "mistral-small-latest",
    },
    # --- TIER 2: Standard ($1-5/1M token) ---
    "claude": {
        "name": "Anthropic Claude",
        "litellm_prefix": "anthropic",
        "priority": 3,
        "cost": "paid_standard",
        "models": {
            "claude-haiku-3-5-20241022": {
                "name": "Claude Haiku 3.5",
                "context_window": 200000,
                "max_output": 8192,
                "strengths": ["speed", "simple_tasks", "classification"],
                "cost_per_1m_input": 0.25,
                "cost_per_1m_output": 1.25,
            },
            "claude-sonnet-4-20250514": {
                "name": "Claude Sonnet 4",
                "context_window": 200000,
                "max_output": 8192,
                "strengths": ["code", "analysis", "reasoning", "writing"],
                "cost_per_1m_input": 3.0,
                "cost_per_1m_output": 15.0,
            },
            "claude-opus-4-20250514": {
                "name": "Claude Opus 4",
                "context_window": 200000,
                "max_output": 8192,
                "strengths": ["complex_reasoning", "research", "creative"],
                "cost_per_1m_input": 15.0,
                "cost_per_1m_output": 75.0,
            },
        },
        "env_key": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-20250514",
    },
    "gpt4": {
        "name": "OpenAI GPT-4",
        "litellm_prefix": "openai",
        "priority": 3,
        "cost": "paid_standard",
        "models": {
            "gpt-4o-mini": {
                "name": "GPT-4o Mini",
                "context_window": 128000,
                "max_output": 16384,
                "strengths": ["speed", "cost_effective"],
                "cost_per_1m_input": 0.15,
                "cost_per_1m_output": 0.60,
            },
            "gpt-4o": {
                "name": "GPT-4o",
                "context_window": 128000,
                "max_output": 16384,
                "strengths": ["creative", "multimodal", "general"],
                "cost_per_1m_input": 2.50,
                "cost_per_1m_output": 10.0,
            },
        },
        "env_key": "OPENAI_API_KEY",
        "default_model": "gpt-4o",
    },
    "grok": {
        "name": "xAI Grok",
        "litellm_prefix": "xai",
        "priority": 3,
        "cost": "paid_standard",
        "models": {
            "grok-2": {
                "name": "Grok 2",
                "context_window": 131072,
                "max_output": 8192,
                "strengths": ["realtime", "news", "humor", "unfiltered"],
                "cost_per_1m_input": 2.0,
                "cost_per_1m_output": 10.0,
            },
        },
        "env_key": "XAI_API_KEY",
        "default_model": "grok-2",
    },
    "google": {
        "name": "Google Gemini",
        "litellm_prefix": "gemini",
        "priority": 3,
        "cost": "paid_standard",
        "models": {
            "gemini-2.0-flash": {
                "name": "Gemini 2.0 Flash",
                "context_window": 1000000,
                "max_output": 8192,
                "strengths": ["speed", "multimodal", "long_context"],
                "cost_per_1m_input": 0.075,
                "cost_per_1m_output": 0.30,
            },
            "gemini-2.5-pro": {
                "name": "Gemini 2.5 Pro",
                "context_window": 1000000,
                "max_output": 8192,
                "strengths": ["reasoning", "multimodal", "long_context"],
                "cost_per_1m_input": 1.25,
                "cost_per_1m_output": 10.0,
            },
        },
        "env_key": "GEMINI_API_KEY",
        "default_model": "gemini-2.0-flash",
    },
}


# ═══════════════════════════════════════════════════════════
# TUTTI I PROVIDER COMBINATI (per lookup rapido)
# ═══════════════════════════════════════════════════════════

ALL_CLOUD_PROVIDERS = {**FREE_CLOUD_PROVIDERS, **CLOUD_PROVIDERS}


# ═══════════════════════════════════════════════════════════
# ROUTING INTELLIGENTE PER TIPO DI RICHIESTA
# ═══════════════════════════════════════════════════════════

REQUEST_TYPE_ROUTING = {
    "code": {
        "local_primary": "codellama:latest",
        "local_fallback": "qwen2.5-coder:3b",
        "free_cloud": "groq",
        "cloud_primary": "claude",
        "cloud_fallback": "deepseek",
    },
    "creative": {
        "local_primary": "llama3:latest",
        "local_fallback": "mistral:latest",
        "free_cloud": "openrouter",
        "cloud_primary": "gpt4",
        "cloud_fallback": "claude",
    },
    "analysis": {
        "local_primary": "llama3:latest",
        "local_fallback": "mistral:latest",
        "free_cloud": "groq",
        "cloud_primary": "claude",
        "cloud_fallback": "mistral",
    },
    "realtime": {
        "local_primary": "llama3.2:3b",
        "local_fallback": "gemma2:2b",
        "free_cloud": "groq",
        "cloud_primary": "grok",
        "cloud_fallback": "gpt4",
    },
    "reasoning": {
        "local_primary": "llama3:latest",
        "local_fallback": "mistral:latest",
        "free_cloud": "openrouter",
        "cloud_primary": "claude",
        "cloud_fallback": "deepseek",
    },
    "conversation": {
        "local_primary": "llama3:latest",
        "local_fallback": "llama3.2:3b",
        "free_cloud": "groq",
        "cloud_primary": "claude",
        "cloud_fallback": "gpt4",
    },
    "math": {
        "local_primary": "mistral:latest",
        "local_fallback": "llama3:latest",
        "free_cloud": "openrouter",
        "cloud_primary": "deepseek",
        "cloud_fallback": "claude",
    },
}


# ═══════════════════════════════════════════════════════════
# FUNZIONI HELPER
# ═══════════════════════════════════════════════════════════

def get_available_cloud_providers() -> dict:
    """Ritorna solo i provider cloud con API key configurata."""
    available = {}
    for key, provider in ALL_CLOUD_PROVIDERS.items():
        env_key = provider["env_key"]
        if os.environ.get(env_key):
            available[key] = provider
    return available


def get_free_cloud_providers() -> dict:
    """Ritorna i provider cloud gratuiti con API key configurata."""
    available = {}
    for key, provider in FREE_CLOUD_PROVIDERS.items():
        env_key = provider["env_key"]
        if os.environ.get(env_key):
            available[key] = provider
    return available


def get_all_providers_ordered() -> list[dict]:
    """
    Ritorna TUTTI i provider ordinati per priorità:
    1. Locali (Ollama) — gratis, sempre disponibili
    2. Cloud gratuiti (Groq, Together, OpenRouter) — gratis con API key
    3. Cloud economici (DeepSeek, Mistral) — pochi centesimi
    4. Cloud standard (Claude, GPT-4, Grok, Gemini) — dollari
    """
    providers = []

    # 1. Locali
    for key, prov in LOCAL_PROVIDERS.items():
        providers.append({
            "id": key,
            "tier": "local",
            "priority": prov.get("priority", 1),
            **prov,
        })

    # 2. Cloud gratuiti
    for key, prov in FREE_CLOUD_PROVIDERS.items():
        env_key = prov["env_key"]
        providers.append({
            "id": key,
            "tier": "free_cloud",
            "priority": prov.get("priority", 2),
            "available": bool(os.environ.get(env_key)),
            **prov,
        })

    # 3. Cloud a pagamento
    for key, prov in CLOUD_PROVIDERS.items():
        env_key = prov["env_key"]
        providers.append({
            "id": key,
            "tier": "paid_cloud",
            "priority": prov.get("priority", 3),
            "available": bool(os.environ.get(env_key)),
            **prov,
        })

    return sorted(providers, key=lambda p: p["priority"])


def get_litellm_model_string(provider: str, model: Optional[str] = None) -> str:
    """Costruisci la stringa modello per LiteLLM."""
    # Check in tutti i provider cloud
    for providers_dict in [FREE_CLOUD_PROVIDERS, CLOUD_PROVIDERS]:
        if provider in providers_dict:
            prefix = providers_dict[provider]["litellm_prefix"]
            model_name = model or providers_dict[provider]["default_model"]
            return f"{prefix}/{model_name}"
    return model or "ollama/llama3:latest"
