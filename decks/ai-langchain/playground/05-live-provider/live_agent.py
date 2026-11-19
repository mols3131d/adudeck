"""Opt-in live OpenAI agent lab. No provider request without --execute and a key."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from typing import Any

from langchain.agents import create_agent
from langchain.messages import AIMessage, ToolMessage
from langchain_core.messages import BaseMessage
from langchain.tools import tool


def require_live_permission(*, execute: bool, api_key: str | None) -> None:
    if not execute:
        raise SystemExit("No API call made. Pass --execute after reviewing provider costs.")
    if not api_key:
        raise SystemExit("No API call made. Set OPENAI_API_KEY outside the repository.")


def inspect_execution(messages: Sequence[BaseMessage]) -> tuple[int, int, str]:
    requests = [
        call["id"]
        for message in messages
        if isinstance(message, AIMessage)
        for call in message.tool_calls
    ]
    results = [
        message for message in messages if isinstance(message, ToolMessage)
    ]
    if not requests:
        raise RuntimeError("The model did not request a tool; compare the prompt/model.")
    if sorted(requests) != sorted(message.tool_call_id for message in results):
        raise RuntimeError("A tool result is missing or its tool_call_id does not match.")
    if any(message.status == "error" for message in results):
        raise RuntimeError("A tool failed; inspect the tool status before accepting a response.")
    last = messages[-1]
    if not isinstance(last, AIMessage) or last.tool_calls:
        raise RuntimeError("The agent did not finish with a final model answer.")
    return len(requests), len(results), str(last.content)


def live_run(model_name: str) -> dict[str, Any]:
    from langchain_openai import ChatOpenAI

    @tool
    def double(value: int) -> int:
        """Return twice an integer."""
        return value * 2

    agent = create_agent(
        model=ChatOpenAI(model=model_name),
        tools=[double],
        system_prompt="For arithmetic, use the provided tool instead of guessing the result.",
    )
    return agent.invoke(
        {"messages": [{"role": "user", "content": "Use double to compute twice 7."}]},
        config={"recursion_limit":8},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="A model available on your OpenAI account")
    parser.add_argument("--execute", action="store_true", help="Approve one paid provider run")
    args = parser.parse_args()

    require_live_permission(execute=args.execute, api_key=os.getenv("OPENAI_API_KEY"))
    state = live_run(args.model)
    requests, results, answer = inspect_execution(state["messages"])
    print(f"model_tool_requests={requests}")
    print(f"tool_results={results}")
    print(f"answer={answer!r}")


if __name__ == "__main__":
    main()
