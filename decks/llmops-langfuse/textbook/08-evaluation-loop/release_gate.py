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
class VariantEvidence:
    status: EvaluationStatus
    score: float | None = None

    def __post_init__(self) -> None:
        if self.status == "scored" and self.score is None:
            raise ValueError("scored evidence requires a score")
        if self.status != "scored" and self.score is not None:
            raise ValueError("non-scored evidence must not carry a score")

    @classmethod
    def scored(cls, score: float) -> VariantEvidence:
        return cls(status="scored", score=score)

    @classmethod
    def gap(cls, status: EvaluationStatus) -> VariantEvidence:
        if status == "scored":
            raise ValueError("use VariantEvidence.scored() for scored evidence")
        return cls(status=status)


@dataclass(frozen=True)
class EvidenceRow:
    case_id: str
    critical: bool
    baseline: VariantEvidence
    candidate: VariantEvidence


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
    baseline_coverage: float
    candidate_coverage: float
    paired_coverage: float


def _coverage(rows: list[EvidenceRow], *, candidate: bool) -> float:
    if not rows:
        return 0.0
    scored = sum(
        1
        for row in rows
        if (row.candidate if candidate else row.baseline).status == "scored"
    )
    return scored / len(rows)


def _paired_scored_rows(rows: list[EvidenceRow]) -> list[EvidenceRow]:
    return [
        row
        for row in rows
        if row.baseline.status == "scored" and row.candidate.status == "scored"
    ]


def _paired_average(
    rows: list[EvidenceRow],
    *,
    candidate: bool,
) -> float | None:
    paired_rows = _paired_scored_rows(rows)
    if not paired_rows:
        return None

    values = [
        row.candidate.score if candidate else row.baseline.score
        for row in paired_rows
    ]
    return sum(score for score in values if score is not None) / len(paired_rows)


def decide_release(
    rows: list[EvidenceRow],
    *,
    candidate_p95_latency_seconds: float,
    policy: ReleasePolicy = ReleasePolicy(),
) -> ReleaseDecision:
    reasons: list[str] = []

    if policy.require_no_evaluation_gaps:
        for row in rows:
            if row.baseline.status != "scored":
                reasons.append(f"{row.case_id}: baseline {row.baseline.status}")
            if row.candidate.status != "scored":
                reasons.append(f"{row.case_id}: candidate {row.candidate.status}")

    if policy.require_all_critical_pass:
        for row in rows:
            if not row.critical or row.candidate.status != "scored":
                continue
            if row.candidate.score == 1.0:
                continue

            if row.baseline.status == "scored" and row.baseline.score == 1.0:
                reasons.append(f"{row.case_id}: critical regression")
            else:
                reasons.append(f"{row.case_id}: critical candidate failure")

    paired_rows = _paired_scored_rows(rows)
    baseline_average = _paired_average(rows, candidate=False)
    candidate_average = _paired_average(rows, candidate=True)

    if baseline_average is None or candidate_average is None:
        reasons.append("paired correctness comparison unavailable")
    elif candidate_average - baseline_average < policy.min_correctness_delta:
        reasons.append("candidate correctness is below the required baseline delta")

    if candidate_p95_latency_seconds > policy.max_p95_latency_seconds:
        reasons.append("candidate p95 latency exceeds the release policy")

    return ReleaseDecision(
        approved=not reasons,
        reasons=tuple(reasons),
        baseline_average=baseline_average,
        candidate_average=candidate_average,
        baseline_coverage=_coverage(rows, candidate=False),
        candidate_coverage=_coverage(rows, candidate=True),
        paired_coverage=len(paired_rows) / len(rows) if rows else 0.0,
    )


def main() -> None:
    rows = [
        EvidenceRow(
            case_id="normal-1",
            critical=False,
            baseline=VariantEvidence.scored(0.8),
            candidate=VariantEvidence.scored(1.0),
        ),
        EvidenceRow(
            case_id="normal-2",
            critical=False,
            baseline=VariantEvidence.scored(0.72),
            candidate=VariantEvidence.scored(0.82),
        ),
        EvidenceRow(
            case_id="critical-refund",
            critical=True,
            baseline=VariantEvidence.scored(1.0),
            candidate=VariantEvidence.scored(0.0),
        ),
        EvidenceRow(
            case_id="judge-timeout-1",
            critical=False,
            baseline=VariantEvidence.scored(0.9),
            candidate=VariantEvidence.gap("evaluator_error"),
        ),
        EvidenceRow(
            case_id="judge-timeout-2",
            critical=False,
            baseline=VariantEvidence.scored(0.8),
            candidate=VariantEvidence.gap("evaluator_error"),
        ),
    ]

    decision = decide_release(
        rows,
        candidate_p95_latency_seconds=1.5,
    )
    print(decision)


if __name__ == "__main__":
    main()
