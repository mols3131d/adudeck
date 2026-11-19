"""Verify task routing, result-only return, and the unknown-subagent failure."""

import unittest

from subagent_lab import run_lab


class SubagentLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.delegated = run_lab()
        cls.unknown = run_lab(unknown_agent=True)

    def test_parent_sees_task_not_child_tool(self) -> None:
        actual = self.delegated
        self.assertIn("task", actual["parent_offered_tools"])
        self.assertNotIn("inspect_fixture", actual["parent_offered_tools"])
        self.assertIn("inspect_fixture", actual["child_offered_tools"])
        self.assertEqual(actual["parent_tool_messages"], ["task"])

    def test_child_runs_real_tool_and_returns_summary(self) -> None:
        actual = self.delegated
        self.assertEqual(actual["child_fixture_calls"], ["alpha"])
        self.assertEqual(actual["task_result"][0]["status"], "success")
        self.assertIn("p95=120ms", actual["task_result"][0]["content"])

    def test_unknown_subagent_does_not_run_child_tool(self) -> None:
        actual = self.unknown
        self.assertEqual(actual["child_fixture_calls"], [])
        self.assertEqual(actual["parent_tool_messages"], ["task"])
        self.assertTrue(
            "unknown" in actual["task_result"][0]["content"].lower()
            or "not found" in actual["task_result"][0]["content"].lower()
            or actual["task_result"][0]["status"] == "error",
            actual["task_result"],
        )


if __name__ == "__main__":
    unittest.main()
