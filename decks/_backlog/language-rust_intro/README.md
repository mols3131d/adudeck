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

## Completion evidence

독립적인 Rust crate 하나에 대해 예상 동작과 실패 사례를 설명하고, 테스트·컴파일·lint 결과로 이를 검증한다.
Compiler error를 단순 수정하는 데 그치지 않고 소유 관계가 왜 잘못되었는지 설명한다.

## References

- [The Rust Programming Language](https://doc.rust-lang.org/book/)
- [Cargo Book](https://doc.rust-lang.org/cargo/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
