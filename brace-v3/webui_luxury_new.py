#!/usr/bin/env python3
"""BRACE Investor Experience — Luxury 3D Hotel Lobby UI.

Full standalone HTTP server. No external CDN dependencies.
3D scene rendered via Canvas 2D API.
"""

from __future__ import annotations

import http.server
import json
import os
import socketserver
import ssl
import subprocess
import urllib.request
from pathlib import Path

HOST = "127.0.0.1"
PORT = int(os.getenv("BRACE_PORT", "9443"))
USE_TLS = os.getenv("BRACE_USE_TLS", "0").strip().lower() not in {"0", "false", "no", "off"}
BACKEND = os.getenv("BRACE_BACKEND_BASE", "http://127.0.0.1:4000")

BASE_DIR = Path(__file__).resolve().parent
CERT_DIR = BASE_DIR / ".security_certs"
CERT_FILE = CERT_DIR / "brace_localhost.pem"
KEY_FILE  = CERT_DIR / "brace_localhost_key.pem"


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def ensure_cert() -> bool:
    if CERT_FILE.exists() and KEY_FILE.exists():
        return True
    CERT_DIR.mkdir(exist_ok=True)
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", str(KEY_FILE), "-out", str(CERT_FILE),
        "-days", "365", "-nodes",
        "-subj", "/C=IT/ST=Local/L=Localhost/O=BRACE/CN=localhost",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)  # noqa: S603  # nosec B603
        CERT_FILE.chmod(0o600)
        KEY_FILE.chmod(0o600)
        return True
    except Exception as exc:
        print(f"TLS cert error: {exc}")
        return False


def _proxy(path: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    url = f"{BACKEND}{path}"
    body = None
    headers: dict = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=headers)  # noqa: S310 — localhost proxy
    try:
        with urllib.request.urlopen(req, timeout=12) as res:  # noqa: S310  # nosec B310 — localhost only
            return int(res.status), json.loads(res.read().decode("utf-8"))
    except Exception as exc:
        return 502, {"error": str(exc)}


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        )
        super().end_headers()

    def _json(self, code: int, payload: dict):
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))
            return
        if self.path == "/api/state":
            c, d = _proxy("/brace/state")
            self._json(c, d)
            return
        if self.path == "/api/scenarios":
            c, d = _proxy("/brace/scenarios")
            if c == 200 and isinstance(d.get("scenarios"), dict):
                d = {"scenarios": list(d["scenarios"].keys())}
            self._json(c, d)
            return
        self._json(404, {"error": "Not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode("utf-8") if n > 0 else "{}"
        payload = json.loads(body)
        if self.path == "/api/input":
            c, d = _proxy("/brace/process", "POST", {"stimulus": payload.get("text", "")})
            self._json(c, d)
            return
        if self.path == "/api/load_scenario":
            c, d = _proxy("/brace/load-scenario", "POST", {"scenario": payload.get("scenario", "")})
            self._json(c, d)
            return
        self._json(404, {"error": "Not found"})


HTML = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>BRACE — Investor Experience</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --cream:   #F5EDD9;
  --ivory:   #FAF6EF;
  --gold:    #C9A84C;
  --gold2:   #E8C97A;
  --gold3:   #F0D98B;
  --walnut:  #2A1F14;
  --deep:    #180E07;
  --mocha:   #3D2B1F;
  --glass:   rgba(26, 16, 8, 0.58);
  --border:  rgba(201, 168, 76, 0.30);
}

html, body {
  width: 100%; height: 100%;
  overflow: hidden;
  background: var(--deep);
}

canvas#scene {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  z-index: 0;
}

#app {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 22px 18px 18px;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: rgba(201,168,76,.22) transparent;
}

/* ── HERO ── */
.hero {
  text-align: center;
  margin-bottom: 18px;
  flex-shrink: 0;
}
.logo {
  font-family: "Optima", "Palatino Linotype", "Palatino", Georgia, serif;
  font-size: clamp(2.2rem, 4.5vw, 3.6rem);
  font-weight: 300;
  letter-spacing: 0.38em;
  color: var(--gold2);
  text-shadow:
    0 0 60px rgba(232, 201, 122, 0.55),
    0 0 20px rgba(201, 168, 76, 0.40),
    0 2px 6px rgba(0,0,0,.6);
}
.tagline {
  margin-top: 7px;
  font-family: "Optima", Georgia, serif;
  font-size: clamp(.72rem, 1.3vw, .92rem);
  letter-spacing: .22em;
  font-weight: 300;
  color: rgba(245, 237, 217, .55);
  text-transform: uppercase;
}
.divider {
  width: 96px;
  height: 1px;
  margin: 13px auto 0;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  box-shadow: 0 0 10px rgba(201,168,76,.4);
}

/* ── GRID ── */
.layout {
  display: grid;
  grid-template-columns: 268px 1fr;
  gap: 14px;
  width: 100%;
  max-width: 1240px;
  flex: 1;
  min-height: 0;
}

/* ── GLASS CARD ── */
.card {
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 18px;
  backdrop-filter: blur(18px) saturate(150%);
  box-shadow:
    inset 0 1px 0 rgba(201,168,76,.10),
    0 30px 60px rgba(0,0,0,.48),
    0 0 0 .5px rgba(201,168,76,.12);
}

.card h2 {
  font-family: "Optima", Georgia, serif;
  font-size: .72rem;
  letter-spacing: .22em;
  text-transform: uppercase;
  font-weight: 400;
  color: var(--gold);
  margin-bottom: 16px;
}

/* ── SIDEBAR ── */
.sidebar { display: flex; flex-direction: column; gap: 13px; overflow: hidden; }

.m-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 4px;
}
.m-label {
  font-size: .8rem;
  color: rgba(245,237,217,.44);
  letter-spacing: .06em;
  font-family: "Optima", Georgia, serif;
  font-weight: 300;
}
.m-val {
  font-size: .98rem;
  font-weight: 500;
  color: var(--gold2);
  min-width: 38px;
  text-align: right;
  letter-spacing: .04em;
}
.bar {
  height: 2px;
  border-radius: 999px;
  background: rgba(201,168,76,.10);
  margin-bottom: 11px;
  overflow: hidden;
}
.bar span {
  display: block; height: 100%; width: 0%;
  border-radius: inherit;
  background: linear-gradient(90deg, #7B5A14, #C9A84C 45%, #F0D98B);
  box-shadow: 0 0 8px rgba(201,168,76,.45);
  transition: width .45s cubic-bezier(.4,0,.2,1);
}
.heartbeat {
  font-size: .72rem;
  color: rgba(201,168,76,.45);
  letter-spacing: .08em;
  margin-top: 4px;
  font-family: "Optima", Georgia, serif;
}

select {
  width: 100%;
  background: rgba(14, 9, 4, .72);
  border: 1px solid var(--border);
  border-radius: 9px;
  color: var(--cream);
  padding: 9px 10px;
  font-size: .85rem;
  font-family: "Optima", Georgia, serif;
  letter-spacing: .04em;
  margin-bottom: 10px;
  cursor: pointer;
  appearance: none;
  outline: none;
}
select:focus { border-color: rgba(201,168,76,.6); }
select option { background: #1a0f08; }

.btn {
  display: block;
  width: 100%;
  border: 1px solid rgba(201,168,76,.48);
  border-radius: 9px;
  padding: 9px 14px;
  color: var(--deep);
  font-weight: 700;
  font-size: .82rem;
  cursor: pointer;
  font-family: "Optima", Georgia, serif;
  letter-spacing: .14em;
  text-transform: uppercase;
  background: linear-gradient(135deg, #A8842C, #C9A84C 48%, #E0BE76);
  box-shadow: 0 4px 18px rgba(201,168,76,.22), 0 0 0 .5px rgba(201,168,76,.45);
  transition: filter .2s, transform .15s;
}
.btn:hover { filter: brightness(1.12); transform: translateY(-1px); }

/* ── CHAT PANEL ── */
.chat-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  max-height: calc(100vh - 140px);
}

.chat-log {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 4px 2px 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scrollbar-width: thin;
  scrollbar-color: rgba(201,168,76,.18) transparent;
}

.bubble {
  max-width: 84%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: .88rem;
  line-height: 1.48;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: "Optima", Georgia, serif;
  letter-spacing: .012em;
}
.bubble.user {
  align-self: flex-end;
  background: rgba(201,168,76,.16);
  border: 1px solid rgba(201,168,76,.38);
  color: var(--ivory);
}
.bubble.brace {
  align-self: flex-start;
  background: rgba(40, 26, 12, .72);
  border: 1px solid rgba(245,237,217,.10);
  color: rgba(245,237,217,.88);
}
.bubble.system {
  align-self: center;
  background: rgba(201,168,76,.05);
  border: 1px solid rgba(201,168,76,.15);
  color: rgba(201,168,76,.58);
  font-size: .76rem;
  text-align: center;
  max-width: 94%;
  letter-spacing: .06em;
}

.input-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: flex-end;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(201,168,76,.14);
  flex-shrink: 0;
}
textarea#input {
  background: rgba(10, 6, 2, .68);
  border: 1px solid var(--border);
  border-radius: 11px;
  color: var(--cream);
  padding: 11px 13px;
  font-size: .9rem;
  font-family: "Optima", Georgia, serif;
  min-height: 72px;
  resize: vertical;
  line-height: 1.45;
  letter-spacing: .025em;
  outline: none;
  transition: border-color .2s, box-shadow .2s;
  width: 100%;
}
textarea#input:focus {
  border-color: rgba(201,168,76,.65);
  box-shadow: 0 0 0 2.5px rgba(201,168,76,.09);
}
textarea#input::placeholder { color: rgba(245,237,217,.25); }

#send-btn {
  border: 1px solid rgba(201,168,76,.55);
  border-radius: 11px;
  padding: 13px 20px;
  background: linear-gradient(145deg, #8B6914, #C9A84C 52%, #DDB85C);
  color: var(--deep);
  font-weight: 800;
  font-size: .82rem;
  font-family: "Optima", Georgia, serif;
  cursor: pointer;
  letter-spacing: .14em;
  text-transform: uppercase;
  box-shadow: 0 6px 22px rgba(201,168,76,.28);
  transition: filter .2s, transform .15s;
  white-space: nowrap;
  align-self: stretch;
  display: flex;
  align-items: center;
  justify-content: center;
}
#send-btn:hover { filter: brightness(1.12); transform: translateY(-1px); }
#send-btn:disabled { opacity: .45; cursor: default; transform: none; }

/* ── RESPONSIVE ── */
@media (max-width: 820px) {
  .layout { grid-template-columns: 1fr; }
  html, body, #app { overflow-y: auto; height: auto; }
  canvas#scene { position: fixed; }
  .chat-panel { max-height: 55vh; }
}
</style>
</head>
<body>
<canvas id="scene"></canvas>
<div id="app">
  <div class="hero">
    <div class="logo">B &nbsp; R &nbsp; A &nbsp; C &nbsp; E</div>
    <div class="tagline">Behavioral Relational AI Conversational Engine &nbsp;&#183;&nbsp; v3.0</div>
    <div class="divider"></div>
  </div>

  <div class="layout">
    <!-- Sidebar -->
    <div class="sidebar">
      <div class="card">
        <h2>Live Intelligence</h2>
        <div class="m-row"><span class="m-label">Relational Phase</span><span class="m-val" id="phase">1</span></div>
        <div class="bar"><span id="phase-fill"></span></div>
        <div class="m-row"><span class="m-label">Trust Score</span><span class="m-val" id="trust">50.0</span></div>
        <div class="bar"><span id="trust-fill"></span></div>
        <div class="m-row"><span class="m-label">IAI Index</span><span class="m-val" id="iai">0.10</span></div>
        <div class="bar"><span id="iai-fill"></span></div>
        <div class="m-row"><span class="m-label">Messages</span><span class="m-val" id="history">0</span></div>
        <div class="bar"><span id="history-fill"></span></div>
        <div class="heartbeat" id="heartbeat">&#9679; waiting first signal&hellip;</div>
      </div>

      <div class="card">
        <h2>Scenario</h2>
        <select id="scenario-select"><option value="">Free conversation</option></select>
        <button class="btn" onclick="loadScenario()">Activate</button>
      </div>
    </div>

    <!-- Chat panel -->
    <div class="card chat-panel">
      <h2>Conversation</h2>
      <div class="chat-log" id="chat-log"></div>
      <div class="input-row">
        <textarea id="input" placeholder="Scrivi qui il messaggio per testare la relational intelligence di BRACE&#8230;"></textarea>
        <button id="send-btn" onclick="processInput()">Send</button>
      </div>
    </div>
  </div>
</div>

<script>
(function () {
  'use strict';

  /* =========================================================
     3D LUXURY HOTEL LOBBY — Canvas 2D Pure JS
     Marble floor · God rays · Chandelier · Columns · Bokeh · Gold dust
  ========================================================= */
  const CVS = document.getElementById('scene');
  const CTX = CVS.getContext('2d');
  let W = 0, H = 0, CX = 0, CY = 0;
  let t = 0;
  let mx = 0.5, my = 0.5;

  function resize() {
    W = CVS.width  = window.innerWidth;
    H = CVS.height = window.innerHeight;
    CX = W / 2; CY = H / 2;
  }
  window.addEventListener('resize', resize);
  resize();
  window.addEventListener('mousemove', e => { mx = e.clientX / W; my = e.clientY / H; });

  /* --- Particles (gold dust) --- */
  const P = Array.from({length: 130}, () => ({
    x: Math.random() * 1.3 - 0.15,
    y: Math.random(),
    vy: -(0.00011 + Math.random() * 0.00024),
    vx: (Math.random() - .5) * 0.00005,
    r:  .5 + Math.random() * 1.9,
    z:  .15 + Math.random() * .85,
    a:  .08 + Math.random() * .42,
    h:  36 + Math.random() * 22,
  }));

  /* --- Bokeh orbs (chandeliers / ambient) --- */
  const B = Array.from({length: 32}, () => ({
    x: Math.random(),
    y: .04 + Math.random() * .58,
    r: 18 + Math.random() * 88,
    a: .04 + Math.random() * .13,
    s: .00014 + Math.random() * .00028,
    p: Math.random() * Math.PI * 2,
    w: Math.random() > .38,
  }));

  /* --- Main draw loop --- */
  function draw(ts) {
    t = ts * .001;
    CTX.clearRect(0, 0, W, H);

    /* 1 · SKY GRADIENT — warm amber ceiling */
    const sky = CTX.createLinearGradient(0, 0, 0, H * .62);
    sky.addColorStop(0,   '#160A03');
    sky.addColorStop(.22, '#221106');
    sky.addColorStop(.5,  '#3A1D08');
    sky.addColorStop(1,   '#5A2E0C');
    CTX.fillStyle = sky;
    CTX.fillRect(0, 0, W, H * .62);

    /* 2 · FLOOR GRADIENT — polished marble */
    const fl = CTX.createLinearGradient(0, H * .62, 0, H);
    fl.addColorStop(0,  '#4A2C10');
    fl.addColorStop(.4, '#2E1A09');
    fl.addColorStop(1,  '#120804');
    CTX.fillStyle = fl;
    CTX.fillRect(0, H * .62, W, H * .38);

    /* 3 · HORIZON GLOW */
    const hg = CTX.createRadialGradient(CX, H * .60, 0, CX, H * .60, W * .52);
    hg.addColorStop(0,   'rgba(220,160,70,.28)');
    hg.addColorStop(.42, 'rgba(170,110,40,.10)');
    hg.addColorStop(1,   'rgba(0,0,0,0)');
    CTX.fillStyle = hg;
    CTX.fillRect(0, H * .30, W, H * .52);

    /* 4 · GOD RAYS */
    CTX.save();
    for (let i = 0; i < 8; i++) {
      const ang  = -.42 + (i / 7) * .84;
      const pulse = .5 + .5 * Math.sin(t * .24 + i * 1.15);
      const alp  = (.016 + .012 * pulse) * (1 - Math.abs(ang) * .7);
      const sw   = W * .42 + W * .32 * pulse;
      const sh   = H * 1.15;
      const sx   = CX + Math.sin(ang) * W * .09;
      const rg   = CTX.createLinearGradient(sx, 0, sx + Math.sin(ang) * sh, sh);
      rg.addColorStop(0,   `rgba(245,195,110,${alp * 1.5})`);
      rg.addColorStop(.5,  `rgba(195,148,68,${alp})`);
      rg.addColorStop(1,   'rgba(0,0,0,0)');
      CTX.beginPath();
      CTX.moveTo(sx - 2, 0);
      CTX.lineTo(sx + 2, 0);
      CTX.lineTo(sx + Math.sin(ang) * sh + sw * .5, sh);
      CTX.lineTo(sx + Math.sin(ang) * sh - sw * .5, sh);
      CTX.closePath();
      CTX.fillStyle = rg;
      CTX.fill();
    }
    CTX.restore();

    /* 5 · MARBLE FLOOR PERSPECTIVE GRID */
    const vpY = H * .605;
    const vpX = CX + (mx - .5) * W * .07;
    CTX.save();
    /* longitudinal lines */
    for (let i = -8; i <= 8; i++) {
      const bx = CX + i * W * .082;
      const a  = .06 + .05 * (1 - Math.abs(i) / 9);
      CTX.beginPath();
      CTX.moveTo(vpX, vpY);
      CTX.lineTo(bx, H + 8);
      CTX.strokeStyle = `rgba(201,168,76,${a})`;
      CTX.lineWidth = .7;
      CTX.stroke();
    }
    /* transversal depth lines */
    for (let d = 0; d < 11; d++) {
      const frac = d / 10;
      const y = vpY + (H - vpY) * Math.pow(frac, .48);
      const sp = (y - vpY) / (H - vpY + 1);
      const lx = vpX - sp * W * .72;
      const rx = vpX + sp * W * .72;
      CTX.beginPath();
      CTX.moveTo(lx, y);
      CTX.lineTo(rx, y);
      CTX.strokeStyle = `rgba(201,168,76,${.035 + .055 * sp})`;
      CTX.lineWidth = .65;
      CTX.stroke();
    }
    CTX.restore();

    /* 6 · MARBLE FLOOR SHEEN */
    CTX.save();
    const sh = CTX.createLinearGradient(CX - W * .28, H * .65, CX + W * .28, H * .76);
    sh.addColorStop(0,   'rgba(0,0,0,0)');
    sh.addColorStop(.4,  `rgba(230,192,120,${.06 + .04 * Math.sin(t * .32)})`);
    sh.addColorStop(.5,  `rgba(255,238,172,${.14 + .06 * Math.sin(t * .32)})`);
    sh.addColorStop(.6,  `rgba(230,192,120,${.06 + .04 * Math.sin(t * .32)})`);
    sh.addColorStop(1,   'rgba(0,0,0,0)');
    CTX.fillStyle = sh;
    CTX.fillRect(0, H * .62, W, H * .38);
    CTX.restore();

    /* 7 · COLUMNS */
    drawColumns(vpX, vpY);

    /* 8 · CHANDELIER */
    drawChandelier(CX, H * .055, t);

    /* 9 · BOKEH ORBS */
    CTX.save();
    for (const b of B) {
      const bx  = b.x * W + Math.sin(t * b.s * 1900 + b.p) * W * .014;
      const by  = b.y * H + Math.cos(t * b.s * 950  + b.p) * H * .009;
      const pls = .7 + .3 * Math.sin(t * b.s * 3200 + b.p);
      const rr  = b.r * pls;
      const bg  = CTX.createRadialGradient(bx, by, 0, bx, by, rr);
      if (b.w) {
        bg.addColorStop(0,   `rgba(242,186,82,${b.a * pls})`);
        bg.addColorStop(.55, `rgba(195,135,52,${b.a * .45 * pls})`);
        bg.addColorStop(1,   'rgba(0,0,0,0)');
      } else {
        bg.addColorStop(0,   `rgba(255,245,210,${b.a * .7 * pls})`);
        bg.addColorStop(.55, `rgba(210,178,118,${b.a * .28 * pls})`);
        bg.addColorStop(1,   'rgba(0,0,0,0)');
      }
      CTX.fillStyle = bg;
      CTX.beginPath();
      CTX.ellipse(bx, by, rr, rr * .88, 0, 0, Math.PI * 2);
      CTX.fill();
    }
    CTX.restore();

    /* 10 · GOLD DUST */
    CTX.save();
    for (const p of P) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.y < -.06) { p.y = 1.06; p.x = Math.random() * 1.3 - .15; }
      const alpha = p.a * (.5 + .5 * Math.abs(Math.sin(t * .38 + p.x * 12)));
      CTX.globalAlpha = alpha;
      CTX.fillStyle = `hsl(${p.h},72%,68%)`;
      CTX.beginPath();
      CTX.arc(p.x * W, p.y * H, p.r * p.z, 0, Math.PI * 2);
      CTX.fill();
    }
    CTX.restore();

    /* 11 · VIGNETTE */
    const vig = CTX.createRadialGradient(CX, CY, H * .28, CX, CY, H * .88);
    vig.addColorStop(0, 'rgba(0,0,0,0)');
    vig.addColorStop(1, 'rgba(8,3,1,.65)');
    CTX.fillStyle = vig;
    CTX.fillRect(0, 0, W, H);

    requestAnimationFrame(draw);
  }

  function drawColumns(vpxc, vpyc) {
    CTX.save();
    const SLOTS = [[.06, .90], [.17, .78], [.30, .66]];
    for (const side of [-1, 1]) {
      for (const [bn, gn] of SLOTS) {
        const baseX = side < 0 ? bn * W : W - bn * W;
        const gx    = side < 0 ? gn * W : W - gn * W;
        const topX  = vpxc + (baseX - vpxc) * .20;
        const topY  = vpyc - H * .44 * (1 - bn * 1.1);
        const botY  = H + 24;
        const cw    = (H - vpyc) * bn * .13;
        const cg    = CTX.createLinearGradient(baseX - cw, 0, baseX + cw, 0);
        if (side < 0) {
          cg.addColorStop(0,   'rgba(20,10,3,0)');
          cg.addColorStop(.18, 'rgba(85,50,18,.62)');
          cg.addColorStop(.58, 'rgba(140,104,48,.52)');
          cg.addColorStop(.84, 'rgba(72,44,14,.70)');
          cg.addColorStop(1,   'rgba(6,3,1,.85)');
        } else {
          cg.addColorStop(0,   'rgba(6,3,1,.85)');
          cg.addColorStop(.16, 'rgba(72,44,14,.70)');
          cg.addColorStop(.42, 'rgba(140,104,48,.52)');
          cg.addColorStop(.82, 'rgba(85,50,18,.62)');
          cg.addColorStop(1,   'rgba(20,10,3,0)');
        }
        CTX.beginPath();
        CTX.moveTo(topX - cw * .38, topY);
        CTX.lineTo(topX + cw * .38, topY);
        CTX.lineTo(gx   + cw,       botY);
        CTX.lineTo(gx   - cw,       botY);
        CTX.closePath();
        CTX.fillStyle = cg;
        CTX.fill();
        /* edge highlight */
        const ex = side < 0 ? gx + cw * .5 : gx - cw * .5;
        CTX.beginPath();
        CTX.moveTo(topX, topY);
        CTX.lineTo(ex, botY);
        CTX.strokeStyle = `rgba(201,168,76,${.08 - bn * .06})`;
        CTX.lineWidth = .7;
        CTX.stroke();
      }
    }
    CTX.restore();
  }

  function drawChandelier(x, y, ts) {
    CTX.save();
    const pulse = .5 + .5 * Math.sin(ts * .45);
    const R = 88 + 14 * pulse;

    /* outer glow */
    const og = CTX.createRadialGradient(x, y, 0, x, y, R);
    og.addColorStop(0,   `rgba(255,242,185,${.58 + .14 * pulse})`);
    og.addColorStop(.28, `rgba(232,184,92,${.32 + .10 * pulse})`);
    og.addColorStop(.65, `rgba(176,124,52,.10)`);
    og.addColorStop(1,   'rgba(0,0,0,0)');
    CTX.fillStyle = og;
    CTX.beginPath();
    CTX.ellipse(x, y, R, R * .68, 0, 0, Math.PI * 2);
    CTX.fill();

    /* arms */
    const ARMS = 14;
    for (let i = 0; i < ARMS; i++) {
      const a  = (i / ARMS) * Math.PI * 2 + ts * .038;
      const r1 = 12 + 3 * Math.sin(ts * .85 + i);
      const r2 = 42 + 8 * Math.sin(ts * .52 + i * .78);
      CTX.beginPath();
      CTX.moveTo(x + Math.cos(a) * r1, y + Math.sin(a) * r1 * .52);
      CTX.lineTo(x + Math.cos(a) * r2, y + Math.sin(a) * r2 * .48);
      CTX.strokeStyle = `rgba(240,200,125,${.48 + .18 * pulse})`;
      CTX.lineWidth = 1.1;
      CTX.stroke();
      /* crystal tip */
      const ta  = .48 + .52 * Math.sin(ts * 1.25 + i * .88);
      CTX.globalAlpha = ta;
      CTX.fillStyle = '#FFE9A8';
      CTX.beginPath();
      CTX.arc(x + Math.cos(a) * r2, y + Math.sin(a) * r2 * .48, 2.2, 0, Math.PI * 2);
      CTX.fill();
      CTX.globalAlpha = 1;
    }

    /* center jewel */
    const jg = CTX.createRadialGradient(x, y, 0, x, y, 11);
    jg.addColorStop(0,   'rgba(255,255,225,.96)');
    jg.addColorStop(.5,  'rgba(242,198,108,.76)');
    jg.addColorStop(1,   'rgba(0,0,0,0)');
    CTX.fillStyle = jg;
    CTX.beginPath();
    CTX.arc(x, y, 11, 0, Math.PI * 2);
    CTX.fill();
    CTX.restore();
  }

  requestAnimationFrame(draw);

  /* =========================================================
     BRACE API + CHAT
  ========================================================= */
  async function updateState() {
    try {
      const r = await fetch('/api/state');
      const j = await r.json();
      const s = j.state || j;
      const phase = Number(s.phase || 1);
      const trust = Number(s.trust_score || 50);
      const iai   = Number(s.iai_score || .1);
      const hist  = Number(s.history_length || 0);
      document.getElementById('phase').textContent   = phase;
      document.getElementById('trust').textContent   = trust.toFixed(1);
      document.getElementById('iai').textContent     = iai.toFixed(3);
      document.getElementById('history').textContent = hist;
      document.getElementById('phase-fill').style.width   = Math.min(100, (phase / 6) * 100) + '%';
      document.getElementById('trust-fill').style.width   = Math.min(100, trust) + '%';
      document.getElementById('iai-fill').style.width     = Math.min(100, iai * 100) + '%';
      document.getElementById('history-fill').style.width = Math.min(100, hist * 5) + '%';
      document.getElementById('heartbeat').textContent =
        '\u25CF  phase ' + phase + '  \u00B7  trust ' + trust.toFixed(1) + '  \u00B7  IAI ' + iai.toFixed(3);
    } catch (_) {}
  }

  async function loadScenarios() {
    try {
      const r = await fetch('/api/scenarios');
      const d = await r.json();
      const list = d.scenarios || [];
      const sel  = document.getElementById('scenario-select');
      list.forEach(s => {
        const o = document.createElement('option');
        o.value = s; o.textContent = s; sel.appendChild(o);
      });
    } catch (_) {}
  }

  function appendBubble(role, text) {
    const log = document.getElementById('chat-log');
    const b   = document.createElement('div');
    b.className = 'bubble ' + role;
    b.textContent = text;
    log.appendChild(b);
    log.scrollTop = log.scrollHeight;
  }

  async function processInput() {
    const inp  = document.getElementById('input');
    const text = inp.value.trim();
    if (!text) return;
    appendBubble('user', text);
    const btn = document.getElementById('send-btn');
    btn.disabled = true;
    inp.value = '';
    try {
      const r   = await fetch('/api/input', {
        method:  'POST',
        headers: {'Content-Type': 'application/json'},
        body:    JSON.stringify({text}),
      });
      const j   = await r.json();
      const res = j.result || j;
      const mode  = res.mode || res.pil_mode || 'standard';
      const trust = Number(res.trust || 0).toFixed(1);
      const iai   = Number(res.iai || 0).toFixed(3);
      const rec   = (res.recommendation || res.prevention || '').toString();
      appendBubble('brace',
        'Mode: ' + mode + '  \u00B7  Trust: ' + trust + '  \u00B7  IAI: ' + iai + '\n' + rec);
      updateState();
    } catch (_) {
      appendBubble('brace', 'Connection error \u2014 check BRACE backend on port 4000.');
    } finally {
      btn.disabled = false;
    }
  }

  async function loadScenario() {
    const sc = document.getElementById('scenario-select').value;
    if (!sc) return;
    try {
      await fetch('/api/load_scenario', {
        method:  'POST',
        headers: {'Content-Type': 'application/json'},
        body:    JSON.stringify({scenario: sc}),
      });
      appendBubble('system', '\u29AC  Scenario attivato: ' + sc);
    } catch (_) {}
  }

  window.loadScenario  = loadScenario;
  window.processInput  = processInput;

  document.addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.target.id === 'input' && !e.shiftKey) {
      e.preventDefault();
      processInput();
    }
  });

  loadScenarios();
  appendBubble('system',
    '\u29AC  BRACE relational engine ready  \u00B7  ' + new Date().toLocaleTimeString('it-IT'));
  setInterval(updateState, 1100);
})();
</script>
</body>
</html>"""


if __name__ == '__main__':
    with ReusableTCPServer((HOST, PORT), Handler) as httpd:
        if USE_TLS:
            if not ensure_cert():
                raise SystemExit(1)
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(str(CERT_FILE), str(KEY_FILE))
            httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
            print(f"BRACE Luxury Demo: https://{HOST}:{PORT}")
        else:
            print(f"BRACE Luxury Demo: http://{HOST}:{PORT}")
        httpd.serve_forever()
