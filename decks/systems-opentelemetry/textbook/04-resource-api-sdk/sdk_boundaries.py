from collections.abc import Sequence

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)


class BoundarySummaryExporter(SpanExporter):
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            scope = span.instrumentation_scope
            print(
                "boundary-summary",
                f"span={span.name}",
                f"service.name={span.resource.attributes.get('service.name')}",
                f"scope={scope.name if scope is not None else None}",
                f"scope.version={scope.version if scope is not None else None}",
            )
        return SpanExportResult.SUCCESS


resource = Resource.create(
    {
        "service.name": "adudeck-otel-boundaries",
        "service.version": "1.0.0",
    }
)
provider = TracerProvider(resource=resource)
provider.add_span_processor(SimpleSpanProcessor(BoundarySummaryExporter()))
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

checkout_tracer = trace.get_tracer("adudeck.checkout", "1.0.0")
payment_tracer = trace.get_tracer("adudeck.payment", "1.0.0")


if __name__ == "__main__":
    with (
        checkout_tracer.start_as_current_span("checkout"),
        payment_tracer.start_as_current_span("charge_payment"),
    ):
        pass
