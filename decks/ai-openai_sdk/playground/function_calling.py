import json
import os
from typing import Any

from openai import OpenAI

ORDERS = {
    "A-101": {"order_id": "A-101", "status": "processing"},
    "A-102": {"order_id": "A-102", "status": "shipped"},
    "A-103": {"order_id": "A-103", "status": "delivered"},
}

LOOKUP_ORDER_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "lookup_order",
    "description": "Look up one order in the application's local teaching dataset.",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
        },
        "required": ["order_id"],
        "additionalProperties": False,
    },
    "strict": True,
}


def lookup_order(order_id: str) -> dict[str, Any]:
    order = ORDERS.get(order_id)
    if order is None:
        return {"order_id": order_id, "found": False}
    return {**order, "found": True}


model = os.getenv("OPENAI_MODEL", "gpt-5.5")
client = OpenAI()

response = client.responses.create(
    model=model,
    input="Look up order A-102 and tell me its current status.",
    tools=[LOOKUP_ORDER_TOOL],
    tool_choice={"type": "function", "name": "lookup_order"},
)

call = next(item for item in response.output if item.type == "function_call")
arguments = json.loads(call.arguments)

print("model proposal:", call.name, arguments, call.call_id)

result = lookup_order(arguments["order_id"])
print("local result:", result)

tool_output = {
    "type": "function_call_output",
    "call_id": call.call_id,
    "output": json.dumps(result),
}

final = client.responses.create(
    model=model,
    previous_response_id=response.id,
    input=[tool_output],
    tools=[LOOKUP_ORDER_TOOL],
    tool_choice="none",
)

print("final:", final.output_text)
