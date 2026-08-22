# Apache Iceberg 직접 구현 실습 시작하기

## Overview

이 교재에서는 PyIceberg로 테이블 생성, append, Time Travel, schema evolution 코드를 직접 작성합니다. 제공 스크립트는 초기화와 관찰만 담당합니다.

## 학습 목표

완주 후 다음을 코드와 자신의 말로 설명할 수 있어야 합니다.

- Parquet와 Iceberg가 담당하는 문제가 어떻게 다른가?
- Catalog 설정은 테이블 이름을 어느 warehouse와 metadata에 연결하는가?
- 테이블 생성과 append는 각각 어떤 파일을 만드는가?
- snapshot ID를 지정하면 왜 과거 행 집합을 읽을 수 있는가?
- 컬럼 추가가 기존 Parquet 파일을 즉시 다시 쓰지 않는 이유는 무엇인가?

## 제공 도구와 학습자 코드의 경계

| 구분 | 위치 | 책임 |
| --- | --- | --- |
| 제공 도구 | `scripts/reset_lab.py` | `warehouse/` 초기화 |
| 제공 도구 | `scripts/inspect_lab.py` | 현재 상태와 파일 한 번 조회 |
| 제공 도구 | `scripts/watch_lab.py` | 현재 상태 반복 관찰 |
| 학습자 코드 | `src/iceberg_basic/*.py` | Catalog 설정, create, append, Time Travel, schema evolution |

`reset`, `status`, `watch`는 학습 보조 작업입니다. Iceberg의 상태를 바꾸는 핵심 작업은 `src/iceberg_basic/`에 직접 작성합니다. 이 디렉터리는 `pyproject.toml`에 등록된 설치 가능한 Python 패키지입니다.

## 정확한 시작 상태

- Python 3.13 이상과 `uv`가 설치되어 있습니다.
- 현재 위치로 이동하면 `pyproject.toml`, `src/`, `scripts/`, `textbook/`이 보입니다.
- `warehouse/`는 없거나 이전 실습 결과가 들어 있을 수 있습니다.

## 정확한 완료 상태

- 직접 작성한 `src/iceberg_basic/catalog.py`, `create_table.py`, `append_first.py`, `append_second.py`, `time_travel.py`, `evolve_schema.py`가 있습니다.
- `warehouse/pyiceberg_catalog.db`와 `warehouse/tutorial/orders/` 아래에 Catalog, Iceberg metadata와 Parquet 파일이 있습니다.
- `tutorial.orders`는 3행, 2개 snapshot, `order_id`, `item`, `channel` schema를 가집니다.
- 첫 snapshot을 지정해 읽으면 2행이 나옵니다.

## 준비

저장소 루트에서 다음을 실행합니다. 이후 모든 명령은 `projects/iceberg_basic`에서 실행합니다.

```bash
cd projects/iceberg_basic
uv sync
uv run python scripts/reset_lab.py
uv run python scripts/inspect_lab.py
```

- **Action:** 의존성과 로컬 `iceberg_basic` 패키지를 설치한 뒤 과거 Iceberg 상태를 제거합니다.
- **Change:** `.venv/`가 준비되고 `warehouse/`는 제거됩니다. `src/`의 코드는 변경되지 않습니다.
- **Verify:** 마지막 상태 출력이 `table : 없음`이고 `files:` 아래가 비어 있어야 합니다.

선택 사항으로 두 번째 터미널에서 관찰기를 실행할 수 있습니다.

```bash
cd projects/iceberg_basic
uv run python scripts/watch_lab.py
```

- **Action:** 현재 상태를 반복해서 읽습니다.
- **Change:** 없음. 종료는 `Ctrl+C`입니다.
- **Verify:** 학습자 코드를 실행한 직후에만 schema, snapshot, rows, files가 달라져야 합니다.

## 범위와 버전

이 교재는 `pyiceberg>=0.11,<0.12` API를 대상으로 합니다. 로컬 SQLite Catalog와 파일시스템으로 핵심 구조만 확인하며, 다중 writer, REST Catalog, 객체 저장소, 인증은 검증하지 않습니다.

## Checklist

- [ ] 제공 스크립트와 직접 작성할 코드의 책임을 구분할 수 있다.
- [ ] `src/iceberg_basic/` 패키지와 초기화된 빈 `warehouse/` 상태를 확인했다.
- [ ] 이후 모든 명령을 `projects/iceberg_basic`에서 실행한다.
