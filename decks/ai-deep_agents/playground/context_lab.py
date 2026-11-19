"""Observe thread-local virtual files, checkpoint replay, and cross-thread store routing.

All operations use in-process LangGraph memory; no host filesystem or model API is used.
"""

from __future__ import annotations

import json

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from first_loop import RecordingFakeModel, tool_call


def scripted_responses() -> list[AIMessage]:
    return [
        AIMessage(content="", tool_calls=[
            tool_call("write_file", "write-local", {
                "file_path": "/scratch/local.md", "content": "only thread A"
            }),
            tool_call("write_file", "write-shared", {
                "file_path": "/memories/shared.md", "content": "shared across threads"
            }),
        ]),
        AIMessage(content="Saved both files."),
        AIMessage(content="", tool_calls=[
            tool_call("read_file", "read-shared-b", {"file_path": "/memories/shared.md"}),
            tool_call("read_file", "read-local-b", {"file_path": "/scratch/local.md"}),
        ]),
        AIMessage(content="Only the shared file was readable."),
        AIMessage(content="", tool_calls=[
            tool_call("read_file", "read-local-a", {"file_path": "/scratch/local.md"}),
        ]),
        AIMessage(content="Thread A can still read its scratch file."),
    ]


def tool_result(messages: list, call_id: str) -> dict[str, str]:
    message = next(
        msg for msg in messages
        if isinstance(msg, ToolMessage) and msg.tool_call_id == call_id
    )
    return {"status": message.status, "content": str(message.content)}


def run_lab() -> dict[str, object]:
    """Use one graph and two thread IDs to distinguish state from shared store."""
    model = RecordingFakeModel(responses=scripted_responses())
    store = InMemoryStore()
    agent = create_deep_agent(
        model=model,
        backend=CompositeBackend(
            default=StateBackend(),
            routes={"/memories/": StoreBackend(namespace=lambda _runtime: ("adudeck-demo",))},
        ),
        checkpointer=InMemorySaver(),
        store=store,
    )
    config_a = {"configurable": {"thread_id": "lesson-a"}}
    config_b = {"configurable": {"thread_id": "lesson-b"}}

    first = agent.invoke({"messages": [{"role": "user", "content": "Save two synthetic notes."}]}, config=config_a)
    snapshot_a = sorted((agent.get_state(config_a).values.get("files") or {}).keys())

    second = agent.invoke({"messages": [{"role": "user", "content": "Read both notes."}]}, config=config_b)
    snapshot_b = sorted((agent.get_state(config_b).values.get("files") or {}).keys())

    revisit = agent.invoke({"messages": [{"role": "user", "content": "Read my local note."}]}, config=config_a)
    return {
        "written": {
            "thread_file": tool_result(first["messages"], "write-local"),
            "shared_file": tool_result(first["messages"], "write-shared"),
        },
        "thread_a_files": snapshot_a,
        "thread_b_files": snapshot_b,
        "thread_b_reads": {
            "shared": tool_result(second["messages"], "read-shared-b"),
            "scratch": tool_result(second["messages"], "read-local-b"),
        },
        "thread_a_revisit": tool_result(revisit["messages"], "read-local-a"),
    }


def run_large_result_lab() -> dict[str, object]:
    """Evict an oversized *tool result* into a virtual StateBackend file."""
    from deepagents.middleware.filesystem import FilesystemMiddleware
    from langchain_core.tools import tool

    original = "alpha:120ms, beta:260ms, error delta:3%; " * 180

    @tool
    def large_report(topic: str) -> str:
        """Return a deliberately oversized synthetic report for context inspection."""
        if topic != "synthetic":
            raise ValueError("Only a synthetic report is available.")
        return original

    model = RecordingFakeModel(responses=[
        AIMessage(content="", tool_calls=[
            tool_call("large_report", "big-report-1", {"topic": "synthetic"})
        ]),
        AIMessage(content="Large report inspection complete."),
    ])
    backend = StateBackend()
    agent = create_deep_agent(
        model=model,
        backend=backend,
        tools=[large_report],
        # Deliberately low for teaching; the SDK default is much higher.
        middleware=[FilesystemMiddleware(backend=backend, tool_token_limit_before_evict=50)],
    )
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Inspect a synthetic large report."}]
    })
    tool_message = next(
        msg for msg in result["messages"]
        if isinstance(msg, ToolMessage) and msg.tool_call_id == "big-report-1"
    )
    saved_files = (result.get("files") or {}).keys()
    return {
        "original_chars": len(original),
        "tool_message_chars": len(str(tool_message.content)),
        "artifact_paths": sorted(path for path in saved_files if path.startswith("/large_tool_results/")),
        "tool_message_excerpt": str(tool_message.content)[:160],
    }


if __name__ == "__main__":
    print(json.dumps({
        "thread_and_store": run_lab(),
        "large_result": run_large_result_lab(),
    }, indent=2, ensure_ascii=False))
