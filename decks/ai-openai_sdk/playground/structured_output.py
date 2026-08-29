# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=3,<4",
#   "pydantic>=2,<3",
# ]
# ///

from __future__ import annotations

import argparse
import json
import os
from typing import Literal

from pydantic import BaseModel, Field

DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_INPUT = (
    "The checkout button freezes after I submit my card. "
    "Classify this support ticket and summarize it."
)


class TicketClassification(BaseModel):
    category: Literal["bug", "question", "request"] = Field(
        description="The primary support-ticket category."
    )
    priority: Literal["low", "medium", "high"] = Field(
        description="The urgency implied by the ticket."
    )
    summary: str = Field(description="A concise factual summary of the ticket.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Observe Responses API structured-output parsing with a Pydantic schema."
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
        help="Print the local schema/call plan without importing the OpenAI SDK or calling the API.",
    )
    return parser.parse_args()


def preview(args: argparse.Namespace) -> None:
    print("== application-owned schema ==")
    print(json.dumps(TicketClassification.model_json_schema(), ensure_ascii=False, indent=2))
    print("\n== call plan ==")
    print(
        json.dumps(
            {
                "model": args.model,
                "input": args.input,
                "text_format": "TicketClassification",
                "expected_application_checks": [
                    "response.status",
                    "response.incomplete_details or response.error when non-completed",
                    "message content type: output_text vs refusal",
                    "parsed TicketClassification object",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    args = parse_args()
    preview(args)

    if args.preview:
        print("\npreview only: no SDK import, HTTP request, or server-side schema enforcement occurred")
        return

    from openai import OpenAI

    client = OpenAI()
    response = client.responses.parse(
        model=args.model,
        input=args.input,
        text_format=TicketClassification,
    )

    print("\n== response boundary ==")
    print(f"status: {response.status}")
    print(f"response_id: {response.id}")
    print(f"request_id: {response._request_id}")
    print(f"incomplete_details: {response.incomplete_details}")
    print(f"error: {response.error}")

    print("\n== output content ==")
    for output in response.output:
        print(f"output_type: {output.type}")
        if output.type != "message":
            continue
        for content in output.content:
            print(f"content_type: {content.type}")
            if content.type == "refusal":
                print(f"refusal: {content.refusal}")
            elif content.type == "output_text":
                print(f"text: {content.text}")
                print(f"parsed: {content.parsed}")

    print("\n== convenience parsed view ==")
    print(f"output_parsed: {response.output_parsed}")

    if response.status != "completed":
        raise RuntimeError(
            f"Response did not complete: {response.error or response.incomplete_details}"
        )
    if response.output_parsed is None:
        raise RuntimeError("Response completed without a parsed TicketClassification result")


if __name__ == "__main__":
    main()
