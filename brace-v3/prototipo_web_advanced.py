#!/usr/bin/env python3
"""
GIU-L_IA v3.1 PROTOTIPO — Web UI Avanzato
Porta 9001 — Interface Interattiva con Controllo Sviluppatore Remoto
Backend + Frontend Integrati • Performance Massima iMac
"""

import http.server
import json
import socketserver
import ssl
import subprocess
import sys
from pathlib import Path

BRACE_DIR = Path(__file__).resolve().parent
PORT = 9001
CERT_DIR = BRACE_DIR / ".security_certs_proto"
CERT_FILE = CERT_DIR / "proto_localhost.pem"
KEY_FILE = CERT_DIR / "proto_localhost_key.pem"
VIDEO_FILE = BRACE_DIR / "media" / "progetto-giulia.m4v"
DOWNLOAD_VIDEO_FILE = Path.home() / "Downloads" / "progetto giulia.m4v"
VIDEO_ROUTE = "/media/progetto-giulia.m4v"

sys.path.insert(0, str(BRACE_DIR.parent))
from brace_v3 import GIU_L_IA  # noqa: E402
from scenarios_db import SCENARIOS  # noqa: E402


class PrototypeState:
    def __init__(self):
        self.engine = GIU_L_IA()
        self.current_scenario = None
        self.current_turns = []
        self.responses = []
        self.engine_label = "BRACE v4.0 GIU-L_IA"
        self.partner_profile = {
            "name": "GIU-L_IA",
            "role": "partner_femminile",
            "tone": "empatica, rispettosa, orientata al consenso",
            "objective": "educazione positiva e relazione sana",
        }


proto_state = PrototypeState()


def get_active_video_file() -> Path:
    for candidate in (VIDEO_FILE, DOWNLOAD_VIDEO_FILE):
        if candidate.exists():
            return candidate
    return VIDEO_FILE


def build_safe_reply(user_text: str, analysis: dict) -> str:
    risk = analysis["risk"]
    prevention = analysis["prevention"]
    phase = analysis["phase"]

    if risk == "high":
        return (
            "Da partner GIU-L_IA ti rispondo con chiarezza e rispetto: qui non seguiamo "
            "pressione, controllo o ambiguita. Fermiamoci, rendiamo espliciti consenso, limiti "
            f"e responsabilita reciproca. Indicazione attiva: {prevention}"
        )
    if risk == "moderate":
        return (
            "Ti ascolto, ma voglio mantenere la relazione su un piano sano e leggibile. "
            "Parliamo in modo diretto, senza forzature, e confermiamo cosa e' reciproco adesso. "
            f"Indicazione utile: {prevention}"
        )

    softened = user_text.strip().rstrip(".!?")
    if softened:
        return (
            f"Ti ascolto con presenza e rispetto. Sul tuo messaggio, '{softened}', ti rispondo "
            "come partner femminile GIU-L_IA: chiarezza, consenso esplicito, ascolto reciproco e "
            f"crescita graduale. Siamo in fase {phase}, quindi continuiamo con calma e coerenza."
        )

    return (
        "Sono qui come GIU-L_IA, partner femminile orientata a rispetto, consenso, confini sani "
        "e relazione reciproca. Dimmi pure cosa vuoi affrontare adesso."
    )


class PrototypeHandler(http.server.SimpleHTTPRequestHandler):
    def add_security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("Strict-Transport-Security", "max-age=31536000")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; media-src 'self'",
        )

    def send_json(self, status: int, payload: dict):
        self.send_response(status)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.add_security_headers()
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body) if body else {}

    def serve_video(self, video_path: Path):
        if not video_path.exists():
            self.send_response(404)
            self.add_security_headers()
            self.end_headers()
            return

        file_size = video_path.stat().st_size
        range_header = self.headers.get("Range", "").strip()
        start = 0
        end = file_size - 1
        status_code = 200

        if range_header.startswith("bytes="):
            byte_range = range_header.split("=", 1)[1]
            start_raw, _, end_raw = byte_range.partition("-")
            try:
                if start_raw:
                    start = int(start_raw)
                if end_raw:
                    end = int(end_raw)
            except ValueError:
                self.send_response(416)
                self.add_security_headers()
                self.end_headers()
                return

            if start >= file_size or start < 0:
                self.send_response(416)
                self.add_security_headers()
                self.end_headers()
                return

            end = min(end, file_size - 1)
            status_code = 206

        content_length = end - start + 1
        self.send_response(status_code)
        self.send_header("Content-type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(content_length))
        if status_code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.add_security_headers()
        self.end_headers()

        with video_path.open("rb") as handle:
            handle.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk = handle.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.add_security_headers()
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif self.path == VIDEO_ROUTE:
            self.serve_video(get_active_video_file())

        elif self.path == "/api/scenarios":
            self.send_json(200, {"scenarios": list(SCENARIOS.keys())})

        elif self.path == "/api/config":
            active_video = get_active_video_file()
            cfg = {
                "engine": proto_state.engine_label,
                "port": PORT,
                "video_route": VIDEO_ROUTE,
                "video_available": active_video.exists(),
                "video_file": str(active_video),
                "video_filename": active_video.name,
                "partner_profile": proto_state.partner_profile,
            }
            self.send_json(200, cfg)

        elif self.path == "/api/state":
            state_data = {
                "phase": proto_state.engine.phase.value,
                "trust_score": proto_state.engine.trust_score,
                "turn_count": proto_state.engine.turn_count,
                "scenario": proto_state.current_scenario,
                "responses_count": len(proto_state.responses),
                "partner": proto_state.partner_profile,
            }
            self.send_json(200, state_data)

    def do_HEAD(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.add_security_headers()
            self.end_headers()
        elif self.path == VIDEO_ROUTE:
            video_path = get_active_video_file()
            if not video_path.exists():
                self.send_response(404)
                self.add_security_headers()
                self.end_headers()
                return

            self.send_response(200)
            self.send_header("Content-type", "video/mp4")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(video_path.stat().st_size))
            self.add_security_headers()
            self.end_headers()
        elif self.path == "/api/config":
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.add_security_headers()
            self.end_headers()
        elif self.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.add_security_headers()
            self.end_headers()
        else:
            self.send_response(404)
            self.add_security_headers()
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/load_scenario":
            data = self.read_json_body()
            scenario_name = data.get("scenario")

            if scenario_name in SCENARIOS:
                proto_state.current_scenario = scenario_name
                proto_state.current_turns = SCENARIOS[scenario_name]
                proto_state.engine = GIU_L_IA()
                proto_state.responses = []

                response = {"success": True, "scenario": scenario_name, "turns": len(proto_state.current_turns)}
                self.send_json(200, response)
            else:
                self.send_json(400, {"success": False, "error": "scenario non valido"})

        elif self.path == "/api/process_turn":
            data = self.read_json_body()
            turn_index = data.get("turn_index", 0)

            if turn_index < len(proto_state.current_turns):
                input_text, context = proto_state.current_turns[turn_index]
                state = {}
                output = proto_state.engine.process(input_text, state)

                proto_state.responses.append(
                    {
                        "turn": turn_index + 1,
                        "text": input_text,
                        "context": context,
                        "output": {
                            "phase": output.relational_state["phase"],
                            "trust": output.relational_state["trust_score"],
                            "iai": output.iai_state["score"],
                            "gaming": output.pil_result["window_gaming"],
                            "risk": output.pil_result["risk_level"],
                        },
                    }
                )

                response = {"success": True, "response": proto_state.responses[-1]}
                self.send_json(200, response)
            else:
                self.send_json(400, {"success": False, "error": "turn_index fuori range"})

        elif self.path == "/api/interact":
            data = self.read_json_body()
            user_text = (data.get("text") or "").strip()

            if not user_text:
                self.send_json(400, {"success": False, "error": "testo vuoto"})
                return

            output = proto_state.engine.process(user_text, {})
            analysis = {
                "phase": output.relational_state["phase"],
                "trust": output.relational_state["trust_score"],
                "iai": output.iai_state["score"],
                "risk": output.pil_result["risk_level"],
                "mode": output.pil_result["mode"],
                "bunker_signals": output.pil_result["bunker_signals"],
                "prevention": output.pil_result["prevention"],
            }
            response = {
                "success": True,
                "partner": proto_state.partner_profile,
                "engine": proto_state.engine_label,
                "analysis": analysis,
                "safe_reply": build_safe_reply(user_text, analysis),
            }

            self.send_json(200, response)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GIU-L_IA v4.0 PROTOTIPO — Web UI Avanzato</title>
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
        .video-wrap {
            margin-top: 14px;
            border: 1px solid #00ff00;
            border-radius: 5px;
            overflow: hidden;
            background: #000;
        }
        video {
            width: 100%;
            height: auto;
            display: block;
        }
        textarea {
            width: 100%;
            min-height: 88px;
            padding: 10px;
            background: #111;
            color: #d9ffd9;
            border: 1px solid #00ff00;
            border-radius: 4px;
            font-family: inherit;
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
            <h1>🎯 BRACE v4.0 GIU-L_IA PROTOTIPO</h1>
            <p>Sessione locale fissata • Porta 9001 HTTPS • Partner femminile GIU-L_IA</p>
            <p>🔐 Safety Bunker attivo • Educazione positiva • Consenso e confini</p>
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

                <h2 style="margin-top: 30px;">🎬 Video Sessione</h2>
                <div class="video-wrap">
                    <video controls autoplay muted loop playsinline>
                        <source src="/media/progetto-giulia.m4v" type="video/mp4">
                        Il browser non supporta il video integrato.
                    </video>
                </div>

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
                <label style="display:block; margin: 10px 0 6px;">Interazione utente con partner GIU-L_IA:</label>
                <textarea id="user-input" placeholder="Scrivi qui il tuo messaggio per GIU-L_IA..."></textarea>
                <button onclick="interactNow()">💬 Invia a GIU-L_IA</button>
                <div id="partner-reply" style="margin: 10px 0; font-size: 0.9em; opacity: 0.9;"></div>
                <div class="responses" id="responses-list">
                    <p style="opacity: 0.5;">Carica uno scenario per iniziare...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function loadScenarios() {
            const resp = await fetch('/api/scenarios');
            const payload = await resp.json();
            const scenarios = payload.scenarios || [];
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
                headers: {'Content-Type': 'application/json'},
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
                headers: {'Content-Type': 'application/json'},
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

        async function interactNow() {
            const text = document.getElementById('user-input').value.trim();
            if (!text) return;

            const resp = await fetch('/api/interact', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ text })
            });
            const out = await resp.json();
            if (!out.success) return;

            const risk = out.analysis.risk;
            const partnerBox = document.getElementById('partner-reply');
            partnerBox.innerHTML =
                `<strong>GIU-L_IA:</strong> ${out.safe_reply}<br>` +
                `Rischio: <span class="risk-${risk}">${risk}</span> | Mode: ${out.analysis.mode}`;
        }

        function resetAll() {
            document.getElementById('scenario-select').value = '';
            document.getElementById('responses-list').innerHTML = '';
            location.reload();
        }

        loadScenarios();
        fetch('/api/config')
            .then(resp => resp.json())
            .then(cfg => {
                const partnerBox = document.getElementById('partner-reply');
                partnerBox.innerHTML =
                    '<strong>Profilo attivo:</strong> ' + cfg.partner_profile.name +
                    ' • ruolo: ' + cfg.partner_profile.role +
                    ' • video: ' + cfg.video_filename;
            })
            .catch(() => null);
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
        subprocess.run(
            [  # noqa: S603, S607
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-keyout",
                str(KEY_FILE),
                "-out",
                str(CERT_FILE),
                "-days",
                "365",
                "-nodes",
                "-subj",
                "/CN=localhost",
            ],
            check=True,
            capture_output=True,
        )
        return True
    except Exception:
        return False


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║  🎯 BRACE v4.0 GIU-L_IA PROTOTIPO — Web UI Avanzato      ║")
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
