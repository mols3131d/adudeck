# 07. 이력 관리 (Snapshots)

## Summary

dbt의 **snapshots** 기능은 "현재 상태만 덮어쓰지 않고 과거 이력도 보존해야 할 때" 사용합니다. 대상 테이블의 특정
행(row)이 변경될 때마다 기존 값을 보존하고 새로운 값을 추가하여, 소위 '천천히 변하는 차원(SCD Type 2)' 및 상태 변경
이력을 쉽게 구축하게 해 줍니다.

---

## Problem & Concept

**왜 과거 이력이 필요한가요?**

만약 특정 주문(`order_id`)이 어제는 `pending`(주문 접수) 상태였고, 오늘은 `paid`(결제 완료) 상태로 변경되었다고 가정해
봅시다. 원본 데이터베이스에서 단순히 `status` 컬럼을 `UPDATE` 해버리면, 과거 `pending` 시절에 발생했던 주문 접수 시점의
기록이나 타임라인 데이터가 유실되어, 주문 상태별 전환 속도(Conversion Velocity)나 깔때기(Funnel) 분석을 할 수 없게
됩니다.

**해결책 (Snapshots):**

dbt 스냅샷은 원본 데이터가 변경되었을 때 이전 레코드를 지우지 않고 만료 처리한 뒤, 변경된 새 레코드를 추가합니다. 이를
위해 dbt가 자동으로 생성하고 관리하는 4가지 메타데이터 컬럼이 추가됩니다.

| order_id | status | dbt_valid_from | dbt_valid_to | dbt_is_current |
|---------|---------|----------------|--------------|----------------|
| 1001    | pending | 2026-05-01     | 2026-05-02   | False          |
| 1001    | paid    | 2026-05-02     | null         | True           |

위 표처럼 과거 이력은 `dbt_valid_to`에 만료일이 찍히고, 현재 유효한 최신 데이터는 `dbt_valid_to`가 `null` 상태로
유지됩니다.

---

## Hands-on / Code

`snapshots/` 폴더에 `orders_snapshot.sql` 파일을 생성하고 아래와 같이 설정할 수 있습니다.

```sql
{% snapshot orders_snapshot %}

{{
    config(
      target_database='dev',
      target_schema='main',
      unique_key='order_id',
      strategy='timestamp',
      updated_at='order_date',
    )
}}

select * from {{ source('ecom_app', 'orders') }}

{% endsnapshot %}
```

**설정(Config) 설명:**

- `unique_key`: 어떤 컬럼을 기준으로 레코드를 식별할지 지정합니다 (주로 Primary Key).
- `strategy='timestamp'`: 데이터가 변경되었는지 감지하는 전략입니다. 원본 데이터에 존재하는 `updated_at` 또는
  `order_date` 같은 수정 시간 컬럼을 기준으로, 이 시간이 미래로 바뀌면 데이터가 변경되었다고 판단합니다. (성능상 가장
  권장됨)
- *(참고: 적절한 수정 시간 컬럼이 없는 경우, 모든 컬럼의 값을 해시(hash)해서 비교하는 `strategy='check'` 방식을 사용할
  수도 있습니다.)*

명령어 실행:

```bash
uv run dbt snapshot
```

---

## Usage (활용 방법)

생성된 스냅샷은 일반 모델이나 Seed와 완전히 똑같이 `{{ ref('orders_snapshot') }}`으로 다른 SQL 모델에서 불러와 사용할 수
있습니다.

**실무 활용 팁:**

가장 최신의 주문 정보만 필요할 때는 조건절에 만료되지 않은 레코드(`dbt_valid_to is null`)를 필터링해서 사용합니다.

```sql
select *
from {{ ref('orders_snapshot') }}
where dbt_valid_to is null
```

과거 특정 시점의 데이터와 조인해야 할 경우, 분석하려는 시점의 시각이 `dbt_valid_from`과 `dbt_valid_to` 사이에 있는지를
확인하는 `BETWEEN` 조건 등으로 조인하게 됩니다.

---

## Common Pitfalls

스냅샷은 주기적으로 `dbt snapshot` 명령어가 스케줄링되어 실행될 때만 변경분을 캡처할 수 있습니다. 예를 들어, 하루에 한
번 스케줄링이 도는데 어떤 주문의 상태가 하루 동안 3번 바뀌었다면, 중간 과정의 이력은 잡히지 않고 스냅샷이 실행될 시점의
마지막 상태만 캡처됩니다.

---

## Checklist

- [ ] 일반적인 UPDATE 방식의 한계점과 과거 이력 보존(SCD Type 2)이 왜 필요한지 이해했다.
- [ ] 스냅샷 실행 시 추가되는 메타데이터 컬럼(`dbt_valid_from`, `dbt_valid_to` 등)의 역할을 표를 통해 이해했다.
- [ ] 데이터의 변경을 감지하는 전략 중 가장 권장되는 `timestamp` 방식의 동작 원리를 확인했다.
- [ ] 만들어진 스냅샷을 다른 모델에서 `{{ ref('orders_snapshot') }}`으로 참조할 수 있음을 이해했다.
