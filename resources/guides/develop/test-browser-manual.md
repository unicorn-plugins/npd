# 브라우저 테스트 — 수동 모드 가이드

> 본 가이드는 `skills/develop/SKILL.md > Phase 4 / Step 1-3`에서 호출됨.
> 사용자가 직접 브라우저에서 테스트하며, AI는 이슈 수정을 담당하는 대화형 흐름을 정의.
> 사용자가 **"수동 테스트"**를 선택한 경우 (`AGENTS.md > ### develop > 지원 변수 > TEST_MODE = MANUAL`) 본 가이드를 수행.

## 입력

- `AGENTS.md > ### develop > 지원 변수 > TEST_MODE = MANUAL`
- `docs/develop/dev-plan.md` (TC-01~N 시나리오 목록 표시용)
- `{PROJECT_DIR}/.env` (FRONTEND_PORT 값 로드)
- `docs/develop/api-test-result.md` (Phase 3 / Step 3 산출물 — 본 Step 진입 사전조건)

## 공통 원칙

- 본 가이드의 모든 사용자 응답 대기 단계에서 **AskUserQuestion 도구를 사용하지 않는다**.
- 안내 메시지를 텍스트로 출력하고 사용자의 자유 입력을 대기한다.
- AI는 Playwright MCP로 사용자와 동일한 브라우저를 보면서 함께 분석·수정한다.

---

## 1-3a. 서비스 기동 + 브라우저 열기

1. 백킹서비스 기동: `docker compose up -d`
2. 백엔드 서비스 기동: `python3 tools/run-backend.py --config-dir . --delay 5`
   (tools/ 미존재 시: `{NPD_PLUGIN_DIR}/resources/tools/customs/general/run-backend.py` 사용)
3. 프론트엔드 개발 서버 기동: `python3 tools/run-frontend.py start --background --force`
   (tools/ 미존재 시: `{NPD_PLUGIN_DIR}/resources/tools/customs/general/run-frontend.py` 사용)
4. AI 서비스 기동 (해당 시): `docker compose --profile ai up -d`
5. `.env`에서 `FRONTEND_PORT` 값을 읽어 Playwright MCP로 브라우저 열기:
   `browser_navigate("http://localhost:{FRONTEND_PORT}")`

## 1-3b. TC 목록 제시 + 사용자 테스트 (대화형)

dev-plan.md의 테스트 시나리오(TC-01~N)를 사용자에게 텍스트로 표시한 뒤, 사용자의 자유 입력을 대기.
**AskUserQuestion을 사용하지 않는다.** 아래 안내 메시지를 텍스트로 출력하고 사용자 메시지를 대기.

```
브라우저가 열렸습니다. 아래 TC를 참고하여 직접 테스트해 주세요.

{TC 목록 표시}

💡 AI가 Playwright MCP로 같은 브라우저를 보고 있습니다.
- 이슈를 발견하면 **해당 화면으로 이동한 뒤** 에러 현상을 설명해 주세요.
- AI에게 직접 클릭, 입력, 페이지 이동 등 브라우저 액션을 요청할 수도 있습니다.
  (예: "회원가입 버튼 클릭해 봐", "이메일 필드에 test@test.com 입력해 봐")
- AI는 browser_snapshot()으로 현재 화면을 확인하고 문제를 함께 분석합니다.
- 테스트가 모두 끝나면 "테스트 완료"라고 입력해 주세요.
```

**사용자 응답 처리:**
- 이슈 설명 또는 액션 요청 → 1-3c 진행
- "테스트 완료" → Step 1-3 완료, Phase 4 / Step 2 진행

## 1-3c. 이슈 수정 루프 (대화형)

사용자가 이슈를 보고하면:
1. `browser_snapshot()`으로 현재 화면을 확인하여 이슈를 함께 파악
2. 이슈 내용을 영향 파일 기준으로 분배 (backend-developer / frontend-developer / ai-engineer)
3. 개발자 에이전트가 수정
4. 수정 완료 후 아래 안내를 텍스트로 출력하고 사용자 메시지를 대기 (**AskUserQuestion 사용 금지**)

```
수정이 완료되었습니다. 브라우저를 새로고침하여 확인해 주세요.
- 다른 이슈가 있으면 해당 화면에서 설명해 주세요.
- AI에게 브라우저 액션을 요청할 수도 있습니다.
- 전체 OK이면 "테스트 완료"라고 입력해 주세요.
- 수정이 안 되었으면 상황을 설명해 주세요.
```

**사용자 응답 처리:**
- 다른 이슈 설명 → 1-3c 반복
- "테스트 완료" → Step 1-3 완료, Phase 4 / Step 2 진행
- 재수정 요청 → 추가 정보 기반 재수정 후 안내 반복

---

## Step 1-3 수동 완료 조건

- [ ] 사용자가 전체 TC OK 확인 ("테스트 완료" 입력)

## 산출물

- 수정된 백엔드/프론트엔드/AI 코드 (사용자 보고 이슈 반영)
- Phase 4 / Step 3 (Final Report) 입력용 대화 이력 (보고된 이슈 + 수정 내역)

> 자동 모드와 달리 e2etest-{N}.md / 스크린샷 산출물은 생성되지 않음. Final Report는 대화 이력 기반.
