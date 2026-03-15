# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA - FastAPI Server v2
Server principale con:
- Chat (non-streaming + SSE streaming)
- Conversazioni persistenti (SQLite)
- Metriche e analytics
- Ollama management
- Health check completo

NON dipende da LiteLLM — usa direct_router per chiamate Ollama.
"""

import os
import time
import json
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from backend.models.schemas import (
    ChatRequest, ChatResponse, ClassifyRequest, ClassifyResponse,
    HealthResponse, RAGAddRequest, RAGSearchRequest, ErrorResponse
)
from backend.config.providers import (
    CLOUD_PROVIDERS, LOCAL_PROVIDERS, FREE_CLOUD_PROVIDERS,
    ALL_CLOUD_PROVIDERS, get_available_cloud_providers,
    get_free_cloud_providers, get_all_providers_ordered,
)
from backend.database.db import (
    init_database, create_conversation, list_conversations,
    get_conversation, update_conversation_title, delete_conversation,
    archive_conversation, add_message, log_metric, get_metrics_summary,
    auto_title_from_message, get_setting, set_setting, get_all_settings,
)
from backend.orchestrator.direct_router import (
    classify_request, orchestrate, call_ollama_streaming,
    check_ollama_status,
)

# RAG è disabilitato per compatibilità Python 3.14
RAG_AVAILABLE = False
# try:
#     from backend.rag.engine import get_rag_engine, RAGSource
#     RAG_AVAILABLE = True
# except Exception as e:
#     print(f"⚠️  RAG Engine legacy non disponibile: {e}")

# Knowledge Base v2 — sempre disponibile (fallback a SQLite FTS5)
KB_AVAILABLE = False
# try:
#     from backend.rag.knowledge_base import get_knowledge_base, KnowledgeBase
#     KB_AVAILABLE = True
# except Exception as e:
#     print(f"⚠️  Knowledge Base non disponibile: {e}")

load_dotenv()
START_TIME = time.time()

# === CORE INFRASTRUCTURE ===
from backend.core.cache import get_cache, CacheEngine
from backend.core.network import get_connection_pool, ConnectionPoolManager
from backend.core.parallel import TaskPool, ParallelQueryEngine
from backend.core.errors import get_error_handler, ErrorHandler, OrchestraException
from backend.core.security import get_vault, EnvironmentValidator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializzazione e shutdown del server."""
    print("🎵 VIO 83 AI ORCHESTRA — Server v2 avviato")
    print("🔧 Inizializzazione Core Infrastructure...")

    # Inizializza database
    init_database()

    # === SECURITY: Validazione ambiente ===
    validator = EnvironmentValidator()
    env_check = validator.validate()
    if env_check["errors"]:
        for err in env_check["errors"]:
            print(f"  ❌ {err}")
    for warn in env_check["warnings"]:
        print(f"  ⚠️  {warn}")

    # === SECURITY: API Key Vault ===
    vault = get_vault()
    print(f"🔐 API Keys: {vault.stats['valid_keys']}/{vault.stats['total_keys']} valide "
          f"→ Provider: {vault.available_providers or 'solo locale'}")

    # === CACHE: Multi-layer cache ===
    cache = get_cache()
    expired = cache.cleanup()
    print(f"💾 Cache Engine: L1 memory + L2 disk | Pulizia: {expired} entry scadute")

    # === NETWORK: Connection Pool + Circuit Breakers ===
    pool = get_connection_pool()
    pool.register_provider("ollama", base_url="http://localhost:11434", timeout=120.0, rate_limit=100)
    for provider_name in vault.available_providers:
        pool.register_provider(provider_name, timeout=60.0, rate_limit=30)
    print(f"🌐 Network Pool: {pool.stats['total_pools']} provider registrati")

    # === ERROR HANDLER ===
    error_handler = get_error_handler()
    print(f"🛡️  Error Handler: attivo")

    # Knowledge Base v2 (sempre disponibile — SQLite FTS5 fallback)
    if KB_AVAILABLE:
        try:
            kb = get_knowledge_base()
            stats = kb.get_stats()
            print(f"📚 Knowledge Base v2: {stats['fts_chunks']} chunk FTS, "
                  f"{stats['chromadb_chunks']} chunk ChromaDB, "
                  f"embedding: {stats['embedding_mode']}")
        except Exception as e:
            print(f"⚠️  Knowledge Base init fallita: {e}")
    else:
        print("📚 Knowledge Base: non disponibile")

    # RAG legacy
    if RAG_AVAILABLE:
        try:
            rag = get_rag_engine()
            rag.initialize()
            print(f"📚 RAG Legacy: {rag.get_stats()['total_documents']} documenti")
        except Exception as e:
            print(f"⚠️  RAG init fallita: {e}")
    else:
        print("📚 RAG Legacy: disabilitato")

    # Check Ollama
    ollama_status = await check_ollama_status()
    if ollama_status["available"]:
        models = [m["name"] for m in ollama_status["models"]]
        print(f"🤖 Ollama: attivo — {len(models)} modelli: {models}")
    else:
        print(f"⚠️  Ollama: non raggiungibile ({ollama_status.get('error', 'unknown')})")

    free_cloud = get_free_cloud_providers()
    if free_cloud:
        print(f"🆓 Provider cloud gratuiti: {list(free_cloud.keys())}")
    available = get_available_cloud_providers()
    paid_only = {k: v for k, v in available.items() if k not in free_cloud}
    if paid_only:
        print(f"☁️  Provider cloud a pagamento: {list(paid_only.keys())}")
    if not available:
        print("☁️  Provider cloud: nessuno (configura .env)")

    yield

    # === SHUTDOWN ===
    print("🎵 VIO 83 AI ORCHESTRA — Shutdown in corso...")
    pool = get_connection_pool()
    await pool.close_all()
    cache = get_cache()
    cache.cleanup()
    print("🎵 VIO 83 AI ORCHESTRA — Server arrestato")


app = FastAPI(
    title="VIO 83 AI ORCHESTRA",
    description="Multi-provider AI orchestration platform — Local-first, privacy-first",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:1420",
        "tauri://localhost",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Stato di salute completo del sistema."""
    available = get_available_cloud_providers()
    ollama = await check_ollama_status()

    providers = {}
    for key in ALL_CLOUD_PROVIDERS:
        providers[key] = {
            "available": key in available,
            "mode": "cloud",
            "name": ALL_CLOUD_PROVIDERS[key]["name"],
            "cost": ALL_CLOUD_PROVIDERS[key].get("cost", "paid"),
        }
    providers["ollama"] = {
        "available": ollama["available"],
        "mode": "local",
        "name": "Ollama (Locale)",
        "models": ollama.get("models", []),
    }

    rag_stats = {"total_documents": 0, "status": "disabled"}
    if RAG_AVAILABLE:
        try:
            rag = get_rag_engine()
            rag_stats = rag.get_stats()
        except Exception:
            pass

    return HealthResponse(
        status="ok",
        version="0.2.0",
        providers=providers,
        rag_stats=rag_stats,
        uptime_seconds=round(time.time() - START_TIME, 1),
    )


# ═══════════════════════════════════════════════
# CHAT — Non-streaming
# ═══════════════════════════════════════════════

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat principale — instrada la richiesta al provider migliore."""
    try:
        messages = [{"role": "user", "content": request.message}]

        # Se c'è una conversazione, recupera il contesto
        if request.conversation_id:
            conv = get_conversation(request.conversation_id)
            if conv and conv.get("messages"):
                messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in conv["messages"]
                ]
                messages.append({"role": "user", "content": request.message})

        # System prompt
        if request.system_prompt:
            messages.insert(0, {"role": "system", "content": request.system_prompt})

        # Orchestratore
        result = await orchestrate(
            messages=messages,
            mode=request.mode,
            provider=request.provider or "ollama",
            ollama_model=request.model or "qwen2.5-coder:3b",
            auto_routing=True,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Salva nel database
        conv_id = request.conversation_id
        if not conv_id:
            title = auto_title_from_message(request.message)
            conv_data = create_conversation(title=title, mode=request.mode)
            conv_id = conv_data["id"]

        add_message(conv_id, "user", request.message)
        add_message(conv_id, "assistant", result["content"],
                    provider=result["provider"], model=result["model"],
                    tokens_used=result.get("tokens_used", 0),
                    latency_ms=result.get("latency_ms", 0))

        # Log metrica
        log_metric(
            provider=result["provider"], model=result["model"],
            request_type=result.get("request_type"),
            tokens_used=result.get("tokens_used", 0),
            latency_ms=result.get("latency_ms", 0),
        )

        return ChatResponse(
            content=result["content"],
            provider=result["provider"],
            model=result["model"],
            tokens_used=result.get("tokens_used", 0),
            latency_ms=result.get("latency_ms", 0),
            request_type=result.get("request_type"),
        )

    except Exception as e:
        log_metric(
            provider=request.provider or "ollama",
            model=request.model or "unknown",
            success=False, error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════
# CHAT — Streaming SSE
# ═══════════════════════════════════════════════

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Chat con Server-Sent Events (SSE) — streaming token per token.
    Il frontend riceve ogni token in tempo reale.
    """
    messages = [{"role": "user", "content": request.message}]

    if request.conversation_id:
        conv = get_conversation(request.conversation_id)
        if conv and conv.get("messages"):
            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in conv["messages"]
            ]
            messages.append({"role": "user", "content": request.message})

    if request.system_prompt:
        messages.insert(0, {"role": "system", "content": request.system_prompt})

    # Inietta system prompt SPECIALIZZATO per tipo di richiesta
    from backend.orchestrator.direct_router import classify_request as _classify
    from backend.orchestrator.system_prompt import build_system_prompt
    has_system = any(m.get("role") == "system" for m in messages)
    if not has_system:
        req_type = _classify(request.message)
        system_prompt = build_system_prompt(req_type)

        # === RAG CONTEXT INJECTION ===
        # Cerca nella Knowledge Base e inietta fonti certificate nel contesto
        if KB_AVAILABLE:
            try:
                kb = get_knowledge_base()
                rag_ctx = kb.build_rag_context(request.message, max_context_tokens=1500)
                if rag_ctx.get("has_context") and rag_ctx.get("context_text"):
                    system_prompt += (
                        f"\n\n=== FONTI CERTIFICATE DALLA KNOWLEDGE BASE ===\n"
                        f"Dominio: {rag_ctx['domain']} | Confidenza: {rag_ctx['confidence']}\n"
                        f"Usa queste fonti per supportare e verificare la tua risposta:\n\n"
                        f"{rag_ctx['context_text']}\n"
                        f"=== FINE FONTI ==="
                    )
            except Exception as e:
                print(f"[KB] Errore context injection: {e}")

        messages.insert(0, {"role": "system", "content": system_prompt})

    model = request.model or "llama3.2:3b"

    async def event_generator():
        full_content = ""
        start = time.time()
        try:
            async for token in call_ollama_streaming(
                messages=messages,
                model=model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                full_content += token
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

            latency = int((time.time() - start) * 1000)
            yield f"data: {json.dumps({'token': '', 'done': True, 'full_content': full_content, 'latency_ms': latency, 'model': model, 'provider': 'ollama'})}\n\n"

            # Salva nel database
            conv_id = request.conversation_id
            if not conv_id:
                title = auto_title_from_message(request.message)
                conv_data = create_conversation(title=title, mode=request.mode)
                conv_id = conv_data["id"]

            add_message(conv_id, "user", request.message)
            add_message(conv_id, "assistant", full_content,
                        provider="ollama", model=model,
                        latency_ms=latency)
            log_metric("ollama", model, tokens_used=0, latency_ms=latency)

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ═══════════════════════════════════════════════
# CONVERSAZIONI
# ═══════════════════════════════════════════════

@app.get("/conversations")
async def api_list_conversations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    include_archived: bool = False,
):
    """Lista conversazioni."""
    return list_conversations(limit=limit, offset=offset, include_archived=include_archived)


@app.post("/conversations")
async def api_create_conversation(title: str = "Nuova conversazione", mode: str = "local"):
    """Crea una nuova conversazione."""
    return create_conversation(title=title, mode=mode)


@app.get("/conversations/{conv_id}")
async def api_get_conversation(conv_id: str):
    """Ottieni conversazione con messaggi."""
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return conv


@app.put("/conversations/{conv_id}/title")
async def api_update_title(conv_id: str, title: str):
    """Aggiorna titolo conversazione."""
    update_conversation_title(conv_id, title)
    return {"status": "ok"}


@app.delete("/conversations/{conv_id}")
async def api_delete_conversation(conv_id: str):
    """Elimina conversazione."""
    delete_conversation(conv_id)
    return {"status": "deleted"}


@app.post("/conversations/{conv_id}/archive")
async def api_archive_conversation(conv_id: str):
    """Archivia conversazione."""
    archive_conversation(conv_id)
    return {"status": "archived"}


# ═══════════════════════════════════════════════
# CLASSIFY
# ═══════════════════════════════════════════════

@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """Classifica il tipo di richiesta per il routing intelligente."""
    req_type = classify_request(request.message)
    from backend.config.providers import REQUEST_TYPE_ROUTING
    routing = REQUEST_TYPE_ROUTING.get(req_type, {})

    return ClassifyResponse(
        request_type=req_type,
        suggested_provider=routing.get("cloud_primary", "ollama"),
        confidence=0.85,
    )


# ═══════════════════════════════════════════════
# OLLAMA MANAGEMENT
# ═══════════════════════════════════════════════

@app.get("/ollama/status")
async def api_ollama_status():
    """Stato Ollama e modelli disponibili."""
    return await check_ollama_status()


@app.get("/ollama/models")
async def api_ollama_models():
    """Lista modelli Ollama installati."""
    status = await check_ollama_status()
    if not status["available"]:
        raise HTTPException(status_code=503, detail="Ollama non raggiungibile")
    return {"models": status["models"]}


# ═══════════════════════════════════════════════
# PROVIDERS
# ═══════════════════════════════════════════════

@app.get("/providers")
async def list_providers():
    """Lista tutti i provider disponibili — 3 tier: locale, gratis, pagamento."""
    available = get_available_cloud_providers()
    free_available = get_free_cloud_providers()
    ollama = await check_ollama_status()

    return {
        "local": {
            "ollama": {
                "name": "Ollama (Locale)",
                "available": ollama["available"],
                "cost": "free",
                "default_model": LOCAL_PROVIDERS["ollama"]["default_model"],
                "models": ollama.get("models", []),
                "installed_models": [m["name"] for m in ollama.get("models", [])],
            }
        },
        "free_cloud": {
            key: {
                "name": FREE_CLOUD_PROVIDERS[key]["name"],
                "available": key in free_available,
                "cost": "free",
                "free_tier": FREE_CLOUD_PROVIDERS[key].get("free_tier", ""),
                "signup_url": FREE_CLOUD_PROVIDERS[key].get("signup_url", ""),
                "default_model": FREE_CLOUD_PROVIDERS[key]["default_model"],
                "models": list(FREE_CLOUD_PROVIDERS[key]["models"].keys()),
            }
            for key in FREE_CLOUD_PROVIDERS
        },
        "paid_cloud": {
            key: {
                "name": CLOUD_PROVIDERS[key]["name"],
                "available": key in available,
                "cost": CLOUD_PROVIDERS[key].get("cost", "paid"),
                "default_model": CLOUD_PROVIDERS[key]["default_model"],
                "models": list(CLOUD_PROVIDERS[key]["models"].keys()),
            }
            for key in CLOUD_PROVIDERS
        },
        "all_ordered": [
            {"id": p["id"], "name": p["name"], "tier": p["tier"],
             "available": p.get("available", True)}
            for p in get_all_providers_ordered()
        ],
    }


# ═══════════════════════════════════════════════
# METRICHE
# ═══════════════════════════════════════════════

@app.get("/metrics")
async def api_metrics(days: int = Query(30, ge=1, le=365)):
    """Metriche e analytics degli ultimi N giorni."""
    return get_metrics_summary(days=days)


# ═══════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════

@app.get("/settings")
async def api_get_settings():
    """Ottieni tutte le impostazioni."""
    return get_all_settings()


@app.put("/settings/{key}")
async def api_set_setting(key: str, value: str):
    """Aggiorna un'impostazione."""
    set_setting(key, value)
    return {"status": "ok", "key": key}


# ═══════════════════════════════════════════════
# RAG (opzionale)
# ═══════════════════════════════════════════════

@app.post("/rag/add")
async def rag_add_source(request: RAGAddRequest):
    """Aggiungi fonte certificata al database RAG."""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG Engine non disponibile")
    rag = get_rag_engine()
    source = RAGSource(
        title=request.title, content=request.content,
        source_type=request.source_type, url=request.url,
        author=request.author, year=request.year,
        reliability_score=request.reliability_score,
    )
    doc_id = rag.add_source(source)
    return {"doc_id": doc_id, "status": "added"}


@app.post("/rag/search")
async def rag_search(request: RAGSearchRequest):
    """Cerca nelle fonti certificate."""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG Engine non disponibile")
    rag = get_rag_engine()
    result = rag.search(request.query, n_results=request.n_results, min_score=request.min_score)
    return {
        "query": result.query, "matches": result.matches,
        "verified": result.verified, "confidence": result.confidence,
        "sources_used": result.sources_used,
    }


@app.get("/rag/stats")
async def rag_stats():
    """Statistiche database RAG."""
    if not RAG_AVAILABLE:
        return {"total_documents": 0, "status": "disabled", "reason": "ChromaDB non compatibile"}
    rag = get_rag_engine()
    return rag.get_stats()


# ═══════════════════════════════════════════════
# KNOWLEDGE BASE v2 — Biblioteca Digitale Completa
# ═══════════════════════════════════════════════

@app.get("/kb/stats")
async def kb_stats():
    """Statistiche Knowledge Base — biblioteca digitale."""
    if not KB_AVAILABLE:
        return {"status": "disabled", "reason": "Knowledge Base non inizializzata"}
    kb = get_knowledge_base()
    return kb.get_stats()


@app.post("/kb/ingest/text")
async def kb_ingest_text(
    text: str,
    title: str = "",
    author: str = "",
    source_type: str = "manual",
    reliability: float = 1.0,
):
    """Ingesci testo diretto nella knowledge base."""
    if not KB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Knowledge Base non disponibile")
    kb = get_knowledge_base()
    chunk_count = kb.ingest_text(
        text=text, title=title, author=author,
        source_type=source_type, reliability=reliability,
    )
    return {"status": "ok", "chunks_created": chunk_count, "title": title}


@app.post("/kb/ingest/file")
async def kb_ingest_file(
    filepath: str,
    source_type: str = "book",
    reliability: float = 1.0,
):
    """Ingesci un file nella knowledge base (PDF, DOCX, EPUB, TXT, HTML, JSON, CSV)."""
    if not KB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Knowledge Base non disponibile")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"File non trovato: {filepath}")
    kb = get_knowledge_base()
    doc = kb.ingest_file(filepath, source_type=source_type, reliability=reliability)
    return {
        "status": doc.status,
        "doc_id": doc.doc_id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "title": doc.title,
        "author": doc.author,
        "language": doc.language,
        "word_count": doc.word_count,
        "chunk_count": doc.chunk_count,
        "error": doc.error,
    }


@app.post("/kb/ingest/directory")
async def kb_ingest_directory(
    directory: str,
    recursive: bool = True,
    source_type: str = "book",
    reliability: float = 1.0,
):
    """Ingesci tutti i file da una directory nella knowledge base."""
    if not KB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Knowledge Base non disponibile")
    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"Directory non trovata: {directory}")
    kb = get_knowledge_base()
    docs = kb.ingest_directory(directory, recursive=recursive,
                                source_type=source_type, reliability=reliability)
    return {
        "status": "ok",
        "files_processed": len([d for d in docs if d.status == "success"]),
        "files_failed": len([d for d in docs if d.status == "error"]),
        "total_chunks": sum(d.chunk_count for d in docs),
        "total_words": sum(d.word_count for d in docs),
        "details": [
            {"filename": d.filename, "status": d.status,
             "chunks": d.chunk_count, "error": d.error}
            for d in docs
        ],
    }


@app.post("/kb/query")
async def kb_query(
    question: str,
    n_results: int = 10,
    min_reliability: float = 0.5,
    domain_filter: Optional[str] = None,
):
    """Cerca nella knowledge base con retrieval semantico + reranking."""
    if not KB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Knowledge Base non disponibile")
    kb = get_knowledge_base()
    results = kb.query(
        question=question, n_results=n_results,
        min_reliability=min_reliability, domain_filter=domain_filter,
    )
    return {"query": question, "results": results, "count": len(results)}


@app.post("/kb/context")
async def kb_build_context(
    question: str,
    max_context_tokens: int = 2000,
    n_results: int = 5,
):
    """Costruisci contesto RAG per una domanda (da iniettare nel prompt AI)."""
    if not KB_AVAILABLE:
        return {"context_text": "", "sources": [], "has_context": False}
    kb = get_knowledge_base()
    return kb.build_rag_context(
        question=question,
        max_context_tokens=max_context_tokens,
        n_results=n_results,
    )


# ═══════════════════════════════════════════════
# CORE INFRASTRUCTURE — Cache, Network, Security
# ═══════════════════════════════════════════════

@app.get("/core/cache/stats")
async def api_cache_stats():
    """Statistiche del multi-layer cache engine."""
    cache = get_cache()
    return cache.stats


@app.post("/core/cache/clear")
async def api_cache_clear():
    """Svuota tutta la cache."""
    cache = get_cache()
    cache.clear()
    return {"status": "ok", "message": "Cache svuotata"}


@app.post("/core/cache/cleanup")
async def api_cache_cleanup():
    """Rimuovi entry scadute dalla cache disco."""
    cache = get_cache()
    removed = cache.cleanup()
    return {"status": "ok", "expired_removed": removed}


@app.get("/core/network/stats")
async def api_network_stats():
    """Statistiche di rete: connection pool, circuit breaker, latenze."""
    pool = get_connection_pool()
    return pool.stats


@app.get("/core/network/health/{provider}")
async def api_provider_health(provider: str):
    """Health check specifico per un provider."""
    pool = get_connection_pool()
    return pool.get_provider_health(provider)


@app.get("/core/errors/stats")
async def api_error_stats():
    """Statistiche errori: conteggi, errori recenti, errori più comuni."""
    handler = get_error_handler()
    return handler.stats


@app.get("/core/security/stats")
async def api_security_stats():
    """Stato sicurezza: chiavi API, provider disponibili."""
    vault = get_vault()
    return vault.stats


@app.get("/core/security/validate")
async def api_validate_environment():
    """Validazione completa dell'ambiente di esecuzione."""
    validator = EnvironmentValidator()
    return validator.validate()


@app.get("/core/status")
async def api_core_status():
    """Status completo di tutta l'infrastruttura core."""
    cache = get_cache()
    pool = get_connection_pool()
    handler = get_error_handler()
    vault = get_vault()

    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "cache": cache.stats,
        "network": pool.stats,
        "errors": {
            "total": handler.stats["total_errors"],
            "most_common": handler.stats["most_common"],
        },
        "security": {
            "valid_keys": vault.stats["valid_keys"],
            "available_providers": vault.available_providers,
        },
    }


# ═══════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("LITELLM_PROXY_PORT", 4000))
    print(f"🎵 Avvio VIO 83 AI ORCHESTRA v2 su porta {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
