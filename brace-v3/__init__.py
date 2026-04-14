#!/usr/bin/env python3
"""
BRACE v3.0 Package Init
Behavioral Reciprocity Engine Core
"""

from .brace_v3 import BRACE_v30, ImplicitProfile, OutputState, RelationalPhase, SpecializationMode, WindowState
from .scenarios_db import SCENARIOS, get_scenario, get_scenario_names, get_scenario_turns

__version__ = "3.0"
__author__ = "VIO AI Orchestra"
__all__ = [
    "BRACE_v30",
    "ImplicitProfile",
    "WindowState",
    "OutputState",
    "RelationalPhase",
    "SpecializationMode",
    "SCENARIOS",
    "get_scenario",
    "get_scenario_names",
    "get_scenario_turns"
]
