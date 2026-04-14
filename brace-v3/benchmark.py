#!/usr/bin/env python3
"""
BRACE v3.0 — Performance Benchmark
Test all 5 scenarios with timing analysis
"""

import time

from brace_v3 import BRACE_v30, ImplicitProfile, WindowState
from scenarios_db import get_scenario, get_scenario_names


def benchmark():
    """Esegui benchmark completo"""
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║  🧪 BRACE v3.0 — Performance Benchmark                   ║")
    print("║  Testing All 5 Scenarios                                 ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    scenarios = get_scenario_names()
    total_turns = 0
    total_time = 0

    for scenario_name in scenarios:
        engine = BRACE_v30()
        scenario = get_scenario(scenario_name)

        state = {
            "phase": 1,
            "trust_score": 50.0,
            "history": [],
            "implicit_profile": ImplicitProfile(),
            "window_state": WindowState()
        }

        print(f"📊 Scenario: {scenario_name}")
        start_time = time.time()

        for input_text, context_type in scenario:
            output = engine.process(input_text, state)
            total_turns += 1

        elapsed = time.time() - start_time
        total_time += elapsed

        throughput = len(scenario) / elapsed if elapsed > 0 else 0
        print(f"   ├─ Turns: {len(scenario)}")
        print(f"   ├─ Time: {elapsed*1000:.2f}ms")
        print(f"   ├─ Throughput: {throughput:.0f} turns/sec")
        print(f"   └─ Final Trust Score: {engine.trust_score:.1f}\n")

    avg_throughput = total_turns / total_time if total_time > 0 else 0
    print("═" * 60)
    print("✅ Benchmark Complete")
    print(f"   Total Turns: {total_turns}")
    print(f"   Total Time: {total_time*1000:.2f}ms")
    print(f"   Avg Throughput: {avg_throughput:.0f} turns/sec\n")

if __name__ == "__main__":
    benchmark()
