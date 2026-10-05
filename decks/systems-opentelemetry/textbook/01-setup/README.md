# 1장 · 환경 준비

실습 결과를 비교하려면 같은 버전의 의존 패키지를 사용해야 한다.
이 장에서는 덱 전용 환경을 준비하고, 첫 예제가 실행되는지 확인한다.
스팬 사이의 관계를 해석하는 일은 다음 [첫 트레이스](../02-first-trace/README.md)에서 다룬다.

## 준비할 것

Python 3.10+와 `uv`를 사용할 수 있는 터미널이 필요하다.
검증된 실행 환경은 Python 3.14.6과 OpenTelemetry API/SDK 1.45.0이다.
의존 패키지를 처음 설치할 때는 패키지 다운로드를 위한 네트워크 연결이 필요하다.
이번 실습에는 Collector나 외부 백엔드, 인증 정보가 필요하지 않다.

## 실습 환경 준비

저장소 최상위 디렉터리에서 덱 디렉터리로 이동하고 의존 패키지를 설치한다.

```bash
cd decks/systems-opentelemetry
uv sync --locked
uv run --locked python --version
```

`pyproject.toml`은 허용하는 의존 패키지 범위를, `uv.lock`은 재현할 실제 버전을 담는다.
[`--locked`](https://docs.astral.sh/uv/concepts/projects/sync/#automatic-lock-and-sync)는 프로젝트 설정과 잠금 파일이
맞지 않으면 조용히 갱신하지 않고 실패하게 한다.
따라서 설치 실패를 해결하려고 잠금 파일부터 다시 만들기보다 현재 디렉터리와 실패 메시지를 먼저 확인한다.

실제 설치된 API와 SDK 버전도 확인한다.

```bash
uv run --locked python -c 'from importlib.metadata import version; print(version("opentelemetry-api")); print(version("opentelemetry-sdk"))'
```

현재 잠금 파일에서는 두 값이 모두 `1.45.0`이다. 다른 Python 환경의 패키지를 확인하지 않도록 이후 명령도
덱 디렉터리에서 `uv run --locked`로 실행한다.

## 실행 확인

별도 자동 계측 없이 실행한다. 샘플링이나 Resource를 변경하는 외부 `OTEL_*` 설정이 없는 환경을 사용한다.

```bash
uv run --locked textbook/02-first-trace/first_trace.py
```

`validate_cart: ok`, `charge_payment: ok`와 스팬 JSON이 나타나야 한다.
이는 로컬 콘솔 출력까지 확인한 결과다. Collector 전송이나 백엔드 저장을 검증한 것은 아니다.
이 단계에서는 출력의 필드를 모두 해석할 필요가 없다.

실행이 막히면 먼저 실패한 경계를 구분한다.

| 증상 | 먼저 확인할 것 |
| --- | --- |
| `uv` 명령을 찾지 못함 | 터미널에서 사용할 도구 설치와 PATH |
| 프로젝트나 스크립트를 찾지 못함 | 현재 디렉터리가 덱 최상위 디렉터리인지 |
| 패키지 다운로드 실패 | 네트워크 연결과 패키지 저장소 접근 |
| 잠금 파일 불일치 | 사용 중인 브랜치의 프로젝트 설정과 잠금 파일이 함께 준비됐는지 |
| 애플리케이션 메시지만 있고 스팬 JSON이 없음 | 외부 `OTEL_*` 설정과 실행 방식을 바꾸지 않았는지 |

## 다음 단계로 넘어갈 기준

사용한 Python과 의존 패키지 버전을 기록하고, 애플리케이션 메시지와 스팬 JSON을 구분해 찾는다.
여기까지 확인했다면 실습을 시작할 준비가 된 것이다. 식별자 관계를 예측하고 해석하는 능력은
[첫 트레이스](../02-first-trace/README.md)의 실습과 평가로 확인한다.
