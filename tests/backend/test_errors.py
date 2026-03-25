"""
VIO 83 AI ORCHESTRA — Error Handling Tests
Tests: ErrorCode enum, OrchestraError, ErrorHandler
"""
import unittest

from backend.core.errors import ErrorCode, OrchestraError, ErrorHandler


class TestErrorCode(unittest.TestCase):

    def test_provr_error_codes_in_1xxx_range(self):
        self.assertEqual(ErrorCode.PROVR_UNAVAILABLE.value, 1001)
        self.assertEqual(ErrorCode.PROVR_TIMEOUT.value, 1002)
        self.assertEqual(ErrorCode.PROVR_RATE_LIMITED.value, 1003)
        self.assertEqual(ErrorCode.PROVR_AUTH_FAILED.value, 1004)

    def test_network_error_codes_in_2xxx_range(self):
        self.assertEqual(ErrorCode.NETWORK_CONNECTION_FAILED.value, 2001)
        self.assertEqual(ErrorCode.NETWORK_DNS_FAILED.value, 2002)

    def test_database_error_codes_in_3xxx_range(self):
        self.assertEqual(ErrorCode.DB_CONNECTION_FAILED.value, 3001)
        self.assertEqual(ErrorCode.DB_QUERY_FAILED.value, 3002)

    def test_system_error_codes_in_9xxx_range(self):
        self.assertEqual(ErrorCode.SYSTEM_OUT_OF_MEMORY.value, 9001)
        self.assertEqual(ErrorCode.SYSTEM_UNKNOWN.value, 9999)

    def test_all_error_codes_have_unique_values(self):
        values = [e.value for e in ErrorCode]
        self.assertEqual(len(values), len(set(values)), "Duplicate error code values found")


class TestOrchestraError(unittest.TestCase):

    def test_error_creation(self):
        err = OrchestraError(
            code=ErrorCode.PROVR_UNAVAILABLE,
            message="Provider X is down"
        )
        self.assertEqual(err.code, ErrorCode.PROVR_UNAVAILABLE)
        self.assertEqual(err.message, "Provider X is down")
        self.assertTrue(err.recoverable)

    def test_error_to_dict(self):
        err = OrchestraError(
            code=ErrorCode.PROVR_TIMEOUT,
            message="Timed out",
            provider="ollama",
            model="llama3"
        )
        d = err.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["error_code"], 1002)
        self.assertEqual(d["provider"], "ollama")
        self.assertEqual(d["model"], "llama3")

    def test_non_recoverable_error(self):
        err = OrchestraError(
            code=ErrorCode.SYSTEM_DISK_FULL,
            message="Disk full",
            recoverable=False
        )
        self.assertFalse(err.recoverable)

    def test_error_with_suggestion(self):
        err = OrchestraError(
            code=ErrorCode.CONFIG_MISSING_KEY,
            message="GROQ key missing",
            suggestion="Set GROQ_API_KEY in .env"
        )
        self.assertEqual(err.suggestion, "Set GROQ_API_KEY in .env")


class TestErrorHandler(unittest.TestCase):

    def setUp(self):
        self.handler = ErrorHandler()

    def test_handler_initializes(self):
        self.assertIsInstance(self.handler, ErrorHandler)

    def test_stats_returns_dict(self):
        stats = self.handler.stats
        self.assertIsInstance(stats, dict)
        self.assertIn("total_errors", stats)

    def test_initial_error_count_is_zero(self):
        handler = ErrorHandler()
        self.assertEqual(handler.stats["total_errors"], 0)


if __name__ == "__main__":
    unittest.main()
