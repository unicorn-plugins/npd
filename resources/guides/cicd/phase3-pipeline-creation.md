# Phase 3 CI/CD 파이프라인 작성 가이드

> 본 가이드는 `skills/cicd/SKILL.md > Phase 3`에서 호출됨.
> CI 도구별 가이드 선택 → 백엔드/프론트엔드/AI 서비스 파이프라인 작성 → 소스 레포 Push까지 4개 Step 절차를 정의.

## 입력

- Phase 0 / Step 5에서 감지된 프로젝트 유형 (백엔드/프론트엔드/AI 서비스)
- Phase 0 / Step 8 + Phase 2 / Step 4에서 조립·보완된 `[실행정보]` 블록 (CI 도구 전용 필드 채워짐)
- 매니페스트 레포지토리 (Phase 2 산출물)

## 의존 가이드 (CI 도구별)

```
IF CI_TOOL == Jenkins:
    백엔드 -> {NPD_PLUGIN_DIR}/resources/guides/cicd/deploy-jenkins-cicd-back.md
    프론트엔드 -> {NPD_PLUGIN_DIR}/resources/guides/cicd/deploy-jenkins-cicd-front.md
    AI 서비스 -> {NPD_PLUGIN_DIR}/resources/guides/cicd/deploy-jenkins-cicd-ai.md
ELSE IF CI_TOOL == GitHubActions:
    백엔드 -> {NPD_PLUGIN_DIR}/resources/guides/cicd/deploy-actions-cicd-back.md
    프론트엔드 -> {NPD_PLUGIN_DIR}/resources/guides/cicd/deploy-actions-cicd-front.md
    AI 서비스 -> {NPD_PLUGIN_DIR}/resources/guides/cicd/deploy-actions-cicd-ai.md
```

> 클라우드별 분기 불필요. 가이드 내 조건부 섹션이 `[실행정보]`의 CLOUD 값에 따라 registry login 방식을 분기.

**추가 참조 가이드**: `{NPD_PLUGIN_DIR}/resources/guides/cicd/deploy-argocd-cicd.md` (manifest repo 업데이트 스크립트 부분만)

## 에이전트 프롬프트 필수 지시

1. "가이드의 **Jenkinsfile 템플릿**을 **그대로 사용**하고, `{플레이스홀더}`만 실제 값으로 치환하세요. 가이드에 없는 파이프라인 구조, 문법, 컨테이너 이미지를 사용하지 마세요."
2. "Jenkins Job 생성, 빌드 실행, 결과 검증까지 가이드의 해당 섹션을 따라 수행하세요."

## 에이전트 검증 체크리스트 (생성된 파일을 가이드와 비교)

- [ ] 파이프라인 방식 일치 (Scripted/Declarative)
- [ ] 컨테이너 런타임 일치 (Podman/Docker)
- [ ] SonarQube 단계 포함 여부 일치
- [ ] 매니페스트 업데이트 방식 일치 (kustomize edit / sed)
- [ ] 리소스 제한(requests/limits) 포함 여부 일치

## 백엔드/프론트엔드/AI 감지 로직

> 백엔드, 프론트엔드, AI 서비스는 별도 프로젝트(리포지토리)에 있을 수 있다. 스킬은 현재 프로젝트의 유형을 자동 감지하여 해당하는 파이프라인만 생성한다.
> - **백엔드 감지**: `settings.gradle` 또는 `build.gradle` 존재
> - **프론트엔드 감지**: `package.json` 존재 (settings.gradle 없음)
> - **AI 서비스 감지**: `pyproject.toml` 존재
> - **여러 유형이 공존하는 경우**: Phase 0 / Step 5에서 사용자에게 확인 후 해당하는 파이프라인 모두 생성

### ⚠️ 모노레포(여러 유형 공존) 파일 충돌 방지

- Jenkins: 백엔드 `Jenkinsfile-backend`, 프론트엔드 `Jenkinsfile-frontend`, AI `Jenkinsfile-ai`로 분리
- GitHub Actions: 워크플로우 파일명이 이미 분리됨 (`backend-cicd.yaml`, `frontend-cicd.yaml`, `ai-cicd.yaml`)

---

## Step 1. 백엔드 CI/CD 파이프라인 작성 → Agent: devops-engineer

- **GUIDE**: 위 의존 가이드의 백엔드 가이드 + ArgoCD 가이드 (manifest 업데이트 스크립트)
- **CONTEXT**: Phase 0 / Step 8 + Phase 2 / Step 4에서 조립·보완된 `[실행정보]` 블록 포함
- **TASK**: 가이드의 **Jenkinsfile 템플릿**을 **그대로 사용**하여 `{플레이스홀더}`만 실제 값으로 치환. 가이드의 'Jenkins Job 생성 및 빌드 실행' 섹션을 따라 Job 생성, 빌드 실행, 결과 검증까지 수행
- **EXPECTED OUTCOME**:
  - Jenkins: `deployment/cicd/Jenkinsfile-backend`, `docs/cicd/deploy-jenkins-cicd-back-result.md`
  - GitHub Actions: `.github/workflows/backend-cicd.yaml`, `docs/cicd/deploy-actions-cicd-back-result.md`

---

## Step 2. 프론트엔드 CI/CD 파이프라인 작성 → Agent: devops-engineer

- **GUIDE**: 위 의존 가이드의 프론트엔드 가이드 + ArgoCD 가이드 (manifest 업데이트 스크립트)
- **CONTEXT**: Phase 0 / Step 8 + Phase 2 / Step 4에서 조립·보완된 `[실행정보]` 블록 포함
- **TASK**: 가이드의 **Jenkinsfile 템플릿**을 **그대로 사용**하여 `{플레이스홀더}`만 실제 값으로 치환. 가이드의 'Jenkins Job 생성 및 빌드 실행' 섹션을 따라 Job 생성, 빌드 실행, 결과 검증까지 수행
- **EXPECTED OUTCOME**:
  - Jenkins: `deployment/cicd/Jenkinsfile-frontend`, `docs/cicd/deploy-jenkins-cicd-front-result.md`
  - GitHub Actions: `.github/workflows/frontend-cicd.yaml`, `docs/cicd/deploy-actions-cicd-front-result.md`

---

## Step 3. AI 서비스 CI/CD 파이프라인 작성 → Agent: devops-engineer

- **GUIDE**: 위 의존 가이드의 AI 서비스 가이드 + ArgoCD 가이드 (manifest 업데이트 스크립트)
- **CONTEXT**: Phase 0 / Step 8 + Phase 2 / Step 4에서 조립·보완된 `[실행정보]` 블록 포함
- **TASK**: 가이드의 **Jenkinsfile 템플릿**을 **그대로 사용**하여 `{플레이스홀더}`만 실제 값으로 치환. 가이드의 'Jenkins Job 생성 및 빌드 실행' 섹션을 따라 Job 생성, 빌드 실행, 결과 검증까지 수행
- **EXPECTED OUTCOME**:
  - Jenkins: `deployment/cicd/Jenkinsfile-ai`, `docs/cicd/deploy-jenkins-cicd-ai-result.md`
  - GitHub Actions: `.github/workflows/ai-cicd.yaml`, `docs/cicd/deploy-actions-cicd-ai-result.md`

---

## Step 4. 소스 레포지토리 Push (POST_ACTION)

Step 1~3에서 생성된 CI/CD 파이프라인 파일을 소스 레포지토리에 커밋·푸시한다.
Jenkins가 파이프라인 파일에 접근하려면 원격 레포에 push되어 있어야 한다.

```bash
# 생성된 파이프라인 파일 커밋 및 푸시
git add deployment/cicd/Jenkinsfile-* deployment/cicd/deploy-jenkins-cicd-*-result.md
# 또는 GitHub Actions인 경우
# git add .github/workflows/*-cicd.yaml deployment/cicd/deploy-actions-cicd-*-result.md
git commit -m "cicd: CI/CD 파이프라인 파일 생성 (Phase 3)"
git push origin main
```

---

## 산출물

- CI/CD 파이프라인 파일 (감지된 프로젝트 유형별):
  - Jenkins: `deployment/cicd/Jenkinsfile-{backend,frontend,ai}`
  - GitHub Actions: `.github/workflows/{backend,frontend,ai}-cicd.yaml`
- 결과 보고서: `docs/cicd/deploy-{jenkins,actions}-cicd-{back,front,ai}-result.md` (해당 시)
- 소스 레포지토리에 push 완료 (Jenkins가 파이프라인 파일에 접근 가능)
- 모든 파이프라인은 manifest repo image tag 업데이트 단계로 종료 (kubectl apply 없음)
