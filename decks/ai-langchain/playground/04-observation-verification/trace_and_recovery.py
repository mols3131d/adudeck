"""Observe each agent step and contrast propagation with middleware recovery."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import AIMessage, HumanMessage, ToolCall, ToolMessage
from langchain.tools import tool
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langgraph.types import Command


class ScriptedToolModel(GenericFakeChatModel):
    """Adapter for the fake model: no provider-facing tool binding is needed."""

    def bind_tools(self, tools: Any, **kwargs: Any) -> ScriptedToolModel:
        return self


def _build_double_tool(calls: list[int]) -> Any:
    @tool
    def double(value: int) -> int:
        """Return twice a number, except the sentinel -1 raises a local failure."""
        calls.append(value)
        if value == -1:
            raise ValueError("intentional tool failure")
        return value * 2

    return double


def build_agent(scenario: str) -> tuple[Any, list[int]]:
    calls: list[int] = []
    double = _build_double_tool(calls)
    if scenario == "tool":
        value = 7
        final_answer = "The doubled value is 14."
    elif scenario == "error":
        value = -1
        final_answer = "Unreachable when unhandled tool error propagates."
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    model = ScriptedToolModel(
        messages=iter(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        ToolCall(
                            name="double",
                            args={"value": value},
                            id="call_double_1",
                        )
                    ],
                ),
                AIMessage(content=final_answer),
            ]
        )
    )
    return create_agent(model, tools=[double]), calls


def stream_success() -> tuple[list[dict[str, Any]], list[int]]:
    agent, calls = build_agent("tool")
    events = list(
        agent.stream(
            {"messages": [HumanMessage(content="Double 7.")]},
            stream_mode="updates",
        )
    )
    return events, calls


def build_recovering_agent() -> tuple[Any, list[int]]:
    calls: list[int] = []
    double = _build_double_tool(calls)

    @wrap_tool_call
    def report_failure(
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        try:
            return handler(request)
        except ValueError as exc:
            # The error remains an error; the model can decide what to say next.
            return ToolMessage(
                content=f"tool failed: {exc}",
                tool_call_id=request.tool_call["id"],
                status="error",
            )

    model = ScriptedToolModel(
        messages=iter(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        ToolCall(name="double", args={"value": -1}, id="failed_call")
                    ],
                ),
                AIMessage(content="I cannot calculate: the tool returned an error."),
            ]
        )
    )
    return create_agent(model, tools=[double], middleware=[report_failure]), calls


def recover_failure() -> tuple[dict[str, Any], list[int]]:
    agent, calls = build_recovering_agent()
    state = agent.invoke({"messages": [HumanMessage(content="Double -1.")]})
    return state, calls


def main() -> None:
    updates, calls = stream_success()
    for index, update in enumerate(updates, start=1):
        for node, changed_state in update.items():
            messages = changed_state.get("messages", [])
            for message in messages:
                if isinstance(message, AIMessage) and message.tool_calls:
                    requested = ", ".join(
                        str(call["id"]) for call in message.tool_calls
                    )
                    detail = f"requested={requested}"
                elif isinstance(message, ToolMessage):
                    detail = (
                        f"result_for={message.tool_call_id} status={message.status}"
                    )
                else:
                    detail = f"response={getattr(message, 'content', None)!r}"
                print(f"step-{index}: node={node} {detail}")
    print(f"tool_executions={calls!r}")

    state, failed_calls = recover_failure()
    error_messages = [
        message
        for message in state["messages"]
        if isinstance(message, ToolMessage) and message.status == "error"
    ]
    for message in error_messages:
        print(f"recovered_error: id={message.tool_call_id} status={message.status}")
    print(f"final={state['messages'][-1].content!r} tool_executions={failed_calls!r}")


if __name__ == "__main__":
    main()
