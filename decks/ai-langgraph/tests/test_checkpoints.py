"""thread 상태의 격리와 새 입력에 의한 state 갱신 확인."""

import unittest

from textbook.checkpoints.checkpoints import build_graph


class CheckpointsTest(unittest.TestCase):
    def test_new_input_in_same_thread_uses_saved_state(self):
        graph = build_graph()
        config = {"configurable": {"thread_id": "thread-a"}}
        self.assertEqual(
            graph.invoke({"total": 10, "delta": 2}, config=config),
            {"total": 12, "delta": 2},
        )
        first = graph.get_state(config)
        self.assertEqual(first.values["total"], 12)
        self.assertEqual(first.next, ())
        self.assertEqual(
            graph.invoke({"delta": 5}, config=config),
            {"total": 17, "delta": 5},
        )
        self.assertEqual(graph.get_state(config).values["total"], 17)
        snapshots = list(graph.get_state_history(config))
        self.assertEqual(snapshots[0].values["total"], 17)
        self.assertTrue(any(s.values.get("total") == 12 for s in snapshots))

    def test_different_threads_are_isolated(self):
        graph = build_graph()
        first = {"configurable": {"thread_id": "thread-a"}}
        second = {"configurable": {"thread_id": "thread-b"}}
        graph.invoke({"total": 10, "delta": 2}, config=first)
        self.assertEqual(
            graph.invoke({"total": 1, "delta": 2}, config=second),
            {"total": 3, "delta": 2},
        )
        self.assertEqual(graph.get_state(first).values["total"], 12)
        self.assertEqual(graph.get_state(second).values["total"], 3)


if __name__ == "__main__":
    unittest.main()
