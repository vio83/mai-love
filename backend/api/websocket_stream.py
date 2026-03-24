# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ============================================================
"""
VIO 83 WEBSOCKET STREAMING ENGINE — Piuma™ Real-Time Layer
===========================================================

Streaming token-per-token via WebSocket e Server-Sent Events (SSE).

Vantaggi vs risposta blocco:
  - Prima parola visibile entro 100-300ms (vs 2-10s blocco intero)
  - Perceived latency ridotta del 70-90%
  - Utente vede progresso, non aspetta al buio
  - Supporto stop mid-stream (risparmio token/costi)

Protocolli supportati:
  1. WebSocket  — ws://localhost:8000/ws/stream  (bidirezionale, optimal)
  2. SSE        — GET /stream?q=...              (unidirezionale, browser-native)
  3. Chunked    — POST /chat/stream              (compatibile con tutto)

Formato messaggi WebSocket:
  Client → Server: {"type": "chat", "message": "...", "provr": "auto", "session_id": "..."}
  Server → Client: {"type": "token", "content": "...", "done": false}
  Server → Client: {"type": "done", "content": "", "done": true, "latency_ms": 234, "provr": "claude"}
  Server → Client: {"type": "error", "content": "...", "done": true}
  Client → Server: {"type": "stop"} → interrompe streaming
"""

import asyncio
import json
import time
import uuid
from typing import AsyncGenerator, Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from backend.core.ultra_engine import get_ultra_engine


# ─────────────────────────────────────────────────────────────
# CONNECTION MANAGER
# ─────────────────────────────────────────────────────────────

class WebSocketConnectionManager:
    """
    Gestisce connessioni WebSocket attive.
    Thread-safe, supporta broadcast e messaggi diretti.
    """

    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}
        self._stop_flags: Set[str] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> str:
        """Accetta connessione e ritorna session_id."""
        await ws.accept()
        session_id = str(uuid.uuid4())[:8]
        async with self._lock:
            self._connections[session_id] = ws
        return session_id

    async def disconnect(self, session_id: str):
        async with self._lock:
            self._connections.pop(session_id, None)
            self._stop_flags.discard(session_id)

    def request_stop(self, session_id: str):
        """Richiedi stop streaming per questa sessione."""
        self._stop_flags.add(session_id)

    def should_stop(self, session_id: str) -> bool:
        return session_id in self._stop_flags

    async def send_token(self, session_id: str, content: str, done: bool = False, **extra):
        ws = self._connections.get(session_id)
        if not ws:
            return
        try:
            payload = {"type": "done" if done else "token", "content": content, "done": done}
            payload.update(extra)
            await ws.send_text(json.dumps(payload, ensure_ascii=False))
        except Exception:
            pass

    async def send_error(self, session_id: str, error: str):
        ws = self._connections.get(session_id)
        if not ws:
            return
        try:
            await ws.send_text(json.dumps({"type": "error", "content": error, "done": True}))
        except Exception:
            pass

    @property
    def active_connections(self) -> int:
        return len(self._connections)


# Singleton
_ws_manager: Optional[WebSocketConnectionManager] = None

def get_ws_manager() -> WebSocketConnectionManager:
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketConnectionManager()
    return _ws_manager


# ─────────────────────────────────────────────────────────────
# SSE STREAMING GENERATOR
# ─────────────────────────────────────────────────────────────

async def sse_stream_generator(
    message: str,
    provr_fn,  # async callable(message) -> AsyncGenerator[str, None]
    session_id: Optional[str] = None,
    include_metadata: bool = True,
) -> AsyncGenerator[str, None]:
    """
    Genera eventi SSE da uno stream provr.

    Formato SSE:
        data: {"type": "token", "content": "Ciao"}\n\n
        data: {"type": "done", "latency_ms": 234}\n\n

    Uso con FastAPI:
        return StreamingResponse(
            sse_stream_generator(msg, my_provr_fn),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )
    """
    start = time.monotonic()
    token_count = 0
    full_response = []
    ws_manager = get_ws_manager()

    try:
        async for chunk in provr_fn(message):
            if not chunk:
                continue

            # Check stop signal
            if session_id and ws_manager.should_stop(session_id):
                yield f"data: {json.dumps({'type': 'stopped', 'content': '', 'done': True})}\n\n"
                return

            full_response.append(chunk)
            token_count += 1

            payload = json.dumps({"type": "token", "content": chunk, "done": False}, ensure_ascii=False)
            yield f"data: {payload}\n\n"

            # Small yield per non bloccare event loop su chunk veloci
            if token_count % 10 == 0:
                await asyncio.sleep(0)

        # Done event
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        done_payload = {
            "type": "done",
            "content": "",
            "done": True,
        }
        if include_metadata:
            done_payload.update({
                "latency_ms": latency_ms,
                "tokens_streamed": token_count,
                "full_response_len": sum(len(c) for c in full_response),
            })
        yield f"data: {json.dumps(done_payload)}\n\n"

    except asyncio.CancelledError:
        yield f"data: {json.dumps({'type': 'cancelled', 'done': True})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e), 'done': True})}\n\n"


# ─────────────────────────────────────────────────────────────
# CHUNKED HTTP STREAMING (fallback universale)
# ─────────────────────────────────────────────────────────────

async def chunked_response_generator(
    chunks: AsyncGenerator[str, None],
) -> AsyncGenerator[bytes, None]:
    """
    Genera risposta HTTP chunked per compatibilità massima.
    Funziona con ogni client HTTP (curl, fetch, Requests, ecc.).

    Formato: ogni chunk è JSON su una riga + newline.
    """
    try:
        async for chunk in chunks:
            if chunk:
                line = json.dumps({"token": chunk}, ensure_ascii=False) + "\n"
                yield line.encode("utf-8")
    except Exception as e:
        error_line = json.dumps({"error": str(e)}) + "\n"
        yield error_line.encode("utf-8")


# ─────────────────────────────────────────────────────────────
# MOCK STREAMING PROVR (per testing e demo)
# ─────────────────────────────────────────────────────────────

async def mock_streaming_provr(message: str) -> AsyncGenerator[str, None]:
    """
    Provr streaming mock per testing.
    Simula risposta token-per-token con latenza realistica.
    """
    response = f"Risposta simulata per: '{message[:50]}'. " * 3
    words = response.split()
    for word in words:
        yield word + " "
        await asyncio.sleep(0.05)  # 50ms per parola → ~20 parole/sec


# ─────────────────────────────────────────────────────────────
# WEBSOCKET HANDLER — da registrare in server.py
# ─────────────────────────────────────────────────────────────

async def websocket_chat_handler(
    ws: WebSocket,
    process_message_fn,  # async callable(message, provr, session_id) -> AsyncGen
):
    """
    Handler WebSocket per chat streaming.

    Registrare in server.py:
        @app.websocket("/ws/stream")
        async def ws_stream(ws: WebSocket):
            await websocket_chat_handler(ws, my_process_fn)

    Protocollo:
      1. Client si connette
      2. Server invia {"type": "connected", "session_id": "abc123"}
      3. Client invia {"type": "chat", "message": "...", "provr": "auto"}
      4. Server invia stream di token {"type": "token", "content": "..."}
      5. Server invia {"type": "done", ...} quando finisce
      6. Client può inviare {"type": "stop"} per interrompere
      7. Client si disconnette o invia {"type": "ping"} per keepalive
    """
    manager = get_ws_manager()
    session_id = await manager.connect(ws)
    engine = get_ultra_engine()

    try:
        # Welcome message
        await ws.send_text(json.dumps({
            "type": "connected",
            "session_id": session_id,
            "server": "VIO 83 AI Orchestra™",
            "version": "0.9.0",
        }))

        while True:
            try:
                raw = await asyncio.wait_for(ws.receive_text(), timeout=300)
                data = json.loads(raw)
            except asyncio.TimeoutError:
                # Keepalive ping
                await ws.send_text(json.dumps({"type": "ping"}))
                continue
            except json.JSONDecodeError:
                await manager.send_error(session_id, "Invalid JSON")
                continue

            msg_type = data.get("type", "")

            if msg_type == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
                continue

            elif msg_type == "stop":
                manager.request_stop(session_id)
                continue

            elif msg_type == "chat":
                message = data.get("message", "").strip()
                if not message:
                    await manager.send_error(session_id, "Empty message")
                    continue

                provr = data.get("provr", "auto")
                start = time.monotonic()

                # Check cache semantica prima di chiamare provr
                cache_key = engine.cache.make_key(message) if hasattr(engine.cache, 'make_key') else message[:50]
                cached = engine.cache.get(cache_key, semantic_key=message)
                if cached:
                    # Serve da cache come stream (simula streaming)
                    words = str(cached).split()
                    for word in words:
                        if manager.should_stop(session_id):
                            break
                        await manager.send_token(session_id, word + " ")
                        await asyncio.sleep(0.01)  # 10ms/word da cache

                    await manager.send_token(
                        session_id, "", done=True,
                        latency_ms=round((time.monotonic() - start) * 1000, 1),
                        provr="cache",
                        from_cache=True,
                    )
                    continue

                # Intent routing
                intent = engine.router.classify(message)

                # Stream effettivo
                full_chunks = []
                try:
                    async for chunk in process_message_fn(message, provr, session_id, intent):
                        if manager.should_stop(session_id):
                            break
                        full_chunks.append(chunk)
                        await manager.send_token(session_id, chunk)

                    full_response = "".join(full_chunks)

                    # Salva in cache semantica
                    if full_response and len(full_response) > 20:
                        engine.cache.set(cache_key, full_response, semantic_key=message)

                    await manager.send_token(
                        session_id, "", done=True,
                        latency_ms=round((time.monotonic() - start) * 1000, 1),
                        provr=provr,
                        intent=intent,
                        from_cache=False,
                    )

                except Exception as e:
                    await manager.send_error(session_id, f"Stream error: {str(e)}")

            else:
                await manager.send_error(session_id, f"Unknown message type: {msg_type}")

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await manager.disconnect(session_id)


# ─────────────────────────────────────────────────────────────
# STREAMING RESPONSE HELPER
# ─────────────────────────────────────────────────────────────

def make_sse_response(
    generator: AsyncGenerator,
    extra_headers: Optional[Dict] = None
) -> StreamingResponse:
    """
    Crea StreamingResponse SSE con headers corretti.

    Uso:
        return make_sse_response(sse_stream_generator(msg, provr_fn))
    """
    headers = {
        "Cache-Control": "no-cache, no-store",
        "X-Accel-Buffering": "no",          # Disable Nginx buffering
        "Access-Control-Allow-Origin": "*",
        "Transfer-Encoding": "chunked",
    }
    if extra_headers:
        headers.update(extra_headers)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers=headers,
    )
