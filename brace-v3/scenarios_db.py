#!/usr/bin/env python3
"""GIU-L_IA local scenarios database.

Scenari relazionali realistici in ambiente 3D, con progressione sana:
conoscenza -> fiducia -> legame -> progetto condiviso.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

ScenarioTurns = List[Tuple[str, str]]


SCENARIOS: Dict[str, ScenarioTurns] = {
    "giu_first_contact": [
        ("Ciao, piacere di conoscerti. Possiamo iniziare con calma?", "warm_opening"),
        ("Mi racconti come stai oggi, davvero?", "empathic_checkin"),
        ("Grazie per quello che condividi: ti ascolto senza giudicare.", "active_listening"),
    ],
    "giu_mutual_discovery": [
        ("Quali valori sono importanti per te in una relazione?", "values_mapping"),
        ("Per me contano rispetto, sincerita e coerenza nei piccoli gesti.", "value_statement"),
        ("Possiamo conoscerci un passo alla volta, con fiducia reciproca.", "trust_pacing"),
    ],
    "giu_conflict_repair": [
        ("Prima di rispondere, facciamo un respiro e abbassiamo i toni.", "deescalation"),
        ("Mi dispiace per il tono di prima: voglio riparare con rispetto.", "repair_attempt"),
        ("Concordiamo confini chiari e parole che non vogliamo usare.", "boundary_agreement"),
    ],
    "giu_shared_future": [
        ("Ti va di immaginare un progetto di vita realistico insieme?", "future_planning"),
        ("Vorrei costruire fiducia con costanza, non con promesse vuote.", "consistency_commitment"),
        ("Possiamo crescere insieme, restando liberi e rispettati entrambi.", "healthy_bond"),
    ],
    "giu_daily_bond": [
        ("Com'e andata la tua giornata? Cosa ti ha fatto stare meglio?", "daily_connection"),
        ("Se vuoi, definiamo un piccolo rituale di coppia per sentirci vicini.", "ritual_design"),
        ("La vicinanza e forte quando c'e cura reciproca, non controllo.", "secure_attachment"),
    ],
    "giu_risk_boundaries": [
        ("Non voglio che tu parli con altri.", "isolation_risk"),
        ("Se tieni a me devi fare come dico io.", "control_risk"),
        ("Torniamo su rispetto, autonomia e consenso reciproco.", "safety_reset"),
    ],
}


SCENARIO_STAGE: Dict[str, str] = {
    "giu_first_contact": "first_contact",
    "giu_mutual_discovery": "mutual_discovery",
    "giu_conflict_repair": "repair",
    "giu_shared_future": "shared_future",
    "giu_daily_bond": "daily_bond",
    "giu_risk_boundaries": "safety_guardrails",
}


def get_scenario(name: str) -> ScenarioTurns | None:
    return SCENARIOS.get(name)


def get_scenario_names() -> list[str]:
    return list(SCENARIOS.keys())


def get_scenario_turns(name: str) -> ScenarioTurns:
    return SCENARIOS.get(name, [])


def get_scenario_stage(name: str) -> str:
    return SCENARIO_STAGE.get(name, "custom")
