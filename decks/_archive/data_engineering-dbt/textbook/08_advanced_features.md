# 08. 기초 이후의 기능

## Summary

dbt 기초의 핵심은 고급 기능을 모두 사용하는 것이 아닙니다. 역할을 쪼갠 모델들을 `ref()`로 의존성 있게 연결하고, 테스트와
문서를 결합한 "단단한 미니 프로젝트"를 안정적으로 완성하는 것입니다. 이후 문제가 생겼을 때 하나씩 고급 기능을 도입하는
것이 올바른 접근입니다.

## Core Concepts

기초 이후에 마주치게 될 dbt의 고급 기능들은 다음과 같은 문제를 해결하기 위해 존재합니다.

| 고급 기능 | 해결하려는 문제 / 핵심 질문 |
| --- | --- |
| **materialization** | 이 모델을 view로 둘까, table로 만들까? |
| **incremental model** | 매번 전체를 재계산하지 않고 새로 추가/변경된 데이터(변경분)만 처리할 수 없을까? |
| **model contract** | 다운스트림에서 깨지지 않게 이 모델의 컬럼 이름과 데이터 타입을 강제로 보장할 수 있을까? |
| **versioned model** | 기존 모델을 쓰는 사용자를 깨뜨리지 않으면서, 모델을 새로운 로직으로 안전하게 버저닝(v1, v2)할 수 있을까? |
| **exposure** | 이 모델을 최종적으로 어떤 외부 BI 대시보드나 리포트가 쓰고 있는지 dbt 내부에 기록해둘 수 있을까? |
| **semantic layer** | '매출액' 같은 핵심 비즈니스 metric 정의를 파편화시키지 않고 중앙에서 하나로 관리할 수 있을까? |

## Hands-on / Code

가장 흔히 마주하는 `materialization` 설정을 변경해 봅니다.
모델 파일 최상단에 Jinja 블록을 이용해 설정합니다.

```sql
-- staging 계층 (보통 view로 충분함)
{{ config(materialized='view') }}

select *
from {{ ref('stg_users') }}
```

```sql
-- marts 계층 (조인과 집계가 많으므로 table 권장)
{{ config(materialized='table') }}

select
    user_id,
    count(*) as order_count
from {{ ref('stg_orders') }}
group by 1
```

## Common Pitfalls

"기능이 멋져 보여서 모든 모델에 다 적용한다"는 가장 흔하게 겪는 안티 패턴입니다.
고급 기능을 무턱대고 쓰면 프로젝트 구조가 복잡해지고 디버깅이 불가능해집니다. 반드시 **문제 기반 접근**을 하세요:

1. 빌드가 너무 느려졌다 -> `materialization` 변경 또는 `incremental` 검토
2. 하위 모델이나 대시보드가 자꾸 깨진다 -> `contract` 또는 `version` 검토
3. 부서마다 KPI 정의가 달라 숫자가 안 맞는다 -> `semantic layer` 검토

## Checklist

- [ ] dbt 기초 학습의 궁극적인 목표가 고급 기능의 남용이 아니라 단단한 기본기임을 동의했다.
- [ ] staging 모델은 `view`, marts 모델은 `table`로 materialization 하는 기본 원칙을 이해했다.
- [ ] 향후 발생할 수 있는 문제 상황과 그에 매핑되는 dbt 고급 기능 1~2개를 설명할 수 있다.
