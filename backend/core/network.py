# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA — Network Optimization Engine
Gestione avanzata delle connessioni di rete:

- Connection Pool: Riuso connessioni HTTP (evita overhead TCP/TLS)
- Retry con Exponential Backoff: Riprova automaticamente su errori transitori
- Circuit Breaker: Protegge da cascade failure quando un servizio è down
- Rate Limiter: Rispetta i limiti delle API esterne
- Health Monitor: Monitora latenza e disponibilità dei provider

Pattern: Circuit Breaker (Martin Fowler)
States: CLOSED → OPEN → HALF_OPEN → CLOSED
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Any, Callable, Optional, TypeVar
from dataclasses import dataclass, field

logger = logging.getLogger("vio83.network")

try:
    import httpx
    HAS_HTTPX = True
    try:
        import h2  # noqa: F401
        HAS_H2 = True
    except ImportError:
        HAS_H2 = False
except ImportError:
    HAS_HTTPX = False
    HAS_H2 = False


# ═══════════════════════════════════════════════════════
# CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════

class CircuitState(Enum):
    CLOSED = "closed"        # Normale, le richieste passano
    OPEN = "open"            # Circuito aperto, richieste bloccate
    HALF_OPEN = "half_open"  # Test: una richiesta passa per verificare


@dataclass
class CircuitBreakerStats:
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    consecutive_failures: int = 0
    state_changes: int = 0


class CircuitBreaker:
    """
    Circuit Breaker pattern per proteggere da cascade failure.

    Funzionamento:
    1. CLOSED: Tutto normale. Conta i fallimenti consecutivi.
    2. Se fallimenti > threshold → OPEN: Blocca tutte le richieste per reset_timeout secondi.
    3. Dopo timeout → HALF_OPEN: Permette UNA richiesta di test.
    4. Se il test ha successo → CLOSED. Se fallisce → OPEN di nuovo.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._last_state_change = time.time()
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_state_change > self.reset_timeout:
                self._transition(CircuitState.HALF_OPEN)
        return self._state

    def _transition(self, new_state: CircuitState):
        old = self._state
        self._state = new_state
        self._last_state_change = time.time()
        self._stats.state_changes += 1
        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
        logger.info(f"[CircuitBreaker:{self.name}] {old.value} → {new_state.value}")

    def can_execute(self) -> bool:
        """Verifica se una richiesta può passare."""
        state = self.state  # Trigger auto-transition
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.half_open_max_calls
        return False  # OPEN

    def record_success(self):
        """Registra una chiamata riuscita."""
        self._stats.total_calls += 1
        self._stats.successful_calls += 1
        self._stats.consecutive_failures = 0
        self._stats.last_success_time = time.time()
        if self._state == CircuitState.HALF_OPEN:
            self._transition(CircuitState.CLOSED)

    def record_failure(self):
        """Registra una chiamata fallita."""
        self._stats.total_calls += 1
        self._stats.failed_calls += 1
        self._stats.consecutive_failures += 1
        self._stats.last_failure_time = time.time()
        if self._state == CircuitState.HALF_OPEN:
            self._transition(CircuitState.OPEN)
        elif self._stats.consecutive_failures >= self.failure_threshold:
            self._transition(CircuitState.OPEN)

    def record_rejected(self):
        """Registra una chiamata rifiutata dal circuito aperto."""
        self._stats.total_calls += 1
        self._stats.rejected_calls += 1

    @property
    def stats(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self._stats.total_calls,
            "successful": self._stats.successful_calls,
            "failed": self._stats.failed_calls,
            "rejected": self._stats.rejected_calls,
            "consecutive_failures": self._stats.consecutive_failures,
        }


# ═══════════════════════════════════════════════════════
# RETRY ENGINE
# ═══════════════════════════════════════════════════════

class RetryEngine:
    """
    Retry con Exponential Backoff + Jitter.
    Formula: delay = min(base_delay * 2^attempt + jitter, max_delay)
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple = (ConnectionError, TimeoutError, OSError),
        retryable_status_codes: tuple = (429, 500, 502, 503, 504),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions
        self.retryable_status_codes = retryable_status_codes

    def _calc_delay(self, attempt: int) -> float:
        import random
        delay = self.base_delay * (self.exponential_base ** attempt)
        jitter = random.uniform(0, delay * 0.1)
        return min(delay + jitter, self.max_delay)

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Esegui funzione con retry automatico."""
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                return result
            except self.retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self._calc_delay(attempt)
                    logger.warning(
                        f"[Retry] Tentativo {attempt+1}/{self.max_retries} fallito: {e}. "
                        f"Riprovo tra {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
            except Exception as e:
                # Non ritentare per errori non transitori
                raise
        raise last_exception or Exception("Max retries exceeded")


# ═══════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════

class RateLimiter:
    """
    Token Bucket Rate Limiter.
    Limita il numero di richieste per unità di tempo.
    """

    def __init__(self, max_requests: int = 60, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._tokens = max_requests
        self._last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Acquisisci un token. Ritorna True se consentito."""
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_refill
            refill = elapsed * (self.max_requests / self.window_seconds)
            self._tokens = min(self.max_requests, self._tokens + refill)
            self._last_refill = now
            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False

    async def wait_and_acquire(self):
        """Attendi fino a quando un token è disponibile."""
        while not await self.acquire():
            await asyncio.sleep(0.1)


# ═══════════════════════════════════════════════════════
# CONNECTION POOL MANAGER
# ═══════════════════════════════════════════════════════

class ConnectionPoolManager:
    """
    Gestisce pool di connessioni HTTP riutilizzabili.
    Evita overhead di apertura connessione TCP + handshake TLS per ogni richiesta.
    """

    def __init__(self):
        self._clients: dict[str, "httpx.AsyncClient"] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._rate_limiters: dict[str, RateLimiter] = {}
        self._retry_engine = RetryEngine()
        self._latency_history: dict[str, list[float]] = {}

    def register_provider(
        self,
        name: str,
        base_url: str = "",
        timeout: float = 120.0,
        max_connections: int = 10,
        rate_limit: int = 60,
        circuit_threshold: int = 5,
        headers: Optional[dict] = None,
    ):
        """Registra un provider con pool dedicato."""
        if HAS_HTTPX:
            try:
                limits = httpx.Limits(
                    max_connections=max_connections,
                    max_keepalive_connections=max_connections // 2,
                    keepalive_expiry=30,
                )
                self._clients[name] = httpx.AsyncClient(
                    base_url=base_url,
                    timeout=httpx.Timeout(timeout),
                    limits=limits,
                    headers=headers or {},
                    http2=HAS_H2,  # HTTP/2 solo se h2 è installato
                    trust_env=False,  # evita conflitti SOCKS/proxy da variabili ambiente
                )
            except (ImportError, Exception) as e:
                logger.warning(f"[Pool] httpx client non creato per {name}: {e}. Fallback a urllib.")
        self._circuit_breakers[name] = CircuitBreaker(
            name=name, failure_threshold=circuit_threshold
        )
        self._rate_limiters[name] = RateLimiter(max_requests=rate_limit)
        self._latency_history[name] = []
        logger.info(f"[Pool] Provider registrato: {name} (max_conn={max_connections})")

    async def request(
        self,
        provider: str,
        method: str,
        url: str,
        **kwargs,
    ) -> Any:
        """
        Esegui richiesta HTTP con:
        1. Circuit Breaker check
        2. Rate Limiting
        3. Connection Pool riuso
        4. Retry automatico
        5. Latency tracking
        """
        cb = self._circuit_breakers.get(provider)
        rl = self._rate_limiters.get(provider)
        client = self._clients.get(provider)

        if cb and not cb.can_execute():
            cb.record_rejected()
            raise ConnectionError(
                f"Circuit breaker OPEN per {provider}. "
                f"Servizio non disponibile. Riprova tra {cb.reset_timeout}s."
            )

        if rl:
            await rl.wait_and_acquire()

        async def _do_request():
            start = time.time()
            try:
                if client:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    latency = time.time() - start
                    self._record_latency(provider, latency)
                    if cb:
                        cb.record_success()
                    return response
                else:
                    raise ConnectionError(f"Client non registrato per {provider}")
            except Exception as e:
                if cb:
                    cb.record_failure()
                raise

        return await self._retry_engine.execute(_do_request)

    def _record_latency(self, provider: str, latency: float):
        history = self._latency_history.get(provider, [])
        history.append(latency)
        if len(history) > 100:
            history = history[-100:]
        self._latency_history[provider] = history

    def get_provider_health(self, provider: str) -> dict:
        """Ottieni metriche di salute per un provider."""
        cb = self._circuit_breakers.get(provider)
        history = self._latency_history.get(provider, [])
        avg_latency = sum(history) / len(history) if history else 0
        p95_latency = sorted(history)[int(len(history) * 0.95)] if len(history) > 5 else 0

        return {
            "provider": provider,
            "circuit_breaker": cb.stats if cb else None,
            "avg_latency_ms": round(avg_latency * 1000, 1),
            "p95_latency_ms": round(p95_latency * 1000, 1),
            "total_requests": len(history),
        }

    async def close_all(self):
        """Chiudi tutti i pool di connessioni."""
        for name, client in self._clients.items():
            await client.aclose()
            logger.info(f"[Pool] Chiuso pool: {name}")
        self._clients.clear()

    @property
    def stats(self) -> dict:
        return {
            "providers": {
                name: self.get_provider_health(name)
                for name in self._circuit_breakers
            },
            "total_pools": len(self._clients),
        }


# === SINGLETON ===
_pool_manager: Optional[ConnectionPoolManager] = None


def get_connection_pool() -> ConnectionPoolManager:
    """Ottieni istanza singleton del Connection Pool Manager."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()
    return _pool_manager
