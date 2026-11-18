from __future__ import annotations

import argparse
import os


APP_REVISION = "abc123"
ROUTE = "/support"
TAGS = ["support", "web"]


def operation_name(base: str, *, user_id: str, unstable_names: bool) -> str:
    if unstable_names:
        return f"{base}-{user_id}"
    return base


def record_trace_design(
    langfuse,
    propagate_attributes,
    *,
    user_id: str,
    session_id: str,
    unstable_names: bool = False,
) -> dict[str, object]:
    root_name = operation_name(
        "support-turn", user_id=user_id, unstable_names=unstable_names
    )
    search_name = operation_name(
        "search-policy", user_id=user_id, unstable_names=unstable_names
    )

    with langfuse.start_as_current_observation(
        as_type="span",
        name=root_name,
        input={"question": "환불 기간은?"},
    ) as root:
        with propagate_attributes(
            user_id=user_id,
            session_id=session_id,
            tags=TAGS,
            metadata={
                "app_revision": APP_REVISION,
                "route": ROUTE,
            },
        ):
            with langfuse.start_as_current_observation(
                as_type="span",
                name=search_name,
                input={"query": "환불 기간"},
            ) as search:
                document = "구매 후 14일 이내 환불 가능"
                search.update(output={"document": document})

            root.update(output={"answer": "14일"})

    return {
        "root_name": root_name,
        "search_name": search_name,
        "trace_id": root.trace_id,
        "root_observation_id": root.id,
        "search_observation_id": search.id,
        "user_id": user_id,
        "session_id": session_id,
        "tags": TAGS,
        "metadata": {
            "app_revision": APP_REVISION,
            "route": ROUTE,
        },
    }


def print_evidence(evidence: dict[str, object]) -> None:
    for key, value in evidence.items():
        print(f"{key}={value}")


def require_langfuse_credentials() -> None:
    required = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        names = ", ".join(missing)
        raise SystemExit(
            f"Missing Langfuse credentials: {names}. "
            "Set them in your shell before running the live trace."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare stable observation names with names polluted by run-specific values."
    )
    parser.add_argument("--user-id", default="user-18472")
    parser.add_argument("--session-id", default="session-refund-1")
    parser.add_argument(
        "--unstable-names",
        action="store_true",
        help="Append user_id to observation names to demonstrate query fragmentation.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    require_langfuse_credentials()

    from langfuse import get_client, propagate_attributes

    langfuse = get_client()
    evidence = record_trace_design(
        langfuse,
        propagate_attributes,
        user_id=args.user_id,
        session_id=args.session_id,
        unstable_names=args.unstable_names,
    )
    print_evidence(evidence)
    langfuse.flush()


if __name__ == "__main__":
    main()
