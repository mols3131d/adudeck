from pathlib import Path

from pyiceberg.catalog import Catalog, load_catalog

TABLE_ID = "tutorial.orders"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WAREHOUSE_ROOT = PROJECT_ROOT / "warehouse"


def load_lab_catalog() -> Catalog:
    WAREHOUSE_ROOT.mkdir(exist_ok=True)
    return load_catalog(
        "local",
        type="sql",
        uri=f"sqlite:///{WAREHOUSE_ROOT / 'pyiceberg_catalog.db'}",
        warehouse=f"file://{WAREHOUSE_ROOT}",
    )
