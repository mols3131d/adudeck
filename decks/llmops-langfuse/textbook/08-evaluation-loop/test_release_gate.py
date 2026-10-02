from __future__ import annotations

import unittest

from release_gate import (
    EvidenceRow,
    ReleasePolicy,
    VariantEvidence,
    decide_release,
)


class ReleaseGateTest(unittest.TestCase):
    def test_average_improvement_does_not_override_critical_regression(self) -> None:
        rows = [
            EvidenceRow(
                "normal-a",
                False,
                VariantEvidence.scored(0.4),
                VariantEvidence.scored(1.0),
            ),
            EvidenceRow(
                "normal-b",
                False,
                VariantEvidence.scored(0.4),
                VariantEvidence.scored(1.0),
            ),
            EvidenceRow(
                "critical-refund",
                True,
                VariantEvidence.scored(1.0),
                VariantEvidence.scored(0.0),
            ),
        ]

        decision = decide_release(rows, candidate_p95_latency_seconds=1.5)

        self.assertIsNotNone(decision.baseline_average)
        self.assertIsNotNone(decision.candidate_average)
        assert decision.baseline_average is not None
        assert decision.candidate_average is not None
        self.assertGreater(decision.candidate_average, decision.baseline_average)
        self.assertFalse(decision.approved)
        self.assertIn("critical-refund: critical regression", decision.reasons)
        self.assertEqual(decision.paired_coverage, 1.0)

    def test_candidate_evaluator_error_is_not_converted_to_score_zero(self) -> None:
        rows = [
            EvidenceRow(
                "normal",
                False,
                VariantEvidence.scored(1.0),
                VariantEvidence.scored(1.0),
            ),
            EvidenceRow(
                "judge-timeout",
                False,
                VariantEvidence.scored(0.8),
                VariantEvidence.gap("evaluator_error"),
            ),
        ]

        decision = decide_release(rows, candidate_p95_latency_seconds=1.0)

        self.assertFalse(decision.approved)
        self.assertIn(
            "judge-timeout: candidate evaluator_error",
            decision.reasons,
        )
        self.assertEqual(decision.baseline_coverage, 1.0)
        self.assertEqual(decision.candidate_coverage, 0.5)
        self.assertEqual(decision.paired_coverage, 0.5)
        self.assertEqual(decision.baseline_average, 1.0)
        self.assertEqual(decision.candidate_average, 1.0)

    def test_baseline_evaluator_error_is_an_explicit_comparison_gap(self) -> None:
        rows = [
            EvidenceRow(
                "judge-timeout",
                False,
                VariantEvidence.gap("evaluator_error"),
                VariantEvidence.scored(1.0),
            )
        ]

        decision = decide_release(rows, candidate_p95_latency_seconds=1.0)

        self.assertFalse(decision.approved)
        self.assertIn(
            "judge-timeout: baseline evaluator_error",
            decision.reasons,
        )
        self.assertIn("paired correctness comparison unavailable", decision.reasons)
        self.assertEqual(decision.baseline_coverage, 0.0)
        self.assertEqual(decision.candidate_coverage, 1.0)
        self.assertEqual(decision.paired_coverage, 0.0)

    def test_candidate_missing_score_is_not_silently_dropped(self) -> None:
        rows = [
            EvidenceRow(
                "missing-candidate",
                False,
                VariantEvidence.scored(1.0),
                VariantEvidence.gap("score_missing"),
            )
        ]

        decision = decide_release(rows, candidate_p95_latency_seconds=1.0)

        self.assertFalse(decision.approved)
        self.assertIn(
            "missing-candidate: candidate score_missing",
            decision.reasons,
        )
        self.assertIn("paired correctness comparison unavailable", decision.reasons)

    def test_baseline_missing_score_is_not_silently_dropped(self) -> None:
        rows = [
            EvidenceRow(
                "missing-baseline",
                False,
                VariantEvidence.gap("score_missing"),
                VariantEvidence.scored(1.0),
            )
        ]

        decision = decide_release(rows, candidate_p95_latency_seconds=1.0)

        self.assertFalse(decision.approved)
        self.assertIn(
            "missing-baseline: baseline score_missing",
            decision.reasons,
        )
        self.assertIn("paired correctness comparison unavailable", decision.reasons)

    def test_existing_critical_failure_is_not_mislabeled_as_regression(self) -> None:
        rows = [
            EvidenceRow(
                "critical-known-failure",
                True,
                VariantEvidence.scored(0.0),
                VariantEvidence.scored(0.0),
            )
        ]

        decision = decide_release(rows, candidate_p95_latency_seconds=1.0)

        self.assertFalse(decision.approved)
        self.assertIn(
            "critical-known-failure: critical candidate failure",
            decision.reasons,
        )
        self.assertNotIn(
            "critical-known-failure: critical regression",
            decision.reasons,
        )

    def test_fixing_a_critical_failure_does_not_count_as_regression(self) -> None:
        rows = [
            EvidenceRow(
                "critical-fixed",
                True,
                VariantEvidence.scored(0.0),
                VariantEvidence.scored(1.0),
            )
        ]

        decision = decide_release(rows, candidate_p95_latency_seconds=1.0)

        self.assertTrue(decision.approved)
        self.assertEqual(decision.reasons, ())

    def test_release_can_pass_when_policy_evidence_is_satisfied(self) -> None:
        rows = [
            EvidenceRow(
                "normal",
                False,
                VariantEvidence.scored(1.0),
                VariantEvidence.scored(1.0),
            ),
            EvidenceRow(
                "critical-refund",
                True,
                VariantEvidence.scored(1.0),
                VariantEvidence.scored(1.0),
            ),
        ]

        decision = decide_release(
            rows,
            candidate_p95_latency_seconds=1.2,
            policy=ReleasePolicy(max_p95_latency_seconds=1.5),
        )

        self.assertTrue(decision.approved)
        self.assertEqual(decision.reasons, ())
        self.assertEqual(decision.baseline_coverage, 1.0)
        self.assertEqual(decision.candidate_coverage, 1.0)
        self.assertEqual(decision.paired_coverage, 1.0)

    def test_variant_evidence_rejects_ambiguous_state(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires a score"):
            VariantEvidence(status="scored")

        with self.assertRaisesRegex(ValueError, "must not carry a score"):
            VariantEvidence(status="evaluator_error", score=0.0)


if __name__ == "__main__":
    unittest.main()
