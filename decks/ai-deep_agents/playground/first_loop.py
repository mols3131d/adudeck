"""Compare a real LangChain/Deep Agents tool loop with deterministic model responses.

No provider credentials, network tool or host-filesystem backend is used.
The fake model scripts decisions; LangGraph still runs the real tools/middleware.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import StateBackend
from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import Field


FIXTURES = {
    "alpha": "alpha: p95=120ms, errors=1%",
    "beta": "beta: p95=260ms, errors=4%",
}
QUESTION = "Compare the synthetic latency and error rates for alpha and beta."


@tool
def lookup_fixture(service: str) -> str:
    """Return synthetic latency and error statistics for a named service."""
    return FIXTURES[service]


class RecordingFakeModel(FakeMessagesListChatModel):
    """Script tool calls while recording the tool surface handed to the model.

    This model-side probe is intentionally not an SDK public introspection API.
    """

    exposed: list[list[str]] = Field(default_factory=list)

    def bind_tools(self, tools: Any, **kwargs: Any) -> RecordingFakeModel:
        names = []
        for item in tools:
            if isinstance(item, dict):
                names.append(item.get("name") or item.get("function", {}).get("name", "?"))
            else:
                names.append(item.name)
        self.exposed.append(names)
        return self


def tool_call(name: str, call_id: str, args: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "id": call_id, "args": args}


def scripted_messages(case: str) -> list[AIMessage]:
    lookups = AIMessage(
        content="",
        tool_calls=[
            tool_call("lookup_fixture", "lookup-alpha", {"service": "alpha"}),
            tool_call("lookup_fixture", "lookup-beta", {"service": "beta"}),
        ],
    )
    answer = AIMessage(content="beta has higher p95 latency (260 vs 120 ms) and error rate (4% vs 1%).")
    if case == "planned":
        return [
            AIMessage(
                content="",
                tool_calls=[
                    tool_call(
                        "write_todos",
                        "plan-1",
                        {"todos": [{"content": "Compare two fixture services", "status": "in_progress"}]},
                    )
                ],
            ),
            lookups,
            AIMessage(
                content="",
                tool_calls=[
                    tool_call(
                        "write_todos",
                        "plan-2",
                        {"todos": [{"content": "Compare two fixture services", "status": "completed"}]},
                    )
                ],
            ),
            answer,
        ]
    if case == "denied":
        return [
            AIMessage(
                content="",
                tool_calls=[
                    tool_call("write_file", "write-1", {"file_path": "/notes/output.txt", "content": "should not persist"}),
                    tool_call("lookup_fixture", "lookup-alpha", {"service": "alpha"}),
                ],
            ),
            AIMessage(content="The filesystem write was denied; the read-only fixture returned alpha statistics."),
        ]
    return [lookups, answer]


def run_case(case: str) -> dict[str, Any]:
    """Run the actual agent graph, returning only small inspection evidence."""
    if case not in ("basic", "deep", "planned", "denied"):
        raise ValueError(f"Unknown experiment: {case}")

    model = RecordingFakeModel(responses=scripted_messages(case))
    if case == "basic":
        agent = create_agent(model=model, tools=[lookup_fixture])
    else:
        middleware = [TodoListMiddleware()] if case == "planned" else []
        agent = create_deep_agent(
            model=model,
            tools=[lookup_fixture],
            backend=StateBackend(),
            middleware=middleware,
            permissions=[FilesystemPermission(operations=["write"], paths=["/**"], mode="deny")],
        )

    result = agent.invoke({"messages": [{"role": "user", "content": QUESTION}]})
    messages = result["messages"]
    calls = [
        {"name": call["name"], "args": call["args"]}
        for message in messages
        if isinstance(message, AIMessage)
        for call in message.tool_calls
    ]
    returns = [
        {"name": message.name, "status": message.status, "content": message.content}
        for message in messages
        if isinstance(message, ToolMessage)
    ]
    timeline = []
    for message in messages:
        if isinstance(message, AIMessage):
            timeline.append({
                "actor": "model",
                "tool_calls": [{"id": call["id"], "name": call["name"]} for call in message.tool_calls],
            })
        elif isinstance(message, ToolMessage):
            timeline.append({
                "actor": "tool",
                "name": message.name,
                "tool_call_id": message.tool_call_id,
                "status": message.status,
            })
        else:
            timeline.append({"actor": message.type})

    return {
        "case": case,
        "timeline": timeline,
        "offered_tools": sorted({name for names in model.exposed for name in names}),
        "calls": calls,
        "tool_results": returns,
        "state_keys": sorted(result),
        "files": sorted((result.get("files") or {}).keys()),
        "todos": result.get("todos"),
        "final_message": messages[-1].content,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("basic", "deep", "planned", "denied", "all"), default="all")
    args = parser.parse_args()
    cases = ("basic", "deep", "planned", "denied") if args.case == "all" else (args.case,)
    print(json.dumps([run_case(case) for case in cases], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
