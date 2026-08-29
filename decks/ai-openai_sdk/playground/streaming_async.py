# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=3,<4",
# ]
# ///

from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any

DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_INPUT = "Explain in three short sentences why Python generators are lazy."
TERMINAL_EVENT_TYPES = {"response.completed", "response.failed", "response.incomplete"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Responses API streaming with synchronous and asynchronous clients."
    )
    parser.add_argument("--mode", choices=["sync", "async"], required=True)
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        help="Model ID. Defaults to OPENAI_MODEL or the deck calibration model.",
    )
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the control-flow plan without importing the SDK or calling the API.",
    )
    return parser.parse_args()


def preview(args: argparse.Namespace) -> None:
    iterator = "for event in stream" if args.mode == "sync" else "async for event in stream"
    create_call = (
        "client.responses.create(..., stream=True)"
        if args.mode == "sync"
        else "await client.responses.create(..., stream=True)"
    )
    print("== control-flow plan ==")
    print(
        json.dumps(
            {
                "mode": args.mode,
                "create": create_call,
                "consume": iterator,
                "important_events": [
                    "response.created",
                    "response.output_item.added",
                    "response.output_text.delta",
                    "response.output_text.done",
                    "response.completed / response.failed / response.incomplete",
                ],
                "application_state": "append text deltas for incremental display; keep terminal response separately",
                "async_difference": "await/async iteration changes Python scheduling, not the API response meaning",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def observe_event(event: Any, text_parts: list[str]) -> Any | None:
    event_type = event.type

    if event_type == "response.output_text.delta":
        text_parts.append(event.delta)
        print(event.delta, end="", flush=True)
        return None

    if event_type in {"response.created", "response.output_item.added", "response.output_text.done"}:
        print(f"\n[event] {event_type}")
        return None

    if event_type in TERMINAL_EVENT_TYPES:
        print(f"\n[event] {event_type}")
        return event.response

    return None


def print_terminal_response(response: Any | None, text_parts: list[str]) -> None:
    print("\n== application observations ==")
    print(f"accumulated_delta_text: {''.join(text_parts)}")

    if response is None:
        raise RuntimeError("Stream ended without a terminal response event")

    print(f"terminal_status: {response.status}")
    print(f"response_id: {response.id}")
    print(f"final_output_text: {response.output_text}")
    print(f"incomplete_details: {response.incomplete_details}")
    print(f"error: {response.error}")

    if response.status != "completed":
        raise RuntimeError(
            f"Streaming response ended as {response.status}: "
            f"{response.error or response.incomplete_details}"
        )


def run_sync(args: argparse.Namespace) -> None:
    from openai import OpenAI

    client = OpenAI()
    stream = client.responses.create(
        model=args.model,
        input=args.input,
        stream=True,
    )

    text_parts: list[str] = []
    terminal_response = None
    for event in stream:
        observed = observe_event(event, text_parts)
        if observed is not None:
            terminal_response = observed

    print_terminal_response(terminal_response, text_parts)


async def run_async(args: argparse.Namespace) -> None:
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    stream = await client.responses.create(
        model=args.model,
        input=args.input,
        stream=True,
    )

    text_parts: list[str] = []
    terminal_response = None
    async for event in stream:
        observed = observe_event(event, text_parts)
        if observed is not None:
            terminal_response = observed

    print_terminal_response(terminal_response, text_parts)


def main() -> None:
    args = parse_args()
    preview(args)

    if args.preview:
        print("\npreview only: no SSE stream or model response was created")
        return

    if args.mode == "sync":
        run_sync(args)
    else:
        asyncio.run(run_async(args))


if __name__ == "__main__":
    main()
