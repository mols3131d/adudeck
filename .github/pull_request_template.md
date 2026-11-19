<!--
Summary, Goal, Tasks, Checklist, Boundaries를 순서대로 필수 H2 섹션으로 유지한다.
긴 섹션은 필요한 경우에만 H3로 나누고 Checklist의 세 H3 그룹은 유지한다.
제출 전에 미사용 선택 섹션, 빈 제목, placeholder, 작성 안내 주석을 제거한다.
-->

## Summary

<!-- 변경 결과를 요약하고 관련 Issue나 작업이 있다면 연결한다. -->

## Goal

<!-- 해결할 문제, 의도한 결과, 완료 기준을 설명한다. Tasks를 반복하지 않는다. -->

## Tasks

<!-- 실제 산출물을 - [ ] / - [x]로 추적하고 완료한 작업만 체크한다.
필요하면 H3로 나누되 변경 파일 목록과 commit history를 반복하지 않는다. -->

## Checklist

<!--
실제로 확인한 항목만 체크한다. 실패·대기·미확인 사항은 미체크하고 이유를 기록한다.
적용되지 않는 항목은 체크박스 대신 일반 bullet `- N/A: <이유>`로 교체한다.
변경의 성격과 위험에 비례하여 필요한 검증만 수행한다.
관련 없는 테스트, 중복 검증, 불필요한 외부 API·runtime 호출은 실행하지 않는다.
실행하지 않은 검증을 통과했다고 표시하지 않는다.
-->

### Self-review

<!--
Push마다 Self-review 체크를 초기화하고 직전 Reviewed HEAD 이후 변경을 검토한다.
첫 리뷰, 기존 SHA가 없는 경우, base가 변경된 경우에는 현재 전체 PR diff를 검토한다.
변경분이 전체 diff의 Goal과 Boundaries에 미치는 영향도 확인한다.
리뷰한 현재 HEAD의 전체 SHA를 `- Reviewed HEAD: <full SHA>` 일반 bullet로 기록한다.
SHA가 현재 HEAD와 다르면 Self-review는 다시 필요하다.
-->

> [!WARNING]
> Self-review는 기록된 `Reviewed HEAD`에 대해서만 유효하다. Push 후에는 체크를 해제하고 변경 사항을 재검토한 뒤, 체크 상태와 `Reviewed HEAD`를 갱신해야 한다.

- [ ] 현재 PR diff가 Goal과 Boundaries에 부합하는지 확인했다.
- [ ] 마지막 Reviewed HEAD 이후 변경(최초 리뷰라면 전체 diff)을 검토하고 의도하지 않은 변경이나 회귀를 확인했다.
- [ ] Self-review에서 발견된 차단 이슈가 남아 있지 않다.

### Automated checks

- [ ] 적용 가능한 formatting 및 lint 검증을 통과했다.
- [ ] 변경과 관련 있는 자동 테스트를 통과했다.
- [ ] 현재 HEAD에 적용되는 GitHub CI 검증을 통과했다.

### Verification

- [ ] 작업의 완료 기준과 필요한 수동/runtime 동작을 검증했다.
- [ ] 실패·생략·미확인 검증과 미해결 위험을 기록했다(없으면 없음을 확인했다).

## Boundaries

<!-- 의도적으로 제외한 범위, 주요 제약, 권한, 부작용, 후속 작업을 적는다.
해당 사항이 없으면 N/A로 명시한다. -->

<!-- 필요할 때만 Risks, Review Focus, Compatibility, Migration, Security,
Handoff, References 등 선택 H2 섹션을 추가한다. 비어 있으면 제거한다. -->
