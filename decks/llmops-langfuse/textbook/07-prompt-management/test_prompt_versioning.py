from __future__ import annotations

import unittest
from types import SimpleNamespace

from prompt_versioning import (
    LAB_PROMPT,
    ensure_lab_prompt,
    fetch_prompt,
    generate_with_prompt,
    prompt_lookup_kwargs,
)


class FakePrompt:
    name = "support/refund-answer"
    version = 21
    labels = ["staging"]
    prompt = LAB_PROMPT

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


class FakeNotFoundError(Exception):
    pass


class FakeLangfuse:
    def __init__(self, *, prompt: object | None = None) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.create_calls: list[dict[str, object]] = []
        self.prompt = FakePrompt() if prompt is None else prompt

    def get_prompt(self, name: str, **kwargs):
        self.calls.append((name, kwargs))
        if self.prompt is MISSING:
            raise FakeNotFoundError("prompt missing")
        return self.prompt

    def create_prompt(self, **kwargs):
        self.create_calls.append(kwargs)
        created = FakePrompt()
        created.labels = list(kwargs["labels"])
        return created


MISSING = object()


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

    def test_label_lookup_uses_movable_pointer(self) -> None:
        langfuse = FakeLangfuse()

        prompt = fetch_prompt(langfuse, label="staging")

        self.assertIs(prompt, langfuse.prompt)
        self.assertEqual(
            langfuse.calls,
            [
                (
                    "support/refund-answer",
                    {"type": "chat", "label": "staging"},
                )
            ],
        )

    def test_exact_version_lookup_does_not_depend_on_label(self) -> None:
        langfuse = FakeLangfuse()

        fetch_prompt(langfuse, version=21)

        self.assertEqual(
            langfuse.calls,
            [
                (
                    "support/refund-answer",
                    {"type": "chat", "version": 21},
                )
            ],
        )

    def test_default_lookup_is_production_label(self) -> None:
        self.assertEqual(
            prompt_lookup_kwargs(label=None, version=None),
            {"type": "chat", "label": "production"},
        )

    def test_label_and_version_cannot_be_selected_together(self) -> None:
        with self.assertRaisesRegex(ValueError, "not both"):
            prompt_lookup_kwargs(label="staging", version=21)

    def test_bootstrap_reuses_matching_prompt_without_creating_version(self) -> None:
        langfuse = FakeLangfuse()

        prompt, created = ensure_lab_prompt(
            langfuse,
            label="staging",
            not_found_error=FakeNotFoundError,
        )

        self.assertIs(prompt, langfuse.prompt)
        self.assertFalse(created)
        self.assertEqual(langfuse.create_calls, [])

    def test_bootstrap_creates_missing_synthetic_prompt(self) -> None:
        langfuse = FakeLangfuse(prompt=MISSING)

        prompt, created = ensure_lab_prompt(
            langfuse,
            label="staging",
            not_found_error=FakeNotFoundError,
        )

        self.assertTrue(created)
        self.assertEqual(prompt.labels, ["staging"])
        self.assertEqual(
            langfuse.create_calls,
            [
                {
                    "name": "support/refund-answer",
                    "type": "chat",
                    "prompt": LAB_PROMPT,
                    "labels": ["staging"],
                    "commit_message": "adudeck Unit 7 synthetic prompt bootstrap",
                }
            ],
        )

    def test_bootstrap_refuses_to_overwrite_different_prompt_content(self) -> None:
        conflicting = FakePrompt()
        conflicting.prompt = [{"role": "system", "content": "different"}]
        langfuse = FakeLangfuse(prompt=conflicting)

        with self.assertRaisesRegex(RuntimeError, "different content"):
            ensure_lab_prompt(
                langfuse,
                label="staging",
                not_found_error=FakeNotFoundError,
            )

        self.assertEqual(langfuse.create_calls, [])


if __name__ == "__main__":
    unittest.main()
