"""
VIO 83 AI ORCHESTRA — Self-Optimizer Engine
============================================
Motore di auto-ottimizzazione che si migliora da solo:
1. Monitora performance reali (latency, tokens, quality)
2. Auto-regola parametri: temperature, max_tokens, provider routing
3. Apprende preferenze implicite dell'utente
4. Ottimizza il rapporto qualità/velocità/costo automaticamente

Funziona come un "cervello metacognitivo" che osserva se stesso
e si migliora giorno per giorno, mantenendo sempre memoria leggera.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class ProviderProfile:
    """Profilo prestazionale di un provider."""
    name: str
    avg_latency_ms: float = 500.0
    avg_tokens: float = 200.0
    success_rate: float = 1.0
    quality_score: float = 0.5
    total_calls: int = 0
    last_used: float = 0.0
    # Parametri auto-tuned
    optimal_temperature: float = 0.7
    optimal_max_tokens: int = 512
    preferred_for: list[str] = field(default_factory=list)  # Domini ottimali

    def ema_update(self, latency_ms: float, tokens: int, success: bool, quality: float) -> None:
        """Exponential Moving Average per aggiornamento smooth."""
        alpha = 0.1  # Smoothing factor
        self.avg_latency_ms = (1 - alpha) * self.avg_latency_ms + alpha * latency_ms
        self.avg_tokens = (1 - alpha) * self.avg_tokens + alpha * tokens
        self.success_rate = (1 - alpha) * self.success_rate + alpha * (1.0 if success else 0.0)
        self.quality_score = (1 - alpha) * self.quality_score + alpha * quality
        self.total_calls += 1
        self.last_used = time.time()


@dataclass(slots=True)
class OptimizationState:
    """Stato persistente dell'ottimizzatore."""
    version: int = 1
    total_optimizations: int = 0
    last_optimization: float = 0.0
    global_quality_trend: float = 0.5  # 0=peggiorando, 1=migliorando
    providers: dict[str, dict] = field(default_factory=dict)
    domain_preferences: dict[str, dict] = field(default_factory=dict)


class SelfOptimizer:
    """
    Motore di auto-ottimizzazione continua.

    Principi:
    - Zero configurazione manuale richiesta
    - Ogni interazione migliora il sistema
    - Mantiene memoria ultra-compatta (~10KB stato)
    - Decisioni basate su dati reali, non ipotesi
    """

    OPTIMIZATION_INTERVAL = 50  # Ottimizza ogni N chiamate
    DECAY_FACTOR = 0.995  # Decadimento lento per dati vecchi
    QUALITY_THRESHOLD = 0.6  # Sotto → trigger re-routing
    LATENCY_PENALTY_MS = 3000  # Penalizza provider > 3s

    def __init__(self, state_path: Optional[Path] = None):
        self._state_path = state_path or Path("data/self_optimizer_state.json")
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._profiles: dict[str, ProviderProfile] = {}
        self._call_count = 0
        self._recent_quality: list[float] = []  # Ultimi 100 punteggi
        self._state = self._load_state()
        self._restore_profiles()

    def _load_state(self) -> OptimizationState:
        """Carica stato persistente."""
        if self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text())
                state = OptimizationState()
                state.version = data.get("version", 1)
                state.total_optimizations = data.get("total_optimizations", 0)
                state.last_optimization = data.get("last_optimization", 0.0)
                state.global_quality_trend = data.get("global_quality_trend", 0.5)
                state.providers = data.get("providers", {})
                state.domain_preferences = data.get("domain_preferences", {})
                return state
            except (json.JSONDecodeError, KeyError):
                pass
        return OptimizationState()

    def _save_state(self) -> None:
        """Salva stato persistente."""
        data = {
            "version": self._state.version,
            "total_optimizations": self._state.total_optimizations,
            "last_optimization": self._state.last_optimization,
            "global_quality_trend": self._state.global_quality_trend,
            "providers": {},
            "domain_preferences": self._state.domain_preferences,
        }
        for name, profile in self._profiles.items():
            data["providers"][name] = {
                "avg_latency_ms": round(profile.avg_latency_ms, 1),
                "avg_tokens": round(profile.avg_tokens, 1),
                "success_rate": round(profile.success_rate, 4),
                "quality_score": round(profile.quality_score, 4),
                "total_calls": profile.total_calls,
                "optimal_temperature": round(profile.optimal_temperature, 2),
                "optimal_max_tokens": profile.optimal_max_tokens,
                "preferred_for": profile.preferred_for,
            }
        self._state_path.write_text(json.dumps(data, indent=2))

    def _restore_profiles(self) -> None:
        """Ripristina profili provider dallo stato."""
        for name, data in self._state.providers.items():
            profile = ProviderProfile(name=name)
            profile.avg_latency_ms = data.get("avg_latency_ms", 500.0)
            profile.avg_tokens = data.get("avg_tokens", 200.0)
            profile.success_rate = data.get("success_rate", 1.0)
            profile.quality_score = data.get("quality_score", 0.5)
            profile.total_calls = data.get("total_calls", 0)
            profile.optimal_temperature = data.get("optimal_temperature", 0.7)
            profile.optimal_max_tokens = data.get("optimal_max_tokens", 512)
            profile.preferred_for = data.get("preferred_for", [])
            self._profiles[name] = profile

    # ─── Core: registra risultato e auto-ottimizza ──────────────────

    def record_result(
        self,
        provider: str,
        model: str,
        request_type: str,
        latency_ms: float,
        tokens_used: int,
        success: bool,
        user_satisfied: bool = True,
    ) -> None:
        """
        Registra il risultato di una chiamata AI.
        Auto-triggers optimization ogni N chiamate.
        """
        key = f"{provider}/{model}" if model else provider

        if key not in self._profiles:
            self._profiles[key] = ProviderProfile(name=key)

        # Calcola quality score composito
        quality = self._compute_quality(latency_ms, tokens_used, success, user_satisfied)
        self._profiles[key].ema_update(latency_ms, tokens_used, success, quality)

        # Track domain affinity
        if request_type and success and user_satisfied:
            profile = self._profiles[key]
            if request_type not in profile.preferred_for:
                if quality > 0.7:
                    profile.preferred_for.append(request_type)
                    if len(profile.preferred_for) > 10:
                        profile.preferred_for = profile.preferred_for[-10:]

        # Track quality trend
        self._recent_quality.append(quality)
        if len(self._recent_quality) > 100:
            self._recent_quality = self._recent_quality[-100:]

        self._call_count += 1

        # Auto-optimize ogni N chiamate
        if self._call_count % self.OPTIMIZATION_INTERVAL == 0:
            self._auto_optimize()

    def _compute_quality(
        self, latency_ms: float, tokens_used: int, success: bool, user_satisfied: bool
    ) -> float:
        """
        Calcola punteggio qualità composito [0.0, 1.0].
        Bilanciamento: 40% soddisfazione, 30% velocità, 20% successo, 10% efficienza token.
        """
        if not success:
            return 0.1

        satisfaction = 0.9 if user_satisfied else 0.3
        speed = max(0.0, 1.0 - (latency_ms / self.LATENCY_PENALTY_MS))
        efficiency = max(0.0, 1.0 - (tokens_used / 2000))  # Penalizza output verbosi

        return 0.4 * satisfaction + 0.3 * speed + 0.2 * 1.0 + 0.1 * efficiency

    # ─── Auto-optimization loop ─────────────────────────────────────

    def _auto_optimize(self) -> None:
        """
        Ciclo di auto-ottimizzazione:
        1. Analizza trend qualità
        2. Regola temperature per provider sotto-performanti
        3. Aggiorna preferenze dominio
        4. Salva stato
        """
        # Calcola trend qualità globale
        if len(self._recent_quality) >= 20:
            recent_half = self._recent_quality[-50:]
            older_half = self._recent_quality[:-50] if len(self._recent_quality) > 50 else self._recent_quality[:len(self._recent_quality)//2]
            if older_half:
                recent_avg = sum(recent_half) / len(recent_half)
                older_avg = sum(older_half) / len(older_half)
                self._state.global_quality_trend = min(1.0, max(0.0, 0.5 + (recent_avg - older_avg) * 5))

        # Auto-tune temperature per provider
        for key, profile in self._profiles.items():
            if profile.total_calls < 10:
                continue

            # Se qualità bassa e troppa randomness, riduci temperatura
            if profile.quality_score < self.QUALITY_THRESHOLD and profile.optimal_temperature > 0.3:
                profile.optimal_temperature = max(0.2, profile.optimal_temperature - 0.05)
            # Se qualità alta e output ripetitivi, aumenta leggermente
            elif profile.quality_score > 0.8 and profile.optimal_temperature < 0.9:
                profile.optimal_temperature = min(1.0, profile.optimal_temperature + 0.02)

            # Auto-tune max_tokens basandosi sull'utilizzo medio
            if profile.avg_tokens > 0:
                # Imposta max_tokens al 150% della media, con floor a 256
                optimal = max(256, int(profile.avg_tokens * 1.5))
                # Non superare 4096
                profile.optimal_max_tokens = min(4096, optimal)

        # Aggiorna preferenze dominio
        self._update_domain_preferences()

        self._state.total_optimizations += 1
        self._state.last_optimization = time.time()
        self._save_state()

    def _update_domain_preferences(self) -> None:
        """Aggiorna la mappa dominio → miglior provider."""
        domain_scores: dict[str, dict[str, float]] = {}

        for key, profile in self._profiles.items():
            for domain in profile.preferred_for:
                if domain not in domain_scores:
                    domain_scores[domain] = {}
                domain_scores[domain][key] = profile.quality_score

        for domain, providers in domain_scores.items():
            if providers:
                best = max(providers, key=lambda p: providers[p])
                self._state.domain_preferences[domain] = {
                    "best_provider": best,
                    "score": round(providers[best], 4),
                    "alternatives": sorted(
                        [p for p in providers if p != best],
                        key=lambda p: providers[p],
                        reverse=True
                    )[:3]
                }

    # ─── Query API per il router ────────────────────────────────────

    def get_optimal_params(self, provider: str, model: str = "", request_type: str = "") -> dict:
        """
        Ritorna parametri ottimali auto-tuned per una richiesta.
        Usato dal router prima di ogni chiamata AI.
        """
        key = f"{provider}/{model}" if model else provider
        profile = self._profiles.get(key)

        result = {
            "temperature": 0.7,
            "max_tokens": 512,
            "provider_quality": 0.5,
            "provider_latency_ms": 500.0,
        }

        if profile and profile.total_calls >= 5:
            result["temperature"] = profile.optimal_temperature
            result["max_tokens"] = profile.optimal_max_tokens
            result["provider_quality"] = profile.quality_score
            result["provider_latency_ms"] = profile.avg_latency_ms

        # Domain-specific override
        if request_type and request_type in self._state.domain_preferences:
            pref = self._state.domain_preferences[request_type]
            if pref.get("best_provider") == key:
                result["temperature"] = max(0.3, result["temperature"] - 0.1)  # Più preciso per dominio forte

        return result

    def get_best_provider_for(self, request_type: str) -> Optional[str]:
        """Ritorna il miglior provider per un tipo di richiesta."""
        pref = self._state.domain_preferences.get(request_type)
        if pref:
            return pref.get("best_provider")
        return None

    def get_stats(self) -> dict:
        """Ritorna statistiche di ottimizzazione."""
        return {
            "total_optimizations": self._state.total_optimizations,
            "global_quality_trend": round(self._state.global_quality_trend, 4),
            "providers_tracked": len(self._profiles),
            "domains_optimized": len(self._state.domain_preferences),
            "total_calls_tracked": sum(p.total_calls for p in self._profiles.values()),
            "avg_quality": round(
                sum(self._recent_quality) / len(self._recent_quality), 4
            ) if self._recent_quality else 0.0,
            "domain_preferences": self._state.domain_preferences,
        }


# ─── Singleton ──────────────────────────────────────────────────────

_INSTANCE: Optional[SelfOptimizer] = None


def get_self_optimizer(state_path: Optional[Path] = None) -> SelfOptimizer:
    """Ottieni singleton SelfOptimizer."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = SelfOptimizer(state_path)
    return _INSTANCE
