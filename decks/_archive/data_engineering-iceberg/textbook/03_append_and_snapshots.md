# 03. 데이터를 직접 append하고 snapshot 확인하기

## Summary

CSV를 미리 Parquet로 변환하지 않습니다. 학습자가 Arrow Table을 만들고 `table.append()`를 호출하면 PyIceberg가 관리 대상 Parquet와 snapshot metadata를 함께 커밋합니다.

## Append 메커니즘

```text
Arrow Table
    ↓ table.append()
새 Parquet data file 작성
    ↓
manifest와 manifest list 작성
    ↓
새 snapshot을 포함한 metadata 커밋
```

직접 만든 Parquet 파일을 warehouse에 복사하는 것만으로는 Iceberg 테이블에 포함되지 않습니다. manifest와 snapshot을 통해 참조되어야 합니다.

## 1. 첫 append 코드 작성

`src/iceberg_basic/append_first.py`를 만듭니다.

```python
import pyarrow as pa

from iceberg_basic.catalog import TABLE_ID, load_lab_catalog

catalog = load_lab_catalog()
table = catalog.load_table(TABLE_ID)
rows = pa.table(
    {
        "order_id": pa.array([1, 2], type=pa.int64()),
        "item": pa.array(["book", "pen"], type=pa.string()),
    }
)

table.append(rows)
table.refresh()
print([snapshot.snapshot_id for snapshot in table.snapshots()])
```

실행하고 즉시 상태를 확인합니다.

```bash
uv run python -m iceberg_basic.append_first
uv run python scripts/inspect_lab.py
```

- **Action:** Arrow Table의 주문 2행을 append합니다.
- **Change:** 첫 Parquet, manifest, manifest list, snapshot과 새 metadata가 생성됩니다.
- **Verify:** 행은 2개, snapshot은 1개, `.parquet` 파일은 1개여야 합니다.

## 2. 두 번째 append 코드 작성

`src/iceberg_basic/append_second.py`를 만듭니다.

```python
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
```

```bash
uv run python -m iceberg_basic.append_second
uv run python scripts/inspect_lab.py
```

- **Action:** 주문 1행을 추가로 append합니다.
- **Change:** 두 번째 Parquet와 두 번째 snapshot 계층이 생기고 첫 Parquet는 유지됩니다.
- **Verify:** 행은 3개, snapshot은 2개, `.parquet` 파일은 2개여야 합니다.

## 파일 이름 해석

| 파일 | 역할 |
| --- | --- |
| `data/*.parquet` | 실제 주문 행 |
| `metadata/*-m0.avro` | data file 경로와 통계를 가진 manifest |
| `metadata/snap-*.avro` | snapshot의 manifest 목록 |
| `metadata/*.metadata.json` | schema, snapshot 이력, 현재 snapshot |

## 흔한 실수

- append 파일을 다시 실행하면 같은 행이 중복됩니다. 잘못 실행했다면 reset 후 2장부터 다시 진행합니다.
- Arrow 컬럼 타입이 Iceberg schema와 맞지 않으면 append가 실패합니다.
- snapshot은 전체 행의 복사본이 아니라 그 시점에 유효한 파일 집합을 가리킵니다.

## Checklist

- [ ] `table.append()`에 전달할 Arrow Table을 직접 만들었다.
- [ ] 첫 append가 Parquet와 snapshot을 함께 만든 것을 확인했다.
- [ ] 두 번째 snapshot이 첫 data file을 재사용하는 이유를 설명할 수 있다.
- [ ] warehouse에 Parquet만 복사하는 것과 Iceberg append의 차이를 설명할 수 있다.
