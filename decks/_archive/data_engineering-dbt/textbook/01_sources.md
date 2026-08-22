# 01. 원천 데이터 관리 (Sources)

## Summary

dbt의 **Sources(소스)**는 분석 DB에 이미 적재되어 있거나 외부 저장소에 존재하는 "원천 데이터"를 dbt 프로젝트로 불러오고
정의하는 공식적인 방법입니다. 원천 데이터를 소스로 선언하고 사용하면 데이터 계보(Lineage, DAG)를 원천 단계부터 시작할 수
있으며, 데이터 신선도(Freshness) 측정과 문서화가 쉬워집니다.

---

## Problem & Concept

### 하드코딩 방식의 문제점

dbt 모델을 구축할 때 다음과 같이 물리적인 경로를 SQL 코드에 직접 작성할 수 있습니다.

```sql
select * from read_csv_auto('../../data/raw/ecom_app/users.csv')
```

이러한 하드코딩 방식은 작동할 수는 있지만 여러 문제점을 야기합니다.

1. **의존성 그래프(Lineage) 단절**: dbt가 해당 SQL 모델이 어떤 원천 데이터를 기반으로 만들어졌는지 추적할 수 없으므로,
   데이터 리니지(DAG)가 중간부터 시작하게 됩니다.
2. **유지보수의 어려움**: 데이터 소스의 파일 경로가 변경되거나 파일 포맷이 확장(ex. CSV -> Parquet)되는 경우, 이를
   참조하는 모든 staging 모델의 SQL 파일들을 일일이 찾아서 직접 수정해야 합니다.

### 해결책: dbt Sources

dbt Sources 기능을 사용하면 원천 데이터 정보를 하나의 YAML 설정 파일에 정의하고, 모델 내에서는 `{{ source() }}` 함수를
통해 동적으로 참조하게 됩니다.

| 개념 | 설명 |
| --- | --- |
| **Source 정의** | `models/` 폴더 내의 YAML 파일에 원천 데이터베이스, 스키마, 테이블 이름, 물리적인 위치 등을 지정합니다. |
| **`source()` 함수** | SQL 모델 내에서 `{{ source('소스_이름', '테이블_이름') }}` 문법을 사용하여 해당 데이터를 불러옵니다. |

---

## Caveats (주의할 점)

dbt는 원천 데이터를 자동으로 추출하거나 적재해주지 않습니다. 원천 CSV나 테이블이 존재하지 않으면 모델 컴파일 및 실행 시
오류가 발생합니다.

이 프로젝트의 소스 정의와 staging 모델들은 로컬 경로의 다음 원천 CSV 데이터를 읽도록 설정됩니다:

- `../../data/raw/ecom_app/orders.csv`
- `../../data/raw/ecom_app/products.csv`
- `../../data/raw/ecom_app/users.csv`

따라서 작업을 시작하기 전에 이 원천 파일들이 지정된 경로에 실제로 존재하는지 확인해야 합니다.

---

## Hands-on / Code

### 1) YAML에 소스 정의하기 (`models/staging/sources.yml`)

staging 폴더 내에 소스 정의 전용 YAML 파일(예: `sources.yml`)을 생성하고 아래와 같이 설정합니다.

DuckDB 어댑터의 경우, `meta.external_location` 속성을 사용해 로컬 CSV 파일들의 위치를 템플릿화할 수 있습니다.

```yaml
version: 2

sources:
  - name: ecom_app
    description: "이커머스 서비스의 원천 CSV 데이터 소스"
    meta:
      external_location: "../../data/raw/ecom_app/{name}.csv"
    tables:
      - name: users
        description: "사용자 원천 데이터"
      - name: orders
        description: "주문 원천 데이터"
      - name: products
        description: "상품 원천 데이터"
```

> [!TIP]
> `external_location` 설정에서 `{name}` 부분은 하위 `tables` 리스트에 정의된 각 테이블의 `name` 값(예: `users`,
> `orders`, `products`)으로 자동 치환됩니다.

### 2) 모델에서 소스 사용하기 (`models/staging/stg_users.sql` 예시)

수정한 YAML에 따라 staging 모델의 `FROM` 절을 `source()` 참조 방식으로 교체합니다.

```sql
select
    user_id,
    name as user_name,
    gender,
    cast(birth_date as date) as birth_date,
    email,
    created_at
from
    {{ source('ecom_app', 'users') }}
```

### 3) 컴파일 및 의존성 확인

명령어를 실행해 프로젝트를 빌드합니다.

```bash
uv run dbt compile
```

dbt는 컴파일 수행 시 YAML의 `external_location` 경로를 해석하여, 실제 실행 SQL을 다음과 같이 자동 변환하여 `target/`
디렉토리에 캐싱합니다.

```sql
-- 컴파일 결과 예시 (target/compiled/...)
select
    ...
from
    read_csv_auto('../../data/raw/ecom_app/users.csv')
```

---

## Common Pitfalls

1. **정의되지 않은 소스 참조**: YAML 파일에 소스 정보를 정의하지 않고 SQL에서 `{{ source('ecom_app', 'users') }}`를
   호출하면 `Compilation Error`가 발생합니다.
2. **파일명/경로 오타**: `external_location`의 파일 경로 설정이 틀리거나 원천 CSV 파일명과 YAML에 선언한 `name`이
   일치하지 않을 경우 `Binder Error: file not found` 계열의 오류가 발생합니다.

---

## Checklist

- [ ] 원천 데이터를 하드코딩해서 읽을 때 발생하는 문제점(리니지 단절, 유지보수 곤란)을 이해했다.
- [ ] YAML 파일에 소스 구조와 DuckDB의 `external_location`을 설정할 수 있다.
- [ ] `{{ source('소스명', '테이블명') }}` 문법을 활용해 SQL 모델을 작성할 수 있다.
- [ ] dbt 컴파일 후에 실제 경로가 알맞은 SQL 쿼리로 매핑되는지 이해했다.
