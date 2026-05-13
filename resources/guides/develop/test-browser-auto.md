# 브라우저 테스트 — 자동 모드 가이드

> 본 가이드는 `skills/develop/SKILL.md > Phase 4 / Step 1-2`에서 호출됨.
> Playwright Test Suite 기반 자동화·체크포인트·재테스트 루프를 정의.
> 사용자가 **"자동 테스트"**를 선택한 경우 (`AGENTS.md > ### develop > 지원 변수 > TEST_MODE = AUTO`) 본 가이드를 수행.

## 입력

- `AGENTS.md > ### develop > 지원 변수 > TEST_MODE = AUTO`
- `docs/develop/dev-plan.md` (TC-01~N 비즈니스 시나리오 + GAP-01~08 공통 시나리오)
- `docs/develop/api-test-result.md` (Phase 3 / Step 3 산출물 — 본 Step 진입 사전조건)
- 실행된 백킹/백엔드/프론트/AI 서비스 (Step 1-2a에서 기동)

## 개요

Playwright Test Suite로 비즈니스 시나리오(TC-01~N) + GAP 공통 시나리오(GAP-01~08)를 자동화 테스트 스크립트로 실행.
FAIL TC가 있으면 개발자가 수정 후 재테스트하는 루프를 최대 3회 반복.

## 진행 상태 체크포인트 (중단 복구)

Step 1-2는 실행 시간이 길어 세션 중단이 발생할 수 있음. 오케스트레이터는 각 sub-flow 완료 시 진행 상태를 체크포인트 파일에 기록하고, 재시작 시 완료된 단계를 건너뜀.

**체크포인트 파일**: `.temp/phase4-step1-checkpoint.json`
(단일 진실원: `skills/develop/SKILL.md > 인수 라우팅` 표)

```json
{
  "current_step": "1-2c",
  "iteration": 2,
  "completed_steps": ["1-2a", "1-2b", "1-2c"],
  "status": "in_progress"
}
```

**Step 1-2 시작 시:**
1. `.temp/phase4-step1-checkpoint.json`이 존재하고 `status`가 `"in_progress"`이면 → 중단된 세션 복구
2. `current_step` 위치부터 재개
3. `iteration` 값으로 현재 e2etest-{N}.md 번호 복원
4. 체크포인트가 없으면 → **1-2a**부터 시작

**각 sub-flow 완료 시:** `current_step`과 `completed_steps`를 갱신.
**Step 1-2 전체 완료 시:** `status`를 `"completed"`로 변경.

---

## 1-2a. Playwright 환경 설정 + 테스트 스크립트 작성 + 실행 → Agent: qa-engineer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/test-on-browser.md`
- **TASK**:
  1. Playwright 환경 설정 (최초 1회: `e2e/` 디렉토리 구성, `playwright.config.ts` 작성)
  2. 서비스 기동:
     - 백킹서비스: `docker compose up -d`
     - 백엔드: `python3 tools/run-backend.py --config-dir . --delay 5`
       (tools/ 미존재 시: `{NPD_PLUGIN_DIR}/resources/tools/customs/general/run-backend.py` 사용)
     - 프론트엔드: `python3 tools/run-frontend.py start --background --force`
       (tools/ 미존재 시: `{NPD_PLUGIN_DIR}/resources/tools/customs/general/run-frontend.py` 사용)
     - AI 서비스 (해당 시): `docker compose --profile ai up -d`
  3. Playwright MCP로 각 페이지의 UI 구조 탐색 (selector 확인용, 페이지 수만큼만)
  4. dev-plan.md의 TC 시나리오 + GAP 시나리오를 `e2e/tests/scenarios.spec.ts`로 작성
  5. `cd e2e && npx playwright test` 실행
  6. `.temp/test-results.json` 기반으로 결과 분석
  7. 전체 페이지 스크린샷을 `.temp/iter-{N}/`에 저장 (PO/SP가 Phase 4 / Step 2에서 활용)
- **EXPECTED OUTCOME**: `docs/develop/test/e2etest-{N}.md` (테스트 레포트), `e2e/tests/scenarios.spec.ts` (테스트 스크립트)
- **주의**: 직접 애플리케이션 코드를 수정하지 않음. 테스트 결과 레포트만 작성

## 1-2b. 오케스트레이터 판정

- e2etest-{N}.md의 FAIL TC 존재 여부 확인
- **FAIL 없음** → Step 1-2 완료, Phase 4 / Step 2로 진행
- **FAIL 있음** → 1-2c로

## 1-2c. 오케스트레이터 → 개발자에게 수정 지시

- e2etest-{N}.md의 이슈를 영향 파일 기준으로 분배:
  - backend-developer: 백엔드 API/로직 관련 버그
  - frontend-developer: 프론트엔드 UI/로직 관련 버그
  - ai-engineer: AI 파이프라인 관련 버그
- **영향 파일이 겹치면 순차 수정** (충돌 방지)
- 개발자들은 병렬 수정 실행

## 1-2d. QA 재테스트 → Agent: qa-engineer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/test-on-browser.md` (섹션 4-2, 7-2, 7-3)
- 프론트엔드 수정이 포함된 FAIL TC는 해당 페이지를 Playwright MCP로 재탐색 → `scenarios.spec.ts` selector 갱신 후 재실행
- qa-engineer가 FAIL TC만 재실행 (`cd e2e && npx playwright test --grep="TC-02|TC-05|..."`)
- 재테스트 시작 전 이전 iter-{N}의 PASS 스크린샷을 iter-{N+1}로 복사 후, FAIL TC만 재실행하여 덮어쓰기 (GUIDE 참조)
- **EXPECTED OUTCOME**: `docs/develop/test/e2etest-{N+1}.md`
- 전체 PASS → Step 1-2 완료, Phase 4 / Step 2 진행 / FAIL 잔존 → 1-2c 복귀
- **루프 제한: 최대 3회**
  - 3회 후 Critical 잔존 → Step 1-2 FAIL 처리, 블로커로 에스컬레이션
  - 3회 후 Major/Minor만 잔존 → known issues로 문서화 후 Phase 4 / Step 2 진행

---

## Step 1-2 자동 완료 조건

- [ ] 전체 TC PASS (비즈니스 TC + GAP TC) 또는 루프 제한 도달 후 known issues 문서화
- [ ] `e2e/tests/scenarios.spec.ts` 테스트 스크립트 존재
- [ ] `.temp/iter-{N}/` 디렉토리에 전체 TC 스크린샷 존재
- [ ] `.temp/phase4-step1-checkpoint.json`의 `status = "completed"`

## 산출물

- `docs/develop/test/e2etest-{N}.md` (반복 횟수만큼 누적)
- `e2e/tests/scenarios.spec.ts`
- `.temp/iter-{N}/tc-*.png` (전체 TC 스크린샷, Phase 4 / Step 2 입력)
- `.temp/phase4-step1-checkpoint.json` (status = completed)
