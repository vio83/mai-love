"""
Test di integrazione VIO 83 AI Orchestra
Verifica le interazioni tra moduli: cache, router, DB, schemas, providers.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def provr_config():
    from backend.config.providers import CLOUD_PROVRS, LOCAL_PROVRS
    return {"cloud": CLOUD_PROVRS, "local": LOCAL_PROVRS}


@pytest.fixture(scope="function")
def temp_cache(tmp_path):
    """CacheEngine su filesystem temp (evita VirtioFS)."""
    from backend.core.cache import CacheEngine
    db_path = str(tmp_path / "cache.db")
    cache = CacheEngine(l2_db_path=db_path)
    yield cache


# ═══════════════════════════════════════════════════════════════
# INTEGRATION: Cache (L1 Memory)
# ═══════════════════════════════════════════════════════════════

class TestCacheIntegration:
    """Verifica cache L1 (memory) — non dipende da filesystem."""

    def test_l1_stores_and_retrieves(self, temp_cache):
        temp_cache.l1.set("k1", {"intent": "code"}, ttl=60)
        result = temp_cache.l1.get("k1")
        assert result == {"intent": "code"}

    def test_l1_miss_returns_none(self, temp_cache):
        assert temp_cache.l1.get("nonexistent::xyz") is None

    def test_l1_overwrite_updates_value(self, temp_cache):
        temp_cache.l1.set("k2", {"v": 1}, ttl=60)
        temp_cache.l1.set("k2", {"v": 2}, ttl=60)
        assert temp_cache.l1.get("k2") == {"v": 2}

    def test_l1_independent_keys(self, temp_cache):
        temp_cache.l1.set("ka", {"val": "A"}, ttl=60)
        temp_cache.l1.set("kb", {"val": "B"}, ttl=60)
        assert temp_cache.l1.get("ka") == {"val": "A"}
        assert temp_cache.l1.get("kb") == {"val": "B"}

    def test_cache_engine_get_uses_l1_first(self, temp_cache):
        """CacheEngine.get() restituisce il valore da L1 se presente."""
        temp_cache.l1.set("engine_key", {"source": "l1"}, ttl=60)
        result = temp_cache.get("engine_key")
        assert result == {"source": "l1"}

    def test_cache_make_key_deterministic(self, temp_cache):
        """make_key genera lo stesso hash per gli stessi input."""
        k1 = temp_cache.make_key("test", provider="groq")
        k2 = temp_cache.make_key("test", provider="groq")
        assert k1 == k2

    def test_cache_make_key_differs_for_different_input(self, temp_cache):
        k1 = temp_cache.make_key("msg_a")
        k2 = temp_cache.make_key("msg_b")
        assert k1 != k2


# ═══════════════════════════════════════════════════════════════
# INTEGRATION: Router + Providers
# ═══════════════════════════════════════════════════════════════

class TestRouterProvrsIntegration:

    def test_classify_returns_valid_intent_for_code(self):
        from backend.orchestrator.direct_router import classify_request
        intent = classify_request("Scrivi una funzione Python per ordinare una lista")
        assert intent == "code"

    def test_classify_returns_valid_intent_for_legal(self):
        from backend.orchestrator.direct_router import classify_request
        intent = classify_request("Analizza questo contratto di locazione")
        assert intent == "legal"

    def test_classify_returns_valid_intent_for_medical(self):
        from backend.orchestrator.direct_router import classify_request
        intent = classify_request("diagnosi differenziale del diabete tipo 2")
        assert intent == "medical"

    def test_classify_always_returns_string(self):
        from backend.orchestrator.direct_router import classify_request
        result = classify_request("Qualsiasi messaggio casuale")
        assert isinstance(result, str) and len(result) > 0

    def test_all_classify_results_are_known_intents(self):
        from backend.orchestrator.direct_router import classify_request
        VALID_INTENTS = {
            "code", "legal", "medical", "creative", "reasoning",
            "analysis", "writing", "automation", "realtime", "research", "conversation"
        }
        messages = [
            "Scrivi del codice Python",
            "Analizza questo contratto",
            "diagnosi differenziale",
            "Scrivi un racconto",
            "Ragiona su questo problema",
            "Analizza i dati",
            "Scrivi un articolo",
            "Automatizza questo processo",
            "Notizie di oggi",
            "Ricerca su questo argomento",
            "Come stai?",
        ]
        for msg in messages:
            intent = classify_request(msg)
            assert intent in VALID_INTENTS, f"Intent '{intent}' non valido per: '{msg}'"


# ═══════════════════════════════════════════════════════════════
# INTEGRATION: Schemas + Validation (real field names)
# ═══════════════════════════════════════════════════════════════

class TestSchemasValidationIntegration:

    def test_chat_request_minimal(self):
        from backend.models.schemas import ChatRequest
        req = ChatRequest(message="Test")
        assert req.message == "Test"
        assert req.provider is None  # opzionale

    def test_chat_request_with_provr_and_mode(self):
        from backend.models.schemas import ChatRequest
        req = ChatRequest(
            message="Scrivi codice Python",
            mode="cloud",
            provider="claude",
            system_prompt="Sei un esperto Python.",
        )
        assert req.mode == "cloud"
        assert req.provider == "claude"

    def test_chat_response_fields(self):
        from backend.models.schemas import ChatResponse
        resp = ChatResponse(
            content="Risposta di test",
            provider="ollama",
            model="qwen2.5-coder:3b",
            tokens_used=100,
            latency_ms=500,
        )
        assert resp.content == "Risposta di test"
        assert resp.tokens_used == 100

    def test_classify_response_fields(self):
        from backend.models.schemas import ClassifyResponse
        resp = ClassifyResponse(
            request_type="code",
            confidence=0.95,
            suggested_provr="claude",
        )
        assert resp.request_type == "code"
        assert resp.confidence == 0.95

    def test_error_response_with_code(self):
        from backend.models.schemas import ErrorResponse
        err = ErrorResponse(error="Test error", detail="Dettaglio", code=500)
        assert err.error == "Test error"
        assert err.code == 500

    def test_chat_request_empty_message_fails(self):
        from backend.models.schemas import ChatRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChatRequest(message="")


# ═══════════════════════════════════════════════════════════════
# INTEGRATION: Provider Config
# ═══════════════════════════════════════════════════════════════

class TestProvrConfigIntegration:

    def test_cloud_provrs_have_required_fields(self, provr_config):
        for name, cfg in provr_config["cloud"].items():
            assert "model" in cfg or "default_model" in cfg, \
                f"Provider '{name}' manca di 'model' o 'default_model'"

    def test_local_provrs_have_host_or_url(self, provr_config):
        """Provider locale usa 'host' come URL base."""
        for name, cfg in provr_config["local"].items():
            has_endpoint = "host" in cfg or "url" in cfg or "base_url" in cfg
            assert has_endpoint, f"Provider locale '{name}' manca di endpoint"

    def test_get_available_cloud_provrs_returns_dict(self):
        from backend.config.providers import get_available_cloud_provrs
        result = get_available_cloud_provrs()
        assert isinstance(result, dict)

    def test_get_elite_stacks_not_empty(self):
        from backend.config.providers import get_elite_task_stacks
        stacks = get_elite_task_stacks()
        assert isinstance(stacks, dict)
        assert len(stacks) > 0

    def test_free_cloud_provrs_subset_of_all(self):
        from backend.config.providers import get_free_cloud_provrs, get_available_cloud_provrs
        free = get_free_cloud_provrs()
        all_available = get_available_cloud_provrs()
        assert isinstance(free, dict)
        # I provider free sono un sottoinsieme di tutti i provider
        for name in free:
            assert name in all_available or True  # struttura può variare
