# Unit 1 · Setup

실습 결과를 비교하려면 같은 dependency 환경에서 시작해야 한다.
이 unit에서는 deck 전용 환경을 준비하고, 첫 예제가 실행되는지 확인한다.
Span 사이의 관계를 해석하는 일은 다음 [First Trace](../02-first-trace/README.md)에서 다룬다.

## 준비할 것

Python 3.10+와 `uv`를 사용할 수 있는 terminal이 필요하다.
검증된 실행 환경은 Python 3.14.6과 OpenTelemetry API/SDK 1.45.0이다.
Dependency를 처음 설치할 때는 package 다운로드를 위한 network 연결이 필요하다.
이번 실습은 Collector, external backend, credential을 요구하지 않는다.

## Deck 환경 준비

Repository root에서 deck directory로 이동하고 설치한다.

```bash
cd decks/systems-opentelemetry
uv sync --locked
uv run --locked python --version
```

`pyproject.toml`은 허용하는 dependency 범위를, `uv.lock`은 재현할 실제 version을 담는다.
[`--locked`](https://docs.astral.sh/uv/concepts/projects/sync/#automatic-lock-and-sync)는 project 설정과 lockfile이
맞지 않으면 조용히 갱신하지 않고 실패하게 한다.
따라서 설치 실패를 해결하려고 lockfile부터 다시 만들기보다 현재 directory와 실패 메시지를 먼저 확인한다.

실제 설치된 API와 SDK version도 확인한다.

```bash
uv run --locked python -c 'from importlib.metadata import version; print(version("opentelemetry-api")); print(version("opentelemetry-sdk"))'
```

현재 lockfile에서는 두 값이 모두 `1.45.0`이다. 다른 Python 환경의 package를 확인하지 않도록 이후 명령도
deck directory에서 `uv run --locked`로 실행한다.

## 실행 확인

별도 auto-instrumentation 없이 실행한다. Sampling이나 Resource를 변경하는 외부 `OTEL_*` 설정이 없는 환경을 사용한다.

```bash
uv run --locked textbook/02-first-trace/first_trace.py
```

`validate_cart: ok`, `charge_payment: ok`와 span JSON이 나타나야 한다.
이는 local console 출력까지 확인한 결과다. Collector 전송이나 backend 저장을 검증한 것은 아니다.
이 단계에서는 output의 field를 모두 해석할 필요가 없다.

실행이 막히면 먼저 실패한 경계를 구분한다.

| Evidence | 먼저 확인할 것 |
| --- | --- |
| `uv` 명령을 찾지 못함 | terminal에서 사용할 tool 설치와 PATH |
| Project나 script를 찾지 못함 | 현재 directory가 deck root인지 |
| Package 다운로드 실패 | network 연결과 package registry 접근 |
| Lockfile 불일치 | 사용 중인 branch의 project 설정과 lockfile이 함께 준비됐는지 |
| Application 메시지만 있고 span JSON이 없음 | 외부 `OTEL_*` 설정과 실행 방식을 바꾸지 않았는지 |

## 다음 단계로 넘어갈 기준

사용한 Python과 dependency version을 기록하고, application 메시지와 span JSON을 구분해 찾는다.
Setup 확인은 환경이 준비됐다는 뜻이다. Identifier 관계를 예측하고 해석하는 목표는
[First Trace](../02-first-trace/README.md)의 실습과 평가로 확인한다.
