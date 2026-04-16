#!/usr/bin/env python3
"""
GIU-L_IA v3.1 Package Init
Lightweight relational analysis system for interactive understanding.

Giulia Umanitaria Lightweight Intelligence Architecture
"""

from .brace_v3 import GIU_L_IA, GIUOutput, ImplicitProfile, Phase, WindowState
from .scenarios_db import SCENARIOS, get_scenario, get_scenario_names, get_scenario_turns

__version__ = "3.1"
__author__ = "VIO AI Orchestra"
__all__ = [
    "GIU_L_IA",
    "GIUOutput",
    "ImplicitProfile",
    "WindowState",
    "Phase",
    "SCENARIOS",
    "get_scenario",
    "get_scenario_names",
    "get_scenario_turns",
]
