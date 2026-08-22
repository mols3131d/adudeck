# Apache Iceberg 직접 구현 실습 마무리

## Summary

이 실습에서 학습자는 Iceberg 변경 코드를 직접 작성했고, 제공 도구는 결과만 관찰했습니다. 최종 목표는 명령을 기억하는 것이 아니라 각 API 호출이 어떤 상태와 파일을 바꾸는지 설명하는 것입니다.

## 최종 검증

```bash
uv run python scripts/inspect_lab.py
uv run python -m iceberg_basic.time_travel
```

- **Action:** 직접 만든 최종 테이블과 Time Travel 코드를 다시 읽습니다.
- **Change:** 없음.
- **Verify:** 아래 증거가 모두 실제 출력에 있어야 합니다.
- [ ] schema에 field ID 1, 2, 3이 있다.
- [ ] 현재 데이터는 3행이고 `channel`은 `None`이다.
- [ ] append로 생성된 snapshot이 2개다.
- [ ] Parquet 2개와 metadata JSON, manifest, manifest list가 있다.
- [ ] 첫 snapshot은 2행이고 현재 snapshot은 3행이다.

## 작성한 코드를 설명하기

파일을 열어 다음 질문에 답합니다.

1. `src/iceberg_basic/catalog.py`의 Catalog URI와 warehouse는 각각 무엇을 가리키는가?
2. `create_table()`에 schema가 필요한 이유는 무엇인가?
3. `table.append()`는 Arrow 데이터를 어떤 관리 대상 파일로 바꾸는가?
4. 두 snapshot은 각각 어떤 data file 집합을 참조하는가?
5. `scan(snapshot_id=...)`가 현재 상태를 바꾸지 않는 이유는 무엇인가?
6. `update_schema()` 이후 기존 Parquet를 다시 쓰지 않은 이유는 무엇인가?

답을 코드의 특정 줄과 `warehouse/`의 실제 파일에 연결해서 설명할 수 있어야 합니다.

## 초기화와 재실행

```bash
uv run python scripts/reset_lab.py
```

- **Action:** 생성된 Catalog와 warehouse를 제거합니다.
- **Change:** `warehouse/`만 삭제되고 직접 작성한 `src/iceberg_basic/*.py`는 보존됩니다.
- **Verify:** `uv run python scripts/inspect_lab.py`가 `table : 없음`을 출력해야 합니다.

초기화 후에는 2장부터 자신이 작성한 파일을 순서대로 다시 실행할 수 있습니다.

## Checklist

- [ ] 준비된 변경 명령 없이 전체 실습을 자신의 코드로 재현했다.
- [ ] 각 코드의 입력, 상태 변화, 검증 증거를 연결해서 설명할 수 있다.
- [ ] 로컬 최소 실습과 운영 환경의 차이를 설명할 수 있다.
