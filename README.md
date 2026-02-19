# NPD — New Product Development

> 사람과 AI가 협업하여 새로운 프로젝트의 기획-설계-개발-배포 전 과정을 지원하는 Claude Code 플러그인

---

## 개요

NPD는 PO·서비스기획자·아키텍트·도메인전문가·AI엔지니어·백엔드·프론트엔드·QA·DevOps 등 9개 전문가 AI 에이전트가 협업하여
새로운 소프트웨어 제품의 전체 개발 수명주기를 지원하는 DMAP 플러그인임.

MVP 주제를 입력하면 도메인 전문가 에이전트를 자동 생성하고,
모노레포 기반 프로젝트 구조를 생성하며, 기획→설계→개발→배포 전 과정을 AI와 함께 수행함.

**주요 기능:**
- MVP 주제 입력 시 도메인 전문가(`domain-expert-{서비스명}`) 에이전트 자동 동적 생성
- 복수 서비스 병행 개발 시 서비스별 독립 domain-expert 관리 (덮어쓰기 방지)
- Spring Boot 백엔드 + 모노레포 패턴 기반 프로젝트 구조 자동 생성
- GitHub 레포 자동 생성 (`create_repo` 도구 연동)
- 기획 단계: 상위기획→도메인검토→기획구체화→기술검토→AI기회발굴→유저스토리 순 6개 산출물 자동 생성
- 설계 단계: 아키텍처→논리설계→시퀀스→API→클래스/데이터→AI연동 설계 7개 산출물
- 개발 단계: 공통모듈→DB→백엔드→프론트→AI기능→테스트 순 구현
- 배포 단계: Docker 빌드→컨테이너 검증→K8s 배포→CI/CD 파이프라인 자동 구성

---

## 설치

### 사전 요구사항

- [Claude Code](https://claude.com/claude-code) CLI 설치
- Git + GitHub 계정 (GitHub 레포 자동 생성 시 `GITHUB_TOKEN` 환경변수 필요)
- Docker (배포 단계 컨테이너 빌드 시 필요)
- kubectl (Kubernetes 배포 시 필요)

### 플러그인 설치

**방법 1: GitHub (권장)**

```bash
# 1. GitHub 저장소를 마켓플레이스로 등록
claude plugin marketplace add unicorn-plugins/npd

# 2. 플러그인 설치
claude plugin install npd@npd

# 3. 설치 확인
claude plugin list
```

**방법 2: 로컬**

```bash
# 1. 로컬 경로 등록
claude plugin marketplace add ~/workspace/npd

# 2. 플러그인 설치
claude plugin install npd@npd
```

> **설치 후 초기 설정:**
> ```
> /npd:setup
> ```

---

## 업그레이드

```bash
claude plugin update npd
```

---

## 사용법

### 권장 사용 순서

```
1. /npd:setup    → MCP 서버 설치, 환경변수 설정
2. /npd:create   → 새 프로젝트 생성 (모노레포 + domain-expert + GitHub 레포)
3. /npd:plan     → 기획 단계 (PO·서비스기획자·아키텍트·도메인전문가·AI엔지니어 협업)
4. /npd:design   → 설계 단계 (아키텍트·AI엔지니어 협업)
5. /npd:develop  → 개발 단계 (백엔드·프론트엔드·AI엔지니어·QA 협업)
6. /npd:deploy   → 배포 단계 (DevOps 엔지니어)
```

### 명령어 목록

| 명령어 | 유형 | 설명 |
|--------|------|------|
| `/npd:setup` | Setup | 플러그인 초기 설정 (MCP 서버, 환경변수) |
| `/npd:help` | Utility | 사용법 안내 |
| `/npd:create` | Core | 새 프로젝트 생성 (모노레포 + domain-expert + GitHub 레포) |
| `/npd:plan` | Core | 기획 단계 AI 협업 |
| `/npd:design` | Orchestrator | 설계 단계 AI 협업 |
| `/npd:develop` | Orchestrator | 개발 단계 AI 협업 |
| `/npd:deploy` | Orchestrator | 배포 단계 AI 협업 |
| `/npd:add-ext-skill` | Utility | 외부 플러그인 연동 스킬 추가 |
| `/npd:remove-ext-skill` | Utility | 외부 플러그인 연동 스킬 제거 |

### 사용 예시

```
# 새 프로젝트 생성
/npd:create
> 프로젝트명: diet-manager
> MVP 주제: 당뇨 환자를 위한 식단 관리 및 혈당 추적 앱
> 기술스택: Spring Boot 백엔드, React 프론트엔드

→ domain-expert-diet-manager 에이전트 자동 생성
→ 모노레포 구조 생성
→ GitHub 레포 생성
```

---

## 에이전트 구성

| 에이전트 | Tier | 담당 단계 | 역할 |
|----------|------|----------|------|
| `orchestrator` | HIGH | 전체 | 단계 전환 판단, 에이전트 간 핸드오프 |
| `product-owner` | HIGH | 기획 | 비즈니스 가치 판단, MVP 범위 정의 |
| `service-planner` | MEDIUM | 기획 | 사용자 경험 설계, 유저스토리 작성 |
| `architect` | HIGH | 기획·설계 | 아키텍처 설계, 기술 실현 가능성 검토 |
| `domain-expert-{서비스명}` | HIGH | 기획 | 도메인 특화 지식 (create 시 동적 생성) |
| `ai-engineer` | HIGH | 기획·설계·개발 | AI/ML 기회 발굴 및 구현 |
| `backend-developer` | MEDIUM | 개발 | Spring Boot 백엔드 개발 |
| `frontend-developer` | MEDIUM | 개발 | 프론트엔드 개발 |
| `qa-engineer` | MEDIUM | 개발 | 테스트 및 버그 리포트 |
| `devops-engineer` | MEDIUM | 배포 | Docker·K8s·CI/CD |

---

## 요구사항

- Claude Code ≥ 1.0.0
- Git
- Docker (배포 단계)
- kubectl (K8s 배포 단계)
- GitHub 계정 + Personal Access Token (GitHub 레포 자동 생성 시)

---

## 라이선스

MIT License — Copyright (c) 2026 Unicorn Inc.
