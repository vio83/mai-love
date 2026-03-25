"""
VIO 83 AI ORCHESTRA — Network Reliability Tests
Tests: retry engine on transient HTTP failures and no retry on permanent client errors
"""
import unittest

from backend.core.network import RetryEngine, HAS_HTTPX


@unittest.skipUnless(HAS_HTTPX, "httpx richiesto per testare HTTPStatusError")
class TestRetryEngine(unittest.IsolatedAsyncioTestCase):

    async def test_retries_on_retryable_http_status(self):
        import httpx

        engine = RetryEngine(max_retries=2, base_delay=0.0, max_delay=0.0)
        attempts = {"count": 0}

        async def flaky_call():
            attempts["count"] += 1
            if attempts["count"] < 3:
                request = httpx.Request("POST", "https://api.example.com/chat")
                response = httpx.Response(503, request=request, text="temporary outage")
                raise httpx.HTTPStatusError("503", request=request, response=response)
            return {"ok": True}

        result = await engine.execute(flaky_call)

        self.assertEqual(result, {"ok": True})
        self.assertEqual(attempts["count"], 3)

    async def test_does_not_retry_on_non_retryable_http_status(self):
        import httpx

        engine = RetryEngine(max_retries=2, base_delay=0.0, max_delay=0.0)
        attempts = {"count": 0}

        async def bad_request():
            attempts["count"] += 1
            request = httpx.Request("POST", "https://api.example.com/chat")
            response = httpx.Response(400, request=request, text="bad request")
            raise httpx.HTTPStatusError("400", request=request, response=response)

        with self.assertRaises(httpx.HTTPStatusError):
            await engine.execute(bad_request)

        self.assertEqual(attempts["count"], 1)