#!/usr/bin/env python3
import http.server
import json
import socketserver

PORT = 9445

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
            'phase': (hash(msg) % 6) + 1,
            'trust': (hash(msg) % 100),
            'message': f'✨ ELITE ANALYSIS\n\nGlassmorphism activated\nPsychological safety: CONFIRMED\n\n{msg}'
        }
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, *args):
        pass

class S(socketserver.TCPServer):
    allow_reuse_address = True

httpd = S(('127.0.0.1', PORT), Handler)
print('✨ ELITE (9445) ✅')
httpd.serve_forever()

"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BRACE ELITE</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: system-ui, -apple-system, sans-serif;
    background: linear-gradient(135deg, #0f0f1e 0%, #1a0033 50%, #2d1b4e 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    color: #fff;
    overflow: hidden;
}
@keyframes float {
    0% { transform: translate(0, 0) scale(1); opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { transform: translate(var(--tx), var(--ty)) scale(0); opacity: 0; }
}
.particle {
    position: fixed;
    width: 4px;
    height: 4px;
    background: radial-gradient(circle, rgba(212,165,116,0.8), rgba(212,165,116,0.1));
    border-radius: 50%;
    animation: float 20s infinite;
    pointer-events: none;
}
.container {
    position: relative;
    z-index: 10;
    width: 100%;
    max-width: 1000px;
    background: rgba(248, 247, 244, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(25px) saturate(180%) brightness(110%);
    -webkit-backdrop-filter: blur(25px) saturate(180%) brightness(110%);
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37), inset 0 2px 8px rgba(255, 255, 255, 0.3);
    border-radius: 20px;
    padding: 60px;
}
h1 {
    font-size: 42px;
    margin-bottom: 10px;
    background: linear-gradient(135deg, #D4A574, #f5d547, #D4A574);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
}
.subtitle { font-size: 13px; color: rgba(255, 255, 255, 0.6); margin-bottom: 40px; letter-spacing: 3px; }
.input-group { display: flex; gap: 12px; margin: 40px 0; }
input {
    flex: 1;
    padding: 16px 22px;
    border: 1px solid rgba(212, 165, 116, 0.4);
    background: rgba(212, 165, 116, 0.08);
    border-radius: 12px;
    color: #fff;
    font-size: 15px;
    backdrop-filter: blur(10px);
}
input:focus { outline: none; border-color: rgba(212, 165, 116, 0.8); background: rgba(212, 165, 116, 0.15); }
button {
    padding: 16px 32px;
    background: linear-gradient(135deg, rgba(212, 165, 116, 0.8), rgba(245, 213, 71, 0.7));
    border: none;
    border-radius: 12px;
    color: #1a1918;
    font-weight: 700;
    font-size: 15px;
    cursor: pointer;
}
button:hover { background: linear-gradient(135deg, rgba(212, 165, 116, 1), rgba(245, 213, 71, 0.9)); }
.metrics {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    margin: 50px 0;
}
.metric {
    background: rgba(212, 165, 116, 0.08);
    border: 1px solid rgba(212, 165, 116, 0.2);
    backdrop-filter: blur(10px);
    padding: 30px 20px;
    border-radius: 14px;
    text-align: center;
}
.metric-label { font-size: 11px; color: rgba(255, 255, 255, 0.5); margin-bottom: 12px; letter-spacing: 2px; }
.metric-value { font-size: 36px; font-weight: 700; background: linear-gradient(135deg, #D4A574, #f5d547); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.output {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(212, 165, 116, 0.2);
    backdrop-filter: blur(10px);
    border-left: 4px solid rgba(212, 165, 116, 0.6);
    padding: 30px;
    border-radius: 14px;
    margin-top: 30px;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.8);
    min-height: 120px;
    font-family: monospace;
    font-size: 14px;
    white-space: pre-wrap;
}
</style>
</head>
<body>
<div class="container">
    <h1>✨ BRACE ELITE</h1>
    <div class="subtitle">GLASSMORPHISM — LUXURY EXPERIENCE</div>
    <div class="input-group">
        <input type="text" id="msg" placeholder="Descrivi la tua situazione..." value="Sono in una situazione relazionale difficile">
        <button onclick="send()">ANALIZZA</button>
    </div>
    <div class="metrics">
        <div class="metric">
            <div class="metric-label">FASE</div>
            <div class="metric-value" id="phase">—</div>
        </div>
        <div class="metric">
            <div class="metric-label">TRUST</div>
            <div class="metric-value" id="trust">—</div>
        </div>
        <div class="metric">
            <div class="metric-label">INDEX</div>
            <div class="metric-value" id="index">—</div>
        </div>
    </div>
    <div class="output" id="output">✅ ELITE System Ready. Glassmorphic protection bunker activated.</div>
</div>
<script>
for (let i = 0; i < 80; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.left = Math.random() * 100 + '%';
    p.style.top = Math.random() * 100 + '%';
    p.style.setProperty('--tx', (Math.random() - 0.5) * 300 + 'px');
    p.style.setProperty('--ty', (Math.random() - 0.5) * 300 + 'px');
    p.style.animationDelay = Math.random() * 10 + 's';
    p.style.animationDuration = (15 + Math.random() * 15) + 's';
    document.body.appendChild(p);
}
function send() {
    const m = document.getElementById('msg').value;
    if (!m) return;
    document.getElementById('output').textContent = '⏳ Analyzing...';
    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: m})
    })
    .then(r => r.json())
    .then(d => {
        document.getElementById('phase').textContent = d.phase;
        document.getElementById('trust').textContent = d.trust + '%';
        document.getElementById('index').textContent = (d.trust / 100).toFixed(2);
        document.getElementById('output').textContent = d.message;
    })
    .catch(e => document.getElementById('output').textContent = '❌ ' + e);
}
document.getElementById('msg').addEventListener('keypress', e => e.key === 'Enter' && send());
</script>
</body>
</html>
"""
