"""실습 4 확장: 완료된 실행의 과거 checkpoint로 replay한다."""

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    number: int
    offset: int


def build_graph(trace: list[str]):
    def prepare(state: State) -> dict[str, int]:
        trace.append("prepare")
        return {"offset": 5}

    def apply(state: State) -> dict[str, int]:
        trace.append("apply")
        return {"number": state["number"] + state["offset"]}

    builder = StateGraph(State)
    builder.add_node("prepare", prepare)
    builder.add_node("apply", apply)
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "apply")
    builder.add_edge("apply", END)
    return builder.compile(checkpointer=InMemorySaver())


def checkpoint_before_apply(graph, config):
    """이미 완료된 thread의 history에서 apply 직전 super-step을 찾는다."""
    return next(
        snapshot
        for snapshot in graph.get_state_history(config)
        if snapshot.next == ("apply",)
    )


def main() -> None:
    trace: list[str] = []
    graph = build_graph(trace)
    config = {"configurable": {"thread_id": "replay-example"}}

    first = graph.invoke({"number": 2, "offset": 0}, config=config)
    print("first:", first)
    print("after completed None:", graph.invoke(None, config=config))

    saved = checkpoint_before_apply(graph, config)
    print("checkpoint before apply:", saved.values, "next:", saved.next)

    print("replay:", graph.invoke(None, config=saved.config))
    print("visits after replay:", trace)

    print("new input:", graph.invoke({"number": 10, "offset": 0}, config=config))
    print("visits after new input:", trace)


if __name__ == "__main__":
    main()
