"""Verify streamed agent steps and explicit error-preserving middleware behavior."""

import unittest

from langchain.messages import AIMessage, HumanMessage, ToolMessage

from first_agent import build_agent
from trace_and_recovery import recover_failure, stream_success


class StreamAndRecoveryTests(unittest.TestCase):
    def test_updates_expose_request_tool_and_final_model(self) -> None:
        updates, calls = stream_success()
        self.assertEqual(calls, [7])
        self.assertEqual(
            [node for update in updates for node in update],
            ["model", "tools", "model"],
        )

    def test_stream_pairs_result_with_original_request(self) -> None:
        updates, _ = stream_success()
        request = updates[0]["model"]["messages"][-1]
        result = updates[1]["tools"]["messages"][-1]
        answer = updates[2]["model"]["messages"][-1]
        self.assertIsInstance(request, AIMessage)
        self.assertIsInstance(result, ToolMessage)
        self.assertEqual(request.tool_calls[0]["id"], result.tool_call_id)
        self.assertEqual(result.content, "14")
        self.assertEqual(answer.content, "The doubled value is 14.")

    def test_without_middleware_failure_still_propagates(self) -> None:
        agent, calls = build_agent("error")
        with self.assertRaisesRegex(ValueError, "intentional tool failure"):
            agent.invoke({"messages": [HumanMessage(content="Double -1.")]})
        self.assertEqual(calls, [-1])

    def test_middleware_converts_exception_to_explicit_error_message(self) -> None:
        state, calls = recover_failure()
        self.assertEqual(calls, [-1])
        messages = state["messages"]
        self.assertEqual(
            [type(message) for message in messages],
            [HumanMessage, AIMessage, ToolMessage, AIMessage],
        )
        self.assertEqual(messages[1].tool_calls[0]["id"], messages[2].tool_call_id)
        self.assertEqual(messages[2].status, "error")
        self.assertIn("intentional tool failure", messages[2].content)
        self.assertIn("cannot calculate", messages[-1].content)


if __name__ == "__main__":
    unittest.main()
