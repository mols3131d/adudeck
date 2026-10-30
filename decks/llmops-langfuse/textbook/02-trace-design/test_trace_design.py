from __future__ import annotations

import unittest
from contextlib import AbstractContextManager
from dataclasses import dataclass

from trace_design import record_trace_design


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
        self.client.observations.append(self.observation)
        return self.observation

    def __exit__(self, exc_type, exc, traceback) -> None:
        popped = self.client.stack.pop()
        assert popped is self.observation


class FakeLangfuse:
    def __init__(self) -> None:
        self.stack: list[FakeObservation] = []
        self.observations: list[FakeObservation] = []
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


class PropagationContext(AbstractContextManager[None]):
    def __init__(
        self, recorder: "PropagationRecorder", attributes: dict[str, object]
    ) -> None:
        self.recorder = recorder
        self.attributes = attributes

    def __enter__(self) -> None:
        self.recorder.calls.append(self.attributes)
        return None

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


class PropagationRecorder:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(self, **attributes: object) -> PropagationContext:
        return PropagationContext(self, attributes)


class TraceDesignContractTest(unittest.TestCase):
    def test_stable_names_keep_run_specific_values_out_of_operation_names(self) -> None:
        client = FakeLangfuse()
        propagation = PropagationRecorder()

        evidence = record_trace_design(
            client,
            propagation,
            user_id="user-18472",
            session_id="session-refund-1",
        )

        self.assertEqual(evidence["root_name"], "support-turn")
        self.assertEqual(evidence["search_name"], "search-policy")
        self.assertNotIn("user-18472", str(evidence["root_name"]))
        self.assertEqual(client.observations[0].trace_id, client.observations[1].trace_id)
        self.assertEqual(len(propagation.calls), 1)
        self.assertEqual(propagation.calls[0]["user_id"], "user-18472")
        self.assertEqual(propagation.calls[0]["session_id"], "session-refund-1")
        self.assertEqual(propagation.calls[0]["tags"], ["support", "web"])
        self.assertEqual(
            propagation.calls[0]["metadata"],
            {"app_revision": "abc123", "route": "/support"},
        )

    def test_stable_names_group_different_users_under_same_operations(self) -> None:
        first = record_trace_design(
            FakeLangfuse(),
            PropagationRecorder(),
            user_id="user-18472",
            session_id="session-refund-1",
        )
        second = record_trace_design(
            FakeLangfuse(),
            PropagationRecorder(),
            user_id="user-88420",
            session_id="session-refund-2",
        )

        self.assertEqual(first["root_name"], second["root_name"])
        self.assertEqual(first["search_name"], second["search_name"])
        self.assertNotEqual(first["user_id"], second["user_id"])
        self.assertNotEqual(first["session_id"], second["session_id"])

    def test_unstable_names_change_grouping_but_not_correlation_attributes(self) -> None:
        client = FakeLangfuse()
        propagation = PropagationRecorder()

        evidence = record_trace_design(
            client,
            propagation,
            user_id="user-18472",
            session_id="session-refund-1",
            unstable_names=True,
        )

        self.assertEqual(evidence["root_name"], "support-turn-user-18472")
        self.assertEqual(evidence["search_name"], "search-policy-user-18472")
        self.assertEqual(propagation.calls[0]["user_id"], "user-18472")
        self.assertEqual(propagation.calls[0]["session_id"], "session-refund-1")


if __name__ == "__main__":
    unittest.main()
