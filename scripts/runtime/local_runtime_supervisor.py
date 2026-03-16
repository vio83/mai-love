#!/usr/bin/env python3
"""
VIO 83 AI ORCHESTRA — Local Runtime Services Supervisor

Supervisiona OpenClaw / LegalRoom / n8n in locale con:
- avvio automatico
- restart automatico se processo cade o health fallisce
- stato continuo su file JSON per audit operativo

Configurazione via .env (root progetto):
  OPENCLAW_START_CMD="..."
  LEGALROOM_START_CMD="..."
  N8N_START_CMD="..."                       (default: npx n8n ...)
  OPENCLAW_HEALTH_URLS="url1,url2"
  LEGALROOM_HEALTH_URLS="url1,url2"
  N8N_HEALTH_URLS="url1,url2,url3"
  OPENCLAW_WORKDIR="..."
  LEGALROOM_WORKDIR="..."
  N8N_WORKDIR="..."
  RUNTIME_SUPERVISOR_TICK_SEC="8"
  RUNTIME_SUPERVISOR_UNHEALTHY_RESTART_SEC="45"
"""

from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib import error, request

PROJECT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_DIR / ".logs"
PID_DIR = PROJECT_DIR / ".pids"
ENV_PATH = PROJECT_DIR / ".env"
STATE_PATH = PID_DIR / "runtime-supervisor-state.json"
SUPERVISOR_PID_PATH = PID_DIR / "runtime-supervisor.pid"

LOG_DIR.mkdir(parents=True, exist_ok=True)
PID_DIR.mkdir(parents=True, exist_ok=True)

STOP_REQUESTED = False


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
    except Exception as exc:  # pragma: no cover
        print(f"[{now_iso()}] [supervisor] WARN: impossibile leggere .env ({exc})", flush=True)


@dataclass
class ServiceConfig:
    service_id: str
    display_name: str
    cmd_env_key: str
    default_cmd: str
    health_urls: list[str]
    workdir: Path
    log_path: Path


class ManagedService:
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.process: Optional[subprocess.Popen[str]] = None
        self.last_start_at: Optional[float] = None
        self.last_start_attempt_at: Optional[float] = None
        self.last_health_ok: Optional[bool] = None
        self.last_health_check_at: Optional[float] = None
        self.unhealthy_since: Optional[float] = None
        self.disabled_reason: Optional[str] = None

    @property
    def command(self) -> str:
        cmd = os.environ.get(self.config.cmd_env_key, "").strip()
        if cmd:
            return cmd
        return self.config.default_cmd.strip()

    @property
    def enabled(self) -> bool:
        if not self.command:
            self.disabled_reason = f"missing {self.config.cmd_env_key}"
            return False
        self.disabled_reason = None
        return True

    def is_process_alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def check_health(self, timeout_seconds: float = 2.5) -> bool:
        self.last_health_check_at = time.time()
        for url in self.config.health_urls:
            try:
                req = request.Request(url, method="GET", headers={"User-Agent": "VIO83-Runtime-Supervisor/1.0"})
                with request.urlopen(req, timeout=timeout_seconds) as response:
                    status = int(getattr(response, "status", 200))
                    if status < 500:
                        self.last_health_ok = True
                        return True
            except error.HTTPError as http_exc:
                if int(http_exc.code) < 500:
                    self.last_health_ok = True
                    return True
            except Exception:
                continue
        self.last_health_ok = False
        return False

    def start(self) -> bool:
        if not self.enabled:
            print(
                f"[{now_iso()}] [supervisor] SKIP {self.config.display_name}: {self.disabled_reason}",
                flush=True,
            )
            return False

        if self.is_process_alive():
            return True

        self.config.log_path.parent.mkdir(parents=True, exist_ok=True)
        log_fp = self.config.log_path.open("a", encoding="utf-8")
        cmd = self.command
        self.last_start_attempt_at = time.time()

        print(f"[{now_iso()}] [supervisor] START {self.config.display_name}: {cmd}", flush=True)

        # shell=True permette comandi complessi da .env (es. source/&&/npx)
        self.process = subprocess.Popen(
            cmd,
            shell=True,
            executable="/bin/bash",
            cwd=str(self.config.workdir),
            stdout=log_fp,
            stderr=log_fp,
            env={
                **os.environ,
                "PYTHONUNBUFFERED": "1",
                "PROJECT_DIR": str(PROJECT_DIR),
            },
        )
        self.last_start_at = time.time()
        self.unhealthy_since = None
        return True

    def can_start(self, now_s: float, backoff_s: int) -> bool:
        if self.last_start_attempt_at is None:
            return True
        return (now_s - self.last_start_attempt_at) >= backoff_s

    def stop(self, grace_seconds: float = 8.0) -> None:
        if not self.process:
            return

        if self.process.poll() is not None:
            self.process = None
            return

        try:
            self.process.terminate()
            deadline = time.time() + grace_seconds
            while time.time() < deadline:
                if self.process.poll() is not None:
                    break
                time.sleep(0.2)

            if self.process.poll() is None:
                self.process.kill()
        except Exception:
            pass
        finally:
            self.process = None

    def restart(self) -> bool:
        self.stop(grace_seconds=5.0)
        return self.start()

    def as_state_dict(self) -> dict:
        pid = self.process.pid if self.process and self.process.poll() is None else None
        return {
            "id": self.config.service_id,
            "name": self.config.display_name,
            "pid": pid,
            "enabled": self.enabled,
            "disabled_reason": self.disabled_reason,
            "health_urls": self.config.health_urls,
            "command_env_key": self.config.cmd_env_key,
            "last_start_at": now_iso() if self.last_start_at else None,
            "last_start_attempt_at": self.last_start_attempt_at,
            "last_health_ok": self.last_health_ok,
            "last_health_check_at": self.last_health_check_at,
            "unhealthy_since": self.unhealthy_since,
            "workdir": str(self.config.workdir),
            "log": str(self.config.log_path),
        }


def build_services() -> list[ManagedService]:
    n8n_default = f"bash {PROJECT_DIR / 'scripts/runtime/run_n8n_runtime.sh'}"

    def parse_urls(env_key: str, fallback: str) -> list[str]:
        raw = os.environ.get(env_key, fallback)
        return [url.strip() for url in raw.split(",") if url.strip()]

    def service_workdir(env_key: str) -> Path:
        val = os.environ.get(env_key, "").strip()
        return Path(val).expanduser() if val else PROJECT_DIR

    configs = [
        ServiceConfig(
            service_id="openclaw",
            display_name="OpenClaw",
            cmd_env_key="OPENCLAW_START_CMD",
            default_cmd="",
            health_urls=parse_urls("OPENCLAW_HEALTH_URLS", "http://127.0.0.1:4111/health,http://127.0.0.1:4111/"),
            workdir=service_workdir("OPENCLAW_WORKDIR"),
            log_path=LOG_DIR / "runtime-openclaw.log",
        ),
        ServiceConfig(
            service_id="legalroom",
            display_name="LegalRoom",
            cmd_env_key="LEGALROOM_START_CMD",
            default_cmd="",
            health_urls=parse_urls("LEGALROOM_HEALTH_URLS", "http://127.0.0.1:4222/health,http://127.0.0.1:4222/"),
            workdir=service_workdir("LEGALROOM_WORKDIR"),
            log_path=LOG_DIR / "runtime-legalroom.log",
        ),
        ServiceConfig(
            service_id="n8n",
            display_name="n8n",
            cmd_env_key="N8N_START_CMD",
            default_cmd=n8n_default,
            health_urls=parse_urls("N8N_HEALTH_URLS", "http://127.0.0.1:5678/healthz,http://127.0.0.1:5678/rest/healthz,http://127.0.0.1:5678/"),
            workdir=service_workdir("N8N_WORKDIR"),
            log_path=LOG_DIR / "runtime-n8n.log",
        ),
    ]

    return [ManagedService(cfg) for cfg in configs]


def write_state(services: list[ManagedService], tick_s: int, restart_after_s: int) -> None:
    payload = {
        "status": "ok",
        "generated_at": now_iso(),
        "tick_seconds": tick_s,
        "unhealthy_restart_seconds": restart_after_s,
        "services": [svc.as_state_dict() for svc in services],
    }
    STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def signal_handler(signum: int, _frame) -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True
    print(f"[{now_iso()}] [supervisor] signal {signum} ricevuto: shutdown richiesto", flush=True)


def main() -> int:
    load_env_file(ENV_PATH)

    tick_s = max(4, int(float(os.environ.get("RUNTIME_SUPERVISOR_TICK_SEC", "8"))))
    restart_after_s = max(12, int(float(os.environ.get("RUNTIME_SUPERVISOR_UNHEALTHY_RESTART_SEC", "45"))))
    restart_backoff_s = max(6, int(float(os.environ.get("RUNTIME_SUPERVISOR_RESTART_BACKOFF_SEC", "15"))))

    services = build_services()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    if SUPERVISOR_PID_PATH.exists():
        try:
            existing_pid = int(SUPERVISOR_PID_PATH.read_text(encoding="utf-8").strip())
            if existing_pid > 0 and existing_pid != os.getpid():
                try:
                    os.kill(existing_pid, 0)
                    print(
                        f"[{now_iso()}] [supervisor] rilevata istanza precedente pid={existing_pid}, handover in corso",
                        flush=True,
                    )
                    os.kill(existing_pid, signal.SIGTERM)
                    deadline = time.time() + 5.0
                    while time.time() < deadline:
                        try:
                            os.kill(existing_pid, 0)
                            time.sleep(0.2)
                        except ProcessLookupError:
                            break
                except ProcessLookupError:
                    pass
        except Exception:
            pass

    SUPERVISOR_PID_PATH.write_text(str(os.getpid()), encoding="utf-8")
    print(f"[{now_iso()}] [supervisor] avviato (pid={os.getpid()}) in {PROJECT_DIR}", flush=True)

    warned_disabled: set[str] = set()

    try:
        while not STOP_REQUESTED:
            now = time.time()

            for svc in services:
                if not svc.enabled:
                    if svc.config.service_id not in warned_disabled:
                        print(
                            f"[{now_iso()}] [supervisor] {svc.config.display_name} non configurato — "
                            f"imposta {svc.config.cmd_env_key} in .env",
                            flush=True,
                        )
                        warned_disabled.add(svc.config.service_id)
                    continue

                healthy = svc.check_health()
                alive = svc.is_process_alive()

                if healthy:
                    svc.unhealthy_since = None
                    if not alive:
                        if svc.can_start(now, restart_backoff_s):
                            svc.start()
                    continue

                if svc.unhealthy_since is None:
                    svc.unhealthy_since = now

                if not alive:
                    if svc.can_start(now, restart_backoff_s):
                        svc.start()
                    continue

                unhealthy_duration = now - svc.unhealthy_since
                if unhealthy_duration >= restart_after_s:
                    print(
                        f"[{now_iso()}] [supervisor] restart {svc.config.display_name} "
                        f"(health KO da {int(unhealthy_duration)}s)",
                        flush=True,
                    )
                    if svc.can_start(now, restart_backoff_s):
                        svc.restart()

            write_state(services, tick_s=tick_s, restart_after_s=restart_after_s)
            time.sleep(tick_s)

    except Exception as exc:
        print(f"[{now_iso()}] [supervisor] errore fatale: {exc}", flush=True)
        return 1
    finally:
        print(f"[{now_iso()}] [supervisor] arresto in corso…", flush=True)
        for svc in services:
            svc.stop()

        if SUPERVISOR_PID_PATH.exists():
            SUPERVISOR_PID_PATH.unlink(missing_ok=True)

    print(f"[{now_iso()}] [supervisor] arrestato", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
