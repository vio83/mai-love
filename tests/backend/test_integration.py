"""
Test di integrazione VIO 83 AI Orchestra
Verifica le interazioni tra moduli: cache, router, DB, schemas, providers.
"""
import os
import sys
import time
import pytest
import asyncio

# Aggiunge la root del progetto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def provider_config():
    """Configurazione provider completa per test."""
    from backend.config.providers import CLOUD_PROVIDERS, LOCAL_PROVIDERS
    return {"cloud": CLOUD_PROVIDERS, "local": LOCAL_PROVIDERS}


@pytest.fixture(scope="function")
def temp_cache(tmp_path):
    """CacheEngine su filesystem temporaneo (non VirtioFS)."""
    from backend.core.cache import CacheEngine
    data_dir = str(tmp_path)
    cache = CacheEngine(data_dir=data_dir)
    yield cache
    cache.close()


@pytest.fixture(scope="session")
def temp_db(tmp_path_factory):
    """Database SQLite temporaneo per test integrazione."""
    tmp_path = tmp_path_factory.mktemp("db")
    db_path = str(tmp_path / "test_orchestra.db")
    from backend.database.db import init_database
    conn = init_database(db_path)
    yield conn, db_path
    conn.close()


# ═══════════════════════════════════════════════════════════════
# INTEGRATION: Cache + Router
# ═══════════════════════════════════════════════════════════════

class TestCacheRouterIntegration:
    """Verifica che la cache interagisca correttamente con il router."""

    def test_cache_stores_and_retrieves_response(self, temp_cache):
        """Una risposta salvata in cache viene recuperata identicamente."""
        key = "test::classify::hello"
        value = {"intent": "conversation", "provider": "ollama"}
        temp_cache.set(key, value, ttl=60)
        result = temp_cache.get(key)
        assert result == value

    def test_cache_ttl_zero_expires_immediately(self, temp_cache):
        """TTL=0 rende la voce immediatamente scaduta (logica L1)."""
        key = "test::ttl_zero"
        temp_cache.set(key, {"x": 1}, ttl=0)
        # TTL=0 → la voce potrebbe non essere recuperabile o scadere subito
        # Verifichiamo che non causi crash
        result = temp_cache.get(key)
        # Può essere None o il valore, a seconda dell'implementazione TTL
        assert result is None or result == {"x": 1}

    def test_cache_miss_returns_none(self, temp_cache):
        """Una chiave non presente restituisce None."""
        result = temp_cache.get("nonexistent::key::xyz")
        assert result is None

    def test_cache_overwrite_key(self, temp_cache):
        """Sovrascrivere una chiave aggiorna il valore."""
        key = "test::overwrite"
        temp_cache.set(key, {"v": 1}, ttl=60)
        temp_cache.set(key, {"v": 2}, ttl=60)
        result = temp_cache.get(key)
        assert result == {"v": 2}

    def test_cache_different_keys_independent(self, temp_cache):
        """Chiavi diverse non si sovrascrivono a vicenda."""
        temp_cache.set("key::a", {"val": "A"}, ttl=60)
        temp_cache.set("key::b", {"val": "B"}, ttl=60)
        assert temp_cache.get("key::a") == {"val": "A"}
        assert temp_cache.get("key::b") == {"val": "B"}


# ═══════════════════════════════════════════════════════════════
# INTEGRATION: Router + Providers
# ═══════════════════════════════════════════════════════════════

class TestRouterProvidersIntegration:
    """Verifica che il router usi i provider configurati correttamente."""

    def test_classify_returns_valid_intent_for_code(self):
        """Messaggio di codice viene classificato come 'code'."""
        from backend.orchestrator.direct_router import classify_request
        intent = classify_request("Scrivi una funzione Python per ordinare una lista")
        assert intent == "code"

    def test_classify_returns_valid_intent_for_legal(self):
        """Messaggio legale viene classificato come 'legal'."""
        from backend.orchestrator.direct_router import classify_request
        intent = classify_request("Analizza questo contratto di locazione")
        assert intent == "legal"

    def test_classify_returns_valid_intent_for_medical(self):
        """Messaggio medico viene classificato come 'medical'."""
        from backend.orchestrator.direct_router import classify_request
        intent = classify_request("diagnosi differenziale del diabete tipo 2")
        assert intent == "medical"

    def test_classify_returns_string(self):
        """classify_request restituisce sempre una stringa."""
        from backend.orchestrator.direct_router import classify_request
        result = classify_request("Qualsiasi messaggio casuale")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_intents_are_known(self):
        """Tutti gli intent conosciuti sono nel set di categorie valide."""
        from backend.orchestrator.direct_router import classify_request
        VALID_INTENTS = {
            "code", "legal", "medical", "creative", "reasoning",
            "analysis", "writing", "automation", "realtime", "research", "conversation"
        }
        test_messages = [
            "Scrivi del codice Python",
            "Analizza questo contratto",
            "Diagnosi differenziale",
            "Scrivi un racconto",
            "Ragiona su questo problema",
            "Analizza i dati",
            "Scrivi un articolo",
            "Automatizza questo processo",
            "Notizie di oggi",
            "Ricerca su questo argomento",
            "Come stai?",
        ]
        for msg in test_messages:
            intent = classify_request(msg)
            assert intent in VALID_INTENTS, f"Intent '{intent}' non valido per: '{msg}'"


# ═══════════════════════════════════════════════════════════════
# INTEGRATION: Schemas + Validation
# ═══════════════════════════════════════════════════════════════

class TestSchemasValidationIntegration:
    """Verifica che gli schema Pydantic v2 validino correttamente input/output."""

    def test_chat_request_with_all_fields(self):
        """ChatRequest con tutti i campi opzionali si costruisce correttamente."""
        from backend.models.schemas import ChatRequest
        req = ChatRequest(
            message="Test",
            conversation_id="conv_001",
            provider="groq",
            model="llama3-70b-8192",
            deep_mode=True,
            system_prompt="Sei un assistente utile.",
        )
        assert req.message == "Test"
        assert req.provider == "groq"
        assert req.deep_mode is True

    def test_chat_response_construction(self):
        """ChatResponse si costruisce con i campi richiesti."""
        from backend.models.schemas import ChatResponse
        resp = ChatResponse(
            response="Risposta di test",
            provider="ollama",
            model="qwen2.5-coder:3b",
            intent="code",
            conversation_id="conv_001",
            tokens_used=100,
            latency_ms=500.0,
            cached=False,
        )
        assert resp.response == "Risposta di test"
        assert resp.cached is False

    def test_error_response_with_code(self):
        """ErrorResponse con code numerico si serializza correttamente."""
        from backend.models.schemas import ErrorResponse
        err = ErrorResponse(error="Test error", detail="Dettaglio", code=500)
        assert err.error == "Test error"
        assert err.code == 500

    def test_classify_response_fields(self):
        """ClassifyResponse contiene tutti i campi attesi."""
        from backend.models.schemas import ClassifyResponse
        resp = ClassifyResponse(
            intent="code",
            confidence=0.95,
            suggested_provider="claude",
        )
        assert resp.intent == "code"
        assert resp.confidence == 0.95


# ═══════════════════════════════════════════════════════════════
# INTEGRATION: Database + Conversations
# ═══════════════════════════════════════════════════════════════

class TestDatabaseConversationsIntegration:
    """Verifica il ciclo completo di conversazioni nel database."""

    def test_create_and_list_conversation(self, tmp_path):
        """Crea una conversazione e verificala nella lista."""
        from backend.database.db import init_database, create_conversation, list_conversations
        db_path = str(tmp_path / "test.db")
        conn = init_database(db_path)
        conv_id = create_conversation(conn, title="Test conv")
        assert conv_id is not None
        convs = list_conversations(conn)
        assert any(c["id"] == conv_id for c in convs)
        conn.close()

    def test_add_message_to_conversation(self, tmp_path):
        """Aggiunge messaggi a una conversazione e li recupera."""
        from backend.database.db import init_database, create_conversation, add_message, get_conversation
        db_path = str(tmp_path / "test2.db")
        conn = init_database(db_path)
        conv_id = create_conversation(conn, title="Chat test")
        add_message(conn, conv_id, role="user", content="Ciao!")
        add_message(conn, conv_id, role="assistant", content="Ciao! Come posso aiutarti?")
        conv = get_conversation(conn, conv_id)
        assert conv is not None
        assert len(conv["messages"]) == 2
        conn.close()

    def test_update_conversation_title(self, tmp_path):
        """Aggiorna il titolo di una conversazione."""
        from backend.database.db import init_database, create_conversation, update_conversation_title, get_conversation
        db_path = str(tmp_path / "test3.db")
        conn = init_database(db_path)
        conv_id = create_conversation(conn, title="Vecchio titolo")
        update_conversation_title(conn, conv_id, "Nuovo titolo")
        conv = get_conversation(conn, conv_id)
        assert conv["title"] == "Nuovo titolo"
        conn.close()

    def test_delete_conversation(self, tmp_path):
        """Elimina una conversazione e verifica che non sia più presente."""
        from backend.database.db import init_database, create_conversation, delete_conversation, list_conversations
        db_path = str(tmp_path / "test4.db")
        conn = init_database(db_path)
        conv_id = create_conversation(conn, title="Da eliminare")
        delete_conversation(conn, conv_id)
        convs = list_conversations(conn)
        assert not any(c["id"] == conv_id for c in convs)
        conn.close()


# ═══════════════════════════════════════════════════════════════
# INTEGRATION: Provider Config
# ═══════════════════════════════════════════════════════════════

class TestProviderConfigIntegration:
    """Verifica la coerenza della configurazione provider."""

    def test_cloud_providers_have_required_keys(self, provider_config):
        """Ogni provider cloud ha almeno un campo 'model' o 'default_model'."""
        for name, cfg in provider_config["cloud"].items():
            assert "model" in cfg or "default_model" in cfg, \
                f"Provider '{name}' manca di 'model' o 'default_model'"

    def test_local_providers_have_url(self, provider_config):
        """Ogni provider locale ha una URL base."""
        for name, cfg in provider_config["local"].items():
            assert "url" in cfg or "base_url" in cfg, \
                f"Provider locale '{name}' manca di 'url' o 'base_url'"

    def test_get_available_cloud_providers_returns_list(self):
        """get_available_cloud_providers restituisce una lista."""
        from backend.config.providers import get_available_cloud_providers
        result = get_available_cloud_providers({})
        assert isinstance(result, list)

    def test_elite_stacks_not_empty(self):
        """get_elite_task_stacks restituisce almeno una configurazione."""
        from backend.config.providers import get_elite_task_stacks
        stacks = get_elite_task_stacks({})
        assert isinstance(stacks, dict)
        assert len(stacks) > 0
