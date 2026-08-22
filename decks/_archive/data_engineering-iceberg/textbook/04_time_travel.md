# 04. snapshot ID로 과거 데이터 읽기

## Summary

학습자가 snapshot ID를 가져와 `table.scan(snapshot_id=...)`에 직접 전달합니다. Time Travel은 현재 상태를 바꾸지 않고
과거 snapshot의 파일 집합을 읽습니다.

## 현재와 과거

```text
Snapshot S1: file A       → order 1, 2
       │ append file B
       ▼
Snapshot S2: file A + B   → order 1, 2, 3 (current)
```

## 1. Time Travel 코드 작성

`src/iceberg_basic/time_travel.py`를 만듭니다.

```python
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
```

## 2. 실행 전후 비교

```bash
uv run python scripts/inspect_lab.py
uv run python -m iceberg_basic.time_travel
uv run python scripts/inspect_lab.py
```

- **Action:** 첫 snapshot ID를 지정한 scan과 현재 scan을 실행합니다.
- **Change:** 없음. 읽기만 수행합니다.
- **Verify:** 첫 결과는 2행, 현재 결과는 3행이며 전후 snapshot ID와 파일 목록이 같아야 합니다.

## Time Travel과 rollback

| 작업 | 현재 metadata 변경 | 결과 |
| --- | --- | --- |
| Time Travel | 없음 | 선택한 과거 상태를 읽음 |
| Rollback | 있음 | 과거 snapshot을 다시 현재 상태로 지정 |

과거 snapshot과 참조 파일을 만료하거나 삭제하면 해당 시점은 더 이상 읽을 수 없습니다.

## Checklist

- [ ] snapshot ID를 코드에서 직접 가져왔다.
- [ ] `scan(snapshot_id=...)`와 현재 `scan()` 결과를 비교했다.
- [ ] Time Travel 전후에 테이블 상태가 변하지 않은 것을 확인했다.
- [ ] Time Travel과 rollback을 상태 변경 여부로 구분할 수 있다.
