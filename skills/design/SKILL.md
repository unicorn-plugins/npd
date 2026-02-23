---
name: design
description: 기술 설계 단계 AI 협업 — 아키텍트·AI엔지니어가 협업하여 아키텍처 패턴 선정, 논리/물리/시퀀스/API/클래스/데이터/프론트엔드 설계 및 HighLevel 아키텍처 정의 수행
type: orchestrator
user-invocable: true
allowed-tools: Read, Write, Task, Bash
---

# Design

[NPD Design 활성화]

## 목표

아키텍트·AI엔지니어가 협업하여 클라우드 아키텍처 패턴 선정부터
논리/물리/시퀀스/API/클래스/데이터/프론트엔드 설계 및 HighLevel 아키텍처 정의까지
전체 기술 설계 과정을 수행함.

> **참고**: 서비스 기획(고객 분석, 유저스토리, UI/UX 설계, 프로토타입)은
> `/npd:plan`에서 수행합니다. 본 스킬은 기술 아키텍처 설계에 집중합니다.


## 에이전트 호출 규칙

| 에이전트 | FQN |
|----------|-----|
| architect | `npd:architect:architect` |
| ai-engineer | `npd:ai-engineer:ai-engineer` |
| product-owner | `npd:product-owner:product-owner` |
| backend-developer | `npd:backend-developer:backend-developer` |

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

**예시**: `{PLUGIN_DIR}/resources/guides/design/common-principles.md`
→ `~/.claude/plugins/cache/npd/npd/0.2.0/resources/guides/design/common-principles.md`

### 에이전트에 전달 시

1. 가이드 파일(`{PLUGIN_DIR}/resources/guides/...`)은 Read로 읽어 프롬프트에 포함
2. 가이드 내에서 참조하는 플러그인 리소스(`{PLUGIN_DIR}/resources/references/...`, `{PLUGIN_DIR}/resources/samples/...` 등)는 `{PLUGIN_DIR}`를 절대 경로로 치환하여 에이전트에게 전달하여 에이전트가 직접 읽을 수 있도록 함

## 공통 설계 원칙

모든 Step에서 `{PLUGIN_DIR}/resources/guides/design/common-principles.md`를 준수:

## Step 0. 진행 모드 선택

설계 워크플로우 시작 전, 각 단계별 승인 여부를 선택합니다.

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

## 워크플로우

### Step 1. 아키텍처 패턴 선정 → Agent: architect + ai-engineer (병렬) (`/oh-my-claudecode:ralplan` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/design/architecture-patterns.md` 참조
- **TASK**: 기획 산출물과 기술스택을 기반으로 패턴 후보를 정량 평가하고 MVP→확장→고도화 로드맵을 수립
  - **AI 패턴 병렬 평가**: ai-engineer가 AI 서비스에 필요한 패턴(비동기 통신, Circuit Breaker, Cache-Aside, Rate Limiting 등)의 적합성을 평가하고 AI 관점의 가중치를 제시. architect와 병렬 수행
- **EXPECTED OUTCOME**: `architecture.md` (패턴 평가 매트릭스, Mermaid 다이어그램, Phase별 로드맵)

### Step 1-R. 아키텍처 패턴 리뷰 → Agent: product-owner + backend-developer (병렬)

> **리뷰 수행 조건**: 단계별 승인 모드일 때만 사용자에게 리뷰 수행 여부를 묻고, 사용자가 희망하는 경우에만 리뷰를 수행한다. 자동 진행 모드에서는 리뷰를 건너뛴다.

- **단계별 승인** 모드인 경우 → 아래 질문을 표시:

<!--ASK_USER-->
{"title":"아키텍처 패턴 리뷰","questions":[
  {"question":"아키텍처 패턴 선정 결과(docs/design/pattern-definition.md)에 대해 리뷰를 수행할까요?","type":"radio","options":["리뷰 수행","건너뛰기"]}
]}
<!--/ASK_USER-->

  - **리뷰 수행** → 아래 리뷰 절차를 진행
  - **건너뛰기** → Step 2로 진행

- **자동 진행** 모드인 경우 → 리뷰를 건너뛰고 Step 2로 진행

- **리뷰어 1 — product-owner (피오)**:
  - 관점: 비즈니스 가치 정렬
  - 검토 항목: MVP/스타트업 프로파일 가중치 적절성, Phase별 로드맵과 비즈니스 우선순위(S05→S04→S06) 일치 여부, 비용 효율성 판단의 합리성
  - 입력: `docs/design/pattern-definition.md`, `docs/plan/think/핵심솔루션.md`

- **리뷰어 2 — backend-developer (데브-백)**:
  - 관점: 구현 현실성
  - 검토 항목: 11개 패턴의 실제 구현 난이도, Sprint 0~4 일정의 현실성, 기술 선택(resilience4j, Redis, Spring Scheduler 등)의 팀 역량 부합 여부
  - 입력: `docs/design/pattern-definition.md`, `docs/plan/design/userstory.md`

- **수행 방식**: 두 리뷰어를 **병렬**로 호출하여 리뷰 의견을 수집
- **리뷰 결과 형식**: 각 리뷰어는 아래 형식으로 의견을 제출
  ```
  ## 리뷰 의견 ({리뷰어 닉네임})
  ### 승인/조건부 승인/재작업 요청
  ### 긍정적 평가
  - {항목}
  ### 개선 필요 사항
  - [{심각도: 높음/중간/낮음}] {항목}: {구체적 사유와 대안}
  ### 질문 사항
  - {항목}
  ```
- **반영 절차**:
  1. 두 리뷰어의 의견을 종합하여 사용자에게 보고
  2. 심각도 '높음' 항목이 있으면 → architect 에이전트가 `architecture.md`를 수정 후 재리뷰
  3. 심각도 '중간' 이하만 있으면 → architect 에이전트가 반영 후 다음 단계 진행
  4. 모두 승인이면 → 다음 단계 진행
- **EXPECTED OUTCOME**: 리뷰 반영 완료된 `architecture.md`

### Step 2. 논리 아키텍처 설계 → Agent: architect + ai-engineer (병렬) (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/design/logical-architecture-design.md` 참조
- **TASK**: 선정된 아키텍처 패턴 기반으로 서비스 간 관계·통신 전략·데이터 흐름을 설계하고 Context Map 스타일 Mermaid 다이어그램 작성
  - **AI 서비스 병렬 설계**: ai-engineer가 AI 서비스 식별·경계·통신 방식·폴백 전략을 설계. architect와 병렬 수행 (가이드의 2.2 AI 서비스 아키텍처 설계 참조)
- **EXPECTED OUTCOME**: `logical-architecture.md`, `logical-architecture.mmd`

### Step 3. 시퀀스 설계 → Agent: architect + ai-engineer (내부 시퀀스 병렬) (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/design/sequence-outer-design.md`, `{PLUGIN_DIR}/resources/guides/design/sequence-inner-design.md` 참조
- **TASK**: 핵심 유저스토리의 외부(서비스 간) 및 내부(서비스 내) 시퀀스 다이어그램을 PlantUML로 작성하고 문법 검사 수행
  - **외부 시퀀스 AI 검토**: 설계 완료 후 ai-engineer가 AI Pipeline 서비스 참여자 포함 여부 및 AI 호출 흐름 표현을 검토
  - **내부 시퀀스 AI 병렬 설계**: ai-engineer가 AI Pipeline 서비스(Python/FastAPI)의 내부 시퀀스(Router→PromptBuilder→LLMClient→ResponseParser)를 직접 설계. architect와 병렬 수행
- **EXPECTED OUTCOME**: `sequence/outer/{플로우명}.puml` (플로우별), `sequence/inner/{서비스명}-{시나리오}.puml` (서비스-시나리오별)

### Step 4. API 설계 → Agent: architect + ai-engineer (병렬) (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/design/api-design.md` 참조
- **TASK**: 유저스토리와 시퀀스 설계 기반으로 서비스별 REST API를 OpenAPI 3.0으로 설계하고 swagger-cli 검증 수행
  - **Phase 0 접점 계약**: 병렬 작업 시작 전 architect와 ai-engineer가 서비스 간 API 스키마(요청/응답 JSON, 에러코드)를 합의
  - **AI API 병렬 설계**: ai-engineer가 AI Pipeline 서비스의 API를 직접 설계. architect와 병렬 수행
- **EXPECTED OUTCOME**: `api/{service-name}-api.yaml` (서비스별)

### Step 5. 클래스 설계 → Agent: architect + ai-engineer (병렬) (`/oh-my-claudecode:ralph` 활용)

#### 5-0. 패키지 네이밍 정보 확인

Step 5 시작 시 Java 패키지 네이밍에 필요한 정보를 사용자에게 확인하고 프로젝트 `CLAUDE.md`에 기록합니다.

<!--ASK_USER-->
{"title":"패키지 네이밍 정보","questions":[
  {"question":"Java 패키지명에 사용할 회사/조직명(ORG)을 입력해 주세요.\n예) unicorn → com.unicorn.{ROOT}.{서비스명}","type":"text"},
  {"question":"대표 시스템명(ROOT, Root Project명)을 입력해 주세요.\n예) lifesub → com.{ORG}.lifesub.{서비스명}","type":"text"}
]}
<!--/ASK_USER-->

입력된 값을 프로젝트 루트의 `CLAUDE.md`에 아래 형식으로 기록합니다:

```markdown
## 프로젝트 네이밍
- ORG (회사/조직명): {입력값}
- ROOT (대표 시스템명): {입력값}
- 기본 패키지: com.{ORG}.{ROOT}
```

> 이후 모든 설계·개발 가이드에서 `CLAUDE.md`의 `{ORG}`, `{ROOT}` 값을 참조합니다.

#### 5-0b. 마이크로서비스별 설계 아키텍처 패턴 선택

`docs/design/logical-architecture.md`에서 마이크로서비스 목록을 추출한 뒤, 각 마이크로서비스별로 적용할 설계 아키텍처 패턴을 사용자에게 확인합니다.

1. `docs/design/logical-architecture.md`를 읽어 마이크로서비스 목록을 파악 (AI Pipeline 등 AI 서비스는 제외 — AI 서비스는 Python/FastAPI 고유 아키텍처를 따르므로 Layered/Clean 선택 불필요)
2. 아래 형식으로 마이크로서비스별 패턴을 질문 (AI 서비스를 제외한 서비스 수만큼 반복):

<!--ASK_USER-->
{"title":"설계 아키텍처 패턴 선택","questions":[
  {"question":"{한글명1}({영문명1})에 적용할 설계 아키텍처 패턴을 선택해 주세요.","type":"radio","options":["Layered Architecture","Clean Architecture"]},
  {"question":"{한글명2}({영문명2})에 적용할 설계 아키텍처 패턴을 선택해 주세요.","type":"radio","options":["Layered Architecture","Clean Architecture"]},
  {"question":"{한글명N}({영문명N})에 적용할 설계 아키텍처 패턴을 선택해 주세요.","type":"radio","options":["Layered Architecture","Clean Architecture"]}
]}
<!--/ASK_USER-->

> `{한글명}({영문명})`은 `logical-architecture.md`에서 추출한 실제 마이크로서비스의 한글명과 영문명으로 치환합니다. (예: 여행 서비스(travel-service))

3. 각 서비스별 선택 결과를 `{설계 아키텍처 패턴}` 변수에 **서비스명→패턴** 매핑으로 바인딩
4. 이후 Step 5~Step 6의 에이전트 프롬프트에 서비스별 `{설계 아키텍처 패턴}` 매핑을 전달

#### 5-1. 클래스 설계 수행

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/design/class-design.md` 참조
- **TASK**: **{설계 아키텍처 패턴}** 기반으로 공통 컴포넌트 순차 설계 → 서비스별 병렬 클래스 다이어그램 설계(상세+요약) → 통합 검증 3단계로 수행하고 PlantUML 문법 검사 실행
  - **Phase 0 접점 계약**: 병렬 작업 시작 전 architect와 ai-engineer가 서비스 간 인터페이스를 합의
  - **AI 클래스 병렬 설계**: ai-engineer가 AI Pipeline 서비스(Python/FastAPI)의 클래스를 직접 설계. architect와 병렬 수행
- **EXPECTED OUTCOME**: `class/common-base.puml`, `class/{service-name}.puml`, `class/{service-name}-simple.puml`, `class/package-structure.md`

### Step 6. 데이터 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/design/data-design.md` 참조
- **TASK**: 클래스 설계 기반으로 서비스별 DB 스키마·ERD·Redis 캐시 설계를 병렬 수행하고 PlantUML 문법 검사 실행
  - **AI 검토**: 설계 완료 후 ai-engineer가 AI 응답 캐시(Redis 키 패턴, TTL) 설계를 검토
- **EXPECTED OUTCOME**: `database/{service-name}.md`, `database/{service-name}-erd.puml`, `database/{service-name}-schema.psql`, `database/cache-db-design.md`

### Step 7. HighLevel 아키텍처 정의 → Agent: architect + 멀티 리뷰어 (`/oh-my-claudecode:ralph` 활용)

#### 7-0. Cloud 서비스 선택

Step 7 시작 시 사용자에게 배포 대상 Cloud 서비스를 확인합니다.

<!--ASK_USER-->
{"title":"Cloud 서비스 선택","questions":[
  {"question":"사용할 Cloud 서비스를 선택해 주세요.","type":"radio","options":["AWS","Azure","GCP"]}
]}
<!--/ASK_USER-->

선택된 값을 `{CLOUD}` 변수에 바인딩하고, 이후 Step 7~Step 10의 에이전트 프롬프트에 `{CLOUD}` 값을 전달합니다.

#### 7-1. HighLevel 아키텍처 정의 수행

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/design/architecture-highlevel.md` 참조
- **TASK**: 전체 설계 산출물을 종합하여 Executive Summary부터 ADR까지 HighLevel 아키텍처 정의서 작성. Cloud 환경은 **{CLOUD}** 기준으로 설계
  - **멀티 리뷰**: architect 작성 완료 후 아래 리뷰어가 병렬로 담당 섹션을 검토
    - **backend-developer**: 6장(개발 아키텍처 — 백엔드 기술스택, 아키텍처 패턴, 개발 가이드라인), 8장(기술 스택)
    - **frontend-developer**: 6장(프론트엔드 기술스택, 개발 가이드라인), 8장(기술 스택)
    - **devops-engineer**: 7장(물리 아키텍처), 10장(DevOps — CI/CD, 컨테이너 오케스트레이션)
    - **qa-engineer**: 12장(품질 속성 구현 전략)
    - **ai-engineer**: 9장(AI/ML 아키텍처 — AI 서비스/모델 매핑, 프롬프트 관리 전략, 비용/성능 최적화)
- **EXPECTED OUTCOME**: `high-level-architecture.md` (전체 아키텍처 종합, 각 산출물 참조 경로, ADR)

### Step 8. 물리 아키텍처 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/design/physical-architecture-design.md` 참조
- **TASK**: 개발·운영 환경별 K8s 인프라·네트워크·배포 구조를 Mermaid 다이어그램과 함께 설계하고 문법 검증 수행
  - **AI 검토**: 설계 완료 후 ai-engineer가 AI 서비스 Pod 리소스, GPU/메모리 요구사항, AI 외부 API 네트워크 설정을 검토
- **EXPECTED OUTCOME**: `physical/physical-architecture.md`, `physical/physical-architecture-dev.md`, `physical/physical-architecture-prod.md`, `physical/physical-architecture-dev.mmd`, `physical/physical-architecture-prod.mmd`, `physical/network-dev.mmd`, `physical/network-prod.mmd`

### Step 9. AI 서비스 설계 → Agent: ai-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/design/ai-service-design.md` 참조
- **TASK**: 핵심 솔루션의 AI 활용 기회를 우선순위화하고 LLM API 연동·프롬프트 설계·모델 선정·RAG·Function Calling·MCP·비용 최적화·AI 서비스 아키텍처를 설계
- **EXPECTED OUTCOME**: `ai-service-design.md` (AI 활용 기회 목록, 엔드포인트·프롬프트 설계, 모델 선정 근거, RAG/FC/MCP 설계, 비용·성능 최적화 전략, 아키텍처 다이어그램)

### Step 10. 프론트엔드 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/design/frontend-design.md` 참조
- **TASK**: UI/UX 설계서와 프로토타입 기반으로 UI 프레임워크 선정, 화면별 상세 설계, 스타일가이드, 정보 아키텍처, API 매핑 설계서 작성
- **EXPECTED OUTCOME**: `frontend/uiux-design.md`, `frontend/style-guide.md`, `frontend/ia.md`, `frontend/api-mapping.md`

### Step 11. 설계 완료 보고

```
## 설계 완료

### 생성된 산출물

#### 아키텍처
- architecture.md — 아키텍처 패턴 및 상위수준 설계
- logical-architecture.md — 논리 아키텍처 설계서
- logical-architecture.mmd — 논리 아키텍처 다이어그램
- high-level-architecture.md — HighLevel 아키텍처 정의서

#### 시퀀스
- sequence/outer/{플로우명}.puml — 외부 시퀀스 (플로우별)
- sequence/inner/{서비스명}-{시나리오}.puml — 내부 시퀀스 (서비스-시나리오별)

#### API
- api/{service-name}-api.yaml — 서비스별 OpenAPI 명세

#### 클래스
- class/common-base.puml — 공통 컴포넌트
- class/{service-name}.puml — 서비스별 상세 클래스
- class/{service-name}-simple.puml — 서비스별 요약 클래스
- class/package-structure.md — 패키지 구조도

#### 데이터
- database/{service-name}.md — 서비스별 데이터 설계서
- database/{service-name}-erd.puml — ERD
- database/{service-name}-schema.psql — DB 스키마 스크립트
- database/cache-db-design.md — 캐시 DB 설계서

#### 프론트엔드
- frontend/uiux-design.md — UI/UX 설계서 (기술 관점)
- frontend/style-guide.md — 스타일 가이드
- frontend/ia.md — 정보 아키텍처
- frontend/api-mapping.md — API 매핑 설계서

#### 물리 아키텍처
- physical/physical-architecture.md — 마스터 설계서
- physical/physical-architecture-dev.md — 개발환경 설계서
- physical/physical-architecture-prod.md — 운영환경 설계서
- physical/physical-architecture-dev.mmd — 개발환경 다이어그램
- physical/physical-architecture-prod.mmd — 운영환경 다이어그램
- physical/network-dev.mmd — 개발환경 네트워크
- physical/network-prod.mmd — 운영환경 네트워크

#### AI
- ai-service-design.md — AI 서비스 설계

### 다음 단계
`/npd:develop` 으로 개발을 시작하세요.
```

## 완료 조건

- [ ] 모든 워크플로우 단계(Step 1~1R~11)가 정상 완료됨
- [ ] 산출물이 `docs/design/` 하위 디렉토리에 생성됨
- [ ] 검증 프로토콜을 통과함
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (docs/design/ 하위 전체 파일)
2. PlantUML 문법 검사 통과 확인
3. swagger-cli validate 통과 확인 (API YAML)
4. 이전 Phase 산출물과의 일관성 확인 (기획 → 설계 연계)
5. 설계 산출물 간 상호 일관성 확인 (유저스토리 ID 추적, API-시퀀스-클래스 일치)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.
