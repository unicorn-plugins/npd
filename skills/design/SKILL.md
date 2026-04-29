---
name: design
description: 기술 설계 단계 AI 협업 — 아키텍트·AI엔지니어가 협업하여 아키텍처 패턴 선정, 논리/시퀀스/API/클래스/데이터/AI 서비스 설계 및 HighLevel 아키텍처 정의 수행
type: orchestrator
user-invocable: true
---

# Design

[NPD Design 활성화]

## 목표

아키텍트·AI엔지니어가 협업하여 클라우드 아키텍처 패턴 선정부터
논리/시퀀스/API/클래스/데이터/AI 서비스 설계 및 HighLevel 아키텍처 정의까지
전체 기술 설계 과정을 수행함.

> **참고**: 서비스 기획(고객 분석, 유저스토리, UI/UX 설계, 프로토타입)은
> `/npd:plan`에서 수행합니다. 본 스킬은 기술 아키텍처 설계에 집중합니다.

## 활성화 조건

사용자가 `/npd:design` 호출 시 또는 "설계 시작", "설계해줘", "기술 설계" 키워드 감지 시.

주의사항: 중간 단계부터 시작할 때도 사전 설정 수집 및 진행 모드를 설정하는 Phase 0은 항상 수행해야 합니다.

## 선행 조건

- `/npd:create` 완료 (프로젝트 디렉토리 및 AGENTS.md 존재)
- `/npd:plan` 완료 (기획 산출물 존재)

## 작업 환경 변수 로드

AGENTS.md 파일에서 `## 환경변수` 섹션의 환경변수 로딩.
로딩 실패 시 사용자에게 `/npd:create`를 먼저 수행하라고 안내하고 종료.

## 에이전트 호출 규칙

| 에이전트 | FQN |
|----------|-----|
| architect | `npd:architect:architect` |
| ai-engineer | `npd:ai-engineer:ai-engineer` |
| product-owner | `npd:product-owner:product-owner` |
| backend-developer | `npd:backend-developer:backend-developer` |
| frontend-developer | `npd:frontend-developer:frontend-developer` |
| devops-engineer | `npd:devops-engineer:devops-engineer` |
| qa-engineer | `npd:qa-engineer:qa-engineer` |

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

## 공통 설계 원칙

모든 Step에서 `{NPD_PLUGIN_DIR}/resources/guides/design/common-principles.md`를 준수.

## 진행상황 업데이트 및 재개

`{PROJECT_DIR}/AGENTS.md`에 각 Phase의 Step 완료 시 저장. 최종 완료 시 `Done`으로 표기.

```md
## 워크플로우 진행상황
### design
- 진행 모드: {선택값}
- ORG: {입력값}, ROOT: {입력값} (Phase 0 / Step 1에서 기록)
- CLOUD: {선택값} (Phase 0 / Step 2에서 기록)
- 설계 아키텍처 패턴: {서비스명}→{패턴}, ... (Phase 2 / Step 3-2 완료 후 기록)
- 마지막 완료 Phase/Step: Phase 1/Step 0
```

`{PROJECT_DIR}/AGENTS.md`의 `## 워크플로우 진행상황 > ### design`에 진행상황 정보가 있는 경우 마지막 완료 Step 이후부터 자동 재개. 

## 워크플로우

### 개요

```
Phase 0: 사전 설정·진행 모드 선택 (패키지 네이밍 + Cloud 선택 + 진행 모드)
   ↓
Phase 1: 아키텍처 기반 설계 (패턴 선정 + 패턴 리뷰 + 논리 아키텍처)
   ↓
Phase 2: 상세 설계 (시퀀스 + API + 클래스 + 데이터)
   ↓
Phase 3: 종합 아키텍처 (HighLevel + AI 서비스)
   ↓
Phase 4: 완료 보고
```

### Phase 0: 사전 설정·진행 모드 선택

설계 워크플로우 시작 전, **사전 설정 수집**과 **진행 모드**를 결정합니다.
Phase 1 이후 실행 중 사용자 입력이 필요한 항목을 사전에 수집하여,
**"자동 진행" 선택 후 질문 없이 실행**을 보장합니다.

#### Step 1. 패키지 네이밍 정보 확인

Java 패키지 네이밍에 필요한 정보를 사용자에게 확인하고 프로젝트 `AGENTS.md`에 기록합니다.

<!--ASK_USER-->
{"title":"패키지 네이밍 정보","questions":[
  {"question":"Java 패키지명에 사용할 회사/조직명(ORG)을 입력해 주세요.\n예) unicorn → com.unicorn.{ROOT}.{서비스명}","type":"text"},
  {"question":"대표 시스템명(ROOT, Root Project명)을 입력해 주세요.\n예) lifesub → com.{ORG}.lifesub.{서비스명}","type":"text"}
]}
<!--/ASK_USER-->

입력된 값을 프로젝트 루트의 `AGENTS.md`의 `### design` 진행상황 섹션에 기록.  

> 이후 모든 설계·개발 가이드에서 `AGENTS.md`의 `{ORG}`, `{ROOT}` 값을 참조합니다.

#### Step 2. Cloud 서비스 선택

<!--ASK_USER-->
{"title":"Cloud 서비스 선택","questions":[
  {"question":"사용할 Cloud 서비스를 선택해 주세요.","type":"radio","options":["AWS","Azure","GCP"]}
]}
<!--/ASK_USER-->

선택된 값을 `{CLOUD}` 변수에 바인딩하고, `AGENTS.md`의 `### design` 진행상황 섹션에 기록.

#### Step 3. 진행 모드 선택

<!--ASK_USER-->
{"title":"진행 모드 선택","questions":[
  {"question":"각 단계 완료 후 승인을 받고 진행할까요, 자동으로 진행할까요?","type":"radio","options":["단계별 승인","자동 진행"]}
]}
<!--/ASK_USER-->

- **단계별 승인** 선택 시 → 각 스텝 완료 후 아래 ASK_USER로 승인 요청을 표시하고 응답에 따라 분기:
  - **승인** → 다음 스텝 진행
  - **재작업 요청** → 사용자 피드백을 받아 현재 스텝 재수행
  - **중단** → 현재까지 산출물 보존 후 스킬 종료
- **자동 진행** 선택 시 → 승인 없이 연속 실행

승인 요청 ASK_USER 형식:

<!--ASK_USER-->
{"title":"단계 승인","questions":[
  {"question":"{완료된 스텝명} 단계가 완료되었습니다. 결과 파일({생성된 파일 경로})을 검토하고 {다음 스텝명} 단계로 계속 진행할 지 승인해 주십시오.","type":"radio","options":["승인","재작업 요청","중단"]}
]}
<!--/ASK_USER-->

---

### Phase 1: 아키텍처 기반 설계

#### Step 1. 아키텍처 패턴 선정 → Agent: architect + ai-engineer (병렬)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/design/architecture-patterns.md`
- **TASK**: 기획 산출물과 기술스택을 기반으로 패턴 후보를 정량 평가하고 MVP→확장→고도화 로드맵을 수립
  - **AI 패턴 병렬 평가**: ai-engineer가 AI 서비스에 필요한 패턴(비동기 통신, Circuit Breaker, Cache-Aside, Rate Limiting 등)의 적합성을 평가하고 AI 관점의 가중치를 제시. architect와 병렬 수행
- **EXPECTED OUTCOME**: `docs/design/pattern-definition.md` (패턴 평가 매트릭스, Mermaid 다이어그램, Phase별 로드맵)

#### Step 2. 아키텍처 패턴 리뷰 → Agent: product-owner + backend-developer (병렬)

> **리뷰 수행 조건**: 단계별 승인 모드일 때만 사용자에게 리뷰 수행 여부를 묻고, 사용자가 희망하는 경우에만 리뷰를 수행합니다. 자동 진행 모드에서는 리뷰를 건너뜁니다.

- **단계별 승인** 모드인 경우 → 아래 질문을 표시:

<!--ASK_USER-->
{"title":"아키텍처 패턴 리뷰","questions":[
  {"question":"아키텍처 패턴 선정 결과(docs/design/pattern-definition.md)에 대해 리뷰를 수행할까요?","type":"radio","options":["리뷰 수행","건너뛰기"]}
]}
<!--/ASK_USER-->

- **리뷰 수행** → 아래 리뷰 절차를 진행
- **건너뛰기** → Step 3으로 진행
- **자동 진행** 모드인 경우 → 리뷰를 건너뛰고 Step 3으로 진행

**2a. 리뷰어 1 — product-owner (피오)**

- 관점: 비즈니스 가치 정렬
- 검토 항목: MVP/스타트업 프로파일 가중치 적절성, Phase별 로드맵과 비즈니스 우선순위 일치 여부, 비용 효율성 판단의 합리성
- 입력: `docs/design/pattern-definition.md`, `docs/plan/think/핵심솔루션.md`

**2b. 리뷰어 2 — backend-developer (데브-백)**

- 관점: 구현 현실성
- 검토 항목: 11개 패턴의 실제 구현 난이도, Sprint 0~4 일정의 현실성, 기술 선택(resilience4j, Redis, Spring Scheduler 등)의 팀 역량 부합 여부
- 입력: `docs/design/pattern-definition.md`, `docs/plan/design/userstory.md`

**2c. 수행 방식 및 반영 절차**

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
  2. 심각도 '높음' 항목이 있으면 → architect 에이전트가 `pattern-definition.md`를 수정 후 재리뷰
  3. 심각도 '중간' 이하만 있으면 → architect 에이전트가 반영 후 다음 단계 진행
  4. 모두 승인이면 → 다음 단계 진행
- **EXPECTED OUTCOME**: 리뷰 반영 완료된 `docs/design/pattern-definition.md`

#### Step 3. 논리 아키텍처 설계 → Agent: architect + ai-engineer (병렬)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/design/logical-architecture-design.md`
- **TASK**: 선정된 아키텍처 패턴 기반으로 서비스 간 관계·통신 전략·데이터 흐름을 설계하고 Context Map 스타일 Mermaid 다이어그램 작성
  - **AI 서비스 병렬 설계**: ai-engineer가 AI 서비스 식별·경계·통신 방식·폴백 전략을 설계. architect와 병렬 수행 (가이드의 2.2 AI 서비스 아키텍처 설계 참조)
- **EXPECTED OUTCOME**: `docs/design/logical-architecture.md`, `docs/design/logical-architecture.mmd`

---

### Phase 2: 상세 설계

#### Step 1. 시퀀스 설계 → Agent: architect + ai-engineer (내부 시퀀스 병렬)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/design/sequence-outer-design.md`, `{NPD_PLUGIN_DIR}/resources/guides/design/sequence-inner-design.md`
- **TASK**: 핵심 유저스토리의 외부(서비스 간) 및 내부(서비스 내) 시퀀스 다이어그램을 PlantUML로 작성하고 문법 검사 수행
  - **외부 시퀀스 AI 검토**: 설계 완료 후 ai-engineer가 AI Pipeline 서비스 참여자 포함 여부 및 AI 호출 흐름 표현을 검토
  - **내부 시퀀스 AI 병렬 설계**: ai-engineer가 AI Pipeline 서비스(Python/FastAPI)의 내부 시퀀스(Router→PromptBuilder→LLMClient→ResponseParser)를 직접 설계. architect와 병렬 수행
- **EXPECTED OUTCOME**: `docs/design/sequence/outer/{플로우명}.puml` (플로우별), `docs/design/sequence/inner/{서비스명}-{시나리오}.puml` (서비스-시나리오별)

#### Step 2. API 설계 → Agent: architect + ai-engineer (병렬)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/design/api-design.md`
- **TASK**: 유저스토리와 시퀀스 설계 기반으로 서비스별 REST API를 OpenAPI 3.0으로 설계하고 swagger-cli 검증 수행
  - **Phase 0 접점 계약**: 병렬 작업 시작 전 architect와 ai-engineer가 서비스 간 API 스키마(요청/응답 JSON, 에러코드)를 합의
  - **AI API 병렬 설계**: ai-engineer가 AI Pipeline 서비스의 API를 직접 설계. architect와 병렬 수행
- **EXPECTED OUTCOME**: `docs/design/api/{service-name}-api.yaml` (서비스별)

#### Step 3. 클래스 설계 → Agent: architect + ai-engineer (병렬)

##### Step 3-1. 패키지 네이밍 정보 확인

> Phase 0 / Step 1에서 패키지 네이밍 정보(ORG, ROOT)를 사전 수집하였습니다.
> `AGENTS.md`의 `## 프로젝트 네이밍` 섹션에서 값을 참조합니다.

##### Step 3-2. 마이크로서비스별 설계 아키텍처 패턴 선택

`docs/design/logical-architecture.md`에서 마이크로서비스 목록을 추출한 뒤, 각 마이크로서비스별로 적용할 설계 아키텍처 패턴을 결정합니다.

- **자동 진행 모드** (Phase 0 / Step 3) → architect 에이전트가 서비스 특성을 분석하여 자율 결정:
  - 단순 CRUD 중심 서비스 → Layered Architecture
  - 복잡한 도메인 로직·외부 연동이 많은 서비스 → Clean Architecture
  - 판단 근거를 `docs/design/class/architecture-pattern-rationale.md`에 서비스별로 기록
- **단계별 승인 모드** (Phase 0 / Step 3) → 사용자에게 선택 요청:

**3-2a. 마이크로서비스 목록 파악**

`docs/design/logical-architecture.md`를 읽어 마이크로서비스 목록을 파악 (AI Pipeline 등 AI 서비스는 제외 — AI 서비스는 Python/FastAPI 고유 아키텍처를 따르므로 Layered/Clean 선택 불필요).

**3-2b. 서비스별 패턴 질문**

아래 형식으로 마이크로서비스별 패턴을 질문 (AI 서비스를 제외한 서비스 수만큼 반복):

<!--ASK_USER-->
{"title":"설계 아키텍처 패턴 선택","questions":[
  {"question":"{한글명1}({영문명1})에 적용할 설계 아키텍처 패턴을 선택해 주세요.","type":"radio","options":["Layered Architecture","Clean Architecture"]},
  {"question":"{한글명2}({영문명2})에 적용할 설계 아키텍처 패턴을 선택해 주세요.","type":"radio","options":["Layered Architecture","Clean Architecture"]},
  {"question":"{한글명N}({영문명N})에 적용할 설계 아키텍처 패턴을 선택해 주세요.","type":"radio","options":["Layered Architecture","Clean Architecture"]}
]}
<!--/ASK_USER-->

> `{한글명}({영문명})`은 `logical-architecture.md`에서 추출한 실제 마이크로서비스의 한글명과 영문명으로 치환합니다. (예: 여행 서비스(travel-service))

**3-2c. 변수 바인딩 및 상태 기록**

- 각 서비스별 선택 결과를 `{설계 아키텍처 패턴}` 변수에 **서비스명→패턴** 매핑으로 바인딩
- 이후 Phase 2 / Step 3-3 ~ Phase 2 / Step 4의 에이전트 프롬프트에 서비스별 `{설계 아키텍처 패턴}` 매핑을 전달
- `{설계 아키텍처 패턴}` 매핑을 `AGENTS.md`의 `### design` 진행상황 섹션에 기록

##### Step 3-3. 클래스 설계 수행

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/design/class-design.md`
- **TASK**: **{설계 아키텍처 패턴}** 기반으로 공통 컴포넌트 순차 설계 → 서비스별 병렬 클래스 다이어그램 설계(상세+요약) → 통합 검증 3단계로 수행하고 PlantUML 문법 검사 실행
  - **Phase 0 접점 계약**: 병렬 작업 시작 전 architect와 ai-engineer가 서비스 간 인터페이스를 합의
  - **AI 클래스 병렬 설계**: ai-engineer가 AI Pipeline 서비스(Python/FastAPI)의 클래스를 직접 설계. architect와 병렬 수행
- **EXPECTED OUTCOME**: `docs/design/class/common-base.puml`, `docs/design/class/{service-name}.puml`, `docs/design/class/{service-name}-simple.puml`, `docs/design/class/package-structure.md`

#### Step 4. 데이터 설계 → Agent: architect

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/design/data-design.md`
- **TASK**: 클래스 설계 기반으로 서비스별 DB 스키마·ERD·Redis 캐시 설계를 병렬 수행하고 PlantUML 문법 검사 실행
  - **AI 검토**: 설계 완료 후 ai-engineer가 AI 응답 캐시(Redis 키 패턴, TTL) 설계를 검토
- **EXPECTED OUTCOME**: `docs/design/database/{service-name}.md`, `docs/design/database/{service-name}-erd.puml`, `docs/design/database/{service-name}-schema.md`, `docs/design/database/cache-db-design.md`

---

### Phase 3: 종합 아키텍처

#### Step 1. HighLevel 아키텍처 정의 → Agent: architect + 멀티 리뷰어

##### Step 1-1. Cloud 서비스 확인

> Phase 0 / Step 2에서 Cloud 서비스를 사전 선택하였습니다.
> `AGENTS.md`의 `### design` 진행상황 섹션에서 `{CLOUD}` 값을 참조합니다.

##### Step 1-2. HighLevel 아키텍처 정의 수행

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/design/architecture-highlevel.md`
- **TASK**: 전체 설계 산출물을 종합하여 Executive Summary부터 ADR까지 HighLevel 아키텍처 정의서 작성. Cloud 환경은 **{CLOUD}** 기준으로 설계
  - **멀티 리뷰**: architect 작성 완료 후 아래 리뷰어가 병렬로 담당 섹션을 검토
    - **backend-developer**: 6장(개발 아키텍처 — 백엔드 기술스택, 아키텍처 패턴, 개발 가이드라인), 8장(기술 스택)
    - **frontend-developer**: 6장(프론트엔드 기술스택, 개발 가이드라인), 8장(기술 스택)
    - **devops-engineer**: 7장(물리 아키텍처), 10장(DevOps — CI/CD, 컨테이너 오케스트레이션)
    - **qa-engineer**: 12장(품질 속성 구현 전략)
    - **ai-engineer**: 9장(AI/ML 아키텍처 — AI 서비스/모델 매핑, 프롬프트 관리 전략, 비용/성능 최적화)
- **EXPECTED OUTCOME**: `docs/design/high-level-architecture.md` (전체 아키텍처 종합, 각 산출물 참조 경로, ADR)

#### Step 2. AI 서비스 설계 → Agent: ai-engineer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/design/ai-service-design.md`
- **TASK**: 핵심 솔루션의 AI 활용 기회를 우선순위화하고 LLM API 연동·프롬프트 설계·모델 선정·RAG·Function Calling·MCP·비용 최적화·AI 서비스 아키텍처를 설계
- **EXPECTED OUTCOME**: `docs/design/ai-service-design.md` (AI 활용 기회 목록, 엔드포인트·프롬프트 설계, 모델 선정 근거, RAG/FC/MCP 설계, 비용·성능 최적화 전략, 아키텍처 다이어그램)

---

### Phase 4: 완료 보고

#### Step 1. 설계 완료 보고

```
## 설계 완료

### 생성된 산출물

#### 아키텍처
- docs/design/pattern-definition.md — 아키텍처 패턴 정의서
- docs/design/logical-architecture.md — 논리 아키텍처 설계서
- docs/design/logical-architecture.mmd — 논리 아키텍처 다이어그램
- docs/design/high-level-architecture.md — HighLevel 아키텍처 정의서

#### 시퀀스
- docs/design/sequence/outer/{플로우명}.puml — 외부 시퀀스 (플로우별)
- docs/design/sequence/inner/{서비스명}-{시나리오}.puml — 내부 시퀀스 (서비스-시나리오별)

#### API
- docs/design/api/{service-name}-api.yaml — 서비스별 OpenAPI 명세

#### 클래스
- docs/design/class/common-base.puml — 공통 컴포넌트
- docs/design/class/{service-name}.puml — 서비스별 상세 클래스
- docs/design/class/{service-name}-simple.puml — 서비스별 요약 클래스
- docs/design/class/package-structure.md — 패키지 구조도

#### 데이터
- docs/design/database/{service-name}.md — 서비스별 데이터 설계서
- docs/design/database/{service-name}-erd.puml — ERD
- docs/design/database/{service-name}-schema.md — DB 스키마 스크립트
- docs/design/database/cache-db-design.md — 캐시 DB 설계서

#### AI
- docs/design/ai-service-design.md — AI 서비스 설계

### 다음 단계
`/npd:develop` 으로 개발을 시작하세요.
```

---

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |

## 완료 조건

- [ ] 모든 워크플로우 단계(Phase 0 ~ Phase 4)가 정상 완료됨
- [ ] 산출물이 `docs/design/` 하위 디렉토리에 생성됨
- [ ] 검증 프로토콜을 통과함
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (docs/design/ 하위 전체 파일)
2. PlantUML 문법 검사 통과 확인
3. swagger-cli validate 통과 확인 (API YAML)
4. 이전 워크플로우(`/npd:plan`) 산출물과의 일관성 확인
5. 설계 산출물 간 상호 일관성 확인 (유저스토리 ID 추적, API-시퀀스-클래스 일치)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.
