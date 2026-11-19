"""관찰 실습 1: partial update, 조건부 edge, 종료 state."""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    number: int
    branch: str


def classify(state: State) -> dict[str, str]:
    return {"branch": "odd" if state["number"] % 2 else "even"}


def choose_branch(state: State) -> Literal["increment", "double"]:
    return "increment" if state["branch"] == "odd" else "double"


def increment(state: State) -> dict[str, int]:
    return {"number": state["number"] + 1}


def double(state: State) -> dict[str, int]:
    return {"number": state["number"] * 2}


def build_graph():
    builder = StateGraph(State)
    builder.add_node("classify", classify)
    builder.add_node("increment", increment)
    builder.add_node("double", double)
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", choose_branch)
    builder.add_edge("increment", END)
    builder.add_edge("double", END)
    return builder.compile()


def main() -> None:
    graph = build_graph()
    for initial in ({"number": 3, "branch": ""}, {"number": 4, "branch": ""}):
        print(f"input: {initial}")
        for event in graph.stream(initial, stream_mode="updates"):
            print(f"update: {event}")
        # 별도 실행: 앞의 stream과 같은 invocation이 아니다.
        print(f"final (new invocation): {graph.invoke(initial)}")


if __name__ == "__main__":
    main()
