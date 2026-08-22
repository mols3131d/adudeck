# Python DuckDB Tutorial Roadmap

Python에서 DuckDB를 사용해 로컬 분석과 재현 가능한 데이터 처리 파이프라인을 구축한다.

## 학습 경로

- [ ] [01. DuckDB와 실행 환경](01_duckdb_environment.md)
- [ ] [02. Connection과 SQL 실행](02_connection_and_sql.md)
- [ ] [03. Query 결과 처리](03_query_results.md)
- [ ] [04. CSV와 Parquet 조회](04_csv_and_parquet.md)
- [ ] [05. Polars DataFrame 연동](05_polars_integration.md)
- [ ] [06. Table과 View 관리](06_tables_and_views.md)
- [ ] [07. Parameter Binding과 안전한 SQL](07_parameter_binding.md)
- [ ] [08. Transaction과 Idempotent Ingestion](08_transactions_and_ingestion.md)
- [ ] [09. Profiling과 데이터 품질 검사](09_profiling_and_quality.md)
- [ ] [10. 실전 ETL Mini Project](10_etl_mini_project.md)
- [ ] [11. 테스트와 운영 패턴](11_testing_and_operations.md)

## 보조 문서

- [시작 안내](00_intro.md)
- [최종 점검과 다음 단계](99_outro.md)

## 최종 결과물

학습 완료 후 다음 파일과 동작을 갖는다.

```text
duckdb-python-basic/
├── pyproject.toml
├── data/
│   ├── users.csv
│   └── trips.parquet
├── output/
│   └── daily_trip_metrics.parquet
├── src/
│   └── duckdb_python_basic/
│       ├── connection.py
│       ├── ingestion.py
│       ├── profiling.py
│       └── pipeline.py
├── tests/
│   ├── test_ingestion.py
│   └── test_profiling.py
└── warehouse.duckdb
```

## 완료 기준

- [ ] Python에서 in-memory DuckDB connection을 생성할 수 있다.
- [ ] 파일 기반 DuckDB database를 생성하고 다시 열 수 있다.
- [ ] CSV와 Parquet를 table 적재 없이 SQL로 조회할 수 있다.
- [ ] Polars DataFrame을 DuckDB SQL에서 조회할 수 있다.
- [ ] parameter binding으로 값을 안전하게 전달할 수 있다.
- [ ] transaction으로 partition overwrite를 원자적으로 실행할 수 있다.
- [ ] profile query로 row count, null rate, freshness를 계산할 수 있다.
- [ ] ETL 결과를 Parquet로 저장하고 pytest로 검증할 수 있다.
