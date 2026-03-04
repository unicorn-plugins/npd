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
- 사전 도구 설치 완료 필수: CI 도구(Jenkins K8s Pod 기반 또는 GitHub Actions), SonarQube, ArgoCD, Image Registry Credential

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
| `{FRONTEND_SERVICE}` | `[실행정보]` | 프론트엔드 서비스명 (package.json의 name) |
| `{SERVICE_NAMES}` | `settings.gradle` 파싱 | 백엔드 서비스명 목록 (include 'common' 하위). `[실행정보]`에 포함되지 않으며, 에이전트가 settings.gradle에서 직접 파싱 |
| `{서비스명1}`, `{서비스명2}` ... | `{SERVICE_NAMES}`의 개별 항목 | 가이드 내 예시에서 사용하는 반복 표기 |

> **주의**: 가이드 파일마다 `{SERVICE_NAME1}` (밑줄 없음), `{SERVICE_NAME_1}` (밑줄 있음), `{서비스명1}` (한글), `{SERVICE_NAMEN}` (N번째를 의미하는 말줄임) 등이 혼용됩니다. 모두 동일하게 `{SERVICE_NAMES}`의 개별 항목을 의미합니다.

## 클라우드별 차이 처리 안내

- Jenkins, GitHub Actions 모두 **클라우드 무관하게 동일 가이드** 사용 (가이드 내 조건부 섹션으로 처리)
- 클라우드별 차이는 registry login 인증 방식뿐이며, `[실행정보]`의 `CLOUD` 값에 따라 가이드 내 조건부 섹션 적용
- `{IMG_REG}/{IMG_ORG}` 변수로 레지스트리 URL을 추상화하므로 build/push/manifest 업데이트 로직은 동일

## 가이드 선택 매트릭스

CI 도구에 따라 참조할 가이드 파일이 결정된다. **클라우드별 분기 불필요** — CI/CD 분리 후 클라우드별 차이는 registry login 1개 step뿐이므로, 가이드 내 조건부 섹션으로 처리한다. 모든 가이드는 `resources/guides/cicd/` 경로에 위치한다.

| CI 도구 | 백엔드 가이드 | 프론트엔드 가이드 |
|---------|-------------|----------------|
| Jenkins | `deploy-jenkins-cicd-back.md` | `deploy-jenkins-cicd-front.md` |
| GitHub Actions | `deploy-actions-cicd-back.md` | `deploy-actions-cicd-front.md` |

## 에이전트 모드 매핑

| Step | 에이전트 모드 | 이유 |
|------|-------------|------|
| Step 0 | (orchestrator 직접) | 사용자 인터랙션 + 정보 수집 |
| Step 1 | `/ralph` | 매니페스트 레포지토리 구성 + ArgoCD Application YAML 생성·등록 |
| Step 2 | `/ralph` | CI/CD 파이프라인 코드 생성 (빌드+푸시+manifest tag 업데이트) |
| Step 3 | (orchestrator 직접) | 완료 보고서 작성 |

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

CI/CD 워크플로우 시작 전, 진행 모드 선택, 사전 도구 확인, 환경 정보 수집을 수행한다.

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

- **자동 진행** 선택 시 → Step 0에서 필요한 정보를 모두 수집한 뒤, 워크플로우 실행 중(Step 1~2)에는 `<!--ASK_USER-->`를 호출하지 않고 자동 처리한다.

### 2) CI 도구 선택

<!--ASK_USER-->
{"title":"CI 도구 선택","questions":[
  {"question":"CI 파이프라인에 사용할 도구를 선택하세요.","type":"radio","options":["Jenkins","GitHub Actions"]}
]}
<!--/ASK_USER-->

### 3) 사전 도구 설치 체크

K8s 클러스터에 CI/CD 도구가 설치되어 있는지 **설치 여부만 확인**한다. 미설치 도구가 있으면 가이드 링크를 제공하고 설치 완료를 대기한다. **자동 설치는 수행하지 않는다.**

**Jenkins 선택 시:**

<!--ASK_USER-->
{"title":"CI/CD 사전 도구 설치 확인","questions":[
  {"question":"K8s 클러스터에 아래 도구들이 모두 설치되어 있나요?\n\n1. Jenkins (K8s Pod 기반)\n2. SonarQube\n3. ArgoCD\n4. Image Registry Credential (Jenkins에 등록)\n5. DockerHub Credential (Jenkins에 등록, Rate Limit 해결용 — imagereg-credentials와 별도)\n\n미설치 시 아래 가이드를 참고하세요. 크리덴셜 설정(Jenkins Credential, SonarQube Token, DockerHub Credential)도 해당 가이드에 포함되어 있습니다:\nhttps://github.com/unicorn-plugins/npd/blob/main/resources/references/create-cicd-tools.md","type":"radio","options":["모두 설치 완료","아직 미완료"]}
]}
<!--/ASK_USER-->

**GitHub Actions 선택 시:**

<!--ASK_USER-->
{"title":"CI/CD 사전 도구 설치 확인","questions":[
  {"question":"K8s 클러스터에 아래 도구들이 모두 설치되어 있나요?\n\n1. SonarQube\n2. ArgoCD\n\nGitHub Actions는 별도 설치 불필요합니다.\nImage Registry Credential과 기타 인증정보는 GitHub Repository Secrets으로 등록합니다.\n\n미설치 시 아래 가이드를 참고하세요 (SonarQube, ArgoCD 설치 + GitHub Actions Secrets/Variables 설정 포함):\nhttps://github.com/unicorn-plugins/npd/blob/main/resources/references/create-cicd-tools.md","type":"radio","options":["모두 설치 완료","아직 미완료"]}
]}
<!--/ASK_USER-->

- **"아직 미완료"** 선택 시: 가이드 링크를 다시 안내하고 설치 완료 대기. 자동 설치 시도 금지.

### 4) 백킹서비스 배포 체크

K8s 클러스터에 백킹서비스(DB, Redis, Kafka 등)가 배포되어 있는지 확인한다. CI/CD 파이프라인이 배포할 애플리케이션이 의존하는 백킹서비스가 사전에 준비되어 있어야 파이프라인 실행 시 정상 동작한다.

<!--ASK_USER-->
{"title":"백킹서비스 배포 확인","questions":[
  {"question":"K8s 클러스터에 애플리케이션이 의존하는 백킹서비스(DB, Redis, Kafka 등)가 모두 배포되어 있나요?\n\n`/npd:deploy`의 백킹서비스 배포 단계가 완료된 상태여야 합니다.","type":"radio","options":["모두 배포 완료","아직 미완료"]}
]}
<!--/ASK_USER-->

- **"아직 미완료"** 선택 시: `/npd:deploy` 스킬을 통해 백킹서비스를 먼저 배포하도록 안내하고 완료 대기.

### 5) CLOUD 판단

`CLAUDE.md`의 `## NPD 워크플로우 상태`에서 `CLOUD` 값을 읽는다. 없으면:

<!--ASK_USER-->
{"title":"Cloud 서비스 선택","questions":[
  {"question":"배포할 Cloud 서비스를 선택하세요.","type":"radio","options":["AWS","Azure","GCP"]}
]}
<!--/ASK_USER-->

Jenkins와 GitHub Actions 모두 3개 클라우드(AWS EKS, Azure AKS, GCP GKE)를 지원하므로 별도 제한 없음.

### 6) K8s 클러스터 정보 수집

`kubectx`로 로컬의 kubeconfig 컨텍스트를 조회하여 `{CLOUD}`에 해당하는 클러스터를 자동 감지한다.

**컨텍스트 목록 조회:**
```bash
kubectx
```

> `kubectx`가 설치되어 있지 않은 경우 아래 명령으로 대체한다:
> ```bash
> kubectl config get-contexts -o name
> ```

**클라우드별 컨텍스트 필터링 패턴:**

| CLOUD | 필터링 방법 | 예시 |
|-------|-----------|------|
| AWS | `arn:aws:eks:` 포함 | `arn:aws:eks:ap-northeast-2:851725211153:cluster/eks-ondal` |
| Azure | 컨텍스트명에 `aks` 포함 (대소문자 무시) | `aks-ondal` |
| GCP | `gke_`로 시작 | `gke_lunchpick-489007_asia-northeast3_gce-ondal` |

**자동 감지 규칙:**

```bash
# AWS EKS
kubectx | grep 'arn:aws:eks:'

# Azure AKS
kubectx | grep -i 'aks'

# GCP GKE
kubectx | grep '^gke_'
```

> `kubectx` 미설치 시 대체 명령:
> ```bash
> # AWS EKS
> kubectl config get-contexts -o name | grep 'arn:aws:eks:'
> # Azure AKS
> kubectl config get-contexts -o name | grep -i 'aks'
> # GCP GKE
> kubectl config get-contexts -o name | grep '^gke_'
> ```

**분기 처리:**

- **매칭 1개 이상** → 감지된 컨텍스트 목록을 사용자에게 제시하고 배포 대상을 확인받음:

<!--ASK_USER-->
{"title":"K8s 클러스터 선택","questions":[
  {"question":"{CLOUD}에 연결된 클러스터가 감지되었습니다. CI/CD 대상 클러스터를 선택하세요.","type":"radio","options":["{감지된 컨텍스트 목록}"]}
]}
<!--/ASK_USER-->

- **매칭 0개** → 클러스터가 감지되지 않음을 안내하고, 아래 가이드를 참조하여 클러스터 생성을 요청:
  - 참조: [K8s 클러스터 생성 가이드](https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-k8s.md)

**컨텍스트 전환 및 클러스터명 추출:**
```bash
kubectx {선택된 컨텍스트}
```

클러스터명은 컨텍스트 이름에서 추출한다:
- AWS: `arn:aws:eks:{region}:{account}:cluster/{클러스터명}` → 마지막 `/` 뒤
- Azure: 컨텍스트 이름 자체가 클러스터명
- GCP: `gke_{project}_{region}_{클러스터명}` → 마지막 `_` 뒤

**NAMESPACE 결정:**

네임스페이스는 `{SYSTEM_NAME}` (프로젝트명, CLAUDE.md의 시스템명)를 기본값으로 사용한다.

### 7) 이미지 레지스트리 정보 수집

> **참고**: 이 섹션은 **Jenkins** 선택 시 레지스트리 유형을 선택받고, **GitHub Actions** 선택 시 CLOUD 값에 따라 자동 결정합니다. 수집된 정보는 [실행정보] 템플릿의 `IMG_REG`/`IMG_ORG`에 반영됩니다.

`{CLOUD}` 값에 따라 Docker Hub와 해당 Cloud의 이미지 레지스트리 정보를 수집한다.

> **GitHub Actions 선택 시**: CLOUD 값에 따라 레지스트리가 자동 결정됨 (AWS→ECR, Azure→ACR, GCP→Artifact Registry). 별도 레지스트리 유형 질문 불필요.

**Jenkins 선택 시 — 1차 질문 (레지스트리 유형):**

<!--ASK_USER-->
{"title":"이미지 레지스트리 선택","questions":[
  {"question":"이미지 레지스트리 유형을 선택하세요.","type":"radio","options":["Docker Hub","{CLOUD 레지스트리}"]}
]}
<!--/ASK_USER-->

> **{CLOUD 레지스트리} 매핑**: Azure → `Azure ACR`, AWS → `AWS ECR`, GCP → `Google Artifact Registry`

**2차 질문 (유형별 조건 분기):**

- **Docker Hub** 선택 시:
<!--ASK_USER-->
{"title":"Docker Hub 정보","questions":[
  {"question":"Docker Hub Organization 또는 Username을 입력하세요.","type":"text","placeholder":"myorg"}
]}
<!--/ASK_USER-->

- **AWS ECR** 선택 시:
<!--ASK_USER-->
{"title":"AWS ECR 정보","questions":[
  {"question":"AWS 계정 ID를 입력하세요.","type":"text","placeholder":"123456789012"},
  {"question":"AWS 리전을 입력하세요.","type":"text","placeholder":"ap-northeast-2"}
]}
<!--/ASK_USER-->

- **Azure ACR** 선택 시:
<!--ASK_USER-->
{"title":"Azure ACR 정보","questions":[
  {"question":"ACR 이름을 입력하세요.","type":"text","placeholder":"acrdigitalgarage01"}
]}
<!--/ASK_USER-->

- **Google Artifact Registry** 선택 시:
<!--ASK_USER-->
{"title":"Google Artifact Registry 정보","questions":[
  {"question":"GCP 프로젝트 ID를 입력하세요.","type":"text","placeholder":"my-project-id"},
  {"question":"리전을 입력하세요.","type":"text","placeholder":"asia-northeast3"},
  {"question":"리포지토리 이름을 입력하세요.","type":"text","placeholder":"my-repo"}
]}
<!--/ASK_USER-->

### 8) 프로젝트 유형 감지 및 사전 검증

#### 프로젝트 유형 자동 감지

> 백엔드와 프론트엔드는 별도 프로젝트(리포지토리)에 있을 수 있다. 현재 프로젝트의 유형을 자동 감지하여 이후 단계에서 해당하는 파이프라인만 생성한다.

- **백엔드 감지**: `settings.gradle` 또는 `build.gradle` 존재
- **프론트엔드 감지**: `package.json` 존재 (settings.gradle 없음)
- **둘 다 있는 경우 (모노레포)**: 사용자에게 확인 후 양쪽 모두 생성

#### 기존 K8s 매니페스트 존재 검증

```bash
# deployment/k8s/ 디렉토리 존재 확인
ls deployment/k8s/
```

> `deployment/k8s/` 디렉토리가 없으면 `/npd:deploy` Step 4를 먼저 완료하도록 안내하고 중단한다.

#### 프로젝트명 자동 감지

- **SYSTEM_NAME**: `settings.gradle` 파일에서 `rootProject.name` 값을 파싱하여 자동 감지
- **FRONTEND_SERVICE**: `package.json` 파일에서 `name` 필드를 파싱하여 자동 감지
- 감지 실패 시 ASK_USER로 수동 입력

```bash
# SYSTEM_NAME 자동 감지
grep "rootProject.name" settings.gradle | sed "s/rootProject.name = '//;s/'//"

# FRONTEND_SERVICE 자동 감지
cat package.json | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])"
```

### 9) CI 도구별 추가 정보 수집

> **참고**: Jenkins 선택 시 Jenkins Credential 관련 정보를, GitHub Actions 선택 시 클라우드별 추가 정보를 수집합니다. 각각 해당하는 [실행정보] 템플릿에 반영됩니다.

**Jenkins 선택 시:**

<!--ASK_USER-->
{"title":"Jenkins 설정 정보","questions":[
  {"question":"Jenkins에 설정한 Kubernetes Cloud 이름을 입력하세요.","type":"text","placeholder":"k8s"},
  {"question":"매니페스트 레포지토리 접근용 Jenkins Credential ID를 입력하세요. (ArgoCD용 Git 인증)","type":"text","placeholder":"github-credentials"}
]}
<!--/ASK_USER-->

- `JENKINS_CLOUD_NAME`: 기본값 `k8s` 제안
- `JENKINS_GIT_CREDENTIALS`: ArgoCD 매니페스트 레포지토리 접근용

**GitHub Actions 선택 시:**

<!--ASK_USER-->
{"title":"GitHub Actions 설정 정보","questions":[
  {"question":"매니페스트 레포지토리 접근용 GitHub Secret 이름 (Username)을 입력하세요.","type":"text","placeholder":"GIT_USERNAME"},
  {"question":"매니페스트 레포지토리 접근용 GitHub Secret 이름 (Password/Token)을 입력하세요.","type":"text","placeholder":"GIT_PASSWORD"}
]}
<!--/ASK_USER-->

- `MANIFEST_SECRET_GIT_USERNAME`: GitHub Secret 이름
- `MANIFEST_SECRET_GIT_PASSWORD`: GitHub Secret 이름

**GitHub Actions + CLOUD별 추가 정보 수집:**

- **GitHub Actions + AWS**:
<!--ASK_USER-->
{"title":"AWS EKS 설정 정보","questions":[
  {"question":"ECR AWS 계정 ID를 입력하세요.","type":"text","placeholder":"123456789012"},
  {"question":"ECR 리전을 입력하세요.","type":"text","placeholder":"ap-northeast-2"},
  {"question":"EKS 클러스터명을 입력하세요.","type":"text","placeholder":"eks-myproject"}
]}
<!--/ASK_USER-->

- **GitHub Actions + Azure**:
<!--ASK_USER-->
{"title":"Azure AKS 설정 정보","questions":[
  {"question":"ACR 이름을 입력하세요.","type":"text","placeholder":"acrdigitalgarage01"},
  {"question":"리소스 그룹 이름을 입력하세요.","type":"text","placeholder":"rg-myproject"},
  {"question":"AKS 클러스터명을 입력하세요.","type":"text","placeholder":"aks-myproject"}
]}
<!--/ASK_USER-->

- **GitHub Actions + GCP**:
<!--ASK_USER-->
{"title":"GCP GKE 설정 정보","questions":[
  {"question":"GCR 리전을 입력하세요.","type":"text","placeholder":"asia-northeast3"},
  {"question":"GCP 프로젝트 ID를 입력하세요.","type":"text","placeholder":"my-project-id"},
  {"question":"GCR 리포지토리 이름을 입력하세요.","type":"text","placeholder":"my-repo"},
  {"question":"GKE 클러스터명을 입력하세요.","type":"text","placeholder":"gke-myproject"},
  {"question":"GKE Zone을 입력하세요.","type":"text","placeholder":"asia-northeast3-a"}
]}
<!--/ASK_USER-->

> `IMG_REG`와 `IMG_ORG`는 수집된 정보에서 자동 파생한다 (ArgoCD 가이드 호환용).

### 10) 매니페스트 레포지토리 정보

<!--ASK_USER-->
{"title":"매니페스트 레포지토리 정보","questions":[
  {"question":"ArgoCD가 감시할 매니페스트 레포지토리 URL을 입력하세요.\n(없으면 새로 생성합니다)","type":"text","placeholder":"https://github.com/org/project-manifest.git"}
]}
<!--/ASK_USER-->

### 11) [실행정보] 조립

수집된 정보를 `[실행정보]` 블록으로 조립한다. **CI 도구 + 클라우드/레지스트리 조합**에 따라 아래 7가지 템플릿 중 하나를 사용한다.
조립된 `[실행정보]` 블록은 이후 에이전트 호출 시 **프롬프트의 동적(작업 지시) 영역에 텍스트로 포함**하여 전달한다. 에이전트는 별도 컨텍스트에서 실행되므로, `Task(prompt=...)` 호출 시 `[실행정보]` 블록 전문을 반드시 포함해야 가이드 내 변수를 치환할 수 있다.

---

#### [실행정보] 조립 템플릿 (CI 도구별 + 클라우드/레지스트리별 7가지)

**Jenkins + Docker Hub:**
```
[실행정보]
- CI_TOOL: Jenkins
- CLOUD: {CLOUD}
- SYSTEM_NAME: {SYSTEM_NAME}
- FRONTEND_SERVICE: {FRONTEND_SERVICE}
- 레지스트리유형: DockerHub
- IMG_REG: docker.io
- IMG_ORG: {Organization/Username}
- JENKINS_CLOUD_NAME: {JENKINS_CLOUD_NAME}
- JENKINS_GIT_CREDENTIALS: {JENKINS_GIT_CREDENTIALS}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
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
- 레지스트리유형: ECR
- IMG_REG: {ECR_ACCOUNT}.dkr.ecr.{ECR_REGION}.amazonaws.com
- IMG_ORG: {SYSTEM_NAME}
- JENKINS_CLOUD_NAME: {JENKINS_CLOUD_NAME}
- JENKINS_GIT_CREDENTIALS: {JENKINS_GIT_CREDENTIALS}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
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
- 레지스트리유형: ACR
- IMG_REG: {ACR명}.azurecr.io
- IMG_ORG: {SYSTEM_NAME}
- JENKINS_CLOUD_NAME: {JENKINS_CLOUD_NAME}
- JENKINS_GIT_CREDENTIALS: {JENKINS_GIT_CREDENTIALS}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
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
- 레지스트리유형: GCR  # Google Artifact Registry (구 GCR 약칭 사용)
- IMG_REG: {GCR_REGION}-docker.pkg.dev/{GCR_PROJECT}/{GCR_REPO}
- IMG_ORG: {SYSTEM_NAME}
- JENKINS_CLOUD_NAME: {JENKINS_CLOUD_NAME}
- JENKINS_GIT_CREDENTIALS: {JENKINS_GIT_CREDENTIALS}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
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
- 레지스트리유형: ACR
- IMG_REG: {ACR_NAME}.azurecr.io
- IMG_ORG: {SYSTEM_NAME}
- ACR_NAME: {ACR명}
- RESOURCE_GROUP: {리소스그룹}
- AKS_CLUSTER: {AKS클러스터명}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
- MANIFEST_SECRET_GIT_USERNAME: {MANIFEST_SECRET_GIT_USERNAME}
- MANIFEST_SECRET_GIT_PASSWORD: {MANIFEST_SECRET_GIT_PASSWORD}
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
- 레지스트리유형: ECR
- IMG_REG: {ECR_ACCOUNT}.dkr.ecr.{ECR_REGION}.amazonaws.com
- IMG_ORG: {SYSTEM_NAME}
- ECR_ACCOUNT: {ECR_ACCOUNT}
- ECR_REGION: {ECR_REGION}
- EKS_CLUSTER: {EKS클러스터명}
- MANIFEST_REPO_URL: {MANIFEST_REPO_URL}
- MANIFEST_SECRET_GIT_USERNAME: {MANIFEST_SECRET_GIT_USERNAME}
- MANIFEST_SECRET_GIT_PASSWORD: {MANIFEST_SECRET_GIT_PASSWORD}
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
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
```

---

### 자동 진행 모드 동작 규칙

- Step 0의 사전 수집 질문은 자동 진행 모드에서도 수행 (CI 도구 선택, 레지스트리 정보 등은 자동 감지 불가)
- Step 1~2 실행 중에는 `<!--ASK_USER-->` 호출하지 않음
- 자동 감지 가능 항목: K8s 클러스터 (1개이면 자동 선택), CLOUD (CLAUDE.md에서 읽기), SYSTEM_NAME (settings.gradle), FRONTEND_SERVICE (package.json)

## 워크플로우

### Step 1. 매니페스트 레포지토리 + ArgoCD 구성 → Agent: devops-engineer (/ralph 활용)

- **GUIDE**: `resources/guides/cicd/deploy-argocd-cicd.md` (매니페스트 레포 구성 부분만 참조)
- **에이전트 프롬프트 필수 지시**: "ArgoCD 가이드의 '매니페스트 레포지토리 구성' 및 'ArgoCD Application YAML 생성' 섹션을 참조하세요. 'CI 파이프라인의 매니페스트 업데이트 스크립트 참조' 섹션은 Step 2에서 처리합니다."

> **Kustomize 파일 관리 원칙**: Step 1에서 매니페스트 레포지토리에 직접 Kustomize 파일을 생성합니다 (ArgoCD가 감시하는 "라이브" 매니페스트). Step 2에서 소스 레포지토리에도 동일 구조의 Kustomize 파일을 생성하지만, 이는 CI 파이프라인 초기 설정 및 가이드 참조용 "소스 템플릿"입니다. 실제 배포에 사용되는 것은 매니페스트 레포지토리의 Kustomize 파일이며, CI 파이프라인은 매니페스트 레포의 image tag만 업데이트합니다.

#### 매니페스트 레포 구성

- Kustomize base/overlays(dev/staging/prod) 디렉토리 구조를 매니페스트 레포지토리에 생성
- 디렉토리 구조: `{SYSTEM_NAME}/kustomize/` (백엔드), `{FRONTEND_SERVICE}/kustomize/` (프론트엔드)
- 각 서비스별 base에 deployment.yaml, service.yaml 등 기본 매니페스트 포함
- overlays에 환경별(dev/staging/prod) kustomization.yaml 포함

#### ArgoCD Application YAML 자동 생성

서비스별 x 환경별 ArgoCD Application CRD YAML 파일을 자동 생성한다.

**생성 위치**: 매니페스트 레포지토리 루트의 `argocd/` 디렉토리
**생성 파일 예시**: `argocd/{service}-{env}.yaml`

**Application YAML 템플릿:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {service}-{env}
  namespace: argocd
spec:
  project: default
  source:
    repoURL: {MANIFEST_REPO_URL}
    targetRevision: HEAD
    path: {SYSTEM_NAME}/kustomize/overlays/{env}   # 또는 {FRONTEND_SERVICE}/kustomize/overlays/{env}
  destination:
    server: https://kubernetes.default.svc
    namespace: {NAMESPACE}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

- **백엔드**: Kustomize overlay가 모든 서비스를 포함하므로, **환경별 1개 Application** 생성 (시스템 단위). Application 이름: `{SYSTEM_NAME}-{env}`
- **프론트엔드**: `{FRONTEND_SERVICE}` 환경별 1개 Application 생성. Application 이름: `{FRONTEND_SERVICE}-{env}`
- 환경(env): `dev`, `staging`, `prod` 3개
- **총 생성 수**: (백엔드 1 + 프론트엔드 1) x 3환경 = 6개

#### ArgoCD Application 등록

생성된 YAML을 K8s 클러스터에 적용하여 ArgoCD Application을 등록한다.

```bash
kubectl apply -f argocd/
```

> 이 `kubectl apply`는 ArgoCD Application CRD 등록용이며, 애플리케이션 배포용 kubectl apply가 아님.

- **CONTEXT**: 조립된 `[실행정보]` 블록 포함
- **ArgoCD Private 레포 인증**: 매니페스트 레포지토리가 Private인 경우, ArgoCD 인증 등록에 Git 크리덴셜이 필요합니다. Jenkins 선택 시 `JENKINS_GIT_CREDENTIALS`에 등록된 Username/Password를 사용하고, GitHub Actions 선택 시 `MANIFEST_SECRET_GIT_USERNAME`/`MANIFEST_SECRET_GIT_PASSWORD`에 해당하는 값을 사용자에게 확인하여 전달하세요.
- **EXPECTED OUTCOME**:
  - 매니페스트 레포지토리 구조 생성 (Kustomize base/overlays)
  - ArgoCD 매니페스트 레포지토리 인증 등록 (Private 레포인 경우)
  - ArgoCD Application YAML 파일 생성 (`argocd/*.yaml`)
  - ArgoCD Application 등록 완료
  - `deploy-argocd-prepare.md` 결과 보고서 작성 (프로젝트 루트)

### Step 2. CI/CD 파이프라인 작성 → Agent: devops-engineer (/ralph 활용)

- **에이전트 프롬프트 필수 지시**: "가이드의 Deploy 단계(kubectl apply)는 무시하세요. 대신 CI 파이프라인의 마지막 단계로 manifest repo image tag 업데이트를 포함하세요. 각 CI 가이드(`deploy-jenkins-cicd-*.md`, `deploy-actions-cicd-*.md`)의 `Update Manifest Repository` stage (Jenkins) 또는 `update-manifest` job (GitHub Actions)을 참조하여 결합하세요."

#### 가이드 선택 로직

```
IF CI_TOOL == Jenkins:
    백엔드 -> resources/guides/cicd/deploy-jenkins-cicd-back.md
    프론트엔드 -> resources/guides/cicd/deploy-jenkins-cicd-front.md
ELSE IF CI_TOOL == GitHubActions:
    백엔드 -> resources/guides/cicd/deploy-actions-cicd-back.md
    프론트엔드 -> resources/guides/cicd/deploy-actions-cicd-front.md
```

> 클라우드별 분기 불필요. 가이드 내 조건부 섹션이 `[실행정보]`의 CLOUD 값에 따라 registry login 방식을 분기.

**추가 참조 가이드**: `resources/guides/cicd/deploy-argocd-cicd.md` (manifest repo 업데이트 스크립트 부분만)

#### 백엔드 CI/CD 파이프라인 작성 (에이전트 호출)

- **GUIDE**: 위 로직에서 결정된 백엔드 가이드 + ArgoCD 가이드 (manifest 업데이트 스크립트)
- **CONTEXT**: 조립된 `[실행정보]` 블록 포함
- **TASK**: 가이드를 참조하여 CI/CD 파이프라인 파일 생성 (빌드+푸시+manifest tag 업데이트)
- **EXPECTED OUTCOME**:
  - Jenkins: `deployment/cicd/Jenkinsfile`, `deployment/cicd/kustomize/*`, `deployment/cicd/config/*`, `deployment/cicd/jenkins-pipeline-guide.md`
  - GitHub Actions: `.github/workflows/backend-cicd.yaml`, `.github/kustomize/*`, `.github/config/*`, `deployment/cicd/actions-pipeline-guide.md`

#### 프론트엔드 CI/CD 파이프라인 작성 (에이전트 호출)

- **GUIDE**: 위 로직에서 결정된 프론트엔드 가이드 + ArgoCD 가이드 (manifest 업데이트 스크립트)
- **CONTEXT**: 조립된 `[실행정보]` 블록 포함
- **TASK**: 가이드를 참조하여 CI/CD 파이프라인 파일 생성 (빌드+푸시+manifest tag 업데이트)
- **EXPECTED OUTCOME**:
  - Jenkins: `deployment/cicd/Jenkinsfile` (프론트엔드용), `deployment/cicd/kustomize/*`, `deployment/cicd/config/*`, `deployment/cicd/jenkins-pipeline-guide.md`
  - GitHub Actions: `.github/workflows/frontend-cicd.yaml`, `.github/kustomize/*`, `.github/config/*`, `deployment/cicd/actions-pipeline-guide.md`

#### 백엔드/프론트엔드 감지 로직

> 백엔드와 프론트엔드는 별도 프로젝트(리포지토리)에 있을 수 있다. 스킬은 현재 프로젝트의 유형을 자동 감지하여 해당하는 파이프라인만 생성한다.
> - **백엔드 감지**: `settings.gradle` 또는 `build.gradle` 존재
> - **프론트엔드 감지**: `package.json` 존재 (settings.gradle 없음)
> - **둘 다 있는 경우**: 사용자에게 확인 후 양쪽 모두 생성
>
> **⚠️ 모노레포(둘 다 있는 경우) 파일 충돌 방지:**
> - Jenkins: 백엔드 `deployment/cicd/Jenkinsfile-backend`, 프론트엔드 `deployment/cicd/Jenkinsfile-frontend`로 분리
> - Jenkins Kustomize: 백엔드 `deployment/cicd/kustomize-backend/`, 프론트엔드 `deployment/cicd/kustomize-frontend/`로 분리
> - GitHub Actions: 워크플로우 파일명이 이미 분리됨 (`backend-cicd.yaml`, `frontend-cicd.yaml`)
> - GitHub Actions Kustomize: 백엔드 `.github/kustomize-backend/`, 프론트엔드 `.github/kustomize-frontend/`로 분리

### Step 3. 완료 보고

스킬 레벨에서 직접 수행 (에이전트 호출 없음).

```
## CI/CD 파이프라인 구성 완료

### 환경 정보
- CI 도구: {Jenkins / GitHub Actions}
- CD 도구: ArgoCD (GitOps)
- Cloud: {AWS / Azure / GCP}
- K8s 클러스터: {클러스터명}

### Step 1: 매니페스트 레포지토리 + ArgoCD 산출물
- 매니페스트 레포지토리: {MANIFEST_REPO_URL}
- ArgoCD Application YAML: argocd/*.yaml
- ArgoCD Application 등록: 완료
- ArgoCD 준비 보고서: `deploy-argocd-prepare.md`

### Step 2: CI/CD 파이프라인 산출물
- 백엔드: {파이프라인 파일 경로} (빌드+푸시+manifest tag 업데이트)
- 프론트엔드: {파이프라인 파일 경로} (빌드+푸시+manifest tag 업데이트)

### 다음 단계
1. 매니페스트 레포지토리를 원격에 push
2. CI 파이프라인 실행하여 전체 흐름 검증 (빌드 → 푸시 → manifest 업데이트 → ArgoCD 자동 배포)
```

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |
| 2 | CI 도구 선택(Jenkins/GitHub Actions)에 따라 가이드 선택 매트릭스를 참조하여 해당하는 가이드만 참조할 것 (클라우드별 분기 불필요) |
| 3 | CI 파이프라인에 kubectl apply를 포함하지 않을 것. 마지막 단계는 manifest repo image tag 업데이트여야 함 |
| 4 | `[실행정보]` 블록을 에이전트 프롬프트에 반드시 포함할 것 — CI 도구 + 레지스트리유형 조합에 맞는 템플릿 사용 |
| 5 | GitHub Actions 가이드 내 클라우드별 조건부 섹션이 `[실행정보]`의 CLOUD 값에 따라 올바르게 적용되도록 할 것 |
| 6 | 사전 도구 체크는 설치 여부 확인 + 미설치 시 가이드 링크 제공만 수행. 자동 설치 금지 |

## 완료 조건

- [ ] 매니페스트 레포지토리 구조가 생성됨 (Kustomize base/overlays)
- [ ] ArgoCD Application YAML이 서비스별 x 환경별로 생성·등록됨
- [ ] CI/CD 파이프라인 파일이 생성됨 (Jenkinsfile 또는 GitHub Actions Workflow) — kubectl apply 없이 manifest repo image tag 업데이트 포함
- [ ] 완료 보고서가 작성됨
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (매니페스트 레포 구조, ArgoCD YAML, 파이프라인 파일)
2. ArgoCD Application YAML 유효성 검사 (`kubectl apply --dry-run=client -f argocd/`)
3. Kustomize 유효성 검사 (`kubectl kustomize` dry-run)
4. 파이프라인 파일 문법 검증 (변수 참조 `${variable}` 사용, `\${variable}` 사용 금지 등)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.
