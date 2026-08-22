# 01. 왜 Iceberg가 필요한가

## Summary

Parquet는 한 파일의 행과 열을 효율적으로 저장합니다. Iceberg는 여러 data file 중 현재 테이블에 속하는 파일과 과거 상태를
metadata와 커밋 규칙으로 관리합니다.

## 서로 다른 책임

```text
PyIceberg       작업 실행: create, append, scan
Iceberg         테이블 상태: schema, snapshot, 유효한 파일 집합
Parquet         실제 행과 열 저장
파일시스템      파일 바이트 보관
```

Parquet 파일만 디렉터리에 모아 두면 파일 이름만으로 다음을 안정적으로 결정하기 어렵습니다.

- 실패한 쓰기의 파일이 유효한가?
- 동시에 추가된 파일 중 무엇이 현재 상태인가?
- 어제의 정확한 파일 집합은 무엇인가?
- schema가 바뀐 뒤 과거 파일을 어떻게 해석하는가?

Iceberg는 Parquet를 대체하지 않습니다. Iceberg 테이블의 실제 행도 이 실습에서는 Parquet에 저장됩니다.

## 시작 상태 관찰

```bash
uv run python scripts/inspect_lab.py
```

- **Action:** 아직 테이블이 없는 상태를 읽습니다.
- **Change:** 없음.
- **Verify:** `table : 없음`이고 data file과 metadata file이 없어야 합니다.

## 다음 장을 위한 질문

빈 Iceberg 테이블을 만든 직후에는 schema와 테이블 이름은 존재하지만 행은 없습니다. 그렇다면 Parquet data file도 생겨야
할까요? 다음 장에서 직접 생성한 뒤 확인합니다.

## Checklist

- [ ] Parquet가 파일 형식이고 Iceberg가 테이블 포맷인 이유를 설명할 수 있다.
- [ ] Parquet 파일 집합만으로 해결하기 어려운 문제를 두 가지 말할 수 있다.
- [ ] Iceberg가 실행 엔진이나 저장소가 아님을 설명할 수 있다.
