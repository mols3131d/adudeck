from __future__ import annotations

import unittest
from uuid import NAMESPACE_URL, uuid5

from dataset_case import build_refund_regression_case, upload_case


class FakeLangfuse:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.items: dict[str, dict[str, object]] = {}

    def create_dataset_item(self, **kwargs):
        self.calls.append(kwargs)
        self.items[kwargs["id"]] = kwargs
        return object()


class DatasetCaseContractTest(unittest.TestCase):
    def test_case_preserves_reproducible_contract_and_source_link(self) -> None:
        case = build_refund_regression_case(
            case_id="refund-day-10",
            days_since_delivery=10,
            source_trace_id="trace-production-1",
            source_observation_id="obs-generation-1",
        )

        payload = case.as_langfuse_item(dataset_name="support/refund-policy")

        self.assertEqual(
            payload["id"],
            str(uuid5(NAMESPACE_URL, "adudeck-langfuse-lab:support/refund-policy:refund-day-10")),
        )
        self.assertEqual(payload["input"], {"days_since_delivery": 10})
        self.assertEqual(
            payload["expected_output"],
            {"eligible": True, "policy_days": 14},
        )
        self.assertEqual(payload["source_trace_id"], "trace-production-1")
        self.assertEqual(payload["source_observation_id"], "obs-generation-1")
        self.assertEqual(payload["metadata"]["failure_mode"], "refund-eligibility")

    def test_case_exports_only_the_synthetic_domain_allowlist(self) -> None:
        case = build_refund_regression_case(
            case_id="refund-day-15",
            days_since_delivery=15,
            source_trace_id="trace-production-2",
        )

        payload = case.as_langfuse_item(dataset_name="support/refund-policy")

        self.assertEqual(
            payload,
            {
                "id": str(uuid5(NAMESPACE_URL, "adudeck-langfuse-lab:support/refund-policy:refund-day-15")),
                "dataset_name": "support/refund-policy",
                "input": {"days_since_delivery": 15},
                "expected_output": {"eligible": False, "policy_days": 14},
                "metadata": {
                    "source": "production-review",
                    "failure_mode": "refund-eligibility",
                    "case_id": "refund-day-15",
                },
                "source_trace_id": "trace-production-2",
            },
        )

    def test_upload_uses_dataset_item_contract(self) -> None:
        langfuse = FakeLangfuse()
        case = build_refund_regression_case(
            case_id="refund-day-10",
            days_since_delivery=10,
            source_trace_id="trace-production-1",
        )

        upload_case(langfuse, case, dataset_name="support/refund-policy")

        self.assertEqual(len(langfuse.calls), 1)
        self.assertEqual(
            langfuse.calls[0]["dataset_name"],
            "support/refund-policy",
        )
        self.assertEqual(
            langfuse.calls[0]["source_trace_id"],
            "trace-production-1",
        )

    def test_repeat_upload_reuses_the_same_id_and_dataset_name_scopes_identity(self) -> None:
        case = build_refund_regression_case(
            case_id="refund-day-10",
            days_since_delivery=10,
            source_trace_id="trace-production-1",
        )
        langfuse = FakeLangfuse()
        upload_case(langfuse, case, dataset_name="support/refund-policy")
        upload_case(langfuse, case, dataset_name="support/refund-policy")

        self.assertEqual(len(langfuse.calls), 2)
        self.assertEqual(len(langfuse.items), 1)
        self.assertEqual(langfuse.calls[0]["id"], langfuse.calls[1]["id"])
        self.assertNotEqual(
            case.as_langfuse_item(dataset_name="other/refunds")["id"],
            langfuse.calls[0]["id"],
        )


if __name__ == "__main__":
    unittest.main()
