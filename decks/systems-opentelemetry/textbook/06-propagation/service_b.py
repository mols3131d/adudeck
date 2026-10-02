import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer

from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import SpanKind


resource = Resource.create({"service.name": "adudeck-service-b"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("adudeck.service_b")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        # HTTP field names are case-insensitive, while a plain dict lookup is not.
        # Normalize the carrier before OpenTelemetry looks up "traceparent".
        carrier = {key.lower(): value for key, value in self.headers.items()}
        context = extract(carrier)
        with tracer.start_as_current_span("service_b.handle", context=context, kind=SpanKind.SERVER) as span:
            ctx = span.get_span_context()
            print(f"service-b trace_id={ctx.trace_id:032x} span_id={ctx.span_id:016x}", flush=True)
            body = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        # SimpleSpanProcessor exported the ended span before this marker is emitted.
        print("service-b request complete", flush=True)

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"service-b listening on http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()
