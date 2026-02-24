# 개발 검증 게이트 가이드

## 목적

각 Phase 완료 시 **작업자와 독립된 에이전트**가 실제 빌드·테스트·산출물을 검증하여,
미완료 상태에서의 다음 단계 진입을 구조적으로 차단한다.

> **핵심 원칙**: 작업자 ≠ 검증자. 검증 에이전트는 해당 Phase의 작업 에이전트와 반드시 다른 에이전트여야 한다.

---

## 정직한 검증 원칙

모든 검증 절차는 아래 원칙을 **절대적으로** 준수한다.

### 원칙 1: 실행하지 않은 것을 PASS라고 보고하지 않는다
- 문서 작성 ≠ 작업 완료. 문서는 실제 결과를 기록하는 것이지, 문서를 쓰면 완료가 되는 것이 아님
- 코드 작성 ≠ 동작 확인. 빌드 통과는 "코드가 컴파일된다"일 뿐, "서비스가 동작한다"가 아님
- 스크립트 작성 ≠ 실행 완료. 테스트 코드를 작성했다고 테스트가 통과한 것이 아님

### 원칙 2: 모든 검증은 증거 기반이어야 한다
- 각 검증 항목은 반드시 **실제 명령어 실행 + 출력 캡처**로 확인한다
- "확인했다"라는 텍스트 보고가 아니라, 실제 명령어 출력 로그를 증거로 제시한다
- 검증 결과는 `PASS (증거: 명령어 출력)` 또는 `FAIL (증거: 에러 메시지)` 형식으로 기록한다

### 원칙 3: 도구가 없으면 SKIP이 아니라 FAIL이다
- 필수 도구(SDK, CLI 등)가 설치되어 있지 않으면 해당 검증 항목은 **FAIL**이다
- "도구 미설치로 건너뜀"은 허용하지 않는다
- FAIL 시 설치 방법을 안내하고, 설치 완료 후 게이트를 재수행해야 한다

### 원칙 4: 검증은 반드시 순서대로 수행한다
- Pre-flight → 정적 검증 → 빌드 검증 → 런타임 검증 순서를 지킨다
- 앞 단계가 FAIL이면 뒷 단계를 실행하지 않고 즉시 보고한다 (fail-fast)

---

## Pre-flight: 도구 및 환경 사전 점검

**모든 Part 실행 전에 반드시 먼저 수행한다.** 하나라도 FAIL이면 게이트 진입 자체를 차단한다.

### PF-1. 필수 도구 설치 확인

아래 명령을 실행하여 각 도구의 설치 여부와 버전을 확인한다.

```bash
echo "=== 필수 도구 점검 ==="

# Java
java -version 2>&1 | head -1 || echo "FAIL: java not installed"

# Gradle (wrapper 사용 시 gradlew 존재 확인)
ls gradlew 2>/dev/null && echo "OK: gradlew exists" || echo "FAIL: gradlew not found"

# Docker
docker --version 2>/dev/null || echo "FAIL: docker not installed"
docker compose version 2>/dev/null || echo "FAIL: docker compose not installed"

# 프론트엔드 (플랫폼별 분기)
<!-- IF PLATFORM == REACT -->
node --version 2>/dev/null || echo "FAIL: node not installed"
npm --version 2>/dev/null || echo "FAIL: npm not installed"
<!-- ELIF PLATFORM == VUE -->
node --version 2>/dev/null || echo "FAIL: node not installed"
npm --version 2>/dev/null || echo "FAIL: npm not installed"
<!-- ELIF PLATFORM == FLUTTER -->
flutter --version 2>/dev/null || echo "FAIL: flutter not installed"
dart --version 2>/dev/null || echo "FAIL: dart not installed"
<!-- ENDIF -->

# Python (AI 서비스 해당 시)
python3 --version 2>/dev/null || echo "FAIL: python3 not installed"
```

- 모든 도구에서 버전이 출력되어야 PASS
- 하나라도 "not installed"가 출력되면 **FAIL** → 설치 방법 안내 후 재점검

### PF-2. Docker 데몬 상태 확인

```bash
docker info > /dev/null 2>&1 && echo "PASS: Docker daemon running" || echo "FAIL: Docker daemon not running"
```

### PF-3. 포트 가용성 확인

```bash
echo "=== 포트 가용성 점검 ==="
# 프로젝트에서 사용하는 포트 목록을 docker-compose.yml과 application.yml에서 추출하여 확인
for port in $(grep -oP '\d{4,5}(?=:)' docker-compose.yml 2>/dev/null | sort -u); do
  (echo > /dev/tcp/localhost/$port) 2>/dev/null && echo "WARN: port $port already in use" || echo "OK: port $port available"
done
```

- 백킹서비스·백엔드·프론트엔드가 사용할 포트가 이미 점유되어 있으면 **WARN** (기존 서비스가 이미 기동 중일 수 있음)
- 기동 단계에서 포트 충돌이 발생하면 **FAIL**

### Pre-flight 판정

PF-1 ~ PF-3 모두 PASS해야 본 게이트의 Part 검증 진입. FAIL 항목이 있으면:
1. 누락 도구의 설치 가이드를 제시
2. 사용자에게 설치 완료 후 재수행을 요청
3. **도구 미설치 상태로 게이트를 진행하지 않는다**

---

## Part 1. Phase 2 완료 검증 (Step 3-5, qa-engineer)

Step 3-1 ~ 3-3 완료 후, **작업자와 독립된 qa-engineer**가 실제 빌드·테스트·산출물을 재검증한다.
(작업한 에이전트가 스스로 완료를 선언하는 것을 방지하기 위한 독립 검증)

> **검증 순서**: fail-fast 원칙에 따라 비용이 낮은 정적 검사부터 수행하고, 비용이 높은 동적 검증(빌드·기동)은 후순위로 배치한다.

### 검증 절차

#### 1. EXPECTED OUTCOME 산출물 존재 확인
- `docs/develop/dev-plan.md`에 명시된 산출물 파일이 모두 존재하는지 확인
- 각 파일에 대해 `ls -la {파일경로}` 실행 → 출력을 증거로 기록
- 누락 파일이 있으면 FAIL

#### 2. TODO/FIXME 전수 검사
```bash
grep -rn "TODO\|FIXME\|HACK" --include="*.java" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.vue" --include="*.dart" . | grep -v "/build/" | grep -v "node_modules/" | grep -v "/.gradle/"
```
- 결과 0건이어야 PASS
- 발견된 항목이 있으면 **파일명:라인:내용**을 기록하고 FAIL

#### 3. API 명세 vs 실제 구현 대조
- `docs/design/api-design.md` (또는 OpenAPI 명세)의 엔드포인트 목록을 추출
- 각 엔드포인트에 대응하는 Controller 메서드가 실제 코드에 존재하는지 전수 확인
- **확인 방법**: `grep -rn "@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping\|@PatchMapping" --include="*.java" .` 로 실제 매핑 목록 추출 후 대조
- 누락 엔드포인트가 있으면 FAIL + 누락 목록 기록

#### 4. 프론트엔드 빌드 + 정적 분석 + 테스트

**Pre-flight에서 도구 설치를 확인한 상태에서만 실행한다.**

<!-- IF PLATFORM == REACT -->
```bash
cd frontend && npm ci && npm run build && npm run lint && npm test --if-present
```
- `npm ci` 성공 (의존성 설치)
- `npm run build` 종료코드 0 (빌드 성공)
- `npm run lint` 경고만 허용, 에러 0건
- `npm test` 실패 0건 (test 스크립트 미정의 시 건너뜀)
<!-- ELIF PLATFORM == VUE -->
```bash
cd frontend && npm ci && npm run build && npm run lint && npm test --if-present
```
- 동일 기준
<!-- ELIF PLATFORM == FLUTTER -->
```bash
cd frontend
flutter pub get
flutter analyze --no-fatal-warnings
flutter build apk --debug 2>&1 | tail -5   # Android 빌드 (또는 flutter build web)
flutter test 2>&1 | tail -20               # 단위/위젯 테스트
```
- `flutter pub get` 성공 (의존성 설치)
- `flutter analyze` 에러 0건 (warning은 허용, `--no-fatal-warnings` 사용)
- `flutter build` 종료코드 0 (빌드 성공). Android SDK 미설치 시 `flutter build web`으로 대체
- `flutter test` 실패 0건. 테스트 파일 미존재 시 "No tests" 출력은 PASS로 간주하되 **경고 기록**
- **각 명령의 실제 출력을 증거로 캡처한다**
<!-- ENDIF -->

- 위 전체가 성공이어야 PASS

> **중요**: `flutter`/`npm`/`node` 명령이 `command not found`로 실패하면 FAIL이다. Pre-flight에서 이미 확인했으므로 이 단계에서 발생하면 안 되지만, 방어적으로 재확인한다.

#### 5. 백엔드 빌드 + 전체 단위 테스트
```bash
./gradlew clean build test 2>&1 | tee /tmp/gradle-test-output.log
echo "Exit code: $?"
# 결과 요약
grep -E "tests completed|BUILD" /tmp/gradle-test-output.log
```
- 빌드 종료코드 0 (BUILD SUCCESSFUL)
- 테스트 실패 0건 (`X tests completed, 0 failed` 패턴 확인)
- **실제 Gradle 출력의 결과 라인을 증거로 캡처한다**

#### 6. AI 서비스 테스트 (해당 시)
```bash
cd ai-service && pip install -r requirements.txt && pytest -v 2>&1 | tee /tmp/pytest-output.log
echo "Exit code: $?"
```
- `pip install` 성공
- `pytest` 종료코드 0 (전체 PASS)
- **pytest 출력의 결과 라인을 증거로 캡처한다**
- **SKIP 조건**: AI 서비스 디렉토리(`ai-service/`)가 존재하지 않으면 이 항목을 건너뜀

#### 7. 각 서비스 독립 기동 + 헬스체크 + Mock 연동 검증

**7-a. 백킹서비스 + 백엔드 기동**
```bash
# 백킹서비스 기동
docker compose up -d
sleep 10
docker compose ps   # 모든 컨테이너 running 확인

# 백엔드 전체 서비스 기동
python3 tools/run-intellij-service-profile.py --config-dir . --delay 5
sleep 30

# 헬스체크 — 각 서비스 포트에 대해 실행
for port in $(grep -oP 'server\.port=\K\d+' */src/main/resources/application.yml 2>/dev/null | sort -u); do
  status=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$port/actuator/health 2>/dev/null)
  echo "Port $port: HTTP $status"
  if [ "$status" != "200" ]; then echo "FAIL: port $port health check failed"; fi
done
```
- 모든 Docker 컨테이너 상태가 `running`/`Up`이어야 PASS
- 모든 서비스의 헬스체크 응답이 `200`이어야 PASS
- `logs/{service-name}.log`에서 `ERROR` 레벨 로그 검색:
  - 일시적 DB 재연결 에러(`HikariPool.*Connection|Reconnect|retry|Connection reset` 패턴)는 최종 헬스체크 성공 시 무시
  - 그 외 ERROR 로그가 있으면 FAIL

**7-b. Prism Mock 연동 검증**
```bash
# Prism Mock 서버 기동
docker compose --profile mock up -d
sleep 5
# Prism 응답 확인
curl -s -o /dev/null -w '%{http_code}' http://localhost:4010/{대표 엔드포인트}
```
- Prism Mock 서버 응답 확인 → 정상 응답(2xx)이어야 PASS

**7-c. 프론트엔드 → Mock 서버 연동 확인**
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
# Flutter는 기기/에뮬레이터가 필요하므로 빌드 성공 여부로 대체
cd frontend && flutter build web 2>&1 | tail -5
echo "Exit code: $?"
```
- Flutter는 모바일 앱이므로 `flutter run`은 에뮬레이터가 필요하다
- **빌드 성공 (`flutter build web` 또는 `flutter build apk --debug`)을 프론트엔드 동작 검증으로 대체한다**
- 빌드 종료코드 0이어야 PASS
<!-- ENDIF -->

**7-d. AI 서비스 독립 기동** (해당 시)
```bash
docker compose --profile ai up -d
sleep 10
curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health
```
- 헬스체크 엔드포인트 호출 → 정상 응답 확인
- `logs/ai-service.log`에서 `ERROR` 레벨 로그 검색 (기준 동일)

### 게이트 판정

위 7개 항목 모두 PASS해야 Step 4 진입. FAIL 항목 발견 시 아래 형식으로 보고한다:

```
## Part 1 검증 결과

| # | 항목 | 결과 | 증거 |
|---|------|------|------|
| 1 | 산출물 존재 | PASS | ls 출력 첨부 |
| 2 | TODO/FIXME | PASS | grep 결과 0건 |
| 3 | API 명세 대조 | PASS | 누락 0건 |
| 4 | 프론트엔드 빌드 | FAIL | flutter analyze 에러 3건 (출력 첨부) |
| 5 | 백엔드 빌드+테스트 | PASS | BUILD SUCCESSFUL, 204 tests, 0 failed |
| 6 | AI 서비스 | SKIP | ai-service/ 미존재 |
| 7 | 서비스 기동+헬스체크 | PASS | 모든 포트 200 |

### FAIL 항목 상세
- **항목 4**: flutter analyze에서 3건의 에러 발견
  - lib/screens/home.dart:42 — unused_import
  - ...

### 판정: FAIL (1건)
→ 오케스트레이터에 보고하여 frontend-developer에게 수정 지시 필요
```

---

## Part 2. Phase 3 완료 검증 (Step 4-4, architect)

Step 4-1 ~ 4-3 완료 후, **작업자와 독립된 architect**가 통합 연동의 실제 동작을 검증한다.
(통합이 정상 완료되지 않은 상태에서 테스트 단계로 넘어가는 것을 방지)

### 검증 절차

#### 1. Mock 참조 잔존 확인
```bash
echo "=== Mock URL 잔존 검사 ==="
# 테스트 코드, 설정의 mock 프로파일, 주석은 제외
grep -rn "localhost:4010\|prism\|mock-api\|MOCK_" \
  --include="*.ts" --include="*.tsx" --include="*.vue" --include="*.dart" --include="*.java" --include="*.py" \
  frontend/ src/ ai-service/ 2>/dev/null \
  | grep -v "/test/" \
  | grep -v "/build/" \
  | grep -v "node_modules/" \
  | grep -v "\.gradle/" \
  | grep -v "// " \
  | grep -v "# " \
  | grep -v "mock.*profile\|AppEnvironment\.mock"
```
- 프론트엔드·백엔드 **프로덕션 코드**에 Prism/Mock URL이 남아있으면 FAIL
- 테스트 코드, 주석, mock 프로파일 설정은 제외

#### 2. 전체 서비스 동시 기동 + 헬스체크
```bash
# 백킹서비스 기동
docker compose up -d
sleep 10
docker compose ps

# 백엔드 전체 서비스 기동
python3 tools/run-intellij-service-profile.py --config-dir . --delay 5
sleep 30

# 헬스체크 — 각 서비스별 실행
echo "=== 헬스체크 ==="
FAIL_COUNT=0
for port in $(grep -oP 'server\.port=\K\d+' */src/main/resources/application.yml 2>/dev/null | sort -u); do
  status=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$port/actuator/health 2>/dev/null)
  echo "Port $port: HTTP $status"
  if [ "$status" != "200" ]; then FAIL_COUNT=$((FAIL_COUNT+1)); fi
done
echo "Health check failures: $FAIL_COUNT"

# AI 서비스 기동 (해당 시)
# docker compose --profile ai up -d
```
- 전 서비스 기동 후 헬스체크 실패 0건이어야 PASS
- **Docker 컨테이너 상태 + 헬스체크 출력을 증거로 기록한다**

#### 3. 통합 테스트 자동 실행
```bash
./gradlew test --tests '*IntegrationTest' --continue 2>&1 | tee /tmp/integration-test-output.log
echo "Exit code: $?"
# 결과 요약
grep -E "tests completed|BUILD" /tmp/integration-test-output.log
```
- Step 4-3에서 작성한 통합 테스트 코드 전체 실행
- 테스트 실패 0건이어야 PASS
- 실패 시 실패 테스트명 및 원인을 기록
- **Gradle 출력의 결과 라인을 증거로 캡처한다**

#### 4. BE↔AI 연동 호출 검증 (해당 시)
- 백엔드에서 AI 서비스를 호출하는 API를 식별
- 해당 API를 `curl`로 호출 → AI 서비스까지 정상 도달·응답 확인
```bash
# 예시: 브리핑 생성 API가 AI 서비스를 호출하는 경우
curl -s -X POST http://localhost:{be_port}/api/v1/{endpoint} \
  -H "Authorization: Bearer {test_token}" \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```
- 정상 응답(2xx) 또는 AI Fallback 응답이어야 PASS
- Circuit Breaker/Fallback 동작 확인:
  ```bash
  # AI 서비스 중지 후 호출 → Fallback 응답 확인
  docker compose --profile ai stop
  curl -s http://localhost:{be_port}/api/v1/{ai_endpoint}
  # Fallback 응답이 오는지 확인 (5xx가 아닌 규칙 기반 응답 등)
  ```
- **SKIP 조건**: AI 서비스 미존재 시 건너뜀

#### 5. 프론트엔드 → 백엔드 실제 연동 검증

**5-a. API URL 정적 검증**
<!-- IF PLATFORM == REACT -->
- `frontend/.env.production` (또는 `.env.local`)의 `REACT_APP_API_URL` (CRA) 또는 `VITE_API_URL` (Vite) 변수가 실제 백엔드 URL(`http://localhost:{port}`)을 가리키는지 확인
<!-- ELIF PLATFORM == VUE -->
- `frontend/.env.production` (또는 `.env.local`)의 `VUE_APP_API_URL` (Vue CLI) 또는 `VITE_API_URL` (Vite) 변수가 실제 백엔드 URL(`http://localhost:{port}`)을 가리키는지 확인
<!-- ELIF PLATFORM == FLUTTER -->
- `frontend/lib/` 하위의 환경 설정 파일(예: `config/app_config.dart`, `core/config/`)에서 API base URL이 실제 백엔드 URL(`http://localhost:{port}`)을 가리키는지 확인
```bash
grep -rn "localhost:" frontend/lib/ --include="*.dart" | grep -v "test" | grep -v "//"
```
<!-- ENDIF -->
- Prism Mock URL(`localhost:4010`)이 **프로덕션 코드**에 남아있으면 FAIL (mock 프로파일 설정은 제외)

**5-b. 백엔드 주요 엔드포인트 curl 검증**
```bash
echo "=== 주요 엔드포인트 curl 검증 ==="
# docs/design/api-design.md에서 주요 엔드포인트 3~5개를 선정하여 호출
# 인증 불필요 엔드포인트
curl -s -o /dev/null -w 'GET /api/v1/subscriptions/plans -> HTTP %{http_code}\n' http://localhost:{payment_port}/api/v1/subscriptions/plans
# 인증 필요 엔드포인트 (토큰 없이 호출 → 401 확인)
curl -s -o /dev/null -w 'GET /api/v1/trips -> HTTP %{http_code}\n' http://localhost:{schedule_port}/api/v1/trips
```
- 인증 불필요 엔드포인트: 2xx 응답이어야 PASS
- 인증 필요 엔드포인트: 401 응답이어야 PASS (보안 필터 동작 확인)
- 5xx 서버 에러가 반환되면 **FAIL**

**5-c. 프론트엔드 빌드 확인**
<!-- IF PLATFORM == REACT -->
```bash
cd frontend && npm run build 2>&1 | tail -10
echo "Exit code: $?"
```
<!-- ELIF PLATFORM == VUE -->
```bash
cd frontend && npm run build 2>&1 | tail -10
echo "Exit code: $?"
```
<!-- ELIF PLATFORM == FLUTTER -->
```bash
cd frontend
flutter pub get
flutter analyze --no-fatal-warnings 2>&1 | tail -10
flutter build web 2>&1 | tail -10   # 또는 flutter build apk --debug
echo "Exit code: $?"
```
- `flutter pub get`: 의존성 설치 성공
- `flutter analyze`: 에러 0건 (warning 허용)
- `flutter build`: 종료코드 0
- **빌드 도구가 설치되어 있지 않으면 FAIL** (Pre-flight에서 확인했으므로 발생 시 프로세스 오류)
<!-- ENDIF -->
- 실제 API URL 설정 상태에서 빌드 성공이어야 PASS
- **빌드 명령의 실제 출력을 증거로 캡처한다**

### 게이트 판정

위 5개 항목 모두 PASS해야 Step 5 진입. 보고 형식은 Part 1과 동일하게 증거 기반 테이블을 사용한다.

---

## Part 3. 최종 완료 검증 (Step 5-3, architect)

Step 5-2(종합 QA) 완료 후, **qa-engineer와 독립된 architect**가 최종 완료 여부를 판정한다.
(QA 에이전트가 자기 작업을 자기가 완료 선언하는 것을 방지하고, 설계↔구현 추적성까지 검증)

### 검증 절차

#### 1. 테스트 리포트 존재 및 품질 확인
```bash
# 파일 존재
ls -la docs/develop/test-report.md

# 실패 0건 확인 — 리포트 내에 "FAIL" 카운트가 0인지
grep -i "FAIL\|failed\|실패" docs/develop/test-report.md | grep -v "0건\| 0 \|0%\|: 0\|FAIL.*수정 완료\|이전.*수정"
```
- 파일이 존재하고, 미해결 실패가 0건이어야 PASS
- 테스트 커버리지(논리적 또는 JaCoCo)가 리포트에 명시되어 있는지 확인
- "MVP Must Have 커버리지" 섹션의 커버리지가 100%인지 확인 (100% 미만이면 FAIL)
- "미해결 버그" 항목이 0건인지 확인 (1건 이상이면 FAIL)

#### 2. 완료 조건 전수 체크

아래 파일/디렉토리의 존재를 **실제 명령어로** 확인한다:

```bash
echo "=== 완료 조건 전수 체크 ==="
FAIL_COUNT=0
for target in \
  "docs/develop/dev-plan.md" \
  "gradlew" \
  "settings.gradle" \
  "build.gradle" \
  "docker-compose.yml" \
  ".env.example" \
  "docs/develop/test-report.md" \
  "docs/develop/integration-test-cases.md" \
  "docs/develop/e2e-test-cases.md"
do
  if [ -f "$target" ]; then echo "OK: $target"; else echo "MISSING: $target"; FAIL_COUNT=$((FAIL_COUNT+1)); fi
done

# 프론트엔드 프로젝트 존재
<!-- IF PLATFORM == REACT -->
[ -f "frontend/package.json" ] && echo "OK: frontend/package.json" || { echo "MISSING: frontend/package.json"; FAIL_COUNT=$((FAIL_COUNT+1)); }
<!-- ELIF PLATFORM == VUE -->
[ -f "frontend/package.json" ] && echo "OK: frontend/package.json" || { echo "MISSING: frontend/package.json"; FAIL_COUNT=$((FAIL_COUNT+1)); }
<!-- ELIF PLATFORM == FLUTTER -->
[ -f "frontend/pubspec.yaml" ] && echo "OK: frontend/pubspec.yaml" || { echo "MISSING: frontend/pubspec.yaml"; FAIL_COUNT=$((FAIL_COUNT+1)); }
<!-- ENDIF -->

# 통합 테스트 코드 존재
IT_COUNT=$(find . -name "*IntegrationTest.java" -path "*/test/*" | wc -l)
echo "IntegrationTest files: $IT_COUNT"
[ "$IT_COUNT" -gt 0 ] || { echo "FAIL: No IntegrationTest files"; FAIL_COUNT=$((FAIL_COUNT+1)); }

# E2E 테스트 존재
[ -d "e2e" ] && echo "OK: e2e/ directory exists" || { echo "MISSING: e2e/ directory"; FAIL_COUNT=$((FAIL_COUNT+1)); }
E2E_COUNT=$(find e2e/ -name "*.sh" -o -name "*.spec.ts" -o -name "*_test.dart" 2>/dev/null | wc -l)
echo "E2E test files: $E2E_COUNT"
[ "$E2E_COUNT" -gt 0 ] || { echo "FAIL: No E2E test files"; FAIL_COUNT=$((FAIL_COUNT+1)); }

# AI 서비스 (해당 시)
if [ -d "ai-service" ]; then
  echo "OK: ai-service/ exists"
else
  echo "SKIP: ai-service/ not present (AI service not in scope)"
fi

echo "=== 누락 항목: $FAIL_COUNT 건 ==="
```
- 모든 항목 OK (누락 0건)이어야 PASS

#### 3. 설계↔구현 추적성 검증
- `docs/design/api-design.md`의 전체 엔드포인트 목록 추출
- 각 엔드포인트에 대응하는 Controller 코드가 존재하는지 대조
```bash
echo "=== Controller 매핑 전수 조사 ==="
grep -rn "@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping\|@PatchMapping\|@RequestMapping" \
  --include="*.java" . | grep -v "/test/" | grep -v "/build/"
```
- `docs/design/data-design.md`의 Entity 목록과 실제 Entity 클래스 대조
```bash
echo "=== Entity 클래스 전수 조사 ==="
grep -rn "@Entity" --include="*.java" . | grep -v "/test/" | grep -v "/build/"
```
- 누락 구현이 있으면 FAIL + 누락 목록 기록

#### 4. 전체 테스트 스위트 최종 실행

**4-a. 백엔드 단위 + 통합 테스트**
```bash
./gradlew clean build test 2>&1 | tee /tmp/final-test-output.log
echo "=== Gradle Exit Code: $? ==="
grep -E "tests completed|BUILD" /tmp/final-test-output.log
```
- BUILD SUCCESSFUL + 테스트 실패 0건이어야 PASS
- **Gradle 출력을 증거로 캡처한다**

**4-b. 프론트엔드 빌드 + 테스트**
<!-- IF PLATFORM == REACT -->
```bash
cd frontend && npm ci && npm run build && npm test --if-present 2>&1 | tee /tmp/frontend-test-output.log
echo "=== npm Exit Code: $? ==="
```
<!-- ELIF PLATFORM == VUE -->
```bash
cd frontend && npm ci && npm run build && npm test --if-present 2>&1 | tee /tmp/frontend-test-output.log
echo "=== npm Exit Code: $? ==="
```
<!-- ELIF PLATFORM == FLUTTER -->
```bash
cd frontend
flutter pub get 2>&1 | tail -3
flutter analyze --no-fatal-warnings 2>&1 | tee /tmp/flutter-analyze-output.log
flutter test 2>&1 | tee /tmp/flutter-test-output.log
flutter build web 2>&1 | tee /tmp/flutter-build-output.log
echo "=== Flutter Build Exit Code: $? ==="
```
- `flutter analyze`: 에러 0건
- `flutter test`: 실패 0건 (테스트 파일 미존재 시 경고만 기록)
- `flutter build`: 종료코드 0
- **각 명령의 출력을 증거로 캡처한다**
<!-- ENDIF -->

**4-c. E2E 테스트 실행**
<!-- IF PLATFORM == REACT -->
```bash
cd e2e && npx playwright test 2>&1 | tee /tmp/e2e-test-output.log
echo "=== E2E Exit Code: $? ==="
```
<!-- ELIF PLATFORM == VUE -->
```bash
cd e2e && npx playwright test 2>&1 | tee /tmp/e2e-test-output.log
echo "=== E2E Exit Code: $? ==="
```
<!-- ELIF PLATFORM == FLUTTER -->
```bash
# Flutter 프로젝트의 E2E 테스트: API 레벨 스크립트 또는 Flutter integration test
if [ -f "e2e/api-e2e-test.sh" ]; then
  bash e2e/api-e2e-test.sh 2>&1 | tee /tmp/e2e-test-output.log
  echo "=== E2E Exit Code: $? ==="
fi
if ls frontend/integration_test/*_test.dart 1>/dev/null 2>&1; then
  cd frontend && flutter test integration_test/ 2>&1 | tee /tmp/flutter-integration-output.log
  echo "=== Flutter Integration Test Exit Code: $? ==="
fi
```
- E2E 스크립트/테스트가 존재하면 **반드시 실행한다** (작성만 하고 실행 안 하는 것은 불허)
- 종료코드 0이어야 PASS
- E2E 스크립트가 존재하지만 실행하지 않으면 **FAIL**
- **E2E 테스트 출력을 증거로 캡처한다**
<!-- ENDIF -->

**4-d. AI 서비스** (해당 시)
```bash
cd ai-service && pytest -v 2>&1 | tee /tmp/ai-test-output.log
echo "=== pytest Exit Code: $? ==="
```

#### 5. 설정 일관성 교차 검증
```bash
echo "=== 설정 일관성 검증 ==="

# .env.example의 키 목록
echo "--- .env.example keys ---"
grep -oP '^[A-Z_]+=?' .env.example 2>/dev/null | sed 's/=$//' | sort

# docker-compose.yml의 environment 변수
echo "--- docker-compose.yml env vars ---"
grep -oP '\$\{[A-Z_]+\}' docker-compose.yml 2>/dev/null | tr -d '${' | tr -d '}' | sort -u

# application.yml의 placeholder
echo "--- application.yml placeholders ---"
grep -roh '\$\{[A-Z_]*\}' */src/main/resources/application.yml 2>/dev/null | tr -d '${' | tr -d '}' | sort -u
```
- `.env.example`의 키 ⊇ `docker-compose.yml`의 `${VAR}` 참조
- `.env.example`의 키 ⊇ `application.yml`의 `${VAR}` 참조
- 불일치 항목이 있으면 FAIL + 불일치 목록 기록

### 게이트 판정

위 5개 항목 모두 PASS해야 Step 6(개발 완료 보고) 진입 허용.

보고 형식:

```
## Part 3 최종 검증 결과

| # | 항목 | 결과 | 증거 |
|---|------|------|------|
| 1 | 테스트 리포트 품질 | PASS/FAIL | 파일 존재, 실패 0건, 커버리지 명시 |
| 2 | 완료 조건 전수 체크 | PASS/FAIL | 누락 N건 (상세 목록) |
| 3 | 설계↔구현 추적성 | PASS/FAIL | 누락 엔드포인트 N건 |
| 4-a | 백엔드 테스트 | PASS/FAIL | Gradle 출력: X tests, 0 failed |
| 4-b | 프론트엔드 빌드+테스트 | PASS/FAIL | flutter build exit code: 0 |
| 4-c | E2E 테스트 | PASS/FAIL | 스크립트 실행 결과 (출력 첨부) |
| 4-d | AI 서비스 테스트 | PASS/SKIP | pytest 출력 |
| 5 | 설정 일관성 | PASS/FAIL | 불일치 N건 |

### 최종 판정: PASS / FAIL
```

FAIL 항목 발견 시 해당 작업 에이전트에게 수정을 지시하고, 수정 완료 후 Part 3을 처음부터 재수행한다.

**이 게이트를 통과하지 않으면 개발 완료 보고를 절대 수행하지 않는다.**
