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
- **실행 우선**: 프롬프트 우선으로 바로 실행, 가이드로 깊이 학습
- **병렬 처리**: 서브 에이전트(Task)로 서비스별 동시 작업, 의존성 기반 그룹화
- **마이크로서비스 원칙**: 서비스 독립성, 캐시 우선, 독립 배포
- **표준화**: PlantUML(`!theme mono`), OpenAPI 3.0, Mermaid 다이어그램
- **검증 우선**: 각 단계마다 자동 검증 (PlantUML 문법 검사, swagger-cli 검증)
- **점진적 구현**: MVP → 확장 → 고도화, YAGNI 원칙

## 워크플로우

### Step 1. 아키텍처 패턴 선정 → Agent: architect (`/oh-my-claudecode:ralplan` 활용)

- **TASK**: 기획 산출물과 기술스택을 기반으로 클라우드 아키텍처 패턴을 선정
  1. 유저스토리에서 기능적/비기능적 요구사항 분석
  2. UI/UX 설계서에서 사용자 인터랙션 패턴, 데이터 플로우 파악
  3. 기술적 도전과제 식별 (복잡한 트랜잭션, 대용량 데이터, 실시간 처리 등)
  4. 패턴 후보별 정량적 평가 (기능 적합성 35%, 성능 효과 25%, 운영 복잡도 20%, 확장성 15%, 비용 효율성 5%)
  5. MVP → 확장 → 고도화 3단계 적용 로드맵 수립
  6. Mermaid 다이어그램으로 서비스 아키텍처 및 패턴 적용 영역 시각화
- **EXPECTED OUTCOME**: `docs/design/architecture.md` 생성
  - 요구사항 분석 결과 (기능적/비기능적)
  - 패턴 선정 매트릭스 (평가표 포함)
  - 서비스별 패턴 적용 설계 (Mermaid 다이어그램)
  - Phase별 구현 로드맵
  - 예상 성과 지표
- **MUST DO**: `resources/guides/design/architecture-patterns.md` 반드시 참조. 정량적 평가 매트릭스 포함. Mermaid 다이어그램으로 시각화
- **MUST NOT DO**: 패턴 선택 근거 없이 결정하지 않을 것. 과도한 엔지니어링 지양
- **CONTEXT**: `docs/plan/design/userstory.md`, `docs/plan/think/es/*.puml`, `docs/plan/think/핵심솔루션.md`, `docs/plan/design/uiux/uiux.md`, CLAUDE.md 기술스택, `resources/guides/design/common-principles.md`

### Step 2. 논리 아키텍처 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **TASK**: 선정된 아키텍처 패턴을 기반으로 논리 아키텍처를 설계
  1. 유저스토리, UI/UX 설계서, 아키텍처 패턴 분석
  2. 논리 아키텍처 설계서 작성 (개요, 서비스별 책임, 서비스 간 통신 전략, 주요 사용자 플로우, 데이터 흐름 및 캐싱 전략, 확장성/보안 고려사항)
  3. 논리 아키텍처 다이어그램 작성 (Mermaid)
     - Context Map 스타일: 서비스 내부 구조 생략, 서비스 간 관계에 집중
     - 클라이언트 → API Gateway 단일 연결선
     - 통신 전략 표현: 실선(동기), 점선(비동기), 양방향(상호 의존)
     - 의존성 레이블에 목적 명시
- **EXPECTED OUTCOME**:
  - `docs/design/logical-architecture.md` — 논리 아키텍처 설계서
  - `docs/design/logical-architecture.mmd` — Mermaid 다이어그램
- **MUST DO**: `resources/guides/design/logical-architecture-design.md` 참조. 유저스토리와 매칭 확인. 불필요한 추가 설계 금지. Mermaid 문법 검증
- **MUST NOT DO**: 물리적 배포 구조를 이 단계에서 결정하지 않을 것
- **CONTEXT**: `docs/design/architecture.md`, `docs/plan/design/userstory.md`, `docs/plan/design/uiux/uiux.md`, `resources/guides/design/common-principles.md`

### Step 3. 시퀀스 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **TASK**: 핵심 유저스토리의 외부·내부 시퀀스 다이어그램 작성
  - **외부 시퀀스** (서비스 간):
    1. 핵심 비즈니스 플로우별 파일 분리 작성
    2. 해당 플로우에 참여하는 프론트엔드, 서비스, 인프라 컴포넌트를 참여자로 추가
    3. 동기(실선)/비동기(점선) 통신 구분
    4. 마이크로서비스 내부 처리 흐름은 표시하지 않음
    5. 서브 에이전트 병렬 작성 (플로우별 독립 에이전트)
  - **내부 시퀀스** (서비스 내부):
    1. 각 서비스-시나리오별로 분리하여 작성
    2. 표현 요소: API 레이어 → 비즈니스 레이어 → 데이터 레이어 → 인프라 레이어
    3. 참여자: Controller, Service, Repository, Cache, External API
    4. 외부 참여자는 이름 끝에 "(E)" 표시
    5. 서브 에이전트 병렬 작성 (서비스별 독립 에이전트)
  - **PlantUML 문법 검사**: 각 파일 생성 즉시 `resources/guides/tools/plantuml-guide.md` 준용 검증
- **EXPECTED OUTCOME**:
  - `docs/design/sequence/outer/{플로우명}.puml` — 외부 시퀀스 (플로우별)
  - `docs/design/sequence/inner/{서비스명}-{시나리오}.puml` — 내부 시퀀스 (서비스-시나리오별)
- **MUST DO**: `resources/guides/design/sequence-outer-design.md`, `sequence-inner-design.md` 참조. MVP Must Have 유저스토리 전체 커버. `!theme mono` 사용. 한국어로 작성. PlantUML 문법 검사 필수
- **MUST NOT DO**: sequence diagram에서 `..>` 사용 금지. 비동기는 `->>` 또는 `-->>` 사용
- **CONTEXT**: `docs/plan/design/userstory.md`, `docs/design/logical-architecture.md`, `docs/plan/design/uiux/uiux.md`, `resources/guides/design/common-principles.md`

### Step 4. API 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **TASK**: REST API 엔드포인트를 서비스별 독립 파일로 설계
  1. 유저스토리와 매칭되는 API만 선정 (x-user-story 확장 필드에 유저스토리 ID 명시)
  2. 외부/내부 시퀀스 설계서와 일관성 있게 선정
  3. OpenAPI 3.0 스펙 준용, YAML 형식
  4. 각 API별 필수 항목: summary, operationId, x-user-story, x-controller, tags, requestBody/responses
  5. servers 섹션 필수 (SwaggerHub Mock URL 포함)
  6. example 데이터 추가
  7. 테스트 시나리오 포함 (성공/실패 케이스)
  8. 서브 에이전트 병렬 작성 (독립 서비스는 병렬, 의존 서비스는 순차)
  9. `swagger-cli validate` 검증 수행
- **EXPECTED OUTCOME**:
  - `docs/design/api/{service-name}-api.yaml` — 서비스별 OpenAPI 명세
- **MUST DO**: `resources/guides/design/api-design.md` 참조. OpenAPI 3.0 준수. 서비스별 독립 파일. swagger-cli 검증 필수. 파일명은 kebab-case
- **MUST NOT DO**: 구현 코드를 이 단계에서 작성하지 않을 것. 유저스토리에 없는 API 추가 금지
- **CONTEXT**: `docs/plan/design/userstory.md`, `docs/design/sequence/`, `resources/guides/design/common-principles.md`

### Step 5. 클래스 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **TASK**: 도메인 클래스 다이어그램을 서비스별로 설계
  - **1단계 - 공통 컴포넌트 설계** (순차):
    - 공통 인터페이스, 기본 클래스 정의
    - 결과: `docs/design/class/common-base.puml`
  - **2단계 - 서비스별 병렬 설계** (병렬):
    - 1단계 공통 컴포넌트 참조 (`!include` 사용 금지, 필요한 인터페이스 직접 정의)
    - API 설계서와 일관성 있게 설계 (Controller 클래스 메소드 = API 엔드포인트)
    - 각 서비스별 지정된 설계 아키텍처 패턴 적용 (Clean Architecture 등)
    - 클래스의 프로퍼티와 메소드 모두 기술 (Getter/Setter 제외)
    - 클래스 간 관계 표현: Generalization, Realization, Dependency, Association, Aggregation, Composition
    - 상세 버전 + 요약 버전(프로퍼티/메소드 생략) 동시 작성
    - 요약 버전에 Controller 메소드-API 매핑표를 Note로 작성
    - 결과: `docs/design/class/{service-name}.puml`, `docs/design/class/{service-name}-simple.puml`
  - **3단계 - 통합 및 검증** (순차):
    - 패키지 구조도 작성 (트리구조 텍스트)
    - 인터페이스 일치성, 명명 규칙, 의존성, 크로스 서비스 참조 검증
    - PlantUML 문법 검사 실행
    - 결과: `docs/design/class/package-structure.md`
- **EXPECTED OUTCOME**:
  - `docs/design/class/common-base.puml` — 공통 컴포넌트
  - `docs/design/class/{service-name}.puml` — 서비스별 상세 클래스
  - `docs/design/class/{service-name}-simple.puml` — 서비스별 요약 클래스
  - `docs/design/class/package-structure.md` — 패키지 구조도
- **MUST DO**: `resources/guides/design/class-design.md` 참조. `!theme mono` 사용. API 설계서/내부 시퀀스와 일관성 확인. PlantUML 문법 검사 필수
- **MUST NOT DO**: ORM 설정 코드를 이 단계에서 작성하지 않을 것
- **CONTEXT**: `docs/design/api/`, `docs/design/sequence/inner/`, `docs/plan/think/es/*.puml`, `resources/guides/design/common-principles.md`

### Step 6. 데이터 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **TASK**: 클래스 설계 기반으로 데이터베이스 스키마와 캐시 설계 수행
  - 서비스별 병렬 수행 (서브 에이전트)
  - **서비스별 데이터 설계서**: 데이터 설계 요약, 테이블 정의, 캐시 설계 (캐시 대상, 키 패턴, TTL 정책)
  - **ERD**: PlantUML로 작성, 문법 검사 즉시 실행
  - **DB 스키마 스크립트**: 실행 가능한 SQL 스크립트 (.psql)
  - **캐시 DB 설계서**: Redis database 번호별 할당표
    - DB 0: 공통 영역 (세션, 인증 토큰)
    - DB 1~14: 서비스별 전용 캐시
    - DB 15: 예비 영역
    - Key Naming: `{domain}:{entity}:{id}` 형식
  - 데이터 독립성 원칙: 서비스별 DB 분리, 크로스 서비스 조인 금지, 캐시를 통한 타 서비스 데이터 참조
- **EXPECTED OUTCOME**:
  - `docs/design/database/{service-name}.md` — 서비스별 데이터 설계서
  - `docs/design/database/{service-name}-erd.puml` — ERD
  - `docs/design/database/{service-name}-schema.psql` — DB 스키마 스크립트
  - `docs/design/database/cache-db-design.md` — 캐시 DB 설계서
- **MUST DO**: `resources/guides/design/data-design.md` 참조. 클래스 설계서 Entity와 일치. 서비스별 독립 DB. PlantUML 문법 검사 필수
- **MUST NOT DO**: 서비스 간 FK 관계 설정 금지. 유저스토리에 없는 테이블 추가 금지
- **CONTEXT**: `docs/design/class/`, `resources/guides/design/common-principles.md`

### Step 7. 프론트엔드 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **TASK**: UI/UX 설계서와 프로토타입을 기반으로 프론트엔드 기술 설계 수행
  - **준비**: 프로토타입 분석, API 명세서 분석, 화면 요구사항 분석
  - **설계**:
    1. UI/UX 설계서 상세화: UI 프레임워크 선택 (MUI, Ant Design 등), 화면목록, 사용자 플로우, 화면별 상세 설계 (상세기능, UI 구성요소, 인터랙션), 반응형/접근성/성능 전략
    2. 스타일가이드 작성: 브랜드 아이덴티티, 컬러 시스템, 타이포그래피, 간격 시스템, 컴포넌트 스타일, 반응형 브레이크포인트
    3. 정보 아키텍처 설계: 사이트맵, 프로젝트 구조 (패키지와 파일까지 설계)
    4. API 매핑 설계서: API 경로 매핑 (runtime-env.js), API와 화면 상세기능 매칭
- **EXPECTED OUTCOME**:
  - `docs/design/frontend/uiux-design.md` — UI/UX 설계서 (기술 설계 관점)
  - `docs/design/frontend/style-guide.md` — 스타일 가이드
  - `docs/design/frontend/ia.md` — 정보 아키텍처
  - `docs/design/frontend/api-mapping.md` — API 매핑 설계서
- **MUST DO**: `resources/guides/design/frontend-design.md` 참조. 프로토타입과 동일하게 설계. 백엔드 API 명세서와 반드시 일치. 반응형 디자인 (모바일, 태블릿, 웹)
- **MUST NOT DO**: 프론트엔드 구현 코드를 이 단계에서 작성하지 않을 것
- **CONTEXT**: `docs/plan/design/uiux/uiux.md`, `docs/plan/design/uiux/style-guide.md`, `docs/plan/design/uiux/prototype/`, `docs/design/api/`, `resources/guides/design/common-principles.md`

### Step 8. 물리 아키텍처 설계 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **TASK**: 물리 아키텍처 설계 (인프라, 네트워크, 배포 구조)
  - **물리 아키텍처 다이어그램** (서브 에이전트 병렬):
    - 개발환경: 사용자 → API G/W → 서비스 → DB 플로우만, 클라우드 서비스 최소한, 모니터링/보안 생략
    - 운영환경: 고가용성, 관리형 서비스, 보안 포함
    - Mermaid 형식, 문법 검사 실행
  - **네트워크 아키텍처 다이어그램** (서브 에이전트 병렬):
    - 개발환경/운영환경 각각 Mermaid로 작성
  - **개발환경 물리 아키텍처 설계서**: K8s 클러스터, 리소스 할당, 네트워크, 데이터, 보안, 모니터링, 비용 최적화
  - **운영환경 물리 아키텍처 설계서**: 고가용성, Multi-Zone, HPA, 관리형 서비스, 보안 계층, 재해복구
  - **마스터 물리 아키텍처 설계서**: 환경별 비교, 전환 전략, 비용 분석, SLA 지표
- **EXPECTED OUTCOME**:
  - `docs/design/physical/physical-architecture.md` — 마스터 설계서
  - `docs/design/physical/physical-architecture-dev.md` — 개발환경 설계서
  - `docs/design/physical/physical-architecture-prod.md` — 운영환경 설계서
  - `docs/design/physical/physical-architecture-dev.mmd` — 개발환경 다이어그램
  - `docs/design/physical/physical-architecture-prod.mmd` — 운영환경 다이어그램
  - `docs/design/physical/network-dev.mmd` — 개발환경 네트워크
  - `docs/design/physical/network-prod.mmd` — 운영환경 네트워크
- **MUST DO**: `resources/guides/design/physical-architecture-design.md` 참조. HighLevel 아키텍처 정의서와 일치. 환경별 차별화 전략. Mermaid 문법 검증
- **MUST NOT DO**: 구현 코드 작성 금지
- **CONTEXT**: `docs/design/architecture.md`, `docs/design/logical-architecture.md`, `docs/design/database/`, `resources/guides/design/common-principles.md`

### Step 9. AI 연동 설계 → Agent: ai-engineer (`/oh-my-claudecode:ralph` 활용)

- **TASK**: 핵심 솔루션의 AI 활용 기회를 분석하고 AI API 연동 설계, 프롬프트 설계, 모델 선정 수행
  1. AI 활용 기회 식별 및 우선순위화 (가치 vs 구현 복잡도)
  2. AI API 연동 설계 (엔드포인트, 요청/응답 스키마)
  3. 프롬프트 설계 (시스템 프롬프트, 컨텍스트 관리 전략)
  4. 모델 선정 (Claude, GPT-4, Gemini 등 용도별 최적 모델)
  5. AI 기능 아키텍처 (RAG, 에이전트, 파인튜닝 등)
- **EXPECTED OUTCOME**: `docs/design/ai-integration.md` 생성
  - AI 활용 기회 목록 (우선순위, ROI 평가)
  - AI 엔드포인트 설계
  - 프롬프트 설계 (시스템 프롬프트, 컨텍스트 관리)
  - 모델 선정 근거
  - AI 기능 아키텍처 다이어그램
- **MUST DO**: 핵심 솔루션에서 AI가 가치를 더할 수 있는 기능을 우선순위화. 모델 선정 근거 명시. 최신 AI SDK 공식 문서 확인
- **MUST NOT DO**: 구현 코드를 이 단계에서 작성하지 않을 것
- **CONTEXT**: `docs/plan/think/핵심솔루션.md`, `docs/design/api/`, `docs/design/frontend/api-mapping.md`, `resources/guides/design/common-principles.md`

### Step 10. HighLevel 아키텍처 정의 → Agent: architect (`/oh-my-claudecode:ralph` 활용)

- **TASK**: 전체 설계 산출물을 종합하여 HighLevel 아키텍처 정의서 작성
  - **준비**: 유저스토리, 아키텍처 패턴, 논리/물리 아키텍처, API/시퀀스/클래스/데이터 설계서 전체 분석
  - **섹션별 작성**:
    1. 개요 (Executive Summary): 아키텍처 범위 및 경계 (유저스토리, 논리 아키텍처와 일치)
    2. 프로젝트 구조: 모노레포/폴리레포 전략, 서비스 구조
    3. 시스템 컨텍스트: 논리 아키텍처 참조
    4. 논리 아키텍처: 바운디드 컨텍스트 (Mermaid)
    5. 프로세스 아키텍처: 핵심 사용자 여정 (Mermaid), 시스템 간 통합 프로세스 (외부 시퀀스 참조)
    6. 개발 아키텍처: 백엔드/프론트엔드 기술스택, 서비스별 설계 패턴 (클래스 설계와 일치), 코딩표준/테스트 전략 링크
    7. 물리 아키텍처: 클라우드 아키텍처 패턴, 인프라 구성 (물리 설계 참조)
    8. 기술 스택 아키텍처: GA 최신 버전
    9. AI/ML 아키텍처: AI 서비스/모델 매핑 (논리 아키텍처, 외부 시퀀스와 일치)
    10. DevOps: CI/CD 파이프라인, 컨테이너 오케스트레이션
    11. 보안 아키텍처: 클라우드 플랫폼에 맞는 보안 전략
    12. 품질 속성 구현 전략: 아키텍처 패턴, 데이터 설계와 일치
    13. ADR (Architecture Decision Records): 주요 의사결정 기록 (후보, 장단점, 이유)
    14. 부록: 관련 문서 목록 및 경로
- **EXPECTED OUTCOME**: `docs/design/high-level-architecture.md` 생성
  - 전체 아키텍처를 종합한 정의서
  - 각 설계 산출물에 대한 참조 경로 포함
  - ADR (주요 아키텍처 의사결정)
- **MUST DO**: `resources/guides/design/architecture-highlevel.md` 참조. 모든 설계 산출물과 일치 확인. ADR 필수 포함
- **MUST NOT DO**: 기존 설계 산출물과 모순되는 내용 작성 금지
- **CONTEXT**: `docs/design/` 하위 전체 산출물, `docs/plan/design/userstory.md`, `resources/guides/design/common-principles.md`

### Step 11. 설계 완료 보고

```
## 설계 완료

### 생성된 산출물

#### 아키텍처
- docs/design/architecture.md — 아키텍처 패턴 및 상위수준 설계
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
- docs/design/database/{service-name}-schema.psql — DB 스키마 스크립트
- docs/design/database/cache-db-design.md — 캐시 DB 설계서

#### 프론트엔드
- docs/design/frontend/uiux-design.md — UI/UX 설계서 (기술 관점)
- docs/design/frontend/style-guide.md — 스타일 가이드
- docs/design/frontend/ia.md — 정보 아키텍처
- docs/design/frontend/api-mapping.md — API 매핑 설계서

#### 물리 아키텍처
- docs/design/physical/physical-architecture.md — 마스터 설계서
- docs/design/physical/physical-architecture-dev.md — 개발환경 설계서
- docs/design/physical/physical-architecture-prod.md — 운영환경 설계서
- docs/design/physical/physical-architecture-dev.mmd — 개발환경 다이어그램
- docs/design/physical/physical-architecture-prod.mmd — 운영환경 다이어그램
- docs/design/physical/network-dev.mmd — 개발환경 네트워크
- docs/design/physical/network-prod.mmd — 운영환경 네트워크

#### AI
- docs/design/ai-integration.md — AI 연동 설계

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
2. 산출물 내용 품질 검증 (Mermaid/PlantUML 다이어그램 포함, 설계 가이드 준수)
3. PlantUML 문법 검사 통과 확인
4. swagger-cli validate 통과 확인 (API YAML)
5. 이전 Phase 산출물과의 일관성 확인 (기획 산출물 → 설계 산출물 연계)
6. 설계 산출물 간 상호 일관성 확인 (유저스토리 ID 추적, API-시퀀스-클래스 일치)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | 모든 설계 산출물은 `docs/design/` 하위 디렉토리에 저장할 것 |
| 2 | PlantUML은 `!theme mono` 사용, Mermaid는 코드블록으로 포함할 것 |
| 3 | 각 단계는 이전 단계 산출물을 CONTEXT로 활용할 것 |
| 4 | 이벤트 스토밍 결과(`docs/plan/think/es/*.puml`)를 반드시 참조할 것 |
| 5 | 유저스토리와 매칭되지 않는 불필요한 설계를 추가하지 않을 것 |
| 6 | PlantUML 스크립트는 생성 즉시 문법 검사를 실행할 것 |
| 7 | API YAML은 swagger-cli로 검증할 것 |
| 8 | 서비스별 독립적으로 병렬 설계가 가능한 경우 서브 에이전트를 활용할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 설계 단계에서 구현 코드를 작성하지 않을 것 |
| 2 | 기획 산출물(`docs/plan/`) 없이 설계를 시작하지 않을 것 |
| 3 | 서비스 기획(고객 분석, UI/UX 설계)을 이 단계에서 수행하지 않을 것 |
| 4 | sequence diagram에서 `..>` 화살표를 사용하지 않을 것 |
| 5 | 서비스 간 DB FK 관계를 설정하지 않을 것 |

## 검증 체크리스트

### 아키텍처
- [ ] architecture.md 생성 완료 (패턴 평가 매트릭스, Mermaid 다이어그램 포함)
- [ ] logical-architecture.md + .mmd 생성 완료
- [ ] high-level-architecture.md 생성 완료 (ADR 포함)

### 시퀀스
- [ ] sequence/outer/ 외부 시퀀스 생성 완료 (플로우별 파일)
- [ ] sequence/inner/ 내부 시퀀스 생성 완료 (서비스-시나리오별 파일)
- [ ] PlantUML 문법 검사 통과

### API
- [ ] api/{service-name}-api.yaml 생성 완료 (서비스별)
- [ ] swagger-cli validate 통과

### 클래스
- [ ] class/common-base.puml 생성 완료
- [ ] class/{service-name}.puml + {service-name}-simple.puml 생성 완료
- [ ] class/package-structure.md 생성 완료
- [ ] PlantUML 문법 검사 통과

### 데이터
- [ ] database/{service-name}.md + -erd.puml + -schema.psql 생성 완료
- [ ] database/cache-db-design.md 생성 완료
- [ ] 클래스 설계의 Entity와 테이블 일치 확인

### 프론트엔드
- [ ] frontend/uiux-design.md 생성 완료
- [ ] frontend/style-guide.md 생성 완료
- [ ] frontend/ia.md 생성 완료
- [ ] frontend/api-mapping.md 생성 완료
- [ ] 백엔드 API 명세서와 일치 확인

### 물리 아키텍처
- [ ] physical/ 하위 7개 파일 생성 완료 (마스터, 개발/운영 설계서, 다이어그램, 네트워크)
- [ ] Mermaid 문법 검증 통과

### AI/기타
- [ ] ai-integration.md 생성 완료
- [ ] 유저스토리 ID 전체 추적 가능 (유저스토리 → 시퀀스 → API → 클래스)
- [ ] 완료 보고에 다음 단계 안내 포함
