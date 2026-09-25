# 0. Environment: 첫 호출까지 필요한 것만 준비한다

첫 실습의 목표는 environment tooling을 배우는 것이 아니라 **OpenAI SDK call을 한 번 성공시키는 것**이다.

필요한 것은 세 가지다.

```text
Python 3.10+
uv
OPENAI_API_KEY
```

## 0.1 Deck project dependency 준비

이 deck의 dependency requirement는 `pyproject.toml`, 현재 exact resolution은 `uv.lock`이 관리한다.

```toml
[project]
requires-python = ">=3.10"
dependencies = [
  "openai>=3.19.2,<4",
  "pydantic>=2,<3",
]
```

Repository root에서 deck directory로 이동해 committed lockfile 그대로 project environment를 준비한다.

```bash
cd decks/ai-openai_sdk
uv sync --locked
```

`3.19.2`는 이 deck을 검토한 baseline이고 dependency range는 compatible v3 update를 허용한다. `uv.lock`은 현재 deck에서
실제로 resolve한 exact dependency set을 기록한다. Playground file 자체에는 PEP 723 dependency metadata를 두지 않는다.
Dependency ownership을 deck project에 유지하기 위해서다.

`uv run`은 이 project environment를 사용한다.

```bash
uv run playground/request_response.py
```

`uv`가 설치되어 있지 않다면 [uv 공식 설치 문서](https://docs.astral.sh/uv/getting-started/installation/)를 따른다.

## 0.2 API key 설정

실제 key를 source file에 적지 않는다.

macOS/Linux:

```bash
export OPENAI_API_KEY='...'
```

PowerShell:

```powershell
$env:OPENAI_API_KEY = '...'
```

SDK는 기본적으로 이 environment variable을 사용할 수 있다.

## 0.3 첫 호출

Deck directory에서 실행한다.

```bash
uv run playground/request_response.py
```

정상이라면 한 줄짜리 model output이 출력된다.

Official OpenAI API를 호출하는 playground는 API usage와 quota를 소비할 수 있으며 계정 설정에 따라 비용이 발생할 수 있다.
학습 전에 사용할 model과 account usage policy를 확인한다.

이 시점에서 아직 request IDs나 output item 구조를 알 필요는 없다.
첫 성공 이후 Unit 1에서 같은 file에 관찰 코드를 조금씩 추가한다.

## 0.4 Model 변경은 필요할 때만

예제의 기본 model은 현재 deck baseline의 `gpt-5.5`다.

다른 accessible model을 사용하려면 source를 수정하지 않고 environment로 바꿀 수 있다.

```bash
export OPENAI_MODEL='gpt-5.5'
```

Playground는 다음처럼 읽는다.

```python
model = os.getenv("OPENAI_MODEL", "gpt-5.5")
```

## 0.5 문제가 있을 때만 preflight 사용

첫 호출이 되지 않을 때 optional helper를 실행한다.

```bash
python scripts/setup.py
```

이 helper는 다음만 확인한다.

- Python version
- `uv`가 PATH에 있는지
- deck `pyproject.toml`과 `uv.lock`이 존재하는지
- `OPENAI_API_KEY`가 현재 process environment에 있는지
- 첫 playground path가 존재하는지

환경을 자동으로 바꾸거나 provider를 대신 선택하지 않는다.

## 0.6 Ollama는 전체 deck의 대체 environment가 아니다

Ollama는 OpenAI-compatible endpoint 일부를 지원하므로 stateless Responses 실험에는 사용할 수 있다.
하지만 현재 Responses compatibility는 non-stateful subset이며 `previous_response_id`와 `conversation`을 지원하지 않는다.

Unit 2 이후에는 이 차이가 학습 결과에 직접 영향을 준다.

따라서:

```text
official OpenAI API
→ canonical learning path

Ollama compatibility
→ 특정 stateless experiment를 위한 optional comparison
```

로 취급한다.

Provider compatibility를 학습하려는 별도 목적이 아니라면, 처음부터 base URL과 provider abstraction을 추가하지 않는다.

## 0.7 준비 완료 기준

다음 command가 성공하면 Unit 1을 시작할 수 있다.

```bash
uv run playground/request_response.py
```

이제 [01-client-request-response.md](01-client-request-response.md)로 이동한다.
