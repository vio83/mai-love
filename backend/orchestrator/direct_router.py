# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA - Direct Orchestrator (senza LiteLLM)
Gestisce chiamate dirette a Ollama e provider cloud via HTTP.
Non dipende da LiteLLM — funziona con Python 3.14.
"""

import re
import os
import time
import json
import asyncio
import logging
import random
from typing import Optional, AsyncGenerator
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from backend.core.tracing import traced_span
from backend.config.providers import (
    CLOUD_PROVRS,
    FREE_CLOUD_PROVRS,
    REQUEST_TYPE_ROUTING,
)

# Per chiamate async HTTP usiamo aiohttp se disponibile, altrimenti asyncio
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    logging.getLogger(__name__).warning(
        "httpx non disponibile — fallback a urllib (prestazioni ridotte in async)"
    )

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


# === SYSTEM PROMPT CERTIFICATO VIO 83 ===
# Importato dal modulo dedicato (versione completa con tutti i campi)

from backend.orchestrator.system_prompt import (
    VIO83_MASTER_PROMPT,
    build_system_prompt,
    build_local_system_prompt,
)

# === AUTO-LEARNING + SELF-OPTIMIZATION + REASONING ENGINES ===
from backend.core.auto_learner import get_auto_learner
from backend.core.self_optimizer import get_self_optimizer
from backend.core.world_knowledge import get_world_knowledge
from backend.core.reasoning_engine import get_reasoning_engine
from backend.core.errors import (
    ErrorCode,
    OrchestraError,
    ProvrException,
    NetworkException,
)
from backend.core.network import get_connection_pool

# === JETENGINE™ + KNOWLEDGE TAXONOMY ===
from backend.core.jet_engine import get_jet_engine
from backend.core.knowledge_taxonomy import get_optimal_config

# Alias per retrocompatibilità (server.py lo importa come VIO83_SYSTEM_PROMPT)
VIO83_SYSTEM_PROMPT = VIO83_MASTER_PROMPT
logger = logging.getLogger(__name__)


# === CLASSIFICAZIONE RICHIESTE ===

KEYWORDS = {
    "code": ["codice", "code", "funzione", "function", "bug", "debug", "api",
             "database", "sql", "python", "javascript", "typescript", "react",
             "script", "algoritmo", "classe", "metodo", "array", "json",
             "html", "css", "endpoint", "backend", "frontend"],
    "legal": ["legge", "norma", "contratto", "compliance", "gdpr", "privacy",
              "tribunale", "sentenza", "clausola", "regolamento", "licenza", "diritto"],
    "medical": ["medicina", "clinico", "diagnosi", "terapia", "farmaco", "sintomo",
                "linea guida", "paziente", "epmiologia", "oncologia", "cardiologia", "pubmed"],
    "writing": ["linkedin", "headline", "about", "copy", "newsletter", "ghostwrite",
                "articolo", "post", "caption", "seo", "landing page", "scrittura"],
    "research": ["ricerca", "paper", "citazioni", "fonti", "survey", "benchmark",
                 "state of the art", "deep research", "letteratura", "bibliografia"],
    "automation": ["workflow", "automazione", "agent", "agente", "tool", "mcp",
                   "n8n", "pipeline", "orchestrazione", "browser automation", "task runner",
                   "openclaw", "esegui tool", "run tool", "multi-step", "usa plugin"],
    "creative": ["scrivi", "write", "storia", "story", "poesia", "poem",
                 "creativo", "creative", "articolo", "article", "blog",
                 "racconto", "romanzo", "canzone", "email", "lettera"],
    "analysis": ["analiz", "analy", "dati", "data", "grafico", "chart",
                 "statistic", "csv", "excel", "tabella", "confronta",
                 "compare", "trend", "metrica", "report"],
    "realtime": ["oggi", "today", "attual", "current", "news", "notizie",
                 "ultimo", "latest", "2026", "2025", "tempo reale"],
    "reasoning": ["spiega", "explain", "perché", "why", "come funziona",
                  "how does", "ragion", "reason", "logic", "matematica",
                  "math", "teoria", "filosofia", "dimostrazione"],
}

ROUTING_MAP = {
    "code": "claude",
    "legal": "claude",
    "medical": "claude",
    "writing": "claude",
    "research": "perplexity",
    "automation": "claude",
    "creative": "gpt4",
    "analysis": "claude",
    "realtime": "grok",
    "reasoning": "claude",
    "conversation": "claude",
}

# ─── Embedding-based Classification (via Ollama) ───────────────────

import math as _math
import logging as _logging

_log = _logging.getLogger("embedding_classifier")

# Frasi di riferimento per ogni categoria (embeddings pre-calcolati al primo uso)
_REFERENCE_PHRASES: dict[str, list[str]] = {
    "code": [
        "scrivi una funzione Python",
        "debug this JavaScript error",
        "create a REST API endpoint",
        "fix the SQL query bug",
    ],
    "legal": [
        "analizza questo contratto",
        "GDPR compliance requirements",
        "clausola di riservatezza",
    ],
    "medical": [
        "diagnosi differenziale per questi sintomi",
        "terapia farmacologica raccomanda",
        "linee guida cliniche",
    ],
    "writing": [
        "scrivi un post LinkedIn",
        "write a newsletter article",
        "SEO copywriting headline",
    ],
    "research": [
        "ricerca accademica su questo argomento",
        "trova paper e citazioni",
        "state of the art survey",
    ],
    "automation": [
        "crea un workflow di automazione",
        "configura un agent multi-step",
        "orchestrazione pipeline n8n",
    ],
    "creative": [
        "scrivi una storia creativa",
        "write a poem about nature",
        "inventa un racconto originale",
    ],
    "analysis": [
        "analizza questi dati CSV",
        "crea un grafico statistico",
        "confronta i trend nei dati",
    ],
    "realtime": [
        "quali sono le notizie di oggi",
        "what is the latest news about",
        "aggiornamenti in tempo reale",
    ],
    "reasoning": [
        "spiega perché funziona così",
        "ragionamento logico step by step",
        "dimostra questo teorema matematico",
    ],
}

# Cache embeddings di riferimento (calcolati una sola volta)
_REF_EMBEDDINGS: dict[str, list[list[float]]] = {}
_EMBED_MODEL = "nomic-embed-text"  # modello embedding leggero


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Cosine similarity tra due vettori."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = _math.sqrt(sum(x * x for x in a))
    norm_b = _math.sqrt(sum(x * x for x in b))
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return dot / (norm_a * norm_b)


def _get_embedding_sync(text: str) -> list[float] | None:
    """Chiama Ollama /api/embeddings in modo sincrono."""
    import json as _json
    try:
        body = _json.dumps({"model": _EMBED_MODEL, "prompt": text}).encode()
        req = Request(
            "http://127.0.0.1:11434/api/embeddings",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=5) as resp:
            data = _json.loads(resp.read())
            return data.get("embedding")
    except Exception:
        return None


def _ensure_ref_embeddings() -> bool:
    """
    Calcola embeddings di riferimento per ogni categoria (lazy, una sola volta).
    Ritorna True se disponibili, False se Ollama non ha il modello.
    """
    # _REF_EMBEDDINGS è un dict mutabile a livello modulo — no global necessario
    if _REF_EMBEDDINGS:
        return True

    # Test con una frase
    test = _get_embedding_sync("test")
    if test is None:
        return False

    for cat, phrases in _REFERENCE_PHRASES.items():
        embeddings = []
        for phrase in phrases:
            emb = _get_embedding_sync(phrase)
            if emb:
                embeddings.append(emb)
        if embeddings:
            _REF_EMBEDDINGS[cat] = embeddings

    if _REF_EMBEDDINGS:
        _log.info(f"[EmbeddingClassifier] Caricati {len(_REF_EMBEDDINGS)} categorie con embeddings")
    return bool(_REF_EMBEDDINGS)


def classify_request_embedding(message: str) -> tuple[str, float]:
    """
    Classifica una richiesta usando cosine similarity con embedding Ollama.

    Returns:
        (request_type, confidence) — tipo e confnza [0, 1]
    """
    if not _ensure_ref_embeddings():
        # Fallback a keyword
        return classify_request(message), 0.5

    msg_emb = _get_embedding_sync(message)
    if msg_emb is None:
        return classify_request(message), 0.5

    best_type = "conversation"
    best_score = -1.0

    for cat, ref_embs in _REF_EMBEDDINGS.items():
        # Media della max similarity con ogni frase di riferimento
        sims = [_cosine_sim(msg_emb, ref) for ref in ref_embs]
        avg_sim = sum(sims) / len(sims) if sims else 0.0
        if avg_sim > best_score:
            best_score = avg_sim
            best_type = cat

    confidence = max(0.0, min(1.0, best_score))
    return best_type, confidence


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except Exception:
        return default


def _execution_profile() -> str:
    raw = os.environ.get("VIO_EXECUTION_PROFILE", "real-max-local").strip().lower()
    if raw in {"", "balanced", "real-max", "hybrid"}:
        return "real-max-local"
    return raw


def _speed_mode_enabled() -> bool:
    return _env_flag("VIO_SPEED_MODE", True)


def _force_local_orchestration(mode: str) -> bool:
    """Controlla se l'orchestrazione deve restare locale.
    Rispetta VIO_NO_HYBRID da .env: se true forza locale, altrimenti segue il mode della request.
    """
    env_val = os.environ.get("VIO_NO_HYBRID", "").strip().lower()
    if env_val in ("true", "1", "yes"):
        return True
    return mode == "local"


def _local_model_candidates(
    request_type: str,
    explicit_model: Optional[str],
    default_model: str,
    prefer_fast: bool = False,
) -> list[str]:
    if explicit_model:
        return [explicit_model]

    routing = REQUEST_TYPE_ROUTING.get(request_type, {})
    preference = os.environ.get("VIO_LOCAL_MODEL_PREFERENCE", "").strip()

    fast_chain = [
        "smollm2:135m",
        "smollm2:360m",
        "qwen2.5:0.5b",
        "qwen2.5:1.5b",
    ]

    quality_chain = [
        preference,
        routing.get("local_primary"),
        routing.get("local_fallback"),
        default_model,
        "qwen2.5-coder:3b",
        "llama3.2:3b",
        "gemma2:2b",
        "mistral:latest",
        "llama3:latest",
    ]

    raw_candidates = ([*fast_chain, *quality_chain] if prefer_fast else quality_chain)

    seen: set[str] = set()
    candidates: list[str] = []
    for item in raw_candidates:
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        candidates.append(item)

    return candidates


def _effective_generation_params(
    request_type: str,
    last_msg: str,
    requested_temperature: float,
    requested_max_tokens: int,
) -> tuple[float, int, bool]:
    speed_mode = _speed_mode_enabled()

    hard_cap = _env_int("VIO_MAX_TOKENS_HARD_CAP", 768)
    turbo_cap = _env_int("VIO_TURBO_MAX_TOKENS", 320)
    medium_cap = _env_int("VIO_MEDIUM_MAX_TOKENS", 512)

    message_len = len((last_msg or "").strip())
    short_query = message_len <= 180

    if not speed_mode:
        capped = min(max(64, requested_max_tokens), max(128, hard_cap))
        temp = max(0.0, min(1.0, requested_temperature))
        return temp, capped, False

    # Turbo strategy: meno token, temperatura più bassa, modello più rapido per query brevi.
    if short_query and request_type in {"conversation", "realtime", "analysis", "reasoning"}:
        capped = min(max(64, requested_max_tokens), max(128, turbo_cap))
        temp = min(requested_temperature, 0.2)
        return temp, capped, True

    capped = min(max(96, requested_max_tokens), max(192, medium_cap))
    temp = min(requested_temperature, 0.25)
    return temp, capped, False

ALL_CLOUD_ROUTER_PROVRS = {
    **FREE_CLOUD_PROVRS,
    **CLOUD_PROVRS,
}

PERPLEXITY_PRESETS = {"pro-search", "deep-research"}

# Pre-compiled classification patterns — ~10x faster than keyword loops
_CLASSIFY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (req_type, re.compile(r"\b(?:" + "|".join(re.escape(kw) for kw in kws) + r")\b", re.IGNORECASE))
    for req_type, kws in KEYWORDS.items()
]


def classify_request(message: str) -> str:
    """Classifica il tipo di richiesta per il routing intelligente (pre-compiled regex)."""
    best_type = "conversation"
    best_score = 0
    for req_type, pattern in _CLASSIFY_PATTERNS:
        matches = pattern.findall(message)
        if len(matches) > best_score:
            best_score = len(matches)
            best_type = req_type
    return best_type


def route_to_provr(request_type: str, mode: str = "cloud") -> str:
    """Determina il provider ottimale basato sul tipo di richiesta."""
    if mode == "local":
        return "ollama"
    return ROUTING_MAP.get(request_type, "claude")


def _resolve_cloud_provr_entry(provider: str) -> dict:
    entry = ALL_CLOUD_ROUTER_PROVRS.get(provider)
    if not entry:
        raise ProvrException(OrchestraError(
            code=ErrorCode.PROVR_UNAVAILABLE,
            message=f"Provider cloud non supportato: {provider}",
            provider=provider,
            recoverable=False,
            suggestion="Usa un provider configurato in backend/config/providers.py",
        ))
    return entry


def _resolve_cloud_model(provider: str, requested_model: Optional[str] = None) -> str:
    entry = _resolve_cloud_provr_entry(provider)
    models = entry.get("models", {})
    default_model = entry.get("default_model")

    if requested_model:
        if requested_model in models:
            return requested_model
        # Accetta override esplicito anche se non in registry (compatibilità avanzata)
        return requested_model

    if default_model:
        return default_model

    if models:
        return next(iter(models.keys()))

    raise ProvrException(OrchestraError(
        code=ErrorCode.PROVR_MODEL_NOT_FOUND,
        message=f"Nessun modello disponibile per provider {provider}",
        provider=provider,
        recoverable=False,
        suggestion="Imposta default_model o aggiungi almeno un modello al registry del provider",
    ))


def _resolve_cloud_api_key(provider: str) -> str:
    entry = _resolve_cloud_provr_entry(provider)
    env_key = entry.get("env_key")
    if not env_key:
        raise ProvrException(OrchestraError(
            code=ErrorCode.CONFIG_INVALID_VALUE,
            message=f"env_key mancante per provider {provider}",
            provider=provider,
            recoverable=False,
        ))

    api_key = os.environ.get(env_key, "").strip()
    if not api_key:
        raise ProvrException(OrchestraError(
            code=ErrorCode.CONFIG_MISSING_KEY,
            message=f"API key mancante per provider '{provider}'",
            details=f"Imposta {env_key} nel file .env",
            provider=provider,
            recoverable=False,
            suggestion=f"Aggiungi {env_key} al file .env o usa mode='local'",
        ))
    return api_key


def _cloud_base_url(provider: str) -> str:
    base_urls = {
        "claude": "https://api.anthropic.com/v1",
        "gpt4": "https://api.openai.com/v1",
        "grok": "https://api.x.ai/v1",
        "mistral": "https://api.mistral.ai/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "google": "https://generativelanguage.googleapis.com/v1beta/openai",
        "groq": "https://api.groq.com/openai/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "together": "https://api.together.xyz/v1",
        "perplexity": "https://api.perplexity.ai/v1",
    }
    if provider not in base_urls:
        raise ProvrException(OrchestraError(
            code=ErrorCode.CONFIG_INVALID_VALUE,
            message=f"Base URL non configurata per provider {provider}",
            provider=provider,
            recoverable=False,
        ))
    return base_urls[provider]


def _retryable_http_status(status_code: int) -> bool:
    return status_code in {408, 409, 425, 429, 500, 502, 503, 504}


def _retry_delay_seconds(attempt: int, retry_after: float | None = None) -> float:
    """Exponential backoff con jitter e supporto Retry-After header."""
    if retry_after is not None and retry_after > 0:
        # Rispetta il Retry-After del server, con cap a 60s per sicurezza
        return min(retry_after + random.uniform(0.0, 0.5), 60.0)
    delay = min(1.0 * (2 ** attempt), 16.0)
    # Full jitter: delay uniformemente distribuito in [0, delay]
    return random.uniform(0.5, delay) + random.uniform(0.0, 0.25)


def _extract_retry_after(headers: dict | None) -> float | None:
    """Estrae Retry-After header (secondi o HTTP-date) da risposta."""
    if not headers:
        return None
    val = None
    for k, v in headers.items():
        if k.lower() == "retry-after":
            val = v
            break
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _orchestra_http_error(
    provider: str,
    status_code: int,
    details: str,
    model: Optional[str] = None,
) -> ProvrException:
    truncated = (details or "")[:600]
    if status_code in {401, 403}:
        code = ErrorCode.PROVR_AUTH_FAILED
        suggestion = "Verifica la API key e i permessi del provider"
        recoverable = False
    elif status_code == 404:
        code = ErrorCode.PROVR_MODEL_NOT_FOUND
        suggestion = "Verifica modello ed endpoint configurati per il provider"
        recoverable = False
    elif status_code == 429:
        code = ErrorCode.PROVR_RATE_LIMITED
        suggestion = "Riduci il rate o attendi il reset del provider"
        recoverable = True
    else:
        code = ErrorCode.PROVR_UNAVAILABLE
        suggestion = "Riprova o usa un provider di fallback"
        recoverable = _retryable_http_status(status_code)

    return ProvrException(OrchestraError(
        code=code,
        message=f"{provider} ha risposto con HTTP {status_code}",
        details=truncated,
        provider=provider,
        model=model,
        recoverable=recoverable,
        suggestion=suggestion,
    ))


def _normalize_transport_exception(
    provider: str,
    exc: Exception,
    model: Optional[str] = None,
) -> Exception:
    if isinstance(exc, (ProvrException, NetworkException)):
        return exc

    message = str(exc)

    if "Circuit breaker OPEN" in message:
        return NetworkException(OrchestraError(
            code=ErrorCode.NETWORK_CIRCUIT_OPEN,
            message=f"Circuit breaker aperto per {provider}",
            details=message,
            provider=provider,
            model=model,
            suggestion="Attendi il reset del circuito o usa un fallback provider",
        ))

    if HAS_HTTPX and isinstance(exc, httpx.HTTPStatusError):
        try:
            response_text = exc.response.text
        except Exception:
            response_text = message
        return _orchestra_http_error(provider, exc.response.status_code, response_text, model=model)

    if HAS_HTTPX and isinstance(exc, httpx.TimeoutException):
        return NetworkException(OrchestraError(
            code=ErrorCode.PROVR_TIMEOUT,
            message=f"Timeout verso provider {provider}",
            details=message,
            provider=provider,
            model=model,
            suggestion="Riprova con un modello piu rapido o aumenta il timeout",
        ))

    if isinstance(exc, (ConnectionError, OSError, URLError)):
        return NetworkException(OrchestraError(
            code=ErrorCode.NETWORK_CONNECTION_FAILED,
            message=f"Errore di connessione verso {provider}",
            details=message,
            provider=provider,
            model=model,
            suggestion="Verifica connettivita, DNS e disponibilita del servizio",
        ))

    return ProvrException(OrchestraError(
        code=ErrorCode.SYSTEM_UNKNOWN,
        message=f"Errore imprevisto del provider {provider}",
        details=message[:600],
        provider=provider,
        model=model,
    ))


def _ensure_network_provider_registered(
    provider: str,
    base_url: str,
    timeout_s: float,
) -> None:
    pool = get_connection_pool()
    if provider in pool.stats.get("providers", {}):
        return

    rate_limit = 100 if provider == "ollama" else 30
    pool.register_provr(
        provider,
        base_url=base_url,
        timeout=timeout_s,
        rate_limit=rate_limit,
    )


def _build_cloud_headers(provider: str, api_key: str) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    if provider == "claude":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"

    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/vio83/vio83-ai-orchestra"
        headers["X-Title"] = "VIO 83 AI ORCHESTRA"

    return headers


def _normalize_messages_for_claude(messages: list[dict]) -> tuple[str, list[dict]]:
    # Fast path: skip processing if no system messages exist
    if not any(m.get("role") == "system" for m in messages):
        normalized = [
            {"role": ("assistant" if m.get("role") == "assistant" else "user"), "content": m.get("content", "")}
            for m in messages
        ]
        return "", normalized or [{"role": "user", "content": ""}]

    system_parts: list[str] = []
    anthropic_messages: list[dict] = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            if content:
                system_parts.append(content)
            continue

        normalized_role = "assistant" if role == "assistant" else "user"
        anthropic_messages.append({
            "role": normalized_role,
            "content": content,
        })

    if not anthropic_messages:
        anthropic_messages = [{"role": "user", "content": ""}]

    return "\n\n".join(system_parts), anthropic_messages


def _extract_perplexity_output(data: dict) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = data.get("output")
    if isinstance(output, list):
        chunks: list[str] = []
        for item in output:
            content = item.get("content") if isinstance(item, dict) else None
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        text = part.get("text")
                        if isinstance(text, str) and text:
                            chunks.append(text)
        if chunks:
            return "".join(chunks).strip()

    return ""


async def _http_post_json(
    url: str,
    headers: dict,
    payload: dict,
    timeout_s: float = 120.0,
    provider: str = "unknown",
    model: Optional[str] = None,
) -> dict:
    if HAS_HTTPX:
        try:
            _ensure_network_provider_registered(provider, url, timeout_s)
            pool = get_connection_pool()
            response = await pool.request(
                provider,
                "POST",
                url,
                headers=headers,
                json=payload,
                timeout=timeout_s,
            )
            return response.json()
        except Exception as exc:
            raise _normalize_transport_exception(provider, exc, model=model) from exc

    if HAS_AIOHTTP:
        timeout = aiohttp.ClientTimeout(total=timeout_s)
        last_exc: Optional[Exception] = None
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, headers=headers, json=payload) as response:
                        text = await response.text()
                        if response.status >= 400:
                            raise _orchestra_http_error(provider, response.status, text, model=model)
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError as exc:
                            raise ProvrException(OrchestraError(
                                code=ErrorCode.PROVR_RESPONSE_INVALID,
                                message=f"Risposta JSON non valida da {provider}",
                                details=str(exc),
                                provider=provider,
                                model=model,
                            )) from exc
            except Exception as exc:
                normalized = _normalize_transport_exception(provider, exc, model=model)
                last_exc = normalized
                if isinstance(normalized, ProvrException) and normalized.error.code == ErrorCode.PROVR_RATE_LIMITED and attempt < 2:
                    await asyncio.sleep(_retry_delay_seconds(attempt))
                    continue
                if isinstance(exc, aiohttp.ClientError) and attempt < 2:
                    await asyncio.sleep(_retry_delay_seconds(attempt))
                    continue
                raise normalized

        if last_exc:
            raise last_exc

    # Fallback sincrono via urllib
    def _sync_request() -> dict:
        last_exc: Optional[Exception] = None
        for attempt in range(3):
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
            )
            try:
                with urlopen(req, timeout=timeout_s) as resp:
                    body = resp.read().decode("utf-8")
                    return json.loads(body)
            except HTTPError as exc:
                body = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
                last_exc = _orchestra_http_error(provider, exc.code, body, model=model)
                if _retryable_http_status(exc.code) and attempt < 2:
                    time.sleep(_retry_delay_seconds(attempt))
                    continue
                raise last_exc
            except (URLError, OSError, json.JSONDecodeError) as exc:
                last_exc = _normalize_transport_exception(provider, exc, model=model)
                if attempt < 2:
                    time.sleep(_retry_delay_seconds(attempt))
                    continue
                raise last_exc

        if last_exc:
            raise last_exc

        raise NetworkException(OrchestraError(
            code=ErrorCode.SYSTEM_UNKNOWN,
            message=f"Errore sconosciuto verso {provider}",
            provider=provider,
            model=model,
        ))

    return await asyncio.to_thread(_sync_request)


async def _call_cloud_compatible_chat(
    provider: str,
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    response_format: dict | None = None,
    show_thinking: bool = False,
) -> dict:
    start = time.time()
    api_key = _resolve_cloud_api_key(provider)
    base_url = _cloud_base_url(provider)
    headers = _build_cloud_headers(provider, api_key)

    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    # G1: Structured output — JSON mode per provider OpenAI-compatible
    if response_format:
        payload["response_format"] = response_format

    data = await _http_post_json(
        f"{base_url}/chat/completions",
        headers=headers,
        payload=payload,
        timeout_s=180.0,
        provider=provider,
        model=model,
    )

    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content = msg.get("content", "")
    tokens_used = data.get("usage", {}).get("total_tokens", 0) or 0

    # G3: Cattura reasoning_content da OpenAI o-series models
    thinking = None
    if show_thinking:
        thinking = msg.get("reasoning_content") or msg.get("reasoning") or None

    result: dict = {
        "content": content,
        "provider": provider,
        "model": model,
        "tokens_used": tokens_used,
        "latency_ms": int((time.time() - start) * 1000),
    }
    if thinking:
        result["thinking"] = thinking
    return result


async def _call_cloud_claude(
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    response_format: dict | None = None,
    show_thinking: bool = False,
) -> dict:
    start = time.time()
    provider = "claude"
    api_key = _resolve_cloud_api_key(provider)
    base_url = _cloud_base_url(provider)
    headers = _build_cloud_headers(provider, api_key)

    system_text, anthropic_messages = _normalize_messages_for_claude(messages)
    payload: dict = {
        "model": model,
        "system": system_text,
        "messages": anthropic_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # G3: Extended thinking per Claude (richiede modelli compatibili)
    if show_thinking:
        payload["thinking"] = {"type": "enabled", "budget_tokens": 10000}
        # Anthropic richiede temperature=1 quando thinking è attivo
        payload["temperature"] = 1

    data = await _http_post_json(
        f"{base_url}/messages",
        headers=headers,
        payload=payload,
        timeout_s=180.0,
        provider=provider,
        model=model,
    )

    content_chunks = data.get("content", [])
    text_parts: list[str] = []
    thinking_parts: list[str] = []
    if isinstance(content_chunks, list):
        for chunk in content_chunks:
            if isinstance(chunk, dict):
                ctype = chunk.get("type", "")
                if ctype == "text":
                    text = chunk.get("text")
                    if isinstance(text, str):
                        text_parts.append(text)
                elif ctype == "thinking" and show_thinking:
                    # G3: Cattura thinking blocks da Claude extended thinking
                    thinking_text = chunk.get("thinking", "")
                    if isinstance(thinking_text, str) and thinking_text:
                        thinking_parts.append(thinking_text)

    usage = data.get("usage", {}) if isinstance(data.get("usage"), dict) else {}
    tokens_used = int(usage.get("input_tokens", 0) or 0) + int(usage.get("output_tokens", 0) or 0)

    result: dict = {
        "content": "".join(text_parts).strip(),
        "provider": provider,
        "model": model,
        "tokens_used": tokens_used,
        "latency_ms": int((time.time() - start) * 1000),
    }
    if thinking_parts:
        result["thinking"] = "\n\n".join(thinking_parts)
    return result


async def _call_cloud_perplexity(
    model: str,
    messages: list[dict],
) -> dict:
    start = time.time()
    provider = "perplexity"
    api_key = _resolve_cloud_api_key(provider)
    base_url = _cloud_base_url(provider)
    headers = _build_cloud_headers(provider, api_key)

    preset = model if model in PERPLEXITY_PRESETS else "pro-search"
    input_text = "\n\n".join(
        f"{(m.get('role') or 'user').upper()}: {m.get('content', '')}"
        for m in messages
    )

    payload = {
        "preset": preset,
        "input": input_text,
    }
    data = await _http_post_json(
        f"{base_url}/responses",
        headers=headers,
        payload=payload,
        timeout_s=180.0,
        provider=provider,
        model=model,
    )

    content = _extract_perplexity_output(data)
    tokens_used = data.get("usage", {}).get("total_tokens", 0) if isinstance(data.get("usage"), dict) else 0

    return {
        "content": content,
        "provider": provider,
        "model": data.get("model", preset),
        "tokens_used": tokens_used or 0,
        "latency_ms": int((time.time() - start) * 1000),
    }


async def call_cloud(
    messages: list[dict],
    provider: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: dict | None = None,
    show_thinking: bool = False,
) -> dict:
    """
    Chiamata cloud reale backend-s.
    Supporta provider OpenAI-compatible + endpoint specifici Anthropic/Perplexity.
    G1: response_format per structured output (JSON mode).
    G3: show_thinking per catturare reasoning/thinking blocks.
    G4: tracing OpenTelemetry per osservabilità.
    """
    resolved_model = _resolve_cloud_model(provider, model)
    _call_start = time.time()

    if provider == "claude":
        result = await _call_cloud_claude(
            model=resolved_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            show_thinking=show_thinking,
        )
    elif provider == "perplexity":
        result = await _call_cloud_perplexity(
            model=resolved_model,
            messages=messages,
        )
    else:
        result = await _call_cloud_compatible_chat(
            provider=provider,
            model=resolved_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            show_thinking=show_thinking,
        )

    # G4: registra span di tracing
    _call_ms = (time.time() - _call_start) * 1000
    with traced_span("call_cloud", {
        "ai.provider": provider,
        "ai.model": resolved_model,
        "ai.tokens_used": result.get("tokens_used", 0),
        "ai.latency_ms": round(_call_ms, 2),
    }):
        pass  # span registra solo attributi, la chiamata è già completata

    return result


# === OLLAMA DIRETTO ===


async def call_cloud_streaming(
    messages: list[dict],
    provider: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    """
    Streaming SSE per provider cloud (OpenAI-compatible + Claude).
    Genera token come stringhe, usabile dal /chat/stream endpoint.
    """
    resolved_model = _resolve_cloud_model(provider, model)
    api_key = _resolve_cloud_api_key(provider)
    base_url = _cloud_base_url(provider)
    headers = _build_cloud_headers(provider, api_key)

    if provider == "claude":
        system_text, anthropic_messages = _normalize_messages_for_claude(messages)
        payload = {
            "model": resolved_model,
            "system": system_text,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        url = f"{base_url}/messages"
    else:
        payload = {
            "model": resolved_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        url = f"{base_url}/chat/completions"

    cloud_timeout = float(_env_int("VIO_CLOUD_STREAM_TIMEOUT_SEC", 120))

    if not HAS_HTTPX:
        # Fallback: non-streaming
        result = await call_cloud(messages, provider, model, temperature, max_tokens)
        yield result.get("content", "")
        return

    try:
        async with httpx.AsyncClient(timeout=cloud_timeout, trust_env=False) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            return
                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        if provider == "claude":
                            # Anthropic: event con content_block_delta
                            ctype = chunk.get("type", "")
                            if ctype == "content_block_delta":
                                delta = chunk.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        yield text
                            elif ctype == "message_stop":
                                return
                        else:
                            # OpenAI-compatible: choices[0].delta.content
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
    except Exception as e:
        logger.warning(f"Cloud streaming fallito per {provider}: {e}")
        # Fallback: non-streaming
        result = await call_cloud(messages, provider, model, temperature, max_tokens)
        yield result.get("content", "")


async def call_ollama(
    messages: list[dict],
    model: str = "qwen2.5-coder:3b",
    host: str = "http://localhost:11434",
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> dict:
    """
    Chiama Ollama direttamente via HTTP.
    Restituisce dict con: content, provider, model, tokens_used, latency_ms
    """
    start = time.time()
    url = f"{host}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,  # Per ora non-streaming dal backend
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
    }

    ollama_timeout = float(_env_int("VIO_OLLAMA_TIMEOUT_SEC", 45))
    data = await _http_post_json(
        url,
        headers={"Content-Type": "application/json"},
        payload=payload,
        timeout_s=ollama_timeout,
        provider="ollama",
        model=model,
    )

    content = data.get("message", {}).get("content", "")
    tokens = (data.get("prompt_eval_count", 0) or 0) + (data.get("eval_count", 0) or 0)

    return {
        "content": content,
        "provider": "ollama",
        "model": model,
        "tokens_used": tokens,
        "latency_ms": int((time.time() - start) * 1000),
    }


async def call_ollama_streaming(
    messages: list[dict],
    model: str = "qwen2.5-coder:3b",
    host: str = "http://localhost:11434",
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> AsyncGenerator[str, None]:
    """
    Streaming Ollama — genera token uno alla volta.
    Usa per Server-Sent Events (SSE) dall'endpoint /chat/stream.
    """
    url = f"{host}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
    }

    streaming_timeout = float(_env_int("VIO_OLLAMA_STREAM_TIMEOUT_SEC", 90))

    if HAS_HTTPX:
        async with httpx.AsyncClient(timeout=streaming_timeout, trust_env=False) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            token = data.get("message", {}).get("content", "")
                            if token:
                                yield token
                            if data.get("done"):
                                return
                        except json.JSONDecodeError:
                            continue
    elif HAS_AIOHTTP:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=streaming_timeout)) as resp:
                resp.raise_for_status()
                async for line in resp.content:
                    decoded = line.decode("utf-8").strip()
                    if decoded:
                        try:
                            data = json.loads(decoded)
                            token = data.get("message", {}).get("content", "")
                            if token:
                                yield token
                            if data.get("done"):
                                return
                        except json.JSONDecodeError:
                            continue
    else:
        # Fallback: non-streaming
        result = await call_ollama(messages, model, host, temperature=temperature, max_tokens=max_tokens)
        yield result["content"]


# === OLLAMA MANAGEMENT ===

async def check_ollama_status(host: str = "http://localhost:11434") -> dict:
    """Verifica stato Ollama e modelli disponibili."""
    result = {"available": False, "models": [], "error": None}

    try:
        if HAS_HTTPX:
            async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
                # Check se Ollama è attivo
                resp = await client.get(f"{host}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                result["available"] = True
                result["models"] = [
                    {
                        "name": m["name"],
                        "size_gb": round(m.get("size", 0) / 1e9, 1),
                        "modified_at": m.get("modified_at", ""),
                        "family": m.get("details", {}).get("family", "unknown"),
                        "parameter_size": m.get("details", {}).get("parameter_size", "unknown"),
                        "quantization": m.get("details", {}).get("quantization_level", "unknown"),
                    }
                    for m in data.get("models", [])
                ]
        else:
            import urllib.request
            req = urllib.request.Request(f"{host}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                result["available"] = True
                result["models"] = [
                    {"name": m["name"], "size_gb": round(m.get("size", 0) / 1e9, 1)}
                    for m in data.get("models", [])
                ]
    except Exception as e:
        result["error"] = str(e)

    return result


# === ORCHESTRATOR PRINCIPALE ===

def _post_call_learn(messages: list[dict], result: dict, request_type: str) -> None:
    """
    Post-processing auto-apprendimento dopo ogni chiamata AI.
    Non blocca mai l'orchestrazione — tutto in try/except.
    """
    try:
        # 1. Auto-Learner: analizza conversazione ed estrai pattern
        learner = get_auto_learner()
        learner.analyze_conversation(messages)

        # 2. World Knowledge: ingerisci nuovi fatti dalla risposta
        wk = get_world_knowledge()
        # Aggiungi la risposta ai messaggi per l'ingestione
        full_msgs = messages + [{"role": "assistant", "content": result.get("content", "")}]
        wk.ingest_from_conversation(full_msgs)

        # 3. Self-Optimizer: registra metriche reali
        optimizer = get_self_optimizer()
        optimizer.record_result(
            provider=result.get("provider", "ollama"),
            model=result.get("model", ""),
            request_type=request_type,
            latency_ms=result.get("latency_ms", 0),
            tokens_used=result.get("tokens_used", 0),
            success=True,
        )

        # 4. Reasoning Engine: registra outcome
        reasoning = get_reasoning_engine()
        complexity = reasoning.assess_complexity(messages[-1].get("content", "") if messages else "")
        reasoning.record_outcome(
            request_type=request_type,
            complexity=complexity,
            user_satisfied=True,  # Default — sarà aggiornato se l'utente corregge
        )
    except Exception:
        pass  # Mai bloccare per errori di learning


def _validate_structured_output(content: str, response_format: dict | None) -> dict | None:
    """
    Valida che il contenuto sia JSON valido quando response_format.type == 'json_schema'.
    Ritorna il dict parsato se OK, None se non richiesto, raise se invalido.
    """
    if not response_format:
        return None
    fmt_type = response_format.get("type", "")
    if fmt_type not in ("json_object", "json_schema"):
        return None
    # Prova a parsare JSON dal contenuto (potrebbe avere markdown code blocks)
    text = content.strip()
    if text.startswith("```"):
        # Rimuovi code fence
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Structured output validation failed: %s", e)
        return None


async def orchestrate(
    messages: list[dict],
    mode: str = "local",
    provider: str = "ollama",
    model: Optional[str] = None,
    auto_routing: bool = True,
    ollama_host: str = "http://localhost:11434",
    ollama_model: str = "qwen2.5-coder:3b",
    temperature: float = 0.7,
    max_tokens: int = 512,
    cross_check: bool = False,
    protocollo_100x: bool = True,
    response_format: dict | None = None,
    show_thinking: bool = False,
) -> dict:
    """
    Funzione orchestratore principale.
    Supporta sia locale (Ollama) sia cloud provider reali backend-s.
    G1: response_format per structured JSON output.
    G3: show_thinking per esporre reasoning/thinking blocks.
    """
    last_msg = messages[-1]["content"] if messages else ""
    t0 = time.perf_counter()

    # ✈️  JetEngine™: cache semantica ultra-veloce + routing intelligente
    jet = get_jet_engine()
    jet_decision = jet.dec(
        message=last_msg,
        model=model or "auto",
        runtime_mode=mode,
        explicit_provr=provider if provider != "ollama" or mode != "local" else None,
        history_len=len(messages),
    )

    # TurboCache hit → risposta istantanea (<2ms)
    if jet_decision.cache_hit and jet_decision.cached_resp:
        cached = jet_decision.cached_resp
        latency_ms = (time.perf_counter() - t0) * 1000
        logger.info("JetEngine cache_hit intent=%s latency=%.1fms", jet_decision.profile.intent, latency_ms)
        cached["_diagnostic"] = {
            "cache_hit": True, "latency_ms": round(latency_ms, 1),
            "intent": jet_decision.profile.intent, "complexity": jet_decision.profile.score,
        }
        return cached

    # 🧬 Knowledge Taxonomy: configurazione ottimale per dominio
    try:
        tax_config = get_optimal_config(last_msg)
        tax_provider = tax_config.get("provider")
        tax_temperature = tax_config.get("temperature")
        tax_max_tokens = tax_config.get("max_tokens")
        tax_system_frag = tax_config.get("system_fragment", "")
    except Exception:
        tax_provider = None
        tax_temperature = None
        tax_max_tokens = None
        tax_system_frag = ""

    # Routing intelligente — classifica PRIMA di costruire il prompt
    request_type = classify_request(last_msg) if auto_routing else "conversation"
    effective_temperature, effective_max_tokens, prefer_fast_model = _effective_generation_params(
        request_type=request_type,
        last_msg=last_msg,
        requested_temperature=tax_temperature if tax_temperature is not None else temperature,
        requested_max_tokens=tax_max_tokens if tax_max_tokens is not None else max_tokens,
    )

    force_local = _force_local_orchestration(mode)
    if force_local:
        effective_provr = "ollama"
    elif jet_decision.routing.provider != "cache" and auto_routing:
        # JetEngine routing ha priorità (local-first / parallel-sprint)
        effective_provr = jet_decision.routing.provider
    else:
        effective_provr = route_to_provr(request_type, mode) if auto_routing else provider

    # Taxonomy override: se tax consiglia provider diverso e non siamo forzati
    if tax_provider and not force_local and auto_routing and effective_provr != "ollama":
        effective_provr = tax_provider

    # Inietta system prompt SPECIALIZZATO per tipo di richiesta
    has_system = any(m.get("role") == "system" for m in messages)
    if not has_system:
        # Turbo locale: prompt compatto per ridurre token overhead e first-token latency.
        if force_local or _speed_mode_enabled():
            system_prompt = build_local_system_prompt(request_type, protocollo_100x=protocollo_100x)
        else:
            system_prompt = build_system_prompt(request_type, protocollo_100x=protocollo_100x)

        # === AUTO-LEARNING: arricchisci prompt con conoscenza appresa ===
        try:
            learner = get_auto_learner()
            system_prompt = learner.enhance_prompt(last_msg, system_prompt, request_type)
        except Exception:
            pass  # Non bloccare mai l'orchestrazione per errori di learning

        # === WORLD KNOWLEDGE: inietta contesto aggiornato ===
        try:
            wk = get_world_knowledge()
            wk_context = wk.build_context_injection(last_msg, request_type)
            if wk_context:
                system_prompt += wk_context
        except Exception:
            pass

        # === REASONING ENGINE: guida strutturata per query complesse ===
        try:
            reasoning = get_reasoning_engine()
            reasoning_ctx = reasoning.build_reasoning_context(last_msg, request_type)
            if reasoning_ctx:
                system_prompt += reasoning_ctx
        except Exception:
            pass

        # === KNOWLEDGE TAXONOMY: frammento di dominio specializzato ===
        if tax_system_frag:
            system_prompt += f"\n\n{tax_system_frag}"

        messages = [{"role": "system", "content": system_prompt}] + messages

    # === SELF-OPTIMIZER: parametri auto-tuned ===
    try:
        optimizer = get_self_optimizer()
        opt_params = optimizer.get_optimal_params(effective_provr, model or "", request_type)
        if opt_params.get("provr_quality", 0) > 0.3:
            effective_temperature = opt_params.get("temperature", effective_temperature)
            effective_max_tokens = max(effective_max_tokens, opt_params.get("max_tokens", effective_max_tokens))
    except Exception:
        pass

    # In modalità locale, usa sempre Ollama
    if mode == "local" or effective_provr == "ollama" or force_local:
        candidate_models = _local_model_candidates(
            request_type=request_type,
            explicit_model=model,
            default_model=ollama_model or "llama3.2:3b",
            prefer_fast=prefer_fast_model,
        )
        if not candidate_models:
            candidate_models = ["llama3.2:3b"]

        print(
            f"[Orchestra] Tipo: {request_type} | Profilo: {_execution_profile()} | "
            f"No-Hybrid: {force_local} | Candidati locali: {candidate_models}"
        )

        last_error: Optional[Exception] = None
        for idx, local_model in enumerate(candidate_models):
            try:
                if idx > 0:
                    print(f"[Orchestra] Fallback locale -> {local_model}")

                result = await call_ollama(
                    messages,
                    local_model,
                    ollama_host,
                    temperature=effective_temperature,
                    max_tokens=effective_max_tokens,
                )
                result["request_type"] = request_type
                result["execution_profile"] = _execution_profile()
                result["forced_local"] = force_local

                # ✈️ JetEngine: salva in TurboCache
                jet.cache_store(last_msg, local_model, result)

                # 📊 Diagnostic
                latency_ms = (time.perf_counter() - t0) * 1000
                result["_diagnostic"] = {
                    "cache_hit": False,
                    "latency_ms": round(latency_ms, 1),
                    "intent": jet_decision.profile.intent,
                    "complexity": jet_decision.profile.score,
                    "jet_routing": jet_decision.routing.reason,
                    "provider": "ollama",
                    "model": local_model,
                    "fallback_idx": idx,
                }

                # === POST-CALL: Auto-learning + Self-optimization ===
                _post_call_learn(messages, result, request_type)

                return result
            except Exception as e:
                last_error = e
                continue

        raise Exception(
            f"Ollama non raggiungibile o modelli locali indisponibili. Ultimo errore: {last_error}\n"
            "Verifica che Ollama sia attivo con: ollama serve"
        )

    # Cloud mode reale backend-s
    print(f"[Orchestra] Tipo: {request_type} | Cloud provider: {effective_provr}")

    try:
        result = await call_cloud(
            messages=messages,
            provider=effective_provr,
            model=model,
            temperature=effective_temperature,
            max_tokens=effective_max_tokens,
            response_format=response_format,
            show_thinking=show_thinking,
        )
        result["request_type"] = request_type
        result["execution_profile"] = _execution_profile()
        result["forced_local"] = force_local

        # G1: Validazione structured output post-risposta
        if response_format:
            parsed = _validate_structured_output(result.get("content", ""), response_format)
            if parsed is not None:
                result["structured_output"] = parsed

        # ✈️ JetEngine: salva in TurboCache
        jet.cache_store(last_msg, model or effective_provr, result)

        # 📊 Diagnostic
        latency_ms = (time.perf_counter() - t0) * 1000
        result["_diagnostic"] = {
            "cache_hit": False,
            "latency_ms": round(latency_ms, 1),
            "intent": jet_decision.profile.intent,
            "complexity": jet_decision.profile.score,
            "jet_routing": jet_decision.routing.reason,
            "provider": effective_provr,
            "model": model,
        }

        # === POST-CALL: Auto-learning + Self-optimization ===
        _post_call_learn(messages, result, request_type)

        return result
    except Exception as e:
        routing_cfg = REQUEST_TYPE_ROUTING.get(request_type, {})
        fallback_provr = routing_cfg.get("cloud_fallback")

        if fallback_provr and fallback_provr != effective_provr:
            try:
                print(f"[Orchestra] Cloud fallback: {effective_provr} -> {fallback_provr}")
                result = await call_cloud(
                    messages=messages,
                    provider=fallback_provr,
                    model=None,
                    temperature=effective_temperature,
                    max_tokens=effective_max_tokens,
                    response_format=response_format,
                    show_thinking=show_thinking,
                )
                result["request_type"] = request_type
                result["fallback_from"] = effective_provr
                result["execution_profile"] = _execution_profile()
                result["forced_local"] = force_local

                # ✈️ JetEngine: salva in TurboCache anche fallback
                jet.cache_store(last_msg, fallback_provr, result)

                # 📊 Diagnostic
                latency_ms = (time.perf_counter() - t0) * 1000
                result["_diagnostic"] = {
                    "cache_hit": False,
                    "latency_ms": round(latency_ms, 1),
                    "intent": jet_decision.profile.intent,
                    "complexity": jet_decision.profile.score,
                    "jet_routing": jet_decision.routing.reason,
                    "provider": fallback_provr,
                    "fallback_from": effective_provr,
                }

                return result
            except Exception as fallback_error:
                raise Exception(
                    f"Cloud provider primario '{effective_provr}' fallito: {e}. "
                    f"Fallback '{fallback_provr}' fallito: {fallback_error}"
                )

        raise Exception(
            f"Cloud provider '{effective_provr}' fallito: {e}"
        )
