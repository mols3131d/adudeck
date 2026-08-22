# 06. 생성된 증거로 운영 비용 판단하기

## Summary

직접 작성한 두 번의 작은 append가 두 개의 작은 Parquet를 만들었습니다. Iceberg는 일관된 테이블 상태를 제공하지만 파일 최적화와 metadata 보존 정책까지 없애지는 않습니다.

## 최종 상태 관찰

```bash
uv run python scripts/inspect_lab.py
find warehouse -type f | sort
```

- **Action:** 논리 상태와 실제 파일을 읽습니다.
- **Change:** 없음.
- **Verify:** 데이터는 3행이지만 append 횟수에 대응하는 Parquet 2개와 여러 metadata 파일이 있어야 합니다.

## 작은 파일 문제

이 실습은 원리를 드러내기 위해 2행과 1행을 따로 썼습니다. 운영 환경에서도 작은 batch를 자주 append하면 파일 수가 늘어나 query planning과 저장소 요청 비용이 커질 수 있습니다. Iceberg 테이블이라고 해서 작은 파일이 자동으로 사라지지는 않습니다.

## 대표 유지보수

| 작업 | 해결하려는 문제 | 비용 또는 위험 |
| --- | --- | --- |
| Data file compaction | 작은 파일 증가 | I/O 비용, 동시 쓰기 충돌 가능성 |
| Manifest rewrite | manifest 과다 | metadata 재작성 비용 |
| Snapshot expiration | 오래된 이력 누적 | 필요한 Time Travel 이력 상실 |
| Orphan file 제거 | 미참조 파일 누적 | 유효한 파일 오삭제 위험 |

구체적인 명령과 옵션은 실행 엔진 및 버전에 따라 달라 이 로컬 실습에서는 실행하지 않습니다.

## 도입 판단

Iceberg의 가치가 커지는 경우:

- 동시 쓰기나 update/delete/merge가 필요하다.
- 과거 상태 재현과 감사가 필요하다.
- schema 또는 partition 전략이 변한다.
- 여러 실행 엔진이 같은 테이블을 공유한다.

단순한 파일 관리가 나을 수 있는 경우:

- 단일 프로세스가 작은 데이터 전체를 항상 다시 만든다.
- snapshot, 동시 쓰기, schema evolution 요구가 없다.
- Catalog와 유지보수 비용이 얻는 이점보다 크다.

## 실습에서 검증하지 않은 것

| 직접 확인한 사실 | 확인하지 않은 운영 항목 |
| --- | --- |
| 로컬 append와 snapshot 생성 | 다중 writer 충돌과 재시도 |
| snapshot ID 기반 과거 읽기 | snapshot 만료와 복구 정책 |
| nullable 컬럼 추가 | 여러 엔진 간 schema 호환성 |
| SQLite Catalog | REST Catalog의 인증과 가용성 |

## Checklist

- [ ] 두 번의 작은 append가 두 Parquet를 만든 것을 직접 확인했다.
- [ ] compaction과 snapshot expiration의 목적과 비용을 구분할 수 있다.
- [ ] 이 실습에서 검증하지 않은 운영 항목을 두 가지 말할 수 있다.
- [ ] 자신의 사례에서 Iceberg가 불필요할 조건을 제시할 수 있다.
