"""동일 super-step 동시 update와 key별 reducer 계약 검증."""

import unittest

from langgraph.errors import InvalidUpdateError

from textbook.reducers.parallel_updates import build_graph


class ReducerTest(unittest.TestCase):
    def test_parallel_updates_are_merged_before_join(self):
        initial = {"events": [], "summary": ""}
        graph = build_graph(with_reducer=True)
        updates = list(graph.stream(initial, stream_mode="updates"))
        self.assertEqual(updates[0], {"seed": {"events": ["seed"]}})
        self.assertIn({"left": {"events": ["left"]}}, updates)
        self.assertIn({"right": {"events": ["right"]}}, updates)
        self.assertEqual(updates[-1], {"join": {"summary": "left, right, seed"}})
        final = graph.invoke(initial)
        self.assertEqual(final["summary"], "left, right, seed")
        self.assertEqual(final["events"][0], "seed")
        self.assertCountEqual(final["events"][1:], ["left", "right"])

    def test_concurrent_writes_without_reducer_fail(self):
        graph = build_graph(with_reducer=False)
        with self.assertRaises(InvalidUpdateError):
            graph.invoke({"events": [], "summary": ""})


if __name__ == "__main__":
    unittest.main()
