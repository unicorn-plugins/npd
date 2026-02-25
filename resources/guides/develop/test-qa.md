# 종합 테스트 및 QA 가이드

## 목적

구현된 전체 시스템(백엔드, 프론트엔드, AI 서비스)에 대해 **자동화된 테스트 코드**를 작성하고 실행하여, dev-plan.md에 정의된 전체 기능이 정상 동작함을 검증한다. curl 수동 확인이 아닌, 재실행 가능한 테스트 코드 기반의 검증 체계를 구축한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 구현된 백엔드 코드 | `{service-name}/src/` | 테스트 대상 |
| 구현된 프론트엔드 코드 | `frontend/` | 테스트 대상 |
| 구현된 AI 서비스 코드 | `ai-service/` | 테스트 대상 (존재 시) |
| 테스트 시나리오 | `docs/develop/dev-plan.md` 섹션 9 | E2E 테스트 시나리오 결정 |
| API 설계서 | `docs/design/api/*.yaml` | 통합 테스트 케이스 결정 |
| 데이터 설계서 | `docs/design/data-design.md` | 샘플 데이터 설계 |
| 서비스 실행 프로파일 | `{service-name}/.run/{service-name}.run.xml` | 실행 환경 확인 |
| 서비스 실행기 | `{PLUGIN_DIR}/resources/tools/customs/general/run-intellij-service-profile.py` | 백엔드 서비스 실행 |
| 백킹서비스 설치 결과서 | `docs/develop/backing-service-result.md` | 연결 정보 확인 |
| Docker Compose 파일 | `./docker-compose.yml` | 백킹서비스 기동 |
| 행위 계약 테스트 | `test/design-contract/*.spec.ts` | 시퀀스 기반 행위 계약 검증 대상 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 통합 테스트 케이스 문서 | `docs/develop/integration-test-cases.md` |
| 통합 테스트 샘플 데이터 | `{service}/src/test/resources/data/` |
| 통합 테스트 코드 | `{service}/src/test/.../integration/*IntegrationTest.java` |
| E2E 테스트 케이스 문서 | `docs/develop/e2e-test-cases.md` |
| E2E 테스트 샘플 데이터 | `e2e/fixtures/` |
| E2E 테스트 코드 | `e2e/tests/*.spec.ts` |
| 종합 테스트 리포트 | `docs/develop/test-report.md` |

---

## Part 1. 통합 테스트 (Step 4-3에서 수행)

서비스 간 API 호출이 정상적으로 동작하는지 자동화된 코드로 검증한다.

### 1-1. 통합 테스트 케이스 설계

**입력**: API 설계서(`docs/design/api/*.yaml`), 개발 계획서(`docs/develop/dev-plan.md`)

**절차:**

1. API 설계서에서 서비스 간 호출 관계를 분석한다
2. 각 API 엔드포인트별로 테스트 케이스를 정의한다:
   - 정상 요청 → 기대 응답 (Happy Path)
   - 잘못된 입력 → 에러 응답 (Validation)
   - 인증 필요 API → 토큰 없이 호출 → 401 (Auth)
   - 서비스 간 의존 호출 → 연쇄 동작 확인 (Cross-Service)
3. 테스트 케이스 문서를 작성한다

**산출물**: `docs/develop/integration-test-cases.md`

```markdown
# 통합 테스트 케이스

## 1. 테스트 범위

| 서비스 | 엔드포인트 수 | 테스트 케이스 수 |
|--------|-------------|----------------|
| {service-name} | {N} | {M} |

## 2. 테스트 케이스 목록

### {Service Name}

| ID | 엔드포인트 | 메서드 | 시나리오 | 입력 | 기대 결과 | 유형 |
|----|-----------|--------|---------|------|----------|------|
| IT-{NNN} | {path} | {GET/POST/...} | {시나리오 설명} | {요청 바디/파라미터} | {HTTP 상태코드 + 응답 구조} | {Happy/Validation/Auth/Cross-Service} |
```

### 1-2. 통합 테스트 샘플 데이터 작성

**입력**: 데이터 설계서(`docs/design/data-design.md`), 테스트 케이스 문서

**절차:**

1. 테스트 케이스의 전제 조건(Precondition)에 필요한 데이터를 식별한다
2. 서비스별 SQL seed 스크립트를 작성한다:
   - `{service}/src/test/resources/data/seed.sql` — 기본 테스트 데이터
   - 테이블 TRUNCATE → INSERT 순서로 작성 (멱등성 보장)
3. API 요청에 사용할 JSON fixture를 작성한다:
   - `{service}/src/test/resources/data/request/{endpoint-name}.json`
4. 인증 토큰 생성을 위한 테스트용 사용자 데이터를 포함한다

**샘플 데이터 구조:**
```
{service}/src/test/resources/data/
├── seed.sql                          # DB 초기 데이터
├── request/
│   ├── create-{resource}.json        # POST 요청 바디
│   └── update-{resource}.json        # PUT 요청 바디
└── expected/
    └── {resource}-response.json      # 기대 응답 구조
```

### 1-3. 통합 테스트 코드 작성

**기술 스택**: Spring Boot Test + TestRestTemplate / WebTestClient

**절차:**

1. 서비스별 통합 테스트 베이스 클래스를 작성한다:
   ```java
   @SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
   @ActiveProfiles("test")
   @Sql(scripts = "/data/seed.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
   public abstract class IntegrationTestBase {
       @Autowired
       protected TestRestTemplate restTemplate;

       // 공통 헬퍼: 인증 토큰 생성, 헤더 빌드 등
   }
   ```

2. 테스트 케이스 문서의 각 케이스를 테스트 메서드로 구현한다:
   ```java
   class UserApiIntegrationTest extends IntegrationTestBase {
       @Test
       void 회원가입_정상요청_201응답() {
           // Given: seed.sql 로드 완료
           String requestBody = loadFixture("request/create-user.json");

           // When
           ResponseEntity<String> response = restTemplate.postForEntity(
               "/api/users", createRequest(requestBody), String.class);

           // Then
           assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
           assertThat(response.getBody()).contains("userId");
       }

       @Test
       void 회원가입_중복이메일_409응답() { ... }

       @Test
       void 회원조회_인증없음_401응답() { ... }
   }
   ```

3. 네이밍 규칙: `{Resource}ApiIntegrationTest.java`
4. 테스트 클래스 위치: `{service}/src/test/java/.../integration/`

### 1-4. 통합 테스트 실행

**사전 조건**: 전체 서비스가 기동된 상태에서 통합 테스트를 실행한다.

**1단계. 전체 서비스 동시 기동**

```bash
# 백킹서비스 기동
docker compose up -d
# 백엔드 전체 서비스 기동
python3 tools/run-intellij-service-profile.py --config-dir . --delay 5
# AI 서비스 기동 (해당 시)
docker compose --profile ai up -d
```
- 전 서비스 기동 후 에러 로그 0건이어야 PASS

**2단계. 통합 테스트 실행**

```bash
# 전체 통합 테스트 실행
./gradlew test --tests '*IntegrationTest'

# 서비스별 실행
./gradlew :{service-name}:test --tests '*IntegrationTest'
```

- 전체 PASS 확인
- 실패 시: 실패 원인 분석 → 테스트 코드 또는 구현 코드 수정 → 재실행
- 모든 통합 테스트 PASS 될 때까지 반복

---

## Part 2. E2E 테스트 (Step 5-1에서 수행)

사용자 시나리오 기반으로 FE → BE → DB → (AI) 전체 흐름을 자동화 코드로 검증한다.

### 2-1. E2E 테스트 케이스 설계

**입력**: 테스트 시나리오(`docs/develop/dev-plan.md` 섹션 9)

**절차:**

1. dev-plan.md 섹션 9의 테스트 시나리오를 E2E 사용자 시나리오로 변환한다
2. 각 시나리오의 단계별 동작·검증 포인트를 정의한다:
   - 페이지 이동 경로
   - 입력 데이터
   - 기대하는 UI 변화
   - 기대하는 API 호출 및 응답
3. 에러 시나리오도 포함한다 (잘못된 입력, 인증 만료 등)

**산출물**: `docs/develop/e2e-test-cases.md`

```markdown
# E2E 테스트 케이스

## 1. 테스트 범위

| 테스트 시나리오 (TC-ID) | 시나리오 수 | 우선순위 |
|------------------------|-----------|---------|
| {TC-ID} {제목} | {N} | {우선순위} |

## 2. 테스트 시나리오 목록

### {TC-ID}: {시나리오 제목}

| ID | 시나리오 | 사전 조건 | 단계 | 기대 결과 | 유형 |
|----|---------|----------|------|----------|------|
| E2E-{NNN} | {시나리오명} | {필요한 초기 상태} | 1. {페이지 이동}\n2. {입력}\n3. {클릭}\n4. {확인} | {기대하는 최종 상태} | {Happy/Error/Edge} |
```

### 2-2. E2E 샘플 데이터 작성

**절차:**

1. 시나리오의 사전 조건(Precondition)에 필요한 데이터를 식별한다
2. DB seed 스크립트를 작성한다:
   - `e2e/fixtures/seed.sql` — E2E 테스트용 초기 데이터
3. 시나리오별 입력 데이터 fixture를 작성한다:
   - `e2e/fixtures/{scenario-name}.json`
4. 테스트용 계정 정보를 정의한다:
   - `e2e/fixtures/accounts.json` — 테스트용 사용자 계정 목록

**샘플 데이터 구조:**
```
e2e/fixtures/
├── seed.sql                    # DB 초기 데이터
├── accounts.json               # 테스트용 계정 정보
├── signup-scenario.json        # 시나리오별 입력 데이터
├── login-scenario.json
└── order-scenario.json
```

### 2-3. E2E 테스트 코드 작성

**기술 스택**: Playwright

**프로젝트 초기화:**
```bash
mkdir -p e2e
cd e2e
npm init -y
npm install -D @playwright/test
npx playwright install
```

**`e2e/playwright.config.ts`:**
```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  outputDir: '../.temp/playwright-results',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'cd ../frontend && npm run dev',
    port: 5173,
    reuseExistingServer: true,
  },
});
```

**테스트 코드 작성 절차:**

1. 공통 fixture를 작성한다:
   ```typescript
   // e2e/tests/fixtures/auth.ts
   import { test as base, Page } from '@playwright/test';
   import accounts from '../fixtures/accounts.json';

   export const test = base.extend<{ authenticatedPage: Page }>({
     authenticatedPage: async ({ page }, use) => {
       await page.goto('/login');
       await page.fill('[name="email"]', accounts.testUser.email);
       await page.fill('[name="password"]', accounts.testUser.password);
       await page.click('button[type="submit"]');
       await page.waitForURL('/dashboard');
       await use(page);
     },
   });
   ```

2. 시나리오별 테스트를 작성한다:
   ```typescript
   // e2e/tests/user-registration.spec.ts
   import { test, expect } from '@playwright/test';
   import signupData from '../fixtures/signup-scenario.json';

   test.describe('회원가입 시나리오', () => {
     test('E2E-001: 정상 회원가입 후 로그인 가능', async ({ page }) => {
       // 1. 회원가입 페이지 이동
       await page.goto('/signup');

       // 2. 필드 입력
       await page.fill('[name="email"]', signupData.validUser.email);
       await page.fill('[name="password"]', signupData.validUser.password);
       await page.fill('[name="name"]', signupData.validUser.name);

       // 3. 제출
       await page.click('button[type="submit"]');

       // 4. 성공 확인
       await expect(page).toHaveURL('/login');
       await expect(page.locator('.success-message')).toBeVisible();
     });

     test('E2E-002: 중복 이메일로 가입 시 에러 표시', async ({ page }) => {
       // ...
     });
   });
   ```

3. 네이밍 규칙: `{scenario-name}.spec.ts`
4. 테스트 파일 위치: `e2e/tests/`

### 2-4. E2E 테스트 실행

**사전 조건**: 백킹서비스 + 백엔드 전체 서비스 + AI 서비스(해당 시) + 프론트엔드 기동 상태

```bash
# 사전 준비
docker compose up -d
python3 tools/run-intellij-service-profile.py --config-dir . --delay 5
# AI 서비스 기동 (해당 시)
docker compose --profile ai up -d

# E2E 테스트 실행
cd e2e && npx playwright test

# 특정 시나리오만 실행
npx playwright test tests/user-registration.spec.ts

# 브라우저 표시하며 실행 (디버깅용)
npx playwright test --headed

# 리포트 확인
npx playwright show-report
```

- 전체 PASS 확인
- 실패 시: 스크린샷·트레이스 분석 → 구현 코드 수정 → 재실행
- 모든 E2E 테스트 PASS 될 때까지 반복

---

## Part 3. 종합 테스트 실행 및 리포트 (Step 5-2에서 수행)

### 3-1. 전체 테스트 스위트 실행

모든 레벨의 테스트를 순서대로 실행한다:

```bash
# 1. 백엔드 단위 + 통합 테스트
./gradlew clean build test

# 2. 프론트엔드 빌드 + 린트
cd frontend && npm run build && npm run lint

# 3. AI 서비스 테스트 (해당 시)
cd ai-service && pytest

# 4. E2E 테스트
cd e2e && npx playwright test

# 5. design-contract 행위 계약 테스트
cd test/design-contract && npx jest --verbose
```

### 3-2. 실패 분석 및 버그 수정 사이클

1. 실패한 테스트를 분류한다:
   - **단위 테스트 실패** → backend-developer / frontend-developer에게 수정 재지시
   - **통합 테스트 실패** → 연동 관련 코드 수정 재지시
   - **E2E 테스트 실패** → UI 또는 API 연동 수정 재지시
2. 수정 완료 후 해당 테스트 재실행
3. 전체 PASS 될 때까지 반복

### 3-3. 종합 테스트 리포트 작성

모든 테스트 PASS 후 최종 리포트를 작성한다.

**산출물**: `docs/develop/test-report.md`

```markdown
# 종합 테스트 리포트

## 1. 테스트 환경

| 항목 | 값 |
|------|-----|
| 테스트 일시 | {YYYY-MM-DD} |
| 백킹서비스 환경 | docker-compose |
| 백엔드 서비스 수 | {N}개 |
| 프론트엔드 프레임워크 | {React/Vue} |
| AI 서비스 | {포함/미포함} |
| E2E 테스트 프레임워크 | Playwright |

## 2. 테스트 결과 요약

| 테스트 레벨 | 총 케이스 | 성공 | 실패 | 통과율 |
|------------|----------|------|------|--------|
| 단위 테스트 | {N} | {N} | 0 | 100% |
| 통합 테스트 | {N} | {N} | 0 | 100% |
| E2E 테스트 | {N} | {N} | 0 | 100% |
| AI 서비스 테스트 | {N} | {N} | 0 | 100% |
| design-contract 테스트 | {N} | {N} | 0 | 100% |
| **합계** | **{N}** | **{N}** | **0** | **100%** |

## 3. 백엔드 통합 테스트 상세

| 서비스 | 테스트 클래스 | 케이스 수 | 결과 |
|--------|-------------|----------|------|
| {service} | {TestClass} | {N} | PASS |

## 4. E2E 테스트 상세

| 테스트 시나리오 | 시나리오 | 테스트 파일 | 결과 |
|---------------|---------|-----------|------|
| {TC-ID} | {시나리오명} | {file.spec.ts} | PASS |

## 5. 프론트엔드 테스트 상세

| 항목 | 결과 |
|------|------|
| 빌드 (`npm run build`) | PASS |
| 린트 (`npm run lint`) | PASS |

## 6. AI 서비스 테스트 상세 (해당 시)

| 테스트 파일 | 케이스 수 | 결과 |
|-----------|----------|------|
| {test_file.py} | {N} | PASS |

## 7. 버그 수정 이력

| ID | 심각도 | 서비스 | 발견 테스트 | 설명 | 수정 상태 |
|----|--------|--------|-----------|------|----------|
| BUG-{N} | {Critical/Major/Minor} | {서비스명} | {테스트 ID} | {버그 설명} | 수정완료 |

## 8. 기능 커버리지

| 테스트 시나리오 | E2E 테스트 | 통합 테스트 | 커버 여부 |
|---------------|-----------|-----------|----------|
| {TC-ID} {제목} | {E2E-NNN} | {IT-NNN} | 커버됨 |

**기능 커버리지**: {N}/{M} ({%})

## 9. 최종 요약

- 전체 테스트 수: {N}
- 전체 통과율: 100%
- 기능 커버리지: {N}/{M} (100%)
- 미해결 버그: 0건
```

---

## 서비스 시작/중지 방법

백엔드(Spring Boot) 서비스는 반드시 `run-intellij-service-profile.py`를 사용하여 실행한다. 이 도구는 IntelliJ `.run/*.run.xml` 실행 프로파일을 파싱하여 환경변수(DB 접속 정보, 포트, 서비스 간 연동 URL 등)를 자동 주입한 후 `gradlew bootRun`을 실행한다. `./gradlew bootRun`을 직접 실행하면 환경변수가 누락되어 DB 연결 실패 등의 오류가 발생한다.

### 서비스 실행기 준비

`{PLUGIN_DIR}/resources/tools/customs/general/run-intellij-service-profile.py`를 프로젝트 루트의 `tools/` 디렉토리에 복사한다.

```bash
mkdir -p tools
cp {PLUGIN_DIR}/resources/tools/customs/general/run-intellij-service-profile.py tools/
```

### 서비스 목록 확인

```bash
python3 tools/run-intellij-service-profile.py --list
```

출력 예시:
```
발견된 서비스 (3개) — /home/user/project
  auth                 port=8081   task=auth:bootRun
  member               port=8082   task=member:bootRun
  schedule             port=8083   task=schedule:bootRun
```

### 백엔드 서비스 시작

**전체 서비스 시작** (서비스 간 5초 지연):
```bash
python3 tools/run-intellij-service-profile.py --config-dir . --delay 5
```

백그라운드 실행이 필요한 경우:
```bash
nohup python3 tools/run-intellij-service-profile.py --config-dir . --delay 5 > /dev/null 2>&1 &
```

**개별 서비스 시작**:
```bash
python3 tools/run-intellij-service-profile.py {service-name}
```

백그라운드 실행이 필요한 경우:
```bash
nohup python3 tools/run-intellij-service-profile.py {service-name} > logs/{service-name}.log 2>&1 &
```

### 서비스 시작 확인

```bash
# 각 서비스의 actuator/health 엔드포인트 확인
curl -s http://localhost:{port}/actuator/health
```

로그 확인:
```bash
# 실시간 로그 확인
tail -f logs/{service-name}.log
```

### 서비스 중지

**전체 서비스 중지:**
```bash
python3 tools/run-intellij-service-profile.py --stop
```

**개별 서비스 중지:**
```bash
python3 tools/run-intellij-service-profile.py --stop {service-name}
```

### AI 서비스 시작/중지

```bash
# Docker Compose ai 프로파일로 시작
docker compose --profile ai up -d

# 또는 직접 실행
cd ai-service && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 중지
docker compose --profile ai down
```

### 프론트엔드 개발 서버 시작

```bash
cd frontend && npm run dev
```

---

## 품질 기준

- [ ] 통합 테스트 케이스 문서(`docs/develop/integration-test-cases.md`) 작성 완료
- [ ] 통합 테스트 샘플 데이터(`{service}/src/test/resources/data/`) 작성 완료
- [ ] 통합 테스트 코드(`*IntegrationTest.java`) 전체 PASS
- [ ] E2E 테스트 케이스 문서(`docs/develop/e2e-test-cases.md`) 작성 완료
- [ ] E2E 테스트 샘플 데이터(`e2e/fixtures/`) 작성 완료
- [ ] E2E 테스트 코드(`e2e/tests/*.spec.ts`) 전체 PASS
- [ ] dev-plan.md 정의 기능 전체 테스트 커버
- [ ] 발견된 버그 전체 수정 완료
- [ ] 종합 테스트 리포트(`docs/develop/test-report.md`) 작성 완료

## 주의사항

- 백엔드 서비스 시작은 반드시 `run-intellij-service-profile.py`를 사용한다. `./gradlew bootRun`을 직접 실행하면 `.run.xml`의 환경변수가 주입되지 않아 DB 연결 실패 등이 발생한다
- 백킹서비스(`docker compose up -d`)가 실행 중이어야 함
- 설정 Manifest(`application.yml`)의 민감 정보는 하드코딩하지 않고 환경변수 처리
- 설정 Manifest 수정 시 실행 프로파일(`.run/*.run.xml`)도 함께 업데이트 (run-profile.md 가이드 참조)
- 실행 결과 로그는 `logs/` 디렉토리 하위에 자동 생성됨 (`logs/{service-name}.log`)
- 소스 수정 후 `run-intellij-service-profile.py --stop`으로 서비스 중지 → 재시작 (Gradle이 자동으로 컴파일 후 실행)
- AI 서비스 테스트 시 LLM API 호출 비용 주의 (가능하면 mock 활용)
- 테스트 리포트 경로는 `docs/develop/test-report.md`로 통일
- E2E 테스트의 Playwright는 `e2e/` 디렉토리에 독립 프로젝트로 구성한다 (프론트엔드 `frontend/`와 분리)
- 통합 테스트의 `@Sql` seed 스크립트는 멱등성을 보장해야 한다 (TRUNCATE → INSERT)
