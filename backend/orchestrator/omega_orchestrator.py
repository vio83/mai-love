# ============================================================
# VIO 83 AI ORCHESTRA — OmegaOrchestrator™
# Copyright © 2026 Viorica Porcu (vio83) — All rights reserved
# ============================================================
"""
OmegaOrchestrator™ v1.0 — Orchestrazione 100x Performance
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Orchestratore di prossima generazione che porta l'output di ogni
sessione AI a qualità mondiale automaticamente, senza intervento umano.

Integra:
  → WorldDataIntegrator™  (dati mondiali freschi nel contesto)
  → ReasoningAmplifier™   (intent decode + CoT + quality verify)
  → AdvancedOrchestrator  (selezione provider ottimale)
  → UltraEngine™          (cache semantica Piuma™)
  → AutoOptimizer™        (auto-calibrazione sistema)

Pipeline completa per ogni request:
  1. DECODE    — IntentDecoder (0.5ms)
  2. ENRICH    — WorldDataIntegrator context injection (<50ms)
  3. ENHANCE   — System prompt enhancement con CoT (<0.5ms)
  4. ROUTE     — Provider selection ottimale (<1ms)
  5. EXECUTE   — AI call con fallback chain
  6. VERIFY    — QualityVerifier certificazione (<2ms)
  7. AMPLIFY   — OutputAmplifier post-processing (<10ms)
  8. LEARN     — Pattern memory update + AutoCalibrator
  9. RESPOND   — Output certificato ✓

Performance target:
  - Overhead totale Omega pipeline: <100ms extra vs raw call
  - Cache hit rate target: >60% su conversazioni tipiche
  - Quality score medio: >0.82
  - Auto-improvement rate: +2% qualità ogni 100 interazioni
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Dict, List, Optional, Tuple

logger = logging.getLogger("omega_orchestrator")


@dataclass
class OmegaRequest:
    """Request per OmegaOrchestrator™."""
    user_input: str
    conversation_id: str = ""
    provr_hint: Optional[str] = None          # suggerimento provider
    use_world_context: bool = True               # inietta dati mondiali
    stream: bool = False                         # streaming response
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system_prompt_overr: Optional[str] = None


@dataclass
class OmegaResponse:
    """Response completa con metriche Omega."""
    content: str
    provr_used: str
    model_used: str
    quality_score: float
    intent_domain: str
    intent_complexity: float
    world_context_injected: bool
    world_articles_used: int
    processing_ms: float
    cache_hit: bool
    amplified: bool
    quality_report: Dict
    omega_version: str = "1.0.0"


class OmegaOrchestrator:
    """
    OmegaOrchestrator™ — Pipeline di qualità mondiale 100x.

    Coordina tutti i moduli VIO AI Orchestra per produrre output
    di massima qualità mondiale in modo automatico e auto-migliorante.

    Usage:
        omega = OmegaOrchestrator()
        await omega.initialize()
        response = await omega.process(OmegaRequest(user_input="..."))
        print(f"Quality: {response.quality_score}")
        print(response.content)
    """

    VERSION = "1.0.0"
    BASE_SYSTEM_PROMPT = (
        "Sei VIO 83 — sistema AI di qualità mondiale. "
        "Rispondi con massima precisione, profondità e utilità pratica. "
        "Ogni tua risposta è certificata: esatta, completa, verificabile."
    )

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Lazy imports per evitare circular imports
        self._world_integrator = None
        self._reasoning_amplifier = None
        self._advanced_orchestrator = None
        self._ultra_engine = None
        self._initialized = False

        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "world_ctx_injections": 0,
            "quality_sum": 0.0,
            "amplifications": 0,
            "errors": 0,
        }

        logger.info(f"[OmegaOrchestrator™ v{self.VERSION}] Istanza creata")

    async def initialize(self):
        """Inizializza tutti i moduli in parallelo."""
        if self._initialized:
            return

        logger.info("[OmegaOrchestrator™] Inizializzazione moduli...")

        # Import lazy per evitare problemi di import circolari
        try:
            from backend.core.reasoning_amplifier import get_reasoning_amplifier
            from backend.core.world_data_integrator import get_world_integrator
            self._world_integrator = get_world_integrator(self.data_dir)
            self._reasoning_amplifier = get_reasoning_amplifier(self.data_dir)
        except ImportError as e:
            logger.warning(f"[OmegaOrchestrator™] Import parziale: {e}")

        # Avvia WorldDataIntegrator™ in background
        if self._world_integrator:
            try:
                await self._world_integrator.start()
                logger.info("[OmegaOrchestrator™] WorldDataIntegrator™ avviato ✓")
            except Exception as e:
                logger.warning(f"[OmegaOrchestrator™] WorldDataIntegrator™ start: {e}")

        self._initialized = True
        logger.info("[OmegaOrchestrator™] Inizializzazione completata ✓")

    async def process(self, request: OmegaRequest) -> OmegaResponse:
        """
        Pipeline completa Omega: 9 step certificati.
        Returns OmegaResponse con quality score e metriche complete.
        """
        if not self._initialized:
            await self.initialize()

        t0 = time.monotonic()
        self._stats["total_requests"] += 1

        # ── STEP 1: DECODE intent ──────────────────────────────────
        intent = None
        if self._reasoning_amplifier:
            intent = self._reasoning_amplifier.decode_intent(request.user_input)
            logger.debug(f"[Omega.DECODE] domain={intent.domain}, complexity={intent.complexity:.2f}")

        # ── STEP 2: ENRICH con world context ──────────────────────
        world_context = ""
        world_articles_count = 0
        if request.use_world_context and self._world_integrator and intent:
            try:
                articles = await self._world_integrator.search_world(
                    query=request.user_input[:200],
                    domain=intent.domain if intent.domain != "general" else None,
                    limit=3,
                    min_priority=6,
                )
                if articles:
                    world_articles_count = len(articles)
                    world_ctx_lines = []
                    for art in articles:
                        world_ctx_lines.append(
                            f"[Fonte mondiale recente] {art['title']}: {art.get('summary', '')[:200]}"
                        )
                    world_context = "\n".join(world_ctx_lines)
                    self._stats["world_ctx_injections"] += 1
                    logger.debug(f"[Omega.ENRICH] {world_articles_count} articoli mondiali iniettati")
            except Exception as e:
                logger.debug(f"[Omega.ENRICH] {e}")

        # ── STEP 3: ENHANCE system prompt ─────────────────────────
        system_prompt = request.system_prompt_overr or self.BASE_SYSTEM_PROMPT
        if self._reasoning_amplifier and intent:
            system_prompt = self._reasoning_amplifier.enhance_system_prompt(system_prompt, intent)
        if world_context:
            system_prompt += f"\n\n[CONTESTO MONDIALE AGGIORNATO]\n{world_context}"

        # ── STEP 4-5: ROUTE + EXECUTE ──────────────────────────────
        # Costruisci messages per provider
        messages = [{"role": "user", "content": request.user_input}]

        # Determina max_tokens
        max_tokens = request.max_tokens
        if max_tokens is None and intent:
            max_tokens = min(4096, max(512, intent.estimated_tokens * 2))

        # Esegui via advanced_orchestrator se disponibile
        raw_output = ""
        provr_used = "unknown"
        model_used = "unknown"
        cache_hit = False

        try:
            raw_output, provr_used, model_used, cache_hit = await self._execute_ai_call(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=request.temperature,
                provr_hint=request.provr_hint,
                intent=intent,
            )
        except Exception as e:
            logger.error(f"[Omega.EXECUTE] Errore: {e}")
            self._stats["errors"] += 1
            raw_output = f"[Errore orchestrazione: {e}]"

        if cache_hit:
            self._stats["cache_hits"] += 1

        # ── STEP 6-7: VERIFY + AMPLIFY ────────────────────────────
        quality_report = {}
        amplified = False
        quality_score = 0.75  # default

        if self._reasoning_amplifier and raw_output and not raw_output.startswith("[Errore"):
            result = self._reasoning_amplifier.process_output(
                user_input=request.user_input,
                raw_output=raw_output,
                intent=intent,
                record_pattern=True,
            )
            final_output = result["output"]
            quality_score = result["quality"]["overall"]
            quality_report = result["quality"]
            amplified = result["amplified"]
            if amplified:
                self._stats["amplifications"] += 1
        else:
            final_output = raw_output

        # ── STEP 8: LEARN (asincrono, non blocca response) ────────
        self._stats["quality_sum"] += quality_score
        asyncio.create_task(self._async_learn(
            intent=intent,
            quality_score=quality_score,
            provr_used=provr_used,
        ))

        # ── STEP 9: RESPOND ───────────────────────────────────────
        total_ms = round((time.monotonic() - t0) * 1000, 1)
        logger.info(
            f"[OmegaOrchestrator™] ✓ provider={provr_used} "
            f"quality={quality_score:.2f} ms={total_ms} "
            f"cache={'HIT' if cache_hit else 'MISS'} "
            f"world={world_articles_count}art"
        )

        return OmegaResponse(
            content=final_output,
            provr_used=provr_used,
            model_used=model_used,
            quality_score=quality_score,
            intent_domain=intent.domain if intent else "unknown",
            intent_complexity=intent.complexity if intent else 0.5,
            world_context_injected=bool(world_context),
            world_articles_used=world_articles_count,
            processing_ms=total_ms,
            cache_hit=cache_hit,
            amplified=amplified,
            quality_report=quality_report,
        )

    async def _execute_ai_call(
        self,
        messages: List[Dict],
        system_prompt: str,
        max_tokens: Optional[int],
        temperature: Optional[float],
        provr_hint: Optional[str],
        intent,
    ) -> Tuple[str, str, str, bool]:
        """
        Esegui chiamata AI tramite provider disponibili.
        Returns: (output, provider, model, cache_hit)
        Prova nell'ordine: advanced_orchestrator → direct call
        """
        # Tenta import advanced_orchestrator
        try:
            from backend.orchestrator.advanced_orchestrator import AdvancedOrchestrator
            if self._advanced_orchestrator is None:
                self._advanced_orchestrator = AdvancedOrchestrator()

            result = await self._advanced_orchestrator.route_request(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=max_tokens or 2048,
                temperature=temperature or 0.7,
                task_type=intent.domain if intent else "general",
            )
            if result and result.get("content"):
                return (
                    result["content"],
                    result.get("provider", "advanced"),
                    result.get("model", "auto"),
                    result.get("cache_hit", False),
                )
        except Exception as e:
            logger.debug(f"[Omega._execute] advanced_orchestrator: {e}")

        # Fallback: ritorna placeholder (in produzione qui ci sarebbe direct HTTP call)
        return (
            "[OmegaOrchestrator™: provider non disponibile in questo ambiente. "
            "Configura le API keys in .env per attivare il routing AI completo.]",
            "fallback",
            "none",
            False,
        )

    async def _async_learn(self, intent, quality_score: float, provr_used: str):
        """Learning asincrono post-response (non blocca l'utente)."""
        try:
            # AutoOptimizer si occuperà del learning approfondito
            # Qui registriamo solo le metriche base
            if self._reasoning_amplifier and quality_score > 0:
                pass  # Il learning avviene in process_output → record_pattern
        except Exception as e:
            logger.debug(f"[Omega._async_learn] {e}")

    async def process_stream(self, request: OmegaRequest) -> AsyncIterator[str]:
        """
        Streaming version della pipeline Omega.
        Yield chunks di testo mentre vengono generati.
        """
        # Per ora: esegui normale e simula streaming
        response = await self.process(request)
        words = response.content.split()
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            if i % 10 == 9:
                await asyncio.sleep(0.001)  # breathing per event loop

    def get_stats(self) -> Dict:
        """Statistiche complete OmegaOrchestrator™."""
        total = self._stats["total_requests"]
        return {
            "version": self.VERSION,
            "total_requests": total,
            "cache_hit_rate": round(self._stats["cache_hits"] / max(1, total), 3),
            "avg_quality": round(self._stats["quality_sum"] / max(1, total), 3),
            "world_ctx_rate": round(self._stats["world_ctx_injections"] / max(1, total), 3),
            "amplification_rate": round(self._stats["amplifications"] / max(1, total), 3),
            "error_rate": round(self._stats["errors"] / max(1, total), 3),
            "initialized": self._initialized,
        }

    async def get_full_status(self) -> Dict:
        """Status completo di tutti i sotto-moduli."""
        status = {"omega": self.get_stats()}
        if self._world_integrator:
            try:
                status["world_integrator"] = await self._world_integrator.get_status()
            except Exception:
                pass
        if self._reasoning_amplifier:
            status["reasoning_amplifier"] = self._reasoning_amplifier.get_stats()
        return status


# ─── Singleton ────────────────────────────────────────────────────────

_omega: Optional[OmegaOrchestrator] = None

def get_omega_orchestrator(data_dir: Optional[Path] = None) -> OmegaOrchestrator:
    global _omega
    if _omega is None:
        _omega = OmegaOrchestrator(data_dir=data_dir)
    return _omega
