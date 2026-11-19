"""Contract checks for SDK tool routing; no provider credentials required."""

import unittest

from first_loop import run_case


class AgentLoopEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = {name: run_case(name) for name in ("basic", "deep", "planned", "denied")}

    def test_fixture_calls_execute_in_every_variant(self) -> None:
        for case in ("basic", "deep", "planned"):
            with self.subTest(case=case):
                results = self.cases[case]["tool_results"]
                names = [result["name"] for result in results]
                self.assertEqual(names.count("lookup_fixture"), 2)
                self.assertTrue(any("alpha: p95=120ms" in str(r["content"]) for r in results))
                self.assertTrue(any("beta: p95=260ms" in str(r["content"]) for r in results))

    def test_exposed_tools_differ_from_invoked_tools(self) -> None:
        basic = self.cases["basic"]
        deep = self.cases["deep"]
        self.assertIn("lookup_fixture", basic["offered_tools"])
        self.assertNotIn("write_file", basic["offered_tools"])
        self.assertIn("lookup_fixture", deep["offered_tools"])
        self.assertIn("write_file", deep["offered_tools"])
        self.assertIn("task", deep["offered_tools"])
        self.assertNotIn("execute", deep["offered_tools"])
        self.assertNotIn("write_file", [call["name"] for call in deep["calls"]])

    def test_todo_planning_requires_opt_in(self) -> None:
        self.assertNotIn("write_todos", self.cases["deep"]["offered_tools"])
        planned = self.cases["planned"]
        self.assertIn("write_todos", planned["offered_tools"])
        self.assertEqual([call["name"] for call in planned["calls"]].count("write_todos"), 2)
        self.assertEqual(planned["todos"][0]["status"], "completed")

    def test_permission_denies_internal_write_not_custom_tool(self) -> None:
        denied = self.cases["denied"]
        by_name = {result["name"]: result for result in denied["tool_results"]}
        self.assertEqual(by_name["write_file"]["status"], "error")
        self.assertIn("permission denied", str(by_name["write_file"]["content"]).lower())
        self.assertIn("alpha: p95=120ms", str(by_name["lookup_fixture"]["content"]))
        self.assertNotIn("/notes/output.txt", denied["files"])


if __name__ == "__main__":
    unittest.main()
