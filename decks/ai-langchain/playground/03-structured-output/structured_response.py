"""Inspect structured output success, validation feedback, and explicit no-retry policy."""

from __future__ import annotations

import argparse
from typing import Any

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.messages import AIMessage, HumanMessage, ToolCall, ToolMessage
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from pydantic import BaseModel, Field


class Rating(BaseModel):
    """A product score and short reason."""

    score: int = Field(ge=1, le=5)
    reason: str = Field(min_length=1)


class ScriptedStructuredModel(GenericFakeChatModel):
    """The scripted model does not need provider-side bind_tools."""

    def bind_tools(self, tools: Any, **kwargs: Any) -> ScriptedStructuredModel:
        return self


def scripted_rating(score: int, *, call_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name="Rating",
                args={"score": score, "reason": "Documented evidence"},
                id=call_id,
            )
        ],
    )


def build_agent(scenario: str) -> Any:
    if scenario == "valid":
        outputs = [scripted_rating(4, call_id="rating_ok")]
        retry = False
    elif scenario == "repair":
        outputs = [
            scripted_rating(9, call_id="rating_invalid"),
            scripted_rating(4, call_id="rating_repaired"),
        ]
        retry = True
    elif scenario == "reject":
        outputs = [scripted_rating(9, call_id="rating_rejected")]
        retry = False
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    return create_agent(
        model=ScriptedStructuredModel(messages=iter(outputs)),
        tools=[],
        response_format=ToolStrategy(Rating, handle_errors=retry),
    )


def run_scenario(scenario: str) -> dict[str, Any]:
    agent = build_agent(scenario)
    return agent.invoke(
        {"messages": [HumanMessage(content="Score the example from 1 to 5.")]}
    )


def print_state(state: dict[str, Any]) -> None:
    for message in state["messages"]:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                print(f"request: {call['id']}, score={call['args']['score']}")
        elif isinstance(message, ToolMessage):
            print(f"feedback: {message.tool_call_id}, {message.content}")
    print(f"structured_response={state.get('structured_response')!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario", choices=("valid", "repair", "reject"), default="valid"
    )
    args = parser.parse_args()

    if args.scenario == "reject":
        from langchain.agents.structured_output import StructuredOutputValidationError

        try:
            run_scenario("reject")
        except StructuredOutputValidationError as exc:
            print(f"rejected={type(exc).__name__}")
        else:
            raise AssertionError("Expected schema validation to reject score 9")
        return
    print_state(run_scenario(args.scenario))


if __name__ == "__main__":
    main()
