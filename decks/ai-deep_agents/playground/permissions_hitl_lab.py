"""Test real SDK filesystem permission ordering and HITL pause/resume.

All changes are confined to LangGraph's in-process StateBackend or a Python list.
No host filesystem, external service, or email is modified.
"""

from __future__ import annotations

import json

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import StateBackend
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from first_loop import RecordingFakeModel, tool_call


def run_permission_case() -> dict[str, object]:
    model = RecordingFakeModel(responses=[
        AIMessage(content="", tool_calls=[
            tool_call("write_file", "permitted", {
                "file_path": "/reports/approved/summary.md", "content": "approved content"
            }),
            tool_call("write_file", "blocked", {
                "file_path": "/reports/private/summary.md", "content": "blocked content"
            }),
            tool_call("write_file", "unmatched", {
                "file_path": "/scratch/free.md", "content": "default allow content"
            }),
        ]),
        AIMessage(content="Finished permission checks."),
    ])
    agent = create_deep_agent(
        model=model,
        backend=StateBackend(),
        permissions=[
            FilesystemPermission(
                operations=["write"], paths=["/reports/approved/**"], mode="allow"
            ),
            FilesystemPermission(
                operations=["write"], paths=["/reports/**"], mode="deny"
            ),
        ],
    )
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Write three synthetic reports."}]
    })
    responses = {
        message.tool_call_id: {
            "status": message.status,
            "content": str(message.content),
        }
        for message in result["messages"] if isinstance(message, ToolMessage)
    }
    return {
        "responses": responses,
        "files": sorted((result.get("files") or {}).keys()),
    }


def run_review_case(decision: str) -> dict[str, object]:
    """Pause before a synthetic action, then approve or reject on the SAME thread."""
    if decision not in ("approve", "reject"):
        raise ValueError(f"Invalid decision: {decision}")

    effects: list[str] = []

    @tool
    def record_local_change(label: str) -> str:
        """Record a synthetic local action requiring approval."""
        effects.append(label)
        return f"Recorded local change: {label}"

    model = RecordingFakeModel(responses=[
        AIMessage(content="", tool_calls=[
            tool_call("record_local_change", "approval-1", {"label": "ready"}),
        ]),
        AIMessage(content="The review decision has been applied."),
    ])
    agent = create_deep_agent(
        model=model,
        tools=[record_local_change],
        backend=StateBackend(),
        interrupt_on={
            "record_local_change": {"allowed_decisions": ["approve", "reject"]},
        },
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": f"review-{decision}"}}
    paused = agent.invoke({
        "messages": [{"role": "user", "content": "Record the synthetic local change."}]
    }, config=config)
    action_requests = []
    for item in paused.get("__interrupt__", ()):
        action_requests.extend(item.value.get("action_requests", []))
    effects_before = effects.copy()

    action = {"type": decision}
    if decision == "reject":
        action["message"] = "The change is not authorized."
    resumed = agent.invoke(
        Command(resume={"decisions": [action]}),
        config=config,
    )
    return {
        "interrupted": "__interrupt__" in paused,
        "requested_actions": [request["name"] for request in action_requests],
        "effects_at_pause": effects_before,
        "effects_after_resume": effects.copy(),
        "resumed_without_interrupt": "__interrupt__" not in resumed,
        "returned_tools": [
            {"name": m.name, "content": str(m.content), "status": m.status}
            for m in resumed.get("messages", []) if isinstance(m, ToolMessage)
        ],
    }


if __name__ == "__main__":
    print(json.dumps({
        "permissions": run_permission_case(),
        "approved": run_review_case("approve"),
        "rejected": run_review_case("reject"),
    }, indent=2, ensure_ascii=False))
