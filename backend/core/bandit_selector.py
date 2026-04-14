# ============================================================
# VIO 83 AI ORCHESTRA — BanditSelector™ (REAL ML)
# Copyright © 2026 Viorica Porcu (vio83) — All rights reserved
# ============================================================
"""
BanditSelector™ v1.0 — Multi-Armed Bandit per Provider Selection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUESTO È MACHINE LEARNING REALE — non keyword matching.

Implementa:
  UCB1 (Upper Confnce Bound)  → esplorazione vs sfruttamento
  Thompson Sampling (Beta)       → bayesiano, gestisce incertezza
  Contextual Bandit              → consra dominio come contesto

Ogni provider AI è un "braccio" della slot machine.
L'algoritmo impara quale provider produce la migliore qualità
per ogni tipo di task, bilanciando esplorazione di provider nuovi
con sfruttamento di provider noti come buoni.

Matematica:
  UCB1:  score(a) = x̄(a) + c * √(ln(N) / n(a))
         dove x̄(a) = media reward del braccio a
              N     = numero totale di pull
              n(a)  = numero di pull del braccio a
              c     = parametro di esplorazione (√2 di default)

  Thompson: sample ~ Beta(α, β) dove α=successi+1, β=fallimenti+1
"""

from __future__ import annotations

import logging
import math
import random
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("bandit_selector")


# ─── Dataclasses ──────────────────────────────────────────────────────

@dataclass
class ArmStats:
    """Statistiche di un braccio (provider) della slot machine."""
    arm_id: str          # es. "claude/claude-sonnet-4-6"
    total_pulls: int = 0
    total_reward: float = 0.0
    successes: float = 0.0   # Per Thompson (reward > 0.7)
    failures: float = 0.0    # Per Thompson (reward <= 0.7)
    last_reward: float = 0.0
    last_pull_ts: float = 0.0

    @property
    def mean_reward(self) -> float:
        if self.total_pulls == 0:
            return 0.0
        return self.total_reward / self.total_pulls

    @property
    def alpha(self) -> float:
        """Parametro α per distribuzione Beta (Thompson Sampling)."""
        return self.successes + 1.0

    @property
    def beta_param(self) -> float:
        """Parametro β per distribuzione Beta (Thompson Sampling)."""
        return self.failures + 1.0


@dataclass
class ContextualArm:
    """Braccio con statistiche per-contesto (dominio)."""
    arm_id: str
    domain: str
    total_pulls: int = 0
    total_reward: float = 0.0
    successes: float = 0.0
    failures: float = 0.0

    @property
    def mean_reward(self) -> float:
        if self.total_pulls == 0:
            return 0.0
        return self.total_reward / self.total_pulls

    @property
    def alpha(self) -> float:
        return self.successes + 1.0

    @property
    def beta_param(self) -> float:
        return self.failures + 1.0


# ─── UCB1 Algorithm ───────────────────────────────────────────────────

class UCB1:
    """
    Upper Confnce Bound 1 — Algoritmo classico di banditi.

    Bilancia esplorazione/sfruttamento in modo ottimale (regret O(√T ln T)).
    Nessuna distribuzione assunta sui reward — funziona per qualsiasi distribuzione.
    """

    def __init__(self, exploration_param: float = 1.414):
        """
        Args:
            exploration_param: c nel formula UCB1. Default √2 (ottimale teorico).
                              Aumenta → più esplorazione.
                              Riduci → più sfruttamento.
        """
        self.c = exploration_param

    def select(self, arms: Dict[str, ArmStats], total_pulls: int) -> str:
        """
        Seleziona il braccio con il più alto UCB1 score.

        Formula: UCB1(a) = x̄(a) + c * √(ln(N) / n(a))

        Returns: arm_id del braccio selezionato
        """
        if not arms:
            raise ValueError("Nessun braccio disponibile")

        # Fase iniziale: ogni braccio deve essere provato almeno una volta
        untried = [aid for aid, a in arms.items() if a.total_pulls == 0]
        if untried:
            return random.choice(untried)

        # Calcola UCB1 score per ogni braccio
        best_arm = None
        best_score = -float("inf")

        for arm_id, arm in arms.items():
            exploitation = arm.mean_reward
            exploration = self.c * math.sqrt(math.log(total_pulls) / arm.total_pulls)
            ucb_score = exploitation + exploration

            if ucb_score > best_score:
                best_score = ucb_score
                best_arm = arm_id

        return best_arm


# ─── Thompson Sampling ────────────────────────────────────────────────

class ThompsonSampling:
    """
    Thompson Sampling — Approccio bayesiano ai banditi.

    Campiona da distribuzione Beta(α, β) per ogni braccio.
    α = numero di "successi" + 1
    β = numero di "fallimenti" + 1

    Vantaggi rispetto a UCB1:
    - Gestisce naturalmente l'incertezza
    - Converge più velocemente in pratica
    - Funziona bene con reward non stazionari (i provider cambiano nel tempo)
    """

    def select(self, arms: Dict[str, ArmStats]) -> str:
        """
        Campiona da Beta distribution per ogni braccio, seleziona il più alto.
        """
        if not arms:
            raise ValueError("Nessun braccio disponibile")

        best_arm = None
        best_sample = -float("inf")

        for arm_id, arm in arms.items():
            # Campiona dalla distribuzione Beta
            sample = random.betavariate(arm.alpha, arm.beta_param)
            if sample > best_sample:
                best_sample = sample
                best_arm = arm_id

        return best_arm


# ─── Contextual Bandit ────────────────────────────────────────────────

class ContextualBandit:
    """
    Bandit contestuale: consra il dominio del task come contesto.

    Mantiene statistiche separate per ogni combinazione (provider, dominio).
    Un provider potrebbe essere ottimo per "code" ma pessimo per "creative".

    Strategia: Thompson Sampling per-contesto con fallback globale.
    """

    def __init__(self):
        self._thompson = ThompsonSampling()

    def select(
        self,
        available_arms: List[str],
        domain: str,
        contextual_stats: Dict[str, Dict[str, ContextualArm]],
        global_stats: Dict[str, ArmStats],
    ) -> str:
        """
        Seleziona provider ottimale dato il contesto (dominio).

        Args:
            available_arms: lista di arm_id disponibili
            domain: dominio del task corrente (es. "code", "creative")
            contextual_stats: stats per-contesto [domain][arm_id] → ContextualArm
            global_stats: stats globali per arm_id → ArmStats

        Returns: arm_id selezionato
        """
        if not available_arms:
            raise ValueError("Nessun provider disponibile")

        # Se abbiamo stats contestuali per questo dominio, usiamo quelle
        domain_stats = contextual_stats.get(domain, {})

        # Costruisci arms per Thompson Sampling
        arms_for_thompson: Dict[str, ArmStats] = {}
        for arm_id in available_arms:
            if arm_id in domain_stats and domain_stats[arm_id].total_pulls >= 3:
                # Usa stats contestuali (specifiche per dominio)
                ctx = domain_stats[arm_id]
                arms_for_thompson[arm_id] = ArmStats(
                    arm_id=arm_id,
                    total_pulls=ctx.total_pulls,
                    total_reward=ctx.total_reward,
                    successes=ctx.successes,
                    failures=ctx.failures,
                )
            elif arm_id in global_stats:
                # Fallback a stats globali
                arms_for_thompson[arm_id] = global_stats[arm_id]
            else:
                # Provider mai provato → esplorazione forzata (prior uniforme)
                arms_for_thompson[arm_id] = ArmStats(arm_id=arm_id)

        return self._thompson.select(arms_for_thompson)


# ─── BanditSelector™ — Entry Point ───────────────────────────────────

class BanditSelector:
    """
    BanditSelector™ — Machine Learning reale per provider selection.

    Sostituisce il keyword matching hardcoded con algoritmi di banditi
    che imparano dal feedback reale degli utenti.

    Usage:
        bs = BanditSelector(data_dir=Path("data"))

        # Seleziona provider migliore per un task
        provider = bs.select_provr(
            available=["claude/sonnet", "openai/gpt-4o", "ollama/llama3"],
            domain="code",
            strategy="thompson"  # o "ucb1" o "contextual"
        )

        # Dopo aver ricevuto il risultato, aggiorna con il reward
        bs.update(
            arm_id="claude/sonnet",
            domain="code",
            reward=0.92,  # da user feedback o quality score reale
        )

        # Stats
        print(bs.get_stats())
    """

    VERSION = "1.0.0"
    SUCCESS_THRESHOLD = 0.70  # reward > questo = "successo" per Thompson

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "bandit_stats.db"

        self._ucb1 = UCB1(exploration_param=1.414)
        self._thompson = ThompsonSampling()
        self._contextual = ContextualBandit()

        self._global_stats: Dict[str, ArmStats] = {}
        self._contextual_stats: Dict[str, Dict[str, ContextualArm]] = {}
        self._total_pulls = 0

        self._init_db()
        self._load_stats()

        logger.info(f"[BanditSelector™ v{self.VERSION}] Caricati {len(self._global_stats)} provider, {self._total_pulls} pull totali")

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS global_arms (
                    arm_id TEXT PRIMARY KEY,
                    total_pulls INTEGER DEFAULT 0,
                    total_reward REAL DEFAULT 0.0,
                    successes REAL DEFAULT 0.0,
                    failures REAL DEFAULT 0.0,
                    last_reward REAL DEFAULT 0.0,
                    last_pull_ts REAL DEFAULT 0.0
                );
                CREATE TABLE IF NOT EXISTS contextual_arms (
                    arm_id TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    total_pulls INTEGER DEFAULT 0,
                    total_reward REAL DEFAULT 0.0,
                    successes REAL DEFAULT 0.0,
                    failures REAL DEFAULT 0.0,
                    PRIMARY KEY (arm_id, domain)
                );
                CREATE TABLE IF NOT EXISTS pull_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    arm_id TEXT NOT NULL,
                    domain TEXT,
                    reward REAL,
                    strategy TEXT,
                    timestamp REAL
                );
                CREATE INDEX IF NOT EXISTS idx_pull_log_ts ON pull_log(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_pull_log_arm ON pull_log(arm_id);
            """)

    def _load_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            # Global stats
            for row in conn.execute("SELECT * FROM global_arms"):
                arm_id, total_pulls, total_reward, successes, failures, last_reward, last_pull_ts = row
                self._global_stats[arm_id] = ArmStats(
                    arm_id=arm_id, total_pulls=total_pulls,
                    total_reward=total_reward, successes=successes,
                    failures=failures, last_reward=last_reward,
                    last_pull_ts=last_pull_ts,
                )
                self._total_pulls += total_pulls

            # Contextual stats
            for row in conn.execute("SELECT * FROM contextual_arms"):
                arm_id, domain, total_pulls, total_reward, successes, failures = row
                if domain not in self._contextual_stats:
                    self._contextual_stats[domain] = {}
                self._contextual_stats[domain][arm_id] = ContextualArm(
                    arm_id=arm_id, domain=domain,
                    total_pulls=total_pulls, total_reward=total_reward,
                    successes=successes, failures=failures,
                )

    # ── Public API ─────────────────────────────────────────────────

    def select_provr(
        self,
        available: List[str],
        domain: str = "general",
        strategy: str = "contextual",
    ) -> str:
        """
        Seleziona il provider migliore usando ML reale.

        Args:
            available: lista di provider disponibili (es. ["claude/sonnet", "openai/gpt-4o"])
            domain: tipo di task (es. "code", "creative", "medical")
            strategy: "ucb1" | "thompson" | "contextual" (default)

        Returns: arm_id del provider selezionato
        """
        if not available:
            raise ValueError("Nessun provider disponibile")

        if len(available) == 1:
            return available[0]

        # Assicura che tutti i provider siano nelle stats
        for arm_id in available:
            if arm_id not in self._global_stats:
                self._global_stats[arm_id] = ArmStats(arm_id=arm_id)

        if strategy == "ucb1":
            # Filter global stats to available arms
            filtered = {k: v for k, v in self._global_stats.items() if k in available}
            selected = self._ucb1.select(filtered, max(1, self._total_pulls))

        elif strategy == "thompson":
            filtered = {k: v for k, v in self._global_stats.items() if k in available}
            selected = self._thompson.select(filtered)

        elif strategy == "contextual":
            selected = self._contextual.select(
                available_arms=available,
                domain=domain,
                contextual_stats=self._contextual_stats,
                global_stats=self._global_stats,
            )
        else:
            raise ValueError(f"Strategia sconosciuta: {strategy}")

        logger.debug(
            f"[BanditSelector] strategy={strategy} domain={domain} "
            f"selected={selected} from {len(available)} arms"
        )
        return selected

    def update(self, arm_id: str, domain: str, reward: float) -> None:
        """
        Aggiorna statistiche dopo aver osservato il reward.

        Args:
            arm_id: provider usato (es. "claude/sonnet")
            domain: dominio del task
            reward: 0.0-1.0 basato su quality reale (da user feedback o quality verifier)
        """
        reward = max(0.0, min(1.0, reward))
        now = time.time()
        is_success = reward > self.SUCCESS_THRESHOLD

        # ── Aggiorna stats globali ──
        if arm_id not in self._global_stats:
            self._global_stats[arm_id] = ArmStats(arm_id=arm_id)

        arm = self._global_stats[arm_id]
        arm.total_pulls += 1
        arm.total_reward += reward
        arm.last_reward = reward
        arm.last_pull_ts = now
        if is_success:
            arm.successes += 1.0
        else:
            arm.failures += 1.0

        self._total_pulls += 1

        # ── Aggiorna stats contestuali ──
        if domain not in self._contextual_stats:
            self._contextual_stats[domain] = {}
        if arm_id not in self._contextual_stats[domain]:
            self._contextual_stats[domain][arm_id] = ContextualArm(
                arm_id=arm_id, domain=domain
            )

        ctx = self._contextual_stats[domain][arm_id]
        ctx.total_pulls += 1
        ctx.total_reward += reward
        if is_success:
            ctx.successes += 1.0
        else:
            ctx.failures += 1.0

        # ── Persisti su DB ──
        self._persist_update(arm_id, domain, reward, now)

    def _persist_update(self, arm_id: str, domain: str, reward: float, ts: float):
        """Salva su SQLite (batch-friendly)."""
        try:
            arm = self._global_stats[arm_id]
            ctx = self._contextual_stats.get(domain, {}).get(arm_id)

            with sqlite3.connect(self.db_path) as conn:
                # Upsert global
                conn.execute(
                    """INSERT INTO global_arms (arm_id, total_pulls, total_reward, successes, failures, last_reward, last_pull_ts)
                       VALUES (?,?,?,?,?,?,?)
                       ON CONFLICT(arm_id) DO UPDATE SET
                           total_pulls=?, total_reward=?, successes=?, failures=?,
                           last_reward=?, last_pull_ts=?""",
                    (arm_id, arm.total_pulls, arm.total_reward, arm.successes,
                     arm.failures, arm.last_reward, arm.last_pull_ts,
                     arm.total_pulls, arm.total_reward, arm.successes,
                     arm.failures, arm.last_reward, arm.last_pull_ts),
                )
                # Upsert contextual
                if ctx:
                    conn.execute(
                        """INSERT INTO contextual_arms (arm_id, domain, total_pulls, total_reward, successes, failures)
                           VALUES (?,?,?,?,?,?)
                           ON CONFLICT(arm_id, domain) DO UPDATE SET
                               total_pulls=?, total_reward=?, successes=?, failures=?""",
                        (arm_id, domain, ctx.total_pulls, ctx.total_reward,
                         ctx.successes, ctx.failures,
                         ctx.total_pulls, ctx.total_reward,
                         ctx.successes, ctx.failures),
                    )
                # Log
                conn.execute(
                    "INSERT INTO pull_log (arm_id, domain, reward, strategy, timestamp) VALUES (?,?,?,?,?)",
                    (arm_id, domain, reward, "contextual", ts),
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"[BanditSelector._persist] {e}")

    def get_rankings(self, domain: Optional[str] = None) -> List[Dict]:
        """
        Ritorna ranking dei provider per reward medio.
        Se domain specificato, usa stats contestuali.
        """
        if domain and domain in self._contextual_stats:
            arms = self._contextual_stats[domain]
            ranked = sorted(
                arms.values(),
                key=lambda a: a.mean_reward,
                reverse=True,
            )
            return [
                {
                    "provider": a.arm_id,
                    "domain": a.domain,
                    "pulls": a.total_pulls,
                    "mean_reward": round(a.mean_reward, 4),
                    "success_rate": round(a.successes / max(1, a.total_pulls), 4),
                }
                for a in ranked
            ]
        else:
            ranked = sorted(
                self._global_stats.values(),
                key=lambda a: a.mean_reward,
                reverse=True,
            )
            return [
                {
                    "provider": a.arm_id,
                    "pulls": a.total_pulls,
                    "mean_reward": round(a.mean_reward, 4),
                    "success_rate": round(a.successes / max(1, a.total_pulls), 4),
                }
                for a in ranked
            ]

    def get_stats(self) -> Dict:
        """Statistiche complete del Bandit."""
        return {
            "version": self.VERSION,
            "algorithm": "UCB1 + Thompson Sampling + Contextual Bandit",
            "total_pulls": self._total_pulls,
            "provrs_tracked": len(self._global_stats),
            "domains_tracked": len(self._contextual_stats),
            "global_rankings": self.get_rankings()[:10],
            "domain_best": {
                domain: self.get_rankings(domain)[:3]
                for domain in list(self._contextual_stats.keys())[:10]
            },
        }


# ─── Singleton ────────────────────────────────────────────────────────

_bandit: Optional[BanditSelector] = None

def get_bandit_selector(data_dir: Optional[Path] = None) -> BanditSelector:
    global _bandit
    if _bandit is None:
        _bandit = BanditSelector(data_dir=data_dir)
    return _bandit
