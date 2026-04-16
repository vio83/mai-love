#!/usr/bin/env python3
"""
GIU-L_IA v3.0 — Algorithm Demo
7-turn demonstration showing core capabilities
"""

from brace_v3 import GIU_L_IA, ImplicitProfile, WindowState
from scenarios_db import get_scenario


def run_demo():
    """Esegui demo GIU-L_IA"""
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║  🎯 GIU-L_IA v3.0 — Algorithm Demonstration              ║")
    print("║  7-Turn Analysis with Pattern Detection                 ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    # Inizializza engine
    engine = GIU_L_IA()

    # Recupera scenario giu_risk_boundaries (pattern a rischio)
    scenario = get_scenario("giu_risk_boundaries")
    if scenario is None:
        print("❌ Scenario 'giu_risk_boundaries' non trovato in scenarios_db")
        return

    # Simula stato
    state = {
        "phase": 1,
        "trust_score": 50.0,
        "history": [],
        "implicit_profile": ImplicitProfile(),
        "window_state": WindowState()
    }

    print("📋 SCENARIO: Risk Boundaries (Pattern Detection)\n")

    for turn_num, (input_text, context_type) in enumerate(scenario[:7], 1):
        print(f"─ Turn {turn_num} ({context_type}):")
        print(f"   💬 Input: {input_text}")

        # Process input
        output = engine.process(input_text, state)

        # Print results
        print(f"   ├─ Phase: {output.relational_state['phase']}")
        print(f"   ├─ Trust Score: {output.relational_state['trust_score']:.1f}")
        print(f"   ├─ IAI Score: {output.iai_state['score']:.3f}")
        print(f"   ├─ Gaming Detected: {output.pil_result['window_gaming']}")
        print(f"   ├─ Risk Level: {output.pil_result['risk_level']}")
        print(f"   └─ Prevention: {output.system_prompt}\n")

    print("═" * 60)
    print(f"✅ Demo completed. {engine.turn_count} turns analyzed.\n")

if __name__ == "__main__":
    run_demo()
