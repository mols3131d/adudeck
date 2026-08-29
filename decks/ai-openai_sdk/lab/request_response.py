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
DEFAULT_INSTRUCTIONS = (
    "Explain the answer in at most three concise bullet points. "
    "Prefer concrete Python terminology."
)
DEFAULT_PROMPT = "What is the difference between a Python list and tuple?"


def build_request(model: str, instructions: str, prompt: str) -> dict[str, Any]:
    """Build the public call arguments used by the calibration experiment."""
    return {
        "model": model,
        "instructions": instructions,
        "input": prompt,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Observe one OpenAI Responses API call and its typed response."
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        help="Model ID. Defaults to OPENAI_MODEL or the deck calibration default.",
    )
    parser.add_argument("--instructions", default=DEFAULT_INSTRUCTIONS)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument(
        "--preview",
        action="store_true",
        help=(
            "Print local responses.create() arguments and exit without importing "
            "the SDK or calling the API."
        ),
    )
    parser.add_argument(
        "--full-response",
        action="store_true",
        help="Also print response.to_dict() so the full typed response can be inspected.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    request = build_request(args.model, args.instructions, args.prompt)

    print("== application call arguments ==")
    print(json.dumps(request, ensure_ascii=False, indent=2))

    if args.preview:
        print("\npreview only: the SDK did not serialize or send an HTTP request")
        return

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is not set. Export it in the shell or rerun with --preview."
        )

    # Keep the import behind the preview boundary so application-owned call
    # arguments can be inspected with plain Python before installing the SDK.
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(**request)

    print("\n== selected response fields ==")
    print(f"response_id: {response.id}")
    print(f"request_id: {response._request_id}")
    print(f"model: {response.model}")
    print(f"output_types: {[item.type for item in response.output]}")
    print(f"output_text: {response.output_text}")

    usage = response.usage.to_dict() if response.usage is not None else None
    print("usage:")
    print(json.dumps(usage, ensure_ascii=False, indent=2))

    if args.full_response:
        print("\n== full typed response as dict ==")
        print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
