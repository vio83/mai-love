"""
VIO 83 AI ORCHESTRA — Test per feature G1–G4, G6
Tests: structured output, thinking blocks, parallel tools, tracing, retry
"""
import asyncio
import json
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models.schemas import ChatRequest, ChatResponse, StructuredOutputFormat


# ═══════════════════════════════════════════════════════════════
# G1: Structured Output — Schema tests
# ═══════════════════════════════════════════════════════════════

class TestStructuredOutputFormat(unittest.TestCase):

    def test_json_object_default(self):
        fmt = StructuredOutputFormat()
        self.assertEqual(fmt.type, "json_object")
        self.assertIsNone(fmt.json_schema)

    def test_json_schema_with_schema(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        fmt = StructuredOutputFormat(type="json_schema", json_schema=schema)
        self.assertEqual(fmt.type, "json_schema")
        self.assertEqual(fmt.json_schema, schema)

    def test_invalid_type_rejected(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            StructuredOutputFormat(type="xml")


class TestChatRequestG1(unittest.TestCase):

    def test_response_format_absent_by_default(self):
        req = ChatRequest(message="test")
        self.assertIsNone(req.response_format)

    def test_response_format_json_object(self):
        req = ChatRequest(
            message="dammi json",
            response_format=StructuredOutputFormat(type="json_object"),
        )
        self.assertEqual(req.response_format.type, "json_object")

    def test_response_format_json_schema(self):
        schema = {"type": "object", "properties": {"x": {"type": "number"}}}
        req = ChatRequest(
            message="dammi schema",
            response_format=StructuredOutputFormat(type="json_schema", json_schema=schema),
        )
        self.assertEqual(req.response_format.json_schema, schema)


# ═══════════════════════════════════════════════════════════════
# G3: Thinking / Reasoning blocks — Schema tests
# ═══════════════════════════════════════════════════════════════

class TestChatRequestG3(unittest.TestCase):

    def test_show_thinking_default_false(self):
        req = ChatRequest(message="test")
        self.assertFalse(req.show_thinking)

    def test_show_thinking_enabled(self):
        req = ChatRequest(message="test", show_thinking=True)
        self.assertTrue(req.show_thinking)


class TestChatResponseThinking(unittest.TestCase):

    def test_thinking_absent_by_default(self):
        resp = ChatResponse(
            content="ciao", provider="ollama", model="llama3",
            tokens_used=10, latency_ms=100, request_type="conversation",
        )
        self.assertIsNone(resp.thinking)

    def test_thinking_populated(self):
        resp = ChatResponse(
            content="risultato", provider="claude", model="sonnet",
            tokens_used=200, latency_ms=500, request_type="reasoning",
            thinking="Step 1: analisi\nStep 2: sintesi",
        )
        self.assertIn("Step 1", resp.thinking)


# ═══════════════════════════════════════════════════════════════
# G6: Retry delay con Retry-After
# ═══════════════════════════════════════════════════════════════

class TestRetryDelay(unittest.TestCase):

    def test_basic_exponential_backoff(self):
        from backend.orchestrator.direct_router import _retry_delay_seconds
        for attempt in range(5):
            delay = _retry_delay_seconds(attempt)
            # Should be > 0 and capped at 60
            self.assertGreater(delay, 0)
            self.assertLessEqual(delay, 60.0)

    def test_retry_after_respected(self):
        from backend.orchestrator.direct_router import _retry_delay_seconds
        delay = _retry_delay_seconds(0, retry_after=10.0)
        # Must be at least 10 (the Retry-After value)
        self.assertGreaterEqual(delay, 10.0)
        self.assertLessEqual(delay, 60.0)

    def test_cap_at_60(self):
        from backend.orchestrator.direct_router import _retry_delay_seconds
        delay = _retry_delay_seconds(10, retry_after=100.0)
        self.assertLessEqual(delay, 60.0)


class TestExtractRetryAfter(unittest.TestCase):

    def test_numeric_header(self):
        from backend.orchestrator.direct_router import _extract_retry_after
        headers = {"retry-after": "5"}
        self.assertAlmostEqual(_extract_retry_after(headers), 5.0, places=1)

    def test_missing_header(self):
        from backend.orchestrator.direct_router import _extract_retry_after
        self.assertIsNone(_extract_retry_after({}))

    def test_invalid_header(self):
        from backend.orchestrator.direct_router import _extract_retry_after
        self.assertIsNone(_extract_retry_after({"retry-after": "not-a-number"}))


# ═══════════════════════════════════════════════════════════════
# G2: Parallel tool calling — execution tests
# ═══════════════════════════════════════════════════════════════

class TestParallelToolExecution(unittest.TestCase):

    def test_asyncio_gather_runs_concurrently(self):
        """Verify that asyncio.gather actually runs tasks in parallel."""
        call_times = []

        async def slow_task(task_id):
            start = time.time()
            await asyncio.sleep(0.1)
            call_times.append((task_id, time.time() - start))
            return task_id

        async def run():
            results = await asyncio.gather(
                slow_task("a"), slow_task("b"), slow_task("c"),
                return_exceptions=True,
            )
            return results

        results = asyncio.run(run())
        self.assertEqual(set(results), {"a", "b", "c"})
        # All 3 should finish in ~0.1s total, not ~0.3s
        total_time = max(t for _, t in call_times)
        self.assertLess(total_time, 0.25)  # generous bound

    def test_gather_handles_exceptions(self):
        """Verify that return_exceptions=True captures errors."""
        async def failing():
            raise ValueError("boom")

        async def succeeding():
            return "ok"

        async def run():
            return await asyncio.gather(
                succeeding(), failing(), succeeding(),
                return_exceptions=True,
            )

        results = asyncio.run(run())
        self.assertEqual(results[0], "ok")
        self.assertIsInstance(results[1], ValueError)
        self.assertEqual(results[2], "ok")


# ═══════════════════════════════════════════════════════════════
# G4: Tracing — noop mode tests
# ═══════════════════════════════════════════════════════════════

class TestTracingNoop(unittest.TestCase):
    """Test tracing module in noop mode (OTel disabled or not installed)."""

    def test_traced_span_noop(self):
        from backend.core.tracing import traced_span
        with traced_span("test_span", {"key": "val"}) as span:
            self.assertIsNone(span)
        # Should not raise

    def test_record_ai_call_noop(self):
        from backend.core.tracing import record_ai_call
        # Should not raise with span=None
        record_ai_call(None, provider="test", model="test", tokens_used=0)

    def test_tracing_stats(self):
        from backend.core.tracing import tracing_stats
        stats = tracing_stats()
        self.assertIn("otel_available", stats)
        self.assertIn("tracer_active", stats)
        self.assertIsInstance(stats["otel_available"], bool)

    def test_init_tracing_disabled(self):
        from backend.core.tracing import init_tracing
        with patch.dict("os.environ", {"OTEL_ENABLED": "false"}):
            result = init_tracing()
            self.assertFalse(result)


# ═══════════════════════════════════════════════════════════════
# G1+G3: orchestrate() signature tests
# ═══════════════════════════════════════════════════════════════

class TestOrchestrateSignature(unittest.TestCase):
    """Verify that orchestrate() accepts the new G1/G3 parameters."""

    def test_orchestrate_has_response_format_param(self):
        import inspect
        from backend.orchestrator.direct_router import orchestrate
        sig = inspect.signature(orchestrate)
        self.assertIn("response_format", sig.parameters)

    def test_orchestrate_has_show_thinking_param(self):
        import inspect
        from backend.orchestrator.direct_router import orchestrate
        sig = inspect.signature(orchestrate)
        self.assertIn("show_thinking", sig.parameters)

    def test_call_cloud_has_new_params(self):
        import inspect
        from backend.orchestrator.direct_router import call_cloud
        sig = inspect.signature(call_cloud)
        self.assertIn("response_format", sig.parameters)
        self.assertIn("show_thinking", sig.parameters)


if __name__ == "__main__":
    unittest.main()
