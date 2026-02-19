---
name: help
description: NPD 플러그인 사용법 및 명령어 안내
type: utility
user-invocable: true
allowed-tools: Read
---

# Help

## 목표

NPD 플러그인의 사용 가능한 명령어와 사용법을 즉시 출력함.

## 활성화 조건

사용자가 `/npd:help` 호출 시 또는 "도움말", "명령어 목록" 키워드 감지 시.

## 워크플로우

**중요: 추가적인 파일 탐색이나 에이전트 위임 없이, 아래 내용을 즉시 사용자에게 출력하세요.**

아래 내용을 즉시 출력:

---

## NPD 플러그인 — 사용 안내

사람과 AI가 협업하여 새로운 프로젝트의 기획-설계-개발-배포 전 과정을 지원하는 플러그인.

### 명령어 목록

| 명령어 | 설명 |
|--------|------|
| `/npd:prepare` | 로컬 개발 환경 사전준비 (기본 프로그램, Claude Code + OMC 설치 안내) |
| `/npd:setup` | 플러그인 초기 설정 (MCP 서버 설치, 토큰 설정) |
| `/npd:help` | 이 도움말 출력 |
| `/npd:create` | 새 프로젝트 생성 (모노레포 + domain-expert 생성 + GitHub 레포) |
| `/npd:plan` | 기획 단계 AI 협업 (PO·서비스기획자·아키텍트·도메인전문가·AI엔지니어) |
| `/npd:design` | 설계 단계 AI 협업 (아키텍트·AI엔지니어) |
| `/npd:develop` | 개발 단계 AI 협업 (백엔드·프론트엔드·AI엔지니어·QA) |
| `/npd:deploy` | 배포 단계 AI 협업 (DevOps 엔지니어) |
| `/npd:add-ext-skill` | 외부 플러그인 연동 스킬 추가 |
| `/npd:remove-ext-skill` | 외부 플러그인 연동 스킬 제거 |

### 권장 사용 순서

```
0. /npd:prepare    → 로컬 개발 환경 사전준비
1. /npd:setup      → 초기 설정
2. /npd:create     → 프로젝트 생성
3. /npd:plan       → 기획
4. /npd:design     → 설계
5. /npd:develop    → 개발
6. /npd:deploy     → 배포
```

### 팁

- 각 단계는 독립적으로 실행 가능 (중간 단계부터 시작 가능)
- `domain-expert`는 `/npd:create` 시 MVP 주제를 입력하면 자동 생성됨
- 외부 플러그인 연동이 필요하면 `/npd:add-ext-skill` 사용

---

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | 에이전트 위임 없이 즉시 출력할 것 |
| 2 | 명령어 테이블을 항상 최신 상태로 유지할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 에이전트를 호출하지 않을 것 (직결형) |

## 검증 체크리스트

- [ ] 모든 명령어가 테이블에 포함되어 있는가
- [ ] 권장 사용 순서가 명시되어 있는가
- [ ] 즉시 출력 방식으로 동작하는가