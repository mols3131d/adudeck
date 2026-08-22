# 06. 기준 데이터 적재 (Seeds)

## Summary

dbt의 **seeds** 기능은 시스템 상태값이나 국가 코드처럼 작고 정적인 기준 데이터(CSV)를 버전 컨트롤(Git)로 관리하며
데이터베이스에 테이블로 직접 적재하는 기능입니다.

## Core Concepts

- **seeds:** `.csv` 형태의 원천 데이터를 `seeds/` 디렉토리에 두고 `dbt seed` 명령을 통해 데이터베이스에 테이블로
  생성합니다.
- 조인 시 다른 모델들과 동일하게 `{{ ref('csv_파일명') }}` 구문을 사용해 참조할 수 있습니다.

## Hands-on / Code

`seeds/order_status.csv` 파일을 생성하고 아래 내용을 입력하세요.

```csv
status,status_ko
pending,주문 접수
paid,결제 완료
cancelled,주문 취소
```

다음 명령어로 CSV를 데이터베이스에 적재합니다.

```bash
uv run dbt seed
```

적재 성공 후에는 `dbt show` 명령어로 데이터가 테이블 형태로 잘 들어갔는지 확인할 수 있습니다.

```bash
uv run dbt show --select order_status
```

데이터베이스에 테이블로 적재된 이후부터는, 일반 모델을 작성할 때와 완전히 동일하게 `{{ ref('order_status') }}` 구문을
사용하여 다른 SQL 모델에서 참조하고 조인할 수 있습니다.

### 실전 활용 실습: Marts 모델에 Seed 데이터 조인하기

앞서 `stg_orders` 모델을 작성할 때 원천 데이터에 있던 `status` 컬럼을 이미 추가해 두었습니다. 이제 마트 모델에서 방금
적재한 Seed 테이블과 조인하여 상태의 한국어 설명을 가져와 봅시다.

**1. 마트 모델 수정 (`models/marts/fct_orders.sql`)** 파일을 열고, 최하단에 Seed 테이블(`order_status`)을 조인하여
상태의 한국어 설명(`status_ko`)을 가져오도록 코드를 수정합니다.

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
    o.order_date,
    -- Seed 테이블에서 조인한 상태명(한글) 컬럼 추가
    s.status_ko 
from {{ ref('stg_orders') }} as o
left join {{ ref('stg_users') }} as u
    on o.user_id = u.user_id
left join {{ ref('stg_products') }} as p
    on o.product_id = p.product_id
-- Seed 테이블 조인
left join {{ ref('order_status') }} as s
    on o.status = s.status
```

**2. 모델 빌드 및 데이터 확인**
터미널에서 변경된 모델만 지정하여 실행해 봅니다. 에러 없이 `fct_orders` 테이블이 완성되면 조인에 성공한 것입니다.

```bash
uv run dbt run --select stg_orders fct_orders
```

## Common Pitfalls

seed 기능은 '수백~수천 건 이내의 잘 변하지 않는 기준 데이터'에만 적합합니다. 수만 건 이상의 대규모 원천 데이터를 seed로
적재하려고 하면 프로젝트 빌드가 심각하게 느려지며 관리도 어려워지므로 피해야 합니다. 대용량 원천 데이터는 외부 테이블
로드 등 다른 방식으로 처리해야 합니다.

## Checklist

- [ ] `seeds/order_status.csv` 파일을 만들고 `uv run dbt seed` 명령어로 DB에 적재했다.
- [ ] `uv run dbt show --select order_status` 명령어로 적재된 데이터를 확인했다.
- [ ] `fct_orders` 모델 코드를 수정하고 Seed 데이터를 조인하여 성공적으로 `dbt run`을 마쳤다.
- [ ] Seed 테이블도 일반 모델과 동일하게 `ref()` 함수를 사용해 참조하고 조인할 수 있음을 이해했다.
- [ ] 대용량 원천 데이터는 seed가 아닌 다른 방식(외부 테이블 로드 등)으로 처리해야 함을 이해했다.
