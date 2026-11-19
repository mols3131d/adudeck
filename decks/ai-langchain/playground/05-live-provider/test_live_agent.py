"""Safe validation of live-lab opt-in and response-inspection invariants."""

import unittest

from langchain.messages import AIMessage, HumanMessage, ToolCall, ToolMessage

from live_agent import inspect_execution, require_live_permission


def example_messages(tool_result_id: str = "call_1") -> list:
    return [
        HumanMessage(content="Double 7."),
        AIMessage(
            content="",
            tool_calls=[ToolCall(name="double", args={"value": 7}, id="call_1")],
        ),
        ToolMessage(content="14", tool_call_id=tool_result_id),
        AIMessage(content="14"),
    ]


class LiveSafetyTests(unittest.TestCase):
    def test_no_explicit_approval_makes_no_provider_request(self) -> None:
        with self.assertRaisesRegex(SystemExit, "No API call made"):
            require_live_permission(execute=False, api_key="an-example-not-a-real-key")

    def test_missing_credential_makes_no_provider_request(self) -> None:
        with self.assertRaisesRegex(SystemExit, "No API call made"):
            require_live_permission(execute=True, api_key=None)

    def test_tool_id_consistency_is_required(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "does not match"):
            inspect_execution(example_messages("wrong_call"))

    def test_success_output_requires_tool_execution_evidence(self) -> None:
        self.assertEqual(inspect_execution(example_messages()), (1, 1, "14"))

    def test_failure_tool_result_is_not_success(self) -> None:
        messages = example_messages()
        messages[2] = ToolMessage(content="failed", tool_call_id="call_1", status="error")
        with self.assertRaisesRegex(RuntimeError, "tool failed"):
            inspect_execution(messages)


if __name__ == "__main__":
    unittest.main()
