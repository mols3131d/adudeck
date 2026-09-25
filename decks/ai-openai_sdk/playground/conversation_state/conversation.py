import os

from openai import OpenAI

model = os.getenv("OPENAI_MODEL", "gpt-5.5")
client = OpenAI()

conversation = client.conversations.create()
print("conversation id:", conversation.id)

try:
    first = client.responses.create(
        model=model,
        conversation=conversation.id,
        input="Remember that my project codename is Juniper. Reply with the codename only.",
    )
    print("first:", first.output_text)

    second = client.responses.create(
        model=model,
        conversation=conversation.id,
        input="What project codename did I give you? Reply with the codename only.",
    )
    print("second:", second.output_text)
finally:
    items = list(client.conversations.items.list(conversation.id, order="asc", limit=100))
    print("stored item ids:", [item.id for item in items])

    for item in items:
        client.conversations.items.delete(item.id, conversation_id=conversation.id)

    deleted = client.conversations.delete(conversation.id)
    print("conversation deleted:", deleted.deleted)
