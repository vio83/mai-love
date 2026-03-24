"""
VIO 83 AI ORCHESTRA — Router / Orchestrator Tests
Tests: classify_request intent detection, provr routing
"""
import unittest

from backend.orchestrator.direct_router import classify_request


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


if __name__ == "__main__":
    unittest.main()
