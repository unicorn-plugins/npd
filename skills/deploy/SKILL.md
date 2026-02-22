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

## 에이전트 호출 규칙

| 에이전트 | FQN |
|----------|-----|
| devops-engineer | `npd:devops-engineer:devops-engineer` |

### 프롬프트 조립

1. `agents/{agent-name}/`에서 3파일 로드 (AGENT.md + agentcard.yaml + tools.yaml)
2. `gateway/runtime-mapping.yaml` 참조하여 구체화:
   - **모델 구체화**: agentcard.yaml의 `tier` → `tier_mapping`에서 모델 결정
   - **툴 구체화**: tools.yaml의 추상 도구 → `tool_mapping`에서 실제 도구 결정
   - **금지액션 구체화**: agentcard.yaml의 `forbidden_actions` → `action_mapping`에서 제외할 실제 도구 결정
   - **최종 도구** = (구체화된 도구) - (제외 도구)
3. 프롬프트 조립: 공통 정적(runtime-mapping) → 에이전트별 정적(3파일) → 인격(persona) → 동적(작업 지시)
4. `Task(subagent_type=FQN, model=구체화된 모델, prompt=조립된 프롬프트)` 호출

## Step 0. 진행 모드 선택

배포 워크플로우 시작 전, 각 단계별 승인 여부를 선택합니다.

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

## 배포 환경 선택

사용자에게 배포 환경을 확인하여 적절한 가이드를 참조함.

### 배포 대상 클러스터

| 옵션 | 설명 | 참조 가이드 (K8s 배포) |
|------|------|----------------------|
| AKS (Azure) | Azure Kubernetes Service 클러스터 배포 | `deploy-k8s-back.md`, `deploy-k8s-front.md` |
| Minikube | Minikube/Generic K8s 클러스터 배포 (SSH 터널링) | `deploy-k8s-back-minikube.md`, `deploy-k8s-front-minikube.md` |

### CI/CD 파이프라인 유형

| 옵션 | 설명 | 참조 가이드 |
|------|------|------------|
| GitHub Actions (AKS) | Azure 기반 GitHub Actions CI/CD | `deploy-actions-cicd-back.md`, `deploy-actions-cicd-front.md` |
| GitHub Actions (Minikube) | Minikube/Generic K8s 대상 GitHub Actions CI/CD (SSH 터널링, Docker Hub) | `deploy-actions-cicd-back-minikube.md`, `deploy-actions-cicd-front-minikube.md` |
| Jenkins | Jenkins + Podman 기반 CI/CD 파이프라인 | `deploy-jenkins-cicd-back.md`, `deploy-jenkins-cicd-front.md` |
| ArgoCD | GitOps 방식 CI/CD 분리 (매니페스트 레포지토리 활용) | `deploy-argocd-cicd.md` |

### 환경 선택 분기 규칙

1. `[실행정보]`에 `ACR_NAME` 또는 `AKS_CLUSTER`가 있으면 **AKS** 경로 선택
2. `[실행정보]`에 `VM_IP` 또는 `MINIKUBE_IP`가 있으면 **Minikube** 경로 선택
3. `[실행정보]`에 `JENKINS_GIT_CREDENTIALS`가 있으면 **Jenkins** CI/CD 추가 구성
4. `[실행정보]`에 `MANIFEST_REPO_URL`이 있으면 **ArgoCD** CI/CD 추가 구성
5. 명시적 지정이 없으면 사용자에게 확인 후 진행

## 워크플로우

### Step 1. 컨테이너 이미지 빌드 → Agent: devops-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/deploy/build-image-back.md`, `resources/guides/deploy/build-image-front.md` 참조
- **TASK**: 백엔드와 프론트엔드 Dockerfile을 작성하고 컨테이너 이미지를 빌드
- **EXPECTED OUTCOME**: Dockerfile 생성, 이미지 빌드 성공

### Step 2. 컨테이너 실행 검증 → Agent: devops-engineer (`/oh-my-claudecode:ultraqa` 활용)

- **GUIDE**: `resources/guides/deploy/run-container-guide-back.md`, `resources/guides/deploy/run-container-guide-front.md` 참조
- **TASK**: 빌드된 이미지로 컨테이너를 실행하여 정상 동작 확인
- **EXPECTED OUTCOME**: 백엔드·프론트엔드 컨테이너 정상 실행 확인

### Step 3. Kubernetes 배포 → Agent: devops-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**:
  - AKS: `resources/guides/deploy/deploy-k8s-back.md`, `resources/guides/deploy/deploy-k8s-front.md`
  - Minikube: `resources/guides/deploy/deploy-k8s-back-minikube.md`, `resources/guides/deploy/deploy-k8s-front-minikube.md`
- **TASK**: K8s Deployment, Service, Ingress 매니페스트를 작성하고 배포
- **EXPECTED OUTCOME**: `deploy/k8s/` 매니페스트 파일 생성, 배포 성공

### Step 4. CI/CD 파이프라인 구성 → Agent: devops-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**:
  - GitHub Actions (AKS): `resources/guides/deploy/deploy-actions-cicd-back.md`, `resources/guides/deploy/deploy-actions-cicd-front.md`
  - GitHub Actions (Minikube): `resources/guides/deploy/deploy-actions-cicd-back-minikube.md`, `resources/guides/deploy/deploy-actions-cicd-front-minikube.md`
  - Jenkins: `resources/guides/deploy/deploy-jenkins-cicd-back.md`, `resources/guides/deploy/deploy-jenkins-cicd-front.md`
  - ArgoCD: `resources/guides/deploy/deploy-argocd-cicd.md`
- **TASK**: 선택된 CI/CD 유형에 따라 파이프라인을 구성
- **EXPECTED OUTCOME**: CI/CD 파이프라인 설정 파일 생성

#### Step 4 산출물 (CI/CD 유형별)

| CI/CD 유형 | 산출물 |
|-----------|--------|
| GitHub Actions (AKS) | `.github/workflows/backend-cicd.yaml`, `.github/workflows/frontend-cicd.yaml`, `.github/kustomize/*`, `.github/config/*` |
| GitHub Actions (Minikube) | `.github/workflows/backend-cicd.yaml`, `.github/workflows/frontend-cicd.yaml`, `.github/kustomize/*` |
| Jenkins | `deployment/cicd/Jenkinsfile` (백엔드/프론트엔드), `deployment/cicd/kustomize/*`, `deployment/cicd/config/*` |
| ArgoCD | `deployment/cicd/Jenkinsfile_ArgoCD` 또는 `.github/workflows/*_ArgoCD.yaml`, 매니페스트 레포지토리 구성 |

### Step 5. 배포 완료 보고

```
## 배포 완료

### 배포 환경
- 클러스터 유형: {AKS / Minikube}
- CI/CD 유형: {GitHub Actions / Jenkins / ArgoCD}

### 배포 결과
- 백엔드 컨테이너: 빌드 및 배포 완료
- 프론트엔드 컨테이너: 빌드 및 배포 완료
- K8s 배포: 완료
- CI/CD 파이프라인: 구성 완료

### 접속 정보
- 백엔드 API: {URL}
- 프론트엔드: {URL}

### 구성된 파이프라인 정보
- 파이프라인 유형: {유형}
- 환경별 배포: dev / staging / prod
- SonarQube 연동: {연동 여부}
```

## 완료 조건

- [ ] 모든 워크플로우 단계가 정상 완료됨
- [ ] Dockerfile(백엔드/프론트엔드)이 생성되고 빌드 성공
- [ ] K8s 매니페스트(`deploy/k8s/`)가 생성되고 배포 성공
- [ ] CI/CD 파이프라인이 선택된 유형에 맞게 구성됨
- [ ] 검증 프로토콜을 통과함
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (Dockerfile, K8s 매니페스트, CI/CD 설정 파일)
2. 산출물 내용 품질 검증 (컨테이너 빌드 성공, 로컬 실행 정상, 배포 정상)
3. 이전 Phase 산출물과의 일관성 확인 (개발 산출물 → 배포 산출물 연계)
4. CI/CD 파이프라인 설정 검증 (환경별 Kustomize overlay 구성, 시크릿 관리 방식)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.
