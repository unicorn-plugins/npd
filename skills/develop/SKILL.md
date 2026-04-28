---
name: develop
description: 개발 단계 AI 협업 — 백엔드·프론트엔드·AI엔지니어·QA가 API 계약 기반 병렬 개발 수행
type: orchestrator
user-invocable: true
---

# Develop

[NPD Develop 활성화]

## 목표

백엔드개발자·프론트엔드개발자·AI엔지니어·QA가 협업하여
API 계약(OpenAPI 명세) 기반 병렬 개발 전략으로 개발을 수행함.

- **Phase 1**: 환경 구성 (백엔드/프론트엔드/AI/백킹서비스 병렬 초기화)
- **Phase 2**: API 계약 기반 병렬 개발 (BE API + FE Mock + AI 서비스 동시 진행)
- **Phase 3**: 통합 연동 (Mock→실제 API 전환, BE↔AI 연동)
- **Phase 4**: 종합 테스트 및 QA

## 활성화 조건

사용자가 `/npd:develop` 호출 시 또는 "개발 시작", "개발해줘", "구현 시작" 키워드 감지 시.

주의사항: 중간 단계부터 시작할 때도 사전 설정 수집 및 진행 모드를 설정하는 Phase 0은 항상 수행해야 합니다.

## 선행 조건

- `/npd:create` 완료 (프로젝트 디렉토리 및 AGENTS.md 존재)
- `/npd:design` 완료 (`docs/design/` 산출물 존재)

## 작업 환경 변수 로드

AGENTS.md 파일에서 `## 환경변수` 섹션의 환경변수 로딩.
로딩 실패 시 사용자에게 `/npd:create`를 먼저 수행하라고 안내하고 종료.

## AI 개발 키트

설계→개발 경계에서 1회 컴파일되는 개발 입력 세트. Phase 1 / Step 1에서 생성되며 이후 모든 Step의 유일한 입력이다.

| 구성 요소 | 경로 | 원본 | 역할 |
|-----------|------|------|------|
| 통합 맥락 | `docs/develop/dev-plan.md` | 전체 설계 산출물 분석 결과 | 전체 그림 + 아키텍처 결정사항 |
| 백엔드 계약 | `docs/design/api/*.yaml` | 이미 존재 (변환 불요) | API 엔드포인트·스키마 정의 |
| DB 계약 | `docs/design/database/*.md` | 이미 존재 (변환 불요) | 테이블·인덱스·관계 정의 |
| 패키지 구조 | `docs/design/class/package-structure.md` | 이미 존재 (변환 불요) | 서비스별 패키지 레이아웃 |
| 프론트엔드 계약 | `docs/plan/.../prototype/*.html+css` | 이미 존재 (변환 불요) | UI 레이아웃·스타일 정의 |
| 행위 계약 | `test/design-contract/*.spec.ts` | 시퀀스 설계서에서 변환 | alt/else 분기 → it() 테스트 케이스 (참고 자료, 실행 불요) |

> **원칙**: **Phase 1 / Step 1 (AI 개발 키트 컴파일) 이후의 에이전트**는 `docs/design/sequence/`, `docs/design/class/*.puml` 등 원본 설계 문서를 직접 읽지 않는다.
> 필요한 정보는 모두 AI 개발 키트에 포함되어 있다. 원본이 필요한 경우는 키트에 누락이 있는 것이므로 Phase 1 / Step 1을 보완한다.
> **단, Phase 1 / Step 1 (AI 개발 키트 컴파일)은 변환 단계이므로 원본 설계 문서 읽기가 필수이다.** 이 단계에서만 원본을 읽어 키트로 변환한다.

## 에이전트 호출 규칙

| 에이전트 | FQN |
|----------|-----|
| backend-developer | `npd:backend-developer:backend-developer` |
| frontend-developer | `npd:frontend-developer:frontend-developer` |
| ai-engineer | `npd:ai-engineer:ai-engineer` |
| qa-engineer | `npd:qa-engineer:qa-engineer` |
| product-owner | `npd:product-owner:product-owner` |
| service-planner | `npd:service-planner:service-planner` |

### 프롬프트 조립

- `{NPD_PLUGIN_DIR}/resources/guides/combine-prompt.md`에 따라
  AGENT.md + agentcard.yaml + tools.yaml 합치기
- `Agent(subagent_type=FQN, model=tier_mapping 결과, prompt=조립된 프롬프트)` 호출
- tier → 모델 매핑은 `{NPD_PLUGIN_DIR}/gateway/runtime-mapping.yaml` 참조

### 서브 에이전트 호출

워크플로우 단계에 `Agent: {agent-name}`이 명시된 경우,
메인 에이전트는 해당 단계를 직접 수행하지 않고,
반드시 위 프롬프트 조립 규칙에 따라 해당 에이전트를 호출하여 결과를 받아야 함.

서브에이전트 호출 없이 메인 에이전트가 해당 산출물을 직접 작성하면
스킬 미준수로 간주함.

## 공통 참조 리소스

모든 Step에서 아래 표준을 준수:

- **개발주석표준**: `{NPD_PLUGIN_DIR}/resources/references/standard_comment.md`
- **테스트코드표준**: `{NPD_PLUGIN_DIR}/resources/references/standard_testcode.md`
- **패키지구조표준**: `{NPD_PLUGIN_DIR}/resources/references/standard_package_structure.md`
- **병렬 처리 전략**: `{NPD_PLUGIN_DIR}/resources/guides/design/common-principles.md`

## 가이드 문서 조건 분기 프로토콜

가이드 문서(.md) 내 `<!-- IF VAR == VALUE -->` 조건 지시문 처리. 지원 변수
(PLATFORM, FRONTEND_PORT, MOCK, TEST_MODE)는 `AGENTS.md > ### develop > 지원 변수`
에 저장·조회한다.
상세: `{NPD_PLUGIN_DIR}/resources/guides/develop/conditional-branching-protocol.md` ← **필수 로드**

## 진행상황 업데이트 및 재개

`{PROJECT_DIR}/AGENTS.md`에 각 Phase의 Step 완료 시 저장. 최종 완료 시 `Done`으로 표기.

```md
## 워크플로우 진행상황
### develop
- 진행 모드: {선택값}
- 개발 범위: {선택된 Phase 목록} (Phase 0 / Step 1에서 기록)
- 마지막 완료 Phase/Step: Phase 1/Step 0
- 지원 변수:
  - PLATFORM: {REACT|VUE|FLUTTER} (Phase 1 / Step 4 시작 시 결정)
  - FRONTEND_PORT: {3000} (PLATFORM 결정 직후)
  - MOCK: {SINGLE} (Phase 1 / Step 3 완료 후)
  - TEST_MODE: {AUTO|MANUAL} (Phase 0 / Step 5)
- 기술스택:
  - Java: {버전}
  - Spring Boot: {버전}
  - 빌드 도구: {Gradle/Maven}
  - Node.js: {버전}
  - 프론트엔드: {React/Vue/Flutter}
  - Python: {버전}
  - AI 프레임워크: {FastAPI}
```

진행상황 정보가 있는 경우 마지막 완료 Step 이후부터 자동 재개.
`기술스택`은 Phase 1 / Step 1 (AI 개발 키트 컴파일) 수립 시 `dev-plan.md`의 `### 10-5. 기술스택 정보`에서 추출하여 기록.
`지원 변수`는 `## 가이드 문서 조건 분기 프로토콜`의 결정 시점에 따라 단계별로 채워지며, 이후 가이드 실행 시 해당 값을 우선 조회한다.

## 워크플로우

### 개요

```
Phase 0: 사전 설정·진행 모드 선택 (개발 범위 + 크리덴셜 + 테스트 모드 + 진행 모드)
   ↓
Phase 1: 환경 구성 (AI 개발 키트 + 백엔드/백킹/FE/AI/실행 프로파일)
   ↓
Phase 2: API 계약 기반 병렬 개발 (BE API + FE Mock + AI)
   ↓
Phase 3: 통합 연동 (FE 실제 API + BE↔AI + API 테스트)
   ↓
Phase 4: 종합 테스트 및 QA (브라우저 테스트 + 제품 검증 + Final Report)
   ↓
Phase 5: 개발 완료
```

### Phase 0: 사전 설정·진행 모드 선택

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/phase0-presetup.md` ← **필수 로드**
- **TASK**: 위 GUIDE의 6개 Step 절차에 따라 사용자 입력을 사전 수집
- **EXPECTED OUTCOME**:
  - `AGENTS.md > ### develop` 섹션에 진행 모드·개발 범위·지원 변수(TEST_MODE) 기록
  - `{PROJECT_DIR}/.env`에 크리덴셜 (또는 `.env.example`에 키 등록)

#### Step 1. 개발 범위 결정
HighLevel 아키텍처 14.1 개발 단계에서 구현 범위를 사용자에게 선택받음.

#### Step 2. OAuth2 크리덴셜 확인 (조건부)
설계서의 인증 방식이 OAuth2/하이브리드인 경우 Provider 크리덴셜 수집.

#### Step 3. Gemini API Key 확인
프론트엔드 이미지 생성용 GEMINI_API_KEY 수집.

#### Step 4. AI 서비스 크리덴셜 확인 (조건부)
ai-service-design.md 존재 시 LLM/Tool/RAG 크리덴셜 수집.

#### Step 5. 테스트 모드 선택
브라우저 테스트 모드(자동/수동) 선택 → AGENTS.md `지원 변수 > TEST_MODE`에 저장.

#### Step 6. 진행 모드 선택
단계별 승인/자동 진행 선택. 단계별 승인 시 ASK_USER 형식 정의됨.

---

### Phase 1: 환경 구성

#### Step 1. AI 개발 키트 컴파일 → Agent: architect (주도) + backend-developer + frontend-developer + ai-engineer (병렬 검증)

Step 1은 두 단계로 구성된다:

##### Step 1-1. 종합 개발 계획 수립

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/dev-plan.md`
- **INPUT**: Phase 0 / Step 1에서 선택된 개발 단계(Phase) 범위
- **TASK**: 3개 에이전트 분담 작성 → architect 통합 리뷰
- **EXPECTED OUTCOME**: `docs/develop/dev-plan.md`

##### Step 1-2. 행위 계약 테스트 생성

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/design-contract-compile.md`
- **INPUT**:
  - `docs/develop/dev-plan.md` (Step 1-1 산출물)
  - `docs/design/sequence/inner/*.puml` (내부 시퀀스)
  - `docs/design/sequence/outer/*.puml` (외부 시퀀스)
  - `docs/design/api/*.yaml` (API 명세)
- **TASK**:
  1. dev-plan.md를 통합 맥락 문서로 확장 (아키텍처 결정사항, 서비스 간 의존관계 시각화 추가)
  2. 시퀀스 설계서의 alt/else 분기를 test spec의 describe/it 구조로 1:1 변환
  3. API 명세의 요청/응답 스키마를 assertion으로 변환
- **EXPECTED OUTCOME** (AI 개발 키트):
  - `docs/develop/dev-plan.md` (확장된 통합 맥락)
  - `test/design-contract/*.spec.ts` (행위 계약 참고 자료 — 백엔드 구현 시 분기 누락 방지용, 실행 불요)
- **SKIP 조건 결정**: AI 서비스 설계서 미존재 시, AI 관련 test spec 생성 건너뜀

> **이후 모든 Step의 입력**:
> - `docs/develop/dev-plan.md` (통합 맥락)
> - `docs/design/api/*.yaml` (백엔드 계약)
> - `docs/design/database/*-schema.psql` 또는 `docs/design/database/*.md` (DB 계약)
> - `docs/design/class/package-structure.md` (패키지 구조)
> - `docs/plan/.../prototype/*.html+css` (프론트엔드 계약)
> - `test/design-contract/*.spec.ts` (행위 계약 참고 자료)

#### Step 2. 백엔드 환경 구성 → Agent: backend-developer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/backend-env-setup.md`
- **TASK**: Gradle Wrapper 생성 + 멀티모듈 build.gradle 구성 + 공통 모듈 개발
- **EXPECTED OUTCOME**: `gradlew`, `gradlew.bat`, `gradle/wrapper/`, `settings.gradle`, `build.gradle`(루트), `{service-name}/build.gradle`(서비스별), `{service-name}/src/main/resources/application.yml`(서비스별), `common/src/main/java/.../common/`
- **주의**: application.yml의 환경변수는 placeholder만 작성 (환경변수 키는 Step 3의 `.env.example` 템플릿에 정의되며, 실제 값은 `{PROJECT_DIR}/.env`에서 통일)

#### Step 3. 백킹서비스 + Mock 서버 로컬 구성 → Agent: backend-developer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/backing-service-setup.md`
- **TASK**: 데이터설계서 기반 프로젝트 루트 단일 `docker-compose.yml` 작성 → DB(PostgreSQL/MySQL/MariaDB/MongoDB)/Cache/MQ + Prism Mock 서버 구성. 기본 제품(PostgreSQL) 외 선택 시 카테고리 가이드 참조
- **EXPECTED OUTCOME**: `./docker-compose.yml`, `./.env.example`, `docs/develop/backing-service-result.md`
- **docker-compose 서비스 구성**:
  - 기본 서비스 (항상 기동): DB, Cache, MQ(설계서 명시 시만)
  - mock 프로파일: Prism Mock 서버 (`docker compose --profile mock up`)
  - ai 프로파일: AI 서비스 컨테이너 (`docker compose --profile ai up`, AI 서비스 존재 시만)
- **사용자 선택**: 사용자가 선택한 백킹서비스 환경에 따라 분기

#### Step 4. 프론트엔드 프로젝트 초기화 → Agent: frontend-developer

- **GUIDE** (플랫폼별 선택):
  - REACT: `{NPD_PLUGIN_DIR}/resources/guides/develop/frontend-env-setup-react.md`
  - VUE: `{NPD_PLUGIN_DIR}/resources/guides/develop/frontend-env-setup-vue.md`
  - FLUTTER: `{NPD_PLUGIN_DIR}/resources/guides/develop/frontend-env-setup-flutter.md`
- **TASK**: 기술스택 결정 → 프로젝트 생성 → 기반 시스템(스타일/라우팅/상태관리) 구축 → Prism Mock 서버 연동 준비
- **EXPECTED OUTCOME**: `frontend/` 프로젝트 골격, `tools/generate-runtime-env.sh` (프로젝트 서비스 구성에 맞게 동적 생성됨), `npm run dev` 실행 확인

#### Step 5. AI 서비스 프로젝트 초기화 → Agent: ai-engineer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/ai-service-env-setup.md`
- **TASK**: Python/FastAPI 프로젝트 생성 → 의존성 설치 → 기본 구조 설정 → docker-compose ai 프로파일에 등록
- **EXPECTED OUTCOME**: `ai-service/` 프로젝트 골격, uvicorn 실행 확인
- **SKIP 조건**: Phase 1 / Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **Phase 1 / Step 2 ~ Step 5는 병렬 실행**: 4개 에이전트가 동시에 작업. Step 2와 Step 3의 환경변수 정합성은 placeholder 방식으로 해결 (각자 독립 작성, 값은 `{PROJECT_DIR}/.env`에서 통일. `.env.example`은 키 템플릿)

#### Step 6. 실행 프로파일 작성 → Agent: backend-developer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/run-profile.md`
- **TASK**: 백킹서비스 연결 정보(Phase 1 / Step 3) + application.yml(Phase 1 / Step 2) 기반 실행 프로파일 작성
- **EXPECTED OUTCOME**: `{service-name}/.run/{service-name}.run.xml` (서비스별)
- **선행 조건**: Phase 1 / Step 2, Step 3 완료 필수 (Phase 2 진입 전 게이트)

---

### Phase 2: API 계약 기반 병렬 개발

#### Step 1. 백엔드 API 구현 → Agent: backend-developer

> **참고**: Phase 0 / Step 2에서 OAuth2 크리덴셜을 사전 수집하였다. '나중에 설정'을 선택한 경우: 본 Step 에이전트에 "OAuth2 크리덴셜 미설정, 코드 구현만 진행하고 통합 테스트는 생략" 지시를 포함한다. Phase 3 진입 전에 `{PROJECT_DIR}/.env` 파일에서 다시 확인한다.

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/backend-api-dev.md`
- **INPUT**:
  - `docs/develop/dev-plan.md` (통합 맥락 — 서비스 목록, 의존관계, 개발 순서)
  - `docs/design/api/{service-name}-api.yaml` (API 계약)
  - `docs/design/database/{service-name}.md` (DB 계약)
  - `docs/design/class/package-structure.md` (패키지 구조)
  - `test/design-contract/{service-name}/*.spec.ts` (행위 계약 참고 자료)
- **TASK**:
  - API 설계서 + 행위 계약 참고 자료 기반 컨트롤러·서비스·레포지토리 구현 + 단위 테스트
  - **Sprint 분할 제거**: 서비스 1개를 하나의 작업 단위로 완결. 의존관계 기반 순서만 유지
  - **서비스 구현 시**: `test/design-contract/{service-name}/*.spec.ts`의 it() 케이스를 참고하여 alt/else 분기 누락 방지 (테스트 실행 불요)
- **EXPECTED OUTCOME**: `{service-name}/src/main/java/.../{service-name}/`(API 구현 코드), `{service-name}/src/test/java/.../{service-name}/`(단위 테스트 코드)
- **병렬**: 서비스 간 의존성 분석 후 독립 서비스는 병렬 구현 (서브에이전트 활용)

#### Step 2. 프론트엔드 Prism Mock 기반 개발 → Agent: frontend-developer

> **참고**: Phase 0 / Step 3에서 Gemini API Key를 사전 수집하였다. '나중에 설정'을 선택한 경우: 본 Step 에이전트에 "Gemini API Key 미설정, 이미지 생성 불가 — 이미지가 필요한 곳은 CSS/SVG 기반 대체 구현" 지시를 포함한다.

- **GUIDE** (플랫폼별 선택):
  - REACT: `{NPD_PLUGIN_DIR}/resources/guides/develop/frontend-dev-react.md`
  - VUE: `{NPD_PLUGIN_DIR}/resources/guides/develop/frontend-dev-vue.md`
  - FLUTTER: `{NPD_PLUGIN_DIR}/resources/guides/develop/frontend-dev-flutter.md`
- **TASK**: docker-compose의 Prism Mock 서버 활용 → 페이지별 구현
- **EXPECTED OUTCOME**: `frontend/src/components/`, `frontend/src/layouts/`, `frontend/src/services/api/`, `frontend/src/hooks/`, `frontend/src/pages/`
- **Prism 실행**: `docker compose --profile mock up` (Phase 1 / Step 3에서 구성)

#### Step 3. AI 서비스 구현 → Agent: ai-engineer

> **SKIP 조건**: Phase 1 / Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **참고**: Phase 0 / Step 4에서 AI 서비스 크리덴셜을 사전 수집하였다. '나중에 설정'을 선택한 경우: 본 Step 에이전트에 "LLM 크리덴셜 미설정, 코드 구현만 진행하고 실제 LLM 호출 테스트는 생략" 지시를 포함한다. Phase 3 진입 전에 `{PROJECT_DIR}/.env` 파일에서 다시 확인한다.

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/ai-service-dev.md`
- **TASK**: AI 서비스 설계서 기반 엔드포인트 구현, 프롬프트 작성, LLM 연동
- **EXPECTED OUTCOME**: `{service-name}/models/`, `{service-name}/clients/`, `{service-name}/prompts/`, `{service-name}/services/`, `{service-name}/routers/`, `{service-name}/tests/`

> **Phase 2 / Step 1 ~ Step 3은 병렬 실행**: 백엔드는 실제 API 구현, 프론트엔드는 Prism Mock으로 독립 개발, AI는 별도 서비스로 독립 개발

---

### Phase 3: 통합 연동

#### Step 1. 프론트엔드 실제 API 연동 → Agent: frontend-developer

- **PREV_ACTION**: Phase 3 진입 전에 반드시 아래 수행
  - 프로토타입 화면과 개발 화면 매핑
  - Playwright MCP로 웹브라우저로 개발된 화면의 첫 화면 오픈
  - 각 개발된 화면을 클릭하여 프로토타입과 비교하여 UI/UX 일치 여부 확인 (개발 화면이 프로토타입과 다를 경우, 프론트엔드 개발자에게 피드백하여 수정 요청)
  - 모든 개발된 화면이 프로토타입과 일치할 때까지 반복 수행
- **GUIDE** (플랫폼별 선택):
  - REACT: `{NPD_PLUGIN_DIR}/resources/guides/develop/frontend-integration-react.md`
  - VUE: `{NPD_PLUGIN_DIR}/resources/guides/develop/frontend-integration-vue.md`
  - FLUTTER: `{NPD_PLUGIN_DIR}/resources/guides/develop/frontend-integration-flutter.md`
- **TASK**: Prism Mock → 실제 백엔드 API 전환, E2E 동작 확인
- **EXPECTED OUTCOME**: `frontend/public/runtime-env.js`, `frontend/src/services/api/client.ts`, `frontend/src/services/api/authService.ts`, `frontend/src/store/authStore.ts`, `frontend/`(실제 API 연동 완료)

#### Step 2. 백엔드 ↔ AI 서비스 연동 → Agent: backend-developer + ai-engineer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/backend-ai-integration.md`
- **TASK**: 백엔드에서 AI 서비스 호출 코드 구현, Circuit Breaker/Fallback 설정
- **EXPECTED OUTCOME**: `.../client/AiServiceClient.java`(인터페이스), `.../client/AiServiceClientImpl.java`(HTTP 클라이언트), `{service-name}/src/main/resources/application.yml`(resilience4j 섹션), `.../client/AiServiceClientTest.java`(통합 테스트)
- **SKIP 조건**: Phase 1 / Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **Phase 3 / Step 1, Step 2는 병렬 실행 가능** (단, Step 1은 Phase 2 / Step 1 완료 필요, Step 2는 Phase 2 / Step 1 + Step 3 완료 필요)

#### Step 3. API 테스트 → Agent: qa-engineer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/test-api.md`
- **TASK**: 가이드에 따라 백엔드·AI 서비스의 전체 API를 curl로 호출하여 정상 동작을 검증
  1. 빌드 사전 확인 (`./gradlew clean build` 성공)
  2. Controller 레이어에서 API 목록 정리
  3. 샘플 데이터 작성 (seed.sql, JSON fixture)
  4. 백킹서비스 + 백엔드 서비스 기동
  5. 각 API를 curl로 호출하여 응답 확인
  6. 실패 시 원인 분석 → 코드 수정 → 재테스트
- **EXPECTED OUTCOME**:
  - `docs/develop/api-test-result.md` (API 테스트 결과)
  - `{service}/src/test/resources/data/` (SQL seed, JSON fixture)
- **선행 조건**: Phase 3 / Step 1, Step 2 완료 필수

---

### Phase 4: 종합 테스트 및 QA

#### Step 1. 브라우저 테스트

> **선행 조건**: Phase 3 / Step 3 (API 테스트) 전체 PASS 필수

##### Step 1-1. 테스트 모드 적용

Phase 0 / Step 5에서 사전 수집된 테스트 모드를 적용한다.

- **자동 진행 모드** (Phase 0 / Step 6) → 테스트 모드를 **"자동 테스트"**로 강제 설정 (Phase 0 / Step 5 선택과 무관)
- **단계별 승인 모드** (Phase 0 / Step 6) → Phase 0 / Step 5에서 선택한 테스트 모드 적용

결정된 테스트 모드를 `AGENTS.md`의 `### develop > 지원 변수` 섹션에 `TEST_MODE: {AUTO|MANUAL}` 로 기록한다.

##### Step 1-2. 자동 테스트 모드 수행 → Agent: qa-engineer + (수정 시) backend/frontend/ai-engineer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/test-browser-auto.md` ← **필수 로드**
- **수행 조건**: `TEST_MODE = AUTO`인 경우만
- **TASK**: 위 GUIDE의 1-2a~1-2d sub-flow + 체크포인트(`.temp/phase4-step1-checkpoint.json`) + 재테스트 루프(최대 3회) 수행
- **EXPECTED OUTCOME**:
  - `docs/develop/test/e2etest-{N}.md`
  - `e2e/tests/scenarios.spec.ts`
  - `.temp/iter-{N}/tc-*.png` (Step 2 입력)

##### Step 1-3. 수동 테스트 모드 수행 → Agent: backend/frontend/ai-engineer (이슈 수정 시)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/test-browser-manual.md` ← **필수 로드**
- **수행 조건**: `TEST_MODE = MANUAL`인 경우만
- **TASK**: 위 GUIDE의 1-3a~1-3c 대화형 sub-flow 수행. AskUserQuestion 사용 금지
- **EXPECTED OUTCOME**: 사용자 보고 이슈 반영된 코드 + Step 3 (Final Report) 입력용 대화 이력

#### Step 2. 제품 검증

> **선행 조건**: Phase 4 / Step 1 완료

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/product-verify.md` ← **필수 로드**
- **TASK**: 위 GUIDE의 모드별 sub-flow 수행
  - `TEST_MODE = AUTO` → Step 2-1 자동 모드 (5단계: 2-1a~2-1e, 체크포인트 `.temp/phase4-step2-checkpoint.json`, 개선 루프 최대 2회. PO/SP 재검증이 회귀 영향을 통합 검증하므로 별도 회귀 TC 재실행은 수행하지 않음)
  - `TEST_MODE = MANUAL` → Step 2-2 수동 모드 (2-2a~2-2b 대화형, AskUserQuestion 사용 금지)
- **EXPECTED OUTCOME**:
  - 자동: `docs/develop/test/verify-po-{N}.md`, `verify-sp-{N}.md`, `.temp/iter-{N+1}/`
  - 수동: 개선된 코드 + 대화 이력

#### Step 3. Final Report 작성

> **선행 조건**: Phase 4 / Step 2 완료

- **입력**:
  - 자동 모드: `docs/develop/test/e2etest-*.md`, `verify-po-*.md`, `verify-sp-*.md`
  - 수동 모드: Phase 4 / Step 1~2 대화에서 보고된 이슈 + 수정·개선 내역 + 사용자 최종 판정
- **TASK**: 전체 테스트 과정 요약 + 최종 결과 + 잔여 이슈/개선사항 정리
- **EXPECTED OUTCOME**: `docs/develop/test/final-report.md`

---

### Phase 5: 개발 완료

#### Step 1. 개발 완료

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/dev-complete.md` ← **필수 로드**
- **TASK**: 위 GUIDE의 6단계 절차 수행
  1. 서비스 중지 (백엔드/프론트/백킹/AI)
  2. 실행 도구 복사 (`tools/run-backend.py`, `tools/run-frontend.py`)
  3. README.md 생성 (참조: `readme-generation.md`)
  4. 축하 메시지 출력
  5. 실행 가이드 템플릿 출력
  6. 다음 단계 안내 (`/npd:deploy`)
- **EXPECTED OUTCOME**: `tools/run-backend.py`, `tools/run-frontend.py`, `{PROJECT_DIR}/README.md`

---

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |
| 2 | **Phase 1 / Step 1 (AI 개발 키트 컴파일) 이후의 에이전트는 `docs/design/sequence/`, `docs/design/class/*.puml` 등 원본 설계 문서를 직접 읽지 않을 것** (AI 개발 키트만 사용. 원본이 필요한 경우 키트에 누락이 있는 것이므로 Phase 1 / Step 1을 보완) |
| 3 | 외부 가이드(`{NPD_PLUGIN_DIR}/resources/guides/develop/*.md`)가 명시된 Step은 해당 가이드를 **반드시 Read로 로드한 뒤** 절차를 수행할 것. SKILL.md 본문의 요약만 보고 직접 수행하면 스킬 미준수로 간주 |

## 완료 조건

- [ ] Phase 0 / Step 1~6 완료 (개발 범위·크리덴셜·테스트 모드·진행 모드 결정)
- [ ] Phase 1 / Step 1: AI 개발 키트 생성 완료 (`docs/develop/dev-plan.md` 확장 + `test/design-contract/*.spec.ts` 참고 자료)
- [ ] Phase 1 / Step 2~6: 백엔드 환경·백킹서비스·프론트엔드·AI 서비스·실행 프로파일 완료
- [ ] Phase 2 / Step 1~3: 백엔드 API·프론트엔드 Mock·AI 서비스 구현 완료 (해당 시)
- [ ] Phase 3 / Step 1~3: 프론트 실제 API 연동·BE↔AI 연동·API 테스트 전체 PASS
- [ ] Phase 4 / Step 1: 브라우저 테스트 전체 TC PASS (자동 모드 시 e2e/tests/scenarios.spec.ts + Playwright Test Suite, 수동 모드 시 사용자 OK 확인)
- [ ] Phase 4 / Step 2: 제품 검증 PO/SP Critical/Major 이슈 0건 + 회귀 의심 0건 (자동 모드 — PO/SP 재검증 4종 범위 OK)
- [ ] Phase 4 / Step 1·2 루프 제한 준수 (Step 1 재테스트 ≤ 3회, Step 2 개선 ≤ 2회)
- [ ] Phase 4 / Step 3: Final Report 생성 (`docs/develop/test/final-report.md`)
- [ ] Phase 5 / Step 1: `README.md` 생성 완료 (프로젝트 루트)
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (개발 계획서, 백엔드 코드, 프론트엔드 코드, AI 코드, 실행 프로파일)
2. Phase 3 / Step 3 (API 테스트) 전체 PASS (curl 기반 전 엔드포인트 검증)
3. Phase 4 / Step 1 (브라우저 테스트) 전체 PASS (Playwright Test Suite 기반 유저 시나리오 + GAP 패턴 검증)
4. Phase 4 / Step 2 (제품 검증) PO/SP 완료 (Critical/Major 0건 + 회귀 의심 0건 — PO/SP 재검증 4종 범위)
5. Phase 4 / Step 1·2 루프 제한 준수 (Step 1 재테스트 ≤ 3회, Step 2 개선 ≤ 2회)
6. Phase 4 / Step 3 (Final Report) 생성 확인 (`docs/develop/test/final-report.md`)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 인수 라우팅

ARGUMENTS가 전달된 경우, 아래 매핑 테이블에서 키워드를 매칭하여 특정 Step으로 직접 점프한다.
이 로직은 **재개 로직보다 우선** 적용된다.

| 인수 키워드 | 시작 Step | 선행 조건 확인 |
|------------|-----------|---------------|
| `브라우저테스트`, `브라우저 테스트`, `phase4-step1`, `step5` | Phase 4 / Step 1 | `docs/develop/api-test-result.md` 존재 |
| `제품검증`, `제품 검증`, `phase4-step2`, `step6` | Phase 4 / Step 2 | `.temp/phase4-step1-checkpoint.json`의 status가 `completed` |

### 처리 절차

1. ARGUMENTS에서 매핑 테이블의 키워드를 매칭한다 (부분 일치 허용)
2. 매칭 시:
   a. `AGENTS.md`의 `### develop` 섹션에서 변수를 복원한다 (진행 모드, 개발 범위, 지원 변수(TEST_MODE 등), 기술스택)
   b. **테스트 모드 재선택 (Phase 4 / Step 1 점프 시)**: 복원된 `지원 변수 > TEST_MODE`를 표시하고, 이번 실행에서 변경할지 사용자에게 확인한다.

<!--ASK_USER-->
{"title":"테스트 모드 확인","questions":[
  {"question":"현재 설정된 테스트 모드: **{복원된 테스트 모드}**\n\n이번 브라우저 테스트에서 테스트 모드를 변경하시겠습니까?","type":"radio","options":["자동 테스트 유지 (AI가 Playwright Test Suite로 자동 수행)","수동 테스트로 변경 (사람이 브라우저에서 직접 테스트, AI가 수정 지원)"]}
]}
<!--/ASK_USER-->

   - 변경 시 `AGENTS.md`의 `지원 변수 > TEST_MODE` 값을 갱신한다
   - Phase 4 / Step 1-1의 "자동 진행 모드 → 자동 테스트 강제" 규칙은 **인수 라우팅 점프 시에는 적용하지 않는다** (사용자가 명시적으로 Step을 지정했으므로 테스트 모드 선택을 존중)
   c. 해당 Step의 체크포인트 파일(`.temp/phase4-step{N}-checkpoint.json`)이 존재하면 iteration 값을 보존(`status`가 `completed`이면 +1)하고 나머지(`current_step`, `completed_steps`, `status`)를 초기화한다. 미존재 시 `iteration=1`로 새로 생성한다.
   d. 인증 상태 파일(`e2e/.auth/state.json`)을 삭제한다 (Phase 4 / Step 1 점프 시)
   e. 선행 조건 산출물 존재 여부를 확인한다 (미존재 시 사용자에게 경고 후 중단)
   f. **Phase 0을 건너뛰고** 해당 Step부터 실행한다
3. 미매칭 시: 진행상황 업데이트 및 재개 로직을 수행한다
