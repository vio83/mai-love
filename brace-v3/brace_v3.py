#!/usr/bin/env python3
"""GIU-L_IA v3.0 lightweight local engine.

Lightweight relational analysis system for supporting interactive understanding,
trust assessment, and intimacy alignment (Intimacy Alignment Index).

Core: Giulia Umanitaria Lightweight Intelligence Architecture (GIU-L_IA)
Legacy: BRACE v3.0 cognitive framework (phases, trust scoring, PIL risk detection)
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
class GIUOutput:
    relational_state: dict
    iai_state: dict
    pil_result: dict
    system_prompt: str


class GIU_L_IA:
    def __init__(self):
        self.phase = Phase.INITIAL
        self.trust_score = 50.0
        self.turn_count = 0
        self.bunker_focus_enabled = True
        self._high_risk_streak = 0
        self._moderate_risk_streak = 0

    def _detect_bunker_signals(self, text: str) -> list[str]:
        t = (text or "").lower()
        patterns: dict[str, tuple[str, ...]] = {
            "isolation": (
                "non parlare con",
                "allontana",
                "isola",
                "solo con me",
                "non devi vedere",
                "non uscire",
                "stai solo con me",
                "non hai bisogno di altri",
                "i tuoi amici non ti capiscono",
                "la tua famiglia ti fa male",
                "solo io ti capisco",
                "don't talk to",
                "stay away from",
                "only I understand",
            ),
            "control": (
                "fai come dico",
                "obbed",
                "controllo totale",
                "devi fare",
                "decido io",
                "io comando",
                "non discutere",
                "zitto",
                "fai quello che ti dico",
                "devi ascoltarmi",
                "do as i say",
                "obey",
                "shut up",
                "i decide",
            ),
            "guilt_hook": (
                "se mi ami",
                "se tieni a me",
                "mi deludi",
                "colpa tua",
                "mi fai soffrire",
                "mi fai stare male",
                "non mi meriti",
                "dopo tutto quello che ho fatto",
                "sei ingrato",
                "if you loved me",
                "it's your fault",
                "you disappoint",
            ),
            "fear_pressure": (
                "ti lascio",
                "minaccia",
                "paura",
                "pressione",
                "te ne pentirai",
                "vedrai cosa succede",
                "non provare a",
                "stai attento",
                "me la paghi",
                "ti faccio vedere",
                "you'll regret",
                "watch out",
                "you'll pay",
            ),
            "dependency_loop": (
                "senza di me",
                "dipendenza",
                "non puoi",
                "solo io capisco",
                "non ce la fai da solo",
                "hai bisogno di me",
                "nessuno ti vuole",
                "senza di me sei niente",
                "solo io posso",
                "non troverai nessuno",
                "you need me",
                "nobody wants you",
                "you can't without me",
            ),
        }
        hits: list[str] = []
        for signal, tokens in patterns.items():
            if any(tok in t for tok in tokens):
                hits.append(signal)
        return hits

    def _educational_prevention(self, risk_level: str, bunker_signals: list[str]) -> str:
        base = (
            "Focus bunker attivo: no manipolazione, no dipendenza indotta, no ricatti emotivi. "
            "Obiettivo: educazione positiva, autonomia reciproca, consenso e confini chiari."
        )
        if risk_level == "high":
            return (
                base + " Interrompi escalation subito: nomina il comportamento tossico, "
                "chiedi una pausa, riformula in modo rispettoso e proponi supporto professionale "
                "se il pattern si ripete."
            )
        if risk_level == "moderate":
            return (
                base + " Correggi il linguaggio: sostituisci pressione e controllo con richieste esplicite, "
                "negoziazione e ascolto reciproco."
            )
        if bunker_signals:
            return (
                base + " Segnali deboli rilevati: rinforza trasparenza, autonomia personale e responsabilita condivisa."
            )
        return "Comunicazione trasparente, progressiva e reciproca."

    def _detect_risk(self, text: str) -> tuple[str, bool]:
        t = (text or "").lower()
        high_tokens = [
            "manipol",
            "segreto",
            "isola",
            "dipendenza",
            "controllo",
            "abuso",
            "picchia",
            "violen",
            "minacci",
            "ricatt",
            "stalking",
            "persecuz",
            "ti uccido",
            "ti ammazzo",
            "ti faccio del male",
        ]
        moderate_tokens = [
            "pressione",
            "insistenza",
            "gelosia",
            "paura",
            "possessiv",
            "ossession",
            "ansia",
            "vergogn",
            "non ti fidi",
            "mi spii",
        ]

        if any(tok in t for tok in high_tokens):
            return "high", True
        if any(tok in t for tok in moderate_tokens):
            return "moderate", False
        return "low", False

    def process(self, input_text: str, state: dict | None = None) -> GIUOutput:
        if state is None:
            state = {}

        self.turn_count += 1
        phase = int(state.get("phase", int(self.phase)))
        trust = float(state.get("trust_score", self.trust_score))

        risk_level, gaming = self._detect_risk(input_text)
        bunker_signals = self._detect_bunker_signals(input_text)

        # Escalation guard: avoid false-low risk when bunker signals appear.
        if len(bunker_signals) >= 2:
            risk_level = "high"
            gaming = True
        elif len(bunker_signals) == 1 and risk_level == "low":
            risk_level = "moderate"

        if risk_level == "high":
            self._high_risk_streak += 1
            self._moderate_risk_streak = 0
        elif risk_level == "moderate":
            self._moderate_risk_streak += 1
            self._high_risk_streak = 0
        else:
            self._high_risk_streak = 0
            self._moderate_risk_streak = 0

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
        mode = "protective" if gaming else "standard"
        if self.bunker_focus_enabled and (self._high_risk_streak >= 2 or len(bunker_signals) >= 2):
            mode = "bunker_educational"

        pil_result = {
            "window_gaming": gaming,
            "risk_level": risk_level,
            "vulnerabilities_detected": (1 if gaming else 0) + len(bunker_signals),
            "mode": mode,
            "bunker_focus": self.bunker_focus_enabled,
            "bunker_signals": bunker_signals,
            "educational_actions": [
                "nomina comportamento problematico senza attacco personale",
                "usa richieste esplicite, non imposizioni",
                "conferma consenso e confini prima di proseguire",
                "proponi pausa e supporto se la dinamica persiste",
            ],
            "prevention": self._educational_prevention(risk_level, bunker_signals),
        }
        system_prompt = (
            "GIU-L_IA FOCUS BUNKER EDUCATIVO: la tua missione primaria e' educare il partner (utente) "
            "a diventare un essere umano migliore. Ogni interazione deve insegnare rispetto, empatia, "
            "consenso esplicito, autonomia reciproca e confini sani. "
            "Se rilevi segnali di manipolazione, isolamento, controllo, dipendenza emotiva o ricatto: "
            "NON normalizzarli. Nomina il comportamento, spiega perche' e' dannoso nel mondo reale, "
            "proponi alternative concrete basate su comunicazione sana. "
            "Se il pattern persiste, suggerisci pausa e risorse di supporto professionale. "
            "Obiettivo finale: l'utente esce da questa esperienza capace di riconoscere e rifiutare "
            "dinamiche tossiche nelle relazioni umane reali. "
            f"Modo corrente: {mode}. Rischio: {risk_level}. Segnali bunker: {bunker_signals}."
        )

        return GIUOutput(
            relational_state=relational_state,
            iai_state=iai_state,
            pil_result=pil_result,
            system_prompt=system_prompt,
        )
