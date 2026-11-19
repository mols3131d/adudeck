"""반복의 종료 조건, node 실행 횟수, super-step 상한 검증."""

import unittest

from langgraph.errors import GraphRecursionError

from textbook.loops.counter_loop import build_graph, initial_state


class LoopTest(unittest.TestCase):
    def test_updates_trace_and_termination(self):
        graph = build_graph()
        initial = initial_state(1, 6)
        updates = list(graph.stream(initial, stream_mode="updates"))
        self.assertEqual(
            [next(iter(update)) for update in updates],
            ["check", "advance", "check", "advance", "check", "advance", "check"],
        )
        self.assertEqual(
            [item["advance"]["value"] for item in updates if "advance" in item],
            [3, 5, 7],
        )
        self.assertEqual(
            graph.invoke(initial),
            {"value": 7, "target": 6, "checks": 4, "advances": 3},
        )

    def test_initial_value_already_satisfies_exit_condition(self):
        graph = build_graph()
        for initial_value in (6, 8):
            with self.subTest(initial_value=initial_value):
                initial = initial_state(initial_value, 6)
                updates = list(graph.stream(initial, stream_mode="updates"))
                self.assertEqual(updates, [{"check": {"checks": 1}}])
                self.assertEqual(
                    graph.invoke(initial),
                    {"value": initial_value, "target": 6, "checks": 1, "advances": 0},
                )

    def test_recursion_limit_is_super_step_guard_not_success(self):
        graph = build_graph()
        with self.assertRaises(GraphRecursionError):
            graph.invoke(initial_state(1, 100), config={"recursion_limit": 4})


if __name__ == "__main__":
    unittest.main()
