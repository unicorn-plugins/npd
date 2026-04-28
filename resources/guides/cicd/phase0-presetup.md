# Phase 0 사전 체크 + 모드 선택 + 정보 수집 가이드

> 본 가이드는 `skills/cicd/SKILL.md > Phase 0`에서 호출됨.
> hosts 파일 확인·진행 모드 선택·CI 도구 선택·deploy 환경 복원·프로젝트 유형 감지·MANIFEST_REPO·환경 선택·`[실행정보]` 조립까지 8개 Step 절차를 정의.

## 입력

- `{PROJECT_DIR}/AGENTS.md > ## 워크플로우 진행상황 > ### deploy` (Step 4 환경 정보 복원)
- `~/.ssh/config` (VM_HOST 매핑)
- 프로젝트 루트의 `settings.gradle` / `package.json` / `pyproject.toml` (Step 5 자동 감지)
- 프로젝트 루트의 `deployment/k8s/` (Step 5 사전 검증)
- `git remote get-url origin` (Step 6 매니페스트 레포 URL 결정)

## 공통 원칙

- **자동 진행 보장**: Phase 1~3 실행 중 사용자 입력이 필요한 항목을 본 Phase에서 사전에 모두 수집
- **저장 위치**:
  - 진행 모드·CI 도구·시작 Phase·환경 변수 → `AGENTS.md > ### cicd`
  - `[실행정보]` 블록 → 메모리 + Phase 2~3 Agent 호출 시 프롬프트에 포함

## 자동 진행 모드 동작 규칙

- Phase 0 / Step 2 (진행 모드 선택)·Step 3 (CI 도구 선택)은 자동 진행 모드에서도 수행
- deploy 환경 정보(Phase 0 / Step 4)는 `### deploy` 상태에서 자동 복원 (질문 없음)
- Phase 1 ~ Phase 3 실행 중에는 `<!--ASK_USER-->` 호출하지 않음
- 자동 감지 가능 항목: SYSTEM_NAME (settings.gradle), FRONTEND_SERVICE (package.json), AI_SERVICE (pyproject.toml)

> **조건부 필드**: `FRONTEND_SERVICE`는 `package.json` 감지 시에만, `AI_SERVICE`는 `pyproject.toml` 감지 시에만 `[실행정보]`에 포함. 순수 AI 프로젝트는 FRONTEND_SERVICE 없이 AI_SERVICE만 포함 가능.

---

## Step 1. hosts 파일 등록 확인

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
  > `AGENTS.md`의 `### deploy` 상태에서 `VM_HOST`를 확인하고, `ssh {VM_HOST} 'curl -s ifconfig.me'`로 Public IP 조회 가능.

---

## Step 2. 진행 모드 선택

<!--ASK_USER-->
{"title":"진행 모드 선택","questions":[
  {"question":"각 단계 완료 후 승인을 받고 진행할까요, 자동으로 진행할까요?","type":"radio","options":["단계별 승인","자동 진행"]}
]}
<!--/ASK_USER-->

- **단계별 승인** 선택 시 → 각 스텝 완료 후 아래 ASK_USER로 승인 요청을 표시하고 응답에 따라 분기:
  - **승인** → 다음 스텝 진행
  - **재작업 요청** → 사용자 피드백을 받아 현재 스텝 재수행
  - **중단** → 현재까지 산출물 보존 후 스킬 종료
- **자동 진행** 선택 시 → Phase 0에서 필요한 정보를 모두 수집한 뒤, 워크플로우 실행 중(Phase 1 ~ Phase 3)에는 `<!--ASK_USER-->`를 호출하지 않고 자동 처리한다.

승인 요청 ASK_USER 형식:

<!--ASK_USER-->
{"title":"단계 승인","questions":[
  {"question":"{완료된 스텝명} 단계가 완료되었습니다. 결과 파일({생성된 파일 경로})을 검토하고 {다음 스텝명} 단계로 계속 진행할 지 승인해 주십시오.","type":"radio","options":["승인","재작업 요청","중단"]}
]}
<!--/ASK_USER-->

**저장**: 선택 결과를 `AGENTS.md > ### cicd > 진행 모드`에 기록.

---

## Step 3. CI 도구 선택

<!--ASK_USER-->
{"title":"CI 도구 선택","questions":[
  {"question":"CI 파이프라인에 사용할 도구를 선택하세요.","type":"radio","options":["Jenkins","GitHub Actions"]}
]}
<!--/ASK_USER-->

**저장**: 선택 결과(`Jenkins` 또는 `GitHubActions`)를 `AGENTS.md > ### cicd > CI_TOOL`에 기록.

---

## Step 4. deploy 환경 정보 복원

`AGENTS.md`의 `## 워크플로우 진행상황 > ### deploy` 섹션에서 환경 정보를 읽어 변수를 바인딩.
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

---

## Step 5. 프로젝트 유형 감지 및 사전 검증

> 백엔드와 프론트엔드는 별도 프로젝트(리포지토리)에 있을 수 있다. 현재 프로젝트의 유형을 자동 감지하여 이후 단계에서 해당하는 파이프라인만 생성한다.

**프로젝트 유형 자동 감지:**
- **백엔드 감지**: `settings.gradle` 또는 `build.gradle` 존재
- **프론트엔드 감지**: `package.json` 존재 (settings.gradle 없음)
- **AI 서비스 감지**: `pyproject.toml` 존재 (settings.gradle, package.json 없음)
- **복합 프로젝트 (여러 유형 파일 공존)**: 사용자에게 확인 후 해당하는 파이프라인 모두 생성

**기존 K8s 매니페스트 존재 검증:**
```bash
# deployment/k8s/ 디렉토리 존재 확인
ls deployment/k8s/
```

> `deployment/k8s/` 디렉토리가 없으면 `/npd:deploy` Phase 5를 먼저 완료하도록 안내하고 중단한다.

**프로젝트명 자동 감지:**
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

---

## Step 6. 매니페스트 레포지토리 URL 결정

현재 프로젝트의 GitHub origin에서 org를 추출하여 매니페스트 레포 URL을 자동 결정:

```bash
ORIGIN_URL=$(git remote get-url origin)
# https://github.com/{org}/{repo}.git → {org} 추출
MANIFEST_REPO_URL="https://github.com/{org}/{SYSTEM_NAME}-manifest.git"
```

> Phase 1 / Step 1에서 `gh repo create`로 실제 생성. 이미 존재하면 기존 URL 사용.

**저장**: `MANIFEST_REPO_URL`을 `AGENTS.md > ### cicd > MANIFEST_REPO_URL`에 기록.

---

## Step 7. 배포 환경 선택

<!--ASK_USER-->
{"title":"배포 환경 선택","questions":[
  {"question":"ArgoCD Application을 생성할 환경을 선택하세요. (나중에 Phase 2 재실행으로 추가 가능)","type":"checkbox","options":["dev","staging","prod"]}
]}
<!--/ASK_USER-->

- 선택된 환경만 Kustomize overlays 디렉토리 및 ArgoCD Application YAML을 생성
- 기본값: `dev`
- `[실행정보]`의 `ENVIRONMENTS` 필드에 쉼표 구분으로 기록 (예: `dev,staging`)

**저장**: `ENVIRONMENTS`를 `AGENTS.md > ### cicd > ENVIRONMENTS`에 기록.

---

## Step 8. [실행정보] 조립

수집된 정보를 `[실행정보]` 블록으로 조립한다. **CI 도구 + 클라우드/레지스트리 조합**에 따라 7가지 템플릿 중 하나를 사용.

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/cicd/cicd-runinfo-templates.md` ← **필수 로드**
- **TASK**: 위 GUIDE의 7가지 템플릿 중 `{CI_TOOL} + {레지스트리유형}` 조합에 해당하는 1개를 채택하여 변수 치환
- **2단계 조립**: 본 Step에서 base [실행정보]를 조립하되, CI 도구 전용 필드(JENKINS_CLOUD_NAME, JENKINS_GIT_CREDENTIALS, MANIFEST_SECRET_GIT_USERNAME/PASSWORD, RESOURCE_GROUP, GKE_ZONE)는 미정으로 남긴다. Phase 2 / Step 4에서 해당 필드를 수집한 후 [실행정보]를 보완.

**상태 기록**: `[실행정보]` 조립 완료 시, `skills/cicd/SKILL.md > 진행상황 업데이트 및 재개` 섹션의 형식에 따라 `AGENTS.md`의 `## 워크플로우 진행상황 > ### cicd` 섹션을 갱신.

---

## 산출물

- `AGENTS.md > ## 워크플로우 진행상황 > ### cicd` 섹션:
  - `진행 모드`, `CI_TOOL`, `CLOUD`, `레지스트리유형`, `MANIFEST_REPO_URL`, `ENVIRONMENTS`, `K8S_CLUSTER`, `K8S_NAMESPACE`, `VM_HOST`
- `[실행정보]` 블록 (Phase 2~3 Agent 호출 시 프롬프트의 동적 영역에 포함, CI 도구 전용 필드는 Phase 2 / Step 4에서 보완)
