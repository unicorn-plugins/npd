---
name: cicd  
description: CI/CD 파이프라인 구성 AI 협업 -- DevOps 엔지니어가 Jenkins/GitHub Actions CI + ArgoCD CD 파이프라인 구축  
type: orchestrator  
user-invocable: true  
---

# CI/CD

[NPD CI/CD 활성화]

## 목표

DevOps 엔지니어가 CI/CD 파이프라인 코드(Jenkinsfile, GitHub Actions Workflow, Kustomize 매니페스트)를 생성하고,  
ArgoCD GitOps 방식으로 CD를 분리하는 파이프라인을 구축한다.

주의사항: 중간 단계부터 시작할 때도 Step 0(사전 체크 + 모드 선택 + 정보 수집)은 항상 수행하여 진행 모드와 환경 정보를 설정해야 합니다.

## 선행 조건

- `/npd:deploy` Step 4(K8s 배포)까지 완료된 상태 (기존 K8s 매니페스트 `deployment/k8s/` 존재)
- CI/CD 도구 설치: Step 1에서 자동 설치 또는 사전 설치 완료 (CI 도구, SonarQube, ArgoCD, Image Registry Credential)

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

## 변수명 규약

가이드 파일에서 사용하는 서비스명 관련 플레이스홀더 규약:

| 플레이스홀더 | 출처 | 설명 |
|------------|------|------|
| `{SYSTEM_NAME}` | `[실행정보]` | 백엔드 시스템명 (settings.gradle의 rootProject.name) |
| `{FRONTEND_SERVICE}` | `[실행정보]` | 프론트엔드 서비스명 (package.json의 name). `package.json` 감지 시에만 포함 |
| `{AI_SERVICE}` | `[실행정보]` | AI 서비스명 (pyproject.toml의 [tool.poetry] name). `pyproject.toml` 감지 시에만 포함 |
| `{SERVICE_NAMES}` | `settings.gradle` 파싱 | 백엔드 서비스명 목록 (include 'common' 하위). `[실행정보]`에 포함되지 않으며, 에이전트가 settings.gradle에서 직접 파싱 |
| `{서비스명1}`, `{서비스명2}` ... | `{SERVICE_NAMES}`의 개별 항목 | 가이드 내 예시에서 사용하는 반복 표기 |
| `{PYTHON_VERSION}` | `pyproject.toml` 파싱 | Python 버전. `[tool.poetry.dependencies]`의 python 필드. 미감지 시 3.11 |

> **주의**: 가이드 파일마다 `{SERVICE_NAME1}` (밑줄 없음), `{SERVICE_NAME_1}` (밑줄 있음), `{서비스명1}` (한글), `{SERVICE_NAMEN}` (N번째를 의미하는 말줄임) 등이 혼용됩니다. 모두 동일하게 `{SERVICE_NAMES}`의 개별 항목을 의미합니다.

## 클라우드별 차이 처리 안내

- Jenkins, GitHub Actions 모두 **클라우드 무관하게 동일 가이드** 사용 (가이드 내 조건부 섹션으로 처리)
- 클라우드별 차이는 registry login 인증 방식뿐이며, `[실행정보]`의 `CLOUD` 값에 따라 가이드 내 조건부 섹션 적용
- `{IMG_REG}/{IMG_ORG}` 변수로 레지스트리 URL을 추상화하므로 build/push/manifest 업데이트 로직은 동일

## 가이드 선택 매트릭스

CI 도구에 따라 참조할 가이드 파일이 결정된다. **클라우드별 분기 불필요** — CI/CD 분리 후 클라우드별 차이는 registry login 1개 step뿐이므로, 가이드 내 조건부 섹션으로 처리한다. 모든 가이드는 `resources/guides/cicd/` 경로에 위치한다.

| CI 도구 | 백엔드 가이드 | 프론트엔드 가이드 | AI 서비스 가이드 |
|---------|-------------|----------------|----------------|
| Jenkins | `deploy-jenkins-cicd-back.md` | `deploy-jenkins-cicd-front.md` | `deploy-jenkins-cicd-ai.md` |
| GitHub Actions | `deploy-actions-cicd-back.md` | `deploy-actions-cicd-front.md` | `deploy-actions-cicd-ai.md` |

> **Step 1 가이드**: CI/CD 도구 사전 설치는 `cicd-pre-setup.md` 가이드를 참조한다 (CI 도구·클라우드 무관 공통).

## 에이전트 모드 매핑

| Step | 에이전트 모드 | 이유 |
|------|-------------|------|
| Step 0 | (orchestrator 직접) | 사용자 인터랙션 + 정보 수집 |
| Step 1 | `/ralph` | 클라우드별 사전작업 + CI/CD 도구 Helm 설치 자동화 |
| Step 2 | `/ralph` | 매니페스트 레포지토리 구성 + ArgoCD Application YAML 생성·등록 |
| Step 3 | `/ralph` | CI/CD 파이프라인 코드 생성 (빌드+푸시+manifest tag 업데이트) |
| Step 4 | (orchestrator 직접) | 완료 보고서 작성 |

### CI/CD 분리 핵심 원칙

> **CI의 책임**: 빌드 → 이미지 푸시 → **manifest repository의 YAML에서 image tag만 변경**  
> **CD의 책임**: ArgoCD가 manifest repository 변경을 감지하여 K8s에 자동 배포  
> **CI에서 kubectl apply 절대 금지**: CI 파이프라인은 K8s에 직접 배포하지 않는다.  
>
> 기존 CI 가이드(deploy-jenkins-cicd-*.md, deploy-actions-cicd-*.md)의 빌드·푸시 부분과  
> ArgoCD 가이드(deploy-argocd-cicd.md)의 manifest repo 업데이트 부분을 **하나의 파이프라인에 결합**하여  
> 처음부터 CI/CD가 분리된 파이프라인을 생성한다.  
> 별도의 `_ArgoCD` 변환 단계는 불필요하다.

## Step 0. 사전 체크 + 모드 선택 + 정보 수집

CI/CD 워크플로우 시작 전, hosts 파일 등록 확인, 진행 모드 선택, 사전 도구 확인, 환경 정보 수집을 수행한다.

### 0) hosts 파일 등록 확인

CI/CD 도구(Jenkins, SonarQube, ArgoCD) 웹 UI 접속을 위해 로컬 PC의 hosts 파일에 도메인이 등록되어 있어야 함.

<!--ASK_USER-->
{"title":"hosts 파일 등록 확인","questions":[
  {"question":"로컬 PC의 hosts 파일에 아래 항목이 등록되어 있나요?\n\n{WEB_SERVER_PUBLIC_IP}  myjenkins.io mysonar.io myargocd.io\n\n※ Windows: c:\\windows\\system32\\drivers\\etc\\hosts (관리자 권한으로 편집)\n※ Mac/Linux: /etc/hosts (sudo 권한으로 편집)","type":"radio","options":["등록 완료","아직 미등록"]}
]}
<!--/ASK_USER-->

- **등록 완료** 선택 시: 다음 단계 진행
- **아직 미등록** 선택 시: 아래 안내 후 등록 완료 대기
  - Windows: 메모장을 **관리자 권한으로 실행** → `c:\windows\system32\drivers\etc\hosts` 열기 → 아래 줄 추가 후 저장
  - Mac/Linux: `sudo vi /etc/hosts`로 아래 줄 추가 후 저장
  ```
  {WEB_SERVER_PUBLIC_IP}  myjenkins.io mysonar.io myargocd.io
  ```
  > `{WEB_SERVER_PUBLIC_IP}`는 Web Server VM의 Public IP 주소.
  > `CLAUDE.md`의 `### deploy` 상태에서 `VM_HOST`를 확인하고, `ssh {VM_HOST} 'curl -s ifconfig.me'`로 Public IP 조회 가능.

### 1) 진행 모드 선택

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

- **자동 진행** 선택 시 → Step 0에서 필요한 정보를 모두 수집한 뒤, 워크플로우 실행 중(Step 1~3)에는 `<!--ASK_USER-->`를 호출하지 않고 자동 처리한다.

### 2) CI 도구 선택

<!--ASK_USER-->  
{"title":"CI 도구 선택","questions":[  
  {"question":"CI 파이프라인에 사용할 도구를 선택하세요.","type":"radio","options":["Jenkins","GitHub Actions"]}  
]}  
<!--/ASK_USER-->

### 3) deploy 환경 정보 복원

`CLAUDE.md`의 `## NPD 워크플로우 상태 > ### deploy` 섹션에서 환경 정보를 읽어 변수를 바인딩.
`### deploy` 섹션이 없으면 에러 중단 (`/npd:deploy` 선행 필요).

| deploy 필드 | 바인딩 변수 | 비고 |
|-------------|------------|------|
| CLOUD | `{CLOUD}` | Cloud 서비스 |
| 레지스트리유형 | `{레지스트리유형}` | DockerHub/ECR/ACR/GCR |
| IMG_REG | `{IMG_REG}` | 레지스트리 URL |
| IMG_ORG | `{IMG_ORG}` | 이미지 조직/사용자명 |
| ECR_ACCOUNT | `{ECR_ACCOUNT}` | ECR인 경우 |
| ECR_REGION | `{ECR_REGION}` | ECR인 경우 |
| ACR명 | `{ACR명}` | ACR인 경우 |
| GCR_PROJECT | `{GCR_PROJECT}` | GCR인 경우 |
| GCR_REGION | `{GCR_REGION}` | GCR인 경우 |
| GCR_REPO | `{GCR_REPO}` | GCR인 경우 |
| VM_HOST | `{VM_HOST}` | Web Server VM |
| K8S_CLUSTER | `{K8S_CLUSTER}` | K8s 클러스터 (→ EKS/AKS/GKE_CLUSTER 매핑) |
| K8S_NAMESPACE | `{K8S_NAMESPACE}` | K8s 네임스페이스 |

**K8s 컨텍스트 전환:**
```bash
kubectx {K8S_CLUSTER가 포함된 컨텍스트}
```

> `kubectx` 미설치 시 `kubectl config use-context`로 대체.

**SSH 접속 테스트:**
```bash
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new {VM_HOST} exit
```

실패 시 1회 재시도 후 재실패 시 에러 중단.

### 4) 프로젝트 유형 감지 및 사전 검증

#### 프로젝트 유형 자동 감지

> 백엔드와 프론트엔드는 별도 프로젝트(리포지토리)에 있을 수 있다. 현재 프로젝트의 유형을 자동 감지하여 이후 단계에서 해당하는 파이프라인만 생성한다.

- **백엔드 감지**: `settings.gradle` 또는 `build.gradle` 존재
- **프론트엔드 감지**: `package.json` 존재 (settings.gradle 없음)
- **AI 서비스 감지**: `pyproject.toml` 존재 (settings.gradle, package.json 없음)
- **복합 프로젝트 (여러 유형 파일 공존)**: 사용자에게 확인 후 해당하는 파이프라인 모두 생성

#### 기존 K8s 매니페스트 존재 검증

```bash
# deployment/k8s/ 디렉토리 존재 확인
ls deployment/k8s/
```

> `deployment/k8s/` 디렉토리가 없으면 `/npd:deploy` Step 4를 먼저 완료하도록 안내하고 중단한다.

#### 프로젝트명 자동 감지

- **SYSTEM_NAME**: `settings.gradle` 파일에서 `rootProject.name` 값을 파싱하여 자동 감지
- **FRONTEND_SERVICE**: `package.json` 파일에서 `name` 필드를 파싱하여 자동 감지
- **AI_SERVICE**: `pyproject.toml` 파일에서 `[tool.poetry] name` 필드를 파싱하여 자동 감지. `pyproject.toml`이 없으면 AI 서비스 디렉토리명 사용
- 감지 실패 시 ASK_USER로 수동 입력

```bash
# SYSTEM_NAME 자동 감지
grep "rootProject.name" settings.gradle | sed "s/rootProject.name = '//;s/'//"

# FRONTEND_SERVICE 자동 감지
cat package.json | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])"

# AI_SERVICE 자동 감지
grep -A5 '^\[tool\.poetry\]' pyproject.toml | grep 'name' | sed 's/.*= *"//;s/"//'
```

### 5) 매니페스트 레포지토리 URL 결정

현재 프로젝트의 GitHub origin에서 org를 추출하여 매니페스트 레포 URL을 자동 결정:

```bash
ORIGIN_URL=$(git remote get-url origin)
# https://github.com/{org}/{repo}.git → {org} 추출
MANIFEST_REPO_URL="https://github.com/{org}/{SYSTEM_NAME}-manifest.git"
```

> Step 1에서 `gh repo create`로 실제 생성. 이미 존재하면 기존 URL 사용.

### 6) 배포 환경 선택

<!--ASK_USER-->
{"title":"배포 환경 선택","questions":[
  {"question":"ArgoCD Application을 생성할 환경을 선택하세요. (나중에 Step 2 재실행으로 추가 가능)","type":"checkbox","options":["dev","staging","prod"]}
]}
<!--/ASK_USER-->

- 선택된 환경만 Kustomize overlays 디렉토리 및 ArgoCD Application YAML을 생성
- 기본값: `dev`
- `[실행정보]`의 `ENVIRONMENTS` 필드에 쉼표 구분으로 기록 (예: `dev,staging`)

### 7) [실행정보] 조립

수집된 정보를 `[실행정보]` 블록으로 조립한다. **CI 도구 + 클라우드/레지스트리 조합**에 따라 아래 7가지 템플릿 중 하나를 사용한다.
조립된 `[실행정보]` 블록은 이후 에이전트 호출 시 **프롬프트의 동적(작업 지시) 영역에 텍스트로 포함**하여 전달한다. 에이전트는 별도 컨텍스트에서 실행되므로, `Task(prompt=...)` 호출 시 `[실행정보]` 블록 전문을 반드시 포함해야 가이드 내 변수를 치환할 수 있다.

> **2단계 조립**: Step 0에서 base [실행정보]를 조립하되, CI 도구 전용 필드(JENKINS_CLOUD_NAME, JENKINS_GIT_CREDENTIALS, MANIFEST_SECRET_GIT_USERNAME/PASSWORD, RESOURCE_GROUP, GKE_ZONE)는 미정으로 남긴다.
> Step 2.5에서 해당 필드를 수집한 후 [실행정보]를 보완하여 Step 3에 전달.

---

#### [실행정보] 조립 템플릿 (CI 도구별 + 클라우드/레지스트리별 7가지)

**Jenkins + Docker Hub:**
```
[실행정보]
- CI_TOOL: Jenkins
- CLOUD: {CLOUD}
- SYSTEM_NAME: {SYSTEM_NAME}
- FRONTEND_SERVICE: {FRONTEND_SERVICE}
- AI_SERVICE: {AI_SERVICE}
- 레지스트리유형: DockerHub
- IMG_REG: docker.io
- IMG_ORG: {Organization/Username}
- JENKINS_CLOUD_NAME: {JENKINS_CLOUD_NAME}
- JENKINS_GIT_CREDENTIALS: {JENKINS_GIT_CREDENTIALS}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
- VM_HOST: {VM_HOST}
- ENVIRONMENTS: {ENVIRONMENTS}
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
```

**Jenkins + ECR:**
```
[실행정보]
- CI_TOOL: Jenkins
- CLOUD: AWS
- SYSTEM_NAME: {SYSTEM_NAME}
- FRONTEND_SERVICE: {FRONTEND_SERVICE}
- AI_SERVICE: {AI_SERVICE}
- 레지스트리유형: ECR
- IMG_REG: {ECR_ACCOUNT}.dkr.ecr.{ECR_REGION}.amazonaws.com
- IMG_ORG: {SYSTEM_NAME}
- JENKINS_CLOUD_NAME: {JENKINS_CLOUD_NAME}
- JENKINS_GIT_CREDENTIALS: {JENKINS_GIT_CREDENTIALS}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
- VM_HOST: {VM_HOST}
- ENVIRONMENTS: {ENVIRONMENTS}
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
```

**Jenkins + ACR:**
```
[실행정보]
- CI_TOOL: Jenkins
- CLOUD: Azure
- SYSTEM_NAME: {SYSTEM_NAME}
- FRONTEND_SERVICE: {FRONTEND_SERVICE}
- AI_SERVICE: {AI_SERVICE}
- 레지스트리유형: ACR
- IMG_REG: {ACR명}.azurecr.io
- IMG_ORG: {SYSTEM_NAME}
- JENKINS_CLOUD_NAME: {JENKINS_CLOUD_NAME}
- JENKINS_GIT_CREDENTIALS: {JENKINS_GIT_CREDENTIALS}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
- VM_HOST: {VM_HOST}
- ENVIRONMENTS: {ENVIRONMENTS}
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
```

**Jenkins + Google Artifact Registry (GCR):**
```
[실행정보]
- CI_TOOL: Jenkins
- CLOUD: GCP
- SYSTEM_NAME: {SYSTEM_NAME}
- FRONTEND_SERVICE: {FRONTEND_SERVICE}
- AI_SERVICE: {AI_SERVICE}
- 레지스트리유형: GCR  # Google Artifact Registry (구 GCR 약칭 사용)
- IMG_REG: {GCR_REGION}-docker.pkg.dev/{GCR_PROJECT}/{GCR_REPO}
- IMG_ORG: {SYSTEM_NAME}
- JENKINS_CLOUD_NAME: {JENKINS_CLOUD_NAME}
- JENKINS_GIT_CREDENTIALS: {JENKINS_GIT_CREDENTIALS}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
- VM_HOST: {VM_HOST}
- ENVIRONMENTS: {ENVIRONMENTS}
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
```

**GitHub Actions + Azure AKS (ACR):**
```
[실행정보]
- CI_TOOL: GitHubActions
- CLOUD: Azure
- SYSTEM_NAME: {SYSTEM_NAME}
- FRONTEND_SERVICE: {FRONTEND_SERVICE}
- AI_SERVICE: {AI_SERVICE}
- 레지스트리유형: ACR
- IMG_REG: {ACR_NAME}.azurecr.io
- IMG_ORG: {SYSTEM_NAME}
- ACR_NAME: {ACR명}
- RESOURCE_GROUP: {리소스그룹}
- AKS_CLUSTER: {AKS클러스터명}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
- MANIFEST_SECRET_GIT_USERNAME: {MANIFEST_SECRET_GIT_USERNAME}
- MANIFEST_SECRET_GIT_PASSWORD: {MANIFEST_SECRET_GIT_PASSWORD}
- VM_HOST: {VM_HOST}
- ENVIRONMENTS: {ENVIRONMENTS}
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
```

**GitHub Actions + AWS EKS (ECR):**
```
[실행정보]
- CI_TOOL: GitHubActions
- CLOUD: AWS
- SYSTEM_NAME: {SYSTEM_NAME}
- FRONTEND_SERVICE: {FRONTEND_SERVICE}
- AI_SERVICE: {AI_SERVICE}
- 레지스트리유형: ECR
- IMG_REG: {ECR_ACCOUNT}.dkr.ecr.{ECR_REGION}.amazonaws.com
- IMG_ORG: {SYSTEM_NAME}
- ECR_ACCOUNT: {ECR_ACCOUNT}
- ECR_REGION: {ECR_REGION}
- EKS_CLUSTER: {EKS클러스터명}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
- MANIFEST_SECRET_GIT_USERNAME: {MANIFEST_SECRET_GIT_USERNAME}
- MANIFEST_SECRET_GIT_PASSWORD: {MANIFEST_SECRET_GIT_PASSWORD}
- VM_HOST: {VM_HOST}
- ENVIRONMENTS: {ENVIRONMENTS}
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
```

**GitHub Actions + GCP GKE (Google Artifact Registry):**
```
[실행정보]
- CI_TOOL: GitHubActions
- CLOUD: GCP
- SYSTEM_NAME: {SYSTEM_NAME}
- FRONTEND_SERVICE: {FRONTEND_SERVICE}
- AI_SERVICE: {AI_SERVICE}
- 레지스트리유형: GCR  # Google Artifact Registry (구 GCR 약칭 사용)
- IMG_REG: {GCR_REGION}-docker.pkg.dev/{GCR_PROJECT}/{GCR_REPO}
- IMG_ORG: {SYSTEM_NAME}
- GCR_REGION: {GCR_REGION}
- GCR_PROJECT: {GCP_PROJECT_ID}
- GCR_REPO: {GCR_REPO}
- GKE_CLUSTER: {GKE클러스터명}
- GKE_ZONE: {GKE_ZONE}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
- MANIFEST_SECRET_GIT_USERNAME: {MANIFEST_SECRET_GIT_USERNAME}
- MANIFEST_SECRET_GIT_PASSWORD: {MANIFEST_SECRET_GIT_PASSWORD}
- VM_HOST: {VM_HOST}
- ENVIRONMENTS: {ENVIRONMENTS}
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
```

---

### 자동 진행 모드 동작 규칙

- Step 0의 진행 모드·CI 도구 선택은 자동 진행 모드에서도 수행
- deploy 환경 정보는 `### deploy` 상태에서 자동 복원 (질문 없음)
- Step 1~3 실행 중에는 `<!--ASK_USER-->` 호출하지 않음
- 자동 감지 가능 항목: SYSTEM_NAME (settings.gradle), FRONTEND_SERVICE (package.json), AI_SERVICE (pyproject.toml)

> **조건부 필드**: `FRONTEND_SERVICE`는 `package.json` 감지 시에만, `AI_SERVICE`는 `pyproject.toml` 감지 시에만 `[실행정보]`에 포함. 순수 AI 프로젝트는 FRONTEND_SERVICE 없이 AI_SERVICE만 포함 가능.

### 상태 기록 (`/clear` 대비)

[실행정보] 조립 완료 시, 프로젝트 루트 `CLAUDE.md`의 `## NPD 워크플로우 상태` 섹션 하위에
`### cicd` 서브섹션을 생성(이미 있으면 갱신):

```
## NPD 워크플로우 상태
### cicd
- 진행 모드: {선택값}
- CI_TOOL: {Jenkins/GitHubActions}
- CLOUD: {선택값}
- 레지스트리유형: {DockerHub/ECR/ACR/GCR}
- AI_SERVICE: {값}
- MANIFEST_REPO_URL: {값}
- VM_HOST: {값}
- ENVIRONMENTS: {값}
- K8S_CLUSTER: {값}
- K8S_NAMESPACE: {값}
- 마지막 완료 Step: {Step명}
```

각 Step 완료 시 `마지막 완료 Step` 값을 갱신.

## 워크플로우

### Step 1. CI/CD 도구 사전 설정 → Agent: devops-engineer (/ralph 활용)

- **GUIDE**: `resources/guides/cicd/cicd-pre-setup.md`
- **CONTEXT**: 조립된 `[실행정보]` 블록 포함
- **TASK**: 가이드를 참조하여 클라우드별 사전작업 수행 및 CI/CD 도구(Jenkins/SonarQube/ArgoCD) 설치

#### 실행 조건
- 항상 수행. 이미 설치된 도구는 자동 건너뜀 (idempotent).

#### 실행 순서 (병렬화)

Step 1은 3단계로 나뉘며, **Phase B는 병렬 실행**한다:

```
Phase A (순차) → Phase B (병렬) → Phase C (순차)
```

**Phase A: 사전작업 (순차, 에이전트 1개)**
1. 클라우드별 사전작업 (StorageClass, IngressClass, NodePool)
2. 매니페스트 레포지토리 생성 (`gh repo create {org}/{SYSTEM_NAME}-manifest --private`, 이미 존재 시 건너뜀)

**Phase B: 도구 설치 (병렬, 에이전트 최대 3개 동시)**

Phase A 완료 후, 아래 도구를 **병렬로 설치** (각각 독립 에이전트 호출):

| 에이전트 | 가이드 섹션 | 설치 내용 |
|----------|-----------|----------|
| devops-engineer #1 | Phase 2 | Jenkins Helm 설치 + RBAC (CI_TOOL == Jenkins인 경우) |
| devops-engineer #2 | Phase 3 | SonarQube Helm 설치 + affinity 패치 + scale 재시작 + 백엔드 단위테스트 실행·에러 해결 |
| devops-engineer #3 | Phase 4 | ArgoCD Helm 설치 + --insecure 검증 |

> Jenkins와 ArgoCD는 cicd NodePool을, SonarQube는 sonarqube NodePool을 사용.
> NodePool 리밋(cpu:16, mem:64Gi)이 충분하므로 동시 스케줄링 가능.
> CI_TOOL == GitHubActions이면 Jenkins 에이전트는 건너뜀 (2개만 병렬).

**Phase C: Nginx 프록시 + 보고서 (순차, 에이전트 1개)**

Phase B의 모든 에이전트 완료 후:
1. Nginx 프록시 설정 (SSH로 Web Server VM에 자동 설정)
2. 프록시 연결 검증 (curl)
3. `docs/cicd/cicd-pre-setup-report.md` 결과 보고서 작성 (접속정보 + 암호 포함)

#### 수동 후속 작업 안내
에이전트가 자동 설치 완료 후, 사용자에게 수동 후속 작업 목록 안내:
- hosts 파일 등록
- Jenkins 플러그인 설치 및 K8s Cloud 연결
- SonarQube Token/Webhook/Quality Gate 설정
- Image Registry / DockerHub Credential 등록
- (GitHub Actions 선택 시) Repository Secrets/Variables 등록

수동 안내 시 `setup-cicd-tools.md` 원본 가이드 링크를 참조 제공.

#### EXPECTED OUTCOME
- 클라우드별 사전작업 완료 (StorageClass, NodePool 등)
- Jenkins Pod 정상 실행 (CI_TOOL == Jenkins인 경우)
- SonarQube Pod 정상 실행
- 백엔드 단위테스트 통과 및 JaCoCo 리포트 생성 확인 (SonarQube 설정 후)
- ArgoCD Pod 정상 실행
- Nginx 프록시 설정 완료 (SSH 자동, `nginx -t` 성공, curl 검증 통과)
- 수동 후속 작업 안내 메시지 출력
- `docs/cicd/cicd-pre-setup-report.md` 결과 보고서 작성 (프로젝트 루트)

### Step 1.5) 수동 설정 완료 확인 (Step 2 시작 전)

> Step 1 자동 설치 완료 후 (또는 "이미 설치 완료" 선택 시), Step 2 진행 전에  
> `setup-cicd-tools.md`의 수동 후속 설정 완료 여부를 확인한다.

<!--ASK_USER-->  
{"title":"수동 설정 완료 확인","questions":[  
  {"question":"CI/CD 도구의 수동 후속 설정을 완료했나요?\n\n- hosts 파일 등록\n- Jenkins 플러그인 설치 및 K8s Cloud 연결 (Jenkins 선택 시)\n- SonarQube Token/Webhook/Quality Gate 설정\n- Image Registry / DockerHub Credential 등록 (Jenkins 선택 시)\n- GitHub Actions Secrets/Variables 등록 (GitHub Actions 선택 시)\n\n미완료 시 아래 가이드를 참조하세요:\nhttps://github.com/unicorn-plugins/npd/blob/main/resources/references/setup-cicd-tools.md","type":"radio","options":["모두 완료","아직 미완료"]}  
]}  
<!--/ASK_USER-->

- **"모두 완료"** 선택 시: Step 2 진행.
- **"아직 미완료"** 선택 시: 가이드 링크를 다시 안내하고 완료 대기.

### Step 2. 매니페스트 레포지토리 + ArgoCD 구성 → Agent: devops-engineer (/ralph 활용)

- **GUIDE**: `resources/guides/cicd/deploy-argocd-cicd.md`
- **에이전트 프롬프트 필수 지시**: "ArgoCD 가이드의 '매니페스트 레포지토리 구성', 'ArgoCD Application YAML 생성', 'ArgoCD 매니페스트 레포지토리 인증 등록', 'ArgoCD Application 등록' 섹션을 참조하세요. 'CI 파이프라인의 매니페스트 업데이트 스크립트 참조' 섹션은 Step 3에서 처리합니다."
- **CONTEXT**: 조립된 `[실행정보]` 블록 포함

> **Kustomize 파일 관리 원칙**: Step 2에서 매니페스트 레포지토리에 Kustomize 파일을 생성합니다 (ArgoCD가 감시하는 "라이브" 매니페스트). Step 3에서는 CI/CD 파이프라인 파일(Jenkinsfile/GitHub Actions workflow)을 생성하며, 파이프라인의 마지막 단계에서 매니페스트 레포의 image tag만 업데이트합니다.

#### Git 크리덴셜 사전 수집 (에이전트 호출 전)

> 에이전트는 사용자에게 직접 질문할 수 없으므로, ArgoCD 인증 등록에 필요한 Git 크리덴셜을 오케스트레이터가 사전 수집하여 에이전트 프롬프트에 포함해야 한다.

<!--ASK_USER-->
{"title":"ArgoCD 매니페스트 레포 인증 정보","questions":[
  {"question":"ArgoCD에서 Private 매니페스트 레포지토리에 접근하기 위한 Git 인증 정보를 입력하세요.\n\n1) GitHub 사용자명\n2) GitHub Personal Access Token (repo 권한 필요)\n\n※ Jenkins Credential에 등록한 동일한 PAT를 사용해도 됩니다.","type":"text","placeholder":"username / token"}
]}
<!--/ASK_USER-->

수집된 Git 크리덴셜을 에이전트 프롬프트에 다음과 같이 포함한다:
- `GIT_USERNAME`: 사용자명
- `GIT_TOKEN`: Personal Access Token

#### 가이드에 없는 보충 정보

- **ArgoCD Private 레포 인증**: 매니페스트 레포지토리가 Private인 경우, ArgoCD 인증 등록에 Git 크리덴셜이 필요합니다. 오케스트레이터가 사전 수집한 `GIT_USERNAME`/`GIT_TOKEN` 값을 에이전트 프롬프트에 포함하여 전달하세요.

#### EXPECTED OUTCOME
- 매니페스트 레포지토리 구조 생성 (Kustomize base/overlays — `{ENVIRONMENTS}` 환경만)
- ArgoCD 매니페스트 레포지토리 인증 등록 (Private 레포인 경우)
- ArgoCD Application YAML 파일 생성 (`argocd/*.yaml` — `{ENVIRONMENTS}` 환경만)
- ArgoCD Application 등록 완료
- `deploy-argocd-prepare.md` 결과 보고서 작성 (프로젝트 루트)

### Step 2 POST_ACTION: 매니페스트 레포지토리 Push

Step 2에서 생성된 매니페스트 레포지토리 파일을 원격에 커밋·푸시한다.
ArgoCD가 매니페스트 레포지토리 변경을 감지하려면 원격에 push되어 있어야 한다.

```bash
cd {매니페스트 레포지토리 로컬 경로}
git add .
git commit -m "cicd: 매니페스트 레포지토리 초기 구성 (Kustomize + ArgoCD Application)"
git push origin main
```

### Step 2.5) CI 도구별 추가 정보 수집 + [실행정보] 보완

> Step 2 완료 후, Step 3(파이프라인 작성) 전에 CI 도구 전용 필드를 수집하여 [실행정보]를 보완.

**Jenkins 선택 시:**

<!--ASK_USER-->
{"title":"Jenkins 설정 정보","questions":[
  {"question":"Jenkins에 설정한 Kubernetes Cloud 이름을 입력하세요.","type":"text","placeholder":"k8s"},
  {"question":"매니페스트 레포지토리 접근용 Jenkins Credential ID를 입력하세요. (ArgoCD용 Git 인증)","type":"text","placeholder":"github-credentials"}
]}
<!--/ASK_USER-->

- `JENKINS_CLOUD_NAME`: 기본값은 K8s 클러스터명(`{K8S_CLUSTER}`)과 동일하게 제안
- `JENKINS_GIT_CREDENTIALS`: ArgoCD 매니페스트 레포지토리 접근용

**GitHub Actions 선택 시:**

- `MANIFEST_SECRET_GIT_USERNAME`: `GIT_USERNAME` (고정)
- `MANIFEST_SECRET_GIT_PASSWORD`: `GIT_PASSWORD` (고정)

> 매니페스트 레포지토리 접근용 Secret은 `setup-cicd-tools.md`에서 `GIT_USERNAME`/`GIT_PASSWORD`로 등록하도록 안내하므로 별도 질문 불필요.

수집된 필드를 [실행정보]에 보완하여 Step 3에 전달.

### Step 3. CI/CD 파이프라인 작성 → Agent: devops-engineer (/ralph 활용)

- **에이전트 프롬프트 필수 지시**:
  1. "가이드의 **Jenkinsfile 템플릿**을 **그대로 사용**하고, `{플레이스홀더}`만 실제 값으로 치환하세요. 가이드에 없는 파이프라인 구조, 문법, 컨테이너 이미지를 사용하지 마세요."
  2. "Jenkins Job 생성, 빌드 실행, 결과 검증까지 가이드의 해당 섹션을 따라 수행하세요."
- **에이전트 검증 체크리스트** (생성된 파일을 가이드와 비교):
  - [ ] 파이프라인 방식 일치 (Scripted/Declarative)
  - [ ] 컨테이너 런타임 일치 (Podman/Docker)
  - [ ] SonarQube 단계 포함 여부 일치
  - [ ] 매니페스트 업데이트 방식 일치 (kustomize edit / sed)
  - [ ] 리소스 제한(requests/limits) 포함 여부 일치

#### 가이드 선택 로직

```
IF CI_TOOL == Jenkins:
    백엔드 -> resources/guides/cicd/deploy-jenkins-cicd-back.md
    프론트엔드 -> resources/guides/cicd/deploy-jenkins-cicd-front.md
    AI 서비스 -> resources/guides/cicd/deploy-jenkins-cicd-ai.md
ELSE IF CI_TOOL == GitHubActions:
    백엔드 -> resources/guides/cicd/deploy-actions-cicd-back.md
    프론트엔드 -> resources/guides/cicd/deploy-actions-cicd-front.md
    AI 서비스 -> resources/guides/cicd/deploy-actions-cicd-ai.md
```

> 클라우드별 분기 불필요. 가이드 내 조건부 섹션이 `[실행정보]`의 CLOUD 값에 따라 registry login 방식을 분기.

**추가 참조 가이드**: `resources/guides/cicd/deploy-argocd-cicd.md` (manifest repo 업데이트 스크립트 부분만)

#### 백엔드 CI/CD 파이프라인 작성 (에이전트 호출)

- **GUIDE**: 위 로직에서 결정된 백엔드 가이드 + ArgoCD 가이드 (manifest 업데이트 스크립트)
- **CONTEXT**: 조립된 `[실행정보]` 블록 포함
- **TASK**: 가이드의 **Jenkinsfile 템플릿**을 **그대로 사용**하여 `{플레이스홀더}`만 실제 값으로 치환. 가이드의 'Jenkins Job 생성 및 빌드 실행' 섹션을 따라 Job 생성, 빌드 실행, 결과 검증까지 수행
- **EXPECTED OUTCOME**:
  - Jenkins: `deployment/cicd/Jenkinsfile-backend`, `docs/cicd/deploy-jenkins-cicd-back-result.md`
  - GitHub Actions: `.github/workflows/backend-cicd.yaml`, `docs/cicd/deploy-actions-cicd-back-result.md`

#### 프론트엔드 CI/CD 파이프라인 작성 (에이전트 호출)

- **GUIDE**: 위 로직에서 결정된 프론트엔드 가이드 + ArgoCD 가이드 (manifest 업데이트 스크립트)
- **CONTEXT**: 조립된 `[실행정보]` 블록 포함
- **TASK**: 가이드의 **Jenkinsfile 템플릿**을 **그대로 사용**하여 `{플레이스홀더}`만 실제 값으로 치환. 가이드의 'Jenkins Job 생성 및 빌드 실행' 섹션을 따라 Job 생성, 빌드 실행, 결과 검증까지 수행
- **EXPECTED OUTCOME**:
  - Jenkins: `deployment/cicd/Jenkinsfile-frontend`, `docs/cicd/deploy-jenkins-cicd-front-result.md`
  - GitHub Actions: `.github/workflows/frontend-cicd.yaml`, `docs/cicd/deploy-actions-cicd-front-result.md`

#### AI 서비스 CI/CD 파이프라인 작성 (에이전트 호출)

- **GUIDE**: 위 로직에서 결정된 AI 서비스 가이드 + ArgoCD 가이드 (manifest 업데이트 스크립트)
- **CONTEXT**: 조립된 `[실행정보]` 블록 포함
- **TASK**: 가이드의 **Jenkinsfile 템플릿**을 **그대로 사용**하여 `{플레이스홀더}`만 실제 값으로 치환. 가이드의 'Jenkins Job 생성 및 빌드 실행' 섹션을 따라 Job 생성, 빌드 실행, 결과 검증까지 수행
- **EXPECTED OUTCOME**:
  - Jenkins: `deployment/cicd/Jenkinsfile-ai`, `docs/cicd/deploy-jenkins-cicd-ai-result.md`
  - GitHub Actions: `.github/workflows/ai-cicd.yaml`, `docs/cicd/deploy-actions-cicd-ai-result.md`

#### 백엔드/프론트엔드/AI 감지 로직

> 백엔드, 프론트엔드, AI 서비스는 별도 프로젝트(리포지토리)에 있을 수 있다. 스킬은 현재 프로젝트의 유형을 자동 감지하여 해당하는 파이프라인만 생성한다.
> - **백엔드 감지**: `settings.gradle` 또는 `build.gradle` 존재
> - **프론트엔드 감지**: `package.json` 존재 (settings.gradle 없음)
> - **AI 서비스 감지**: `pyproject.toml` 존재
> - **여러 유형이 공존하는 경우**: 사용자에게 확인 후 해당하는 파이프라인 모두 생성
>
> **⚠️ 모노레포(여러 유형 공존) 파일 충돌 방지:**
> - Jenkins: 백엔드 `Jenkinsfile-backend`, 프론트엔드 `Jenkinsfile-frontend`, AI `Jenkinsfile-ai`로 분리
> - GitHub Actions: 워크플로우 파일명이 이미 분리됨 (`backend-cicd.yaml`, `frontend-cicd.yaml`, `ai-cicd.yaml`)

### Step 3 POST_ACTION: 소스 레포지토리 Push

Step 3에서 생성된 CI/CD 파이프라인 파일을 소스 레포지토리에 커밋·푸시한다.
Jenkins가 파이프라인 파일에 접근하려면 원격 레포에 push되어 있어야 한다.

```bash
# 생성된 파이프라인 파일 커밋 및 푸시
git add deployment/cicd/Jenkinsfile-* deployment/cicd/deploy-jenkins-cicd-*-result.md
# 또는 GitHub Actions인 경우
# git add .github/workflows/*-cicd.yaml deployment/cicd/deploy-actions-cicd-*-result.md
git commit -m "cicd: CI/CD 파이프라인 파일 생성 (Step 3)"
git push origin main
```

### Step 4. 완료 보고

스킬 레벨에서 직접 수행 (에이전트 호출 없음).

```
## CI/CD 파이프라인 구성 완료

### 환경 정보
- CI 도구: {Jenkins / GitHub Actions}
- CD 도구: ArgoCD (GitOps)
- Cloud: {AWS / Azure / GCP}
- K8s 클러스터: {클러스터명}

### Step 1: CI/CD 도구 사전 설정 산출물
- 클라우드 사전작업: {완료/건너뜀}
- Jenkins: {설치 완료/건너뜀} (CI_TOOL에 따라)
- SonarQube: {설치 완료/건너뜀}
- ArgoCD: {설치 완료/건너뜀}
- Nginx 프록시: {설정 완료} (VM: {VM_HOST})
- 사전 설정 보고서: `docs/cicd/cicd-pre-setup-report.md`

### Step 2: 매니페스트 레포지토리 + ArgoCD 산출물
- 매니페스트 레포지토리: {MANIFEST_REPO_URL}
- ArgoCD Application YAML: argocd/*.yaml
- ArgoCD Application 등록: 완료
- ArgoCD 준비 보고서: `deploy-argocd-prepare.md`

### Step 3: CI/CD 파이프라인 산출물
- 백엔드: {파이프라인 파일 경로} (빌드+푸시+manifest tag 업데이트)
- 프론트엔드: {파이프라인 파일 경로} (빌드+푸시+manifest tag 업데이트)
- AI 서비스: {파이프라인 파일 경로} (빌드+푸시+manifest tag 업데이트)

### 다음 단계
1. CI 파이프라인 실행하여 전체 흐름 검증 (빌드 → 푸시 → manifest 업데이트 → ArgoCD 자동 배포)
```

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |
| 2 | CI 도구 선택(Jenkins/GitHub Actions)에 따라 가이드 선택 매트릭스를 참조하여 해당하는 가이드만 참조할 것 (클라우드별 분기 불필요) |
| 3 | CI 파이프라인에 kubectl apply를 포함하지 않을 것. 마지막 단계는 manifest repo image tag 업데이트여야 함 |
| 4 | `[실행정보]` 블록을 에이전트 프롬프트에 반드시 포함할 것 — CI 도구 + 레지스트리유형 조합에 맞는 템플릿 사용 |
| 5 | GitHub Actions 가이드 내 클라우드별 조건부 섹션이 `[실행정보]`의 CLOUD 값에 따라 올바르게 적용되도록 할 것 |
| 6 | Step 0의 사전 도구 체크는 설치 여부 확인만 수행. 미설치 시 Step 1에서 가이드(`cicd-pre-setup.md`) 기반 자동 설치 진행. Step 0에서 직접 설치 금지 |

## 완료 조건

- [ ] 클라우드별 사전작업 완료 (StorageClass, NodePool 등 — Step 1)
- [ ] CI/CD 도구 Pod 정상 실행 (Jenkins/SonarQube/ArgoCD — Step 1)
- [ ] Nginx 프록시 설정 완료 — `nginx -t` 성공 (Step 1)
- [ ] 수동 후속 작업 안내 출력 (Step 1)
- [ ] `docs/cicd/cicd-pre-setup-report.md` 생성 (Step 1)
- [ ] 매니페스트 레포지토리 구조가 생성됨 (Kustomize base/overlays)
- [ ] ArgoCD Application YAML이 서비스별 x 환경별로 생성·등록됨
- [ ] CI/CD 파이프라인 파일이 생성됨 (Jenkinsfile 또는 GitHub Actions Workflow) — kubectl apply 없이 manifest repo image tag 업데이트 포함
- [ ] AI 서비스 감지 시, AI CI/CD 파이프라인 파일이 생성됨 (Jenkinsfile-ai 또는 ai-cicd.yaml)
- [ ] 완료 보고서가 작성됨
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (매니페스트 레포 구조, ArgoCD YAML, 파이프라인 파일)
2. ArgoCD Application YAML 유효성 검사 (`kubectl apply --dry-run=client -f argocd/`)
3. Kustomize 유효성 검사 (`kubectl kustomize` dry-run)
4. 파이프라인 파일 문법 검증 (변수 참조 `${variable}` 사용, `\${variable}` 사용 금지 등)
5. Step 1 도구 설치 검증: `kubectl get po -n jenkins` (Jenkins 선택 시), `kubectl get po -n sonarqube`, `kubectl get po -n argocd`
6. Step 1 사전작업 검증: `kubectl get storageclass` (AWS), `kubectl get nodepool` (AWS/Azure)
7. Step 1 Nginx 검증: `ssh {VM_HOST} 'sudo nginx -t'`

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.

1. `CLAUDE.md`의 `## NPD 워크플로우 상태 > ### cicd` 섹션에서 변수를 복원:
   - `진행 모드` → 승인/자동 모드 결정
   - `CI_TOOL` → CI 도구
   - `CLOUD` → Cloud 서비스
   - `레지스트리유형` → 레지스트리 유형
   - `MANIFEST_REPO_URL` → 매니페스트 레포지토리
   - `VM_HOST` → VM 접속 정보
   - `K8S_CLUSTER`, `K8S_NAMESPACE` → K8s 배포 대상
   - `마지막 완료 Step` → 재개 시작점 결정
2. 상태 섹션이 없으면 **Step 0** 부터 시작
3. `### deploy` 섹션도 함께 읽어 사전 바인딩 적용 (2-1 규칙)
