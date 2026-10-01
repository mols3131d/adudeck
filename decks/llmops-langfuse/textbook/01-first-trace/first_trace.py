from __future__ import annotations

import argparse
import os


def search_policy(langfuse, query: str) -> dict[str, str]:
    with langfuse.start_as_current_observation(
        as_type="span",
        name="search-policy",
        input={"query": query},
    ) as search:
        document = "구매 후 14일 이내 환불 가능"
        search.update(output={"document": document})

        return {
            "trace_id": search.trace_id,
            "observation_id": search.id,
            "document": document,
        }


def record_support_turn(langfuse, *, detach_search: bool = False) -> dict[str, str | None]:
    with langfuse.start_as_current_observation(
        as_type="span",
        name="support-turn",
        input={"question": "환불 기간은?"},
    ) as root:
        root_trace_id = root.trace_id
        root_observation_id = root.id

        if not detach_search:
            search = search_policy(langfuse, "환불 기간")
            current_after_search = langfuse.get_current_observation_id()
        else:
            search = None
            current_after_search = None

        root.update(output={"answer": "14일"})

    if detach_search:
        search = search_policy(langfuse, "환불 기간")
        current_after_search = langfuse.get_current_observation_id()

    assert search is not None

    return {
        "root_trace_id": root_trace_id,
        "root_observation_id": root_observation_id,
        "search_trace_id": search["trace_id"],
        "search_observation_id": search["observation_id"],
        "current_after_search": current_after_search,
    }


def print_evidence(evidence: dict[str, str | None]) -> None:
    for key, value in evidence.items():
        print(f"{key}={value}")

    same_trace = evidence["root_trace_id"] == evidence["search_trace_id"]
    print(f"same_trace={str(same_trace).lower()}")


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
        description="Create a Langfuse trace and compare nested vs detached observations."
    )
    parser.add_argument(
        "--detach-search",
        action="store_true",
        help="Run search-policy after the root observation closes, creating a separate trace.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    require_langfuse_credentials()

    from langfuse import get_client

    langfuse = get_client()
    evidence = record_support_turn(langfuse, detach_search=args.detach_search)
    print_evidence(evidence)
    langfuse.flush()


if __name__ == "__main__":
    main()
