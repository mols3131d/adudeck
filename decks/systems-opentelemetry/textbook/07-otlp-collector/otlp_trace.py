import argparse

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def main(endpoint: str) -> None:
    resource = Resource.create({"service.name": "adudeck-otel-otlp"})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("adudeck.otlp")

    with tracer.start_as_current_span("checkout") as span:
        span.set_attribute("checkout.currency", "KRW")
        ctx = span.get_span_context()
        print(f"application trace_id={ctx.trace_id:032x} span_id={ctx.span_id:016x}")
        print(f"application endpoint={endpoint}")
        print("checkout: business work completed")

    provider.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://127.0.0.1:4318/v1/traces")
    args = parser.parse_args()
    main(args.endpoint)
