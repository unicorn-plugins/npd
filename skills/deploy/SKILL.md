---
name: deploy
description: 배포 단계 AI 협업 — DevOps 엔지니어가 컨테이너 빌드·K8s 배포·CI/CD 파이프라인 구성 수행
type: orchestrator
user-invocable: true
---

# Deploy

[NPD Deploy 활성화]

## 목표

DevOps 엔지니어가 컨테이너 이미지 빌드 → 컨테이너 실행 →
Kubernetes 배포 → CI/CD 파이프라인 구성 순서로 배포 환경을 구축함.

주의사항: 중간 단계부터 시작할 때도 각 단계별 승인 여부를 선택하는 Step 0은 항상 수행하여 진행 모드를 설정해야 합니다.

## 선행 조건

- `/npd:develop` 완료 (소스코드 존재)

## 에이전트 호출 규칙

| 에이전트 | FQN |
|----------|-----|
| architect | `npd:architect:architect` |
| ai-engineer | `npd:ai-engineer:ai-engineer` |
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

## Step 1. 배포 사전 준비

배포에 필요한 로컬 도구와 VM 원격 도구를 자동으로 설치하고, VM 접속 정보를 수집한다.

- **GUIDE**: `resources/guides/setup/deploy-pre-setup.md` 참조
- **TASK**: CLOUD 판단 → 로컬 도구 설치(kubectl, kubens, helm, Cloud CLI) → Cloud CLI 로그인 확인 → VM 생성 안내 → `~/.ssh/config` 파싱 → SSH 접속 테스트 → VM 원격 도구 설치(Cloud CLI, Docker, kubectl, kubens, helm, JDK)
- **EXPECTED OUTCOME**: 로컬/VM 도구 설치 완료, VM 접속 정보(`VM.HOST`, `VM.IP`, `VM.USERID`, `VM.KEY파일`) 수집

### 1-1. CLOUD 판단

`CLAUDE.md`의 `## NPD 워크플로우 상태 > ### design`에서 `CLOUD` 값을 읽는다. 없으면:

<!--ASK_USER-->
{"title":"Cloud 서비스 선택","questions":[
  {"question":"배포할 Cloud 서비스를 선택하세요.","type":"radio","options":["AWS","Azure","GCP"]}
]}
<!--/ASK_USER-->

### 1-2. 로컬 도구 자동 설치

가이드의 1-2절 참조. OS 감지 후 kubectl, kubens/kubectx, helm, {CLOUD} CLI를 미설치분만 자동 설치한다.

### 1-3. Cloud CLI 로그인 확인

가이드의 1-3절 참조. 로그인이 안 되어 있으면:

<!--ASK_USER-->
{"title":"Cloud CLI 로그인 확인","questions":[
  {"question":"{CLOUD} CLI 로그인이 필요합니다.\n\n로그인 완료 후 알려주세요.\n참고: https://github.com/unicorn-plugins/npd/blob/main/resources/guides/setup/prepare.md#cloud-cli-설치-및-로그인","type":"radio","options":["로그인 완료"]}
]}
<!--/ASK_USER-->

### 1-4. VM 생성 안내

<!--ASK_USER-->
{"title":"VM 준비 확인","questions":[
  {"question":"컨테이너를 실행할 VM이 {CLOUD}에 준비되어 있나요?\n\nVM이 있고 ~/.ssh/config에 접속 정보가 등록되어 있어야 합니다.","type":"radio","options":["준비 완료","아직 없음"]}
]}
<!--/ASK_USER-->

**"아직 없음"** 선택 시: 가이드의 1-4절 참조. {CLOUD}별 VM 생성 URL(https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-vm.md) 안내 + `~/.ssh/config` 등록 안내 후 완료 대기:

<!--ASK_USER-->
{"title":"VM 생성 완료 확인","questions":[
  {"question":"VM 생성과 ~/.ssh/config 등록이 완료되면 알려주세요.","type":"radio","options":["완료"]}
]}
<!--/ASK_USER-->

### 1-5. ~/.ssh/config 파싱

가이드의 1-5절 참조. `~/.ssh/config`에서 Host 엔트리를 추출하여 사용자에게 선택하게 한다:

<!--ASK_USER-->
{"title":"배포 대상 VM 선택","questions":[
  {"question":"~/.ssh/config에서 배포 대상 VM의 Host를 선택하세요.","type":"radio","options":["{파싱된 Host alias 목록}"]}
]}
<!--/ASK_USER-->

선택된 Host에서 VM.HOST, VM.IP, VM.USERID, VM.KEY파일을 추출한다.

### 1-6. SSH 접속 테스트

가이드의 1-6절 참조. 실패 시:

<!--ASK_USER-->
{"title":"SSH 접속 실패","questions":[
  {"question":"SSH 접속에 실패했습니다. ~/.ssh/config의 접속 정보를 확인하고 다시 시도하시겠습니까?\n\n에러: {에러 메시지}","type":"radio","options":["다시 시도","건너뛰기 (VM 도구 수동 설치)"]}
]}
<!--/ASK_USER-->

### 1-7. VM 원격 도구 설치

가이드의 1-7절 참조. SSH로 VM에 접속하여 미설치 도구를 자동 설치한다.

### 1-8. 완료 보고

가이드의 1-8절 템플릿으로 로컬/VM 설치 도구 목록 + VM 접속 방법(`ssh {VM_HOST_ALIAS}`)을 보고한다.

## 배포 환경 선택

사용자에게 배포 환경을 확인하여 적절한 가이드를 참조함.

### 이미지 레지스트리 및 VM 정보 수집

Step 3(컨테이너 실행 검증) 이전에 이미지 레지스트리 유형과 VM 접속 정보를 수집한다.
`{CLOUD}` 값(CLAUDE.md에서 읽음)에 따라 Docker Hub와 해당 Cloud의 이미지 레지스트리만 선택지로 표시한다.

#### 1차 질문 (공통)

<!--ASK_USER-->
{"title":"이미지 레지스트리 선택","questions":[
  {"question":"이미지 레지스트리 유형을 선택하세요.","type":"radio","options":["Docker Hub","{CLOUD 레지스트리}"]}
]}
<!--/ASK_USER-->

> **{CLOUD 레지스트리} 매핑**: Azure → `Azure ACR`, AWS → `AWS ECR`, GCP → `Google GCR (Artifact Registry)`

#### 2차 질문 (유형별 조건 분기)

1차 질문에서 선택된 레지스트리 유형에 따라 추가 정보를 수집한다.

- **Docker Hub** 선택 시:
<!--ASK_USER-->
{"title":"Docker Hub 정보","questions":[
  {"question":"Docker Hub Organization 또는 Username을 입력하세요.","type":"text","placeholder":"myorg"},
  {"question":"Docker Hub Access Token(PAT)을 입력하세요.","type":"text","placeholder":"dckr_pat_xxxxx"}
]}
<!--/ASK_USER-->

- **AWS ECR** 선택 시:
<!--ASK_USER-->
{"title":"AWS ECR 정보","questions":[
  {"question":"AWS 리전을 입력하세요.","type":"text","placeholder":"ap-northeast-2"},
  {"question":"AWS 계정 ID를 입력하세요.","type":"text","placeholder":"123456789012"}
]}
<!--/ASK_USER-->

- **Azure ACR** 선택 시:
<!--ASK_USER-->
{"title":"Azure ACR 정보","questions":[
  {"question":"ACR 이름을 입력하세요.","type":"text","placeholder":"acrdigitalgarage01"}
]}
<!--/ASK_USER-->

- **Google GCR (Artifact Registry)** 선택 시:
<!--ASK_USER-->
{"title":"Google Artifact Registry 정보","questions":[
  {"question":"GCP 프로젝트 ID를 입력하세요.","type":"text","placeholder":"my-project-id"},
  {"question":"리전을 입력하세요.","type":"text","placeholder":"asia-northeast3"},
  {"question":"리포지토리 이름을 입력하세요.","type":"text","placeholder":"my-repo"}
]}
<!--/ASK_USER-->

#### [실행정보] 조립 규칙

수집된 정보를 아래 템플릿에 따라 `[실행정보]`로 조립한다.
조립된 `[실행정보]` 블록은 이후 에이전트 호출 시 **프롬프트의 동적(작업 지시) 영역에 텍스트로 포함**하여 전달한다. 에이전트는 별도 컨텍스트에서 실행되므로, `Task(prompt=...)` 호출 시 `[실행정보]` 블록 전문을 반드시 포함해야 가이드 내 `${REGISTRY_URL}`, `${IMG_ID}` 등의 변수를 치환할 수 있다.

> VM 접속 정보는 Step 1(배포 사전 준비)에서 `~/.ssh/config`를 파싱하여 자동 수집된다.
> 사용자가 선택한 Host alias의 HostName, User, IdentityFile 값이 매핑된다.

**Docker Hub:**
```
[실행정보]
- 레지스트리유형: DockerHub
- IMG_REG: docker.io
- IMG_ORG: {Organization/Username}
- IMG_ID: {Organization/Username}
- IMG_PW: {Access Token}
- REGISTRY_URL: docker.io/{IMG_ORG}
- VM
  - HOST: {~/.ssh/config Host alias}
  - KEY파일: {~/.ssh/config IdentityFile}
  - USERID: {~/.ssh/config User}
  - IP: {~/.ssh/config HostName}
```

**AWS ECR:**
```
[실행정보]
- 레지스트리유형: ECR
- ECR_ACCOUNT: {AWS 계정 ID}
- ECR_REGION: {AWS 리전}
- REGISTRY_URL: {ECR_ACCOUNT}.dkr.ecr.{ECR_REGION}.amazonaws.com/{ROOT}
- VM
  - HOST: {~/.ssh/config Host alias}
  - KEY파일: {~/.ssh/config IdentityFile}
  - USERID: {~/.ssh/config User}
  - IP: {~/.ssh/config HostName}
```

**Azure ACR:**
```
[실행정보]
- 레지스트리유형: ACR
- ACR명: {ACR 이름}
- REGISTRY_URL: {ACR명}.azurecr.io/{ROOT}
- VM
  - HOST: {~/.ssh/config Host alias}
  - KEY파일: {~/.ssh/config IdentityFile}
  - USERID: {~/.ssh/config User}
  - IP: {~/.ssh/config HostName}
```

**Google GCR:**
```
[실행정보]
- 레지스트리유형: GCR
- GCR_PROJECT: {프로젝트 ID}
- GCR_REGION: {리전}
- GCR_REPO: {리포지토리 이름}
- REGISTRY_URL: {GCR_REGION}-docker.pkg.dev/{GCR_PROJECT}/{GCR_REPO}
- VM
  - HOST: {~/.ssh/config Host alias}
  - KEY파일: {~/.ssh/config IdentityFile}
  - USERID: {~/.ssh/config User}
  - IP: {~/.ssh/config HostName}
```

> `{ROOT}`는 CLAUDE.md의 시스템명을 참조하여 결정한다.

### 배포 대상 클러스터

| 옵션 | 설명 | 참조 가이드 (K8s 배포) |
|------|------|----------------------|
| AKS (Azure) | Azure Kubernetes Service 클러스터 배포 | `deploy-k8s-back.md`, `deploy-k8s-front.md`, `deploy-k8s-ai.md` |
| Minikube | Minikube/Generic K8s 클러스터 배포 (SSH 터널링) | `deploy-k8s-back-minikube.md`, `deploy-k8s-front-minikube.md`, `deploy-k8s-ai-minikube.md` |

### CI/CD 파이프라인 유형

| 옵션 | 설명 | 참조 가이드 |
|------|------|------------|
| GitHub Actions (AKS) | Azure 기반 GitHub Actions CI/CD | `deploy-actions-cicd-back.md`, `deploy-actions-cicd-front.md` |
| GitHub Actions (Minikube) | Minikube/Generic K8s 대상 GitHub Actions CI/CD (SSH 터널링, Docker Hub) | `deploy-actions-cicd-back-minikube.md`, `deploy-actions-cicd-front-minikube.md` |
| Jenkins | Jenkins + Podman 기반 CI/CD 파이프라인 | `deploy-jenkins-cicd-back.md`, `deploy-jenkins-cicd-front.md` |
| ArgoCD | GitOps 방식 CI/CD 분리 (매니페스트 레포지토리 활용) | `deploy-argocd-cicd.md` |

### 환경 선택 분기 규칙

1. `[실행정보]`에 `레지스트리유형`이 있으면 해당 유형에 맞는 이미지 경로 체계(`REGISTRY_URL`)를 사용
2. `[실행정보]`에 `ACR_NAME` 또는 `AKS_CLUSTER`가 있으면 **AKS** 경로 선택 (`레지스트리유형: ACR`과 동일 효과)
3. `[실행정보]`에 `VM_IP` 또는 `MINIKUBE_IP`가 있으면 **Minikube** 경로 선택
4. `[실행정보]`에 `JENKINS_GIT_CREDENTIALS`가 있으면 **Jenkins** CI/CD 추가 구성
5. `[실행정보]`에 `MANIFEST_REPO_URL`이 있으면 **ArgoCD** CI/CD 추가 구성
6. 명시적 지정이 없으면 사용자에게 확인 후 진행

### Phase 2 다운스트림 영향 (별도 계획 필요)

이미지 레지스트리 4유형 확대에 따라 아래 가이드의 후속 수정이 필요하다:

| 가이드 | 현재 상태 | 필요 작업 |
|--------|----------|----------|
| `deploy-k8s-back.md` | ACR 전용 (`{ACR명}.azurecr.io`) | 4유형 이미지 경로 + ImagePullSecret 분기 |
| `deploy-k8s-front.md` | ACR 전용 | 동일 |
| `deploy-k8s-ai.md` | ACR 전용 | 동일 |
| `deploy-actions-cicd-back.md` | ACR 전용 (`{ACR_NAME}.azurecr.io`) | 4유형 레지스트리 로그인/푸시 분기 |
| `deploy-actions-cicd-front.md` | ACR 전용 | 동일 |
| `deploy-jenkins-cicd-back.md` | IMG_REG/IMG_ORG 패턴 | 4유형 레지스트리 인증/푸시 분기 확인 필요 |
| `deploy-jenkins-cicd-front.md` | IMG_REG/IMG_ORG 패턴 | 동일 |
| `deploy-argocd-cicd.md` | 레지스트리 참조 포함 | 4유형 레지스트리 경로 확인 필요 |

## 워크플로우

### Step 2. 컨테이너 이미지 빌드 & 푸시 → Agent: devops-engineer (`/ralph` 활용)

- **GUIDE**: `resources/guides/deploy/build-image-back.md`, `resources/guides/deploy/build-image-front.md`, `resources/guides/deploy/build-image-ai.md` 참조
- **CONTEXT**: 조립된 `[실행정보]` 블록을 프롬프트에 포함
- **TASK**: 백엔드, 프론트엔드, AI 서비스 Dockerfile을 작성하고 컨테이너 이미지를 빌드하고 푸시
- **EXPECTED OUTCOME**: Dockerfile 생성, 이미지 빌드 성공, 이미지 푸시 성공

#### Step 2-1. 산출물 커밋 & 동기화

Step 2 완료 후, VM에서 생성된 산출물(Dockerfile, build guide 등)을 원격 저장소에 반영하고 로컬과 동기화한다.

**VM에서 커밋 & 푸시:**
```bash
ssh {VM.HOST}
cd ~/workspace/{ROOT}
git add -A
git commit -m "deploy: Step 2 산출물 (Dockerfile, build-image guide)"
git push
```

**Private 저장소인 경우** (PAT 기반 push):
```bash
# PAT 입력 (shell history에 남지 않도록 read -s 사용)
read -s GIT_PAT
git remote set-url origin https://${GIT_PAT}@github.com/{org}/{repo}.git
git push

# 보안 정리: push 후 PAT 제거
git remote set-url origin https://github.com/{org}/{repo}.git
unset GIT_PAT
```

> PAT는 `build-image-*.md`의 clone 단계에서 사용한 것과 동일한 방식이다.
> 로컬에서 `gh auth token`으로 획득할 수 있다.

**로컬 동기화:**
```bash
git pull
```

### Step 3. 컨테이너 실행 검증 → Agent: devops-engineer (`/ultraqa` 활용)

#### Step 3-0. VM 백킹서비스 배포 (선행)

- **GUIDE**: `resources/guides/deploy/backing-service-deploy.md` 참조
- **CONTEXT**: 조립된 `[실행정보]` 블록을 프롬프트에 포함
- **TASK**: VM에 SSH 접속하여 docker-compose로 백킹서비스(DB, Redis, MQ)를 기동하고 health check 수행
- **EXPECTED OUTCOME**: 모든 백킹서비스 healthy 확인, `docs/deploy/backing-service-result.md` 작성

> 백킹서비스가 정상 기동된 후에야 아래 애플리케이션 컨테이너 실행이 가능하다.

#### Step 3-1. 애플리케이션 컨테이너 실행

- **GUIDE**: `resources/guides/deploy/run-container-guide-back.md`, `resources/guides/deploy/run-container-guide-front.md`, `resources/guides/deploy/run-container-guide-ai.md` 참조
- **CONTEXT**: 조립된 `[실행정보]` 블록을 프롬프트에 포함
- **TASK**: 빌드된 이미지로 컨테이너를 실행하여 정상 동작 확인
- **EXPECTED OUTCOME**: 백엔드·프론트엔드·AI 서비스 컨테이너 정상 실행 확인

#### Step 3-2. 산출물 커밋 & 동기화

Step 3 완료 후, VM에서 생성된 산출물(결과 보고서, 컨테이너 실행 가이드 등)을 원격 저장소에 반영하고 로컬과 동기화한다.

**VM에서 커밋 & 푸시:**
```bash
ssh {VM.HOST}
cd ~/workspace/{ROOT}
git add -A
git commit -m "deploy: Step 3 산출물 (backing-service-result, run-container-guide)"
git push
```

**Private 저장소인 경우** — Step 2-1과 동일한 PAT 기반 push 방식 사용.

**로컬 동기화:**
```bash
git pull
```

### Step 4. 물리 아키텍처 설계 → Agent: architect (`/ralph` 활용)

- **GUIDE**: `resources/guides/design/physical-architecture-design.md` 참조
- **TASK**: 개발·운영 환경별 K8s 인프라·네트워크·배포 구조를 Mermaid 다이어그램과 함께 설계하고 문법 검증 수행. Cloud 환경은 `docs/design/high-level-architecture.md`의 Cloud 서비스 선택을 참조
  - **AI 검토**: 설계 완료 후 ai-engineer가 AI 서비스 Pod 리소스, GPU/메모리 요구사항, AI 외부 API 네트워크 설정을 검토
- **EXPECTED OUTCOME**: `docs/design/physical/physical-architecture.md`, `physical-architecture-dev.md`, `physical-architecture-prod.md`, `physical-architecture-dev.mmd`, `physical-architecture-prod.mmd`, `network-dev.mmd`, `network-prod.mmd`

### Step 5. Kubernetes 배포 → Agent: devops-engineer (`/ralph` 활용)

- **GUIDE**:
  - AKS: `resources/guides/deploy/deploy-k8s-back.md`, `resources/guides/deploy/deploy-k8s-front.md`, `resources/guides/deploy/deploy-k8s-ai.md`
  - Minikube: `resources/guides/deploy/deploy-k8s-back-minikube.md`, `resources/guides/deploy/deploy-k8s-front-minikube.md`, `resources/guides/deploy/deploy-k8s-ai-minikube.md`
- **CONTEXT**: 조립된 `[실행정보]` 블록을 프롬프트에 포함
- **TASK**: K8s Deployment, Service, Ingress 매니페스트를 작성하고 배포
- **EXPECTED OUTCOME**: `deploy/k8s/` 매니페스트 파일 생성, 배포 성공

### Step 6. CI/CD 파이프라인 구성 → Agent: devops-engineer (`/ralph` 활용)

- **GUIDE**:
  - GitHub Actions (AKS): `resources/guides/deploy/deploy-actions-cicd-back.md`, `resources/guides/deploy/deploy-actions-cicd-front.md`
  - GitHub Actions (Minikube): `resources/guides/deploy/deploy-actions-cicd-back-minikube.md`, `resources/guides/deploy/deploy-actions-cicd-front-minikube.md`
  - Jenkins: `resources/guides/deploy/deploy-jenkins-cicd-back.md`, `resources/guides/deploy/deploy-jenkins-cicd-front.md`
  - ArgoCD: `resources/guides/deploy/deploy-argocd-cicd.md`
- **CONTEXT**: 조립된 `[실행정보]` 블록을 프롬프트에 포함
- **TASK**: 선택된 CI/CD 유형에 따라 파이프라인을 구성
- **EXPECTED OUTCOME**: CI/CD 파이프라인 설정 파일 생성

#### Step 6 산출물 (CI/CD 유형별)

| CI/CD 유형 | 산출물 |
|-----------|--------|
| GitHub Actions (AKS) | `.github/workflows/backend-cicd.yaml`, `.github/workflows/frontend-cicd.yaml`, `.github/kustomize/*`, `.github/config/*` |
| GitHub Actions (Minikube) | `.github/workflows/backend-cicd.yaml`, `.github/workflows/frontend-cicd.yaml`, `.github/kustomize/*` |
| Jenkins | `deployment/cicd/Jenkinsfile` (백엔드/프론트엔드), `deployment/cicd/kustomize/*`, `deployment/cicd/config/*` |
| ArgoCD | `deployment/cicd/Jenkinsfile_ArgoCD` 또는 `.github/workflows/*_ArgoCD.yaml`, 매니페스트 레포지토리 구성 |

### Step 7. 배포 완료 보고

```
## 배포 완료

### 배포 환경
- 클러스터 유형: {AKS / Minikube}
- CI/CD 유형: {GitHub Actions / Jenkins / ArgoCD}

### 물리 아키텍처
- physical/physical-architecture.md — 마스터 설계서
- physical/physical-architecture-dev.md — 개발환경 설계서
- physical/physical-architecture-prod.md — 운영환경 설계서
- physical/physical-architecture-dev.mmd — 개발환경 다이어그램
- physical/physical-architecture-prod.mmd — 운영환경 다이어그램
- physical/network-dev.mmd — 개발환경 네트워크
- physical/network-prod.mmd — 운영환경 네트워크

### 배포 결과
- 백엔드 컨테이너: 빌드 및 배포 완료
- 프론트엔드 컨테이너: 빌드 및 배포 완료
- AI 서비스 컨테이너: 빌드 및 배포 완료
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

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |

## 완료 조건

- [ ] 모든 워크플로우 단계(Step 1~7)가 정상 완료됨
- [ ] VM 백킹서비스 배포 완료 (`docs/deploy/backing-service-result.md` 생성)
- [ ] 물리 아키텍처 설계서(`docs/design/physical/`)가 생성됨
- [ ] Dockerfile(백엔드/프론트엔드/AI 서비스)이 생성되고 빌드 성공
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
