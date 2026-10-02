from __future__ import annotations

import os
from dataclasses import dataclass
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


def support_application(*, item: dict[str, Any], refund_window_days: int) -> dict[str, bool]:
    """Deliberately simplified app: one global window cannot model category-specific policy."""
    return {"eligible": item["input"]["days"] <= refund_window_days}


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


def run_langfuse_experiment(langfuse: Any, *, name: str, refund_window_days: int):
    from langfuse import Evaluation

    def task(*, item, **kwargs):
        return support_application(
            item=item,
            refund_window_days=refund_window_days,
        )

    def correctness_evaluator(*, output, expected_output, **kwargs):
        return Evaluation(
            name="correctness",
            value=1.0 if output == expected_output else 0.0,
        )

    return langfuse.run_experiment(
        name=name,
        data=LOCAL_DATA,
        task=task,
        evaluators=[correctness_evaluator],
        metadata={"refund_window_days": refund_window_days},
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
    run_langfuse_experiment(
        langfuse,
        name="refund-window-baseline",
        refund_window_days=14,
    )
    run_langfuse_experiment(
        langfuse,
        name="refund-window-candidate",
        refund_window_days=7,
    )
    langfuse.flush()


if __name__ == "__main__":
    main()
