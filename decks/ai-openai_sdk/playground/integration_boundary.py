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
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from pydantic import BaseModel

DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_TICKET = "Exporting a report returns a blank CSV for every workspace."


class TicketClassification(BaseModel):
    category: Literal["bug", "question", "request"]
    priority: Literal["low", "medium", "high"]
    summary: str


class ResponsesParser(Protocol):
    def parse(self, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    priority: str
    summary: str
    response_id: str
    request_id: str | None


class TicketClassifier:
    """Small application boundary around the SDK Responses parsing surface."""

    def __init__(self, responses: ResponsesParser, *, model: str) -> None:
        self._responses = responses
        self._model = model

    def classify(self, ticket: str) -> ClassificationResult:
        response = self._responses.parse(
            model=self._model,
            input=ticket,
            text_format=TicketClassification,
        )

        if response.status != "completed":
            details = response.error or response.incomplete_details
            raise RuntimeError(f"Response ended as {response.status}: {details}")

        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("Completed response did not contain a parsed classification")

        return ClassificationResult(
            category=parsed.category,
            priority=parsed.priority,
            summary=parsed.summary,
            response_id=response.id,
            request_id=getattr(response, "_request_id", None),
        )


class FakeResponse:
    def __init__(
        self,
        *,
        status: str = "completed",
        parsed: TicketClassification | None = None,
        error: Any = None,
        incomplete_details: Any = None,
    ) -> None:
        self.status = status
        self.output_parsed = parsed
        self.error = error
        self.incomplete_details = incomplete_details
        self.id = "resp_fake_001"
        self._request_id = "req_fake_001"


class RecordingResponses:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def parse(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return self.response


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Observe a small, fake-testable application boundary around OpenAI Responses."
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        help="Model ID. Defaults to OPENAI_MODEL or the deck calibration model.",
    )
    parser.add_argument("--ticket", default=DEFAULT_TICKET)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the boundary contract without importing the OpenAI SDK or calling the API.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run deterministic fake-backed assertions without any API call.",
    )
    return parser.parse_args()


def preview(args: argparse.Namespace) -> None:
    print("== application boundary ==")
    print(
        json.dumps(
            {
                "concrete_sdk_client_constructed_outside_adapter": True,
                "adapter_owns": [
                    "model configuration for this use case",
                    "TicketClassification output contract",
                    "completed + parsed-result invariant",
                    "mapping SDK response fields into an application result",
                ],
                "adapter_does_not_own": [
                    "API key value",
                    "SDK transport/retry implementation",
                    "swallowing SDK exceptions",
                ],
                "test_seam": "inject responses.parse-compatible object and record call arguments",
                "live_model": args.model,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def run_self_test(model: str) -> None:
    parsed = TicketClassification(
        category="bug",
        priority="high",
        summary="CSV export is blank across workspaces.",
    )
    fake = RecordingResponses(FakeResponse(parsed=parsed))
    classifier = TicketClassifier(fake, model=model)

    result = classifier.classify("blank CSV")

    assert result.category == "bug"
    assert result.priority == "high"
    assert result.response_id == "resp_fake_001"
    assert result.request_id == "req_fake_001"
    assert len(fake.calls) == 1
    assert fake.calls[0]["model"] == model
    assert fake.calls[0]["input"] == "blank CSV"
    assert fake.calls[0]["text_format"] is TicketClassification

    incomplete = RecordingResponses(
        FakeResponse(status="incomplete", incomplete_details={"reason": "max_output_tokens"})
    )
    incomplete_classifier = TicketClassifier(incomplete, model=model)
    try:
        incomplete_classifier.classify("incomplete case")
    except RuntimeError as exc:
        assert "incomplete" in str(exc)
    else:
        raise AssertionError("Expected incomplete fake response to fail the application invariant")

    print("self-test: passed")
    print(f"recorded_call: {fake.calls[0]}")
    print(f"application_result: {result}")


def run_live(args: argparse.Namespace) -> None:
    from openai import OpenAI

    client = OpenAI()
    classifier = TicketClassifier(client.responses, model=args.model)
    result = classifier.classify(args.ticket)
    print("== application result ==")
    print(result)


def main() -> None:
    args = parse_args()
    preview(args)

    if args.self_test:
        run_self_test(args.model)
        return

    if args.preview:
        print("\npreview only: no SDK import or API call occurred")
        return

    run_live(args)


if __name__ == "__main__":
    main()
