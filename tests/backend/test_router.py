"""
VIO 83 AI ORCHESTRA — Router / Orchestrator Tests
Tests: classify_request intent detection, provider routing
"""
import unittest
from unittest.mock import patch

from backend.core.errors import ProvrException
from backend.orchestrator.direct_router import classify_request, _resolve_cloud_api_key


class TestClassifyRequest(unittest.TestCase):

    def test_code_classification(self):
        self.assertEqual(classify_request("scrivi una funzione python"), "code")
        self.assertEqual(classify_request("debug this JavaScript error"), "code")
        self.assertEqual(classify_request("crea un algoritmo di sorting"), "code")

    def test_medical_classification(self):
        # Usa keywords presenti in KEYWORDS["medical"]: diagnosi, clinico, oncologia
        self.assertEqual(classify_request("diagnosi differenziale del diabete tipo 2"), "medical")
        self.assertEqual(classify_request("linee guida cliniche oncologia avanzata"), "medical")

    def test_legal_classification(self):
        self.assertEqual(classify_request("clausola contrattuale GDPR"), "legal")
        self.assertEqual(classify_request("norma sulla privacy dei dati"), "legal")

    def test_creative_classification(self):
        self.assertEqual(classify_request("scrivi una poesia sulla luna"), "creative")
        self.assertEqual(classify_request("write a short story about AI"), "creative")

    def test_reasoning_classification(self):
        self.assertEqual(classify_request("spiega perché il cielo è blu"), "reasoning")
        self.assertEqual(classify_request("come funziona la fotosintesi"), "reasoning")

    def test_conversation_fallback(self):
        self.assertEqual(classify_request("ciao come stai"), "conversation")
        self.assertEqual(classify_request("ok grazie"), "conversation")

    def test_analysis_classification(self):
        result = classify_request("analizza questi dati CSV")
        self.assertIn(result, ("analysis", "code", "conversation"))

    def test_empty_message_does_not_crash(self):
        result = classify_request("")
        self.assertIsInstance(result, str)


class TestCloudProviderValidation(unittest.TestCase):

    def test_missing_cloud_api_key_raises_typed_exception(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ProvrException) as ctx:
                _resolve_cloud_api_key("claude")

        self.assertIn("API key mancante", str(ctx.exception))


class TestCloudStreamingSignature(unittest.TestCase):
    """Verifica che call_cloud_streaming sia importabile e sia un async generator."""

    def test_call_cloud_streaming_is_async_generator(self):
        from backend.orchestrator.direct_router import call_cloud_streaming
        import inspect
        self.assertTrue(inspect.isasyncgenfunction(call_cloud_streaming))

    def test_call_cloud_streaming_accepts_expected_params(self):
        from backend.orchestrator.direct_router import call_cloud_streaming
        import inspect
        sig = inspect.signature(call_cloud_streaming)
        param_names = list(sig.parameters.keys())
        self.assertIn("messages", param_names)
        self.assertIn("provider", param_names)
        self.assertIn("model", param_names)


class TestExtendedThinkingPayload(unittest.TestCase):
    """Verifica che _call_cloud_claude costruisca il payload thinking corretto."""

    def test_claude_thinking_payload(self):
        import asyncio
        mock_response = {
            "content": [{"type": "text", "text": "risposta"}],
            "usage": {"input_tokens": 10, "output_tokens": 20},
        }
        with patch("backend.orchestrator.direct_router._http_post_json", return_value=mock_response) as mock_http, \
             patch("backend.orchestrator.direct_router._resolve_cloud_api_key", return_value="test-key"):
            from backend.orchestrator.direct_router import _call_cloud_claude
            result = asyncio.run(_call_cloud_claude(
                model="claude-sonnet-4-20250514",
                messages=[{"role": "user", "content": "test"}],
                temperature=0.7,
                max_tokens=1024,
                show_thinking=True,
            ))
            payload = mock_http.call_args.kwargs.get("payload") or mock_http.call_args[1].get("payload")
        self.assertIn("thinking", payload)
        self.assertEqual(payload["thinking"]["type"], "enabled")
        self.assertEqual(payload["temperature"], 1)
        self.assertIn("content", result)


if __name__ == "__main__":
    unittest.main()
