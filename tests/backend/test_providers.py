"""
VIO 83 AI ORCHESTRA — Provr Configuration Tests
Tests: provr lists, ordering, elite stacks, free provrs
"""
import unittest

from backend.config.provrs import (
    CLOUD_PROVRS, LOCAL_PROVRS, FREE_CLOUD_PROVRS,
    ALL_CLOUD_PROVRS, get_available_cloud_provrs,
    get_free_cloud_provrs, get_all_provrs_ordered, get_elite_task_stacks,
)


class TestProvrConfig(unittest.TestCase):

    def test_cloud_provrs_is_dict(self):
        self.assertIsInstance(CLOUD_PROVRS, dict)
        self.assertGreater(len(CLOUD_PROVRS), 0)

    def test_local_provrs_is_dict(self):
        self.assertIsInstance(LOCAL_PROVRS, dict)

    def test_free_provrs_exist(self):
        self.assertIsInstance(FREE_CLOUD_PROVRS, dict)

    def test_all_cloud_provrs_includes_free(self):
        for key in FREE_CLOUD_PROVRS:
            self.assertIn(key, ALL_CLOUD_PROVRS,
                          f"Free provr {key} missing from ALL_CLOUD_PROVRS")

    def test_get_available_cloud_provrs_returns_list(self):
        result = get_available_cloud_provrs()
        self.assertIsInstance(result, (list, dict))

    def test_get_free_cloud_provrs_returns_something(self):
        result = get_free_cloud_provrs()
        self.assertIsNotNone(result)

    def test_get_all_provrs_ordered_returns_list(self):
        result = get_all_provrs_ordered()
        self.assertIsInstance(result, list)

    def test_elite_task_stacks_returns_dict(self):
        stacks = get_elite_task_stacks()
        self.assertIsInstance(stacks, dict)


class TestProvrStructure(unittest.TestCase):

    def test_each_cloud_provr_has_required_fields(self):
        """Ogni provr deve avere env_key e almeno uno tra 'model' o 'default_model'."""
        for name, config in CLOUD_PROVRS.items():
            has_model_key = "model" in config or "default_model" in config
            self.assertTrue(
                has_model_key,
                f"{name} deve avere 'model' o 'default_model'"
            )
            self.assertIn("env_key", config, f"{name} missing 'env_key'")


if __name__ == "__main__":
    unittest.main()
