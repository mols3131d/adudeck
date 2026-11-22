"""Check the schema, retry feedback, and no-retry failure boundary."""

import unittest

from langchain.agents.structured_output import StructuredOutputValidationError
from langchain.messages import AIMessage, ToolMessage
from pydantic import ValidationError

from structured_response import Rating, run_scenario


class StructuredOutputTests(unittest.TestCase):
    def test_schema_rejects_out_of_range_value_locally(self) -> None:
        with self.assertRaises(ValidationError):
            Rating(score=9, reason="Not a valid rating")

    def test_valid_strategy_returns_validated_object(self) -> None:
        state = run_scenario("valid")
        self.assertIsInstance(state["structured_response"], Rating)
        self.assertEqual(state["structured_response"].score, 4)
        self.assertEqual(state["structured_response"].reason, "Documented evidence")
        self.assertEqual(len([m for m in state["messages"] if isinstance(m, AIMessage)]), 1)

    def test_invalid_then_repair_produces_feedback_and_new_request(self) -> None:
        state = run_scenario("repair")
        self.assertEqual(state["structured_response"].score, 4)
        requests = [
            call["id"]
            for message in state["messages"]
            if isinstance(message, AIMessage)
            for call in message.tool_calls
        ]
        self.assertEqual(requests, ["rating_invalid", "rating_repaired"])
        feedback = [m for m in state["messages"] if isinstance(m, ToolMessage)]
        self.assertEqual([m.tool_call_id for m in feedback], requests)
        self.assertIn("9", feedback[0].content)

    def test_no_retry_propagates_schema_error(self) -> None:
        with self.assertRaises(StructuredOutputValidationError):
            run_scenario("reject")


if __name__ == "__main__":
    unittest.main()
