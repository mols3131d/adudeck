# 04. 데이터 테스트

## Summary

dbt의 데이터 테스트(Data test)는 본질적으로 **"나쁜 rows를 찾아내는 SQL"**입니다. 테스트 쿼리를 실행하여
반환되는(실패한) rows가 0개여야 테스트가 통과(Pass)한 것으로 간주합니다.

## Core Concepts

dbt는 대표적인 내장 Generic Data Tests를 제공합니다:

- `not_null`: 해당 컬럼에 null 값이 없어야 한다.
- `unique`: 해당 컬럼 값에 중복이 존재해서는 안 된다.
- `accepted_values`: 컬럼 값이 지정된 허용 목록 안에만 존재해야 한다.
- `relationships`: 다른 모델이나 테이블의 외래키 참조 관계가 성립해야 한다.

※ 최신 dbt에서는 YAML 설정 시 과거의 `tests:` 키워드 대신 `data_tests:`를 사용할 것을 권장합니다.

## Hands-on / Code

현재 프로젝트의 모델명에 맞추어 `models/schema.yml`에 데이터 테스트를 추가해 봅니다.

```yaml
version: 2

models:
  - name: stg_users
    description: "사용자 원천 데이터를 분석하기 좋게 정리한 staging 모델"
    columns:
      - name: user_id
        description: "사용자 식별자"
        data_tests:
          - not_null
          - unique

  - name: stg_orders
    description: "주문 원천 데이터를 정리한 staging 모델"
    columns:
      - name: order_id
        description: "주문 식별자"
        data_tests:
          - not_null
          - unique
      - name: quantity
        data_tests:
          - not_null
      - name: payment_method
        data_tests:
          - accepted_values:
              values: ['Credit Card', 'PayPal', 'Apple Pay', 'Google Pay', 'Bank Transfer']
```

작성 후 전체 테스트 또는 특정 모델 테스트를 실행해 봅니다.

```bash
uv run dbt test
# 특정 모델만 테스트
uv run dbt test --select stg_orders
```

## Common Pitfalls

테스트에 실패(Fail)했다고 해서 dbt 프로그램 자체에 오류가 생긴 것이 아닙니다. 입력 데이터가 사용자가 기대한 품질 규칙을
어겼기 때문입니다. 이때 당황하지 말고 `target/compiled` 폴더로 이동해 컴파일된 테스트 SQL을 열어보고, 실제
데이터베이스에서 이 쿼리를 돌려 실패한 row가 어떤 것인지 직접 파악하는 디버깅 과정을 거쳐야 합니다.

## Checklist

- [ ] 데이터 테스트가 '실패하는 row를 찾는 SQL 쿼리'라는 메커니즘을 이해했다.
- [ ] `models/schema.yml` 파일에 `data_tests:` 구문으로 `not_null`, `unique` 규칙을 직접 작성했다.
- [ ] `uv run dbt test`를 실행하여 통과 여부를 확인했다.
- [ ] 테스트 실패 시 컴파일된 SQL(`target/compiled`)을 찾아 원인을 디버깅하는 플로우를 이해했다.
