---
name: design
description: 설계 단계 AI 협업 — 아키텍트·AI엔지니어가 협업하여 아키텍처 패턴 선정 및 전체 설계 수행
type: orchestrator
user-invocable: true
allowed-tools: Read, Write, Task
---

# Design

[NPD Design 활성화]

## 목표

아키텍트·AI엔지니어가 협업하여 클라우드 아키텍처 패턴 선정부터
논리/시퀀스/API/클래스/데이터 설계까지 전체 설계 과정을 수행함.

## 선행 조건

- `/npd:plan` 완료 (`docs/plan/` 산출물 존재)

## 워크플로우

### Step 1. 아키텍처 패턴 선정 → Agent: architect

- **TASK**: 기획 산출물과 기술스택을 기반으로 클라우드 아키텍처 패턴을 선정하고 상위수준 아키텍처를 설계하여 `docs/design/architecture.md`에 저장
- **EXPECTED OUTCOME**: `docs/design/architecture.md` 생성. 선정 패턴, 선택 근거, 상위수준 아키텍처 다이어그램(Mermaid) 포함
- **MUST DO**: `resources/guides/design/architecture-patterns.md`, `architecture-highlevel.md` 반드시 참조. Mermaid 다이어그램으로 시각화
- **MUST NOT DO**: 패턴 선택 근거 없이 결정하지 않을 것
- **CONTEXT**: `docs/plan/` 산출물 전체, CLAUDE.md 기술스택

### Step 2. 논리 아키텍처 설계 → Agent: architect

- **TASK**: 선정된 아키텍처 패턴을 기반으로 논리 아키텍처를 설계하여 `docs/design/logical-architecture.md`에 저장
- **EXPECTED OUTCOME**: `docs/design/logical-architecture.md` 생성. 레이어별 컴포넌트, 의존 관계 다이어그램 포함
- **MUST DO**: `resources/guides/design/logical-architecture-design.md` 참조
- **MUST NOT DO**: 물리적 배포 구조를 이 단계에서 결정하지 않을 것
- **CONTEXT**: `docs/design/architecture.md`

### Step 3. 시퀀스 설계 → Agent: architect

- **TASK**: 핵심 유저스토리의 외부·내부 시퀀스 다이어그램을 작성하여 `docs/design/sequence.md`에 저장
- **EXPECTED OUTCOME**: `docs/design/sequence.md` 생성. 외부 시퀀스(사용자↔시스템) 및 내부 시퀀스(컴포넌트 간) 다이어그램 포함
- **MUST DO**: `resources/guides/design/sequence-outer-design.md`, `sequence-inner-design.md` 참조. MVP Must Have 유저스토리 전체 커버
- **MUST NOT DO**: 모든 유저스토리를 다 그리려다 핵심을 놓치지 않을 것
- **CONTEXT**: `docs/plan/user-stories.md`, `docs/design/logical-architecture.md`

### Step 4. API 설계 → Agent: architect

- **TASK**: REST API 엔드포인트를 설계하여 `docs/design/api-design.md`에 저장
- **EXPECTED OUTCOME**: `docs/design/api-design.md` 생성. 엔드포인트 목록, 요청/응답 스키마, HTTP 상태코드 포함
- **MUST DO**: `resources/guides/design/api-design.md` 참조. RESTful 원칙 준수
- **MUST NOT DO**: 구현 코드를 이 단계에서 작성하지 않을 것
- **CONTEXT**: `docs/plan/user-stories.md`, `docs/design/sequence.md`

### Step 5. 클래스 및 데이터 설계 → Agent: architect

- **TASK**: 도메인 클래스 다이어그램과 데이터베이스 스키마를 설계하여 `docs/design/class-design.md`, `docs/design/data-design.md`에 저장
- **EXPECTED OUTCOME**: 두 파일 생성. 클래스 다이어그램(Mermaid), ERD(Mermaid) 포함
- **MUST DO**: `resources/guides/design/class-design.md`, `data-design.md` 참조
- **MUST NOT DO**: ORM 설정 코드를 이 단계에서 작성하지 않을 것
- **CONTEXT**: `docs/design/api-design.md`, `docs/plan/domain-requirements.md`

### Step 6. AI 연동 설계 → Agent: ai-engineer

- **TASK**: AI 기회 목록을 기반으로 AI API 연동 설계, 프롬프트 설계, 모델 선정을 수행하여 `docs/design/ai-integration.md`에 저장
- **EXPECTED OUTCOME**: `docs/design/ai-integration.md` 생성. AI 엔드포인트, 프롬프트 설계, 모델 선정 근거 포함
- **MUST DO**: `docs/plan/ai-opportunities.md`의 우선순위 기준으로 설계. 모델 선정 근거 명시
- **MUST NOT DO**: 구현 코드를 이 단계에서 작성하지 않을 것
- **CONTEXT**: `docs/plan/ai-opportunities.md`, `docs/design/api-design.md`

### Step 7. 설계 완료 보고

```
## 설계 완료

### 생성된 산출물
- docs/design/architecture.md — 아키텍처 패턴 및 상위수준 설계
- docs/design/logical-architecture.md — 논리 아키텍처
- docs/design/sequence.md — 시퀀스 다이어그램
- docs/design/api-design.md — API 설계서
- docs/design/class-design.md — 클래스 다이어그램
- docs/design/data-design.md — 데이터 설계
- docs/design/ai-integration.md — AI 연동 설계

### 다음 단계
`/npd:develop` 으로 개발을 시작하세요.
```

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | 모든 설계 산출물은 `docs/design/` 에 저장할 것 |
| 2 | 다이어그램은 Mermaid 코드블록으로 포함할 것 |
| 3 | 각 단계는 이전 단계 산출물을 CONTEXT로 활용할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 설계 단계에서 구현 코드를 작성하지 않을 것 |
| 2 | 기획 산출물 없이 설계를 시작하지 않을 것 |

## 검증 체크리스트

- [ ] architecture.md 생성 완료 (Mermaid 다이어그램 포함)
- [ ] logical-architecture.md 생성 완료
- [ ] sequence.md 생성 완료
- [ ] api-design.md 생성 완료
- [ ] class-design.md, data-design.md 생성 완료
- [ ] ai-integration.md 생성 완료
- [ ] 완료 보고에 다음 단계 안내 포함