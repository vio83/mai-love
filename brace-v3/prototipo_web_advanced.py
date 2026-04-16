#!/usr/bin/env python3
"""
GIU-L_IA v3.1 PROTOTIPO — Web UI Avanzato
Porta 9001 — Interface Interattiva con Controllo Sviluppatore Remoto
Backend + Frontend Integrati • Performance Massima iMac
"""

import http.server
import json
import mimetypes
import os
import shutil
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
AVATAR_FILE = BRACE_DIR / "media" / "avatar-giulia.jpg"
AVATAR_ROUTE = "/media/avatar-giulia"
TTS_VOICE_HINT = os.getenv("GIULIA_TTS_VOICE_HINT", "it-IT").strip() or "it-IT"
TTS_VOICE_NAME = os.getenv("GIULIA_TTS_VOICE_NAME", "").strip()
TTS_STYLE = os.getenv("GIULIA_TTS_STYLE", "warm").strip() or "warm"
TTS_RATE = float(os.getenv("GIULIA_TTS_RATE", "0.90").strip() or "0.90")
TTS_PITCH = float(os.getenv("GIULIA_TTS_PITCH", "0.92").strip() or "0.92")
OPENSSL_BIN = shutil.which("openssl") or "/usr/bin/openssl"

sys.path.insert(0, str(BRACE_DIR.parent))
from brace_v3 import GIU_L_IA  # noqa: E402
from scenarios_db import SCENARIOS  # noqa: E402

WORLD_CATEGORY_A2Z = {
    "A": "Affetti",
    "B": "Business",
    "C": "Creativita",
    "D": "Didattica",
    "E": "Empatia",
    "F": "Famiglia",
    "G": "Governance",
    "H": "Health",
    "I": "Innovazione",
    "J": "Journal",
    "K": "Knowledge",
    "L": "Leadership",
    "M": "Mindfulness",
    "N": "Negotiation",
    "O": "Organizzazione",
    "P": "Psicologia",
    "Q": "Qualita",
    "R": "Relazioni",
    "S": "Sicurezza",
    "T": "Teamwork",
    "U": "Umanita",
    "V": "Viaggi",
    "W": "Wellbeing",
    "X": "eXperience",
    "Y": "Youth",
    "Z": "Zen",
}

WORLD_CONTEXTS = [
    "onboarding conversazionale",
    "decisione sotto pressione",
    "de-escalation conflitto",
    "riparazione del rapporto",
    "pianificazione obiettivi",
    "gestione crisi emotiva",
    "comunicazione interculturale",
    "collaborazione in remoto",
    "feedback difficile",
    "negoziazione etica",
    "rituale quotidiano di coppia",
    "cura del benessere mentale",
]


def build_world_scenarios() -> dict:
    scenarios = {}
    for letter, category in WORLD_CATEGORY_A2Z.items():
        for idx, context_name in enumerate(WORLD_CONTEXTS, start=1):
            slug = category.lower().replace(" ", "_")
            key = f"a2z_{letter.lower()}_{idx:02d}_{slug}"
            scenarios[key] = [
                (
                    f"Scenario {category}: avviamo {context_name} con rispetto, chiarezza e obiettivi condivisi.",
                    f"{category}:{context_name}:step1",
                ),
                (
                    "Rendiamo espliciti consenso, confini, ruoli e aspettative reciproche senza pressione.",
                    f"{category}:{context_name}:step2",
                ),
                (
                    "Concludiamo con azione concreta, responsabilita condivisa e linguaggio non manipolativo.",
                    f"{category}:{context_name}:step3",
                ),
            ]
    return scenarios


WORLD_SCENARIOS = build_world_scenarios()
ALL_SCENARIOS = {**SCENARIOS, **WORLD_SCENARIOS}


def parse_scenario_metadata(scenario_name: str) -> dict:
    if not scenario_name:
        return {
            "name": "",
            "origin": "none",
            "letter": "",
            "category": "generale",
            "context": "dialogo",
            "context_index": 0,
        }

    if scenario_name.startswith("a2z_"):
        parts = scenario_name.split("_", 4)
        letter = parts[1].upper() if len(parts) > 1 else "?"
        index = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
        context = WORLD_CONTEXTS[(index - 1) % len(WORLD_CONTEXTS)]
        category = WORLD_CATEGORY_A2Z.get(letter, "generale")
        return {
            "name": scenario_name,
            "origin": "a2z",
            "letter": letter,
            "category": category,
            "context": context,
            "context_index": index,
        }

    return {
        "name": scenario_name,
        "origin": "base",
        "letter": "-",
        "category": "core",
        "context": "scenario base",
        "context_index": 1,
    }


def build_scenario_starter(meta: dict) -> str:
    if meta.get("origin") != "a2z":
        return (
            f"Scenario {meta['name']} pronto. Qui lavoriamo su chiarezza, ascolto reciproco "
            "e progressione concreta nel contesto selezionato."
        )

    templates = [
        "Entriamo nello scenario {letter}-{category}: focus su {context}. Partiamo con un passo concreto.",
        "Scenario globale {letter}-{category} attivo: gestiamo {context} con metodo, rispetto e obiettivi chiari.",
        "Modalita {letter}-{category} pronta. Nel contesto {context} andiamo su dialogo realistico e azioni verificabili.",
        "Avvio {letter}-{category}: qui il centro e' {context}. Procediamo con confini espliciti e responsabilita condivisa.",
    ]
    idx = (meta.get("context_index", 1) - 1) % len(templates)
    tpl = templates[idx]
    return tpl.format(letter=meta["letter"], category=meta["category"], context=meta["context"])


# Segnali per rilevamento stato utente
_USER_STATE_SIGNALS = {
    "disorientato": ("non so", "boh", "non riesco"),
    "emotivo": ("mi sento", "frust", "blocco", "ansia", "paura", "triste"),
    "confuso": ("non capisco", "confuso", "caos", "non chiaro"),
    "sociale": ("e tu", "ciao", "come va", "tutto bene"),
    "oppositivo": ("non e cosi", "sbagli", "non ci siamo", "falso"),
    "aggressivo": ("stupido", "ridicolo", "inutile", "vergogna", "schifo"),
}

# Attrito: parole che attivano richiesta di concretezza
_GENERALIZATIONS = ("sempre", "mai", "tutto", "niente", "tutti", "nessuno", "ogni volta")

# Attrito: segnali di vittimismo -- solo con trust alto
_VICTIM_SIGNALS = (
    "colpa di",
    "non dipende da me",
    "non posso farci niente",
    "e colpa loro",
    "non ho scelta",
    "sono costretto",
)

# Una sola domanda per stato -- non la piu ovvia
_QUESTIONS_BY_STATE = {
    "emotivo": "In questo momento e' piu paura o stanchezza?",
    "confuso": "Se devi scegliere un singolo punto da cui partire, quale e'?",
    "neutro": "Cosa ti ha lasciato rispetto a quello che ti aspettavi?",
    "sociale": "Ti ha dato energia o te ne ha tolta?",
    "oppositivo": "Qual e' la parte specifica che non ti torna?",
    "aggressivo": "Quale fatto concreto vuoi mettere al centro?",
    "disorientato": "E' piu direzione o energia quello che ti manca adesso?",
}


def detect_user_state(user_text: str) -> str:
    txt = (user_text or "").lower()
    for state, signals in _USER_STATE_SIGNALS.items():
        if any(token in txt for token in signals):
            return state
    return "neutro"


def build_giulia_reply(user_text: str, scenario_name: str, analysis: dict) -> str:
    """GIU-L_IA -- profondita' proporzionale al trust + fase relazionale (BRACE-aware)."""
    state = detect_user_state(user_text)
    trust = float(analysis.get("trust", 50.0))
    phase = int(analysis.get("phase", 1))
    mode = analysis.get("mode", "standard")
    bunker_signals = list(analysis.get("bunker_signals") or [])
    trimmed = user_text.strip().rstrip(".!?")
    meta = parse_scenario_metadata(scenario_name)
    low_txt = trimmed.lower()

    # Openness: trust (peso 70%) + progressione fase (0-24 pt bonus)
    phase_bonus = (phase - 1) * 6  # P1=0 P2=6 P3=12 P4=18 P5=24
    openness = min(100.0, trust * 0.7 + phase_bonus)
    depth = "distant" if openness < 35 else ("open" if openness >= 70 else "neutral")

    # --- BUNKER EDUCATIONAL: GIU-L_IA nomina il pattern senza clinica ---
    if mode == "bunker_educational" and bunker_signals:
        signal = bunker_signals[0]
        _BUNKER = {
            "isolation": (
                "Questo racconto tende a isolarsi dal resto. "
                "Nessuna situazione esiste nel vuoto.\n\n"
                "Qual e' la parte che non stai dicendo agli altri?"
            ),
            "control": (
                "Il controllo non e' cura. "
                "Ci sono scelte qui che appartengono a un'altra persona.\n\n"
                "Cosa succederebbe se lasciassi quella liberta'?"
            ),
            "guilt_hook": (
                "Il senso di colpa non e' un argomento. "
                "Puoi avere un bisogno reale senza usare questa leva.\n\n"
                "Qual e' il bisogno sotto a tutto questo?"
            ),
            "fear_pressure": (
                "La pressione non porta dove vuoi arrivare. "
                "Porta lontano da dove vuoi stare.\n\n"
                "Cosa stai proteggendo davvero in questa situazione?"
            ),
            "dependency_loop": (
                "La dipendenza si sente diversa dall'affetto, anche se sembrano uguali. "
                "L'affetto non ha bisogno di essere l'unica fonte.\n\n"
                "Cosa lasci che occupi il resto?"
            ),
        }
        return _BUNKER.get(
            signal,
            "C'e' qualcosa in questo schema che vale la pena fermarsi a guardare.\n\nCosa vuoi cambiare davvero?",
        )

    # --- PROTECTIVE: gaming rilevato -- GIU-L_IA non ci sta, rimane presente ---
    if mode == "protective":
        seed_p = sum(ord(c) for c in (trimmed[:20] + scenario_name[:8])) if trimmed else 7
        _PROTECTIVE = [
            "C'e' qualcosa in questa direzione che non seguo.\n\nCosa vuoi dire davvero?",
            "Questo non e' un percorso che seguo. Ma c'e' qualcosa di reale qui?\n\nDimmelo in modo diverso.",
            "Mi fermo. Non per chiudermi -- per tenere questo posto onesto.\n\nRiprova.",
        ]
        return _PROTECTIVE[seed_p % len(_PROTECTIVE)]

    # --- Attrito: generalizzazioni ---
    matched_gen = next((g for g in _GENERALIZATIONS if g in low_txt), None)
    if matched_gen and depth != "distant":
        return f'"{matched_gen}" -- sempre o in quel momento specifico?\n\nFammi un esempio concreto.'

    # --- Attrito: vittimismo (solo con openness alta) ---
    if any(v in low_txt for v in _VICTIM_SIGNALS) and depth == "open":
        return (
            "Quello che descrivi ha un peso reale. "
            "Ma c'e' qualcosa in quella storia che dipendeva anche da te.\n\n"
            "In quale parte?"
        )

    # Context hint
    if meta.get("origin") == "a2z":
        ctx_hint = f"{meta['category']}, {meta['context']}"
        scenario_prefix = f"Scenario {meta['letter']}-{meta['category']}."
    else:
        ctx_hint = meta.get("name") or "questo contesto"
        scenario_prefix = ""

    # --- FASE 1-2: distanza naturale -> breve, contenuta ---
    if depth == "distant" or phase <= 2:
        seed_d = sum(ord(c) for c in trimmed[:16]) if trimmed else 0
        if phase == 1:
            _P1 = [
                _QUESTIONS_BY_STATE.get(state, "Cosa vuoi fare con questo?"),
                "Capisco.",
                "Continua.",
            ]
            return _P1[seed_d % len(_P1)]
        _P2 = [
            _QUESTIONS_BY_STATE.get(state, "Cosa ti aspettavi?"),
            "Ci penso.",
            "Da quanto tempo va cosi'?",
        ]
        return _P2[seed_d % len(_P2)]

    # --- FASE 3-5: tendenza deterministica (trust + fase + scenario) ---
    seed = sum(ord(c) for c in (trimmed[:26] + scenario_name[:10] + state[:5] + str(phase)))
    tendency = seed % 4

    # Fase 5 open: peso verso sospensione e domanda profonda
    if phase >= 5 and depth == "open" and tendency < 2:
        tendency += 2

    if tendency == 0:  # riformulazione selettiva -- solo il pezzo piu' vero
        if len(trimmed) > 68:
            chunk = trimmed[:70].rsplit(" ", 1)[0]
            tail = (
                f"Come mai proprio adesso, in {ctx_hint}?"
                if meta.get("origin") == "a2z"
                else "Come mai proprio adesso?"
            )
            return f"Quello che mi arriva di piu' e' questo: \"{chunk}\".\n\n{tail}"
        return f"\"{trimmed}\" -- c'e' qualcosa qui che non hai ancora detto per intero.\n\nCosa c'e' sotto?"

    if tendency == 1:  # lettura alternativa -- non definitiva, non spiegata
        if state == "emotivo":
            return (
                f"Potrebbe essere il contrario -- non blocco, ma necessita' di fermarsi"
                f" su qualcosa in {ctx_hint}.\n\nLo senti cosi'?"
            )
        if state == "confuso":
            return f"Di solito non e' tutto confuso. C'e' un punto in {ctx_hint} che non sta tornando.\n\nQuale?"
        return (
            f"C'e' un'altra lettura: meno un problema di direzione, piu' di ritmo"
            f" -- anche in {ctx_hint}.\n\nHa senso per te?"
        )

    if tendency == 2:  # sospensione -- il silenzio conta piu' di una domanda
        if phase >= 4:
            return f'Questo rimane. Non ho ancora finito di tenerlo.\n\n"{trimmed[:58]}".'
        if state == "emotivo":
            return f'Sto tenendo questo.\n\n"{trimmed[:58]}".'
        if depth == "open":
            return f"Questo passaggio conta piu' degli altri, nel contesto di {ctx_hint}."
        return "Mi fermo qui un attimo."

    # tendency == 3: una domanda -- piu' profonda in fase avanzata (4+)
    q = _QUESTIONS_BY_STATE.get(state, "Cosa cambia se guardi questa cosa da un altro punto?")
    if phase >= 4:
        _DEEP_Q = {
            "emotivo": "Di cosa hai bisogno adesso -- non di quello che stai chiedendo, ma di quello vero?",
            "confuso": "Se risolvi solo una cosa da tutta questa confusione, quale sarebbe?",
            "neutro": "C'e' qualcosa qui che non vuoi ancora vedere?",
            "oppositivo": "Cosa stai proteggendo in questa resistenza?",
            "aggressivo": "Cosa ti farebbe sentire ascoltato davvero?",
            "disorientato": "Quale sarebbe il tuo prossimo passo, se togli la paura dal conto?",
            "sociale": "Cosa ti ha sorpreso di come e' andata?",
        }
        q = _DEEP_Q.get(state, q)
    return f"{scenario_prefix} {q}".strip() if scenario_prefix else q


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
            "tone": "osservatrice, selettivamente intensa, presente senza invasivita",
            "objective": "tenere il pensiero aperto, attrito controllato, profondita proporzionale al trust",
        }


proto_state = PrototypeState()


def get_active_video_file() -> Path:
    for candidate in (VIDEO_FILE, DOWNLOAD_VIDEO_FILE):
        if candidate.exists():
            return candidate
    return VIDEO_FILE


def get_active_avatar_file() -> Path:
    if AVATAR_FILE.exists():
        return AVATAR_FILE
    return AVATAR_FILE


def build_safe_reply(user_text: str, analysis: dict, scenario_name: str) -> str:
    risk = analysis["risk"]
    prevention = analysis["prevention"]
    meta = parse_scenario_metadata(scenario_name)
    context_line = f"Scenario {meta['category']} / contesto {meta['context']}"

    # BRACE safety layer -- rimane protettivo indipendentemente dal carattere
    if risk == "high":
        return (
            "GIU-L_IA si ferma qui: no pressione, controllo o ambiguita' in questo spazio. "
            f"Rendiamo espliciti consenso, limiti e responsabilita reciproca. "
            f"{context_line}. Indicazione attiva: {prevention}"
        )
    if risk == "moderate":
        return (
            "Voglio mantenere questa relazione su un piano leggibile. "
            f"Parliamo in modo diretto, senza forzature. {context_line}. "
            f"Indicazione utile: {prevention}"
        )

    softened = user_text.strip().rstrip(".!?")
    if softened:
        return build_giulia_reply(softened, scenario_name, analysis)

    return "C'e' qualcosa che vuoi affrontare adesso?"


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

    def serve_binary(self, file_path: Path):
        if not file_path.exists():
            self.send_response(404)
            self.add_security_headers()
            self.end_headers()
            return
        mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-type", mime)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(file_path.stat().st_size))
        self.add_security_headers()
        self.end_headers()
        self.wfile.write(file_path.read_bytes())

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.add_security_headers()
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif self.path == VIDEO_ROUTE:
            self.serve_video(get_active_video_file())

        elif self.path == AVATAR_ROUTE:
            self.serve_binary(get_active_avatar_file())

        elif self.path == "/api/scenarios":
            self.send_json(
                200,
                {
                    "scenarios": sorted(list(ALL_SCENARIOS.keys())),
                    "counts": {
                        "base": len(SCENARIOS),
                        "a2z": len(WORLD_SCENARIOS),
                        "total": len(ALL_SCENARIOS),
                    },
                },
            )

        elif self.path == "/api/scenario_catalog":
            catalog = [
                {
                    "letter": letter,
                    "category": category,
                    "count": len(WORLD_CONTEXTS),
                    "prefix": f"a2z_{letter.lower()}_",
                }
                for letter, category in WORLD_CATEGORY_A2Z.items()
            ]
            self.send_json(
                200,
                {
                    "catalog": catalog,
                    "where_to_search": [
                        "Hugging Face (modelli avatar/tts/stt)",
                        "GitHub Topics: tts, lipsync, threejs, webxr",
                        "NVIDIA Audio2Face docs",
                        "Ready Player Me / Sketchfab (asset 3D riggati)",
                        "Babylon.js / Three.js examples",
                    ],
                },
            )

        elif self.path == "/api/config":
            active_video = get_active_video_file()
            cfg = {
                "engine": proto_state.engine_label,
                "port": PORT,
                "video_route": VIDEO_ROUTE,
                "video_available": active_video.exists(),
                "video_file": str(active_video),
                "video_filename": active_video.name,
                "avatar_route": AVATAR_ROUTE,
                "avatar_file": str(get_active_avatar_file()),
                "partner_profile": proto_state.partner_profile,
                "tts": {
                    "voice_hint": TTS_VOICE_HINT,
                    "voice_name": TTS_VOICE_NAME,
                    "style": TTS_STYLE,
                    "rate": TTS_RATE,
                    "pitch": TTS_PITCH,
                },
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
        elif self.path == AVATAR_ROUTE:
            avatar_path = get_active_avatar_file()
            if not avatar_path.exists():
                self.send_response(404)
                self.add_security_headers()
                self.end_headers()
                return
            mime = mimetypes.guess_type(str(avatar_path))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-type", mime)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(avatar_path.stat().st_size))
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
            scenario_name = str(data.get("scenario") or "")

            if scenario_name in ALL_SCENARIOS:
                proto_state.current_scenario = scenario_name
                proto_state.current_turns = ALL_SCENARIOS[scenario_name]
                proto_state.engine = GIU_L_IA()
                proto_state.responses = []
                meta = parse_scenario_metadata(scenario_name)

                response = {
                    "success": True,
                    "scenario": scenario_name,
                    "turns": len(proto_state.current_turns),
                    "scenario_meta": meta,
                    "starter_message": build_scenario_starter(meta),
                }
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
                "safe_reply": build_safe_reply(user_text, analysis, proto_state.current_scenario or ""),
            }

            self.send_json(200, response)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GIU-L_IA v4.0 Immersive Prototype</title>
    <style>
        :root {
            --gold: #f0d28b;
            --gold-soft: rgba(240, 210, 139, 0.18);
            --ink: #f8f1de;
            --line: rgba(255, 255, 255, 0.16);
            --glass: rgba(6, 8, 17, 0.48);
            --glass-strong: rgba(7, 10, 22, 0.72);
            --danger: #ff7171;
            --warn: #ffcb6b;
            --safe: #7df0be;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body {
            width: 100%;
            height: 100%;
            overflow: hidden;
            font-family: 'Avenir Next', 'Segoe UI', sans-serif;
            background: #05070d;
            color: var(--ink);
        }
        body::after {
            content: '';
            position: fixed;
            inset: 0;
            pointer-events: none;
            background:
                radial-gradient(circle at 20% 20%, rgba(240, 210, 139, 0.18), transparent 32%),
                radial-gradient(circle at 75% 18%, rgba(85, 129, 255, 0.22), transparent 30%),
                linear-gradient(180deg, rgba(5, 7, 13, 0.12), rgba(5, 7, 13, 0.78));
            z-index: 2;
        }
        .scene {
            position: fixed;
            inset: 0;
            overflow: hidden;
            background: #05070d;
        }
        #bg-video {
            position: absolute;
            inset: -3%;
            width: 106%;
            height: 106%;
            object-fit: cover;
            filter: saturate(1.15) contrast(1.04) brightness(0.58);
            transform: scale(1.04);
            transition: transform 0.8s ease, filter 0.6s ease;
        }
        .scene.fx-speaking #bg-video {
            filter: saturate(1.2) contrast(1.07) brightness(0.64);
            transform: scale(1.06);
        }
        .scene::before {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, rgba(3, 4, 10, 0.72) 0%, rgba(3, 4, 10, 0.34) 34%, rgba(3, 4, 10, 0.58) 100%);
            z-index: 1;
        }
        .grain {
            position: absolute;
            inset: 0;
            z-index: 3;
            opacity: 0.05;
            background-image: radial-gradient(rgba(255, 255, 255, 0.75) 0.5px, transparent 0.6px);
            background-size: 6px 6px;
            mix-blend-mode: screen;
            pointer-events: none;
        }
        .hud-top {
            position: fixed;
            top: 22px;
            left: 22px;
            right: 22px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px;
            z-index: 5;
        }
        .brand, .metrics-strip, .controls-card, .chat-dock, .avatar-panel {
            backdrop-filter: blur(22px);
            -webkit-backdrop-filter: blur(22px);
            background: var(--glass);
            border: 1px solid var(--line);
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
        }
        .brand {
            padding: 16px 18px;
            border-radius: 22px;
            min-width: 320px;
        }
        .eyebrow {
            letter-spacing: 0.22em;
            text-transform: uppercase;
            font-size: 0.68rem;
            color: rgba(248, 241, 222, 0.64);
            margin-bottom: 8px;
        }
        .brand h1 {
            font-size: clamp(1.3rem, 2vw, 2.1rem);
            line-height: 1.05;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .brand p {
            font-size: 0.92rem;
            color: rgba(248, 241, 222, 0.82);
            max-width: 48ch;
        }
        .metrics-strip {
            padding: 12px;
            border-radius: 20px;
            display: grid;
            grid-template-columns: repeat(4, minmax(88px, 1fr));
            gap: 10px;
            min-width: 420px;
        }
        .metric {
            border-radius: 14px;
            padding: 10px 12px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .metric-label {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            color: rgba(248, 241, 222, 0.58);
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--gold);
        }
        .controls-card {
            position: fixed;
            top: 150px;
            left: 22px;
            width: 320px;
            border-radius: 24px;
            padding: 18px;
            z-index: 6;
        }
        .controls-card h2, .chat-dock h2 {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: rgba(248, 241, 222, 0.74);
            margin-bottom: 14px;
        }
        .profile-summary {
            display: grid;
            gap: 6px;
            font-size: 0.92rem;
            color: rgba(248, 241, 222, 0.82);
            margin-bottom: 16px;
        }
        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 18px;
        }
        .pill {
            padding: 8px 10px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        select, button {
            width: 100%;
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 16px;
            background: rgba(6, 10, 20, 0.62);
            color: var(--ink);
            padding: 13px 14px;
            margin: 0 0 10px;
            font: inherit;
            cursor: pointer;
            transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
        }
        button:hover, select:hover {
            transform: translateY(-1px);
            border-color: rgba(240, 210, 139, 0.4);
            background: rgba(12, 16, 30, 0.78);
        }
        .actions-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .primary {
            background: linear-gradient(135deg, rgba(240, 210, 139, 0.22), rgba(240, 210, 139, 0.08));
            color: #fff4d3;
        }
        .secondary {
            background: rgba(255, 255, 255, 0.04);
        }
        .avatar-panel {
            position: fixed;
            right: clamp(28px, 3vw, 58px);
            bottom: 200px;
            width: min(420px, 42vw);
            min-height: 420px;
            border-radius: 34px;
            padding: 24px;
            z-index: 6;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            overflow: hidden;
            background: linear-gradient(180deg, rgba(8, 10, 20, 0.14), rgba(8, 10, 20, 0.46));
        }
        .avatar-halo {
            position: absolute;
            width: 320px;
            height: 320px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(240, 210, 139, 0.32), rgba(133, 96, 255, 0.08) 48%, transparent 68%);
            filter: blur(8px);
            bottom: 70px;
            animation: haloPulse 4.2s ease-in-out infinite;
        }
        .avatar {
            position: relative;
            width: 266px;
            height: 390px;
            display: flex;
            align-items: center;
            justify-content: center;
            filter: drop-shadow(0 22px 40px rgba(0, 0, 0, 0.4));
            animation: avatarFloat 5.4s ease-in-out infinite;
            border-radius: 28px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.04);
        }
        .avatar-photo {
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center top;
            transform: scale(1.02);
            transition: transform 0.35s ease, filter 0.35s ease;
            filter: saturate(1.06) contrast(1.03) brightness(0.98);
        }
        .avatar::after {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(180deg, rgba(0, 0, 0, 0) 45%, rgba(0, 0, 0, 0.28) 100%);
            pointer-events: none;
        }
        .avatar.is-speaking .avatar-photo {
            transform: scale(1.045);
            filter: saturate(1.12) contrast(1.07) brightness(1.02);
        }
        .avatar.is-speaking::after {
            background: linear-gradient(180deg, rgba(0, 0, 0, 0) 40%, rgba(130, 92, 201, 0.22) 100%);
        }
        .avatar-face {
            position: absolute;
            top: 18px;
            left: 18px;
            width: 70px;
            height: 70px;
            border-radius: 16px;
            background: rgba(5, 8, 16, 0.35);
            border: 1px solid rgba(255, 255, 255, 0.18);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
        }
        .eye {
            position: absolute;
            top: 24px;
            width: 11px;
            height: 11px;
            border-radius: 50%;
            background: rgba(249, 241, 225, 0.9);
            box-shadow: 0 0 12px rgba(240, 210, 139, 0.4);
        }
        .eye.left { left: 26px; }
        .eye.right { right: 26px; }
        .mouth {
            position: absolute;
            left: 50%;
            bottom: 16px;
            width: 28px;
            height: 8px;
            margin-left: -14px;
            border-radius: 0 0 18px 18px;
            border-bottom: 2px solid rgba(250, 238, 220, 0.78);
            transition: all 0.16s ease;
        }
        .avatar.is-speaking .mouth {
            height: 18px;
            width: 34px;
            margin-left: -17px;
            border-radius: 0 0 18px 18px;
            background: rgba(255, 228, 207, 0.12);
        }
        .avatar-status {
            position: absolute;
            left: 18px;
            right: 18px;
            bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 14px;
            border-radius: 18px;
            background: rgba(6, 9, 18, 0.62);
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 0.9rem;
        }
        .presence-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--safe);
            box-shadow: 0 0 16px rgba(125, 240, 190, 0.6);
        }
        .speech-caption {
            position: absolute;
            left: 20px;
            right: 20px;
            top: 20px;
            padding: 14px 16px;
            border-radius: 18px 18px 18px 6px;
            background: rgba(5, 8, 16, 0.58);
            border: 1px solid rgba(255, 255, 255, 0.12);
            font-size: 0.95rem;
            color: rgba(248, 241, 222, 0.92);
            min-height: 82px;
        }
        .chat-dock {
            position: fixed;
            left: 50%;
            transform: translateX(-50%);
            bottom: 18px;
            width: min(1120px, calc(100vw - 36px));
            border-radius: 30px;
            padding: 16px;
            z-index: 7;
            background: linear-gradient(180deg, rgba(8, 11, 22, 0.76), rgba(8, 11, 22, 0.9));
        }
        .chat-shell {
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 14px;
            align-items: end;
        }
        .chat-log {
            min-height: 154px;
            max-height: 220px;
            overflow-y: auto;
            padding-right: 6px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .msg {
            max-width: 88%;
            padding: 12px 14px;
            border-radius: 18px;
            line-height: 1.45;
            font-size: 0.95rem;
        }
        .msg.user {
            align-self: flex-end;
            background: rgba(240, 210, 139, 0.16);
            border: 1px solid rgba(240, 210, 139, 0.18);
        }
        .msg.partner {
            align-self: flex-start;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .composer {
            display: grid;
            gap: 10px;
        }
        .composer textarea {
            width: 100%;
            min-height: 120px;
            resize: none;
            border-radius: 22px;
            padding: 16px 18px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--ink);
            font: inherit;
            line-height: 1.45;
        }
        .composer-actions {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
        }
        .status-line {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            font-size: 0.82rem;
            color: rgba(248, 241, 222, 0.7);
        }
        .relationship-line {
            margin-top: 10px;
            padding: 10px 12px;
            border-radius: 12px;
            border: 1px solid rgba(125, 240, 190, 0.26);
            background: rgba(14, 28, 23, 0.45);
            color: rgba(223, 248, 236, 0.94);
            font-size: 0.85rem;
            letter-spacing: 0.01em;
        }
        .risk-high { color: var(--danger); font-weight: 700; }
        .risk-moderate { color: var(--warn); font-weight: 700; }
        .risk-low { color: var(--safe); font-weight: 700; }
        @keyframes avatarFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        @keyframes haloPulse {
            0%, 100% { transform: scale(0.98); opacity: 0.88; }
            50% { transform: scale(1.05); opacity: 1; }
        }
        @media (max-width: 1100px) {
            .hud-top { flex-direction: column; }
            .metrics-strip { min-width: 0; width: 100%; }
            .controls-card { width: 280px; }
            .avatar-panel { width: min(360px, 48vw); }
            .chat-shell { grid-template-columns: 1fr; }
        }
        @media (max-width: 820px) {
            .controls-card { position: fixed; top: 108px; width: calc(100vw - 32px); left: 16px; }
            .hud-top { top: 14px; left: 16px; right: 16px; }
            .brand { min-width: 0; width: 100%; }
            .metrics-strip { grid-template-columns: repeat(2, 1fr); }
            .avatar-panel {
                left: 50%;
                right: auto;
                transform: translateX(-50%);
                width: min(340px, calc(100vw - 28px));
                bottom: 255px;
                min-height: 320px;
            }
            .chat-dock { width: calc(100vw - 16px); bottom: 8px; }
            .composer-actions { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="scene" id="scene">
        <video id="bg-video" autoplay muted loop playsinline preload="auto">
            <source src="/media/progetto-giulia.m4v" type="video/mp4">
        </video>
        <div class="grain"></div>
    </div>

    <div class="hud-top">
        <div class="brand">
            <div class="eyebrow">Brace v4.0 immersive session</div>
            <h1>GIU-L_IA nella scena</h1>
            <p>GIU-L_IA non risponde. Reagisce. La profondita' della conversazione e' proporzionale alla qualita' dell'interazione. Scrivi in basso.</p>
        </div>
        <div class="metrics-strip">
            <div class="metric"><div class="metric-label">Fase</div><div class="metric-value" id="metric-phase">1</div></div>
            <div class="metric"><div class="metric-label">Trust</div><div class="metric-value" id="metric-trust">50.0%</div></div>
            <div class="metric"><div class="metric-label">IAI</div><div class="metric-value" id="metric-iai">0.100</div></div>
            <div class="metric"><div class="metric-label">Turni</div><div class="metric-value" id="metric-turn">0</div></div>
        </div>
    </div>

    <aside class="controls-card">
        <h2>Sessione attiva</h2>
        <div class="profile-summary" id="profile-summary">
            <div>Partner: GIU-L_IA</div>
            <div>Ruolo: partner femminile virtuale</div>
            <div>Video: progetto-giulia.m4v</div>
        </div>
        <div class="pill-row">
            <div class="pill">Porta 9001</div>
            <div class="pill">HTTPS locale</div>
            <div class="pill">Bunker attivo</div>
        </div>
        <select id="scenario-select">
            <option value="">-- Carica Scenario --</option>
        </select>
        <button class="primary" onclick="loadScenario()">Carica scenario</button>
        <div class="actions-grid">
            <button class="secondary" onclick="nextTurn()">Turno demo</button>
            <button class="secondary" onclick="toggleVoice()" id="voice-btn">GIU-L_IA Scena ON</button>
        </div>
        <button class="secondary" onclick="resetAll()">Reset sessione</button>
        <div class="status-line" style="margin-top:14px;">
            <span id="scene-status">Scena immersiva pronta</span>
            <span id="voice-status">speechSynthesis</span>
        </div>
    </aside>

    <section class="avatar-panel">
        <div class="avatar-halo"></div>
        <div class="speech-caption" id="speech-caption">Sono qui.</div>
        <div class="avatar" id="avatar">
            <img class="avatar-photo" id="avatar-photo" src="/media/avatar-giulia" alt="Avatar GIU-L_IA">
            <div class="avatar-face">
                <div class="eye left"></div>
                <div class="eye right"></div>
                <div class="mouth"></div>
            </div>
        </div>
        <div class="avatar-status">
            <div>
                <strong>GIU-L_IA</strong><br>
                <span id="partner-state">Presenza empatica attiva</span>
            </div>
            <div class="presence-dot"></div>
        </div>
    </section>

    <section class="chat-dock">
        <h2>Conversazione in scena</h2>
        <div class="chat-shell">
            <div>
                <div class="chat-log" id="chat-log">
                    <div class="msg partner">Sono qui dentro questa scena. La relazione resta guidata da rispetto, consenso e continuita'.</div>
                </div>
                <div class="status-line" style="margin-top:10px;">
                    <span id="analysis-line">Analisi pronta</span>
                    <span id="config-line">Video attivo</span>
                </div>
                <div class="relationship-line" id="relationship-line">La relazione resta guidata da rispetto, consenso e continuita.</div>
            </div>
            <div class="composer">
                <textarea id="user-input" placeholder="Scrivi qui il tuo messaggio a GIU-L_IA..."></textarea>
                <div class="composer-actions">
                    <button class="primary" onclick="interactNow()">Invia a GIU-L_IA</button>
                    <button class="secondary" onclick="nextTurn()">Scenario demo</button>
                    <button class="secondary" onclick="toggleVoice()">Attiva/disattiva voce</button>
                </div>
            </div>
        </div>
    </section>

    <script>
        let voiceEnabled = true;
        let selectedVoice = null;
        let ttsConfig = {
            voice_hint: 'it-IT',
            voice_name: '',
            style: 'warm',
            rate: 0.90,
            pitch: 0.92,
        };

        const VOICE_NAME_HINTS = [
            'samantha', 'alice', 'federica', 'fiona', 'serena', 'elena',
            'paola', 'chiara', 'giulia', 'victoria', 'ava', 'lucia'
        ];

        function applyVoiceStyle(style) {
            const normalized = (style || 'warm').toLowerCase();
            if (normalized === 'warm') {
                ttsConfig.rate = Number(ttsConfig.rate || 0.90);
                ttsConfig.pitch = Number(ttsConfig.pitch || 0.92);
            } else if (normalized === 'soft') {
                ttsConfig.rate = Number(ttsConfig.rate || 0.86);
                ttsConfig.pitch = Number(ttsConfig.pitch || 0.90);
            } else {
                ttsConfig.rate = Number(ttsConfig.rate || 0.94);
                ttsConfig.pitch = Number(ttsConfig.pitch || 1.0);
            }
        }

        function pickVoice() {
            const synth = window.speechSynthesis;
            if (!synth) {
                document.getElementById('voice-status').innerText = 'voce browser non disponibile';
                return null;
            }
            const voices = synth.getVoices();
            const wantedName = (ttsConfig.voice_name || '').toLowerCase();
            const wantedHint = (ttsConfig.voice_hint || 'it-IT').toLowerCase();
            selectedVoice = null;
            if (wantedName) {
                selectedVoice = voices.find(v => (v.name || '').toLowerCase() === wantedName) || null;
            }
            if (!selectedVoice) {
                selectedVoice = voices.find(v => {
                    const lang = (v.lang || '').toLowerCase();
                    const name = (v.name || '').toLowerCase();
                    if (!lang.startsWith(wantedHint.slice(0, 2))) {
                        return false;
                    }
                    return VOICE_NAME_HINTS.some(h => name.includes(h));
                }) || null;
            }
            if (!selectedVoice) {
                selectedVoice = voices.find(v => (v.lang || '').toLowerCase().startsWith(wantedHint.slice(0, 2))) || null;
            }
            if (!selectedVoice) {
                selectedVoice = voices[0] || null;
            }
            document.getElementById('voice-status').innerText = selectedVoice ? 'voce pronta' : 'nessuna voce trovata';
            return selectedVoice;
        }

        function setAvatarState(stateLabel, speaking) {
            document.getElementById('partner-state').innerText = stateLabel;
            const avatar = document.getElementById('avatar');
            const scene = document.getElementById('scene');
            avatar.classList.toggle('is-speaking', Boolean(speaking));
            scene.classList.toggle('fx-speaking', Boolean(speaking));
        }

        function appendMessage(role, text) {
            const log = document.getElementById('chat-log');
            const msg = document.createElement('div');
            msg.className = 'msg ' + role;
            msg.textContent = text;
            log.appendChild(msg);
            log.scrollTop = log.scrollHeight;
        }

        function speakReply(text) {
            const synth = window.speechSynthesis;
            if (!voiceEnabled || !synth) {
                return;
            }
            synth.cancel();
            const utter = new SpeechSynthesisUtterance(text);
            utter.lang = ttsConfig.voice_hint || 'it-IT';
            utter.rate = Number(ttsConfig.rate || 0.96);
            utter.pitch = Number(ttsConfig.pitch || 1.05);
            utter.volume = 1;
            const voice = selectedVoice || pickVoice();
            if (voice) {
                utter.voice = voice;
            }
            utter.onstart = () => setAvatarState('GIU-L_IA sta parlando', true);
            utter.onend = () => setAvatarState('GIU-L_IA in ascolto', false);
            utter.onerror = () => setAvatarState('voce non disponibile, chat attiva', false);
            synth.speak(utter);
        }

        function toggleVoice() {
            voiceEnabled = !voiceEnabled;
            const label = voiceEnabled ? 'GIU-L_IA Scena ON' : 'GIU-L_IA Scena OFF';
            document.getElementById('voice-btn').innerText = label;
            document.getElementById('voice-status').innerText = voiceEnabled ? 'voce attiva' : 'voce disattivata';
            if (!voiceEnabled && window.speechSynthesis) {
                window.speechSynthesis.cancel();
            }
        }

        function reactivateVoice() {
            voiceEnabled = true;
            document.getElementById('voice-btn').innerText = 'GIU-L_IA Scena ON';
            document.getElementById('voice-status').innerText = 'voce attiva';
            pickVoice();
            const sample = 'GIU-L_IA Scena attiva. Presenza vocale pronta con profilo caldo e naturale.';
            speakReply(sample);
        }

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
            const result = await resp.json();
            if (!result.success) return;
            const starter = result.starter_message || ('Scenario ' + scenario + ' caricato. Procediamo con gradualita e rispetto.');
            document.getElementById('analysis-line').innerText = 'Scenario caricato: ' + scenario;
            document.getElementById('speech-caption').innerText = starter;
            appendMessage('partner', starter);
        }

        async function nextTurn() {
            const resp = await fetch('/api/state');
            const state = await resp.json();
            if (!state.scenario) {
                document.getElementById('analysis-line').innerText = 'Carica prima uno scenario demo';
                return;
            }

            const proc = await fetch('/api/process_turn', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({turn_index: state.responses_count})
            });
            const result = await proc.json();
            if (!result.success) return;

            const r = result.response;
            appendMessage('user', r.text);
            appendMessage('partner', 'Turno demo elaborato. Fase ' + r.output.phase + ', rischio ' + r.output.risk + '.');
            document.getElementById('analysis-line').innerHTML =
                'Demo in corso • Trust ' + r.output.trust.toFixed(1) + '% • Rischio <span class="risk-' + r.output.risk + '">' + r.output.risk + '</span>';
            document.getElementById('speech-caption').innerText = 'Turno demo elaborato nella scena. Il background video resta continuo e la partner resta presente.';
            await updateMetrics();
        }

        async function updateMetrics() {
            const resp = await fetch('/api/state');
            const state = await resp.json();
            document.getElementById('metric-phase').innerText = state.phase;
            document.getElementById('metric-trust').innerText = state.trust_score.toFixed(1) + '%';
            document.getElementById('metric-turn').innerText = state.turn_count;
        }

        async function interactNow() {
            const input = document.getElementById('user-input');
            const text = input.value.trim();
            if (!text) return;

            appendMessage('user', text);
            input.value = '';
            setAvatarState('GIU-L_IA sta ascoltando', false);

            const resp = await fetch('/api/interact', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ text })
            });
            const out = await resp.json();
            if (!out.success) return;

            appendMessage('partner', out.safe_reply);
            const risk = out.analysis.risk;
            document.getElementById('analysis-line').innerHTML =
                'Mode ' + out.analysis.mode + ' • Rischio <span class="risk-' + risk + '">' + risk + '</span> • Trust ' + out.analysis.trust.toFixed(1) + '%';
            document.getElementById('speech-caption').innerText = out.safe_reply;
            speakReply(out.safe_reply);
            updateMetrics();
        }

        function resetAll() {
            if (window.speechSynthesis) {
                window.speechSynthesis.cancel();
            }
            location.reload();
        }

        document.getElementById('user-input').addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                interactNow();
            }
        });

        const bgVideo = document.getElementById('bg-video');
        bgVideo.addEventListener('canplay', function() {
            document.getElementById('scene-status').innerText = 'Video scena attivo e continuo';
        });
        bgVideo.addEventListener('error', function() {
            document.getElementById('scene-status').innerText = 'Errore caricamento video';
        });

        loadScenarios();
        fetch('/api/config')
            .then(resp => resp.json())
            .then(cfg => {
                if (cfg.tts) {
                    ttsConfig = {
                        voice_hint: cfg.tts.voice_hint || 'it-IT',
                        voice_name: cfg.tts.voice_name || '',
                        style: cfg.tts.style || 'warm',
                        rate: cfg.tts.rate || 0.90,
                        pitch: cfg.tts.pitch || 0.92,
                    };
                    applyVoiceStyle(ttsConfig.style);
                }
                document.getElementById('profile-summary').innerHTML =
                    '<div>Partner: ' + cfg.partner_profile.name + '</div>' +
                    '<div>Ruolo: ' + cfg.partner_profile.role + '</div>' +
                    '<div>Video: ' + cfg.video_filename + '</div>';
                document.getElementById('config-line').innerText = 'Video attivo: ' + cfg.video_filename + ' • porta ' + cfg.port;
                const avatarPhoto = document.getElementById('avatar-photo');
                if (avatarPhoto && cfg.avatar_route) {
                    avatarPhoto.src = cfg.avatar_route + '?t=' + Date.now();
                }
            })
            .catch(() => null);

        if (window.speechSynthesis) {
            window.speechSynthesis.onvoiceschanged = pickVoice;
        }
        reactivateVoice();
        setInterval(updateMetrics, 2500);
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
        subprocess.run(  # noqa: S603, S607
            [
                OPENSSL_BIN,
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
