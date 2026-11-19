"""checkpoint replay와 새 입력·최신 완료 상태의 차이를 검증한다."""

import unittest

from textbook.checkpoints.replay import build_graph, checkpoint_before_apply


class ReplayTest(unittest.TestCase):
    def test_historical_checkpoint_reexecutes_only_later_nodes(self):
        trace: list[str] = []
        graph = build_graph(trace)
        config = {"configurable": {"thread_id": "history"}}

        expected = {"number": 7, "offset": 5}
        self.assertEqual(graph.invoke({"number": 2, "offset": 0}, config=config), expected)
        self.assertEqual(trace, ["prepare", "apply"])

        # 완료된 최신 checkpoint에 None을 넘기면 실행할 node가 없다.
        self.assertEqual(graph.get_state(config).next, ())
        self.assertEqual(graph.invoke(None, config=config), expected)
        self.assertEqual(trace, ["prepare", "apply"])

        selected = checkpoint_before_apply(graph, config)
        self.assertEqual(selected.values, {"number": 2, "offset": 5})
        self.assertEqual(selected.next, ("apply",))
        self.assertIn("checkpoint_id", selected.config["configurable"])

        # 과거 checkpoint config를 쓰면 apply만 다시 실행한다.
        self.assertEqual(graph.invoke(None, config=selected.config), expected)
        self.assertEqual(trace, ["prepare", "apply", "apply"])

    def test_new_input_is_not_replay(self):
        trace: list[str] = []
        graph = build_graph(trace)
        config = {"configurable": {"thread_id": "new-input"}}
        graph.invoke({"number": 2, "offset": 0}, config=config)

        self.assertEqual(
            graph.invoke({"number": 10, "offset": 0}, config=config),
            {"number": 15, "offset": 5},
        )
        # 새 입력은 entry부터 시작한다. 완료된 과거 node도 실행된다.
        self.assertEqual(trace, ["prepare", "apply", "prepare", "apply"])


if __name__ == "__main__":
    unittest.main()
