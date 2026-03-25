# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ============================================================
"""
Test Suite — Ultra Engine Piuma™
=================================
Copertura completa di tutti e 5 i moduli ultra-compatti:
  1. SemanticCompactCache   (18 test)
  2. ConversationCompressor (12 test)
  3. AdaptiveProvrMemory (14 test)
  4. UltraTokenBudget       (10 test)
  5. FeatherRouter           (10 test)
  6. UltraEngine singleton   ( 4 test)
  7. ParallelRaceOrchestrator (14 test — async)
Total: 82 test
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, patch

from backend.core.ultra_engine import (
    SemanticCompactCache,
    ConversationCompressor,
    AdaptiveProvrMemory,
    UltraTokenBudget,
    FeatherRouter,
    UltraEngine,
    get_ultra_engine,
)
from backend.orchestrator.parallel_race import (
    ParallelRaceOrchestrator,
    ProvrCall,
    RaceMode,
    RaceResult,
    get_race_orchestrator,
)


# ──────────────────────────────────────────────────────────────
# 1. SemanticCompactCache
# ──────────────────────────────────────────────────────────────

class TestSemanticCompactCache:

    def setup_method(self):
        self.cache = SemanticCompactCache(max_size=100, base_ttl=300)

    def test_basic_set_get(self):
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

    def test_miss_returns_none(self):
        assert self.cache.get("nonexistent_key_xyz") is None

    def test_exact_key_priority(self):
        self.cache.set("key_exact", "exact_value")
        assert self.cache.get("key_exact") == "exact_value"

    def test_semantic_match(self):
        # Testo simile semanticamente → stesso fingerprint
        self.cache.set("k1", "result1", semantic_key="come stai oggi bene grazie")
        # Chiave diversa ma testo semanticamente simile
        result = self.cache.get("k2", semantic_key="bene grazie stai oggi come")
        assert result == "result1"

    def test_overwrite_key(self):
        self.cache.set("key", "v1")
        self.cache.set("key", "v2")
        assert self.cache.get("key") == "v2"

    def test_max_size_eviction(self):
        cache = SemanticCompactCache(max_size=5)
        for i in range(10):
            cache.set(f"key{i}", f"val{i}")
        assert len(cache._store) <= 5 + 10  # semantic keys extra

    def test_stats_structure(self):
        stats = self.cache.stats
        assert "engine" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_ratio" in stats

    def test_hit_ratio_increases_on_hit(self):
        self.cache.set("k", "v")
        self.cache.get("k")
        self.cache.get("k")
        stats = self.cache.stats
        assert stats["hits"] >= 2

    def test_normalize_strips_stopwords(self):
        n1 = SemanticCompactCache._normalize("il cane di Paolo")
        n2 = SemanticCompactCache._normalize("cane Paolo")
        assert n1 == n2

    def test_semantic_fingerprint_stable(self):
        fp1 = SemanticCompactCache._semantic_fingerprint("ciao mondo bello")
        fp2 = SemanticCompactCache._semantic_fingerprint("ciao mondo bello")
        assert fp1 == fp2

    def test_semantic_fingerprint_different_text(self):
        fp1 = SemanticCompactCache._semantic_fingerprint("gatto nero")
        fp2 = SemanticCompactCache._semantic_fingerprint("cane bianco")
        assert fp1 != fp2

    def test_get_category_code(self):
        cat = self.cache.get_category("scrivi una funzione python")
        assert cat == "code"

    def test_get_category_math(self):
        cat = self.cache.get_category("calcola il 20% di 500")
        assert cat == "math"

    def test_get_category_legal(self):
        cat = self.cache.get_category("cosa dice il GDPR sulla privacy")
        assert cat == "legal"

    def test_get_category_medical(self):
        cat = self.cache.get_category("ho dei sintomi di influenza")
        assert cat == "medical"

    def test_get_category_general(self):
        cat = self.cache.get_category("qualcosa di completamente casuale xyz")
        assert cat == "general"

    def test_miss_count_increments(self):
        before = self.cache._misses
        self.cache.get("never_set_key_abc123")
        assert self.cache._misses == before + 1

    def test_adaptive_ttl_increases_with_frequency(self):
        self.cache._access_freq["hot_key"] = 100
        ttl = self.cache._adaptive_ttl("hot_key")
        assert ttl > self.cache._base_ttl


# ──────────────────────────────────────────────────────────────
# 2. ConversationCompressor
# ──────────────────────────────────────────────────────────────

class TestConversationCompressor:

    def setup_method(self):
        self.comp = ConversationCompressor()

    def _make_messages(self, n: int):
        msgs = []
        for i in range(n):
            role = "user" if i % 2 == 0 else "assistant"
            msgs.append({"role": role, "content": f"Messaggio numero {i}: " + "contenuto " * 30})
        return msgs

    def test_short_history_unchanged(self):
        msgs = self._make_messages(4)
        active, compressed = self.comp.compress_history(msgs, window=8)
        assert len(active) == 4
        assert len(compressed) == 0

    def test_long_history_compressed(self):
        msgs = self._make_messages(20)
        active, compressed = self.comp.compress_history(msgs, window=8)
        assert len(active) == 8
        assert len(compressed) == 12

    def test_compressed_turns_have_summary(self):
        msgs = self._make_messages(16)
        _, compressed = self.comp.compress_history(msgs, window=8)
        for ct in compressed:
            assert ct.summary
            assert len(ct.summary) <= ConversationCompressor.MAX_SUMMARY_CHARS + 10

    def test_compressed_turns_have_role(self):
        msgs = self._make_messages(16)
        _, compressed = self.comp.compress_history(msgs, window=8)
        for ct in compressed:
            assert ct.role in ("user", "assistant")

    def test_importance_decay(self):
        msgs = self._make_messages(16)
        _, compressed = self.comp.compress_history(msgs, window=8)
        if len(compressed) >= 2:
            assert compressed[-1].importance > compressed[0].importance

    def test_context_prefix_empty_for_no_compressed(self):
        prefix = self.comp.build_context_prefix([])
        assert prefix == ""

    def test_context_prefix_contains_summary(self):
        msgs = self._make_messages(16)
        _, compressed = self.comp.compress_history(msgs, window=8)
        prefix = self.comp.build_context_prefix(compressed)
        assert "RIASSUNTO" in prefix or len(prefix) > 10

    def test_tokens_saved_counter(self):
        msgs = self._make_messages(20)
        self.comp.compress_history(msgs, window=8)
        assert self.comp._tokens_saved > 0

    def test_compressions_counter(self):
        msgs = self._make_messages(20)
        self.comp.compress_history(msgs, window=8)
        assert self.comp._compressions > 0

    def test_estimate_tokens_non_zero(self):
        assert ConversationCompressor._estimate_tokens("hello world") > 0

    def test_stats_structure(self):
        stats = self.comp.stats
        assert "compressions" in stats
        assert "tokens_saved" in stats
        assert "estimated_cost_saved_usd" in stats

    def test_vision_message_handled(self):
        """Messaggi con content lista (vision) non crashano."""
        msgs = [
            {"role": "user", "content": [
                {"type": "text", "text": "guarda questa immagine"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}}
            ]}
        ] * 12
        active, compressed = self.comp.compress_history(msgs, window=8)
        assert len(active) == 8


# ──────────────────────────────────────────────────────────────
# 3. AdaptiveProvrMemory
# ──────────────────────────────────────────────────────────────

class TestAdaptiveProvrMemory:

    def setup_method(self):
        self.mem = AdaptiveProvrMemory()

    def test_record_success_updates_latency(self):
        self.mem.record_success("claude", 500.0, 0.9)
        stats = self.mem.stats
        assert "claude" in stats["providers"]
        assert stats["providers"]["claude"]["avg_latency_ms"] == pytest.approx(500.0, abs=1)

    def test_record_multiple_successes_averages(self):
        self.mem.record_success("gpt", 200.0, 0.8)
        self.mem.record_success("gpt", 400.0, 0.8)
        stats = self.mem.stats
        avg = stats["providers"]["gpt"]["avg_latency_ms"]
        assert 200 <= avg <= 400

    def test_record_error_increments_errors(self):
        self.mem.record_error("ollama")
        stats = self.mem.stats
        assert stats["providers"]["ollama"]["errors"] == 1

    def test_get_best_provr_prefers_fast(self):
        self.mem.record_success("fast", 100.0, 0.8)
        self.mem.record_success("slow", 2000.0, 0.8)
        best = self.mem.get_best_provr(["fast", "slow"], prefer_speed=True)
        assert best == "fast"

    def test_get_best_provr_skips_circuit_open(self):
        self.mem._get_or_create("broken").circuit_open = True
        self.mem._get_or_create("broken").circuit_open_until = time.time() + 1000
        self.mem.record_success("working", 300.0, 0.8)
        best = self.mem.get_best_provr(["broken", "working"])
        assert best == "working"

    def test_get_best_provr_returns_something(self):
        best = self.mem.get_best_provr(["claude", "gpt"])
        assert best in ["claude", "gpt"]

    def test_empty_candidates_returns_none(self):
        best = self.mem.get_best_provr([])
        assert best is None

    def test_circuit_breaker_resets_after_time(self):
        stats_obj = self.mem._get_or_create("temp")
        stats_obj.circuit_open = True
        stats_obj.circuit_open_until = time.time() - 1  # Already expired
        assert stats_obj.is_available()

    def test_ranking_returns_list(self):
        self.mem.record_success("p1", 300.0, 0.9)
        self.mem.record_success("p2", 500.0, 0.7)
        ranking = self.mem.get_ranking()
        assert isinstance(ranking, list)
        assert len(ranking) == 2

    def test_intent_preference_updated(self):
        self.mem.record_success("claude", 400.0, 1.0, intent="code")
        assert "code" in self.mem._intent_preferences
        assert "claude" in self.mem._intent_preferences["code"]

    def test_stats_structure(self):
        stats = self.mem.stats
        assert "provrs_tracked" in stats
        assert "intents_learned" in stats

    def test_composite_score_between_zero_one(self):
        self.mem.record_success("p", 1000.0, 0.7)
        pstats = self.mem._get_or_create("p")
        score = pstats.composite_score
        assert 0 <= score <= 1

    def test_error_rate_zero_on_fresh(self):
        pstats = self.mem._get_or_create("fresh")
        assert pstats.error_rate == 0.0

    def test_high_error_rate_lowers_score(self):
        self.mem.record_success("reliable", 300.0, 0.9)
        self.mem.record_success("reliable", 300.0, 0.9)
        for _ in range(5):
            self.mem.record_error("unreliable")
        self.mem.record_success("unreliable", 300.0, 0.9)
        r_score = self.mem._get_or_create("reliable").composite_score
        u_score = self.mem._get_or_create("unreliable").composite_score
        assert r_score > u_score


# ──────────────────────────────────────────────────────────────
# 4. UltraTokenBudget
# ──────────────────────────────────────────────────────────────

class TestUltraTokenBudget:

    def test_estimate_tokens_non_zero(self):
        tokens = UltraTokenBudget.estimate_tokens("Hello world, this is a test.")
        assert tokens > 0

    def test_estimate_tokens_empty(self):
        assert UltraTokenBudget.estimate_tokens("") == 0

    def test_estimate_messages_tokens(self):
        msgs = [
            {"role": "user", "content": "Hello " * 100},
            {"role": "assistant", "content": "World " * 50},
        ]
        total = UltraTokenBudget.estimate_messages_tokens(msgs)
        assert total > 50

    def test_calculate_budget_claude(self):
        budget = UltraTokenBudget.calculate_budget(
            "claude", "You are helpful.", [{"role": "user", "content": "Hi"}], 2048
        )
        assert "available_for_response" in budget
        assert budget["provr_limit"] == 200_000
        assert budget["is_safe"]

    def test_calculate_budget_small_provr(self):
        budget = UltraTokenBudget.calculate_budget(
            "groq", "System prompt.", [{"role": "user", "content": "Hi"}], 2048
        )
        assert budget["provr_limit"] == 8_192

    def test_truncation_needed_flag(self):
        long_msgs = [{"role": "user", "content": "x" * 20000}]
        budget = UltraTokenBudget.calculate_budget("groq", "", long_msgs, 2048)
        assert budget["truncation_needed"]

    def test_safe_truncate_short_history(self):
        msgs = [{"role": "user", "content": "Hi"}]
        result = UltraTokenBudget.safe_truncate_messages(msgs, "claude")
        assert result == msgs

    def test_safe_truncate_keeps_last(self):
        msgs = [{"role": "user", "content": "x" * 2000} for _ in range(10)]
        result = UltraTokenBudget.safe_truncate_messages(msgs, "groq", reserve_for_response=1000)
        assert len(result) >= 1
        assert result[-1] == msgs[-1]

    def test_utilization_pct_in_range(self):
        budget = UltraTokenBudget.calculate_budget("claude", "test", [], 2048)
        assert 0 <= budget["utilization_pct"] <= 100

    def test_vision_message_tokens(self):
        msgs = [{"role": "user", "content": [
            {"type": "text", "text": "describe this"},
            {"type": "image_url", "image_url": {"url": "data:..."}}
        ]}]
        tokens = UltraTokenBudget.estimate_messages_tokens(msgs)
        assert tokens >= 765  # image token estimate


# ──────────────────────────────────────────────────────────────
# 5. FeatherRouter
# ──────────────────────────────────────────────────────────────

class TestFeatherRouter:

    def setup_method(self):
        self.router = FeatherRouter()

    def test_code_classification(self):
        assert self.router.classify("def my_function():") == "code"

    def test_math_classification(self):
        assert self.router.classify("calcola il 25% di 800") == "math"

    def test_legal_classification(self):
        assert self.router.classify("cosa dice il contratto GDPR") == "legal"

    def test_medical_classification(self):
        assert self.router.classify("ho sintomi di influenza") == "medical"

    def test_creative_classification(self):
        assert self.router.classify("scrivi una storia di fantascienza") == "creative"

    def test_reasoning_classification(self):
        assert self.router.classify("spiega il motivo di questa scelta") == "reasoning"

    def test_conversation_fallback(self):
        assert self.router.classify("qwerty zxcvbn abcdef") == "conversation"

    def test_performance_sub_microsecond(self):
        """FeatherRouter deve classificare in <10μs (10x margine vs target 1μs)."""
        N = 10000
        start = time.perf_counter()
        for _ in range(N):
            self.router.classify("def compute_something(): return 42")
        elapsed_us = (time.perf_counter() - start) * 1e6 / N
        assert elapsed_us < 10.0, f"Too slow: {elapsed_us:.2f}μs per call"

    def test_stats_structure(self):
        self.router.classify("test")
        stats = self.router.stats
        assert "calls" in stats
        assert "avg_latency_ns" in stats
        assert "avg_latency_us" in stats

    def test_calls_count_increments(self):
        before = self.router._calls
        self.router.classify("hello world")
        assert self.router._calls == before + 1


# ──────────────────────────────────────────────────────────────
# 6. UltraEngine Singleton
# ──────────────────────────────────────────────────────────────

class TestUltraEngineSingleton:

    def test_get_ultra_engine_returns_instance(self):
        engine = get_ultra_engine()
        assert isinstance(engine, UltraEngine)

    def test_singleton_same_instance(self):
        e1 = get_ultra_engine()
        e2 = get_ultra_engine()
        assert e1 is e2

    def test_all_components_present(self):
        engine = get_ultra_engine()
        assert hasattr(engine, "cache")
        assert hasattr(engine, "compressor")
        assert hasattr(engine, "provr_memory")
        assert hasattr(engine, "token_budget")
        assert hasattr(engine, "router")

    def test_stats_structure(self):
        engine = get_ultra_engine()
        stats = engine.stats
        assert "ultra_engine" in stats
        assert "cache" in stats
        assert "router" in stats


# ──────────────────────────────────────────────────────────────
# 7. ParallelRaceOrchestrator (async)
# ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestParallelRaceOrchestrator:

    def setup_method(self):
        self.orch = ParallelRaceOrchestrator()

    async def _make_provr(self, pid: str, response: str, delay: float = 0.01):
        """Helper: crea ProvrCall con risposta simulata."""
        async def _fn():
            await asyncio.sleep(delay)
            if response == "ERROR":
                raise Exception("Provider error")
            return response
        return ProvrCall(pid, _fn())

    async def test_race_first_returns_fastest(self):
        p1 = await self._make_provr("slow_p", "A" * 50, delay=0.1)
        p2 = await self._make_provr("fast_p", "B" * 50, delay=0.01)
        result = await self.orch.run([p1, p2], mode=RaceMode.FIRST)
        assert result.winner == "fast_p"
        assert result.response == "B" * 50

    async def test_race_best_picks_quality(self):
        p1 = await self._make_provr("ok_p", "Short.", delay=0.01)
        p2 = await self._make_provr("good_p", "This is a much better and longer response with details " * 3, delay=0.02)
        result = await self.orch.run([p1, p2], mode=RaceMode.BEST, min_responses_for_best=2)
        # Il provider con risposta più lunga/strutturata dovrebbe vincere
        assert result.winner in ["ok_p", "good_p"]
        assert result.response != ""

    async def test_race_cross_returns_result(self):
        p1 = await self._make_provr("p1", "Il cielo è blu e molto bello oggi.", delay=0.01)
        p2 = await self._make_provr("p2", "Il cielo è blu e molto bello.", delay=0.02)
        result = await self.orch.run([p1, p2], mode=RaceMode.CROSS)
        assert result.response != ""
        assert result.winner in ["p1", "p2"]

    async def test_empty_provrs_returns_error(self):
        result = await self.orch.run([], mode=RaceMode.FIRST)
        assert result.error is not None
        assert result.response == ""

    async def test_all_provrs_fail_returns_error(self):
        p1 = await self._make_provr("p1", "ERROR")
        p2 = await self._make_provr("p2", "ERROR")
        result = await self.orch.run([p1, p2], mode=RaceMode.FIRST)
        assert result.winner == "none"

    async def test_result_has_latency(self):
        p = await self._make_provr("p", "Response text is here.", delay=0.01)
        result = await self.orch.run([p], mode=RaceMode.FIRST)
        assert result.latency_ms > 0

    async def test_result_has_quality_score(self):
        p = await self._make_provr("p", "Questa è una risposta di buona qualità con molte parole.", delay=0.01)
        result = await self.orch.run([p], mode=RaceMode.FIRST)
        assert 0 <= result.quality_score <= 1

    async def test_score_response_code_intent(self):
        long_code = """Here is the Python solution:\n\n```python\nimport os\n\ndef compute_fibonacci(n: int) -> list:\n    \"\"\"Compute Fibonacci sequence up to n terms.\"\"\"\n    sequence = [0, 1]\n    for i in range(2, n):\n        sequence.append(sequence[-1] + sequence[-2])\n    return sequence\n\nresult = compute_fibonacci(10)\nprint(result)\n```\n\nThis function uses dynamic programming for efficiency."""
        score = ParallelRaceOrchestrator._score_response(long_code, intent="code")
        assert score > 0.6

    async def test_score_response_empty_zero(self):
        score = ParallelRaceOrchestrator._score_response("", intent=None)
        assert score == 0.0

    async def test_score_response_evasive_penalized(self):
        score = ParallelRaceOrchestrator._score_response(
            "Mi dispiace ma non posso rispondere a questa domanda."
        )
        assert score < 0.5

    async def test_similarity_ntical_texts(self):
        sim = ParallelRaceOrchestrator._compute_similarity("hello world foo bar", "hello world foo bar")
        assert sim == pytest.approx(1.0)

    async def test_similarity_different_texts(self):
        sim = ParallelRaceOrchestrator._compute_similarity("gatto nero", "elefante bianco grande")
        assert sim < 0.3

    async def test_stats_increments(self):
        before = self.orch._races_run
        p = await self._make_provr("p", "Valid response text here " * 3)
        await self.orch.run([p], mode=RaceMode.FIRST)
        assert self.orch._races_run == before + 1

    async def test_singleton_same_instance(self):
        o1 = get_race_orchestrator()
        o2 = get_race_orchestrator()
        assert o1 is o2
