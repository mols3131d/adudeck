from __future__ import annotations

import unittest

from release_gate import EvidenceRow, ReleasePolicy, decide_release


class ReleaseGateTest(unittest.TestCase):
    def test_average_improvement_does_not_override_critical_regression(self) -> None:
        rows = [
            EvidenceRow("normal-a", False, 0.4, 1.0),
            EvidenceRow("normal-b", False, 0.4, 1.0),
            EvidenceRow("critical-refund", True, 1.0, 0.0),
        ]

        decision = decide_release(
            rows,
            candidate_p95_latency_seconds=1.5,
        )

        self.assertGreater(decision.candidate_average, decision.baseline_average)
        self.assertFalse(decision.approved)
        self.assertIn(
            "critical-refund: critical regression",
            decision.reasons,
        )

    def test_evaluator_error_is_not_converted_to_score_zero(self) -> None:
        rows = [
            EvidenceRow("normal", False, 1.0, 1.0),
            EvidenceRow(
                "judge-timeout",
                False,
                None,
                None,
                status="evaluator_error",
            ),
        ]

        decision = decide_release(
            rows,
            candidate_p95_latency_seconds=1.0,
        )

        self.assertFalse(decision.approved)
        self.assertIn("judge-timeout: evaluator_error", decision.reasons)
        self.assertEqual(decision.candidate_average, 1.0)

    def test_release_can_pass_when_policy_evidence_is_satisfied(self) -> None:
        rows = [
            EvidenceRow("normal", False, 1.0, 1.0),
            EvidenceRow("critical-refund", True, 1.0, 1.0),
        ]

        decision = decide_release(
            rows,
            candidate_p95_latency_seconds=1.2,
            policy=ReleasePolicy(max_p95_latency_seconds=1.5),
        )

        self.assertTrue(decision.approved)
        self.assertEqual(decision.reasons, ())


if __name__ == "__main__":
    unittest.main()
