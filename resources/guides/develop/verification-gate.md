# 개발 검증 게이트 가이드

## 목적

각 Phase 완료 시 **작업자와 독립된 에이전트**가 실제 빌드·테스트·산출물을 검증하여,
미완료 상태에서의 다음 단계 진입을 구조적으로 차단한다.

> **핵심 원칙**: 작업자 ≠ 검증자. 검증 에이전트는 해당 Phase의 작업 에이전트와 반드시 다른 에이전트여야 한다.

---

## Part 1. Phase 2 완료 검증 (Step 3-4, qa-engineer)

Step 3-1 ~ 3-3 완료 후, **작업자와 독립된 qa-engineer**가 실제 빌드·테스트·산출물을 재검증한다.
(작업한 에이전트가 스스로 완료를 선언하는 것을 방지하기 위한 독립 검증)

> **검증 순서**: fail-fast 원칙에 따라 비용이 낮은 정적 검사부터 수행하고, 비용이 높은 동적 검증(빌드·기동)은 후순위로 배치한다.

### 검증 절차

1. **EXPECTED OUTCOME 산출물 존재 확인**
   - `docs/develop/dev-plan.md`에 명시된 산출물 파일이 모두 존재하는지 확인
   - 누락 파일이 있으면 FAIL

2. **TODO/FIXME 전수 검사**
   ```bash
   grep -rn "TODO\|FIXME\|HACK" --include="*.java" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.vue" --include="*.dart" .
   ```
   - 결과 0건이어야 PASS

3. **API 명세 vs 실제 구현 대조**
   - `docs/design/api-design.md` (또는 OpenAPI 명세)의 엔드포인트 목록을 추출
   - 각 엔드포인트에 대응하는 Controller 메서드가 실제 코드에 존재하는지 전수 확인
   - 누락 엔드포인트가 있으면 FAIL

4. **프론트엔드 빌드 + 린트 + 테스트**
   ```bash
   cd frontend && npm run build && npm run lint && npm test --if-present
   ```
   - 빌드 성공 + 린트 에러 0건 + 테스트 실패 0건이어야 PASS
   - `npm test --if-present`는 test 스크립트가 정의되지 않은 경우 건너뜀

5. **백엔드 빌드 + 전체 단위 테스트**
   ```bash
   ./gradlew clean build test
   ```
   - 빌드 성공 + 테스트 실패 0건이어야 PASS

6. **AI 서비스 테스트** (해당 시)
   ```bash
   cd ai-service && pytest
   ```
   - 테스트 실패 0건이어야 PASS

7. **각 서비스 독립 기동 + 헬스체크 + Prism Mock 연동 검증**

   **7-a. 백킹서비스 + 백엔드 기동**
   ```bash
   # 백킹서비스 기동
   docker compose up -d
   # 백엔드 전체 서비스 기동
   python3 tools/run-intellij-service-profile.py --config-dir . --delay 5
   ```
   - 기동 후 30초 대기
   - 각 서비스의 헬스체크 엔드포인트(`actuator/health`) 호출 → 정상 응답 확인
   - `logs/{service-name}.log`에서 `ERROR` 레벨 로그 검색
     - 일시적 DB 재연결 에러(`HikariPool.*Connection|Reconnect|retry|Connection reset` 패턴)는 최종 헬스체크 성공 시 무시
     - 그 외 ERROR 로그가 있으면 FAIL

   **7-b. Prism Mock 연동 검증**
   ```bash
   # Prism Mock 서버 기동
   docker compose --profile mock up -d
   # 프론트엔드 기동
   cd frontend && npm run dev &
   ```
   - Prism Mock 서버 응답 확인: `curl -s http://localhost:4010/{대표 엔드포인트}` → 정상 응답(2xx)
   - 프론트엔드가 Prism Mock을 통해 API 호출 가능한 상태인지 확인

   **7-c. AI 서비스 독립 기동** (해당 시)
   ```bash
   docker compose --profile ai up -d
   ```
   - 헬스체크 엔드포인트 호출 → 정상 응답 확인
   - `logs/ai-service.log`에서 `ERROR` 레벨 로그 검색 (기준 동일)

### 게이트 판정

위 7개 항목 모두 PASS해야 Step 4 진입. FAIL 항목 발견 시 FAIL 항목·원인·재현 방법을 정리하여 오케스트레이터에게 보고한다. 오케스트레이터가 해당 작업 에이전트(backend-developer/frontend-developer/ai-engineer)에게 수정을 지시하고, 수정 완료 후 Part 1을 처음부터 재수행한다.

---

## Part 2. Phase 3 완료 검증 (Step 4-4, architect)

Step 4-1 ~ 4-3 완료 후, **작업자와 독립된 architect**가 통합 연동의 실제 동작을 검증한다.
(통합이 정상 완료되지 않은 상태에서 테스트 단계로 넘어가는 것을 방지)

### 검증 절차

1. **Mock 참조 잔존 확인**
   ```bash
   grep -rn "localhost:4010\|prism\|mock-api\|MOCK_" --include="*.ts" --include="*.tsx" --include="*.vue" --include="*.dart" --include="*.java" --include="*.py" frontend/ src/ ai-service/ 2>/dev/null
   ```
   - 프론트엔드·백엔드 코드에 Prism/Mock URL이 남아있으면 FAIL (테스트 코드 제외)

2. **전체 서비스 동시 기동**
   ```bash
   # 백킹서비스 기동
   docker compose up -d
   # 백엔드 전체 서비스 기동
   python3 tools/run-intellij-service-profile.py --config-dir . --delay 5
   # AI 서비스 기동 (해당 시)
   docker compose --profile ai up -d
   ```
   - 전 서비스 기동 후 에러 로그 0건이어야 PASS

3. **통합 테스트 자동 실행**
   ```bash
   ./gradlew test --tests '*IntegrationTest'
   ```
   - Step 4-3에서 작성한 통합 테스트 코드 전체 실행
   - 테스트 실패 0건이어야 PASS
   - 실패 시 실패 테스트명 및 원인을 기록

4. **BE↔AI 연동 호출 검증** (해당 시)
   - 백엔드에서 AI 서비스를 호출하는 API를 식별
   - 해당 API를 `curl`로 호출 → AI 서비스까지 정상 도달·응답 확인
   - Circuit Breaker/Fallback 동작 확인 (AI 서비스 중지 후 호출 → Fallback 응답 확인)

5. **프론트엔드 → 백엔드 실제 연동 검증**

   **5-a. API URL 정적 검증**
   <!-- IF PLATFORM == REACT -->
   - `frontend/.env.production` (또는 `.env.local`)의 `REACT_APP_API_URL` (CRA) 또는 `VITE_API_URL` (Vite) 변수가 실제 백엔드 URL(`http://localhost:{port}`)을 가리키는지 확인
   <!-- ELIF PLATFORM == VUE -->
   - `frontend/.env.production` (또는 `.env.local`)의 `VUE_APP_API_URL` (Vue CLI) 또는 `VITE_API_URL` (Vite) 변수가 실제 백엔드 URL(`http://localhost:{port}`)을 가리키는지 확인
   <!-- ELIF PLATFORM == FLUTTER -->
   - `lib/config/` 또는 환경 설정 파일의 API base URL이 실제 백엔드 URL을 가리키는지 확인
   <!-- ENDIF -->
   - Prism Mock URL(`localhost:4010`)이 남아있으면 FAIL

   **5-b. 백엔드 주요 엔드포인트 curl 검증**
   - `docs/design/api-design.md`에서 주요 엔드포인트 3~5개를 선정
   - 실제 백엔드에 `curl`로 호출 → 정상 응답(2xx 또는 4xx 인증 필요) 확인
   - 서버 에러(5xx)가 반환되면 FAIL

   **5-c. 프론트엔드 빌드 확인**
   ```bash
   cd frontend && npm run build
   ```
   - 실제 API URL 설정 상태에서 빌드 성공이어야 PASS

### 게이트 판정

위 5개 항목 모두 PASS해야 Step 5 진입. FAIL 항목 발견 시 FAIL 항목·원인·재현 방법을 정리하여 오케스트레이터에게 보고한다. 오케스트레이터가 해당 작업 에이전트(frontend-developer/backend-developer/ai-engineer)에게 수정을 지시하고, 수정 완료 후 Part 2를 처음부터 재수행한다.

---

## Part 3. 최종 완료 검증 (Step 5-3, architect)

Step 5-2(종합 QA) 완료 후, **qa-engineer와 독립된 architect**가 최종 완료 여부를 판정한다.
(QA 에이전트가 자기 작업을 자기가 완료 선언하는 것을 방지하고, 설계↔구현 추적성까지 검증)

### 검증 절차

1. **테스트 리포트 존재 및 품질 확인**
   - `docs/develop/test-report.md` 파일이 존재하는지 확인
   - 리포트 내용에 테스트 실패·에러가 0건인지 확인
   - 테스트 커버리지가 리포트에 명시되어 있는지 확인
   - "MVP Must Have 커버리지" 섹션의 커버리지가 100%인지 확인 (100% 미만이면 FAIL)
   - "미해결 버그" 항목이 0건인지 확인 (1건 이상이면 FAIL)

2. **완료 조건 전수 체크**
   - SKILL.md 하단 "완료 조건" 항목을 하나씩 순회하며 실제 파일·코드 존재 확인:
     - `docs/develop/dev-plan.md` 존재 여부
     - Gradle Wrapper (`gradlew`, `settings.gradle`, `build.gradle`) 존재 여부
     - `docker-compose.yml`, `.env.example` 존재 여부
     - 프론트엔드 프로젝트 (`frontend/package.json` 등) 존재 여부
     - AI 서비스 프로젝트 (`ai-service/` 등) 존재 여부 (해당 시)
     - 실행 프로파일 (`.run/*.run.xml`) 존재 여부
     - 통합 테스트 코드 (`*IntegrationTest.java`) 존재 여부
     - E2E 테스트 코드 (`e2e/tests/*.spec.ts`) 존재 여부
     - 테스트 리포트 (`docs/develop/test-report.md`) 존재 여부
   - 하나라도 누락이면 FAIL

3. **설계↔구현 추적성 검증**
   - `docs/design/api-design.md`의 전체 엔드포인트 목록 추출
   - 각 엔드포인트에 대응하는 Controller 코드가 존재하는지 대조
   - `docs/design/data-design.md`의 Entity 목록과 실제 Entity 클래스 대조
   - 누락 구현이 있으면 FAIL + 누락 목록 기록

4. **전체 테스트 스위트 최종 실행**
   ```bash
   # 백엔드 단위 + 통합 테스트
   ./gradlew clean build test
   # 프론트엔드 빌드
   cd frontend && npm run build
   # E2E 테스트
   cd e2e && npx playwright test
   # AI 서비스 (해당 시)
   cd ai-service && pytest
   ```
   - 전체 빌드 성공 + 모든 테스트(단위/통합/E2E) 실패 0건이어야 PASS

5. **설정 일관성 교차 검증**
   - `application.yml`의 환경변수 placeholder와 `.env.example`의 키 목록 대조
   - `.env.example`의 키와 `docker-compose.yml`의 environment 섹션 대조
   - 불일치 항목이 있으면 FAIL + 불일치 목록 기록

### 게이트 판정

위 5개 항목 모두 PASS해야 Step 6(개발 완료 보고) 진입 허용. FAIL 항목 발견 시 FAIL 항목·원인·재현 방법을 정리하여 오케스트레이터에게 보고한다. 오케스트레이터가 해당 작업 에이전트에게 수정을 지시하고, 수정 완료 후 Part 3을 처음부터 재수행한다. **이 게이트를 통과하지 않으면 개발 완료 보고를 절대 수행하지 않는다.**
