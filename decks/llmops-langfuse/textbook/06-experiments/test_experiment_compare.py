from __future__ import annotations

import unittest

from experiment_compare import evaluate_variant, run_local_demo


class ExperimentComparisonTest(unittest.TestCase):
    def test_same_aggregate_can_hide_a_critical_regression(self) -> None:
        comparison = run_local_demo()

        self.assertEqual(comparison.baseline_accuracy, 0.75)
        self.assertEqual(comparison.candidate_accuracy, 0.75)
        self.assertEqual(
            comparison.regressions,
            ("electronics-day-14",),
        )
        self.assertEqual(
            comparison.critical_regressions,
            ("electronics-day-14",),
        )

    def test_candidate_fix_and_regression_are_visible_per_item(self) -> None:
        baseline = {row.case_id: row for row in evaluate_variant(refund_window_days=14)}
        candidate = {row.case_id: row for row in evaluate_variant(refund_window_days=7)}

        self.assertEqual(baseline["perishable-day-10"].score, 0.0)
        self.assertEqual(candidate["perishable-day-10"].score, 1.0)
        self.assertEqual(baseline["electronics-day-14"].score, 1.0)
        self.assertEqual(candidate["electronics-day-14"].score, 0.0)


if __name__ == "__main__":
    unittest.main()
