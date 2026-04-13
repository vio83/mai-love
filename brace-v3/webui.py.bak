#!/usr/bin/env python3
import http.server
import json
import socketserver
from brace_v3 import BRACE_v30, ImplicitProfile, WindowState
from scenarios_db import SCENARIOS

HOST='127.0.0.1'
PORT=9443

class S(socketserver.TCPServer):
    allow_reuse_address=True

class State:
    def __init__(self):
        self.engine=BRACE_v30()
        self.state={
            'phase':1,
            'trust_score':50.0,
            'iai_score':0.10,
            'history':[],
            'implicit_profile':ImplicitProfile(),
            'window_state':WindowState(),
        }
        self.current_scenario=None

st=State()

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send(self, code, payload):
        self.send_response(code)
        self.send_header('Content-type','application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def do_GET(self):
        if self.path=='/':
            self.send_response(200)
            self.send_header('Content-type','text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))
            return
        if self.path=='/api/state':
            payload={
                'phase': st.state['phase'],
                'trust_score': st.state['trust_score'],
                'iai_score': st.state['iai_score'],
                'history_length': len(st.state['history']),
                'current_scenario': st.current_scenario,
            }
            self._send(200,payload)
            return
        if self.path=='/api/scenarios':
            self._send(200,{'scenarios':list(SCENARIOS.keys())})
            return
        self._send(404,{'error':'not found'})

    def do_POST(self):
        n=int(self.headers.get('Content-Length',0))
        raw=self.rfile.read(n).decode('utf-8') if n>0 else '{}'
        data=json.loads(raw)
        if self.path=='/api/input':
            text=data.get('text','')
            out=st.engine.process(text, st.state)
            st.state['phase']=out.relational_state['phase']
            st.state['trust_score']=out.relational_state['trust_score']
            st.state['iai_score']=out.iai_state['score']
            st.state['history'].append(text)
            self._send(200,{
                'phase': out.relational_state['phase'],
                'trust': out.relational_state['trust_score'],
                'iai': out.iai_state['score'],
                'pil_mode': out.pil_result['mode'],
                'recommendation': out.pil_result['prevention']
            })
            return
        if self.path=='/api/load_scenario':
            s=data.get('scenario','')
            if s in SCENARIOS:
                st.current_scenario=s
                st.engine=BRACE_v30()
                st.state['phase']=1
                st.state['trust_score']=50.0
                st.state['iai_score']=0.10
                st.state['history']=[]
                self._send(200,{'success':True,'scenario':s,'turns':len(SCENARIOS[s])})
            else:
                self._send(400,{'success':False})
            return
        self._send(404,{'error':'not found'})

HTML='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BRACE Human UI</title><style>
:root{--ink:#202b38;--soft:#617284;--sky:#e6f1ff;--warm:#fff1e4;--glass:rgba(255,255,255,.78);--line:rgba(255,255,255,.52);--acc:#2f73d9;--acc2:#ef7d42;--meter:rgba(47,115,217,.18);--shadow:0 18px 42px rgba(26,43,67,.14)}*{box-sizing:border-box}body{margin:0;font-family:"Avenir Next","Segoe UI",sans-serif;color:var(--ink);background:radial-gradient(1100px 580px at -8% -15%,rgba(239,125,66,.24),transparent 62%),radial-gradient(900px 520px at 108% 0%,rgba(47,115,217,.22),transparent 70%),linear-gradient(160deg,var(--sky) 0%,#f6faff 45%,var(--warm) 100%);min-height:100vh}.page{max-width:1160px;margin:0 auto;padding:20px 14px 26px}.hero,.card{border:1px solid var(--line);background:var(--glass);box-shadow:var(--shadow);border-radius:18px;backdrop-filter:blur(4px)}.hero{padding:22px;margin-bottom:14px}h1{margin:0;font-size:clamp(1.4rem,2.3vw,2rem)}.sub{margin-top:8px;color:var(--soft)}.tag{display:inline-block;margin-top:10px;padding:4px 10px;border-radius:999px;background:rgba(239,125,66,.2);color:#8f451f;font-weight:700;font-size:.82rem}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.card{padding:14px}h2{margin:0 0 10px;font-size:1.02rem}.full{grid-column:1/-1}.m{margin:10px 0}.mh{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;font-size:.94rem}.v{font-weight:800;color:var(--acc)}.meter{width:100%;height:9px;border-radius:999px;overflow:hidden;background:var(--meter)}.meter span{display:block;height:100%;width:0%;border-radius:inherit;background:linear-gradient(90deg,#2f73d9,#34b9ca);transition:width .28s ease}.muted{color:var(--soft);font-size:.9rem;margin-top:8px}select,input{width:100%;border:1px solid rgba(32,43,56,.18);border-radius:10px;background:rgba(255,255,255,.86);color:var(--ink);padding:10px 11px;font-size:.95rem}.row{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center}button{border:none;border-radius:10px;padding:10px 14px;color:#fff;font-weight:700;cursor:pointer;background:linear-gradient(135deg,var(--acc2),#f59f58)}.sec{background:linear-gradient(135deg,var(--acc),#4f93f1)}.out{margin-top:10px;min-height:66px;padding:10px 11px;border-radius:11px;border:1px solid rgba(47,115,217,.2);background:rgba(236,244,255,.82);font-size:.92rem}@media(max-width:900px){.grid{grid-template-columns:1fr}.row{grid-template-columns:1fr}button{width:100%}}
</style></head><body><div class="page"><div class="hero"><h1>BRACE v3.0 Human Visual Layer</h1><div class="sub">Visuale concreta e naturale: contrasto realistico, profondita e segnali operativi chiari.</div><div class="tag">local-first · human-centered · practical</div></div><div class="grid"><div class="card"><h2>State Pulse</h2><div class="m"><div class="mh"><span>Relational Phase</span><span class="v" id="phase">1</span></div><div class="meter"><span id="phase-fill"></span></div></div><div class="m"><div class="mh"><span>Trust</span><span class="v" id="trust">50.0</span></div><div class="meter"><span id="trust-fill"></span></div></div><div class="m"><div class="mh"><span>IAI</span><span class="v" id="iai">0.10</span></div><div class="meter"><span id="iai-fill"></span></div></div><div class="m"><div class="mh"><span>History</span><span class="v" id="history">0</span></div><div class="meter"><span id="history-fill"></span></div></div><div class="muted" id="heartbeat">Heartbeat: waiting first signal...</div></div><div class="card"><h2>Scenario Deck</h2><select id="scenario-select"><option value="">Manual mode</option></select><button class="sec" onclick="loadScenario()">Load Scenario</button><ul id="scenario-list" class="muted"></ul></div><div class="card full"><h2>Input Stream</h2><div class="row"><input type="text" id="input" placeholder="Write your relational prompt..."><button onclick="processInput()">Process</button></div><div class="out" id="result-box">Waiting for input...</div></div></div></div><script>
async function updateState(){try{const r=await fetch('/api/state');const s=await r.json();const p=Number(s.phase||1),t=Number(s.trust_score||50),i=Number(s.iai_score||.1),h=Number(s.history_length||0);document.getElementById('phase').innerText=p;document.getElementById('trust').innerText=t.toFixed(1);document.getElementById('iai').innerText=i.toFixed(2);document.getElementById('history').innerText=h;document.getElementById('phase-fill').style.width=Math.min(100,(p/6)*100)+'%';document.getElementById('trust-fill').style.width=Math.max(0,Math.min(100,t))+'%';document.getElementById('iai-fill').style.width=Math.max(0,Math.min(100,i*100))+'%';document.getElementById('history-fill').style.width=Math.min(100,h*6)+'%';document.getElementById('heartbeat').innerText='Heartbeat: phase '+p+' · trust '+t.toFixed(1)}catch(_){}}
async function loadScenarios(){try{const r=await fetch('/api/scenarios');const d=await r.json();const list=d.scenarios||[];const sel=document.getElementById('scenario-select');const ul=document.getElementById('scenario-list');list.forEach(s=>{const o=document.createElement('option');o.value=s;o.innerText=s;sel.appendChild(o);const li=document.createElement('li');li.innerText=s;ul.appendChild(li)})}catch(_){}}
async function processInput(){const input=document.getElementById('input');const text=input.value.trim();if(!text)return;try{const r=await fetch('/api/input',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});const res=await r.json();document.getElementById('result-box').innerHTML='<strong>Mode:</strong> '+(res.pil_mode||'n/a')+' · <strong>Trust:</strong> '+Number(res.trust||0).toFixed(1)+'<br/><strong>IAI:</strong> '+Number(res.iai||0).toFixed(3)+'<br/><strong>Recommendation:</strong> '+(res.recommendation||'').toString().slice(0,170);input.value='';updateState()}catch(_){}}
async function loadScenario(){const s=document.getElementById('scenario-select').value;if(!s)return;try{await fetch('/api/load_scenario',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:s})});document.getElementById('result-box').innerHTML='<strong>Scenario loaded:</strong> '+s}catch(_){}}
document.addEventListener('keypress',e=>{if(e.key==='Enter'&&e.target.id==='input')processInput()});loadScenarios();setInterval(updateState,1000);
</script></body></html>'''

if __name__=='__main__':
    with S((HOST,PORT),H) as httpd:
        print(f'BRACE Human UI: http://{HOST}:{PORT}')
        httpd.serve_forever()
