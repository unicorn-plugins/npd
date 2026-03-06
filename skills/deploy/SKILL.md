---
name: deploy
description: 배포 단계 AI 협업 — DevOps 엔지니어가 컨테이너 빌드·K8s 배포 수행
type: orchestrator
user-invocable: true
---

# Deploy

[NPD Deploy 활성화]

## 목표

DevOps 엔지니어가 컨테이너 이미지 빌드 → 컨테이너 실행 →
Kubernetes 배포 순서로 배포 환경을 구축함.

주의사항: 중간 단계부터 시작할 때도 각 단계별 승인 여부를 선택하는 Step 0은 항상 수행하여 진행 모드를 설정해야 합니다.

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

- **자동 진행** 선택 시 → Step 0(진행 모드·시작 Step·배포 환경 선택)에서 필요한 정보를 모두 수집한 뒤, 워크플로우 실행 중(Step 1~5)에는 `<!--ASK_USER-->`를 호출하지 않고 아래 규칙으로 자동 처리한다:
  - **단계 간 승인**: 생략 (연속 실행)
  - **자동 감지 가능한 정보** (Cloud CLI 로그인 여부, SSH 접속 테스트, Web Server 설치 여부, SSL 도메인 등): 명령어 실행 결과로 자동 판단하고, 실패 시에만 사용자에게 질문
  - **VM Host 선택**: `~/.ssh/config`에 후보가 1개면 자동 선택, 2개 이상이면 Step 0에서 미리 수집
  - **기타 선택지**: 기본값 또는 자동 감지 결과를 사용

### 시작 Step 선택

<!--ASK_USER-->
{"title":"시작 단계 선택","questions":[
  {"question":"어떤 단계부터 시작하시겠습니까?","type":"radio","options":[
    "Step 1: 배포 사전 준비 (처음부터)",
    "Step 2: 컨테이너 이미지 빌드 & 푸시",
    "Step 3: 컨테이너 실행 검증",
    "Step 4: K8s 매니페스트 작성 & 배포",
    "Step 5: 배포 완료 보고"
  ]}
]}
<!--/ASK_USER-->

선택된 Step 이전 단계는 건너뛴다. 선택된 시작 Step 번호를 `{시작Step}`으로 저장하여 이후 조건부 질문 실행에 사용한다.

### 자동 진행 모드: VM Host 사전 수집

> **조건**: 자동 진행 모드이고, `~/.ssh/config`에 Host 후보가 2개 이상일 때만 수행

`~/.ssh/config`를 파싱하여 후보가 2개 이상이면 여기서 미리 선택받는다:

<!--ASK_USER-->
{"title":"배포 대상 VM 사전 선택 (자동 진행용)","questions":[
  {"question":"자동 진행 모드입니다. ~/.ssh/config에 VM Host가 여러 개 감지되었습니다.\n배포에 사용할 VM을 선택하세요.\n\n※ 용도: 컨테이너 빌드·실행 + Web Server (Nginx Proxy)","type":"radio","options":["{파싱된 Host alias 목록}"]}
]}
<!--/ASK_USER-->

후보가 1개이면 자동 선택한다. 선택된 값을 이후 Step에서 `{VM.HOST}`로 사용한다.

## 워크플로우

### Step 1. 배포 사전 준비

배포에 필요한 로컬 도구와 VM 원격 도구를 자동으로 설치하고, VM 접속 정보를 수집한다.

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/deploy/deploy-pre-setup.md` 참조
- **TASK**: CLOUD 판단 → 로컬 도구 설치(kubectl, kubens, helm, Cloud CLI) → Cloud CLI 로그인 확인 → VM 생성 안내 → `~/.ssh/config` 파싱 → SSH 접속 테스트 → VM 원격 도구 설치(Cloud CLI, Docker, kubectl, kubens, helm, JDK)
- **EXPECTED OUTCOME**: 로컬/VM 도구 설치 완료, VM 접속 정보(`VM.HOST`, `VM.IP`, `VM.USERID`, `VM.KEY파일`) 수집

> **자동 진행 모드 동작**: Step 1 내 모든 `<!--ASK_USER-->`를 생략하고 아래 규칙으로 자동 처리한다.
> - **1-1 CLOUD**: CLAUDE.md에서 읽기 → 없으면 에러 중단
> - **1-3 CLI 로그인**: 로그인 명령어(`aws sts get-caller-identity` / `az account show` / `gcloud auth list`)로 자동 확인 → 미로그인이면 에러 중단
> - **1-4 VM 준비**: `~/.ssh/config`에 Host 엔트리가 1개 이상이면 "준비 완료"로 간주 → 0개이면 에러 중단
> - **1-5 VM 선택**: Host 후보 1개 → 자동 선택 / 2개 이상 → Step 0에서 미리 수집한 값 사용
> - **1-6 SSH 실패**: 1회 자동 재시도 → 재실패 시 에러 중단

#### 1-1. CLOUD 판단

`CLAUDE.md`의 `## NPD 워크플로우 상태 > ### design`에서 `CLOUD` 값을 읽는다. 없으면:

<!--ASK_USER-->
{"title":"Cloud 서비스 선택","questions":[
  {"question":"배포할 Cloud 서비스를 선택하세요.","type":"radio","options":["AWS","Azure","GCP"]}
]}
<!--/ASK_USER-->

#### 1-2. 로컬 도구 자동 설치

가이드의 1-2절 참조. OS 감지 후 kubectl, kubens/kubectx, helm, {CLOUD} CLI를 미설치분만 자동 설치한다.

#### 1-3. Cloud CLI 로그인 확인

가이드의 1-3절 참조. 로그인이 안 되어 있으면:

<!--ASK_USER-->
{"title":"Cloud CLI 로그인 확인","questions":[
  {"question":"{CLOUD} CLI 로그인이 필요합니다.\n\n로그인 완료 후 알려주세요.\n참고: https://github.com/unicorn-plugins/npd/blob/main/resources/guides/setup/prepare.md#cloud-cli-설치-및-로그인","type":"radio","options":["로그인 완료"]}
]}
<!--/ASK_USER-->

#### 1-4. VM 생성 안내

<!--ASK_USER-->
{"title":"VM 준비 확인","questions":[
  {"question":"배포용 VM이 {CLOUD}에 준비되어 있나요?\n\n※ 용도: 컨테이너 빌드·실행 + Web Server (Nginx Proxy)\n\nVM이 있고 ~/.ssh/config에 접속 정보가 등록되어 있어야 합니다.","type":"radio","options":["준비 완료","아직 없음"]}
]}
<!--/ASK_USER-->

**"아직 없음"** 선택 시: 가이드의 1-4절 참조. {CLOUD}별 VM 생성 URL(https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-vm.md) 안내 + `~/.ssh/config` 등록 안내 후 완료 대기:

<!--ASK_USER-->
{"title":"VM 생성 완료 확인","questions":[
  {"question":"VM 생성과 ~/.ssh/config 등록이 완료되면 알려주세요.","type":"radio","options":["완료"]}
]}
<!--/ASK_USER-->

#### 1-5. ~/.ssh/config 파싱

가이드의 1-5절 참조. `~/.ssh/config`에서 Host 엔트리를 추출하여 사용자에게 선택하게 한다:

<!--ASK_USER-->
{"title":"배포 대상 VM 선택","questions":[
  {"question":"~/.ssh/config에서 배포 대상 VM의 Host를 선택하세요.\n\n※ 용도: 컨테이너 빌드·실행 + Web Server (Nginx Proxy)","type":"radio","options":["{파싱된 Host alias 목록}"]}
]}
<!--/ASK_USER-->

선택된 Host에서 VM.HOST, VM.IP, VM.USERID, VM.KEY파일을 추출한다.

#### 1-6. SSH 접속 테스트

가이드의 1-6절 참조. 실패 시:

<!--ASK_USER-->
{"title":"SSH 접속 실패","questions":[
  {"question":"SSH 접속에 실패했습니다. ~/.ssh/config의 접속 정보를 확인하고 다시 시도하시겠습니까?\n\n에러: {에러 메시지}","type":"radio","options":["다시 시도","건너뛰기 (VM 도구 수동 설치)"]}
]}
<!--/ASK_USER-->

#### 1-7. VM 원격 도구 설치

가이드의 1-7절 참조. SSH로 VM에 접속하여 미설치 도구를 자동 설치한다.

#### 1-8. 완료 보고

가이드의 1-8절 템플릿으로 로컬/VM 설치 도구 목록 + VM 접속 방법(`ssh {VM_HOST_ALIAS}`)을 보고한다.

### 배포 환경 선택

> **소속**: Step 0의 마지막 서브섹션. 워크플로우 실행(Step 1~5) 전에 수행한다.

사용자에게 배포 환경을 확인하여 적절한 가이드를 참조함.

> **자동 진행 모드 동작**: "배포 환경 선택"은 Step 0의 사전 수집 단계이므로, 자동 진행 모드에서도 1차~4차 질문을 수행하여 정보를 수집한다.
> 단, 자동 감지 가능한 항목은 질문을 생략한다:
> - **3차 K8s 클러스터**: 감지 결과 1개이면 자동 선택, 2개 이상이면 질문
> - **4차 리소스 설정**: 자동 진행 모드에서는 placeholder 기본값(파드수=2, CPU=0.25/1, 메모리=256/1024)을 사용하고 예외 설정은 "없음"으로 처리

> **조건부 실행 규칙**: 시작 Step에 따라 필요한 질문만 수행한다.
> - **Cloud 판단 (1-1)**: 시작 Step ≤ 4이면 수행 (CLAUDE.md에 이미 있으면 생략)
> - **VM 정보 (1-4~1-6)**: 시작 Step이 1 또는 3이면 수행
> - **1차+2차 (레지스트리)**: 시작 Step ≤ 4이면 수행 (Step 4 시작 시에도 K8s 매니페스트의 이미지 경로에 필요)
> - **3차 (K8S 클러스터)**: 시작 Step ≤ 4이면 수행
> - **4차 (서비스별 리소스)**: 시작 Step ≤ 4이면 수행

### 이미지 레지스트리 및 VM 정보 수집

Step 3(컨테이너 실행 검증) 이전에 이미지 레지스트리 유형과 VM 접속 정보를 수집한다.
`{CLOUD}` 값(CLAUDE.md에서 읽음)에 따라 Docker Hub와 해당 Cloud의 이미지 레지스트리만 선택지로 표시한다.

#### 1차 질문 (공통)

> **조건**: 시작 Step ≤ 4일 때만 수행

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

#### 3차: K8S 클러스터 자동 감지

> **조건**: 시작 Step ≤ 4일 때만 수행

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

**분기 처리:**

- **매칭 1개 이상** → 감지된 컨텍스트 목록을 사용자에게 제시하고 배포 대상을 확인받음:

<!--ASK_USER-->
{"title":"K8s 클러스터 선택","questions":[
  {"question":"{CLOUD}에 연결된 클러스터가 감지되었습니다. 배포 대상 클러스터를 선택하세요.","type":"radio","options":["{감지된 컨텍스트 목록}"]}
]}
<!--/ASK_USER-->

- **매칭 0개** → 클러스터가 감지되지 않음을 안내하고, 아래 가이드를 참조하여 클러스터 생성 및 Web 서버 구성을 요청:
  - 참조: [K8s 클러스터 생성 및 Web 서버 구성 가이드](https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-k8s.md)

**컨텍스트 전환 및 클러스터명 추출:**
```bash
kubectx {선택된 컨텍스트}
```

클러스터명은 컨텍스트 이름에서 추출한다:
- AWS: `arn:aws:eks:{region}:{account}:cluster/{클러스터명}` → 마지막 `/` 뒤
- Azure: 컨텍스트 이름 자체가 클러스터명
- GCP: `gke_{project}_{region}_{클러스터명}` → 마지막 `_` 뒤

**NAMESPACE 결정:**

네임스페이스는 `{ROOT}` (프로젝트명, CLAUDE.md의 시스템명)를 기본값으로 사용한다.

#### 4차: K8S 배포 리소스 설정 (서비스별)

> **조건**: 시작 Step ≤ 4일 때만 수행

`docs/deploy/run-container-{back,front,ai}-result.md`에서 서비스 목록을 감지한 후, 리소스 설정을 수집한다.

##### 4-1. 일괄 기본값 설정

감지된 서비스 목록을 안내한 뒤, 모든 서비스에 적용할 기본값을 질문한다:

<!--ASK_USER-->
{"title":"K8S 리소스 기본값 설정","questions":[
  {"question":"감지된 서비스: {서비스 목록}\n\n모든 서비스에 적용할 기본 파드 수를 입력하세요.","type":"text","placeholder":"2"},
  {"question":"기본 CPU 리소스를 입력하세요 (요청값/최대값, 단위: core).","type":"text","placeholder":"0.25/1"},
  {"question":"기본 메모리 리소스를 입력하세요 (요청값/최대값, 단위: MB).","type":"text","placeholder":"256/1024"}
]}
<!--/ASK_USER-->

##### 4-2. 서비스별 예외 설정

<!--ASK_USER-->
{"title":"서비스별 예외 설정","questions":[
  {"question":"특정 서비스에 다른 리소스를 지정하시겠습니까?","type":"radio","options":["없음 (모두 기본값 적용)","있음 (서비스별 지정)"]}
]}
<!--/ASK_USER-->

**"있음"** 선택 시: 예외 서비스를 선택받고, 선택된 서비스별로 파드수·CPU·메모리를 개별 질문한다.

<!--ASK_USER-->
{"title":"예외 서비스 선택","questions":[
  {"question":"기본값과 다르게 설정할 서비스를 선택하세요. (복수 선택 가능)","type":"multiSelect","options":["{감지된 서비스 목록}"]}
]}
<!--/ASK_USER-->

선택된 각 서비스에 대해 AskUserQuestion으로 파드수·CPU·메모리를 질문한다 (1회 최대 4개 질문).
예외로 지정되지 않은 서비스는 4-1의 기본값을 그대로 사용한다.

수집된 값을 K8s 리소스 단위로 변환하여 `[실행정보]`에 반영한다:
- **파드수**: 입력값 그대로 사용
- **CPU**: core → millicore 변환 (예: `0.25/1` → `250m/1000m`)
- **메모리**: MB → Mi 변환 (예: `256/1024` → `256Mi/1024Mi`)

#### [실행정보] 조립 규칙

> **조건부 조립**: 시작 Step에 따라 수집되지 않은 필드는 `[실행정보]`에서 생략한다.
> - 레지스트리 관련 필드 (레지스트리유형, REGISTRY_URL 등): Step 2 또는 4 실행 시
> - K8S 관련 필드 (CLUSTER, NAMESPACE, 서비스 리소스): Step 4 실행 시에만
> - VM 관련 필드 (HOST, KEY파일 등): Step 1 또는 3 실행 시에만

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
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
  - 서비스 리소스:
    - {서비스명}: 파드수={N}, CPU={요청값}m/{최대값}m, 메모리={요청값}Mi/{최대값}Mi
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
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
  - 서비스 리소스:
    - {서비스명}: 파드수={N}, CPU={요청값}m/{최대값}m, 메모리={요청값}Mi/{최대값}Mi
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
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
  - 서비스 리소스:
    - {서비스명}: 파드수={N}, CPU={요청값}m/{최대값}m, 메모리={요청값}Mi/{최대값}Mi
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
- K8S
  - CLUSTER: {클러스터명}
  - NAMESPACE: {네임스페이스}
  - 서비스 리소스:
    - {서비스명}: 파드수={N}, CPU={요청값}m/{최대값}m, 메모리={요청값}Mi/{최대값}Mi
```

> `{ROOT}`는 CLAUDE.md의 시스템명을 참조하여 결정한다.

#### CLAUDE.md 상태 기록 (`/clear` 대비)

`[실행정보]` 조립 완료 후, 프로젝트 루트 `CLAUDE.md`의 `## NPD 워크플로우 상태` 섹션 하위에
`### deploy` 서브섹션을 생성(이미 있으면 갱신):

```
## NPD 워크플로우 상태
### deploy
- 진행 모드: {선택값}
- CLOUD: {선택값}
- 레지스트리유형: {DockerHub/ECR/ACR/GCR}
- IMG_REG: {값}
- IMG_ORG: {값}
- ECR_ACCOUNT: {값}  ← ECR인 경우
- ECR_REGION: {값}  ← ECR인 경우
- ACR명: {값}  ← ACR인 경우
- GCR_PROJECT: {값}  ← GCR인 경우
- GCR_REGION: {값}  ← GCR인 경우
- GCR_REPO: {값}  ← GCR인 경우
- VM_HOST: {값}
- K8S_CLUSTER: {값}
- K8S_NAMESPACE: {값}
- 마지막 완료 Step: {Step명}
```

클라우드별 전용 필드는 해당 레지스트리유형 선택 시에만 기록하고, 나머지는 생략.
각 Step 완료 시 `마지막 완료 Step` 값을 갱신.
VM_HOST는 Step 1-5(`~/.ssh/config` 파싱) 완료 후 기록.
이 기록은 이후 `/npd:cicd` 스킬에서 중복 질문 없이 환경 정보를 재사용하기 위한 목적.

### 환경 선택 분기 규칙
1. `[실행정보]`의 `레지스트리유형` 필드에 따라 해당 유형에 맞는 이미지 경로 체계(`REGISTRY_URL`)를 사용한다
2. 중간 Step 시작으로 레지스트리 정보가 없는 경우, 배포 환경 선택에서 수집하여 보충한다


### Step 2. 컨테이너 이미지 빌드 & 푸시 → Agent: devops-engineer (`/ralph` 활용)

#### PREV_ACTION: VM 소스 동기화

Step 2 시작 전, 로컬 소스를 커밋 & 푸시하고 VM에서 소스를 준비한다.

**로컬 소스 커밋 & 푸시:**
```bash
git add -A && git commit -m "deploy: Step 2 시작 전 소스 동기화" && git push
```

**VM 소스 준비 (clone 또는 pull):**
```bash
# VM에 소스가 없으면 clone, 있으면 pull
ssh {VM.HOST} 'if [ -d ~/workspace/{ROOT} ]; then cd ~/workspace/{ROOT} && git pull; else mkdir -p ~/workspace && cd ~/workspace && git clone https://github.com/{org}/{repo}.git && cd {ROOT}; fi'
```

> Private repository인 경우 PAT를 사용한다:
> ```bash
> GIT_PAT=$(gh auth token)
> ssh {VM.HOST} "if [ -d ~/workspace/{ROOT} ]; then cd ~/workspace/{ROOT} && git pull; else mkdir -p ~/workspace && cd ~/workspace && git clone https://\${GIT_PAT}@github.com/{org}/{repo}.git && cd {ROOT} && git remote set-url origin https://github.com/{org}/{repo}.git; fi"
> ```

#### TASK: 백엔드·프론트엔드·AI 병렬 빌드 & 푸시

3개 서비스를 **서브에이전트로 병렬 실행**한다. 각 에이전트는 해당 가이드를 참조하여 Dockerfile 작성 → 이미지 빌드 → 레지스트리 푸시를 수행한다.

| 서비스 | GUIDE | 주요 산출물 |
|--------|-------|-----------|
| 백엔드 | `{PLUGIN_DIR}/resources/guides/deploy/build-image-back.md` | `deployment/container/Dockerfile-backend` |
| 프론트엔드 | `{PLUGIN_DIR}/resources/guides/deploy/build-image-front.md` | `deployment/container/Dockerfile-frontend`, `nginx.conf` |
| AI | `{PLUGIN_DIR}/resources/guides/deploy/build-image-ai.md` | `deployment/container/Dockerfile-ai` |

- **CONTEXT**: 조립된 `[실행정보]` 블록을 각 에이전트 프롬프트에 포함
- **EXPECTED OUTCOME**: Dockerfile 생성, 이미지 빌드 성공, 이미지 푸시 성공

#### POST_ACTION: 산출물 커밋 & 동기화

Step 2 완료 후, VM에서 생성된 산출물(Dockerfile, build guide 등)을 원격 저장소에 반영하고 로컬과 동기화한다.

**VM에서 커밋 & 푸시 (Public 저장소):**
```bash
ssh {VM.HOST} 'cd ~/workspace/{ROOT} && git add -A && git commit -m "deploy: Step 2 산출물 (Dockerfile, build-image guide)" && git push'
```

**VM에서 커밋 & 푸시 (Private 저장소 — PAT 기반):**
```bash
GIT_PAT=$(gh auth token)

ssh {VM.HOST} "cd ~/workspace/{ROOT} \
  && git add -A \
  && git commit -m 'deploy: Step 2 산출물 (Dockerfile, build-image guide)' \
  && git remote set-url origin https://${GIT_PAT}@github.com/{org}/{repo}.git \
  && git push \
  && git remote set-url origin https://github.com/{org}/{repo}.git"
```

**로컬 동기화:**
```bash
git pull
```

### Step 3. 컨테이너 실행 검증 → Agent: devops-engineer (`/ultraqa` 활용)

#### PREV_ACTION: VM 소스 동기화 및 환경파일 전송

Step 2 POST_ACTION에서 푸시된 산출물을 VM에 반영하고, 로컬 `.env` 파일을 VM에 복사한다.

**VM 소스 동기화:**
```bash
ssh {VM.HOST} 'cd ~/workspace/{ROOT} && git pull'
```

> Private repository인 경우:
> ```bash
> GIT_PAT=$(gh auth token)
> ssh {VM.HOST} "cd ~/workspace/{ROOT} && git remote set-url origin https://\${GIT_PAT}@github.com/{org}/{repo}.git && git pull && git remote set-url origin https://github.com/{org}/{repo}.git"
> ```

**로컬 `.env` 파일을 VM에 복사:**
```bash
scp .env {VM.HOST}:~/workspace/{ROOT}/.env
```

> `.env`는 `.gitignore`에 포함되어 git으로 전달되지 않으므로 `scp`로 직접 복사한다.
> AI 서비스 컨테이너 실행 시 `--env-file`로 참조한다.

#### VM 백킹서비스 배포 (선행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-service-container.md` 참조
- **CONTEXT**: 조립된 `[실행정보]` 블록을 프롬프트에 포함
- **TASK**: VM에 SSH 접속하여 docker-compose로 백킹서비스(DB, Redis, MQ)를 기동하고 health check 수행. Cloud MQ 사용 시 프로비저닝 포함
- **EXPECTED OUTCOME**: 모든 백킹서비스 healthy 확인, `docs/deploy/backing-service-container-result.md` 작성

> 백킹서비스가 정상 기동된 후에야 아래 애플리케이션 컨테이너 실행이 가능하다.

#### TASK: 백엔드·프론트엔드·AI 병렬 컨테이너 실행

3개 서비스를 **서브에이전트로 병렬 실행**한다. 각 에이전트는 해당 가이드를 참조하여 컨테이너를 실행하고 정상 동작을 확인한다.

| 서비스 | GUIDE |
|--------|-------|
| 백엔드 | `{PLUGIN_DIR}/resources/guides/deploy/run-container-back.md` |
| 프론트엔드 | `{PLUGIN_DIR}/resources/guides/deploy/run-container-front.md` |
| AI | `{PLUGIN_DIR}/resources/guides/deploy/run-container-ai.md` |

- **CONTEXT**: 조립된 `[실행정보]` 블록을 각 에이전트 프롬프트에 포함
- **EXPECTED OUTCOME**: 백엔드·프론트엔드·AI 서비스 컨테이너 정상 실행 확인, `docs/deploy/run-container-{back,front,ai}-result.md` 작성

#### POST_ACTION: 산출물 커밋 & 동기화

Step 3 완료 후, VM에서 생성된 산출물(결과 보고서, 컨테이너 실행 결과서 등)을 원격 저장소에 반영하고 로컬과 동기화한다.

**VM에서 커밋 & 푸시 (Public 저장소):**
```bash
ssh {VM.HOST} 'cd ~/workspace/{ROOT} && git add -A && git commit -m "deploy: Step 3 산출물 (backing-service-result, run-container-result)" && git push'
```

**VM에서 커밋 & 푸시 (Private 저장소 — PAT 기반):**
```bash
GIT_PAT=$(gh auth token)

ssh {VM.HOST} "cd ~/workspace/{ROOT} \
  && git add -A \
  && git commit -m 'deploy: Step 3 산출물 (backing-service-result, run-container-result)' \
  && git remote set-url origin https://${GIT_PAT}@github.com/{org}/{repo}.git \
  && git push \
  && git remote set-url origin https://github.com/{org}/{repo}.git"
```

**로컬 동기화:**
```bash
git pull
```

### Step 4. Kubernetes 배포 → Agent: devops-engineer (`/ralph` 활용)

#### K8s 백킹서비스 배포 (선행)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-service-k8s.md` 참조
- **CONTEXT**: 조립된 `[실행정보]` 블록을 프롬프트에 포함
- **TASK**: K8s 클러스터에 kubectl/helm으로 백킹서비스(DB, Redis)를 Bitnami Helm 차트로 설치하고 health check 수행. Cloud MQ 사용 시 프로비저닝 포함
- **EXPECTED OUTCOME**: 모든 백킹서비스 healthy 확인, `docs/deploy/backing-service-k8s-result.md` 작성

> 백킹서비스가 K8s 클러스터에 정상 배포된 후에야 아래 애플리케이션 K8s 배포가 가능하다.

#### TASK: K8s 매니페스트 작성 및 배포

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/deploy/deploy-k8s-back.md`, `{PLUGIN_DIR}/resources/guides/deploy/deploy-k8s-front.md`, `{PLUGIN_DIR}/resources/guides/deploy/deploy-k8s-ai.md`
- **CONTEXT**: 조립된 `[실행정보]` 블록을 프롬프트에 포함
- **TASK**: K8s Deployment, Service, Ingress 매니페스트를 작성하고 배포
- **EXPECTED OUTCOME**: `deploy/k8s/` 매니페스트 파일 생성, 배포 성공

#### POST_ACTION: Nginx Web Server Proxy 설정

매니페스트 배포 후 Ingress가 생성되면, 외부 HTTPS 접근을 위해 Nginx Proxy 설정을 수행한다.

> **이 POST_ACTION은 배포 스킬(SKILL.md) 레벨에서 실행된다.** 사용자에게 묻는 작업(1~3)은 Agent가 아닌 스킬이 직접 수행한다.

> **자동 진행 모드 동작**: 아래 사용자 확인 단계(1~3)의 `<!--ASK_USER-->`를 생략하고 자동 처리한다.
> - **1. Web Server 설치 확인**: `ssh {VM.HOST} 'nginx -v'`로 자동 확인 → 미설치면 에러 중단
> - **2. VM 접속 정보**: `{VM.HOST}`를 `{WEB_SERVER_SSH_HOST}`로 재사용 (동일 VM 전제)
> - **3. SSL 도메인**: `ssh {WEB_SERVER_SSH_HOST}`로 `/etc/nginx/sites-available/default`의 `server_name` 값을 읽어 자동 사용 → 감지 실패 시 에러 중단

**[사용자 확인 단계]** (스킬이 직접 수행, 자동 진행 모드에서는 위 규칙으로 대체)

**1. Web Server 설치 확인:**

<!--ASK_USER-->
{"title":"Web Server 설치 확인","questions":[
  {"question":"K8s 관리 VM에 Nginx Web Server가 설치되어 있나요?\n\n미설치 시 참고: https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-k8s.md > Web서버 설치","type":"radio","options":["설치 완료","아직 없음"]}
]}
<!--/ASK_USER-->

**"아직 없음"** 선택 시: 가이드 링크를 안내하고 설치 완료 대기.

**2. VM 접속 정보:**

Step 1에서 수집한 `{VM.HOST}`를 `{WEB_SERVER_SSH_HOST}`로 재사용한다 (컨테이너 실행 VM = Web Server VM 동일 전제).

**3. SSL 도메인 확인:**

선택한 VM에 SSH 접속하여 `/etc/nginx/sites-available/default`의 `server_name` 값을 읽은 후 사용자에게 확인:

<!--ASK_USER-->
{"title":"SSL 도메인 확인","questions":[
  {"question":"Web Server의 SSL 도메인을 확인합니다.\n\n감지된 server_name: `{감지된 server_name}`\n\n이 도메인이 맞습니까?","type":"radio","options":["맞음","직접 입력"]}
]}
<!--/ASK_USER-->

**"직접 입력"** 선택 시: 사용자에게 SSL 도메인을 입력받음 (예: `mydomain.com`, `app.example.co.kr`, `{ID}.{VM Public IP}.nip.io` 등). 확인된 값을 `{SSL_DOMAIN}`으로 저장.

**[자동 실행 단계]** (Agent 위임 가능)

4. **Ingress ADDRESS 확인**: `kubectl get ing -n {K8S_NAMESPACE}`로 Ingress ADDRESS 취득

5. **API 도메인 SSL 인증서 발급**: K8s Ingress는 프론트엔드(`{SSL_DOMAIN}`)와 백엔드 API(`api.{SSL_DOMAIN}`)를 별도 Host로 분리하므로, API 도메인용 SSL 인증서도 필요하다.
   ```bash
   ssh {WEB_SERVER_SSH_HOST} "sudo certbot certonly --nginx -d api.{SSL_DOMAIN} --non-interactive --agree-tos --email noreply@example.com"
   ```
   > 이미 `api.{SSL_DOMAIN}` 인증서가 존재하면 이 단계는 건너뛴다.

6. **Proxy 설정**: Web Server VM(`{WEB_SERVER_SSH_HOST}`)에서 Nginx conf를 **프론트엔드 + API 두 개 server 블록**으로 재생성한다.
   ```bash
   ssh {WEB_SERVER_SSH_HOST} 'SERVER_NAME="{SSL_DOMAIN}"
   API_SERVER_NAME="api.{SSL_DOMAIN}"
   PROXY_TARGET="http://{INGRESS_ADDRESS}"

   cat << EOF | sudo tee /etc/nginx/sites-available/default
   # 80 → 443 리다이렉트 (Frontend)
   server {
     listen 80;
     server_name ${SERVER_NAME};
     return 301 https://\$host\$request_uri;
   }
   # 80 → 443 리다이렉트 (API)
   server {
     listen 80;
     server_name ${API_SERVER_NAME};
     return 301 https://\$host\$request_uri;
   }
   # 443 Frontend Proxy
   server {
     listen 443 ssl;
     server_name ${SERVER_NAME};
     ssl_certificate /etc/letsencrypt/live/${SERVER_NAME}/fullchain.pem;
     ssl_certificate_key /etc/letsencrypt/live/${SERVER_NAME}/privkey.pem;
     ssl_protocols TLSv1.2 TLSv1.3;
     ssl_ciphers HIGH:!aNULL:!MD5;
     root /var/www/html;
     index index.html;
     location / {
       proxy_pass ${PROXY_TARGET};
       proxy_ssl_verify off;
       proxy_buffer_size 64k;
       proxy_buffers 4 64k;
       proxy_busy_buffers_size 64k;
       proxy_set_header Host \$host;
       proxy_set_header X-Real-IP \$remote_addr;
       proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto \$scheme;
       proxy_read_timeout 60s;
       proxy_connect_timeout 60s;
       proxy_send_timeout 60s;
     }
   }
   # 443 API Proxy
   server {
     listen 443 ssl;
     server_name ${API_SERVER_NAME};
     ssl_certificate /etc/letsencrypt/live/${API_SERVER_NAME}/fullchain.pem;
     ssl_certificate_key /etc/letsencrypt/live/${API_SERVER_NAME}/privkey.pem;
     ssl_protocols TLSv1.2 TLSv1.3;
     ssl_ciphers HIGH:!aNULL:!MD5;
     location / {
       proxy_pass ${PROXY_TARGET};
       proxy_ssl_verify off;
       proxy_buffer_size 64k;
       proxy_buffers 4 64k;
       proxy_busy_buffers_size 64k;
       proxy_set_header Host \$host;
       proxy_set_header X-Real-IP \$remote_addr;
       proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto \$scheme;
       proxy_read_timeout 60s;
       proxy_connect_timeout 60s;
       proxy_send_timeout 60s;
     }
   }
   EOF'
   ```
   > 두 server 블록 모두 동일한 Ingress ADDRESS로 `proxy_pass`하되, `Host` 헤더를 `$host`로 전달하여 Ingress Controller가 Host 기반 라우팅을 수행한다.

7. **Nginx 재시작**: `sudo nginx -t && sudo systemctl reload nginx`

8. **CORS 확인**: 공통 ConfigMap의 `CORS_ALLOWED_ORIGINS`에 `https://{SSL_DOMAIN}` 포함 여부 확인

### Step 5. 배포 완료 보고

```
## 배포 완료

### 배포 환경
- 클러스터 유형: {EKS / AKS / GKE}

### 배포 결과
- 백엔드 컨테이너: 빌드 및 배포 완료
- 프론트엔드 컨테이너: 빌드 및 배포 완료
- AI 서비스 컨테이너: 빌드 및 배포 완료
- K8s 배포: 완료

### 접속 정보
- 백엔드 API: {URL}
- 프론트엔드: {URL}
```

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |

## 완료 조건

- [ ] 모든 워크플로우 단계(Step 1~5)가 정상 완료됨
- [ ] VM 백킹서비스 배포 완료 (`docs/deploy/backing-service-container-result.md` 생성)
- [ ] 컨테이너 실행 검증 완료 (`docs/deploy/run-container-{back,front,ai}-result.md` 생성)
- [ ] Dockerfile(백엔드/프론트엔드/AI 서비스)이 생성되고 빌드 성공
- [ ] K8s 백킹서비스 배포 완료 (`docs/deploy/backing-service-k8s-result.md` 생성)
- [ ] K8s 매니페스트(`deploy/k8s/`)가 생성되고 배포 성공
- [ ] Nginx Proxy 설정 완료 (HTTPS 접근 가능)
- [ ] 검증 프로토콜을 통과함
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (Dockerfile, K8s 매니페스트)
2. 산출물 내용 품질 검증 (컨테이너 빌드 성공, 로컬 실행 정상, K8s 배포 정상)
3. 이전 Phase 산출물과의 일관성 확인 (개발 산출물 → 배포 산출물 연계)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.

1. `CLAUDE.md`의 `## NPD 워크플로우 상태 > ### deploy` 섹션에서 변수를 복원:
   - `진행 모드` → 승인/자동 모드 결정
   - `CLOUD` → Cloud 서비스
   - `레지스트리유형`, `IMG_REG`, `IMG_ORG` + 클라우드별 필드 → [실행정보] 복원
   - `VM_HOST` → VM 접속 정보
   - `K8S_CLUSTER`, `K8S_NAMESPACE` → K8s 배포 대상
   - `마지막 완료 Step` → 재개 시작점 결정
2. 상태 섹션이 없으면 **Step 0. 진행 모드 선택**부터 시작
