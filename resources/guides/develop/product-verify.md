# 제품 검증 가이드

> 본 가이드는 `skills/develop/SKILL.md > Phase 4 / Step 2`에서 호출됨.
> PO/SP가 제품을 검증하고 필요시 개선을 수행하는 절차를 정의.
> 자동 모드(Step 2-1)·수동 모드(Step 2-2) 두 sub-flow로 분기.
> **선행 조건**: Phase 4 / Step 1 (브라우저 테스트) 완료.

## 입력

- `AGENTS.md > ### develop > 지원 변수 > TEST_MODE` (AUTO 또는 MANUAL)
- `.temp/iter-{N}/tc-*.png` (Step 1-2의 자동 테스트 모드 산출물 — 자동 모드에서만)
- `docs/develop/test/e2etest-{N}.md` (Step 1-2 최종 레포트 — 자동 모드에서만)
- `docs/develop/dev-plan.md` (TC 시나리오 — 핵심 사용자 플로우 식별용)
- 기동 중인 백엔드/프론트엔드/AI 서비스 (수동 모드에서 PO/SP가 직접 순회)

## 모드 분기

- `TEST_MODE = AUTO` → `Step 2-1` 수행
- `TEST_MODE = MANUAL` → `Step 2-2` 수행

---

## Step 2-1. 자동 테스트 모드

> 사용자가 **"자동 테스트"**를 선택한 경우 이 Step을 수행.

Phase 4 / Step 1에서 생성된 스크린샷과 테스트 결과를 기반으로 PO/SP가 제품을 검증하고, 필요시 개선을 수행. 5단계 sub-flow.

### 진행 상태 체크포인트 (중단 복구)

**체크포인트 파일**: `.temp/phase4-step2-checkpoint.json`
(단일 진실원: `skills/develop/SKILL.md > 인수 라우팅` 표)

```json
{
  "current_step": "2-1c",
  "iteration": 1,
  "completed_steps": ["2-1a", "2-1b", "2-1c"],
  "status": "in_progress"
}
```

**Step 2-1 시작 시:**
1. `.temp/phase4-step2-checkpoint.json`이 존재하고 `status`가 `"in_progress"`이면 → 중단된 세션 복구
2. `current_step` 위치부터 재개
3. 체크포인트가 없으면 → **2-1a**부터 시작

### 2-1a. PO, SP 제품 검증 → Agent: product-owner + service-planner (병렬)

- **입력**: QA의 전체 페이지 스크린샷 (`.temp/iter-{N}/tc-*.png`, N은 Phase 4 / Step 1 최종 e2etest 레포트 번호) + 최종 e2etest 레포트
- PO와 SP는 병렬로 제품 검증 실행:
  - **PO** (product-owner): 스크린샷 + Playwright MCP로 사용자 관점 순회
  - **SP** (service-planner): 스크린샷 기반 UI/UX 레이아웃 검수
- **EXPECTED OUTCOME**:
  - `docs/develop/test/verify-po-{N}.md` (PO 제품 검증 레포트)
  - `docs/develop/test/verify-sp-{N}.md` (SP 제품 검증 레포트)
- **주의**: 직접 코드 수정하지 않음. 제품검증 결과 레포트만 작성

### 2-1b. 오케스트레이터 판정

- verify-po/sp-{N}.md의 Critical/Major 이슈 존재 여부 확인
- **이슈 없음** → Step 2-1 완료, Phase 4 / Step 3 (Final Report)로 진행
- **이슈 있음** → 2-1c로

### 2-1c. 오케스트레이터 → 개발자에게 개선 지시

- verify-po/sp-{N}.md의 이슈를 영향 파일 기준으로 분배 (backend-developer / frontend-developer / ai-engineer)
- 개발자들은 병렬 개선 실행
- **영향 파일이 겹치면 순차 수정** (충돌 방지)

### 2-1d. 변경 영역 재테스트 + PO/SP 재검증 (회귀 검증 통합)

본 sub-flow는 두 작업을 한 단계로 통합 수행. **PO/SP 재검증이 회귀 영향까지 함께 검증**하므로 별도의 전체 회귀 TC 재실행 단계는 두지 않음.

#### 2-1d-1. QA 변경 영역 스크린샷 재촬영 → Agent: qa-engineer

- 개선된 TC/페이지만 `cd e2e && npx playwright test --grep="TC-XX|..."` 로 재실행하여 스크린샷 갱신
- 이전 iter-{N}의 스크린샷을 iter-{N+1}로 복사 후, 개선된 영역만 덮어쓰기 (GUIDE 참조: `{NPD_PLUGIN_DIR}/resources/guides/develop/test-on-browser.md`)
- **EXPECTED OUTCOME**: `.temp/iter-{N+1}/` (변경 페이지만 갱신, 나머지는 이전 iter 복사본)

#### 2-1d-2. PO/SP 재검증 (회귀 영향 통합) → Agent: product-owner + service-planner (병렬)

- **입력**: 갱신된 스크린샷 (`.temp/iter-{N+1}/tc-*.png`) + 이전 verify-po/sp-{N}.md (이슈 목록 참조용)
- **검증 범위 (필수 4종)**:
  1. **변경 페이지**: 개발자가 수정한 화면이 의도대로 동작하는지
  2. **직접 의존 페이지**: 변경된 컴포넌트·API를 사용하는 모든 화면 (페이지 간 데이터 흐름 일치 확인)
  3. **핵심 사용자 플로우 1~2개**: `docs/develop/dev-plan.md`의 TC 시나리오 중 **Critical 등급** 플로우 1~2개를 Playwright MCP로 끝까지 수행 (예: 회원가입 → 로그인 → 결제 1사이클)
  4. **데이터 정합성 spot check**: 합계·필터·정렬·집계 등 시각적으로 검증 가능한 계산 결과 1~2개 점검
- **EXPECTED OUTCOME**:
  - `docs/develop/test/verify-po-{N+1}.md`
  - `docs/develop/test/verify-sp-{N+1}.md`
- **주의**: 직접 코드 수정하지 않음. 재검증 결과 레포트만 작성. 회귀 의심 사항 발견 시 레포트의 "회귀 의심" 섹션에 명시.

### 2-1e. 오케스트레이터 재판정

- verify-po/sp-{N+1}.md의 Critical/Major 이슈 + "회귀 의심" 섹션 존재 여부 확인
- **이슈 없음** → Step 2-1 완료, Phase 4 / Step 3 (Final Report)로 진행
- **이슈 있음** → 2-1c로 복귀 (개선 루프, 최대 2회)
  - 2회 후 잔여 개선사항 → known improvements로 문서화 후 Phase 4 / Step 3로 진행

### Step 2-1 자동 완료 조건

- [ ] PO/SP Critical/Major 이슈 0건
- [ ] 회귀 의심 0건 (PO/SP 재검증 4종 범위 모두 OK)
- [ ] 개선 루프: 최대 2회
- [ ] `.temp/phase4-step2-checkpoint.json`의 `status = "completed"`

---

## Step 2-2. 수동 테스트 모드

> 사용자가 **"수동 테스트"**를 선택한 경우 이 Step을 수행.
> 사용자가 직접 제품 품질을 검증하고, AI가 개선을 구현.
> **AskUserQuestion 도구를 사용하지 않는다.** 모든 사용자 응답 대기는 텍스트 안내 + 자유 입력.

### 2-2a. 제품 피드백 수집 (대화형)

아래 안내를 텍스트로 출력하고 사용자 메시지를 대기 (**AskUserQuestion 사용 금지**).

```
브라우저에서 전체 서비스를 둘러보며 UX/UI 개선점이 있으면 알려주세요.
(디자인, 동선, 레이아웃, 성능 등)

💡 AI가 Playwright MCP로 같은 브라우저를 보고 있습니다.
- 개선이 필요한 화면으로 이동한 뒤 개선점을 설명해 주세요.
- AI에게 직접 브라우저 액션을 요청할 수도 있습니다.
- 개선할 점이 없으면 "검증 완료"라고 입력해 주세요.
```

**사용자 응답 처리:**
- 개선 요청 → 2-2b 진행
- "검증 완료" → Step 2-2 완료, Phase 4 / Step 3 진행

### 2-2b. 개선 루프 (대화형)

사용자가 개선을 요청하면:
1. `browser_snapshot()`으로 현재 화면을 확인하여 개선점을 함께 파악
2. 개선 내용을 영향 파일 기준으로 분배 (backend-developer / frontend-developer / ai-engineer)
3. 개발자 에이전트가 개선
4. 개선 완료 후 아래 안내를 텍스트로 출력하고 사용자 메시지를 대기 (**AskUserQuestion 사용 금지**)

```
개선이 완료되었습니다. 브라우저를 새로고침하여 확인해 주세요.
- 추가 개선이 필요하면 해당 화면에서 설명해 주세요.
- AI에게 브라우저 액션을 요청할 수도 있습니다.
- 만족하시면 "검증 완료"라고 입력해 주세요.
```

**사용자 응답 처리:**
- 추가 개선 요청 → 2-2b 반복
- "검증 완료" → Step 2-2 완료, Phase 4 / Step 3 진행

### Step 2-2 수동 완료 조건

- [ ] 사용자가 제품 검증 완료 확인 ("검증 완료" 입력)

---

## 산출물

### 자동 모드 (Step 2-1)
- `docs/develop/test/verify-po-{N}.md` (반복 횟수만큼 누적)
- `docs/develop/test/verify-sp-{N}.md` (반복 횟수만큼 누적)
- `.temp/iter-{N+1}/tc-*.png` (변경 페이지만 갱신된 스크린샷)
- `.temp/phase4-step2-checkpoint.json` (status = completed)

> ※ 별도 회귀 e2etest-{N+1}.md는 생성되지 않음 (PO/SP 재검증 4종 범위가 회귀 영향을 통합 검증).

### 수동 모드 (Step 2-2)
- 개선된 백엔드/프론트엔드/AI 코드 (사용자 보고 개선점 반영)
- Phase 4 / Step 3 (Final Report) 입력용 대화 이력
