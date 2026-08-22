from pyiceberg.types import StringType

from iceberg_basic.catalog import TABLE_ID, load_lab_catalog

catalog = load_lab_catalog()
table = catalog.load_table(TABLE_ID)

with table.update_schema() as update:
    update.add_column("channel", StringType())

table.refresh()
print(table.schema())
