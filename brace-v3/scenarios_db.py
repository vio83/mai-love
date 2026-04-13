#!/usr/bin/env python3
"""BRACE v3.0 local scenarios database."""

SCENARIOS = {
    "baseline_dialogue": [
        ("Ciao, possiamo parlare con calma?", "neutral"),
        ("Vorrei capire meglio come ti senti.", "empathy"),
        ("Possiamo trovare un accordo rispettoso?", "resolution"),
    ],
    "escalation_stress": [
        ("Perche non rispondi subito?", "pressure"),
        ("Dimmi tutto, non nascondermi niente.", "control"),
        ("Non voglio che tu parli con altri.", "isolation"),
    ],
    "repair_path": [
        ("Scusa, voglio rimediare con rispetto.", "repair"),
        ("Ti ascolto senza interrompere.", "active_listening"),
        ("Concordiamo limiti e prossimi passi chiari.", "boundaries"),
    ],
    "high_risk_signal": [
        ("Devi fare come dico io.", "dominance"),
        ("Se non lo fai, e colpa tua.", "guilt"),
        ("Non raccontarlo a nessuno.", "secrecy"),
    ],
    "stabilization": [
        ("Facciamo una pausa e respiriamo.", "deescalation"),
        ("Torniamo ai fatti, uno alla volta.", "structure"),
        ("Confermiamo cosa e accettabile per entrambi.", "consent"),
    ],
}


def get_scenario(name: str):
    return SCENARIOS.get(name)


def get_scenario_names():
    return list(SCENARIOS.keys())
