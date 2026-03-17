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

import os
import time
import json
import asyncio
from typing import Optional, AsyncGenerator
from urllib.request import Request, urlopen
from urllib.error import URLError

from backend.config.providers import (
    CLOUD_PROVIDERS,
    FREE_CLOUD_PROVIDERS,
    REQUEST_TYPE_ROUTING,
)

# Per chiamate async HTTP usiamo aiohttp se disponibile, altrimenti asyncio
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


# === SYSTEM PROMPT CERTIFICATO VIO 83 ===
# Importato dal modulo dedicato (versione completa con tutti i campi)

from backend.orchestrator.system_prompt import (
    VIO83_MASTER_PROMPT,
    SPECIALIZED_PROMPTS,
    build_system_prompt,
    build_local_system_prompt,
)

# Alias per retrocompatibilità (server.py lo importa come VIO83_SYSTEM_PROMPT)
VIO83_SYSTEM_PROMPT = VIO83_MASTER_PROMPT


# === CLASSIFICAZIONE RICHIESTE ===

KEYWORDS = {
    "code": ["codice", "code", "funzione", "function", "bug", "debug", "api",
             "database", "sql", "python", "javascript", "typescript", "react",
             "script", "algoritmo", "classe", "metodo", "array", "json",
             "html", "css", "endpoint", "backend", "frontend"],
    "legal": ["legge", "norma", "contratto", "compliance", "gdpr", "privacy",
              "tribunale", "sentenza", "clausola", "regolamento", "licenza", "diritto"],
    "medical": ["medicina", "clinico", "diagnosi", "terapia", "farmaco", "sintomo",
                "linea guida", "paziente", "epidemiologia", "oncologia", "cardiologia", "pubmed"],
    "writing": ["linkedin", "headline", "about", "copy", "newsletter", "ghostwrite",
                "articolo", "post", "caption", "seo", "landing page", "scrittura"],
    "research": ["ricerca", "paper", "citazioni", "fonti", "survey", "benchmark",
                 "state of the art", "deep research", "letteratura", "bibliografia"],
    "automation": ["workflow", "automazione", "agent", "agente", "tool", "mcp",
                   "n8n", "pipeline", "orchestrazione", "browser automation", "task runner"],
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

ALL_CLOUD_ROUTER_PROVIDERS = {
    **FREE_CLOUD_PROVIDERS,
    **CLOUD_PROVIDERS,
}

PERPLEXITY_PRESETS = {"pro-search", "deep-research"}


def classify_request(message: str) -> str:
    """Classifica il tipo di richiesta per il routing intelligente."""
    lower = message.lower()
    scores = {}
    for req_type, keywords in KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[req_type] = score
    if scores:
        return max(scores, key=scores.get)
    return "conversation"


def route_to_provider(request_type: str, mode: str = "cloud") -> str:
    """Determina il provider ottimale basato sul tipo di richiesta."""
    if mode == "local":
        return "ollama"
    return ROUTING_MAP.get(request_type, "claude")


def _resolve_cloud_provider_entry(provider: str) -> dict:
    entry = ALL_CLOUD_ROUTER_PROVIDERS.get(provider)
    if not entry:
        raise Exception(f"Provider cloud non supportato nel backend: {provider}")
    return entry


def _resolve_cloud_model(provider: str, requested_model: Optional[str] = None) -> str:
    entry = _resolve_cloud_provider_entry(provider)
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

    raise Exception(f"Nessun modello disponibile per provider {provider}")


def _resolve_cloud_api_key(provider: str) -> str:
    entry = _resolve_cloud_provider_entry(provider)
    env_key = entry.get("env_key")
    if not env_key:
        raise Exception(f"env_key mancante per provider {provider}")

    api_key = os.environ.get(env_key, "").strip()
    if not api_key:
        raise Exception(
            f"API key mancante per provider '{provider}'. Imposta {env_key} nel file .env"
        )
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
        raise Exception(f"Base URL non configurata per provider {provider}")
    return base_urls[provider]


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


async def _http_post_json(url: str, headers: dict, payload: dict, timeout_s: float = 120.0) -> dict:
    if HAS_HTTPX:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code >= 400:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            return response.json()

    if HAS_AIOHTTP:
        timeout = aiohttp.ClientTimeout(total=timeout_s)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                text = await response.text()
                if response.status >= 400:
                    raise Exception(f"HTTP {response.status}: {text}")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    raise Exception(f"Risposta JSON non valida da {url}")

    # Fallback sincrono via urllib
    def _sync_request() -> dict:
        req = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
        )
        with urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)

    return await asyncio.to_thread(_sync_request)


async def _call_cloud_compatible_chat(
    provider: str,
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
) -> dict:
    start = time.time()
    api_key = _resolve_cloud_api_key(provider)
    base_url = _cloud_base_url(provider)
    headers = _build_cloud_headers(provider, api_key)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    data = await _http_post_json(
        f"{base_url}/chat/completions",
        headers=headers,
        payload=payload,
        timeout_s=180.0,
    )

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    tokens_used = data.get("usage", {}).get("total_tokens", 0) or 0

    return {
        "content": content,
        "provider": provider,
        "model": model,
        "tokens_used": tokens_used,
        "latency_ms": int((time.time() - start) * 1000),
    }


async def _call_cloud_claude(
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
) -> dict:
    start = time.time()
    provider = "claude"
    api_key = _resolve_cloud_api_key(provider)
    base_url = _cloud_base_url(provider)
    headers = _build_cloud_headers(provider, api_key)

    system_text, anthropic_messages = _normalize_messages_for_claude(messages)
    payload = {
        "model": model,
        "system": system_text,
        "messages": anthropic_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    data = await _http_post_json(
        f"{base_url}/messages",
        headers=headers,
        payload=payload,
        timeout_s=180.0,
    )

    content_chunks = data.get("content", [])
    text_parts: list[str] = []
    if isinstance(content_chunks, list):
        for chunk in content_chunks:
            if isinstance(chunk, dict) and chunk.get("type") == "text":
                text = chunk.get("text")
                if isinstance(text, str):
                    text_parts.append(text)

    usage = data.get("usage", {}) if isinstance(data.get("usage"), dict) else {}
    tokens_used = int(usage.get("input_tokens", 0) or 0) + int(usage.get("output_tokens", 0) or 0)

    return {
        "content": "".join(text_parts).strip(),
        "provider": provider,
        "model": model,
        "tokens_used": tokens_used,
        "latency_ms": int((time.time() - start) * 1000),
    }


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
) -> dict:
    """
    Chiamata cloud reale backend-side.
    Supporta provider OpenAI-compatible + endpoint specifici Anthropic/Perplexity.
    """
    resolved_model = _resolve_cloud_model(provider, model)

    if provider == "claude":
        return await _call_cloud_claude(
            model=resolved_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "perplexity":
        return await _call_cloud_perplexity(
            model=resolved_model,
            messages=messages,
        )

    return await _call_cloud_compatible_chat(
        provider=provider,
        model=resolved_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# === OLLAMA DIRETTO ===

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

    if HAS_HTTPX:
        async with httpx.AsyncClient(timeout=ollama_timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    elif HAS_AIOHTTP:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=ollama_timeout)) as resp:
                resp.raise_for_status()
                data = await resp.json()
    else:
        # Fallback sincrono (non ideale ma funziona)
        import urllib.request
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=ollama_timeout) as resp:
            data = json.loads(resp.read())

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
        async with httpx.AsyncClient(timeout=streaming_timeout) as client:
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
            async with httpx.AsyncClient(timeout=5.0) as client:
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
) -> dict:
    """
    Funzione orchestratore principale.
    Supporta sia locale (Ollama) sia cloud provider reali backend-side.
    """
    last_msg = messages[-1]["content"] if messages else ""

    # Routing intelligente — classifica PRIMA di costruire il prompt
    request_type = classify_request(last_msg) if auto_routing else "conversation"
    effective_temperature, effective_max_tokens, prefer_fast_model = _effective_generation_params(
        request_type=request_type,
        last_msg=last_msg,
        requested_temperature=temperature,
        requested_max_tokens=max_tokens,
    )

    force_local = _force_local_orchestration(mode)
    if force_local:
        effective_provider = "ollama"
    else:
        effective_provider = route_to_provider(request_type, mode) if auto_routing else provider

    # Inietta system prompt SPECIALIZZATO per tipo di richiesta
    has_system = any(m.get("role") == "system" for m in messages)
    if not has_system:
        # Turbo locale: prompt compatto per ridurre token overhead e first-token latency.
        if force_local or _speed_mode_enabled():
            system_prompt = build_local_system_prompt(request_type)
        else:
            system_prompt = build_system_prompt(request_type)
        messages = [{"role": "system", "content": system_prompt}] + messages

    # In modalità locale, usa sempre Ollama
    if mode == "local" or effective_provider == "ollama" or force_local:
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
                return result
            except Exception as e:
                last_error = e
                continue

        raise Exception(
            f"Ollama non raggiungibile o modelli locali indisponibili. Ultimo errore: {last_error}\n"
            "Verifica che Ollama sia attivo con: ollama serve"
        )

    # Cloud mode reale backend-side
    print(f"[Orchestra] Tipo: {request_type} | Cloud provider: {effective_provider}")

    try:
        result = await call_cloud(
            messages=messages,
            provider=effective_provider,
            model=model,
            temperature=effective_temperature,
            max_tokens=effective_max_tokens,
        )
        result["request_type"] = request_type
        result["execution_profile"] = _execution_profile()
        result["forced_local"] = force_local
        return result
    except Exception as e:
        routing_cfg = REQUEST_TYPE_ROUTING.get(request_type, {})
        fallback_provider = routing_cfg.get("cloud_fallback")

        if fallback_provider and fallback_provider != effective_provider:
            try:
                print(f"[Orchestra] Cloud fallback: {effective_provider} -> {fallback_provider}")
                result = await call_cloud(
                    messages=messages,
                    provider=fallback_provider,
                    model=None,
                    temperature=effective_temperature,
                    max_tokens=effective_max_tokens,
                )
                result["request_type"] = request_type
                result["fallback_from"] = effective_provider
                result["execution_profile"] = _execution_profile()
                result["forced_local"] = force_local
                return result
            except Exception as fallback_error:
                raise Exception(
                    f"Cloud provider primario '{effective_provider}' fallito: {e}. "
                    f"Fallback '{fallback_provider}' fallito: {fallback_error}"
                )

        raise Exception(
            f"Cloud provider '{effective_provider}' fallito: {e}"
        )
