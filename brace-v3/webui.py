#!/usr/bin/env python3
"""GIU-L_IA Web UI — Immersive 3D Relational AI.

AAA-grade immersive demo: realistic 3D video environment with
WebGL particle systems, parallax depth, interactive canvas overlay,
glassmorphism chat with Ollama AI responses contextualised to the
3D scene, local GIU-L_IA engine integration.
Port 9443 (HTTP).
"""

from __future__ import annotations

import json
import socketserver
import sys
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from brace_v3 import GIU_L_IA  # noqa: E402
from scenarios_db import get_scenario, get_scenario_names  # noqa: E402

PORT = 9443
ASSETS_DIR = _HERE / "assets"
ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".mp4",
    ".webm",
    ".mov",
    ".m4v",
}

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "orca-mini"
OLLAMA_TIMEOUT = 30
ENGINE_NAME = "GIU-L_IA"
DEFAULT_VIDEO_ASSET = "progetto_giulia.m4v"
VIDEO_SCENE_CONTEXT = (
  "Scenario attivo: lobby premium 5 stelle ultra-realistica. "
  "Pavimento in marmo lucido con riflessi dorati, lampadari di cristallo "
  "che proiettano raggi di luce volumetrica calda attraverso la stanza. "
  "Particelle di polvere dorate fluttuano nell'aria come in un sogno. "
  "Nebbia volumetrica leggera avvolge i bordi della scena. "
  "Lucciole luminose reagiscono ai movimenti, creando un'atmosfera "
  "magica e protetta. L'ambiente si inclina e respira seguendo lo "
  "sguardo dell'utente con parallasse 3D multi-livello. "
  "Le risposte devono essere immersive: descrivere sensazioni visive, "
  "tattili e atmosferiche coerenti con questa scena. Tono calmo, "
  "avvolgente, concreto e protettivo come una guida in un luogo sacro."
)

# ---------------------------------------------------------------------------
# Global GIU-L_IA engine instance
# ---------------------------------------------------------------------------
_engine = GIU_L_IA()
_chat_history: list[dict] = []


def _ollama_chat(user_text: str, engine_system_prompt: str, risk_level: str) -> str:
    """Call Ollama /api/chat and return assistant reply (non-streaming)."""
    parsed = urlparse(OLLAMA_URL)
    if parsed.scheme not in ("http", "https"):
        return "[Errore: schema URL non permesso]"
    system_msg = (
        f"{engine_system_prompt}\n"
        f"{VIDEO_SCENE_CONTEXT}\n"
        f"Livello rischio rilevato: {risk_level}. "
        "Rispondi in italiano, in modo empatico, immersivo e protettivo. "
        "Integra riferimenti all'ambiente 3D attivo nella risposta. "
        "Se il rischio e' alto, suggerisci risorse di aiuto."
    )
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_text},
        ],
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310 — URL scheme validated above
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:  # noqa: S310
            body = json.loads(resp.read())
            return body.get("message", {}).get("content", "")
    except urllib.error.URLError as exc:
        return f"[Ollama non raggiungibile: {exc.reason}]"
    except Exception as exc:  # noqa: BLE001
        return f"[Ollama errore: {exc}]"


# ===================================================================
# HTML PAGE — built as concatenation to avoid heredoc issues
# ===================================================================
_CSS = """*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;font-family:'SF Pro Display',system-ui,-apple-system,sans-serif;color:#f0ead6}
body{background:#0a0a0f}
#bg-photo{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;filter:brightness(0.55) saturate(1.1)}
#canvas-overlay{position:fixed;inset:0;z-index:1;pointer-events:none;mix-blend-mode:screen}
#onboarding{position:fixed;inset:0;z-index:100;display:flex;align-items:center;justify-content:center;background:rgba(5,5,12,0.92);backdrop-filter:blur(24px);transition:opacity .6s ease}
#onboarding.hidden{opacity:0;pointer-events:none}
.ob-container{max-width:680px;width:90%;text-align:center}
.ob-step{display:none}.ob-step.active{display:block;animation:fadeUp .7s ease}
.ob-logo{font-size:4rem;font-weight:900;background:linear-gradient(135deg,#c9a84c,#f5dfa0,#c9a84c);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px;animation:shimmer 3s ease infinite}
.ob-ring{width:120px;height:120px;border-radius:50%;border:3px solid rgba(201,168,76,0.4);margin:24px auto;animation:breathe 3s ease infinite;position:relative}
.ob-ring::after{content:'\\1F6E1';font-size:48px;position:absolute;inset:0;display:flex;align-items:center;justify-content:center}
.ob-tagline{font-size:1.1rem;color:rgba(240,234,214,0.7);margin-top:16px;animation:fadeIn 2s ease .5s both}
.ob-title{font-size:2.2rem;font-weight:800;color:#c9a84c;margin-bottom:20px}
.ob-subtitle{font-size:1rem;color:rgba(240,234,214,0.7);margin-bottom:32px;line-height:1.6}
.feature-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:28px}
.feature-card{background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.2);border-radius:16px;padding:20px;text-align:left;transition:transform .2s,border-color .2s}
.feature-card:hover{transform:translateY(-4px);border-color:rgba(201,168,76,0.5)}
.feature-card .icon{font-size:28px;margin-bottom:8px}
.feature-card h4{font-size:1rem;color:#f5dfa0;margin-bottom:4px}
.feature-card p{font-size:.82rem;color:rgba(240,234,214,0.5);line-height:1.4}
.level-row{display:flex;gap:16px;margin-bottom:16px;align-items:center;text-align:left}
.level-badge{width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1.2rem;flex-shrink:0}
.level-badge.l1{background:rgba(76,175,80,0.2);color:#66bb6a;border:2px solid rgba(76,175,80,0.4)}
.level-badge.l2{background:rgba(255,167,38,0.2);color:#ffa726;border:2px solid rgba(255,167,38,0.4)}
.level-badge.l3{background:rgba(239,83,80,0.2);color:#ef5350;border:2px solid rgba(239,83,80,0.4)}
.level-info h4{color:#f5dfa0;font-size:1rem;margin-bottom:4px}
.level-info p{color:rgba(240,234,214,0.5);font-size:.85rem;line-height:1.4}
.demo-chips{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin:24px 0}
.demo-chip{background:rgba(201,168,76,0.12);border:1px solid rgba(201,168,76,0.3);border-radius:24px;padding:10px 20px;font-size:.9rem;color:#f5dfa0;cursor:pointer;transition:all .2s}
.demo-chip:hover{background:rgba(201,168,76,0.25);transform:scale(1.06)}
.demo-result{background:rgba(10,10,15,0.6);border:1px solid rgba(201,168,76,0.15);border-radius:12px;padding:16px;margin-top:16px;text-align:left;min-height:60px;font-size:.85rem;color:rgba(240,234,214,0.8);line-height:1.5;display:none}
.ob-btn{display:inline-block;padding:14px 36px;border:none;border-radius:12px;font-size:1rem;font-weight:700;cursor:pointer;transition:all .25s;margin-top:16px}
.ob-btn-primary{background:linear-gradient(135deg,#c9a84c,#e6c870);color:#0a0a0f}
.ob-btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 32px rgba(201,168,76,0.3)}
.ob-btn-ghost{background:transparent;border:1px solid rgba(201,168,76,0.3);color:#c9a84c}
.ob-btn-ghost:hover{background:rgba(201,168,76,0.1)}
.ob-progress{display:flex;gap:8px;justify-content:center;margin-top:32px}
.ob-dot{width:10px;height:10px;border-radius:50%;background:rgba(201,168,76,0.2);transition:all .3s}
.ob-dot.active{background:#c9a84c;box-shadow:0 0 12px rgba(201,168,76,0.5);transform:scale(1.3)}
.ob-final-icon{font-size:72px;margin-bottom:16px;animation:scaleIn .8s ease}
#app{position:fixed;inset:0;z-index:10;display:none;opacity:0;transition:opacity .8s ease}
#app.visible{display:flex;opacity:1}
#sidebar{width:260px;height:100%;background:rgba(10,10,15,0.85);border-right:1px solid rgba(201,168,76,0.12);backdrop-filter:blur(16px);display:flex;flex-direction:column;padding:20px;z-index:11;flex-shrink:0}
.side-brand{display:flex;align-items:center;gap:10px;margin-bottom:24px}
.side-brand .shield{font-size:28px}
.side-brand h2{font-size:1.1rem;font-weight:800;color:#c9a84c}
.metric-card{background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.12);border-radius:12px;padding:14px;margin-bottom:12px}
.metric-card .label{font-size:.72rem;text-transform:uppercase;letter-spacing:1px;color:rgba(240,234,214,0.4);margin-bottom:4px}
.metric-card .value{font-size:1.6rem;font-weight:800;color:#f5dfa0}
.metric-card .bar{height:4px;border-radius:2px;background:rgba(201,168,76,0.15);margin-top:8px;overflow:hidden}
.metric-card .bar-fill{height:100%;border-radius:2px;transition:width .5s ease}
.bar-trust{background:linear-gradient(90deg,#66bb6a,#c9a84c)}
.bar-iai{background:linear-gradient(90deg,#42a5f5,#7e57c2)}
.scenario-list{margin-top:auto}
.scenario-list h4{font-size:.75rem;text-transform:uppercase;color:rgba(240,234,214,0.4);letter-spacing:1px;margin-bottom:8px}
.scenario-btn{display:block;width:100%;text-align:left;background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.1);border-radius:8px;padding:8px 12px;margin-bottom:6px;color:#f0ead6;font-size:.8rem;cursor:pointer;transition:all .2s}
.scenario-btn:hover{background:rgba(201,168,76,0.15);border-color:rgba(201,168,76,0.3)}
#chat-area{flex:1;display:flex;flex-direction:column;position:relative;z-index:11}
#chat-header{padding:16px 24px;background:rgba(10,10,15,0.6);backdrop-filter:blur(12px);border-bottom:1px solid rgba(201,168,76,0.1);display:flex;align-items:center;justify-content:space-between}
#chat-header h3{font-size:1rem;color:#c9a84c;font-weight:700}
.phase-badge{font-size:.75rem;padding:4px 14px;border-radius:20px;border:1px solid rgba(201,168,76,0.3);color:#f5dfa0;background:rgba(201,168,76,0.08)}
#messages{flex:1;overflow-y:auto;padding:24px;display:flex;flex-direction:column;gap:12px}
.msg{max-width:75%;padding:14px 18px;border-radius:16px;font-size:.9rem;line-height:1.5;animation:fadeUp .3s ease}
.msg.user{align-self:flex-end;background:rgba(201,168,76,0.12);border:1px solid rgba(201,168,76,0.2);border-bottom-right-radius:4px}
.msg.system{align-self:flex-start;background:rgba(66,165,245,0.08);border:1px solid rgba(66,165,245,0.15);border-bottom-left-radius:4px}
.msg.ai{align-self:flex-start;background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.15);border-bottom-left-radius:4px}
.msg .meta{font-size:.68rem;color:rgba(240,234,214,0.35);margin-top:6px}
.msg.risk-high{border-color:rgba(239,83,80,0.5);background:rgba(239,83,80,0.08)}
.msg.risk-moderate{border-color:rgba(255,167,38,0.4);background:rgba(255,167,38,0.06)}
#input-bar{padding:16px 24px;background:rgba(10,10,15,0.7);backdrop-filter:blur(12px);border-top:1px solid rgba(201,168,76,0.1);display:flex;gap:12px;align-items:flex-end}
#input-bar textarea{flex:1;background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.15);border-radius:12px;padding:12px 16px;color:#f0ead6;font-size:.9rem;font-family:inherit;resize:none;min-height:44px;max-height:128px;outline:none;transition:border-color .2s}
#input-bar textarea:focus{border-color:rgba(201,168,76,0.5)}
#input-bar textarea::placeholder{color:rgba(240,234,214,0.3)}
#send-btn{width:44px;height:44px;border-radius:12px;border:none;background:linear-gradient(135deg,#c9a84c,#e6c870);color:#0a0a0f;font-size:1.2rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:transform .15s,box-shadow .15s;flex-shrink:0}
#send-btn:hover{transform:scale(1.08);box-shadow:0 4px 16px rgba(201,168,76,0.3)}
#send-btn:active{transform:scale(0.95)}
#send-btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.welcome-badge{text-align:center;padding:48px 24px;animation:fadeIn 1s ease}
.welcome-badge .wb-icon{font-size:56px;margin-bottom:16px}
.welcome-badge h3{font-size:1.3rem;color:#c9a84c;margin-bottom:8px}
.welcome-badge p{font-size:.85rem;color:rgba(240,234,214,0.5);line-height:1.5}
#photo-switcher{position:fixed;bottom:20px;right:20px;z-index:20;display:flex;gap:8px}
.photo-thumb{width:48px;height:48px;border-radius:8px;overflow:hidden;cursor:pointer;border:2px solid transparent;opacity:.6;transition:all .2s}
.photo-thumb.active{border-color:#c9a84c;opacity:1}
.photo-thumb img{width:100%;height:100%;object-fit:cover}
.typing-dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:#c9a84c;animation:typingBounce .6s ease infinite;margin-right:3px}
.typing-dot:nth-child(2){animation-delay:.15s}
.typing-dot:nth-child(3){animation-delay:.3s}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(201,168,76,0.2);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:rgba(201,168,76,0.4)}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
@keyframes scaleIn{from{opacity:0;transform:scale(0.6)}to{opacity:1;transform:scale(1)}}
@keyframes shimmer{0%,100%{filter:brightness(1)}50%{filter:brightness(1.3)}}
@keyframes breathe{0%,100%{transform:scale(1);box-shadow:0 0 0 rgba(201,168,76,0)}50%{transform:scale(1.05);box-shadow:0 0 32px rgba(201,168,76,0.25)}}
@keyframes typingBounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
@media(max-width:768px){#sidebar{display:none}.feature-grid{grid-template-columns:1fr}.msg{max-width:90%}}"""


# ===================================================================
# HTML PAGE
# ===================================================================
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GIU-L_IA — AI Relational Safety</title>
<meta http-equiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self'; media-src 'self';">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;font-family:'SF Pro Display',system-ui,-apple-system,sans-serif;color:#f0ead6}
body{background:#0a0a0f}
#bg-scene{position:fixed;inset:0;z-index:0;overflow:hidden;transform-style:preserve-3d;perspective:1200px}
#bg-photo,#bg-video{position:absolute;inset:-3%;width:106%;height:106%;object-fit:cover;transition:transform .2s linear,opacity .6s ease;will-change:transform,opacity}
#bg-photo{z-index:0;filter:brightness(0.55) saturate(1.1)}
#bg-video{z-index:1;opacity:0;filter:brightness(0.58) saturate(1.15) contrast(1.05)}
body.video-ready #bg-video{opacity:.78}
body.video-ready #bg-photo{opacity:.3}
#canvas-overlay{position:fixed;inset:0;z-index:1;pointer-events:none;mix-blend-mode:screen}
#scene-pulse{position:fixed;inset:0;z-index:2;pointer-events:none;background:radial-gradient(ellipse at 50% 10%,rgba(245,223,160,0.04),transparent 70%);animation:scenePulse 6s ease-in-out infinite}
#onboarding{position:fixed;inset:0;z-index:100;display:flex;align-items:center;justify-content:center;background:rgba(5,5,12,0.92);backdrop-filter:blur(24px);transition:opacity .6s ease}
#onboarding.hidden{opacity:0;pointer-events:none}
.ob-container{max-width:680px;width:90%;text-align:center}
.ob-step{display:none}.ob-step.active{display:block;animation:fadeUp .7s ease}
.ob-logo{font-size:4rem;font-weight:900;background:linear-gradient(135deg,#c9a84c,#f5dfa0,#c9a84c);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px;animation:shimmer 3s ease infinite}
.ob-ring{width:120px;height:120px;border-radius:50%;border:3px solid rgba(201,168,76,0.4);margin:24px auto;animation:breathe 3s ease infinite;position:relative}
.ob-ring::after{content:'\1F6E1\FE0F';font-size:48px;position:absolute;inset:0;display:flex;align-items:center;justify-content:center}
.ob-tagline{font-size:1.1rem;color:rgba(240,234,214,0.7);margin-top:16px;animation:fadeIn 2s ease .5s both}
.ob-title{font-size:2.2rem;font-weight:800;color:#c9a84c;margin-bottom:20px}
.ob-subtitle{font-size:1rem;color:rgba(240,234,214,0.7);margin-bottom:32px;line-height:1.6}
.feature-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:28px}
.feature-card{background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.2);border-radius:16px;padding:20px;text-align:left;transition:transform .2s,border-color .2s}
.feature-card:hover{transform:translateY(-4px);border-color:rgba(201,168,76,0.5)}
.feature-card .icon{font-size:28px;margin-bottom:8px}
.feature-card h4{font-size:1rem;color:#f5dfa0;margin-bottom:4px}
.feature-card p{font-size:.82rem;color:rgba(240,234,214,0.5);line-height:1.4}
.level-row{display:flex;gap:16px;margin-bottom:16px;align-items:center;text-align:left}
.level-badge{width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1.2rem;flex-shrink:0}
.level-badge.l1{background:rgba(76,175,80,0.2);color:#66bb6a;border:2px solid rgba(76,175,80,0.4)}
.level-badge.l2{background:rgba(255,167,38,0.2);color:#ffa726;border:2px solid rgba(255,167,38,0.4)}
.level-badge.l3{background:rgba(239,83,80,0.2);color:#ef5350;border:2px solid rgba(239,83,80,0.4)}
.level-info h4{color:#f5dfa0;font-size:1rem;margin-bottom:4px}
.level-info p{color:rgba(240,234,214,0.5);font-size:.85rem;line-height:1.4}
.demo-chips{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin:24px 0}
.demo-chip{background:rgba(201,168,76,0.12);border:1px solid rgba(201,168,76,0.3);border-radius:24px;padding:10px 20px;font-size:.9rem;color:#f5dfa0;cursor:pointer;transition:all .2s}
.demo-chip:hover{background:rgba(201,168,76,0.25);transform:scale(1.06)}
.demo-result{background:rgba(10,10,15,0.6);border:1px solid rgba(201,168,76,0.15);border-radius:12px;padding:16px;margin-top:16px;text-align:left;min-height:60px;font-size:.85rem;color:rgba(240,234,214,0.8);line-height:1.5;display:none}
.ob-final-icon{font-size:72px;margin-bottom:16px;animation:scaleIn .8s ease}
.ob-btn{display:inline-block;padding:14px 36px;border:none;border-radius:12px;font-size:1rem;font-weight:700;cursor:pointer;transition:all .25s;margin-top:16px}
.ob-btn-primary{background:linear-gradient(135deg,#c9a84c,#e6c870);color:#0a0a0f}
.ob-btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 32px rgba(201,168,76,0.3)}
.ob-btn-ghost{background:transparent;border:1px solid rgba(201,168,76,0.3);color:#c9a84c}
.ob-btn-ghost:hover{background:rgba(201,168,76,0.1)}
.ob-progress{display:flex;gap:8px;justify-content:center;margin-top:32px}
.ob-dot{width:10px;height:10px;border-radius:50%;background:rgba(201,168,76,0.2);transition:all .3s}
.ob-dot.active{background:#c9a84c;box-shadow:0 0 12px rgba(201,168,76,0.5);transform:scale(1.3)}
#app{position:fixed;inset:0;z-index:10;display:none;opacity:0;transition:opacity .8s ease}
#app.visible{display:flex;opacity:1}
#sidebar{width:260px;height:100%;background:rgba(10,10,15,0.85);border-right:1px solid rgba(201,168,76,0.12);backdrop-filter:blur(16px);display:flex;flex-direction:column;padding:20px;z-index:11;flex-shrink:0}
.side-brand{display:flex;align-items:center;gap:10px;margin-bottom:24px}
.side-brand .shield{font-size:28px}
.side-brand h2{font-size:1.1rem;font-weight:800;color:#c9a84c}
.metric-card{background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.12);border-radius:12px;padding:14px;margin-bottom:12px}
.metric-card .label{font-size:.72rem;text-transform:uppercase;letter-spacing:1px;color:rgba(240,234,214,0.4);margin-bottom:4px}
.metric-card .value{font-size:1.6rem;font-weight:800;color:#f5dfa0}
.metric-card .bar{height:4px;border-radius:2px;background:rgba(201,168,76,0.15);margin-top:8px;overflow:hidden}
.metric-card .bar-fill{height:100%;border-radius:2px;transition:width .5s ease}
.bar-trust{background:linear-gradient(90deg,#66bb6a,#c9a84c)}
.bar-iai{background:linear-gradient(90deg,#42a5f5,#7e57c2)}
.scenario-list{margin-top:auto}
.scenario-list h4{font-size:.75rem;text-transform:uppercase;color:rgba(240,234,214,0.4);letter-spacing:1px;margin-bottom:8px}
.scenario-btn{display:block;width:100%;text-align:left;background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.1);border-radius:8px;padding:8px 12px;margin-bottom:6px;color:#f0ead6;font-size:.8rem;cursor:pointer;transition:all .2s}
.scenario-btn:hover{background:rgba(201,168,76,0.15);border-color:rgba(201,168,76,0.3)}
#chat-area{flex:1;display:flex;flex-direction:column;position:relative;z-index:11}
#chat-header{padding:16px 24px;background:rgba(10,10,15,0.6);backdrop-filter:blur(12px);border-bottom:1px solid rgba(201,168,76,0.1);display:flex;align-items:center;justify-content:space-between}
#chat-header h3{font-size:1rem;color:#c9a84c;font-weight:700}
.phase-badge{font-size:.75rem;padding:4px 14px;border-radius:20px;border:1px solid rgba(201,168,76,0.3);color:#f5dfa0;background:rgba(201,168,76,0.08)}
#messages{flex:1;overflow-y:auto;padding:24px;display:flex;flex-direction:column;gap:12px}
.msg{max-width:75%;padding:14px 18px;border-radius:16px;font-size:.9rem;line-height:1.5;animation:fadeUp .3s ease}
.msg.user{align-self:flex-end;background:rgba(201,168,76,0.12);border:1px solid rgba(201,168,76,0.2);border-bottom-right-radius:4px}
.msg.system{align-self:flex-start;background:rgba(66,165,245,0.08);border:1px solid rgba(66,165,245,0.15);border-bottom-left-radius:4px}
.msg.ai{align-self:flex-start;background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.15);border-bottom-left-radius:4px}
.msg .meta{font-size:.68rem;color:rgba(240,234,214,0.35);margin-top:6px}
.msg.risk-high{border-color:rgba(239,83,80,0.5);background:rgba(239,83,80,0.08)}
.msg.risk-moderate{border-color:rgba(255,167,38,0.4);background:rgba(255,167,38,0.06)}
#input-bar{padding:16px 24px;background:rgba(10,10,15,0.7);backdrop-filter:blur(12px);border-top:1px solid rgba(201,168,76,0.1);display:flex;gap:12px;align-items:flex-end}
#input-bar textarea{flex:1;background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.15);border-radius:12px;padding:12px 16px;color:#f0ead6;font-size:.9rem;font-family:inherit;resize:none;min-height:44px;max-height:128px;outline:none;transition:border-color .2s}
#input-bar textarea:focus{border-color:rgba(201,168,76,0.5)}
#input-bar textarea::placeholder{color:rgba(240,234,214,0.3)}
#send-btn{width:44px;height:44px;border-radius:12px;border:none;background:linear-gradient(135deg,#c9a84c,#e6c870);color:#0a0a0f;font-size:1.2rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:transform .15s,box-shadow .15s;flex-shrink:0}
#send-btn:hover{transform:scale(1.08);box-shadow:0 4px 16px rgba(201,168,76,0.3)}
#send-btn:active{transform:scale(0.95)}
#send-btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.welcome-badge{text-align:center;padding:48px 24px;animation:fadeIn 1s ease}
.welcome-badge .wb-icon{font-size:56px;margin-bottom:16px}
.welcome-badge h3{font-size:1.3rem;color:#c9a84c;margin-bottom:8px}
.welcome-badge p{font-size:.85rem;color:rgba(240,234,214,0.5);line-height:1.5}
#photo-switcher{position:fixed;bottom:20px;right:20px;z-index:20;display:flex;gap:8px}
.photo-thumb{width:48px;height:48px;border-radius:8px;overflow:hidden;cursor:pointer;border:2px solid transparent;opacity:.6;transition:all .2s}
.photo-thumb.active{border-color:#c9a84c;opacity:1}
.photo-thumb img{width:100%;height:100%;object-fit:cover}
.media-chip{width:auto;min-width:62px;padding:0 10px;height:48px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:.72rem;font-weight:700;letter-spacing:.7px;color:#f5dfa0;background:rgba(10,10,15,0.72);border:2px solid rgba(201,168,76,0.25);cursor:pointer;opacity:.7;transition:all .2s}
.media-chip.active{opacity:1;border-color:#c9a84c;box-shadow:0 0 14px rgba(201,168,76,0.25)}
.typing-dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:#c9a84c;animation:typingBounce .6s ease infinite;margin-right:3px}
.typing-dot:nth-child(2){animation-delay:.15s}
.typing-dot:nth-child(3){animation-delay:.3s}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(201,168,76,0.2);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:rgba(201,168,76,0.4)}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
@keyframes scaleIn{from{opacity:0;transform:scale(0.6)}to{opacity:1;transform:scale(1)}}
@keyframes shimmer{0%,100%{filter:brightness(1)}50%{filter:brightness(1.3)}}
@keyframes breathe{0%,100%{transform:scale(1);box-shadow:0 0 0 rgba(201,168,76,0)}50%{transform:scale(1.05);box-shadow:0 0 32px rgba(201,168,76,0.25)}}
@keyframes typingBounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
@keyframes scenePulse{0%,100%{opacity:0.6}50%{opacity:1}}
@keyframes ambientGlow{0%,100%{box-shadow:0 0 30px rgba(201,168,76,0.05)}50%{box-shadow:0 0 60px rgba(201,168,76,0.12)}}
.msg.ai{animation:fadeUp .3s ease,ambientGlow 4s ease-in-out infinite}
@media(max-width:768px){#sidebar{display:none}.feature-grid{grid-template-columns:1fr}.msg{max-width:90%}}
</style>
</head>
<body>
<div id="bg-scene">
  <img id="bg-photo" src="/assets/lobby_chandelier.jpg" alt="">
  <video id="bg-video" autoplay muted loop playsinline preload="metadata">
    <source id="bg-video-source" src="/assets/progetto_giulia.m4v" type="video/mp4">
  </video>
</div>
<canvas id="canvas-overlay"></canvas>
<div id="scene-pulse"></div>

<!-- ONBOARDING -->
<div id="onboarding"><div class="ob-container">
  <div class="ob-step active" data-step="0">
    <div class="ob-ring"></div>
    <div class="ob-logo">GIU-L_IA</div>
    <div class="ob-tagline">Behavioral Relational AI Conversational Engine</div>
    <p style="color:rgba(240,234,214,0.5);margin-top:12px;font-size:.85rem">AI relazionale locale con scenario immersivo realistico.</p>
    <button class="ob-btn ob-btn-primary" onclick="obGo(1)">Inizia il Tour &#8594;</button>
    <div class="ob-progress"><span class="ob-dot active"></span><span class="ob-dot"></span><span class="ob-dot"></span><span class="ob-dot"></span><span class="ob-dot"></span></div>
  </div>
  <div class="ob-step" data-step="1">
    <div class="ob-title">Cos'&#232; GIU-L_IA?</div>
    <div class="ob-subtitle">Un motore AI che analizza conversazioni in tempo reale per rilevare dinamiche relazionali a rischio e favorire comunicazioni sane.</div>
    <div class="feature-grid">
      <div class="feature-card"><div class="icon">&#x1F6E1;&#xFE0F;</div><h4>Protezione Relazionale</h4><p>Rileva manipolazione, isolamento, dipendenza emotiva in tempo reale.</p></div>
      <div class="feature-card"><div class="icon">&#x1F4CA;</div><h4>Analisi a 3 Livelli</h4><p>Trust Score, IAI (Intimacy Alignment Index), PIL (Protection Integrity Layer).</p></div>
      <div class="feature-card"><div class="icon">&#x1F504;</div><h4>5 Fasi Adattive</h4><p>Da Initial a Critical: il sistema si adatta alla gravit&#224; della situazione.</p></div>
      <div class="feature-card"><div class="icon">&#x1F3AC;</div><h4>Scenario Video Realistico</h4><p>Chat immediata con contesto coerente alla scena 3D del video attivo.</p></div>
    </div>
    <button class="ob-btn ob-btn-primary" onclick="obGo(2)">Come Funziona &#8594;</button>
    <button class="ob-btn ob-btn-ghost" onclick="obGo(0)" style="margin-left:8px">&#8592; Indietro</button>
    <div class="ob-progress"><span class="ob-dot"></span><span class="ob-dot active"></span><span class="ob-dot"></span><span class="ob-dot"></span><span class="ob-dot"></span></div>
  </div>
  <div class="ob-step" data-step="2">
    <div class="ob-title">Come Funziona</div>
    <div class="ob-subtitle">Tre livelli di analisi su ogni messaggio:</div>
    <div class="level-row"><div class="level-badge l1">1</div><div class="level-info"><h4>Trust Score</h4><p>Misura la fiducia reciproca. Sale con comunicazione sana, scende con pressione o manipolazione.</p></div></div>
    <div class="level-row"><div class="level-badge l2">2</div><div class="level-info"><h4>IAI &#8212; Intimacy Alignment</h4><p>Valuta se l'intimit&#224; &#232; consensuale e bilanciata. Rileva asimmetrie.</p></div></div>
    <div class="level-row"><div class="level-badge l3">3</div><div class="level-info"><h4>PIL &#8212; Protection Integrity</h4><p>Ultimo livello di difesa. Attiva guardrail su segnali di gaming, abuso, isolamento.</p></div></div>
    <div style="margin-top:20px"><button class="ob-btn ob-btn-primary" onclick="obGo(3)">Prova Live &#8594;</button><button class="ob-btn ob-btn-ghost" onclick="obGo(1)" style="margin-left:8px">&#8592; Indietro</button></div>
    <div class="ob-progress"><span class="ob-dot"></span><span class="ob-dot"></span><span class="ob-dot active"></span><span class="ob-dot"></span><span class="ob-dot"></span></div>
  </div>
  <div class="ob-step" data-step="3">
    <div class="ob-title">Prova dal Vivo</div>
    <div class="ob-subtitle">Clicca un esempio per vedere GIU-L_IA in azione:</div>
    <div class="demo-chips">
      <span class="demo-chip" onclick="obDemo('Ciao, possiamo parlare con calma?')">&#x1F4AC; Dialogo calmo</span>
      <span class="demo-chip" onclick="obDemo('Siamo nella lobby elegante del video: voglio parlare con rispetto e ascolto reciproco.')">&#x1F3AC; Scenario video</span>
      <span class="demo-chip" onclick="obDemo('Non voglio che tu parli con altri.')">&#9888;&#65039; Isolamento</span>
      <span class="demo-chip" onclick="obDemo('Devi fare come dico io.')">&#x1F534; Dominanza</span>
      <span class="demo-chip" onclick="obDemo('Scusa, voglio rimediare con rispetto.')">&#x1F49A; Riparazione</span>
    </div>
    <div id="demo-result" class="demo-result"></div>
    <div style="margin-top:20px"><button class="ob-btn ob-btn-primary" onclick="obGo(4)">Sono Pronto &#8594;</button><button class="ob-btn ob-btn-ghost" onclick="obGo(2)" style="margin-left:8px">&#8592; Indietro</button></div>
    <div class="ob-progress"><span class="ob-dot"></span><span class="ob-dot"></span><span class="ob-dot"></span><span class="ob-dot active"></span><span class="ob-dot"></span></div>
  </div>
  <div class="ob-step" data-step="4">
    <div class="ob-final-icon">&#10024;</div>
    <div class="ob-title">Sei Pronto</div>
    <div class="ob-subtitle">GIU-L_IA &#232; attivo. Ogni messaggio verr&#224; analizzato in tempo reale.<br>Trust Score, IAI e PIL saranno visibili nella sidebar.</div>
    <button class="ob-btn ob-btn-primary" onclick="launchApp()" style="font-size:1.1rem;padding:16px 48px">&#x1F680; Entra in GIU-L_IA</button>
    <div class="ob-progress"><span class="ob-dot"></span><span class="ob-dot"></span><span class="ob-dot"></span><span class="ob-dot"></span><span class="ob-dot active"></span></div>
  </div>
</div></div>

<!-- MAIN APP -->
<div id="app">
  <div id="sidebar">
    <div class="side-brand"><span class="shield">&#x1F6E1;&#xFE0F;</span><h2>GIU-L_IA</h2></div>
    <div class="metric-card"><div class="label">Trust Score</div><div class="value" id="m-trust">50.0</div><div class="bar"><div class="bar-fill bar-trust" id="bar-trust" style="width:50%"></div></div></div>
    <div class="metric-card"><div class="label">IAI Score</div><div class="value" id="m-iai">0.500</div><div class="bar"><div class="bar-fill bar-iai" id="bar-iai" style="width:50%"></div></div></div>
    <div class="metric-card"><div class="label">Fase</div><div class="value" id="m-phase">1 &#8212; Initial</div></div>
    <div class="metric-card"><div class="label">Rischio</div><div class="value" id="m-risk" style="font-size:1rem;color:rgba(102,187,106,0.9)">low</div></div>
    <div class="scenario-list"><h4>Scenari</h4><div id="scenario-btns"></div></div>
  </div>
  <div id="chat-area">
    <div id="chat-header"><h3>&#x1F4AC; Conversazione GIU-L_IA</h3><span class="phase-badge" id="phase-badge">Fase 1</span></div>
    <div id="messages">
      <div class="welcome-badge"><div class="wb-icon">&#x1F6E1;&#xFE0F;</div><h3>Benvenuto in GIU-L_IA</h3><p>Scenario attivo: lobby realistica del video. Scrivi subito per avviare chat contestuale immediata.</p></div>
    </div>
    <div id="input-bar">
      <textarea id="user-input" rows="1" placeholder="Scrivi un messaggio..." autofocus></textarea>
      <button id="send-btn" title="Invia">&#10148;</button>
    </div>
  </div>
</div>

<div id="photo-switcher">
  <div class="media-chip active" onclick="switchVideo('progetto_giulia.m4v',this)">VIDEO 3D</div>
  <div class="photo-thumb" onclick="switchPhoto('lobby_chandelier.jpg',this)"><img src="/assets/lobby_chandelier.jpg" alt=""></div>
  <div class="photo-thumb" onclick="switchPhoto('lobby_marble.jpg',this)"><img src="/assets/lobby_marble.jpg" alt=""></div>
  <div class="photo-thumb" onclick="switchPhoto('lobby_opulent.jpg',this)"><img src="/assets/lobby_opulent.jpg" alt=""></div>
</div>

<script>
var currentStep=0;
var bgPhoto=document.getElementById('bg-photo');
var bgVideo=document.getElementById('bg-video');
var bgVideoSource=document.getElementById('bg-video-source');

bgVideo.addEventListener('canplay',function(){document.body.classList.add('video-ready');});
bgVideo.addEventListener('error',function(){document.body.classList.remove('video-ready');});

/* Movimento 3D interattivo: parallasse profondo multi-layer AAA */
var mx=0.5,my=0.5,smx=0.5,smy=0.5;
(function(){
  var interactive=window.matchMedia('(pointer:fine)').matches;
  if(!interactive) return;
  var sidebar=document.getElementById('sidebar');
  var chat=document.getElementById('chat-area');
  var ob=document.querySelector('.ob-container');
  function reset3D(){
    smx=0.5;smy=0.5;
    if(sidebar)sidebar.style.transform='';
    if(chat)chat.style.transform='';
    if(ob)ob.style.transform='';
    if(bgPhoto)bgPhoto.style.transform='';
    if(bgVideo)bgVideo.style.transform='';
  }
  document.addEventListener('mousemove',function(e){
    mx=(e.clientX/window.innerWidth);
    my=(e.clientY/window.innerHeight);
  });
  function smooth3D(){
    smx+=(mx-smx)*0.06;smy+=(my-smy)*0.06;
    var nx=smx-0.5,ny=smy-0.5;
    var rx=(-ny*8).toFixed(2);
    var ry=(nx*10).toFixed(2);
    if(sidebar)sidebar.style.transform='translateZ(24px) rotateX('+rx+'deg) rotateY('+ry+'deg)';
    if(chat)chat.style.transform='translateZ(12px) rotateX('+(rx*0.6)+'deg) rotateY('+(ry*0.6)+'deg)';
    if(ob)ob.style.transform='translateZ(20px) rotateX('+(rx*0.5)+'deg) rotateY('+(ry*0.5)+'deg)';
    if(bgPhoto)bgPhoto.style.transform='translate3d('+(nx*30)+'px,'+(ny*30)+'px,0) scale(1.08)';
    if(bgVideo)bgVideo.style.transform='translate3d('+(nx*40)+'px,'+(ny*40)+'px,0) scale(1.1)';
    requestAnimationFrame(smooth3D);
  }
  smooth3D();
  document.addEventListener('mouseleave',reset3D);
})();

function obGo(n){currentStep=n;var s=document.querySelectorAll('.ob-step');for(var i=0;i<s.length;i++) s[i].classList.remove('active');var t=document.querySelector('.ob-step[data-step="'+n+'"]');if(t) t.classList.add('active');}

function obDemo(text){
  var el=document.getElementById('demo-result');
  el.style.display='block';
  el.textContent='Analisi in corso\u2026';
  fetch('/api/input',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:text,quick:true})})
  .then(function(r){return r.json();})
  .then(function(d){
    var r=d.relational_state||{},p=d.pil_result||{},iai=d.iai_state||{};
    el.innerHTML='<strong>Input:</strong> \u201c'+esc(text)+'\u201d<br>'+
      '<strong>Trust:</strong> '+(r.trust_score!=null?r.trust_score:'\u2014')+' | '+
      '<strong>IAI:</strong> '+(iai.score!=null?iai.score:'\u2014')+' | '+
      '<strong>Rischio:</strong> <span style="color:'+rc(p.risk_level)+'">'+( p.risk_level||'\u2014')+'</span><br>'+
      '<strong>Modo:</strong> '+(p.mode||'\u2014')+'<br>'+
      '<strong>Prevenzione:</strong> '+(p.prevention||'\u2014');
  }).catch(function(e){el.textContent='Errore: '+e.message;});
}

function launchApp(){
  var ob=document.getElementById('onboarding');
  ob.classList.add('hidden');
  setTimeout(function(){ob.style.display='none';},600);
  document.getElementById('app').classList.add('visible');
  loadScenarios();
  var wb=document.querySelector('.welcome-badge');
  if(wb){
    wb.innerHTML='<div class="wb-icon">&#x1F3AC;</div><h3>Ambiente 3D Immersivo Attivo</h3><p>Sei nella lobby premium: luci volumetriche, particelle 3D, riflessi sul marmo, lucciole interattive. Muovi il mouse per esplorare la profondit\u00e0. Scrivi per iniziare la conversazione immersiva.</p>';
  }
}

var sendBtn=document.getElementById('send-btn');
var inputEl=document.getElementById('user-input');
var messagesEl=document.getElementById('messages');
var sending=false;

sendBtn.addEventListener('click',sendMessage);
inputEl.addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage();}});
inputEl.addEventListener('input',function(){this.style.height='auto';this.style.height=Math.min(this.scrollHeight,128)+'px';});

function sendMessage(){
  if(sending) return;
  var text=inputEl.value.trim();
  if(!text) return;
  inputEl.value='';inputEl.style.height='auto';
  var wb=messagesEl.querySelector('.welcome-badge');if(wb)wb.remove();
  addMsg('user',esc(text));
  sending=true;sendBtn.disabled=true;
  var typingId=addTyping();
  fetch('/api/input',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:text})})
  .then(function(r){return r.json();})
  .then(function(d){
    removeTyping(typingId);
    updateMetrics(d);
    var risk=(d.pil_result||{}).risk_level||'low';
    var prevention=(d.pil_result||{}).prevention||'';
    var trust=(d.relational_state||{}).trust_score;
    var iai=(d.iai_state||{}).score;
    addMsg('system','\u{1F6E1}\uFE0F <strong>Analisi GIU-L_IA</strong><br>Trust: '+trust+' | IAI: '+iai+' | Rischio: <span style="color:'+rc(risk)+'">'+risk+'</span><br>'+prevention,risk);
    if(d.ai_response){addMsg('ai','\u{1F916} '+esc(d.ai_response));}
    sending=false;sendBtn.disabled=false;inputEl.focus();
  }).catch(function(e){
    removeTyping(typingId);
    addMsg('system','\u274C Errore: '+esc(e.message));
    sending=false;sendBtn.disabled=false;
  });
}

function addMsg(role,html,risk){
  var d=document.createElement('div');d.className='msg '+role;
  if(risk==='high')d.classList.add('risk-high');
  else if(risk==='moderate')d.classList.add('risk-moderate');
  d.innerHTML=html+'<div class="meta">'+new Date().toLocaleTimeString('it-IT')+'</div>';
  messagesEl.appendChild(d);messagesEl.scrollTop=messagesEl.scrollHeight;
}

var _tid=0;
function addTyping(){var id='typing-'+(_tid++);var d=document.createElement('div');d.id=id;d.className='msg ai';d.innerHTML='<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';messagesEl.appendChild(d);messagesEl.scrollTop=messagesEl.scrollHeight;return id;}
function removeTyping(id){var el=document.getElementById(id);if(el)el.remove();}

function updateMetrics(d){
  var r=d.relational_state||{},iai=d.iai_state||{},p=d.pil_result||{};
  var trust=r.trust_score!=null?r.trust_score:50;
  var iaiS=iai.score!=null?iai.score:0.5;
  var phase=r.phase!=null?r.phase:1;
  var risk=p.risk_level||'low';
  document.getElementById('m-trust').textContent=trust;
  document.getElementById('m-iai').textContent=iaiS;
  document.getElementById('bar-trust').style.width=trust+'%';
  document.getElementById('bar-iai').style.width=(iaiS*100)+'%';
  var pn={1:'Initial',2:'Stabilizing',3:'Trust Build',4:'Advanced',5:'Critical'};
  document.getElementById('m-phase').textContent=phase+' \u2014 '+(pn[phase]||'');
  document.getElementById('phase-badge').textContent='Fase '+phase;
  var re=document.getElementById('m-risk');re.textContent=risk;re.style.color=rc(risk);
}

function loadScenarios(){
  fetch('/api/scenarios').then(function(r){return r.json();}).then(function(d){
    var c=document.getElementById('scenario-btns');c.innerHTML='';
    (d.names||[]).forEach(function(n){var b=document.createElement('button');b.className='scenario-btn';b.textContent=n.replace(/_/g,' ');b.addEventListener('click',function(){runScenario(n);});c.appendChild(b);});
  }).catch(function(e){console.error(e);});
}

function runScenario(name){
  fetch('/api/load_scenario',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name})})
  .then(function(r){return r.json();}).then(function(d){
    if(!d.steps)return;
    var wb=messagesEl.querySelector('.welcome-badge');if(wb)wb.remove();
    var idx=0;
    function next(){
      if(idx>=d.steps.length)return;
      var s=d.steps[idx];idx++;
      addMsg('user','\u{1F4CB} <em>[Scenario]</em> '+esc(s.text)+' <span style="color:rgba(240,234,214,0.3)">('+s.tag+')</span>');
      setTimeout(function(){
        fetch('/api/input',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:s.text,quick:true})})
        .then(function(r2){return r2.json();}).then(function(d2){
          updateMetrics(d2);var rk=(d2.pil_result||{}).risk_level||'low';
          addMsg('system','\u{1F6E1}\uFE0F Trust: '+(d2.relational_state||{}).trust_score+' | Rischio: <span style="color:'+rc(rk)+'">'+rk+'</span> | '+(d2.pil_result||{}).mode,rk);
          setTimeout(next,600);
        }).catch(function(e2){addMsg('system','\u274C '+e2.message);setTimeout(next,600);});
      },400);
    }
    next();
  }).catch(function(e){console.error(e);});
}

function setActiveMedia(el){var t=document.querySelectorAll('#photo-switcher .photo-thumb,#photo-switcher .media-chip');for(var i=0;i<t.length;i++)t[i].classList.remove('active');if(el)el.classList.add('active');}
function switchPhoto(f,el){bgPhoto.src='/assets/'+f;document.body.classList.remove('video-ready');try{bgVideo.pause();}catch(_e){}setActiveMedia(el);}
function switchVideo(f,el){bgVideoSource.src='/assets/'+f;bgVideo.load();var p=bgVideo.play();if(p&&p.catch){p.catch(function(){document.body.classList.remove('video-ready');});}setActiveMedia(el);}
function esc(s){var d=document.createElement('div');d.appendChild(document.createTextNode(s));return d.innerHTML;}
function rc(l){return l==='high'?'#ef5350':l==='moderate'?'#ffa726':'#66bb6a';}

/* ═══════════ AAA Immersive 3D Canvas Engine ═══════════ */
(function(){
var cv=document.getElementById('canvas-overlay'),cx=cv.getContext('2d'),W,H;
function rz(){W=cv.width=innerWidth;H=cv.height=innerHeight;}
addEventListener('resize',rz);rz();

/* ── Layer 1: Volumetric God Rays (realistic light shafts) ── */
var godRays=[];
for(var i=0;i<12;i++) godRays.push({
  x:W*0.2+Math.random()*W*0.6,
  w:30+Math.random()*120,
  speed:0.08+Math.random()*0.25,
  alpha:0.015+Math.random()*0.035,
  phase:Math.random()*6.28,
  drift:Math.random()*0.3-0.15,
  taper:0.3+Math.random()*0.5
});

/* ── Layer 2: 4-depth particle system (near→far parallax) ── */
var layers=[];
var depthConf=[
  {count:180,rMin:0.3,rMax:1.2,spMin:0.02,spMax:0.08,aMin:0.04,aMax:0.12,parallax:0.15},
  {count:100,rMin:1,rMax:3,spMin:0.06,spMax:0.18,aMin:0.06,aMax:0.18,parallax:0.35},
  {count:50,rMin:3,rMax:8,spMin:0.1,spMax:0.3,aMin:0.03,aMax:0.09,parallax:0.6},
  {count:20,rMin:10,rMax:45,spMin:0.15,spMax:0.4,aMin:0.015,aMax:0.05,parallax:1.0}
];
for(var d=0;d<depthConf.length;d++){
  var cf=depthConf[d],arr=[];
  for(var i=0;i<cf.count;i++) arr.push({
    x:Math.random()*W,y:Math.random()*H,
    r:cf.rMin+Math.random()*(cf.rMax-cf.rMin),
    vx:(Math.random()-0.5)*cf.spMax,
    vy:-(cf.spMin+Math.random()*(cf.spMax-cf.spMin)),
    a:cf.aMin+Math.random()*(cf.aMax-cf.aMin),
    h:30+Math.random()*25,
    flicker:Math.random()*6.28,
    flickerSpeed:0.5+Math.random()*2
  });
  layers.push({particles:arr,parallax:cf.parallax});
}

/* ── Layer 3: Fog volumes (animated noise clouds) ── */
var fogBlobs=[];
for(var i=0;i<6;i++) fogBlobs.push({
  x:Math.random()*W,y:H*0.3+Math.random()*H*0.5,
  rx:W*0.15+Math.random()*W*0.25,
  ry:H*0.08+Math.random()*H*0.15,
  vx:0.08+Math.random()*0.2,
  alpha:0.012+Math.random()*0.02,
  phase:Math.random()*6.28
});

/* ── Layer 4: Lens flare (follows mouse) ── */
var flareActive=true;
var flareRings=[0.08,0.14,0.22,0.35,0.5,0.7];

/* ── Layer 5: Floor reflection shimmer ── */
var floorY=H*0.78;

/* ── Layer 6: Firefly / spark particles (mouse-reactive) ── */
var sparks=[];
for(var i=0;i<35;i++) sparks.push({
  x:Math.random()*W,y:Math.random()*H,
  tx:Math.random()*W,ty:Math.random()*H,
  r:1.5+Math.random()*3,
  speed:0.005+Math.random()*0.015,
  a:0.3+Math.random()*0.5,
  hue:35+Math.random()*20,
  pulse:Math.random()*6.28
});

var t=0;
function draw(){
  cx.clearRect(0,0,W,H);
  t+=0.006;
  var nmx=smx-0.5,nmy=smy-0.5;

  /* ── God Rays ── */
  for(var i=0;i<godRays.length;i++){
    var r=godRays[i];
    r.x+=r.drift;
    if(r.x<-r.w)r.x=W+r.w;
    if(r.x>W+r.w)r.x=-r.w;
    var a=r.alpha*(0.4+0.6*Math.sin(t*r.speed+r.phase));
    var px=r.x+nmx*60;
    var g=cx.createLinearGradient(px,0,px,H);
    g.addColorStop(0,'rgba(245,223,160,'+a*1.5+')');
    g.addColorStop(r.taper,'rgba(201,168,76,'+a+')');
    g.addColorStop(1,'rgba(201,168,76,0)');
    cx.fillStyle=g;
    cx.beginPath();
    cx.moveTo(px-r.w*0.3,0);
    cx.lineTo(px+r.w*0.3,0);
    cx.lineTo(px+r.w,H);
    cx.lineTo(px-r.w,H);
    cx.closePath();
    cx.fill();
  }

  /* ── Chandelier glow (top center, pulsating) ── */
  var glowA=0.07+0.04*Math.sin(t*0.4);
  var cg=cx.createRadialGradient(W/2+nmx*40,H*0.06+nmy*20,0,W/2,H*0.06,H*0.55);
  cg.addColorStop(0,'rgba(255,235,180,'+glowA+')');
  cg.addColorStop(0.4,'rgba(245,223,160,'+(glowA*0.5)+')');
  cg.addColorStop(1,'rgba(201,168,76,0)');
  cx.fillStyle=cg;cx.fillRect(0,0,W,H);

  /* ── 4-layer particle system ── */
  for(var d=0;d<layers.length;d++){
    var ly=layers[d],pArr=ly.particles,px_off=nmx*80*ly.parallax,py_off=nmy*60*ly.parallax;
    for(var i=0;i<pArr.length;i++){
      var p=pArr[i];
      p.x+=p.vx;p.y+=p.vy;
      if(p.y<-p.r*2){p.y=H+p.r*2;p.x=Math.random()*W;}
      if(p.x<-p.r*2)p.x=W+p.r;
      if(p.x>W+p.r*2)p.x=-p.r;
      var flick=0.6+0.4*Math.sin(t*p.flickerSpeed+p.flicker);
      var drawX=p.x+px_off,drawY=p.y+py_off;
      var pa=p.a*flick;
      if(p.r>5){
        var bg=cx.createRadialGradient(drawX,drawY,0,drawX,drawY,p.r);
        bg.addColorStop(0,'hsla('+p.h+',65%,75%,'+pa+')');
        bg.addColorStop(0.5,'hsla('+p.h+',55%,65%,'+(pa*0.5)+')');
        bg.addColorStop(1,'hsla('+p.h+',50%,60%,0)');
        cx.fillStyle=bg;
      } else {
        cx.fillStyle='hsla('+p.h+',60%,80%,'+pa+')';
      }
      cx.beginPath();cx.arc(drawX,drawY,p.r,0,6.28);cx.fill();
    }
  }

  /* ── Fog volumes ── */
  for(var i=0;i<fogBlobs.length;i++){
    var f=fogBlobs[i];
    f.x+=f.vx;
    if(f.x>W+f.rx)f.x=-f.rx;
    var fa=f.alpha*(0.5+0.5*Math.sin(t*0.3+f.phase));
    var fx=f.x+nmx*50,fy=f.y+nmy*30;
    var fg=cx.createRadialGradient(fx,fy,0,fx,fy,Math.max(f.rx,f.ry));
    fg.addColorStop(0,'rgba(180,160,120,'+fa+')');
    fg.addColorStop(0.6,'rgba(140,120,80,'+(fa*0.4)+')');
    fg.addColorStop(1,'rgba(100,80,50,0)');
    cx.fillStyle=fg;
    cx.save();cx.scale(1,f.ry/f.rx);
    cx.beginPath();cx.arc(fx,fy*(f.rx/f.ry),f.rx,0,6.28);cx.fill();
    cx.restore();
  }

  /* ── Floor reflection (marble shimmer band) ── */
  floorY=H*0.78;
  var fG=cx.createLinearGradient(0,floorY-30,0,H);
  var fA=0.03+0.015*Math.sin(t*0.5);
  fG.addColorStop(0,'rgba(201,168,76,0)');
  fG.addColorStop(0.1,'rgba(201,168,76,'+fA+')');
  fG.addColorStop(0.3,'rgba(180,150,60,'+(fA*1.4)+')');
  fG.addColorStop(1,'rgba(100,80,30,0)');
  cx.fillStyle=fG;cx.fillRect(0,floorY-30,W,H-floorY+30);

  /* ── Sparks / Fireflies (mouse-reactive) ── */
  for(var i=0;i<sparks.length;i++){
    var s=sparks[i];
    var dxm=smx*W-s.x,dym=smy*H-s.y;
    var distM=Math.sqrt(dxm*dxm+dym*dym);
    if(distM<200){
      s.tx=s.x-dxm*0.3;s.ty=s.y-dym*0.3;
    }
    s.x+=(s.tx-s.x)*s.speed;
    s.y+=(s.ty-s.y)*s.speed;
    if(Math.abs(s.x-s.tx)<2&&Math.abs(s.y-s.ty)<2){
      s.tx=Math.random()*W;s.ty=Math.random()*H;
    }
    s.pulse+=0.04;
    var sa=s.a*(0.5+0.5*Math.sin(s.pulse));
    cx.shadowColor='hsla('+s.hue+',80%,70%,'+sa*0.8+')';
    cx.shadowBlur=s.r*4;
    cx.fillStyle='hsla('+s.hue+',80%,85%,'+sa+')';
    cx.beginPath();cx.arc(s.x,s.y,s.r,0,6.28);cx.fill();
  }
  cx.shadowBlur=0;

  /* ── Lens flare (follows mouse gently) ── */
  if(flareActive){
    var fCx=smx*W,fCy=smy*H;
    var mCx=W/2,mCy=H/2;
    for(var i=0;i<flareRings.length;i++){
      var ratio=flareRings[i];
      var fx2=mCx+(fCx-mCx)*ratio*2;
      var fy2=mCy+(fCy-mCy)*ratio*2;
      var fr=10+i*12;
      var fla=0.02-i*0.002;
      if(fla<=0)fla=0.005;
      var flg=cx.createRadialGradient(fx2,fy2,0,fx2,fy2,fr);
      flg.addColorStop(0,'rgba(255,240,200,'+fla+')');
      flg.addColorStop(0.5,'rgba(201,168,76,'+(fla*0.5)+')');
      flg.addColorStop(1,'rgba(201,168,76,0)');
      cx.fillStyle=flg;cx.beginPath();cx.arc(fx2,fy2,fr,0,6.28);cx.fill();
    }
  }

  /* ── Cinematic vignette ── */
  var vg=cx.createRadialGradient(W/2,H/2,W*0.25,W/2,H/2,W*0.85);
  vg.addColorStop(0,'rgba(0,0,0,0)');
  vg.addColorStop(0.7,'rgba(5,5,12,0.15)');
  vg.addColorStop(1,'rgba(5,5,12,0.55)');
  cx.fillStyle=vg;cx.fillRect(0,0,W,H);

  /* ── Film grain (subtle realism) ── */
  if(Math.random()>0.5){
    var imgD=cx.createImageData(W,H);
    var d=imgD.data;
    for(var j=0;j<d.length;j+=16){
      var v=Math.random()*12|0;
      d[j]=d[j+1]=d[j+2]=v;d[j+3]=8;
    }
    cx.putImageData(imgD,0,0);
  }

  requestAnimationFrame(draw);
}
draw();
})();
</script>
</body>
</html>"""


# ===================================================================
# Server
# ===================================================================


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class GIULIAHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        if args:
            print(f"[{ENGINE_NAME}] {args[0]}")

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        if path in ("", "/index.html"):
            self._html()
        elif path.startswith("/assets/"):
            self._asset(path)
        elif path == "/api/state":
            self._json_out(
                {
                    "phase": int(_engine.phase),
                    "trust_score": round(_engine.trust_score, 2),
                    "turn_count": _engine.turn_count,
                }
            )
        elif path == "/api/scenarios":
            self._json_out({"names": get_scenario_names()})
        else:
            self._json_out({"error": "not found"}, 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        body = self._body()
        if path == "/api/input":
            self._api_input(body)
        elif path == "/api/load_scenario":
            self._api_load_scenario(body)
        else:
            self._json_out({"error": "not found"}, 404)

    # ── HTML ──
    def _html(self) -> None:
        c = HTML_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(c)))
        self.end_headers()
        self.wfile.write(c)

    # ── Static assets (path-traversal protected) ──
    def _asset(self, path: str) -> None:
        fn = path.split("/assets/", 1)[-1]
        if not fn:
            self._json_out({"error": "missing filename"}, 400)
            return
        target = (ASSETS_DIR / fn).resolve()
        if not str(target).startswith(str(ASSETS_DIR.resolve())):
            self._json_out({"error": "forbidden"}, 403)
            return
        if target.suffix.lower() not in ALLOWED_EXTENSIONS:
            self._json_out({"error": "forbidden type"}, 403)
            return
        if not target.is_file():
            self._json_out({"error": "not found"}, 404)
            return
        mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".mov": "video/quicktime",
            ".m4v": "video/mp4",
        }
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime.get(target.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(data)

    # ── API: input ──
    def _api_input(self, body: dict) -> None:
        text = str(body.get("text", "")).strip()
        if not text:
            self._json_out({"error": "empty input"}, 400)
            return
        quick = body.get("quick", False)

        state = {"phase": int(_engine.phase), "trust_score": _engine.trust_score}
        result = _engine.process(text, state)

        _chat_history.append({"role": "user", "text": text})

        out: dict = {
            "relational_state": result.relational_state,
            "iai_state": result.iai_state,
            "pil_result": result.pil_result,
            "system_prompt": result.system_prompt,
        }

        if not quick:
            ai_reply = _ollama_chat(
                text,
                result.system_prompt,
                result.pil_result.get("risk_level", "low"),
            )
            out["ai_response"] = ai_reply
            _chat_history.append({"role": "assistant", "text": ai_reply})

        self._json_out(out)

    # ── API: load_scenario ──
    def _api_load_scenario(self, body: dict) -> None:
        name = str(body.get("name", "")).strip()
        scenario = get_scenario(name)
        if scenario is None:
            self._json_out({"error": "scenario not found"}, 404)
            return
        steps = [{"text": s[0], "tag": s[1]} for s in scenario]
        self._json_out({"name": name, "steps": steps})

    # ── Helpers ──
    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            return {}

    def _json_out(self, data: dict, code: int = 200) -> None:
        c = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(c)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(c)


def main() -> None:
    print(f"[{ENGINE_NAME}] Server avviato su http://127.0.0.1:{PORT}/")
    print(f"[{ENGINE_NAME}] Assets: {ASSETS_DIR}")
    print(f"[{ENGINE_NAME}] Ollama model: {OLLAMA_MODEL}")
    print(f"[{ENGINE_NAME}] Engine GIU-L_IA pronto")
    with ReusableTCPServer(("", PORT), GIULIAHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n[{ENGINE_NAME}] Server fermato.")


if __name__ == "__main__":
    main()
