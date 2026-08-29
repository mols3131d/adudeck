from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .ecommerce import generate_ecommerce


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate" and args.scenario == "ecommerce":
        try:
            paths = generate_ecommerce(
                args.output,
                users=args.users,
                products=args.products,
                orders=args.orders,
                seed=args.seed,
            )
        except ValueError as error:
            parser.error(str(error))

        for name, path in paths.items():
            print(f"{name}: {path}")
        return 0

    parser.error("unsupported command")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="adudeck-data",
        description="Generate reproducible datasets for adudeck learning exercises.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="generate a dataset")
    scenarios = generate.add_subparsers(dest="scenario", required=True)

    ecommerce = scenarios.add_parser("ecommerce", help="generate ecommerce CSV files")
    ecommerce.add_argument("--output", type=Path, default=Path("data"))
    ecommerce.add_argument("--users", type=int, default=100)
    ecommerce.add_argument("--products", type=int, default=50)
    ecommerce.add_argument("--orders", type=int, default=500)
    ecommerce.add_argument("--seed", type=int, default=42)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
