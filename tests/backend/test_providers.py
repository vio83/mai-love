"""
VIO 83 AI ORCHESTRA — Provider Configuration Tests
Tests: provider lists, ordering, elite stacks, free providers
"""
import unittest

from backend.config.providers import (
    CLOUD_PROVIDERS, LOCAL_PROVIDERS, FREE_CLOUD_PROVIDERS,
    ALL_CLOUD_PROVIDERS, get_available_cloud_providers,
    get_free_cloud_providers, get_all_providers_ordered, get_elite_task_stacks,
)


class TestProviderConfig(unittest.TestCase):

    def test_cloud_providers_is_dict(self):
        self.assertIsInstance(CLOUD_PROVIDERS, dict)
        self.assertGreater(len(CLOUD_PROVIDERS), 0)

    def test_local_providers_is_dict(self):
        self.assertIsInstance(LOCAL_PROVIDERS, dict)

    def test_free_providers_exist(self):
        self.assertIsInstance(FREE_CLOUD_PROVIDERS, dict)

    def test_all_cloud_providers_includes_free(self):
        for key in FREE_CLOUD_PROVIDERS:
            self.assertIn(key, ALL_CLOUD_PROVIDERS,
                          f"Free provider {key} missing from ALL_CLOUD_PROVIDERS")

    def test_get_available_cloud_providers_returns_list(self):
        result = get_available_cloud_providers()
        self.assertIsInstance(result, (list, dict))

    def test_get_free_cloud_providers_returns_something(self):
        result = get_free_cloud_providers()
        self.assertIsNotNone(result)

    def test_get_all_providers_ordered_returns_list(self):
        result = get_all_providers_ordered()
        self.assertIsInstance(result, list)

    def test_elite_task_stacks_returns_dict(self):
        stacks = get_elite_task_stacks()
        self.assertIsInstance(stacks, dict)


class TestProviderStructure(unittest.TestCase):

    def test_each_cloud_provider_has_required_fields(self):
        """Ogni provider deve avere env_key e almeno uno tra 'model' o 'default_model'."""
        for name, config in CLOUD_PROVIDERS.items():
            has_model_key = "model" in config or "default_model" in config
            self.assertTrue(
                has_model_key,
                f"{name} deve avere 'model' o 'default_model'"
            )
            self.assertIn("env_key", config, f"{name} missing 'env_key'")


if __name__ == "__main__":
    unittest.main()
