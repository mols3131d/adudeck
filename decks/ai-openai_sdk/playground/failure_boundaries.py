# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=3,<4",
# ]
# ///

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, ClassVar

DEFAULT_MODEL = "gpt-5.6-luna"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Observe OpenAI Python SDK status-error classification and automatic retry "
            "against a local synthetic HTTP endpoint."
        )
    )
    parser.add_argument(
        "--status",
        type=int,
        choices=[400, 429, 500],
        default=429,
        help="Synthetic HTTP status returned by the local lab server.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="SDK max_retries passed to OpenAI().",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the experiment plan without importing the SDK or starting a server.",
    )
    return parser.parse_args()


def experiment_plan(status: int, max_retries: int) -> dict[str, Any]:
    retriable_by_default = status in {429, 500}
    return {
        "synthetic_status": status,
        "client_max_retries": max_retries,
        "default_retry_class_for_this_status": retriable_by_default,
        "predicted_request_count_if_every_attempt_gets_same_status": (
            1 + max_retries if retriable_by_default else 1
        ),
        "validation_boundary": (
            "local synthetic HTTP endpoint: validates SDK retry/error behavior, "
            "not OpenAI API availability or server-side behavior"
        ),
    }


class SyntheticErrorHandler(BaseHTTPRequestHandler):
    status_code: ClassVar[int] = 429
    request_count: ClassVar[int] = 0

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        type(self).request_count += 1
        request_number = type(self).request_count

        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length:
            self.rfile.read(content_length)

        payload = {
            "error": {
                "message": f"synthetic lab error {self.status_code}",
                "type": "adudeck_lab_error",
                "param": None,
                "code": "synthetic_error",
            }
        }
        body = json.dumps(payload).encode("utf-8")

        self.send_response(self.status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("x-request-id", f"req_adudeck_{request_number}")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    args = parse_args()
    plan = experiment_plan(args.status, args.max_retries)

    print("== experiment plan ==")
    print(json.dumps(plan, ensure_ascii=False, indent=2))

    if args.preview:
        print("\npreview only: no SDK import, local server, or HTTP request occurred")
        return

    import openai
    from openai import OpenAI

    SyntheticErrorHandler.status_code = args.status
    SyntheticErrorHandler.request_count = 0

    server = ThreadingHTTPServer(("127.0.0.1", 0), SyntheticErrorHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    client = OpenAI(
        api_key="adudeck-local-synthetic-key",
        base_url=f"http://{host}:{port}/v1",
        max_retries=args.max_retries,
        timeout=5.0,
    )

    try:
        client.responses.create(model=DEFAULT_MODEL, input="synthetic local failure experiment")
    except openai.APIStatusError as exc:
        print("\n== observed SDK exception ==")
        print(f"python_type: {type(exc).__name__}")
        print(f"status_code: {exc.status_code}")
        print(f"request_id: {exc.request_id}")
        print(f"request_count: {SyntheticErrorHandler.request_count}")
        print(f"is_rate_limit_error: {isinstance(exc, openai.RateLimitError)}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
