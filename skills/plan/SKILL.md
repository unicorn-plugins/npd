---
name: plan
description: 기획 단계 AI 협업 — PO·서비스기획자·아키텍트·도메인전문가·AI엔지니어가 협업하여 기획 수행
type: core
user-invocable: true
allowed-tools: Read, Write, Task
---

# Plan

[NPD Plan 활성화]

## 목표

PO·서비스기획자·아키텍트·도메인전문가·AI엔지니어가 협업하여
상위수준기획 → 기획구체화 → 유저스토리 → 프로토타입 순서로 기획을 수행함.

## 활성화 조건

사용자가 `/npd:plan` 호출 시 또는 "기획 시작", "기획해줘" 키워드 감지 시.

## 선행 조건

- `/npd:create` 완료 (프로젝트 디렉토리 및 CLAUDE.md 존재)
- `agents/domain-expert-{서비스명}/` 존재

## 워크플로우

### Step 1. 기획 컨텍스트 파악

CLAUDE.md 및 MVP 주제를 읽어 기획 컨텍스트 파악.
`resources/guides/plan/think-prompt.md` 참조하여 기획 접근 방식 확인.

### Step 2. 상위수준 기획 → Agent: product-owner

- **TASK**: MVP 주제를 기반으로 제품 비전, 목표 고객, 핵심 문제, MVP 범위(Must Have/Should Have)를 정의하고 `docs/plan/product-vision.md`에 저장
- **EXPECTED OUTCOME**: `docs/plan/product-vision.md` 생성. 제품 비전, 목표 고객, KPI, MVP 기능 목록 포함
- **MUST DO**: Must Have 기능만 MVP에 포함. 비즈니스 가치 기준으로 우선순위 결정
- **MUST NOT DO**: 기술 구현 방법을 이 단계에서 결정하지 않을 것
- **CONTEXT**: CLAUDE.md의 프로젝트 정보 및 MVP 주제

### Step 3. 도메인 검토 → Agent: domain-expert-{서비스명}

- **TASK**: 제품 비전 문서를 검토하여 도메인 관점의 요구사항 보완, 규제·표준 고려사항 추가, 비즈니스 로직 자문을 `docs/plan/domain-requirements.md`에 저장
- **EXPECTED OUTCOME**: `docs/plan/domain-requirements.md` 생성. 도메인 특화 요구사항, 규제 준수 항목 포함
- **MUST DO**: 해당 도메인의 실제 비즈니스 관행과 규제를 반영할 것
- **MUST NOT DO**: 도메인 외 기술적 구현 방법을 논의하지 않을 것
- **CONTEXT**: `docs/plan/product-vision.md` 내용

### Step 4. 기획 구체화 → Agent: service-planner

- **TASK**: 제품 비전과 도메인 요구사항을 기반으로 페르소나 정의, 사용자 여정 지도, 핵심 사용 시나리오를 작성하여 `docs/plan/service-plan.md`에 저장
- **EXPECTED OUTCOME**: `docs/plan/service-plan.md` 생성. 페르소나, 사용자 여정, 핵심 시나리오 포함
- **MUST DO**: 실제 사용자 관점에서 서비스 흐름을 구체화할 것
- **MUST NOT DO**: 화면 UI 상세 디자인을 이 단계에서 확정하지 않을 것
- **CONTEXT**: `docs/plan/product-vision.md`, `docs/plan/domain-requirements.md`

### Step 5. 기술 실현 가능성 검토 → Agent: architect

- **TASK**: 기획 산출물을 검토하여 기술 실현 가능성을 평가하고, 기술 리스크 및 대안을 `docs/plan/tech-feasibility.md`에 저장
- **EXPECTED OUTCOME**: `docs/plan/tech-feasibility.md` 생성. 기술 스택 적합성, 리스크, 권장 사항 포함
- **MUST DO**: Spring Boot 백엔드 기준으로 실현 가능성 평가. 리스크는 반드시 대안과 함께 제시
- **MUST NOT DO**: 상세 설계를 이 단계에서 수행하지 않을 것
- **CONTEXT**: 기획 산출물 전체 및 기술스택 정보(CLAUDE.md)

### Step 6. AI 활용 기회 발굴 → Agent: ai-engineer

- **TASK**: 기획 산출물을 검토하여 AI로 자동화·고도화 가능한 기회를 발굴하고 `docs/plan/ai-opportunities.md`에 저장
- **EXPECTED OUTCOME**: `docs/plan/ai-opportunities.md` 생성. AI 활용 기회 목록, 가치·복잡도 평가, 우선순위 포함
- **MUST DO**: 각 AI 기회에 대해 비즈니스 가치와 구현 복잡도를 함께 평가할 것
- **MUST NOT DO**: AI를 위한 AI 제안 금지 — 실질적 가치가 있는 것만 제안
- **CONTEXT**: 기획 산출물 전체

### Step 7. 유저스토리 작성 → Agent: service-planner

- **TASK**: 확정된 기획 산출물을 기반으로 에픽별 유저스토리와 인수 조건을 작성하여 `docs/plan/user-stories.md`에 저장
- **EXPECTED OUTCOME**: `docs/plan/user-stories.md` 생성. 에픽 분류, 유저스토리(As a/I want/So that), 인수 조건 포함
- **MUST DO**: MVP 범위의 기능만 유저스토리로 작성. 인수 조건은 테스트 가능한 형태로 작성
- **MUST NOT DO**: Should Have 기능을 Must Have로 격상하지 않을 것
- **CONTEXT**: 기획 산출물 전체

### Step 8. 기획 완료 보고

```
## 기획 완료

### 생성된 산출물
- docs/plan/product-vision.md — 제품 비전 및 MVP 범위
- docs/plan/domain-requirements.md — 도메인 요구사항
- docs/plan/service-plan.md — 서비스 기획서
- docs/plan/tech-feasibility.md — 기술 실현 가능성 검토
- docs/plan/ai-opportunities.md — AI 활용 기회
- docs/plan/user-stories.md — 유저스토리

### 다음 단계
`/npd:design` 으로 설계를 시작하세요.
```

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | domain-expert-{서비스명} 에이전트를 반드시 기획 검토에 참여시킬 것 |
| 2 | 기획 산출물은 반드시 `docs/plan/` 디렉토리에 저장할 것 |
| 3 | 각 단계의 산출물이 다음 단계의 CONTEXT로 연결되도록 할 것 |
| 4 | AI 엔지니어는 기획 단계에서 반드시 AI 활용 기회를 발굴할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 기획 단계에서 코드를 작성하지 않을 것 |
| 2 | 설계 산출물(다이어그램 등)을 기획 단계에서 생성하지 않을 것 |

## 검증 체크리스트

- [ ] CLAUDE.md 및 MVP 주제 파악 완료
- [ ] product-vision.md 생성 완료
- [ ] domain-requirements.md 생성 완료 (domain-expert 참여)
- [ ] service-plan.md 생성 완료
- [ ] tech-feasibility.md 생성 완료
- [ ] ai-opportunities.md 생성 완료
- [ ] user-stories.md 생성 완료
- [ ] 완료 보고에 다음 단계(/npd:design) 안내 포함