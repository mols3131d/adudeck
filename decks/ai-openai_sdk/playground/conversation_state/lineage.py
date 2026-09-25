import os

from openai import OpenAI

model = os.getenv("OPENAI_MODEL", "gpt-5.5")
client = OpenAI()

first = client.responses.create(
    model=model,
    input="Remember that my project codename is Juniper. Reply with the codename only.",
)
print("first:", first.output_text)
print("first response id:", first.id)

second = client.responses.create(
    model=model,
    previous_response_id=first.id,
    input="What project codename did I give you? Reply with the codename only.",
)
print("second:", second.output_text)
