# Dataset Generator

`adudeck`의 여러 deck에서 재사용할 수 있는 학습용 dataset generator다. 실제 서비스용 synthetic-data platform을
목표로 하지 않는다. 현재는 관계가 있는 ecommerce 데이터를 같은 입력에서 반복 생성하는 작은 도구만 제공한다.

`Faker`는 이름, email, 도시 같은 leaf value를 만들고, 이 package가 ID, 관계, 시간 순서, 금액 합계 같은 dataset
invariant를 소유한다.

## Run

```bash
cd tools/dataset_generator
uv run adudeck-data generate ecommerce \
  --output ./data \
  --users 100 \
  --products 50 \
  --orders 500 \
  --seed 42
```

기본값은 위 예시와 같다. 출력 directory가 없으면 생성하고, 같은 이름의 네 CSV는 덮어쓴다.

## Output

```text
data/
├── users.csv
├── products.csv
├── orders.csv
└── order_items.csv
```

관계는 다음과 같다.

```text
users 1 ── N orders 1 ── N order_items N ── 1 products
```

| File | Main columns |
| --- | --- |
| `users.csv` | `user_id`, `name`, `email`, `city`, `created_at` |
| `products.csv` | `product_id`, `name`, `category`, `price` |
| `orders.csv` | `order_id`, `user_id`, `status`, `created_at`, `total_amount` |
| `order_items.csv` | `order_item_id`, `order_id`, `product_id`, `quantity`, `unit_price` |

현재 generator는 다음 invariant를 보장한다.

- 모든 `orders.user_id`는 `users.user_id`를 참조한다.
- 모든 order item은 존재하는 order와 product를 참조한다.
- user의 `created_at`은 해당 user의 order `created_at`보다 늦지 않다.
- 각 order에는 1개 이상의 item이 있다.
- `orders.total_amount`는 item별 `quantity * unit_price`의 합이다.

## Reproducibility

`--seed`가 같고 실행 환경의 Python 및 `Faker` version이 같으면 같은 파일을 생성하도록 설계했다. Faker의 provider
데이터 변경이 seeded output을 바꿀 수 있으므로 package dependency는 patch version까지 고정한다.

## Scope

지금은 `ecommerce` scenario와 CSV output만 지원한다. generic schema DSL, dirty-data injection, JSONL/Parquet,
streaming event generation은 실제 deck에서 필요해질 때 추가한다.

## Test

repository root에서 다음을 실행한다.

```bash
PYTHONPATH=tools/dataset_generator/src \
  uv run --no-project --with Faker==40.37.0 \
  python -m unittest discover -s tools/dataset_generator/tests -v
```
