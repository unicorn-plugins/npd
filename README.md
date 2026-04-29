# NPD — New Product Development

> 사람과 AI가 협업하여 새로운 프로젝트의 기획-설계-개발-배포 전 과정을 지원하는 Claude Code 플러그인

---

## 개요

NPD는 PO·서비스기획자·아키텍트·도메인전문가·AI엔지니어·백엔드·프론트엔드·QA·DevOps 등 9개 전문가 AI 에이전트가 협업하여
새로운 소프트웨어 제품의 전체 개발 수명주기를 지원하는 플러그인임.

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

## 사전설치

<a href="https://github.com/unicorn-plugins/npd/blob/main/resources/guides/setup/prepare.md" target="_blank">설치 가이드 보기</a>
  
---

## 업그레이드

```bash
claude plugin update npd
```

---

## 사용법

### 권장 사용 순서

```
0. /npd:prepare  → 로컬 개발 환경 사전준비 (기본 프로그램, Claude Code + OMC 설치 안내)
2. /npd:create   → 새 프로젝트 생성 (모노레포 + domain-expert + GitHub 레포)
3. /npd:plan     → 기획 단계 (PO·서비스기획자·아키텍트·도메인전문가·AI엔지니어 협업)
4. /npd:design   → 설계 단계 (아키텍트·AI엔지니어 협업)
5. /npd:develop  → 개발 단계 (백엔드·프론트엔드·AI엔지니어·QA 협업)
6. /npd:deploy   → 배포 단계 (DevOps 엔지니어)
7. /npd:cicd     → CI/CD 파이프라인 구축 단계 (DevOps 엔지니어)
```

### 명령어 목록

| 명령어 | 설명 |
|--------|------|
| `/npd:prepare` | 로컬 개발 환경 사전준비 (기본 프로그램, Claude Code + OMC 설치 안내) |
| `/npd:help` | 이 도움말 출력 |
| `/npd:create` | 새 프로젝트 생성 (모노레포 + domain-expert 생성 + GitHub 레포) |
| `/npd:plan` | 기획 단계 AI 협업 (PO·서비스기획자·아키텍트·도메인전문가·AI엔지니어) |
| `/npd:design` | 설계 단계 AI 협업 (아키텍트·AI엔지니어) |
| `/npd:develop` | 개발 단계 AI 협업 (백엔드·프론트엔드·AI엔지니어·QA) |
| `/npd:deploy` | 수동 배포 단계 AI 협업 (DevOps 엔지니어) |
| `/npd:cicd` | 자동 배포 단계 AI 협업 (DevOps 엔지니어) |
| `/npd:design-physical-architecture` | 물리 아키텍처 설계 |

### 시작 하기
1.개발할 프로젝트 디렉토리 생성    
```
cd ~/workspace   
mkdir {project directory} 
cd {project directory}
```
2.Claude Code 또는 Cursor 실행   
Claude Code 실행: 
```
cy 
```

Cursor 실행  
```
cursor .
```
  
3.로컬 개발 환경 사전준비 체크 
```
/npd:prepare
```

4. 프로젝트 초기화 명령 수행    
```
/npd:create
```

5.기획-설계-개발-배포 스킬 수행    
이후 각 단계 명령어를 실행하여 작업 수행      
  
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

## 워크플로우 
각 이미지를 새로운 탭에 열어 확대하여 보십시오.  

- [사전준비 체크](docs/workflow-images/01.prepare.png)
- [프로젝트 초기화](docs/workflow-images/02.create.png)
- [기획](docs/workflow-images/03.plan.png)
- [설계](docs/workflow-images/04.design.png)
- 개발: 
  - [전체](docs/workflow-images/05.develop.png)
  - [개발키트(설계서 요약) 생성](docs/workflow-images/05.develop-1.devkit.png)
  - [개발키트 생성](docs/workflow-images/05.develop-2.prepare.png)
  - [백엔드/프론트엔드/AI 개발 및 단위 테스트](docs/workflow-images/05.develop-3.dev.png)
  - [백엔드/프론트엔드/AI 통합 및 시스템 테스트](docs/workflow-images/05.develop-4.integration.png)
  - [E2E 테스트 및 완료](docs/workflow-images/05.develop-5.test.png)
- [수동배포](docs/workflow-images/06.deploy.png)
- 자동배포: 
  - [전체](docs/workflow-images/07.cicd.png)
  - [도구셋업](docs/workflow-images/07.cicd-1.setup_tools.png)
  - [매니페스트 레포지토리 생성](docs/workflow-images/07.cicd-2.manifest_repo.png)
  - [파이프라인 개발](docs/workflow-images/07.cicd-3.pipeline.png)

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
