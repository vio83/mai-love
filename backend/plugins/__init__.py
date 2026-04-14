# VIO 83 AI ORCHESTRA — Plugin / MCP System
# Copyright (c) 2026 Viorica Porcu. AGPL-3.0 / Proprietaria
"""
Plugin registry per VIO 83 AI Orchestra.
Supporta plugin locali (built-in) e plugin esterni (futuri MCP server).
"""
from .registry import PluginInfo, PluginRegistry, PluginStatus

__all__ = ["PluginRegistry", "PluginInfo", "PluginStatus"]
