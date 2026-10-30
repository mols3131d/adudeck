from time import sleep

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


reader = PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=500)
provider = MeterProvider(
    resource=Resource.create({"service.name": "adudeck-otel-metrics"}),
    metric_readers=[reader],
)
metrics.set_meter_provider(provider)
meter = metrics.get_meter("adudeck.checkout", "1.0.0")

requests = meter.create_counter("checkout.requests", unit="{request}")
active = meter.create_up_down_counter("checkout.active", unit="{request}")
duration = meter.create_histogram("checkout.duration", unit="s")


def checkout(seconds: float, payment_method: str) -> None:
    attrs = {"payment.method": payment_method}
    requests.add(1, attrs)
    active.add(1, attrs)
    try:
        sleep(seconds)
        duration.record(seconds, attrs)
    finally:
        active.add(-1, attrs)


if __name__ == "__main__":
    checkout(0.02, "card")
    checkout(0.04, "card")
    checkout(0.03, "bank_transfer")
    provider.force_flush()
    provider.shutdown()
