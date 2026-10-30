from __future__ import annotations

import unittest
from contextlib import AbstractContextManager
from dataclasses import dataclass

from first_trace import record_support_turn


@dataclass
class FakeObservation:
    client: "FakeLangfuse"
    trace_id: str
    id: str
    name: str
    output: object | None = None

    def update(self, *, output: object) -> None:
        self.output = output


class ObservationContext(AbstractContextManager[FakeObservation]):
    def __init__(self, client: "FakeLangfuse", observation: FakeObservation) -> None:
        self.client = client
        self.observation = observation

    def __enter__(self) -> FakeObservation:
        self.client.stack.append(self.observation)
        return self.observation

    def __exit__(self, exc_type, exc, traceback) -> None:
        popped = self.client.stack.pop()
        assert popped is self.observation


class FakeLangfuse:
    def __init__(self) -> None:
        self.stack: list[FakeObservation] = []
        self.next_trace = 1
        self.next_observation = 1

    def start_as_current_observation(self, *, as_type: str, name: str, input: object):
        assert as_type == "span"
        del input

        if self.stack:
            trace_id = self.stack[-1].trace_id
        else:
            trace_id = f"trace-{self.next_trace}"
            self.next_trace += 1

        observation = FakeObservation(
            client=self,
            trace_id=trace_id,
            id=f"obs-{self.next_observation}",
            name=name,
        )
        self.next_observation += 1
        return ObservationContext(self, observation)

    def get_current_observation_id(self) -> str | None:
        if not self.stack:
            return None
        return self.stack[-1].id


class FirstTraceContractTest(unittest.TestCase):
    def test_nested_search_shares_trace_and_restores_root_context(self) -> None:
        evidence = record_support_turn(FakeLangfuse())

        self.assertEqual(evidence["root_trace_id"], evidence["search_trace_id"])
        self.assertEqual(
            evidence["current_after_search"], evidence["root_observation_id"]
        )

    def test_detached_search_starts_new_trace_and_leaves_no_current_context(self) -> None:
        evidence = record_support_turn(FakeLangfuse(), detach_search=True)

        self.assertNotEqual(evidence["root_trace_id"], evidence["search_trace_id"])
        self.assertIsNone(evidence["current_after_search"])


if __name__ == "__main__":
    unittest.main()
