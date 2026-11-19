"""종합 실습: 병렬 검증 + reducer + thread checkpoint + interrupt + 재시도."""

import operator
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    number: int
    route: str
    checks: Annotated[list[str], operator.add]
    approved: bool | None
    outcome: str


def classify(state: State) -> dict[str, str]:
    return {"route": "odd" if state["number"] % 2 else "even"}


def check_range(state: State) -> dict[str, list[str]]:
    return {"checks": ["range-ok" if 0 <= state["number"] <= 20 else "range-invalid"]}


def check_parity(state: State) -> dict[str, list[str]]:
    return {"checks": [state["route"]]}


def choose_action(state: State) -> Literal["apply", "cancel"]:
    if state["approved"] is True and "range-ok" in state["checks"]:
        return "apply"
    return "cancel"


def initial_state(number: int) -> State:
    return {"number": number, "route": "", "checks": [], "approved": None, "outcome": ""}


def build_graph(trace: list[str], *, fail_first_apply: bool = False):
    apply_attempts = 0

    def ask_approval(state: State) -> dict[str, bool]:
        trace.append("ask_approval")
        decision = interrupt({"number": state["number"], "checks": sorted(state["checks"])})
        return {"approved": decision}

    def apply(state: State) -> dict[str, int | str]:
        nonlocal apply_attempts
        apply_attempts += 1
        trace.append("apply")
        # 외부 요청 대신 오류를 딱 한 번 발생시키는 실습용 fault injection.
        if fail_first_apply and apply_attempts == 1:
            raise RuntimeError("simulated apply failure")
        new_number = state["number"] + 1 if state["route"] == "odd" else state["number"] * 2
        return {"number": new_number, "outcome": "applied"}

    def cancel(state: State) -> dict[str, str]:
        trace.append("cancel")
        return {"outcome": "cancelled"}

    builder = StateGraph(State)
    builder.add_node("classify", classify)
    builder.add_node("check_range", check_range)
    builder.add_node("check_parity", check_parity)
    builder.add_node("ask_approval", ask_approval)
    builder.add_node("apply", apply)
    builder.add_node("cancel", cancel)
    builder.add_edge(START, "classify")
    builder.add_edge("classify", "check_range")
    builder.add_edge("classify", "check_parity")
    # 둘 다 완료되어야 승인 요청으로 합류한다.
    builder.add_edge(["check_range", "check_parity"], "ask_approval")
    builder.add_conditional_edges("ask_approval", choose_action)
    builder.add_edge("apply", END)
    builder.add_edge("cancel", END)
    return builder.compile(checkpointer=InMemorySaver())


def main() -> None:
    trace: list[str] = []
    graph = build_graph(trace)
    config = {"configurable": {"thread_id": "integrated-approved"}}
    paused = graph.invoke(initial_state(3), config=config)
    print("pause:", paused["__interrupt__"][0].value)
    print("snapshot:", graph.get_state(config).values)
    print("next:", graph.get_state(config).next)
    result = graph.invoke(Command(resume=True), config=config)
    print("approved:", result)
    print("approval visits:", trace.count("ask_approval"))

    reject_config = {"configurable": {"thread_id": "integrated-rejected"}}
    graph.invoke(initial_state(4), config=reject_config)
    print("rejected:", graph.invoke(Command(resume=False), config=reject_config))


if __name__ == "__main__":
    main()
