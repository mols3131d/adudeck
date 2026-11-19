"""교본 Unit 1에서 관찰해야 하는 state update와 조건 분기를 검증한다."""

import unittest

from textbook.state_flow.flow import build_graph, classify


class StateFlowTest(unittest.TestCase):
    def test_odd_branch_keeps_unmodified_key(self):
        initial = {"number": 3, "branch": ""}
        self.assertEqual(classify(initial), {"branch": "odd"})
        graph = build_graph()
        self.assertEqual(
            list(graph.stream(initial, stream_mode="updates")),
            [{"classify": {"branch": "odd"}}, {"increment": {"number": 4}}],
        )
        self.assertEqual(graph.invoke(initial), {"number": 4, "branch": "odd"})

    def test_even_branch_skips_increment(self):
        initial = {"number": 4, "branch": ""}
        graph = build_graph()
        updates = list(graph.stream(initial, stream_mode="updates"))
        self.assertEqual(
            updates, [{"classify": {"branch": "even"}}, {"double": {"number": 8}}]
        )
        self.assertEqual(graph.invoke(initial), {"number": 8, "branch": "even"})


if __name__ == "__main__":
    unittest.main()
