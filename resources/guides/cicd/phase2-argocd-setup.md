# Phase 2 매니페스트 레포지토리 + ArgoCD 구성 가이드

> 본 가이드는 `skills/cicd/SKILL.md > Phase 2`에서 호출됨.
> Git 크리덴셜 사전 수집 → ArgoCD 구성 → 매니페스트 레포 Push → CI 도구별 추가 정보 수집 + `[실행정보]` 보완까지 4개 Step 절차를 정의.

## 입력

- Phase 0 / Step 8에서 조립된 `[실행정보]` 블록 (CI 도구 전용 필드 미정 상태)
- `{MANIFEST_REPO_URL}` (Phase 0 / Step 6)
- `{ENVIRONMENTS}` (Phase 0 / Step 7)
- `{K8S_CLUSTER}`, `{K8S_NAMESPACE}` (Phase 0 / Step 4)
- 사용자 입력 가능: GIT_USERNAME, GIT_TOKEN (Step 1), Jenkins 설정 (Step 4)

## 의존 가이드

- **참조 가이드**: `{NPD_PLUGIN_DIR}/resources/guides/cicd/deploy-argocd-cicd.md` — 에이전트가 실제 구성 시 참조하는 가이드

## Kustomize 파일 관리 원칙

> Phase 2에서 매니페스트 레포지토리에 Kustomize 파일을 생성합니다 (ArgoCD가 감시하는 "라이브" 매니페스트). Phase 3에서는 CI/CD 파이프라인 파일(Jenkinsfile/GitHub Actions workflow)을 생성하며, 파이프라인의 마지막 단계에서 매니페스트 레포의 image tag만 업데이트합니다.

---

## Step 1. Git 크리덴셜 사전 수집 (에이전트 호출 전)

> 에이전트는 사용자에게 직접 질문할 수 없으므로, ArgoCD 인증 등록에 필요한 Git 크리덴셜을 오케스트레이터가 사전 수집하여 에이전트 프롬프트에 포함해야 한다.

<!--ASK_USER-->
{"title":"ArgoCD 매니페스트 레포 인증 정보","questions":[
  {"question":"ArgoCD에서 Private 매니페스트 레포지토리에 접근하기 위한 Git 인증 정보를 입력하세요.\n\n1) GitHub 사용자명\n2) GitHub Personal Access Token (repo 권한 필요)\n\n※ Jenkins Credential에 등록한 동일한 PAT를 사용해도 됩니다.","type":"text","placeholder":"username / token"}
]}
<!--/ASK_USER-->

수집된 Git 크리덴셜을 에이전트 프롬프트에 다음과 같이 포함한다:
- `GIT_USERNAME`: 사용자명
- `GIT_TOKEN`: Personal Access Token

---

## Step 2. ArgoCD 구성 (TASK) → Agent: devops-engineer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/cicd/deploy-argocd-cicd.md`
- **에이전트 프롬프트 필수 지시**: "ArgoCD 가이드의 '매니페스트 레포지토리 구성', 'ArgoCD Application YAML 생성', 'ArgoCD 매니페스트 레포지토리 인증 등록', 'ArgoCD Application 등록' 섹션을 참조하세요. 'CI 파이프라인의 매니페스트 업데이트 스크립트 참조' 섹션은 Phase 3에서 처리합니다."
- **CONTEXT**: Phase 0 / Step 8에서 조립된 `[실행정보]` 블록 + Step 1에서 수집한 `GIT_USERNAME`/`GIT_TOKEN` 포함

**가이드에 없는 보충 정보:**
- **ArgoCD Private 레포 인증**: 매니페스트 레포지토리가 Private인 경우, ArgoCD 인증 등록에 Git 크리덴셜이 필요합니다. 오케스트레이터가 Step 1에서 사전 수집한 `GIT_USERNAME`/`GIT_TOKEN` 값을 에이전트 프롬프트에 포함하여 전달하세요.

**EXPECTED OUTCOME:**
- 매니페스트 레포지토리 구조 생성 (Kustomize base/overlays — `{ENVIRONMENTS}` 환경만)
- ArgoCD 매니페스트 레포지토리 인증 등록 (Private 레포인 경우)
- ArgoCD Application YAML 파일 생성 (`argocd/*.yaml` — `{ENVIRONMENTS}` 환경만)
- ArgoCD Application 등록 완료
- `deploy-argocd-prepare.md` 결과 보고서 작성 (프로젝트 루트)

---

## Step 3. 매니페스트 레포지토리 Push (POST_ACTION)

Step 2에서 생성된 매니페스트 레포지토리 파일을 원격에 커밋·푸시한다.
ArgoCD가 매니페스트 레포지토리 변경을 감지하려면 원격에 push되어 있어야 한다.

```bash
cd {매니페스트 레포지토리 로컬 경로}
git add .
git commit -m "cicd: 매니페스트 레포지토리 초기 구성 (Kustomize + ArgoCD Application)"
git push origin main
```

---

## Step 4. CI 도구별 추가 정보 수집 + [실행정보] 보완

> Step 3 완료 후, Phase 3(파이프라인 작성) 전에 CI 도구 전용 필드를 수집하여 [실행정보]를 보완.

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

수집된 필드를 [실행정보]에 보완하여 Phase 3에 전달.

---

## 산출물

- 매니페스트 레포지토리 구조 (Kustomize base/overlays — `{ENVIRONMENTS}` 환경만)
- ArgoCD Application YAML (`argocd/*.yaml` — `{ENVIRONMENTS}` 환경만, 등록 완료)
- 원격 매니페스트 레포지토리에 push 완료
- `deploy-argocd-prepare.md` 결과 보고서 (프로젝트 루트)
- 보완된 `[실행정보]` 블록 (CI 도구 전용 필드 채워짐) — Phase 3 입력으로 사용
