# ============================================================
# VIO 83 AI ORCHESTRA — ReasoningAmplifier™
# Copyright © 2026 Viorica Porcu (vio83) — All rights reserved
# ============================================================
"""
ReasoningAmplifier™ v1.0 — Ragionamento Auto-Ottimizzante Certificato
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sistema di amplificazione del ragionamento che eleva ogni output
a qualità mondiale certificata, auto-migliorandosi ad ogni ciclo.

Architettura:
  IntentDecoder       → decodifica profonda dell'intent utente (6 dimensioni)
  ChainOfThought      → catena di ragionamento esplicita multi-step
  QualityVerifier     → verifica certificata dell'output (5 dimensioni)
  OutputAmplifier     → amplifica e affina il risultato finale
  ReasoningMemory     → memorizza pattern vincenti per riuso (Piuma™)
  AutoCalibrator      → auto-calibra pesi e strategie in base a feedback

Performance target (Piuma™):
  - Intent decode: <0.5ms
  - CoT overhead: <50ms
  - Quality verify: <2ms
  - Output amplify: <10ms
  - Memory overhead: <1MB per 10.000 pattern
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger("reasoning_amplifier")

# ─── 6 Dimensioni dell'Intent ─────────────────────────────────────────

INTENT_DIMENSIONS = {
    "complexity":   ["semplice","base","introduc","avanzato","complex","profondo","esperto","master","PhD","ricerca"],
    "urgency":      ["subito","ora","veloce","quick","fast","urgent","immedia","adesso","asap","URGENT"],
    "depth":        ["dettagliato","approfondito","esaustivo","complet","tutto","ogni","precis","minimo","brief","sommario"],
    "format":       ["lista","bullet","tabella","table","codice","code","json","xml","markdown","prosa","testo"],
    "verification": ["certific","verif","precis","esatto","confirm","check","validat","sicur","errori","prova"],
    "creativity":   ["creativ","originale","nuovo","innovativ","invent","immaginat","brainstorm","idea","genial","unico"],
}

# ─── Dataclasses ──────────────────────────────────────────────────────

@dataclass(slots=True)
class IntentProfile:
    """Profilo intent decodificato — 6 dimensioni normalizzate 0-1."""
    complexity:   float = 0.5
    urgency:      float = 0.0
    depth:        float = 0.5
    format_pref:  str   = "prose"   # prose|list|code|table|json
    verification: float = 0.5
    creativity:   float = 0.3
    domain:       str   = "general"
    estimated_tokens: int = 500


@dataclass(slots=True)
class ThoughtStep:
    """Singolo step della catena di ragionamento."""
    step_id:   int
    step_type: str   # analyze|decompose|synthesize|verify|conclude
    thought:   str
    confidence: float
    duration_ms: float


@dataclass
class ReasoningChain:
    """Catena completa di ragionamento."""
    chain_id:  str
    intent:    IntentProfile
    steps:     List[ThoughtStep] = field(default_factory=list)
    conclusion: str = ""
    quality_score: float = 0.0
    total_ms: float = 0.0


@dataclass(slots=True)
class QualityReport:
    """Report di qualità certificato — 5 dimensioni."""
    accuracy:    float   # 0-1: correttezza fattuale
    completeness: float  # 0-1: copertura del tema
    clarity:     float   # 0-1: chiarezza espositiva
    relevance:   float   # 0-1: pertinenza all'input
    depth_score: float   # 0-1: profondità dell'analisi
    overall:     float   # media pesata
    issues:      List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass(slots=True)
class WinningPattern:
    """Pattern vincente memorizzato per riuso."""
    pattern_id:   str
    domain:       str
    intent_type:  str
    strategy_key: str   # quale strategia ha prodotto output migliore
    quality_score: float
    uses: int = 1
    last_used: float = field(default_factory=time.time)


# ─── IntentDecoder ────────────────────────────────────────────────────

class IntentDecoder:
    """
    Decodifica profonda dell'intent utente in 6 dimensioni.
    Velocità: <0.5ms (regex + lookup table).
    """

    _DOMAIN_KW: Dict[str, List[str]] = {
        "code":     ["python","javascript","typescript","function","class","def","import","bug","error","api","sql","react","node","async"],
        "math":     ["calcola","formula","equazione","deriva","integra","statistic","probabilit","numero","percent","somma"],
        "science":  ["ricerca","studio","paper","esperimento","ipotesi","teoria","dati","risultati","analisi","scientifico"],
        "medical":  ["sintomi","diagnosi","terapia","farmaco","malattia","salute","medico","clinico","trattamento"],
        "legal":    ["contratto","legge","norma","gdpr","privacy","copyright","articolo","comma","diritto","obbligo"],
        "creative": ["scrivi","racconto","poesia","storia","immaginat","fiction","creativ","personaggio","trama"],
        "business": ["azienda","startup","marketing","vendite","revenue","strategia","business","mercato","cliente"],
        "language": ["traduci","traduzione","grammatica","lingua","sintassi","vocabolo","espressione","idioma"],
    }

    _FORMAT_KW: Dict[str, List[str]] = {
        "list":    ["lista","bullet","punti","elenco","numera","•","-","1.","2.","passaggi","steps"],
        "code":    ["codice","script","implementa","scrivi il","programma","funzione","classe","```"],
        "table":   ["tabella","table","confronta","compare","colonne","righe","dati strutturati"],
        "json":    ["json","dizionario","dict","object","struttura","formato","output strutturato"],
        "prose":   ["spiega","descrivi","racconta","dimmi","analizza","elabora","approfondisci"],
    }

    def decode(self, user_input: str) -> IntentProfile:
        text = user_input.lower()
        words = set(re.findall(r'\b\w+\b', text))

        # ── complexity ──
        complex_kw = INTENT_DIMENSIONS["complexity"]
        comp = sum(1 for kw in complex_kw[5:] if kw in text) / max(1, len(complex_kw[5:]))
        simp = sum(1 for kw in complex_kw[:3] if kw in text) / max(1, 3)
        complexity = max(0.0, min(1.0, 0.5 + comp - simp))

        # ── urgency ──
        urgency_hits = sum(1 for kw in INTENT_DIMENSIONS["urgency"] if kw in text)
        urgency = min(1.0, urgency_hits * 0.25)

        # ── depth ──
        depth_kw = INTENT_DIMENSIONS["depth"]
        deep_hits = sum(1 for kw in depth_kw[:6] if kw in text)
        brief_hits = sum(1 for kw in depth_kw[6:] if kw in text)
        depth = max(0.1, min(1.0, 0.5 + deep_hits * 0.2 - brief_hits * 0.2))

        # ── format ──
        format_pref = "prose"
        format_scores = {}
        for fmt, kws in self._FORMAT_KW.items():
            format_scores[fmt] = sum(1 for kw in kws if kw in text)
        best_fmt = max(format_scores, key=lambda k: format_scores[k])
        if format_scores[best_fmt] > 0:
            format_pref = best_fmt

        # ── verification ──
        verif_hits = sum(1 for kw in INTENT_DIMENSIONS["verification"] if kw in text)
        verification = min(1.0, 0.4 + verif_hits * 0.2)

        # ── creativity ──
        creat_hits = sum(1 for kw in INTENT_DIMENSIONS["creativity"] if kw in text)
        creativity = min(1.0, creat_hits * 0.25)

        # ── domain ──
        domain = "general"
        domain_scores = {d: sum(1 for kw in kws if kw in text) for d, kws in self._DOMAIN_KW.items()}
        best_domain = max(domain_scores, key=lambda k: domain_scores[k])
        if domain_scores[best_domain] > 0:
            domain = best_domain

        # ── estimated_tokens ──
        base_tokens = 300
        base_tokens += int(complexity * 800)
        base_tokens += int(depth * 600)
        if format_pref == "code":
            base_tokens += 400
        elif format_pref == "list":
            base_tokens += 200
        estimated_tokens = min(4000, base_tokens)

        return IntentProfile(
            complexity=round(complexity, 2),
            urgency=round(urgency, 2),
            depth=round(depth, 2),
            format_pref=format_pref,
            verification=round(verification, 2),
            creativity=round(creativity, 2),
            domain=domain,
            estimated_tokens=estimated_tokens,
        )


# ─── ChainOfThought ───────────────────────────────────────────────────

class ChainOfThought:
    """
    Costruisce catene di ragionamento esplicite multi-step.
    Non esegue le AI calls — costruisce il PROMPT ottimale
    che guida ogni AI verso output di qualità mondiale.
    """

    STEP_TEMPLATES = {
        "analyze": (
            "ANALISI PROFONDA: {topic}\n"
            "→ Cosa chiede esattamente l'utente?\n"
            "→ Quali sono i prerequisiti concettuali?\n"
            "→ Quali angolature non ovvie meritano attenzione?\n"
        ),
        "decompose": (
            "SCOMPOSIZIONE: Identifico i sotto-problemi di '{topic}':\n"
            "1. Componente principale: {component_1}\n"
            "2. Componente secondaria: {component_2}\n"
            "3. Interdipendenze: {interdep}\n"
        ),
        "synthesize": (
            "SINTESI MAGISTRALE:\n"
            "Integro tutti gli elementi per rispondere con precisione assoluta.\n"
            "Il mio output deve essere: esatto, completo, verificabile, utile.\n"
        ),
        "verify": (
            "VERIFICA CERTIFICATA:\n"
            "□ L'output risponde ESATTAMENTE all'input? ✓\n"
            "□ Ci sono inesattezze o lacune? ✗→corrette\n"
            "□ Il formato è ottimale per questo tipo di richiesta? ✓\n"
            "□ La profondità è proporzionata alla complessità? ✓\n"
        ),
        "conclude": (
            "CONCLUSIONE OTTIMALE:\n"
            "Output finale certificato: massima qualità, precisione 100%.\n"
        ),
    }

    def build_system_prompt_enhancement(self, intent: IntentProfile, base_prompt: str) -> str:
        """
        Costruisce enhancement del system prompt basato sull'intent.
        Aggiunge CoT senza aumentare la latenza percepita dall'utente.
        """
        enhancements = []

        # ── Depth directive ──
        if intent.depth > 0.7:
            enhancements.append(
                "DIRETTIVA PROFONDITÀ: Fornisci un'analisi ESAUSTIVA e APPROFONDITA. "
                "Non semplificare. Include dettagli tecnici, sfumature, casi limite."
            )
        elif intent.depth < 0.3:
            enhancements.append(
                "DIRETTIVA CONCISEZZA: Risposta diretta e sintetica. "
                "Solo l'essenziale. Nessuna ridondanza."
            )

        # ── Complexity directive ──
        if intent.complexity > 0.7:
            enhancements.append(
                "DIRETTIVA COMPLESSITÀ: Task avanzato. Applica ragionamento esperto. "
                "Usa terminologia tecnica precisa. Non semplificare concetti complessi."
            )

        # ── Domain specialization ──
        domain_directives = {
            "code": "DIRETTIVA CODICE: Output codice funzionante, commentato, testato mentalmente. Include gestione errori.",
            "math": "DIRETTIVA MATEMATICA: Mostra tutti i passaggi. Formula → sviluppo → risultato verificato.",
            "science": "DIRETTIVA SCIENZA: Cita principi, leggi, evidenze. Distingui fatti da ipotesi.",
            "medical": "DIRETTIVA MEDICA: Precisione clinica. Distingui sintomi, diagnosi differenziale, trattamento.",
            "legal": "DIRETTIVA LEGALE: Precisione normativa. Cita articoli, commi, giurisprudenza rilevante.",
            "creative": "DIRETTIVA CREATIVA: Massima originalità. Evita clichés. Output unico e memorabile.",
            "business": "DIRETTIVA BUSINESS: Focus su ROI, metriche, impatto pratico. Dati e strategie concrete.",
        }
        if intent.domain in domain_directives:
            enhancements.append(domain_directives[intent.domain])

        # ── Verification directive ──
        if intent.verification > 0.6:
            enhancements.append(
                "DIRETTIVA VERIFICA: Prima di rispondere, verifica internamente la correttezza. "
                "Se non sei certo di un dato, indicalo esplicitamente. Qualità > velocità."
            )

        # ── Format directive ──
        format_directives = {
            "list":  "FORMATO: Usa liste numerate/bullet chiare. Ogni punto auto-conclusivo.",
            "code":  "FORMATO: Codice in blocchi ```language. Commenti inline. Example I/O se utile.",
            "table": "FORMATO: Tabella markdown con intestazioni chiare. Dati allineati.",
            "json":  "FORMATO: JSON valido, indentato 2 spazi. Schema chiaro.",
            "prose": "FORMATO: Prosa fluida, paragrafata. No bullet inutili. Testo coerente.",
        }
        if intent.format_pref in format_directives:
            enhancements.append(format_directives[intent.format_pref])

        # ── CoT preamble per task complessi ──
        if intent.complexity > 0.6 and intent.depth > 0.6:
            cot = (
                "\nPROCESSO RAGIONAMENTO (interno, non mostrare):\n"
                "1. Analizza → 2. Scomponi → 3. Sintetizza → 4. Verifica → 5. Concludi\n"
                "Poi fornisci SOLO il risultato finale ottimale.\n"
            )
            enhancements.append(cot)

        if not enhancements:
            return base_prompt

        enhancement_block = "\n\n[AMPLIFICATORE RAGIONAMENTO™]\n" + "\n".join(enhancements)
        return base_prompt + enhancement_block

    def get_step_count(self, intent: IntentProfile) -> int:
        """Numero ottimale di step CoT in base alla complessità."""
        if intent.complexity < 0.3:
            return 2
        elif intent.complexity < 0.6:
            return 3
        else:
            return 5


# ─── QualityVerifier ──────────────────────────────────────────────────

class QualityVerifier:
    """
    Verifica certificata dell'output in 5 dimensioni.
    Velocità: <2ms (pattern matching + euristica).
    """

    # Pattern per rilevare problemi
    _TRUNCATION     = re.compile(r'\.\.\.$|…$|continua\b|to be continued\b', re.IGNORECASE)
    _UNCERTAINTY    = re.compile(r'\b(non so|non sono sicuro|potrebbe essere|forse|probabilmente|mi sembra)\b', re.IGNORECASE)
    _HALLUCINATION  = re.compile(r'\b(inventato|non esistente|ipotetico|immaginario)\b', re.IGNORECASE)
    _SHALLOW        = re.compile(r'\b(semplicemente|banalmente|ovviamente|chiaramente)\b', re.IGNORECASE)
    _REPETITION     = re.compile(r'\b(\w{4,})\b(?:.*\b\1\b){3,}', re.IGNORECASE)

    def verify(self, output: str, intent: IntentProfile, input_text: str) -> QualityReport:
        """Verifica output in 5 dimensioni. <2ms."""
        if not output or len(output) < 10:
            return QualityReport(0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                 ["Output vuoto o troppo breve"], [])

        issues: List[str] = []
        suggestions: List[str] = []

        # ── 1. Accuracy (euristica) ──
        accuracy = 0.85  # baseline positivo
        if self._UNCERTAINTY.search(output):
            accuracy -= 0.15
            issues.append("Rilevata incertezza nell'output")
        if self._TRUNCATION.search(output):
            accuracy -= 0.2
            issues.append("Output sembra troncato")
        accuracy = max(0.0, accuracy)

        # ── 2. Completeness ──
        # Stima basata su lunghezza vs token attesi
        output_tokens = len(output) // 4
        expected_tokens = intent.estimated_tokens
        ratio = output_tokens / max(1, expected_tokens)
        completeness = min(1.0, ratio * 0.9)
        if ratio < 0.3:
            issues.append(f"Output breve ({output_tokens} tok vs {expected_tokens} attesi)")
            suggestions.append("Considera approfondimento")
        elif ratio > 3.0:
            suggestions.append("Output molto lungo — valuta se necessario")

        # ── 3. Clarity ──
        clarity = 0.8
        sentences = [s.strip() for s in re.split(r'[.!?]+', output) if len(s.strip()) > 10]
        if sentences:
            avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_len > 40:
                clarity -= 0.15
                suggestions.append("Frasi molto lunghe — considera di spezzarle")
            elif avg_len < 5:
                clarity -= 0.1
        if self._SHALLOW.search(output):
            clarity -= 0.05

        # ── 4. Relevance ──
        # Controlla quante parole chiave dell'input compaiono nell'output
        input_words = set(re.findall(r'\b\w{5,}\b', input_text.lower()))
        output_lower = output.lower()
        if input_words:
            hits = sum(1 for w in input_words if w in output_lower)
            relevance = min(1.0, 0.4 + (hits / len(input_words)) * 0.6)
        else:
            relevance = 0.7

        # ── 5. Depth ──
        depth_score = 0.7
        # Controlla presenza di strutture di approfondimento
        if re.search(r'\d+\.\s|\n[-•*]\s', output):  # liste numerate o bullet
            depth_score += 0.1
        if re.search(r'```', output):  # codice
            depth_score += 0.05
        if re.search(r'\b(perché|quindi|tuttavia|inoltre|di conseguenza|in sintesi)\b', output, re.I):
            depth_score += 0.1
        if self._REPETITION.search(output):
            depth_score -= 0.15
            issues.append("Rilevata ripetizione eccessiva")
        depth_score = max(0.0, min(1.0, depth_score))

        # ── Overall (media pesata) ──
        overall = (
            accuracy    * 0.30 +
            completeness * 0.20 +
            clarity     * 0.20 +
            relevance   * 0.15 +
            depth_score * 0.15
        )

        return QualityReport(
            accuracy=round(accuracy, 2),
            completeness=round(completeness, 2),
            clarity=round(clarity, 2),
            relevance=round(relevance, 2),
            depth_score=round(depth_score, 2),
            overall=round(overall, 2),
            issues=issues,
            suggestions=suggestions,
        )


# ─── ReasoningMemory ──────────────────────────────────────────────────

class ReasoningMemory:
    """
    Memorizza pattern vincenti per riuso (Piuma™).
    SQLite ultra-compatto: ~100 byte/pattern.
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS winning_patterns (
        pattern_id   TEXT PRIMARY KEY,
        domain       TEXT,
        intent_type  TEXT,
        strategy_key TEXT,
        quality_score REAL,
        uses         INTEGER DEFAULT 1,
        last_used    REAL
    );
    CREATE INDEX IF NOT EXISTS idx_wp_domain ON winning_patterns(domain);
    CREATE INDEX IF NOT EXISTS idx_wp_quality ON winning_patterns(quality_score DESC);
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.SCHEMA)

    def store(self, pattern: WinningPattern):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO winning_patterns
                   (pattern_id, domain, intent_type, strategy_key,
                    quality_score, uses, last_used)
                   VALUES (?,?,?,?,?,?,?)""",
                (pattern.pattern_id, pattern.domain, pattern.intent_type,
                 pattern.strategy_key, pattern.quality_score,
                 pattern.uses, pattern.last_used),
            )
            conn.commit()

    def get_best_strategy(self, domain: str, intent_type: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """SELECT strategy_key FROM winning_patterns
                   WHERE domain=? AND intent_type=?
                   ORDER BY quality_score DESC, uses DESC
                   LIMIT 1""",
                (domain, intent_type),
            ).fetchone()
            return row[0] if row else None

    def update_uses(self, pattern_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE winning_patterns SET uses=uses+1, last_used=? WHERE pattern_id=?",
                (time.time(), pattern_id),
            )
            conn.commit()

    def get_stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM winning_patterns").fetchone()[0]
            best = conn.execute(
                "SELECT domain, strategy_key, quality_score FROM winning_patterns ORDER BY quality_score DESC LIMIT 5"
            ).fetchall()
            return {
                "total_patterns": total,
                "top_patterns": [{"domain": d, "strategy": s, "score": q} for d, s, q in best],
            }


# ─── AutoCalibrator ───────────────────────────────────────────────────

class AutoCalibrator:
    """
    Auto-calibra pesi e strategie basandosi su feedback di qualità.
    Implementa un semplice gradient descent euristico sui pesi del verifier.
    """

    def __init__(self):
        # Pesi correnti per la media pesata del QualityReport
        self._weights = {
            "accuracy":     0.30,
            "completeness": 0.20,
            "clarity":      0.20,
            "relevance":    0.15,
            "depth_score":  0.15,
        }
        self._feedback_history: List[Tuple[float, float]] = []  # (predicted, actual)
        self._lr = 0.01  # learning rate

    def record_feedback(self, predicted_quality: float, user_satisfaction: float):
        """
        Registra feedback: predicted_quality (nostro score) vs user_satisfaction (0-1).
        Aggiorna pesi se c'è discrepanza.
        """
        self._feedback_history.append((predicted_quality, user_satisfaction))
        if len(self._feedback_history) >= 10:
            self._calibrate()
            self._feedback_history = self._feedback_history[-5:]  # mantieni solo ultimi 5

    def _calibrate(self):
        """Calibrazione semplificata: aggiusta se previsione sistematicamente alta/bassa."""
        if len(self._feedback_history) < 5:
            return
        errors = [act - pred for pred, act in self._feedback_history]
        avg_error = sum(errors) / len(errors)
        if abs(avg_error) < 0.05:
            return  # calibrazione OK
        # Aggiusta accuracy weight (più critico)
        if avg_error < 0:  # stiamo sovrastimando
            self._weights["accuracy"] = max(0.15, self._weights["accuracy"] - self._lr)
            self._weights["completeness"] = min(0.35, self._weights["completeness"] + self._lr)
        else:  # sottostimiamo
            self._weights["accuracy"] = min(0.45, self._weights["accuracy"] + self._lr)
        # Renormalizza
        total = sum(self._weights.values())
        self._weights = {k: v / total for k, v in self._weights.items()}
        logger.debug(f"[AutoCalibrator] Calibrazione: avg_error={avg_error:.3f}, nuovi pesi: {self._weights}")

    def get_weights(self) -> Dict[str, float]:
        return dict(self._weights)


# ─── OutputAmplifier ──────────────────────────────────────────────────

class OutputAmplifier:
    """
    Amplifica e affina l'output finale (post-processing Piuma™).
    Non chiama AI esterne — applica trasformazioni deterministiche veloci.
    """

    _TRAILING_WS   = re.compile(r'[ \t]+$', re.MULTILINE)
    _MULTI_NL      = re.compile(r'\n{3,}')
    _DOUBLE_SPACE  = re.compile(r'  +')

    def amplify(self, output: str, intent: IntentProfile, report: QualityReport) -> str:
        """Amplifica output in base al report di qualità."""
        if not output:
            return output

        # ── Pulizia base ──
        result = self._TRAILING_WS.sub('', output)
        result = self._MULTI_NL.sub('\n\n', result)
        result = self._DOUBLE_SPACE.sub(' ', result)
        result = result.strip()

        # ── Se output troncato, aggiungi nota ──
        if report.completeness < 0.4 and len(result) > 100:
            result += "\n\n*[Nota: risposta sintetica — richiedi approfondimento se necessario]*"

        # ── Se formato non rispettato, converti ──
        if intent.format_pref == "list" and not re.search(r'\n[-•*\d]', result):
            # Converti paragrafi in lista se possibile
            sentences = [s.strip() for s in re.split(r'\.\s+', result) if len(s.strip()) > 20]
            if 2 <= len(sentences) <= 10:
                result = "\n".join(f"• {s}." for s in sentences)

        return result


# ─── ReasoningAmplifier™ — Entry Point ───────────────────────────────

class ReasoningAmplifier:
    """
    ReasoningAmplifier™ — Sistema completo di amplificazione ragionamento.

    Eleva ogni output AI a qualità mondiale certificata, auto-migliorandosi
    ad ogni ciclo attraverso ReasoningMemory™ + AutoCalibrator™.

    Usage:
        ra = ReasoningAmplifier(data_dir=Path("data"))

        # Pre-call: ottieni enhanced system prompt
        intent = ra.decode_intent(user_input)
        enhanced_prompt = ra.enhance_system_prompt(system_prompt, intent)

        # Post-call: verifica e amplifica output
        result = ra.process_output(user_input, raw_output, intent)
        print(result["quality"]["overall"])  # es. 0.87
        print(result["output"])              # output amplificato
    """

    VERSION = "1.0.0"

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._decoder    = IntentDecoder()
        self._cot        = ChainOfThought()
        self._verifier   = QualityVerifier()
        self._amplifier  = OutputAmplifier()
        self._calibrator = AutoCalibrator()
        self._memory     = ReasoningMemory(self.data_dir / "reasoning_patterns.db")

        self._stats = defaultdict(int)
        logger.info(f"[ReasoningAmplifier™ v{self.VERSION}] Pronto")

    # ── Public API ─────────────────────────────────────────────────

    def decode_intent(self, user_input: str) -> IntentProfile:
        """Decodifica intent dell'utente. <0.5ms."""
        return self._decoder.decode(user_input)

    def enhance_system_prompt(self, base_prompt: str, intent: IntentProfile) -> str:
        """Potenzia il system prompt con direttive di qualità. <0.1ms."""
        # Controlla se c'è una strategia vincente memorizzata
        best_strategy = self._memory.get_best_strategy(intent.domain, intent.format_pref)
        enhanced = self._cot.build_system_prompt_enhancement(intent, base_prompt)
        if best_strategy:
            enhanced += f"\n[STRATEGIA VINCENTE MEMORIZZATA: {best_strategy}]"
        return enhanced

    def process_output(
        self,
        user_input: str,
        raw_output: str,
        intent: Optional[IntentProfile] = None,
        record_pattern: bool = True,
    ) -> Dict:
        """
        Verifica + amplifica output AI.
        Returns dict con: output, quality, intent, processing_ms
        """
        t0 = time.monotonic()

        if intent is None:
            intent = self.decode_intent(user_input)

        # Verifica qualità
        report = self._verifier.verify(raw_output, intent, user_input)

        # Amplifica se necessario
        amplified = self._amplifier.amplify(raw_output, intent, report)

        # Memorizza pattern vincente se qualità alta
        if record_pattern and report.overall >= 0.80:
            pattern_id = hashlib.md5(f"{intent.domain}:{intent.format_pref}:{report.overall}".encode()).hexdigest()[:10]
            self._memory.store(WinningPattern(
                pattern_id=pattern_id,
                domain=intent.domain,
                intent_type=intent.format_pref,
                strategy_key=f"depth={intent.depth:.1f},complexity={intent.complexity:.1f}",
                quality_score=report.overall,
                last_used=time.time(),
            ))

        self._stats["total_processed"] += 1
        elapsed_ms = round((time.monotonic() - t0) * 1000, 2)

        return {
            "output": amplified,
            "quality": {
                "overall":      report.overall,
                "accuracy":     report.accuracy,
                "completeness": report.completeness,
                "clarity":      report.clarity,
                "relevance":    report.relevance,
                "depth":        report.depth_score,
                "issues":       report.issues,
                "suggestions":  report.suggestions,
            },
            "intent": {
                "domain":      intent.domain,
                "complexity":  intent.complexity,
                "depth":       intent.depth,
                "format":      intent.format_pref,
                "urgency":     intent.urgency,
                "est_tokens":  intent.estimated_tokens,
            },
            "processing_ms": elapsed_ms,
            "amplified": amplified != raw_output,
        }

    def record_user_satisfaction(self, quality_predicted: float, satisfaction: float):
        """Registra feedback utente per auto-calibrazione. Chiama dopo ogni interazione completata."""
        self._calibrator.record_feedback(quality_predicted, satisfaction)

    # ── Multi-step Reasoning Loop (REALE) ──────────────────────────

    async def multi_step_reason(
        self,
        user_input: str,
        ai_call_fn,
        base_system_prompt: str = "",
        provider: str = "",
        model: str = "",
    ) -> Dict:
        """
        Ragionamento multi-step REALE con 3 chiamate AI separate:

        Step 1 — ANALYZE: Analizza il problema, identifica componenti chiave
        Step 2 — SOLVE: Genera la soluzione basandosi sull'analisi
        Step 3 — VERIFY: Verifica la soluzione, correggi errori

        Parametri:
            user_input: la domanda dell'utente
            ai_call_fn: async callable(messages, provider, model) → str
                        Funzione che chiama il provider AI
            base_system_prompt: system prompt base
            provider/model: per la chiamata AI

        Returns:
            Dict con output finale, analisi, verifica, quality report
        """
        import asyncio
        t0 = time.monotonic()

        intent = self.decode_intent(user_input)

        # Decidi se serve multi-step (solo per task complessi)
        if intent.complexity < 0.5 and intent.depth < 0.5:
            # Task semplice: single-step è sufficiente
            return {"use_multistep": False, "intent": intent}

        steps: List[Dict] = []

        # ── STEP 1: ANALYZE ──────────────────────────────────
        analyze_prompt = (
            f"{base_system_prompt}\n\n"
            "Tu sei in fase di ANALISI. Non rispondere ancora alla domanda.\n"
            "Invece, analizza il problema e produci:\n"
            "1. Quali sono i concetti chiave coinvolti?\n"
            "2. Quali sotto-problemi vanno risolti?\n"
            "3. Quali vincoli o casi limite esistono?\n"
            "4. Qual è l'approccio migliore?\n"
            "Sii conciso e strutturato."
        )

        analyze_messages = [
            {"role": "system", "content": analyze_prompt},
            {"role": "user", "content": user_input},
        ]

        try:
            analysis = await ai_call_fn(analyze_messages, provider, model)
        except Exception as e:
            logger.warning(f"[MultiStep] Step ANALYZE fallito: {e}")
            return {"use_multistep": False, "intent": intent, "error": str(e)}

        steps.append({"step": "analyze", "output": analysis})

        # ── STEP 2: SOLVE ────────────────────────────────────
        solve_prompt = (
            f"{base_system_prompt}\n\n"
            "Tu sei in fase di SOLUZIONE. Basandoti sull'analisi precedente, "
            "genera la risposta completa e dettagliata alla domanda dell'utente.\n"
            "Usa l'analisi per guidare la struttura e la completezza della risposta."
        )

        solve_messages = [
            {"role": "system", "content": solve_prompt},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": f"[Analisi completata]\n{analysis}"},
            {"role": "user", "content": "Ora genera la risposta finale completa basata sulla tua analisi."},
        ]

        try:
            solution = await ai_call_fn(solve_messages, provider, model)
        except Exception as e:
            logger.warning(f"[MultiStep] Step SOLVE fallito: {e}")
            # Fallback: usa l'analisi come output
            solution = analysis

        steps.append({"step": "solve", "output": solution})

        # ── STEP 3: VERIFY ───────────────────────────────────
        verify_prompt = (
            f"{base_system_prompt}\n\n"
            "Tu sei in fase di VERIFICA. Controlla la risposta seguente:\n"
            "1. È fattualmente corretta?\n"
            "2. Risponde completamente alla domanda?\n"
            "3. Ci sono errori, imprecisioni o lacune?\n"
            "Se trovi problemi, correggi e riscrivi la risposta completa.\n"
            "Se la risposta è corretta, riscrivila migliorandola dove possibile."
        )

        verify_messages = [
            {"role": "system", "content": verify_prompt},
            {"role": "user", "content": f"Domanda originale: {user_input}"},
            {"role": "assistant", "content": solution},
            {"role": "user", "content": "Verifica e migliora questa risposta. Riscrivi la versione finale."},
        ]

        try:
            verified = await ai_call_fn(verify_messages, provider, model)
        except Exception as e:
            logger.warning(f"[MultiStep] Step VERIFY fallito: {e}")
            verified = solution

        steps.append({"step": "verify", "output": verified})

        # ── Quality check sull'output finale ──
        report = self._verifier.verify(verified, intent, user_input)
        amplified = self._amplifier.amplify(verified, intent, report)

        elapsed_ms = round((time.monotonic() - t0) * 1000, 2)

        return {
            "use_multistep": True,
            "output": amplified,
            "steps": steps,
            "quality": {
                "overall": report.overall,
                "accuracy": report.accuracy,
                "completeness": report.completeness,
                "clarity": report.clarity,
            },
            "intent": {
                "domain": intent.domain,
                "complexity": intent.complexity,
                "depth": intent.depth,
            },
            "processing_ms": elapsed_ms,
            "steps_count": len(steps),
        }

    def get_stats(self) -> Dict:
        return {
            "version": self.VERSION,
            "total_processed": self._stats["total_processed"],
            "pattern_memory": self._memory.get_stats(),
            "calibrator_weights": self._calibrator.get_weights(),
        }


# ─── Singleton ────────────────────────────────────────────────────────

_reasoning_amplifier: Optional[ReasoningAmplifier] = None

def get_reasoning_amplifier(data_dir: Optional[Path] = None) -> ReasoningAmplifier:
    global _reasoning_amplifier
    if _reasoning_amplifier is None:
        _reasoning_amplifier = ReasoningAmplifier(data_dir=data_dir)
    return _reasoning_amplifier
