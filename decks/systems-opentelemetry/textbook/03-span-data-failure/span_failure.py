from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import Status, StatusCode


class InventoryUnavailable(Exception):
    pass


class PaymentDeclined(Exception):
    pass


resource = Resource.create({"service.name": "adudeck-otel-failure"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("adudeck.opentelemetry.failure")


def error_type(exc: Exception) -> str:
    return f"{type(exc).__module__}.{type(exc).__qualname__}"


def reserve_inventory() -> None:
    with tracer.start_as_current_span("reserve_inventory") as span:
        try:
            raise InventoryUnavailable("primary warehouse unavailable")
        except InventoryUnavailable:
            # The internal attempt failed, but this operation recovers successfully.
            span.set_attribute("inventory.fallback_used", True)
            span.set_attribute("inventory.result", "reserved")


def charge_payment(should_fail: bool) -> None:
    with tracer.start_as_current_span("charge_payment") as span:
        span.set_attribute("payment.method", "card")
        if not should_fail:
            span.set_attribute("payment.result", "charged")
            return

        exc = PaymentDeclined("issuer declined payment")
        span.set_attribute("error.type", error_type(exc))
        span.set_status(Status(StatusCode.ERROR, "payment declined"))
        raise exc


def run_checkout(payment_should_fail: bool) -> None:
    with tracer.start_as_current_span("checkout") as span:
        span.set_attribute("checkout.scenario", "failure" if payment_should_fail else "success")
        reserve_inventory()
        try:
            charge_payment(payment_should_fail)
        except PaymentDeclined as exc:
            span.set_attribute("checkout.result", "failed")
            span.set_attribute("error.type", error_type(exc))
            span.set_status(Status(StatusCode.ERROR, "checkout could not complete"))
        else:
            span.set_attribute("checkout.result", "completed")


if __name__ == "__main__":
    print("=== recovered internal error; checkout succeeds ===")
    run_checkout(payment_should_fail=False)
    print("=== final payment failure; checkout fails ===")
    run_checkout(payment_should_fail=True)
