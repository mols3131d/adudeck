import argparse
from urllib.request import Request, urlopen

from opentelemetry import trace
from opentelemetry.propagate import inject
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import SpanKind


resource = Resource.create({"service.name": "adudeck-service-a"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("adudeck.service_a")


def main(drop_context: bool) -> None:
    with tracer.start_as_current_span("service_a.call_b", kind=SpanKind.CLIENT) as span:
        headers: dict[str, str] = {}
        if not drop_context:
            inject(headers)
        print(f"traceparent={headers.get('traceparent', '<not injected>')}")
        ctx = span.get_span_context()
        print(f"service-a trace_id={ctx.trace_id:032x} span_id={ctx.span_id:016x}")
        request = Request("http://127.0.0.1:8090/", headers=headers)
        with urlopen(request, timeout=3) as response:
            print(f"response={response.read().decode().strip()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--drop-context", action="store_true")
    args = parser.parse_args()
    main(args.drop_context)
