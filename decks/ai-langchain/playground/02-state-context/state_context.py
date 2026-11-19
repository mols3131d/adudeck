"""Compare persisted agent state, ephemeral run context, and middleware hooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import AgentState, after_model, before_model
from langchain.messages import HumanMessage
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime


@dataclass
class RunContext:
    label: str


def build_lab() -> tuple[Any, list[tuple[str, str, int]]]:
    observations: list[tuple[str, str, int]] = []

    @before_model
    def observe_input(state: AgentState, runtime: Runtime) -> None:
        observations.append(("before", runtime.context.label, len(state["messages"])))

    @after_model
    def observe_output(state: AgentState, runtime: Runtime) -> None:
        observations.append(("after", runtime.context.label, len(state["messages"])))

    model = GenericFakeChatModel(messages=iter(["response-1", "response-2", "response-3"]))
    agent = create_agent(
        model=model,
        tools=[],
        checkpointer=InMemorySaver(),
        context_schema=RunContext,
        middleware=[observe_input, observe_output],
    )
    return agent, observations


def run_lab() -> tuple[list[list[Any]], list[tuple[str, str, int]]]:
    agent, observations = build_lab()
    cases = [
        ("thread-a", "run-1"),
        ("thread-a", "run-2"),
        ("thread-b", "run-3"),
    ]
    snapshots: list[list[Any]] = []
    for thread_id, label in cases:
        state = agent.invoke(
            {"messages": [HumanMessage(content=f"message for {label}")]},
            config={"configurable": {"thread_id": thread_id}},
            context=RunContext(label=label),
        )
        snapshots.append(state["messages"])
    return snapshots, observations


if __name__ == "__main__":
    snapshots, events = run_lab()
    for index, messages in enumerate(snapshots, start=1):
        print(f"invoke-{index}: history_length={len(messages)}, last={messages[-1].content}")
    for phase, label, count in events:
        print(f"{phase}: context={label}, history_length={count}")
