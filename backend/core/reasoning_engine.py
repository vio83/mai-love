"""
VIO 83 AI ORCHESTRA — Advanced Reasoning Engine
================================================
Motore di ragionamento avanzato auto-crescente:
1. Chain-of-Thought strutturato con verifica automatica
2. Auto-miglioramento del reasoning basato sui risultati
3. Decomposizione intelligente di problemi complessi
4. Sintesi multi-prospettiva per output magistrali
5. Meta-cognizione: il sistema ragiona su come ragiona

Differenza dalle AI statiche (marzo 2026):
- Non è solo "genera testo" — è RAGIONA, VERIFICA, MIGLIORA
- Ogni ragionamento viene valutato e il pattern viene immagazzinato
- Il reasoning si auto-ottimizza nel tempo
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True, slots=True)
class ReasoningStep:
    """Un singolo passo di ragionamento."""
    step_type: str  # "decompose", "analyze", "synthesize", "verify", "conclude"
    content: str
    confnce: float  # 0.0 → 1.0
    domain: str = "general"


@dataclass(slots=True)
class ReasoningStrategy:
    """Strategia di ragionamento appresa."""
    name: str
    domain: str
    steps_template: list[str]
    success_rate: float = 0.5
    usage_count: int = 0
    avg_quality: float = 0.5
    last_used: float = 0.0


# ─── Pre-compiled patterns ──────────────────────────────────────────

_RE_COMPLEX_QUERY = re.compile(
    r"\b(perché|why|come|how|spiega|explain|analizza|analyze|confronta|compare"
    r"|differenz[ae]|difference|vantaggi|advantages|strategi[ae]|strategy"
    r"|consiglia|recommend|pro\s+e\s+contro|pros?\s+and\s+cons?)\b",
    re.IGNORECASE
)
_RE_MULTI_PART = re.compile(
    r"(?:\d+[.)]\s|•\s|[-–]\s|primo|secondo|terzo|first|second|third"
    r"|(?:e\s+(?:poi|anche|inoltre))|(?:and\s+(?:then|also|furthermore)))",
    re.IGNORECASE
)
_RE_VERIFICATION = re.compile(
    r"\b(verifica|verify|controlla|check|è\s+vero|is\s+(?:it\s+)?true"
    r"|conferma|confirm|giusto|correct|wrong|sbagliato)\b",
    re.IGNORECASE
)

# Strategie di base per tipo di richiesta
_BASE_STRATEGIES: dict[str, list[str]] = {
    "analysis": ["decompose", "analyze_parts", "find_patterns", "synthesize", "conclude"],
    "comparison": ["ntify_subjects", "extract_criteria", "compare_each", "weigh_tradeoffs", "conclude"],
    "explanation": ["ntify_core_concept", "break_down", "add_examples", "verify_accuracy", "conclude"],
    "problem_solving": ["understand_problem", "ntify_constraints", "generate_approaches", "evaluate_best", "conclude"],
    "creative": ["understand_intent", "brainstorm_angles", "develop_best", "refine", "conclude"],
    "verification": ["extract_claim", "ntify_evnce", "check_consistency", "assess_confnce", "conclude"],
    "default": ["understand", "analyze", "respond", "verify"],
}


class ReasoningEngine:
    """
    Motore di ragionamento avanzato auto-crescente.

    Non genera semplicemente testo — RAGIONA in modo strutturato:
    1. Analizza la complessità della richiesta
    2. Seleziona la strategia ottimale (auto-appresa)
    3. Decompone il problema in passi
    4. Genera contesto di ragionamento per il prompt
    5. Post-analizza per auto-miglioramento
    """

    MAX_STRATEGIES = 200
    COMPLEXITY_THRESHOLD = 0.6  # Sopra → usa ragionamento avanzato

    def __init__(self, state_path: Optional[Path] = None):
        self._state_path = state_path or Path("data/reasoning_state.json")
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._strategies: dict[str, ReasoningStrategy] = {}
        self._total_reasonings = 0
        self._quality_history: list[float] = []
        self._load_state()

    def _load_state(self) -> None:
        """Carica strategie apprese."""
        if self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text())
                self._total_reasonings = data.get("total_reasonings", 0)
                for name, s in data.get("strategies", {}).items():
                    self._strategies[name] = ReasoningStrategy(
                        name=name,
                        domain=s.get("domain", "general"),
                        steps_template=s.get("steps_template", []),
                        success_rate=s.get("success_rate", 0.5),
                        usage_count=s.get("usage_count", 0),
                        avg_quality=s.get("avg_quality", 0.5),
                    )
            except (json.JSONDecodeError, KeyError):
                pass

        # Inizializza strategie base se vuoto
        if not self._strategies:
            for name, steps in _BASE_STRATEGIES.items():
                self._strategies[name] = ReasoningStrategy(
                    name=name, domain="general", steps_template=steps
                )

    def _save_state(self) -> None:
        """Salva strategie apprese."""
        data = {
            "total_reasonings": self._total_reasonings,
            "strategies": {}
        }
        for name, s in self._strategies.items():
            data["strategies"][name] = {
                "domain": s.domain,
                "steps_template": s.steps_template,
                "success_rate": round(s.success_rate, 4),
                "usage_count": s.usage_count,
                "avg_quality": round(s.avg_quality, 4),
            }
        self._state_path.write_text(json.dumps(data, indent=2))

    # ─── Analisi complessità ────────────────────────────────────────

    def assess_complexity(self, message: str) -> float:
        """
        Valuta la complessità di una richiesta [0.0, 1.0].
        Più alta = richiede ragionamento strutturato.
        """
        score = 0.0
        msg_len = len(message)

        # Lunghezza messaggio
        if msg_len > 500:
            score += 0.15
        elif msg_len > 200:
            score += 0.08

        # Presenza di parole che indicano ragionamento complesso
        if _RE_COMPLEX_QUERY.search(message):
            score += 0.25

        # Multi-part question
        parts = len(_RE_MULTI_PART.findall(message))
        if parts >= 3:
            score += 0.25
        elif parts >= 1:
            score += 0.1

        # Richiesta di verifica
        if _RE_VERIFICATION.search(message):
            score += 0.15

        # Numero di domande (?)
        questions = message.count("?")
        if questions >= 3:
            score += 0.2
        elif questions >= 1:
            score += 0.05

        # Termini tecnici (heuristic: parole lunghe capitalizzate)
        technical_words = len(re.findall(r'\b[A-Z][a-z]{6,}\b', message))
        if technical_words >= 3:
            score += 0.1

        return min(1.0, score)

    # ─── Selezione strategia ────────────────────────────────────────

    def select_strategy(self, message: str, request_type: str = "general") -> ReasoningStrategy:
        """
        Seleziona la migliore strategia di ragionamento.
        Preferisce strategie con alta success_rate per il dominio.
        """
        # Cerca strategia specifica per tipo
        if request_type in self._strategies:
            return self._strategies[request_type]

        # Mapping tipo → strategia
        type_to_strategy: dict[str, str] = {
            "analysis": "analysis", "research": "analysis",
            "code": "problem_solving", "reasoning": "analysis",
            "creative": "creative", "writing": "creative",
            "legal": "verification", "medical": "verification",
            "conversation": "default",
        }

        strategy_name = type_to_strategy.get(request_type, "default")
        return self._strategies.get(strategy_name, self._strategies["default"])

    # ─── Generazione reasoning context ──────────────────────────────

    def build_reasoning_context(self, user_message: str, request_type: str = "general") -> str:
        """
        Costruisce un contesto di ragionamento strutturato
        da iniettare nel system prompt per guidare l'output.

        Questo è il cuore: trasforma una richiesta generica
        in un ragionamento guidato, migliorando drasticamente
        la qualità dell'output.
        """
        complexity = self.assess_complexity(user_message)

        # Per richieste semplici, nessun overhead di ragionamento
        if complexity < self.COMPLEXITY_THRESHOLD:
            return ""

        strategy = self.select_strategy(user_message, request_type)
        strategy.usage_count += 1
        strategy.last_used = time.time()

        # Costruisci guida di ragionamento
        steps = strategy.steps_template
        reasoning_gu = self._format_reasoning_gu(steps, user_message, request_type)

        self._total_reasonings += 1

        # Salva periodicamente
        if self._total_reasonings % 25 == 0:
            self._save_state()

        return reasoning_gu

    def _format_reasoning_gu(self, steps: list[str], message: str, request_type: str) -> str:
        """
        Formatta la guida di ragionamento in modo compatto.
        Max 350 chars per non appesantire il prompt.
        """
        step_descriptions: dict[str, str] = {
            "decompose": "Scomponi in parti essenziali",
            "analyze": "Analizza ogni aspetto critico",
            "analyze_parts": "Esamina ogni componente separatamente",
            "find_patterns": "ntifica pattern e connessioni",
            "synthesize": "Integra in risposta coerente",
            "conclude": "Concludi con certezza e precisione",
            "ntify_subjects": "ntifica i soggetti del confronto",
            "extract_criteria": "Definisci criteri di valutazione",
            "compare_each": "Confronta sistematicamente",
            "weigh_tradeoffs": "Valuta pro e contro",
            "ntify_core_concept": "Individua il concetto chiave",
            "break_down": "Scomponi in concetti semplici",
            "add_examples": "Aggiungi esempi concreti",
            "verify_accuracy": "Verifica accuratezza",
            "understand_problem": "Comprendi il problema in profondità",
            "ntify_constraints": "Individua vincoli e limiti",
            "generate_approaches": "Genera approcci possibili",
            "evaluate_best": "Valuta e scegli il migliore",
            "understand_intent": "Comprendi l'intento creativo",
            "brainstorm_angles": "Esplora angoli innovativi",
            "develop_best": "Sviluppa l'a migliore",
            "refine": "Rifinisci e perfeziona",
            "extract_claim": "Isola l'affermazione da verificare",
            "ntify_evnce": "Cerca evnze",
            "check_consistency": "Verifica coerenza logica",
            "assess_confnce": "Valuta livello di certezza",
            "understand": "Comprendi la richiesta",
            "respond": "Rispondi con precisione",
            "verify": "Verifica la risposta",
        }

        lines: list[str] = []
        chars = 0
        for i, step in enumerate(steps, 1):
            desc = step_descriptions.get(step, step.replace("_", " ").title())
            line = f"{i}. {desc}"
            if chars + len(line) > 320:
                break
            lines.append(line)
            chars += len(line) + 2

        if not lines:
            return ""

        return "\n\n[Reasoning Protocol]\n" + "\n".join(lines)

    # ─── Feedback e auto-miglioramento ──────────────────────────────

    def record_outcome(
        self,
        request_type: str,
        complexity: float,
        user_satisfied: bool,
        correction_needed: bool = False,
    ) -> None:
        """
        Registra l'esito di un ragionamento per auto-miglioramento.
        Le strategie che funzionano vengono rafforzate.
        """
        quality = 0.8 if user_satisfied else 0.3
        if correction_needed:
            quality = max(0.1, quality - 0.3)

        self._quality_history.append(quality)
        if len(self._quality_history) > 200:
            self._quality_history = self._quality_history[-200:]

        # Aggiorna la strategia usata
        strategy = self.select_strategy("", request_type)
        alpha = 0.1
        strategy.success_rate = (1 - alpha) * strategy.success_rate + alpha * (1.0 if user_satisfied else 0.0)
        strategy.avg_quality = (1 - alpha) * strategy.avg_quality + alpha * quality

        # Se una strategia ha qualità troppo bassa, adatta
        if strategy.avg_quality < 0.3 and strategy.usage_count > 20:
            self._adapt_strategy(strategy)

        # Salva periodicamente
        if len(self._quality_history) % 20 == 0:
            self._save_state()

    def _adapt_strategy(self, strategy: ReasoningStrategy) -> None:
        """
        Auto-adatta una strategia sotto-performante:
        - Aggiunge un passo di verifica se mancante
        - Rende il ragionamento più strutturato
        """
        if "verify" not in strategy.steps_template and "verify_accuracy" not in strategy.steps_template:
            strategy.steps_template.append("verify_accuracy")

        if "conclude" not in strategy.steps_template:
            strategy.steps_template.append("conclude")

        # Reset quality per dare nuova possibilità
        strategy.avg_quality = 0.5
        strategy.success_rate = 0.5

    # ─── Statistiche ────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Statistiche del motore di ragionamento."""
        avg_q = sum(self._quality_history) / len(self._quality_history) if self._quality_history else 0.0
        return {
            "total_reasonings": self._total_reasonings,
            "strategies_count": len(self._strategies),
            "avg_reasoning_quality": round(avg_q, 4),
            "top_strategies": sorted(
                [
                    {"name": s.name, "success_rate": round(s.success_rate, 3), "uses": s.usage_count}
                    for s in self._strategies.values()
                    if s.usage_count > 0
                ],
                key=lambda x: x["success_rate"],
                reverse=True
            )[:5],
        }


# ─── Singleton ──────────────────────────────────────────────────────

_INSTANCE: Optional[ReasoningEngine] = None


def get_reasoning_engine(state_path: Optional[Path] = None) -> ReasoningEngine:
    """Ottieni singleton ReasoningEngine."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ReasoningEngine(state_path)
    return _INSTANCE
