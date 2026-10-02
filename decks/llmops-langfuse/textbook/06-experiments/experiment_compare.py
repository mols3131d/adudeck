from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any


LOCAL_DATA = [
    {
        "input": {"case_id": "electronics-day-3", "category": "electronics", "days": 3},
        "expected_output": {"eligible": True},
        "metadata": {"critical": False},
    },
    {
        "input": {"case_id": "electronics-day-14", "category": "electronics", "days": 14},
        "expected_output": {"eligible": True},
        "metadata": {"critical": True},
    },
    {
        "input": {"case_id": "perishable-day-10", "category": "perishable", "days": 10},
        "expected_output": {"eligible": False},
        "metadata": {"critical": False},
    },
    {
        "input": {"case_id": "perishable-day-3", "category": "perishable", "days": 3},
        "expected_output": {"eligible": True},
        "metadata": {"critical": False},
    },
]


@dataclass(frozen=True)
class ItemResult:
    case_id: str
    critical: bool
    expected: bool
    actual: bool

    @property
    def score(self) -> float:
        return 1.0 if self.actual == self.expected else 0.0


@dataclass(frozen=True)
class Comparison:
    baseline_accuracy: float
    candidate_accuracy: float
    regressions: tuple[str, ...]
    critical_regressions: tuple[str, ...]


def _item_input(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item["input"]
    return item.input


def support_application(*, item: Any, refund_window_days: int) -> dict[str, bool]:
    """Deliberately simplified app: one global window cannot model category-specific policy."""
    item_input = _item_input(item)
    return {"eligible": item_input["days"] <= refund_window_days}


def evaluate_variant(*, refund_window_days: int) -> list[ItemResult]:
    rows: list[ItemResult] = []
    for item in LOCAL_DATA:
        output = support_application(
            item=item,
            refund_window_days=refund_window_days,
        )
        rows.append(
            ItemResult(
                case_id=item["input"]["case_id"],
                critical=bool(item["metadata"]["critical"]),
                expected=bool(item["expected_output"]["eligible"]),
                actual=bool(output["eligible"]),
            )
        )
    return rows


def compare_variants(
    baseline: list[ItemResult],
    candidate: list[ItemResult],
) -> Comparison:
    baseline_by_id = {row.case_id: row for row in baseline}
    candidate_by_id = {row.case_id: row for row in candidate}
    if baseline_by_id.keys() != candidate_by_id.keys():
        raise ValueError("baseline and candidate must evaluate the same cases")

    regressions = tuple(
        case_id
        for case_id, baseline_row in baseline_by_id.items()
        if baseline_row.score == 1.0 and candidate_by_id[case_id].score == 0.0
    )
    critical_regressions = tuple(
        case_id
        for case_id in regressions
        if candidate_by_id[case_id].critical
    )

    return Comparison(
        baseline_accuracy=sum(row.score for row in baseline) / len(baseline),
        candidate_accuracy=sum(row.score for row in candidate) / len(candidate),
        regressions=regressions,
        critical_regressions=critical_regressions,
    )


def run_local_demo() -> Comparison:
    baseline = evaluate_variant(refund_window_days=14)
    candidate = evaluate_variant(refund_window_days=7)
    return compare_variants(baseline, candidate)


def correctness_evaluator(*, output, expected_output, **kwargs):
    from langfuse import Evaluation

    return Evaluation(
        name="correctness",
        value=1.0 if output == expected_output else 0.0,
    )


def _experiment_task(refund_window_days: int):
    def task(*, item, **kwargs):
        return support_application(
            item=item,
            refund_window_days=refund_window_days,
        )

    return task


def run_langfuse_local_experiment(
    langfuse: Any,
    *,
    name: str,
    refund_window_days: int,
):
    return langfuse.run_experiment(
        name=name,
        data=LOCAL_DATA,
        task=_experiment_task(refund_window_days),
        evaluators=[correctness_evaluator],
        metadata={"refund_window_days": refund_window_days},
    )


def run_hosted_dataset_experiment(
    dataset: Any,
    *,
    name: str,
    refund_window_days: int,
    dataset_version: datetime,
):
    return dataset.run_experiment(
        name=name,
        task=_experiment_task(refund_window_days),
        evaluators=[correctness_evaluator],
        metadata={
            "refund_window_days": refund_window_days,
            "dataset_version": dataset_version.isoformat(),
        },
    )


def run_hosted_dataset_pair(
    langfuse: Any,
    *,
    dataset_name: str,
    dataset_version: datetime,
) -> tuple[Any, Any]:
    """Fetch one historical dataset snapshot and reuse it for both variants."""
    dataset = langfuse.get_dataset(
        dataset_name,
        version=dataset_version,
    )
    baseline = run_hosted_dataset_experiment(
        dataset,
        name="refund-window-baseline",
        refund_window_days=14,
        dataset_version=dataset_version,
    )
    candidate = run_hosted_dataset_experiment(
        dataset,
        name="refund-window-candidate",
        refund_window_days=7,
        dataset_version=dataset_version,
    )
    return baseline, candidate


def parse_dataset_version(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        version = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            "LANGFUSE_DATASET_VERSION must be an ISO-8601 timestamp, for example "
            "2026-10-02T06:00:00+00:00"
        ) from exc
    if version.tzinfo is None:
        raise ValueError("LANGFUSE_DATASET_VERSION must include a timezone offset")
    return version


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
            + ". Set them in your shell before the hosted experiment lab."
        )


def main() -> None:
    comparison = run_local_demo()
    print(comparison)

    if os.getenv("RUN_LANGFUSE_EXPERIMENT") != "1":
        print("Langfuse experiment skipped; set RUN_LANGFUSE_EXPERIMENT=1 for the live lab.")
        return

    require_langfuse_credentials()
    from langfuse import get_client

    langfuse = get_client()
    dataset_version_raw = os.getenv("LANGFUSE_DATASET_VERSION")

    if dataset_version_raw:
        dataset_version = parse_dataset_version(dataset_version_raw)
        dataset_name = os.getenv("LANGFUSE_DATASET", "support/refund-policy")
        print(
            "hosted_dataset="
            f"{dataset_name} dataset_version={dataset_version.isoformat()}"
        )
        run_hosted_dataset_pair(
            langfuse,
            dataset_name=dataset_name,
            dataset_version=dataset_version,
        )
    else:
        print(
            "Running local-data Langfuse experiments. Set LANGFUSE_DATASET_VERSION "
            "to an ISO-8601 timestamp to pin a hosted dataset snapshot."
        )
        run_langfuse_local_experiment(
            langfuse,
            name="refund-window-baseline",
            refund_window_days=14,
        )
        run_langfuse_local_experiment(
            langfuse,
            name="refund-window-candidate",
            refund_window_days=7,
        )

    langfuse.flush()


if __name__ == "__main__":
    main()
