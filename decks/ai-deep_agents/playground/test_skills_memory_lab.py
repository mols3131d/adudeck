"""Check the real store, MemoryMiddleware and SkillsMiddleware observation boundaries."""

import unittest

from skills_memory_lab import INITIAL_MEMORY, SKILL_TEXT, UPDATED_MEMORY, run_lab


class SkillsMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = run_lab()

    def test_first_model_request_contains_memory_and_skill_discovery_only(self) -> None:
        before = self.evidence["model_requests"][0]
        self.assertIn(INITIAL_MEMORY, before)
        self.assertIn("compare-services", before)
        self.assertNotIn("When comparing services", before)

    def test_explicit_read_loads_full_skill_body(self) -> None:
        observed = self.evidence["read_skill"]
        self.assertEqual(observed["status"], "success")
        self.assertIn("When comparing services", observed["content"])
        self.assertIn("When comparing services", self.evidence["model_requests"][1])

    def test_memory_update_is_visible_in_new_thread(self) -> None:
        observed = self.evidence["update_memory"]
        self.assertEqual(observed["status"], "success")
        after = self.evidence["model_requests"][-1]
        self.assertIn(UPDATED_MEMORY, after)
        self.assertNotIn(INITIAL_MEMORY, after)

    def test_updates_do_not_change_skill_definition(self) -> None:
        self.assertIn("compare-services", SKILL_TEXT)
        self.assertEqual(len(self.evidence["model_requests"]), 5)


if __name__ == "__main__":
    unittest.main()
