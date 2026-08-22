# 05. 문서화 (Docs)

## Summary

dbt는 작성한 모델과 메타데이터(`schema.yml`)를 기반으로 프로젝트 전체의 의존성 구조(Lineage)와 컬럼 설명을 웹 브라우저에서 열람 가능한 문서로 자동 생성해 줍니다.

## Core Concepts

- **docs:** `schema.yml`에 작성한 모델 설명, 컬럼 설명, 테스트 규칙 등을 취합하여 정적 웹 사이트로 만들어줍니다.
- **Lineage Graph:** `ref()` 함수를 통해 연결된 모델 간의 의존성 흐름을 시각적으로 파악할 수 있게 해줍니다.

## Hands-on / Code

먼저 메타데이터를 기반으로 문서를 생성하고 로컬 서버에서 확인해 봅니다.

```bash
uv run dbt docs generate
uv run dbt docs serve
```

웹 브라우저가 열리면 화면 우측 하단의 파란색 버튼을 눌러 전체 프로젝트의 Lineage Graph를 확인해 보세요.

## Common Pitfalls

`schema.yml`에 모델명이나 컬럼명을 잘못 입력하면, 빌드는 통과하더라도 문서에 해당 설명이 누락되거나 오류가 발생할 수 있습니다. 파일명과 모델명이 일치하는지 항상 주의하세요.

## Checklist

- [ ] `schema.yml`에 작성한 모델과 컬럼 설명이 `dbt docs`에 제대로 나타나는지 확인했다.
- [ ] 문서 하단의 Lineage Graph 버튼을 클릭하여 모델 간의 의존성 흐름을 시각적으로 확인했다.
