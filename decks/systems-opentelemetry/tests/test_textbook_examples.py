"""Validate learner-visible evidence for the core OpenTelemetry textbook examples."""

import json
import os
from pathlib import Path
import re
import selectors
import socket
import subprocess
import sys
import time
import unittest


DECK = Path(__file__).resolve().parents[1]
TEXTBOOK = DECK / "textbook"


def clean_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("OTEL_")}


def json_objects(output: str) -> list[dict]:
    """Extract consecutive or interleaved Console*Exporter JSON objects."""
    decoder = json.JSONDecoder()
    objects: list[dict] = []
    position = 0
    while True:
        start = output.find("{", position)
        if start < 0:
            break
        try:
            value, consumed = decoder.raw_decode(output[start:])
        except json.JSONDecodeError:
            position = start + 1
            continue
        if isinstance(value, dict):
            objects.append(value)
        position = start + consumed
    return objects


class TextbookExampleTest(unittest.TestCase):
    def run_script(self, relative_path: str) -> str:
        result = subprocess.run(
            [sys.executable, str(TEXTBOOK / relative_path)],
            env=clean_env(),
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        self.assertEqual(result.stderr, "")
        return result.stdout

    def test_failure_example_distinguishes_recovery_from_final_failure(self) -> None:
        output = self.run_script("03-span-data-failure/span_failure.py")
        spans = [value for value in json_objects(output) if "context" in value and "name" in value]
        self.assertEqual(len(spans), 6)

        reserve_spans = [span for span in spans if span["name"] == "reserve_inventory"]
        self.assertEqual(len(reserve_spans), 2)
        for span in reserve_spans:
            self.assertTrue(span["attributes"]["inventory.fallback_used"])
            self.assertNotIn("error.type", span["attributes"])
            self.assertNotEqual(span["status"]["status_code"], "ERROR")

        payment_spans = [span for span in spans if span["name"] == "charge_payment"]
        failed_payment = next(span for span in payment_spans if "error.type" in span["attributes"])
        successful_payment = next(span for span in payment_spans if "error.type" not in span["attributes"])
        self.assertEqual(failed_payment["status"]["status_code"], "ERROR")
        self.assertEqual(failed_payment["attributes"]["error.type"], "__main__.PaymentDeclined")
        self.assertNotEqual(successful_payment["status"]["status_code"], "ERROR")

        checkout_spans = [span for span in spans if span["name"] == "checkout"]
        failed_checkout = next(span for span in checkout_spans if span["attributes"]["checkout.result"] == "failed")
        completed_checkout = next(span for span in checkout_spans if span["attributes"]["checkout.result"] == "completed")
        self.assertEqual(failed_checkout["status"]["status_code"], "ERROR")
        self.assertNotEqual(completed_checkout["status"]["status_code"], "ERROR")

    def test_resource_and_instrumentation_scope_are_independent_axes(self) -> None:
        output = self.run_script("04-resource-api-sdk/sdk_boundaries.py")
        summaries = [line for line in output.splitlines() if line.startswith("boundary-summary ")]
        self.assertEqual(len(summaries), 2)
        self.assertTrue(all("service.name=adudeck-otel-boundaries" in line for line in summaries))
        self.assertTrue(any("scope=adudeck.checkout" in line for line in summaries))
        self.assertTrue(any("scope=adudeck.payment" in line for line in summaries))
        self.assertTrue(all("scope.version=1.0.0" in line for line in summaries))

    def test_metric_instruments_expose_expected_measurement_semantics(self) -> None:
        output = self.run_script("08-metrics/metrics_demo.py")
        latest: dict[str, dict] = {}
        for document in json_objects(output):
            for resource_metrics in document.get("resource_metrics", []):
                for scope_metrics in resource_metrics.get("scope_metrics", []):
                    for metric in scope_metrics.get("metrics", []):
                        latest[metric["name"]] = metric

        self.assertEqual(set(latest), {"checkout.requests", "checkout.active", "checkout.duration"})

        request_points = latest["checkout.requests"]["data"]["data_points"]
        self.assertEqual(sum(point["value"] for point in request_points), 3)

        active_points = latest["checkout.active"]["data"]["data_points"]
        self.assertTrue(active_points)
        self.assertTrue(all(point["value"] == 0 for point in active_points))

        duration_points = latest["checkout.duration"]["data"]["data_points"]
        self.assertEqual(sum(point["count"] for point in duration_points), 3)

    def run_propagation_case(self, drop_context: bool) -> tuple[str, str]:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]

        server = subprocess.Popen(
            [sys.executable, "-u", str(TEXTBOOK / "06-propagation/service_b.py"), "--port", str(port)],
            env=clean_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertIsNotNone(server.stdout)
        selector = selectors.DefaultSelector()
        selector.register(server.stdout, selectors.EVENT_READ)
        try:
            self.assertTrue(selector.select(timeout=5), "service B did not announce readiness")
            ready = server.stdout.readline()
            self.assertIn(f"127.0.0.1:{port}", ready)

            command = [sys.executable, str(TEXTBOOK / "06-propagation/client.py"), "--port", str(port)]
            if drop_context:
                command.append("--drop-context")
            client = subprocess.run(
                command,
                env=clean_env(),
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            self.assertEqual(client.stderr, "")
            self.assertEqual(re.search(r"response=ok", client.stdout).group(0), "response=ok")

            self.assertTrue(selector.select(timeout=5), "service B did not emit request evidence")
            service_line = server.stdout.readline()
            self.assertRegex(service_line, r"service-b trace_id=[0-9a-f]{32} span_id=[0-9a-f]{16}")
            time.sleep(0.05)
        finally:
            selector.close()
            server.terminate()
            try:
                remaining_out, _ = server.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                remaining_out, _ = server.communicate(timeout=3)

        return client.stdout, service_line + remaining_out

    def test_context_propagation_connects_processes_and_drop_context_breaks_it(self) -> None:
        normal_client, normal_server = self.run_propagation_case(drop_context=False)
        dropped_client, dropped_server = self.run_propagation_case(drop_context=True)

        client_pattern = r"service-a trace_id=([0-9a-f]{32}) span_id=([0-9a-f]{16})"
        server_pattern = r"service-b trace_id=([0-9a-f]{32}) span_id=([0-9a-f]{16})"

        normal_a = re.search(client_pattern, normal_client)
        normal_b = re.search(server_pattern, normal_server)
        self.assertIsNotNone(normal_a)
        self.assertIsNotNone(normal_b)
        self.assertRegex(normal_client, r"traceparent=00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}")
        self.assertEqual(normal_a.group(1), normal_b.group(1))

        dropped_a = re.search(client_pattern, dropped_client)
        dropped_b = re.search(server_pattern, dropped_server)
        self.assertIsNotNone(dropped_a)
        self.assertIsNotNone(dropped_b)
        self.assertIn("traceparent=<not injected>", dropped_client)
        self.assertNotEqual(dropped_a.group(1), dropped_b.group(1))


if __name__ == "__main__":
    unittest.main()
