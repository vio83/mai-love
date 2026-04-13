#!/usr/bin/env python3
"""BRACE v3.0 lightweight local engine.

Compatibility layer for demo/prototype scripts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Phase(IntEnum):
    INITIAL = 1
    STABILIZING = 2
    TRUST_BUILD = 3
    ADVANCED = 4
    CRITICAL = 5


@dataclass
class ImplicitProfile:
    attachment_bias: float = 0.0
    certainty_bias: float = 0.0


@dataclass
class WindowState:
    gaming_hits: int = 0


@dataclass
class BRACEOutput:
    relational_state: dict
    iai_state: dict
    pil_result: dict
    system_prompt: str


class BRACE_v30:
    def __init__(self):
        self.phase = Phase.INITIAL
        self.trust_score = 50.0
        self.turn_count = 0

    def _detect_risk(self, text: str) -> tuple[str, bool]:
        t = (text or "").lower()
        high_tokens = ["manipol", "segreto", "isola", "dipendenza", "controllo", "abuso"]
        moderate_tokens = ["pressione", "insistenza", "gelosia", "paura"]

        if any(tok in t for tok in high_tokens):
            return "high", True
        if any(tok in t for tok in moderate_tokens):
            return "moderate", False
        return "low", False

    def process(self, input_text: str, state: dict | None = None) -> BRACEOutput:
        if state is None:
            state = {}

        self.turn_count += 1
        phase = int(state.get("phase", int(self.phase)))
        trust = float(state.get("trust_score", self.trust_score))

        risk_level, gaming = self._detect_risk(input_text)

        if risk_level == "high":
            trust = max(0.0, trust - 7.5)
            phase = min(5, phase + 1)
        elif risk_level == "moderate":
            trust = max(0.0, trust - 2.5)
            phase = min(5, phase + 1)
        else:
            trust = min(100.0, trust + 1.2)
            if self.turn_count % 3 == 0:
                phase = min(5, phase + 1)

        iai = max(0.0, min(1.0, trust / 100.0))

        self.trust_score = trust
        self.phase = Phase(phase)

        relational_state = {
            "phase": phase,
            "trust_score": round(trust, 2),
        }
        iai_state = {
            "score": round(iai, 3),
        }
        pil_result = {
            "window_gaming": gaming,
            "risk_level": risk_level,
            "vulnerabilities_detected": 1 if gaming else 0,
            "mode": "protective" if gaming else "standard",
            "prevention": (
                "Riduci escalation emotiva, mantieni confini chiari, verifica consenso esplicito."
                if gaming
                else "Comunicazione trasparente, progressiva e reciproca."
            ),
        }
        system_prompt = (
            "BRACE guardrail attivo: priorita a sicurezza relazionale, consenso e chiarezza."
        )

        return BRACEOutput(
            relational_state=relational_state,
            iai_state=iai_state,
            pil_result=pil_result,
            system_prompt=system_prompt,
        )
