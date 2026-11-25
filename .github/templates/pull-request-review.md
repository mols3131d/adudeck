## Summary

{{ summary }}

{% if scope %}

## Scope

{% for item in scope %}

- {{ item }}
{% endfor %}
{% endif %}

## Findings

{% if findings %}
{% for finding in findings %}

### {{ finding.title }}

**Impact:** {{ finding.impact }}

**Required change:** {{ finding.required_change }}

{% if finding.evidence %}
**Evidence:** {{ finding.evidence }}
{% endif %}

{% endfor %}
{% elif has_inline_findings %}
Finding은 inline review comment를 참고한다.
{% else %}
검토 범위에서 조치가 필요한 finding을 발견하지 못했다.
{% endif %}

## Verification

{% for check in verification %}

- {{ check }}
{% endfor %}

{% if remaining_risks %}

## Remaining Risks

{% for risk in remaining_risks %}

- {{ risk }}
{% endfor %}
{% endif %}

(*Review decision(comment/approve/request changes)은 GitHub가 소유한다. 근거가 확인된 판단만 기록한다.*)
(*Agent가 review를 실질적으로 작성하거나 재작성한 경우 필요하다.*)
{% if author %}

```yaml
author:
{% for identity in author %}
  - {{ identity }}
{% endfor %}
```

{% endif %}
