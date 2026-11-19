"""Validate the optional live-CLI graph setup without calling a provider."""

import unittest

from first_loop import RecordingFakeModel, scripted_messages
from live_provider import build_agent, run_agent


class LiveProviderBoundaryTests(unittest.TestCase):
    def test_case_validation_before_any_remote_call(self) -> None:
        fake = RecordingFakeModel(responses=scripted_messages("basic"))
        with self.assertRaises(ValueError):
            build_agent("unknown", fake)

    def test_basic_and_deep_paths_execute_real_fixture_without_credentials(self) -> None:
        for case in ("basic", "deep"):
            with self.subTest(case=case):
                fake = RecordingFakeModel(responses=scripted_messages(case))
                evidence = run_agent(case, fake)
                self.assertEqual(evidence["requested_tools"], ["lookup_fixture", "lookup_fixture"])
                self.assertEqual(
                    [x["name"] for x in evidence["executed_tools"]],
                    ["lookup_fixture", "lookup_fixture"],
                )
                self.assertEqual(evidence["files"], [])

    def test_planning_is_a_separate_optional_configuration(self) -> None:
        fake = RecordingFakeModel(responses=scripted_messages("planned"))
        evidence = run_agent("planned", fake)
        self.assertEqual(evidence["requested_tools"].count("write_todos"), 2)
        self.assertEqual(evidence["todos"][0]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
