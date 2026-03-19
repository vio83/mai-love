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
import ipaddress
import json
import math
import datetime
import os
import shlex
import socket
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
        self.register(URLFetchPlugin())
        self.register(SystemInfoPlugin())
        self.register(CodeRunnerPlugin())
        self.register(JSONProcessorPlugin())
        self.register(TranslatorPlugin())
        self.register(GitPlugin())

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


# ─── PLUGIN: URL FETCH ────────────────────────────────────────────────────────

class URLFetchPlugin(BasePlugin):
    """Fetch and extract text from web pages (privacy-first, no tracking)."""

    def __init__(self):
        self.info = PluginInfo(
            id="vio.urlfetch",
            name="URL Fetch",
            version="1.0.0",
            description="Scarica e estrai testo da pagine web (privacy-first, no tracking)",
            author="Viorica Porcu",
            icon="🌐",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("fetch", "Scarica il contenuto testuale di un URL",
                           {"url": {"type": "string", "description": "URL da scaricare"}},
                           ["fetch(url='https://example.com')"]),
                PluginTool("headers", "Mostra gli header HTTP di un URL",
                           {"url": {"type": "string"}},
                           ["headers(url='https://example.com')"]),
            ],
        )

    @staticmethod
    def _is_private_or_local_ip(ip: str) -> bool:
        try:
            ip_obj = ipaddress.ip_address(ip)
            return (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_reserved
                or ip_obj.is_multicast
            )
        except ValueError:
            return False

    def _is_blocked_hostname(self, hostname: str) -> bool:
        normalized = (hostname or "").strip().lower()
        if not normalized:
            return True
        if normalized in {"localhost", "0.0.0.0", "::1"}:
            return True

        # Direct IP hostname
        if self._is_private_or_local_ip(normalized):
            return True

        # DNS resolution guard (SSRF mitigation)
        try:
            infos = socket.getaddrinfo(normalized, None)
            for info in infos:
                resolved_ip = info[4][0]
                if isinstance(resolved_ip, str) and self._is_private_or_local_ip(resolved_ip):
                    return True
        except socket.gaierror:
            # If DNS fails we don't classify as blocked here; request will fail downstream.
            pass

        return False

    def _tool_fetch(self, url: str) -> dict:
        import html
        import re as _re
        if not url.startswith(("http://", "https://")):
            return {"error": "URL deve iniziare con http:// o https://"}
        # Block private/internal IPs to prevent SSRF
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""
        if self._is_blocked_hostname(hostname):
            return {"error": "Accesso a indirizzi interni non consentito"}
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "VIO83-URLFetch/1.0 (AI Orchestra)",
                "Accept": "text/html,text/plain,application/json",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read(500_000)  # max 500KB
                charset = "utf-8"
                if "charset=" in content_type:
                    charset = content_type.split("charset=")[-1].split(";")[0].strip()
                text = raw.decode(charset, errors="replace")

                # Strip HTML tags for readability
                if "html" in content_type.lower():
                    text = _re.sub(r"<script[^>]*>.*?</script>", "", text, flags=_re.DOTALL | _re.IGNORECASE)
                    text = _re.sub(r"<style[^>]*>.*?</style>", "", text, flags=_re.DOTALL | _re.IGNORECASE)
                    text = _re.sub(r"<[^>]+>", " ", text)
                    text = html.unescape(text)
                    text = _re.sub(r"\s+", " ", text).strip()

                return {
                    "url": url,
                    "content_type": content_type,
                    "length": len(text),
                    "text": text[:10000],  # cap at 10K chars
                }
        except Exception as e:
            return {"error": str(e), "url": url}

    def _tool_headers(self, url: str) -> dict:
        if not url.startswith(("http://", "https://")):
            return {"error": "URL deve iniziare con http:// o https://"}
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""
        if self._is_blocked_hostname(hostname):
            return {"error": "Accesso a indirizzi interni non consentito"}
        try:
            req = urllib.request.Request(url, method="HEAD", headers={
                "User-Agent": "VIO83-URLFetch/1.0",
            })
            with urllib.request.urlopen(req, timeout=8) as resp:
                headers = {k: v for k, v in resp.headers.items()}
                return {"url": url, "status": resp.status, "headers": headers}
        except Exception as e:
            return {"error": str(e), "url": url}


# ─── PLUGIN: SYSTEM INFO ─────────────────────────────────────────────────────

class SystemInfoPlugin(BasePlugin):
    """System hardware and software information."""

    def __init__(self):
        import platform
        self.info = PluginInfo(
            id="vio.systeminfo",
            name="System Info",
            version="1.0.0",
            description="Informazioni hardware e software del sistema (CPU, RAM, disco, OS)",
            author="Viorica Porcu",
            icon="💻",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("overview", "Panoramica sistema completa", {}),
                PluginTool("disk", "Spazio disco disponibile", {}),
                PluginTool("processes", "Top processi per uso CPU/RAM",
                           {"count": {"type": "integer", "default": 10}}),
            ],
        )

    def _tool_overview(self) -> dict:
        import platform
        try:
            uname = platform.uname()
            result = {
                "os": f"{uname.system} {uname.release}",
                "machine": uname.machine,
                "processor": uname.processor or platform.processor(),
                "python": platform.python_version(),
                "hostname": uname.node,
            }
            # RAM info via sysctl on macOS
            try:
                mem_result = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5)
                mem_bytes = int(mem_result.stdout.strip())
                result["ram_gb"] = str(round(mem_bytes / (1024**3), 1))
            except Exception:
                pass
            return result
        except Exception as e:
            return {"error": str(e)}

    def _tool_disk(self) -> dict:
        try:
            result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                return {
                    "filesystem": parts[0] if len(parts) > 0 else "N/A",
                    "total": parts[1] if len(parts) > 1 else "N/A",
                    "used": parts[2] if len(parts) > 2 else "N/A",
                    "available": parts[3] if len(parts) > 3 else "N/A",
                    "use_percent": parts[4] if len(parts) > 4 else "N/A",
                }
            return {"raw": result.stdout}
        except Exception as e:
            return {"error": str(e)}

    def _tool_processes(self, count: int = 10) -> dict:
        count = min(int(count), 20)  # cap at 20
        try:
            result = subprocess.run(
                ["ps", "-axo", "user,pid,%cpu,%mem,command"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split("\n")
            processes = []
            for line in lines[1:]:
                parts = line.split(None, 4)
                if len(parts) >= 5:
                    mem = 0.0
                    cpu = 0.0
                    try:
                        cpu = float(parts[2])
                        mem = float(parts[3])
                    except ValueError:
                        pass
                    processes.append({
                        "user": parts[0],
                        "pid": parts[1],
                        "cpu": f"{cpu:.1f}",
                        "mem": f"{mem:.1f}",
                        "command": parts[4][:80],
                        "_mem_sort": mem,
                    })
            processes.sort(key=lambda p: p.get("_mem_sort", 0), reverse=True)
            top = processes[:count]
            for proc in top:
                proc.pop("_mem_sort", None)
            return {"count": len(top), "processes": top}
        except Exception as e:
            return {"error": str(e)}


# ─── PLUGIN: CODE RUNNER ─────────────────────────────────────────────────────

class CodeRunnerPlugin(BasePlugin):
    """Sandboxed code execution for Python and shell scripts."""

    def __init__(self):
        self.info = PluginInfo(
            id="vio.coderunner",
            name="Code Runner",
            version="1.0.0",
            description="Esegui codice Python o comandi shell in modo sicuro (sandbox, timeout 10s)",
            author="Viorica Porcu",
            icon="▶️",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("python", "Esegui codice Python",
                           {"code": {"type": "string", "description": "Codice Python da eseguire"}},
                           ["python(code='print(2+2)')", "python(code='import json; print(json.dumps({\"a\":1}))')"]),
                PluginTool("shell", "Esegui un comando shell (read-only, sicuro)",
                           {"command": {"type": "string", "description": "Comando da eseguire"}},
                           ["shell(command='ls -la')", "shell(command='whoami')"]),
            ],
        )

    _PYTHON_BLOCKED = {"import os", "import sys", "import subprocess", "import shutil",
                       "__import__", "exec(", "eval(", "open(", "os.system", "os.popen",
                       "subprocess.", "shutil."}

    def _tool_python(self, code: str) -> dict:
        # Security check
        for blocked in self._PYTHON_BLOCKED:
            if blocked in code:
                return {"error": f"Codice non consentito (contiene: {blocked})"}
        try:
            import io
            import contextlib
            stdout = io.StringIO()
            stderr = io.StringIO()
            safe_globals = {"__builtins__": {"print": print, "range": range, "len": len,
                            "str": str, "int": int, "float": float, "list": list,
                            "dict": dict, "set": set, "tuple": tuple, "bool": bool,
                            "sorted": sorted, "reversed": reversed, "enumerate": enumerate,
                            "zip": zip, "map": map, "filter": filter, "sum": sum,
                            "min": min, "max": max, "abs": abs, "round": round,
                            "type": type, "isinstance": isinstance, "True": True,
                            "False": False, "None": None}}
            safe_globals.update(vars(math))
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec(code, safe_globals)  # noqa: S102
            return {
                "stdout": stdout.getvalue()[:5000],
                "stderr": stderr.getvalue()[:2000],
                "success": True,
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    _SHELL_BLOCKED = {"rm ", "rm\t", "rmdir", "mkfs", "dd ", "chmod", "chown",
                      "> /dev", "sudo ", "su ", "passwd", "kill ", "pkill",
                      "curl ", "wget "}

    def _tool_shell(self, command: str) -> dict:
        for blocked in self._SHELL_BLOCKED:
            if blocked in command:
                return {"error": f"Comando non consentito (contiene: {blocked})"}
        try:
            result = subprocess.run(
                shlex.split(command),
                capture_output=True, text=True, timeout=10,
                cwd=str(Path.home()),
            )
            return {
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:2000],
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Timeout: comando ha superato 10 secondi"}
        except Exception as e:
            return {"error": str(e)}


# ─── PLUGIN: JSON/CSV PROCESSOR ──────────────────────────────────────────────

class JSONProcessorPlugin(BasePlugin):
    """Parse, transform, and analyze JSON and CSV data."""

    def __init__(self):
        self.info = PluginInfo(
            id="vio.jsonprocessor",
            name="JSON/CSV Processor",
            version="1.0.0",
            description="Analizza, trasforma e valida dati JSON e CSV",
            author="Viorica Porcu",
            icon="📊",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("parse_json", "Valida e formatta JSON",
                           {"data": {"type": "string", "description": "Stringa JSON da validare"}}),
                PluginTool("json_query", "Estrai valore da JSON con dot notation",
                           {"data": {"type": "string"}, "path": {"type": "string", "description": "Path dot notation (es: 'user.name')"}}),
                PluginTool("csv_to_json", "Converti CSV in JSON",
                           {"csv_text": {"type": "string", "description": "Testo CSV"}}),
                PluginTool("json_stats", "Statistiche su un array JSON",
                           {"data": {"type": "string"}}),
            ],
        )

    def _tool_parse_json(self, data: str) -> dict:
        try:
            parsed = json.loads(data)
            return {
                "valid": True,
                "type": type(parsed).__name__,
                "formatted": json.dumps(parsed, indent=2, ensure_ascii=False)[:5000],
            }
        except json.JSONDecodeError as e:
            return {"valid": False, "error": str(e)}

    def _tool_json_query(self, data: str, path: str) -> dict:
        try:
            parsed = json.loads(data)
            keys = path.split(".")
            current = parsed
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                elif isinstance(current, list) and key.isdigit():
                    current = current[int(key)]
                else:
                    return {"error": f"Cannot access '{key}' on {type(current).__name__}"}
            return {"path": path, "value": current, "type": type(current).__name__}
        except Exception as e:
            return {"error": str(e)}

    def _tool_csv_to_json(self, csv_text: str) -> dict:
        import csv
        import io
        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            rows = list(reader)[:1000]  # cap at 1000 rows
            return {"rows": len(rows), "columns": reader.fieldnames or [], "data": rows[:50]}
        except Exception as e:
            return {"error": str(e)}

    def _tool_json_stats(self, data: str) -> dict:
        try:
            parsed = json.loads(data)
            if not isinstance(parsed, list):
                return {"error": "Input deve essere un array JSON"}
            stats: dict[str, Any] = {"count": len(parsed)}
            if parsed and isinstance(parsed[0], dict):
                stats["keys"] = list(parsed[0].keys())
                # Numeric stats per field
                for key in parsed[0]:
                    values = [item.get(key) for item in parsed if isinstance(item.get(key), (int, float))]
                    if values:
                        stats[f"{key}_min"] = min(values)
                        stats[f"{key}_max"] = max(values)
                        stats[f"{key}_avg"] = round(sum(values) / len(values), 2)
            return stats
        except Exception as e:
            return {"error": str(e)}


# ─── PLUGIN: TRANSLATOR ──────────────────────────────────────────────────────

class TranslatorPlugin(BasePlugin):
    """Translation utility via MyMemory free API (no API key required)."""

    def __init__(self):
        self.info = PluginInfo(
            id="vio.translator",
            name="Translator",
            version="1.0.0",
            description="Traduttore di testo via MyMemory API (gratis, no API key, 500 char/richiesta)",
            author="Viorica Porcu",
            icon="🌍",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("translate", "Traduci testo tra lingue",
                           {
                               "text": {"type": "string", "description": "Testo da tradurre"},
                               "from_lang": {"type": "string", "description": "Lingua sorgente (es: it, en, fr, de, es)"},
                               "to_lang": {"type": "string", "description": "Lingua destinazione"},
                           },
                           ["translate(text='Ciao mondo', from_lang='it', to_lang='en')"]),
                PluginTool("detect", "Rileva la lingua di un testo",
                           {"text": {"type": "string"}},
                           ["detect(text='Hello world')"]),
            ],
        )

    def _tool_translate(self, text: str, from_lang: str = "it", to_lang: str = "en") -> dict:
        text = text[:500]  # API limit
        try:
            q = urllib.parse.quote(text)
            url = f"https://api.mymemory.translated.net/get?q={q}&langpair={from_lang}|{to_lang}"
            req = urllib.request.Request(url, headers={"User-Agent": "VIO83-Translator/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                translated = data.get("responseData", {}).get("translatedText", "")
                match_score = data.get("responseData", {}).get("match", 0)
                return {
                    "original": text,
                    "translated": translated,
                    "from": from_lang,
                    "to": to_lang,
                    "confidence": match_score,
                }
        except Exception as e:
            return {"error": str(e)}

    def _tool_detect(self, text: str) -> dict:
        text = text[:200]
        try:
            q = urllib.parse.quote(text)
            url = f"https://api.mymemory.translated.net/get?q={q}&langpair=autodetect|en"
            req = urllib.request.Request(url, headers={"User-Agent": "VIO83-Translator/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                detected = data.get("responseData", {}).get("detectedLanguage", "unknown")
                return {"text": text[:50], "detected_language": detected}
        except Exception as e:
            return {"error": str(e)}


# ─── PLUGIN: GIT ─────────────────────────────────────────────────────────────

class GitPlugin(BasePlugin):
    """Git repository information and operations (read-only for safety)."""

    _PROJECT_ROOT = Path(__file__).resolve().parents[2]

    def __init__(self):
        self.info = PluginInfo(
            id="vio.git",
            name="Git",
            version="1.0.0",
            description="Informazioni Git repository (log, status, diff, branches — sola lettura)",
            author="Viorica Porcu",
            icon="🔀",
            status=PluginStatus.ACTIVE,
            tools=[
                PluginTool("status", "Mostra git status", {}),
                PluginTool("log", "Mostra ultimi commit",
                           {"count": {"type": "integer", "default": 10}},
                           ["log(count=5)"]),
                PluginTool("diff", "Mostra diff delle modifiche non committate", {}),
                PluginTool("branches", "Lista tutti i branch", {}),
            ],
        )

    def _git(self, *args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                capture_output=True, text=True, timeout=10,
                cwd=str(self._PROJECT_ROOT),
            )
            return result.stdout.strip() or result.stderr.strip()
        except Exception as e:
            return f"Error: {e}"

    def _tool_status(self) -> dict:
        output = self._git("status", "--porcelain")
        lines = output.split("\n") if output else []
        return {
            "changes": len([l for l in lines if l.strip()]),
            "branch": self._git("rev-parse", "--abbrev-ref", "HEAD"),
            "raw": output[:3000],
        }

    def _tool_log(self, count: int = 10) -> dict:
        count = min(int(count), 50)
        output = self._git("log", f"--oneline", f"-{count}", "--format=%h|%s|%an|%ar")
        commits = []
        for line in output.split("\n"):
            if "|" in line:
                parts = line.split("|", 3)
                commits.append({
                    "hash": parts[0],
                    "message": parts[1] if len(parts) > 1 else "",
                    "author": parts[2] if len(parts) > 2 else "",
                    "date": parts[3] if len(parts) > 3 else "",
                })
        return {"count": len(commits), "commits": commits}

    def _tool_diff(self) -> dict:
        output = self._git("diff", "--stat")
        full_diff = self._git("diff")
        return {
            "stat": output[:2000],
            "diff": full_diff[:5000],
        }

    def _tool_branches(self) -> dict:
        output = self._git("branch", "-a")
        branches = [b.strip() for b in output.split("\n") if b.strip()]
        current = next((b.replace("* ", "") for b in branches if b.startswith("*")), None)
        return {
            "current": current,
            "count": len(branches),
            "branches": [b.replace("* ", "") for b in branches],
        }


# Global singleton
_registry: Optional[PluginRegistry] = None

def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
