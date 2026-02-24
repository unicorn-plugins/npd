---
name: develop
description: 개발 단계 AI 협업 — 백엔드·프론트엔드·AI엔지니어·QA가 API 계약 기반 병렬 개발 수행
type: orchestrator
user-invocable: true
allowed-tools: Read, Write, Bash, Task
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

## 선행 조건

- `/npd:design` 완료 (`docs/design/` 산출물 존재)

## 에이전트 호출 규칙

| 에이전트 | FQN |
|----------|-----|
| backend-developer | `npd:backend-developer:backend-developer` |
| frontend-developer | `npd:frontend-developer:frontend-developer` |
| ai-engineer | `npd:ai-engineer:ai-engineer` |
| qa-engineer | `npd:qa-engineer:qa-engineer` |

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
2. 가이드 내에서 참조하는 플러그인 리소스(`{PLUGIN_DIR}/resources/references/...`, `{PLUGIN_DIR}/resources/standards/...` 등)는 `{PLUGIN_DIR}`를 절대 경로로 치환하여 에이전트에게 전달하여 에이전트가 직접 읽을 수 있도록 함

## 공통 참조 리소스

모든 Step에서 아래 표준을 준수:

- **개발주석표준**: `{PLUGIN_DIR}/resources/standards/standard_comment.md`
- **테스트코드표준**: `{PLUGIN_DIR}/resources/standards/standard_testcode.md`
- **패키지구조표준**: `{PLUGIN_DIR}/resources/standards/standard_package_structure.md`
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
| MOCK | SINGLE | `docker-compose.yml` Prism 서비스 수 |

### 플랫폼 판별 키워드 매핑

에이전트는 `docs/design/high-level-architecture.md`의 기술스택 섹션에서 아래 키워드를 탐색하여 `PLATFORM` 값을 결정한다.

| 키워드 in high-level-architecture.md | 판별 결과 |
|--------------------------------------|-----------|
| React, Next.js, Vite+React | `REACT` |
| Vue, Nuxt, Vite+Vue | `VUE` |
| Flutter, Dart, 모바일 앱 | `FLUTTER` |

- 복수 매칭 또는 매칭 없음 시 사용자에게 질문하여 결정
- 결정된 `{PLATFORM}` 값은 이후 모든 가이드에서 조건 분기에 사용

## Step 0. 개발 범위 및 진행 모드 선택

개발 워크플로우 시작 전, **개발 범위**·**진행 모드**·**백킹서비스 환경**을 결정합니다.

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
> - Step 2~5의 각 작업도 선택 범위에 해당하는 기능만 구현
> - 선택하지 않은 Phase의 기능은 모든 Step에서 제외

### 0-2. 진행 모드 선택

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

---

## 워크플로우

### Step 1. 종합 개발 계획 수립 → Agent: backend-developer + frontend-developer + ai-engineer (병렬) + architect (리뷰) (`/oh-my-claudecode:ralplan` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/dev-plan.md`
- **INPUT**: Step 0-1에서 선택된 개발 단계(Phase) 범위
- **TASK**: 설계 산출물 분석 → **선택된 Phase 범위 내** 기능만 추출 → 3개 에이전트가 담당 영역 분담 작성 → architect 리뷰 → 종합 개발 계획서 통합
  - **backend-developer**: 선택 범위 내 마이크로서비스 목록, 서비스 간 의존관계, 백킹서비스 요구사항, 백엔드 개발 순서
  - **frontend-developer**: 선택 범위 내 프론트엔드 범위, 페이지 목록, API 매핑, 프론트엔드 개발 순서
  - **ai-engineer**: 선택 범위 내 AI 서비스 존재 여부·범위, AI 엔드포인트 목록, AI 개발 순서
  - **architect (리뷰)**: 3개 영역 통합, Phase별 작업 할당 최적화, 의존관계 검증, **선택 범위 외 기능 혼입 방지**
- **EXPECTED OUTCOME**: `dev-plan.md`
- **SKIP 조건 결정**: AI 서비스 설계서(`docs/design/ai-service-design.md`) 미존재 또는 "AI 불필요" 결론 시, 이후 AI 관련 Step(2-4, 3-3, 4-2)을 SKIP으로 표시

### Step 2. Phase 1 — 환경 구성

#### Step 2-1. 백엔드 환경 구성 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backend-env-setup.md`
- **TASK**: Gradle Wrapper 생성 + 멀티모듈 build.gradle 구성 + 공통 모듈 개발
- **EXPECTED OUTCOME**: `gradlew`, `settings.gradle`, `build.gradle`(루트/서비스별), `application.yml`(서비스별), common 모듈 코드
- **주의**: application.yml의 환경변수는 placeholder만 작성 (실제 값은 Step 2-2의 .env.example에서 정의)

#### Step 2-2. 백킹서비스 + Mock 서버 로컬 구성 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backing-service-setup.md`
- **TASK**: 데이터설계서 기반 프로젝트 루트 단일 `docker-compose.yml` 작성 → DB/Cache/MQ + Prism Mock 서버 구성
- **EXPECTED OUTCOME**: `docker-compose.yml`, `env.example`, `backing-service-result.md`
- **docker-compose 서비스 구성**:
  - 기본 서비스 (항상 기동): DB, Cache, MQ(설계서 명시 시만)
  - mock 프로파일: Prism Mock 서버 (`docker compose --profile mock up`)
  - ai 프로파일: AI 서비스 컨테이너 (`docker compose --profile ai up`, AI 서비스 존재 시만)
- **사용자 선택**: Step 0에서 선택한 백킹서비스 환경에 따라 분기

#### Step 2-3. 프론트엔드 프로젝트 초기화 → Agent: frontend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/frontend-env-setup.md`
- **TASK**: 기술스택 결정 → 프로젝트 생성 → 기반 시스템(스타일/라우팅/상태관리) 구축 → Prism Mock 서버 연동 준비
- **EXPECTED OUTCOME**: `frontend/` 프로젝트 골격, `npm run dev` 실행 확인

#### Step 2-4. AI 서비스 프로젝트 초기화 → Agent: ai-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/ai-service-env-setup.md`
- **TASK**: Python/FastAPI 프로젝트 생성 → 의존성 설치 → 기본 구조 설정 → docker-compose ai 프로파일에 등록
- **EXPECTED OUTCOME**: `ai-service/` 프로젝트 골격, uvicorn 실행 확인
- **SKIP 조건**: Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **Step 2-1 ~ 2-4는 병렬 실행**: 4개 에이전트가 동시에 작업. Step 2-1과 2-2의 환경변수 정합성은 placeholder 방식으로 해결 (각자 독립 작성, 값은 .env.example에서 통일)

#### Step 2-5. 실행 프로파일 작성 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/run-profile.md`
- **TASK**: 백킹서비스 연결 정보(Step 2-2) + application.yml(Step 2-1) 기반 실행 프로파일 작성
- **EXPECTED OUTCOME**: `{service-name}/.run/{service-name}.run.xml` (서비스별)
- **선행 조건**: Step 2-1, Step 2-2 완료 필수 (Phase 2 진입 전 게이트)

### Step 3. Phase 2 — API 계약 기반 병렬 개발

#### Step 3 사전 확인: 인증 방식 식별 및 OAuth2 크리덴셜 준비

Step 3 진입 전, 오케스트레이터가 직접 인증 방식을 확인하고 필요 시 사용자에게 크리덴셜을 요청한다.
(위임된 에이전트는 사용자에게 질문할 수 없으므로, 이 확인은 반드시 오케스트레이터 레벨에서 수행)

**확인 절차:**

1. `docs/design/high-level-architecture.md`의 `보안 요구사항 > 인증/인가` 항목을 읽는다
2. 인증 방식을 판별한다:
   - `JWT`, `토큰 기반`, `자체 인증` → **JWT 인증** → 추가 작업 없이 Step 3-1 진행
   - `OAuth2`, `소셜 로그인`, `Google`, `카카오`, `네이버`, `OIDC`, `Federated` → **OAuth2 인증** → 아래 크리덴셜 요청 진행
   - `JWT` + `OAuth2/소셜` 모두 언급 → **하이브리드** → 아래 크리덴셜 요청 진행
3. OAuth2/하이브리드인 경우, `.env` 파일에 해당 Provider의 크리덴셜이 이미 설정되어 있는지 확인한다
4. 크리덴셜이 없으면 사용자에게 요청한다:

<!--ASK_USER-->
{"title":"OAuth2 소셜 로그인 크리덴셜 요청","questions":[
  {"question":"설계서에 OAuth2 소셜 로그인({식별된 Provider 목록})이 정의되어 있습니다.\n\n통합 테스트를 위해 각 Provider의 **Client ID**와 **Client Secret**이 필요합니다.\n아직 발급받지 않으셨다면, 아래 가이드를 참조하여 등록해 주세요:\n\n📄 **Provider별 앱 등록 가이드**: `https://github.com/unicorn-plugins/npd/blob/main/resources/references/oauth2-provider-setup-guide.md`\n\n{Provider별 필요 환경변수 목록 표시}\n\n크리덴셜을 입력해 주세요. (아직 미발급이면 '나중에 설정'을 선택하세요)","type":"text"}
]}
<!--/ASK_USER-->

5. 사용자가 크리덴셜을 제공하면 `.env` 파일에 반영한다
6. '나중에 설정'을 선택한 경우:
   - `.env.example`에 해당 환경변수 키를 빈 값으로 추가
   - Step 3-1 에이전트에 "OAuth2 크리덴셜 미설정, 코드 구현만 진행하고 통합 테스트는 생략" 지시를 포함
   - Step 4(통합 연동) 진입 전에 다시 확인

> **참조 문서**: `{PLUGIN_DIR}/resources/references/oauth2-provider-setup-guide.md` — Google, 카카오, 네이버 앱 등록 절차, 필요 환경변수, Redirect URI 패턴

#### Step 3-1. 백엔드 API 구현 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backend-api-dev.md`
- **TASK**: API 설계서 기반 컨트롤러·서비스·레포지토리 구현 + 단위 테스트
- **EXPECTED OUTCOME**: 서비스별 API 코드 + 테스트 코드
- **병렬**: 서비스 간 의존성 분석 후 독립 서비스는 병렬 구현

#### Step 3-2. Prism Mock API 기반 프론트엔드 개발 → Agent: frontend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/frontend-dev.md`
- **TASK**: docker-compose의 Prism Mock 서버 활용 → 페이지별 구현
- **EXPECTED OUTCOME**: 프론트엔드 컴포넌트 + Prism Mock 연동 코드
- **Prism 실행**: `docker compose --profile mock up` (Step 2-2에서 구성)

#### Step 3-3 사전 확인: AI 서비스 크리덴셜 준비

Step 3-3 진입 전, 오케스트레이터가 직접 AI 서비스에 필요한 크리덴셜을 확인하고 필요 시 사용자에게 요청한다.
(위임된 에이전트는 사용자에게 질문할 수 없으므로, 이 확인은 반드시 오케스트레이터 레벨에서 수행)

**SKIP 조건**: Step 1에서 AI SKIP으로 결정된 경우 건너뜀

**확인 절차:**

1. `docs/design/ai-service-design.md`를 읽어 다음을 식별한다:
   - LLM 제공자 및 모델명 (예: OpenAI/gpt-4o, Anthropic/claude-3-5-sonnet 등)
   - 웹검색 Tool 사용 여부 (Tavily 등)
   - RAG 사용 여부 및 벡터 DB 종류 (ChromaDB, Qdrant 등)
   - LangSmith 모니터링 사용 여부
2. `ai-service/.env` 파일에 해당 키가 이미 설정되어 있는지 확인한다
3. 누락된 크리덴셜이 있으면 사용자에게 요청한다:

<!--ASK_USER-->
{"title":"AI 서비스 크리덴셜 요청","questions":[
  {"question":"설계서에 다음 AI 서비스 연동이 정의되어 있습니다:\n\n{식별된 LLM 제공자/모델, Tool, RAG 등 목록}\n\n아래 크리덴셜을 입력해 주세요 (미발급 항목은 비워두면 됩니다):\n\n**필수:**\n- {LLM 제공자} API Key (예: OPENAI_API_KEY)\n\n**선택 (해당 시):**\n- Tavily API Key (웹검색 Tool 사용 시)\n- LangSmith API Key (LLM 호출 모니터링)\n- Vector DB 접속 정보 (RAG 사용 시)\n\n크리덴셜을 입력하거나 '나중에 설정'을 선택하세요.","type":"text"}
]}
<!--/ASK_USER-->

4. 사용자가 크리덴셜을 제공하면 `ai-service/.env` 파일에 반영한다
5. '나중에 설정'을 선택한 경우:
   - `.env.example`에 해당 환경변수 키를 빈 값으로 추가
   - Step 3-3 에이전트에 "LLM 크리덴셜 미설정, 코드 구현만 진행하고 실제 LLM 호출 테스트는 생략" 지시를 포함
   - Step 4(통합 연동) 진입 전에 다시 확인

#### Step 3-3. AI 서비스 구현 → Agent: ai-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/ai-service-dev.md`
- **TASK**: AI 서비스 설계서 기반 엔드포인트 구현, 프롬프트 작성, LLM 연동
- **EXPECTED OUTCOME**: AI 서비스 API 코드
- **SKIP 조건**: Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **Step 3-1 ~ 3-3은 병렬 실행**: 백엔드는 실제 API 구현, 프론트엔드는 Prism Mock으로 독립 개발, AI는 별도 서비스로 독립 개발

#### Step 3-4. 완료 게이트: 통합 전 교차 검증

Step 3-1 ~ 3-3이 모두 완료된 후, Step 4 진입 전에 오케스트레이터가 **전체 서비스 통합 관점**의 검증을 수행한다.
(개별 서비스의 컴파일·테스트·기동 확인은 각 가이드의 품질 기준에서 에이전트가 이미 수행한 상태)

**검증 절차:**

1. **전체 서비스 동시 기동 검증**
   ```bash
   # 백킹서비스 기동
   docker compose up -d
   # 백엔드 전체 서비스 동시 기동 (포트 충돌·의존성 문제 확인)
   python3 tools/run-intellij-service-profile.py --config-dir . --delay 5
   # AI 서비스 기동 (해당 시)
   docker compose --profile ai up -d
   ```
   - 개별 기동은 성공해도 동시 기동 시 포트 충돌, DB 커넥션 풀 고갈, 의존 서비스 미기동 등이 발생할 수 있다
   - 실패 시: 해당 에이전트에게 수정 재지시

2. **서비스 간 연동 포인트 확인**
   - `dev-plan.md`의 서비스 의존성을 읽어, 서비스 간 호출이 있는 API를 식별
   - 호출하는 쪽 서비스에서 `curl`로 해당 API 호출 → 정상 응답 확인
   - 실패 시: 호출하는 쪽 서비스의 연동 설정(URL, 포트)을 점검

3. **미완성 코드 전수 검사**
   ```bash
   grep -rn "TODO\|FIXME\|HACK" --include="*.java" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.vue" --include="*.dart" .
   ```
   - 결과가 0건이어야 통과. 발견 시 해당 에이전트에게 완전 구현 재지시

> **게이트 통과 기준**: 위 3개 항목 모두 PASS해야 Step 3-5 진입. 실패 시 해당 에이전트에게 수정을 재지시하고 게이트를 재수행한다.

#### Step 3-5. Phase 2 완료 독립 검증 → Agent: qa-engineer

Step 3-4(오케스트레이터 게이트) 통과 후, **작업자와 독립된 에이전트**가 실제 빌드·테스트·산출물을 재검증한다.
(작업한 에이전트가 스스로 완료를 선언하는 것을 방지하기 위한 독립 검증)

**검증 절차:**

1. **백엔드 빌드 + 전체 단위 테스트**
   ```bash
   ./gradlew clean build test
   ```
   - 빌드 성공 + 테스트 실패 0건이어야 PASS

2. **프론트엔드 빌드 + 린트**
   ```bash
   cd frontend && npm run build && npm run lint
   ```
   - 빌드 성공 + 린트 에러 0건이어야 PASS

3. **AI 서비스 테스트** (해당 시)
   ```bash
   cd ai-service && pytest
   ```
   - 테스트 실패 0건이어야 PASS

4. **전체 서비스 기동 검증**
   ```bash
   # 백킹서비스 기동
   docker compose up -d
   # 백엔드 전체 서비스 동시 기동
   python3 tools/run-intellij-service-profile.py --config-dir . --delay 5
   # 프론트엔드 기동
   cd frontend && npm run dev &
   # AI 서비스 기동 (해당 시)
   docker compose --profile ai up -d
   ```
   - 각 서비스의 헬스체크 엔드포인트(actuator/health 등) 호출 → 정상 응답 확인
   - 기동 후 에러 로그 0건이어야 PASS
   - 포트 충돌·커넥션 풀 고갈·의존 서비스 미기동 등 동시 기동 시 발생하는 문제 확인

5. **API 명세 vs 실제 구현 대조**
   - `docs/design/api-design.md` (또는 OpenAPI 명세)의 엔드포인트 목록을 추출
   - 각 엔드포인트에 대응하는 Controller 메서드가 실제 코드에 존재하는지 전수 확인
   - 누락 엔드포인트가 있으면 FAIL

6. **TODO/FIXME 전수 검사**
   ```bash
   grep -rn "TODO\|FIXME\|HACK" --include="*.java" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.vue" --include="*.dart" .
   ```
   - 결과 0건이어야 PASS

7. **EXPECTED OUTCOME 산출물 존재 확인**
   - `docs/develop/dev-plan.md`에 명시된 산출물 파일이 모두 존재하는지 확인
   - 누락 파일이 있으면 FAIL

> **게이트 통과 기준**: 위 7개 항목 모두 PASS해야 Step 4 진입. FAIL 항목 발견 시 해당 작업 에이전트(backend-developer/frontend-developer/ai-engineer)에게 수정을 재지시하고, 수정 완료 후 Step 3-5를 처음부터 재수행한다.

### Step 4. Phase 3 — 통합 연동

#### Step 4-1. 프론트엔드 실제 API 연동 → Agent: frontend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/frontend-integration.md`
- **TASK**: Prism Mock → 실제 백엔드 API 전환, E2E 동작 확인
- **EXPECTED OUTCOME**: 실제 API 연동 완료 코드

#### Step 4-2. 백엔드 ↔ AI 서비스 연동 → Agent: backend-developer + ai-engineer

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backend-ai-integration.md`
- **TASK**: 백엔드에서 AI 서비스 호출 코드 구현, Circuit Breaker/Fallback 설정
- **EXPECTED OUTCOME**: 연동 코드 + 통합 테스트
- **SKIP 조건**: Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **Step 4-1, 4-2는 병렬 실행 가능** (단, 4-1은 Step 3-1 완료 필요, 4-2는 Step 3-1 + 3-3 완료 필요)

#### Step 4-3. 통합 테스트 작성 → Agent: qa-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/test-qa.md` (통합 테스트 섹션)
- **INPUT**: API 설계서(`docs/design/api-design.md`), 개발 계획서(`docs/develop/dev-plan.md`), 구현된 백엔드/AI 코드
- **TASK**: 통합 테스트 케이스 설계 → 샘플 데이터 작성 → 통합 테스트 코드 구현 → 테스트 실행 및 버그 수정
  1. **테스트 케이스 설계**: API 설계서의 서비스 간 호출 시나리오를 분석하여 통합 테스트 케이스 문서 작성
  2. **샘플 데이터 작성**: 테스트 전제 조건 데이터(회원·상품·설정 등) SQL seed 스크립트 및 JSON fixture 작성
  3. **통합 테스트 코드 작성**: `@SpringBootTest` + `TestRestTemplate`/`WebTestClient` 기반 서비스 간 API 호출 검증 코드 구현
  4. **테스트 실행**: `./gradlew test --tests '*IntegrationTest'` → 전체 PASS 확인. 실패 시 원인 분석 후 해당 개발 에이전트에게 수정 재지시
- **EXPECTED OUTCOME**:
  - `docs/develop/integration-test-cases.md` (통합 테스트 케이스 문서)
  - `{service}/src/test/resources/data/` (SQL seed, JSON fixture)
  - `{service}/src/test/.../integration/*IntegrationTest.java` (통합 테스트 코드)
- **선행 조건**: Step 4-1, 4-2 완료 필수

#### Step 4-4. Phase 3 완료 독립 검증 → Agent: qa-engineer

Step 4-1, 4-2 완료 후, **작업자와 독립된 에이전트**가 통합 연동의 실제 동작을 검증한다.
(통합이 정상 완료되지 않은 상태에서 테스트 단계로 넘어가는 것을 방지)

**검증 절차:**

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

5. **프론트엔드 → 백엔드 실제 통신 검증**
   - 프론트엔드를 `npm run dev`로 기동
   - 주요 페이지 접속 시 네트워크 요청이 실제 백엔드(Mock이 아닌)로 향하는지 확인
   - API 호출 성공 여부 확인

> **게이트 통과 기준**: 위 5개 항목 모두 PASS해야 Step 5 진입. FAIL 항목 발견 시 해당 작업 에이전트(frontend-developer/backend-developer/ai-engineer)에게 수정을 재지시하고, 수정 완료 후 Step 4-4를 처음부터 재수행한다.

### Step 5. Phase 4 — 테스트 및 QA

#### Step 5-1. E2E 테스트 작성 → Agent: qa-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/test-qa.md` (E2E 테스트 섹션)
- **INPUT**: 유저스토리(`docs/plan/design/userstory.md`), API 설계서, 구현된 프론트엔드/백엔드/AI 코드
- **TASK**: E2E 테스트 케이스 설계 → 샘플 데이터 작성 → E2E 테스트 코드 구현
  1. **E2E 테스트 케이스 설계**: 유저스토리의 Must Have 기능을 사용자 시나리오로 변환하여 E2E 테스트 케이스 문서 작성
  2. **E2E 샘플 데이터 작성**: 시나리오별 초기 데이터셋(DB seed, 테스트용 계정 등) 작성
  3. **E2E 테스트 코드 작성**: Playwright 기반 FE→BE→DB 전체 흐름 자동화 코드 구현
  4. **테스트 실행**: `npx playwright test` → 전체 PASS 확인. 실패 시 원인 분석 후 해당 개발 에이전트에게 수정 재지시
- **EXPECTED OUTCOME**:
  - `docs/develop/e2e-test-cases.md` (E2E 테스트 케이스 문서)
  - `e2e/fixtures/` (시나리오별 초기 데이터셋)
  - `e2e/tests/*.spec.ts` (Playwright E2E 테스트 코드)

#### Step 5-2. 종합 테스트 실행 및 QA → Agent: qa-engineer (`/oh-my-claudecode:ultraqa` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/test-qa.md` (종합 테스트 실행 섹션)
- **INPUT**: Step 4-3의 통합 테스트 코드, Step 5-1의 E2E 테스트 코드
- **TASK**: 전체 테스트 스위트 실행 → 실패 분석 → 버그 수정 지시 → 재테스트 → 테스트 리포트 작성
  1. **전체 테스트 실행**:
     - 단위 테스트: `./gradlew test`
     - 통합 테스트: `./gradlew test --tests '*IntegrationTest'`
     - E2E 테스트: `npx playwright test`
     - AI 서비스 테스트: `cd ai-service && pytest` (해당 시)
  2. **실패 분석 및 버그 수정**: 실패 테스트 분석 → 해당 개발 에이전트에게 버그 수정 재지시 → 수정 후 재테스트
  3. **테스트 리포트 작성**: 전체 테스트 결과를 종합하여 리포트 생성
- **EXPECTED OUTCOME**: `docs/develop/test-report.md`

#### Step 5-3. 최종 완료 검증 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

Step 5-2(종합 QA) 완료 후, **qa-engineer와 독립된 architect**가 최종 완료 여부를 판정한다.
(QA 에이전트가 자기 작업을 자기가 완료 선언하는 것을 방지하고, 설계↔구현 추적성까지 검증)

**검증 절차:**

1. **테스트 리포트 존재 및 품질 확인**
   - `docs/develop/test-report.md` 파일이 존재하는지 확인
   - 리포트 내용에 테스트 실패·에러가 0건인지 확인
   - 테스트 커버리지가 리포트에 명시되어 있는지 확인

2. **완료 조건 전수 체크**
   - 본 SKILL.md 하단 "완료 조건" 항목을 하나씩 순회하며 실제 파일·코드 존재 확인:
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

> **최종 게이트 판정**: 위 5개 항목 모두 PASS해야 Step 6(개발 완료 보고) 진입 허용. FAIL 항목 발견 시 해당 작업 에이전트에게 수정을 재지시하고, 수정 완료 후 Step 5-3을 처음부터 재수행한다. 이 게이트를 통과하지 않으면 개발 완료 보고를 절대 수행하지 않는다.

### Step 6. 개발 완료 보고

```
## 개발 완료

### 구현된 기능
- 백엔드 API: {엔드포인트 수}개 ({서비스 수}개 서비스)
- 프론트엔드 컴포넌트: {컴포넌트 수}개 ({페이지 수}개 페이지)
- AI 기능: {기능 수}개 (해당 시)
- 테스트 통과율: {비율}

### 백킹서비스 설정
- 데이터베이스: {DB 종류 및 수}
- 캐시: {캐시 종류}
- MQ: {MQ 종류} (해당 시)
- Mock 서버: Prism (docker-compose --profile mock)

### 직접 실행 가이드

#### 1. 백킹서비스 기동
​```bash
docker compose up -d
docker compose ps    # 모든 서비스 running 확인
​```

#### 2. 백엔드 서비스 기동
​```bash
python3 tools/run-intellij-service-profile.py --config-dir . --delay 5
# 헬스체크 확인
curl -s http://localhost:{port}/actuator/health
​```

#### 3. 프론트엔드 기동
​```bash
cd frontend && npm run dev
# 브라우저에서 http://localhost:5173 접속
​```

#### 4. AI 서비스 기동 (해당 시)
​```bash
docker compose --profile ai up -d
curl -s http://localhost:8000/health
​```

#### 5. 테스트 실행
​```bash
# 단위 + 통합 테스트
./gradlew clean test

# E2E 테스트
cd e2e && npx playwright test

# AI 서비스 테스트 (해당 시)
cd ai-service && pytest
​```

#### 6. 서비스 중지
​```bash
# 백엔드 중지
pkill -f 'java.*spring'      # Linux/Mac
# Windows: powershell "Get-Process java | Stop-Process -Force"

# 백킹서비스 중지
docker compose down
​```

### 다음 단계
`/npd:deploy` 로 배포를 시작하세요.
```

---

## 완료 조건

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
- [ ] 통합 테스트 케이스 문서(`docs/develop/integration-test-cases.md`)가 생성됨
- [ ] 통합 테스트 코드(`*IntegrationTest.java`) 및 샘플 데이터가 생성됨
- [ ] E2E 테스트 케이스 문서(`docs/develop/e2e-test-cases.md`)가 생성됨
- [ ] E2E 테스트 코드(`e2e/tests/*.spec.ts`) 및 샘플 데이터(`e2e/fixtures/`)가 생성됨
- [ ] 전체 테스트(단위/통합/E2E) 통과율 100%
- [ ] QA 테스트 리포트(`docs/develop/test-report.md`)가 생성됨
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (개발 계획서, 백엔드 코드, 프론트엔드 코드, AI 코드, 실행 프로파일, 테스트 리포트)
2. 산출물 내용 품질 검증 (단위 테스트 통과, API 응답 정상, 빌드 성공)
3. 이전 Phase 산출물과의 일관성 확인 (설계 산출물 → 구현 코드 연계)
4. 설정 일관성 검증 (application.yml 환경변수 ↔ 실행 프로파일 ↔ .env.example ↔ docker-compose.yml)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.
