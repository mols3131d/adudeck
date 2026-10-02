from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


resource = Resource.create({"service.name": "adudeck-otel-otlp"})
provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:4318/v1/traces")
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("adudeck.otlp")


if __name__ == "__main__":
    with tracer.start_as_current_span("checkout") as span:
        span.set_attribute("checkout.currency", "KRW")
        print("checkout: business work completed")
    provider.shutdown()
