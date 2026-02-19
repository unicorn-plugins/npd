---
name: create
description: 새 프로젝트 생성 — 모노레포 구조 초기화, domain-expert 동적 생성, GitHub 레포 자동 생성
type: core
user-invocable: true
allowed-tools: Read, Write, Bash, Task
---

# Create

[NPD Create 활성화]

## 목표

사용자로부터 프로젝트명·기술스택·MVP 주제를 입력받아
모노레포 디렉토리 구조를 생성하고, MVP 주제로 도메인을 자동 추론하여
`agents/domain-expert-{서비스명}/` 에이전트를 동적 생성하며, GitHub 레포를 자동 생성함.

## 활성화 조건

사용자가 `/npd:create` 호출 시 또는 "새 프로젝트 생성", "프로젝트 만들어줘" 키워드 감지 시.

## 워크플로우

### Step 1. 프로젝트 정보 수집

사용자에게 아래 항목을 질문:

| 항목 | 기본값 | 설명 |
|------|--------|------|
| 프로젝트명 | — | 영문 kebab-case (예: my-project) |
| 서비스명 | 프로젝트명과 동일 | domain-expert 디렉토리명에 사용 |
| MVP 주제 | — | 자유 형식 (예: "당뇨 환자 식단 관리 앱") |
| 백엔드 기술스택 | Spring Boot | Java/Kotlin Spring Boot |
| 프론트엔드 기술스택 | React | React / Vue / Next.js |
| GitHub 레포 생성 여부 | Yes | GitHub 원격 저장소 자동 생성 |

### Step 2. 도메인 추론 → Agent: orchestrator

- **TASK**: MVP 주제를 분석하여 도메인을 추론하고, domain-expert 에이전트의 전문 분야와 페르소나를 정의
- **EXPECTED OUTCOME**: 도메인명(예: healthcare), 전문 지식 목록, 관련 규제/표준, 에이전트 페르소나 정의
- **MUST DO**: MVP 주제의 핵심 도메인을 한 단어로 추론할 것. 전문가 페르소나를 구체적으로 정의할 것
- **MUST NOT DO**: 도메인을 너무 광범위하게 정의하지 않을 것 (예: "IT" 같은 범용 도메인 금지)
- **CONTEXT**: MVP 주제: {사용자 입력값}

### Step 3. 모노레포 디렉토리 구조 생성

아래 구조로 `{프로젝트명}/` 디렉토리 생성:

```
{프로젝트명}/
├── backend/
│   └── src/
├── frontend/
│   └── src/
├── docs/
│   ├── plan/
│   ├── design/
│   └── test/
├── deploy/
│   └── k8s/
├── .github/
│   └── workflows/
└── CLAUDE.md
```

### Step 4. CLAUDE.md 생성

프로젝트 디렉토리에 CLAUDE.md 생성:
- 프로젝트명, MVP 주제, 기술스택 기록
- 사용 중인 NPD 에이전트 목록 기록
- 개발 컨벤션 기본값 설정

### Step 5. domain-expert 에이전트 동적 생성 → Agent: orchestrator

- **TASK**: Step 2에서 추론된 도메인 정보를 기반으로 `agents/domain-expert-{서비스명}/` 디렉토리에 AGENT.md, agentcard.yaml, tools.yaml 생성
- **EXPECTED OUTCOME**: `agents/domain-expert-{서비스명}/AGENT.md`, `agentcard.yaml`, `tools.yaml` 파일 3개 생성 완료
- **MUST DO**: AGENT.md에 도메인 특화 지식과 워크플로우 포함. agentcard.yaml에 도메인 전문가 페르소나 포함. tools.yaml에 필요 추상 도구 정의
- **MUST NOT DO**: 모델명·도구명 하드코딩 금지. 다른 서비스의 domain-expert 덮어쓰기 금지
- **CONTEXT**: 서비스명: {서비스명}, 도메인: {추론된 도메인}, 전문지식: {목록}, MVP 주제: {사용자 입력값}

### Step 6. GitHub 레포 생성 (선택)

사용자가 GitHub 레포 생성을 선택한 경우:
1. `resources/tools/create_repo` 도구 사용 가능 여부 확인
2. 환경변수 `GITHUB_TOKEN` 설정 여부 확인
3. 레포 생성 실행 (공개/비공개 여부 확인)
4. 생성된 레포 URL 보고

### Step 7. 완료 보고

```
## 프로젝트 생성 완료

- 프로젝트명: {프로젝트명}
- MVP 주제: {MVP 주제}
- 도메인: {추론된 도메인}
- domain-expert: agents/domain-expert-{서비스명}/
- GitHub 레포: {URL 또는 "미생성"}

### 다음 단계
`/npd:plan` 으로 기획을 시작하세요.
```

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | MVP 주제로 도메인을 반드시 추론하여 domain-expert 에이전트를 동적 생성할 것 |
| 2 | 복수 서비스 병행 개발 시 서비스명을 다르게 하여 별도 디렉토리에 생성할 것 |
| 3 | 모노레포 구조(backend/, frontend/, docs/, deploy/)를 반드시 생성할 것 |
| 4 | CLAUDE.md를 프로젝트 루트에 반드시 생성할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 기존 domain-expert 에이전트를 덮어쓰지 않을 것 (서비스명 중복 확인) |
| 2 | GitHub 토큰을 코드나 파일에 하드코딩하지 않을 것 |

## 검증 체크리스트

- [ ] 프로젝트 정보(프로젝트명, MVP 주제, 기술스택) 수집 완료
- [ ] 도메인 추론 완료
- [ ] 모노레포 디렉토리 구조 생성 완료
- [ ] CLAUDE.md 생성 완료
- [ ] `agents/domain-expert-{서비스명}/` 3파일 생성 완료
- [ ] 기존 domain-expert와 중복되지 않음
- [ ] 완료 보고에 다음 단계 안내 포함