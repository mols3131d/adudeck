"""통합 그래프의 승인, 검증, checkpoint, 실패 복구 확인."""

import unittest
from contextlib import redirect_stdout
from io import StringIO

from langgraph.types import Command

from textbook.integration.workflow import build_graph, initial_state, main


class IntegratedWorkflowTest(unittest.TestCase):
    def test_approved_odd_number_runs_apply_once(self):
        trace: list[str] = []
        graph = build_graph(trace)
        config = {"configurable": {"thread_id": "approve-3"}}
        paused = graph.invoke(initial_state(3), config=config)
        self.assertCountEqual(paused["__interrupt__"][0].value["checks"], ["odd", "range-ok"])
        snapshot = graph.get_state(config)
        self.assertEqual(snapshot.next, ("ask_approval",))
        self.assertCountEqual(snapshot.values["checks"], ["odd", "range-ok"])
        final = graph.invoke(Command(resume=True), config=config)
        self.assertEqual(final["number"], 4)
        self.assertEqual(final["outcome"], "applied")
        self.assertIs(final["approved"], True)
        self.assertEqual(trace.count("ask_approval"), 2)
        self.assertEqual(trace.count("apply"), 1)

    def test_rejection_routes_to_cancel_even_if_number_is_valid(self):
        trace: list[str] = []
        graph = build_graph(trace)
        config = {"configurable": {"thread_id": "reject-4"}}
        graph.invoke(initial_state(4), config=config)
        final = graph.invoke(Command(resume=False), config=config)
        self.assertEqual(final["number"], 4)
        self.assertEqual(final["outcome"], "cancelled")
        self.assertIs(final["approved"], False)
        self.assertEqual(trace.count("apply"), 0)
        self.assertEqual(trace.count("cancel"), 1)

    def test_range_violation_cancels_even_when_approved(self):
        trace: list[str] = []
        graph = build_graph(trace)
        config = {"configurable": {"thread_id": "invalid-21"}}
        graph.invoke(initial_state(21), config=config)
        final = graph.invoke(Command(resume=True), config=config)
        self.assertIn("range-invalid", final["checks"])
        self.assertEqual(final["number"], 21)
        self.assertEqual(final["outcome"], "cancelled")
        self.assertEqual(trace.count("apply"), 0)

    def test_failed_apply_resumes_at_failed_node(self):
        trace: list[str] = []
        graph = build_graph(trace, fail_first_apply=True)
        config = {"configurable": {"thread_id": "fail-once-3"}}
        graph.invoke(initial_state(3), config=config)
        with self.assertRaisesRegex(RuntimeError, "simulated apply failure"):
            graph.invoke(Command(resume=True), config=config)

        snapshot = graph.get_state(config)
        self.assertEqual(snapshot.next, ("apply",))
        self.assertIs(snapshot.values["approved"], True)
        final = graph.invoke(None, config=config)
        self.assertEqual(final["number"], 4)
        self.assertEqual(final["outcome"], "applied")
        self.assertEqual(trace.count("ask_approval"), 2)
        self.assertEqual(trace.count("apply"), 2)
        self.assertEqual(graph.get_state(config).next, ())

    def test_runnable_demo_exposes_failure_checkpoint_and_recovery(self):
        output = StringIO()
        with redirect_stdout(output):
            main()
        evidence = output.getvalue()
        self.assertIn("expected failure: simulated apply failure", evidence)
        self.assertIn("retry next: ('apply',)", evidence)
        self.assertIn("recovered:", evidence)
        self.assertIn("'outcome': 'applied'", evidence)
        self.assertIn("apply attempts: 2", evidence)
        self.assertIn("node visits after recovery:", evidence)


if __name__ == "__main__":
    unittest.main()
