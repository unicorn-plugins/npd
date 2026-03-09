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

주의사항: 중간 단계부터 시작할 때도 Step 0은 항상 수행하여 사전 설정 수집 및 진행 모드를 설정해야 합니다.

## AI 개발 키트

설계→개발 경계에서 1회 컴파일되는 개발 입력 세트. Step 1에서 생성되며 이후 모든 Step의 유일한 입력이다.

| 구성 요소 | 경로 | 원본 | 역할 |
|-----------|------|------|------|
| 통합 맥락 | `docs/develop/dev-plan.md` | 전체 설계 산출물 분석 결과 | 전체 그림 + 아키텍처 결정사항 |
| 백엔드 계약 | `docs/design/api/*.yaml` | 이미 존재 (변환 불요) | API 엔드포인트·스키마 정의 |
| DB 계약 | `docs/design/database/*.md` | 이미 존재 (변환 불요) | 테이블·인덱스·관계 정의 |
| 패키지 구조 | `docs/design/class/package-structure.md` | 이미 존재 (변환 불요) | 서비스별 패키지 레이아웃 |
| 프론트엔드 계약 | `docs/plan/.../prototype/*.html+css` | 이미 존재 (변환 불요) | UI 레이아웃·스타일 정의 |
| 행위 계약 | `test/design-contract/*.spec.ts` | 시퀀스 설계서에서 변환 | alt/else 분기 → it() 테스트 케이스 (참고 자료, 실행 불요) |

> **원칙**: **Step 2 이후의 에이전트**는 `docs/design/sequence/`, `docs/design/class/*.puml` 등 원본 설계 문서를 직접 읽지 않는다.
> 필요한 정보는 모두 AI 개발 키트에 포함되어 있다. 원본이 필요한 경우는 키트에 누락이 있는 것이므로 Step 1을 보완한다.
> **단, Step 1(AI 개발 키트 컴파일)은 변환 단계이므로 원본 설계 문서 읽기가 필수이다.** 이 단계에서만 원본을 읽어 키트로 변환한다.

## 선행 조건

- `/npd:design` 완료 (`docs/design/` 산출물 존재)

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

1. `agents/{agent-name}/`에서 3파일 로드 (AGENT.md + agentcard.yaml + tools.yaml)
2. `gateway/runtime-mapping.yaml` 참조하여 구체화:
   - **모델 구체화**: agentcard.yaml의 `tier` → `tier_mapping`에서 모델 결정
   - **툴 구체화**: tools.yaml의 추상 도구 → `tool_mapping`에서 실제 도구 결정
   - **금지액션 구체화**: agentcard.yaml의 `forbidden_actions` → `action_mapping`에서 제외할 실제 도구 결정
   - **최종 도구** = (구체화된 도구) - (제외 도구)
3. 프롬프트 조립: 공통 정적(runtime-mapping) → 에이전트별 정적(3파일) → 인격(persona) → 동적(작업 지시)
4. `Task(subagent_type=FQN, model=구체화된 모델, prompt=조립된 프롬프트)` 호출

## 리소스 경로 규칙

본 스킬의 가이드·참조·샘플·도구 파일은 NPD 플러그인 디렉토리에 위치합니다.
프로젝트 작업 디렉토리와 플러그인 디렉토리가 다르므로, 아래 변수를 사용합니다.

**`{PLUGIN_DIR}`**: NPD 플러그인 루트 디렉토리의 절대 경로

### 경로 해석 규칙

오케스트레이터는 실행 시작 시 다음 순서로 `{PLUGIN_DIR}`를 결정합니다:

1. `~/.claude/plugins/cache/npd/npd/` 하위에서 최신 버전 디렉토리를 탐색
2. 해당 디렉토리의 절대 경로를 `{PLUGIN_DIR}`에 바인딩
3. 이후 모든 `{PLUGIN_DIR}/resources/...` 경로를 절대 경로로 치환하여 파일을 읽음

### 에이전트에 전달 시

1. 가이드 파일(`{PLUGIN_DIR}/resources/guides/develop/...`)은 Read로 읽어 프롬프트에 포함
2. 가이드 내에서 참조하는 플러그인 리소스(`{PLUGIN_DIR}/resources/references/...`, `{PLUGIN_DIR}/resources/references/...` 등)는 `{PLUGIN_DIR}`를 절대 경로로 치환하여 에이전트에게 전달하여 에이전트가 직접 읽을 수 있도록 함

## 공통 참조 리소스

모든 Step에서 아래 표준을 준수:

- **개발주석표준**: `{PLUGIN_DIR}/resources/references/standard_comment.md`
- **테스트코드표준**: `{PLUGIN_DIR}/resources/references/standard_testcode.md`
- **패키지구조표준**: `{PLUGIN_DIR}/resources/references/standard_package_structure.md`
- **병렬 처리 전략**: `{PLUGIN_DIR}/resources/guides/design/common-principles.md`

## 가이드 문서 조건 분기 프로토콜

가이드 문서(.md)에는 프로젝트 컨텍스트에 따라 실행할 섹션을 분기하는 조건 지시문이 포함될 수 있다.
에이전트는 아래 규칙에 따라 해석한다.

### 문법

```
<!-- IF {VARIABLE} == {VALUE} -->
... 이 값일 때만 실행할 내용 ...
<!-- ELIF {VARIABLE} == {OTHER_VALUE} -->
... 다른 값일 때만 실행할 내용 ...
<!-- ENDIF -->
```

### 해석 규칙

1. 에이전트는 가이드 실행 시작 시 변수 값을 결정한다 (예: PLATFORM은 high-level-architecture.md에서 판별)
2. 결정된 변수 값과 일치하는 IF/ELIF 블록의 내용만 실행한다
3. 일치하지 않는 블록은 완전히 건너뛴다 (읽지도 실행하지도 않음)
4. 변수 값이 결정되지 않은 경우 사용자에게 질문하여 결정한다

### 지원 변수

| 변수 | 가능한 값 | 판별 소스 |
|------|-----------|-----------|
| PLATFORM | REACT, VUE, FLUTTER | `docs/design/high-level-architecture.md` 기술스택 섹션 |
| FRONTEND_PORT | 3000 | PLATFORM에서 파생 (React/Vue/Flutter 모두 3000 통일) |
| MOCK | SINGLE | `docker-compose.yml` Prism 서비스 수 |
| TEST_MODE | AUTO, MANUAL | Step 0-2-4에서 사용자 선택 |

### 플랫폼 판별 키워드 매핑

에이전트는 `docs/design/high-level-architecture.md`의 기술스택 섹션에서 아래 키워드를 탐색하여 `PLATFORM` 값을 결정한다.

| 키워드 in high-level-architecture.md | 판별 결과 |
|--------------------------------------|-----------|
| React, Next.js, Vite+React | `REACT` |
| Vue, Nuxt, Vite+Vue | `VUE` |
| Flutter, Dart, 모바일 앱 | `FLUTTER` |

- 복수 매칭 또는 매칭 없음 시 사용자에게 질문하여 결정
- 결정된 `{PLATFORM}` 값은 이후 모든 가이드에서 조건 분기에 사용

## Step 0. 개발 범위·사전 설정·진행 모드 선택

개발 워크플로우 시작 전, **개발 범위**·**사전 설정 수집**·**진행 모드**를 결정합니다.

### 0-1. 개발 범위 결정

`docs/design/high-level-architecture.md`의 **"14. 구현 로드맵 > 14.1 개발 단계"** 섹션을 읽어 프로젝트별 개발 단계를 추출합니다.

1. 해당 섹션의 테이블(단계, 기간, 주요 산출물, 마일스톤)을 파싱
2. 추출된 단계 목록을 사용자에게 표시하고 이번에 구현할 범위를 선택받음

<!--ASK_USER-->
{"title":"개발 범위 선택","questions":[
  {"question":"HighLevel 아키텍처 정의서(14.1 개발 단계)에서 이번에 구현할 단계를 선택해 주세요.\n\n{추출된 Phase 테이블 표시}\n\n(복수 선택 가능)","type":"checkbox","options":["{Phase 1: 주요산출물 — 마일스톤}","{Phase 2: 주요산출물 — 마일스톤}","{Phase N: ...}"]}
]}
<!--/ASK_USER-->

> **범위 결정 효과**: 선택된 Phase의 **주요 산출물·마일스톤**이 이후 모든 Step의 개발 범위가 됩니다.
> - Step 1(종합 개발 계획)은 선택된 Phase 범위 내의 기능만 계획에 포함
> - Step 2~6의 각 작업도 선택 범위에 해당하는 기능만 구현
> - 선택하지 않은 Phase의 기능은 모든 Step에서 제외

### 0-2. 사전 설정 수집

Step 3~7 실행 중 사용자 입력이 필요한 항목을 사전에 수집한다.
진행 모드 선택(0-3) 전에 모든 질문을 완료하여, **"자동 진행" 선택 후 질문 없이 실행**을 보장한다.

#### 0-2-1. OAuth2 크리덴셜 확인 (조건부)

1. `docs/design/high-level-architecture.md`의 `보안 요구사항 > 인증/인가` 항목을 읽는다
2. 인증 방식을 판별한다:
   - `JWT`, `토큰 기반`, `자체 인증` → **JWT 인증** → 이 항목 건너뜀
   - `OAuth2`, `소셜 로그인`, `Google`, `카카오`, `네이버`, `OIDC`, `Federated` → **OAuth2 인증** → 아래 진행
   - `JWT` + `OAuth2/소셜` 모두 언급 → **하이브리드** → 아래 진행
3. OAuth2/하이브리드인 경우, `.env` 파일에 해당 Provider의 크리덴셜이 이미 설정되어 있는지 확인한다
4. 크리덴셜이 없으면 사용자에게 요청한다:

<!--ASK_USER-->
{"title":"OAuth2 소셜 로그인 크리덴셜 요청","questions":[
  {"question":"설계서에 OAuth2 소셜 로그인({식별된 Provider 목록})이 정의되어 있습니다.\n\n통합 테스트를 위해 각 Provider의 **Client ID**와 **Client Secret**이 필요합니다.\n아직 발급받지 않으셨다면, 아래 가이드를 참조하여 등록해 주세요:\n\nProvider별 앱 등록 가이드: {PLUGIN_DIR}/resources/references/oauth2-provider-setup-guide.md\n\n{Provider별 필요 환경변수 목록 표시}\n\n크리덴셜을 입력해 주세요. (아직 미발급이면 '나중에 설정'을 선택하세요)","type":"text"}
]}
<!--/ASK_USER-->

5. 사용자가 크리덴셜을 제공하면 `.env` 파일에 반영한다
6. '나중에 설정'을 선택한 경우: `.env.example`에 해당 환경변수 키를 빈 값으로 추가

> **참조 문서**: `{PLUGIN_DIR}/resources/references/oauth2-provider-setup-guide.md` — Google, 카카오, 네이버 앱 등록 절차, 필요 환경변수, Redirect URI 패턴

#### 0-2-2. Gemini API Key 확인

1. `.env` 파일에 `GEMINI_API_KEY`가 이미 설정되어 있는지 확인한다
2. 설정되어 있지 않으면 사용자에게 요청한다:

<!--ASK_USER-->
{"title":"Gemini API Key 요청 (이미지 생성용)","questions":[
  {"question":"프론트엔드 개발 시 필요한 이미지(아이콘, 일러스트, 배너 등)를 Nano Banana(Gemini) 도구로 생성합니다.\n\nGemini API Key를 입력해 주세요.\n(Google AI Studio에서 발급: https://aistudio.google.com/apikey)\n\n아직 미발급이면 '나중에 설정'을 선택하세요.","type":"text"}
]}
<!--/ASK_USER-->

3. 사용자가 API Key를 제공하면 `.env` 파일에 `GEMINI_API_KEY={입력값}`을 추가한다
4. `.env.example`에 `GEMINI_API_KEY=` 항목을 추가한다 (이미 있으면 생략)

#### 0-2-3. AI 서비스 크리덴셜 확인 (조건부)

1. `docs/design/ai-service-design.md`의 존재 여부를 확인한다
2. 미존재 시 → AI 서비스 없음 → 이 항목 건너뜀
3. 존재 시 다음을 식별한다:
   - LLM 제공자 및 모델명 (예: OpenAI/gpt-4o, Anthropic/claude-3-5-sonnet 등)
   - 웹검색 Tool 사용 여부 (Tavily 등)
   - RAG 사용 여부 및 벡터 DB 종류 (ChromaDB, Qdrant 등)
   - LangSmith 모니터링 사용 여부
4. `.env` 파일에 해당 키가 이미 설정되어 있는지 확인한다
5. 누락된 크리덴셜이 있으면 사용자에게 요청한다:

<!--ASK_USER-->
{"title":"AI 서비스 크리덴셜 요청","questions":[
  {"question":"설계서에 다음 AI 서비스 연동이 정의되어 있습니다:\n\n{식별된 LLM 제공자/모델, Tool, RAG 등 목록}\n\n아래 크리덴셜을 입력해 주세요 (미발급 항목은 비워두면 됩니다):\n\n**필수:**\n- {LLM 제공자} API Key (예: OPENAI_API_KEY)\n\n**선택 (해당 시):**\n- Tavily API Key (웹검색 Tool 사용 시)\n- LangSmith API Key (LLM 호출 모니터링)\n- Vector DB 접속 정보 (RAG 사용 시)\n\n크리덴셜을 입력하거나 '나중에 설정'을 선택하세요.","type":"text"}
]}
<!--/ASK_USER-->

6. 사용자가 크리덴셜을 제공하면 `.env` 파일에 반영한다
7. '나중에 설정'을 선택한 경우: `.env.example`에 해당 환경변수 키를 빈 값으로 추가

#### 0-2-4. 테스트 모드 선택

<!--ASK_USER-->
{"title":"테스트 모드 선택","questions":[
  {"question":"브라우저 테스트(Step 5~7)를 어떻게 진행할까요?","type":"radio","options":["자동 테스트 (AI가 Playwright Test Suite로 자동 수행)","수동 테스트 (사람이 브라우저에서 직접 테스트, AI가 수정 지원)"]}
]}
<!--/ASK_USER-->

### 0-3. 진행 모드 선택

<!--ASK_USER-->
{"title":"진행 모드 선택","questions":[
  {"question":"각 단계 완료 후 승인을 받고 진행할까요, 자동으로 진행할까요?","type":"radio","options":["단계별 승인","자동 진행"]}
]}
<!--/ASK_USER-->

- **단계별 승인** 선택 시 → 각 스텝 완료 후 아래 형식의 승인 요청을 표시하고 사용자 승인 후 다음 스텝 진행:

<!--ASK_USER-->
{"title":"단계 승인","questions":[
  {"question":"{완료된 스텝명} 단계가 완료되었습니다. 결과 파일({생성된 파일 경로})을 검토하고 {다음 스텝명} 단계로 계속 진행할 지 승인해 주십시오.","type":"radio","options":["승인","재작업 요청","중단"]}
]}
<!--/ASK_USER-->

  - **승인** → 다음 스텝 진행
  - **재작업 요청** → 사용자 피드백을 받아 현재 스텝 재수행
  - **중단** → 현재까지 산출물 보존 후 스킬 종료

- **자동 진행** 선택 시 → 승인 없이 연속 실행

### 상태 기록 (`/clear` 대비)

사용자 입력이나 변수 바인딩이 발생하는 Step 완료 시, 프로젝트 루트 `CLAUDE.md`의 `## NPD 워크플로우 상태` 섹션 하위에 `### develop` 서브섹션을 생성(이미 있으면 갱신)합니다:

```
## NPD 워크플로우 상태
### develop
- 진행 모드: {선택값}
- 개발 범위: {선택된 Phase 목록}
- 테스트 모드: {자동/수동}
- 마지막 완료 Step: {Step명}
- 기술스택:
  - Java: {버전}
  - Spring Boot: {버전}
  - 빌드 도구: {Gradle/Maven}
  - Node.js: {버전}
  - 프론트엔드: {React/Vue/Flutter}
  - Python: {버전}
  - AI 프레임워크: {FastAPI}
```

각 Step 완료 시 `마지막 완료 Step` 값을 갱신합니다.
`기술스택`은 Step 1(종합 개발 계획) 수립 시 `dev-plan.md`의 `### 10-5. 기술스택 정보`에서 추출하여 기록합니다.

---

## 워크플로우

### Step 1. AI 개발 키트 컴파일 → Agent: architect (주도) + backend-developer + frontend-developer + ai-engineer (병렬 검증)  (ralplan 모드로 수행)

Step 1은 두 단계로 구성된다:

#### Step 1-1. 종합 개발 계획 수립
- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/dev-plan.md`
- **INPUT**: Step 0-1에서 선택된 개발 단계(Phase) 범위
- **TASK**: 기존과 동일 — 3개 에이전트 분담 작성 → architect 통합 리뷰
- **EXPECTED OUTCOME**: `docs/develop/dev-plan.md`

#### Step 1-2. 행위 계약 테스트 생성 (신규)
- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/design-contract-compile.md`
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
  - `test/design-contract/*.spec.ts` (행위 계약 참고 자료 — 백엔드 구현 시 분기 누락 방지용, 실행 불요) ← 신규 산출물
- **SKIP 조건 결정**: AI 서비스 설계서 미존재 시, AI 관련 test spec 생성 건너뜀

> **이후 모든 Step의 입력**:
> - `docs/develop/dev-plan.md` (통합 맥락)
> - `docs/design/api/*.yaml` (백엔드 계약)
> - `docs/design/database/*-schema.psql` 또는 `docs/design/database/*.md` (DB 계약)
> - `docs/design/class/package-structure.md` (패키지 구조)
> - `docs/plan/.../prototype/*.html+css` (프론트엔드 계약)
> - `test/design-contract/*.spec.ts` (행위 계약 참고 자료)

### Step 2. Phase 1 — 환경 구성

#### Step 2-1. 백엔드 환경 구성 → Agent: backend-developer (ralph 모드로 수행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backend-env-setup.md`
- **TASK**: Gradle Wrapper 생성 + 멀티모듈 build.gradle 구성 + 공통 모듈 개발
- **EXPECTED OUTCOME**: `gradlew`, `gradlew.bat`, `gradle/wrapper/`, `settings.gradle`, `build.gradle`(루트), `{service-name}/build.gradle`(서비스별), `{service-name}/src/main/resources/application.yml`(서비스별), `common/src/main/java/.../common/`
- **주의**: application.yml의 환경변수는 placeholder만 작성 (실제 값은 Step 2-2의 .env.example에서 정의)

#### Step 2-2. 백킹서비스 + Mock 서버 로컬 구성 → Agent: backend-developer (ralph 모드로 수행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backing-service-setup.md`
- **TASK**: 데이터설계서 기반 프로젝트 루트 단일 `docker-compose.yml` 작성 → DB(PostgreSQL/MySQL/MariaDB/MongoDB)/Cache/MQ + Prism Mock 서버 구성. 기본 제품(PostgreSQL) 외 선택 시 카테고리 가이드 참조
- **EXPECTED OUTCOME**: `./docker-compose.yml`, `./.env.example`, `docs/develop/backing-service-result.md`
- **docker-compose 서비스 구성**:
  - 기본 서비스 (항상 기동): DB, Cache, MQ(설계서 명시 시만)
  - mock 프로파일: Prism Mock 서버 (`docker compose --profile mock up`)
  - ai 프로파일: AI 서비스 컨테이너 (`docker compose --profile ai up`, AI 서비스 존재 시만)
- **사용자 선택**: Step 0에서 선택한 백킹서비스 환경에 따라 분기

#### Step 2-3. 프론트엔드 프로젝트 초기화 → Agent: frontend-developer (ralph 모드로 수행)

- **GUIDE** (플랫폼별 선택):
  - REACT: `{PLUGIN_DIR}/resources/guides/develop/frontend-env-setup-react.md`
  - VUE: `{PLUGIN_DIR}/resources/guides/develop/frontend-env-setup-vue.md`
  - FLUTTER: `{PLUGIN_DIR}/resources/guides/develop/frontend-env-setup-flutter.md`
- **TASK**: 기술스택 결정 → 프로젝트 생성 → 기반 시스템(스타일/라우팅/상태관리) 구축 → Prism Mock 서버 연동 준비
- **EXPECTED OUTCOME**: `frontend/` 프로젝트 골격, `tools/generate-runtime-env.sh` (프로젝트 서비스 구성에 맞게 동적 생성됨), `npm run dev` 실행 확인

#### Step 2-4. AI 서비스 프로젝트 초기화 → Agent: ai-engineer (ralph 모드로 수행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/ai-service-env-setup.md`
- **TASK**: Python/FastAPI 프로젝트 생성 → 의존성 설치 → 기본 구조 설정 → docker-compose ai 프로파일에 등록
- **EXPECTED OUTCOME**: `ai-service/` 프로젝트 골격, uvicorn 실행 확인
- **SKIP 조건**: Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **Step 2-1 ~ 2-4는 병렬 실행**: 4개 에이전트가 동시에 작업. Step 2-1과 2-2의 환경변수 정합성은 placeholder 방식으로 해결 (각자 독립 작성, 값은 .env.example에서 통일)

#### Step 2-5. 실행 프로파일 작성 → Agent: backend-developer (ralph 모드로 수행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/run-profile.md`
- **TASK**: 백킹서비스 연결 정보(Step 2-2) + application.yml(Step 2-1) 기반 실행 프로파일 작성
- **EXPECTED OUTCOME**: `{service-name}/.run/{service-name}.run.xml` (서비스별)
- **선행 조건**: Step 2-1, Step 2-2 완료 필수 (Phase 2 진입 전 게이트)

### Step 3. 서비스 단위 병렬 개발

#### Step 3 사전 참조: OAuth2 크리덴셜

> Step 0-2-1에서 OAuth2 크리덴셜을 사전 수집하였다.
> '나중에 설정'을 선택한 경우: Step 3-1 에이전트에 "OAuth2 크리덴셜 미설정, 코드 구현만 진행하고 통합 테스트는 생략" 지시를 포함한다.
> Step 4(통합 연동) 진입 전에 `.env` 파일에서 다시 확인한다.

#### Step 3-1. 백엔드 API 구현 → Agent: backend-developer (ralph 모드로 수행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backend-api-dev.md`
- **INPUT** (변경):
  - `docs/develop/dev-plan.md` (통합 맥락 — 서비스 목록, 의존관계, 개발 순서)
  - `docs/design/api/{service-name}-api.yaml` (API 계약)
  - `docs/design/database/{service-name}.md` (DB 계약)
  - `docs/design/class/package-structure.md` (패키지 구조)
  - `test/design-contract/{service-name}/*.spec.ts` (행위 계약 참고 자료) ← 신규 입력
- **TASK**:
  - API 설계서 + 행위 계약 참고 자료 기반 컨트롤러·서비스·레포지토리 구현 + 단위 테스트
  - **Sprint 분할 제거**: 서비스 1개를 하나의 작업 단위로 완결. 의존관계 기반 순서만 유지
  - **서비스 구현 시**: `test/design-contract/{service-name}/*.spec.ts`의 it() 케이스를 참고하여 alt/else 분기 누락 방지 (테스트 실행 불요)
- **EXPECTED OUTCOME**: `{service-name}/src/main/java/.../{service-name}/`(API 구현 코드), `{service-name}/src/test/java/.../{service-name}/`(단위 테스트 코드)
- **병렬**: 서비스 간 의존성 분석 후 독립 서비스는 병렬 구현 (서브에이전트 활용)

#### Step 3-2 사전 참조: Gemini API Key

> Step 0-2-2에서 Gemini API Key를 사전 수집하였다.
> '나중에 설정'을 선택한 경우: Step 3-2 에이전트에 "Gemini API Key 미설정, 이미지 생성 불가 — 이미지가 필요한 곳은 CSS/SVG 기반 대체 구현" 지시를 포함한다.

#### Step 3-2. Prism Mock API 기반 프론트엔드 개발 → Agent: frontend-developer (ralph 모드로 수행)

- **GUIDE** (플랫폼별 선택):
  - REACT: `{PLUGIN_DIR}/resources/guides/develop/frontend-dev-react.md`
  - VUE: `{PLUGIN_DIR}/resources/guides/develop/frontend-dev-vue.md`
  - FLUTTER: `{PLUGIN_DIR}/resources/guides/develop/frontend-dev-flutter.md`
- **TASK**: docker-compose의 Prism Mock 서버 활용 → 페이지별 구현
- **EXPECTED OUTCOME**: `frontend/src/components/`, `frontend/src/layouts/`, `frontend/src/services/api/`, `frontend/src/hooks/`, `frontend/src/pages/`
- **Prism 실행**: `docker compose --profile mock up` (Step 2-2에서 구성)
- **POST_ACTION**:
  - 프로토타입 화면과 개발 화면 매핑 
  - Playwright MCP로 웹브라우저로 개발된 화면의 첫 화면 오픈
  - 각 개발된 화면을 클릭하여 프로토타입과 비교하여 UI/UX 일치 여부 확인 (개발 화면이 프로토타입과 다를 경우, 프론트엔드 개발자에게 피드백하여 수정 요청) 
  - 모든 개발된 화면이 프로토타입과 일치할 때까지 반복 수행

#### Step 3-3 사전 참조: AI 서비스 크리덴셜

> **SKIP 조건**: Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> Step 0-2-3에서 AI 서비스 크리덴셜을 사전 수집하였다.
> '나중에 설정'을 선택한 경우: Step 3-3 에이전트에 "LLM 크리덴셜 미설정, 코드 구현만 진행하고 실제 LLM 호출 테스트는 생략" 지시를 포함한다.
> Step 4(통합 연동) 진입 전에 `.env` 파일에서 다시 확인한다.

#### Step 3-3. AI 서비스 구현 → Agent: ai-engineer (ralph 모드로 수행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/ai-service-dev.md`
- **TASK**: AI 서비스 설계서 기반 엔드포인트 구현, 프롬프트 작성, LLM 연동
- **EXPECTED OUTCOME**: `{service-name}/models/`, `{service-name}/clients/`, `{service-name}/prompts/`, `{service-name}/services/`, `{service-name}/routers/`, `{service-name}/tests/`
- **SKIP 조건**: Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **Step 3-1 ~ 3-3은 병렬 실행**: 백엔드는 실제 API 구현, 프론트엔드는 Prism Mock으로 독립 개발, AI는 별도 서비스로 독립 개발

### Step 4. Phase 3 — 통합 연동 및 테스트

#### Step 4-1. 프론트엔드 실제 API 연동 → Agent: frontend-developer (ralph 모드로 수행)

- **GUIDE** (플랫폼별 선택):
  - REACT: `{PLUGIN_DIR}/resources/guides/develop/frontend-integration-react.md`
  - VUE: `{PLUGIN_DIR}/resources/guides/develop/frontend-integration-vue.md`
  - FLUTTER: `{PLUGIN_DIR}/resources/guides/develop/frontend-integration-flutter.md`
- **TASK**: Prism Mock → 실제 백엔드 API 전환, E2E 동작 확인
- **EXPECTED OUTCOME**: `frontend/public/runtime-env.js`, `frontend/src/services/api/client.ts`, `frontend/src/services/api/authService.ts`, `frontend/src/store/authStore.ts`, `frontend/`(실제 API 연동 완료)
  
#### Step 4-2. 백엔드 ↔ AI 서비스 연동 → Agent: backend-developer + ai-engineer (ralph 모드로 수행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backend-ai-integration.md`
- **TASK**: 백엔드에서 AI 서비스 호출 코드 구현, Circuit Breaker/Fallback 설정
- **EXPECTED OUTCOME**: `.../client/AiServiceClient.java`(인터페이스), `.../client/AiServiceClientImpl.java`(HTTP 클라이언트), `{service-name}/src/main/resources/application.yml`(resilience4j 섹션), `.../client/AiServiceClientTest.java`(통합 테스트)
- **SKIP 조건**: Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **Step 4-1, 4-2는 병렬 실행 가능** (단, 4-1은 Step 3-1 완료 필요, 4-2는 Step 3-1 + 3-3 완료 필요)

#### Step 4-3. API 테스트 → Agent: qa-engineer (ralph 모드로 수행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/test-api.md`
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
- **선행 조건**: Step 4-1, 4-2 완료 필수

### Step 5. 브라우저 테스트

> **선행 조건**: Step 4-3(API 테스트) 전체 PASS 필수

#### Step 5-0. 테스트 모드 적용

Step 0-2-4에서 사전 수집된 테스트 모드를 적용한다.

- **자동 진행 모드** (Step 0-3) → 테스트 모드를 **"자동 테스트"**로 강제 설정 (Step 0-2-4 선택과 무관)
- **단계별 승인 모드** (Step 0-3) → Step 0-2-4에서 선택한 테스트 모드 적용

결정된 테스트 모드를 `CLAUDE.md`의 `### develop` 섹션에 `테스트 모드: {자동/수동}` 으로 기록한다.

---

#### 자동 테스트 모드 (Step 5)

> 사용자가 **"자동 테스트"**를 선택한 경우 이 섹션을 수행한다.

Playwright Test Suite로 비즈니스 시나리오(TC-01~N) + GAP 공통 시나리오(GAP-01~08)를 자동화 테스트 스크립트로 실행한다.
FAIL TC가 있으면 개발자가 수정 후 재테스트하는 루프를 최대 3회 반복한다.

##### 진행 상태 체크포인트 (중단 복구)

Step 5는 실행 시간이 길어 세션 중단이 발생할 수 있다. 오케스트레이터는 각 sub-step 완료 시 진행 상태를 체크포인트 파일에 기록하고, 재시작 시 완료된 단계를 건너뛴다.

**체크포인트 파일:** `.temp/step5-checkpoint.json`

```json
{
  "current_step": "5-3",
  "iteration": 2,
  "completed_steps": ["5-1", "5-2", "5-3"],
  "status": "in_progress"
}
```

**Step 5 시작 시:**
1. `.temp/step5-checkpoint.json`이 존재하고 `status`가 `"in_progress"`이면 → 중단된 세션 복구
2. `current_step` 위치부터 재개
3. `iteration` 값으로 현재 e2etest-{N}.md 번호 복원
4. 체크포인트가 없으면 → Step 5-1부터 시작

**각 sub-step 완료 시:** `current_step`과 `completed_steps`를 갱신한다.
**Step 5 전체 완료 시:** `status`를 `"completed"`로 변경한다.

##### Step 5-1. Playwright 환경 설정 + 테스트 스크립트 작성 + 실행 → Agent: qa-engineer (ralph 모드로 수행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/test-on-browser.md`
- **TASK**:
  1. Playwright 환경 설정 (최초 1회: `e2e/` 디렉토리 구성, playwright.config.ts 작성)
  2. 서비스 기동:
     - 백킹서비스: `docker compose up -d`
     - 백엔드: `python3 tools/run-intellij-service-profile.py --config-dir . --delay 5`
       (tools/ 미존재 시: `{PLUGIN_DIR}/resources/tools/customs/general/run-intellij-service-profile.py` 사용)
     - 프론트엔드: `python3 tools/run-frontend-devserver.py start --background --force`
       (tools/ 미존재 시: `{PLUGIN_DIR}/resources/tools/customs/general/run-frontend-devserver.py` 사용)
     - AI 서비스 (해당 시): `docker compose --profile ai up -d`
  3. Playwright MCP로 각 페이지의 UI 구조 탐색 (selector 확인용, 페이지 수만큼만)
  4. dev-plan.md의 TC 시나리오 + GAP 시나리오를 `e2e/tests/scenarios.spec.ts`로 작성
  5. `cd e2e && npx playwright test` 실행
  6. `.temp/test-results.json` 기반으로 결과 분석
  7. 전체 페이지 스크린샷을 `.temp/iter-{N}/`에 저장 (PO/SP가 Step 6에서 활용)
- **EXPECTED OUTCOME**: `docs/develop/test/e2etest-{N}.md` (테스트 레포트), `e2e/tests/scenarios.spec.ts` (테스트 스크립트)
- **주의**: 직접 애플리케이션 코드를 수정하지 않음. 테스트 결과 레포트만 작성

##### Step 5-2. 오케스트레이터 판정

- e2etest-{N}.md의 FAIL TC 존재 여부 확인
- **FAIL 없음** → Step 5 완료, Step 6으로 진행
- **FAIL 있음** → Step 5-3으로

##### Step 5-3. 오케스트레이터 → 개발자에게 수정 지시

- e2etest-{N}.md의 이슈를 영향 파일 기준으로 분배:
  - backend-developer: 백엔드 API/로직 관련 버그
  - frontend-developer: 프론트엔드 UI/로직 관련 버그
  - ai-engineer: AI 파이프라인 관련 버그
- **영향 파일이 겹치면 순차 수정** (충돌 방지)
- 개발자들은 ralph 모드로 병렬 수정 실행

##### Step 5-4. QA 재테스트 → Agent: qa-engineer (ralph 모드로 수행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/test-on-browser.md` (섹션 4-2, 7-2, 7-3)
- 프론트엔드 수정이 포함된 FAIL TC는 해당 페이지를 Playwright MCP로 재탐색 → `scenarios.spec.ts` selector 갱신 후 재실행
- qa-engineer가 FAIL TC만 재실행 (`cd e2e && npx playwright test --grep="TC-02|TC-05|..."`)
- 재테스트 시작 전 이전 iter-{N}의 PASS 스크린샷을 iter-{N+1}로 복사 후, FAIL TC만 재실행하여 덮어쓰기 (GUIDE 참조)
- **EXPECTED OUTCOME**: `docs/develop/test/e2etest-{N+1}.md`
- 전체 PASS → Step 5 완료, Step 6 진행 / FAIL 잔존 → Step 5-3 복귀
- **루프 제한: 최대 3회**
  - 3회 후 Critical 잔존 → Step 5 FAIL 처리, 블로커로 에스컬레이션
  - 3회 후 Major/Minor만 잔존 → known issues로 문서화 후 Step 6 진행

##### Step 5 자동 완료 조건

- [ ] 전체 TC PASS (비즈니스 TC + GAP TC) 또는 루프 제한 도달 후 known issues 문서화
- [ ] `e2e/tests/scenarios.spec.ts` 테스트 스크립트 존재
- [ ] `.temp/iter-{N}/` 디렉토리에 전체 TC 스크린샷 존재

---

#### 수동 테스트 모드 (Step 5)

> 사용자가 **"수동 테스트"**를 선택한 경우 이 섹션을 수행한다.
> 사용자가 직접 브라우저에서 테스트하며, AI는 이슈 수정을 담당한다.

##### Step 5-M1. 서비스 기동 + 브라우저 열기

1. 백킹서비스 기동: `docker compose up -d`
2. 백엔드 서비스 기동: `python3 tools/run-intellij-service-profile.py --config-dir . --delay 5`
   (tools/ 미존재 시: `{PLUGIN_DIR}/resources/tools/customs/general/run-intellij-service-profile.py` 사용)
3. 프론트엔드 개발 서버 기동: `python3 tools/run-frontend-devserver.py start --background --force`
   (tools/ 미존재 시: `{PLUGIN_DIR}/resources/tools/customs/general/run-frontend-devserver.py` 사용)
4. AI 서비스 기동 (해당 시): `docker compose --profile ai up -d`
5. `.env`에서 `FRONTEND_PORT` 값을 읽어 Playwright MCP로 브라우저 열기:
   `browser_navigate("http://localhost:{FRONTEND_PORT}")`

##### Step 5-M2. TC 목록 제시 + 사용자 테스트 (대화형)

dev-plan.md의 테스트 시나리오(TC-01~N)를 사용자에게 텍스트로 표시한 뒤, 사용자의 자유 입력을 기다린다.
**AskUserQuestion을 사용하지 않는다.** 아래 안내 메시지를 텍스트로 출력하고 사용자 메시지를 대기한다.

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
- 이슈 설명 또는 액션 요청 → Step 5-M3 진행
- "테스트 완료" → Step 5 완료, Step 6 진행

##### Step 5-M3. 이슈 수정 루프 (대화형)

사용자가 이슈를 보고하면:
1. `browser_snapshot()`으로 현재 화면을 확인하여 이슈를 함께 파악
2. 이슈 내용을 영향 파일 기준으로 분배 (backend-developer / frontend-developer / ai-engineer)
3. 개발자 에이전트가 ralph 모드로 수정
4. 수정 완료 후 아래 안내를 텍스트로 출력하고 사용자 메시지를 대기한다 (**AskUserQuestion 사용 금지**)

```
수정이 완료되었습니다. 브라우저를 새로고침하여 확인해 주세요.
- 다른 이슈가 있으면 해당 화면에서 설명해 주세요.
- AI에게 브라우저 액션을 요청할 수도 있습니다.
- 전체 OK이면 "테스트 완료"라고 입력해 주세요.
- 수정이 안 되었으면 상황을 설명해 주세요.
```

**사용자 응답 처리:**
- 다른 이슈 설명 → Step 5-M3 반복
- "테스트 완료" → Step 5 완료, Step 6 진행
- 재수정 요청 → 추가 정보 기반 재수정 후 안내 반복

##### Step 5 수동 완료 조건

- [ ] 사용자가 전체 TC OK 확인

---

### Step 6. 제품 검증

> **선행 조건**: Step 5 완료

---

#### 자동 테스트 모드 (Step 6)

> 사용자가 **"자동 테스트"**를 선택한 경우 이 섹션을 수행한다.

Step 5에서 생성된 스크린샷과 테스트 결과를 기반으로 PO/SP가 제품을 검증하고, 필요시 개선을 수행한다.

##### 진행 상태 체크포인트 (중단 복구)

**체크포인트 파일:** `.temp/step6-checkpoint.json`

```json
{
  "current_step": "6-3",
  "iteration": 1,
  "phase_transition_count": 0,
  "completed_steps": ["6-1", "6-2", "6-3"],
  "status": "in_progress"
}
```

**Step 6 시작 시:**
1. `.temp/step6-checkpoint.json`이 존재하고 `status`가 `"in_progress"`이면 → 중단된 세션 복구
2. `current_step` 위치부터 재개
3. `phase_transition_count`로 Step 5 복귀 제한 상태 복원
4. 체크포인트가 없으면 → Step 6-1부터 시작

##### Step 6-1. PO, SP 제품 검증 → Agent: product-owner + service-planner (병렬)

- **입력**: QA의 전체 페이지 스크린샷 (.temp/iter-{N}/tc-*.png, N은 Step 5 최종 e2etest 레포트 번호) + 최종 e2etest 레포트
- PO와 SP는 병렬로 제품 검증 실행:
  - **PO** (product-owner): 스크린샷 + Playwright MCP로 사용자 관점 순회
  - **SP** (service-planner): 스크린샷 기반 UI/UX 레이아웃 검수
- **EXPECTED OUTCOME**:
  - `docs/develop/test/verify-po-{N}.md` (PO 제품 검증 레포트)
  - `docs/develop/test/verify-sp-{N}.md` (SP 제품 검증 레포트)
- **주의**: 직접 코드 수정하지 않음. 제품검증 결과 레포트만 작성

##### Step 6-2. 오케스트레이터 판정

- verify-po/sp-{N}.md의 Critical/Major 이슈 존재 여부 확인
- **이슈 없음** → Step 6-4(회귀 테스트)로
- **이슈 있음** → Step 6-3으로

##### Step 6-3. 오케스트레이터 → 개발자에게 개선 지시

- verify-po/sp-{N}.md의 이슈를 영향 파일 기준으로 분배
- 개발자들은 ralph 모드로 병렬 개선 실행
- **영향 파일이 겹치면 순차 수정** (충돌 방지)

##### Step 6-3a. QA 스크린샷 재촬영 → Agent: qa-engineer (ralph 모드로 수행)

- qa-engineer가 개선된 TC/페이지만 `cd e2e && npx playwright test --grep="TC-XX|..."` 로 재실행하여 스크린샷 갱신
- 이전 iter-{N}의 스크린샷을 iter-{N+1}로 복사 후, 개선된 영역만 덮어쓰기 (GUIDE 참조)
- **EXPECTED OUTCOME**: `.temp/iter-{N+1}/` (전체 TC의 최신 스크린샷 완비)

##### Step 6-3b. PO, SP 재검증 → Agent: product-owner + service-planner (병렬)

- **입력**: 갱신된 스크린샷 (.temp/iter-{N+1}/tc-*.png) + 이전 verify-po/sp-{N}.md (이슈 목록 참조용)
- PO와 SP는 이전에 지적한 이슈가 개선되었는지 중심으로 재검증
- **EXPECTED OUTCOME**:
  - `docs/develop/test/verify-po-{N+1}.md`
  - `docs/develop/test/verify-sp-{N+1}.md`
- **주의**: 직접 코드 수정하지 않음. 재검증 결과 레포트만 작성

##### Step 6-3c. 오케스트레이터 판정 (재검증)

- verify-po/sp-{N+1}.md의 Critical/Major 이슈 존재 여부 확인
- **이슈 없음** → Step 6-4(회귀 테스트)로
- **이슈 있음** → Step 6-3으로 복귀 (최대 2회 루프)
- 2회 후 잔여 개선사항 → known improvements로 문서화 후 Step 6-4 진행

##### Step 6-4. QA 회귀 테스트 → Agent: qa-engineer (ralph 모드로 수행)

- qa-engineer가 전체 TC 재실행 (`cd e2e && npx playwright test`, 개선으로 인한 회귀 버그 확인)
- 이전 iter의 스크린샷을 iter-{N+1}로 복사 후, 전체 TC 재실행하여 덮어쓰기 (GUIDE 참조)
- **EXPECTED OUTCOME**: `docs/develop/test/e2etest-{N+1}.md`
- 회귀 버그 없음 → Step 7로
- 회귀 버그 있음 → Step 5 (버그픽스) 루프로 복귀
- **Step 5 복귀 제한: 최대 1회**
  - 1차 복귀 시: Step 5 버그픽스(최대 3회 루프) 후 Step 6을 재실행하지 않고 바로 Step 7로 진행
  - 이 시점에서 잔여 Minor 이슈가 있으면 known issues로 문서화

##### Step 6 자동 완료 조건

- [ ] PO/SP Critical/Major 이슈 0건
- [ ] 회귀 테스트 전체 TC PASS, 신규 버그 0건
- [ ] 개선 루프: 최대 2회

---

#### 수동 테스트 모드 (Step 6)

> 사용자가 **"수동 테스트"**를 선택한 경우 이 섹션을 수행한다.
> 사용자가 직접 제품 품질을 검증하고, AI가 개선을 구현한다.

##### Step 6-M1. 제품 피드백 수집 (대화형)

아래 안내를 텍스트로 출력하고 사용자 메시지를 대기한다 (**AskUserQuestion 사용 금지**).

```
브라우저에서 전체 서비스를 둘러보며 UX/UI 개선점이 있으면 알려주세요.
(디자인, 동선, 레이아웃, 성능 등)

💡 AI가 Playwright MCP로 같은 브라우저를 보고 있습니다.
- 개선이 필요한 화면으로 이동한 뒤 개선점을 설명해 주세요.
- AI에게 직접 브라우저 액션을 요청할 수도 있습니다.
- 개선할 점이 없으면 "검증 완료"라고 입력해 주세요.
```

**사용자 응답 처리:**
- 개선 요청 → Step 6-M2 진행
- "검증 완료" → Step 6 완료, Step 7 진행

##### Step 6-M2. 개선 루프 (대화형)

사용자가 개선을 요청하면:
1. `browser_snapshot()`으로 현재 화면을 확인하여 개선점을 함께 파악
2. 개선 내용을 영향 파일 기준으로 분배 (backend-developer / frontend-developer / ai-engineer)
3. 개발자 에이전트가 ralph 모드로 개선
4. 개선 완료 후 아래 안내를 텍스트로 출력하고 사용자 메시지를 대기한다 (**AskUserQuestion 사용 금지**)

```
개선이 완료되었습니다. 브라우저를 새로고침하여 확인해 주세요.
- 추가 개선이 필요하면 해당 화면에서 설명해 주세요.
- AI에게 브라우저 액션을 요청할 수도 있습니다.
- 만족하시면 "검증 완료"라고 입력해 주세요.
```

**사용자 응답 처리:**
- 추가 개선 요청 → Step 6-M2 반복
- "검증 완료" → Step 6 완료, Step 7 진행

##### Step 6 수동 완료 조건

- [ ] 사용자가 제품 검증 완료 확인

---

### Step 7. Final Report 작성

> **선행 조건**: Step 6 완료

---

#### 자동 테스트 모드 (Step 7)

> 사용자가 **"자동 테스트"**를 선택한 경우 이 섹션을 수행한다.

##### Step 7-1. 오케스트레이터가 Final Report 생성

- **입력**:
  - `docs/develop/test/e2etest-*.md` (전체 QA 레포트)
  - `docs/develop/test/verify-po-*.md` (전체 PO 레포트)
  - `docs/develop/test/verify-sp-*.md` (전체 SP 레포트)
- **TASK**: 전체 테스트 과정 요약 + 최종 결과 + 잔여 이슈/개선사항 정리
- **EXPECTED OUTCOME**: `docs/develop/test/final-report.md`

---

#### 수동 테스트 모드 (Step 7)

> 사용자가 **"수동 테스트"**를 선택한 경우 이 섹션을 수행한다.

##### Step 7-1. 오케스트레이터가 Final Report 생성

- **입력**: Step 5~6 대화에서 보고된 이슈 목록 + 수정/개선 내역 + 사용자 최종 판정
- **TASK**: 테스트 과정 요약 + 최종 결과 + 잔여 이슈/개선사항 정리
- **EXPECTED OUTCOME**: `docs/develop/test/final-report.md`

---

#### Step 7 완료 조건

- [ ] Final Report 생성: `docs/develop/test/final-report.md`

### Step 8. 개발 완료

1. **서비스 중지**: 기동 중인 백엔드·프론트엔드·백킹서비스·AI 서비스를 모두 중지한다
   - 프론트엔드 중지: `python3 tools/run-frontend-devserver.py stop`
2. **실행 도구 복사**: 아래 도구를 프로젝트 루트 `tools/`로 복사한다
   - `{PLUGIN_DIR}/resources/tools/customs/general/run-intellij-service-profile.py` → `tools/run-intellij-service-profile.py`
   - `{PLUGIN_DIR}/resources/tools/customs/general/run-frontend-devserver.py` → `tools/run-frontend-devserver.py`
   - **EXPECTED OUTCOME**: `tools/run-intellij-service-profile.py`, `tools/run-frontend-devserver.py`
3. **README.md 생성**: 오케스트레이터가 직접 가이드에 따라 프로젝트 루트에 `README.md`를 생성한다
   - **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/readme-generation.md`
   - **EXPECTED OUTCOME**: `README.md`
4. **축하 메시지**: 개발이 성공적으로 완료되었다는 감성적 축하 메시지를 사용자에게 전달한다
5. **실행 가이드**: 아래 템플릿을 사용자에게 출력한다 (프론트엔드는 프로젝트에서 사용하는 플랫폼만 표시)

```
### 실행 가이드

#### 1. 백킹서비스 기동
​```bash
docker compose up -d
docker compose ps
​```

#### 2. 백엔드 서비스 기동
​```bash
python3 tools/run-intellij-service-profile.py --config-dir . --delay 5
curl -s http://localhost:{port}/actuator/health
​```

#### 3. 프론트엔드 기동
​```bash
python3 tools/run-frontend-devserver.py start --background --force   # 백그라운드 시작 (포트 점유 시 강제 종료)
python3 tools/run-frontend-devserver.py status                       # 상태 확인
python3 tools/run-frontend-devserver.py stop                         # 중지
​```

#### 4. AI 서비스 기동 (해당 시)
​```bash
docker compose --profile ai up -d
curl -s http://localhost:8000/health
​```

#### 5. 서비스 중지
​```bash
docker compose down
​```
```

6. **다음 단계 안내**: `/npd:deploy` 로 배포를 시작할 수 있음을 안내한다

---

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |

## 완료 조건

- [ ] AI 개발 키트 생성 완료 (`docs/develop/dev-plan.md` 확장 + `test/design-contract/*.spec.ts` 참고 자료)
- [ ] 종합 개발 계획서(`docs/develop/dev-plan.md`)가 생성됨
- [ ] 백엔드 환경 구성 완료 (Gradle Wrapper, build.gradle, common 모듈)
- [ ] 백킹서비스 로컬 구성 완료 (docker-compose.yml, .env.example)
- [ ] 프론트엔드 프로젝트 초기화 완료
- [ ] AI 서비스 프로젝트 초기화 완료 (해당 시)
- [ ] 실행 프로파일 작성 완료
- [ ] 백엔드 API 구현 및 단위 테스트 코드 생성됨
- [ ] 프론트엔드 Prism Mock 기반 구현 완료
- [ ] AI 서비스 구현 완료 (해당 시)
- [ ] 프론트엔드 실제 API 연동 완료
- [ ] 백엔드-AI 연동 완료 (해당 시)
- [ ] API 테스트 전체 PASS (`docs/develop/api-test-result.md` 생성됨)
- [ ] Step 5: 브라우저 버그픽스 테스트 전체 TC PASS (`e2e/tests/scenarios.spec.ts` + Playwright Test Suite)
- [ ] Step 6: 제품 검증 PO/SP Critical/Major 이슈 0건
- [ ] Step 6: 회귀 테스트 전체 TC PASS, 신규 버그 0건
- [ ] Step 5~6: 루프 제한 준수 (Step 5 ≤ 3회, Step 6 개선 ≤ 2회)
- [ ] Step 7: Final Report 생성 (`docs/develop/test/final-report.md`)
- [ ] `README.md` 생성 완료 (프로젝트 루트)
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (개발 계획서, 백엔드 코드, 프론트엔드 코드, AI 코드, 실행 프로파일)
2. API 테스트 전체 PASS (curl 기반 전 엔드포인트 검증)
3. Step 5: 브라우저 버그픽스 전체 PASS (Playwright Test Suite 기반 유저 시나리오 + GAP 패턴 검증)
4. Step 6: 제품 검증 PO/SP 완료 (Critical/Major 0건) + 회귀 테스트 전체 PASS
5. Step 5~6: 루프 제한 준수 (Step 5 ≤ 3회, Step 6 개선 ≤ 2회)
6. Step 7: Final Report 생성 확인 (`docs/develop/test/final-report.md`)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 인수 라우팅

ARGUMENTS가 전달된 경우, 아래 매핑 테이블에서 키워드를 매칭하여 특정 Step으로 직접 점프한다.
이 로직은 **재개 로직보다 우선** 적용된다.

| 인수 키워드 | 시작 Step | 선행 조건 확인 |
|------------|-----------|---------------|
| `브라우저테스트`, `브라우저 테스트`, `step5` | Step 5 | `docs/develop/api-test-result.md` 존재 |
| `제품검증`, `제품 검증`, `step6` | Step 6 | `.temp/step5-checkpoint.json`의 status가 `completed` |

### 처리 절차

1. ARGUMENTS에서 매핑 테이블의 키워드를 매칭한다 (부분 일치 허용)
2. 매칭 시:
   a. `CLAUDE.md`의 `### develop` 섹션에서 변수를 복원한다 (진행 모드, 개발 범위, 테스트 모드, 기술스택)
   b. **테스트 모드 재선택 (Step 5 점프 시)**: 복원된 테스트 모드를 표시하고, 이번 실행에서 변경할지 사용자에게 확인한다.

<!--ASK_USER-->
{"title":"테스트 모드 확인","questions":[
  {"question":"현재 설정된 테스트 모드: **{복원된 테스트 모드}**\n\n이번 브라우저 테스트에서 테스트 모드를 변경하시겠습니까?","type":"radio","options":["자동 테스트 유지 (AI가 Playwright Test Suite로 자동 수행)","수동 테스트로 변경 (사람이 브라우저에서 직접 테스트, AI가 수정 지원)"]}
]}
<!--/ASK_USER-->

   - 변경 시 `CLAUDE.md`의 `테스트 모드` 값을 갱신한다
   - Step 5-0의 "자동 진행 모드 → 자동 테스트 강제" 규칙은 **인수 라우팅 점프 시에는 적용하지 않는다** (사용자가 명시적으로 Step을 지정했으므로 테스트 모드 선택을 존중)
   c. 해당 Step의 체크포인트 파일(`.temp/step{N}-checkpoint.json`)이 존재하면 iteration 값을 보존(`status`가 `completed`이면 +1)하고 나머지(`current_step`, `completed_steps`, `status`)를 초기화한다. 미존재 시 `iteration=1`로 새로 생성한다.
   d. 인증 상태 파일(`e2e/.auth/state.json`)을 삭제한다 (Step 5 점프 시)
   e. 선행 조건 산출물 존재 여부를 확인한다 (미존재 시 사용자에게 경고 후 중단)
   f. **Step 0을 건너뛰고** 해당 Step부터 실행한다
3. 미매칭 시: 아래 재개 로직을 수행한다

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.

1. `CLAUDE.md`의 `## NPD 워크플로우 상태 > ### develop` 섹션에서 변수를 복원:
   - `진행 모드` → 승인/자동 모드 결정
   - `개발 범위` → 선택된 Phase 범위
   - `마지막 완료 Step` → 재개 시작점 결정
2. 상태 섹션이 없으면 **Step 0. 개발 범위 및 진행 모드 선택**부터 시작
