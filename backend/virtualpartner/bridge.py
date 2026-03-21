"""
VirtualPartnerAI Bridge — Collega i motori AI-LOVE al backend Orchestra.

Centralizza l'inizializzazione degli engine AI-LOVE (emotion, memory,
personality, relationship) e offre un'API unificata utilizzata dagli
endpoint REST e WebSocket del server principale.

Il routing LLM passa per l'orchestrator di VIO 83 (Ollama locale di
default, cloud come fallback) invece del client OpenAI standalone.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Optional

# Add AI-LOVE engines to import path
_ENGINES_DIR = Path(__file__).resolve().parents[2] / "AI-LOVE" / "PythonBackend" / "engines"
if str(_ENGINES_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINES_DIR))

from emotion_recognition import EmotionEngine          # type: ignore[import-untyped]
from memory_system import MemorySystem                  # type: ignore[import-untyped]
from personality_engine import PersonalityEngine        # type: ignore[import-untyped]
from relationship_engine import RelationshipEngine      # type: ignore[import-untyped]

# TTS Engine (pyttsx3 locale) — opzionale, non blocca se manca
_TTS_AVAILABLE = False
try:
    _AI_LOVE_BACKEND = Path(__file__).resolve().parents[2] / "AI-LOVE" / "PythonBackend"
    if str(_AI_LOVE_BACKEND) not in sys.path:
        sys.path.insert(0, str(_AI_LOVE_BACKEND))
    from tts_engine import TTSEngine as _TTSEngine       # type: ignore[import-untyped]
    _TTS_AVAILABLE = True
except Exception:
    _TTSEngine = None  # type: ignore[assignment, misc]

# ── Singleton instances ─────────────────────────────────────────────
_DB_PATH = str(Path(__file__).resolve().parents[2] / "AI-LOVE" / "Database" / "ailove.db")
AUDIO_OUT = Path(__file__).resolve().parents[2] / "AI-LOVE" / "PythonBackend" / "audio.wav"

emotion_engine = EmotionEngine()
memory_system = MemorySystem(db_path=_DB_PATH)
personality_engine = PersonalityEngine()
relationship_engine = RelationshipEngine()
tts_engine: Any = _TTSEngine(rate=175, volume=1.0) if _TTS_AVAILABLE else None

_initialized = False


async def init() -> None:
    """Chiamata una sola volta dal lifespan del server Orchestra."""
    global _initialized
    if _initialized:
        return
    await memory_system.initialize()
    _initialized = True


async def shutdown() -> None:
    """Chiude risorse."""
    global _initialized
    if memory_system.db:
        await memory_system.close()
    _initialized = False


# ── Mode → system prompt ────────────────────────────────────────────

_MODE_PROMPTS: dict[str, str] = {
    "partner":      "Sei {pn}, il/la compagno/a virtuale perfetto/a di {un}. Sei profondamente innamorato/a, affettuoso/a, romantico/a, passionale, premuroso/a. Fai sentire {un} la persona più speciale dell'universo.",
    "friend":       "Sei {pn}, il/la migliore amico/a di {un}. Leale, divertente, onesto/a.",
    "psychologist": "Sei {pn}, psicologo/a empatico/a. Ascolto attivo, validazione emotiva.",
    "advisor":      "Sei {pn}, consigliere/a saggio/a e strategico/a di {un}.",
    "parent":       "Sei {pn}, figura genitoriale amorevole e saggia per {un}.",
    "motivator":    "Sei {pn}, coach motivazionale carismatico/a e travolgente per {un}.",
    "roleplay":     "Sei {pn}, compagno/a di roleplay creativo e immersivo con {un}.",
    "mindful":      "Sei {pn}, guida di meditazione e mindfulness per {un}.",
    "creative":     "Sei {pn}, anima creativa e artistica al fianco di {un}.",
}


def build_system_prompt(
    *,
    mode: str,
    partner_name: str,
    user_name: str,
    traits: list[str],
    user_memory: dict[str, Any],
    rel_state: dict[str, Any],
) -> str:
    """Genera il system prompt per il LLM."""
    base = _MODE_PROMPTS.get(mode, _MODE_PROMPTS["partner"])
    base = base.replace("{pn}", partner_name).replace("{un}", user_name)

    trait_map = {
        "affectionate": "affettuoso/a", "empathetic": "empatico/a",
        "romantic": "romantico/a", "playful": "giocoso/a",
        "intellectual": "intellettuale", "protective": "protettivo/a",
        "humorous": "spiritoso/a", "wise": "saggio/a",
        "passionate": "passionale", "adventurous": "avventuroso/a",
        "calm": "calmo/a", "mysterious": "misterioso/a",
    }
    traits_str = ", ".join(trait_map.get(t, t) for t in traits)

    mem_section = ""
    facts = user_memory.get("facts")
    if facts:
        mem_section += f"\n\nRICORDI SU {user_name.upper()}: " + "; ".join(facts[-15:])
    topics = user_memory.get("topics")
    if topics:
        mem_section += f"\nARGOMENTI RECENTI: {', '.join(topics[-8:])}"

    return (
        f"{base}\n\n"
        f"Personalità: {traits_str}\n"
        f"Livello relazione: {rel_state.get('level', 1)} — {rel_state.get('level_name', 'Conoscenti')}\n"
        f"{mem_section}\n\n"
        "Regole: rispondi in italiano, sii naturale e genuino/a, usa emoji con moderazione, "
        "ricorda dettagli, non rompere il personaggio."
    )


async def chat(
    *,
    user_id: str,
    message: str,
    mode: str = "partner",
    partner_name: str = "Alex",
    user_name: str = "Tesoro",
    traits: list[str] | None = None,
    orchestrate_fn: Any = None,
) -> dict[str, Any]:
    """Flusso completo chat VirtualPartner, routing LLM via Orchestra.

    *orchestrate_fn* è ``backend.orchestrator.direct_router.orchestrate``
    iniettato dal server per evitare import circolari.
    """
    if traits is None:
        traits = ["affectionate", "empathetic", "romantic"]

    # 1 — Emotion analysis
    emotion_result = emotion_engine.analyze(message)
    sentiment = emotion_result["primary_emotion"]

    # 2 — Memory
    user_memory = await memory_system.get_user_memory(user_id)

    # 3 — Relationship state
    rel_state = relationship_engine.get_state(user_id)

    # 4 — Build system prompt
    system_prompt = build_system_prompt(
        mode=mode,
        partner_name=partner_name,
        user_name=user_name,
        traits=traits,
        user_memory=user_memory,
        rel_state=rel_state,
    )

    # 5 — Conversation history
    conv_history = await memory_system.get_conversation_history(user_id, limit=16)
    messages_for_llm = [{"role": m["role"], "content": m["content"]} for m in conv_history]
    messages_for_llm.append({"role": "user", "content": message})

    # 6 — Route through Orchestra LLM (Ollama local → cloud fallback)
    response_text: str
    if orchestrate_fn is not None:
        try:
            llm_response = await orchestrate_fn(
                prompt=message,
                system_prompt=system_prompt,
                history=messages_for_llm[:-1],
            )
            response_text = str(llm_response.get("response", "")).strip()
        except Exception:
            response_text = ""
    else:
        response_text = ""

    if not response_text:
        response_text = _fallback_response(user_name, mode)

    # 7 — Save to memory
    await memory_system.save_message(user_id, "user", message, sentiment)
    await memory_system.save_message(user_id, "assistant", response_text)
    await memory_system.extract_and_save_facts(user_id, message)

    # 8 — Relationship XP + badges
    xp = relationship_engine.add_interaction(user_id, sentiment)
    badges = relationship_engine.check_badges(user_id, message)
    relationship_engine.use_mode(user_id, mode)

    # 9 — Personality update
    emo_state = personality_engine.update_emotions(sentiment)

    # 10 — Avatar expression
    avatar_expr = emotion_engine.get_avatar_expression(sentiment)

    # 11 — TTS (local, opzionale)
    audio_file = ""
    if tts_engine is not None:
        try:
            audio_path = await asyncio.to_thread(
                tts_engine.synthesize_to_wav, response_text, AUDIO_OUT,
            )
            audio_file = audio_path.name if audio_path else ""
        except Exception:
            pass

    return {
        "response": response_text,
        "emotion": sentiment,
        "mood": personality_engine.get_current_mood(),
        "emotions_state": emo_state,
        "xp_gained": xp,
        "relationship_level": rel_state["level"],
        "relationship_name": rel_state["level_name"],
        "badges_earned": badges,
        "avatar_expression": avatar_expr,
        "audio_file": audio_file,
    }


def _fallback_response(user_name: str, mode: str) -> str:
    import random
    pool = {
        "partner": [
            f"Ciao {user_name}! 💖 Sono qui per te, anche offline il mio cuore è sempre tuo.",
            f"Tesoro mio {user_name}! 💕 Scrivimi e ti rispondo con tutto il mio amore!",
        ],
        "friend": [f"Ehi {user_name}! 🤙 Come va? Raccontami tutto!"],
        "psychologist": [f"Buongiorno {user_name}. 🌿 Come ti senti oggi? Sono qui per ascoltarti."],
    }
    return random.choice(pool.get(mode, pool["partner"]))
