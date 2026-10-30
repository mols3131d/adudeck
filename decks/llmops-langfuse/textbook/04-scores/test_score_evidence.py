from __future__ import annotations

import unittest

from score_evidence import evaluate_then_record_scores


class ScoreRecorder:
    def __init__(self) -> None:
        self.trace_scores: list[dict[str, object]] = []
        self.observation_scores: list[dict[str, object]] = []

    def score_trace(self, **kwargs) -> None:
        self.trace_scores.append(kwargs)

    def score(self, **kwargs) -> None:
        self.observation_scores.append(kwargs)


class ScoreEvidenceContractTest(unittest.TestCase):
    def test_scores_attach_to_the_level_the_evaluator_judges(self) -> None:
        root = ScoreRecorder()
        retrieval = ScoreRecorder()

        result = evaluate_then_record_scores(
            root,
            retrieval,
            answer="14일 이내 환불 가능합니다.",
            document="환불 정책: 구매 후 14일 이내",
        )

        self.assertEqual(result, {"answer_passed": True, "retrieval_passed": True})
        self.assertEqual(root.trace_scores[0]["name"], "policy-answer-correct")
        self.assertEqual(root.trace_scores[0]["value"], 1.0)
        self.assertEqual(root.trace_scores[0]["data_type"], "BOOLEAN")
        self.assertEqual(
            retrieval.observation_scores[0]["name"],
            "retrieval-relevant",
        )
        self.assertEqual(retrieval.observation_scores[0]["value"], 1.0)

    def test_valid_low_quality_is_score_zero(self) -> None:
        root = ScoreRecorder()
        retrieval = ScoreRecorder()

        result = evaluate_then_record_scores(
            root,
            retrieval,
            answer="환불할 수 없습니다.",
            document="배송 안내",
        )

        self.assertEqual(result, {"answer_passed": False, "retrieval_passed": False})
        self.assertEqual(root.trace_scores[0]["value"], 0.0)
        self.assertEqual(retrieval.observation_scores[0]["value"], 0.0)

    def test_evaluator_failure_produces_no_score_instead_of_zero(self) -> None:
        root = ScoreRecorder()
        retrieval = ScoreRecorder()

        def failing_evaluator(_: str) -> bool:
            raise RuntimeError("evaluator unavailable")

        with self.assertRaisesRegex(RuntimeError, "evaluator unavailable"):
            evaluate_then_record_scores(
                root,
                retrieval,
                answer="14일",
                document="환불 정책: 14일",
                answer_evaluator=failing_evaluator,
            )

        self.assertEqual(root.trace_scores, [])
        self.assertEqual(retrieval.observation_scores, [])


if __name__ == "__main__":
    unittest.main()
