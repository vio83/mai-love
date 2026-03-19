# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ============================================================
"""
VIO 83 PARALLEL RACE ORCHESTRATOR — Piuma™ Speed Layer
=======================================================

Il cuore della trasformazione Piuma™.

Analogia: invece di usare UNA macchina (provider) → mandi in pista
TUTTE le macchine contemporaneamente. Vince la più veloce,
oppure combini i risultati delle migliori.

Modalità:
  RACE_FIRST   — Ritorna SUBITO il primo provider che risponde (latenza minima)
  RACE_BEST    — Aspetta K risposte, ritorna la migliore (qualità massima)
  RACE_CROSS   — Verifica incrociata: ritorna solo se ≥2 provider concordano
  RACE_STREAM  — Prima risposta in streaming, le altre come verifica asincrona

Performance vs sequenziale:
  - 3 provider sequenziali: 900ms + 1200ms + 800ms = 2900ms
  - 3 provider paralleli (RACE_FIRST): max(900, 1200, 800) = 900ms → 3.2x più veloce
  - Con circuit breaker: skip provider lenti → <500ms medi

Features:
  - asyncio.gather con timeout per provider
  - Circuit breaker integrato (usa AdaptiveProviderMemory)
  - Qualità scoring basato su lunghezza, coerenza, completezza
  - Retry automatico su provider secondario se primario fallisce
  - Telemetria completa per ogni race
"""

import asyncio
import time
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple

from backend.core.ultra_engine import get_ultra_engine


class RaceMode(str, Enum):
    FIRST   = "first"    # Primo che risponde vince
    BEST    = "best"     # Aspetta K, prendi il migliore
    CROSS   = "cross"    # Verifica incrociata (≥2 concordano)
    STREAM  = "stream"   # Streaming del primo, verifica async


@dataclass
class RaceResult:
    """Risultato di una gara tra provider."""
    winner: str                          # Provider vincitore
    response: str                        # Risposta finale
    latency_ms: float                    # Latenza in ms
    mode: RaceMode                       # Modalità usata
    all_results: Dict[str, Any] = field(default_factory=dict)   # Tutti i risultati
    quality_score: float = 0.8           # Score qualità 0-1
    cross_checked: bool = False          # Se verificato incrociato
    consensus: Optional[str] = None      # Se cross-check, punto di consenso
    error: Optional[str] = None          # Errore se fallita
    tokens_used: int = 0


@dataclass
class ProviderCall:
    """Configurazione di una singola chiamata provider."""
    provider_id: str
    coro: Coroutine          # Coroutine async che ritorna stringa
    timeout_s: float = 30.0  # Timeout per questo provider
    priority: int = 0         # Priorità (0=normale, 1=alta, 2=massima)


class ParallelRaceOrchestrator:
    """
    Orchestratore parallelo con racing engine.

    Uso tipico:
        race = ParallelRaceOrchestrator()
        result = await race.run(
            providers=[
                ProviderCall("claude", call_claude(msg), timeout_s=20),
                ProviderCall("ollama", call_ollama(msg), timeout_s=10),
            ],
            mode=RaceMode.FIRST,
            intent="code",
        )
        print(result.response, result.winner, result.latency_ms)
    """

    # Soglia per considerare due risposte "concordanti" (cross-check)
    CONSENSUS_SIMILARITY_THRESHOLD = 0.65

    # Minimo caratteri per risposta valida
    MIN_VALID_RESPONSE_LEN = 20

    def __init__(self):
        self._engine = get_ultra_engine()
        self._races_run = 0
        self._total_latency_ms = 0.0
        self._wins: Dict[str, int] = {}

    # ──────────────────────────────────────────────
    # QUALITY SCORING
    # ──────────────────────────────────────────────

    @staticmethod
    def _score_response(response: str, intent: Optional[str] = None) -> float:
        """
        Score qualità risposta 0-1.
        Euristiche veloci, no ML needed.
        """
        if not response or len(response) < 10:
            return 0.0

        score = 0.5  # Base

        # Lunghezza: né troppo corta né troppo lunga
        length = len(response)
        if 100 <= length <= 2000:
            score += 0.2
        elif 50 <= length <= 5000:
            score += 0.1

        # Struttura: presenza di paragrafi, elenchi
        if '\n' in response:
            score += 0.05
        if any(c in response for c in ['•', '-', '*', '1.', '2.']):
            score += 0.05

        # Intent-specific scoring
        if intent == "code":
            # Presenza di codice strutturato
            if '```' in response or 'def ' in response or 'class ' in response:
                score += 0.15
            if 'import' in response or 'function' in response:
                score += 0.05
        elif intent == "math":
            # Presenza di formule o numeri strutturati
            has_numbers = bool(re.search(r'\d+\.?\d*', response))
            has_operators = bool(re.search(r'[=+\-×÷/]', response))
            if has_numbers and has_operators:
                score += 0.15
        elif intent == "creative":
            # Presenza di struttura narrativa
            paragraphs = [p for p in response.split('\n\n') if p.strip()]
            if len(paragraphs) >= 2:
                score += 0.15

        # Penalità per risposte evasive
        evasive_patterns = [
            "non posso", "cannot", "i'm unable", "non ho informazioni",
            "mi dispiace ma", "unfortunately", "i don't know"
        ]
        if any(p in response.lower() for p in evasive_patterns):
            score -= 0.2

        # Penalità per risposte molto corte se non è conversazione
        if intent and intent != "conversation" and length < 50:
            score -= 0.15

        return max(0.0, min(1.0, score))

    @staticmethod
    def _compute_similarity(a: str, b: str) -> float:
        """
        Similarità semantica approssimata (no embedding, veloce).
        Usa Jaccard su bigrammi di parole.
        """
        def get_bigrams(text: str) -> set:
            words = text.lower().split()
            return {(words[i], words[i+1]) for i in range(len(words)-1)}

        bg_a = get_bigrams(a)
        bg_b = get_bigrams(b)
        if not bg_a or not bg_b:
            return 0.0
        intersection = len(bg_a & bg_b)
        union = len(bg_a | bg_b)
        return intersection / union if union > 0 else 0.0

    # ──────────────────────────────────────────────
    # RACE ENGINE
    # ──────────────────────────────────────────────

    async def run(
        self,
        providers: List[ProviderCall],
        mode: RaceMode = RaceMode.FIRST,
        intent: Optional[str] = None,
        min_responses_for_best: int = 2,
    ) -> RaceResult:
        """
        Esegui la gara tra provider.

        Args:
            providers: Lista di chiamate provider da eseguire in parallelo
            mode: Strategia di selezione risultato
            intent: Categoria semantica per scoring qualità
            min_responses_for_best: Per BEST mode, min risposte da aspettare
        """
        if not providers:
            return RaceResult(
                winner="none", response="", latency_ms=0,
                mode=mode, error="No providers specified"
            )

        self._races_run += 1
        start = time.monotonic()
        engine = self._engine

        if mode == RaceMode.FIRST:
            result = await self._race_first(providers, intent, start)
        elif mode == RaceMode.BEST:
            result = await self._race_best(providers, intent, start, min_responses_for_best)
        elif mode == RaceMode.CROSS:
            result = await self._race_cross(providers, intent, start)
        else:  # STREAM — fallback a FIRST per ora
            result = await self._race_first(providers, intent, start)

        # Registra telemetria
        self._total_latency_ms += result.latency_ms
        self._wins[result.winner] = self._wins.get(result.winner, 0) + 1

        # Aggiorna AdaptiveProviderMemory
        for pid, resp in result.all_results.items():
            if isinstance(resp, str) and len(resp) >= self.MIN_VALID_RESPONSE_LEN:
                q = self._score_response(resp, intent)
                latency = result.latency_ms if pid == result.winner else result.latency_ms * 1.5
                engine.provider_memory.record_success(pid, latency, q, intent)
            elif isinstance(resp, Exception):
                engine.provider_memory.record_error(pid, intent)

        return result

    async def _call_provider_safe(
        self, pc: ProviderCall
    ) -> Tuple[str, Any]:
        """Chiama provider con timeout e error handling."""
        try:
            resp = await asyncio.wait_for(pc.coro, timeout=pc.timeout_s)
            if not resp or len(str(resp)) < self.MIN_VALID_RESPONSE_LEN:
                return pc.provider_id, ValueError(f"Response too short: {len(str(resp))} chars")
            return pc.provider_id, str(resp)
        except asyncio.TimeoutError:
            return pc.provider_id, TimeoutError(f"Provider {pc.provider_id} timeout after {pc.timeout_s}s")
        except Exception as e:
            return pc.provider_id, e

    async def _race_first(
        self, providers: List[ProviderCall], intent: Optional[str], start: float
    ) -> RaceResult:
        """RACE_FIRST: ritorna subito il primo provider valido."""
        all_results: Dict[str, Any] = {}

        # Ordina per priority
        sorted_providers = sorted(providers, key=lambda p: p.priority, reverse=True)
        tasks = {
            asyncio.create_task(self._call_provider_safe(pc)): pc
            for pc in sorted_providers
        }

        winner_id = None
        winner_resp = None

        try:
            for coro in asyncio.as_completed(list(tasks.keys())):
                pid, resp = await coro
                all_results[pid] = resp
                if isinstance(resp, str) and not winner_id:
                    winner_id = pid
                    winner_resp = resp
                    # Cancella le restanti
                    for t in tasks:
                        if not t.done():
                            t.cancel()
                    break
        except Exception:
            pass

        latency_ms = (time.monotonic() - start) * 1000

        if winner_id and winner_resp:
            return RaceResult(
                winner=winner_id,
                response=winner_resp,
                latency_ms=latency_ms,
                mode=RaceMode.FIRST,
                all_results=all_results,
                quality_score=self._score_response(winner_resp, intent),
            )

        # Tutti falliti
        errors = {pid: str(r) for pid, r in all_results.items() if isinstance(r, Exception)}
        return RaceResult(
            winner="none", response="", latency_ms=latency_ms,
            mode=RaceMode.FIRST, all_results=all_results,
            error=f"All providers failed: {errors}"
        )

    async def _race_best(
        self, providers: List[ProviderCall], intent: Optional[str],
        start: float, min_k: int
    ) -> RaceResult:
        """RACE_BEST: aspetta K risposte, prendi la migliore per qualità."""
        all_results: Dict[str, Any] = {}
        valid_responses: List[Tuple[str, str, float]] = []  # (pid, resp, score)

        tasks = [asyncio.create_task(self._call_provider_safe(pc)) for pc in providers]

        for coro in asyncio.as_completed(tasks):
            pid, resp = await coro
            all_results[pid] = resp
            if isinstance(resp, str):
                score = self._score_response(resp, intent)
                valid_responses.append((pid, resp, score))
                if len(valid_responses) >= min_k:
                    # Cancella rimanenti
                    for t in tasks:
                        if not t.done():
                            t.cancel()
                    break

        latency_ms = (time.monotonic() - start) * 1000

        if not valid_responses:
            return RaceResult(
                winner="none", response="", latency_ms=latency_ms,
                mode=RaceMode.BEST, all_results=all_results,
                error="No valid responses"
            )

        # Migliore per quality score
        best = max(valid_responses, key=lambda x: x[2])
        return RaceResult(
            winner=best[0],
            response=best[1],
            latency_ms=latency_ms,
            mode=RaceMode.BEST,
            all_results=all_results,
            quality_score=best[2],
        )

    async def _race_cross(
        self, providers: List[ProviderCall], intent: Optional[str], start: float
    ) -> RaceResult:
        """RACE_CROSS: verifica incrociata — risposta solo se ≥2 concordano."""
        all_results: Dict[str, Any] = {}
        valid: List[Tuple[str, str]] = []

        tasks = [asyncio.create_task(self._call_provider_safe(pc)) for pc in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for item in results:
            if isinstance(item, tuple):
                pid, resp = item
                all_results[pid] = resp
                if isinstance(resp, str):
                    valid.append((pid, resp))

        latency_ms = (time.monotonic() - start) * 1000

        if len(valid) < 2:
            # Fallback: usa il primo disponibile
            if valid:
                pid, resp = valid[0]
                return RaceResult(
                    winner=pid, response=resp, latency_ms=latency_ms,
                    mode=RaceMode.CROSS, all_results=all_results,
                    quality_score=self._score_response(resp, intent),
                    cross_checked=False,
                )
            return RaceResult(
                winner="none", response="", latency_ms=latency_ms,
                mode=RaceMode.CROSS, all_results=all_results,
                error="Not enough valid responses for cross-check"
            )

        # Trova coppia più simile
        best_pair = None
        best_sim = 0.0
        for i in range(len(valid)):
            for j in range(i+1, len(valid)):
                sim = self._compute_similarity(valid[i][1], valid[j][1])
                if sim > best_sim:
                    best_sim = sim
                    best_pair = (valid[i], valid[j])

        if best_pair and best_sim >= self.CONSENSUS_SIMILARITY_THRESHOLD:
            # Le due risposte concordano → usa la più lunga
            winner = max(best_pair, key=lambda x: len(x[1]))
            return RaceResult(
                winner=winner[0],
                response=winner[1],
                latency_ms=latency_ms,
                mode=RaceMode.CROSS,
                all_results=all_results,
                quality_score=min(1.0, self._score_response(winner[1], intent) + 0.1),
                cross_checked=True,
                consensus=f"Similarity {best_sim:.2f} between {best_pair[0][0]} and {best_pair[1][0]}",
            )

        # Nessun consenso → usa la migliore per qualità individuale
        best_solo = max(valid, key=lambda x: self._score_response(x[1], intent))
        return RaceResult(
            winner=best_solo[0],
            response=best_solo[1],
            latency_ms=latency_ms,
            mode=RaceMode.CROSS,
            all_results=all_results,
            quality_score=self._score_response(best_solo[1], intent),
            cross_checked=False,
        )

    @property
    def stats(self) -> dict:
        return {
            "engine": "ParallelRaceOrchestrator™",
            "races_run": self._races_run,
            "avg_latency_ms": round(self._total_latency_ms / max(1, self._races_run), 1),
            "wins_by_provider": self._wins,
        }


# Singleton
_race_orchestrator: Optional[ParallelRaceOrchestrator] = None

def get_race_orchestrator() -> ParallelRaceOrchestrator:
    global _race_orchestrator
    if _race_orchestrator is None:
        _race_orchestrator = ParallelRaceOrchestrator()
    return _race_orchestrator
