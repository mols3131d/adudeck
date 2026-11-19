<!--
PR 작성 규칙
- Summary, Goal, Tasks, Checklist, Boundaries를 이 순서의 필수 H2로 유지한다.
- 주제·작업 흐름이 길 때만 H3로 나눈다. Checklist의 세 H3 그룹은 유지한다.
- PR 제출 전 사용하지 않는 선택 섹션, 빈 제목, placeholder, 작성 안내 주석을 제거한다.
-->

## Summary

<!-- 변경 결과를 짧게 요약한다. 관련 Issue나 작업이 있으면 연결한다. -->

## Goal

<!-- 해결할 문제, 의도한 결과, 완료 기준을 설명한다. Tasks를 반복하지 않는다. -->

## Tasks

<!-- 구체적인 산출물을 - [ ] / - [x]로 추적한다. 완료한 작업만 체크한다.
     필요하면 H3로 묶되 파일 변경 목록이나 commit history를 복제하지 않는다. -->

## Checklist

<!--
실제로 충족한 기준만 체크한다. 실패·대기·미확인 항목은 미체크 상태로 두고 이유를 기록한다.
적용하지 않는 항목은 체크박스 전체를 '- N/A: <이유>'라는 일반 bullet로 바꾼다.
N/A에 체크박스를 사용하면 GitHub task progress가 왜곡된다.

변경 종류에 따라 검증 항목을 추가하되, 해당하지 않는 검증을 모든 PR에 강제하지 않는다.
- Deck: 학습 목표·선행 개념·설명/실습/평가의 연결, 상대 경로, 실습 재현성,
  version-sensitive 내용의 현재 공식 자료 근거를 필요한 범위에서 확인한다.
- Agent Assets: .rulesync/의 canonical source를 수정하고 필요한 projection 및
  rulesync 검증을 수행한다. generated file만 단독 수정하지 않는다.
- Code / scripts / automation: 변경에 맞는 test와 실행 검증, 비용이 드는
  외부 API·runtime 호출의 범위 및 부작용을 확인한다.

저장소 검증 entrypoint: mise run format:check, mise run test, mise run ci:fast.
CI의 현재 HEAD 검증 결과는 ci/validated 상태를 확인한다.
-->

### Self-review

<!--
Push할 때마다 Self-review 체크를 해제하고 이전 Reviewed HEAD와 새 PR HEAD를 비교한다.
첫 리뷰, 이전 SHA를 알 수 없는 경우, base가 바뀐 경우에는 현재 전체 PR diff를 검토한다.
새 변경의 영향뿐 아니라 전체 diff의 Goal 및 Boundaries 적합성까지 확인한다.
현재 HEAD를 리뷰한 뒤에만 아래에 일반 bullet '- Reviewed HEAD: <full SHA>'를 기록/갱신한다.
기록한 SHA가 현재 HEAD와 다르면 Self-review는 다시 해야 한다.
-->

Self-review는 기록된 `Reviewed HEAD`에서만 유효하다. Push 후 재검토한다.

- [ ] 현재 PR diff가 Goal과 Boundaries에 부합하는지 확인했다.
- [ ] 마지막 Reviewed HEAD 이후 변경(최초 리뷰라면 전체 diff)을 검토하고 회귀·의도하지 않은 변경을 확인했다.
- [ ] Self-review에서 발견된 차단 이슈가 남아 있지 않다.

### Automated checks

- [ ] 해당하는 formatting 및 lint 검증을 통과했다.
- [ ] 해당하는 automated tests를 통과했다.
- [ ] 현재 HEAD에 적용되는 GitHub CI 검증을 통과했다.

### Verification

- [ ] 작업별 완료 기준과 해당하는 runtime/manual 동작을 검증했다.
- [ ] 실패·생략·미확인 검증과 남은 위험을 기록했다(없다면 없음을 확인했다).

## Boundaries

<!-- 의도적으로 제외한 범위, 주요 제약, 권한, 부작용, 후속 작업을 적는다.
     해당 사항이 전혀 없으면 N/A로 명시한다. -->

<!-- 필요한 경우 Risks, Review Focus, Compatibility, Migration, Security, Handoff,
     References 같은 선택 H2를 추가하되 비어 있으면 제거한다. -->
