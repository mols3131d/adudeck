import os
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel


class TicketClassification(BaseModel):
    category: Literal["bug", "question", "request"]
    priority: Literal["low", "medium", "high"]
    summary: str


model = os.getenv("OPENAI_MODEL", "gpt-5.5")
client = OpenAI()

response = client.responses.parse(
    model=model,
    input=(
        "The checkout button freezes after I submit my card. "
        "Classify this support ticket and summarize it."
    ),
    text_format=TicketClassification,
)

print("status:", response.status)
print("parsed type:", type(response.output_parsed).__name__)
print("parsed value:", response.output_parsed)
