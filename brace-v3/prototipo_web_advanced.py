#!/usr/bin/env python3
"""
GIU-L_IA v3.1 PROTOTIPO — Web UI Avanzato
Porta 9001 — Interface Interattiva con Controllo Sviluppatore Remoto
Backend + Frontend Integrati • Performance Massima iMac
"""

import http.server
import json
import os
import socketserver
import ssl
import subprocess
import sys
from pathlib import Path

BRACE_DIR = Path(__file__).resolve().parent
PORT = int(os.getenv("GIULIA_PROTO_PORT", "9001"))
CERT_DIR = BRACE_DIR / ".security_certs_proto"
CERT_FILE = CERT_DIR / "proto_localhost.pem"
KEY_FILE = CERT_DIR / "proto_localhost_key.pem"

sys.path.insert(0, str(BRACE_DIR.parent))
from brace_v3 import GIU_L_IA  # noqa: E402
from scenarios_db import SCENARIOS  # noqa: E402


class PrototypeState:
    def __init__(self):
        self.engine = GIU_L_IA()
        self.current_scenario = None
        self.current_turns = []
        self.responses = []

proto_state = PrototypeState()

class PrototypeHandler(http.server.SimpleHTTPRequestHandler):
    def add_security_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Strict-Transport-Security', 'max-age=31536000')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.add_security_headers()
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))

        elif self.path == '/api/scenarios':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            self.wfile.write(json.dumps(list(SCENARIOS.keys())).encode('utf-8'))

        elif self.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.add_security_headers()
            self.end_headers()
            state_data = {
                "phase": proto_state.engine.phase.value,
                "trust_score": proto_state.engine.trust_score,
                "turn_count": proto_state.engine.turn_count,
                "scenario": proto_state.current_scenario,
                "responses_count": len(proto_state.responses)
            }
            self.wfile.write(json.dumps(state_data).encode('utf-8'))

    def do_POST(self):
        if self.path == '/api/load_scenario':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            scenario_name = data.get('scenario')

            if scenario_name in SCENARIOS:
                proto_state.current_scenario = scenario_name
                proto_state.current_turns = SCENARIOS[scenario_name]
                proto_state.engine = GIU_L_IA()
                proto_state.responses = []

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.add_security_headers()
                self.end_headers()

                response = {
                    "success": True,
                    "scenario": scenario_name,
                    "turns": len(proto_state.current_turns)
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                self.send_response(400)
                self.end_headers()

        elif self.path == '/api/process_turn':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            turn_index = data.get('turn_index', 0)

            if turn_index < len(proto_state.current_turns):
                input_text, context = proto_state.current_turns[turn_index]
                state = {}
                output = proto_state.engine.process(input_text, state)

                proto_state.responses.append({
                    "turn": turn_index + 1,
                    "text": input_text,
                    "context": context,
                    "output": {
                        "phase": output.relational_state['phase'],
                        "trust": output.relational_state['trust_score'],
                        "iai": output.iai_state['score'],
                        "gaming": output.pil_result['window_gaming'],
                        "risk": output.pil_result['risk_level']
                    }
                })

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.add_security_headers()
                self.end_headers()

                response = {"success": True, "response": proto_state.responses[-1]}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                self.send_response(400)
                self.end_headers()


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GIU-L_IA v3.1 PROTOTIPO — Web UI Avanzato</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Fira Code', 'Monaco', monospace;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #00ff00;
            line-height: 1.6;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            border: 2px solid #00ff00;
            padding: 20px;
            margin-bottom: 30px;
            background: rgba(0, 255, 0, 0.05);
            border-radius: 5px;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header p { opacity: 0.7; }
        .main {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
        }
        .panel {
            border: 1px solid #00ff00;
            padding: 20px;
            background: rgba(0, 30, 0, 0.3);
            border-radius: 5px;
        }
        .panel h2 {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #00ff00;
            border-bottom: 1px solid #00ff00;
            padding-bottom: 10px;
        }
        select, button {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            background: #1a1a1a;
            color: #00ff00;
            border: 1px solid #00ff00;
            border-radius: 3px;
            font-family: inherit;
            cursor: pointer;
            transition: all 0.2s;
        }
        select:hover, button:hover {
            background: #00ff00;
            color: #000;
        }
        .metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
        }
        .metric {
            padding: 10px;
            background: rgba(0, 255, 0, 0.1);
            border-left: 3px solid #00ff00;
        }
        .metric-label { opacity: 0.7; font-size: 0.9em; }
        .metric-value { font-size: 1.3em; font-weight: bold; color: #00ff00; }
        .responses {
            max-height: 500px;
            overflow-y: auto;
        }
        .response-item {
            padding: 10px;
            margin: 10px 0;
            background: rgba(0, 255, 0, 0.05);
            border-left: 3px solid #00ff00;
            font-size: 0.9em;
        }
        .response-item.gaming {
            border-left-color: #ff0000;
            background: rgba(255, 0, 0, 0.05);
        }
        .risk-high { color: #ff0000; font-weight: bold; }
        .risk-moderate { color: #ffaa00; font-weight: bold; }
        .risk-low { color: #00ff00; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 BRACE v3.0 PROTOTIPO</h1>
            <p>Web UI Avanzato • Performance Massima • Porta 9001 HTTPS</p>
            <p>🔐 Modifica Remota Abilitata • Sincronizzazione VS Code In Tempo Reale</p>
        </div>

        <div class="main">
            <div class="panel" id="control-panel">
                <h2>⚙️  Controlli</h2>
                <label>Seleziona Scenario:</label>
                <select id="scenario-select">
                    <option value="">-- Carica Scenario --</option>
                </select>
                <button onclick="loadScenario()">📂 Carica</button>
                <button onclick="nextTurn()">▶️  Turn Successivo</button>
                <button onclick="resetAll()">🔄 Reset</button>

                <h2 style="margin-top: 30px;">📊 Metriche Attuali</h2>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Fase</div>
                        <div class="metric-value" id="metric-phase">1</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Trust Score</div>
                        <div class="metric-value" id="metric-trust">50%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">IAI Score</div>
                        <div class="metric-value" id="metric-iai">0.10</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Turn</div>
                        <div class="metric-value" id="metric-turn">0</div>
                    </div>
                </div>

                <div style="margin-top: 20px; padding: 10px; background: rgba(255, 170, 0, 0.1); border-left: 3px solid #ffaa00; font-size: 0.85em;">
                    💡 <strong>Tip:</strong> Accedi via SSH Remote (VS Code) per modificare lo scenario in real-time
                </div>
            </div>

            <div class="panel">
                <h2>📋 Risposte Scenario</h2>
                <div class="responses" id="responses-list">
                    <p style="opacity: 0.5;">Carica uno scenario per iniziare...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function loadScenarios() {
            const resp = await fetch('/api/scenarios');
            const scenarios = await resp.json();
            const select = document.getElementById('scenario-select');
            scenarios.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s;
                opt.innerText = s;
                select.appendChild(opt);
            });
        }

        async function loadScenario() {
            const scenario = document.getElementById('scenario-select').value;
            if (!scenario) return;
            const resp = await fetch('/api/load_scenario', {
                method: 'POST',
                body: JSON.stringify({scenario})
            });
            document.getElementById('responses-list').innerHTML = '';
            alert('Scenario caricato: ' + scenario);
        }

        async function nextTurn() {
            const resp = await fetch('/api/state');
            const state = await resp.json();
            if (!state.scenario) { alert('Carica uno scenario prima'); return; }

            const proc = await fetch('/api/process_turn', {
                method: 'POST',
                body: JSON.stringify({turn_index: state.responses_count})
            });
            const result = await proc.json();

            if (result.success) {
                const r = result.response;
                const div = document.createElement('div');
                div.className = 'response-item' + (r.output.gaming ? ' gaming' : '');
                div.innerHTML = `
                    <strong>Turn ${r.turn}:</strong> ${r.text}<br>
                    Phase: ${r.output.phase} | Trust: ${r.output.trust.toFixed(1)}% |
                    Risk: <span class="risk-${r.output.risk}">${r.output.risk}</span>
                `;
                document.getElementById('responses-list').appendChild(div);
                await updateMetrics();
            }
        }

        async function updateMetrics() {
            const resp = await fetch('/api/state');
            const state = await resp.json();
            document.getElementById('metric-phase').innerText = state.phase;
            document.getElementById('metric-trust').innerText = state.trust_score.toFixed(1) + '%';
            document.getElementById('metric-turn').innerText = state.turn_count;
        }

        function resetAll() {
            document.getElementById('scenario-select').value = '';
            document.getElementById('responses-list').innerHTML = '';
            location.reload();
        }

        loadScenarios();
        setInterval(updateMetrics, 2000);
    </script>
</body>
</html>"""


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def create_cert():
    """Crea certificato auto-firmato"""
    if CERT_FILE.exists() and KEY_FILE.exists():
        return True
    CERT_DIR.mkdir(exist_ok=True)
    try:
        subprocess.run([  # noqa: S603, S607
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", str(KEY_FILE), "-out", str(CERT_FILE),
            "-days", "365", "-nodes",
            "-subj", "/CN=localhost"
        ], check=True, capture_output=True)
        return True
    except Exception:
        return False


if __name__ == '__main__':
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║  🎯 BRACE v3.0 PROTOTIPO — Web UI Avanzato               ║")
    print(f"║  Performance Massima • iMac Arch Linux • Porta {PORT:<9}║")
    print("╚════════════════════════════════════════════════════════════╝")

    if create_cert():
        print(f"  ✅ Certificato: {CERT_FILE}")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(CERT_FILE), str(KEY_FILE))

        httpd = ReusableTCPServer(("127.0.0.1", PORT), PrototypeHandler)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

        print(f"\n  🌐 HTTPS://localhost:{PORT}/")
        print("  🔒 Sicurezza: Privacy Bunker + Security Bunker")
        print("\n  📡 VS Code SSH Remote: vio@172.20.10.5")
        print("  ⏹️  Premi Ctrl+C per fermare\n")

        httpd.serve_forever()
    else:
        print("  ❌ Errore creazione certificato")
