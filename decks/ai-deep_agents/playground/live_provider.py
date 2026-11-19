"""Optional provider-backed execution of the Deep Agents comparison lesson.

This module never calls a remote model on import. API calls require
both an explicit CLI flag and an OPENAI_API_KEY in the environment.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import StateBackend
from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.language_models import BaseChatModel

from first_loop import QUESTION, lookup_fixture


SYSTEM_PROMPT = (
    "Compare only the two fictional services alpha and beta. "
    "Use lookup_fixture to retrieve each service's numbers. "
    "Explain the p95 latency and error-rate differences, and cite tool results. "
    "Do not use files, shells or subagents for this small task."
)


def build_agent(case: str, model: BaseChatModel):
    """Build the SAME graph configuration used for scripted case comparisons."""
    if case == "basic":
        return create_agent(model=model, tools=[lookup_fixture], system_prompt=SYSTEM_PROMPT)
    if case not in ("deep", "planned"):
        raise ValueError(f"Unknown comparison case: {case}")
    return create_deep_agent(
        model=model,
        tools=[lookup_fixture],
        system_prompt=SYSTEM_PROMPT,
        backend=StateBackend(),
        middleware=[TodoListMiddleware()] if case == "planned" else [],
        permissions=[
            FilesystemPermission(operations=["write"], paths=["/**"], mode="deny")
        ],
    )


def run_agent(case: str, model: BaseChatModel) -> dict[str, Any]:
    """Return observed calls and results rather than assuming model behavior."""
    result = build_agent(case, model).invoke(
        {"messages": [{"role": "user", "content": QUESTION}]},
        config={"recursion_limit": 12},
    )
    messages = result["messages"]
    return {
        "case": case,
        "requested_tools": [
            call["name"]
            for message in messages if isinstance(message, AIMessage)
            for call in message.tool_calls
        ],
        "executed_tools": [
            {"name": message.name, "status": message.status, "content": str(message.content)}
            for message in messages if isinstance(message, ToolMessage)
        ],
        "todos": result.get("todos"),
        "files": sorted((result.get("files") or {}).keys()),
        "last_assistant_message": str(messages[-1].content),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("basic", "deep", "planned"), default="basic")
    parser.add_argument("--model", required=True, help="An OpenAI tool-calling model available to your API account.")
    parser.add_argument(
        "--run-paid-api", action="store_true",
        help="Explicitly allow real OpenAI API calls and associated charges."
    )
    args = parser.parse_args()
    if not args.run_paid_api:
        parser.error("Provide --run-paid-api to permit billable model requests.")
    if not os.environ.get("OPENAI_API_KEY"):
        parser.error("OPENAI_API_KEY is not set; no remote request was started.")

    from langchain_openai import ChatOpenAI

    # No synthetic tool writes to the host. The model request is the only external call.
    model = ChatOpenAI(model=args.model, max_retries=0)
    print(json.dumps(run_agent(args.case, model), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
