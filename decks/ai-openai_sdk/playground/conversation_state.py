# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=3,<4",
# ]
# ///

from __future__ import annotations

import argparse
import json
import os
from typing import Any

DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_FIRST = "Remember that my project codename is Juniper. Reply with the codename only."
DEFAULT_FOLLOWUP = "What project codename did I give you? Reply with the codename only."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare three Responses API conversation-state ownership patterns."
    )
    parser.add_argument(
        "--mode",
        choices=["manual", "lineage", "conversation"],
        required=True,
        help="State ownership pattern to observe.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        help="Model ID. Defaults to OPENAI_MODEL or the deck calibration default.",
    )
    parser.add_argument("--first", default=DEFAULT_FIRST)
    parser.add_argument("--followup", default=DEFAULT_FOLLOWUP)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the application-side call plan without importing the SDK or calling the API.",
    )
    return parser.parse_args()


def preview_plan(args: argparse.Namespace) -> dict[str, Any]:
    if args.mode == "manual":
        return {
            "mode": "manual",
            "state_owner": "application",
            "first_call": {
                "model": args.model,
                "input": [{"role": "user", "content": args.first}],
                "store": False,
            },
            "between_calls": [
                "application keeps response.output items",
                "application appends the next user input",
                "application sends the reconstructed history again",
            ],
            "second_call": {
                "model": args.model,
                "input": "<application-owned history + followup>",
                "store": False,
            },
        }

    if args.mode == "lineage":
        return {
            "mode": "lineage",
            "state_owner": "response lineage resolved by the API",
            "first_call": {"model": args.model, "input": args.first},
            "between_calls": ["application keeps first response.id"],
            "second_call": {
                "model": args.model,
                "previous_response_id": "<first response.id>",
                "input": args.followup,
            },
        }

    return {
        "mode": "conversation",
        "state_owner": "durable Conversation object",
        "setup": "create one conversation and keep conversation.id",
        "first_call": {
            "model": args.model,
            "conversation": "<conversation.id>",
            "input": args.first,
        },
        "second_call": {
            "model": args.model,
            "conversation": "<same conversation.id>",
            "input": args.followup,
        },
    }


def print_response(label: str, response: Any) -> None:
    print(f"\n== {label} ==")
    print(f"response_id: {response.id}")
    print(f"request_id: {response._request_id}")
    print(f"output_types: {[item.type for item in response.output]}")
    print(f"output_text: {response.output_text}")


def run_manual(client: Any, args: argparse.Namespace) -> None:
    history: list[Any] = [{"role": "user", "content": args.first}]

    first = client.responses.create(model=args.model, input=history, store=False)
    print_response("first response", first)

    # Keep every output item, not only output_text. Response output can contain
    # non-message items that are part of the next turn's context.
    history += first.output
    history.append({"role": "user", "content": args.followup})

    print("\n== application-owned history before second call ==")
    print(f"items: {len(history)}")
    print(f"item_types: {[getattr(item, 'type', 'message-dict') for item in history]}")

    second = client.responses.create(model=args.model, input=history, store=False)
    print_response("second response", second)


def run_lineage(client: Any, args: argparse.Namespace) -> None:
    first = client.responses.create(model=args.model, input=args.first)
    print_response("first response", first)

    print("\n== application state before second call ==")
    print(f"previous_response_id: {first.id}")

    second = client.responses.create(
        model=args.model,
        previous_response_id=first.id,
        input=args.followup,
    )
    print_response("second response", second)


def run_conversation(client: Any, args: argparse.Namespace) -> None:
    conversation = client.conversations.create()
    print("== durable conversation ==")
    print(f"conversation_id: {conversation.id}")

    first = client.responses.create(
        model=args.model,
        conversation=conversation.id,
        input=args.first,
    )
    print_response("first response", first)

    second = client.responses.create(
        model=args.model,
        conversation=conversation.id,
        input=args.followup,
    )
    print_response("second response", second)


def main() -> None:
    args = parse_args()

    print("== application call plan ==")
    print(json.dumps(preview_plan(args), ensure_ascii=False, indent=2))

    if args.preview:
        print("\npreview only: no SDK import, HTTP request, response lineage, or Conversation object was created")
        return

    from openai import OpenAI

    client = OpenAI()

    if args.mode == "manual":
        run_manual(client, args)
    elif args.mode == "lineage":
        run_lineage(client, args)
    else:
        run_conversation(client, args)


if __name__ == "__main__":
    main()
