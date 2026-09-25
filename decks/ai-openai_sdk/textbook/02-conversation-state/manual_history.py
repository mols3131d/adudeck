import os

from openai import OpenAI

model = os.getenv("OPENAI_MODEL", "gpt-5.5")
client = OpenAI()

first_prompt = "Remember that my project codename is Juniper. Reply with the codename only."
followup = "What project codename did I give you? Reply with the codename only."

history = [{"role": "user", "content": first_prompt}]

first = client.responses.create(
    model=model,
    input=history,
    store=False,
)
print("first:", first.output_text)

history += first.output
history.append({"role": "user", "content": followup})

second = client.responses.create(
    model=model,
    input=history,
    store=False,
)
print("second:", second.output_text)
