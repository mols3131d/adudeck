"""관찰 실습 4: interrupt 이후 같은 node의 재실행 경계."""

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    number: int
    approved: bool | None
    finished: bool


def build_graph(trace: list[str]):
    def prepare(state: State) -> dict[str, int]:
        trace.append("prepare")
        return {"number": state["number"] + 1}

    def request_approval(state: State) -> dict[str, bool]:
        # 이 메모리 기록은 재실행을 관찰하려는 학습용 instrumentation이다.
        trace.append("request_approval")
        decision = interrupt({"question": "Proceed?", "number": state["number"]})
        return {"approved": decision}

    def finish(state: State) -> dict[str, bool]:
        trace.append("finish")
        return {"finished": state["approved"] is True}

    builder = StateGraph(State)
    builder.add_node("prepare", prepare)
    builder.add_node("request_approval", request_approval)
    builder.add_node("finish", finish)
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "request_approval")
    builder.add_edge("request_approval", "finish")
    builder.add_edge("finish", END)
    return builder.compile(checkpointer=InMemorySaver())


def main() -> None:
    trace: list[str] = []
    graph = build_graph(trace)
    config = {"configurable": {"thread_id": "approval-example"}}
    initial = {"number": 2, "approved": None, "finished": False}

    paused = graph.invoke(initial, config=config)
    print("interrupt:", paused["__interrupt__"][0].value)
    print("saved:", graph.get_state(config).values)
    print("next:", graph.get_state(config).next)

    result = graph.invoke(Command(resume=True), config=config)
    print("result:", result)
    print("node visits:", trace)


if __name__ == "__main__":
    main()
