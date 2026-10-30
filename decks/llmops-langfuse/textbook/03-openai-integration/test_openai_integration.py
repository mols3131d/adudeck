from __future__ import annotations

import unittest
from contextlib import AbstractContextManager
from dataclasses import dataclass
from types import SimpleNamespace

from openai_integration import record_support_turn


@dataclass
class FakeObservation:
    trace_id: str = "trace-1"
    id: str = "obs-root"
    output: object | None = None

    def update(self, *, output: object) -> None:
        self.output = output


class ObservationContext(AbstractContextManager[FakeObservation]):
    def __init__(self, observation: FakeObservation) -> None:
        self.observation = observation

    def __enter__(self) -> FakeObservation:
        return self.observation

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


class FakeLangfuse:
    def __init__(self) -> None:
        self.root = FakeObservation()
        self.start_calls: list[dict[str, object]] = []

    def start_as_current_observation(self, **kwargs):
        self.start_calls.append(kwargs)
        return ObservationContext(self.root)


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="구매 후 14일 이내입니다.")


class FakeOpenAI:
    def __init__(self) -> None:
        self.responses = FakeResponses()


class OpenAIIntegrationContractTest(unittest.TestCase):
    def test_application_span_wraps_provider_call_without_reimplementing_generation(self) -> None:
        langfuse = FakeLangfuse()
        openai_client = FakeOpenAI()

        evidence = record_support_turn(
            langfuse,
            openai_client,
            model="test-model",
            question="환불 기간은?",
        )

        self.assertEqual(
            langfuse.start_calls,
            [
                {
                    "as_type": "span",
                    "name": "support-turn",
                    "input": {"question": "환불 기간은?"},
                }
            ],
        )
        self.assertEqual(
            openai_client.responses.calls,
            [
                {
                    "name": "answer-generation",
                    "model": "test-model",
                    "input": [{"role": "user", "content": "환불 기간은?"}],
                }
            ],
        )
        self.assertEqual(
            langfuse.root.output,
            {"answer": "구매 후 14일 이내입니다."},
        )
        self.assertEqual(evidence["trace_id"], "trace-1")
        self.assertEqual(evidence["root_observation_id"], "obs-root")

    def test_model_is_injected_instead_of_hard_coded(self) -> None:
        langfuse = FakeLangfuse()
        openai_client = FakeOpenAI()

        record_support_turn(langfuse, openai_client, model="candidate-model")

        self.assertEqual(
            openai_client.responses.calls[0]["model"],
            "candidate-model",
        )


if __name__ == "__main__":
    unittest.main()
