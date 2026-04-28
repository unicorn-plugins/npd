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

## 활성화 조건

사용자가 `/npd:cicd` 호출 시 또는 "CICD 시작", "CI/CD 구성", "파이프라인 작성", "자동 배포" 키워드 감지 시.

주의사항: 중간 단계부터 시작할 때도 진행 모드 결정 + 환경 정보 수집을 위해 Phase 0은 항상 수행해야 합니다.

## 선행 조건

- `/npd:create` 완료 (프로젝트 디렉토리 및 AGENTS.md 존재)
- `/npd:deploy` Phase 5 (K8s 배포)까지 완료된 상태 (기존 K8s 매니페스트 `deployment/k8s/` 존재)
- CI/CD 도구 설치: Phase 1에서 자동 설치 또는 사전 설치 완료 (CI 도구, SonarQube, ArgoCD, Image Registry Credential)

## 작업 환경 변수 로드

AGENTS.md 파일에서 `## 환경변수` 섹션의 환경변수 로딩.
로딩 실패 시 사용자에게 `/npd:create`을 먼저 수행하라고 안내하고 종료.

## 에이전트 호출 규칙

| 에이전트 | FQN |
|----------|-----|
| devops-engineer | `npd:devops-engineer:devops-engineer` |

### 프롬프트 조립

- `{NPD_PLUGIN_DIR}/resources/guides/combine-prompt.md`에 따라
  AGENT.md + agentcard.yaml + tools.yaml 합치기
- `Agent(subagent_type=FQN, model=tier_mapping 결과, prompt=조립된 프롬프트)` 호출
- tier → 모델 매핑은 `{NPD_PLUGIN_DIR}/gateway/runtime-mapping.yaml` 참조

### 서브 에이전트 호출

워크플로우 단계에 `Agent: {agent-name}`이 명시된 경우,
메인 에이전트는 해당 단계를 직접 수행하지 않고,
반드시 위 프롬프트 조립 규칙에 따라 해당 에이전트를 호출하여 결과를 받아야 함.

서브에이전트 호출 없이 메인 에이전트가 해당 산출물을 직접 작성하면
스킬 미준수로 간주함.

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

CI 도구에 따라 참조할 가이드 파일이 결정된다. **클라우드별 분기 불필요** — CI/CD 분리 후 클라우드별 차이는 registry login 1개 step뿐이므로, 가이드 내 조건부 섹션으로 처리한다. 모든 가이드는 `{NPD_PLUGIN_DIR}/resources/guides/cicd/` 경로에 위치한다.

| CI 도구 | 백엔드 가이드 | 프론트엔드 가이드 | AI 서비스 가이드 |
|---------|-------------|----------------|----------------|
| Jenkins | `deploy-jenkins-cicd-back.md` | `deploy-jenkins-cicd-front.md` | `deploy-jenkins-cicd-ai.md` |
| GitHub Actions | `deploy-actions-cicd-back.md` | `deploy-actions-cicd-front.md` | `deploy-actions-cicd-ai.md` |

> **Phase 1 가이드**: CI/CD 도구 사전 설치는 `cicd-pre-setup.md` 가이드를 참조한다 (CI 도구·클라우드 무관 공통).

## CI/CD 분리 핵심 원칙

> **CI의 책임**: 빌드 → 이미지 푸시 → **manifest repository의 YAML에서 image tag만 변경**  
> **CD의 책임**: ArgoCD가 manifest repository 변경을 감지하여 K8s에 자동 배포  
> **CI에서 kubectl apply 절대 금지**: CI 파이프라인은 K8s에 직접 배포하지 않는다.  
>
> 기존 CI 가이드(deploy-jenkins-cicd-*.md, deploy-actions-cicd-*.md)의 빌드·푸시 부분과
> ArgoCD 가이드(deploy-argocd-cicd.md)의 manifest repo 업데이트 부분을 **하나의 파이프라인에 결합**하여
> 처음부터 CI/CD가 분리된 파이프라인을 생성한다.
> 별도의 `_ArgoCD` 변환 단계는 불필요하다.

## 진행상황 업데이트 및 재개

`{PROJECT_DIR}/AGENTS.md`에 각 Phase의 Step 완료 시 저장. 최종 완료 시 `Done`으로 표기.

```md
## 워크플로우 진행상황
### cicd
- 진행 모드: {선택값}
- CI_TOOL: {Jenkins|GitHubActions} (Phase 0 / Step 3에서 기록)
- CLOUD: {AWS|Azure|GCP} (`### deploy`에서 복원)
- 레지스트리유형: {DockerHub|ECR|ACR|GCR}
- AI_SERVICE: {값}
- MANIFEST_REPO_URL: {값} (Phase 0 / Step 6에서 기록)
- VM_HOST: {값}
- ENVIRONMENTS: {값} (Phase 0 / Step 7에서 기록)
- K8S_CLUSTER, K8S_NAMESPACE: {값}
- 마지막 완료 Phase/Step: {Phase X / Step Y}
```

진행상황 정보가 있는 경우 마지막 완료 Step 이후부터 자동 재개.
`### deploy` 섹션도 함께 읽어 사전 바인딩 적용 (Phase 0 / Step 4 규칙).

## 워크플로우

### 개요

```
Phase 0: 사전 체크 + 모드 선택 + 정보 수집 (8 Step)
   ↓
Phase 1: CI/CD 도구 사전 설정 (사전작업 + 병렬 도구 설치 + Nginx + 수동 확인)
   ↓
Phase 2: 매니페스트 레포지토리 + ArgoCD 구성 (Git 크리덴셜 + ArgoCD 구성 + Push + CI 도구별 추가 정보)
   ↓
Phase 3: CI/CD 파이프라인 작성 (백엔드·프론트엔드·AI + Push)
   ↓
Phase 4: 완료 보고
```

### Phase 0: 사전 체크 + 모드 선택 + 정보 수집

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/cicd/phase0-presetup.md` ← **필수 로드**
- **TASK**: 위 GUIDE의 8개 Step 절차에 따라 사용자 입력 사전 수집 + `[실행정보]` 조립 (Step 8은 `cicd-runinfo-templates.md` 참조)
- **EXPECTED OUTCOME**: `[실행정보]` 블록 (CI 도구 + Cloud 조합별 7가지 템플릿 중 하나) + AGENTS.md `### cicd` 진행상황 갱신

#### Step 1. hosts 파일 등록 확인
CI/CD 도구 웹 UI 접속용 hosts 파일 등록 확인.

#### Step 2. 진행 모드 선택
단계별 승인/자동 진행 선택. 자동 진행 시 Phase 1~3 실행 중 ASK_USER 호출 자제.

#### Step 3. CI 도구 선택
Jenkins / GitHub Actions 선택.

#### Step 4. deploy 환경 정보 복원
`AGENTS.md > ### deploy`에서 CLOUD/레지스트리/VM_HOST/K8S 변수 바인딩.

#### Step 5. 프로젝트 유형 감지 및 사전 검증
백/프/AI 자동 감지 + K8s 매니페스트 존재 검증 + 프로젝트명 자동 감지.

#### Step 6. 매니페스트 레포지토리 URL 결정
`{org}/{SYSTEM_NAME}-manifest.git` 자동 결정.

#### Step 7. 배포 환경 선택
ENVIRONMENTS = dev/staging/prod (multi-select).

#### Step 8. [실행정보] 조립
- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/cicd/cicd-runinfo-templates.md` ← **필수 로드**
- CI 도구 + 레지스트리 조합에 따라 7가지 템플릿 중 1개 조립 + AGENTS.md 상태 기록.

---

### Phase 1: CI/CD 도구 사전 설정 → Agent: devops-engineer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/cicd/cicd-pre-setup.md` ← **필수 로드**
- **CONTEXT**: Phase 0 / Step 8에서 조립된 `[실행정보]` 블록 포함
- **TASK**: 가이드를 참조하여 클라우드별 사전작업 수행 및 CI/CD 도구(Jenkins/SonarQube/ArgoCD) 설치
- **실행 조건**: 항상 수행. 이미 설치된 도구는 자동 건너뜀 (idempotent)

#### Step 1. 사전작업 + 매니페스트 레포 생성 (순차)

1. 클라우드별 사전작업 (StorageClass, IngressClass, NodePool)
2. 매니페스트 레포지토리 생성 (`gh repo create {org}/{SYSTEM_NAME}-manifest --private`, 이미 존재 시 건너뜀)

#### Step 2. 도구 설치 (병렬)

Step 1 완료 후, 아래 도구를 **병렬로 설치** (각각 독립 에이전트 호출).

| Sub-step | 가이드 섹션 | 설치 내용 |
|----------|-----------|----------|
| **Step 2-1** | Phase 2 | Jenkins Helm 설치 + RBAC (CI_TOOL == Jenkins인 경우) |
| **Step 2-2** | Phase 3 | SonarQube Helm 설치 + affinity 패치 + scale 재시작 + 백엔드 단위테스트 실행·에러 해결 |
| **Step 2-3** | Phase 4 | ArgoCD Helm 설치 + --insecure 검증 |

> Jenkins와 ArgoCD는 cicd NodePool을, SonarQube는 sonarqube NodePool을 사용.
> NodePool 리밋(cpu:16, mem:64Gi)이 충분하므로 동시 스케줄링 가능.
> CI_TOOL == GitHubActions이면 Step 2-1(Jenkins)는 건너뜀 (Step 2-2·2-3 2개만 병렬).

##### Step 2-1. Jenkins Helm 설치 + RBAC → Agent: devops-engineer

- 가이드의 Phase 2 섹션 참조
- CI_TOOL == Jenkins인 경우만 수행. GitHub Actions이면 건너뜀.

##### Step 2-2. SonarQube Helm 설치 + 설정 → Agent: devops-engineer

- 가이드의 Phase 3 섹션 참조
- affinity 패치 + scale 재시작 + 백엔드 단위테스트 실행·에러 해결 포함

##### Step 2-3. ArgoCD Helm 설치 + 검증 → Agent: devops-engineer

- 가이드의 Phase 4 섹션 참조
- --insecure 검증 포함

#### Step 3. Nginx 프록시 + 보고서 (순차) → Agent: devops-engineer

Step 2 (병렬 도구 설치) 완료 후:
1. Nginx 프록시 설정 (SSH로 Web Server VM에 자동 설정)
2. 프록시 연결 검증 (curl)
3. `docs/cicd/cicd-pre-setup-report.md` 결과 보고서 작성 (접속정보 + 암호 포함)

**EXPECTED OUTCOME (Phase 1 / Step 1~3 종합):**
- 클라우드별 사전작업 완료 (StorageClass, NodePool 등)
- Jenkins Pod 정상 실행 (CI_TOOL == Jenkins인 경우)
- SonarQube Pod 정상 실행
- 백엔드 단위테스트 통과 및 JaCoCo 리포트 생성 확인 (SonarQube 설정 후)
- ArgoCD Pod 정상 실행
- Nginx 프록시 설정 완료 (SSH 자동, `nginx -t` 성공, curl 검증 통과)
- 수동 후속 작업 안내 메시지 출력
- `docs/cicd/cicd-pre-setup-report.md` 결과 보고서 작성 (프로젝트 루트)

**수동 후속 작업 안내** (에이전트가 자동 설치 완료 후, 사용자에게 안내):
- hosts 파일 등록
- Jenkins 플러그인 설치 및 K8s Cloud 연결
- SonarQube Token/Webhook/Quality Gate 설정
- Image Registry / DockerHub Credential 등록
- (GitHub Actions 선택 시) Repository Secrets/Variables 등록

수동 안내 시 `setup-cicd-tools.md` 원본 가이드 링크를 참조 제공.

#### Step 4. 수동 설정 완료 확인 (Phase 2 시작 전)

> Step 1~3 자동 설치 완료 후 (또는 "이미 설치 완료" 선택 시), Phase 2 진행 전에
> `setup-cicd-tools.md`의 수동 후속 설정 완료 여부를 확인한다.

<!--ASK_USER-->
{"title":"수동 설정 완료 확인","questions":[
  {"question":"CI/CD 도구의 수동 후속 설정을 완료했나요?\n\n- hosts 파일 등록\n- Jenkins 플러그인 설치 및 K8s Cloud 연결 (Jenkins 선택 시)\n- SonarQube Token/Webhook/Quality Gate 설정\n- Image Registry / DockerHub Credential 등록 (Jenkins 선택 시)\n- GitHub Actions Secrets/Variables 등록 (GitHub Actions 선택 시)\n\n미완료 시 아래 가이드를 참조하세요:\nhttps://github.com/unicorn-plugins/npd/blob/main/resources/references/setup-cicd-tools.md","type":"radio","options":["모두 완료","아직 미완료"]}
]}
<!--/ASK_USER-->

- **"모두 완료"** 선택 시: Phase 2 진행
- **"아직 미완료"** 선택 시: 가이드 링크를 다시 안내하고 완료 대기

---

### Phase 2: 매니페스트 레포지토리 + ArgoCD 구성 → Agent: devops-engineer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/cicd/phase2-argocd-setup.md` ← **필수 로드**
  (참조: `{NPD_PLUGIN_DIR}/resources/guides/cicd/deploy-argocd-cicd.md`)
- **TASK**: 위 GUIDE의 4개 Step에 따라 Git 크리덴셜 수집 → ArgoCD 구성 → 매니페스트 레포 Push → CI 도구별 추가 정보 수집
- **EXPECTED OUTCOME**: 매니페스트 레포지토리 구조 + ArgoCD Application YAML + AGENTS.md `### cicd > [실행정보]` 보완

> **Kustomize 파일 관리 원칙**: Phase 2에서 매니페스트 레포지토리에 Kustomize 파일을 생성합니다 (ArgoCD가 감시하는 "라이브" 매니페스트). Phase 3에서는 CI/CD 파이프라인 파일(Jenkinsfile/GitHub Actions workflow)을 생성하며, 파이프라인의 마지막 단계에서 매니페스트 레포의 image tag만 업데이트합니다.

#### Step 1. Git 크리덴셜 사전 수집 (에이전트 호출 전)
ArgoCD Private 레포 인증용 GIT_USERNAME/GIT_TOKEN 수집.

#### Step 2. ArgoCD 구성 (TASK)
Kustomize base/overlays + ArgoCD Application YAML 생성·등록.

#### Step 3. 매니페스트 레포지토리 Push (POST_ACTION)
ArgoCD가 변경 감지하도록 원격 레포에 push.

#### Step 4. CI 도구별 추가 정보 수집 + [실행정보] 보완
Jenkins: JENKINS_CLOUD_NAME, JENKINS_GIT_CREDENTIALS / GitHub Actions: 고정값 사용.

---

### Phase 3: CI/CD 파이프라인 작성 → Agent: devops-engineer

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/cicd/phase3-pipeline-creation.md` ← **필수 로드**
  (참조: 위 `## 가이드 선택 매트릭스`의 CI 도구별 가이드 + `deploy-argocd-cicd.md` manifest 업데이트 스크립트)
- **TASK**: 위 GUIDE의 4개 Step에 따라 백엔드·프론트엔드·AI 서비스 파이프라인 작성 (Phase 0 / Step 5에서 감지된 유형만) + 소스 레포 Push
- **EXPECTED OUTCOME**: CI/CD 파이프라인 파일 (Jenkinsfile 또는 GitHub Actions workflow) + 결과 보고서

#### Step 1. 백엔드 CI/CD 파이프라인 작성
가이드의 Jenkinsfile 템플릿 그대로 사용 + `{플레이스홀더}` 치환 + Job 생성·빌드·검증.

#### Step 2. 프론트엔드 CI/CD 파이프라인 작성
프론트엔드 가이드 + ArgoCD manifest 업데이트 스크립트.

#### Step 3. AI 서비스 CI/CD 파이프라인 작성
AI 가이드 + ArgoCD manifest 업데이트 스크립트.

#### Step 4. 소스 레포지토리 Push (POST_ACTION)
Step 1~3 산출물을 소스 레포에 push (Jenkins가 파이프라인 파일에 접근 가능하도록).

---

### Phase 4: 완료 보고

스킬 레벨에서 직접 수행 (에이전트 호출 없음).

#### Step 1. 완료 보고

```
## CI/CD 파이프라인 구성 완료

### 환경 정보
- CI 도구: {Jenkins / GitHub Actions}
- CD 도구: ArgoCD (GitOps)
- Cloud: {AWS / Azure / GCP}
- K8s 클러스터: {클러스터명}

### Phase 1: CI/CD 도구 사전 설정 산출물
- 클라우드 사전작업: {완료/건너뜀}
- Jenkins: {설치 완료/건너뜀} (CI_TOOL에 따라)
- SonarQube: {설치 완료/건너뜀}
- ArgoCD: {설치 완료/건너뜀}
- Nginx 프록시: {설정 완료} (VM: {VM_HOST})
- 사전 설정 보고서: `docs/cicd/cicd-pre-setup-report.md`

### Phase 2: 매니페스트 레포지토리 + ArgoCD 산출물
- 매니페스트 레포지토리: {MANIFEST_REPO_URL}
- ArgoCD Application YAML: argocd/*.yaml
- ArgoCD Application 등록: 완료
- ArgoCD 준비 보고서: `deploy-argocd-prepare.md`

### Phase 3: CI/CD 파이프라인 산출물
- 백엔드: {파이프라인 파일 경로} (빌드+푸시+manifest tag 업데이트)
- 프론트엔드: {파이프라인 파일 경로} (빌드+푸시+manifest tag 업데이트)
- AI 서비스: {파이프라인 파일 경로} (빌드+푸시+manifest tag 업데이트)

### 다음 단계
1. CI 파이프라인 실행하여 전체 흐름 검증 (빌드 → 푸시 → manifest 업데이트 → ArgoCD 자동 배포)
```

---

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |
| 2 | CI 도구 선택(Jenkins/GitHub Actions)에 따라 가이드 선택 매트릭스를 참조하여 해당하는 가이드만 참조할 것 (클라우드별 분기 불필요) |
| 3 | CI 파이프라인에 kubectl apply를 포함하지 않을 것. 마지막 단계는 manifest repo image tag 업데이트여야 함 |
| 4 | `[실행정보]` 블록을 에이전트 프롬프트에 반드시 포함할 것 — CI 도구 + 레지스트리유형 조합에 맞는 템플릿 사용 |
| 5 | GitHub Actions 가이드 내 클라우드별 조건부 섹션이 `[실행정보]`의 CLOUD 값에 따라 올바르게 적용되도록 할 것 |
| 6 | Phase 0의 사전 도구 체크는 설치 여부 확인만 수행. 미설치 시 Phase 1에서 가이드(`cicd-pre-setup.md`) 기반 자동 설치 진행. Phase 0에서 직접 설치 금지 |
| 7 | `Agent: {agent-name}`이 명시된 Step은 메인 에이전트가 직접 수행 금지. 반드시 프롬프트 조립 규칙에 따라 서브에이전트 호출 |
| 8 | 외부 가이드(`{NPD_PLUGIN_DIR}/resources/guides/cicd/*.md`)가 명시된 Step은 해당 가이드를 **반드시 Read로 로드한 뒤** 절차를 수행할 것. SKILL.md 본문의 요약만 보고 직접 수행하면 스킬 미준수로 간주 |

## 완료 조건

- [ ] Phase 0 / Step 1~8 완료 (hosts·진행 모드·CI 도구·deploy 복원·프로젝트 감지·MANIFEST·환경·`[실행정보]` 조립)
- [ ] Phase 1 / Step 1: 클라우드별 사전작업 + 매니페스트 레포지토리 생성 완료
- [ ] Phase 1 / Step 2: CI/CD 도구 Pod 정상 실행 (Jenkins/SonarQube/ArgoCD — 병렬 설치)
- [ ] Phase 1 / Step 3: Nginx 프록시 설정 완료 (`nginx -t` 성공) + `docs/cicd/cicd-pre-setup-report.md` 작성
- [ ] Phase 1 / Step 4: 수동 후속 작업 완료 확인
- [ ] Phase 2 / Step 1~2: Git 크리덴셜 수집·매니페스트 레포지토리 구조 생성·ArgoCD Application YAML 생성·등록
- [ ] Phase 2 / Step 3: 매니페스트 레포지토리 Push 완료
- [ ] Phase 2 / Step 4: CI 도구별 추가 정보 수집·`[실행정보]` 보완
- [ ] Phase 3 / Step 1~3: CI/CD 파이프라인 파일 생성 (백엔드/프론트엔드/AI 해당 시) — kubectl apply 없이 manifest repo image tag 업데이트 포함
- [ ] Phase 3 / Step 4: 소스 레포지토리 Push 완료
- [ ] Phase 4 / Step 1: 완료 보고서 작성
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (매니페스트 레포 구조, ArgoCD YAML, 파이프라인 파일)
2. ArgoCD Application YAML 유효성 검사 (`kubectl apply --dry-run=client -f argocd/`)
3. Kustomize 유효성 검사 (`kubectl kustomize` dry-run)
4. 파이프라인 파일 문법 검증 (변수 참조 `${variable}` 사용, `\${variable}` 사용 금지 등)
5. Phase 1 / Step 2 도구 설치 검증: `kubectl get po -n jenkins` (Jenkins 선택 시), `kubectl get po -n sonarqube`, `kubectl get po -n argocd`
6. Phase 1 / Step 1 사전작업 검증: `kubectl get storageclass` (AWS), `kubectl get nodepool` (AWS/Azure)
7. Phase 1 / Step 3 Nginx 검증: `ssh {VM_HOST} 'sudo nginx -t'`

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.
