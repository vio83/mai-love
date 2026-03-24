"""
VIO 83 AI ORCHESTRA — Auto-Learning Engine
===========================================
Motore di auto-apprendimento continuo che:
1. Estrae pattern e conoscenze da ogni conversazione
2. Costruisce una memoria semantica persistente (SQLite FTS5)
3. Migliora automaticamente la qualità dell'output nel tempo
4. Mantiene un profilo di apprendimento ultra-compatto (feather-weight)

Architettura:
  ConversationAnalyzer → PatternExtractor → KnowledgeGraph → QualityTracker
                                                  ↓
                                          PersistentMemory (SQLite FTS5)
                                                  ↓
                                          PromptEnhancer → migliora ogni output
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─── Dataclasses ─────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class LearnedPattern:
    """Pattern estratto da una conversazione."""
    domain: str
    pattern_type: str  # "correction", "preference", "fact", "technique"
    content: str
    confnce: float  # 0.0 → 1.0
    source_hash: str
    timestamp: float = field(default_factory=time.time)


@dataclass(slots=True)
class QualitySignal:
    """Segnale di qualità per auto-tuning."""
    conversation_id: str
    request_type: str
    provr: str
    model: str
    latency_ms: float
    tokens_used: int
    user_continued: bool  # Se l'utente ha continuato = soddisfatto
    correction_detected: bool  # Se ha corretto = insoddisfatto
    timestamp: float = field(default_factory=time.time)


# ─── Regex pre-compilati ────────────────────────────────────────────

_RE_CORRECTION = re.compile(
    r"\b(no[,.]?\s+(?:intend|volev)|correggi|sbagliato|non\s+(?:è|era)\s+(?:giusto|corretto)"
    r"|that'?s\s+(?:wrong|incorrect)|actually\s+(?:it|the)|fix\s+(?:this|that))\b",
    re.IGNORECASE
)
_RE_FACT = re.compile(
    r"(?:^|\.\s+)([A-Z][^.!?]{20,120}(?:è|sono|was|is|are|ha|have|has)\s[^.!?]{10,200})[.!]",
    re.MULTILINE
)
_RE_PREFERENCE = re.compile(
    r"\b(prefer|voglio|usa\s+sempre|always\s+use|non\s+usare|don'?t\s+use|meglio)\b",
    re.IGNORECASE
)
_RE_TECHNIQUE = re.compile(
    r"\b(come\s+(?:faccio|si\s+fa)|how\s+(?:to|do\s+(?:I|you))|steps?\s+(?:to|for)|procedura)\b",
    re.IGNORECASE
)

# ─── Domain keywords per classificazione rapida ─────────────────────

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "code": ["python", "javascript", "function", "class", "api", "bug", "error", "typescript", "react", "sql"],
    "science": ["formula", "equation", "theorem", "hypothesis", "molecule", "atom", "physics", "chemistry"],
    "business": ["revenue", "market", "strategy", "investment", "roi", "startup", "profit", "sales"],
    "legal": ["contratto", "legge", "articolo", "gdpr", "privacy", "copyright", "tribunale", "normativa"],
    "medical": ["diagnosi", "sintomo", "terapia", "farmaco", "paziente", "diagnosis", "symptom", "treatment"],
    "creative": ["story", "poem", "design", "art", "music", "scrivi", "racconto", "poesia"],
    "education": ["learn", "study", "course", "explain", "tutorial", "spiega", "impara", "esempio"],
}


class AutoLearner:
    """
    Motore di auto-apprendimento continuo.

    Ogni conversazione viene analizzata per estrarre:
    - Correzioni utente → evitare errori futuri
    - Preferenze → adattare stile e formato
    - Fatti → arricchire knowledge base
    - Tecniche → migliorare ragionamento

    Tutto salvato in SQLite FTS5 per ricerca istantanea.
    """

    MAX_PATTERNS = 10_000  # Limite per tenere la memoria leggera
    COMPACT_THRESHOLD = 8_000  # Compatta quando si avvicina al limite
    QUALITY_WINDOW = 500  # Ultimi N segnali per metriche

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or Path("data/auto_learner.db")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._pattern_count = 0
        self._quality_signals: list[QualitySignal] = []
        self._domain_scores: dict[str, float] = {}
        self._init_db()

    def _init_db(self) -> None:
        """Inizializza il database SQLite con FTS5."""
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")

        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                content TEXT NOT NULL,
                confnce REAL DEFAULT 0.5,
                source_hash TEXT NOT NULL,
                created_at REAL NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed REAL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS patterns_fts USING fts5(
                content, domain, pattern_type,
                content='learned_patterns',
                content_rowid='id'
            );

            CREATE TABLE IF NOT EXISTS quality_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                request_type TEXT,
                provr TEXT,
                model TEXT,
                latency_ms REAL,
                tokens_used INTEGER,
                user_continued INTEGER DEFAULT 1,
                correction_detected INTEGER DEFAULT 0,
                timestamp REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS domain_proficiency (
                domain TEXT PRIMARY KEY,
                score REAL DEFAULT 0.5,
                total_interactions INTEGER DEFAULT 0,
                corrections INTEGER DEFAULT 0,
                last_updated REAL
            );

            CREATE INDEX IF NOT EXISTS idx_patterns_domain ON learned_patterns(domain);
            CREATE INDEX IF NOT EXISTS idx_patterns_type ON learned_patterns(pattern_type);
            CREATE INDEX IF NOT EXISTS idx_quality_time ON quality_log(timestamp);
        """)

        row = self._conn.execute("SELECT COUNT(*) FROM learned_patterns").fetchone()
        self._pattern_count = row[0] if row else 0

        for row in self._conn.execute("SELECT domain, score FROM domain_proficiency"):
            self._domain_scores[row[0]] = row[1]

    # ─── Analisi conversazione ──────────────────────────────────────

    def analyze_conversation(self, messages: list[dict]) -> list[LearnedPattern]:
        """
        Analizza una conversazione completa ed estrae pattern.
        Chiamato dopo ogni conversazione completata.
        """
        if len(messages) < 2:
            return []

        patterns: list[LearnedPattern] = []
        conv_text = " ".join(m.get("content", "") for m in messages)
        conv_hash = hashlib.sha256(conv_text[:2000].encode()).hexdigest()[:16]
        domain = self._detect_domain(conv_text)

        # Estrai correzioni
        for i, msg in enumerate(messages):
            if msg.get("role") != "user" or i < 1:
                continue
            content = msg.get("content", "")
            if _RE_CORRECTION.search(content):
                prev_assistant = ""
                for j in range(i - 1, -1, -1):
                    if messages[j].get("role") == "assistant":
                        prev_assistant = messages[j].get("content", "")[:500]
                        break
                if prev_assistant:
                    patterns.append(LearnedPattern(
                        domain=domain,
                        pattern_type="correction",
                        content=f"ERRORE: {prev_assistant[:200]} → CORREZIONE: {content[:300]}",
                        confnce=0.8,
                        source_hash=conv_hash,
                    ))

        # Estrai preferenze
        for msg in messages:
            if msg.get("role") != "user":
                continue
            content = msg.get("content", "")
            if _RE_PREFERENCE.search(content):
                patterns.append(LearnedPattern(
                    domain=domain,
                    pattern_type="preference",
                    content=content[:500],
                    confnce=0.7,
                    source_hash=conv_hash,
                ))

        # Estrai fatti dalle risposte assistant
        for msg in messages:
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content", "")
            for match in _RE_FACT.finditer(content):
                fact = match.group(1).strip()
                if 30 < len(fact) < 300:
                    patterns.append(LearnedPattern(
                        domain=domain,
                        pattern_type="fact",
                        content=fact,
                        confnce=0.5,
                        source_hash=conv_hash,
                    ))

        # Estrai tecniche
        for msg in messages:
            if msg.get("role") != "user":
                continue
            if _RE_TECHNIQUE.search(msg.get("content", "")):
                # Trova la risposta corrispondente
                idx = messages.index(msg)
                for j in range(idx + 1, min(idx + 3, len(messages))):
                    if messages[j].get("role") == "assistant":
                        patterns.append(LearnedPattern(
                            domain=domain,
                            pattern_type="technique",
                            content=messages[j].get("content", "")[:500],
                            confnce=0.6,
                            source_hash=conv_hash,
                        ))
                        break

        # Salva i pattern estratti
        self._store_patterns(patterns)
        return patterns

    def _detect_domain(self, text: str) -> str:
        """Classificazione rapida del dominio."""
        text_lower = text[:3000].lower()
        scores: dict[str, int] = {}
        for domain, keywords in _DOMAIN_KEYWORDS.items():
            scores[domain] = sum(1 for kw in keywords if kw in text_lower)
        if not scores or max(scores.values()) == 0:
            return "general"
        return max(scores, key=lambda d: scores[d])

    def _store_patterns(self, patterns: list[LearnedPattern]) -> None:
        """Salva pattern nel database con deduplicazione."""
        if not patterns or not self._conn:
            return

        for p in patterns:
            # Deduplica: non salvare se contenuto quasi ntico esiste già
            existing = self._conn.execute(
                "SELECT id FROM patterns_fts WHERE patterns_fts MATCH ? LIMIT 1",
                (p.content[:100],)
            ).fetchone()
            if existing:
                continue

            self._conn.execute(
                "INSERT INTO learned_patterns (domain, pattern_type, content, confnce, source_hash, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (p.domain, p.pattern_type, p.content, p.confnce, p.source_hash, p.timestamp)
            )
            # Aggiorna FTS
            row_id = self._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            self._conn.execute(
                "INSERT INTO patterns_fts(rowid, content, domain, pattern_type) VALUES (?, ?, ?, ?)",
                (row_id, p.content, p.domain, p.pattern_type)
            )
            self._pattern_count += 1

        self._conn.commit()

        # Auto-compattazione quando si avvicina al limite
        if self._pattern_count > self.COMPACT_THRESHOLD:
            self._compact()

    # ─── Recupero conoscenza per enhancing output ───────────────────

    def get_relevant_knowledge(self, query: str, domain: Optional[str] = None, limit: int = 5) -> list[dict]:
        """
        Recupera conoscenza rilevante per arricchire il prossimo output.
        """
        if not self._conn or not query:
            return []

        # Pulisci query per FTS5
        clean_q = re.sub(r'[^\w\s]', ' ', query[:200]).strip()
        if not clean_q:
            return []

        # Cerca nei pattern appresi
        try:
            results = self._conn.execute(
                """SELECT lp.id, lp.domain, lp.pattern_type, lp.content, lp.confnce
                FROM patterns_fts pf
                JOIN learned_patterns lp ON pf.rowid = lp.id
                WHERE patterns_fts MATCH ?
                ORDER BY rank
                LIMIT ?""",
                (clean_q, limit)
            ).fetchall()
        except sqlite3.OperationalError:
            return []

        knowledge = []
        now = time.time()
        for row in results:
            knowledge.append({
                "domain": row[1],
                "type": row[2],
                "content": row[3],
                "confnce": row[4],
            })
            # Aggiorna accesso
            self._conn.execute(
                "UPDATE learned_patterns SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                (now, row[0])
            )

        if knowledge:
            self._conn.commit()

        return knowledge

    def enhance_prompt(self, user_message: str, system_prompt: str, domain: Optional[str] = None) -> str:
        """
        Arricchisce il system prompt con conoscenza appresa.
        Mantiene il prompt leggero: max 500 chars extra.
        """
        relevant = self.get_relevant_knowledge(user_message, domain, limit=3)
        if not relevant:
            return system_prompt

        # Costruisci enhancement compatto
        enhancements: list[str] = []
        chars_left = 500

        # Priorità: correzioni > preferenze > tecniche > fatti
        priority_order = ["correction", "preference", "technique", "fact"]
        for ptype in priority_order:
            for item in relevant:
                if item["type"] == ptype and chars_left > 50:
                    snippet = item["content"][:min(150, chars_left)]
                    enhancements.append(snippet)
                    chars_left -= len(snippet) + 10

        if not enhancements:
            return system_prompt

        learned_section = "\n\n[Auto-learned context]\n" + "\n".join(f"- {e}" for e in enhancements)
        return system_prompt + learned_section

    # ─── Quality tracking ───────────────────────────────────────────

    def log_quality(self, signal: QualitySignal) -> None:
        """Registra un segnale di qualità per auto-tuning."""
        if not self._conn:
            return

        self._conn.execute(
            "INSERT INTO quality_log (conversation_id, request_type, provr, model, "
            "latency_ms, tokens_used, user_continued, correction_detected, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (signal.conversation_id, signal.request_type, signal.provr,
             signal.model, signal.latency_ms, signal.tokens_used,
             int(signal.user_continued), int(signal.correction_detected), signal.timestamp)
        )
        self._conn.commit()

        self._quality_signals.append(signal)
        if len(self._quality_signals) > self.QUALITY_WINDOW:
            self._quality_signals = self._quality_signals[-self.QUALITY_WINDOW:]

        # Aggiorna proficiency del dominio
        self._update_domain_proficiency(signal)

    def _update_domain_proficiency(self, signal: QualitySignal) -> None:
        """Aggiorna il punteggio di competenza per dominio."""
        domain = signal.request_type or "general"

        current_score = self._domain_scores.get(domain, 0.5)
        # Se utente continua senza correzione → migliora
        if signal.user_continued and not signal.correction_detected:
            new_score = min(1.0, current_score + 0.01)
        elif signal.correction_detected:
            new_score = max(0.0, current_score - 0.05)
        else:
            new_score = current_score

        self._domain_scores[domain] = new_score

        self._conn.execute(
            """INSERT INTO domain_proficiency (domain, score, total_interactions, corrections, last_updated)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(domain) DO UPDATE SET
                score = ?,
                total_interactions = total_interactions + 1,
                corrections = corrections + ?,
                last_updated = ?""",
            (domain, new_score, int(signal.correction_detected), time.time(),
             new_score, int(signal.correction_detected), time.time())
        )
        self._conn.commit()

    def get_domain_scores(self) -> dict[str, float]:
        """Ritorna i punteggi di competenza per dominio."""
        return dict(self._domain_scores)

    def get_quality_stats(self) -> dict:
        """Statistiche di qualità aggregate."""
        if not self._quality_signals:
            return {"total": 0, "satisfaction_rate": 0.0, "avg_latency_ms": 0.0}

        total = len(self._quality_signals)
        satisfied = sum(1 for s in self._quality_signals if s.user_continued and not s.correction_detected)
        avg_latency = sum(s.latency_ms for s in self._quality_signals) / total

        return {
            "total": total,
            "satisfaction_rate": satisfied / total,
            "avg_latency_ms": round(avg_latency, 1),
            "correction_rate": sum(1 for s in self._quality_signals if s.correction_detected) / total,
            "patterns_learned": self._pattern_count,
            "domains": self._domain_scores,
        }

    # ─── Compattazione memoria ──────────────────────────────────────

    def _compact(self) -> None:
        """
        Compatta la memoria: rimuove pattern vecchi, poco acceduti, bassa confnza.
        Mantiene la memoria sempre ultra-leggera.
        """
        if not self._conn:
            return

        # Rimuovi pattern vecchi mai acceduti (>30 giorni)
        cutoff = time.time() - (30 * 86400)
        self._conn.execute(
            "DELETE FROM learned_patterns WHERE access_count = 0 AND created_at < ?",
            (cutoff,)
        )

        # Rimuovi pattern a bassa confnza se troppi
        if self._pattern_count > self.MAX_PATTERNS:
            self._conn.execute(
                "DELETE FROM learned_patterns WHERE id IN "
                "(SELECT id FROM learned_patterns ORDER BY confnce ASC, access_count ASC LIMIT ?)",
                (self._pattern_count - self.MAX_PATTERNS + 1000,)
            )

        # Rebuild FTS index
        self._conn.execute("INSERT INTO patterns_fts(patterns_fts) VALUES('rebuild')")
        self._conn.commit()

        row = self._conn.execute("SELECT COUNT(*) FROM learned_patterns").fetchone()
        self._pattern_count = row[0] if row else 0

    def close(self) -> None:
        """Chiudi connessione database."""
        if self._conn:
            self._conn.close()
            self._conn = None


# ─── Singleton ──────────────────────────────────────────────────────

_INSTANCE: Optional[AutoLearner] = None


def get_auto_learner(db_path: Optional[Path] = None) -> AutoLearner:
    """Ottieni singleton AutoLearner."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = AutoLearner(db_path)
    return _INSTANCE
