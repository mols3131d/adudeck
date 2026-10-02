from __future__ import annotations

import argparse
import os
from typing import Any


def generate_with_prompt(
    openai_client: Any,
    prompt: Any,
    *,
    model: str,
    policy_days: int,
    question: str,
) -> dict[str, Any]:
    compiled = prompt.compile(
        policy_days=policy_days,
        question=question,
    )

    response = openai_client.responses.create(
        name="answer-generation",
        model=model,
        input=compiled,
        langfuse_prompt=prompt,
    )

    return {
        "answer": response.output_text,
        "prompt_name": prompt.name,
        "prompt_version": prompt.version,
        "prompt_labels": tuple(prompt.labels),
    }


def require_live_environment() -> str:
    required = (
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise SystemExit(
            "Missing live credentials/config: "
            + ", ".join(missing)
            + ". Set them in your shell; never commit them."
        )
    return os.environ["OPENAI_MODEL"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a Langfuse prompt by label and link the exact version to a generation."
    )
    parser.add_argument(
        "--label",
        default="production",
        help="Prompt label to fetch. Missing labels fail instead of silently falling back.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = require_live_environment()

    from langfuse import get_client
    from langfuse.openai import OpenAI

    langfuse = get_client()
    openai_client = OpenAI()

    prompt = langfuse.get_prompt(
        "support/refund-answer",
        type="chat",
        label=args.label,
    )
    evidence = generate_with_prompt(
        openai_client,
        prompt,
        model=model,
        policy_days=14,
        question="환불 기간은?",
    )

    for key, value in evidence.items():
        print(f"{key}={value}")

    langfuse.flush()


if __name__ == "__main__":
    main()
