from __future__ import annotations

import argparse
import os
from typing import Any


PROMPT_NAME = "support/refund-answer"


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


def prompt_lookup_kwargs(
    *,
    label: str | None,
    version: int | None,
) -> dict[str, Any]:
    if label is not None and version is not None:
        raise ValueError("choose a prompt label or an exact version, not both")
    if version is not None:
        return {"type": "chat", "version": version}
    return {"type": "chat", "label": label or "production"}


def fetch_prompt(
    langfuse: Any,
    *,
    label: str | None = None,
    version: int | None = None,
) -> Any:
    return langfuse.get_prompt(
        PROMPT_NAME,
        **prompt_lookup_kwargs(label=label, version=version),
    )


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
        description=(
            "Fetch a Langfuse prompt by movable label or immutable version and link "
            "the resolved prompt object to a generation."
        )
    )
    selector = parser.add_mutually_exclusive_group()
    selector.add_argument(
        "--label",
        help=(
            "Prompt label to fetch. If neither selector is provided, production is used. "
            "Missing labels fail instead of silently falling back."
        ),
    )
    selector.add_argument(
        "--version",
        type=int,
        help="Exact immutable prompt version to fetch for reproducible historical runs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = require_live_environment()

    from langfuse import get_client
    from langfuse.openai import OpenAI

    langfuse = get_client()
    openai_client = OpenAI()

    prompt = fetch_prompt(
        langfuse,
        label=args.label,
        version=args.version,
    )
    evidence = generate_with_prompt(
        openai_client,
        prompt,
        model=model,
        policy_days=14,
        question="환불 기간은?",
    )

    selection = (
        f"version={args.version}"
        if args.version is not None
        else f"label={args.label or 'production'}"
    )
    print(f"prompt_selection={selection}")
    for key, value in evidence.items():
        print(f"{key}={value}")

    langfuse.flush()


if __name__ == "__main__":
    main()
