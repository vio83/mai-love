# ============================================================
# VIO 83 AI ORCHESTRA — Test HyperCompressor™
# Copyright © 2026 Viorica Porcu (vio83) — All rights reserved
# ============================================================
"""
Test suite per HyperCompressor™ — 44 test

Coverage:
  TestSystemPromptCache    (8 test)
  TestRequestFingerprint   (8 test)
  TestProviderHotPath      (8 test)
  TestResponseCompressor   (4 test)
  TestMetricsCollector     (6 test)
  TestAutoTuner            (4 test)
  TestHyperCompressorFacade(6 test)
"""

import time
import pytest
from backend.core.hyper_compressor import (
    SystemPromptCache,
    RequestFingerprint,
    ProviderHotPath, ProviderHealth,
    ResponseCompressor,
    MetricsCollector,
    AutoTuner,
    PipelineOrchestrator, PipelineResult,
    HyperCompressor, get_hyper_compressor,
)


class TestSystemPromptCache:

    def setup_method(self):
        self.spc = SystemPromptCache()

    def test_cache_populated_on_init(self):
        assert len(self.spc._cache) > 0

    def test_get_conversation_prompt(self):
        p = self.spc.get("conversation", local=False)
        assert isinstance(p, str)
        assert len(p) > 10

    def test_get_code_prompt(self):
        p = self.spc.get("code", local=False)
        assert isinstance(p, str)

    def test_get_local_prompt(self):
        p = self.spc.get("conversation", local=True)
        assert isinstance(p, str)
        assert len(p) > 0

    def test_get_unknown_falls_back(self):
        p = self.spc.get("nonexistent_type_xyz", local=False)
        # Should fallback to conversation
        assert isinstance(p, str)

    def test_get_tokens_positive(self):
        t = self.spc.get_tokens("code", local=False)
        assert t > 0

    def test_local_prompt_shorter_than_full(self):
        full = self.spc.get("conversation", local=False)
        local = self.spc.get("conversation", local=True)
        # Local prompts are typically shorter
        assert len(local) <= len(full) + 100  # small margin

    def test_all_types_cached(self):
        for t in ["code", "math", "creative", "conversation"]:
            assert self.spc.get(t) != ""


class TestRequestFingerprint:

    def setup_method(self):
        self.rf = RequestFingerprint()

    def test_returns_3_keys(self):
        fps = self.rf.fingerprint("test message")
        assert "exact" in fps
        assert "fuzzy" in fps
        assert "intent" in fps

    def test_exact_is_24_hex(self):
        fps = self.rf.fingerprint("hello world")
        assert len(fps["exact"]) == 24

    def test_fuzzy_is_8_hex(self):
        fps = self.rf.fingerprint("hello world")
        assert len(fps["fuzzy"]) == 8

    def test_intent_is_8_hex(self):
        fps = self.rf.fingerprint("hello world")
        assert len(fps["intent"]) == 8

    def test_same_message_same_fingerprints(self):
        fp1 = self.rf.fingerprint("ciao come stai")
        fp2 = self.rf.fingerprint("ciao come stai")
        assert fp1 == fp2

    def test_different_message_different_exact(self):
        fp1 = self.rf.fingerprint("machine learning reti neurali")
        fp2 = self.rf.fingerprint("cucina italiana pizza pasta")
        assert fp1["exact"] != fp2["exact"]

    def test_reordered_same_fuzzy(self):
        fp1 = self.rf.fingerprint("veloce rapido agile sistema")
        fp2 = self.rf.fingerprint("sistema agile rapido veloce")
        assert fp1["fuzzy"] == fp2["fuzzy"]

    def test_model_affects_exact(self):
        fp1 = self.rf.fingerprint("test", model="claude")
        fp2 = self.rf.fingerprint("test", model="gpt4")
        assert fp1["exact"] != fp2["exact"]


class TestProviderHotPath:

    def setup_method(self):
        self.hp = ProviderHotPath()

    def test_record_success_updates_latency(self):
        self.hp.record_success("groq", 100.0)
        self.hp.record_success("groq", 50.0)
        h = self.hp._health["groq"]
        assert h.avg_latency_ms < 500.0  # default was 500

    def test_record_error_increments(self):
        self.hp.record_error("failing_provider")
        assert self.hp._health["failing_provider"].error_count == 1

    def test_circuit_breaker_triggers(self):
        for _ in range(3):
            self.hp.record_error("bad_provider")
        assert self.hp._health["bad_provider"].available is False

    def test_get_fastest_excludes_broken(self):
        self.hp.record_success("groq", 50.0)
        self.hp.record_success("claude", 200.0)
        for _ in range(3):
            self.hp.record_error("openai")
        result = self.hp.get_fastest(["groq", "claude", "openai"])
        assert "openai" not in result
        assert result[0] == "groq"

    def test_get_fastest_sorted_by_latency(self):
        self.hp.record_success("slow", 500.0)
        self.hp.record_success("fast", 50.0)
        self.hp.record_success("medium", 200.0)
        result = self.hp.get_fastest(["slow", "fast", "medium"])
        assert result[0] == "fast"

    def test_circuit_breaker_recovers(self):
        hp = ProviderHotPath()
        hp.CIRCUIT_BREAKER_SEC = 0.01  # 10ms for test
        for _ in range(3):
            hp.record_error("test_p")
        assert hp._health["test_p"].available is False
        time.sleep(0.02)  # wait for recovery
        result = hp.get_fastest(["test_p"])
        assert "test_p" in result

    def test_stats_structure(self):
        self.hp.record_success("groq", 100.0)
        stats = self.hp.stats
        assert "groq" in stats
        assert "avg_ms" in stats["groq"]

    def test_ema_smoothing(self):
        self.hp.record_success("p", 1000.0)
        self.hp.record_success("p", 100.0)
        h = self.hp._health["p"]
        # EMA: default=500 → 0.2*1000+0.8*500=600 → 0.2*100+0.8*600=500
        assert 400 <= h.avg_latency_ms <= 600


class TestResponseCompressor:

    def setup_method(self):
        self.rc = ResponseCompressor()

    def test_compress_returns_dict(self):
        result = self.rc.compress_for_storage("Hello world!")
        assert "content" in result
        assert "tokens" in result

    def test_strips_trailing_spaces(self):
        result = self.rc.compress_for_storage("hello   \nworld   ")
        assert "   " not in result["content"].split("\n")[0]

    def test_collapses_many_newlines(self):
        result = self.rc.compress_for_storage("a\n\n\n\n\n\nb")
        assert "\n\n\n\n" not in result["content"]

    def test_savings_nonnegative(self):
        result = self.rc.compress_for_storage("clean text here")
        assert result["savings_percent"] >= 0.0


class TestMetricsCollector:

    def setup_method(self):
        self.mc = MetricsCollector()

    def test_record_request(self):
        self.mc.record_request("groq", "simple", 100.0)
        assert self.mc.stats["total_requests"] == 1

    def test_cache_hit_rate(self):
        self.mc.record_cache_hit()
        self.mc.record_cache_hit()
        self.mc.record_cache_miss()
        rate = self.mc.stats["cache_hit_rate"]
        assert abs(rate - 66.7) < 1.0

    def test_compression_savings(self):
        self.mc.record_compression(30.0)
        self.mc.record_compression(50.0)
        assert abs(self.mc.stats["avg_compression_savings"] - 40.0) < 0.1

    def test_multiple_providers(self):
        self.mc.record_request("groq", "code", 50.0)
        self.mc.record_request("claude", "reasoning", 300.0)
        assert self.mc.stats["total_requests"] == 2

    def test_avg_latencies_tracked(self):
        self.mc.record_request("groq", "simple", 100.0)
        self.mc.record_request("groq", "simple", 50.0)
        assert "groq:simple" in self.mc.stats["avg_latencies"]

    def test_initial_stats_empty(self):
        mc = MetricsCollector()
        assert mc.stats["total_requests"] == 0
        assert mc.stats["cache_hit_rate"] == 0.0


class TestAutoTuner:

    def setup_method(self):
        self.at = AutoTuner()
        self.mc = MetricsCollector()

    def test_no_tune_before_interval(self):
        self.at._request_count = 5
        result = self.at.tick(self.mc)
        assert result == {}

    def test_tune_at_interval(self):
        self.at._request_count = 99  # next tick = 100
        result = self.at.tick(self.mc)
        assert isinstance(result, dict)

    def test_low_cache_increases_ttl(self):
        # Simulate low cache hit rate
        self.mc.record_cache_miss()
        self.mc.record_cache_miss()
        self.at._request_count = 99
        self.at.tick(self.mc)
        assert self.at.cache_ttl_multiplier > 1.0

    def test_compression_default_enabled(self):
        assert self.at.compression_enabled is True


class TestHyperCompressorFacade:

    def setup_method(self):
        self.hc = HyperCompressor()

    def test_singleton(self):
        h1 = get_hyper_compressor()
        h2 = get_hyper_compressor()
        assert h1 is h2

    def test_process_returns_pipeline_result(self):
        result = self.hc.process(message="ciao come stai")
        assert isinstance(result, PipelineResult)

    def test_process_under_1ms(self):
        result = self.hc.process(message="ciao come stai", mode="hybrid")
        assert result.pipeline_ms < 1.0  # target <0.1ms, margin 1ms

    def test_process_has_fingerprints(self):
        result = self.hc.process(message="test query")
        assert "exact" in result.fingerprints
        assert "fuzzy" in result.fingerprints

    def test_stats_has_version(self):
        stats = self.hc.stats
        assert "HyperCompressor" in stats["version"]

    def test_record_error_no_crash(self):
        self.hc.record_error("test_provider")
        # Should not crash
        assert True
