# 03. Jinja, ref, source, macro

## Summary

dbt SQL은 순수 SQL에 **Jinja 템플릿 엔진** 기능이 결합되어 있습니다. Jinja를 활용하여 모델 간의 실행 의존성을 정의하고,
반복되는 로직을 재사용하며 동적인 SQL 작성이 가능해집니다.

## Core Concepts

- **ref() 함수:** `{{ ref('stg_users') }}` 형식으로 다른 모델을 참조합니다. 현재 실행 환경(dev, prod)에 맞는
  테이블명으로 자동 치환되며, 가장 중요한 점은 dbt에게 이 모델이 `stg_users`에 의존한다는 사실(DAG)을 알려준다는
  것입니다.
- **source() 함수 (1장 복습):** `{{ source('ecom_app', 'users') }}` 형식으로 원천 데이터 테이블을 명시할 때 씁니다.
  dbt가 원천 데이터와 모델 간의 의존성을 파악하는 첫 시작점입니다.
- **macro:** 프로그래밍 언어의 함수처럼, 반복되는 SQL 조각을 한 번만 정의하고 여러 모델에서 재사용할 때 사용합니다.

## Hands-on / Code

staging 모델들을 조인하여 실질적인 분석용 마트 모델을 만들어 봅니다.
`models/marts/fct_orders.sql` 파일을 다음과 같이 작성하세요.

```sql
{{ config(materialized='table') }}

select
    o.order_id,
    o.user_id,
    u.user_name,
    u.membership_tier,
    o.product_id,
    p.product_name,
    p.brand,
    p.category,
    o.quantity,
    o.total_price,
    o.discount_amount,
    o.delivery_fee,
    o.final_price,
    o.payment_method,
    o.order_date
from {{ ref('stg_orders') }} as o
left join {{ ref('stg_users') }} as u
    on o.user_id = u.user_id
left join {{ ref('stg_products') }} as p
    on o.product_id = p.product_id
```

작성한 마트 모델을 실행합니다.

```bash
uv run dbt run --select fct_orders
```

## Common Pitfalls

`from stg_orders`와 같이 데이터베이스 테이블명을 직접 하드코딩하면 안 됩니다. 이 경우 dbt가 의존성 그래프를 그릴 수
없어서, 테이블이 빌드되는 순서가 꼬이고 다른 환경 배포 시 테이블명이 치환되지 않는 치명적인 문제가 발생합니다. 반드시
`{{ ref('모델명') }}` 문법을 사용하세요.

## Checklist

- [ ] 하드코딩 대신 `ref()`를 사용했을 때 얻는 이점 2가지(이름 치환, DAG 형성)를 설명할 수 있다.
- [ ] `models/marts/fct_orders.sql` 파일을 생성하고 3개의 staging 테이블을 `ref()`로 참조하여 작성했다.
- [ ] `uv run dbt run --select fct_orders`로 의존성을 가진 마트 모델 빌드에 성공했다.
