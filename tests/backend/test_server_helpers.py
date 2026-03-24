import unittest

from backend.api import server


class ServerHelpersTest(unittest.TestCase):
    def test_cap_request_tokens_respects_bounds(self) -> None:
        self.assertEqual(server._cap_request_tokens(16), 64)
        self.assertEqual(server._cap_request_tokens(9999), 1024)

    def test_effective_temperature_prefers_speed_profile(self) -> None:
        self.assertEqual(server._effective_temperature(0.9), 0.25)
        self.assertEqual(server._effective_temperature(0.1), 0.1)

    def test_knowledge_registry_payload_contains_domains_and_policy(self) -> None:
        payload = server._build_knowledge_registry_payload()

        self.assertEqual(payload['status'], 'ok')
        self.assertGreater(payload['coverage']['domain_count'], 0)
        self.assertGreaterEqual(payload['scores']['average_reliability'], 0)
        self.assertIn('strict_evnce_mode', payload['policy'])
        self.assertTrue(any(domain['id'] == 'computer-ai' for domain in payload['domains']))


if __name__ == '__main__':
    unittest.main()
