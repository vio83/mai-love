# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA — OpenTelemetry Tracing (G4)

Tracing distribuito per l'osservabilità di ogni chiamata AI:
  - Span per ogni request /chat, /chat/stream
  - Span figlio per orchestrate(), call_cloud(), call_ollama()
  - Attributi: provider, model, tokens, latency, request_type
  - Export: OTLP (Jaeger/Zipkin/Grafana Tempo) o console

Configurazione via .env:
  OTEL_ENABLED=true
  OTEL_SERVICE_NAME=vio83-ai-orchestra
  OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
  OTEL_TRACES_EXPORTER=otlp  (oppure: console, none)

Se opentelemetry non è installato, tutto funziona in modalità noop
(zero overhead, nessun errore).
"""
from __future__ import annotations

import os
import logging
import time
from contextlib import contextmanager
from typing import Any, Optional

logger = logging.getLogger("vio83.tracing")

# ─── Graceful import ──────────────────────────────────────────────────
_OTEL_AVAILABLE = False
_tracer = None

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import StatusCode
    _OTEL_AVAILABLE = True
except ImportError:
    trace = None  # type: ignore
    StatusCode = None  # type: ignore


def init_tracing() -> bool:
    """
    Inizializza OpenTelemetry tracing.
    Ritorna True se attivato, False se disabilitato o non disponibile.

    Chiama questa funzione nel lifespan del server (una volta sola).
    """
    global _tracer

    enabled = os.environ.get("OTEL_ENABLED", "false").lower() in ("true", "1", "yes")
    if not enabled:
        logger.info("[Tracing] OTEL_ENABLED=false — tracing disabilitato")
        return False

    if not _OTEL_AVAILABLE:
        logger.warning(
            "[Tracing] OTEL_ENABLED=true ma opentelemetry non installato. "
            "Installa con: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp"
        )
        return False

    service_name = os.environ.get("OTEL_SERVICE_NAME", "vio83-ai-orchestra")
    exporter_type = os.environ.get("OTEL_TRACES_EXPORTER", "otlp").lower()

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if exporter_type == "console":
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    elif exporter_type == "otlp":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        except ImportError:
            logger.warning("[Tracing] OTLP exporter non installato, fallback a console")
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    elif exporter_type == "none":
        pass  # Noop — utile per test
    else:
        logger.warning(f"[Tracing] Exporter sconosciuto: {exporter_type}, usando console")
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("vio83.orchestra", "0.9.0")

    logger.info(f"[Tracing] OpenTelemetry attivo — service={service_name}, exporter={exporter_type}")
    return True


def get_tracer():
    """Ritorna il tracer OTel, o None se non inizializzato."""
    return _tracer


@contextmanager
def traced_span(
    name: str,
    attributes: Optional[dict[str, Any]] = None,
):
    """
    Context manager per creare uno span di tracing.
    Se OTel non è attivo, è un noop con zero overhead.

    Uso:
        with traced_span("orchestrate", {"provider": "claude", "model": "sonnet"}):
            result = await orchestrate(...)
    """
    if _tracer is None:
        yield None
        return

    with _tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                if v is not None:
                    span.set_attribute(k, str(v) if not isinstance(v, (int, float, bool)) else v)
        start = time.perf_counter()
        try:
            yield span
        except Exception as exc:
            if StatusCode is not None:
                span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            span.set_attribute("duration_ms", round(elapsed_ms, 2))


def record_ai_call(
    span,
    *,
    provider: str = "",
    model: str = "",
    tokens_used: int = 0,
    latency_ms: float = 0,
    request_type: str = "",
    success: bool = True,
    error: str = "",
):
    """
    Registra attributi standard di una chiamata AI sullo span attivo.
    Sicuro da chiamare anche con span=None (noop).
    """
    if span is None:
        return
    span.set_attribute("ai.provider", provider)
    span.set_attribute("ai.model", model)
    span.set_attribute("ai.tokens_used", tokens_used)
    span.set_attribute("ai.latency_ms", round(latency_ms, 2))
    span.set_attribute("ai.request_type", request_type)
    span.set_attribute("ai.success", success)
    if error:
        span.set_attribute("ai.error", error[:500])


def tracing_stats() -> dict:
    """Ritorna lo stato del tracing per l'endpoint /health."""
    return {
        "otel_available": _OTEL_AVAILABLE,
        "otel_enabled": os.environ.get("OTEL_ENABLED", "false").lower() in ("true", "1", "yes"),
        "tracer_active": _tracer is not None,
        "service_name": os.environ.get("OTEL_SERVICE_NAME", "vio83-ai-orchestra"),
        "exporter": os.environ.get("OTEL_TRACES_EXPORTER", "otlp"),
    }
