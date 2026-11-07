# Rust 학습 덱 3종: 기술·교육 자료 조사 보고서

- 조사일: 2026-11-08
- 대상: PR #36 (`feat/backlog-language-rust`)
- 목적: Rust 입문·심화·Python 확장 모듈 실습의 후속 교본 제작을 위한 근거와 검증 조건 정리
- 상태: 조사 보고서 / `inbox/`의 비정규 작업 자료. 교본·실습 구현 및 실행 검증을 완료했다는 의미가 아님

## 결론

**현재 PR #36의 덱 분리는 유지한다.** Python 사용자는 Rust의 ownership·오류·테스트를 먼저 익히고, 이후 **고성능 Rust 라이브러리 설계**와 **Python에서 호출 가능한 확장 모듈**을 서로 다른 목표로 학습하는 편이 적합하다. Rust 심화 전체를 Python 연동 실습의 필수 선수 과정으로 두지 않는다.

교본 제작에서는 다음 원칙이 중요하다.

1. Rust 입문은 문법 번역보다 **move/borrow의 상태 변화 예측 → 컴파일러 진단 해석 → 테스트로 확인**하는 실습에 집중한다.
2. Python 연동은 Python API와 동작·오류 계약을 먼저 정의하고 Rust core → PyO3 binding → maturin wheel 순서로 검증한다.
3. 성능은 Rust 함수 단독 실행 시간과 **Python 호출 경로 전체 시간**을 구분한다. 빠르다는 전제 대신 profiling·반복 측정으로 이득을 입증한다.
4. Rust의 엄격한 컴파일러 피드백이 agentic coding 생산성을 높인다는 주장은 **학습 가설**이다. 정답률·수정 횟수·검토 비용·총 소요 시간을 실제로 비교한다.
5. 라이브 튜토리얼은 버전이 일치하지 않을 수 있으므로 **실제 설치된 compiler / PyO3 / maturin / Python 조합**에서 예제를 먼저 검증한다.

이 문서는 기존 [Rust 3덱 구상](../2026-10-28/rust-three-decks-learning-plan.md)의 *학습 의도*를 교체하지 않는다. 세 덱의 목적·범위·완료 기준은 각각의 README가 소유한다.

## 1. 확인된 기술 현황과 유의점

| 주제 | 2026-11-08 조사 결과 | 교본에 반영할 판단 |
| --- | --- | --- |
| Rust stable | 공식 release 목록의 최신 안정 릴리스는 **1.99.1**(2026-10-15) [S1] | 새 실습은 stable 사용을 기본으로 하되, 작성·검증 시 실제 `rustc --version` 기록 |
| Rust Edition | Rust 2024는 1.85.0부터 제공되며 현재 Rust Book의 기본 edition [S2, S3] | 신규 crate는 `edition = "2024"` 기본. compiler 버전과 edition을 혼동하지 않음 |
| Rust 입문 | 공식 Rust Book, Rust by Example, Cargo Book이 1차 자료 [S3, S4, S5] | 문법·ownership·Result·test·Cargo를 단계적으로 학습 |
| PyO3 | 최신 확인 릴리스 **0.30.1**(2026-10-14). 0.30에서 Python 3.8 지원 종료, 최소 Rust 1.85 [S6] | Python 지원 하한 및 PyO3 API를 실제 릴리스에 맞춰 선택 |
| maturin | 확인된 릴리스 **1.15.0**. `maturin develop`은 기본적으로 debug 빌드·가상환경 설치 [S7, S8] | 기능 확인에는 develop, 성능 비교에는 `--release` 및 설치 검증 |
| Python wheel | OS·아키텍처·Python 버전·ABI에 따라 호환성이 달라짐 [S9, S10] | 로컬 import 성공을 범용 배포 성공으로 오해하지 않음 |
| free-threaded Python | PyO3는 별도의 지원·주의사항이 있고, 최신 안내는 `abi3`와 `abi3t`를 구분 [S10, S11] | 입문 기본 경로에 강제하지 않고 별도 심화·호환성 실험으로 분리 |

**자료 간 차이:** maturin 공식 튜토리얼 일부는 Rust 2021 Edition, 이전 PyO3, `abi3-py38` 같은 예시를 유지한다 [S12]. 반면 PyO3 0.30 릴리스는 Python 3.8 지원을 종료했다 [S6]. 따라서 튜토리얼을 원문 그대로 복사하지 말고 버전과 기능 플래그를 함께 갱신·컴파일해야 한다. `pyo3.rs/main`은 다음 버전 작업이 반영될 수 있으므로 특정 릴리스에 종속된 코드는 릴리스 문서·migration guide·잠금된 의존성과 대조한다.

## 2. 덱별 자료 검토와 실습 제안

### 2.1 Rust 입문 — Python 개발자의 실행 모델 전환

대상: [language-rust_intro](../../decks/_backlog/language-rust_intro/README.md).

**핵심 자료:** Rust Book [S3], Rust by Example [S4], Cargo Book [S5], Clippy 문서 [S13].

추천 학습 흐름:

1. `cargo new --lib`로 시작해 crate·module·build·test의 관계를 확인한다. `cargo fmt`, `cargo clippy`, `cargo test`를 처음부터 피드백 루프로 사용한다.
2. Python 변수 참조와 Rust의 소유권·이동·차용을 대비한다. **코드 실행 전** 값의 소유자, 참조 가능 여부, compiler 결과를 예측하게 한다.
3. `String` / `&str`, `Vec<T>`, `Option<T>`, `Result<T, E>`, `match` / `?`를 단순 API 암기가 아닌 데이터·실패 흐름으로 다룬다.
4. 작은 텍스트 파서 또는 레코드 정규화 라이브러리를 구현한다. 정상·빈 입력·잘못된 UTF-8 또는 파싱 실패·경계값 테스트를 만든다.
5. 컴파일이 거절된 예제를 agent에게 수정하게 하되, **왜 오류인지**를 학습자가 설명하도록 한다.

권장 단원별 과제: 소유권 이동 추적, 빌림 충돌 디버깅, 실패 형태 예측, 파서 테스트 설계, 서로 다른 API 설계 비교. 초기에는 `unsafe`, 복잡한 async runtime, Python FFI를 넣지 않는다.

**완료 증거:** 독립적인 Rust crate가 컴파일·테스트·lint를 통과하고, 학습자가 적어도 소유권 오류 한 건과 실패 흐름 한 건을 근거와 함께 설명한다. 교본은 명령의 성공 여부뿐 아니라 컴파일 전후 상태를 확인하도록 설계한다.

### 2.2 Rust 심화 — 정확성·비용 모델·최적화

대상: [language-rust_advanced](../../decks/_backlog/language-rust_advanced/README.md).

**핵심 자료:** Rust Reference [S14], Rust Performance Book [S15], Rustonomicon [S16; `unsafe`가 실제 필요할 때만].

추천 학습 흐름:

1. trait / generic / lifetime을 라이브러리의 호출 계약과 연결한다.
2. `Vec`, iterator, allocation, copy, owned/borrowed 반환 방식의 trade-off를 예측하고 profiler로 확인한다.
3. 정상 경로와 오류 경로의 invariant, panic 경계, property 기반 검증 사례를 비교한다.
4. concurrency에서는 `Send`/`Sync`와 동기화 비용을 이해하고, 병렬화 전후에 정확성과 성능을 검증한다.
5. 최적화 전 baseline, 변경 의도, 프로파일링 근거, 반복 benchmark 결과를 남긴다.

실습 후보: 레코드 스캐너의 할당 줄이기, 문자열 파싱의 borrowed/owned 대안 비교, 순차 처리와 병렬 처리의 break-even point 찾기. **순수 Rust 내부 성능**에 초점을 맞추고 Python FFI를 섞지 않는다.

**완료 증거:** 변경 전후의 동작 일치와 반복 측정 결과, 성능이 개선되거나 악화되는 입력 범위, 복잡성·유지보수 비용 설명.

### 2.3 Python 확장 — API 경계와 배포 검증

대상: [language-rust_python_extensions](../../decks/_backlog/language-rust_python_extensions/README.md).

**핵심 자료:** PyO3 type conversions [S17], PyO3 build/distribution [S10], maturin local development·project layout [S8, S18], Python Packaging Guide [S9].

권장 실습은 **Python-first 레코드/텍스트 처리 라이브러리** 한 개를 고정 사례로 유지한다.

1. Python 함수 시그니처·결과·예외·순서·인코딩·빈 입력 등 동작 계약과 `pytest`를 정의한다.
2. Python-only baseline을 구현하고 먼저 profiling한다. 병목이 작으면 이식하지 않는 판단도 허용한다.
3. 동일 알고리즘의 Rust core를 순수 Rust로 작성하고 독립 테스트를 수행한다.
4. PyO3 `#[pyfunction]` / `#[pymodule]`로 연결한다. `FromPyObject`/`IntoPyObject` 타입 변환, `PyResult`, Python 예외 매핑을 검증한다 [S17].
5. maturin으로 로컬 설치 후 **새 Python 프로세스**에서 `import`·동작·예외·타입 일치를 검증한다. wheel 빌드·설치·재설치를 분리해 검사한다.
6. 작은 호출을 반복하는 경우와 큰 입력을 일괄 처리하는 경우를 나누어 측정한다. 변환·복사·호출 오버헤드가 순수 Rust의 이득을 상쇄할 수 있다 [S17].
7. 충분히 검증한 뒤, 필요한 범위에서만 `abi3`, 여러 OS/아키텍처용 wheel, free-threaded Python을 확장 과제로 다룬다 [S9–S11].

**완료 증거:** Python baseline 대비 동작·예외 계약을 통과하는 wheel, 재현 가능한 설치와 import, 공개된 측정 조건 및 성능 비교. 지원하지 않는 플랫폼/인터프리터는 명시한다.

## 3. 성능 검증 설계: Rust를 쓰는 이유 확인

Python Packaging Guide는 profiling 후 확장 모듈을 고려하고, 먼저 기존 최적화 구현이나 라이브러리 대안을 검토하도록 안내한다 [S9]. Rust Performance Book도 최적화 대상의 hotspot 확인을 강조한다 [S15].

권장 비교 대상은 최소 네 가지다.

| 비교 경로 | 무엇을 측정하나 | 잘못 해석하기 쉬운 점 |
| --- | --- | --- |
| Python baseline | 사용자 호출부터 결과 반환까지 | 기존 Python 알고리즘이 비효율적이면 언어 효과와 혼동 |
| Python 최적화 대안 | built-in/표준 라이브러리/검증된 패키지 대안 | Rust만의 이점이라고 단정하지 않음 |
| 순수 Rust core | 알고리즘 자체의 native 비용 | Python 사용자가 실제 체감하는 속도가 아님 |
| Python → PyO3 → Rust | 호출·변환·계산·반환 총비용 | 작은 입력의 경계 비용을 누락하기 쉬움 |

**측정 protocol 제안:**

- 동일 입력·동일 출력·동일 실패 동작과 같은 알고리즘적 복잡도를 우선 확인한다.
- 입력 크기(빈 값, 수십 바이트, 수 KB, 수 MB 등), 호출 횟수(1회·다회), 단건/배치를 나눈다.
- Rust release 최적화 빌드를 기준으로 하고, debug와 비교한 결과를 혼합하지 않는다.
- warm-up, 반복 횟수, 실행 순서, CPU·OS·Python/Rust/PyO3/maturin 버전, 프로세스 실행 방식을 기록한다.
- Python 측은 `pyperf` 같은 반복 측정 도구를 검토하고 [S19], Rust 측은 profiler와 검증된 benchmark harness를 별도로 선택한다.
- 단일 평균만 제시하지 않고 분산/중앙값, measurement noise, 설치·빌드 비용과 유지보수 비용을 함께 보고한다.
- 이득이 미미하거나 변동폭보다 작으면 **성능 이득 미확인**으로 기록한다. benchmark 수치는 이 조사 단계에서 생산하지 않는다.

예상 가능한 역전 조건: 짧은 함수의 과도한 FFI 호출, Python 자료구조의 대량 변환·복사, 작은 데이터셋, 최적화된 기존 Python C-extension 사용. 해당 조건은 가설이며 실제 실험으로 확인해야 한다.

## 4. Agentic coding 효율성 검증 설계

**검증할 가설:** Rust의 타입/ownership/compiler feedback이 agent의 실수를 빠르게 드러내어 수정 과정에 도움을 줄 수 있다. 그러나 API 설계·빌드·FFI 복잡성으로 전체 작업 시간은 오히려 증가할 수도 있다. Rust의 실행 속도와 코딩 작업 효율은 별도 지표다.

학습용 비교 실험:

- 동일한 기능 요구사항·테스트 계약을 **Python-only**와 **Rust-backed** 구현에 적용한다. 과제 난이도·도구·모델·프롬프트 및 테스트 예산을 기록한다.
- 성공 여부는 컴파일 성공이 아니라 **공통 블랙박스 동작 테스트 + 오류 사례 + 회귀 테스트**로 판정한다.
- 시간은 요구사항 전달부터 최초 테스트 통과, 수정 완료, 배포 가능한 결과까지 분리한다. Rust의 빌드·환경 설정 시간을 포함한다.
- agent의 시도 횟수, 컴파일/테스트 실패 유형, 인간 검토가 발견한 결함, API 계약 수정, 최종 산출물 유지보수 부담을 기록한다.
- 반복 과제의 순서·난도 효과와 모델 확률성을 통제하지 못했다면 인과적 우열을 주장하지 않는다.

이 결과는 **개인 작업 환경에서의 학습 관찰**이지 언어나 agent 일반의 우월성을 입증하는 벤치마크가 아니다. 특정 프레임워크의 도입을 선제 결정할 필요도 없다.

## 5. 제작 착수 시 결정할 사안

| 결정 | 권장 초기값 | 변경/재검증 조건 |
| --- | --- | --- |
| 첫 학습 덱 | Rust 입문 1개를 먼저 실행 가능한 상태로 | 입문 crate의 컴파일·검증 후 다음 덱 착수 |
| 학습 경로 | 입문 → 심화 또는 Python 연동 | 최적화·동시성 과제에 한해 심화 내용을 선행 |
| Edition | Rust 2024 | 명시적 호환성 제약이 있을 때 |
| 도구 버전 | 개발 착수 시 stable + 호환되는 릴리스 조합 확정 | PyO3 지원 Python 하한, Rust MSRV, maturin 빌드 지원 확인 |
| Python binding | PyO3 + maturin | 실제 요구가 다른 binding/packaging 방식을 필요로 할 때 |
| Wheel 정책 | 최초에는 로컬 대상 Python/OS에 한정 | 여러 Python 버전, OS, 아키텍처 배포 요구가 생길 때 |
| Free-threading/`abi3t` | 별도 확장 과제 | free-threaded interpreter 지원이 명시적 목표가 될 때 |
| 성능 목표 | 수치 목표 사전 확정 없이 관찰·기록 | 기준 workload와 합리적인 개선 목표가 생길 때 |

**첫 제작 단위 제안:** Rust 입문 덱에 1개의 작은 crate, 소유권 상태 추적 과제, 정상·오류 테스트, `fmt`/`clippy`/`test` 체크포인트를 만든다. 빈 장·폴더를 대량 생성하거나 Python 연동까지 한꺼번에 구현하지 않는다.

## 6. 조사 한계와 다음 검증

- 웹의 공식 안내·릴리스 노트와 PR #36의 README를 대조한 **문헌 조사**다. 이 보고서에서는 crate를 빌드하거나 패키지를 설치·테스트하지 않았다.
- 버전은 조사 시점의 snapshot이다. 새 교본의 코드 작성 직전에 `rustc --version`, `python --version`, `cargo tree`, `maturin --version` 및 공식 지원 범위를 다시 확인한다.
- 특정 PyO3 문서의 `main` 브랜치 내용과 배포 릴리스가 다를 수 있다. 배포 릴리스 기준으로 튜토리얼 코드를 컴파일한 결과만 정상 동작 근거로 삼는다.
- Benchmark와 agentic coding 효율성은 측정하지 않았다. 이 단계에서 성능 향상이나 작업 효율을 수치로 주장할 근거가 없다.
- 이 문서는 PR #36에 교본/실습을 추가하라고 요구하지 않는다. 기존 PR은 Backlog 목표 정의로서 분리하고, 실행형 교본·실습은 후속 변경에서 검증한다.

## 출처 (공식 또는 원 저작자 문서)

- [S1] [Rust Release Announcements](https://blog.rust-lang.org/releases/) — stable 릴리스 날짜·버전
- [S2] [Rust 2024 Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/) — edition 도입 시점
- [S3] [The Rust Programming Language](https://doc.rust-lang.org/book/) — 입문 학습 및 ownership·테스트
- [S4] [Rust by Example](https://doc.rust-lang.org/rust-by-example/) — 실습 예제
- [S5] [Cargo Book / cargo test](https://doc.rust-lang.org/cargo/commands/cargo-test.html) — 빌드·테스트 실행
- [S6] [PyO3 Releases](https://github.com/PyO3/pyo3/releases) — 0.30.1 릴리스 및 최소 지원 조건
- [S7] [maturin Releases](https://github.com/PyO3/maturin/releases) — 버전 현황
- [S8] [maturin Local Development](https://www.maturin.rs/local_development) — 개발·release 빌드
- [S9] [Python Packaging: Binary Extensions](https://packaging.python.org/en/latest/guides/packaging-binary-extensions/) — ABI, wheel, 가속의 대안
- [S10] [PyO3 Building and Distribution](https://pyo3.rs/main/building-and-distribution) — extension packaging, `abi3`/`abi3t`
- [S11] [PyO3 Free-Threaded Python](https://pyo3.rs/main/free-threading) — 동시성 호환성
- [S12] [maturin Tutorial](https://www.maturin.rs/tutorial) — 교육용 예시와 버전 차이
- [S13] [Clippy Usage](https://doc.rust-lang.org/clippy/usage.html) — lint feedback
- [S14] [Rust Reference](https://doc.rust-lang.org/reference/) — 언어 세부 계약
- [S15] [Rust Performance Book](https://nnethercote.github.io/perf-book/) — profiling·최적화
- [S16] [Rustonomicon](https://doc.rust-lang.org/nomicon/) — unsafe/FFI의 전문 참고
- [S17] [PyO3 Type Conversions](https://pyo3.rs/main/conversions/tables) — 타입 변환·비용·예외 매핑
- [S18] [maturin Project Layout](https://www.maturin.rs/project_layout) — Python/Rust 혼합 구조
- [S19] [pyperf Documentation](https://pyperf.readthedocs.io/en/latest/) — 반복 Python benchmark
