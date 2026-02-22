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

## 선행 조건

- `/npd:plan` 완료 (`docs/plan/` 산출물 존재)
  - 필수: `docs/plan/design/userstory.md` (유저스토리)
  - 필수: `docs/plan/think/es/*.puml` (이벤트 스토밍)
  - 필수: `docs/plan/design/uiux/uiux.md` (UI/UX 설계서)
  - 필수: `docs/plan/design/uiux/style-guide.md` (스타일 가이드)
  - 참조: `docs/plan/think/핵심솔루션.md` (핵심 솔루션)
  - 참조: `docs/plan/define/시장조사.md` (시장 조사)
  - 참조: `docs/plan/design/uiux/prototype/` (프로토타입)

## 에이전트 호출 규칙

| 에이전트 | FQN |
|----------|-----|
| architect | `npd:architect:architect` |
| ai-engineer | `npd:ai-engineer:ai-engineer` |

### 프롬프트 조립

1. `agents/{agent-name}/`에서 3파일 로드 (AGENT.md + agentcard.yaml + tools.yaml)
2. `gateway/runtime-mapping.yaml` 참조하여 구체화:
   - **모델 구체화**: agentcard.yaml의 `tier` → `tier_mapping`에서 모델 결정
   - **툴 구체화**: tools.yaml의 추상 도구 → `tool_mapping`에서 실제 도구 결정
   - **금지액션 구체화**: agentcard.yaml의 `forbidden_actions` → `action_mapping`에서 제외할 실제 도구 결정
   - **최종 도구** = (구체화된 도구) - (제외 도구)
3. 프롬프트 조립: 공통 정적(runtime-mapping) → 에이전트별 정적(3파일) → 인격(persona) → 동적(작업 지시)
4. `Task(subagent_type=FQN, model=구체화된 모델, prompt=조립된 프롬프트)` 호출

## 공통 설계 원칙

모든 Step에서 `resources/guides/design/common-principles.md`를 준수:

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

### Step 1. 아키텍처 패턴 선정 → Agent: architect (`/oh-my-claudecode:ralplan` 활용)

- **GUIDE**: `resources/guides/design/architecture-patterns.md` 참조
- **TASK**: 기획 산출물과 기술스택을 기반으로 패턴 후보를 정량 평가하고 MVP→확장→고도화 로드맵을 수립
- **EXPECTED OUTCOME**: `architecture.md` (패턴 평가 매트릭스, Mermaid 다이어그램, Phase별 로드맵)

### Step 2. 논리 아키텍처 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/design/logical-architecture-design.md` 참조
- **TASK**: 선정된 아키텍처 패턴 기반으로 서비스 간 관계·통신 전략·데이터 흐름을 설계하고 Context Map 스타일 Mermaid 다이어그램 작성
- **EXPECTED OUTCOME**: `logical-architecture.md`, `logical-architecture.mmd`

### Step 3. 시퀀스 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/design/sequence-outer-design.md`, `resources/guides/design/sequence-inner-design.md` 참조
- **TASK**: 핵심 유저스토리의 외부(서비스 간) 및 내부(서비스 내) 시퀀스 다이어그램을 PlantUML로 작성하고 문법 검사 수행
- **EXPECTED OUTCOME**: `sequence/outer/{플로우명}.puml` (플로우별), `sequence/inner/{서비스명}-{시나리오}.puml` (서비스-시나리오별)

### Step 4. API 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/design/api-design.md` 참조
- **TASK**: 유저스토리와 시퀀스 설계 기반으로 서비스별 REST API를 OpenAPI 3.0으로 설계하고 swagger-cli 검증 수행
- **EXPECTED OUTCOME**: `api/{service-name}-api.yaml` (서비스별)

### Step 5. 클래스 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/design/class-design.md` 참조
- **TASK**: 공통 컴포넌트 순차 설계 → 서비스별 병렬 클래스 다이어그램 설계(상세+요약) → 통합 검증 3단계로 수행하고 PlantUML 문법 검사 실행
- **EXPECTED OUTCOME**: `class/common-base.puml`, `class/{service-name}.puml`, `class/{service-name}-simple.puml`, `class/package-structure.md`

### Step 6. 데이터 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/design/data-design.md` 참조
- **TASK**: 클래스 설계 기반으로 서비스별 DB 스키마·ERD·Redis 캐시 설계를 병렬 수행하고 PlantUML 문법 검사 실행
- **EXPECTED OUTCOME**: `database/{service-name}.md`, `database/{service-name}-erd.puml`, `database/{service-name}-schema.psql`, `database/cache-db-design.md`

### Step 7. 프론트엔드 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/design/frontend-design.md` 참조
- **TASK**: UI/UX 설계서와 프로토타입 기반으로 UI 프레임워크 선정, 화면별 상세 설계, 스타일가이드, 정보 아키텍처, API 매핑 설계서 작성
- **EXPECTED OUTCOME**: `frontend/uiux-design.md`, `frontend/style-guide.md`, `frontend/ia.md`, `frontend/api-mapping.md`

### Step 8. 물리 아키텍처 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/design/physical-architecture-design.md` 참조
- **TASK**: 개발·운영 환경별 K8s 인프라·네트워크·배포 구조를 Mermaid 다이어그램과 함께 설계하고 문법 검증 수행
- **EXPECTED OUTCOME**: `physical/physical-architecture.md`, `physical/physical-architecture-dev.md`, `physical/physical-architecture-prod.md`, `physical/physical-architecture-dev.mmd`, `physical/physical-architecture-prod.mmd`, `physical/network-dev.mmd`, `physical/network-prod.mmd`

### Step 9. AI 연동 설계 → Agent: ai-engineer (`/oh-my-claudecode:ralph` 활용)

- **TASK**: 핵심 솔루션의 AI 활용 기회를 우선순위화하고 API 연동·프롬프트·모델 선정·AI 기능 아키텍처를 설계
- **EXPECTED OUTCOME**: `ai-integration.md` (AI 활용 기회 목록, 엔드포인트·프롬프트 설계, 모델 선정 근거, 아키텍처 다이어그램)

### Step 10. HighLevel 아키텍처 정의 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/design/architecture-highlevel.md` 참조
- **TASK**: 전체 설계 산출물을 종합하여 Executive Summary부터 ADR까지 HighLevel 아키텍처 정의서 작성
- **EXPECTED OUTCOME**: `high-level-architecture.md` (전체 아키텍처 종합, 각 산출물 참조 경로, ADR)

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
- ai-integration.md — AI 연동 설계

### 다음 단계
`/npd:develop` 으로 개발을 시작하세요.
```

## 완료 조건

- [ ] 모든 워크플로우 단계(Step 1~11)가 정상 완료됨
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
