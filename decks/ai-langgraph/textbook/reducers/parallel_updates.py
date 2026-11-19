"""관찰 실습 2: 병렬 node update를 reducer로 합류시키기."""

import operator
from typing import Annotated, TypedDict

from langgraph.errors import InvalidUpdateError
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    events: Annotated[list[str], operator.add]
    summary: str


class PlainState(TypedDict):
    events: list[str]
    summary: str


def seed(state) -> dict[str, list[str]]:
    return {"events": ["seed"]}


def left(state) -> dict[str, list[str]]:
    return {"events": ["left"]}


def right(state) -> dict[str, list[str]]:
    return {"events": ["right"]}


def join(state) -> dict[str, str]:
    return {"summary": ", ".join(sorted(state["events"]))}


def build_graph(*, with_reducer: bool):
    # Node input annotation을 고정하지 않아 두 State schema에 재사용한다.
    builder = StateGraph(State if with_reducer else PlainState)
    builder.add_node("seed", seed)
    builder.add_node("left", left)
    builder.add_node("right", right)
    builder.add_node("join", join)
    builder.add_edge(START, "seed")
    builder.add_edge("seed", "left")
    builder.add_edge("seed", "right")
    builder.add_edge(["left", "right"], "join")
    builder.add_edge("join", END)
    return builder.compile()


def main() -> None:
    initial = {"events": [], "summary": ""}
    graph = build_graph(with_reducer=True)
    print("updates:")
    for update in graph.stream(initial, stream_mode="updates"):
        print(update)
    print(f"final (new invocation): {graph.invoke(initial)}")

    # 고의로 같은 key에 두 update를 보내는 부정 사례.
    print("without reducer:")
    try:
        build_graph(with_reducer=False).invoke(initial)
    except InvalidUpdateError as error:
        print(f"expected failure: {type(error).__name__}")


if __name__ == "__main__":
    main()
