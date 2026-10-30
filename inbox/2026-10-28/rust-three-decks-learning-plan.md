# Rust 3개 덱 구상: Python용 구현체와 Agentic Coding

Status: working note in `inbox/`; non-canonical.
**확정된 학습 의도와 초기 scope를 기록하며, 실제 교본/실습이 완성되었다는 뜻은 아니다.**

## 결정

Rust 학습을 하나의 광범위한 덱 대신 서로 다른 학습 책임을 가진 세 개의 **Backlog** 덱으로 시작한다.

| 덱 | 독립적인 학습 책임 | 완료 증거 |
| --- | --- | --- |
| [Rust 입문](../../decks/_backlog/language-rust_intro/README.md) | Python 사용자에게 Rust 문법, ownership, Cargo, 테스트, compiler feedback을 익히게 한다 | Rust crate 및 테스트·lint와 오류 설명 |
| [Rust 심화](../../decks/_backlog/language-rust_advanced/README.md) | 라이브러리 내부 설계, 메모리·동시성·성능 최적화 판단 능력을 기른다 | 정확성 테스트와 재현 가능한 성능 비교 |
| [Python에서 사용하는 Rust 구현체 실습](../../decks/_backlog/language-rust_python_extensions/README.md) | PyO3/maturin으로 Rust core를 Python API 뒤에 연결한다 | Python에서 import 가능한 wheel, 통합 테스트, baseline 대비 benchmark |

위 세 README가 **각 덱 scope와 목표의 canonical owner**이고, 이 메모는 선택 배경과 이후 작업의 판단 지점을 기록한다.
현재 filesystem backlog에만 기록하며 Notion과 별도 동기화하지 않는다.

## 사용자의 학습 목적

- 기존 주력 언어인 Python으로 사용하는 도구·라이브러리의 내부 구현을 Rust로 작성할 수 있다.
- **성능**: CPU/메모리 비용이 큰 연산을 Rust로 구현할 실질적 이유와 효과를 검증한다.
- **Agentic coding 효율성**: Rust의 명시적인 타입·소유권 계약과 compiler/test feedback이 agent의 반복 수정·검증에 어떤
  도움을 주는지 실험한다.
- **Python 연결성**: Python 사용성을 포기하지 않고 Rust를 선택적으로 활용한다.

이것은 *학습 동기 및 검증할 가설*이지, Rust를 쓰면 항상 Python보다 빠르거나 agent가 언제나 효율적이라는 보장이 아니다.
FFI 호출과 변환 비용, 빌드 시간, 학습 난도, 배포 복잡성도 함께 비교한다.

## 학습 순서와 경계

```text
Rust 입문
  ├─→ Rust 심화 (설계 / 성능 / 동시성)
  └─→ Python–Rust 구현체 실습 (API / binding / packaging)
                  ↑
           성능·동시성 과제는 심화에서 필요한 개념을 선별해 가져온다
```

- 입문에서 처음으로 Cargo·컴파일러와 Ownership을 배우며 Python 경험을 연결한다.
- 심화는 Python binding을 만들지 않는다. 독립적인 Rust core 설계와 측정이 주목적이다.
- 연동 실습은 Rust 언어 전체를 다시 가르치지 않고 Python API와 Rust 실행 경계에 집중한다.
- Python–Rust 실습은 입문 완료 후 시작할 수 있으며 심화 전체를 필수 선행 조건으로 두지 않는다.
- 구체적 초급/심화 교본, 버전 고정, `playground/`는 실제 제작 작업에 착수할 때 확정한다.

## 후속 제작 시 검증할 것

1. **입문**: Python 개념과 Rust 소유권의 차이를 단순 syntax translation이 아니라 예측·설명·디버깅 실습으로 확인.
2. **심화**: 변경 전후 결과 일치, 반복 benchmark, profiler evidence, 리소스 사용량 측정.
3. **연동**: Python baseline과 native extension의 type/error semantics 일치, `maturin develop` 및 wheel 재설치, 외부
   Python 측 통합 테스트.
4. **Agentic coding**: 같은 기능 요구에 대해 test-feedback 반복 횟수, 인간 검토가 필요한 결함, 수행 시간(빌드 포함)을
   관찰. 지표와 작업 조건이 다르면 단순 언어 우열로 해석하지 않는다.
5. **성능 경계**: 작은 입력·빈번한 FFI 호출과 큰 입력·batch 처리의 성능을 별도로 측정한다. Release build를 사용하고
   결과를 기록한다.
6. **버전/환경**: Rust edition, Rust/Python 지원 버전, PyO3/maturin 호환 범위를 실제 개발 시점의 공식 문서와 실행
   환경에서 확인한다.

## 착수 제안

첫 iteration은 세 덱 모두에 빈 장을 미리 생성하지 않고, Rust 입문의 첫 runnable crate와 테스트부터 시작한다. 그 다음
Rust 심화에서 검증 가능한 작은 라이브러리를 구현하고, Python–Rust 실습에서 Python baseline과 Rust-backed API를 나란히
비교한다.

## 참고 자료

- [Rust Book](https://doc.rust-lang.org/book/)
- [Cargo Book](https://doc.rust-lang.org/cargo/)
- [PyO3 User Guide](https://pyo3.rs/)
- [Maturin User Guide](https://www.maturin.rs/)
