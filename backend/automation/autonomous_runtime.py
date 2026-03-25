from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower())
    return cleaned.strip("-._") or "default"


@dataclass
class RuntimeTrigger:
    trigger_type: str
    source: str
    account: str
    channel: str
    session_id: str
    title: str
    content: str
    payload: dict[str, Any]
    background: bool = False

    def namespace_key(self) -> str:
        prefix = "bg" if self.background else "fg"
        return "__".join([
            prefix,
            slugify(self.account),
            slugify(self.channel),
            slugify(self.session_id),
        ])


class AutonomousRuntime:
    """
    Cicli di pianificazione + memoria esternalizzata persistente su Markdown.

    Principi:
    - il contesto LLM è una cache;
    - il disco è la source of truth;
    - compaction periodica per non esplodere il contesto;
    - trigger → route → esecuzione in namespace di sessione.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data" / "autonomous_runtime"
        self.sessions_dir = self.data_dir / "sessions"
        self.runtime_state_path = self.data_dir / "runtime_state.json"
        self.index_path = self.data_dir / "sessions-index.json"
        self.config_path = self.data_dir / "config.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        self._tasks: list[asyncio.Task[Any]] = []
        self._stop_event = asyncio.Event()
        self._last_cron_slot: Optional[str] = None
        self._watch_snapshot: dict[str, float] = {}
        self.config = self._load_config()
        self._write_runtime_state("initialized")

    # ──────────────────────────────────────────────────────
    # Config
    # ──────────────────────────────────────────────────────
    def _env_bool(self, key: str, default: bool) -> bool:
        val = os.environ.get(key)
        if val is None:
            return default
        return val.strip().lower() in {"1", "true", "yes", "on"}

    def _env_int(self, key: str, default: int, minimum: int = 1) -> int:
        raw = os.environ.get(key, "").strip()
        try:
            return max(minimum, int(float(raw))) if raw else default
        except Exception:
            return default

    def _env_csv(self, key: str, default: str) -> list[str]:
        raw = os.environ.get(key, default)
        return [item.strip() for item in raw.split(",") if item.strip()]

    def _load_config(self) -> dict[str, Any]:
        config = {
            "enabled": self._env_bool("AUTONOMOUS_RUNTIME_ENABLED", True),
            "heartbeat_sec": self._env_int("AUTONOMOUS_RUNTIME_HEARTBEAT_SEC", 300, minimum=30),
            "watch_poll_sec": self._env_int("AUTONOMOUS_RUNTIME_WATCH_POLL_SEC", 90, minimum=15),
            "compact_every_notes": self._env_int("AUTONOMOUS_RUNTIME_COMPACT_EVERY_NOTES", 12, minimum=3),
            "context_tail_notes": self._env_int("AUTONOMOUS_RUNTIME_CONTEXT_TAIL_NOTES", 12, minimum=3),
            "default_account": os.environ.get("AUTONOMOUS_RUNTIME_DEFAULT_ACCOUNT", "vio83-local").strip() or "vio83-local",
            "default_channel": os.environ.get("AUTONOMOUS_RUNTIME_DEFAULT_CHANNEL", "main").strip() or "main",
            "cron_utc": self._env_csv("AUTONOMOUS_RUNTIME_CRON_UTC", "00:15,06:15,12:15,18:15"),
            "watch_dirs": self._env_csv("AUTONOMOUS_RUNTIME_WATCH_DIRS", "backend,src,docs,data/config"),
            "watch_extensions": self._env_csv("AUTONOMOUS_RUNTIME_WATCH_EXTENSIONS", ".py,.ts,.tsx,.js,.jsx,.md,.json,.yml,.yaml,.toml,.sh"),
            "background_isolation": self._env_bool("AUTONOMOUS_RUNTIME_BACKGROUND_ISOLATION", True),
            "max_files_per_tick": self._env_int("AUTONOMOUS_RUNTIME_MAX_FILES_PER_TICK", 20, minimum=1),
        }
        self.config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return config

    def reload_config(self) -> dict[str, Any]:
        self.config = self._load_config()
        self._write_runtime_state("config-reloaded")
        return self.config

    # ──────────────────────────────────────────────────────
    # State & index
    # ──────────────────────────────────────────────────────
    def _read_index(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return {"generated_at": utc_iso(), "sessions": {}}
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except Exception:
            return {"generated_at": utc_iso(), "sessions": {}}

    def _write_index(self, index: dict[str, Any]) -> None:
        index["generated_at"] = utc_iso()
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    def _write_runtime_state(self, status: str) -> None:
        payload = {
            "status": status,
            "updated_at": utc_iso(),
            "enabled": self.config.get("enabled", True),
            "tasks": [task.get_name() for task in self._tasks if not task.done()],
            "config": self.config,
        }
        self.runtime_state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _session_dir(self, namespace: str) -> Path:
        return self.sessions_dir / slugify(namespace)

    def _session_paths(self, namespace: str) -> dict[str, Path]:
        base = self._session_dir(namespace)
        base.mkdir(parents=True, exist_ok=True)
        return {
            "base": base,
            "notes": base / "notes.md",
            "summary": base / "summary.md",
            "events": base / "events.jsonl",
            "state": base / "state.json",
        }

    def _read_session_state(self, namespace: str) -> dict[str, Any]:
        state_path = self._session_paths(namespace)["state"]
        if not state_path.exists():
            return {
                "namespace": namespace,
                "created_at": utc_iso(),
                "updated_at": utc_iso(),
                "note_count": 0,
                "event_count": 0,
                "last_compact_at": None,
                "last_trigger_type": None,
                "account": None,
                "channel": None,
                "session_id": None,
                "background": False,
            }
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            return {
                "namespace": namespace,
                "created_at": utc_iso(),
                "updated_at": utc_iso(),
                "note_count": 0,
                "event_count": 0,
            }

    def _write_session_state(self, namespace: str, state: dict[str, Any]) -> None:
        state["updated_at"] = utc_iso()
        self._session_paths(namespace)["state"].write_text(
            json.dumps(state, indent=2),
            encoding="utf-8",
        )

    def _ensure_session(self, namespace: str, *, account: str, channel: str, session_id: str, background: bool) -> dict[str, Any]:
        state = self._read_session_state(namespace)
        state.update({
            "namespace": namespace,
            "account": account,
            "channel": channel,
            "session_id": session_id,
            "background": background,
        })
        self._write_session_state(namespace, state)

        index = self._read_index()
        sessions = index.setdefault("sessions", {})
        sessions[namespace] = {
            "namespace": namespace,
            "account": account,
            "channel": channel,
            "session_id": session_id,
            "background": background,
            "updated_at": state["updated_at"],
            "note_count": state.get("note_count", 0),
            "event_count": state.get("event_count", 0),
            "last_compact_at": state.get("last_compact_at"),
        }
        self._write_index(index)
        return state

    # ──────────────────────────────────────────────────────
    # Durable memory
    # ──────────────────────────────────────────────────────
    def append_note(
        self,
        namespace: str,
        *,
        title: str,
        content: str,
        kind: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        metadata = metadata or {}
        paths = self._session_paths(namespace)
        state = self._read_session_state(namespace)
        note_number = int(state.get("note_count", 0)) + 1
        ts = utc_iso()

        block = [
            f"## [{note_number:05d}] {title}",
            "",
            f"- timestamp: {ts}",
            f"- kind: {kind}",
            f"- metadata: `{json.dumps(metadata, ensure_ascii=False, sort_keys=True)}`",
            "",
            content.strip(),
            "",
        ]

        with paths["notes"].open("a", encoding="utf-8") as fp:
            fp.write("\n".join(block) + "\n")

        state["note_count"] = note_number
        self._write_session_state(namespace, state)

        index = self._read_index()
        if namespace in index.get("sessions", {}):
            index["sessions"][namespace]["note_count"] = note_number
            index["sessions"][namespace]["updated_at"] = ts
            self._write_index(index)

        if note_number % int(self.config["compact_every_notes"]) == 0:
            self.compact_namespace(namespace)

        return {"namespace": namespace, "note_number": note_number, "timestamp": ts}

    def log_event(self, namespace: str, event: dict[str, Any]) -> None:
        paths = self._session_paths(namespace)
        state = self._read_session_state(namespace)
        state["event_count"] = int(state.get("event_count", 0)) + 1
        state["last_trigger_type"] = event.get("trigger_type")
        self._write_session_state(namespace, state)

        with paths["events"].open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(event, ensure_ascii=False) + "\n")

        index = self._read_index()
        if namespace in index.get("sessions", {}):
            index["sessions"][namespace]["event_count"] = state["event_count"]
            index["sessions"][namespace]["updated_at"] = utc_iso()
            self._write_index(index)

    def compact_namespace(self, namespace: str) -> dict[str, Any]:
        paths = self._session_paths(namespace)
        notes_path = paths["notes"]
        state = self._read_session_state(namespace)

        if not notes_path.exists():
            summary = "# Summary\n\nNessuna nota disponibile.\n"
            paths["summary"].write_text(summary, encoding="utf-8")
            return {"namespace": namespace, "summary_lines": 1}

        raw = notes_path.read_text(encoding="utf-8")
        sections = [section.strip() for section in raw.split("## ") if section.strip()]
        tail_size = int(self.config["context_tail_notes"])
        recent_sections = sections[-tail_size:]

        bullets: list[str] = []
        for section in recent_sections:
            lines = [line.strip() for line in section.splitlines() if line.strip()]
            if not lines:
                continue
            header = lines[0]
            body_candidates = [
                line for line in lines[1:]
                if not line.startswith("- timestamp:")
                and not line.startswith("- kind:")
                and not line.startswith("- metadata:")
            ]
            excerpt = " ".join(body_candidates[:2]).strip()
            if len(excerpt) > 220:
                excerpt = excerpt[:217] + "..."
            bullets.append(f"- **{header}** — {excerpt or 'nota registrata'}")

        summary_lines = [
            f"# Session Summary — {namespace}",
            "",
            f"- generated_at: {utc_iso()}",
            f"- note_count: {state.get('note_count', 0)}",
            f"- event_count: {state.get('event_count', 0)}",
            f"- last_trigger_type: {state.get('last_trigger_type')}",
            "",
            "## Curated Summary",
            "",
        ]
        summary_lines.extend(bullets or ["- Nessun evento ancora riassumibile."])
        summary_lines.extend([
            "",
            "## Retrieval Policy",
            "",
            "- Il file `notes.md` è la fonte della verità.",
            "- Questo `summary.md` è una compattazione curata per mantenere il contesto corto.",
            "- Il retrieval rilegge sempre anche il tail delle note recenti.",
            "",
        ])

        paths["summary"].write_text("\n".join(summary_lines), encoding="utf-8")
        state["last_compact_at"] = utc_iso()
        self._write_session_state(namespace, state)

        index = self._read_index()
        if namespace in index.get("sessions", {}):
            index["sessions"][namespace]["last_compact_at"] = state["last_compact_at"]
            index["sessions"][namespace]["updated_at"] = utc_iso()
            self._write_index(index)

        return {
            "namespace": namespace,
            "summary_path": str(paths["summary"]),
            "summary_lines": len(summary_lines),
        }

    def retrieve_context(self, namespace: str, query: str = "") -> dict[str, Any]:
        paths = self._session_paths(namespace)
        summary = paths["summary"].read_text(encoding="utf-8") if paths["summary"].exists() else ""
        notes = paths["notes"].read_text(encoding="utf-8") if paths["notes"].exists() else ""
        sections = [f"## {section.strip()}" for section in notes.split("## ") if section.strip()]
        recent_sections = sections[-int(self.config["context_tail_notes"]):]

        query_terms = [term.lower() for term in re.findall(r"[a-zA-Z0-9àèéìòù_-]+", query or "") if len(term) > 1]
        scored: list[tuple[int, str]] = []
        for section in recent_sections:
            lowered = section.lower()
            score = sum(lowered.count(term) for term in query_terms) if query_terms else 1
            if score > 0:
                scored.append((score, section))

        scored.sort(key=lambda item: item[0], reverse=True)
        snippets = [item[1] for item in scored[:5]] if scored else recent_sections[-5:]

        return {
            "namespace": namespace,
            "summary": summary,
            "snippets": snippets,
            "notes_path": str(paths["notes"]),
            "summary_path": str(paths["summary"]),
            "query": query,
        }

    # ──────────────────────────────────────────────────────
    # Trigger routing
    # ──────────────────────────────────────────────────────
    def route_trigger(self, trigger: RuntimeTrigger) -> str:
        namespace = trigger.namespace_key()
        self._ensure_session(
            namespace,
            account=trigger.account,
            channel=trigger.channel,
            session_id=trigger.session_id,
            background=trigger.background,
        )
        event = {
            "timestamp": utc_iso(),
            "trigger_type": trigger.trigger_type,
            "source": trigger.source,
            "account": trigger.account,
            "channel": trigger.channel,
            "session_id": trigger.session_id,
            "background": trigger.background,
            "title": trigger.title,
            "payload": trigger.payload,
        }
        self.log_event(namespace, event)
        self.append_note(
            namespace,
            title=trigger.title,
            content=trigger.content,
            kind=trigger.trigger_type,
            metadata={
                "source": trigger.source,
                "background": trigger.background,
                **trigger.payload,
            },
        )
        return namespace

    def record_chat_turn(
        self,
        *,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        provider: str,
        model: str,
        mode: str,
    ) -> str:
        trigger = RuntimeTrigger(
            trigger_type="message",
            source="chat-api",
            account=self.config["default_account"],
            channel=f"chat-{slugify(mode)}",
            session_id=conversation_id,
            title=f"Conversazione {conversation_id}",
            content=(
                "### User\n"
                f"{user_message.strip()}\n\n"
                "### Assistant\n"
                f"{assistant_message.strip()}\n\n"
                f"Provider: `{provider}` | Model: `{model}`"
            ),
            payload={"provider": provider, "model": model, "mode": mode},
            background=False,
        )
        return self.route_trigger(trigger)

    def trigger_from_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        account = str(payload.get("account") or self.config["default_account"])
        channel = str(payload.get("channel") or self.config["default_channel"])
        session_id = str(payload.get("session_id") or payload.get("namespace") or f"{channel}-session")
        trigger = RuntimeTrigger(
            trigger_type=str(payload.get("trigger_type") or "webhook"),
            source=str(payload.get("source") or "api"),
            account=account,
            channel=channel,
            session_id=session_id,
            title=str(payload.get("title") or f"Trigger {payload.get('trigger_type', 'webhook')}").strip(),
            content=str(payload.get("content") or json.dumps(payload, ensure_ascii=False, indent=2)),
            payload={k: v for k, v in payload.items() if k not in {"content"}},
            background=bool(payload.get("background", False)) if self.config["background_isolation"] else False,
        )
        namespace = self.route_trigger(trigger)
        return {"status": "ok", "namespace": namespace, "trigger_type": trigger.trigger_type}

    # ──────────────────────────────────────────────────────
    # Background loops
    # ──────────────────────────────────────────────────────
    async def start(self) -> None:
        if not self.config.get("enabled", True):
            self._write_runtime_state("disabled")
            return
        if any(not task.done() for task in self._tasks):
            return

        self._stop_event = asyncio.Event()
        self._watch_snapshot = self._build_watch_snapshot()
        self._tasks = [
            asyncio.create_task(self._heartbeat_loop(), name="autonomy-heartbeat"),
            asyncio.create_task(self._cron_loop(), name="autonomy-cron"),
            asyncio.create_task(self._file_watch_loop(), name="autonomy-file-watch"),
        ]
        self._write_runtime_state("running")

    async def stop(self) -> None:
        self._stop_event.set()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
        self._tasks = []
        self._write_runtime_state("stopped")

    async def _heartbeat_loop(self) -> None:
        while not self._stop_event.is_set():
            self.trigger_from_payload({
                "trigger_type": "heartbeat",
                "source": "runtime-loop",
                "account": "system",
                "channel": "heartbeat",
                "session_id": "main-planner",
                "title": "Heartbeat runtime autonomo",
                "content": (
                    "Tick periodico del runtime autonomo. "
                    "Conferma che scheduler, memoria persistente e routing delle sessioni sono attivi."
                ),
                "background": True,
            })
            self._write_runtime_state("running")
            await asyncio.sleep(int(self.config["heartbeat_sec"]))

    async def _cron_loop(self) -> None:
        while not self._stop_event.is_set():
            now = utc_now()
            slot = now.strftime("%H:%M")
            slot_key = now.strftime("%Y-%m-%dT%H:%M")
            if slot in self.config["cron_utc"] and self._last_cron_slot != slot_key:
                self._last_cron_slot = slot_key
                namespace = self.trigger_from_payload({
                    "trigger_type": "cron",
                    "source": "runtime-cron",
                    "account": "system",
                    "channel": "scheduler",
                    "session_id": "daily-planner",
                    "title": f"Trigger cron {slot} UTC",
                    "content": (
                        "Attivazione temporale stile cron. "
                        "Eseguo manutenzione sessioni, compattazione e keep-warm del contesto persistente."
                    ),
                    "cron_slot": slot,
                    "background": True,
                })
                await asyncio.to_thread(self._compact_active_sessions, namespace["namespace"] if isinstance(namespace, dict) else None)
            await asyncio.sleep(20)

    def _build_watch_snapshot(self) -> dict[str, float]:
        snapshot: dict[str, float] = {}
        allowed_ext = {ext.lower() for ext in self.config["watch_extensions"]}
        for rel_dir in self.config["watch_dirs"]:
            base = (self.project_root / rel_dir).resolve()
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file():
                    continue
                if allowed_ext and path.suffix.lower() not in allowed_ext:
                    continue
                try:
                    snapshot[str(path)] = path.stat().st_mtime
                except Exception:
                    continue
        return snapshot

    async def _file_watch_loop(self) -> None:
        while not self._stop_event.is_set():
            changed: list[str] = []
            current = self._build_watch_snapshot()
            previous = self._watch_snapshot
            for path_str, mtime in current.items():
                if path_str not in previous or previous[path_str] != mtime:
                    changed.append(path_str)
            self._watch_snapshot = current

            if changed:
                max_files = int(self.config["max_files_per_tick"])
                changed = changed[:max_files]
                rel_paths = [str(Path(path).resolve().relative_to(self.project_root)) for path in changed]
                self.trigger_from_payload({
                    "trigger_type": "file-change",
                    "source": "file-watch",
                    "account": "system",
                    "channel": "filesystem",
                    "session_id": "project-watch",
                    "title": f"Modifica file rilevata ({len(rel_paths)})",
                    "content": "\n".join(["File modificati:"] + [f"- {item}" for item in rel_paths]),
                    "files": rel_paths,
                    "background": True,
                })
            await asyncio.sleep(int(self.config["watch_poll_sec"]))

    def _compact_active_sessions(self, exclude_namespace: Optional[str] = None) -> None:
        index = self._read_index()
        sessions = index.get("sessions", {})
        for namespace in list(sessions.keys())[:50]:
            if exclude_namespace and namespace == exclude_namespace:
                continue
            state = self._read_session_state(namespace)
            if int(state.get("note_count", 0)) >= int(self.config["compact_every_notes"]):
                self.compact_namespace(namespace)

    # ──────────────────────────────────────────────────────
    # Public status helpers
    # ──────────────────────────────────────────────────────
    def list_sessions(self) -> dict[str, Any]:
        index = self._read_index()
        items = []
        for namespace, meta in sorted(index.get("sessions", {}).items()):
            state = self._read_session_state(namespace)
            items.append({
                **meta,
                "note_count": state.get("note_count", 0),
                "event_count": state.get("event_count", 0),
                "last_trigger_type": state.get("last_trigger_type"),
                "updated_at": state.get("updated_at"),
            })
        return {
            "status": "ok",
            "count": len(items),
            "sessions": items,
            "generated_at": utc_iso(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "runtime": json.loads(self.runtime_state_path.read_text(encoding="utf-8")) if self.runtime_state_path.exists() else {},
            "sessions": self.list_sessions(),
            "paths": {
                "base": str(self.data_dir),
                "sessions_dir": str(self.sessions_dir),
                "index": str(self.index_path),
                "config": str(self.config_path),
            },
        }
