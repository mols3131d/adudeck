from __future__ import annotations

import unittest
from types import SimpleNamespace

from prompt_versioning import generate_with_prompt


class FakePrompt:
    name = "support/refund-answer"
    version = 21
    labels = ["staging"]

    def compile(self, **variables):
        return [
            {
                "role": "system",
                "content": f"환불 기간은 {variables['policy_days']}일입니다.",
            },
            {
                "role": "user",
                "content": variables["question"],
            },
        ]


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="14일 이내입니다.")


class FakeOpenAI:
    def __init__(self) -> None:
        self.responses = FakeResponses()


class PromptVersioningContractTest(unittest.TestCase):
    def test_compiled_prompt_and_version_object_travel_together(self) -> None:
        client = FakeOpenAI()
        prompt = FakePrompt()

        evidence = generate_with_prompt(
            client,
            prompt,
            model="test-model",
            policy_days=14,
            question="환불 기간은?",
        )

        call = client.responses.calls[0]
        self.assertEqual(call["name"], "answer-generation")
        self.assertEqual(call["model"], "test-model")
        self.assertIs(call["langfuse_prompt"], prompt)
        self.assertEqual(
            call["input"],
            [
                {"role": "system", "content": "환불 기간은 14일입니다."},
                {"role": "user", "content": "환불 기간은?"},
            ],
        )
        self.assertEqual(evidence["prompt_name"], "support/refund-answer")
        self.assertEqual(evidence["prompt_version"], 21)
        self.assertEqual(evidence["prompt_labels"], ("staging",))


if __name__ == "__main__":
    unittest.main()
