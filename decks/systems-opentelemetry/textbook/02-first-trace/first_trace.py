from time import sleep

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

resource = Resource.create({"service.name": "adudeck-otel-first-trace"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("adudeck.opentelemetry.first_trace")


def validate_cart() -> None:
    with tracer.start_as_current_span("validate_cart") as span:
        span.set_attribute("cart.item_count", 2)
        sleep(0.02)
        print("validate_cart: ok")


def charge_payment() -> None:
    with tracer.start_as_current_span("charge_payment") as span:
        span.set_attribute("payment.method", "card")
        sleep(0.03)
        print("charge_payment: ok")


def checkout() -> None:
    with tracer.start_as_current_span("checkout") as span:
        span.set_attribute("checkout.currency", "KRW")
        validate_cart()
        charge_payment()


if __name__ == "__main__":
    checkout()
