"""
Test di performance VIO 83 AI Orchestra
Verifica latenze e throughput dei moduli core senza dipendenze esterne.
"""
import os
import sys
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

CLASSIFY_MAX_MS = 50
CACHE_L1_SET_MAX_MS = 5
CACHE_L1_GET_MAX_MS = 2
SCHEMA_PARSE_MAX_MS = 30


def ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def l1_cache():
    """L1MemoryCache isolata — nessun filesystem richiesto."""
    from backend.core.cache import L1MemoryCache
    return L1MemoryCache(max_size=4096, default_ttl=300)


@pytest.fixture(scope="function")
def cache_engine(tmp_path):
    """CacheEngine con L2 su /tmp."""
    from backend.core.cache import CacheEngine
    return CacheEngine(l2_db_path=str(tmp_path / "perf_cache.db"))


# ═══════════════════════════════════════════════════════════════
# PERFORMANCE: Intent Classification
# ═══════════════════════════════════════════════════════════════

class TestClassificationPerformance:

    def test_single_classify_under_50ms(self):
        from backend.orchestrator.direct_router import classify_request
        start = time.perf_counter()
        classify_request("Scrivi una funzione Python per ordinare una lista")
        elapsed = ms(start)
        assert elapsed < CLASSIFY_MAX_MS, f"classify troppo lento: {elapsed:.2f}ms"

    def test_100_classifies_under_500ms(self):
        from backend.orchestrator.direct_router import classify_request
        messages = [
            "Scrivi del codice Python",
            "Analizza questo contratto legale",
            "Come stai oggi?",
            "diagnosi differenziale diabete",
            "Scrivi un racconto fantastico",
        ] * 20
        start = time.perf_counter()
        for msg in messages:
            classify_request(msg)
        total = ms(start)
        assert total < 500, f"100 classificazioni troppo lente: {total:.1f}ms"

    def test_all_intents_consistent_speed(self):
        from backend.orchestrator.direct_router import classify_request
        cases = {
            "code": "Scrivi una funzione Python ricorsiva",
            "legal": "Analizza questo contratto d'appalto",
            "medical": "diagnosi differenziale cefalea tensiva",
            "creative": "Scrivi una poesia sull'autunno",
            "reasoning": "Ragiona su questo paradosso logico",
            "conversation": "Come stai oggi?",
        }
        for intent, msg in cases.items():
            start = time.perf_counter()
            classify_request(msg)
            elapsed = ms(start)
            assert elapsed < CLASSIFY_MAX_MS * 3, f"Intent '{intent}' lento: {elapsed:.2f}ms"


# ═══════════════════════════════════════════════════════════════
# PERFORMANCE: L1 Memory Cache
# ═══════════════════════════════════════════════════════════════

class TestL1CachePerformance:

    def test_l1_set_under_5ms(self, l1_cache):
        start = time.perf_counter()
        l1_cache.set("perf::001", {"data": "x" * 500}, ttl=60)
        elapsed = ms(start)
        assert elapsed < CACHE_L1_SET_MAX_MS, f"L1 set troppo lento: {elapsed:.3f}ms"

    def test_l1_get_hit_under_2ms(self, l1_cache):
        l1_cache.set("perf::get", {"result": "cached"}, ttl=60)
        start = time.perf_counter()
        l1_cache.get("perf::get")
        elapsed = ms(start)
        assert elapsed < CACHE_L1_GET_MAX_MS, f"L1 get (hit) troppo lento: {elapsed:.3f}ms"

    def test_l1_1000_sets_under_500ms(self, l1_cache):
        start = time.perf_counter()
        for i in range(1000):
            l1_cache.set(f"bulk::{i}", {"idx": i}, ttl=60)
        total = ms(start)
        assert total < 500, f"1000 L1 set troppo lenti: {total:.1f}ms"

    def test_l1_1000_gets_miss_under_200ms(self, l1_cache):
        start = time.perf_counter()
        for i in range(1000):
            l1_cache.get(f"miss::{i}")
        total = ms(start)
        assert total < 200, f"1000 L1 get (miss) troppo lenti: {total:.1f}ms"

    def test_l1_hit_not_slower_than_miss(self, l1_cache):
        key = "hit_vs_miss"
        l1_cache.set(key, {"data": "cached_value"}, ttl=60)
        # HIT
        start = time.perf_counter()
        for _ in range(500):
            l1_cache.get(key)
        hit_avg = ms(start) / 500
        # MISS
        start = time.perf_counter()
        for i in range(500):
            l1_cache.get(f"miss_unique::{i}")
        miss_avg = ms(start) / 500
        # Hit non deve essere più di 20x più lento del miss (sono entrambi sub-ms)
        assert hit_avg < miss_avg * 20 + 1, \
            f"Hit ({hit_avg:.4f}ms) molto più lento di miss ({miss_avg:.4f}ms)"


# ═══════════════════════════════════════════════════════════════
# PERFORMANCE: Schema Validation
# ═══════════════════════════════════════════════════════════════

class TestSchemaPerformance:

    def test_chat_request_parse_under_30ms(self):
        from backend.models.schemas import ChatRequest
        start = time.perf_counter()
        ChatRequest(message="Test performance schema")
        elapsed = ms(start)
        assert elapsed < SCHEMA_PARSE_MAX_MS, f"ChatRequest parse: {elapsed:.2f}ms"

    def test_100_schema_parses_under_300ms(self):
        from backend.models.schemas import ChatRequest
        start = time.perf_counter()
        for i in range(100):
            ChatRequest(message=f"Messaggio {i} per test performance schema")
        total = ms(start)
        assert total < 300, f"100 parse troppo lenti: {total:.1f}ms"

    def test_error_response_100_under_100ms(self):
        from backend.models.schemas import ErrorResponse
        start = time.perf_counter()
        for _ in range(100):
            ErrorResponse(error="Test", code=500)
        total = ms(start)
        assert total < 100, f"100 ErrorResponse troppo lenti: {total:.1f}ms"

    def test_classify_response_100_under_100ms(self):
        from backend.models.schemas import ClassifyResponse
        start = time.perf_counter()
        for _ in range(100):
            ClassifyResponse(request_type="code", confidence=0.9, suggested_provider="claude")
        total = ms(start)
        assert total < 100, f"100 ClassifyResponse troppo lenti: {total:.1f}ms"


# ═══════════════════════════════════════════════════════════════
# PERFORMANCE: Provider Config (in-memory, no I/O)
# ═══════════════════════════════════════════════════════════════

class TestProviderConfigPerformance:

    def test_get_available_providers_under_10ms(self):
        from backend.config.providers import get_available_cloud_providers
        start = time.perf_counter()
        get_available_cloud_providers()
        elapsed = ms(start)
        assert elapsed < 10, f"get_available_cloud_providers troppo lento: {elapsed:.2f}ms"

    def test_get_elite_stacks_under_10ms(self):
        from backend.config.providers import get_elite_task_stacks
        start = time.perf_counter()
        get_elite_task_stacks()
        elapsed = ms(start)
        assert elapsed < 10, f"get_elite_task_stacks troppo lento: {elapsed:.2f}ms"

    def test_100_provider_lookups_under_100ms(self):
        from backend.config.providers import get_available_cloud_providers
        start = time.perf_counter()
        for _ in range(100):
            get_available_cloud_providers()
        total = ms(start)
        assert total < 100, f"100 provider lookup troppo lenti: {total:.1f}ms"
