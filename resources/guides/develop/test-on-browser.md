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
