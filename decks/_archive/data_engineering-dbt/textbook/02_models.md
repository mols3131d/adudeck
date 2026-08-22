# 02. 프로젝트 구조와 모델

## Summary

dbt에서 모델(Model)은 본질적으로 확장자가 `.sql`인 파일입니다. dbt는 이 SQL 파일을 읽어 데이터베이스 내의 뷰(view) 또는
테이블(table) 형태의 릴레이션(relation)으로 컴파일 및 실행합니다.

## Core Concepts

현재 프로젝트의 핵심 디렉토리 및 파일 역할은 다음과 같습니다.

- `dbt_project.yml`: 프로젝트 이름, 모델 경로, 모델별 기본 설정 관리
- `profiles.yml`: 타겟 데이터베이스(ex. DuckDB) 연결 정보 설정
- `models/`: dbt가 실행할 SQL 모델들 위치
- `models/schema.yml`: 모델 및 컬럼의 메타데이터(설명)와 테스트 정의
- `seeds/`: 작은 CSV 기준 데이터를 dbt로 직접 적재할 때 사용
- `snapshots/`: 천천히 변하는 데이터(SCD)의 변경 이력 보관
- `tests/`: singular data test SQL 저장 공간

## Hands-on / Code

데이터 정제를 담당하는 3개의 Staging 모델을 생성하고 작성해 봅시다. 이 모델들은 선언된 dbt Source를 읽어와 필요한 데이터
타입으로 변환(Cast)하고 가독성 좋은 컬럼명으로 변경합니다.

### 1) 주문 정보 정제 (`models/staging/stg_orders.sql`)

아래 내용을 작성하여 주문 수량이 0보다 큰 데이터만 남기고 타입을 정제하는 모델을 만듭니다.

```sql
select
    order_id,
    user_id,
    product_id,
    cast(quantity as integer) as quantity,
    cast(total_price as integer) as total_price,
    cast(discount_amount as integer) as discount_amount,
    cast(delivery_fee as integer) as delivery_fee,
    cast(final_price as integer) as final_price,
    payment_method,
    status,
    cast(order_date as timestamp) as order_date
from
    {{ source('ecom_app', 'orders') }}
```

### 2) 상품 정보 정제 (`models/staging/stg_products.sql`)

아래 내용을 작성하여 상품 식별자, 상품명, 카테고리, 수치 정보의 타입을 정제합니다.

```sql
select
    product_id,
    name as product_name,
    brand,
    category,
    sub_category,
    cast(price as integer) as price,
    cast(cost_price as integer) as cost_price,
    cast(stock as integer) as stock
from
    {{ source('ecom_app', 'products') }}
```

### 3) 사용자 정보 정제 (`models/staging/stg_users.sql`)

아래 내용을 작성하여 가입 시각(`created_at`)을 타임스탬프 타입으로 정제하고 사용자명을 보기 좋게 변경합니다.

```sql
select
    user_id,
    name as user_name,
    gender,
    cast(birth_date as date) as birth_date,
    email,
    phone_number,
    address,
    job,
    membership_tier,
    cast(marketing_opt_in as boolean) as marketing_opt_in,
    cast(created_at as timestamp) as created_at
from
    {{ source('ecom_app', 'users') }}
```

---

### 4) 특정 모델 혹은 전체 모델 빌드하기

작성한 모델들을 데이터베이스에 빌드해 봅니다.

- **특정 모델만 빌드할 때:**

  ```bash
  uv run dbt run --select stg_orders
  ```

- **staging 폴더 아래의 모든 모델을 빌드할 때:**

  ```bash
  uv run dbt run --select staging
  ```

---

### 5) 실행 결과 확인 방법

`dbt run`이 정상적으로 수행되었는지 확인하는 두 가지 방법이 있습니다.

#### ① DuckDB 내부 데이터 조회하기

실제 데이터베이스에 View가 정상적으로 생성되었는지 쿼리를 날려 확인합니다.

- **방법 A: DuckDB CLI 사용 (설치된 경우)**

  ```bash
  duckdb dev.duckdb
  ```

  접속 후 아래 명령어를 실행합니다:

  ```sql
  -- 생성된 테이블/뷰 목록 조회
  .tables

  -- 뷰 데이터 조회 테스트
  SELECT * FROM stg_users LIMIT 5;

  -- 종료
  .exit
  ```

- **방법 B: Python 스크립트로 확인**

  ```python
  import duckdb

  con = duckdb.connect("dev.duckdb")

  # 생성된 테이블 목록 조회
  print("=== 테이블 목록 ===")
  print(con.execute("SHOW TABLES").fetchall())

  # 뷰 데이터 조회 테스트
  print("\n=== stg_users 데이터 샘플 ===")
  print(con.execute("SELECT * FROM stg_users LIMIT 5").df())
  ```

#### ② `target/` 디렉토리의 컴파일된 SQL 확인하기

dbt는 우리가 작성한 SQL 템플릿을 실제 SQL로 변환하여 `target/` 폴더에 캐싱합니다.

- **컴파일된 SELECT 문:** `target/compiled/dbt_basic/models/staging/`
- **실제 실행된 DDL 문 (CREATE VIEW/TABLE):** `target/run/dbt_basic/models/staging/`

이 경로에서 빌드된 SQL을 열어보고, SQL이 의도한 대로 컴파일되었는지 검토할 수 있습니다.

---

## Common Pitfalls

모델의 이름은 반드시 **파일명**에서 자동으로 부여됩니다. (`stg_orders.sql` -> 모델명: `stg_orders`) `schema.yml`에서
모델명을 선언할 때 실제 파일명과 불일치하면 설정, 테스트, 문서화가 올바르게 매핑되지 않으므로 가장 흔히 겪는 오류 원인
중 하나입니다.

---

## Checklist

- [ ] dbt 프로젝트의 핵심 디렉토리(`models`, `seeds`, `tests`) 역할을 숙지했다.
- [ ] 파일명 자체가 곧 dbt의 모델명이 된다는 규칙을 이해했다.
- [ ] 3개의 staging 모델(`stg_orders`, `stg_products`, `stg_users`)을 모두 정상적으로 생성 및 작성했다.
- [ ] `uv run dbt run --select staging` 명령어로 작성한 staging 모델들을 일괄 빌드하는 방법을 실습했다.
