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
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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

# RAG è disabilitato per compatibilità Python 3.14
RAG_AVAILABLE = False
# try:
#     from backend.rag.engine import get_rag_engine, RAGSource
#     RAG_AVAILABLE = True
# except Exception as e:
#     print(f"⚠️  RAG Engine legacy non disponibile: {e}")

# Knowledge Base v2 — sempre disponibile (fallback a SQLite FTS5)
KB_AVAILABLE = False
# try:
#     from backend.rag.knowledge_base import get_knowledge_base, KnowledgeBase
#     KB_AVAILABLE = True
# except Exception as e:
#     print(f"⚠️  Knowledge Base non disponibile: {e}")

load_dotenv()
START_TIME = time.time()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ENV_PATH = PROJECT_ROOT / ".env"
RUNTIME_SUPERVISOR_STATE_PATH = PROJECT_ROOT / ".pids" / "runtime-supervisor-state.json"
RUNTIME_SUPERVISOR_PID_PATH = PROJECT_ROOT / ".pids" / "runtime-supervisor.pid"
RUNTIME_LAUNCH_AGENT_PATH = Path.home() / "Library" / "LaunchAgents" / "com.vio83.runtime-services.plist"
ORCHESTRA_LAUNCH_AGENT_PATH = Path.home() / "Library" / "LaunchAgents" / "com.vio83.ai-orchestra.plist"

RUNTIME_ENV_DEFAULTS = {
    "OPENCLAW_START_CMD": "",
    "LEGALROOM_START_CMD": "",
    "N8N_START_CMD": "",
    "OPENCLAW_HEALTH_URLS": "http://127.0.0.1:4111/health,http://127.0.0.1:4111/",
    "LEGALROOM_HEALTH_URLS": "http://127.0.0.1:4222/health,http://127.0.0.1:4222/",
    "N8N_HEALTH_URLS": "http://127.0.0.1:5678/healthz,http://127.0.0.1:5678/rest/healthz,http://127.0.0.1:5678/",
    "RUNTIME_APPS_UPDATE_POLICY": "user-approved",
    "RUNTIME_APPS_OFFLINE_MODE": "keep-last-approved",
    "RUNTIME_APPS_LAST_USER_APPROVED_AT": "",
}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _iso_from_epoch(epoch_s: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch_s))


def _read_project_env_map() -> dict[str, str]:
    env_map: dict[str, str] = {}

    if not PROJECT_ENV_PATH.exists():
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


def _claude_desktop_snapshot() -> dict[str, Any]:
    base_path = Path.home() / "Library" / "Application Support" / "Claude"
    ext_path = base_path / "extensions-installations.json"
    cfg_path = base_path / "claude_desktop_config.json"
    ext_data = _read_json_file(ext_path) or {}
    cfg_data = _read_json_file(cfg_path) or {}
    ext_map = ext_data.get("extensions", {}) if isinstance(ext_data, dict) else {}
    preferences = cfg_data.get("preferences", {}) if isinstance(cfg_data, dict) else {}

    return {
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
        print("📚 Knowledge Base: non disponibile")

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

    free_cloud = get_free_cloud_providers()
    if free_cloud:
        print(f"🆓 Provider cloud gratuiti: {list(free_cloud.keys())}")
    available = get_available_cloud_providers()
    paid_only = {k: v for k, v in available.items() if k not in free_cloud}
    if paid_only:
        print(f"☁️  Provider cloud a pagamento: {list(paid_only.keys())}")
    if not available:
        print("☁️  Provider cloud: nessuno (configura .env)")

    app.state.knowledge_auto_refresh_task = asyncio.create_task(_knowledge_auto_refresh_loop())
    print("🌍 Knowledge Watch: auto-refresh ogni 6h attivo")

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

    pool = get_connection_pool()
    await pool.close_all()
    cache = get_cache()
    cache.cleanup()
    print("🎵 VIO 83 AI ORCHESTRA — Server arrestato")


app = FastAPI(
    title="VIO 83 AI ORCHESTRA",
    description="Multi-provider AI orchestration platform — Local-first, privacy-first",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:1420",
        "tauri://localhost",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Stato di salute completo del sistema."""
    available = get_available_cloud_providers()
    ollama = await check_ollama_status()

    providers = {}
    for key in ALL_CLOUD_PROVIDERS:
        providers[key] = {
            "available": key in available,
            "mode": "cloud",
            "name": ALL_CLOUD_PROVIDERS[key]["name"],
            "cost": ALL_CLOUD_PROVIDERS[key].get("cost", "paid"),
        }
    providers["ollama"] = {
        "available": ollama["available"],
        "mode": "local",
        "name": "Ollama (Locale)",
        "models": ollama.get("models", []),
    }

    rag_stats = {"total_documents": 0, "status": "disabled"}
    if RAG_AVAILABLE:
        try:
            rag = get_rag_engine()
            rag_stats = rag.get_stats()
        except Exception:
            pass

    return HealthResponse(
        status="ok",
        version="0.2.0",
        providers=providers,
        rag_stats=rag_stats,
        uptime_seconds=round(time.time() - START_TIME, 1),
    )


# ═══════════════════════════════════════════════
# CHAT — Non-streaming
# ═══════════════════════════════════════════════

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat principale — instrada la richiesta al provider migliore."""
    try:
        messages = [{"role": "user", "content": request.message}]

        # Se c'è una conversazione, recupera il contesto
        if request.conversation_id:
            conv = get_conversation(request.conversation_id)
            if conv and conv.get("messages"):
                messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in conv["messages"]
                ]
                messages.append({"role": "user", "content": request.message})

        # System prompt
        if request.system_prompt:
            messages.insert(0, {"role": "system", "content": request.system_prompt})

        # Orchestratore
        result = await orchestrate(
            messages=messages,
            mode=request.mode,
            provider=request.provider or ("claude" if request.mode == "cloud" else "ollama"),
            model=request.model,
            ollama_model=request.model or "qwen2.5-coder:3b",
            auto_routing=True,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Salva nel database
        conv_id = request.conversation_id
        if not conv_id:
            title = auto_title_from_message(request.message)
            conv_data = create_conversation(title=title, mode=request.mode)
            conv_id = conv_data["id"]

        add_message(conv_id, "user", request.message)
        add_message(conv_id, "assistant", result["content"],
                    provider=result["provider"], model=result["model"],
                    tokens_used=result.get("tokens_used", 0),
                    latency_ms=result.get("latency_ms", 0))

        # Log metrica
        log_metric(
            provider=result["provider"], model=result["model"],
            request_type=result.get("request_type"),
            tokens_used=result.get("tokens_used", 0),
            latency_ms=result.get("latency_ms", 0),
        )

        return ChatResponse(
            content=result["content"],
            provider=result["provider"],
            model=result["model"],
            tokens_used=result.get("tokens_used", 0),
            latency_ms=result.get("latency_ms", 0),
            request_type=result.get("request_type"),
        )

    except Exception as e:
        log_metric(
            provider=request.provider or "ollama",
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
    messages = [{"role": "user", "content": request.message}]

    if request.conversation_id:
        conv = get_conversation(request.conversation_id)
        if conv and conv.get("messages"):
            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in conv["messages"]
            ]
            messages.append({"role": "user", "content": request.message})

    if request.system_prompt:
        messages.insert(0, {"role": "system", "content": request.system_prompt})

    # Inietta system prompt SPECIALIZZATO per tipo di richiesta
    from backend.orchestrator.direct_router import classify_request as _classify
    from backend.orchestrator.system_prompt import build_system_prompt
    has_system = any(m.get("role") == "system" for m in messages)
    if not has_system:
        req_type = _classify(request.message)
        system_prompt = build_system_prompt(req_type)

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

    async def event_generator():
        full_content = ""
        start = time.time()
        try:
            async for token in call_ollama_streaming(
                messages=messages,
                model=model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                full_content += token
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

            latency = int((time.time() - start) * 1000)
            yield f"data: {json.dumps({'token': '', 'done': True, 'full_content': full_content, 'latency_ms': latency, 'model': model, 'provider': 'ollama'})}\n\n"

            # Salva nel database
            conv_id = request.conversation_id
            if not conv_id:
                title = auto_title_from_message(request.message)
                conv_data = create_conversation(title=title, mode=request.mode)
                conv_id = conv_data["id"]

            add_message(conv_id, "user", request.message)
            add_message(conv_id, "assistant", full_content,
                        provider="ollama", model=model,
                        latency_ms=latency)
            log_metric("ollama", model, tokens_used=0, latency_ms=latency)

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
# CLASSIFY
# ═══════════════════════════════════════════════

@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """Classifica il tipo di richiesta per il routing intelligente."""
    req_type = classify_request(request.message)
    from backend.config.providers import REQUEST_TYPE_ROUTING
    routing = REQUEST_TYPE_ROUTING.get(req_type, {})

    return ClassifyResponse(
        request_type=req_type,
        suggested_provider=routing.get("cloud_primary", "ollama"),
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
# PROVIDERS
# ═══════════════════════════════════════════════

@app.get("/providers")
async def list_providers():
    """Lista tutti i provider disponibili — 3 tier: locale, gratis, pagamento."""
    available = get_available_cloud_providers()
    free_available = get_free_cloud_providers()
    ollama = await check_ollama_status()

    return {
        "local": {
            "ollama": {
                "name": "Ollama (Locale)",
                "available": ollama["available"],
                "cost": "free",
                "default_model": LOCAL_PROVIDERS["ollama"]["default_model"],
                "models": ollama.get("models", []),
                "installed_models": [m["name"] for m in ollama.get("models", [])],
            }
        },
        "free_cloud": {
            key: {
                "name": FREE_CLOUD_PROVIDERS[key]["name"],
                "available": key in free_available,
                "cost": "free",
                "free_tier": FREE_CLOUD_PROVIDERS[key].get("free_tier", ""),
                "signup_url": FREE_CLOUD_PROVIDERS[key].get("signup_url", ""),
                "default_model": FREE_CLOUD_PROVIDERS[key]["default_model"],
                "models": list(FREE_CLOUD_PROVIDERS[key]["models"].keys()),
            }
            for key in FREE_CLOUD_PROVIDERS
        },
        "paid_cloud": {
            key: {
                "name": CLOUD_PROVIDERS[key]["name"],
                "available": key in available,
                "cost": CLOUD_PROVIDERS[key].get("cost", "paid"),
                "default_model": CLOUD_PROVIDERS[key]["default_model"],
                "models": list(CLOUD_PROVIDERS[key]["models"].keys()),
            }
            for key in CLOUD_PROVIDERS
        },
        "all_ordered": [
            {"id": p["id"], "name": p["name"], "tier": p["tier"],
             "available": p.get("available", True)}
            for p in get_all_providers_ordered()
        ],
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
        return {"status": "disabled", "reason": "Knowledge Base non inizializzata"}
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
# RUN
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("LITELLM_PROXY_PORT", 4000))
    print(f"🎵 Avvio VIO 83 AI ORCHESTRA v2 su porta {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
