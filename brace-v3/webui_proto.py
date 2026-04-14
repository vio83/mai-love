#!/usr/bin/env python3
import http.server
import json
import socketserver

PORT = 9444

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = open(__file__).read().split('"""')[2]
        self.wfile.write(html.encode())

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        data = json.loads(body)
        msg = data.get('message', '')

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            'status': 'ok',
            'message': f'🎭 ADVANCED ANALYSIS\n\nSituazione: {msg}\n\nScenario protocol activated\nTrust analysis: In progress\nRecommendations: Generating...'
        }
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, *args):
        pass

class S(socketserver.TCPServer):
    allow_reuse_address = True

httpd = S(('127.0.0.1', PORT), Handler)
print('🌿 PROTOTIPO (9444) ✅')
httpd.serve_forever()

"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BRACE PROTOTIPO</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: system-ui, -apple-system, sans-serif;
    background: linear-gradient(135deg, #2d5a4e 0%, #4a7a6d 20%, #6b9b8f 40%, #a8d5c8 60%, #7ab5a8 80%, #2d5a4e 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    color: #fff;
}
.container {
    width: 100%;
    max-width: 900px;
    background: rgba(45, 90, 78, 0.25);
    backdrop-filter: blur(12px);
    border: 2px solid rgba(168, 213, 200, 0.3);
    border-radius: 22px;
    padding: 50px;
}
h1 { font-size: 38px; margin-bottom: 8px; color: #a8d5c8; font-weight: 700; }
.subtitle { font-size: 13px; color: rgba(255, 255, 255, 0.7); margin-bottom: 30px; letter-spacing: 2px; }
.tabs {
    display: flex;
    gap: 12px;
    margin-bottom: 30px;
    border-bottom: 2px solid rgba(168, 213, 200, 0.2);
    padding-bottom: 12px;
}
.tab {
    flex: 1;
    padding: 11px 18px;
    background: transparent;
    border: 2px solid rgba(168, 213, 200, 0.3);
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.7);
    font-weight: 600;
    cursor: pointer;
}
.tab.active { background: rgba(168, 213, 200, 0.2); color: #a8d5c8; border-color: rgba(168, 213, 200, 0.6); }
.content { display: none; }
.content.active { display: block; }
input {
    width: 100%;
    padding: 13px 17px;
    border: 2px solid rgba(168, 213, 200, 0.3);
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    color: #fff;
    font-size: 15px;
    margin-bottom: 12px;
}
input:focus { outline: none; border-color: rgba(168, 213, 200, 0.6); background: rgba(255, 255, 255, 0.15); }
button {
    width: 100%;
    padding: 13px;
    background: linear-gradient(135deg, #4a7a6d, #6b9b8f);
    border: none;
    border-radius: 10px;
    color: #fff;
    font-weight: 700;
    cursor: pointer;
}
button:hover { background: linear-gradient(135deg, #6b9b8f, #a8d5c8); }
.scenario {
    background: rgba(168, 213, 200, 0.1);
    border: 2px solid rgba(168, 213, 200, 0.3);
    padding: 18px;
    border-radius: 10px;
    margin-bottom: 12px;
    cursor: pointer;
    font-weight: 600;
    color: #a8d5c8;
    transition: all 0.3s;
}
.scenario:hover { background: rgba(168, 213, 200, 0.2); transform: translateX(4px); }
.output {
    background: rgba(0, 0, 0, 0.2);
    border: 2px solid rgba(168, 213, 200, 0.2);
    border-left: 4px solid rgba(168, 213, 200, 0.6);
    padding: 22px;
    border-radius: 10px;
    margin-top: 18px;
    line-height: 1.7;
    color: rgba(255, 255, 255, 0.85);
    min-height: 100px;
    font-family: monospace;
    font-size: 13px;
    white-space: pre-wrap;
}
</style>
</head>
<body>
<div class="container">
    <h1>🌿 BRACE PROTOTIPO</h1>
    <div class="subtitle">Luxury Spa — Advanced Scenarios</div>
    <div class="tabs">
        <button class="tab active" onclick="switchTab(0)">📝 FREE CHAT</button>
        <button class="tab" onclick="switchTab(1)">🎭 SCENARIOS</button>
    </div>
    <div class="content active" id="c0">
        <input type="text" id="msg0" placeholder="Descrivi la situazione..." value="Sono in una situazione relazionale difficile">
        <button onclick="analyzeChat()">ANALIZZA</button>
        <div class="output" id="out0">✅ Pronto per analisi libera.</div>
    </div>
    <div class="content" id="c1">
        <div class="scenario" onclick="runScenario('⚔️ Conflitto', 'Gestione disagio')">⚔️ CONFLITTO RELAZIONALE</div>
        <div class="scenario" onclick="runScenario('💔 Tradimento', 'Ricostruzione fiducia')">💔 TRADIMENTO</div>
        <div class="scenario" onclick="runScenario('🗣️ Comunicazione', 'Ascolto reciproco')">🗣️ COMUNICAZIONE</div>
        <div class="scenario" onclick="runScenario('📏 Distanza', 'Riavvicinamento')">📏 DISTANZA EMOTIVA</div>
        <div class="scenario" onclick="runScenario('🤝 Dipendenza', 'Equilibrio')">🤝 DIPENDENZA EMOTIVA</div>
        <div class="output" id="out1">Seleziona scenario...</div>
    </div>
</div>
<script>
function switchTab(i) {
    document.querySelectorAll('.tab').forEach((t, x) => t.className = x === i ? 'tab active' : 'tab');
    document.querySelectorAll('.content').forEach((c, x) => c.className = x === i ? 'content active' : 'content');
}
function analyzeChat() {
    const m = document.getElementById('msg0').value;
    if (!m) return;
    document.getElementById('out0').textContent = '⏳ Analizzando...';
    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: m})
    })
    .then(r => r.json())
    .then(d => document.getElementById('out0').textContent = d.message)
    .catch(e => document.getElementById('out0').textContent = '❌ ' + e);
}
function runScenario(t, d) {
    document.getElementById('out1').textContent = '🎭 ' + t + '\n' + d + '\n\n✅ Protocol activated\nAnalyzing relational dynamics...';
}
document.getElementById('msg0').addEventListener('keypress', e => e.key === 'Enter' && analyzeChat());
</script>
</body>
</html>
"""
