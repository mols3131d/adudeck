# Rust 심화

Rust 입문 이후, **고성능·신뢰성 있는 라이브러리의 내부 구현을 설계하고 agent가 만든 변경을 검증**하는 학습 덱이다.

현재는 후속 학습을 위한 backlog이다. 교본이나 실습 코드는 아직 작성되지 않았다.

## Goal

학습 후에는 다음을 할 수 있어야 한다.

- Borrowing, lifetime, trait, generic, error model을 복합적인 라이브러리 코드에서 설명하고 설계한다.
- 복사·할당·데이터 구조·API 경계의 비용을 식별하고 성능을 측정한 뒤 개선한다.
- Iterator, collection, memory layout, allocation 선택의 정확성과 trade-off를 설명한다.
- Thread, `Send`/`Sync`, shared state와 synchronization을 올바르게 선택한다.
- 요구사항·불변조건·테스트·benchmark를 통해 agent 생성 코드의 correctness와 성능 회귀를 검증한다.

## Prerequisites

[Rust 입문](../language-rust_intro/README.md)의 학습 목표를 충족해야 한다. Python의 profiling 및 기본 동시성 경험은 도움이 되지만 필수는 아니다.

## Learning scope

1. 소유권 모델 심화: lifetime, trait bounds, generics, API design
2. 자료구조 선택과 allocation / zero-copy 지향 설계의 비용 모델
3. 오류의 표현, panic boundary, invariant와 property-oriented testing
4. Concurrency: threads, channels, locks, `Send`/`Sync`
5. Async/await와 runtime 개념: 동시성과 병렬성 구분
6. Profiling, criterion-based benchmarking, 최적화 전후 회귀 검증
7. 작은 성능 민감 라이브러리의 설계 변경·검증

`unsafe`/FFI는 안전한 API로 표현할 수 없는 요구가 확인되었을 때 경계와 invariant를 학습한다. GPU, embedded, kernel 개발이나 production distributed system 구축은 core 범위가 아니다.

## Completion evidence

같은 기능의 기준 구현과 개선 구현에 대해 correctness test와 반복 benchmark를 제시한다.
최적화가 실제로 도움이 되는 조건, 되지 않는 조건, 복잡성 비용을 설명한다. Agent의 구현 속도와 Rust 실행 성능을 같은 지표로 섞지 않는다.

## References

- [The Rust Reference](https://doc.rust-lang.org/reference/)
- [The Rustonomicon](https://doc.rust-lang.org/nomicon/)
- [Rust Performance Book](https://nnethercote.github.io/perf-book/)
