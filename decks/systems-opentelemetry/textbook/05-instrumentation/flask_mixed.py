import argparse
from collections.abc import Sequence

from flask import Flask
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult


class ScopeSummaryExporter(SpanExporter):
    """Teaching probe that exposes Instrumentation Scope for each finished span."""

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            scope = span.instrumentation_scope
            print(
                "scope-summary",
                f"span={span.name}",
                f"scope={scope.name if scope else '<none>'}",
                f"scope.version={scope.version if scope and scope.version else '<none>'}",
                flush=True,
            )
        return SpanExportResult.SUCCESS


app = Flask(__name__)
provider = trace.get_tracer_provider()
if isinstance(provider, TracerProvider):
    provider.add_span_processor(SimpleSpanProcessor(ScopeSummaryExporter()))

tracer = trace.get_tracer("adudeck.checkout.business", "1.0.0")


@app.get("/checkout")
def checkout() -> dict[str, int]:
    with tracer.start_as_current_span("checkout.calculate_total") as span:
        span.set_attribute("cart.item_count", 2)
        return {"total": 42000}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8087)
    args = parser.parse_args()
    app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
