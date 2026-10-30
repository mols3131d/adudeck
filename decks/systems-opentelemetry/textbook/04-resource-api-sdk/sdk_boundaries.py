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
    def export(self, spans: tuple[ReadableSpan, ...]) -> SpanExportResult:
        for span in spans:
            print(
                "boundary-summary",
                f"span={span.name}",
                f"service.name={span.resource.attributes.get('service.name')}",
                f"scope={span.instrumentation_scope.name}",
                f"scope.version={span.instrumentation_scope.version}",
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
    with checkout_tracer.start_as_current_span("checkout"):
        with payment_tracer.start_as_current_span("charge_payment"):
            pass
