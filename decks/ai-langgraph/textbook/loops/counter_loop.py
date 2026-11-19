"""실습 2: graph의 conditional edge로 되돌아가는 반복과 종료를 관찰한다."""

from typing import Literal, TypedDict

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    value: int
    target: int
    checks: int
    advances: int


def initial_state(value: int, target: int) -> State:
    return {"value": value, "target": target, "checks": 0, "advances": 0}


def check(state: State) -> dict[str, int]:
    return {"checks": state["checks"] + 1}


def choose_next(state: State) -> Literal["again", "done"]:
    # 비교는 check update가 반영된 state를 읽는다.
    return "done" if state["value"] >= state["target"] else "again"


def advance(state: State) -> dict[str, int]:
    return {"value": state["value"] + 2, "advances": state["advances"] + 1}


def build_graph():
    builder = StateGraph(State)
    builder.add_node("check", check)
    builder.add_node("advance", advance)
    builder.add_edge(START, "check")
    builder.add_conditional_edges("check", choose_next, {"again": "advance", "done": END})
    builder.add_edge("advance", "check")
    return builder.compile()


def main() -> None:
    graph = build_graph()
    inputs = initial_state(1, 6)
    print("initial:", inputs)
    for update in graph.stream(inputs, stream_mode="updates"):
        print("update:", update)
    # stream과 invoke는 별도의 실행이며 여기의 node들은 side effect가 없다.
    print("final (new invocation):", graph.invoke(inputs))

    try:
        graph.invoke(initial_state(1, 100), config={"recursion_limit": 4})
    except GraphRecursionError:
        print("expected failure: GraphRecursionError (super-step budget exhausted)")


if __name__ == "__main__":
    main()
