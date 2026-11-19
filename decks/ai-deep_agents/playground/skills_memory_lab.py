"""Inspect skills' lazy loading and the memory file injected into model prompts.

The model is scripted, while SDK middleware, tool reads/writes, and store are real.
"""

from __future__ import annotations

import json
from typing import Any

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from pydantic import Field

from first_loop import RecordingFakeModel, tool_call


INITIAL_MEMORY = "Project preference: discuss p95 latency and error percentage."
UPDATED_MEMORY = "Project preference: discuss error percentage before p95 latency."
SKILL_TEXT = """---
name: compare-services
description: Evaluate synthetic service latency and errors.
---
When comparing services, include both p95 latency and error percentage.
"""


class InspectingModel(RecordingFakeModel):
    """Record actual model request text; do not derive behavior from scripted responses."""

    prompts: list[str] = Field(default_factory=list)

    def _generate(self, messages: list, stop: list[str] | None = None, run_manager: Any = None, **kwargs: Any):
        self.prompts.append("\n".join(str(message.content) for message in messages))
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


def run_lab() -> dict[str, object]:
    store = InMemoryStore()
    skills_backend = StoreBackend(namespace=lambda _runtime: ("adudeck-demo", "skills"), store=store)
    memory_backend = StoreBackend(namespace=lambda _runtime: ("adudeck-demo", "memory"), store=store)
    skills_backend.write("/compare/SKILL.md", SKILL_TEXT)
    memory_backend.write("/AGENTS.md", INITIAL_MEMORY)

    model = InspectingModel(responses=[
        AIMessage(content="", tool_calls=[
            tool_call("read_file", "skill-read", {"file_path": "/skills/compare/SKILL.md"}),
        ]),
        AIMessage(content="The skill instructions have been read."),
        AIMessage(content="", tool_calls=[
            tool_call("write_file", "memory-write", {
                "file_path": "/memories/AGENTS.md", "content": UPDATED_MEMORY
            }),
        ]),
        AIMessage(content="Memory was updated."),
        AIMessage(content="A different thread sees the new memory at model-call time."),
    ])
    agent = create_deep_agent(
        model=model,
        backend=CompositeBackend(
            default=StateBackend(),
            routes={
                "/skills/": skills_backend,
                "/memories/": memory_backend,
            },
        ),
        skills=["/skills/"],
        memory=["/memories/AGENTS.md"],
        store=store,
        checkpointer=InMemorySaver(),
        permissions=[
            FilesystemPermission(operations=["write"], paths=["/skills/**"], mode="deny")
        ],
    )
    def config(thread: str) -> dict:
        return {"configurable": {"thread_id": thread}}

    first = agent.invoke({"messages": [{"role": "user", "content": "Use the comparison skill."}]}, config=config("reader"))
    second = agent.invoke({"messages": [{"role": "user", "content": "Update the memory note."}]}, config=config("editor"))
    agent.invoke({"messages": [{"role": "user", "content": "Read current memory."}]}, config=config("new-reader"))

    def result(messages: list, call_id: str) -> dict:
        item = next(msg for msg in messages if isinstance(msg, ToolMessage) and msg.tool_call_id == call_id)
        return {"status": item.status, "content": str(item.content)}

    return {
        "model_requests": model.prompts,
        "read_skill": result(first["messages"], "skill-read"),
        "update_memory": result(second["messages"], "memory-write"),
        "store_memory": memory_backend.read("/AGENTS.md").file_data,
        "stored_skill_after": skills_backend.read("/compare/SKILL.md").file_data,
    }


if __name__ == "__main__":
    evidence = run_lab()
    evidence["model_requests"] = [
        {"turn": i + 1, "contains_old_memory": INITIAL_MEMORY in text,
         "contains_new_memory": UPDATED_MEMORY in text,
         "skill_summary": "compare-services" in text,
         "full_skill_body": "When comparing services" in text}
        for i, text in enumerate(evidence["model_requests"])
    ]
    print(json.dumps(evidence, ensure_ascii=False, indent=2, default=str))
