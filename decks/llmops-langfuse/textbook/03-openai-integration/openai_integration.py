from __future__ import annotations

import os
from typing import Any


def record_support_turn(
    langfuse: Any,
    openai_client: Any,
    *,
    model: str,
    question: str = "환불 기간은?",
) -> dict[str, str]:
    """Record application context while letting the OpenAI integration own the generation."""
    with langfuse.start_as_current_observation(
        as_type="span",
        name="support-turn",
        input={"question": question},
    ) as root:
        response = openai_client.responses.create(
            name="answer-generation",
            model=model,
            input=[{"role": "user", "content": question}],
        )
        answer = response.output_text
        root.update(output={"answer": answer})

        return {
            "trace_id": root.trace_id,
            "root_observation_id": root.id,
            "answer": answer,
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


def main() -> None:
    model = require_live_environment()

    from langfuse import get_client
    from langfuse.openai import OpenAI

    langfuse = get_client()
    openai_client = OpenAI()

    evidence = record_support_turn(
        langfuse,
        openai_client,
        model=model,
    )
    for key, value in evidence.items():
        print(f"{key}={value}")

    langfuse.flush()


if __name__ == "__main__":
    main()
