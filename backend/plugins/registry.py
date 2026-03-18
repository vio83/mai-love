# VIO 83 AI ORCHESTRA — Plugin Registry
# Copyright (c) 2026 Viorica Porcu. AGPL-3.0 / Proprietaria
"""
Registry dei plugin per VIO 83 AI Orchestra.

Ogni plugin espone:
- metadata (name, version, description, author, icon)
- tools: lista di funzioni chiamabili
- execute(tool_name, params) -> result

Built-in plugins:
  vio.filesystem  — legge/scrive file sul Mac (path whitelist)
  vio.clipboard   — legge/scrive clipboard
  vio.websearch   — ricerca web via DuckDuckGo (no API key)
  vio.datetime    — ora/data/timezone
  vio.calculator  — calcoli matematici sicuri
  vio.memory      — note persistenti cross-session
"""
from __future__ import annotations
import json
import math
import datetime
import os
import subprocess
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class PluginStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginTool:
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema style
    examples: List[str] = field(default_factory=list)


@dataclass
class PluginInfo:
    id: str
    name: str
    version: str
    description: str
    author: str
    icon: str
    status: PluginStatus
    tools: List[PluginTool]
    built_in: bool = True

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


class PluginRegistry:
    """Registry centrale di tutti i plugin installati."""

    def __init__(self):
        self._plugins: Dict[str, "BasePlugin"] = {}
        self._register_built_ins()

    def _register_built_ins(self):
        self.register(FilesystemPlugin())
        self.register(ClipboardPlugin())
        self.register(WebSearchPlugin())
        self.register(DateTimePlugin())
        self.register(CalculatorPlugin())
        self.register(MemoryPlugin())

    def register(self, plugin: "BasePlugin"):
        self._plugins[plugin.info.id] = plugin

    def list_plugins(self) -> List[dict]:
        return [p.info.to_dict() for p in self._plugins.values()]

    def get_plugin(self, plugin_id: str) -> Optional["BasePlugin"]:
        return self._plugins.get(plugin_id)

    def execute(self, plugin_id: str, tool_name: str, params: dict) -> dict:
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return {"error": f"Plugin '{plugin_id}' not found"}
        if plugin.info.status != PluginStatus.ACTIVE:
            return {"error": f"Plugin '{plugin_id}' is {plugin.info.status}"}
        return plugin.execute(tool_name, params)

    def get_tools_for_prompt(self) -> str:
        """Returns a formatted string of all available tools for AI context."""
        lines = ["# Available Tools\n"]
        for plugin in self._plugins.values():
            if plugin.info.status != PluginStatus.ACTIVE:
                continue
            lines.append(f"## Plugin: {plugin.info.name} ({plugin.info.id})")
            for tool in plugin.info.tools:
                lines.append(f"  - {tool.name}: {tool.description}")
        return "\n".join(lines)


class BasePlugin:
    info: PluginInfo

    def execute(self, tool_name: str, params: dict) -> dict:
        handler = getattr(self, f"_tool_{tool_name}", None)
        if not handler:
            return {"error": f"Tool '{tool_name}' not found in plugin '{self.info.id}'"}
        try:
            return handler(**params)
        except Exception as e:
            return {"error": str(e)}


# ─── PLUGIN: FILESYSTEM ───────────────────────────────────────────────────────

class FilesystemPlugin(BasePlugin):
    # Whitelist di cartelle sicure (HOME e project)
    SAFE_ROOTS = [
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.home() / "Downloads",
        Path.home() / "Projects",
    ]

    def __init__(self):
        self.info = PluginInfo(
            id="vio.filesystem",
            name="File System",
            version="1.0.0",
            description="Leggi e scrivi file sul Mac (cartelle sicure: Desktop, Documents, Downloads, Projects)",
            author="Viorica Porcu",
            icon="📁",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("read_file", "Legge il contenuto di un file",
                           {"path": {"type": "string", "description": "Path assoluto del file"}},
                           ["read_file(path='/Users/x/Desktop/note.txt')"]),
                PluginTool("write_file", "Scrive contenuto in un file",
                           {"path": {"type": "string"}, "content": {"type": "string"}},
                           ["write_file(path='/Users/x/Desktop/out.txt', content='Hello')"]),
                PluginTool("list_dir", "Lista i file in una cartella",
                           {"path": {"type": "string"}},
                           ["list_dir(path='/Users/x/Desktop')"]),
            ],
        )

    def _is_safe(self, path: str) -> bool:
        p = Path(path).resolve()
        return any(str(p).startswith(str(root)) for root in self.SAFE_ROOTS)

    def _tool_read_file(self, path: str) -> dict:
        if not self._is_safe(path):
            return {"error": f"Path non autorizzato: {path}. Usa Desktop, Documents, Downloads, o Projects."}
        p = Path(path)
        if not p.exists():
            return {"error": f"File non trovato: {path}"}
        if p.stat().st_size > 1_000_000:  # 1MB max
            return {"error": "File troppo grande (max 1MB)"}
        return {"content": p.read_text(errors="replace"), "size": p.stat().st_size, "path": path}

    def _tool_write_file(self, path: str, content: str) -> dict:
        if not self._is_safe(path):
            return {"error": f"Path non autorizzato: {path}"}
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return {"success": True, "path": path, "bytes_written": len(content.encode())}

    def _tool_list_dir(self, path: str) -> dict:
        if not self._is_safe(path):
            return {"error": f"Path non autorizzato: {path}"}
        p = Path(path)
        if not p.is_dir():
            return {"error": f"Non è una cartella: {path}"}
        items = []
        for entry in sorted(p.iterdir())[:100]:  # max 100 entries
            items.append({
                "name": entry.name,
                "type": "dir" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else None,
            })
        return {"path": path, "count": len(items), "items": items}


# ─── PLUGIN: CLIPBOARD ───────────────────────────────────────────────────────

class ClipboardPlugin(BasePlugin):
    def __init__(self):
        self.info = PluginInfo(
            id="vio.clipboard",
            name="Clipboard",
            version="1.0.0",
            description="Leggi e scrivi gli appunti del Mac",
            author="Viorica Porcu",
            icon="📋",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("read", "Legge il contenuto degli appunti", {}),
                PluginTool("write", "Scrive testo negli appunti",
                           {"text": {"type": "string"}}),
            ],
        )

    def _tool_read(self) -> dict:
        try:
            result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
            return {"content": result.stdout, "length": len(result.stdout)}
        except Exception as e:
            return {"error": str(e)}

    def _tool_write(self, text: str) -> dict:
        try:
            subprocess.run(["pbcopy"], input=text, text=True, timeout=5)
            return {"success": True, "length": len(text)}
        except Exception as e:
            return {"error": str(e)}


# ─── PLUGIN: WEB SEARCH ──────────────────────────────────────────────────────

class WebSearchPlugin(BasePlugin):
    def __init__(self):
        self.info = PluginInfo(
            id="vio.websearch",
            name="Web Search",
            version="1.0.0",
            description="Ricerca web via DuckDuckGo (nessuna API key richiesta, privacy-first)",
            author="Viorica Porcu",
            icon="🔍",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("search", "Cerca sul web",
                           {"query": {"type": "string"}, "max_results": {"type": "integer", "default": 5}},
                           ["search(query='Tauri 2.0 performance', max_results=5)"]),
            ],
        )

    def _tool_search(self, query: str, max_results: int = 5) -> dict:
        try:
            q = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers={"User-Agent": "VIO83-Plugin/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())

            results = []
            # Abstract
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", "Abstract"),
                    "snippet": data["AbstractText"][:300],
                    "url": data.get("AbstractURL", ""),
                    "source": "DuckDuckGo Abstract",
                })
            # Related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:80],
                        "snippet": topic.get("Text", "")[:200],
                        "url": topic.get("FirstURL", ""),
                        "source": "DuckDuckGo",
                    })
                if len(results) >= max_results:
                    break

            return {"query": query, "results": results[:max_results], "count": len(results)}
        except Exception as e:
            return {"error": str(e), "query": query}


# ─── PLUGIN: DATETIME ────────────────────────────────────────────────────────

class DateTimePlugin(BasePlugin):
    def __init__(self):
        self.info = PluginInfo(
            id="vio.datetime",
            name="Date & Time",
            version="1.0.0",
            description="Ora, data, giorno della settimana, timezone",
            author="Viorica Porcu",
            icon="🕐",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("now", "Restituisce data e ora correnti", {}),
                PluginTool("timestamp", "Restituisce timestamp Unix corrente", {}),
            ],
        )

    def _tool_now(self) -> dict:
        now = datetime.datetime.now()
        return {
            "iso": now.isoformat(),
            "date": now.strftime("%d/%m/%Y"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"][now.weekday()],
            "week_number": now.isocalendar()[1],
            "timezone": str(datetime.datetime.now().astimezone().tzinfo),
        }

    def _tool_timestamp(self) -> dict:
        import time
        return {"timestamp": time.time(), "ms": int(time.time() * 1000)}


# ─── PLUGIN: CALCULATOR ──────────────────────────────────────────────────────

class CalculatorPlugin(BasePlugin):
    # Whitelist di funzioni sicure per eval
    _SAFE_NAMES = {
        k: v for k, v in vars(math).items() if not k.startswith("_")
    }
    _SAFE_NAMES.update({"abs": abs, "round": round, "min": min, "max": max, "sum": sum})

    def __init__(self):
        self.info = PluginInfo(
            id="vio.calculator",
            name="Calculator",
            version="1.0.0",
            description="Calcoli matematici sicuri (eval sandbox, no import)",
            author="Viorica Porcu",
            icon="🔢",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("calculate", "Esegui un calcolo matematico",
                           {"expression": {"type": "string"}},
                           ["calculate(expression='2**10 + sqrt(144)')",
                            "calculate(expression='sin(pi/2) * 100')"]),
            ],
        )

    def _tool_calculate(self, expression: str) -> dict:
        # Security: block dangerous keywords
        forbidden = ["import", "__", "exec", "eval", "open", "os", "sys",
                     "subprocess", "globals", "locals", "getattr", "setattr"]
        lower_expr = expression.lower()
        for f in forbidden:
            if f in lower_expr:
                return {"error": f"Espressione non consentita (parola vietata: {f})"}
        try:
            result = eval(expression, {"__builtins__": {}}, self._SAFE_NAMES)  # noqa: S307
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"error": str(e), "expression": expression}


# ─── PLUGIN: MEMORY ──────────────────────────────────────────────────────────

class MemoryPlugin(BasePlugin):
    _DB_PATH = Path.home() / ".vio83" / "plugin_memory.json"

    def __init__(self):
        self._DB_PATH.parent.mkdir(exist_ok=True)
        if not self._DB_PATH.exists():
            self._DB_PATH.write_text("{}")
        self.info = PluginInfo(
            id="vio.memory",
            name="Memory",
            version="1.0.0",
            description="Note persistenti cross-session (salvate in ~/.vio83/plugin_memory.json)",
            author="Viorica Porcu",
            icon="🧠",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("save", "Salva una nota con chiave",
                           {"key": {"type": "string"}, "value": {"type": "string"}}),
                PluginTool("load", "Carica una nota per chiave",
                           {"key": {"type": "string"}}),
                PluginTool("list", "Lista tutte le chiavi salvate", {}),
                PluginTool("delete", "Cancella una nota",
                           {"key": {"type": "string"}}),
            ],
        )

    def _read(self) -> dict:
        try:
            return json.loads(self._DB_PATH.read_text())
        except Exception:
            return {}

    def _write(self, data: dict):
        self._DB_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _tool_save(self, key: str, value: str) -> dict:
        data = self._read()
        data[key] = {"value": value, "saved_at": datetime.datetime.now().isoformat()}
        self._write(data)
        return {"success": True, "key": key}

    def _tool_load(self, key: str) -> dict:
        data = self._read()
        if key not in data:
            return {"error": f"Chiave '{key}' non trovata"}
        return {"key": key, **data[key]}

    def _tool_list(self) -> dict:
        data = self._read()
        return {"count": len(data), "keys": list(data.keys())}

    def _tool_delete(self, key: str) -> dict:
        data = self._read()
        if key not in data:
            return {"error": f"Chiave '{key}' non trovata"}
        del data[key]
        self._write(data)
        return {"success": True, "key": key}


# Global singleton
_registry: Optional[PluginRegistry] = None

def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
