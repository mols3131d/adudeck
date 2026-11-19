"""Observe each agent step and contrast propagation with middleware recovery."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import AIMessage, HumanMessage, ToolCall, ToolMessage
from langchain.tools import tool
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command

from first_agent import ScriptedToolModel, build_agent


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

    @tool
    def double(value: int) -> int:
        """Return twice a number, except the sentinel -1 raises a local failure."""
        calls.append(value)
        if value == -1:
            raise ValueError("intentional tool failure")
        return value * 2

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
            last = messages[-1] if messages else None
            if isinstance(last, AIMessage) and last.tool_calls:
                detail = f"requested={last.tool_calls[0]['id']}"
            elif isinstance(last, ToolMessage):
                detail = f"result_for={last.tool_call_id} status={last.status}"
            else:
                detail = f"response={getattr(last, 'content', None)!r}"
            print(f"step-{index}: node={node} {detail}")
    print(f"tool_executions={calls!r}")

    state, failed_calls = recover_failure()
    error_messages = [
        message for message in state["messages"]
        if isinstance(message, ToolMessage) and message.status == "error"
    ]
    for message in error_messages:
        print(f"recovered_error: id={message.tool_call_id} status={message.status}")
    print(f"final={state['messages'][-1].content!r} tool_executions={failed_calls!r}")


if __name__ == "__main__":
    main()
