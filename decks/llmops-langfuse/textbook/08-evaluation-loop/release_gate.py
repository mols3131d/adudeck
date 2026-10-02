from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


EvaluationStatus = Literal[
    "scored",
    "application_error",
    "evaluator_error",
    "score_missing",
]


@dataclass(frozen=True)
class EvidenceRow:
    case_id: str
    critical: bool
    baseline_score: float | None
    candidate_score: float | None
    status: EvaluationStatus = "scored"


@dataclass(frozen=True)
class ReleasePolicy:
    require_all_critical_pass: bool = True
    require_no_evaluation_gaps: bool = True
    min_correctness_delta: float = 0.0
    max_p95_latency_seconds: float = 1.6


@dataclass(frozen=True)
class ReleaseDecision:
    approved: bool
    reasons: tuple[str, ...]
    baseline_average: float | None
    candidate_average: float | None


def _average_scored(rows: list[EvidenceRow], *, candidate: bool) -> float | None:
    values = [
        row.candidate_score if candidate else row.baseline_score
        for row in rows
        if row.status == "scored"
        and (row.candidate_score if candidate else row.baseline_score) is not None
    ]
    if not values:
        return None
    return sum(values) / len(values)


def decide_release(
    rows: list[EvidenceRow],
    *,
    candidate_p95_latency_seconds: float,
    policy: ReleasePolicy = ReleasePolicy(),
) -> ReleaseDecision:
    reasons: list[str] = []

    if policy.require_no_evaluation_gaps:
        for row in rows:
            if row.status != "scored":
                reasons.append(f"{row.case_id}: {row.status}")

    if policy.require_all_critical_pass:
        for row in rows:
            if (
                row.critical
                and row.status == "scored"
                and row.candidate_score != 1.0
            ):
                reasons.append(f"{row.case_id}: critical regression")

    baseline_average = _average_scored(rows, candidate=False)
    candidate_average = _average_scored(rows, candidate=True)

    if baseline_average is None or candidate_average is None:
        reasons.append("correctness average unavailable")
    elif candidate_average - baseline_average < policy.min_correctness_delta:
        reasons.append(
            "candidate correctness is below the required baseline delta"
        )

    if candidate_p95_latency_seconds > policy.max_p95_latency_seconds:
        reasons.append(
            "candidate p95 latency exceeds the release policy"
        )

    return ReleaseDecision(
        approved=not reasons,
        reasons=tuple(reasons),
        baseline_average=baseline_average,
        candidate_average=candidate_average,
    )


def main() -> None:
    rows = [
        EvidenceRow(
            case_id="normal-1",
            critical=False,
            baseline_score=0.8,
            candidate_score=1.0,
        ),
        EvidenceRow(
            case_id="normal-2",
            critical=False,
            baseline_score=0.72,
            candidate_score=0.82,
        ),
        EvidenceRow(
            case_id="critical-refund",
            critical=True,
            baseline_score=1.0,
            candidate_score=0.0,
        ),
        EvidenceRow(
            case_id="judge-timeout-1",
            critical=False,
            baseline_score=None,
            candidate_score=None,
            status="evaluator_error",
        ),
        EvidenceRow(
            case_id="judge-timeout-2",
            critical=False,
            baseline_score=None,
            candidate_score=None,
            status="evaluator_error",
        ),
    ]

    decision = decide_release(
        rows,
        candidate_p95_latency_seconds=1.5,
    )
    print(decision)


if __name__ == "__main__":
    main()
