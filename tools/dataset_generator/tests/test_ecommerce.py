from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from adudeck_data import generate_ecommerce

EXPECTED_FIELDS = {
    "users": ["user_id", "name", "email", "city", "created_at"],
    "products": ["product_id", "name", "category", "price"],
    "orders": ["order_id", "user_id", "status", "created_at", "total_amount"],
    "order_items": ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
}


class GenerateEcommerceTest(unittest.TestCase):
    def test_generates_related_rows_with_expected_invariants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = generate_ecommerce(tmp, users=5, products=4, orders=10, seed=7)

            users = _read_csv(paths["users"])
            products = _read_csv(paths["products"])
            orders = _read_csv(paths["orders"])
            items = _read_csv(paths["order_items"])

            self.assertEqual(len(users), 5)
            self.assertEqual(len(products), 4)
            self.assertEqual(len(orders), 10)
            self.assertGreaterEqual(len(items), 10)

            users_by_id = {row["user_id"]: row for row in users}
            product_ids = {row["product_id"] for row in products}
            order_ids = {row["order_id"] for row in orders}

            totals = {order_id: Decimal("0") for order_id in order_ids}
            item_counts = {order_id: 0 for order_id in order_ids}
            for item in items:
                self.assertIn(item["order_id"], order_ids)
                self.assertIn(item["product_id"], product_ids)
                totals[item["order_id"]] += Decimal(item["unit_price"]) * int(item["quantity"])
                item_counts[item["order_id"]] += 1

            for order in orders:
                user = users_by_id[order["user_id"]]
                self.assertLessEqual(
                    datetime.fromisoformat(user["created_at"]),
                    datetime.fromisoformat(order["created_at"]),
                )
                self.assertGreaterEqual(item_counts[order["order_id"]], 1)
                self.assertEqual(Decimal(order["total_amount"]), totals[order["order_id"]])

    def test_preserves_documented_csv_schema_and_primary_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = generate_ecommerce(tmp, users=5, products=4, orders=10, seed=13)

            for name, expected_fields in EXPECTED_FIELDS.items():
                with self.subTest(name=name):
                    with paths[name].open(encoding="utf-8", newline="") as handle:
                        reader = csv.DictReader(handle)
                        self.assertEqual(reader.fieldnames, expected_fields)
                        rows = list(reader)

                    primary_key = expected_fields[0]
                    self.assertEqual(len(rows), len({row[primary_key] for row in rows}))

    def test_same_seed_generates_identical_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            first_paths = generate_ecommerce(first, users=5, products=4, orders=10, seed=11)
            second_paths = generate_ecommerce(second, users=5, products=4, orders=10, seed=11)

            for name in first_paths:
                self.assertEqual(first_paths[name].read_bytes(), second_paths[name].read_bytes())

    def test_rejects_non_positive_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("users", "products", "orders"):
                kwargs = {"users": 1, "products": 1, "orders": 1, name: 0}
                with self.subTest(name=name):
                    with self.assertRaises(ValueError):
                        generate_ecommerce(tmp, **kwargs)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
