"""Observe the LangChain agent loop with scripted model responses, without API calls."""

from __future__ import annotations

import argparse
from typing import Any

from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, ToolCall, ToolMessage
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel


class ScriptedToolModel(GenericFakeChatModel):
    """Adapter for the fake model: no provider-facing tool binding is needed."""

    def bind_tools(self, tools: Any, **kwargs: Any) -> ScriptedToolModel:
        return self


def scripted_model(scenario: str) -> ScriptedToolModel:
    if scenario == "no-tool":
        responses = [AIMessage(content="No calculation is needed.")]
    elif scenario in {"tool", "error"}:
        value = 7 if scenario == "tool" else -1
        responses = [
            AIMessage(
                content="",
                tool_calls=[
                    ToolCall(name="double", args={"value": value}, id="call_double_1")
                ],
            ),
            AIMessage(content="The doubled value is 14."),
        ]
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    return ScriptedToolModel(messages=iter(responses))


def build_agent(scenario: str) -> tuple[Any, list[int]]:
    calls: list[int] = []

    @tool
    def double(value: int) -> int:
        """Return twice an integer; -1 intentionally raises an example error."""
        calls.append(value)
        if value == -1:
            raise ValueError("intentional tool failure")
        return value * 2

    return create_agent(scripted_model(scenario), tools=[double]), calls


def run_agent(scenario: str) -> tuple[list[Any], list[int]]:
    agent, calls = build_agent(scenario)
    state = agent.invoke({"messages": [HumanMessage(content="Double 7 if needed.")]})
    return state["messages"], calls


def describe(messages: list[Any], calls: list[int]) -> None:
    for index, message in enumerate(messages):
        print(f"{index}: {type(message).__name__} content={message.content!r}")
        if isinstance(message, AIMessage):
            for call in message.tool_calls:
                print(
                    f"   tool_call id={call['id']} name={call['name']} "
                    f"args={call['args']}"
                )
        if isinstance(message, ToolMessage):
            print(f"   tool_result call_id={message.tool_call_id} status={message.status}")
    print(f"tool_executions={calls!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario", choices=("model-only", "no-tool", "tool", "error"), default="tool"
    )
    args = parser.parse_args()
    if args.scenario == "model-only":
        response = scripted_model("tool").invoke([HumanMessage(content="Double 7.")])
        describe([HumanMessage(content="Double 7."), response], [])
        return

    if args.scenario == "error":
        agent, calls = build_agent("error")
        try:
            agent.invoke({"messages": [HumanMessage(content="Double -1.")]})
        except ValueError as exc:
            print(f"raised={type(exc).__name__}: {exc}")
            print(f"tool_executions={calls!r}")
            return
        raise AssertionError("Expected the deliberate tool failure to propagate")

    messages, calls = run_agent(args.scenario)
    describe(messages, calls)


if __name__ == "__main__":
    main()
