# ArgoCD 매니페스트 레포지토리 구성 가이드

## 목적
ArgoCD GitOps 방식의 CD를 위해 매니페스트 레포지토리를 구성한다. 환경별(dev/staging/prod) Kustomize 매니페스트를 별도 레포지토리로 관리하고, ArgoCD Application CRD YAML을 생성·등록한다.

> CI 파이프라인(Jenkins/GitHub Actions)의 마지막 단계에서 이 매니페스트 레포지토리의 image tag를 업데이트하면, ArgoCD가 변경을 감지하여 자동 배포한다. CI 파이프라인 작성은 별도 가이드(`deploy-jenkins-cicd-*.md`, `deploy-actions-cicd-*.md`)를 참조한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| K8s 클러스터 정보 | `(런타임 결정)` | 배포 대상 |
| 매니페스트 레포지토리 | `(런타임 결정)` | GitOps 대상 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| ArgoCD 준비 가이드 | `deploy-argocd-prepare.md` |
| 매니페스트 레포지토리 구조 | `{MANIFEST_REPO}/` |
| ArgoCD Application YAML | `{MANIFEST_REPO}/argocd/*.yaml` |

## 방법론

### 사전 준비사항 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {CI_TOOL}: CI 도구 (Jenkins / GitHubActions) — 매니페스트 복사 경로 분기에 사용
- {SYSTEM_NAME}: 대표 시스템명
- {FRONTEND_SERVICE}: 프론트엔드 서비스명
- {AI_SERVICE}: AI 서비스명
- {IMG_REG}: Container Image Registry 주소
- {IMG_ORG}: Container Image Organization
- {MANIFEST_REPO_URL}: 매니페스트 레포지토리 URL
- {NAMESPACE}: K8s 네임스페이스

예시)
```
[실행정보]
- CI_TOOL: Jenkins
- SYSTEM_NAME: phonebill
- FRONTEND_SERVICE: phonebill-front
- AI_SERVICE: ai-service
- IMG_REG: docker.io
- IMG_ORG: hiondal
- MANIFEST_REPO_URL: https://github.com/cna-bootcamp/phonebill-manifest.git
- NAMESPACE: phonebill
```

### 작업 편의를 위한 환경변수

> **디렉토리 레이아웃 전제**: 아래 변수는 매니페스트 레포지토리 디렉토리 안에서 작업하는 것을 전제합니다.
> 애플리케이션 소스 코드 레포지토리(`{SYSTEM_NAME}`, `{FRONTEND_SERVICE}`, `{AI_SERVICE}`)는 매니페스트 레포의 **형제(sibling) 디렉토리**에 있다고 가정합니다.
> SKILL.md Step 1이 Step 2보다 먼저 실행되므로, CI 산출물이 아직 없는 경우 복사 대신 직접 생성합니다.

- {BASE_DIR}: ..
- {BACKEND_DIR}: ${BASE_DIR}/${SYSTEM_NAME}
- {FRONTEND_DIR}: ${BASE_DIR}/${FRONTEND_SERVICE}
- {AI_DIR}: ${BASE_DIR}/${AI_SERVICE}
- {MANIFEST_DIR}: .

### 백엔드 서비스명 확인
${BACKEND_DIR}/settings.gradle에서 확인.
{SERVICE_NAMES}: include 'common'하위의 include문 뒤의 값임

예시) include 'common'하위의 서비스명들.
```
rootProject.name = 'phonebill'

include 'common'
include 'api-gateway'
include 'user-service'
include 'order-service'
include 'payment-service'
```

### AI 서비스명 확인
${AI_DIR}/pyproject.toml에서 확인.
{AI_SERVICE}: `[tool.poetry] name` 필드값

예시)
```toml
[tool.poetry]
name = "ai-service"
```

> `pyproject.toml`이 없는 경우 AI 서비스 디렉토리명을 서비스명으로 사용

### 매니페스트 레포지토리 초기화 (신규 생성 시)

매니페스트 레포지토리가 아직 없는 경우(`[실행정보]`에서 "없으면 새로 생성"을 선택한 경우) 아래 단계를 먼저 수행한다.

> **{MANIFEST_REPO_NAME}**: `{MANIFEST_REPO_URL}`에서 레포지토리 이름을 추출한다. 예) `https://github.com/org/phonebill-manifest.git` → `phonebill-manifest`

```bash
# 매니페스트 레포지토리 디렉토리 생성 및 초기화
mkdir {MANIFEST_REPO_NAME} && cd {MANIFEST_REPO_NAME}
git init
git remote add origin {MANIFEST_REPO_URL}

# 초기 커밋 (빈 레포에 push하기 위해)
echo "# {SYSTEM_NAME} Manifest Repository" > README.md
git add README.md
git commit -m "Initial commit"
git push -u origin main
```

> 이미 원격 레포지토리가 존재하는 경우 `git clone {MANIFEST_REPO_URL}`로 클론 후 진행한다.

### 매니페스트 레포지토리 구성

> **참고: Step 순서에 따른 분기**
> - CI 파이프라인(Step 2) 산출물이 **이미 존재하는 경우**: 아래 복사 명령으로 기존 Kustomize 파일을 매니페스트 레포로 복사합니다.
> - CI 파이프라인보다 **먼저 실행하는 경우** (SKILL.md Step 1): 복사 대신 아래 "디렉토리 구조 확인" 섹션의 구조에 맞춰 Kustomize 파일을 직접 생성합니다.

#### 1) 백엔드 매니페스트 복사 (CI 산출물이 존재하는 경우)
```bash
mkdir -p ${MANIFEST_DIR}/${SYSTEM_NAME}
# Jenkins 기반인 경우:
cp -r ${BACKEND_DIR}/deployment/cicd/kustomize ${MANIFEST_DIR}/${SYSTEM_NAME}/
# GitHub Actions 기반인 경우:
cp -r ${BACKEND_DIR}/.github/kustomize ${MANIFEST_DIR}/${SYSTEM_NAME}/
```

#### 2) 프론트엔드 매니페스트 복사 (CI 산출물이 존재하는 경우)
```bash
mkdir -p ${MANIFEST_DIR}/${FRONTEND_SERVICE}
# Jenkins 기반인 경우:
cp -r ${FRONTEND_DIR}/deployment/cicd/kustomize ${MANIFEST_DIR}/${FRONTEND_SERVICE}/
# GitHub Actions 기반인 경우:
cp -r ${FRONTEND_DIR}/.github/kustomize ${MANIFEST_DIR}/${FRONTEND_SERVICE}/
```

#### 3) AI 매니페스트 복사 (CI 산출물이 존재하는 경우)
```bash
mkdir -p ${MANIFEST_DIR}/${AI_SERVICE}
# Jenkins 기반인 경우:
cp -r ${AI_DIR}/deployment/cicd/kustomize ${MANIFEST_DIR}/${AI_SERVICE}/
# GitHub Actions 기반인 경우:
cp -r ${AI_DIR}/.github/kustomize ${MANIFEST_DIR}/${AI_SERVICE}/
```

#### 4) 디렉토리 구조 확인
```
{MANIFEST_REPO}/
├── {SYSTEM_NAME}/
│   └── kustomize/
│       ├── base/
│       │   ├── {서비스1}/
│       │   │   ├── deployment.yaml
│       │   │   └── service.yaml
│       │   ├── {서비스2}/
│       │   │   ├── deployment.yaml
│       │   │   └── service.yaml
│       │   └── kustomization.yaml
│       └── overlays/
│           ├── dev/
│           │   └── kustomization.yaml
│           ├── staging/
│           │   └── kustomization.yaml
│           └── prod/
│               └── kustomization.yaml
├── {FRONTEND_SERVICE}/
│   └── kustomize/
│       ├── base/
│       │   ├── deployment.yaml
│       │   └── service.yaml
│       └── overlays/
│           ├── dev/
│           ├── staging/
│           └── prod/
├── {AI_SERVICE}/
│   └── kustomize/
│       ├── base/
│       │   ├── deployment.yaml
│       │   └── service.yaml
│       └── overlays/
│           ├── dev/
│           ├── staging/
│           └── prod/
└── argocd/
    ├── {SYSTEM_NAME}-dev.yaml
    ├── {SYSTEM_NAME}-staging.yaml
    ├── {SYSTEM_NAME}-prod.yaml
    ├── {FRONTEND_SERVICE}-dev.yaml
    ├── {FRONTEND_SERVICE}-staging.yaml
    ├── {FRONTEND_SERVICE}-prod.yaml
    ├── {AI_SERVICE}-dev.yaml
    ├── {AI_SERVICE}-staging.yaml
    └── {AI_SERVICE}-prod.yaml
```

### ArgoCD Application YAML 생성

서비스별 x 환경별 ArgoCD Application CRD YAML 파일을 자동 생성한다.

**생성 위치**: 매니페스트 레포지토리 루트의 `argocd/` 디렉토리
**생성 파일명**: `argocd/{service}-{env}.yaml`

#### Application YAML 템플릿

**백엔드 시스템용 (환경별 1개, 시스템 단위):**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {SYSTEM_NAME}-{env}
  namespace: argocd
spec:
  project: default
  source:
    repoURL: {MANIFEST_REPO_URL}
    targetRevision: HEAD
    path: {SYSTEM_NAME}/kustomize/overlays/{env}
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

**프론트엔드 서비스용:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {FRONTEND_SERVICE}-{env}
  namespace: argocd
spec:
  project: default
  source:
    repoURL: {MANIFEST_REPO_URL}
    targetRevision: HEAD
    path: {FRONTEND_SERVICE}/kustomize/overlays/{env}
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

**AI 서비스용:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {AI_SERVICE}-{env}
  namespace: argocd
spec:
  project: default
  source:
    repoURL: {MANIFEST_REPO_URL}
    targetRevision: HEAD
    path: {AI_SERVICE}/kustomize/overlays/{env}
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

#### 생성 규칙
- **백엔드**: Kustomize overlay가 모든 서비스를 포함하므로, **환경별 1개 Application**을 생성한다 (서비스별이 아닌 시스템 단위). Application 이름: `{SYSTEM_NAME}-{env}`
- **프론트엔드**: `{FRONTEND_SERVICE}` 환경별 1개 Application 생성. Application 이름: `{FRONTEND_SERVICE}-{env}`
- **AI**: `{AI_SERVICE}` 환경별 1개 Application 생성. Application 이름: `{AI_SERVICE}-{env}`
  - 설계 근거: AI 서비스는 프론트엔드와 동일하게 단일 서비스 단위로 독립 Kustomize 구조를 사용하므로, 시스템 단위가 아닌 서비스 단위 Application으로 관리
- 환경(env): `dev`, `staging`, `prod` 3개
- **총 생성 수**: (백엔드 1 + 프론트엔드 1 + AI 1) x 3환경 = 9개

> **설계 근거**: 백엔드 Kustomize overlay(`{SYSTEM_NAME}/kustomize/overlays/{env}`)는 `../../base`를 참조하여 모든 서비스를 포함합니다. 서비스별로 ArgoCD Application을 생성하면 동일한 리소스를 중복 관리하게 되므로, 시스템 단위로 1개 Application을 생성합니다.

### ArgoCD 매니페스트 레포지토리 인증 등록

Private 레포지토리인 경우, ArgoCD가 매니페스트 레포를 감시(poll)할 수 있도록 인증 정보를 등록해야 한다.

```bash
# 방법 1: argocd CLI 사용 (argocd CLI가 설치된 경우)
argocd repo add {MANIFEST_REPO_URL} \
  --username {Git사용자명} \
  --password {Git토큰} \
  --insecure-skip-server-verification

# 방법 2: kubectl로 Secret 직접 생성
kubectl create secret generic manifest-repo-cred -n argocd \
  --from-literal=type=git \
  --from-literal=url={MANIFEST_REPO_URL} \
  --from-literal=username={Git사용자명} \
  --from-literal=password={Git토큰}
kubectl label secret manifest-repo-cred -n argocd argocd.argoproj.io/secret-type=repository
```

등록 확인:
```bash
# argocd CLI
argocd repo list
# 또는 ArgoCD UI > Settings > Repositories에서 확인
```

> Public 레포지토리인 경우 이 단계를 건너뛸 수 있다.

### ArgoCD Application 등록

생성된 YAML을 K8s 클러스터에 적용하여 ArgoCD Application을 등록한다.

```bash
kubectl apply -f argocd/
```

> 이 `kubectl apply`는 ArgoCD Application CRD 등록용이며, 애플리케이션 배포용 kubectl apply가 아님.

등록 확인:
```bash
kubectl get applications -n argocd
```

### CI 파이프라인의 매니페스트 업데이트 스크립트 참조

CI 파이프라인(Jenkins/GitHub Actions)의 마지막 단계에서 매니페스트 레포지토리의 image tag를 업데이트하는 로직이 필요하다. 각 CI 도구별 가이드에 해당 스크립트가 포함되어 있다:

| CI 도구 | 백엔드 가이드 | 프론트엔드 가이드 | AI 가이드 | 참조 스테이지/잡 |
|---------|-------------|----------------|----------|-----------------|
| Jenkins | `deploy-jenkins-cicd-back.md` | `deploy-jenkins-cicd-front.md` | `deploy-jenkins-cicd-ai.md` | `Update Manifest Repository` stage |
| GitHub Actions | `deploy-actions-cicd-back.md` | `deploy-actions-cicd-front.md` | `deploy-actions-cicd-ai.md` | `update-manifest` job |

> CI 파이프라인 작성 시 위 가이드의 해당 스테이지/잡을 참조하여 manifest repo image tag 업데이트를 포함한다.

## 출력 형식

작업 결과를 `deploy-argocd-prepare.md` 파일에 다음 항목을 포함하여 작성한다.

- 매니페스트 레포지토리 구성 완료 내역
- ArgoCD Application YAML 생성 목록
- ArgoCD Application 등록 결과
- ArgoCD가 감시할 레포지토리 및 경로 정보

## 품질 기준
- [ ] CI/CD 분리 원칙 준수 (CI: 빌드·푸시·manifest tag 업데이트, CD: ArgoCD 자동 배포)
- [ ] 매니페스트 레포지토리 구성 (Kustomize base/overlays 구조)
- [ ] ArgoCD Application YAML 서비스별 x 환경별 생성
- [ ] ArgoCD Application 등록 완료
- [ ] 시크릿 하드코딩 금지

## 주의사항
- 매니페스트 레포지토리는 애플리케이션 소스 코드와 별도의 Git 레포지토리로 관리한다
- ArgoCD Application의 `syncPolicy.automated`를 설정하여 자동 동기화를 활성화한다
- `kubectl apply -f argocd/`는 ArgoCD Application CRD 등록 전용이다. 애플리케이션 배포에 kubectl apply를 사용하지 않는다
- CI 파이프라인에서의 manifest repo 업데이트 스크립트는 각 CI 도구별 가이드를 참조한다
