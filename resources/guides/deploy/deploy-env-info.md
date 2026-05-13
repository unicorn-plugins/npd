# 배포 환경 정보 수집 가이드

> 본 가이드는 `skills/deploy/SKILL.md > Phase 2`에서 호출됨.
> 이미지 레지스트리·K8S 클러스터·서비스 리소스 정보를 수집하고 `[실행정보]` 블록을 조립하는 절차를 정의.

## 입력

- `{PROJECT_DIR}/AGENTS.md > ## 워크플로우 진행상황 > ### design > CLOUD` (이미지 레지스트리 분기 결정)
- `{PROJECT_DIR}/AGENTS.md > ### deploy > VM_HOST` (Phase 1 / Step 5에서 기록)
- `~/.ssh/config` (HostName, User, IdentityFile 매핑)
- 로컬 kubeconfig (kubectx로 컨텍스트 조회)
- `docs/deploy/run-container-{back,front,ai}-result.md` (서비스 목록 감지, Step 4 입력)
- `{ROOT}` (AGENTS.md 시스템명, NAMESPACE 기본값)

## 모드 분기

> **자동 진행 모드 동작**: Phase 2의 사용자 입력 단계는 자동 감지 가능한 항목 우선 처리.
> - **Step 3 K8s 클러스터**: 감지 결과 1개이면 자동 선택, 2개 이상이면 질문
> - **Step 4 리소스 설정**: 자동 진행 모드에서는 placeholder 기본값(파드수=2, CPU=0.25/1, 메모리=256/1024)을 사용하고 예외 설정은 "없음"으로 처리

> **조건부 실행 규칙**: 시작 Phase에 따라 필요한 Step만 수행한다.
> - **Step 1·2 (이미지 레지스트리)**: 시작 Phase ≤ 5이면 수행
> - **Step 3 (K8S 클러스터)**: 시작 Phase ≤ 5이면 수행
> - **Step 4 (서비스별 리소스)**: 시작 Phase ≤ 5이면 수행
> - **VM 정보 (Phase 1 결과)**: 시작 Phase ∈ {1, 3, 4, 5}이면 사용

---

## Step 1. 이미지 레지스트리 정보 수집 (1차)

> **조건**: 시작 Phase ≤ 5일 때만 수행

<!--ASK_USER-->
{"title":"이미지 레지스트리 선택","questions":[
  {"question":"이미지 레지스트리 유형을 선택하세요.","type":"radio","options":["Docker Hub","{CLOUD 레지스트리}"]}
]}
<!--/ASK_USER-->

> **{CLOUD 레지스트리} 매핑**: Azure → `Azure ACR`, AWS → `AWS ECR`, GCP → `Google GCR (Artifact Registry)`

---

## Step 2. 이미지 레지스트리 정보 수집 (2차, 유형별 분기)

Step 1에서 선택된 레지스트리 유형에 따라 추가 정보를 수집한다.

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

---

## Step 3. K8S 클러스터 자동 감지 + 선택

> **조건**: 시작 Phase ≤ 5일 때만 수행

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

네임스페이스는 `{ROOT}` (프로젝트명, AGENTS.md의 시스템명)를 기본값으로 사용한다.

---

## Step 4. K8S 배포 리소스 설정 (서비스별)

> **조건**: 시작 Phase ≤ 5일 때만 수행

`docs/deploy/run-container-{back,front,ai}-result.md`에서 서비스 목록을 감지한 후, 리소스 설정을 수집한다.

### Step 4-1. 일괄 기본값 설정

감지된 서비스 목록을 안내한 뒤, 모든 서비스에 적용할 기본값을 질문한다:

<!--ASK_USER-->
{"title":"K8S 리소스 기본값 설정","questions":[
  {"question":"감지된 서비스: {서비스 목록}\n\n모든 서비스에 적용할 기본 파드 수를 입력하세요.","type":"text","placeholder":"2"},
  {"question":"기본 CPU 리소스를 입력하세요 (요청값/최대값, 단위: core).","type":"text","placeholder":"0.25/1"},
  {"question":"기본 메모리 리소스를 입력하세요 (요청값/최대값, 단위: MB).","type":"text","placeholder":"256/1024"}
]}
<!--/ASK_USER-->

### Step 4-2. 서비스별 예외 설정

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
예외로 지정되지 않은 서비스는 Step 4-1의 기본값을 그대로 사용한다.

수집된 값을 K8s 리소스 단위로 변환하여 `[실행정보]`에 반영한다:
- **파드수**: 입력값 그대로 사용
- **CPU**: core → millicore 변환 (예: `0.25/1` → `250m/1000m`)
- **메모리**: MB → Mi 변환 (예: `256/1024` → `256Mi/1024Mi`)

---

## Step 5. 실행정보 조립 + 상태 기록

> **조건부 조립**: 시작 Phase에 따라 수집되지 않은 필드는 `[실행정보]`에서 생략한다.
> - 레지스트리 관련 필드 (레지스트리유형, REGISTRY_URL 등): Phase 3 또는 Phase 5 실행 시
> - K8S 관련 필드 (CLUSTER, NAMESPACE, 서비스 리소스): Phase 5 실행 시에만
> - VM 관련 필드 (HOST, KEY파일 등): Phase 3 또는 Phase 4 또는 Phase 5 (Nginx Proxy) 실행 시

수집된 정보를 아래 템플릿에 따라 `[실행정보]`로 조립한다.
조립된 `[실행정보]` 블록은 이후 에이전트 호출 시 **프롬프트의 동적(작업 지시) 영역에 텍스트로 포함**하여 전달한다. 에이전트는 별도 컨텍스트에서 실행되므로, `Agent(prompt=...)` 호출 시 `[실행정보]` 블록 전문을 반드시 포함해야 가이드 내 `${REGISTRY_URL}`, `${IMG_ID}` 등의 변수를 치환할 수 있다.

> VM 접속 정보는 Phase 1 / Step 5(`~/.ssh/config` 파싱)에서 자동 수집된다.
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

> `{ROOT}`는 AGENTS.md의 시스템명을 참조하여 결정한다.

**상태 기록**: `[실행정보]` 조립 완료 후, `skills/deploy/SKILL.md > 진행상황 업데이트 및 재개` 섹션의 형식에 따라 `AGENTS.md`의 `## 워크플로우 진행상황 > ### deploy` 섹션을 갱신(생성)한다. 클라우드별 전용 필드는 해당 레지스트리유형 선택 시에만 기록하고 나머지는 생략. VM_HOST는 Phase 1 / Step 5 완료 후 이미 기록되어 있다. K8S_CLUSTER, K8S_NAMESPACE는 본 Step 완료 시 추가 기록.

**환경 선택 분기 규칙:**
1. `[실행정보]`의 `레지스트리유형` 필드에 따라 해당 유형에 맞는 이미지 경로 체계(`REGISTRY_URL`)를 사용한다
2. 중간 Phase 시작으로 레지스트리 정보가 없는 경우, 본 Step에서 수집하여 보충한다

---

## 산출물

- `[실행정보]` 블록 (Cloud별 4개 템플릿 중 하나, Phase 3·4·5 Agent 호출 시 프롬프트의 동적 영역에 포함)
- `AGENTS.md > ## 워크플로우 진행상황 > ### deploy` 섹션 갱신:
  - `레지스트리유형`, `IMG_REG`, `IMG_ORG`, Cloud별 전용 필드 (ECR_ACCOUNT/REGION, ACR명, GCR_PROJECT/REGION/REPO)
  - `K8S_CLUSTER`, `K8S_NAMESPACE`
