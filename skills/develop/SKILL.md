---
name: develop
description: 개발 단계 AI 협업 — 백엔드·프론트엔드·AI엔지니어·QA가 협업하여 코드 생성 및 테스트 수행
type: orchestrator
user-invocable: true
allowed-tools: Read, Write, Bash, Task
---

# Develop

[NPD Develop 활성화]

## 목표

백엔드개발자·프론트엔드개발자·AI엔지니어·QA가 협업하여
공통모듈 → 백엔드 → 프론트엔드 → AI기능 → 테스트 순서로 개발을 수행함.

## 선행 조건

- `/npd:design` 완료 (`docs/design/` 산출물 존재)

## 워크플로우

### Step 1. 공통 모듈 개발 → Agent: backend-developer

- **TASK**: 모노레포 구조에 맞게 백엔드 공통 모듈(예외처리, 응답 포맷, 공통 설정)을 개발
- **EXPECTED OUTCOME**: `backend/src/main/java/.../common/` 디렉토리에 공통 모듈 코드 생성
- **MUST DO**: `resources/guides/develop/dev-backend.md` 참조. Spring Boot 기준 공통 모듈 구조 적용
- **MUST NOT DO**: 비즈니스 로직을 공통 모듈에 포함하지 않을 것
- **CONTEXT**: CLAUDE.md 기술스택, `docs/design/architecture.md`

### Step 2. 데이터베이스 설정 → Agent: backend-developer

- **TASK**: 데이터 설계서 기반으로 JPA 엔티티와 레포지토리를 구현하고 데이터베이스 설정을 완료
- **EXPECTED OUTCOME**: 엔티티 클래스, 레포지토리 인터페이스, application.yml DB 설정 생성
- **MUST DO**: `resources/guides/develop/database-plan.md` 참조. `docs/design/data-design.md` 기준으로 구현
- **MUST NOT DO**: 설계서에 없는 컬럼을 임의로 추가하지 않을 것
- **CONTEXT**: `docs/design/data-design.md`, `docs/design/class-design.md`

### Step 3. 백엔드 API 개발 → Agent: backend-developer

- **TASK**: API 설계서 기반으로 컨트롤러·서비스·레포지토리 레이어를 구현하고 단위 테스트 작성
- **EXPECTED OUTCOME**: API 엔드포인트 구현 코드 및 단위 테스트 코드 생성
- **MUST DO**: `resources/guides/develop/dev-backend.md`, `dev-backend-testcode.md` 참조. 모든 API에 단위 테스트 작성
- **MUST NOT DO**: 테스트 없는 코드 제출 금지
- **CONTEXT**: `docs/design/api-design.md`, `docs/design/sequence.md`

### Step 4. 프론트엔드 개발 → Agent: frontend-developer

- **TASK**: UI/UX 설계서 기반으로 프론트엔드 컴포넌트를 구현하고 백엔드 API와 연동
- **EXPECTED OUTCOME**: 프론트엔드 컴포넌트 코드 및 API 연동 코드 생성
- **MUST DO**: `resources/guides/develop/dev-frontend.md` 참조. 반응형 UI 구현
- **MUST NOT DO**: 백엔드 API 없이 프론트엔드를 완성 처리하지 않을 것
- **CONTEXT**: `docs/design/uiux-design.md`(존재 시), `docs/design/api-design.md`

### Step 5. AI 기능 구현 → Agent: ai-engineer

- **TASK**: AI 연동 설계서 기반으로 AI API 연동 코드와 프롬프트를 구현
- **EXPECTED OUTCOME**: `src/ai/` 디렉토리에 AI 연동 코드 생성
- **MUST DO**: `docs/design/ai-integration.md` 기준으로 구현. 프롬프트 최적화 포함
- **MUST NOT DO**: 설계에 없는 AI 기능을 임의로 추가하지 않을 것
- **CONTEXT**: `docs/design/ai-integration.md`

### Step 6. 테스트 및 버그 수정 → Agent: qa-engineer

- **TASK**: 구현된 백엔드 API와 프론트엔드 UI를 테스트하고 버그를 리포트
- **EXPECTED OUTCOME**: `docs/test/test-report.md` 생성. 테스트 통과 여부 및 버그 목록 포함
- **MUST DO**: `resources/guides/develop/test-backend.md` 참조. MVP Must Have 기능 전체 테스트
- **MUST NOT DO**: 버그 발견 시 무시하지 않을 것 — 반드시 리포트 작성
- **CONTEXT**: 구현된 전체 코드, `docs/plan/user-stories.md`

### Step 7. 개발 완료 보고

```
## 개발 완료

### 구현된 기능
- 백엔드 API: {엔드포인트 수}개
- 프론트엔드 컴포넌트: {컴포넌트 수}개
- AI 기능: {기능 수}개
- 테스트 통과율: {비율}

### 다음 단계
`/npd:deploy` 로 배포를 시작하세요.
```

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | 공통모듈 → 백엔드 → 프론트엔드 → AI → 테스트 순서를 반드시 준수할 것 |
| 2 | 모든 백엔드 코드에 단위 테스트를 포함할 것 |
| 3 | 설계 산출물(`docs/design/`)을 반드시 CONTEXT로 활용할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 설계 없이 개발을 시작하지 않을 것 |
| 2 | 테스트 없이 개발 완료를 선언하지 않을 것 |

## 검증 체크리스트

- [ ] 공통 모듈 개발 완료
- [ ] 데이터베이스 설정 완료
- [ ] 백엔드 API 구현 및 단위 테스트 완료
- [ ] 프론트엔드 컴포넌트 구현 완료
- [ ] AI 기능 구현 완료
- [ ] QA 테스트 완료 및 test-report.md 생성
- [ ] 완료 보고에 다음 단계 안내 포함