from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any


BooleanEvaluator = Callable[[str], bool]


def answer_mentions_policy_days(answer: str) -> bool:
    return "14일" in answer


def retrieval_contains_policy(document: str) -> bool:
    return "14일" in document and "환불" in document


def evaluate_then_record_scores(
    root_observation: Any,
    retrieval_observation: Any,
    *,
    answer: str,
    document: str,
    answer_evaluator: BooleanEvaluator = answer_mentions_policy_days,
    retrieval_evaluator: BooleanEvaluator = retrieval_contains_policy,
) -> dict[str, bool]:
    """Evaluate first, then record scores so evaluator failure is not disguised as score 0."""
    answer_passed = answer_evaluator(answer)
    retrieval_passed = retrieval_evaluator(document)

    root_observation.score_trace(
        name="policy-answer-correct",
        value=1.0 if answer_passed else 0.0,
        data_type="BOOLEAN",
        comment="deterministic policy-days check",
    )
    retrieval_observation.score(
        name="retrieval-relevant",
        value=1.0 if retrieval_passed else 0.0,
        data_type="BOOLEAN",
        comment="deterministic retrieval evidence check",
    )

    return {
        "answer_passed": answer_passed,
        "retrieval_passed": retrieval_passed,
    }


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

    from langfuse import get_client

    langfuse = get_client()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="support-turn",
        input={"question": "환불 기간은?"},
    ) as root:
        with langfuse.start_as_current_observation(
            as_type="span",
            name="retrieve-policy",
            input={"query": "환불 기간"},
        ) as retrieval:
            document = "구매 후 14일 이내 환불 가능"
            retrieval.update(output={"document": document})

        answer = "구매 후 14일 이내라면 환불할 수 있습니다."
        root.update(output={"answer": answer})

        evidence = evaluate_then_record_scores(
            root,
            retrieval,
            answer=answer,
            document=document,
        )

    print(evidence)
    langfuse.flush()


if __name__ == "__main__":
    main()
