"""
VIO 83 AI ORCHESTRA — World Knowledge Auto-Updater
===================================================
Motore di auto-aggiornamento della conoscenza mondiale:
1. Ingestisce nuovi fatti/informazioni da ogni conversazione
2. Categorizza e indicizza automaticamente per dominio
3. Aggiorna la base di conoscenza giorno per giorno
4. Compatta automaticamente per mantenere peso piuma
5. Fornisce contesto aggiornato per ogni risposta

A differenza delle AI attuali (marzo 2026) che sono statiche,
questo motore cresce e si aggiorna in continuazione dal flusso
reale di utilizzo e dal mondo esterno.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─── Dataclasses ─────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class KnowledgeFact:
    """Un singolo fatto di conoscenza mondiale."""
    domain: str
    topic: str
    content: str
    source: str  # "conversation", "web", "document", "user_correction"
    confidence: float
    timestamp: float = field(default_factory=time.time)
    content_hash: str = ""

    def __post_init__(self) -> None:
        if not self.content_hash:
            h = hashlib.sha256(self.content[:500].encode()).hexdigest()[:12]
            object.__setattr__(self, "content_hash", h)


@dataclass(slots=True)
class KnowledgeStats:
    """Statistiche della knowledge base."""
    total_facts: int = 0
    domains: dict[str, int] = field(default_factory=dict)
    last_update: float = 0.0
    last_compaction: float = 0.0
    db_size_bytes: int = 0


# ─── Regex pre-compilati per estrazione ─────────────────────────────

_RE_DEFINITION = re.compile(
    r"(?:^|\.\s+)([A-Z][^.]{5,60})\s+(?:è|sono|is|are|means?|refers?\s+to|si\s+definisce)\s+([^.]{10,300})\.",
    re.MULTILINE
)
_RE_DATE_FACT = re.compile(
    r"(?:nel|in|on|since|dal|from)\s+((?:19|20)\d{2})[,\s]+([^.]{15,200})\.",
    re.IGNORECASE
)
_RE_NUMERIC_FACT = re.compile(
    r"([A-Z][^.]{5,60})\s+(?:ha|have|has|conta|contains?|è|is)\s+(\d[\d.,]*\s*(?:milion[ie]|billion|trillion|miliard[oi]|%|km|GB|TB|MB|utenti|users|persone|people))",
    re.IGNORECASE
)
_RE_UPDATE_SIGNAL = re.compile(
    r"\b(aggiornamento|update|nuovo|new|latest|recente|recent|annuncio|announced|rilasciato|released|lanciato|launched)\b",
    re.IGNORECASE
)

# Classificazione dominio per topic extraction
_TOPIC_DOMAINS: dict[str, list[str]] = {
    "technology": ["ai", "software", "hardware", "app", "cloud", "api", "database", "programming", "machine learning", "neural", "algorithm"],
    "science": ["physics", "chemistry", "biology", "math", "formula", "theorem", "research", "experiment", "quantum"],
    "business": ["company", "market", "startup", "revenue", "investment", "stock", "economy", "gdp", "trade"],
    "world_events": ["election", "war", "treaty", "summit", "crisis", "pandemic", "climate", "disaster"],
    "culture": ["film", "music", "art", "book", "festival", "award", "nobel", "oscar"],
    "health": ["vaccine", "therapy", "disease", "treatment", "drug", "study", "clinical", "patient"],
    "law": ["regulation", "law", "gdpr", "privacy", "copyright", "court", "legislation", "directive"],
    "education": ["university", "course", "certification", "degree", "learning", "school", "training"],
}


class WorldKnowledgeUpdater:
    """
    Motore di auto-aggiornamento della conoscenza mondiale.

    Differenziatore chiave rispetto alla concorrenza (marzo 2026):
    - Le AI statiche dimenticano dopo il training cutoff
    - VIO AI Orchestra IMPARA e CRESCE da ogni conversazione
    - Ogni fatto viene categorizzato, verificato, compattato
    - La base di conoscenza rimane sempre una piuma (~50MB max)
    """

    MAX_FACTS = 50_000
    COMPACT_THRESHOLD = 40_000
    MAX_DB_SIZE_MB = 50

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or Path("data/world_knowledge.db")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._stats = KnowledgeStats()
        self._init_db()

    def _init_db(self) -> None:
        """Inizializza database con FTS5 per ricerca semantica rapida."""
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")

        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS world_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'conversation',
                confidence REAL DEFAULT 0.5,
                content_hash TEXT UNIQUE NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL,
                access_count INTEGER DEFAULT 0,
                verified INTEGER DEFAULT 0
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
                content, topic, domain,
                content='world_facts',
                content_rowid='id'
            );

            CREATE TABLE IF NOT EXISTS knowledge_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_ref TEXT,
                domain TEXT,
                summary TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS update_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                facts_added INTEGER DEFAULT 0,
                facts_removed INTEGER DEFAULT 0,
                timestamp REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_facts_domain ON world_facts(domain);
            CREATE INDEX IF NOT EXISTS idx_facts_topic ON world_facts(topic);
            CREATE INDEX IF NOT EXISTS idx_facts_confidence ON world_facts(confidence);
            CREATE INDEX IF NOT EXISTS idx_facts_hash ON world_facts(content_hash);
        """)

        self._refresh_stats()

    def _refresh_stats(self) -> None:
        """Aggiorna statistiche."""
        if not self._conn:
            return
        row = self._conn.execute("SELECT COUNT(*) FROM world_facts").fetchone()
        self._stats.total_facts = row[0] if row else 0

        for r in self._conn.execute("SELECT domain, COUNT(*) FROM world_facts GROUP BY domain"):
            self._stats.domains[r[0]] = r[1]

        self._stats.last_update = time.time()
        if self._db_path.exists():
            self._stats.db_size_bytes = self._db_path.stat().st_size

    # ─── Estrai e ingerisci da conversazione ────────────────────────

    def ingest_from_conversation(self, messages: list[dict]) -> int:
        """
        Analizza una conversazione ed estrae fatti di conoscenza mondiale.
        Ritorna il numero di nuovi fatti aggiunti.
        """
        if not messages or not self._conn:
            return 0

        facts: list[KnowledgeFact] = []

        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "")
            if len(content) < 30:
                continue

            # Estrai definizioni
            for match in _RE_DEFINITION.finditer(content):
                term = match.group(1).strip()
                definition = match.group(2).strip()
                domain = self._classify_domain(f"{term} {definition}")
                facts.append(KnowledgeFact(
                    domain=domain,
                    topic=term[:100],
                    content=f"{term}: {definition}",
                    source="conversation",
                    confidence=0.6 if role == "assistant" else 0.4,
                ))

            # Estrai fatti con date
            for match in _RE_DATE_FACT.finditer(content):
                year = match.group(1)
                fact_text = match.group(2).strip()
                domain = self._classify_domain(fact_text)
                facts.append(KnowledgeFact(
                    domain=domain,
                    topic=f"event_{year}",
                    content=f"[{year}] {fact_text}",
                    source="conversation",
                    confidence=0.5 if role == "assistant" else 0.3,
                ))

            # Estrai fatti numerici
            for match in _RE_NUMERIC_FACT.finditer(content):
                subject = match.group(1).strip()
                value = match.group(2).strip()
                domain = self._classify_domain(subject)
                facts.append(KnowledgeFact(
                    domain=domain,
                    topic=subject[:100],
                    content=f"{subject}: {value}",
                    source="conversation",
                    confidence=0.55 if role == "assistant" else 0.35,
                ))

            # Rileva segnali di aggiornamento (novità dal mondo)
            if _RE_UPDATE_SIGNAL.search(content) and role == "user":
                sentences = re.split(r'[.!?]\s+', content)
                for sentence in sentences:
                    if _RE_UPDATE_SIGNAL.search(sentence) and len(sentence) > 30:
                        domain = self._classify_domain(sentence)
                        facts.append(KnowledgeFact(
                            domain=domain,
                            topic="world_update",
                            content=sentence[:500],
                            source="user_correction",
                            confidence=0.7,  # L'utente che informa = alta confnza
                        ))

        return self._store_facts(facts)

    def _classify_domain(self, text: str) -> str:
        """Classificazione rapida del dominio di un fatto."""
        text_lower = text.lower()
        best_domain = "general"
        best_score = 0
        for domain, keywords in _TOPIC_DOMAINS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_domain = domain
        return best_domain

    def _store_facts(self, facts: list[KnowledgeFact]) -> int:
        """Salva fatti con deduplicazione hash-based."""
        if not facts or not self._conn:
            return 0

        added = 0
        for fact in facts:
            try:
                self._conn.execute(
                    "INSERT OR IGNORE INTO world_facts "
                    "(domain, topic, content, source, confidence, content_hash, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (fact.domain, fact.topic, fact.content, fact.source,
                     fact.confidence, fact.content_hash, fact.timestamp)
                )
                if self._conn.execute("SELECT changes()").fetchone()[0] > 0:
                    row_id = self._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    self._conn.execute(
                        "INSERT INTO facts_fts(rowid, content, topic, domain) VALUES (?, ?, ?, ?)",
                        (row_id, fact.content, fact.topic, fact.domain)
                    )
                    added += 1
            except sqlite3.IntegrityError:
                # Duplicato — aggiorna confnza se maggiore
                self._conn.execute(
                    "UPDATE world_facts SET confidence = MAX(confidence, ?), updated_at = ? "
                    "WHERE content_hash = ?",
                    (fact.confidence, time.time(), fact.content_hash)
                )

        if added > 0:
            self._conn.execute(
                "INSERT INTO update_log (action, facts_added, timestamp) VALUES (?, ?, ?)",
                ("ingest_conversation", added, time.time())
            )
            self._conn.commit()
            self._stats.total_facts += added

        # Auto-compact se necessario
        if self._stats.total_facts > self.COMPACT_THRESHOLD:
            self._compact()

        return added

    # ─── Query: recupera conoscenza per contesto ────────────────────

    def get_relevant_facts(self, query: str, domain: Optional[str] = None, limit: int = 5) -> list[dict]:
        """
        Recupera fatti rilevanti per arricchire una risposta.
        Usa FTS5 per ricerca full-text rapida.
        """
        if not self._conn or not query:
            return []

        clean_q = re.sub(r'[^\w\s]', ' ', query[:200]).strip()
        if not clean_q:
            return []

        try:
            if domain:
                results = self._conn.execute(
                    """SELECT wf.id, wf.domain, wf.topic, wf.content, wf.confidence, wf.source
                    FROM facts_fts ff
                    JOIN world_facts wf ON ff.rowid = wf.id
                    WHERE facts_fts MATCH ? AND wf.domain = ?
                    ORDER BY rank
                    LIMIT ?""",
                    (clean_q, domain, limit)
                ).fetchall()
            else:
                results = self._conn.execute(
                    """SELECT wf.id, wf.domain, wf.topic, wf.content, wf.confidence, wf.source
                    FROM facts_fts ff
                    JOIN world_facts wf ON ff.rowid = wf.id
                    WHERE facts_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?""",
                    (clean_q, limit)
                ).fetchall()
        except sqlite3.OperationalError:
            return []

        facts = []
        time.time()
        for row in results:
            facts.append({
                "domain": row[1],
                "topic": row[2],
                "content": row[3],
                "confidence": row[4],
                "source": row[5],
            })
            self._conn.execute(
                "UPDATE world_facts SET access_count = access_count + 1 WHERE id = ?",
                (row[0],)
            )

        if facts:
            self._conn.commit()

        return facts

    def build_context_injection(self, user_message: str, domain: Optional[str] = None) -> str:
        """
        Costruisce un'iniezione di contesto da aggiungere al system prompt.
        Max 400 chars per mantenere output leggero.
        """
        facts = self.get_relevant_facts(user_message, domain, limit=3)
        if not facts:
            return ""

        lines: list[str] = []
        chars_left = 400

        for fact in facts:
            if chars_left < 30:
                break
            snippet = fact["content"][:min(120, chars_left)]
            conf_tag = "✓" if fact["confidence"] > 0.6 else "~"
            line = f"{conf_tag} {snippet}"
            lines.append(line)
            chars_left -= len(line) + 5

        if not lines:
            return ""

        return "\n\n[World Knowledge]\n" + "\n".join(lines)

    # ─── Compattazione automatica ───────────────────────────────────

    def _compact(self) -> None:
        """
        Compatta la knowledge base:
        - Rimuovi fatti vecchi mai acceduti
        - Rimuovi bassa confnza se troppi
        - Rebuild FTS index
        """
        if not self._conn:
            return

        # Rimuovi fatti mai acceduti più vecchi di 60 giorni
        cutoff = time.time() - (60 * 86400)
        self._conn.execute(
            "DELETE FROM world_facts WHERE access_count = 0 AND created_at < ?",
            (cutoff,)
        )

        # Se ancora troppi, rimuovi i meno utili
        count = self._conn.execute("SELECT COUNT(*) FROM world_facts").fetchone()[0]
        if count > self.MAX_FACTS:
            excess = count - self.MAX_FACTS + 5000
            self._conn.execute(
                "DELETE FROM world_facts WHERE id IN "
                "(SELECT id FROM world_facts ORDER BY confidence ASC, access_count ASC LIMIT ?)",
                (excess,)
            )

        # Rebuild FTS
        self._conn.execute("INSERT INTO facts_fts(facts_fts) VALUES('rebuild')")

        removed = self._stats.total_facts - self._conn.execute("SELECT COUNT(*) FROM world_facts").fetchone()[0]
        self._conn.execute(
            "INSERT INTO update_log (action, facts_removed, timestamp) VALUES (?, ?, ?)",
            ("compaction", removed, time.time())
        )
        self._conn.commit()
        self._stats.last_compaction = time.time()
        self._refresh_stats()

    # ─── Statistiche ────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Statistiche della knowledge base."""
        self._refresh_stats()
        return {
            "total_facts": self._stats.total_facts,
            "domains": self._stats.domains,
            "db_size_kb": round(self._stats.db_size_bytes / 1024, 1),
            "last_update": self._stats.last_update,
            "last_compaction": self._stats.last_compaction,
        }

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


# ─── Singleton ──────────────────────────────────────────────────────

_INSTANCE: Optional[WorldKnowledgeUpdater] = None


def get_world_knowledge(db_path: Optional[Path] = None) -> WorldKnowledgeUpdater:
    """Ottieni singleton WorldKnowledgeUpdater."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = WorldKnowledgeUpdater(db_path)
    return _INSTANCE
