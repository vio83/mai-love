# ============================================================
# VIO 83 AI ORCHESTRA — Test FeatherMemory™
# Copyright © 2026 Viorica Porcu (vio83) — All rights reserved
# ============================================================
"""
Test suite per FeatherMemory™ — 50 test totali

Coverage:
  TestMessageCompactor  (12 test) — compressione, dedup, batch
  TestContextWindow     (10 test) — finestra scorrevole, promozione
  TestSemanticDigest    ( 8 test) — digest, keywords, prefix
  TestTokenAllocator    ( 8 test) — budget, limiti, compressione
  TestMemoryPool        ( 6 test) — pool, eviction, stats
  TestFeatherMemory     ( 6 test) — facade, prepare, singleton
"""

import time
import pytest
from backend.core.feather_memory import (
    MessageCompactor, CompactMessage,
    ContextWindow,
    SemanticDigest,
    TokenAllocator,
    MemoryPool,
    ResponseAccelerator, AcceleratorConfig,
    FeatherMemory, get_feather_memory,
)


# ═══════════════════════════════════════════════
# TestMessageCompactor — 12 test
# ═══════════════════════════════════════════════

class TestMessageCompactor:

    def setup_method(self):
        self.mc = MessageCompactor()

    def test_compact_returns_compact_message(self):
        cm = self.mc.compact("user", "ciao come stai")
        assert isinstance(cm, CompactMessage)
        assert cm.role == "user"

    def test_compact_strips_whitespace(self):
        cm = self.mc.compact("user", "  ciao    come   stai  ")
        assert "  " not in cm.content
        assert cm.content == "ciao come stai"

    def test_compact_collapses_newlines(self):
        cm = self.mc.compact("user", "riga1\n\n\n\n\nriga2")
        assert "\n\n\n" not in cm.content

    def test_compact_collapses_punctuation(self):
        cm = self.mc.compact("user", "ciao!!!!!!!")
        assert cm.content == "ciao!!"

    def test_compact_removes_fillers_user(self):
        cm = self.mc.compact("user", "ehm diciamo che tipo forse sì")
        assert "ehm" not in cm.content
        assert "tipo" not in cm.content

    def test_compact_keeps_fillers_assistant(self):
        cm = self.mc.compact("assistant", "basically this is the answer")
        assert "basically" in cm.content  # non rimuove filler da assistant

    def test_token_est_reasonable(self):
        cm = self.mc.compact("user", "a" * 100)
        assert 20 <= cm.token_est <= 40  # ~100/4 + 1 = 26

    def test_hash_6_is_6_hex(self):
        cm = self.mc.compact("user", "test message")
        assert len(cm.hash_6) == 6
        assert all(c in "0123456789abcdef" for c in cm.hash_6)

    def test_compact_batch_deduplicates(self):
        msgs = [
            {"role": "user", "content": "stessa domanda"},
            {"role": "user", "content": "stessa domanda"},
            {"role": "user", "content": "diversa domanda"},
        ]
        batch = self.mc.compact_batch(msgs)
        assert len(batch) == 2  # dedup

    def test_compact_batch_preserves_order(self):
        msgs = [
            {"role": "user", "content": "primo"},
            {"role": "assistant", "content": "risposta"},
            {"role": "user", "content": "secondo"},
        ]
        batch = self.mc.compact_batch(msgs)
        assert batch[0].content == "primo"
        assert batch[1].content == "risposta"
        assert batch[2].content == "secondo"

    def test_to_api_format(self):
        cms = [CompactMessage("user","ciao",2,0.0,"aaa111")]
        result = MessageCompactor.to_api_format(cms)
        assert result == [{"role": "user", "content": "ciao"}]

    def test_total_tokens(self):
        cms = [
            CompactMessage("user","a",10,0.0,"a1"),
            CompactMessage("user","b",20,0.0,"b2"),
        ]
        assert MessageCompactor.total_tokens(cms) == 30


# ═══════════════════════════════════════════════
# TestContextWindow — 10 test
# ═══════════════════════════════════════════════

class TestContextWindow:

    def setup_method(self):
        self.cw = ContextWindow()
        self.mc = MessageCompactor()

    def _add_n(self, n: int):
        for i in range(n):
            cm = self.mc.compact("user" if i%2==0 else "assistant", f"messaggio {i}")
            self.cw.add(cm)

    def test_add_single_message(self):
        cm = self.mc.compact("user", "ciao")
        self.cw.add(cm)
        assert self.cw.stats["active"] == 1

    def test_active_max_size(self):
        self._add_n(20)
        assert self.cw.stats["active"] <= ContextWindow.ACTIVE_SIZE

    def test_summary_created_on_overflow(self):
        self._add_n(12)
        assert self.cw.stats["summary"] > 0

    def test_archive_tracks_hashes(self):
        self._add_n(15)
        assert self.cw.stats["archive"] > 0

    def test_build_context_empty(self):
        ctx = self.cw.build_context()
        assert ctx == []

    def test_build_context_with_system(self):
        cm = self.mc.compact("user", "domanda")
        self.cw.add(cm)
        ctx = self.cw.build_context("Sei un assistente.")
        assert ctx[0]["role"] == "system"
        assert ctx[1]["role"] == "user"

    def test_build_context_includes_summary(self):
        self._add_n(15)
        ctx = self.cw.build_context()
        # Ci dovrebbe essere un system message con riepilogo
        system_msgs = [m for m in ctx if m["role"] == "system"]
        assert len(system_msgs) >= 1
        assert "Riepilogo" in system_msgs[0]["content"]

    def test_memory_bytes_grows(self):
        mem0 = self.cw.memory_bytes()
        self._add_n(5)
        mem5 = self.cw.memory_bytes()
        assert mem5 > mem0

    def test_stats_structure(self):
        stats = self.cw.stats
        assert "active" in stats
        assert "summary" in stats
        assert "archive" in stats
        assert "active_tokens" in stats

    def test_summary_max_respected(self):
        self._add_n(50)
        assert self.cw.stats["summary"] <= ContextWindow.SUMMARY_MAX


# ═══════════════════════════════════════════════
# TestSemanticDigest — 8 test
# ═══════════════════════════════════════════════

class TestSemanticDigest:

    def setup_method(self):
        self.sd = SemanticDigest()
        self.mc = MessageCompactor()

    def _make_msgs(self, texts):
        return [self.mc.compact("user" if i%2==0 else "assistant", t)
                for i, t in enumerate(texts)]

    def test_empty_returns_empty(self):
        assert self.sd.digest([]) == ""

    def test_digest_returns_string(self):
        msgs = self._make_msgs(["come funziona Python?", "Python è un linguaggio di programmazione"])
        d = self.sd.digest(msgs)
        assert isinstance(d, str)
        assert len(d) > 0

    def test_digest_contains_keywords(self):
        msgs = self._make_msgs([
            "spiegami l'intelligenza artificiale",
            "l'intelligenza artificiale è un campo dell'informatica",
        ])
        d = self.sd.digest(msgs)
        assert "intelligenza" in d.lower() or "artificiale" in d.lower()

    def test_digest_max_length(self):
        msgs = self._make_msgs(["testo lungo " * 100] * 10)
        d = self.sd.digest(msgs)
        assert len(d) <= SemanticDigest.MAX_DIGEST_CHARS + 10  # piccolo margine

    def test_digest_has_user_requests(self):
        msgs = self._make_msgs(["come stai?", "sto bene grazie"])
        d = self.sd.digest(msgs)
        assert "Richieste utente" in d or "come stai" in d.lower()

    def test_digest_to_system_prefix_empty(self):
        assert self.sd.digest_to_system_prefix("") == ""

    def test_digest_to_system_prefix_wraps(self):
        prefix = self.sd.digest_to_system_prefix("test digest content")
        assert "FeatherMemory" in prefix
        assert "test digest content" in prefix

    def test_digest_filters_stopwords(self):
        msgs = self._make_msgs(["il gatto mangia la pizza calda"])
        d = self.sd.digest(msgs)
        # Stopword "il" e "la" non dovrebbero essere nelle parole chiave
        if "Parole chiave" in d:
            kw_section = d.split("Parole chiave:")[-1]
            words = kw_section.lower().split(",")
            assert not any(w.strip() == "il" for w in words)


# ═══════════════════════════════════════════════
# TestTokenAllocator — 8 test
# ═══════════════════════════════════════════════

class TestTokenAllocator:

    def setup_method(self):
        self.ta = TokenAllocator()

    def test_allocate_returns_dict(self):
        result = self.ta.allocate("claude", 100, 1000)
        assert isinstance(result, dict)
        assert "max_output_tokens" in result

    def test_claude_has_200k_budget(self):
        result = self.ta.allocate("claude", 0, 0)
        assert result["total_budget"] == 200_000

    def test_groq_has_8k_budget(self):
        result = self.ta.allocate("groq", 0, 0)
        assert result["total_budget"] == 8_192

    def test_needs_compression_when_over_budget(self):
        result = self.ta.allocate("groq", 100, 7000)
        assert result["needs_compression"] is True

    def test_no_compression_when_under_budget(self):
        result = self.ta.allocate("claude", 100, 1000)
        assert result["needs_compression"] is False

    def test_utilization_between_0_and_1(self):
        result = self.ta.allocate("claude", 500, 5000)
        assert 0.0 <= result["utilization"] <= 1.0

    def test_optimal_output_code(self):
        tok = self.ta.optimal_output_tokens("claude", "code")
        assert tok >= 512

    def test_optimal_output_simple(self):
        tok = self.ta.optimal_output_tokens("ollama", "simple")
        assert tok <= 2048


# ═══════════════════════════════════════════════
# TestMemoryPool — 6 test
# ═══════════════════════════════════════════════

class TestMemoryPool:

    def setup_method(self):
        self.pool = MemoryPool()

    def test_get_or_create_new(self):
        cw = self.pool.get_or_create("conv-1")
        assert isinstance(cw, ContextWindow)
        assert self.pool.stats["active_conversations"] == 1

    def test_get_or_create_existing(self):
        cw1 = self.pool.get_or_create("conv-1")
        cw2 = self.pool.get_or_create("conv-1")
        assert cw1 is cw2  # stessa istanza

    def test_remove(self):
        self.pool.get_or_create("conv-1")
        self.pool.remove("conv-1")
        assert self.pool.stats["active_conversations"] == 0

    def test_eviction_at_max(self):
        for i in range(self.pool.MAX_CONVERSATIONS + 10):
            self.pool.get_or_create(f"conv-{i}")
        assert self.pool.stats["active_conversations"] <= self.pool.MAX_CONVERSATIONS

    def test_stats_structure(self):
        stats = self.pool.stats
        assert "active_conversations" in stats
        assert "total_memory_bytes" in stats
        assert "max_memory_mb" in stats

    def test_memory_tracking(self):
        cw = self.pool.get_or_create("conv-x")
        mc = MessageCompactor()
        cw.add(mc.compact("user", "test " * 100))
        assert self.pool.stats["total_memory_bytes"] > 0


# ═══════════════════════════════════════════════
# TestFeatherMemory — 6 test
# ═══════════════════════════════════════════════

class TestFeatherMemory:

    def setup_method(self):
        self.fm = FeatherMemory()

    def test_singleton(self):
        f1 = get_feather_memory()
        f2 = get_feather_memory()
        assert f1 is f2

    def test_prepare_returns_dict(self):
        result = self.fm.prepare("ciao", provr="ollama")
        assert "messages" in result
        assert "max_tokens" in result
        assert "compression" in result

    def test_prepare_under_3ms(self):
        result = self.fm.prepare("ciao come stai oggi?", provr="ollama")
        assert result["compression"]["prepare_ms"] < 3.0  # target <2.5ms

    def test_prepare_with_history(self):
        history = [
            {"role": "user", "content": "domanda precedente"},
            {"role": "assistant", "content": "risposta precedente"},
        ]
        result = self.fm.prepare("nuova domanda", history=history, provr="claude")
        assert len(result["messages"]) >= 2

    def test_compact_message_works(self):
        cm = self.fm.compact_message("user", "test   message   here")
        assert "  " not in cm.content

    def test_stats_has_version(self):
        stats = self.fm.stats
        assert "version" in stats
        assert "FeatherMemory" in stats["version"]
