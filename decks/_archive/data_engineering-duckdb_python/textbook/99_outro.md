# Python DuckDB Tutorial 마무리

## Retrospective

이 교재에서는 Python 내부에서 DuckDB를 실행하는 기본 mechanics부터 파일 query, DataFrame integration, table 관리, transaction, idempotent ingestion, profiling, ETL test까지 연결했다.

완성된 흐름은 다음과 같다.

```text
CSV / Parquet / DataFrame
          ↓
     DuckDB SQL
          ↓
   Staging / Table
          ↓
 Profile / Validation
          ↓
 Transactional ETL
          ↓
 Parquet Output
          ↓
       pytest
```

## 최종 검증

### Environment

- [ ] `uv run python -c "import duckdb; import polars"`가 성공한다.
- [ ] `uv run pytest -q`가 성공한다.

### Files

- [ ] `warehouse.duckdb`가 존재한다.
- [ ] `data/users.csv`가 존재한다.
- [ ] `data/trips.parquet`가 존재한다.
- [ ] `output/daily_trip_metrics.parquet`가 존재한다.

### DuckDB Mechanics

- [ ] in-memory와 파일 database를 구분한다.
- [ ] `execute()`와 `sql()`의 차이를 설명할 수 있다.
- [ ] relation을 DataFrame 또는 Arrow로 변환할 수 있다.
- [ ] `read_csv`와 `read_parquet`를 사용할 수 있다.
- [ ] table, view, temporary view의 lifecycle을 구분한다.

### Reliability

- [ ] parameter binding을 사용한다.
- [ ] transaction 실패 시 rollback한다.
- [ ] partition overwrite를 반복 실행해도 중복이 없다.
- [ ] row count와 null rate를 검증한다.
- [ ] schema drift를 명시적으로 감지한다.
- [ ] test fixture가 독립 database를 사용한다.

## 다음 단계

1. dbt-duckdb를 연결해 SQL model과 test를 관리한다.
2. Dagster asset으로 partition ingestion과 backfill을 orchestration한다.
3. Parquet 대신 Iceberg metadata를 추가해 snapshot과 schema evidence를 관리한다.
4. Profile snapshot을 저장하고 baseline 비교 detector를 구현한다.
5. dbt artifact의 lineage를 읽어 downstream impact를 계산한다.

## 최종 실행 명령

```bash
uv run python -m duckdb_python_basic.pipeline
uv run pytest -q
```

두 명령이 모두 성공하고 output Parquet의 metric이 예상과 일치하면 tutorial을 완료한 것이다.
