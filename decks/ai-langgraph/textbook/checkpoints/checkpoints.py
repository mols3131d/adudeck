"""관찰 실습 3: checkpoint, thread_id, 새 입력의 상태 업데이트."""

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    total: int
    delta: int


def add(state: State) -> dict[str, int]:
    return {"total": state["total"] + state["delta"]}


def build_graph():
    builder = StateGraph(State)
    builder.add_node("add", add)
    builder.add_edge(START, "add")
    builder.add_edge("add", END)
    # 이 저장소는 프로세스 메모리만 사용한다. 재시작 후 데이터는 사라진다.
    return builder.compile(checkpointer=InMemorySaver())


def main() -> None:
    graph = build_graph()
    first = {"configurable": {"thread_id": "study-a"}}
    other = {"configurable": {"thread_id": "study-b"}}

    print("A first:", graph.invoke({"total": 10, "delta": 2}, config=first))
    snapshot = graph.get_state(first)
    print("A checkpoint:", snapshot.values, "next:", snapshot.next)

    print("A new input:", graph.invoke({"delta": 5}, config=first))
    print("B independent:", graph.invoke({"total": 1, "delta": 2}, config=other))
    print("A latest:", graph.get_state(first).values)
    print("B latest:", graph.get_state(other).values)


if __name__ == "__main__":
    main()
