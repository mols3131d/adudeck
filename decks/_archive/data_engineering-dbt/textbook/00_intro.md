# 00. dbt Basic 튜토리얼 시작하기

이 텍스트북은 `projects/dbt_basic` 프로젝트에서 dbt 기초를 처음부터 끝까지 실습하기 위한 가이드입니다.

## 학습 목표

데이터 웨어하우스(DuckDB) 환경에서 dbt의 핵심 역할(Transform, Test, Document)을 직접 구성해 보며, 파편화된 원천 데이터를
분석 가능한 마트 데이터로 탈바꿈시키는 전체 파이프라인을 구축합니다.

## dbt의 핵심 개념

dbt는 데이터를 가져오는(Extract/Load) 도구가 아니라, 이미 데이터베이스에 적재된 데이터를 변환(Transform), 검증(Test),
문서화(Document)하는 도구입니다. dbt를 구성하는 핵심 개념은 다음과 같습니다:

| 개념 | 의미 |
| --- | --- |
| **Model (모델)** | 하나의 `.sql` 파일. 실행되면 데이터베이스 안에 View 또는 Table로 생성됩니다. |
| **DAG (의존성 그래프)** | 모델 간의 흐름을 나타내는 방향성 그래프입니다. `ref()` 또는 `source()` 함수를 통해 모델 간의 연결(선후 관계)이 자동으로 파악됩니다. |
| **Source (소스)** | 분석 DB에 적재된 원천 데이터를 정의한 것. `source()`로 호출하며 YAML로 선언합니다. |
| **Test (테스트)** | 데이터가 지켜야 할 조건(예: unique, not_null). 테스트 쿼리를 실행해 오류 데이터를 검출합니다. |
| **Docs (문서화)** | 모델과 컬럼의 설명, 그리고 데이터 흐름도(Lineage Graph)를 자동으로 생성해 주는 웹 문서입니다. |

### Key takeaway

dbt는 데이터를 가져오는 도구가 아니라, 이미 데이터 웨어하우스나 로컬 분석 DB에 있는 데이터를 SQL로 변환하고 검증하고
문서화하는 도구입니다.

이 프로젝트에서는 DuckDB를 데이터베이스로 사용합니다.

### Explanation

데이터 파이프라인은 보통 세 단계로 나눕니다.

```text
Extract/Load        Transform                 Analyze
원천 데이터 적재  ->  SQL로 정제/조인/집계  ->  BI, 리포트, 분석
```

dbt는 가운데 Transform 영역을 담당합니다.

기존 데이터 웨어하우스나 데이터베이스에 데이터가 적재되어 있으면, dbt를 활용해 이를 정제(Staging), 관계
형성(Intermediate), 최종 마트(Marts) 테이블로 유연하게 모델링할 수 있습니다.

## 시작 상태 (Start State)

이 튜토리얼을 시작하는 현재 시점에 여러분은 다음 항목들을 가지고 있습니다:

- **로컬 디렉토리:** 빈 dbt 뼈대인 `projects/dbt_basic` 폴더
- **원천 데이터:** `../../data/raw/ecom_app/` 폴더에 위치한 `orders.csv`, `users.csv`, `products.csv`
- **실행 환경:** dbt Core와 DuckDB 어댑터가 설치된 환경 (`uv run dbt debug`로 접속 확인 가능)

## 최종 상태 (End State)

튜토리얼을 모두 완주하면 여러분의 프로젝트는 다음과 같은 산출물을 확실하게 갖추게 됩니다:

- **Staging Models:** 원천 CSV를 읽고 타입을 정제한 3개의 뷰(`stg_orders`, `stg_users`, `stg_products`)
- **Marts Model:** 조인과 집계가 완료된 분석용 최종 테이블(`fct_orders.sql`)
- **품질 보증(QA):** 각 핵심 키(Primary Key)에 대한 `not_null`, `unique` 데이터 테스트 로직
- **문서화(Docs):** 컬럼 설명과 데이터 흐름(Lineage Graph)이 포함된 자동 생성 웹 문서

## 튜토리얼 범위

- **다루는 것:** model 작성, `ref()`를 통한 DAG 구성, 데이터 테스트(generic tests), dbt docs 시각화, seeds 기본.
- **다루지 않는 것:** dbt Cloud 운영, 대규모 CI/CD 파이프라인 구성, 고급 incremental 로직.

준비가 되셨다면, `00_roadmap.md`에서 전체 진행 상황을 확인하고 `01_sources.md`부터 첫걸음을 떼어 보세요!
