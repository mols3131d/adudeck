"""Runtime-contract assertions for scoped backend behavior."""

import unittest

from context_lab import run_lab


class ContextLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = run_lab()

    def test_both_file_writes_complete(self) -> None:
        for item in self.evidence["written"].values():
            self.assertEqual(item["status"], "success")

    def test_state_backend_files_are_thread_scoped(self) -> None:
        self.assertIn("/scratch/local.md", self.evidence["thread_a_files"])
        self.assertNotIn("/scratch/local.md", self.evidence["thread_b_files"])
        self.assertIn("only thread A", self.evidence["thread_a_revisit"]["content"])

    def test_store_backend_is_visible_across_threads(self) -> None:
        self.assertIn("shared across threads", self.evidence["thread_b_reads"]["shared"]["content"])
        self.assertNotIn("only thread A", self.evidence["thread_b_reads"]["scratch"]["content"])

    def test_failed_read_has_observable_error(self) -> None:
        missing = self.evidence["thread_b_reads"]["scratch"]
        self.assertTrue(
            missing["status"] == "error" or "error" in missing["content"].lower()
            or "not found" in missing["content"].lower(),
            missing,
        )


if __name__ == "__main__":
    unittest.main()
