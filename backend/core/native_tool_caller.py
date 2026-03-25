# ============================================================
# VIO 83 AI ORCHESTRA — NativeToolCaller™
# Copyright © 2026 Viorica Porcu (vio83) — All rights reserved
# ============================================================
"""
NativeToolCaller™ v1.0 — Tool Calling Nativo per Claude/OpenAI/Ollama
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sostituisce il parsing XML regex-based di OpenClaw con chiamate
NATIVE ai formati di tool calling di ogni provider.

Strategia per provider:
  Claude API  → content block "tool_use" (nativo, 99.9% affidabile)
  OpenAI API  → function_call / tool_calls (nativo, 99.9% affidabile)
  Ollama      → XML fallback (locale, nessun formato nativo)
  Gemini      → functionCall (nativo)

Questo modulo:
1. Converte tool definitions in formato nativo per ogni provider
2. Parsa le risposte tool_use native (non regex su testo libero)
3. Gestisce loop tool call → tool result → risposta finale
4. Fallback XML solo per Ollama (unico caso necessario)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger("native_tool_caller")


# ─── Dataclasses ──────────────────────────────────────────────────────

@dataclass
class ToolDefinition:
    """Definizione universale di un tool (provider-agnostic)."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema

    def to_claude_format(self) -> Dict:
        """Converte in formato Claude API (Anthropic)."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def to_openai_format(self) -> Dict:
        """Converte in formato OpenAI API."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def to_gemini_format(self) -> Dict:
        """Converte in formato Google Gemini API."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    def to_ollama_xml(self) -> str:
        """Converte in formato XML per Ollama (fallback)."""
        params_desc = json.dumps(self.parameters, indent=2)
        return (
            f"<tool name=\"{self.name}\">\n"
            f"  <description>{self.description}</description>\n"
            f"  <parameters>{params_desc}</parameters>\n"
            f"</tool>"
        )


@dataclass
class ToolCall:
    """Risultato di un tool call parsato."""
    tool_name: str
    tool_input: Dict[str, Any]
    call_id: str = ""  # ID della chiamata (per Claude/OpenAI)


@dataclass
class ToolResult:
    """Risultato dell'esecuzione di un tool."""
    call_id: str
    tool_name: str
    output: Any
    is_error: bool = False


# ─── Provider-Specific Parsers ────────────────────────────────────────

class ClaudeToolParser:
    """Parser per risposte Claude API con tool_use nativo."""

    @staticmethod
    def extract_tool_calls(response: Dict) -> List[ToolCall]:
        """
        Estrae tool calls dalla risposta Claude API.

        Formato Claude:
        {
            "content": [
                {"type": "text", "text": "..."},
                {"type": "tool_use", "id": "toolu_xxx", "name": "tool_name", "input": {...}}
            ]
        }
        """
        calls = []
        content = response.get("content", [])
        if isinstance(content, str):
            return calls  # Nessun tool use in testo puro

        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                calls.append(ToolCall(
                    tool_name=block.get("name", ""),
                    tool_input=block.get("input", {}),
                    call_id=block.get("id", ""),
                ))
        return calls

    @staticmethod
    def format_tool_result(result: ToolResult) -> Dict:
        """Formatta il risultato per rimandarlo a Claude."""
        return {
            "type": "tool_result",
            "tool_use_id": result.call_id,
            "content": json.dumps(result.output) if not isinstance(result.output, str) else result.output,
            "is_error": result.is_error,
        }


class OpenAIToolParser:
    """Parser per risposte OpenAI API con function/tool calling nativo."""

    @staticmethod
    def extract_tool_calls(response: Dict) -> List[ToolCall]:
        """
        Estrae tool calls dalla risposta OpenAI API.

        Formato OpenAI:
        {
            "choices": [{
                "message": {
                    "tool_calls": [
                        {"id": "call_xxx", "type": "function",
                         "function": {"name": "...", "arguments": "{...}"}}
                    ]
                }
            }]
        }
        """
        calls = []
        choices = response.get("choices", [])
        if not choices:
            return calls

        message = choices[0].get("message", {})
        tool_calls = message.get("tool_calls", [])

        for tc in tool_calls:
            if tc.get("type") == "function":
                func = tc.get("function", {})
                try:
                    args = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                calls.append(ToolCall(
                    tool_name=func.get("name", ""),
                    tool_input=args,
                    call_id=tc.get("id", ""),
                ))
        return calls

    @staticmethod
    def format_tool_result(result: ToolResult) -> Dict:
        """Formatta il risultato per rimandarlo a OpenAI."""
        return {
            "role": "tool",
            "tool_call_id": result.call_id,
            "content": json.dumps(result.output) if not isinstance(result.output, str) else result.output,
        }


class OllamaToolParser:
    """Parser XML fallback per Ollama (nessun tool calling nativo)."""

    _TOOL_CALL_RE = re.compile(
        r'<tool_call>\s*(\{.*?\})\s*</tool_call>',
        re.DOTALL,
    )

    @staticmethod
    def extract_tool_calls(response_text: str) -> List[ToolCall]:
        """
        Estrae tool calls dal testo di risposta Ollama (XML embedded).
        Questo è il FALLBACK — usato solo per Ollama che non ha formato nativo.
        """
        calls = []
        for match in OllamaToolParser._TOOL_CALL_RE.finditer(response_text):
            try:
                data = json.loads(match.group(1))
                calls.append(ToolCall(
                    tool_name=data.get("tool", data.get("name", "")),
                    tool_input=data.get("params", data.get("input", data.get("arguments", {}))),
                    call_id=f"ollama_{len(calls)}",
                ))
            except json.JSONDecodeError:
                logger.debug(f"[OllamaToolParser] JSON malformato: {match.group(1)[:100]}")
        return calls

    @staticmethod
    def build_tool_prompt(tools: List[ToolDefinition]) -> str:
        """Costruisce il prompt con catalogo tool per Ollama."""
        if not tools:
            return ""
        tool_xml = "\n".join(t.to_ollama_xml() for t in tools)
        return (
            "\n\n<available_tools>\n"
            f"{tool_xml}\n"
            "</available_tools>\n\n"
            "Per usare un tool, rispondi con:\n"
            '<tool_call>{"tool": "nome_tool", "params": {"param1": "valore1"}}</tool_call>\n'
        )


# ─── NativeToolCaller™ — Entry Point ─────────────────────────────────

class NativeToolCaller:
    """
    NativeToolCaller™ — Tool calling con formato nativo per ogni provider.

    Usage:
        ntc = NativeToolCaller()

        # Registra tools
        ntc.register_tool(ToolDefinition(
            name="web_search",
            description="Cerca nel web",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        ))

        # Per Claude API
        tools_claude = ntc.get_tools_for_provr("claude")
        # Passa tools_claude nella chiamata API Anthropic come parametro "tools"

        # Parsa risposta
        tool_calls = ntc.parse_response(response, provider="claude")
        for tc in tool_calls:
            result = execute_tool(tc.tool_name, tc.tool_input)
            formatted = ntc.format_result(ToolResult(...), provider="claude")
    """

    VERSION = "1.0.0"

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._claude_parser = ClaudeToolParser()
        self._openai_parser = OpenAIToolParser()
        self._ollama_parser = OllamaToolParser()

    def register_tool(self, tool: ToolDefinition):
        """Registra un tool disponibile."""
        self._tools[tool.name] = tool

    def register_tools(self, tools: List[ToolDefinition]):
        """Registra multipli tools."""
        for t in tools:
            self._tools[t.name] = t

    def get_tools_for_provr(self, provider: str) -> Any:
        """
        Ritorna le definizioni tool nel formato nativo del provider.

        Args:
            provider: "claude" | "openai" | "gemini" | "ollama"

        Returns:
            - Claude: List[Dict] per parametro "tools"
            - OpenAI: List[Dict] per parametro "tools"
            - Gemini: Dict per parametro "tools"
            - Ollama: str (prompt addendum con XML)
        """
        tools_list = list(self._tools.values())

        if provider in ("claude", "anthropic"):
            return [t.to_claude_format() for t in tools_list]

        elif provider in ("openai", "gpt"):
            return [t.to_openai_format() for t in tools_list]

        elif provider in ("gemini", "google"):
            return {
                "function_declarations": [t.to_gemini_format() for t in tools_list]
            }

        elif provider in ("ollama", "local"):
            return OllamaToolParser.build_tool_prompt(tools_list)

        else:
            # Default: OpenAI format (più diffuso)
            return [t.to_openai_format() for t in tools_list]

    def parse_response(self, response: Any, provider: str) -> List[ToolCall]:
        """
        Parsa la risposta AI ed estrae tool calls nel formato nativo.

        Args:
            response: risposta dal provider (Dict per Claude/OpenAI, str per Ollama)
            provider: "claude" | "openai" | "ollama"
        """
        if provider in ("claude", "anthropic"):
            return self._claude_parser.extract_tool_calls(response)
        elif provider in ("openai", "gpt"):
            return self._openai_parser.extract_tool_calls(response)
        elif provider in ("ollama", "local"):
            text = response if isinstance(response, str) else str(response)
            return self._ollama_parser.extract_tool_calls(text)
        else:
            # Prova tutti i parser
            if isinstance(response, dict):
                calls = self._claude_parser.extract_tool_calls(response)
                if calls:
                    return calls
                calls = self._openai_parser.extract_tool_calls(response)
                if calls:
                    return calls
            if isinstance(response, str):
                return self._ollama_parser.extract_tool_calls(response)
            return []

    def format_result(self, result: ToolResult, provider: str) -> Any:
        """
        Formatta il risultato tool nel formato nativo del provider.
        """
        if provider in ("claude", "anthropic"):
            return self._claude_parser.format_tool_result(result)
        elif provider in ("openai", "gpt"):
            return self._openai_parser.format_tool_result(result)
        else:
            # Per Ollama/altri: testo semplice
            return f"[Tool Result: {result.tool_name}]\n{json.dumps(result.output, indent=2)}"

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_stats(self) -> Dict:
        return {
            "version": self.VERSION,
            "registered_tools": len(self._tools),
            "tool_names": self.list_tools(),
        }


# ─── Singleton ────────────────────────────────────────────────────────

_caller: Optional[NativeToolCaller] = None

def get_native_tool_caller() -> NativeToolCaller:
    global _caller
    if _caller is None:
        _caller = NativeToolCaller()
    return _caller
