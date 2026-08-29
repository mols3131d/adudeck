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
DEFAULT_INPUT = "Look up order A-102 and tell me its current status."

ORDERS = {
    "A-101": {"order_id": "A-101", "status": "processing", "eta": "2026-09-02"},
    "A-102": {"order_id": "A-102", "status": "shipped", "eta": "2026-08-31"},
    "A-103": {"order_id": "A-103", "status": "delivered", "eta": "2026-08-27"},
}

LOOKUP_ORDER_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "lookup_order",
    "description": "Look up one order in the application's local teaching dataset.",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "Order identifier such as A-102.",
            }
        },
        "required": ["order_id"],
        "additionalProperties": False,
    },
    "strict": True,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Observe the Responses API function-call loop and application-owned execution."
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        help="Model ID. Defaults to OPENAI_MODEL or the deck calibration model.",
    )
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the tool contract and control-flow plan without importing the SDK or calling the API.",
    )
    return parser.parse_args()


def lookup_order(order_id: str) -> dict[str, Any]:
    order = ORDERS.get(order_id)
    if order is None:
        return {"order_id": order_id, "found": False}
    return {**order, "found": True}


def dispatch_tool(name: str, arguments_json: str) -> dict[str, Any]:
    if name != "lookup_order":
        raise ValueError(f"Unexpected tool name: {name}")

    arguments = json.loads(arguments_json)
    if set(arguments) != {"order_id"} or not isinstance(arguments["order_id"], str):
        raise ValueError(f"Invalid lookup_order arguments: {arguments!r}")

    return lookup_order(arguments["order_id"])


def preview(args: argparse.Namespace) -> None:
    print("== tool schema ==")
    print(json.dumps(LOOKUP_ORDER_TOOL, ensure_ascii=False, indent=2))
    print("\n== application-owned execution plan ==")
    print(
        json.dumps(
            {
                "first_request": {
                    "model": args.model,
                    "input": args.input,
                    "tools": ["lookup_order"],
                    "tool_choice": {"type": "function", "name": "lookup_order"},
                },
                "model_can_return": "function_call(name, arguments, call_id)",
                "application_then": [
                    "validates the requested function name and JSON arguments",
                    "executes local Python code",
                    "serializes the local result",
                    "returns function_call_output with the same call_id",
                ],
                "final_request": "continues with previous_response_id and tool outputs",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    args = parse_args()
    preview(args)

    if args.preview:
        print("\npreview only: the model did not request a tool and no local tool function was executed")
        return

    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(
        model=args.model,
        input=args.input,
        tools=[LOOKUP_ORDER_TOOL],
        tool_choice={"type": "function", "name": "lookup_order"},
    )

    for round_number in range(1, 5):
        print(f"\n== response round {round_number} ==")
        print(f"status: {response.status}")
        print(f"response_id: {response.id}")
        print(f"request_id: {response._request_id}")
        print(f"output_types: {[item.type for item in response.output]}")

        if response.status != "completed":
            raise RuntimeError(
                f"Response ended as {response.status}: {response.error or response.incomplete_details}"
            )

        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            print(f"final_output_text: {response.output_text}")
            return

        tool_outputs: list[dict[str, str]] = []
        for call in calls:
            print("\n-- model-proposed call --")
            print(f"name: {call.name}")
            print(f"call_id: {call.call_id}")
            print(f"arguments_json: {call.arguments}")

            result = dispatch_tool(call.name, call.arguments)
            encoded_result = json.dumps(result, ensure_ascii=False)

            print("-- application execution --")
            print(f"result: {encoded_result}")

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": encoded_result,
                }
            )

        response = client.responses.create(
            model=args.model,
            previous_response_id=response.id,
            input=tool_outputs,
            tools=[LOOKUP_ORDER_TOOL],
        )

    raise RuntimeError("Tool loop exceeded the lab's four-round safety bound")


if __name__ == "__main__":
    main()
