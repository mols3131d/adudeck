# Python에서 사용하는 Rust 구현체 실습

**Python API는 Python 사용자에게 자연스럽게 유지하고, 성능·정확성·배포 요구가 있는 내부 구현을 Rust로 작성**하는
hands-on 덱이다. Agentic coding을 통해 구현·실험·수정·검증하는 과정을 학습한다.

현재는 후속 학습을 위한 backlog이다. 실습 프로젝트와 배포 artifact는 아직 작성되지 않았다.

## Goal

학습 후에는 다음을 할 수 있어야 한다.

- Python으로 동작과 테스트를 먼저 정의하고, 성능이 중요한 부분을 profiling으로 찾아낸다.
- Rust 구현을 Python에서 호출할 수 있도록 PyO3와 maturin으로 extension module을 작성한다.
- Python/Rust 경계에서 타입 변환, ownership, copy, error mapping, 호출 비용을 설명한다.
- Rust 측 단위 테스트와 Python 측 통합 테스트로 동일한 결과와 실패 동작을 검증한다.
- Release 빌드, wheel 설치와 Python import를 재현하고 baseline 대비 성능 차이를 측정한다.
- Agent가 변경한 Python API와 Rust core의 계약이 함께 유지되는지 검토한다.

## Prerequisites

- [Rust 입문](../language-rust_intro/README.md)의 학습 목표
- Python의 패키징, 가상환경, `pytest`와 간단한 profiling 경험
- [Rust 심화](../language-rust_advanced/README.md)는 최적화·동시성 단계에서 유용하며, 모든 단원을 선행 완료할 필요는
  없다.

## Learning scope

1. Python-only baseline: API, test case, profiler로 hotspot 찾기
2. Rust `lib` 구현과 동일 동작 검증
3. PyO3 `#[pyfunction]` / `#[pymodule]` 기반 최소 binding
4. Maturin으로 local develop, release build, wheel 설치·import
5. Type conversion, ownership boundary, exception mapping, batch 처리
6. `pytest` + Rust tests, ABI / interpreter compatibility와 packaging 확인
7. End-to-end benchmark: 호출 오버헤드, 데이터 전송 비용, 작은 입력과 큰 입력 비교
8. Agentic iteration: 요구사항 → 구현 → 컴파일/테스트 → 벤치마크 → 수정

첫 프로젝트 후보는 Python용 텍스트·레코드 처리 라이브러리의 작은 핵심 함수다. 실제 Python 병목이 확인되지 않으면 Rust
이식이 최적의 선택이라고 가정하지 않는다.

## Completion evidence

Python에서 `import` 가능한 installable wheel 하나를 만들고, Python baseline과 Rust-backed 구현의 동작 일치·실패
처리·성능 측정을 재현한다. 측정에서 이점이 없거나 maintenance cost가 더 크면 Python 구현을 유지한다는 판단도 유효한
결과다.

## References

- [PyO3 User Guide](https://pyo3.rs/)
- [Maturin User Guide](https://www.maturin.rs/)
- [Python packaging guide](https://packaging.python.org/)
