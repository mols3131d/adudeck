from __future__ import annotations

import csv
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from faker import Faker

BASE_TIME = datetime(2025, 1, 1, tzinfo=UTC)
CATEGORIES = ("books", "electronics", "home", "office", "sports")
ORDER_STATUSES = ("paid", "shipped", "completed")


def generate_ecommerce(
    output: str | Path,
    *,
    users: int = 100,
    products: int = 50,
    orders: int = 500,
    seed: int = 42,
) -> dict[str, Path]:
    """Generate one deterministic ecommerce dataset as four related CSV files."""
    _require_positive("users", users)
    _require_positive("products", products)
    _require_positive("orders", orders)

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    fake = Faker("en_US")
    fake.seed_instance(seed)

    user_rows = _build_users(fake, rng, users)
    product_rows = _build_products(fake, rng, products)
    order_rows, order_item_rows = _build_orders(rng, user_rows, product_rows, orders)

    paths = {
        "users": output_dir / "users.csv",
        "products": output_dir / "products.csv",
        "orders": output_dir / "orders.csv",
        "order_items": output_dir / "order_items.csv",
    }

    _write_csv(paths["users"], user_rows)
    _write_csv(paths["products"], product_rows)
    _write_csv(paths["orders"], order_rows)
    _write_csv(paths["order_items"], order_item_rows)
    return paths


def _build_users(fake: Faker, rng: random.Random, count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(1, count + 1):
        created_at = BASE_TIME + timedelta(
            days=rng.randint(0, 30),
            seconds=rng.randint(0, 86_399),
        )
        rows.append(
            {
                "user_id": f"user_{index:06d}",
                "name": fake.name(),
                "email": fake.unique.email(),
                "city": fake.city(),
                "created_at": _iso(created_at),
            }
        )
    return rows


def _build_products(fake: Faker, rng: random.Random, count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(1, count + 1):
        price = Decimal(rng.randint(500, 50_000)) / 100
        rows.append(
            {
                "product_id": f"product_{index:05d}",
                "name": f"{fake.word().title()} {fake.word().title()}",
                "category": rng.choice(CATEGORIES),
                "price": _money(price),
            }
        )
    return rows


def _build_orders(
    rng: random.Random,
    users: list[dict[str, Any]],
    products: list[dict[str, Any]],
    count: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    orders: list[dict[str, Any]] = []
    order_items: list[dict[str, Any]] = []
    next_item_id = 1

    for index in range(1, count + 1):
        user = rng.choice(users)
        created_at = datetime.fromisoformat(user["created_at"]) + timedelta(
            days=rng.randint(0, 90),
            seconds=rng.randint(0, 86_399),
        )
        item_count = rng.randint(1, min(4, len(products)))
        selected_products = rng.sample(products, k=item_count)
        total = Decimal("0")
        order_id = f"order_{index:07d}"

        for product in selected_products:
            quantity = rng.randint(1, 5)
            unit_price = Decimal(product["price"])
            total += unit_price * quantity
            order_items.append(
                {
                    "order_item_id": f"item_{next_item_id:08d}",
                    "order_id": order_id,
                    "product_id": product["product_id"],
                    "quantity": quantity,
                    "unit_price": _money(unit_price),
                }
            )
            next_item_id += 1

        orders.append(
            {
                "order_id": order_id,
                "user_id": user["user_id"],
                "status": rng.choice(ORDER_STATUSES),
                "created_at": _iso(created_at),
                "total_amount": _money(total),
            }
        )

    return orders, order_items


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty dataset: {path.name}")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _require_positive(name: str, value: int) -> None:
    if value < 1:
        raise ValueError(f"{name} must be at least 1")


def _money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")
