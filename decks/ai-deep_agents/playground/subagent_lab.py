"""Observe real task delegation with separate parent and child model contexts."""

from __future__ import annotations

import json

from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool

from first_loop import RecordingFakeModel, tool_call


def run_lab(*, unknown_agent: bool = False) -> dict[str, object]:
    """Use a scripted supervisor and researcher; run real subagent dispatch."""
    child_calls: list[str] = []

    @tool
    def inspect_fixture(service: str) -> str:
        """Return a synthetic alpha service observation for the researcher."""
        child_calls.append(service)
        return "alpha: p95=120ms, errors=1%"

    child_model = RecordingFakeModel(responses=[
        AIMessage(content="", tool_calls=[
            tool_call("inspect_fixture", "child-lookup", {"service": "alpha"}),
        ]),
        AIMessage(content="The researcher found alpha p95=120ms and 1% errors."),
    ])
    subagent = {
        "name": "researcher",
        "description": "Inspect one synthetic service and return a short result.",
        "system_prompt": "Use inspect_fixture and summarize the alpha service observation.",
        "model": child_model,
        "tools": [inspect_fixture],
    }

    target = "unknown-researcher" if unknown_agent else "researcher"
    parent_model = RecordingFakeModel(responses=[
        AIMessage(content="", tool_calls=[
            tool_call("task", "parent-task", {
                "subagent_type": target,
                "description": "Inspect synthetic alpha latency and errors.",
            }),
        ]),
        AIMessage(content="The parent received the researcher's summary."),
    ])
    parent = create_deep_agent(
        model=parent_model,
        backend=StateBackend(),
        subagents=[subagent],
    )
    result = parent.invoke({
        "messages": [{"role": "user", "content": "Delegate alpha service inspection."}]
    })

    task_messages = [
        message for message in result["messages"]
        if isinstance(message, ToolMessage) and message.name == "task"
    ]
    return {
        "target": target,
        "parent_offered_tools": sorted({name for row in parent_model.exposed for name in row}),
        "child_offered_tools": sorted({name for row in child_model.exposed for name in row}),
        "parent_tool_messages": [message.name for message in result["messages"] if isinstance(message, ToolMessage)],
        "task_result": [
            {"status": message.status, "content": str(message.content)}
            for message in task_messages
        ],
        "child_fixture_calls": child_calls,
        "parent_last": str(result["messages"][-1].content),
    }


if __name__ == "__main__":
    print(json.dumps({
        "delegated": run_lab(),
        "unknown_subagent": run_lab(unknown_agent=True),
    }, indent=2, ensure_ascii=False))
