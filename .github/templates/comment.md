(*Issue·PR 대화 댓글. 결론부터 작성하고 빈 섹션과 치환하지 않은 표기를 제출 전에 제거한다.*)

{{ message }}

{% if next_actions %}

## Next Actions

{% for action in next_actions %}

- [ ] {{ action }}
{% endfor %}
{% endif %}

{% if evidence %}

## Evidence

{% for item in evidence %}

- {{ item }}
{% endfor %}
{% endif %}

(*Agent가 댓글을 실질적으로 작성하거나 재작성한 경우 필요하다.*)
{% if author %}

```yaml
author:
{% for identity in author %}
  - {{ identity }}
{% endfor %}
```

{% endif %}
