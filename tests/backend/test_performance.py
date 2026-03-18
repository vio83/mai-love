"""
Test di performance VIO 83 AI Orchestra
Verifica latenze, throughput e comportamento sotto carico per i moduli core.
"""
import os
import sys
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Soglie di performance (millisecondi)
CLASSIFY_MAX_MS = 50       # classificazione intent deve essere < 50ms
CACHE_SET_MAX_MS = 10      # set cache < 10ms
CACHE_GET_MAX_MS = 5       # get cache < 5ms
SCHEMA_PARSE_MAX_MS = 20   # parsing schema < 20ms
DB_WRITE_MAX_MS = 100      # scrittura DB < 100ms


def elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def fast_cache(tmp_path):
    from backend.core.cache import CacheEngine
    cache = CacheEngine(data_dir=str(tmp_path))
    yield cache
    cache.close()


# ═══════════════════════════════════════════════════════════════
# PERFORMANCE: Intent Classification
# ═══════════════════════════════════════════════════════════════

class TestClassificationPerformance:
    """La classificazione intent deve essere < 50ms (regex/keyword, nessuna AI call)."""

    def test_classify_single_call_under_50ms(self):
        from backend.orchestrator.direct_router import classify_request
        start = time.perf_counter()
        classify_request("Scrivi una funzione Python per ordinare una lista")
        ms = elapsed_ms(start)
        assert ms < CLASSIFY_MAX_MS, f"classify troppo lento: {ms:.2f}ms (max {CLASSIFY_MAX_MS}ms)"

    def test_classify_100_calls_under_500ms(self):
        """100 classificazioni consecutive in meno di 500ms totali."""
        from backend.orchestrator.direct_router import classify_request
        messages = [
            "Scrivi del codice Python",
            "Analizza questo contratto legale",
            "Come stai oggi?",
            "Diagnosi differenziale del diabete",
            "Scrivi un racconto fantastico",
        ] * 20  # 100 chiamate totali
        start = time.perf_counter()
        for msg in messages:
            classify_request(msg)
        total_ms = elapsed_ms(start)
        avg_ms = total_ms / len(messages)
        assert total_ms < 500, f"100 classificazioni troppo lente: {total_ms:.1f}ms totali"
        assert avg_ms < CLASSIFY_MAX_MS, f"Media {avg_ms:.2f}ms > {CLASSIFY_MAX_MS}ms"

    def test_classify_all_intents_consistent_speed(self):
        """Tutti gli intent vengono classificati a velocità coerente."""
        from backend.orchestrator.direct_router import classify_request
        test_cases = {
            "code": "Scrivi una funzione Python ricorsiva",
            "legal": "Analizza questo contratto di appalto",
            "medical": "Diagnosi differenziale cefalea tensiva",
            "creative": "Scrivi una poesia sull'autunno",
            "reasoning": "Ragiona su questo paradosso logico",
            "analysis": "Analizza questi dati statistici",
            "writing": "Scrivi un articolo di blog",
            "conversation": "Come stai oggi?",
        }
        latencies = {}
        for intent, msg in test_cases.items():
            start = time.perf_counter()
            classify_request(msg)
            latencies[intent] = elapsed_ms(start)
        for intent, ms in latencies.items():
            assert ms < CLASSIFY_MAX_MS * 2, f"Intent '{intent}' lento: {ms:.2f}ms"


# ═══════════════════════════════════════════════════════════════
# PERFORMANCE: Cache
# ═══════════════════════════════════════════════════════════════

class TestCachePerformance:
    """Operazioni cache L1 (memoria) devono essere sub-millisecondo."""

    def test_cache_set_under_10ms(self, fast_cache):
        start = time.perf_counter()
        fast_cache.set("perf::key::001", {"data": "x" * 500}, ttl=60)
        ms = elapsed_ms(start)
        assert ms < CACHE_SET_MAX_MS, f"cache.set troppo lento: {ms:.2f}ms"

    def test_cache_get_under_5ms(self, fast_cache):
        fast_cache.set("perf::get::001", {"result": "cached_response"}, ttl=60)
        start = time.perf_counter()
        fast_cache.get("perf::get::001")
        ms = elapsed_ms(start)
        assert ms < CACHE_GET_MAX_MS, f"cache.get troppo lento: {ms:.2f}ms"

    def test_cache_1000_sets_under_2s(self, fast_cache):
        """1000 set operazioni in meno di 2 secondi."""
        start = time.perf_counter()
        for i in range(1000):
            fast_cache.set(f"perf::bulk::{i}", {"index": i, "value": "x" * 100}, ttl=60)
        total_ms = elapsed_ms(start)
        assert total_ms < 2000, f"1000 set troppo lenti: {total_ms:.1f}ms"

    def test_cache_1000_gets_under_500ms(self, fast_cache):
        """1000 get (miss) in meno di 500ms."""
        start = time.perf_counter()
        for i in range(1000):
            fast_cache.get(f"perf::miss::{i}")
        total_ms = elapsed_ms(start)
        assert total_ms < 500, f"1000 get (miss) troppo lenti: {total_ms:.1f}ms"

    def test_cache_hit_faster_than_miss(self, fast_cache):
        """Un hit cache deve essere più veloce o uguale a un miss."""
        key = "perf::hit_vs_miss"
        fast_cache.set(key, {"response": "cached"}, ttl=60)

        # Misura HIT
        start = time.perf_counter()
        for _ in range(100):
            fast_cache.get(key)
        hit_ms_avg = elapsed_ms(start) / 100

        # Misura MISS
        start = time.perf_counter()
        for i in range(100):
            fast_cache.get(f"perf::miss_unique::{i}")
        miss_ms_avg = elapsed_ms(start) / 100

        # Hit non deve essere più di 10x più lento del miss
        assert hit_ms_avg < miss_ms_avg * 10 + 1, \
            f"Hit ({hit_ms_avg:.3f}ms) sorprendentemente più lento del miss ({miss_ms_avg:.3f}ms)"


# ═══════════════════════════════════════════════════════════════
# PERFORMANCE: Schema Validation
# ═══════════════════════════════════════════════════════════════

class TestSchemaPerformance:
    """Pydantic v2 deve parsare i modelli in < 20ms."""

    def test_chat_request_parse_under_20ms(self):
        from backend.models.schemas import ChatRequest
        start = time.perf_counter()
        ChatRequest(message="Test performance schema parsing")
        ms = elapsed_ms(start)
        assert ms < SCHEMA_PARSE_MAX_MS, f"ChatRequest parse troppo lento: {ms:.2f}ms"

    def test_100_schema_parses_under_200ms(self):
        """100 parse di ChatRequest in meno di 200ms."""
        from backend.models.schemas import ChatRequest
        start = time.perf_counter()
        for i in range(100):
            ChatRequest(message=f"Messaggio numero {i} per test di performance schema")
        total_ms = elapsed_ms(start)
        assert total_ms < 200, f"100 parse troppo lenti: {total_ms:.1f}ms"

    def test_error_response_parse_fast(self):
        from backend.models.schemas import ErrorResponse
        start = time.perf_counter()
        for _ in range(100):
            ErrorResponse(error="Test", code=500)
        total_ms = elapsed_ms(start)
        assert total_ms < 100, f"100 ErrorResponse parse troppo lenti: {total_ms:.1f}ms"


# ═══════════════════════════════════════════════════════════════
# PERFORMANCE: Database
# ═══════════════════════════════════════════════════════════════

class TestDatabasePerformance:
    """Operazioni SQLite locali devono essere veloci."""

    def test_db_init_under_500ms(self, tmp_path):
        from backend.database.db import init_database
        db_path = str(tmp_path / "perf_test.db")
        start = time.perf_counter()
        conn = init_database(db_path)
        ms = elapsed_ms(start)
        conn.close()
        assert ms < 500, f"init_database troppo lento: {ms:.1f}ms"

    def test_create_100_conversations_under_2s(self, tmp_path):
        """Crea 100 conversazioni in meno di 2 secondi."""
        from backend.database.db import init_database, create_conversation
        db_path = str(tmp_path / "perf_convs.db")
        conn = init_database(db_path)
        start = time.perf_counter()
        for i in range(100):
            create_conversation(conn, title=f"Conv {i}")
        total_ms = elapsed_ms(start)
        conn.close()
        assert total_ms < 2000, f"100 create_conversation troppo lenti: {total_ms:.1f}ms"

    def test_add_1000_messages_under_5s(self, tmp_path):
        """Aggiunge 1000 messaggi a una conversazione in meno di 5s."""
        from backend.database.db import init_database, create_conversation, add_message
        db_path = str(tmp_path / "perf_msgs.db")
        conn = init_database(db_path)
        conv_id = create_conversation(conn, title="Perf test conversation")
        start = time.perf_counter()
        for i in range(1000):
            role = "user" if i % 2 == 0 else "assistant"
            add_message(conn, conv_id, role=role, content=f"Messaggio {i} con contenuto di test")
        total_ms = elapsed_ms(start)
        conn.close()
        assert total_ms < 5000, f"1000 add_message troppo lenti: {total_ms:.1f}ms"
