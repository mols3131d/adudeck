from iceberg_basic.catalog import TABLE_ID, load_lab_catalog

catalog = load_lab_catalog()
table = catalog.load_table(TABLE_ID)
snapshots = list(table.snapshots())

if len(snapshots) != 2:
    raise RuntimeError(f"snapshot 2개가 필요합니다: {len(snapshots)}개 발견")

first_snapshot_id = snapshots[0].snapshot_id
current_snapshot_id = snapshots[-1].snapshot_id

first_rows = table.scan(snapshot_id=first_snapshot_id).to_arrow().to_pylist()
current_rows = table.scan().to_arrow().to_pylist()

print(f"first   {first_snapshot_id}: {first_rows}")
print(f"current {current_snapshot_id}: {current_rows}")
