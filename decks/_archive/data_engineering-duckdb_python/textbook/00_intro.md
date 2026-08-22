# Python DuckDB Tutorial 소개

## 목표

이 교재는 Python과 DuckDB를 이용해 로컬에서 재현 가능한 분석 및 데이터 처리 흐름을 구현한다. SQL 문법 자체보다 Python
application 안에서 DuckDB를 안전하게 연결하고 파일, DataFrame, table, transaction을 다루는 방법에 초점을 둔다.

## 시작 상태

학습 시작 시 다음만 준비되어 있다고 가정한다.

```text
현재 파일
└── 없음

현재 환경
├── Python 3.11 이상
├── 터미널 사용 가능
└── SQL SELECT 문에 대한 기초 지식
```

DuckDB, Pandas, PyArrow, pytest는 아직 설치되지 않았고 database 파일도 없다.

## 종료 상태

학습 종료 시 다음 결과물을 갖는다.

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
│       ├── __init__.py
│       ├── connection.py
│       ├── ingestion.py
│       ├── profiling.py
│       └── pipeline.py
├── tests/
│   ├── test_ingestion.py
│   └── test_profiling.py
└── warehouse.duckdb
```

다음 동작을 직접 확인한다.

- Python에서 DuckDB SQL 실행
- CSV와 Parquet 직접 조회
- Polars DataFrame 등록 및 조회
- table과 view 생성
- transaction 기반 partition overwrite
- profile snapshot 계산
- ETL 결과 Parquet export
- pytest 기반 반복 실행 검증

## 사전 지식

- Python 함수와 context manager 기초
- `pathlib.Path` 사용법
- SQL의 `SELECT`, `WHERE`, `GROUP BY`
- 가상환경 또는 `uv` 사용 경험

## 실습 원칙

각 실습은 다음 순서를 따른다.

1. **Action**: 실행할 명령이나 코드를 작성한다.
2. **Change**: 파일, table, database 상태가 어떻게 바뀌는지 확인한다.
3. **Verify**: query 결과나 test로 변화를 검증한다.

## 프로젝트 생성

### Action

```bash
mkdir duckdb-tutorial
cd duckdb-tutorial
uv init
uv add duckdb polars pyarrow
uv add --dev pytest marimo
mkdir -p data output src/duckdb_python_basic tests
touch src/duckdb_python_basic/__init__.py
```

### Change

```text
duckdb-python-basic/
├── pyproject.toml
├── data/
├── output/
├── src/
│   └── duckdb_python_basic/
│       └── __init__.py
└── tests/
```

### Verify

```bash
uv run python -c "import duckdb; print(duckdb.__version__)"
```

버전 문자열이 출력되면 환경 구성이 완료된 것이다.
