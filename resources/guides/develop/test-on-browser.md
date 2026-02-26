# 브라우저 테스트

## 목적

프론트엔드와 백엔드/AI 서비스 간 E2E 동작을 Playwright MCP 도구로 실제 브라우저에서 검증한다.
`docs/develop/dev-plan.md`의 테스트 시나리오(TC-01~N)를 순서대로 실행하여, 사용자 관점에서 핵심 기능이 동작하는지 확인한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 테스트 시나리오 | `docs/develop/dev-plan.md` 섹션 9 | 시나리오 목록 추출 |
| API 테스트 결과 | `docs/develop/api-test-result.md` | API 정상 동작 확인 전제 |
| 샘플 데이터 | `{service}/src/test/resources/data/` | API 테스트에서 생성된 데이터 재활용 |
| 서비스 실행기 | `{PLUGIN_DIR}/resources/tools/customs/general/run-intellij-service-profile.py` | 백엔드 서비스 실행 |

## 사전 조건

- Step 4-3(API 테스트) 전체 PASS 완료
- 백킹서비스 + 백엔드 서비스 기동 상태 (API 테스트에서 기동된 상태 유지)
- 필요시 AI 서비스 기동 상태

---

## 방법론

### 1. 프론트엔드 개발 서버 기동

<!-- IF PLATFORM == REACT -->
```bash
cd frontend && npm run dev &
sleep 10
curl -s -o /dev/null -w '%{http_code}' http://localhost:5173
```
<!-- ELIF PLATFORM == VUE -->
```bash
cd frontend && npm run dev &
sleep 10
curl -s -o /dev/null -w '%{http_code}' http://localhost:5173
```
<!-- ELIF PLATFORM == FLUTTER -->
```bash
cd frontend && flutter build web 2>&1 | tail -5
python3 -m http.server 5173 -d frontend/build/web &
sleep 3
curl -s -o /dev/null -w '%{http_code}' http://localhost:5173
```
<!-- ENDIF -->

- HTTP 200 응답이어야 진행 가능

### 2. 인증 토큰 주입 (OAuth2/소셜 로그인 프로젝트)

OAuth2 소셜 로그인은 외부 Provider 리디렉트가 필요하므로 Playwright MCP로 직접 수행할 수 없다.
API 테스트(Step 4-3)에서 구현한 테스트 전용 로그인 엔드포인트를 활용하여 브라우저에 인증 상태를 주입한다.

**인증 방식 확인:**
- JWT 자체 로그인만 사용 → 브라우저에서 직접 로그인 폼 입력으로 테스트 가능 → **이 섹션 건너뜀**
- OAuth2/소셜 로그인 사용 → 아래 절차로 토큰 주입

**토큰 주입 절차:**

1. 테스트 전용 로그인 API로 토큰 획득:
```bash
TOKEN=$(curl -s -X POST http://localhost:{auth_port}/api/test/login \
  -H 'Content-Type: application/json' \
  -d '{"userId": "test-user-01"}' | jq -r '.accessToken')
echo $TOKEN
```

2. Playwright MCP로 브라우저에 토큰 주입:
```
browser_navigate("http://localhost:5173")
browser_evaluate("localStorage.setItem('accessToken', '{TOKEN}')")
browser_navigate("http://localhost:5173/dashboard")  → 인증 후 랜딩 페이지
browser_snapshot()  → 로그인 상태 확인
```

- 토큰 저장 키(`accessToken`)는 프론트엔드 코드의 실제 키와 일치해야 한다
  - 프론트엔드 소스에서 `localStorage.setItem` 또는 `sessionStorage.setItem`을 검색하여 실제 키명을 확인
  - cookie 기반인 경우: `browser_evaluate("document.cookie = 'token={TOKEN}; path=/'")` 사용
- 토큰 주입 후 페이지 리로드하면 인증된 상태로 동작한다
- **이후 모든 시나리오는 인증된 상태에서 진행한다**

### 3. 시나리오 목록 추출

`docs/develop/dev-plan.md`의 테스트 시나리오(TC-01~N)를 추출한다.

#### 3-1. GAP 공통 시나리오 추가

비즈니스 시나리오(TC-01~N) 이후에, 아래 GAP 패턴별 TC를 프로젝트에 맞게 인스턴스화하여 추가한다.
GAP TC는 기존 Happy-path가 놓치는 비정상 경로를 검증한다.

| GAP-ID | 패턴명 | 검증 포인트 |
|--------|--------|------------|
| GAP-01 | API 에러 시 Graceful Degradation | 핵심 버튼/폼 제출/데이터 갱신 시 API 에러 → fallback/toast 표시, 크래시 없음 |
| GAP-02 | 빈 데이터/Null 시 Empty State | 목록/상세 페이지에 데이터 없을 때 안내 UI 표시 |
| GAP-03 | 환경변수/외부키 미설정 시 Guard | API Key 미설정 시 안전한 동작, 대체 진입 수단 |
| GAP-04 | CSS 레이아웃 깨짐 | 고정 요소 가림, 모바일(375px) 가독성, 미디어 요소 크기 |
| GAP-05 | 외부 SDK/CDN 로딩 실패 Fallback | SDK 미로드 시 fallback UI, 프로토콜 명시 |
| GAP-06 | 개발 도구/디버그 UI 노출 | DevTools import/UI가 사용자에게 미노출 |
| GAP-07 | 경계값 (날짜/시간/수량 계산) | 24시 초과, 월말, 0건, 최대값 등 비정상 문자열 미발생 |
| GAP-08 | 데모 모드 End-to-End | 백엔드 미연결 상태에서 전체 플로우 연속성 |

**인스턴스화 방법:**
1. 프로젝트의 페이지 목록을 나열한다
2. 각 페이지에서 사용하는 API 호출, 외부 SDK, 환경변수를 식별한다
3. GAP 패턴별로 해당 페이지의 구체적 TC를 생성한다

### 4. 시나리오별 브라우저 검증

각 시나리오를 Playwright MCP 도구로 실제 브라우저에서 수행한다:

```
시나리오별 반복:
  1. browser_navigate() → 해당 페이지로 이동
  2. browser_snapshot() → 페이지 구조 확인, 필요한 UI 요소 존재 확인
  3. browser_click() / browser_fill_form() → 사용자 행위 수행
     (로그인, 폼 입력, 버튼 클릭, 페이지 이동 등)
  4. browser_snapshot() → 결과 화면 확인
  5. browser_network_requests() → API 호출 성공 여부 확인 (5xx = FAIL)
  6. browser_console_messages() → JavaScript 에러 확인
  7. browser_take_screenshot() → .temp/ 디렉토리에 증거 저장
```

#### 스크린샷 전체 페이지 저장 규칙

- 모든 시나리오의 최종 상태 스크린샷을 `.temp/tc-{번호}.png`로 저장한다
- PASS/FAIL 무관하게 전체 페이지를 캡처한다
- 이 스크린샷은 Phase 2에서 PO(사용자 관점)와 SP(UI/UX 관점)가 제품 검증 시 활용한다

### 5. 시나리오별 판정

| 결과 | 판정 |
|------|------|
| 페이지 이동 성공 + UI 요소 정상 + API 응답 정상 + 콘솔 에러 없음 | **PASS** |
| 페이지 이동 실패 또는 빈 화면 | **FAIL** |
| API 호출 5xx 응답 | **FAIL** |
| JavaScript 콘솔 에러 (CORS, TypeError, null reference 등) | **FAIL** |
| 기대한 UI 요소 미존재 (버튼, 폼, 데이터 목록 등) | **FAIL** |

### 6. 결과 정리 및 수정 반복

모든 시나리오 완료 후 결과를 요약한다:

```
## 유저 시나리오 검증 결과
| TC | 시나리오 | 결과 | 증거 |
|----|---------|------|------|
| TC-01 | 소셜 로그인 | PASS | 스크린샷: .temp/tc-01.png |
| TC-02 | 여행 생성 + 장소 추가 | FAIL | API 5xx: POST /api/v1/schedules (스크린샷: .temp/tc-02.png) |
| ... | ... | ... | ... |

FAIL 시나리오: N건 → 해당 서비스 에이전트에게 수정 지시
```

- **FAIL 시나리오가 1건이라도 있으면** 해당 에러의 원인(백엔드/프론트엔드/설정)을 분류하여 오케스트레이터에 보고
- 수정 후 FAIL 시나리오만 재검증 (PASS 시나리오는 재실행 불요)
- **모든 시나리오 PASS까지 반복**

### 7. 레포트 양식

테스트 결과는 `docs/develop/test/e2etest-{N}.md`에 아래 양식으로 작성한다:

```
# E2E 테스트 결과 레포트 #{N}

> 테스트일: YYYY-MM-DD
> 테스터: qa-engineer
> 테스트 범위: {전체 / 재테스트 TC 목록}

## 요약
| 항목 | 결과 |
|------|------|
| 총 TC | X개 |
| PASS | X개 |
| FAIL | X개 |
| console.error | X건 |
| 판정 | PASS / FAIL |

## FAIL TC 상세

### [CRITICAL/MAJOR/MINOR] TC-XX: {시나리오명}
- **현상**: {무엇이 잘못되었는지}
- **재현 절차**: {1) ... 2) ... 3) ...}
- **기대 동작**: {어떻게 되어야 하는지}
- **실제 동작**: {어떻게 되었는지}
- **영향 파일**: {수정이 필요한 파일 목록}
- **담당**: {backend-developer / frontend-developer / ai-engineer}
- **스크린샷**: `.temp/tc-XX-fail.png`

## PASS TC 목록
| TC | 시나리오 | 스크린샷 |
|----|---------|---------|
| TC-01 | ... | `.temp/tc-01.png` |
```

### 8. 역할 분리 주의사항

- **QA 에이전트는 테스트 결과 레포트만 작성한다. 직접 코드를 수정하지 않는다.**
- FAIL TC의 원인 분류(백엔드/프론트엔드/설정)와 영향 파일 목록을 레포트에 명시한다
- 오케스트레이터가 레포트를 기반으로 해당 개발자 에이전트에게 수정을 지시한다
- 수정 완료 후 QA 에이전트가 FAIL TC만 재테스트한다
