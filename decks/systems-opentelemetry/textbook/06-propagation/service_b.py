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
        carrier = {key: value for key, value in self.headers.items()}
        context = extract(carrier)
        with tracer.start_as_current_span("service_b.handle", context=context, kind=SpanKind.SERVER) as span:
            ctx = span.get_span_context()
            print(f"service-b trace_id={ctx.trace_id:032x} span_id={ctx.span_id:016x}")
            body = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    print("service-b listening on http://127.0.0.1:8090")
    HTTPServer(("127.0.0.1", 8090), Handler).serve_forever()
