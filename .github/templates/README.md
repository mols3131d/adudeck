---
description: GitHub Issue·PR·Review·Comment 양식의 선택과 작성자 표기 규칙을 확인한다.
---

# GitHub Templates

GitHub 기본 [Issue 양식](../ISSUE_TEMPLATE/issue.md)과 [상세 PR 양식](../pull_request_template.md)을 사용한다. [간결형 PR 후보](../PULL_REQUEST_TEMPLATE/compact-candidate.md)는 `template=compact-candidate.md`로 명시적으로 선택할 수 있다.

| Surface | Template |
| --- | --- |
| Issue·PR conversation comment | [Comment](comment.md) |
| PR review | [Review](pull-request-review.md) |
| PR inline review comment | [Inline comment](pull-request-inline-comment.md) |

괄호와 이탤릭체로 표시한 안내는 작성할 때만 참고하고 제출 전에 제거한다. `{{ value }}`, `{% if ... %}`, `{% for ... %}`는 실행되는 엔진이 아니라 작성 보조 표기다. 미사용 섹션, 예시와 치환하지 않은 표기를 제거한다. GitHub native 상태와 CI 결과는 반복하지 않는다.

Agent가 Review·Comment를 실질적으로 작성한 경우, 최종 본문 끝의 fenced YAML에 확인된 작성 주체를 기록한다.

```yaml
author:
  - <user>:<provider>:<product>:<model>
```

확인하지 못한 구성 요소는 `unknown`으로 기록한다. 사람이 작성한 내용을 그대로 게시한 경우에는 생략한다. PR 본문에는 attribution YAML을 요구하지 않는다.
