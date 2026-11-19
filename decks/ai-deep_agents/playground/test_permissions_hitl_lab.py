"""Verify filesystem rules and HITL actions through actual Deep Agents middleware."""

import unittest

from permissions_hitl_lab import run_permission_case, run_review_case


class PermissionAndReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.permissions = run_permission_case()
        cls.approved = run_review_case("approve")
        cls.rejected = run_review_case("reject")

    def test_first_matching_filesystem_rule_and_default_allow(self) -> None:
        r = self.permissions["responses"]
        files = self.permissions["files"]
        self.assertEqual(r["permitted"]["status"], "success")
        self.assertEqual(r["blocked"]["status"], "error")
        self.assertIn("permission denied", r["blocked"]["content"].lower())
        self.assertEqual(r["unmatched"]["status"], "success")
        self.assertIn("/reports/approved/summary.md", files)
        self.assertNotIn("/reports/private/summary.md", files)
        self.assertIn("/scratch/free.md", files)

    def test_sensitive_action_pauses_before_any_effect(self) -> None:
        for observed in (self.approved, self.rejected):
            self.assertTrue(observed["interrupted"])
            self.assertEqual(observed["requested_actions"], ["record_local_change"])
            self.assertEqual(observed["effects_at_pause"], [])

    def test_approve_executes_the_tool_exactly_once(self) -> None:
        self.assertTrue(self.approved["resumed_without_interrupt"])
        self.assertEqual(self.approved["effects_after_resume"], ["ready"])
        self.assertIn("Recorded local change", self.approved["returned_tools"][0]["content"])

    def test_reject_prevents_tool_execution(self) -> None:
        self.assertTrue(self.rejected["resumed_without_interrupt"])
        self.assertEqual(self.rejected["effects_after_resume"], [])

    def test_approval_result_corresponds_to_requested_custom_tool(self) -> None:
        self.assertEqual(
            [tool["name"] for tool in self.approved["returned_tools"]],
            ["record_local_change"],
        )
        self.assertEqual(self.approved["returned_tools"][0]["status"], "success")


if __name__ == "__main__":
    unittest.main()
