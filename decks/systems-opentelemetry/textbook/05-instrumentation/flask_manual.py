import argparse

from flask import Flask
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor


app = Flask(__name__)
resource = Resource.create({"service.name": "adudeck-otel-manual"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("adudeck.checkout.business", "1.0.0")


@app.get("/checkout")
def checkout() -> dict[str, int]:
    with tracer.start_as_current_span("checkout.calculate_total") as span:
        span.set_attribute("cart.item_count", 2)
        return {"total": 42000}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8085)
    args = parser.parse_args()
    app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
