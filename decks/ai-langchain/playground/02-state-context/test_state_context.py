"""Test state persistence, thread separation, and middleware observation order."""

import unittest

from langchain.messages import AIMessage, HumanMessage

from state_context import run_lab


class StateContextTests(unittest.TestCase):
    def test_same_thread_preserves_history_without_repeating_input(self) -> None:
        snapshots, _ = run_lab()
        self.assertEqual([len(messages) for messages in snapshots], [2, 4, 2])
        self.assertEqual(
            [type(message) for message in snapshots[1]],
            [HumanMessage, AIMessage, HumanMessage, AIMessage],
        )
        self.assertEqual(snapshots[1][0].content, "message for run-1")
        self.assertEqual(snapshots[1][-1].content, "response-2")

    def test_other_thread_does_not_inherit_history(self) -> None:
        snapshots, _ = run_lab()
        self.assertEqual(snapshots[2][0].content, "message for run-3")
        self.assertEqual(len(snapshots[2]), 2)

    def test_runtime_context_is_per_invocation(self) -> None:
        _, events = run_lab()
        self.assertEqual([event[1] for event in events], [
            "run-1", "run-1", "run-2", "run-2", "run-3", "run-3"
        ])

    def test_before_and_after_hooks_inspect_different_state(self) -> None:
        _, events = run_lab()
        self.assertEqual(events, [
            ("before", "run-1", 1),
            ("after", "run-1", 2),
            ("before", "run-2", 3),
            ("after", "run-2", 4),
            ("before", "run-3", 1),
            ("after", "run-3", 2),
        ])


if __name__ == "__main__":
    unittest.main()
