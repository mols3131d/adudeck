from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RegressionCase:
    case_id: str
    input: dict[str, Any]
    expected_output: dict[str, Any]
    metadata: dict[str, Any]
    source_trace_id: str
    source_observation_id: str | None = None

    def as_langfuse_item(self, *, dataset_name: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "dataset_name": dataset_name,
            "input": self.input,
            "expected_output": self.expected_output,
            "metadata": self.metadata,
            "source_trace_id": self.source_trace_id,
        }
        if self.source_observation_id is not None:
            payload["source_observation_id"] = self.source_observation_id
        return payload


def build_refund_regression_case(
    *,
    case_id: str,
    days_since_delivery: int,
    source_trace_id: str,
    source_observation_id: str | None = None,
) -> RegressionCase:
    """Promote only the minimum reproducible policy facts, not a raw customer transcript."""
    return RegressionCase(
        case_id=case_id,
        input={"days_since_delivery": days_since_delivery},
        expected_output={
            "eligible": days_since_delivery <= 14,
            "policy_days": 14,
        },
        metadata={
            "source": "production-review",
            "failure_mode": "refund-eligibility",
            "case_id": case_id,
        },
        source_trace_id=source_trace_id,
        source_observation_id=source_observation_id,
    )


def upload_case(langfuse: Any, case: RegressionCase, *, dataset_name: str) -> Any:
    return langfuse.create_dataset_item(
        **case.as_langfuse_item(dataset_name=dataset_name)
    )


def require_langfuse_credentials() -> None:
    missing = [
        name
        for name in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
        if not os.getenv(name)
    ]
    if missing:
        raise SystemExit(
            "Missing Langfuse credentials: "
            + ", ".join(missing)
            + ". Set them in your shell before the live lab."
        )


def main() -> None:
    require_langfuse_credentials()

    source_trace_id = os.getenv("SOURCE_TRACE_ID")
    if not source_trace_id:
        raise SystemExit(
            "Set SOURCE_TRACE_ID to a trace you intentionally selected for the dataset."
        )

    from langfuse import get_client

    langfuse = get_client()
    case = build_refund_regression_case(
        case_id="refund-day-10",
        days_since_delivery=10,
        source_trace_id=source_trace_id,
        source_observation_id=os.getenv("SOURCE_OBSERVATION_ID"),
    )
    item = upload_case(
        langfuse,
        case,
        dataset_name=os.getenv("LANGFUSE_DATASET", "support/refund-policy"),
    )
    print(f"dataset_item_id={item.id}")


if __name__ == "__main__":
    main()
