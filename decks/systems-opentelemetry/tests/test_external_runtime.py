"""End-to-end acceptance for version-sensitive OpenTelemetry textbook boundaries.

This suite intentionally exercises dependencies that are not part of the deck's core lock:
Flask/zero-code instrumentation and an actual Collector container.
"""

import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4


DECK = Path(__file__).resolve().parents[1]
TEXTBOOK = DECK / "textbook"
FLASK_VERSION = "3.1.3"
OTEL_CONTRIB_VERSION = "0.66b0"
OTEL_EXPORTER_VERSION = "1.45.0"
COLLECTOR_VERSION = "0.162.0"
COLLECTOR_IMAGE = f"otel/opentelemetry-collector:{COLLECTOR_VERSION}"


def clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("OTEL_")}
    if extra:
        env.update(extra)
    return env


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def uv_command(with_deps: list[str], command: list[str]) -> list[str]:
    result = ["uv", "run", "--project", str(DECK), "--locked"]
    for dependency in with_deps:
        result.extend(["--with", dependency])
    return [*result, *command]


def json_objects(output: str) -> list[dict]:
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


def wait_http(url: str, process: subprocess.Popen, timeout: float = 20) -> str:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"server exited before request succeeded: returncode={process.returncode}")
        try:
            with urlopen(url, timeout=0.5) as response:
                return response.read().decode()
        except (URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
            time.sleep(0.1)
    raise AssertionError(f"server did not accept request at {url}: {last_error}")


def wait_for_file_text(path: Path, required: list[str], timeout: float = 10) -> str:
    deadline = time.monotonic() + timeout
    text = ""
    while time.monotonic() < deadline:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if all(fragment in text for fragment in required):
            return text
        time.sleep(0.1)
    return text


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


def parse_scope_summary(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key in ("trace_id", "span_id", "parent_id", "scope"):
        match = re.search(rf"(?:^| ){key}=([^ ]+)", line)
        if match is None:
            raise AssertionError(f"missing {key} in scope summary: {line}")
        fields[key] = match.group(1)
    return fields


class ExternalRuntimeAcceptanceTest(unittest.TestCase):
    def run_flask_server(
        self,
        script: str,
        *,
        instrumented: bool,
        port: int,
    ) -> tuple[subprocess.Popen, Path]:
        with_deps = [f"flask=={FLASK_VERSION}"]
        command: list[str]
        env = clean_env()

        if instrumented:
            with_deps.extend(
                [
                    f"opentelemetry-distro=={OTEL_CONTRIB_VERSION}",
                    f"opentelemetry-instrumentation-flask=={OTEL_CONTRIB_VERSION}",
                ]
            )
            command = [
                "opentelemetry-instrument",
                "python",
                "-u",
                str(TEXTBOOK / "05-instrumentation" / script),
                "--port",
                str(port),
            ]
            env = clean_env(
                {
                    "OTEL_SERVICE_NAME": "adudeck-otel-acceptance",
                    "OTEL_TRACES_EXPORTER": "console",
                    "OTEL_METRICS_EXPORTER": "none",
                    "OTEL_LOGS_EXPORTER": "none",
                    "OTEL_BSP_SCHEDULE_DELAY": "100",
                }
            )
        else:
            command = [
                "python",
                "-u",
                str(TEXTBOOK / "05-instrumentation" / script),
                "--port",
                str(port),
            ]

        log = tempfile.NamedTemporaryFile(prefix="adudeck-otel-flask-", suffix=".log", delete=False)
        log_path = Path(log.name)
        log.close()
        handle = log_path.open("w", encoding="utf-8")
        process = subprocess.Popen(
            uv_command(with_deps, command),
            cwd=DECK,
            env=env,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
        handle.close()
        return process, log_path

    def test_flask_plain_and_mixed_instrumentation(self) -> None:
        plain_port = free_port()
        plain_process, plain_log = self.run_flask_server(
            "flask_zero_code.py", instrumented=False, port=plain_port
        )
        try:
            body = wait_http(f"http://127.0.0.1:{plain_port}/checkout", plain_process)
            self.assertIn("42000", body)
        finally:
            stop_process(plain_process)
        plain_output = plain_log.read_text(encoding="utf-8")
        plain_log.unlink(missing_ok=True)
        self.assertEqual(
            [value for value in json_objects(plain_output) if value.get("context")],
            [],
            plain_output,
        )

        mixed_port = free_port()
        mixed_process, mixed_log = self.run_flask_server(
            "flask_mixed.py", instrumented=True, port=mixed_port
        )
        try:
            body = wait_http(f"http://127.0.0.1:{mixed_port}/checkout", mixed_process)
            self.assertIn("42000", body)
            mixed_output = wait_for_file_text(
                mixed_log,
                [
                    "scope=adudeck.checkout.business",
                    "scope=opentelemetry.instrumentation.flask",
                ],
                timeout=15,
            )
        finally:
            stop_process(mixed_process)
        mixed_output = mixed_log.read_text(encoding="utf-8")
        mixed_log.unlink(missing_ok=True)

        summaries = [line for line in mixed_output.splitlines() if line.startswith("scope-summary ")]
        business_line = next(
            line for line in summaries if "scope=adudeck.checkout.business" in line
        )
        framework_lines = [
            line for line in summaries if "scope=opentelemetry.instrumentation.flask" in line
        ]
        self.assertEqual(len(framework_lines), 1, mixed_output)

        business = parse_scope_summary(business_line)
        framework = parse_scope_summary(framework_lines[0])
        self.assertEqual(business["trace_id"], framework["trace_id"])
        self.assertEqual(business["parent_id"], framework["span_id"])
        self.assertNotEqual(business["scope"], framework["scope"])

    def test_otlp_http_reaches_collector_and_failure_stays_outside_business_work(self) -> None:
        if shutil.which("docker") is None:
            self.fail("Docker is required for the OpenTelemetry Collector acceptance test")

        info = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(info.returncode, 0, info.stdout + info.stderr)

        pull = subprocess.run(
            ["docker", "pull", COLLECTOR_IMAGE],
            capture_output=True,
            text=True,
            timeout=240,
        )
        self.assertEqual(pull.returncode, 0, pull.stdout + pull.stderr)

        host_port = free_port()
        container_name = f"adudeck-otel-{uuid4().hex[:10]}"
        config = TEXTBOOK / "07-otlp-collector" / "collector-config.yaml"
        try:
            run = subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--rm",
                    "--name",
                    container_name,
                    "-p",
                    f"127.0.0.1:{host_port}:4318",
                    "-v",
                    f"{config.resolve()}:/etc/otelcol/config.yaml:ro",
                    COLLECTOR_IMAGE,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

            deadline = time.monotonic() + 20
            while True:
                try:
                    with socket.create_connection(("127.0.0.1", host_port), timeout=0.5):
                        break
                except OSError:
                    if time.monotonic() >= deadline:
                        logs = subprocess.run(
                            ["docker", "logs", container_name], capture_output=True, text=True
                        )
                        self.fail("Collector did not open OTLP/HTTP port:\n" + logs.stdout + logs.stderr)
                    time.sleep(0.1)

            endpoint = f"http://127.0.0.1:{host_port}/v1/traces"
            success = subprocess.run(
                uv_command(
                    [f"opentelemetry-exporter-otlp-proto-http=={OTEL_EXPORTER_VERSION}"],
                    [
                        "python",
                        str(TEXTBOOK / "07-otlp-collector" / "otlp_trace.py"),
                        "--endpoint",
                        endpoint,
                    ],
                ),
                cwd=DECK,
                env=clean_env(),
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(success.returncode, 0, success.stdout + success.stderr)
            self.assertIn("checkout: business work completed", success.stdout)
            match = re.search(
                r"application trace_id=([0-9a-f]{32}) span_id=([0-9a-f]{16})",
                success.stdout,
            )
            self.assertIsNotNone(match, success.stdout)
            trace_id, span_id = match.groups()

            collector_logs = ""
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                logs = subprocess.run(
                    ["docker", "logs", container_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                collector_logs = (logs.stdout + logs.stderr).lower()
                if trace_id in collector_logs and span_id in collector_logs and "checkout" in collector_logs:
                    break
                time.sleep(0.2)
            self.assertIn(trace_id, collector_logs)
            self.assertIn(span_id, collector_logs)
            self.assertIn("checkout", collector_logs)

            failed_endpoint = f"http://127.0.0.1:{host_port}/not-traces"
            failed = subprocess.run(
                uv_command(
                    [f"opentelemetry-exporter-otlp-proto-http=={OTEL_EXPORTER_VERSION}"],
                    [
                        "python",
                        str(TEXTBOOK / "07-otlp-collector" / "otlp_trace.py"),
                        "--endpoint",
                        failed_endpoint,
                    ],
                ),
                cwd=DECK,
                env=clean_env(),
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(failed.returncode, 0, failed.stdout + failed.stderr)
            self.assertIn("checkout: business work completed", failed.stdout)
            failed_match = re.search(r"application trace_id=([0-9a-f]{32})", failed.stdout)
            self.assertIsNotNone(failed_match, failed.stdout)
            failed_trace_id = failed_match.group(1)

            time.sleep(0.5)
            logs = subprocess.run(
                ["docker", "logs", container_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertNotIn(failed_trace_id, (logs.stdout + logs.stderr).lower())
        finally:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                timeout=20,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
