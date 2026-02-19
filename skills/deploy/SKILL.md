---
name: deploy
description: 배포 단계 AI 협업 — DevOps 엔지니어가 컨테이너 빌드·K8s 배포·CI/CD 파이프라인 구성 수행
type: orchestrator
user-invocable: true
allowed-tools: Read, Write, Bash, Task
---

# Deploy

[NPD Deploy 활성화]

## 목표

DevOps 엔지니어가 컨테이너 이미지 빌드 → 컨테이너 실행 →
Kubernetes 배포 → CI/CD 파이프라인 구성 순서로 배포 환경을 구축함.

## 선행 조건

- `/npd:develop` 완료 (소스코드 존재)

## 워크플로우

### Step 1. 컨테이너 이미지 빌드 → Agent: devops-engineer

- **TASK**: 백엔드와 프론트엔드 Dockerfile을 작성하고 컨테이너 이미지를 빌드
- **EXPECTED OUTCOME**: `backend/Dockerfile`, `frontend/Dockerfile` 생성 및 빌드 성공
- **MUST DO**: `resources/guides/deploy/build-image-back.md`, `build-image-front.md` 참조
- **MUST NOT DO**: 빌드 실패 상태로 다음 단계 진행하지 않을 것
- **CONTEXT**: CLAUDE.md 기술스택, 프로젝트 디렉토리 구조

### Step 2. 컨테이너 실행 검증 → Agent: devops-engineer

- **TASK**: 빌드된 이미지로 컨테이너를 실행하여 정상 동작 확인
- **EXPECTED OUTCOME**: 백엔드·프론트엔드 컨테이너 정상 실행 확인
- **MUST DO**: `resources/guides/deploy/run-container-guide-back.md`, `run-container-guide-front.md` 참조
- **MUST NOT DO**: 로컬 검증 없이 K8s 배포를 진행하지 않을 것
- **CONTEXT**: 빌드된 Docker 이미지명

### Step 3. Kubernetes 배포 → Agent: devops-engineer

- **TASK**: K8s Deployment, Service, Ingress 매니페스트를 작성하고 배포
- **EXPECTED OUTCOME**: `deploy/k8s/` 디렉토리에 매니페스트 파일 생성 및 배포 성공
- **MUST DO**: `resources/guides/deploy/deploy-k8s-back.md`, `deploy-k8s-front.md` 참조
- **MUST NOT DO**: 컨테이너 실행 검증 없이 K8s 배포를 진행하지 않을 것
- **CONTEXT**: Docker 이미지명, 서비스 포트 정보

### Step 4. CI/CD 파이프라인 구성 → Agent: devops-engineer

- **TASK**: GitHub Actions 워크플로우를 작성하여 자동 빌드·테스트·배포 파이프라인 구성
- **EXPECTED OUTCOME**: `.github/workflows/backend.yml`, `.github/workflows/frontend.yml` 생성
- **MUST DO**: `resources/guides/deploy/deploy-actions-cicd-back.md`, `deploy-actions-cicd-front.md` 참조. main 브랜치 push 시 자동 배포 트리거
- **MUST NOT DO**: 시크릿(GITHUB_TOKEN 등)을 워크플로우 파일에 하드코딩하지 않을 것
- **CONTEXT**: K8s 클러스터 정보, 컨테이너 레지스트리 정보

### Step 5. 배포 완료 보고

```
## 배포 완료

### 배포 결과
- 백엔드 컨테이너: ✅ 빌드 및 배포 완료
- 프론트엔드 컨테이너: ✅ 빌드 및 배포 완료
- K8s 배포: ✅ 완료
- CI/CD 파이프라인: ✅ 구성 완료

### 접속 정보
- 백엔드 API: {URL}
- 프론트엔드: {URL}
```

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | 컨테이너 빌드 → 로컬 실행 검증 → K8s 배포 → CI/CD 순서를 반드시 준수할 것 |
| 2 | 각 단계 실패 시 다음 단계로 진행하지 않고 오류를 보고할 것 |
| 3 | 모든 시크릿은 환경변수 또는 K8s Secret으로 관리할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 로컬 검증 없이 K8s 배포를 진행하지 않을 것 |
| 2 | 시크릿을 파일에 하드코딩하지 않을 것 |

## 검증 체크리스트

- [ ] 백엔드 Dockerfile 생성 및 빌드 성공
- [ ] 프론트엔드 Dockerfile 생성 및 빌드 성공
- [ ] 컨테이너 로컬 실행 검증 완료
- [ ] K8s 매니페스트 생성 및 배포 완료
- [ ] GitHub Actions 워크플로우 생성 완료
- [ ] 시크릿 하드코딩 없음
- [ ] 배포 완료 보고 생성