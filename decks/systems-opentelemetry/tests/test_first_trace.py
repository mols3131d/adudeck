"""Check learner-visible console evidence in fresh processes, including Unit 0's edit."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "textbook/00-first-trace/first_trace.py"


class FirstTraceTest(unittest.TestCase):
    def run_script(self, script: Path) -> dict:
        # Ambient SDK configuration must not change this local experiment's sampling/resource.
        env = {key: value for key, value in os.environ.items() if not key.startswith("OTEL_")}
        result = subprocess.run(
            [sys.executable, str(script)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.count("validate_cart: ok\n"), 1)
        self.assertEqual(result.stdout.count("charge_payment: ok\n"), 1)
        output = result.stdout.replace("validate_cart: ok\n", "").replace("charge_payment: ok\n", "")
        decoder = json.JSONDecoder()
        spans = []
        while output.strip():
            span, end = decoder.raw_decode(output.lstrip())
            spans.append(span)
            output = output.lstrip()[end:]

        self.assertEqual(len(spans), 3)
        self.assertEqual({span["name"] for span in spans}, {"checkout", "validate_cart", "charge_payment"})
        self.assertEqual(len({span["context"]["span_id"] for span in spans}), 3)
        expected_attributes = {
            "checkout": {"checkout.currency": "KRW"},
            "validate_cart": {"cart.item_count": 2},
            "charge_payment": {"payment.method": "card"},
        }
        for span in spans:
            self.assertEqual(span["attributes"], expected_attributes[span["name"]])
            self.assertEqual(span["resource"]["attributes"]["service.name"], "adudeck-otel-first-trace")
            self.assertRegex(span["context"]["trace_id"], r"^0x[0-9a-f]{32}$")
            self.assertRegex(span["context"]["span_id"], r"^0x[0-9a-f]{16}$")
            self.assertNotEqual(int(span["context"]["trace_id"], 16), 0)
            self.assertNotEqual(int(span["context"]["span_id"], 16), 0)
        return {span["name"]: span for span in spans}

    def test_children_share_checkout_trace(self) -> None:
        spans = self.run_script(SCRIPT)
        checkout = spans["checkout"]
        self.assertIsNone(checkout["parent_id"])
        for name in ("validate_cart", "charge_payment"):
            self.assertEqual(spans[name]["context"]["trace_id"], checkout["context"]["trace_id"])
            self.assertEqual(spans[name]["parent_id"], checkout["context"]["span_id"])

    def test_payment_outside_current_span_starts_new_trace(self) -> None:
        source = SCRIPT.read_text()
        original = "        validate_cart()\n        charge_payment()\n"
        self.assertEqual(source.count(original), 1, "Update the smoke variation when the teaching script changes.")
        # Apply exactly the learner's one-line indentation change to a disposable copy.
        with tempfile.TemporaryDirectory() as directory:
            variant = Path(directory) / "first_trace.py"
            variant.write_text(source.replace(original, "        validate_cart()\n    charge_payment()\n"))
            spans = self.run_script(variant)
        checkout = spans["checkout"]
        self.assertIsNone(checkout["parent_id"])
        self.assertEqual(spans["validate_cart"]["parent_id"], checkout["context"]["span_id"])
        self.assertEqual(spans["validate_cart"]["context"]["trace_id"], checkout["context"]["trace_id"])
        self.assertIsNone(spans["charge_payment"]["parent_id"])
        self.assertNotEqual(spans["charge_payment"]["context"]["trace_id"], checkout["context"]["trace_id"])


if __name__ == "__main__":
    unittest.main()
