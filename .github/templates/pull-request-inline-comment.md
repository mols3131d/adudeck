(*GitHub가 파일과 line 위치를 제공한다. Inline comment 하나에는 구체적인 finding 하나를 기록한다.*)

{{ finding }}

{% if impact %}
**Impact:** {{ impact }}
{% endif %}

{% if required_change %}
**Required change:** {{ required_change }}
{% endif %}

{% if evidence %}
**Evidence:** {{ evidence }}
{% endif %}

(*Agent가 inline comment를 실질적으로 작성하거나 재작성한 경우 필요하다.*)
{% if author %}

```yaml
author:
{% for identity in author %}
  - {{ identity }}
{% endfor %}
```

{% endif %}
