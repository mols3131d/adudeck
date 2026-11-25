"""Behavior checks for the visible message and tool execution boundaries."""

import unittest

from first_agent import build_agent, run_agent, scripted_model
from langchain.messages import AIMessage, HumanMessage, ToolMessage


class AgentLoopTests(unittest.TestCase):
    def test_model_tool_call_is_only_a_request(self) -> None:
        response = scripted_model("tool").invoke([HumanMessage(content="Double 7.")])
        self.assertIsInstance(response, AIMessage)
        self.assertEqual(response.tool_calls[0]["args"], {"value": 7})
        self.assertEqual(response.tool_calls[0]["id"], "call_double_1")
        # No tool has been registered with or executed by this model invocation.

    def test_agent_executes_one_tool_then_resumes_model(self) -> None:
        messages, calls = run_agent("tool")
        self.assertEqual(calls, [7])
        self.assertEqual(
            [type(message) for message in messages],
            [HumanMessage, AIMessage, ToolMessage, AIMessage],
        )
        self.assertEqual(messages[1].tool_calls[0]["id"], messages[2].tool_call_id)
        self.assertEqual(messages[2].content, "14")
        self.assertEqual(messages[-1].content, "The doubled value is 14.")

    def test_no_tool_call_means_no_tool_execution(self) -> None:
        messages, calls = run_agent("no-tool")
        self.assertEqual(calls, [])
        self.assertEqual(
            [type(message) for message in messages], [HumanMessage, AIMessage]
        )
        self.assertFalse(messages[-1].tool_calls)

    def test_unhandled_tool_failure_is_not_a_successful_response(self) -> None:
        agent, calls = build_agent("error")
        with self.assertRaisesRegex(ValueError, "intentional tool failure"):
            agent.invoke({"messages": [HumanMessage(content="Double -1.")]})
        self.assertEqual(calls, [-1])


if __name__ == "__main__":
    unittest.main()
