# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA - FastAPI Server v2
Server principale con:
- Chat (non-streaming + SSE streaming)
- Conversazioni persistenti (SQLite)
- Metriche e analytics
- Ollama management
- Health check completo

NON dipende da LiteLLM — usa direct_router per chiamate Ollama.
"""

import os
import time
import json
import asyncio
import shutil
import signal
import subprocess
import shlex
import uuid
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Any
from collections import defaultdict

from fastapi import Body, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv

from backend.models.schemas import (
    ChatRequest, ChatResponse, ClassifyRequest, ClassifyResponse,
    HealthResponse, RAGAddRequest, RAGSearchRequest, ErrorResponse
)
from backend.config.providers import (
    CLOUD_PROVIDERS, LOCAL_PROVIDERS, FREE_CLOUD_PROVIDERS,
    ALL_CLOUD_PROVIDERS, get_available_cloud_providers,
    get_free_cloud_providers, get_all_providers_ordered, get_elite_task_stacks,
)
from backend.database.db import (
    init_database, create_conversation, list_conversations,
    get_conversation, update_conversation_title, delete_conversation,
    archive_conversation, add_message, log_metric, get_metrics_summary,
    auto_title_from_message, get_setting, set_setting, get_all_settings,
)
from backend.orchestrator.direct_router import (
    classify_request, orchestrate, call_ollama_streaming,
    check_ollama_status,
)
from backend.automation.autonomous_runtime import AutonomousRuntime
from backend.core.user_auth import get_user_auth, UserProfile
from backend.core.api_key_manager import get_key_vault
from backend.core.subscription_manager import get_subscription_manager

# RAG è disabilitato per compatibilità Python 3.14
RAG_AVAILABLE = False
# try:
#     from backend.rag.engine import get_rag_engine, RAGSource
#     RAG_AVAILABLE = True
# except Exception as e:
#     print(f"⚠️  RAG Engine legacy non disponibile: {e}")

# Stubs per evitare errori Pylance sui path RAG_AVAILABLE==False
def get_rag_engine():
    raise RuntimeError("RAG Engine non disponibile")

class RAGSource:
    def __init__(self, **kwargs: Any): ...

# Knowledge Base v2 — attiva quando il modulo è importabile (fallback SQLite FTS5)
KB_AVAILABLE = False
KB_IMPORT_ERROR: str | None = None
try:
    from backend.rag.knowledge_base import get_knowledge_base, KnowledgeBase
    KB_AVAILABLE = True
except Exception as e:
    KB_IMPORT_ERROR = str(e)
    print(f"⚠️  Knowledge Base non disponibile: {e}")

load_dotenv()
START_TIME = time.time()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ENV_PATH = PROJECT_ROOT / ".env"
RUNTIME_SUPERVISOR_STATE_PATH = PROJECT_ROOT / ".pids" / "runtime-supervisor-state.json"
RUNTIME_SUPERVISOR_PID_PATH = PROJECT_ROOT / ".pids" / "runtime-supervisor.pid"
RUNTIME_LAUNCH_AGENT_PATH = Path.home() / "Library" / "LaunchAgents" / "com.vio83.runtime-services.plist"
ORCHESTRA_LAUNCH_AGENT_PATH = Path.home() / "Library" / "LaunchAgents" / "com.vio83.ai-orchestra.plist"

RUNTIME_ENV_DEFAULTS = {
    "OPENCLAW_START_CMD": "builtin",  # Built-in agent runtime on main server
    "LEGALROOM_START_CMD": "",
    "N8N_START_CMD": "",
    "OPENCLAW_HEALTH_URLS": "http://127.0.0.1:4000/openclaw/health,http://127.0.0.1:4111/health",
    "LEGALROOM_HEALTH_URLS": "http://127.0.0.1:4222/health,http://127.0.0.1:4222/",
    "N8N_HEALTH_URLS": "http://127.0.0.1:5678/healthz,http://127.0.0.1:5678/rest/healthz,http://127.0.0.1:5678/",
    "RUNTIME_APPS_UPDATE_POLICY": "user-approved",
    "RUNTIME_APPS_OFFLINE_MODE": "keep-last-approved",
    "RUNTIME_APPS_LAST_USER_APPROVED_AT": "",
    "AUTONOMOUS_RUNTIME_ENABLED": "true",
    "AUTONOMOUS_RUNTIME_HEARTBEAT_SEC": "300",
    "AUTONOMOUS_RUNTIME_WATCH_POLL_SEC": "90",
    "AUTONOMOUS_RUNTIME_COMPACT_EVERY_NOTES": "12",
    "AUTONOMOUS_RUNTIME_CONTEXT_TAIL_NOTES": "12",
    "AUTONOMOUS_RUNTIME_DEFAULT_ACCOUNT": "vio83-local",
    "AUTONOMOUS_RUNTIME_DEFAULT_CHANNEL": "main",
    "AUTONOMOUS_RUNTIME_CRON_UTC": "00:15,06:15,12:15,18:15",
    "AUTONOMOUS_RUNTIME_WATCH_DIRS": "backend,src,docs,data/config",
    "AUTONOMOUS_RUNTIME_WATCH_EXTENSIONS": ".py,.ts,.tsx,.js,.jsx,.md,.json,.yml,.yaml,.toml,.sh",
    "AUTONOMOUS_RUNTIME_BACKGROUND_ISOLATION": "true",
    "AUTONOMOUS_RUNTIME_MAX_FILES_PER_TICK": "20",
    "VIO_EXECUTION_PROFILE": "real-max-local",
    "VIO_NO_HYBRID": "false",
    "VIO_LOCAL_MODEL_PREFERENCE": "qwen2.5-coder:3b",
}

AUTONOMOUS_RUNTIME = AutonomousRuntime(PROJECT_ROOT)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _iso_from_epoch(epoch_s: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch_s))


# Cached _read_project_env_map with 30s TTL — avoids re-parsing .env on every call
_ENV_MAP_CACHE: dict[str, str] | None = None
_ENV_MAP_CACHE_TS: float = 0.0
_ENV_MAP_CACHE_TTL: float = 30.0


def _read_project_env_map() -> dict[str, str]:
    global _ENV_MAP_CACHE, _ENV_MAP_CACHE_TS
    now = time.time()
    if _ENV_MAP_CACHE is not None and (now - _ENV_MAP_CACHE_TS) < _ENV_MAP_CACHE_TTL:
        return _ENV_MAP_CACHE

    env_map: dict[str, str] = {}

    if not PROJECT_ENV_PATH.exists():
        _ENV_MAP_CACHE = env_map
        _ENV_MAP_CACHE_TS = now
        return env_map

    try:
        for raw_line in PROJECT_ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            env_map[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        return env_map

    _ENV_MAP_CACHE = env_map
    _ENV_MAP_CACHE_TS = now
    return env_map


def _write_project_env_updates(updates: dict[str, str]) -> dict[str, str]:
    existing_lines = PROJECT_ENV_PATH.read_text(encoding="utf-8").splitlines() if PROJECT_ENV_PATH.exists() else []
    updated_keys: set[str] = set()
    next_lines: list[str] = []

    for raw_line in existing_lines:
        stripped = raw_line.strip()
        replaced = False

        if stripped and not stripped.startswith("#") and "=" in raw_line:
            key = raw_line.split("=", 1)[0].strip()
            if key in updates:
                next_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
                replaced = True

        if not replaced:
            next_lines.append(raw_line)

    if next_lines and next_lines[-1].strip() != "":
        next_lines.append("")

    for key, value in updates.items():
        if key not in updated_keys:
            next_lines.append(f"{key}={value}")

    PROJECT_ENV_PATH.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")
    return _read_project_env_map()


def _runtime_env_value(env_map: dict[str, str], key: str) -> str:
    return env_map.get(key, os.environ.get(key, RUNTIME_ENV_DEFAULTS.get(key, "")))


def _as_bool(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _get_orchestration_policy() -> dict:
    no_hybrid = _as_bool(os.environ.get("VIO_NO_HYBRID", "false"))
    if no_hybrid:
        return {"available": True, "mode": "local", "name": "Local-only no-hybrid", "enforced": True}
    return {"available": True, "mode": "dual", "name": "Dual-mode (local + cloud)", "enforced": False}


def _cap_request_tokens(requested: int) -> int:
    soft_cap = int(os.environ.get("VIO_SERVER_MAX_TOKENS", "512") or 512)
    hard_cap = int(os.environ.get("VIO_SERVER_MAX_TOKENS_HARD", "1024") or 1024)
    upper = max(soft_cap, hard_cap)
    return max(64, min(int(requested), upper))


def _effective_temperature(requested: float) -> float:
    speed_mode = _as_bool(os.environ.get("VIO_SPEED_MODE", "true"))
    if not speed_mode:
        return requested
    return min(requested, 0.25)


def _command_status(command: str) -> dict[str, Any]:
    normalized = (command or "").strip()
    if not normalized:
        return {"configured": False, "binary_ok": False, "command_type": "missing", "entry": None}

    if any(token in normalized for token in ["&&", ";", "|", "source ", "export "]):
        return {"configured": True, "binary_ok": True, "command_type": "shell-composite", "entry": "shell"}

    try:
        parts = shlex.split(normalized)
    except Exception:
        return {"configured": True, "binary_ok": True, "command_type": "shell-raw", "entry": normalized.split(" ", 1)[0]}

    if not parts:
        return {"configured": False, "binary_ok": False, "command_type": "missing", "entry": None}

    entry = parts[0]
    if entry.startswith("/") or entry.startswith("~"):
        expanded = str(Path(entry).expanduser())
        return {
            "configured": True,
            "binary_ok": Path(expanded).exists(),
            "command_type": "absolute-path",
            "entry": expanded,
        }

    found = shutil.which(entry)
    return {
        "configured": True,
        "binary_ok": bool(found),
        "command_type": "binary",
        "entry": found or entry,
    }


def _probe_runtime_urls(urls: list[str], timeout_s: float = 1.4) -> dict[str, Any]:
    import urllib.request
    import urllib.error

    last_error = None
    for url in urls:
        started = time.time()
        try:
            req = urllib.request.Request(url, method="GET", headers={"User-Agent": "VIO83-Runtime-Analysis/1.0"})
            with urllib.request.urlopen(req, timeout=timeout_s) as response:
                latency_ms = max(1, int((time.time() - started) * 1000))
                status_code = int(getattr(response, "status", 200))
                return {
                    "reachable": status_code < 500,
                    "url": url,
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                    "error": None,
                }
        except urllib.error.HTTPError as http_exc:
            latency_ms = max(1, int((time.time() - started) * 1000))
            if int(http_exc.code) < 500:
                return {
                    "reachable": True,
                    "url": url,
                    "status_code": int(http_exc.code),
                    "latency_ms": latency_ms,
                    "error": str(http_exc),
                }
            last_error = str(http_exc)
        except Exception as exc:
            last_error = str(exc)

    return {
        "reachable": False,
        "url": urls[0] if urls else None,
        "status_code": None,
        "latency_ms": None,
        "error": last_error,
    }


def _launch_agent_loaded(label: str) -> bool:
    try:
        result = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=6)
        return label in (result.stdout or "")
    except Exception:
        return False


def _safe_version_output(command: list[str]) -> Optional[str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=6)
        output = (result.stdout or result.stderr or "").strip()
        return output.splitlines()[0] if output else None
    except Exception:
        return None


def _read_json_file(path: Path) -> Optional[dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# Cached Claude Desktop snapshot with 15s TTL
_CLAUDE_DESKTOP_CACHE: dict[str, Any] | None = None
_CLAUDE_DESKTOP_CACHE_TS: float = 0.0


def _claude_desktop_snapshot() -> dict[str, Any]:
    global _CLAUDE_DESKTOP_CACHE, _CLAUDE_DESKTOP_CACHE_TS
    now = time.time()
    if _CLAUDE_DESKTOP_CACHE is not None and (now - _CLAUDE_DESKTOP_CACHE_TS) < 15.0:
        return _CLAUDE_DESKTOP_CACHE

    base_path = Path.home() / "Library" / "Application Support" / "Claude"
    ext_path = base_path / "extensions-installations.json"
    cfg_path = base_path / "claude_desktop_config.json"
    ext_data = _read_json_file(ext_path) or {}
    cfg_data = _read_json_file(cfg_path) or {}
    ext_map = ext_data.get("extensions", {}) if isinstance(ext_data, dict) else {}
    preferences = cfg_data.get("preferences", {}) if isinstance(cfg_data, dict) else {}

    result = {
        "installed": base_path.exists(),
        "base_path": str(base_path),
        "extensions_count": len(ext_map) if isinstance(ext_map, dict) else 0,
        "preferences": {
            "coworkScheduledTasksEnabled": preferences.get("coworkScheduledTasksEnabled", False),
            "coworkWebSearchEnabled": preferences.get("coworkWebSearchEnabled", False),
            "keepAwakeEnabled": preferences.get("keepAwakeEnabled", False),
            "sidebarMode": preferences.get("sidebarMode", ""),
        },
    }
    _CLAUDE_DESKTOP_CACHE = result
    _CLAUDE_DESKTOP_CACHE_TS = now
    return result


def _runtime_apps_snapshot() -> dict[str, Any]:
    env_map = _read_project_env_map()
    supervisor_state = _read_json_file(RUNTIME_SUPERVISOR_STATE_PATH) or {}
    supervisor_pid_raw = None
    if RUNTIME_SUPERVISOR_PID_PATH.exists():
        try:
            supervisor_pid_raw = int(RUNTIME_SUPERVISOR_PID_PATH.read_text(encoding="utf-8").strip())
        except Exception:
            supervisor_pid_raw = None

    dependencies = {
        "python3": {"available": shutil.which("python3") is not None, "version": _safe_version_output(["python3", "--version"])},
        "node": {"available": shutil.which("node") is not None, "version": _safe_version_output(["node", "--version"])},
        "npm": {"available": shutil.which("npm") is not None, "version": _safe_version_output(["npm", "--version"])},
        "ollama": {"available": shutil.which("ollama") is not None, "version": _safe_version_output(["ollama", "--version"])},
        "docker": {"available": shutil.which("docker") is not None, "version": _safe_version_output(["docker", "--version"])},
        "nvm": {"available": (Path.home() / ".nvm" / "nvm.sh").exists(), "version": None},
    }

    app_specs = [
        {
            "id": "openclaw",
            "name": "OpenClaw",
            "env_key": "OPENCLAW_START_CMD",
            "health_env_key": "OPENCLAW_HEALTH_URLS",
            "health_default": RUNTIME_ENV_DEFAULTS["OPENCLAW_HEALTH_URLS"],
            "port": 4111,
            "stack": ["Agent runtime", "Tools bridge", "Task ops"],
            "required_dependencies": ["python3 or node", "local source/repo", "health endpoint 4111"],
            "notes": [
                "Richiede comando reale di avvio configurato dall'utente.",
                "Nessun fake service viene generato automaticamente.",
            ],
        },
        {
            "id": "legalroom",
            "name": "LegalRoom",
            "env_key": "LEGALROOM_START_CMD",
            "health_env_key": "LEGALROOM_HEALTH_URLS",
            "health_default": RUNTIME_ENV_DEFAULTS["LEGALROOM_HEALTH_URLS"],
            "port": 4222,
            "stack": ["Legal workflow engine", "Context memory", "Document pipeline"],
            "required_dependencies": ["python3 or node", "local source/repo", "health endpoint 4222"],
            "notes": [
                "Per stare verde deve esistere un server reale in ascolto su 4222.",
                "La configurazione può essere Python, Node, Docker o shell custom.",
            ],
        },
        {
            "id": "n8n",
            "name": "n8n",
            "env_key": "N8N_START_CMD",
            "health_env_key": "N8N_HEALTH_URLS",
            "health_default": RUNTIME_ENV_DEFAULTS["N8N_HEALTH_URLS"],
            "port": 5678,
            "stack": ["Workflow automation", "Webhooks", "Cron orchestration"],
            "required_dependencies": ["node 18/20/22 or docker", "n8n runtime"],
            "notes": [
                "Se N8N_START_CMD è vuoto, il runner usa fallback Docker -> nvm node22 -> npx.",
                "Node 24 non è supportato da n8n nelle verifiche attuali.",
            ],
        },
    ]

    supervisor_services = {
        item.get("id"): item
        for item in (supervisor_state.get("services") or [])
        if isinstance(item, dict) and item.get("id")
    }

    apps: list[dict[str, Any]] = []
    for spec in app_specs:
        command = _runtime_env_value(env_map, spec["env_key"])
        health_urls_str = _runtime_env_value(env_map, spec["health_env_key"]) or spec["health_default"]
        health_urls = [url.strip() for url in health_urls_str.split(",") if url.strip()]
        health = _probe_runtime_urls(health_urls)
        command_state = _command_status(command)
        supervisor_info = supervisor_services.get(spec["id"], {})

        apps.append({
            "id": spec["id"],
            "name": spec["name"],
            "configured": command_state["configured"] or spec["id"] == "n8n",
            "command": command,
            "command_status": command_state,
            "health_urls": health_urls,
            "health": health,
            "port": spec["port"],
            "stack": spec["stack"],
            "required_dependencies": spec["required_dependencies"],
            "notes": spec["notes"],
            "supervisor": supervisor_info,
            "recommended_actions": [
                f"Configura {spec['env_key']}" if not command_state["configured"] and spec["id"] != "n8n" else None,
                "Installa/abilita LaunchAgent runtime" if not _launch_agent_loaded("com.vio83.runtime-services") else None,
                f"Verifica endpoint health sulla porta {spec['port']}" if not health.get("reachable") else None,
            ],
        })

    return {
        "status": "ok",
        "detected_at": _now_iso(),
        "preferences": {
            "update_policy": _runtime_env_value(env_map, "RUNTIME_APPS_UPDATE_POLICY") or RUNTIME_ENV_DEFAULTS["RUNTIME_APPS_UPDATE_POLICY"],
            "offline_mode": _runtime_env_value(env_map, "RUNTIME_APPS_OFFLINE_MODE") or RUNTIME_ENV_DEFAULTS["RUNTIME_APPS_OFFLINE_MODE"],
            "last_user_approved_at": _runtime_env_value(env_map, "RUNTIME_APPS_LAST_USER_APPROVED_AT") or None,
        },
        "controls": {
            "project_root": str(PROJECT_ROOT),
            "env_path": str(PROJECT_ENV_PATH),
            "runtime_launch_agent_installed": RUNTIME_LAUNCH_AGENT_PATH.exists(),
            "runtime_launch_agent_loaded": _launch_agent_loaded("com.vio83.runtime-services"),
            "orchestra_launch_agent_installed": ORCHESTRA_LAUNCH_AGENT_PATH.exists(),
            "orchestra_launch_agent_loaded": _launch_agent_loaded("com.vio83.ai-orchestra"),
            "supervisor_pid": supervisor_pid_raw,
            "supervisor_state_path": str(RUNTIME_SUPERVISOR_STATE_PATH),
        },
        "dependencies": dependencies,
        "claude_desktop": _claude_desktop_snapshot(),
        "apps": apps,
        "honesty_notes": [
            "OpenClaw e LegalRoom non possono diventare verdi senza un comando reale di avvio.",
            "La policy di update controlla la configurazione approvata dall'utente, non aggiorna magicamente binari esterni.",
            "n8n risulta operativo solo se il runtime reale risponde sugli endpoint configurati.",
        ],
    }


def _run_local_script(script_path: Path, timeout_s: int = 45) -> dict[str, Any]:
    if not script_path.exists():
        return {"ok": False, "output": f"Script non trovato: {script_path}"}

    try:
        result = subprocess.run(
            ["/bin/bash", str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env={**os.environ, "PROJECT_DIR": str(PROJECT_ROOT)},
        )
        output = "\n".join(filter(None, [(result.stdout or "").strip(), (result.stderr or "").strip()])).strip()
        return {"ok": result.returncode == 0, "exit_code": result.returncode, "output": output}
    except Exception as exc:
        return {"ok": False, "exit_code": None, "output": str(exc)}


GLOBAL_KNOWLEDGE_DOMAINS = [
    {
        "id": "medicine-health",
        "name": "Medicina e Salute",
        "subdomains": [
            "medicina generale", "oncologia", "cardiologia", "neurologia", "psichiatria",
            "epidemiologia", "sanità pubblica", "farmacologia", "genetica clinica",
        ],
        "trusted_sources": ["WHO", "CDC", "EMA", "AIFA", "PubMed", "Cochrane"],
    },
    {
        "id": "law-policy",
        "name": "Diritto, Regolazione e Policy",
        "subdomains": [
            "diritto civile", "diritto penale", "diritto amministrativo", "privacy", "compliance",
            "diritto internazionale", "ai act", "diritto del lavoro", "fisco",
        ],
        "trusted_sources": ["EUR-Lex", "Gazzetta Ufficiale", "UN", "OECD", "WIPO"],
    },
    {
        "id": "math-logic",
        "name": "Matematica e Logica",
        "subdomains": [
            "algebra", "analisi", "statistica", "probabilità", "logica formale", "ottimizzazione",
        ],
        "trusted_sources": ["arXiv", "Springer", "IEEE", "ACM", "SIAM"],
    },
    {
        "id": "computer-ai",
        "name": "Informatica, AI e Sistemi",
        "subdomains": [
            "machine learning", "llm engineering", "security", "sistemi distribuiti", "database",
            "rete", "hci", "software engineering",
        ],
        "trusted_sources": ["NIST", "CISA", "IEEE", "IETF", "W3C", "ACM"],
    },
    {
        "id": "physics-space",
        "name": "Fisica, Astrofisica e Astronomia",
        "subdomains": [
            "fisica teorica", "astrofisica", "cosmologia", "strumentazione", "missioni spaziali",
        ],
        "trusted_sources": ["NASA", "ESA", "CERN", "arXiv", "Nature"],
    },
    {
        "id": "engineering",
        "name": "Ingegneria e Tecnologia Applicata",
        "subdomains": [
            "ingegneria civile", "elettronica", "robotica", "materiali", "automazione", "energia",
        ],
        "trusted_sources": ["ISO", "IEC", "IEEE", "ASTM", "ASME"],
    },
    {
        "id": "history-humanities",
        "name": "Storia, Filosofia e Scienze Umane",
        "subdomains": [
            "storia moderna", "storia antica", "filosofia", "etica", "antropologia", "sociologia",
        ],
        "trusted_sources": ["UNESCO", "Europeana", "WorldCat", "Britannica", "JSTOR"],
    },
    {
        "id": "psychology-cognition",
        "name": "Psicologia e Scienze Cognitive",
        "subdomains": [
            "psicologia clinica", "neuroscienze cognitive", "psicometria", "comportamento", "educazione",
        ],
        "trusted_sources": ["APA", "NIH", "WHO", "PubMed", "PsycNet"],
    },
    {
        "id": "economics-politics-journalism",
        "name": "Economia, Politica e Giornalismo Dati",
        "subdomains": [
            "macroeconomia", "microeconomia", "mercati", "policy pubbliche", "fact-checking", "data journalism",
        ],
        "trusted_sources": ["World Bank", "IMF", "OECD", "Eurostat", "UNData"],
    },
]


GLOBAL_LEGAL_WATCH = {
    "global": [
        {"name": "UN Treaty Collection", "url": "https://treaties.un.org/", "scope": "international"},
        {"name": "WIPO Lex", "url": "https://www.wipo.int/wipolex/", "scope": "ip-law"},
    ],
    "eu": [
        {"name": "EUR-Lex", "url": "https://eur-lex.europa.eu/", "scope": "eu-law"},
        {"name": "EDPB", "url": "https://edpb.europa.eu/", "scope": "privacy"},
    ],
    "it": [
        {"name": "Normattiva", "url": "https://www.normattiva.it/", "scope": "italian-law"},
        {"name": "Gazzetta Ufficiale", "url": "https://www.gazzettaufficiale.it/", "scope": "italian-law"},
    ],
    "us": [
        {"name": "Federal Register", "url": "https://www.federalregister.gov/", "scope": "us-law"},
        {"name": "Congress.gov", "url": "https://www.congress.gov/", "scope": "us-law"},
    ],
}


KNOWLEDGE_REFRESH_STATE = {
    "last_refresh_at": None,
    "jurisdiction": None,
    "source_count": 0,
    "reachable_count": 0,
    "fail_count": 0,
    "results": [],
}


KNOWLEDGE_POLICY_STATE = {
    "strict_evidence_mode": True,
    "refresh_interval_hours": 6,
    "minimum_domain_score": 70.0,
    "last_policy_update_at": _now_iso(),
    "next_scheduled_refresh_at": None,
}


def _compute_domain_scores():
    last_refresh_iso = KNOWLEDGE_REFRESH_STATE.get("last_refresh_at")
    source_count = max(1, int(KNOWLEDGE_REFRESH_STATE.get("source_count", 0) or 0))
    reachable_count = int(KNOWLEDGE_REFRESH_STATE.get("reachable_count", 0) or 0)

    if source_count > 0:
        watch_health_score = max(0.0, min(100.0, (reachable_count / source_count) * 100.0))
    else:
        watch_health_score = 60.0

    if last_refresh_iso:
        try:
            last_refresh_ts = time.mktime(time.strptime(last_refresh_iso, "%Y-%m-%dT%H:%M:%SZ"))
            age_h = max(0.0, (time.time() - last_refresh_ts) / 3600.0)
            freshness_score = max(30.0, min(100.0, 100.0 - age_h * 8.0))
        except Exception:
            freshness_score = 55.0
    else:
        freshness_score = 45.0

    scored_domains = []
    for domain in GLOBAL_KNOWLEDGE_DOMAINS:
        coverage_score = max(
            0.0,
            min(
                100.0,
                35.0
                + len(domain.get("subdomains", [])) * 4.0
                + len(domain.get("trusted_sources", [])) * 3.5,
            ),
        )

        reliability_score = round(
            coverage_score * 0.45 + freshness_score * 0.25 + watch_health_score * 0.30,
            1,
        )

        scored_domains.append({
            "id": domain["id"],
            "name": domain["name"],
            "coverage_score": round(coverage_score, 1),
            "freshness_score": round(freshness_score, 1),
            "watch_health_score": round(watch_health_score, 1),
            "reliability_score": reliability_score,
            "status": "high" if reliability_score >= 85 else "medium" if reliability_score >= 70 else "low",
        })

    return scored_domains


def _build_knowledge_registry_payload():
    total_domains = len(GLOBAL_KNOWLEDGE_DOMAINS)
    total_subdomains = sum(len(d["subdomains"]) for d in GLOBAL_KNOWLEDGE_DOMAINS)
    unique_sources = sorted({source for d in GLOBAL_KNOWLEDGE_DOMAINS for source in d["trusted_sources"]})
    scores = _compute_domain_scores()
    score_by_id = {score["id"]: score for score in scores}

    return {
        "status": "ok",
        "version": "2026.03-verified-knowledge-stack-v1",
        "domains": [
            {
                **domain,
                "reliability": score_by_id.get(domain["id"]),
            }
            for domain in GLOBAL_KNOWLEDGE_DOMAINS
        ],
        "coverage": {
            "domain_count": total_domains,
            "subdomain_count": total_subdomains,
            "trusted_source_count": len(unique_sources),
            "trusted_sources": unique_sources,
        },
        "scores": {
            "domains": scores,
            "average_reliability": round(sum(item["reliability_score"] for item in scores) / max(1, len(scores)), 1),
            "minimum_required": KNOWLEDGE_POLICY_STATE["minimum_domain_score"],
        },
        "policy": KNOWLEDGE_POLICY_STATE,
        "legal_watch_jurisdictions": list(GLOBAL_LEGAL_WATCH.keys()),
        "last_generated_at": _now_iso(),
    }


async def _probe_watch_source(source: dict, timeout_s: float = 4.5):
    import urllib.request

    started = time.time()

    def _run_request():
        req = urllib.request.Request(source["url"], method="GET", headers={"User-Agent": "VIO83-HealthProbe/1.0"})
        with urllib.request.urlopen(req, timeout=timeout_s) as response:
            return int(getattr(response, "status", 200))

    try:
        status_code = await asyncio.to_thread(_run_request)
        latency_ms = int((time.time() - started) * 1000)
        return {
            "name": source["name"],
            "url": source["url"],
            "scope": source.get("scope", "generic"),
            "ok": 200 <= status_code < 400,
            "status_code": status_code,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        latency_ms = int((time.time() - started) * 1000)
        return {
            "name": source["name"],
            "url": source["url"],
            "scope": source.get("scope", "generic"),
            "ok": False,
            "status_code": None,
            "latency_ms": latency_ms,
            "error": str(e),
        }


async def _refresh_knowledge_watch(jurisdiction: str = "global"):
    if jurisdiction == "all":
        sources = [source for group in GLOBAL_LEGAL_WATCH.values() for source in group]
    else:
        sources = GLOBAL_LEGAL_WATCH.get(jurisdiction)
        if sources is None:
            raise ValueError(f"Jurisdiction non supportata: {jurisdiction}")

    results = await asyncio.gather(*[_probe_watch_source(source) for source in sources])
    reachable_count = sum(1 for item in results if item.get("ok"))

    summary = {
        "last_refresh_at": _now_iso(),
        "jurisdiction": jurisdiction,
        "source_count": len(results),
        "reachable_count": reachable_count,
        "fail_count": len(results) - reachable_count,
        "results": results,
    }

    KNOWLEDGE_REFRESH_STATE.update(summary)
    next_h = float(KNOWLEDGE_POLICY_STATE.get("refresh_interval_hours", 6))
    KNOWLEDGE_POLICY_STATE["next_scheduled_refresh_at"] = _iso_from_epoch(time.time() + next_h * 3600.0)
    return summary


async def _knowledge_auto_refresh_loop():
    while True:
        try:
            await _refresh_knowledge_watch("all")
            print("🌍 Knowledge Watch auto-refresh completato")
        except Exception as e:
            print(f"⚠️ Knowledge Watch auto-refresh fallito: {e}")

        next_h = max(1.0, float(KNOWLEDGE_POLICY_STATE.get("refresh_interval_hours", 6)))
        KNOWLEDGE_POLICY_STATE["next_scheduled_refresh_at"] = _iso_from_epoch(time.time() + next_h * 3600.0)
        await asyncio.sleep(next_h * 60 * 60)

# === CORE INFRASTRUCTURE ===
from backend.core.cache import get_cache, CacheEngine
from backend.core.network import get_connection_pool, ConnectionPoolManager
from backend.core.parallel import TaskPool, ParallelQueryEngine
from backend.core.errors import get_error_handler, ErrorHandler, OrchestraException
from backend.core.security import get_vault, EnvironmentValidator
from backend.core.jet_engine import get_jet_engine, JetEngine, JetDecision
from backend.core.feather_memory import get_feather_memory, FeatherMemory
from backend.core.hyper_compressor import get_hyper_compressor, HyperCompressor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializzazione e shutdown del server."""
    print("🎵 VIO 83 AI ORCHESTRA — Server v2 avviato")
    print("🔧 Inizializzazione Core Infrastructure...")

    # Inizializza database
    init_database()

    # === SECURITY: Validazione ambiente ===
    validator = EnvironmentValidator()
    env_check = validator.validate()
    if env_check["errors"]:
        for err in env_check["errors"]:
            print(f"  ❌ {err}")
    for warn in env_check["warnings"]:
        print(f"  ⚠️  {warn}")

    # === SECURITY: API Key Vault ===
    vault = get_vault()
    print(f"🔐 API Keys: {vault.stats['valid_keys']}/{vault.stats['total_keys']} valide "
          f"→ Provider: {vault.available_providers or 'solo locale'}")

    # === CACHE: Multi-layer cache ===
    cache = get_cache()
    expired = cache.cleanup()
    print(f"💾 Cache Engine: L1 memory + L2 disk | Pulizia: {expired} entry scadute")

    # === NETWORK: Connection Pool + Circuit Breakers ===
    pool = get_connection_pool()
    pool.register_provider("ollama", base_url="http://localhost:11434", timeout=120.0, rate_limit=100)
    for provider_name in vault.available_providers:
        pool.register_provider(provider_name, timeout=60.0, rate_limit=30)
    print(f"🌐 Network Pool: {pool.stats['total_pools']} provider registrati")

    # === ERROR HANDLER ===
    error_handler = get_error_handler()
    print(f"🛡️  Error Handler: attivo")

    # === JET ENGINE™: velocità aereo militare ===
    jet = get_jet_engine()
    jet_stats = jet.stats()
    print(f"✈️  JetEngine™ Mach 1.6+: TurboCache {jet_stats['turbo_cache']['max_size']} slot | local-first | parallel-sprint ATTIVI")

    # === FEATHER MEMORY™: macchina 400kg → piuma ===
    fm = get_feather_memory()
    fm_stats = fm.stats
    print(f"🪶 FeatherMemory™: pool {fm_stats['pool']['max_conversations']} conv | 50MB max | 100x compression ATTIVO")

    # === HYPER COMPRESSOR™: ottimizzazione 1000x ===
    hc = get_hyper_compressor()
    hc_stats = hc.stats
    print(f"⚡ HyperCompressor™ 1000x: {hc_stats['prompt_cache_size']} prompt pre-compilati | AutoTuner | ProviderHotPath ATTIVI")

    # Knowledge Base v2 (sempre disponibile — SQLite FTS5 fallback)
    if KB_AVAILABLE:
        try:
            kb = get_knowledge_base()
            stats = kb.get_stats()
            print(f"📚 Knowledge Base v2: {stats['fts_chunks']} chunk FTS, "
                  f"{stats['chromadb_chunks']} chunk ChromaDB, "
                  f"embedding: {stats['embedding_mode']}")
        except Exception as e:
            print(f"⚠️  Knowledge Base init fallita: {e}")
    else:
        reason = KB_IMPORT_ERROR or "modulo non importabile"
        print(f"📚 Knowledge Base: non disponibile ({reason})")

    # RAG legacy
    if RAG_AVAILABLE:
        try:
            rag = get_rag_engine()
            rag.initialize()
            print(f"📚 RAG Legacy: {rag.get_stats()['total_documents']} documenti")
        except Exception as e:
            print(f"⚠️  RAG init fallita: {e}")
    else:
        print("📚 RAG Legacy: disabilitato")

    # Check Ollama
    ollama_status = await check_ollama_status()
    if ollama_status["available"]:
        models = [m["name"] for m in ollama_status["models"]]
        print(f"🤖 Ollama: attivo — {len(models)} modelli: {models}")
    else:
        print(f"⚠️  Ollama: non raggiungibile ({ollama_status.get('error', 'unknown')})")

    _no_hybrid = _as_bool(os.environ.get("VIO_NO_HYBRID", "false"))
    if _no_hybrid:
        print("🛡️ Policy orchestrazione: local-only no-hybrid (provider cloud disattivati runtime)")
    else:
        print("🌐 Policy orchestrazione: dual-mode (provider cloud abilitati)")

    app.state.knowledge_auto_refresh_task = asyncio.create_task(_knowledge_auto_refresh_loop())
    print("🌍 Knowledge Watch: auto-refresh ogni 6h attivo")

    await AUTONOMOUS_RUNTIME.start()
    app.state.autonomous_runtime = AUTONOMOUS_RUNTIME
    print("🧠 Autonomous Runtime: trigger→route→session namespace + memoria Markdown attivo")

    # === AUTO-LEARNING ENGINES: cervello auto-crescente ===
    try:
        from backend.core.auto_learner import get_auto_learner
        al = get_auto_learner()
        al_stats = al.get_quality_stats()
        print(f"📖 AutoLearner: {al_stats['patterns_learned']} pattern appresi | satisfaction: {al_stats['satisfaction_rate']:.0%}")
    except Exception as e:
        print(f"⚠️  AutoLearner init: {e}")

    try:
        from backend.core.self_optimizer import get_self_optimizer
        so = get_self_optimizer()
        so_stats = so.get_stats()
        print(f"🎯 SelfOptimizer: {so_stats['providers_tracked']} provider tracked | {so_stats['domains_optimized']} domini ottimizzati")
    except Exception as e:
        print(f"⚠️  SelfOptimizer init: {e}")

    try:
        from backend.core.world_knowledge import get_world_knowledge
        wk = get_world_knowledge()
        wk_stats = wk.get_stats()
        print(f"🌍 WorldKnowledge: {wk_stats['total_facts']} fatti | {wk_stats['db_size_kb']:.0f}KB | domini: {len(wk_stats['domains'])}")
    except Exception as e:
        print(f"⚠️  WorldKnowledge init: {e}")

    try:
        from backend.core.reasoning_engine import get_reasoning_engine
        re_engine = get_reasoning_engine()
        re_stats = re_engine.get_stats()
        print(f"🧩 ReasoningEngine: {re_stats['total_reasonings']} ragionamenti | {re_stats['strategies_count']} strategie | quality: {re_stats['avg_reasoning_quality']:.2f}")
    except Exception as e:
        print(f"⚠️  ReasoningEngine init: {e}")

    print("✅ VIO 83 AI ORCHESTRA — TUTTI I MOTORI AUTO-CRESCENTI ATTIVI")

    yield

    # === SHUTDOWN ===
    print("🎵 VIO 83 AI ORCHESTRA — Shutdown in corso...")

    knowledge_task = getattr(app.state, "knowledge_auto_refresh_task", None)
    if knowledge_task:
        knowledge_task.cancel()
        try:
            await knowledge_task
        except asyncio.CancelledError:
            pass

    autonomous_runtime = getattr(app.state, "autonomous_runtime", None)
    if autonomous_runtime:
        await autonomous_runtime.stop()

    pool = get_connection_pool()
    await pool.close_all()
    cache = get_cache()
    cache.cleanup()
    print("🎵 VIO 83 AI ORCHESTRA — Server arrestato")


app = FastAPI(
    title="VIO 83 AI ORCHESTRA",
    description="Multi-provider AI orchestration platform — Local-first, privacy-first",
    version="0.9.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:1420",
        "tauri://localhost",
        "https://tauri.localhost",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:1420",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════
# PRODUCTION MIDDLEWARE: Structured Logging + Rate Limit
# ═══════════════════════════════════════════════

_structured_logger = logging.getLogger("vio83.requests")
_RATE_LIMIT_WINDOW = 60  # secondi
_RATE_LIMIT_MAX_CHAT = int(os.environ.get("VIO_RATE_LIMIT_CHAT_PER_MIN", "30"))
_rate_buckets: dict[str, list[float]] = defaultdict(list)
_ADMIN_PIN_ENV = "VIO_ADMIN_PIN"
_ADMIN_PIN_HEADER = "x-vio-admin-pin"

_ADMIN_PROTECTED_PREFIXES: tuple[str, ...] = (
    "/runtime/apps/",
    "/autonomy/config",
)

_ADMIN_PROTECTED_EXACT: set[tuple[str, str]] = {
    ("/orchestration/profile", "PUT"),
    ("/knowledge/scheduler", "PUT"),
    ("/knowledge/policy", "PUT"),
    ("/core/cache/clear", "POST"),
    ("/core/cache/cleanup", "POST"),
    ("/autonomy/compact", "POST"),
    ("/autonomy/trigger", "POST"),
}

# Pattern per endpoint DELETE conversazioni (path dinamico /conversations/<id>)
_ADMIN_DELETE_CONVERSATIONS = True  # DELETE /conversations/* richiede admin PIN


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(client_id: str, path: str) -> bool:
    """Rate limit solo per /chat e /chat/stream."""
    if "/chat" not in path:
        return True
    now = time.time()
    bucket = _rate_buckets[client_id]
    # Pulisci timestamp vecchi
    _rate_buckets[client_id] = [t for t in bucket if now - t < _RATE_LIMIT_WINDOW]
    if len(_rate_buckets[client_id]) >= _RATE_LIMIT_MAX_CHAT:
        return False
    _rate_buckets[client_id].append(now)
    # Periodic cleanup: prevent unbounded memory growth
    if len(_rate_buckets) > 5000:
        stale_keys = [k for k, v in _rate_buckets.items() if not v or (now - max(v)) > 600]
        for k in stale_keys:
            del _rate_buckets[k]
    return True


def _requires_admin_auth(path: str, method: str) -> bool:
    req_method = (method or "GET").upper()

    if req_method == "OPTIONS":
        return False

    if (path, req_method) in _ADMIN_PROTECTED_EXACT:
        return True

    # DELETE /conversations/<id> richiede admin PIN
    if _ADMIN_DELETE_CONVERSATIONS and req_method == "DELETE" and path.startswith("/conversations/"):
        return True

    return any(path.startswith(prefix) for prefix in _ADMIN_PROTECTED_PREFIXES)


@app.middleware("http")
async def structured_request_logger(request: Request, call_next):
    """Middleware: request ID, structured logging, rate limiting."""
    request_id = str(uuid.uuid4())[:12]
    start = time.time()
    client_ip = _client_ip(request)
    path = request.url.path

    # Admin auth opzionale: attivo solo se VIO_ADMIN_PIN è valorizzata
    admin_pin = (os.environ.get(_ADMIN_PIN_ENV, "") or "").strip()
    if admin_pin and _requires_admin_auth(path, request.method):
        provided_pin = (request.headers.get(_ADMIN_PIN_HEADER, "") or "").strip()
        if provided_pin != admin_pin:
            return Response(
                content=json.dumps({
                    "detail": "Admin authentication required",
                    "hint": f"Invia header {_ADMIN_PIN_HEADER}",
                }),
                status_code=401,
                media_type="application/json",
                headers={"X-Request-ID": request_id},
            )

    # Rate limiting per /chat endpoints
    if not _check_rate_limit(client_ip, path):
        return Response(
            content=json.dumps({"detail": "Rate limit exceeded. Max {}/min per client.".format(_RATE_LIMIT_MAX_CHAT)}),
            status_code=429,
            media_type="application/json",
            headers={"Retry-After": "60", "X-Request-ID": request_id},
        )

    response = await call_next(request)
    elapsed_ms = int((time.time() - start) * 1000)

    # Header tracciabilità
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

    # Structured log (solo per endpoint significativi, skip assets statici)
    if not path.startswith(("/docs", "/openapi", "/favicon")):
        _structured_logger.info(json.dumps({
            "rid": request_id,
            "method": request.method,
            "path": path,
            "status": response.status_code,
            "ms": elapsed_ms,
            "client": client_ip,
        }, ensure_ascii=False))

    return response


# ═══════════════════════════════════════════════
# METADATA CACHE (per endpoint lenti: /providers, /health)
# ═══════════════════════════════════════════════

_metadata_cache: dict[str, tuple[Any, float]] = {}
_METADATA_TTL = 10.0  # secondi — evita query ripetute in rapida sequenza


def _cached_metadata(key: str, ttl: float = _METADATA_TTL):
    """Decorator per cache temporanea su endpoint metadata read-only."""
    entry = _metadata_cache.get(key)
    if entry:
        value, expires = entry
        if time.time() < expires:
            return value
    return None


def _set_metadata_cache(key: str, value: Any, ttl: float = _METADATA_TTL):
    _metadata_cache[key] = (value, time.time() + ttl)


# ═══════════════════════════════════════════════
# USER AUTH — Registrazione, Login, Verifica
# ═══════════════════════════════════════════════


def _extract_user_token(request: Request) -> Optional[str]:
    """Estrae il token utente dall'header Authorization (Bearer ...)."""
    auth_header = (request.headers.get("authorization", "") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None


async def _require_user(request: Request) -> UserProfile:
    """Verifica autenticazione utente, solleva 401 se non valido."""
    token = _extract_user_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Token di autenticazione richiesto")
    auth = get_user_auth()
    user = auth.verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token non valido o scaduto")
    return user


@app.post("/auth/register")
async def api_auth_register(request: Request):
    """
    Registrazione utente con email + password + codice acquisto.
    L'email diventa l'impronta digitale unica dell'utente.
    """
    body = await request.json()
    email = str(body.get("email", "")).strip()
    password = str(body.get("password", "")).strip()
    purchase_code = str(body.get("purchase_code", "")).strip()
    plan_id = str(body.get("plan_id", "free_local")).strip()

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email e password obbligatori")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password minimo 8 caratteri")

    # Verifica piano valido
    sub_mgr = get_subscription_manager()
    if not sub_mgr.get_plan(plan_id):
        raise HTTPException(status_code=400, detail=f"Piano non valido: {plan_id}")

    auth = get_user_auth()
    result = auth.register(
        email=email,
        password=password,
        purchase_code=purchase_code,
        plan_id=plan_id,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    user = result.user
    assert user is not None

    # Auto-genera le VIO API keys per i provider del piano
    vault = get_key_vault()
    allowed_providers = sub_mgr.get_allowed_providers(plan_id)
    keys = vault.generate_keys_for_user(
        user_id=user.user_id,
        email_hash=user.email_hash,
        plan_providers=allowed_providers,
    )

    return {
        "status": "ok",
        "message": result.message,
        "token": result.token,
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "email_hash": user.email_hash,
            "plan_id": user.plan_id,
        },
        "keys_generated": len(keys),
        "providers": allowed_providers,
    }


@app.post("/auth/login")
async def api_auth_login(request: Request):
    """Login utente con email + password."""
    body = await request.json()
    email = str(body.get("email", "")).strip()
    password = str(body.get("password", "")).strip()

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email e password obbligatori")

    auth = get_user_auth()
    result = auth.login(email=email, password=password)

    if not result.success:
        raise HTTPException(status_code=401, detail=result.message)
    user = result.user
    assert user is not None

    return {
        "status": "ok",
        "message": result.message,
        "token": result.token,
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "email_hash": user.email_hash,
            "plan_id": user.plan_id,
        },
    }


@app.get("/auth/verify")
async def api_auth_verify(request: Request):
    """Verifica token corrente e restituisce profilo utente."""
    user = await _require_user(request)
    sub_mgr = get_subscription_manager()
    plan = sub_mgr.get_plan(user.plan_id)

    return {
        "status": "ok",
        "authenticated": True,
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "email_hash": user.email_hash,
            "plan_id": user.plan_id,
            "activated_at": user.activated_at,
            "last_login": user.last_login,
        },
        "plan": {
            "name": plan.name if plan else "unknown",
            "providers": plan.providers if plan else [],
            "features": plan.features if plan else [],
        },
    }


@app.post("/auth/logout")
async def api_auth_logout(request: Request):
    """Logout — revoca il token corrente."""
    token = _extract_user_token(request)
    if not token:
        raise HTTPException(status_code=400, detail="Nessun token fornito")
    auth = get_user_auth()
    auth.logout(token)
    return {"status": "ok", "message": "Logout effettuato"}


# ═══════════════════════════════════════════════
# VIO API KEYS — Gestione chiavi per utente
# ═══════════════════════════════════════════════


@app.get("/keys/list")
async def api_keys_list(request: Request):
    """Lista tutte le VIO API keys dell'utente (mascherate)."""
    user = await _require_user(request)
    vault = get_key_vault()
    keys = vault.get_user_keys(user.user_id)
    return {
        "status": "ok",
        "user_id": user.user_id,
        "keys": keys,
        "total": len(keys),
    }


@app.post("/keys/regenerate")
async def api_keys_regenerate(request: Request):
    """Rigenera la VIO key per un provider specifico."""
    user = await _require_user(request)
    body = await request.json()
    provider = str(body.get("provider", "")).strip()

    if not provider:
        raise HTTPException(status_code=400, detail="Provider obbligatorio")

    # Verificare che il provider sia nel piano dell'utente
    sub_mgr = get_subscription_manager()
    if not sub_mgr.can_use_provider(user.plan_id, provider):
        raise HTTPException(
            status_code=403,
            detail=f"Provider '{provider}' non incluso nel tuo piano ({user.plan_id})"
        )

    vault = get_key_vault()
    new_key = vault.regenerate_key(
        user_id=user.user_id,
        email_hash=user.email_hash,
        provider=provider,
    )

    if not new_key:
        raise HTTPException(status_code=500, detail="Errore rigenerazione chiave")

    return {
        "status": "ok",
        "provider": provider,
        "vio_key": new_key.vio_key[:12] + "..." + new_key.vio_key[-4:],
        "created_at": new_key.created_at,
    }


@app.post("/keys/revoke")
async def api_keys_revoke(request: Request):
    """Revoca la VIO key per un provider specifico."""
    user = await _require_user(request)
    body = await request.json()
    provider = str(body.get("provider", "")).strip()

    if not provider:
        raise HTTPException(status_code=400, detail="Provider obbligatorio")

    vault = get_key_vault()
    vault.revoke_key(user.user_id, provider)
    return {"status": "ok", "provider": provider, "revoked": True}


# ═══════════════════════════════════════════════
# SUBSCRIPTION — Piani e abbonamenti
# ═══════════════════════════════════════════════


@app.get("/subscription/plans")
async def api_subscription_plans():
    """Lista tutti i piani disponibili (pubblico, no auth)."""
    sub_mgr = get_subscription_manager()
    return {
        "status": "ok",
        "plans": sub_mgr.get_all_plans(),
    }


@app.get("/subscription/current")
async def api_subscription_current(request: Request):
    """Piano corrente dell'utente autenticato."""
    user = await _require_user(request)
    sub_mgr = get_subscription_manager()
    plan = sub_mgr.get_plan(user.plan_id)
    rate = sub_mgr.check_rate_limit(user.user_id, user.plan_id)

    return {
        "status": "ok",
        "plan_id": user.plan_id,
        "plan": {
            "name": plan.name if plan else "unknown",
            "name_it": plan.name_it if plan else "sconosciuto",
            "providers": plan.providers if plan else [],
            "features": plan.features if plan else [],
            "max_requests_day": plan.max_requests_day if plan else 0,
            "max_requests_month": plan.max_requests_month if plan else 0,
            "price_monthly_eur": plan.price_monthly_eur if plan else 0,
        },
        "usage": rate,
    }


@app.post("/subscription/upgrade")
async def api_subscription_upgrade(request: Request):
    """Upgrade piano utente (dopo verifica pagamento)."""
    user = await _require_user(request)
    body = await request.json()
    new_plan_id = str(body.get("plan_id", "")).strip()

    sub_mgr = get_subscription_manager()
    new_plan = sub_mgr.get_plan(new_plan_id)
    if not new_plan:
        raise HTTPException(status_code=400, detail=f"Piano non valido: {new_plan_id}")

    # Aggiorna piano utente
    auth = get_user_auth()
    auth.update_plan(user.user_id, new_plan_id)

    # Rigenera chiavi per i nuovi provider
    vault = get_key_vault()
    allowed = sub_mgr.get_allowed_providers(new_plan_id)
    new_keys = vault.generate_keys_for_user(
        user_id=user.user_id,
        email_hash=user.email_hash,
        plan_providers=allowed,
    )

    return {
        "status": "ok",
        "old_plan": user.plan_id,
        "new_plan": new_plan_id,
        "providers": allowed,
        "keys_generated": len(new_keys),
    }


# ═══════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Stato di salute completo del sistema."""
    cached = _cached_metadata("health", ttl=5.0)
    if cached:
        return cached

    ollama = await check_ollama_status()

    providers = {
        "ollama": {
        "available": ollama["available"],
        "mode": "local",
        "name": "Ollama (Locale)",
        "models": ollama.get("models", []),
        },
        "policy": _get_orchestration_policy(),
    }

    rag_stats = {"total_documents": 0, "status": "disabled"}
    if RAG_AVAILABLE:
        try:
            rag = get_rag_engine()
            rag_stats = rag.get_stats()
        except Exception:
            pass

    result = HealthResponse(
        status="ok",
        version="0.9.0",
        providers=providers,
        rag_stats=rag_stats,
        uptime_seconds=round(time.time() - START_TIME, 1),
    )
    _set_metadata_cache("health", result, ttl=5.0)
    return result


@app.get("/auth/status")
async def auth_status():
    """Stato autenticazione admin locale (PIN via header)."""
    enabled = bool((os.environ.get(_ADMIN_PIN_ENV, "") or "").strip())
    return {
        "status": "ok",
        "admin_auth": {
            "enabled": enabled,
            "header": _ADMIN_PIN_HEADER,
            "protected": [
                "runtime/apps/*",
                "orchestration/profile (PUT)",
                "knowledge policy/scheduler (PUT)",
                "cache admin actions",
                "autonomy admin actions",
            ],
        },
    }


# ═══════════════════════════════════════════════
# CHAT — Non-streaming
# ═══════════════════════════════════════════════

_CHAT_CONTEXT_MAX_MESSAGES = int(os.environ.get("VIO_CHAT_CONTEXT_MAX_MESSAGES", "16"))
_CHAT_CONTEXT_MAX_CHARS = int(os.environ.get("VIO_CHAT_CONTEXT_MAX_CHARS", "14000"))


def _trim_chat_messages(messages: list[dict[str, Any]], max_messages: int = _CHAT_CONTEXT_MAX_MESSAGES, max_chars: int = _CHAT_CONTEXT_MAX_CHARS) -> list[dict[str, Any]]:
    """Mantiene solo la finestra recente di messaggi per ridurre latenza e token cost."""
    if len(messages) <= 1:
        return messages

    selected: list[dict[str, Any]] = []
    total_chars = 0

    for message in reversed(messages):
        content = str(message.get("content", "") or "")
        message_len = len(content)
        must_keep = len(selected) == 0  # ultimo messaggio sempre presente

        if not must_keep:
            if len(selected) >= max_messages:
                break
            if total_chars + message_len > max_chars:
                break

        selected.append(message)
        total_chars += message_len

    selected.reverse()
    return selected

def _build_vision_message(text: str, images: list) -> dict:
    """
    Costruisce un messaggio in formato OpenAI vision (multi-content).
    Compatibile con: GPT-4V, Claude 3+, Gemini, Ollama llava.
    """
    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for img in images:
        if img.get("data_url"):
            # Extract base64 data from data URL
            data_url = img["data_url"]
            if "," in data_url:
                header, b64_data = data_url.split(",", 1)
                mime = header.split(":")[1].split(";")[0] if ":" in header else "image/png"
            else:
                b64_data = data_url
                mime = img.get("mime_type", "image/png")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64_data}", "detail": "high"},
            })
        elif img.get("url"):
            content.append({
                "type": "image_url",
                "image_url": {"url": img["url"], "detail": "high"},
            })
    return {"role": "user", "content": content}


# Vision-capable providers (priority order)
_VISION_PROVIDERS = ["claude", "openai", "gemini", "groq", "openrouter"]


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat principale — instrada la richiesta al provider migliore. Supporta vision/multimodal e agent mode."""
    try:
        runtime_mode = request.mode or "local"

        # === AGENT MODE: delega a OpenClaw per task multi-step ===
        if request.agent_mode:
            from backend.openclaw.agent import run_agent
            registry = _get_plugin_registry()
            agent_result = await run_agent(
                task=request.message,
                model=request.model or "qwen2.5-coder:3b",
                provider=request.provider or "ollama",
                registry=registry,
            )
            content = agent_result.answer
            tools_info = ""
            if agent_result.tools_used:
                tools_info = f"\n\n🔧 Tools: {', '.join(agent_result.tools_used)}"
            return ChatResponse(
                content=content + tools_info,
                provider="openclaw",
                model=request.model or "qwen2.5-coder:3b",
                tokens_used=0,
                latency_ms=agent_result.total_latency_ms,
                request_type="automation",
            )

        # === VISION MODE: immagini allegate ===
        has_images = bool(request.images)
        if has_images:
            # Force cloud mode for vision (Ollama llava supportato ma limitato)
            runtime_mode = "cloud"
            images_dicts = [img.dict() for img in request.images] if request.images else []
            vision_message = _build_vision_message(request.message, images_dicts)
            messages = [vision_message]
        else:
            messages = [{"role": "user", "content": request.message}]

        conv = get_conversation(request.conversation_id) if request.conversation_id else None

        # ✈️  JetEngine™: cache semantica ultra-veloce + routing intelligente
        _jet = get_jet_engine()
        _history_len = 0
        if conv and conv.get("messages"):
            _history_len = len(conv["messages"])

        _jet_decision = _jet.decide(
            message=request.message,
            model=request.model or "auto",
            runtime_mode=runtime_mode,
            explicit_provider=request.provider,
            available_cloud=None,
            history_len=_history_len,
        )

        # TurboCache hit → risposta istantanea (<2ms)
        if _jet_decision.cache_hit and not request.conversation_id and not request.system_prompt:
            _structured_logger.info(json.dumps({"event": "jet_cache_hit", "intent": _jet_decision.profile.intent}))
            cached_resp = _jet_decision.cached_resp or {}
            return ChatResponse(
                content=str(cached_resp.get("content", "")),
                provider=str(cached_resp.get("provider", "ollama")),
                model=str(cached_resp.get("model", request.model or "qwen2.5-coder:3b")),
                tokens_used=int(cached_resp.get("tokens_used", 0) or 0),
                latency_ms=int(cached_resp.get("latency_ms", 0) or 0),
                request_type=str(cached_resp.get("request_type", "general")),
            )

        chosen_provider = request.provider or ("ollama" if runtime_mode == "local" else "claude")

        # Applica routing JetEngine™ (local-first / parallel-sprint)
        if not has_images and not request.provider:
            routed_provider = _jet_decision.routing.provider
            if routed_provider != "cache":
                chosen_provider = routed_provider

        # Se c'è una conversazione, recupera il contesto
        if conv and conv.get("messages"):
            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in conv["messages"]
            ]
            messages.append({"role": "user", "content": request.message})

        messages = _trim_chat_messages(messages)

        # System prompt
        if request.system_prompt:
            messages.insert(0, {"role": "system", "content": request.system_prompt})

        # Orchestratore con timeout guardrail
        effective_max_tokens = _cap_request_tokens(request.max_tokens)
        effective_temperature = _effective_temperature(request.temperature)

        # Per vision: scegli provider cloud con vision capability
        if has_images:
            # Se il provider scelto non supporta vision, usa claude come fallback
            if chosen_provider not in _VISION_PROVIDERS:
                chosen_provider = "claude"
            effective_max_tokens = max(effective_max_tokens, 1024)  # vision needs more tokens

        _orchestrate_timeout = float(os.environ.get("VIO_CHAT_TIMEOUT_SEC", "120"))
        try:
            result = await asyncio.wait_for(
                orchestrate(
                    messages=messages,
                    mode=runtime_mode,
                    provider=chosen_provider,
                    model=request.model,
                    ollama_model=request.model or "qwen2.5-coder:3b",
                    auto_routing=not has_images,  # no auto-routing for vision (provider forced)
                    temperature=effective_temperature,
                    max_tokens=effective_max_tokens,
                ),
                timeout=_orchestrate_timeout,
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail=f"Timeout: l'orchestratore non ha risposto entro {_orchestrate_timeout:.0f}s",
            )

        # Salva nel database
        conv_id = request.conversation_id
        if not conv_id:
            title = auto_title_from_message(request.message)
            conv_data = create_conversation(title=title, mode=runtime_mode)
            conv_id = conv_data["id"]

        add_message(conv_id, "user", request.message)
        add_message(conv_id, "assistant", result["content"],
                    provider=result["provider"], model=result["model"],
                    tokens_used=result.get("tokens_used", 0),
                    latency_ms=result.get("latency_ms", 0))

        # Log metrica
        log_metric(
            provider=result["provider"], model=result["model"],
            request_type=str(result.get("request_type", "general")),
            tokens_used=result.get("tokens_used", 0),
            latency_ms=result.get("latency_ms", 0),
        )

        AUTONOMOUS_RUNTIME.record_chat_turn(
            conversation_id=conv_id,
            user_message=request.message,
            assistant_message=result["content"],
            provider=result["provider"],
            model=result["model"],
            mode=runtime_mode,
        )

        chat_response = ChatResponse(
            content=result["content"],
            provider=result["provider"],
            model=result["model"],
            tokens_used=result.get("tokens_used", 0),
            latency_ms=result.get("latency_ms", 0),
            request_type=str(result.get("request_type", "general")),
        )

        # ✈️  JetEngine™: salva risposta nel TurboCache semantico
        if not request.conversation_id and not request.system_prompt:
            _jet.cache_store(request.message, request.model or "auto", {
                "content": result["content"],
                "provider": result["provider"],
                "model": result["model"],
                "tokens_used": result.get("tokens_used", 0),
                "latency_ms": result.get("latency_ms", 0),
                "request_type": result.get("request_type"),
            })

        return chat_response

    except HTTPException:
        raise
    except Exception as e:
        error_handler = get_error_handler()
        error_handler.handle(e, context={
            "endpoint": "/chat",
            "mode": request.mode,
            "provider": request.provider,
            "model": request.model,
        })
        log_metric(
            provider="ollama",
            model=request.model or "unknown",
            success=False, error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════
# CHAT — Streaming SSE
# ═══════════════════════════════════════════════

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Chat con Server-Sent Events (SSE) — streaming token per token.
    Il frontend riceve ogni token in tempo reale.
    """
    runtime_mode = request.mode or "local"
    messages = [{"role": "user", "content": request.message}]

    if request.conversation_id:
        conv = get_conversation(request.conversation_id)
        if conv and conv.get("messages"):
            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in conv["messages"]
            ]
            messages.append({"role": "user", "content": request.message})

    messages = _trim_chat_messages(messages)

    if request.system_prompt:
        messages.insert(0, {"role": "system", "content": request.system_prompt})

    # 🪶 FeatherMemory™: comprimi messaggi + alloca token ottimale
    _fm = get_feather_memory()
    _fm_prepared = _fm.prepare(
        message=request.message,
        conversation_id=request.conversation_id,
        history=[{"role":m["role"],"content":m["content"]} for m in messages] if len(messages) > 1 else None,
        provider="ollama",
        intent="simple",
    )
    # Usa messaggi compressi al posto dei raw
    if _fm_prepared["compression"]["savings_percent"] > 5:
        messages = _fm_prepared["messages"]

    # Inietta system prompt SPECIALIZZATO per tipo di richiesta
    from backend.orchestrator.direct_router import classify_request as _classify
    from backend.orchestrator.system_prompt import build_local_system_prompt
    has_system = any(m.get("role") == "system" for m in messages)
    if not has_system:
        req_type = _classify(request.message)
        system_prompt = build_local_system_prompt(req_type)

        # === RAG CONTEXT INJECTION ===
        # Cerca nella Knowledge Base e inietta fonti certificate nel contesto
        if KB_AVAILABLE:
            try:
                kb = get_knowledge_base()
                rag_ctx = kb.build_rag_context(request.message, max_context_tokens=1500)
                if rag_ctx.get("has_context") and rag_ctx.get("context_text"):
                    system_prompt += (
                        f"\n\n=== FONTI CERTIFICATE DALLA KNOWLEDGE BASE ===\n"
                        f"Dominio: {rag_ctx['domain']} | Confidenza: {rag_ctx['confidence']}\n"
                        f"Usa queste fonti per supportare e verificare la tua risposta:\n\n"
                        f"{rag_ctx['context_text']}\n"
                        f"=== FINE FONTI ==="
                    )
            except Exception as e:
                print(f"[KB] Errore context injection: {e}")

        messages.insert(0, {"role": "system", "content": system_prompt})

    model = request.model or "llama3.2:3b"
    effective_max_tokens = _cap_request_tokens(request.max_tokens)
    effective_temperature = _effective_temperature(request.temperature)

    async def event_generator():
        full_content = ""
        start = time.time()
        try:
            async for token in call_ollama_streaming(
                messages=messages,
                model=model,
                temperature=effective_temperature,
                max_tokens=effective_max_tokens,
            ):
                full_content += token
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

            latency = int((time.time() - start) * 1000)
            yield f"data: {json.dumps({'token': '', 'done': True, 'full_content': full_content, 'latency_ms': latency, 'model': model, 'provider': 'ollama'})}\n\n"

            # Salva nel database
            conv_id = request.conversation_id
            if not conv_id:
                title = auto_title_from_message(request.message)
                conv_data = create_conversation(title=title, mode=runtime_mode)
                conv_id = conv_data["id"]

            add_message(conv_id, "user", request.message)
            add_message(conv_id, "assistant", full_content,
                        provider="ollama", model=model,
                        latency_ms=latency)
            log_metric("ollama", model, tokens_used=0, latency_ms=latency)
            AUTONOMOUS_RUNTIME.record_chat_turn(
                conversation_id=conv_id,
                user_message=request.message,
                assistant_message=full_content,
                provider="ollama",
                model=model,
                mode=runtime_mode,
            )

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ═══════════════════════════════════════════════
# ═══════════════════════════════════════════════
# JET ENGINE™ — Stats & Control endpoints
# ═══════════════════════════════════════════════

@app.get("/ultra/stats")
async def ultra_stats():
    """JetEngine™ performance stats — velocità in tempo reale."""
    jet = get_jet_engine()
    stats = jet.stats()
    # Aggiungi info taxonomy
    try:
        from backend.core.knowledge_taxonomy import taxonomy_stats
        stats["taxonomy"] = taxonomy_stats()
    except Exception as e:
        stats["taxonomy"] = {"error": str(e)}
    # Aggiungi info ultra_engine (Piuma)
    try:
        from backend.core.ultra_engine import get_ultra_engine
        ue = get_ultra_engine()
        cache_obj = getattr(ue, "cache", None)
        cache_store = getattr(cache_obj, "_cache", {}) if cache_obj is not None else {}
        provider_memory_obj = getattr(ue, "provider_memory", None)
        provider_stats = getattr(provider_memory_obj, "_stats", {}) if provider_memory_obj is not None else {}
        stats["piuma_engine"] = {
            "cache_size": len(cache_store) if isinstance(cache_store, dict) else 0,
            "provider_memory": len(provider_stats) if isinstance(provider_stats, dict) else 0,
        }
    except Exception as e:
        stats["piuma_engine"] = {"error": str(e)}
    # FeatherMemory stats
    try:
        fm = get_feather_memory()
        stats["feather_memory"] = fm.stats
    except Exception as e:
        stats["feather_memory"] = {"error": str(e)}
    # HyperCompressor stats
    try:
        hc = get_hyper_compressor()
        stats["hyper_compressor"] = hc.stats
    except Exception as e:
        stats["hyper_compressor"] = {"error": str(e)}
    return {"status": "ok", "jet_engine": stats, "timestamp": time.time()}

@app.post("/ultra/classify")
async def ultra_classify(request: dict = Body(...)):
    """Classifica una query: intento, complessità, provider ottimale."""
    message = request.get("message", "")
    if not message:
        raise HTTPException(400, "message required")
    jet = get_jet_engine()
    decision = jet.decide(message=message, runtime_mode=request.get("mode", "hybrid"))
    try:
        from backend.core.knowledge_taxonomy import classify_text, get_optimal_config
        tax_results = classify_text(message, max_results=3)
        tax_config  = get_optimal_config(message)
        taxonomy_match = [
            {"node_id": nid, "name": node.name_it, "score": sc}
            for nid, node, sc in tax_results
        ]
    except Exception:
        taxonomy_match = []
        tax_config = {}
    return {
        "complexity": {
            "score":       decision.profile.score,
            "intent":      decision.profile.intent,
            "local_ok":    decision.profile.local_ok,
            "stream_prio": decision.profile.stream_prio,
            "race_prio":   decision.profile.race_prio,
            "tokens_est":  decision.profile.tokens_est,
        },
        "routing": {
            "provider": decision.routing.provider,
            "model":    decision.routing.model,
            "stream":   decision.routing.stream,
            "race":     decision.routing.race,
            "reason":   decision.routing.reason,
        },
        "cache_hit": decision.cache_hit,
        "taxonomy":  taxonomy_match,
        "optimal_config": tax_config,
    }

# CONVERSAZIONI
# ═══════════════════════════════════════════════

@app.get("/conversations")
async def api_list_conversations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    include_archived: bool = False,
):
    """Lista conversazioni."""
    return list_conversations(limit=limit, offset=offset, include_archived=include_archived)


@app.post("/conversations")
async def api_create_conversation(title: str = "Nuova conversazione", mode: str = "local"):
    """Crea una nuova conversazione."""
    return create_conversation(title=title, mode=mode)


@app.get("/conversations/{conv_id}")
async def api_get_conversation(conv_id: str):
    """Ottieni conversazione con messaggi."""
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return conv


@app.put("/conversations/{conv_id}/title")
async def api_update_title(conv_id: str, title: str):
    """Aggiorna titolo conversazione."""
    update_conversation_title(conv_id, title)
    return {"status": "ok"}


@app.delete("/conversations/{conv_id}")
async def api_delete_conversation(conv_id: str):
    """Elimina conversazione."""
    delete_conversation(conv_id)
    return {"status": "deleted"}


@app.post("/conversations/{conv_id}/archive")
async def api_archive_conversation(conv_id: str):
    """Archivia conversazione."""
    archive_conversation(conv_id)
    return {"status": "archived"}


# ═══════════════════════════════════════════════
# USER FEEDBACK (thumbs up/down)
# ═══════════════════════════════════════════════

@app.post("/feedback")
async def api_user_feedback(
    provider: str = Body(...),
    model: str = Body(""),
    thumbs_up: bool = Body(...),
    message_id: str = Body(""),
):
    """
    Registra feedback reale dell'utente (thumbs up/down).
    Aggiorna il Thompson Sampling bandit nel SelfOptimizer.
    """
    try:
        from backend.core.self_optimizer import get_self_optimizer
        optimizer = get_self_optimizer()
        optimizer.record_user_feedback(provider, model, thumbs_up)
        return {
            "status": "ok",
            "feedback": "positive" if thumbs_up else "negative",
            "provider": provider,
            "model": model,
        }
    except Exception as e:
        logging.error(f"[Feedback] Errore: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════
# CLASSIFY
# ═══════════════════════════════════════════════

@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """Classifica il tipo di richiesta per il routing intelligente."""
    req_type = classify_request(request.message)

    return ClassifyResponse(
        request_type=req_type,
        suggested_provider="ollama",
        confidence=0.85,
    )


# ═══════════════════════════════════════════════
# OLLAMA MANAGEMENT
# ═══════════════════════════════════════════════

@app.get("/ollama/status")
async def api_ollama_status():
    """Stato Ollama e modelli disponibili."""
    return await check_ollama_status()


@app.get("/ollama/models")
async def api_ollama_models():
    """Lista modelli Ollama installati."""
    status = await check_ollama_status()
    if not status["available"]:
        raise HTTPException(status_code=503, detail="Ollama non raggiungibile")
    return {"models": status["models"]}


# ═══════════════════════════════════════════════
# AUTO-LEARNING ENGINES STATUS
# ═══════════════════════════════════════════════

@app.get("/intelligence/status")
async def intelligence_status():
    """Stato dei motori auto-crescenti: learning, optimization, knowledge, reasoning."""
    result = {}
    try:
        from backend.core.auto_learner import get_auto_learner
        result["auto_learner"] = get_auto_learner().get_quality_stats()
    except Exception as e:
        result["auto_learner"] = {"error": str(e)}
    try:
        from backend.core.self_optimizer import get_self_optimizer
        result["self_optimizer"] = get_self_optimizer().get_stats()
    except Exception as e:
        result["self_optimizer"] = {"error": str(e)}
    try:
        from backend.core.world_knowledge import get_world_knowledge
        result["world_knowledge"] = get_world_knowledge().get_stats()
    except Exception as e:
        result["world_knowledge"] = {"error": str(e)}
    try:
        from backend.core.reasoning_engine import get_reasoning_engine
        result["reasoning_engine"] = get_reasoning_engine().get_stats()
    except Exception as e:
        result["reasoning_engine"] = {"error": str(e)}
    return result


# ═══════════════════════════════════════════════
# PROVIDERS
# ═══════════════════════════════════════════════

@app.get("/providers")
async def list_providers():
    """Lista provider runtime effettivi — rispetta VIO_NO_HYBRID da .env."""
    ollama = await check_ollama_status()
    no_hybrid = _as_bool(os.environ.get("VIO_NO_HYBRID", ""))

    local = {
        "ollama": {
            "name": "Ollama (Locale)",
            "available": ollama["available"],
            "cost": "free",
            "default_model": LOCAL_PROVIDERS["ollama"]["default_model"],
            "models": ollama.get("models", []),
            "installed_models": [m["name"] for m in ollama.get("models", [])],
        }
    }

    if no_hybrid:
        return {
            "local": local,
            "free_cloud": {},
            "paid_cloud": {},
            "all_ordered": [
                {"id": "ollama", "name": "Ollama (Locale)", "tier": "local", "available": ollama["available"]}
            ],
            "policy": {
                "no_hybrid": True,
                "cloud_runtime_enabled": False,
                "note": "VIO_NO_HYBRID=true nel .env — solo Ollama locale attivo.",
            },
        }

    # Cloud abilitato: restituisci tutti i provider configurati
    free_cloud = get_free_cloud_providers()
    paid_cloud = get_available_cloud_providers()
    all_ordered = get_all_providers_ordered()

    return {
        "local": local,
        "free_cloud": free_cloud,
        "paid_cloud": paid_cloud,
        "all_ordered": all_ordered,
        "policy": {
            "no_hybrid": False,
            "cloud_runtime_enabled": True,
            "note": "L'utente può scegliere tra locale e cloud. API keys necessarie per provider cloud.",
        },
    }


@app.get("/orchestration/elite-stacks")
async def api_orchestration_elite_stacks():
    """Stack consigliati ad alta specializzazione per task complessi e replica locale/proxy."""
    payload = get_elite_task_stacks()
    return {
        "status": "ok",
        "generated_at": _now_iso(),
        "stacks": payload,
        "notes": [
            "Replica 100% identica di LegalRoom/OpenClaw non onestamente garantibile senza codice e workflow originali.",
            "Replica ad alta fedeltà di capacità, orchestrazione e runtime locale/proxy è invece implementabile e già parzialmente presente nel progetto.",
            "Per task medico-legali è consigliata la strict evidence policy con knowledge base e fonti certificate.",
        ],
    }


@app.get("/orchestration/profile")
async def api_orchestration_profile():
    """Profilo orchestrazione runtime — legge policy da .env."""
    env_map = _read_project_env_map()
    profile = _runtime_env_value(env_map, "VIO_EXECUTION_PROFILE") or "real-max-local"
    no_hybrid = _as_bool(_runtime_env_value(env_map, "VIO_NO_HYBRID"))
    local_preference = _runtime_env_value(env_map, "VIO_LOCAL_MODEL_PREFERENCE") or "qwen2.5-coder:3b"

    effective_mode = "local-only" if no_hybrid else "dual-mode"
    notes = (
        [
            "Policy no-hybrid attiva: solo Ollama locale",
            "Per abilitare cloud: imposta VIO_NO_HYBRID=false nel .env",
        ]
        if no_hybrid
        else [
            "Dual-mode attivo: locale + cloud disponibili",
            "L'utente può scegliere tra Ollama locale e provider cloud con API key",
        ]
    )

    return {
        "status": "ok",
        "profile": profile,
        "no_hybrid": no_hybrid,
        "local_model_preference": local_preference,
        "effective_mode": effective_mode,
        "notes": notes,
    }


@app.put("/orchestration/profile")
async def api_set_orchestration_profile(
    profile: str = Query("real-max-local"),
    no_hybrid: bool = Query(True),
    local_model_preference: str = Query("qwen2.5-coder:3b"),
):
    """Imposta profilo orchestrazione persistente nel .env e ricarica runtime env."""
    normalized = (profile or "").strip().lower() or "real-max-local"
    allowed = {"balanced", "real-max", "real-max-local", "ultra-local", "local-only"}
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail=f"Profilo non valido: {profile}")

    local_pref = (local_model_preference or "qwen2.5-coder:3b").strip() or "qwen2.5-coder:3b"

    updates = {
        "VIO_EXECUTION_PROFILE": normalized,
        "VIO_NO_HYBRID": "false" if not no_hybrid else "true",
        "VIO_LOCAL_MODEL_PREFERENCE": local_pref,
    }

    _write_project_env_updates(updates)
    load_dotenv(PROJECT_ENV_PATH, override=True)

    effective_mode = "local-only" if no_hybrid else "dual-mode"

    return {
        "status": "ok",
        "updated": updates,
        "requested": {
            "profile": profile,
            "no_hybrid": no_hybrid,
            "local_model_preference": local_model_preference,
        },
        "effective_mode": effective_mode,
    }


# ═══════════════════════════════════════════════
# METRICHE
# ═══════════════════════════════════════════════

@app.get("/metrics")
async def api_metrics(days: int = Query(30, ge=1, le=365)):
    """Metriche e analytics degli ultimi N giorni."""
    return get_metrics_summary(days=days)


# ═══════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════

@app.get("/settings")
async def api_get_settings():
    """Ottieni tutte le impostazioni."""
    return get_all_settings()


@app.put("/settings/{key}")
async def api_set_setting(key: str, value: str):
    """Aggiorna un'impostazione."""
    set_setting(key, value)
    return {"status": "ok", "key": key}


# ═══════════════════════════════════════════════
# RAG (opzionale)
# ═══════════════════════════════════════════════

@app.post("/rag/add")
async def rag_add_source(request: RAGAddRequest):
    """Aggiungi fonte certificata al database RAG."""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG Engine non disponibile")
    rag = get_rag_engine()
    source = RAGSource(
        title=request.title, content=request.content,
        source_type=request.source_type, url=request.url,
        author=request.author, year=request.year,
        reliability_score=request.reliability_score,
    )
    doc_id = rag.add_source(source)
    return {"doc_id": doc_id, "status": "added"}


@app.post("/rag/search")
async def rag_search(request: RAGSearchRequest):
    """Cerca nelle fonti certificate."""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG Engine non disponibile")
    rag = get_rag_engine()
    result = rag.search(request.query, n_results=request.n_results, min_score=request.min_score)
    return {
        "query": result.query, "matches": result.matches,
        "verified": result.verified, "confidence": result.confidence,
        "sources_used": result.sources_used,
    }


@app.get("/rag/stats")
async def rag_stats():
    """Statistiche database RAG."""
    if not RAG_AVAILABLE:
        return {"total_documents": 0, "status": "disabled", "reason": "ChromaDB non compatibile"}
    rag = get_rag_engine()
    return rag.get_stats()


# ═══════════════════════════════════════════════
# KNOWLEDGE BASE v2 — Biblioteca Digitale Completa
# ═══════════════════════════════════════════════

@app.get("/kb/stats")
async def kb_stats():
    """Statistiche Knowledge Base — biblioteca digitale."""
    if not KB_AVAILABLE:
        return {
            "status": "disabled",
            "reason": KB_IMPORT_ERROR or "Knowledge Base non inizializzata",
        }
    kb = get_knowledge_base()
    return kb.get_stats()


@app.post("/kb/ingest/text")
async def kb_ingest_text(
    text: str,
    title: str = "",
    author: str = "",
    source_type: str = "manual",
    reliability: float = 1.0,
):
    """Ingesci testo diretto nella knowledge base."""
    if not KB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Knowledge Base non disponibile")
    kb = get_knowledge_base()
    chunk_count = kb.ingest_text(
        text=text, title=title, author=author,
        source_type=source_type, reliability=reliability,
    )
    return {"status": "ok", "chunks_created": chunk_count, "title": title}


@app.post("/kb/ingest/file")
async def kb_ingest_file(
    filepath: str,
    source_type: str = "book",
    reliability: float = 1.0,
):
    """Ingesci un file nella knowledge base (PDF, DOCX, EPUB, TXT, HTML, JSON, CSV)."""
    if not KB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Knowledge Base non disponibile")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"File non trovato: {filepath}")
    kb = get_knowledge_base()
    doc = kb.ingest_file(filepath, source_type=source_type, reliability=reliability)
    return {
        "status": doc.status,
        "doc_id": doc.doc_id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "title": doc.title,
        "author": doc.author,
        "language": doc.language,
        "word_count": doc.word_count,
        "chunk_count": doc.chunk_count,
        "error": doc.error,
    }


@app.post("/kb/ingest/directory")
async def kb_ingest_directory(
    directory: str,
    recursive: bool = True,
    source_type: str = "book",
    reliability: float = 1.0,
):
    """Ingesci tutti i file da una directory nella knowledge base."""
    if not KB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Knowledge Base non disponibile")
    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"Directory non trovata: {directory}")
    kb = get_knowledge_base()
    docs = kb.ingest_directory(directory, recursive=recursive,
                                source_type=source_type, reliability=reliability)
    return {
        "status": "ok",
        "files_processed": len([d for d in docs if d.status == "success"]),
        "files_failed": len([d for d in docs if d.status == "error"]),
        "total_chunks": sum(d.chunk_count for d in docs),
        "total_words": sum(d.word_count for d in docs),
        "details": [
            {"filename": d.filename, "status": d.status,
             "chunks": d.chunk_count, "error": d.error}
            for d in docs
        ],
    }


@app.post("/kb/query")
async def kb_query(
    question: str,
    n_results: int = 10,
    min_reliability: float = 0.5,
    domain_filter: Optional[str] = None,
):
    """Cerca nella knowledge base con retrieval semantico + reranking."""
    if not KB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Knowledge Base non disponibile")
    kb = get_knowledge_base()
    results = kb.query(
        question=question, n_results=n_results,
        min_reliability=min_reliability, domain_filter=domain_filter,
    )
    return {"query": question, "results": results, "count": len(results)}


@app.post("/kb/context")
async def kb_build_context(
    question: str,
    max_context_tokens: int = 2000,
    n_results: int = 5,
):
    """Costruisci contesto RAG per una domanda (da iniettare nel prompt AI)."""
    if not KB_AVAILABLE:
        return {"context_text": "", "sources": [], "has_context": False}
    kb = get_knowledge_base()
    return kb.build_rag_context(
        question=question,
        max_context_tokens=max_context_tokens,
        n_results=n_results,
    )


# ═══════════════════════════════════════════════
# CLAUDE DESKTOP INTEGRATION
# ═══════════════════════════════════════════════

@app.get("/claude/extensions")
async def api_claude_extensions():
    """Rileva estensioni MCP installate in Claude Desktop (macOS)."""
    import pathlib

    ext_path = pathlib.Path.home() / "Library" / "Application Support" / "Claude" / "extensions-installations.json"
    cfg_path = pathlib.Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"

    extensions = []
    preferences: dict = {}

    if ext_path.exists():
        try:
            raw = json.loads(ext_path.read_text())
            for _ext_id, data in raw.get("extensions", {}).items():
                manifest = data.get("manifest", {})
                tools = manifest.get("tools", [])
                extensions.append({
                    "id": data.get("id", _ext_id),
                    "name": manifest.get("display_name") or manifest.get("name") or _ext_id,
                    "version": data.get("version"),
                    "description": manifest.get("description", ""),
                    "tool_count": len(tools),
                    "tools": [t.get("name") for t in tools[:12]],
                    "installed_at": data.get("installedAt"),
                    "source": data.get("source", "registry"),
                })
        except Exception as e:
            return {"status": "error", "error": str(e), "extensions": [], "preferences": {}}

    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text())
            prefs = cfg.get("preferences", {})
            preferences = {
                "coworkEnabled": prefs.get("coworkScheduledTasksEnabled", False),
                "webSearchEnabled": prefs.get("coworkWebSearchEnabled", False),
                "keepAwake": prefs.get("keepAwakeEnabled", False),
                "sidebarMode": prefs.get("sidebarMode", ""),
            }
        except Exception:
            pass

    return {
        "status": "ok",
        "extensions": extensions,
        "count": len(extensions),
        "preferences": preferences,
        "detected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.get("/claude/activity-summary")
async def api_claude_activity_summary():
    """Sintesi attività locale di Claude Desktop per audit tecnico (macOS)."""
    import pathlib

    base_path = pathlib.Path.home() / "Library" / "Application Support" / "Claude"
    sessions_root = base_path / "local-agent-mode-sessions"
    sessions_index_path = sessions_root / "sessions-index.json"

    workspace_count = 0
    session_count = 0
    audit_files_count = 0
    latest_session_id: Optional[str] = None
    latest_session_updated_at: Optional[str] = None
    latest_session_mtime = 0.0

    if sessions_root.exists() and sessions_root.is_dir():
        for workspace_dir in sessions_root.iterdir():
            if not workspace_dir.is_dir():
                continue
            workspace_count += 1

            for session_dir in workspace_dir.iterdir():
                if not session_dir.is_dir():
                    continue

                session_count += 1
                try:
                    st = session_dir.stat()
                    if st.st_mtime > latest_session_mtime:
                        latest_session_mtime = st.st_mtime
                        latest_session_id = session_dir.name
                        latest_session_updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime))
                except Exception:
                    pass

                try:
                    audit_files_count += sum(1 for _ in session_dir.glob("local_*/audit.jsonl"))
                except Exception:
                    pass

    indexed_sessions = 0
    if sessions_index_path.exists():
        try:
            raw = json.loads(sessions_index_path.read_text())
            if isinstance(raw, dict):
                sessions_val = raw.get("sessions")
                if isinstance(sessions_val, list):
                    indexed_sessions = len(sessions_val)
                elif isinstance(sessions_val, dict):
                    indexed_sessions = len(sessions_val.keys())
        except Exception:
            pass

    return {
        "status": "ok",
        "sessions": {
            "workspace_count": workspace_count,
            "session_count": session_count,
            "indexed_sessions": indexed_sessions,
            "audit_files": audit_files_count,
            "latest_session_id": latest_session_id,
            "latest_session_updated_at": latest_session_updated_at,
        },
        "paths": {
            "base": str(base_path),
            "sessions_root": str(sessions_root),
            "sessions_index": str(sessions_index_path),
        },
        "detected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ═══════════════════════════════════════════════
# GLOBAL VERIFIED KNOWLEDGE STACK
# ═══════════════════════════════════════════════

@app.get("/knowledge/registry")
async def api_knowledge_registry():
    """Catalogo domini ultra-specializzati con fonti certificate e tracciamento globale."""
    return _build_knowledge_registry_payload()


@app.get("/knowledge/legal-watch")
async def api_knowledge_legal_watch(jurisdiction: str = Query("global")):
    """Fonti legali monitorate per giurisdizione (global/eu/it/us/all)."""
    if jurisdiction != "all" and jurisdiction not in GLOBAL_LEGAL_WATCH:
        raise HTTPException(status_code=404, detail=f"Giurisdizione non supportata: {jurisdiction}")

    if jurisdiction == "all":
        sources = [source for group in GLOBAL_LEGAL_WATCH.values() for source in group]
    else:
        sources = GLOBAL_LEGAL_WATCH[jurisdiction]

    return {
        "status": "ok",
        "jurisdiction": jurisdiction,
        "sources": sources,
        "refresh_state": KNOWLEDGE_REFRESH_STATE,
        "detected_at": _now_iso(),
    }


@app.post("/knowledge/refresh")
async def api_knowledge_refresh(jurisdiction: str = Query("all")):
    """Aggiorna lo stato raggiungibilità delle fonti certificate monitorate."""
    if jurisdiction != "all" and jurisdiction not in GLOBAL_LEGAL_WATCH:
        raise HTTPException(status_code=404, detail=f"Giurisdizione non supportata: {jurisdiction}")

    summary = await _refresh_knowledge_watch(jurisdiction)
    return {
        "status": "ok",
        "summary": summary,
    }


@app.get("/knowledge/domain-scores")
async def api_knowledge_domain_scores():
    """Restituisce score affidabilità per dominio specializzato."""
    scores = _compute_domain_scores()
    average = round(sum(item["reliability_score"] for item in scores) / max(1, len(scores)), 1)
    return {
        "status": "ok",
        "scores": scores,
        "average_reliability": average,
        "minimum_required": KNOWLEDGE_POLICY_STATE["minimum_domain_score"],
        "strict_evidence_mode": KNOWLEDGE_POLICY_STATE["strict_evidence_mode"],
        "detected_at": _now_iso(),
    }


@app.get("/knowledge/scheduler")
async def api_knowledge_scheduler():
    """Configurazione scheduler knowledge auto-refresh."""
    return {
        "status": "ok",
        "scheduler": {
            "refresh_interval_hours": KNOWLEDGE_POLICY_STATE["refresh_interval_hours"],
            "next_scheduled_refresh_at": KNOWLEDGE_POLICY_STATE.get("next_scheduled_refresh_at"),
            "last_refresh_at": KNOWLEDGE_REFRESH_STATE.get("last_refresh_at"),
        },
        "policy": {
            "strict_evidence_mode": KNOWLEDGE_POLICY_STATE["strict_evidence_mode"],
            "minimum_domain_score": KNOWLEDGE_POLICY_STATE["minimum_domain_score"],
            "last_policy_update_at": KNOWLEDGE_POLICY_STATE.get("last_policy_update_at"),
        },
    }


@app.put("/knowledge/scheduler")
async def api_set_knowledge_scheduler(
    refresh_interval_hours: int = Query(6, ge=1, le=168),
):
    """Aggiorna intervallo scheduler auto-refresh (in ore)."""
    KNOWLEDGE_POLICY_STATE["refresh_interval_hours"] = int(refresh_interval_hours)
    KNOWLEDGE_POLICY_STATE["last_policy_update_at"] = _now_iso()
    KNOWLEDGE_POLICY_STATE["next_scheduled_refresh_at"] = _iso_from_epoch(time.time() + int(refresh_interval_hours) * 3600.0)
    return {
        "status": "ok",
        "refresh_interval_hours": KNOWLEDGE_POLICY_STATE["refresh_interval_hours"],
        "next_scheduled_refresh_at": KNOWLEDGE_POLICY_STATE["next_scheduled_refresh_at"],
    }


@app.put("/knowledge/policy")
async def api_set_knowledge_policy(
    strict_evidence_mode: bool = Query(True),
    minimum_domain_score: float = Query(70.0, ge=0.0, le=100.0),
):
    """Aggiorna policy qualità: strict evidence + soglia minima dominio."""
    KNOWLEDGE_POLICY_STATE["strict_evidence_mode"] = bool(strict_evidence_mode)
    KNOWLEDGE_POLICY_STATE["minimum_domain_score"] = float(minimum_domain_score)
    KNOWLEDGE_POLICY_STATE["last_policy_update_at"] = _now_iso()
    return {
        "status": "ok",
        "policy": KNOWLEDGE_POLICY_STATE,
    }


# ═══════════════════════════════════════════════
# CORE INFRASTRUCTURE — Cache, Network, Security
# ═══════════════════════════════════════════════

@app.get("/core/cache/stats")
async def api_cache_stats():
    """Statistiche del multi-layer cache engine."""
    cache = get_cache()
    return cache.stats


@app.post("/core/cache/clear")
async def api_cache_clear():
    """Svuota tutta la cache."""
    cache = get_cache()
    cache.clear()
    return {"status": "ok", "message": "Cache svuotata"}


@app.post("/core/cache/cleanup")
async def api_cache_cleanup():
    """Rimuovi entry scadute dalla cache disco."""
    cache = get_cache()
    removed = cache.cleanup()
    return {"status": "ok", "expired_removed": removed}


@app.get("/core/network/stats")
async def api_network_stats():
    """Statistiche di rete: connection pool, circuit breaker, latenze."""
    pool = get_connection_pool()
    return pool.stats


@app.get("/core/network/health/{provider}")
async def api_provider_health(provider: str):
    """Health check specifico per un provider."""
    pool = get_connection_pool()
    return pool.get_provider_health(provider)


@app.get("/core/errors/stats")
async def api_error_stats():
    """Statistiche errori: conteggi, errori recenti, errori più comuni."""
    handler = get_error_handler()
    return handler.stats


@app.get("/core/security/stats")
async def api_security_stats():
    """Stato sicurezza: chiavi API, provider disponibili."""
    vault = get_vault()
    return vault.stats


@app.get("/core/security/validate")
async def api_validate_environment():
    """Validazione completa dell'ambiente di esecuzione."""
    validator = EnvironmentValidator()
    return validator.validate()


@app.get("/core/status")
async def api_core_status():
    """Status completo di tutta l'infrastruttura core."""
    cache = get_cache()
    pool = get_connection_pool()
    handler = get_error_handler()
    vault = get_vault()

    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "cache": cache.stats,
        "network": pool.stats,
        "errors": {
            "total": handler.stats["total_errors"],
            "most_common": handler.stats["most_common"],
        },
        "security": {
            "valid_keys": vault.stats["valid_keys"],
            "available_providers": vault.available_providers,
        },
    }


# ═══════════════════════════════════════════════
# RUNTIME APPS — ANALYSIS / CONFIG / ACTIONS
# ═══════════════════════════════════════════════

@app.get("/runtime/apps/analysis")
async def api_runtime_apps_analysis():
    """Analisi reale di app runtime esterne, dipendenze, stack e configurazione utente."""
    return _runtime_apps_snapshot()


@app.put("/runtime/apps/config")
async def api_runtime_apps_config(payload: dict[str, Any] = Body(...)):
    """Salva configurazione runtime apps nel .env del progetto."""
    updates: dict[str, str] = {}

    field_map = {
        "openclaw_start_cmd": "OPENCLAW_START_CMD",
        "legalroom_start_cmd": "LEGALROOM_START_CMD",
        "n8n_start_cmd": "N8N_START_CMD",
        "openclaw_health_urls": "OPENCLAW_HEALTH_URLS",
        "legalroom_health_urls": "LEGALROOM_HEALTH_URLS",
        "n8n_health_urls": "N8N_HEALTH_URLS",
        "update_policy": "RUNTIME_APPS_UPDATE_POLICY",
        "offline_mode": "RUNTIME_APPS_OFFLINE_MODE",
    }

    for incoming_key, env_key in field_map.items():
        if incoming_key in payload:
            value = payload.get(incoming_key)
            updates[env_key] = "" if value is None else str(value).strip()

    if not updates:
        raise HTTPException(status_code=400, detail="Nessun campo valido da aggiornare")

    if "RUNTIME_APPS_UPDATE_POLICY" in updates or "RUNTIME_APPS_OFFLINE_MODE" in updates:
        updates["RUNTIME_APPS_LAST_USER_APPROVED_AT"] = _now_iso()

    _write_project_env_updates(updates)

    return {
        "status": "ok",
        "updated_keys": list(updates.keys()),
        "snapshot": _runtime_apps_snapshot(),
    }


@app.post("/runtime/apps/action")
async def api_runtime_apps_action(payload: dict[str, Any] = Body(...)):
    """Esegue azioni locali controllate per supervisor/autostart runtime."""
    action = str(payload.get("action", "")).strip()

    actions = {
        "start-supervisor": PROJECT_ROOT / "scripts" / "runtime" / "start_runtime_services.sh",
        "stop-supervisor": PROJECT_ROOT / "scripts" / "runtime" / "stop_runtime_services.sh",
        "install-autostart": PROJECT_ROOT / "install_autostart.sh",
    }

    if action not in actions:
        raise HTTPException(status_code=400, detail=f"Azione non supportata: {action}")

    result = _run_local_script(actions[action], timeout_s=90 if action == "install-autostart" else 45)
    result["snapshot"] = _runtime_apps_snapshot()
    result["action"] = action

    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result)

    return result


# ═══════════════════════════════════════════════
# AUTONOMOUS RUNTIME — Trigger, Memory, Session Namespace
# ═══════════════════════════════════════════════

@app.get("/autonomy/status")
async def api_autonomy_status():
    """Status del runtime autonomo: scheduler, memoria persistente, session namespaces."""
    return AUTONOMOUS_RUNTIME.status()


@app.get("/autonomy/sessions")
async def api_autonomy_sessions():
    """Lista namespace persistenti con contatori note/eventi."""
    return AUTONOMOUS_RUNTIME.list_sessions()


@app.get("/autonomy/sessions/{namespace}/memory")
async def api_autonomy_memory(namespace: str, query: str = Query("")):
    """Recupera memoria persistente da Markdown con summary + snippets."""
    return AUTONOMOUS_RUNTIME.retrieve_context(namespace, query=query)


@app.post("/autonomy/compact")
async def api_autonomy_compact(namespace: str = Query(...)):
    """Compatta esplicitamente una sessione, trattando il contesto come cache."""
    return {
        "status": "ok",
        "result": AUTONOMOUS_RUNTIME.compact_namespace(namespace),
    }


@app.post("/autonomy/trigger")
async def api_autonomy_trigger(payload: dict[str, Any] = Body(...)):
    """Trigger manuale/API: webhook, messaggio esterno, job, heartbeat simulato."""
    return AUTONOMOUS_RUNTIME.trigger_from_payload(payload)


@app.post("/autonomy/webhook/{account}/{channel}/{session_id}")
async def api_autonomy_webhook(
    account: str,
    channel: str,
    session_id: str,
    payload: dict[str, Any] = Body(...),
):
    """Trigger esterno stile webhook instradato nel namespace corretto."""
    merged = {
        **payload,
        "account": account,
        "channel": channel,
        "session_id": session_id,
        "trigger_type": payload.get("trigger_type", "webhook"),
        "source": payload.get("source", "webhook-endpoint"),
    }
    return AUTONOMOUS_RUNTIME.trigger_from_payload(merged)


@app.put("/autonomy/config")
async def api_autonomy_config(payload: dict[str, Any] = Body(...)):
    """Aggiorna la configurazione persistente del runtime autonomo nel .env."""
    field_map = {
        "enabled": "AUTONOMOUS_RUNTIME_ENABLED",
        "heartbeat_sec": "AUTONOMOUS_RUNTIME_HEARTBEAT_SEC",
        "watch_poll_sec": "AUTONOMOUS_RUNTIME_WATCH_POLL_SEC",
        "compact_every_notes": "AUTONOMOUS_RUNTIME_COMPACT_EVERY_NOTES",
        "context_tail_notes": "AUTONOMOUS_RUNTIME_CONTEXT_TAIL_NOTES",
        "default_account": "AUTONOMOUS_RUNTIME_DEFAULT_ACCOUNT",
        "default_channel": "AUTONOMOUS_RUNTIME_DEFAULT_CHANNEL",
        "cron_utc": "AUTONOMOUS_RUNTIME_CRON_UTC",
        "watch_dirs": "AUTONOMOUS_RUNTIME_WATCH_DIRS",
        "watch_extensions": "AUTONOMOUS_RUNTIME_WATCH_EXTENSIONS",
        "background_isolation": "AUTONOMOUS_RUNTIME_BACKGROUND_ISOLATION",
        "max_files_per_tick": "AUTONOMOUS_RUNTIME_MAX_FILES_PER_TICK",
    }

    updates: dict[str, str] = {}
    for incoming_key, env_key in field_map.items():
        if incoming_key not in payload:
            continue
        value = payload.get(incoming_key)
        if isinstance(value, bool):
            updates[env_key] = "true" if value else "false"
        elif isinstance(value, list):
            updates[env_key] = ",".join(str(item).strip() for item in value if str(item).strip())
        else:
            updates[env_key] = str(value).strip()

    if not updates:
        raise HTTPException(status_code=400, detail="Nessun campo autonomia valido da aggiornare")

    _write_project_env_updates(updates)
    load_dotenv(PROJECT_ENV_PATH, override=True)
    config = AUTONOMOUS_RUNTIME.reload_config()
    return {
        "status": "ok",
        "updated_keys": list(updates.keys()),
        "config": config,
    }


# ═══════════════════════════════════════════════
# PLUGIN / MCP ENDPOINTS
# ═══════════════════════════════════════════════

from backend.plugins.registry import get_registry as _get_plugin_registry

@app.get("/plugins")
async def list_plugins():
    """Lista tutti i plugin installati con metadata e tools."""
    registry = _get_plugin_registry()
    return {
        "status": "ok",
        "count": len(registry.list_plugins()),
        "plugins": registry.list_plugins(),
    }


@app.get("/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    """Dettaglio di un singolo plugin."""
    registry = _get_plugin_registry()
    plugin = registry.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' non trovato")
    return plugin.info.to_dict()


@app.post("/plugins/{plugin_id}/execute")
async def execute_plugin_tool(plugin_id: str, body: dict = Body(...)):
    """
    Esegui un tool di un plugin.

    Body: { "tool": "tool_name", "params": { ... } }
    """
    tool_name = body.get("tool", "")
    params = body.get("params", {})
    if not tool_name:
        raise HTTPException(status_code=400, detail="Campo 'tool' obbligatorio")

    registry = _get_plugin_registry()
    start = time.perf_counter()
    result = registry.execute(plugin_id, tool_name, params)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 3)

    return {
        "plugin_id": plugin_id,
        "tool": tool_name,
        "params": params,
        "result": result,
        "elapsed_ms": elapsed_ms,
    }


@app.get("/plugins/tools/context")
async def get_tools_context():
    """Restituisce tutti i tool disponibili come stringa per il contesto AI."""
    registry = _get_plugin_registry()
    return {"context": registry.get_tools_for_prompt()}


# ═══════════════════════════════════════════════
# VOICE & VISION ENDPOINTS
# ═══════════════════════════════════════════════

@app.post("/voice/transcribe")
async def voice_transcribe(request: Request):
    """
    Riceve audio base64 e restituisce trascrizione.
    In locale usa Whisper via Ollama se disponibile, altrimenti stub
    per Web Speech API (il client fa STT nativo).
    """
    body = await request.json()
    text = body.get("text", "")
    # Se il client manda testo già trascritto (Web Speech API), lo conferma
    if text:
        return {"transcription": text, "source": "client-stt", "language": body.get("language", "auto")}
    return {"transcription": "", "source": "no-audio", "note": "Use Web Speech API on the client for STT"}


@app.post("/voice/tts")
async def voice_tts(request: Request):
    """
    Text-to-Speech endpoint.
    Restituisce metadati per TTS client-side (Web Speech Synthesis API).
    Il backend gestisce la preparazione del testo e la selezione voce.
    """
    body = await request.json()
    text = body.get("text", "")
    language = body.get("language", "it")

    if not text:
        raise HTTPException(status_code=400, detail="Campo 'text' obbligatorio")

    # Pulisci il testo per TTS: rimuovi markdown, code blocks, link
    import re
    clean = text
    clean = re.sub(r"```[\s\S]*?```", " codice omesso ", clean)
    clean = re.sub(r"`[^`]+`", "", clean)
    clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean)
    clean = re.sub(r"[#*_~>]", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    # Seleziona voce e rate in base alla lingua
    voice_config = {
        "it": {"lang": "it-IT", "rate": 1.0, "pitch": 1.0},
        "en": {"lang": "en-US", "rate": 1.0, "pitch": 1.0},
        "fr": {"lang": "fr-FR", "rate": 0.95, "pitch": 1.0},
        "de": {"lang": "de-DE", "rate": 0.95, "pitch": 1.0},
        "es": {"lang": "es-ES", "rate": 1.0, "pitch": 1.0},
    }
    config = voice_config.get(language, voice_config["en"])

    return {
        "text": clean[:5000],  # Cap per TTS
        "language": config["lang"],
        "rate": config["rate"],
        "pitch": config["pitch"],
        "source": "server-prepared",
        "char_count": len(clean),
    }


@app.post("/vision/analyze")
async def vision_analyze(request: Request):
    """
    Analizza un'immagine usando provider cloud con capacità vision.
    Accetta base64 image data o URL.
    """
    body = await request.json()
    image_data = body.get("image")  # base64 data URL o URL
    prompt = body.get("prompt", "Describe this image in detail.")

    if not image_data:
        raise HTTPException(status_code=400, detail="Campo 'image' obbligatorio (base64 data URL o URL)")

    # Costruisci immagine nel formato corretto
    if image_data.startswith("data:"):
        images = [{"data_url": image_data}]
    elif image_data.startswith("http"):
        images = [{"url": image_data}]
    else:
        images = [{"base64": image_data, "mime_type": "image/png"}]

    vision_msg = _build_vision_message(prompt, images)

    # Prova provider vision-capable in ordine
    env_map = _read_project_env_map()
    provider_keys = {
        "claude": env_map.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", "")),
        "gpt4": env_map.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
        "gemini": env_map.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")),
    }

    for provider in _VISION_PROVIDERS:
        api_key = provider_keys.get(provider, "")
        if not api_key:
            continue

        try:
            result = await orchestrate(
                messages=[vision_msg],
                mode="cloud",
                provider=provider,
                auto_routing=False,
                temperature=0.3,
                max_tokens=1024,
            )
            return {
                "analysis": result.get("content", ""),
                "provider": result.get("provider", provider),
                "model": result.get("model", ""),
                "tokens_used": result.get("tokens_used", 0),
                "latency_ms": result.get("latency_ms", 0),
            }
        except Exception:
            continue

    # Fallback: prova Ollama con modello vision (llava)
    try:
        result = await orchestrate(
            messages=[vision_msg],
            mode="local",
            provider="ollama",
            model="llava",
            auto_routing=False,
        )
        return {
            "analysis": result.get("content", ""),
            "provider": "ollama",
            "model": "llava",
        }
    except Exception:
        pass

    raise HTTPException(
        status_code=503,
        detail="Nessun provider vision disponibile. Configura una API key cloud (Claude, GPT-4, Gemini) o installa llava su Ollama."
    )


@app.get("/voice/capabilities")
async def voice_capabilities():
    """Restituisce le capacità voice disponibili nel sistema."""
    return {
        "stt": {
            "available": True,
            "engine": "Web Speech API (browser-native)",
            "languages": ["it-IT", "en-US", "fr-FR", "de-DE", "es-ES"],
            "note": "STT runs client-side, zero latency, zero install",
        },
        "tts": {
            "available": True,
            "engine": "Web Speech Synthesis API (browser-native)",
            "languages": ["it-IT", "en-US", "fr-FR", "de-DE", "es-ES"],
            "note": "TTS runs client-side with server-side text preparation",
        },
    }


@app.get("/vision/capabilities")
async def vision_capabilities():
    """Restituisce le capacità vision disponibili."""
    env_map = _read_project_env_map()
    available_providers = []
    for p in _VISION_PROVIDERS:
        key_map = {"claude": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY",
                    "gemini": "GEMINI_API_KEY", "groq": "GROQ_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY"}
        key_name = key_map.get(p, "")
        if env_map.get(key_name, os.environ.get(key_name, "")):
            available_providers.append(p)

    # Check Ollama llava
    ollama_vision = False
    try:
        status = await check_ollama_status()
        if status.get("running"):
            ollama_vision = any("llava" in m.get("name", "") for m in status.get("models", []))
    except Exception:
        pass

    return {
        "available": bool(available_providers) or ollama_vision,
        "cloud_providers": available_providers,
        "local_ollama_llava": ollama_vision,
        "supported_formats": ["image/png", "image/jpeg", "image/gif", "image/webp"],
        "max_size_mb": 10,
    }


# ═══════════════════════════════════════════════
# OPENCLAW AGENT RUNTIME
# ═══════════════════════════════════════════════

@app.post("/openclaw/run")
async def openclaw_run(request: Request):
    """
    Execute an agentic task via OpenClaw.
    The agent loops: AI → tool call → result → AI → ... → final answer.
    """
    from backend.openclaw.agent import run_agent
    body = await request.json()
    task = body.get("task", "").strip()
    if not task:
        return JSONResponse({"error": "task is required"}, status_code=400)

    model = body.get("model", "qwen2.5-coder:3b")
    provider = body.get("provider", "ollama")
    max_iterations = min(body.get("max_iterations", 8), 12)

    registry = _get_plugin_registry()
    result = await run_agent(
        task=task,
        model=model,
        provider=provider,
        registry=registry,
        max_iterations=max_iterations,
    )
    return {
        "task": result.task,
        "answer": result.answer,
        "status": result.status,
        "total_steps": result.total_steps,
        "total_latency_ms": result.total_latency_ms,
        "tools_used": result.tools_used,
        "steps": [
            {
                "step": s.step,
                "action": s.action,
                "content": s.content,
                "latency_ms": s.latency_ms,
            }
            for s in result.steps
        ],
    }


@app.get("/openclaw/capabilities")
async def openclaw_capabilities():
    """Return OpenClaw agent capabilities and loaded tools."""
    from backend.openclaw.agent import get_agent_capabilities
    registry = _get_plugin_registry()
    return get_agent_capabilities(registry)


@app.get("/openclaw/health")
async def openclaw_health():
    """Health check for OpenClaw agent runtime (built-in, always healthy)."""
    from backend.openclaw.agent import get_agent_capabilities
    registry = _get_plugin_registry()
    caps = get_agent_capabilities(registry)
    return {
        "status": "healthy",
        "agent": "OpenClaw",
        "plugins": caps["plugins_loaded"],
        "tools": caps["total_tools"],
    }


# ═══════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("LITELLM_PROXY_PORT", 4000))
    print(f"🎵 Avvio VIO 83 AI ORCHESTRA v2 su porta {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
