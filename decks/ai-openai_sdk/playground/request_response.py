import os

from openai import OpenAI

model = os.getenv("OPENAI_MODEL", "gpt-5.5")

client = OpenAI()

response = client.responses.create(
    model=model,
    input="Explain the difference between a Python list and tuple in one sentence.",
)

print(response.output_text)
