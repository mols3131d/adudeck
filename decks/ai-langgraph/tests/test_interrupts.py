"""interrupt pause/resume와 node 재실행 경계를 검증한다."""

import unittest

from langgraph.types import Command

from textbook.interrupts.approval import build_graph


class InterruptsTest(unittest.TestCase):
    def test_resume_restarts_only_interrupted_node(self):
        trace: list[str] = []
        graph = build_graph(trace)
        config = {"configurable": {"thread_id": "approve"}}
        initial = {"number": 2, "approved": None, "finished": False}

        paused = graph.invoke(initial, config=config)
        self.assertIn("__interrupt__", paused)
        self.assertEqual(paused["__interrupt__"][0].value["number"], 3)
        self.assertEqual(trace, ["prepare", "request_approval"])
        snapshot = graph.get_state(config)
        self.assertEqual(snapshot.values["number"], 3)
        self.assertIsNone(snapshot.values["approved"])
        self.assertEqual(snapshot.next, ("request_approval",))

        final = graph.invoke(Command(resume=True), config=config)
        self.assertEqual(
            final, {"number": 3, "approved": True, "finished": True}
        )
        self.assertEqual(
            trace,
            ["prepare", "request_approval", "request_approval", "finish"],
        )
        self.assertEqual(graph.get_state(config).next, ())

    def test_rejection_finishes_without_approval(self):
        trace: list[str] = []
        graph = build_graph(trace)
        config = {"configurable": {"thread_id": "reject"}}
        graph.invoke({"number": 2, "approved": None, "finished": False}, config=config)
        final = graph.invoke(Command(resume=False), config=config)
        self.assertEqual(final["number"], 3)
        self.assertIs(final["approved"], False)
        self.assertIs(final["finished"], False)
        self.assertEqual(trace.count("request_approval"), 2)
        self.assertEqual(trace.count("prepare"), 1)


if __name__ == "__main__":
    unittest.main()
