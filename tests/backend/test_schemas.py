"""
VIO 83 AI ORCHESTRA — Schema Validation Tests
Tests: Pydantic models for API request/response validation
"""
import unittest

from backend.models.schemas import (
    ChatRequest, ChatResponse, ClassifyRequest, ClassifyResponse,
    HealthResponse, ErrorResponse
)


class TestChatRequest(unittest.TestCase):

    def test_minimal_valid_request(self):
        req = ChatRequest(message="Hello")
        self.assertEqual(req.message, "Hello")

    def test_request_with_all_fields(self):
        req = ChatRequest(
            message="Test",
            mode="local",
            model="llama3",
            max_tokens=512,
            temperature=0.7
        )
        self.assertEqual(req.mode, "local")
        self.assertEqual(req.model, "llama3")
        self.assertEqual(req.max_tokens, 512)

    def test_empty_message_raises_validation_error(self):
        """ChatRequest richiede min_length=1 — stringa vuota non valida."""
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            ChatRequest(message="")

    def test_system_prompt_too_long_raises_validation_error(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            ChatRequest(message="ok", system_prompt="x" * 12001)


class TestClassifyRequest(unittest.TestCase):

    def test_classify_creation(self):
        req = ClassifyRequest(message="Scrivi codice Python")
        self.assertEqual(req.message, "Scrivi codice Python")


class TestClassifyResponse(unittest.TestCase):

    def test_response_creation(self):
        resp = ClassifyResponse(
            request_type="code",
            confidence=0.95,
            suggested_provr="ollama"
        )
        self.assertEqual(resp.request_type, "code")


class TestErrorResponse(unittest.TestCase):

    def test_error_response(self):
        """ErrorResponse richiede campo 'error' (obbligatorio), 'detail' opzionale."""
        resp = ErrorResponse(error="Something went wrong", detail="Extra context", code=422)
        self.assertEqual(resp.error, "Something went wrong")
        self.assertEqual(resp.detail, "Extra context")
        self.assertEqual(resp.code, 422)

    def test_error_response_minimal(self):
        """ErrorResponse con solo il campo obbligatorio 'error'."""
        resp = ErrorResponse(error="Minimal error")
        self.assertEqual(resp.error, "Minimal error")
        self.assertIsNone(resp.detail)
        self.assertEqual(resp.code, 500)  # default


if __name__ == "__main__":
    unittest.main()
