# Apache Iceberg 직접 구현 실습 로드맵

이 교재의 목표는 준비된 명령을 실행하는 것이 아니라, PyIceberg 코드를 직접 작성하고 그 코드가 만든 metadata와 Parquet 파일을 확인하는 것입니다.

## Main Chapters

- [x] [01. 왜 Iceberg가 필요한가](01_why_iceberg.md)
- [x] [02. Catalog와 테이블 직접 만들기](02_create_table.md)
- [x] [03. 데이터를 직접 append하고 snapshot 확인하기](03_append_and_snapshots.md)
- [x] [04. snapshot ID로 과거 데이터 읽기](04_time_travel.md)
- [x] [05. schema를 직접 변경하기](05_schema_evolution.md)
- [x] [06. 생성된 증거로 운영 비용 판단하기](06_operations_and_tradeoffs.md)

## 학습 흐름

```text
파일 형식과 테이블 포맷 구분
              ↓
src layout 패키지에서 Catalog 모듈 작성
              ↓
Catalog 설정과 빈 테이블 생성 코드 작성
              ↓
Arrow 데이터 append 코드 작성
              ↓
snapshot ID를 지정한 읽기 코드 작성
              ↓
field ID 기반 schema 변경 코드 작성
              ↓
생성된 파일과 운영 비용 해석
```

`scripts/reset_lab.py`, `inspect_lab.py`, `watch_lab.py`는 실습을 대신하지 않습니다. 각각 초기화, 단일 상태 조회, 반복 관찰만 담당합니다.
학습자 코드는 `src/iceberg_basic/` 패키지에 작성하고 `python -m iceberg_basic.<module>` 형태로 실행합니다.

[시작 안내](00_intro.md)부터 순서대로 진행하고, 각 장에서 예상 결과와 실제 결과가 일치한 뒤 다음 장으로 이동하세요. 마지막에는 [학습 마무리](99_outro.md)에서 작성한 코드를 설명합니다.
