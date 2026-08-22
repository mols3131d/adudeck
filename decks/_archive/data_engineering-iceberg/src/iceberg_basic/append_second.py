import pyarrow as pa

from iceberg_basic.catalog import TABLE_ID, load_lab_catalog

catalog = load_lab_catalog()
table = catalog.load_table(TABLE_ID)
rows = pa.table(
    {
        "order_id": pa.array([3], type=pa.int64()),
        "item": pa.array(["cup"], type=pa.string()),
    }
)

table.append(rows)
table.refresh()
print([snapshot.snapshot_id for snapshot in table.snapshots()])
