# ============================================================
# VIO 83 AI ORCHESTRA — MultiStepReasoning™ (REAL Chain-of-Thought)
# Copyright © 2026 Viorica Porcu (vio83) — All rights reserved
# ============================================================
"""
MultiStepReasoning™ v1.0 — Ragionamento Multi-Step REALE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A differenza del vecchio ReasoningAmplifier (che aggiungeva solo
testo al system prompt), questo modulo esegue VERE chiamate AI
multiple in sequenza:

  Step 1: ANALYZE  → Chiama AI per analizzare la domanda
  Step 2: SOLVE    → Chiama AI con l'analisi per risolvere
  Step 3: VERIFY   → Chiama AI per verificare la risposta
  Step 4: REFINE   → Se verifica fallisce, corregge (opzionale)

Ogni step = 1 vera chiamata API = reasoning reale.
Costa 3-4x in token, ma la qualità aumenta significativamente.

Quando usare MultiStep vs SingleStep:
  - Complessità alta (>0.7)     → MultiStep obbligatorio
  - Task critico (medical/legal) → MultiStep obbligatorio
  - Task semplice/chat          → SingleStep (veloce)
  - Budget token limitato       → SingleStep con enhanced prompt
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("multistep_reasoning")


# ─── Dataclasses ──────────────────────────────────────────────────────

@dataclass
class ReasoningStep:
    """Risultato di un singolo step di ragionamento."""
    step_name: str          # "analyze" | "solve" | "verify" | "refine"
    step_number: int
    provr: str
    model: str
    input_prompt: str
    output: str
    tokens_used: int
    latency_ms: float
    quality_estimate: float  # 0-1 (stima euristica)


@dataclass
class ReasoningResult:
    """Risultato completo del reasoning multi-step."""
    final_output: str
    steps: List[ReasoningStep]
    total_tokens: int
    total_latency_ms: float
    steps_executed: int
    verification_passed: bool
    refined: bool
    quality_estimate: float


# Tipo per la funzione di chiamata AI (iniettata dall'orchestratore)
AICallFn = Callable  # async (messages, system_prompt, max_tokens, temperature) -> Dict


# ─── Step Templates ───────────────────────────────────────────────────

ANALYZE_SYSTEM = """Sei un analista esperto. Il tuo compito è SOLO analizzare la domanda dell'utente.
NON rispondere alla domanda. Invece:
1. ntifica il dominio esatto della domanda
2. ntifica le sotto-domande implicite
3. ntifica possibili ambiguità o trappole
4. Elenca i prerequisiti concettuali necessari per rispondere
5. Suggerisci la struttura ottimale della risposta
Rispondi in formato strutturato e conciso."""

SOLVE_SYSTEM_TEMPLATE = """Sei un esperto mondiale nel dominio richiesto. Rispondi alla domanda dell'utente con la massima precisione e completezza.

CONTESTO DALL'ANALISI PRECEDENTE:
{analysis}

Usa questa analisi per guidare la tua risposta. Assicurati di:
- Rispondere a TUTTE le sotto-domande ntificate
- Evitare le ambiguità segnalate
- Seguire la struttura suggerita
- Essere preciso e verificabile"""

VERIFY_SYSTEM_TEMPLATE = """Sei un verificatore critico. Devi controllare la correttezza di questa risposta.

DOMANDA ORIGINALE:
{question}

RISPOSTA DA VERIFICARE:
{answer}

Verifica:
1. La risposta è FATTUALMENTE corretta? (cita errori specifici se no)
2. La risposta è COMPLETA? (manca qualcosa di importante?)
3. La risposta è CHIARA e ben strutturata?
4. Ci sono contraddizioni interne?

Rispondi con ESATTAMENTE questo formato:
VERDICT: PASS oppure FAIL
ISSUES: [lista problemi se FAIL, "nessuno" se PASS]
SUGGESTIONS: [miglioramenti suggeriti]"""

REFINE_SYSTEM_TEMPLATE = """Sei un editor esperto. Devi correggere e migliorare questa risposta basandoti sulla verifica.

DOMANDA ORIGINALE:
{question}

RISPOSTA ORIGINALE:
{answer}

PROBLEMI NTIFICATI:
{issues}

SUGGERIMENTI:
{suggestions}

Produci una versione CORRETTA e MIGLIORATA della risposta. Mantieni tutto ciò che era giusto, correggi gli errori, aggiungi ciò che mancava."""


# ─── MultiStepReasoner ────────────────────────────────────────────────

class MultiStepReasoner:
    """
    MultiStepReasoning™ — Chain-of-Thought REALE con chiamate AI multiple.

    Usage:
        reasoner = MultiStepReasoner()

        # Definisci la funzione di chiamata AI (dal tuo orchestratore)
        async def call_ai(messages, system_prompt, max_tokens, temperature):
            # ... chiama il provr AI ...
            return {"content": "...", "tokens": 500, "latency_ms": 1200}

        # Esegui reasoning multi-step
        result = await reasoner.reason(
            user_input="Spiega la meccanica quantistica",
            ai_call_fn=call_ai,
            complexity=0.8,
            domain="science",
        )

        print(f"Steps: {result.steps_executed}")
        print(f"Verified: {result.verification_passed}")
        print(result.final_output)
    """

    VERSION = "1.0.0"

    # Soglie per decre quanti step
    MULTISTEP_THRESHOLD = 0.6    # Complexity > questa → multi-step
    VERIFICATION_THRESHOLD = 0.7  # Complexity > questa → verifica obbligatoria
    CRITICAL_DOMAINS = {"medical", "legal", "science", "math"}  # Sempre verifica

    def __init__(self):
        self._stats = {
            "total_calls": 0,
            "multistep_calls": 0,
            "verifications": 0,
            "verification_failures": 0,
            "refinements": 0,
        }

    async def reason(
        self,
        user_input: str,
        ai_call_fn: AICallFn,
        complexity: float = 0.5,
        domain: str = "general",
        force_multistep: bool = False,
        max_tokens_per_step: int = 2048,
        temperature: float = 0.7,
    ) -> ReasoningResult:
        """
        Esegui reasoning. Dec automaticamente se usare multi-step.

        Args:
            user_input: domanda dell'utente
            ai_call_fn: funzione async per chiamare AI
            complexity: 0-1, complessità stimata della domanda
            domain: dominio del task
            force_multistep: forza multi-step anche per task semplici
            max_tokens_per_step: token budget per singolo step
            temperature: temperatura per le chiamate AI
        """
        self._stats["total_calls"] += 1
        t0 = time.monotonic()

        # Dec se multi-step è necessario
        needs_multistep = (
            force_multistep
            or complexity > self.MULTISTEP_THRESHOLD
            or domain in self.CRITICAL_DOMAINS
        )

        if not needs_multistep:
            # SingleStep: una sola chiamata diretta (veloce)
            return await self._single_step(user_input, ai_call_fn, max_tokens_per_step, temperature)

        self._stats["multistep_calls"] += 1

        # ── STEP 1: ANALYZE ──────────────────────────────────────
        analyze_result = await self._call_step(
            step_name="analyze",
            step_number=1,
            user_input=user_input,
            system_prompt=ANALYZE_SYSTEM,
            ai_call_fn=ai_call_fn,
            max_tokens=max_tokens_per_step // 2,  # Analisi più corta
            temperature=0.3,  # Bassa temperature per analisi precisa
        )

        steps = [analyze_result]

        # ── STEP 2: SOLVE ────────────────────────────────────────
        solve_system = SOLVE_SYSTEM_TEMPLATE.format(analysis=analyze_result.output[:2000])
        solve_result = await self._call_step(
            step_name="solve",
            step_number=2,
            user_input=user_input,
            system_prompt=solve_system,
            ai_call_fn=ai_call_fn,
            max_tokens=max_tokens_per_step,
            temperature=temperature,
        )
        steps.append(solve_result)

        # ── STEP 3: VERIFY (se complessità alta o dominio critico) ──
        needs_verification = (
            complexity > self.VERIFICATION_THRESHOLD
            or domain in self.CRITICAL_DOMAINS
        )

        verification_passed = True
        refined = False
        final_output = solve_result.output

        if needs_verification:
            self._stats["verifications"] += 1

            verify_system = VERIFY_SYSTEM_TEMPLATE.format(
                question=user_input[:1000],
                answer=solve_result.output[:3000],
            )
            verify_result = await self._call_step(
                step_name="verify",
                step_number=3,
                user_input="Verifica la risposta sopra.",
                system_prompt=verify_system,
                ai_call_fn=ai_call_fn,
                max_tokens=max_tokens_per_step // 2,
                temperature=0.1,  # Molto precisa per verifica
            )
            steps.append(verify_result)

            # Parsa il verdetto
            verification_passed = "VERDICT: PASS" in verify_result.output.upper()

            # ── STEP 4: REFINE (se verifica fallita) ─────────────
            if not verification_passed:
                self._stats["verification_failures"] += 1
                self._stats["refinements"] += 1

                # Estrai issues e suggestions dal verify output
                issues = self._extract_section(verify_result.output, "ISSUES:")
                suggestions = self._extract_section(verify_result.output, "SUGGESTIONS:")

                refine_system = REFINE_SYSTEM_TEMPLATE.format(
                    question=user_input[:1000],
                    answer=solve_result.output[:2000],
                    issues=issues,
                    suggestions=suggestions,
                )
                refine_result = await self._call_step(
                    step_name="refine",
                    step_number=4,
                    user_input="Correggi e migliora la risposta.",
                    system_prompt=refine_system,
                    ai_call_fn=ai_call_fn,
                    max_tokens=max_tokens_per_step,
                    temperature=temperature * 0.8,  # Leggermente più bassa per correzione
                )
                steps.append(refine_result)
                final_output = refine_result.output
                refined = True

        # ── Costruisci risultato finale ──
        total_tokens = sum(s.tokens_used for s in steps)
        total_ms = round((time.monotonic() - t0) * 1000, 1)
        avg_quality = sum(s.quality_estimate for s in steps) / len(steps)

        return ReasoningResult(
            final_output=final_output,
            steps=steps,
            total_tokens=total_tokens,
            total_latency_ms=total_ms,
            steps_executed=len(steps),
            verification_passed=verification_passed,
            refined=refined,
            quality_estimate=round(avg_quality, 3),
        )

    async def _single_step(
        self, user_input: str, ai_call_fn: AICallFn,
        max_tokens: int, temperature: float,
    ) -> ReasoningResult:
        """Esecuzione single-step (per task semplici)."""
        result = await self._call_step(
            step_name="direct",
            step_number=1,
            user_input=user_input,
            system_prompt="Rispondi con massima precisione e completezza.",
            ai_call_fn=ai_call_fn,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return ReasoningResult(
            final_output=result.output,
            steps=[result],
            total_tokens=result.tokens_used,
            total_latency_ms=result.latency_ms,
            steps_executed=1,
            verification_passed=True,
            refined=False,
            quality_estimate=result.quality_estimate,
        )

    async def _call_step(
        self,
        step_name: str,
        step_number: int,
        user_input: str,
        system_prompt: str,
        ai_call_fn: AICallFn,
        max_tokens: int,
        temperature: float,
    ) -> ReasoningStep:
        """Esegui un singolo step di reasoning (1 vera chiamata AI)."""
        t0 = time.monotonic()
        messages = [{"role": "user", "content": user_input}]

        try:
            result = await ai_call_fn(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            output = result.get("content", "")
            tokens = result.get("tokens", 0)
            provr = result.get("provr", "unknown")
            model = result.get("model", "unknown")
        except Exception as e:
            logger.error(f"[MultiStep.{step_name}] Errore: {e}")
            output = f"[Errore nello step {step_name}: {e}]"
            tokens = 0
            provr = "error"
            model = "error"

        latency = round((time.monotonic() - t0) * 1000, 1)

        # Stima qualità euristica
        quality = self._estimate_step_quality(output, step_name)

        return ReasoningStep(
            step_name=step_name,
            step_number=step_number,
            provr=provr,
            model=model,
            input_prompt=user_input[:200],
            output=output,
            tokens_used=tokens,
            latency_ms=latency,
            quality_estimate=quality,
        )

    def _estimate_step_quality(self, output: str, step_name: str) -> float:
        """Stima euristica della qualità di uno step."""
        if not output or output.startswith("[Errore"):
            return 0.0

        quality = 0.6  # baseline

        # Lunghezza ragionevole
        if 50 < len(output) < 5000:
            quality += 0.1

        # Step-specific
        if step_name == "analyze" and any(w in output.lower() for w in ["dominio", "domain", "sotto-domanda", "struttura"]):
            quality += 0.15
        elif step_name == "verify" and "VERDICT" in output.upper():
            quality += 0.15
        elif step_name in ("solve", "refine", "direct") and len(output) > 200:
            quality += 0.1

        return min(1.0, quality)

    def _extract_section(self, text: str, header: str) -> str:
        """Estrai sezione da testo strutturato."""
        lines = text.split("\n")
        capture = False
        result = []
        for line in lines:
            if header.upper() in line.upper():
                capture = True
                # Prendi il resto della riga dopo l'header
                rest = line.split(":", 1)[-1].strip()
                if rest:
                    result.append(rest)
                continue
            if capture:
                if line.strip().startswith(("VERDICT", "ISSUES", "SUGGESTIONS")) and line.strip() != header.strip():
                    break
                result.append(line)
        return "\n".join(result).strip() or "nessun dettaglio"

    def should_use_multistep(self, complexity: float, domain: str) -> bool:
        """Ritorna True se multi-step è raccomandato."""
        return complexity > self.MULTISTEP_THRESHOLD or domain in self.CRITICAL_DOMAINS

    def get_stats(self) -> Dict:
        return {
            "version": self.VERSION,
            **self._stats,
            "verification_failure_rate": round(
                self._stats["verification_failures"] / max(1, self._stats["verifications"]), 3
            ),
        }


# ─── Singleton ────────────────────────────────────────────────────────

_reasoner: Optional[MultiStepReasoner] = None

def get_multistep_reasoner() -> MultiStepReasoner:
    global _reasoner
    if _reasoner is None:
        _reasoner = MultiStepReasoner()
    return _reasoner
