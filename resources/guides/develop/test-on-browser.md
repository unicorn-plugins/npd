# 브라우저 테스트 (Playwright Test Suite)

## 목적

프론트엔드와 백엔드/AI 서비스 간 E2E 동작을 **Playwright Test Suite**(자동화 테스트 스크립트)로 검증한다.
`docs/develop/dev-plan.md`의 테스트 시나리오(TC-01~N)를 자동화된 테스트 스크립트로 일괄 실행하여, 사용자 관점에서 핵심 기능이 동작하는지 확인한다.

> **핵심 원칙**: TC별로 Playwright MCP 도구를 반복 호출하지 않는다.
> 대신 TC 전체를 하나의 테스트 스크립트로 작성하고 `npx playwright test` 한 번으로 실행한다.
> Playwright MCP는 스크립트 작성 전 **페이지 구조 탐색** 용도로만 사용한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 테스트 시나리오 | `docs/develop/dev-plan.md` 섹션 9 | TC별 test() 블록 생성 |
| API 테스트 결과 | `docs/develop/api-test-result.md` | API 정상 동작 확인 전제 |
| 샘플 데이터 | `{service}/src/test/resources/data/` | API 테스트에서 생성된 데이터 재활용 |
| 서비스 실행기 | `{PLUGIN_DIR}/resources/tools/customs/general/run-backend.py` | 백엔드 서비스 실행 |

## 사전 조건

- Step 4-3(API 테스트) 전체 PASS 완료
- 백킹서비스 + 백엔드 서비스 기동 상태 (API 테스트에서 기동된 상태 유지)
- 필요시 AI 서비스 기동 상태

---

## 방법론

### 1. Playwright 환경 설정 (최초 1회)

프로젝트 루트에 E2E 테스트 환경을 구성한다. `e2e/` 디렉토리가 이미 존재하면 건너뛴다.

```bash
mkdir -p e2e && cd e2e
npm init -y
npm install -D @playwright/test
npx playwright install chromium
```

`e2e/playwright.config.ts` 작성:

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  outputDir: '../.temp/playwright-output',
  timeout: 30000,
  retries: 0,
  workers: 1,
  reporter: [
    ['json', { outputFile: '../.temp/test-results.json' }],
    ['list']
  ],
  use: {
    baseURL: `http://localhost:${process.env.FRONTEND_PORT || '3000'}`,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
});
```

### 2. 프론트엔드 개발 서버 기동

```bash
python3 tools/run-frontend.py start --background --force
python3 tools/run-frontend.py status
```

> tools/ 미존재 시: `{PLUGIN_DIR}/resources/tools/customs/general/run-frontend.py` 사용

- `status` 명령으로 "상태: 실행 중" 출력을 확인한 뒤 진행

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

### 4. 페이지 구조 탐색 (Playwright MCP 사용)

**Playwright MCP 도구**로 각 페이지의 UI 구조를 확인한다.
Playwright MCP는 **스크립트 작성/수정을 위한 탐색 용도**로만 사용하며, 실제 TC 실행은 스크립트가 담당한다.

#### 4-1. 최초 스크립트 작성 시 (전체 탐색)

```
페이지별 반복 (TC에서 사용하는 페이지만):
  1. browser_navigate("http://localhost:{FRONTEND_PORT}/{경로}")
  2. browser_snapshot() → DOM 구조, 사용 가능한 selector, 폼 필드명 확인
  3. 필요시 browser_click()으로 모달/탭 열어 숨겨진 요소 확인
```

**수집할 정보:**
- 각 페이지의 주요 UI 요소 selector (버튼, 폼, 목록 등)
- 네비게이션 경로 (라우팅 구조)
- 인증 상태에 따른 UI 변화
- 폼 필드의 name/id/placeholder 속성

> **주의**: 이 탐색은 TC 수에 관계없이 **페이지 수**만큼만 수행한다.
> 같은 페이지를 사용하는 TC가 여러 개여도 탐색은 1회이다.

#### 4-2. 버그픽스/개선 후 재테스트 시 (부분 탐색)

개발자가 버그를 수정하면 UI 구조(selector, 요소 배치 등)가 변경될 수 있다.
재테스트 전에 **수정된 TC에 해당하는 페이지만** Playwright MCP로 재탐색하여 스크립트를 갱신한다.

```
FAIL TC의 영향 페이지만 반복:
  1. e2etest-{N}.md의 FAIL TC에서 영향 파일 목록 확인
  2. 프론트엔드 파일이 수정된 TC의 페이지만 browser_navigate + browser_snapshot
  3. selector 변경이 감지되면 scenarios.spec.ts의 해당 test() 블록 업데이트
  4. 백엔드만 수정된 TC는 스크립트 변경 불요 → 바로 재실행
```

> **판단 기준**: FAIL TC의 `영향 파일`에 프론트엔드 파일(`frontend/src/...`)이 포함되면 해당 페이지 재탐색 필요.
> 백엔드 파일만 수정된 경우 UI 구조는 변하지 않으므로 스크립트 수정 없이 재실행한다.

### 5. 인증 처리

#### JWT 자체 로그인

브라우저에서 직접 로그인 폼을 입력하는 방식으로 테스트한다.
테스트 스크립트의 `beforeAll`에서 로그인 수행:

```typescript
test.beforeAll(async ({ browser }) => {
  const page = await browser.newPage();
  await page.goto('/login');
  await page.fill('#email', 'test@example.com');
  await page.fill('#password', 'testpassword');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard');
  // 인증 토큰이 localStorage/cookie에 저장됨
  await page.context().storageState({ path: 'e2e/.auth/state.json' });
  await page.close();
});

// 이후 각 test()에서 인증 상태 재사용
test.use({ storageState: 'e2e/.auth/state.json' });
```

#### OAuth2/소셜 로그인

외부 Provider 리디렉트가 필요하므로 테스트 전용 로그인 API를 활용:

```typescript
test.beforeAll(async ({ browser }) => {
  // 1. 테스트 전용 API로 토큰 획득
  const response = await fetch('http://localhost:{auth_port}/api/test/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId: 'test-user-01' }),
  });
  const { accessToken } = await response.json();

  // 2. 브라우저에 토큰 주입
  const page = await browser.newPage();
  await page.goto('/');
  await page.evaluate((token) => {
    localStorage.setItem('accessToken', token);
  }, accessToken);
  await page.context().storageState({ path: 'e2e/.auth/state.json' });
  await page.close();
});

test.use({ storageState: 'e2e/.auth/state.json' });
```

- 토큰 저장 키(`accessToken`)는 프론트엔드 코드의 실제 키와 일치해야 한다
  - 프론트엔드 소스에서 `localStorage.setItem` 또는 `sessionStorage.setItem`을 검색하여 실제 키명을 확인
  - cookie 기반인 경우: `page.context().addCookies([...])` 사용

### 6. Playwright 테스트 스크립트 작성

추출한 시나리오와 탐색한 페이지 구조를 기반으로 `e2e/tests/scenarios.spec.ts`를 작성한다.

#### 6-1. 테스트 스크립트 구조

```typescript
import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// ─── 스크린샷 저장 설정 ───
// {N}은 현재 iteration 번호로 치환 (e2etest-{N}.md와 동기화)
const ITER_DIR = path.resolve(__dirname, '../../.temp/iter-{N}');

// ─── 공통 유틸리티 ───
const networkErrors: string[] = [];
const consoleErrors: string[] = [];

test.beforeEach(async ({ page }) => {
  // 네트워크 에러 수집
  page.on('response', response => {
    if (response.status() >= 500) {
      networkErrors.push(`${response.status()} ${response.request().method()} ${response.url()}`);
    }
  });
  // 콘솔 에러 수집
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
});

// ─── 인증 설정 ───
// (섹션 5의 방식에 따라 beforeAll + storageState 작성)

// ─── 비즈니스 시나리오 ───

test('TC-01: {시나리오명}', async ({ page }) => {
  await page.goto('/{경로}');

  // 사용자 행위 수행
  await page.click('{selector}');
  await page.fill('{selector}', '{value}');
  await page.click('{submit selector}');

  // 결과 확인
  await expect(page.locator('{결과 selector}')).toBeVisible();

  // 스크린샷 저장
  fs.mkdirSync(ITER_DIR, { recursive: true });
  await page.screenshot({ path: path.join(ITER_DIR, 'tc-01.png'), fullPage: true });
});

test('TC-02: {시나리오명}', async ({ page }) => {
  // ... 동일 패턴
  await page.screenshot({ path: path.join(ITER_DIR, 'tc-02.png'), fullPage: true });
});

// TC-03 ~ TC-N: 동일 패턴으로 작성

// ─── GAP 시나리오 ───

test('GAP-01: API 에러 시 Graceful Degradation', async ({ page }) => {
  // 네트워크 차단으로 API 에러 시뮬레이션
  await page.route('**/api/**', route => route.abort());
  await page.goto('/{핵심 페이지}');

  // 크래시 없이 fallback UI 표시되는지 확인
  await expect(page.locator('{fallback selector}')).toBeVisible();

  await page.screenshot({ path: path.join(ITER_DIR, 'gap-01.png'), fullPage: true });
});

test('GAP-02: 빈 데이터 Empty State', async ({ page }) => {
  // 빈 데이터 응답 모킹
  await page.route('**/api/{목록 endpoint}', route =>
    route.fulfill({ status: 200, body: JSON.stringify([]) })
  );
  await page.goto('/{목록 페이지}');

  await expect(page.locator('{empty state selector}')).toBeVisible();

  await page.screenshot({ path: path.join(ITER_DIR, 'gap-02.png'), fullPage: true });
});

// GAP-03 ~ GAP-08: 프로젝트에 맞게 구체화하여 작성
```

#### 6-2. 테스트 작성 원칙

1. **TC 1:1 매핑**: dev-plan.md의 각 TC가 하나의 `test()` 블록이 됨
2. **스크린샷 필수**: 모든 TC의 최종 상태를 `.temp/iter-{N}/tc-{번호}.png`로 저장
3. **에러 수집 자동화**: `beforeEach`에서 네트워크/콘솔 에러를 자동 수집
4. **독립성**: 각 TC는 독립적으로 실행 가능 (인증은 storageState로 공유)
5. **네이밍 규칙**: test 이름은 `TC-{번호}: {시나리오명}` 또는 `GAP-{번호}: {패턴명}` 형식 (재테스트 시 `--grep` 필터에 사용)

### 7. 테스트 실행

#### 7-1. 전체 실행 (최초 또는 회귀 테스트)

```bash
cd e2e && npx playwright test 2>&1
```

실행 결과:
- 터미널에 PASS/FAIL 목록 출력
- `.temp/test-results.json`에 구조화된 JSON 결과 생성
- `.temp/iter-{N}/tc-*.png`에 스크린샷 저장

#### 7-2. FAIL TC만 재실행 (재테스트)

**재실행 전 준비:**
1. e2etest-{N}.md의 FAIL TC 중 프론트엔드 파일이 수정된 TC를 식별한다
2. 해당 페이지를 Playwright MCP로 재탐색한다 (섹션 4-2 참조)
3. selector 변경이 있으면 `scenarios.spec.ts`의 해당 `test()` 블록을 업데이트한다
4. 백엔드만 수정된 TC는 스크립트 변경 없이 바로 재실행한다

```bash
# FAIL TC만 선택적 재실행
cd e2e && npx playwright test --grep="TC-02|TC-05|GAP-03" 2>&1
```

#### 7-3. 재테스트 시 PASS 스크린샷 계승

FAIL TC만 재실행하는 경우, 이전 iteration의 PASS 스크린샷을 현재 디렉토리로 복사한 뒤 재테스트를 시작한다:

```bash
# iter-{N-1}에서 PASS였던 TC 스크린샷을 iter-{N}으로 복사
mkdir -p .temp/iter-{N}
cp .temp/iter-{N-1}/tc-*.png .temp/iter-{N}/
cp .temp/iter-{N-1}/gap-*.png .temp/iter-{N}/
# 이후 재실행 시 FAIL TC의 스크린샷만 덮어쓰기됨
```

이를 통해 매 iteration 디렉토리가 항상 **전체 TC의 최신 스크린샷**을 보유하며, 제품 검증(Step 6)에서 PO/SP가 최종 iteration만 참조해도 누락이 없다.

### 8. 결과 분석 및 레포트 작성

#### 8-1. JSON 결과 파싱

`.temp/test-results.json`을 읽어 각 TC의 PASS/FAIL을 추출한다:

```
JSON 결과 구조:
  suites[].specs[].tests[].results[]
    - status: "passed" | "failed" | "timedOut"
    - error.message: 실패 원인
    - attachments[]: 스크린샷 경로
```

#### 8-2. FAIL TC 분석

FAIL TC에 대해 다음을 분석한다:

1. **에러 유형 분류**:
   - 네트워크 5xx → 백엔드 이슈 → `backend-developer`
   - DOM 요소 미발견 / UI 깨짐 → 프론트엔드 이슈 → `frontend-developer`
   - AI 응답 실패 → AI 이슈 → `ai-engineer`
2. **영향 파일 추정**: 에러 메시지와 API 경로에서 관련 소스 파일 식별
3. **심각도 분류**: CRITICAL / MAJOR / MINOR

#### 8-3. 레포트 작성

`docs/develop/test/e2etest-{N}.md`에 아래 양식으로 작성한다:

```markdown
# E2E 테스트 결과 레포트 #{N}

> 테스트일: YYYY-MM-DD
> 테스터: qa-engineer
> 테스트 범위: {전체 / 재테스트 TC 목록}
> 실행 방식: Playwright Test Suite

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
- **에러 메시지**: {Playwright 테스트 에러 메시지}
- **재현 절차**: {1) ... 2) ... 3) ...}
- **기대 동작**: {어떻게 되어야 하는지}
- **실제 동작**: {어떻게 되었는지}
- **영향 파일**: {수정이 필요한 파일 목록}
- **담당**: {backend-developer / frontend-developer / ai-engineer}
- **스크린샷**: `.temp/iter-{N}/tc-XX.png`

## PASS TC 목록
| TC | 시나리오 | 스크린샷 |
|----|---------|---------|
| TC-01 | ... | `.temp/iter-{N}/tc-01.png` |
```

### 9. 시나리오별 판정

| 결과 | 판정 |
|------|------|
| 테스트 통과 (expect 충족 + 에러 없음) | **PASS** |
| 페이지 이동 실패 또는 빈 화면 | **FAIL** |
| API 호출 5xx 응답 (networkErrors) | **FAIL** |
| JavaScript 콘솔 에러 (CORS, TypeError, null reference 등) | **FAIL** |
| 기대한 UI 요소 미존재 (expect 실패) | **FAIL** |

### 10. 역할 분리 주의사항

- **QA 에이전트는 테스트 스크립트 작성 + 실행 + 레포트 작성만 한다. 직접 애플리케이션 코드를 수정하지 않는다.**
- FAIL TC의 원인 분류(백엔드/프론트엔드/AI)와 영향 파일 목록을 레포트에 명시한다
- 오케스트레이터가 레포트를 기반으로 해당 개발자 에이전트에게 수정을 지시한다
- 수정 완료 후 QA 에이전트가 FAIL TC만 재테스트한다 (`--grep` 옵션 사용)
- 테스트 스크립트(`e2e/tests/scenarios.spec.ts`) 자체의 수정은 QA가 담당 (selector 변경 등)
