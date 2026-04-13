#!/usr/bin/env python3
"""
VS Code True Mirror System
Sincronizzazione Editor State in Real-Time (WebSocket)
Digita su MacBook Air → Vedi su iMac (specchio visivo identico)
"""

import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path

import websockets


class VSCodeMirrorServer:
    """Server WebSocket per mirrorare VS Code in tempo reale"""

    def __init__(self, port=9999):
        self.port = port
        self.clients = set()
        self.current_file = ""
        self.current_content = ""
        self.cursor_pos = 0

    async def mirror_handler(self, websocket, path):
        """Handle WebSocket connections for mirror sync"""
        self.clients.add(websocket)
        print(f"✅ Client connesso: {websocket.remote_address}")

        try:
            async for message in websocket:
                data = json.loads(message)
                await self.broadcast_mirror(data)
        finally:
            self.clients.remove(websocket)
            print(f"❌ Client disconnesso: {websocket.remote_address}")

    async def broadcast_mirror(self, data):
        """Broadcast editor state to all connected clients"""
        if self.clients:
            message = json.dumps(data)
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )

    async def start_server(self):
        """Start WebSocket server"""
        async with websockets.serve(self.mirror_handler, "0.0.0.0", self.port):
            print(f"🌐 VS Code Mirror Server listening on ws://0.0.0.0:{self.port}")
            await asyncio.Future()  # run forever

    def run(self):
        """Run the mirror server"""
        asyncio.run(self.start_server())


class VSCodeMirrorClient:
    """Client che monitora cambiamenti VS Code e li sincronizza"""

    def __init__(self, server_url="ws://localhost:9999"):
        self.server_url = server_url
        self.last_content = {}
        self.vscode_config_dir = Path.home() / "Library/Application Support/Code/User"

    async def monitor_and_sync(self):
        """Monitora VS Code e sincronizza cambiamenti"""
        async with websockets.connect(self.server_url) as websocket:
            print(f"✅ Connesso al mirror server: {self.server_url}")

            while True:
                try:
                    # Monitora file aperti in VS Code
                    state = self._get_vs_code_state()

                    if state != self.last_content:
                        # Invia stato al server
                        await websocket.send(json.dumps(state))
                        self.last_content = state
                        print(f"📤 Stato sincronizzato: {state.get('file', 'unknown')}")

                    await asyncio.sleep(0.1)  # 100ms sync interval (instant)

                except Exception as e:
                    print(f"❌ Errore sync: {e}")
                    await asyncio.sleep(1)

    def _get_vs_code_state(self):
        """Estrai stato corrente da VS Code"""
        try:
            # Usa VS Code CLI per ottenere file aperto
            result = subprocess.run(
                ["code", "--status"],
                capture_output=True,
                text=True,
                timeout=1
            )

            # Monitora editor.json se disponibile
            editor_file = self.vscode_config_dir / "editor.json"
            if editor_file.exists():
                with open(editor_file) as f:
                    editor_state = json.load(f)
                    return {
                        "file": str(editor_state.get("file", "")),
                        "content": editor_state.get("content", ""),
                        "cursor": editor_state.get("cursor", 0),
                        "selection": editor_state.get("selection", 0),
                        "timestamp": datetime.now().isoformat()
                    }
        except:
            pass

        return self.last_content

    def run(self):
        """Run the mirror client"""
        asyncio.run(self.monitor_and_sync())


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        server = VSCodeMirrorServer(port=9999)
        server.run()
    else:
        client = VSCodeMirrorClient(server_url="ws://172.20.10.5:9999")
        client.run()
