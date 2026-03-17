import unittest

from backend.api import server


class ServerAuthHelpersTest(unittest.TestCase):
    def test_requires_admin_auth_for_runtime_prefix(self) -> None:
        self.assertTrue(server._requires_admin_auth('/runtime/apps/config', 'PUT'))
        self.assertTrue(server._requires_admin_auth('/runtime/apps/action', 'POST'))

    def test_requires_admin_auth_for_exact_protected_routes(self) -> None:
        self.assertTrue(server._requires_admin_auth('/orchestration/profile', 'PUT'))
        self.assertTrue(server._requires_admin_auth('/core/cache/clear', 'POST'))

    def test_does_not_require_admin_auth_for_public_routes(self) -> None:
        self.assertFalse(server._requires_admin_auth('/health', 'GET'))
        self.assertFalse(server._requires_admin_auth('/chat', 'POST'))


if __name__ == '__main__':
    unittest.main()
