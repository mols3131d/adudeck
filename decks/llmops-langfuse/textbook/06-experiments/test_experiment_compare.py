from __future__ import annotations

import sys
import unittest
from pathlib import Path

# This executable chapter test checks the producer contract of Unit 5 directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "05-datasets"))
from dataset_case import build_refund_regression_case  # noqa: E402
from datetime import datetime, timezone
from types import SimpleNamespace

from experiment_compare import (
    evaluate_variant,
    hosted_support_application,
    parse_dataset_version,
    run_hosted_dataset_pair,
    run_local_demo,
    support_application,
)


class FakeDataset:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def run_experiment(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(name=kwargs["name"])


class FakeLangfuse:
    def __init__(self) -> None:
        self.dataset = FakeDataset()
        self.get_dataset_calls: list[dict[str, object]] = []

    def get_dataset(self, name: str, *, version: datetime):
        self.get_dataset_calls.append({"name": name, "version": version})
        return self.dataset


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

    def test_unit5_hosted_case_runs_through_unit6_task_with_exact_output_contract(self) -> None:
        case = build_refund_regression_case(
            case_id="refund-day-10",
            days_since_delivery=10,
            source_trace_id="synthetic-source-trace",
        )
        item = SimpleNamespace(input=case.input, expected_output=case.expected_output)
        baseline = hosted_support_application(item=item, refund_window_days=14)
        candidate = hosted_support_application(item=item, refund_window_days=7)

        self.assertEqual(baseline, case.expected_output)
        self.assertEqual(candidate, {"eligible": False, "policy_days": 7})
        self.assertNotEqual(candidate, case.expected_output)
        self.assertEqual(
            support_application(item={"input": {"days": 10}}, refund_window_days=14),
            {"eligible": True},
        )

    def test_hosted_pair_reuses_one_pinned_dataset_snapshot(self) -> None:
        langfuse = FakeLangfuse()
        version = datetime(2026, 10, 2, 6, 0, tzinfo=timezone.utc)

        baseline, candidate = run_hosted_dataset_pair(
            langfuse,
            dataset_name="support/refund-policy",
            dataset_version=version,
        )

        self.assertEqual(
            langfuse.get_dataset_calls,
            [{"name": "support/refund-policy", "version": version}],
        )
        self.assertEqual(len(langfuse.dataset.calls), 2)
        self.assertEqual(baseline.name, "refund-window-baseline")
        self.assertEqual(candidate.name, "refund-window-candidate")
        self.assertEqual(
            [call["metadata"]["dataset_version"] for call in langfuse.dataset.calls],
            [version.isoformat(), version.isoformat()],
        )
        self.assertEqual(
            [call["metadata"]["refund_window_days"] for call in langfuse.dataset.calls],
            [14, 7],
        )
        item = SimpleNamespace(input={"days_since_delivery": 10})
        self.assertEqual(
            [call["task"](item=item) for call in langfuse.dataset.calls],
            [
                {"eligible": True, "policy_days": 14},
                {"eligible": False, "policy_days": 7},
            ],
        )

    def test_dataset_version_requires_timezone(self) -> None:
        parsed = parse_dataset_version("2026-10-02T06:00:00Z")
        self.assertEqual(parsed.tzinfo, timezone.utc)

        with self.assertRaisesRegex(ValueError, "timezone offset"):
            parse_dataset_version("2026-10-02T06:00:00")

    def test_dataset_version_normalizes_non_utc_offset_to_utc(self) -> None:
        parsed = parse_dataset_version("2026-10-02T15:00:00+09:00")
        self.assertEqual(parsed, datetime(2026, 10, 2, 6, 0, tzinfo=timezone.utc))
        self.assertEqual(parsed.tzinfo, timezone.utc)


if __name__ == "__main__":
    unittest.main()
