# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA - Pydantic Schemas
Definizione modelli dati per API e validazione.
"""

from typing import Optional, Literal, List
from pydantic import BaseModel, Field
from datetime import datetime


# === Multimodal / Vision ===

class ImageAttachment(BaseModel):
    """Immagine allegata a un messaggio (base64 data URL o URL remota)."""
    name: str
    mime_type: str = "image/png"
    data_url: Optional[str] = None   # "data:image/png;base64,..."
    url: Optional[str] = None         # URL remota


# === Request Models ===

class StructuredOutputFormat(BaseModel):
    """Formato output strutturato (JSON mode)."""
    type: Literal["json_object", "json_schema"] = "json_object"
    json_schema: Optional[dict] = None  # JSON Schema da rispettare (solo con type=json_schema)


class ChatRequest(BaseModel):
    """Richiesta chat dall'utente."""
    message: str = Field(..., min_length=1, max_length=50000)
    conversation_id: Optional[str] = None
    mode: Literal["cloud", "local"] = "local"
    provider: Optional[str] = Field(None, max_length=64)
    model: Optional[str] = Field(None, max_length=128)
    enable_cross_check: bool = False
    enable_rag: bool = True
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(512, ge=1, le=128000)
    system_prompt: Optional[str] = Field(None, max_length=12000)
    images: Optional[List[ImageAttachment]] = None  # Vision / multimodal
    agent_mode: bool = False  # OpenClaw agent: multi-step tool calling
    enable_protocollo_100x: bool = True  # Protocollo di Aderenza Totale 100x
    response_format: Optional[StructuredOutputFormat] = None  # G1: Structured output (JSON mode)
    show_thinking: bool = False  # G3: Mostra reasoning/thinking blocks dell'AI


class ClassifyRequest(BaseModel):
    """Richiesta classificazione tipo di query."""
    message: str = Field(..., min_length=1)


class RAGAddRequest(BaseModel):
    """Richiesta aggiunta fonte certificata."""
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=10)
    source_type: Literal["academic", "library", "official", "manual"] = "official"
    url: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    reliability_score: float = Field(1.0, ge=0.0, le=1.0)


class RAGSearchRequest(BaseModel):
    """Richiesta ricerca RAG."""
    query: str = Field(..., min_length=1)
    n_results: int = Field(5, ge=1, le=20)
    min_score: float = Field(0.7, ge=0.0, le=1.0)


class APIKeyUpdate(BaseModel):
    """Aggiornamento chiave API."""
    provider: str
    api_key: str = Field(..., min_length=5)


class ProvrConfig(BaseModel):
    """Configurazione provider AI."""
    provider: str
    enabled: bool = True
    model: Optional[str] = None
    priority: int = Field(1, ge=1, le=10)
    max_tokens: int = 512
    temperature: float = 0.7


# === Response Models ===

class ChatResponse(BaseModel):
    """Risposta chat dalla AI."""
    content: str
    provider: str
    model: str
    tokens_used: int = 0
    latency_ms: int = 0
    request_type: Optional[str] = None
    cross_check: Optional[dict] = None
    rag_verification: Optional[dict] = None
    thinking: Optional[str] = None  # G3: Reasoning/thinking visibile dall'AI
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ClassifyResponse(BaseModel):
    """Risposta classificazione."""
    request_type: str
    suggested_provr: str
    confidence: float


class HealthResponse(BaseModel):
    """Stato di salute del sistema."""
    status: str = "ok"
    version: str = "0.9.0"
    providers: dict = {}
    rag_stats: dict = {}
    uptime_seconds: float = 0.0


class ProvrStatus(BaseModel):
    """Stato di un provider AI."""
    name: str
    available: bool
    model: str
    mode: Literal["cloud", "local"]
    latency_ms: Optional[int] = None


class ErrorResponse(BaseModel):
    """Risposta errore."""
    error: str
    detail: Optional[str] = None
    code: int = 500
