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
- {SYSTEM_NAME}: 대표 시스템명
- {FRONTEND_SERVICE}: 프론트엔드 서비스명
- {IMG_REG}: Container Image Registry 주소
- {IMG_ORG}: Container Image Organization
- {MANIFEST_REPO_URL}: 매니페스트 레포지토리 URL
- {NAMESPACE}: K8s 네임스페이스

예시)
```
[실행정보]
- SYSTEM_NAME: phonebill
- FRONTEND_SERVICE: phonebill-front
- IMG_REG: docker.io
- IMG_ORG: hiondal
- MANIFEST_REPO_URL: https://github.com/cna-bootcamp/phonebill-manifest.git
- NAMESPACE: phonebill
```

### 작업 편의를 위한 환경변수
- {BASE_DIR}: ..
- {BACKEND_DIR}: ${BASE_DIR}/${SYSTEM_NAME}
- {FRONTEND_DIR}: ${BASE_DIR}/${FRONTEND_SERVICE}
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

### 매니페스트 레포지토리 구성

#### 1) 백엔드 매니페스트 복사
```bash
mkdir -p ${MANIFEST_DIR}/${SYSTEM_NAME}
# Jenkins 기반인 경우:
cp -r ${BACKEND_DIR}/deployment/cicd/kustomize ${MANIFEST_DIR}/${SYSTEM_NAME}/
# GitHub Actions 기반인 경우:
cp -r ${BACKEND_DIR}/.github/kustomize ${MANIFEST_DIR}/${SYSTEM_NAME}/
```

#### 2) 프론트엔드 매니페스트 복사
```bash
mkdir -p ${MANIFEST_DIR}/${FRONTEND_SERVICE}
# Jenkins 기반인 경우:
cp -r ${FRONTEND_DIR}/deployment/cicd/kustomize ${MANIFEST_DIR}/${FRONTEND_SERVICE}/
# GitHub Actions 기반인 경우:
cp -r ${FRONTEND_DIR}/.github/kustomize ${MANIFEST_DIR}/${FRONTEND_SERVICE}/
```

#### 3) 디렉토리 구조 확인
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
└── argocd/
    ├── {서비스1}-dev.yaml
    ├── {서비스1}-staging.yaml
    ├── {서비스1}-prod.yaml
    └── ...
```

### ArgoCD Application YAML 생성

서비스별 x 환경별 ArgoCD Application CRD YAML 파일을 자동 생성한다.

**생성 위치**: 매니페스트 레포지토리 루트의 `argocd/` 디렉토리
**생성 파일명**: `argocd/{service}-{env}.yaml`

#### Application YAML 템플릿

**백엔드 서비스용 (서비스별 생성):**
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

#### 생성 규칙
- 백엔드 서비스: `settings.gradle`의 `include` 목록에서 각 서비스명 추출 → 서비스별 Application 생성
- 프론트엔드 서비스: `{FRONTEND_SERVICE}` 1개 Application 생성
- 환경(env): `dev`, `staging`, `prod` 3개
- **총 생성 수**: (백엔드 서비스 수 + 1) x 3환경

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

| CI 도구 | 백엔드 가이드 | 프론트엔드 가이드 | 참조 스테이지/잡 |
|---------|-------------|----------------|-----------------|
| Jenkins | `deploy-jenkins-cicd-back.md` | `deploy-jenkins-cicd-front.md` | `Update Manifest Repository` stage |
| GitHub Actions | `deploy-actions-cicd-back.md` | `deploy-actions-cicd-front.md` | `update-manifest` job |

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
