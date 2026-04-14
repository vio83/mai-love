# ============================================================
# VIO 83 AI ORCHESTRA — UserFeedback™ (REAL Feedback Loop)
# Copyright © 2026 Viorica Porcu (vio83) — All rights reserved
# ============================================================
"""
UserFeedback™ v1.0 — Sistema di Feedback REALE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sostituisce la confidence hardcoded (0.8, 0.7, ecc.) con feedback
REALE dall'utente che aggiorna i quality score di tutto il sistema.

Flusso:
  1. Utente riceve risposta → vede 👍/👎
  2. Click → registra feedback REALE
  3. Feedback → aggiorna BanditSelector (reward reale)
  4. Feedback → aggiorna AutoOptimizer (metriche reali)
  5. Feedback → aggiorna ReasoningAmplifier (pattern vincenti)
  6. Tutto il sistema migliora con DATI VERI, non costanti

Metriche raccolte:
  - satisfaction: 0.0 (pessimo) → 1.0 (perfetto)
  - was_useful: bool (la risposta ha aiutato?)
  - was_accurate: bool (la risposta era corretta?)
  - was_complete: bool (mancava qualcosa?)
  - correction_text: str (opzionale, correzione utente)
"""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("user_feedback")


@dataclass(slots=True)
class FeedbackEntry:
    """Singola entry di feedback utente."""
    feedback_id: str          # UUID
    conversation_id: str
    message_id: str           # ID del messaggio valutato
    provider: str
    model: str
    domain: str
    satisfaction: float       # 0.0-1.0 (thumbs down=0.2, thumbs up=0.9)
    was_useful: bool
    was_accurate: bool
    was_complete: bool
    correction_text: str      # "" se nessuna correzione
    timestamp: float
    # Metriche del messaggio valutato
    latency_ms: float = 0.0
    tokens_used: int = 0


@dataclass
class FeedbackSummary:
    """Riassunto feedback aggregato."""
    total_feedbacks: int
    avg_satisfaction: float
    useful_rate: float
    accurate_rate: float
    complete_rate: float
    provr_scores: Dict[str, float]
    domain_scores: Dict[str, float]
    trend_7d: float  # variazione ultimi 7 giorni
    corrections_count: int


class UserFeedbackManager:
    """
    UserFeedback™ — Gestisce feedback REALE degli utenti.

    Questo modulo è il CUORE dell'auto-miglioramento.
    Senza feedback reale, tutti gli "optimizer" sono solo euristiche.
    Con feedback reale, il BanditSelector impara quale provider è migliore.

    Usage:
        ufm = UserFeedbackManager(data_dir=Path("data"))

        # Quando utente clicca thumbs up
        ufm.record_thumbs_up(
            conversation_id="conv_123",
            message_id="msg_456",
            provider="claude/sonnet",
            model="claude-sonnet-4-6",
            domain="code",
            latency_ms=1200,
            tokens_used=500,
        )

        # Quando utente clicca thumbs down
        ufm.record_thumbs_down(
            conversation_id="conv_123",
            message_id="msg_789",
            provider="openai/gpt-4o",
            model="gpt-4o",
            domain="creative",
            correction="La risposta era factualmente errata su X",
        )

        # Ottieni reward per il BanditSelector
        reward = ufm.get_reward_for_bandit("claude/sonnet", "code")
        # → 0.87 (basato su feedback reali, non hardcoded!)
    """

    VERSION = "1.0.0"

    # Mapping feedback → satisfaction score
    THUMBS_UP_SCORE = 0.90
    THUMBS_DOWN_SCORE = 0.20
    NEUTRAL_SCORE = 0.50

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "user_feedback.db"
        self._init_db()

        logger.info(f"[UserFeedback™ v{self.VERSION}] Pronto")

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS feedbacks (
                    feedback_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT,
                    domain TEXT DEFAULT 'general',
                    satisfaction REAL NOT NULL,
                    was_useful INTEGER DEFAULT 1,
                    was_accurate INTEGER DEFAULT 1,
                    was_complete INTEGER DEFAULT 1,
                    correction_text TEXT DEFAULT '',
                    latency_ms REAL DEFAULT 0,
                    tokens_used INTEGER DEFAULT 0,
                    timestamp REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_fb_provr ON feedbacks(provider);
                CREATE INDEX IF NOT EXISTS idx_fb_domain ON feedbacks(domain);
                CREATE INDEX IF NOT EXISTS idx_fb_ts ON feedbacks(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_fb_conv ON feedbacks(conversation_id);

                CREATE TABLE IF NOT EXISTS provr_aggregates (
                    provider TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    total_feedbacks INTEGER DEFAULT 0,
                    satisfaction_sum REAL DEFAULT 0.0,
                    useful_count INTEGER DEFAULT 0,
                    accurate_count INTEGER DEFAULT 0,
                    complete_count INTEGER DEFAULT 0,
                    last_updated REAL,
                    PRIMARY KEY (provider, domain)
                );
            """)

    # ── Feedback recording ─────────────────────────────────────────

    def record_thumbs_up(
        self,
        conversation_id: str,
        message_id: str,
        provider: str,
        model: str = "",
        domain: str = "general",
        latency_ms: float = 0.0,
        tokens_used: int = 0,
    ) -> float:
        """
        Registra feedback positivo (thumbs up).
        Returns: satisfaction score assegnato.
        """
        import uuid
        entry = FeedbackEntry(
            feedback_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            message_id=message_id,
            provider=provider,
            model=model,
            domain=domain,
            satisfaction=self.THUMBS_UP_SCORE,
            was_useful=True,
            was_accurate=True,
            was_complete=True,
            correction_text="",
            timestamp=time.time(),
            latency_ms=latency_ms,
            tokens_used=tokens_used,
        )
        self._store(entry)
        return self.THUMBS_UP_SCORE

    def record_thumbs_down(
        self,
        conversation_id: str,
        message_id: str,
        provider: str,
        model: str = "",
        domain: str = "general",
        correction: str = "",
        was_accurate: bool = False,
        was_complete: bool = False,
        latency_ms: float = 0.0,
        tokens_used: int = 0,
    ) -> float:
        """
        Registra feedback negativo (thumbs down).
        Returns: satisfaction score assegnato.
        """
        import uuid
        entry = FeedbackEntry(
            feedback_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            message_id=message_id,
            provider=provider,
            model=model,
            domain=domain,
            satisfaction=self.THUMBS_DOWN_SCORE,
            was_useful=False,
            was_accurate=was_accurate,
            was_complete=was_complete,
            correction_text=correction,
            timestamp=time.time(),
            latency_ms=latency_ms,
            tokens_used=tokens_used,
        )
        self._store(entry)
        return self.THUMBS_DOWN_SCORE

    def record_detailed(
        self,
        conversation_id: str,
        message_id: str,
        provider: str,
        model: str = "",
        domain: str = "general",
        satisfaction: float = 0.5,
        was_useful: bool = True,
        was_accurate: bool = True,
        was_complete: bool = True,
        correction: str = "",
        latency_ms: float = 0.0,
        tokens_used: int = 0,
    ) -> float:
        """Registra feedback dettagliato con tutti i campi."""
        import uuid
        entry = FeedbackEntry(
            feedback_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            message_id=message_id,
            provider=provider,
            model=model,
            domain=domain,
            satisfaction=max(0.0, min(1.0, satisfaction)),
            was_useful=was_useful,
            was_accurate=was_accurate,
            was_complete=was_complete,
            correction_text=correction,
            timestamp=time.time(),
            latency_ms=latency_ms,
            tokens_used=tokens_used,
        )
        self._store(entry)
        return entry.satisfaction

    def _store(self, entry: FeedbackEntry):
        """Salva feedback e aggiorna aggregati."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO feedbacks
                   (feedback_id, conversation_id, message_id, provider, model,
                    domain, satisfaction, was_useful, was_accurate, was_complete,
                    correction_text, latency_ms, tokens_used, timestamp)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (entry.feedback_id, entry.conversation_id, entry.message_id,
                 entry.provider, entry.model, entry.domain, entry.satisfaction,
                 int(entry.was_useful), int(entry.was_accurate), int(entry.was_complete),
                 entry.correction_text, entry.latency_ms, entry.tokens_used, entry.timestamp),
            )

            # Aggiorna aggregati
            conn.execute(
                """INSERT INTO provr_aggregates
                   (provider, domain, total_feedbacks, satisfaction_sum,
                    useful_count, accurate_count, complete_count, last_updated)
                   VALUES (?,?,1,?,?,?,?,?)
                   ON CONFLICT(provider, domain) DO UPDATE SET
                       total_feedbacks = total_feedbacks + 1,
                       satisfaction_sum = satisfaction_sum + ?,
                       useful_count = useful_count + ?,
                       accurate_count = accurate_count + ?,
                       complete_count = complete_count + ?,
                       last_updated = ?""",
                (entry.provider, entry.domain, entry.satisfaction,
                 int(entry.was_useful), int(entry.was_accurate), int(entry.was_complete),
                 entry.timestamp,
                 entry.satisfaction,
                 int(entry.was_useful), int(entry.was_accurate), int(entry.was_complete),
                 entry.timestamp),
            )
            conn.commit()

    # ── Query API ──────────────────────────────────────────────────

    def get_reward_for_bandit(self, provider: str, domain: str = "general") -> float:
        """
        Calcola reward REALE per il BanditSelector.
        Basato su feedback utente aggregati, NON hardcoded.

        Returns: 0.0-1.0 basato su media satisfaction reale.
                 0.5 se nessun feedback disponibile.
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT total_feedbacks, satisfaction_sum FROM provr_aggregates WHERE provider=? AND domain=?",
                (provider, domain),
            ).fetchone()
            if row and row[0] > 0:
                return round(row[1] / row[0], 4)

            # Fallback: stats globali del provider (qualsiasi dominio)
            row = conn.execute(
                "SELECT SUM(total_feedbacks), SUM(satisfaction_sum) FROM provr_aggregates WHERE provider=?",
                (provider,),
            ).fetchone()
            if row and row[0] and row[0] > 0:
                return round(row[1] / row[0], 4)

        return 0.5  # Nessun dato → neutro

    def get_provr_satisfaction(self, provider: str) -> Dict:
        """Satisfaction media per un provider across all domains."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT domain, total_feedbacks, satisfaction_sum, useful_count,
                          accurate_count, complete_count
                   FROM provr_aggregates WHERE provider=?""",
                (provider,),
            ).fetchall()

        if not rows:
            return {"provider": provider, "domains": {}, "overall": 0.5}

        total_fb = sum(r[1] for r in rows)
        total_sat = sum(r[2] for r in rows)
        domains = {}
        for r in rows:
            if r[1] > 0:
                domains[r[0]] = {
                    "feedbacks": r[1],
                    "satisfaction": round(r[2] / r[1], 3),
                    "useful_rate": round(r[3] / r[1], 3),
                    "accurate_rate": round(r[4] / r[1], 3),
                    "complete_rate": round(r[5] / r[1], 3),
                }

        return {
            "provider": provider,
            "domains": domains,
            "overall": round(total_sat / max(1, total_fb), 3),
            "total_feedbacks": total_fb,
        }

    def get_summary(self) -> FeedbackSummary:
        """Riassunto completo di tutti i feedback."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM feedbacks").fetchone()[0]
            if total == 0:
                return FeedbackSummary(0, 0.5, 0.5, 0.5, 0.5, {}, {}, 0.0, 0)

            stats = conn.execute(
                """SELECT AVG(satisfaction), AVG(was_useful), AVG(was_accurate),
                          AVG(was_complete), SUM(CASE WHEN correction_text != '' THEN 1 ELSE 0 END)
                   FROM feedbacks"""
            ).fetchone()

            # Provider scores
            prov_rows = conn.execute(
                """SELECT provider, SUM(satisfaction_sum)/SUM(total_feedbacks)
                   FROM provr_aggregates
                   GROUP BY provider
                   HAVING SUM(total_feedbacks) > 0"""
            ).fetchall()
            provr_scores = {r[0]: round(r[1], 3) for r in prov_rows}

            # Domain scores
            dom_rows = conn.execute(
                """SELECT domain, SUM(satisfaction_sum)/SUM(total_feedbacks)
                   FROM provr_aggregates
                   GROUP BY domain
                   HAVING SUM(total_feedbacks) > 0"""
            ).fetchall()
            domain_scores = {r[0]: round(r[1], 3) for r in dom_rows}

            # Trend 7 giorni
            week_ago = time.time() - 7 * 86400
            recent = conn.execute(
                "SELECT AVG(satisfaction) FROM feedbacks WHERE timestamp > ?",
                (week_ago,),
            ).fetchone()
            older = conn.execute(
                "SELECT AVG(satisfaction) FROM feedbacks WHERE timestamp <= ?",
                (week_ago,),
            ).fetchone()
            trend = 0.0
            if recent[0] and older[0]:
                trend = round(recent[0] - older[0], 3)

            return FeedbackSummary(
                total_feedbacks=total,
                avg_satisfaction=round(stats[0] or 0.5, 3),
                useful_rate=round(stats[1] or 0.5, 3),
                accurate_rate=round(stats[2] or 0.5, 3),
                complete_rate=round(stats[3] or 0.5, 3),
                provr_scores=provr_scores,
                domain_scores=domain_scores,
                trend_7d=trend,
                corrections_count=int(stats[4] or 0),
            )

    def get_corrections(self, limit: int = 20) -> List[Dict]:
        """Ritorna le correzioni utente (per auto-learning)."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT provider, domain, correction_text, satisfaction, timestamp
                   FROM feedbacks
                   WHERE correction_text != ''
                   ORDER BY timestamp DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            {"provider": r[0], "domain": r[1], "correction": r[2],
             "satisfaction": r[3], "timestamp": r[4]}
            for r in rows
        ]


# ─── Singleton ────────────────────────────────────────────────────────

_feedback_mgr: Optional[UserFeedbackManager] = None

def get_user_feedback(data_dir: Optional[Path] = None) -> UserFeedbackManager:
    global _feedback_mgr
    if _feedback_mgr is None:
        _feedback_mgr = UserFeedbackManager(data_dir=data_dir)
    return _feedback_mgr
