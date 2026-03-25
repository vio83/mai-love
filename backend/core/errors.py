# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA — Centralized Error Handling
Gestione errori robusta con:
- Eccezioni tipizzate per ogni dominio
- Error codes univoci per debugging
- Structured logging degli errori
- Fallback chain automatica
- Error recovery strategies
"""

import time
import logging
import traceback
from enum import Enum
from typing import Any, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("vio83.errors")


class ErrorCode(Enum):
    """Codici errore univoci per ogni tipo di problema."""
    # Provider errors (1xxx)
    PROVR_UNAVAILABLE = 1001
    PROVR_TIMEOUT = 1002
    PROVR_RATE_LIMITED = 1003
    PROVR_AUTH_FAILED = 1004
    PROVR_MODEL_NOT_FOUND = 1005
    PROVR_RESPONSE_INVALID = 1006

    # Network errors (2xxx)
    NETWORK_CONNECTION_FAILED = 2001
    NETWORK_DNS_FAILED = 2002
    NETWORK_SSL_ERROR = 2003
    NETWORK_CIRCUIT_OPEN = 2004

    # Database errors (3xxx)
    DB_CONNECTION_FAILED = 3001
    DB_QUERY_FAILED = 3002
    DB_INTEGRITY_ERROR = 3003
    DB_MIGRATION_FAILED = 3004

    # RAG/KB errors (4xxx)
    RAG_INGESTION_FAILED = 4001
    RAG_EMBEDDING_FAILED = 4002
    RAG_SEARCH_FAILED = 4003
    RAG_INDEX_CORRUPTED = 4004

    # Config/Security (5xxx)
    CONFIG_MISSING_KEY = 5001
    CONFIG_INVALID_VALUE = 5002
    SECURITY_KEY_EXPIRED = 5003
    SECURITY_KEY_INVALID = 5004

    # System (9xxx)
    SYSTEM_OUT_OF_MEMORY = 9001
    SYSTEM_DISK_FULL = 9002
    SYSTEM_UNKNOWN = 9999


@dataclass
class OrchestraError:
    """Errore strutturato con contesto completo."""
    code: ErrorCode
    message: str
    details: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    traceback_str: Optional[str] = None
    recoverable: bool = True
    suggestion: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "error_code": self.code.value,
            "error_name": self.code.name,
            "message": self.message,
            "details": self.details,
            "provider": self.provider,
            "model": self.model,
            "recoverable": self.recoverable,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp,
        }

    def log(self):
        """Logga l'errore con il livello appropriato."""
        if self.recoverable:
            logger.warning(f"[{self.code.name}] {self.message} | {self.details or ''}")
        else:
            logger.error(f"[{self.code.name}] {self.message} | {self.details or ''}")
            if self.traceback_str:
                logger.error(self.traceback_str)


# === ECCEZIONI TIPIZZATE ===

class OrchestraException(Exception):
    """Eccezione base per VIO 83 AI Orchestra."""
    def __init__(self, error: OrchestraError):
        self.error = error
        super().__init__(error.message)


class ProvrException(OrchestraException):
    """Errore da un provider AI."""


class NetworkException(OrchestraException):
    """Errore di rete."""


class DatabaseException(OrchestraException):
    """Errore database."""


class SecurityException(OrchestraException):
    """Errore di sicurezza."""


# === ERROR HANDLER CENTRALIZZATO ===

class ErrorHandler:
    """
    Gestore errori centralizzato con:
    - Logging strutturato
    - Error history per analytics
    - Automatic recovery suggestions
    - Fallback chain management
    """

    def __init__(self, max_history: int = 500):
        self._error_history: list[OrchestraError] = []
        self._max_history = max_history
        self._error_counts: dict[str, int] = {}

    def handle(self, exception: Exception, context: dict = None) -> OrchestraError:
        """Converte qualsiasi eccezione in un OrchestraError strutturato."""
        context = context or {}

        if isinstance(exception, OrchestraException):
            error = exception.error
        else:
            error = self._classify_exception(exception, context)

        error.traceback_str = traceback.format_exc()
        error.log()
        self._record_error(error)
        return error

    def _classify_exception(self, exc: Exception, context: dict) -> OrchestraError:
        """Classifica automaticamente un'eccezione generica."""
        exc_type = type(exc).__name__
        exc_msg = str(exc)

        # Timeout (check BEFORE connection errors since TimeoutError is subclass of OSError)
        if isinstance(exc, (TimeoutError,)) or "timeout" in exc_type.lower():
            return OrchestraError(
                code=ErrorCode.PROVR_TIMEOUT,
                message=f"Timeout: {context.get('provider', 'unknown')}",
                details=exc_msg,
                provider=context.get("provider"),
                suggestion="Prova con un modello più leggero o aumenta il timeout",
            )

        # Connection errors
        if isinstance(exc, (ConnectionError, OSError)):
            if "refused" in exc_msg.lower():
                return OrchestraError(
                    code=ErrorCode.NETWORK_CONNECTION_FAILED,
                    message=f"Connessione rifiutata: {context.get('provider', 'unknown')}",
                    details=exc_msg,
                    provider=context.get("provider"),
                    suggestion="Verifica che il servizio sia attivo e raggiungibile",
                )
            return OrchestraError(
                code=ErrorCode.NETWORK_CONNECTION_FAILED,
                message=f"Errore di rete: {exc_msg}",
                details=exc_msg,
                provider=context.get("provider"),
            )

        # HTTP errors
        if "status" in exc_msg.lower() or "http" in exc_type.lower() or "http" in exc_msg.lower():
            if "401" in exc_msg or "403" in exc_msg:
                return OrchestraError(
                    code=ErrorCode.PROVR_AUTH_FAILED,
                    message=f"Autenticazione fallita per {context.get('provider', 'unknown')}",
                    details=exc_msg,
                    provider=context.get("provider"),
                    suggestion="Verifica la API key nel file .env",
                )
            if "429" in exc_msg:
                return OrchestraError(
                    code=ErrorCode.PROVR_RATE_LIMITED,
                    message=f"Rate limit raggiunto per {context.get('provider', 'unknown')}",
                    details=exc_msg,
                    provider=context.get("provider"),
                    recoverable=True,
                    suggestion="Attendi qualche secondo prima di riprovare",
                )
            if "404" in exc_msg:
                return OrchestraError(
                    code=ErrorCode.PROVR_MODEL_NOT_FOUND,
                    message=f"Modello non trovato: {context.get('model', 'unknown')}",
                    details=exc_msg,
                    provider=context.get("provider"),
                    model=context.get("model"),
                    suggestion="Verifica il nome del modello o installalo con 'ollama pull'",
                )

        # SQLite errors
        if "sqlite" in exc_type.lower() or "database" in exc_msg.lower():
            return OrchestraError(
                code=ErrorCode.DB_QUERY_FAILED,
                message=f"Errore database: {exc_msg[:200]}",
                details=exc_msg,
            )

        # Fallback generico
        return OrchestraError(
            code=ErrorCode.SYSTEM_UNKNOWN,
            message=f"Errore imprevisto: {exc_type}",
            details=exc_msg[:500],
            provider=context.get("provider"),
            model=context.get("model"),
        )

    def _record_error(self, error: OrchestraError):
        self._error_history.append(error)
        if len(self._error_history) > self._max_history:
            self._error_history = self._error_history[-self._max_history:]
        key = error.code.name
        self._error_counts[key] = self._error_counts.get(key, 0) + 1

    @property
    def stats(self) -> dict:
        recent = self._error_history[-50:] if self._error_history else []
        return {
            "total_errors": len(self._error_history),
            "error_counts": dict(self._error_counts),
            "recent_errors": [e.to_dict() for e in recent[-10:]],
            "most_common": sorted(
                self._error_counts.items(), key=lambda x: -x[1]
            )[:5] if self._error_counts else [],
        }


# === FALLBACK CHAIN ===

class FallbackChain:
    """
    Catena di fallback: prova A, se fallisce prova B, poi C...
    Registra quale provider ha funzionato per ottimizzare future richieste.
    """

    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self._chains: dict[str, list[Callable]] = {}
        self._success_history: dict[str, str] = {}
        self._error_handler = error_handler or ErrorHandler()

    def register_chain(self, name: str, providers: list[tuple[str, Callable]]):
        """Registra una catena di fallback."""
        self._chains[name] = providers

    async def execute(self, chain_name: str, *args, **kwargs) -> Any:
        """Esegui la catena di fallback fino al primo successo."""
        chain = self._chains.get(chain_name, [])
        if not chain:
            raise ValueError(f"Catena '{chain_name}' non registrata")

        last_error = None
        for provr_name, func in chain:
            try:
                result = await func(*args, **kwargs)
                self._success_history[chain_name] = provr_name
                return result
            except Exception as e:
                last_error = self._error_handler.handle(
                    e, context={"provider": provr_name, "chain": chain_name}
                )
                logger.info(f"[Fallback] {provr_name} fallito, provo il prossimo...")
                continue

        raise OrchestraException(last_error or OrchestraError(
            code=ErrorCode.SYSTEM_UNKNOWN,
            message=f"Tutti i provider nella catena '{chain_name}' hanno fallito",
            recoverable=False,
        ))


# === SINGLETON ===
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler
