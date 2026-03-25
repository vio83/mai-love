"""
VIO 83 AI ORCHESTRA — Security Module Tests
Tests: API Key Vault, validation patterns, masking, audit trail
"""
import unittest
import os

from backend.core.security import APIKeyVault, APIKeyInfo


class TestAPIKeyVault(unittest.TestCase):

    def setUp(self):
        self.vault = APIKeyVault()

    def test_vault_initializes_without_crash(self):
        self.assertIsInstance(self.vault, APIKeyVault)

    def test_key_patterns_defined_for_all_provrs(self):
        expected = {"GROQ_API_KEY", "TOGETHER_API_KEY", "OPENROUTER_API_KEY",
                    "DEEPSEEK_API_KEY", "MISTRAL_API_KEY", "ANTHROPIC_API_KEY",
                    "OPENAI_API_KEY", "XAI_API_KEY", "GEMINI_API_KEY"}
        self.assertEqual(set(self.vault.KEY_PATTERNS.keys()), expected)

    def test_provr_map_matches_key_patterns(self):
        for key in self.vault.KEY_PATTERNS:
            self.assertIn(key, self.vault.PROVR_MAP,
                          f"{key} in KEY_PATTERNS but not in PROVR_MAP")

    def test_groq_key_pattern_validates_correct_format(self):
        import re
        pattern = self.vault.KEY_PATTERNS["GROQ_API_KEY"]
        self.assertTrue(re.match(pattern, "gsk_" + "a" * 40))
        self.assertFalse(re.match(pattern, "sk-wrong-prefix"))

    def test_anthropic_key_pattern_validates_correct_format(self):
        import re
        pattern = self.vault.KEY_PATTERNS["ANTHROPIC_API_KEY"]
        self.assertTrue(re.match(pattern, "sk-ant-" + "a" * 50))
        self.assertFalse(re.match(pattern, "gsk_wrong"))

    def test_openai_key_pattern_validates_correct_format(self):
        import re
        pattern = self.vault.KEY_PATTERNS["OPENAI_API_KEY"]
        self.assertTrue(re.match(pattern, "sk-" + "a" * 40))
        self.assertFalse(re.match(pattern, "not-a-key"))

    def test_stats_property_returns_dict(self):
        stats = self.vault.stats
        self.assertIsInstance(stats, dict)
        self.assertIn("valid_keys", stats)
        self.assertIn("total_keys", stats)

    def test_available_provrs_returns_list(self):
        providers = self.vault.available_provrs
        self.assertIsInstance(providers, list)

    def test_empty_env_yields_zero_valid_keys(self):
        # With no real API keys set, should have 0 valid
        self.assertEqual(self.vault.stats["valid_keys"], 0)


class TestAPIKeyInfo(unittest.TestCase):

    def test_dataclass_fields(self):
        info = APIKeyInfo(
            provider="test", env_var="TEST_KEY",
            masked_key="sk-...xxxx", is_valid=True,
            key_length=40, prefix="sk-"
        )
        self.assertEqual(info.provider, "test")
        self.assertTrue(info.is_valid)
        self.assertEqual(info.use_count, 0)
        self.assertIsNone(info.last_error)


if __name__ == "__main__":
    unittest.main()
