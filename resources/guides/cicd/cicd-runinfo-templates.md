# CI/CD `[실행정보]` 조립 템플릿 가이드

> 본 가이드는 `skills/cicd/SKILL.md > Phase 0 / Step 8`(및 `Phase 2 / Step 4`의 보완 단계)에서 호출됨.
> CI 도구 + 클라우드/레지스트리 조합에 따른 `[실행정보]` 블록 조립 템플릿 7가지를 정의.

## 입력

- `{CI_TOOL}`: Jenkins / GitHubActions (Phase 0 / Step 3)
- `{CLOUD}`: AWS / Azure / GCP (Phase 0 / Step 4에서 `### deploy` 복원)
- `{레지스트리유형}`: DockerHub / ECR / ACR / GCR (Phase 0 / Step 4)
- `{SYSTEM_NAME}`, `{FRONTEND_SERVICE}`, `{AI_SERVICE}` (Phase 0 / Step 5)
- `{MANIFEST_REPO_URL}` (Phase 0 / Step 6)
- `{ENVIRONMENTS}` (Phase 0 / Step 7)
- `{VM_HOST}`, `{K8S_CLUSTER}`, `{K8S_NAMESPACE}` (deploy 복원)

## 사용 원칙

- 조립된 `[실행정보]` 블록은 이후 Agent 호출 시 **프롬프트의 동적(작업 지시) 영역에 텍스트로 포함**하여 전달
- 에이전트는 별도 컨텍스트에서 실행되므로, `Agent(prompt=...)` 호출 시 `[실행정보]` 블록 전문을 반드시 포함해야 가이드 내 변수를 치환 가능
- **2단계 조립**: Phase 0 / Step 8에서 base [실행정보] 조립. CI 도구 전용 필드(JENKINS_CLOUD_NAME, JENKINS_GIT_CREDENTIALS, MANIFEST_SECRET_GIT_USERNAME/PASSWORD, RESOURCE_GROUP, GKE_ZONE)는 미정으로 남기고, Phase 2 / Step 4에서 보완

---

## 7가지 템플릿

### Jenkins + Docker Hub
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

### Jenkins + ECR
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

### Jenkins + ACR
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

### Jenkins + Google Artifact Registry (GCR)
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

### GitHub Actions + Azure AKS (ACR)
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

### GitHub Actions + AWS EKS (ECR)
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

### GitHub Actions + GCP GKE (Google Artifact Registry)
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

## 조건부 필드 규칙

- `FRONTEND_SERVICE`: `package.json` 감지 시에만 포함 (Phase 0 / Step 5)
- `AI_SERVICE`: `pyproject.toml` 감지 시에만 포함 (Phase 0 / Step 5)
- 순수 AI 프로젝트는 FRONTEND_SERVICE 없이 AI_SERVICE만 포함 가능

## 산출물

- 7가지 템플릿 중 1개를 채택하여 조립된 `[실행정보]` 블록
- Phase 3 ~ Phase 5의 모든 Agent 호출 시 프롬프트의 동적 영역에 텍스트로 포함
- `AGENTS.md > ## 워크플로우 진행상황 > ### cicd` 섹션에 주요 필드 갱신 (CI_TOOL·CLOUD·레지스트리유형·MANIFEST_REPO_URL·ENVIRONMENTS·K8S_CLUSTER·K8S_NAMESPACE)
