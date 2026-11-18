# Rust 입문

Python 사용자가 Rust의 기본 문법과 실행 모델을 이해하고, **작은 Rust 라이브러리를 agent와 함께 안전하게 개발·검증**하기
위한 학습 덱이다.

현재는 후속 학습을 위한 backlog이다. 교본이나 실습 코드는 아직 작성되지 않았다.

## Goal

학습 후에는 다음을 할 수 있어야 한다.

- `rustup`, `cargo`, `rustfmt`, `clippy`, `cargo test`로 프로젝트를 생성·수정·검증한다.
- 변수, 타입, `struct`, `enum`, `match`, `Option`, `Result`, `Vec`, `String`을 Python 개념과 비교해 설명한다.
- Ownership, borrowing, move, lifetime의 기본 제약을 컴파일 오류와 실제 값의 소유 관계로 설명한다.
- 함수와 모듈을 분리하고, 작은 변환·파싱 로직의 테스트를 작성한다.
- Agent가 작성한 코드의 타입·소유권·실패 처리 가정을 컴파일러와 테스트로 검증하고 수정한다.

## Prerequisites

Python 함수, 자료구조, 예외 처리, 패키지 및 테스트의 기본 지식. C/C++ 경험은 요구하지 않는다.

## Learning scope

1. Rust toolchain, Cargo project, build와 test feedback loop
2. 표현식, 제어 흐름, 데이터 타입과 pattern matching
3. Ownership / borrowing / references와 compiler diagnostics
4. `struct`, `enum`, `Option`, `Result`, error propagation
5. `Vec`, `String`, iterator와 trait/generic의 기초
6. 모듈, 단위 테스트, `fmt`/`clippy` 기반 수정·검증
7. 작은 Rust-only parsing 또는 transformation library 구현

Async runtime, 복잡한 concurrent architecture, `unsafe`, Python extension packaging은 이 덱의 core 범위가 아니다.

## Learning progression and checkpoints

기존 학습 범위는 다음 의존 관계로 가르친다. 주제 목록을 암기한 것만으로 완료하지 않고 각 단계에서 설명과 관찰을
함께 확인한다.

| 학습 단계 | 앞서 알아야 할 것 | 검증 가능한 학습 결과 |
| --- | --- | --- |
| Cargo와 기본 데이터 모델 | Python의 함수·변수·테스트 경험 | crate, source, compile, test의 관계를 설명하고 작은 표준 라이브러리 함수를 검사한다 |
| 소유권과 차용 | 함수 호출, `String`과 값의 생성 | `String` move 후 원래 이름의 사용 가능 여부 및 `&str` 차용의 차이를 **컴파일 전에 예측**한다 |
| 오류 모델과 자료 구조 | `match`, `struct`/`enum`, 차용의 기본 | `Option`/`Result`와 `?`를 사용해 정상·실패 흐름을 추적한다 |
| 작은 라이브러리와 테스트 | 앞 단계의 값·오류 모델 | 모듈로 분리하고 실패·경계값 테스트를 추가하며 lint 결과를 해석한다 |
| 독립적인 수정·검증 | 기본 라이브러리와 테스트 경험 | agent가 수정한 코드의 계약과 소유권 가정을 스스로 검토하고 반례를 제시한다 |

첫 제작 단위는 **Cargo → 값의 소유자 → 함수 인자 move와 shared borrowing → compiler 진단**까지만 다룬다.
처음부터 명시적 lifetime annotation, `unsafe`, concurrency 또는 Python binding을 설명하지 않는다. 컴파일되지 않는
예시는 통과해야 하는 기본 crate의 빌드 경로와 분리하고, 예측·실패 근거·수정 이유를 교본 과제로 남긴다.

## Completion evidence

독립적인 Rust crate 하나에 대해 예상 동작과 실패 사례를 설명하고, 테스트·컴파일·lint 결과로 이를 검증한다.
Compiler error를 단순 수정하는 데 그치지 않고 소유 관계가 왜 잘못되었는지 설명한다.

## References

- [The Rust Programming Language](https://doc.rust-lang.org/book/)
- [Cargo Book](https://doc.rust-lang.org/cargo/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
