from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator


class SyntheticErrorServer:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        self.request_count = 0
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        if self._server is None:
            raise RuntimeError("server is not running")
        host, port = self._server.server_address
        return f"http://{host}:{port}/v1"

    def start(self) -> None:
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                owner.request_count += 1

                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length:
                    self.rfile.read(content_length)

                body = json.dumps(
                    {
                        "error": {
                            "message": f"synthetic lab error {owner.status_code}",
                            "type": "adudeck_lab_error",
                            "param": None,
                            "code": "synthetic_error",
                        }
                    }
                ).encode("utf-8")

                self.send_response(owner.status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("x-request-id", f"req_adudeck_{owner.request_count}")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)


@contextmanager
def synthetic_error_server(status_code: int) -> Iterator[SyntheticErrorServer]:
    server = SyntheticErrorServer(status_code)
    server.start()
    try:
        yield server
    finally:
        server.close()
