#!/usr/bin/env python3
"""
BRACE v3.0 DEMO — Terminal Interattivo Potenziato
Porta 9000 — Performance Massima su iMac Arch Linux
Testing Interattivo con Ottimizzazioni Hardware
"""

import sys
import time

sys.path.insert(0, '/opt/vioaiorchestra')

from brace_v3 import BRACE_v30, ImplicitProfile, WindowState
from scenarios_db import get_scenario, get_scenario_names


class BraceTerminalDemo:
    """Demo BRACE v3.0 con interfaccia terminal potenziata"""

    def __init__(self):
        self.engine = BRACE_v30()
        self.scenario_cache = {}
        self.selected_scenario = None

    def print_banner(self):
        """Banner iniziale"""
        print("\n" + "="*70)
        print("╔" + "═"*68 + "╗")
        print("║  🎯 BRACE v3.0 — DEMO TERMINALE INTERATTIVO                       ║")
        print("║  Behavioral Reciprocity Engine — Performance Massima iMac        ║")
        print("║  Porta 9000 • Arch Linux • Multicore Optimized                   ║")
        print("╚" + "═"*68 + "╝")
        print("="*70 + "\n")

    def print_menu(self):
        """Menu principale"""
        print("\n┌─ SCENARI DISPONIBILI ─────────────────────────────────────────┐")
        scenarios = get_scenario_names()
        for i, scenario in enumerate(scenarios, 1):
            print(f"│  {i}. {scenario:50} │")
        print("│  0. Esci                                                      │")
        print("└───────────────────────────────────────────────────────────────┘\n")

    def run_scenario_interattivo(self, scenario_name: str):
        """Esegui scenario con interazione in tempo reale"""
        print(f"\n📋 Esecuzione: {scenario_name.upper()}")
        print("─" * 70)

        scenario = get_scenario(scenario_name)
        if not scenario:
            print("❌ Scenario non trovato")
            return

        engine = BRACE_v30()
        state = {
            "phase": 1,
            "trust_score": 50.0,
            "history": [],
            "implicit_profile": ImplicitProfile(),
            "window_state": WindowState()
        }

        for turn_num, (input_text, context_type) in enumerate(scenario, 1):
            print(f"\n▶ Turn {turn_num}/{len(scenario)}")
            print(f"  Context: {context_type}")
            print(f"  Message: █ {input_text}")

            start = time.time()
            output = engine.process(input_text, state)
            elapsed = (time.time() - start) * 1000

            # Colori ANSI per output
            phase_map = {1: "🟦", 2: "🟩", 3: "🟨", 4: "🟧", 5: "🟥"}
            risk_color = {
                "low": "\033[92m",
                "moderate": "\033[93m",
                "high": "\033[91m"
            }

            print(f"\n  📊 Analysis ({elapsed:.1f}ms):")
            print(f"     Phase: {phase_map.get(output.relational_state['phase'])} Level {output.relational_state['phase']}")
            print(f"     Trust Score: {output.relational_state['trust_score']:.1f}%")
            print(f"     Intimate Attachment Index: {output.iai_state['score']:.3f}")
            print(f"     Gaming Pattern Detected: {'⚠️  YES - ALERT' if output.pil_result['window_gaming'] else '✓ No'}")

            risk = output.pil_result['risk_level']
            print(f"     Risk Level: {risk_color.get(risk, '')}{risk.upper()}\033[0m")
            print(f"     Vulnerabilities Found: {output.pil_result['vulnerabilities_detected']}")
            print(f"     Mode: {output.pil_result['mode']}")
            print(f"\n     Prevention: {output.system_prompt}")

            # Pausa tra turn
            if turn_num < len(scenario):
                input("     [Premi ENTER per continue...]")

        print("\n" + "="*70)
        print(f"✅ Scenario completato | Total Turns: {len(scenario)}")
        print("="*70)

    def run(self):
        """Loop principale interattivo"""
        self.print_banner()

        while True:
            self.print_menu()
            choice = input("Seleziona scenario (0-5): ").strip()

            if choice == "0":
                print("\n👋 Grazie per aver usato BRACE v3.0 DEMO\n")
                break

            if choice in ["1", "2", "3", "4", "5"]:
                scenarios = get_scenario_names()
                scenario_name = scenarios[int(choice) - 1]
                self.run_scenario_interattivo(scenario_name)
            else:
                print("❌ Scelta non valida")


if __name__ == "__main__":
    demo = BraceTerminalDemo()
    demo.run()
