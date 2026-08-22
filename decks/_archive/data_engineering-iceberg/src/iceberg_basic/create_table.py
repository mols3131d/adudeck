from pyiceberg.schema import Schema
from pyiceberg.types import LongType, NestedField, StringType

from iceberg_basic.catalog import TABLE_ID, load_lab_catalog

catalog = load_lab_catalog()

if ("tutorial",) not in catalog.list_namespaces():
    catalog.create_namespace("tutorial")

table = catalog.create_table(
    TABLE_ID,
    schema=Schema(
        NestedField(1, "order_id", LongType(), required=False),
        NestedField(2, "item", StringType(), required=False),
    ),
)

print(table.schema())
