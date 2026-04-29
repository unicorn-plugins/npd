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

## 활성화 조건

사용자가 `/npd:deploy` 호출 시 또는 "수동 배포 시작", "수동 배포해줘" 키워드 감지 시.

주의사항: 중간 단계부터 시작할 때도 진행 모드 결정 + 환경 정보 수집을 위해 Phase 0은 항상 수행해야 합니다.

## 선행 조건

- `/npd:create` 완료 (프로젝트 디렉토리 및 AGENTS.md 존재)
- `/npd:develop` 완료 (소스코드 존재)

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

## 진행상황 업데이트 및 재개

`{PROJECT_DIR}/AGENTS.md`에 각 Phase의 Step 완료 시 저장. 최종 완료 시 `Done`으로 표기.

```md
## 워크플로우 진행상황
### deploy
- 진행 모드: {선택값}
- CLOUD: {AWS|Azure|GCP}
- 레지스트리유형: {DockerHub|ECR|ACR|GCR}
- IMG_REG: {값}
- IMG_ORG: {값}
- ECR_ACCOUNT, ECR_REGION: {값} ← ECR인 경우
- ACR명: {값} ← ACR인 경우
- GCR_PROJECT, GCR_REGION, GCR_REPO: {값} ← GCR인 경우
- VM_HOST: {값} (Phase 1 / Step 5에서 기록)
- K8S_CLUSTER, K8S_NAMESPACE: {값} (Phase 2 / Step 3 완료 후 기록)
- 마지막 완료 Phase/Step: {Phase X / Step Y}
```

`{PROJECT_DIR}/AGENTS.md`의 `## 워크플로우 진행상황 > ### deploy`에 진행상황 정보가 있는 경우 마지막 완료 Step 이후부터 자동 재개. 
이 기록은 이후 `/npd:cicd` 스킬에서 중복 질문 없이 환경 정보를 재사용하기 위한 목적이기도 함.

## 워크플로우

### 개요

```
Phase 0: 진행 모드 선택
   ↓
Phase 1: 배포 사전 준비 (CLOUD·로컬/VM 도구·VM 접속)
   ↓
Phase 2: 배포 환경 정보 수집 (이미지 레지스트리·K8S 클러스터·리소스·실행정보 조립)
   ↓
Phase 3: 컨테이너 이미지 빌드 & 푸시
   ↓
Phase 4: 컨테이너 실행 검증
   ↓
Phase 5: Kubernetes 배포 (백킹서비스·매니페스트·Nginx Proxy)
   ↓
Phase 6: 배포 완료 보고
```

### Phase 0: 진행 모드 선택

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/deploy/phase0-deploy-mode.md` ← **필수 로드**
- **TASK**: 위 GUIDE에 따라 진행 모드(단계별 승인/자동 진행) 결정 + 자동 진행 모드 시 VM Host 사전 수집
- **EXPECTED OUTCOME**: `AGENTS.md > ### deploy > 진행 모드` 기록 + (자동 진행 시) `{VM.HOST}` 사전 결정

#### Step 1. 진행 모드 선택
단계별 승인/자동 진행 선택. 자동 진행 시 Phase 1~6 실행 중 ASK_USER 호출 자제.

#### Step 2. VM Host 사전 수집 (자동 진행 모드)
~/.ssh/config Host 후보 2개 이상이고 자동 진행 모드일 때만 사전 선택.

---

### Phase 1: 배포 사전 준비 → Agent: devops-engineer

배포에 필요한 로컬 도구와 VM 원격 도구를 자동으로 설치하고, VM 접속 정보를 수집한다.

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/deploy/deploy-pre-setup.md` ← **필수 로드**
- **TASK**: CLOUD 판단 → 로컬 도구 설치(kubectl, kubens, helm, Cloud CLI) → Cloud CLI 로그인 확인 → VM 생성 안내 → `~/.ssh/config` 파싱 → SSH 접속 테스트 → VM 원격 도구 설치(Cloud CLI, Docker, kubectl, kubens, helm, JDK)
- **EXPECTED OUTCOME**: 로컬/VM 도구 설치 완료, VM 접속 정보(`VM.HOST`, `VM.IP`, `VM.USERID`, `VM.KEY파일`) 수집, AGENTS.md `### deploy > VM_HOST` 기록

> **자동 진행 모드 동작**: Phase 1 내 모든 `<!--ASK_USER-->`를 생략하고 아래 규칙으로 자동 처리한다.
> - **Step 1 CLOUD**: AGENTS.md에서 읽기 → 없으면 에러 중단
> - **Step 3 CLI 로그인**: 로그인 명령어(`aws sts get-caller-identity` / `az account show` / `gcloud auth list`)로 자동 확인 → 미로그인이면 에러 중단
> - **Step 4 VM 준비**: `~/.ssh/config`에 Host 엔트리가 1개 이상이면 "준비 완료"로 간주 → 0개이면 에러 중단
> - **Step 5 VM 선택**: Host 후보 1개 → 자동 선택 / 2개 이상 → Phase 0 / Step 2에서 미리 수집한 값 사용
> - **Step 6 SSH 실패**: 1회 자동 재시도 → 재실패 시 에러 중단

#### Step 1. CLOUD 판단
AGENTS.md `### design > CLOUD` 값을 읽음. 없으면 사용자에게 AWS/Azure/GCP 선택 요청.

#### Step 2. 로컬 도구 자동 설치
OS 감지 후 kubectl, kubens/kubectx, helm, {CLOUD} CLI 미설치분만 자동 설치.

#### Step 3. Cloud CLI 로그인 확인
{CLOUD} CLI 로그인 상태 확인. 미로그인 시 가이드 링크 안내 + 완료 대기.

#### Step 4. VM 생성 안내
배포용 VM 준비 여부 확인. 미준비 시 {CLOUD}별 VM 생성 URL 안내 + `~/.ssh/config` 등록 안내.

#### Step 5. ~/.ssh/config 파싱
Host 엔트리 추출 → 사용자 선택 → VM.HOST/IP/USERID/KEY파일 추출 → AGENTS.md `### deploy > VM_HOST` 기록.

#### Step 6. SSH 접속 테스트
SSH 접속 검증. 실패 시 재시도 또는 건너뛰기 분기.

#### Step 7. VM 원격 도구 설치
SSH로 VM에 접속하여 Cloud CLI/Docker/kubectl/kubens/helm/JDK 미설치 도구 자동 설치.

#### Step 8. 완료 보고
로컬/VM 설치 도구 목록 + VM 접속 방법(`ssh {VM_HOST_ALIAS}`) 보고.

---

### Phase 2: 배포 환경 정보 수집

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/deploy/deploy-env-info.md` ← **필수 로드**
- **TASK**: 위 GUIDE에 따라 이미지 레지스트리·K8S 클러스터·서비스 리소스 정보 수집 후 `[실행정보]` 블록 조립
- **EXPECTED OUTCOME**: `[실행정보]` 블록 (Cloud별 4개 템플릿 중 하나) + AGENTS.md `### deploy` 진행상황 섹션 갱신

> **조건부 실행 규칙**: 시작 Phase ≤ 5인 경우만 본 Phase 수행 (Phase 6은 정보 수집 불필요)
> VM 정보(Phase 1 결과)는 시작 Phase ∈ {1, 3, 4, 5}일 때만 사용

#### Step 1. 이미지 레지스트리 정보 수집 (1차)
레지스트리 유형(Docker Hub / Cloud 레지스트리) 선택.

#### Step 2. 이미지 레지스트리 정보 수집 (2차, 유형별 분기)
선택된 유형에 따라 Org/Token, ECR Region/Account, ACR명, GCR Project/Region/Repo 수집.

#### Step 3. K8S 클러스터 자동 감지 + 선택
kubectx 기반 자동 감지·필터링·컨텍스트 전환·NAMESPACE 결정.

#### Step 4. K8S 배포 리소스 설정 (서비스별)
Step 4-1 일괄 기본값 + Step 4-2 서비스별 예외 → core/MB → millicore/Mi 변환.

#### Step 5. 실행정보 조립 + 상태 기록
Cloud별 `[실행정보]` 블록 조립 → AGENTS.md `### deploy` 갱신 (K8S_CLUSTER, K8S_NAMESPACE 추가 기록).

---

### Phase 3: 컨테이너 이미지 빌드 & 푸시 → Agent: devops-engineer

#### Step 1. VM 소스 동기화 (PREV_ACTION)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/deploy/vm-git-sync.md` ← **필수 로드**
- **모드**: 모드 A (Phase 진입 전 동기화)
- **commit message**: `"deploy: Phase 3 시작 전 소스 동기화"`
- **EXPECTED OUTCOME**: VM `~/workspace/{ROOT}`에 최신 소스 적재

#### Step 2. 백엔드·프론트엔드·AI 병렬 빌드 & 푸시 (TASK)

3개 서비스를 **서브에이전트로 병렬 실행**한다. 각 에이전트는 해당 가이드를 참조하여 Dockerfile 작성 → 이미지 빌드 → 레지스트리 푸시를 수행한다.

| 서비스 | GUIDE | 주요 산출물 |
|--------|-------|-----------|
| 백엔드 | `{NPD_PLUGIN_DIR}/resources/guides/deploy/build-image-back.md` | `deployment/container/Dockerfile-backend` |
| 프론트엔드 | `{NPD_PLUGIN_DIR}/resources/guides/deploy/build-image-front.md` | `deployment/container/Dockerfile-frontend`, `nginx.conf` |
| AI | `{NPD_PLUGIN_DIR}/resources/guides/deploy/build-image-ai.md` | `deployment/container/Dockerfile-ai` |

- **CONTEXT**: Phase 2 / Step 5에서 조립된 `[실행정보]` 블록을 각 에이전트 프롬프트에 포함
- **EXPECTED OUTCOME**: Dockerfile 생성, 이미지 빌드 성공, 이미지 푸시 성공

#### Step 3. 산출물 커밋 & 동기화 (POST_ACTION)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/deploy/vm-git-sync.md` ← **필수 로드**
- **모드**: 모드 C (산출물 커밋)
- **commit message**: `"deploy: Phase 3 산출물 (Dockerfile, build-image guide)"`
- **EXPECTED OUTCOME**: VM 산출물(Dockerfile 등) 원격 저장소 반영 + 로컬 동기화

---

### Phase 4: 컨테이너 실행 검증 → Agent: devops-engineer

#### Step 1. VM 소스 동기화 + 환경파일 전송 (PREV_ACTION)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/deploy/vm-git-sync.md` ← **필수 로드**
- **모드**: 모드 B (Phase 진입 전 동기화 + `.env` scp)
- **EXPECTED OUTCOME**: VM `~/workspace/{ROOT}`에 최신 소스 + `.env` 파일 적재 (AI 서비스 컨테이너 `--env-file` 참조용)

#### Step 2. VM 백킹서비스 배포 (선행)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-service-container.md`
- **CONTEXT**: Phase 2 / Step 5에서 조립된 `[실행정보]` 블록을 프롬프트에 포함
- **TASK**: VM에 SSH 접속하여 docker-compose로 백킹서비스(DB, Redis, MQ)를 기동하고 health check 수행. Cloud MQ 사용 시 프로비저닝 포함
- **EXPECTED OUTCOME**: 모든 백킹서비스 healthy 확인, `docs/deploy/backing-service-container-result.md` 작성

> 백킹서비스가 정상 기동된 후에야 Step 3 애플리케이션 컨테이너 실행이 가능하다.

#### Step 3. 백엔드·프론트엔드·AI 병렬 컨테이너 실행 (TASK)

3개 서비스를 **서브에이전트로 병렬 실행**한다. 각 에이전트는 해당 가이드를 참조하여 컨테이너를 실행하고 정상 동작을 확인한다.

| 서비스 | GUIDE |
|--------|-------|
| 백엔드 | `{NPD_PLUGIN_DIR}/resources/guides/deploy/run-container-back.md` |
| 프론트엔드 | `{NPD_PLUGIN_DIR}/resources/guides/deploy/run-container-front.md` |
| AI | `{NPD_PLUGIN_DIR}/resources/guides/deploy/run-container-ai.md` |

- **CONTEXT**: Phase 2 / Step 5에서 조립된 `[실행정보]` 블록을 각 에이전트 프롬프트에 포함
- **EXPECTED OUTCOME**: 백엔드·프론트엔드·AI 서비스 컨테이너 정상 실행 확인, `docs/deploy/run-container-{back,front,ai}-result.md` 작성

#### Step 4. 산출물 커밋 & 동기화 (POST_ACTION)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/deploy/vm-git-sync.md` ← **필수 로드**
- **모드**: 모드 C (산출물 커밋)
- **commit message**: `"deploy: Phase 4 산출물 (backing-service-result, run-container-result)"`
- **EXPECTED OUTCOME**: VM 산출물(*-result.md 등) 원격 저장소 반영 + 로컬 동기화

---

### Phase 5: Kubernetes 배포 → Agent: devops-engineer

#### Step 1. K8s 백킹서비스 배포 (선행)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-service-k8s.md`
- **CONTEXT**: Phase 2 / Step 5에서 조립된 `[실행정보]` 블록을 프롬프트에 포함
- **TASK**: K8s 클러스터에 kubectl/helm으로 백킹서비스(DB, Redis)를 Bitnami Helm 차트로 설치하고 health check 수행. Cloud MQ 사용 시 프로비저닝 포함
- **EXPECTED OUTCOME**: 모든 백킹서비스 healthy 확인, `docs/deploy/backing-service-k8s-result.md` 작성

> 백킹서비스가 K8s 클러스터에 정상 배포된 후에야 Step 2 애플리케이션 K8s 배포가 가능하다.

#### Step 2. K8s 매니페스트 작성 및 배포 (TASK)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/deploy/deploy-k8s-back.md`, `{NPD_PLUGIN_DIR}/resources/guides/deploy/deploy-k8s-front.md`, `{NPD_PLUGIN_DIR}/resources/guides/deploy/deploy-k8s-ai.md`
- **CONTEXT**: Phase 2 / Step 5에서 조립된 `[실행정보]` 블록을 프롬프트에 포함
- **TASK**: K8s Deployment, Service, Ingress 매니페스트를 작성하고 배포
- **EXPECTED OUTCOME**: `deploy/k8s/` 매니페스트 파일 생성, 배포 성공

#### Step 3. Nginx Web Server Proxy 설정 (POST_ACTION)

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/deploy/nginx-proxy-setup.md` ← **필수 로드**
- **TASK**: 위 GUIDE에 따라 Web Server 확인 → SSL 인증서 발급 → Frontend·API 두 server 블록 Nginx conf 작성 → 재시작 → CORS 확인
- **EXPECTED OUTCOME**: 외부 HTTPS 접근 가능 (`https://{SSL_DOMAIN}`, `https://api.{SSL_DOMAIN}`)

---

### Phase 6: 배포 완료 보고

#### Step 1. 배포 완료 보고

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

---

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |
| 2 | `Agent: {agent-name}`이 명시된 Step은 메인 에이전트가 직접 수행 금지. 반드시 프롬프트 조립 규칙에 따라 서브에이전트 호출 |
| 3 | Phase 2 / Step 5 (실행정보 조립) 결과 `[실행정보]` 블록은 Phase 3 ~ Phase 5의 모든 Agent 호출 시 프롬프트의 동적 영역에 텍스트로 포함 |
| 4 | 외부 가이드(`{NPD_PLUGIN_DIR}/resources/guides/deploy/*.md`)가 명시된 Step은 해당 가이드를 **반드시 Read로 로드한 뒤** 절차를 수행할 것. SKILL.md 본문의 요약만 보고 직접 수행하면 스킬 미준수로 간주 |

## 완료 조건

- [ ] Phase 0 / Step 1~2 완료 (진행 모드 결정·자동 진행 시 VM Host 사전 수집)
- [ ] Phase 1 / Step 1~8 완료 (CLOUD 판단·로컬/VM 도구 설치·VM 접속 정보 수집)
- [ ] Phase 2 / Step 1~5 완료 (이미지 레지스트리·K8s 클러스터·리소스 정보 수집·`[실행정보]` 조립·AGENTS.md 상태 기록)
- [ ] Phase 3 / Step 1~3 완료 (VM 소스 동기화·백엔드/프론트/AI Dockerfile 생성·이미지 빌드·푸시·산출물 커밋)
- [ ] Phase 4 / Step 1~4 완료 (VM 백킹서비스 healthy·컨테이너 실행 검증, `docs/deploy/backing-service-container-result.md`, `docs/deploy/run-container-{back,front,ai}-result.md` 생성)
- [ ] Phase 5 / Step 1~3 완료 (K8s 백킹서비스·매니페스트 배포·Nginx Proxy(HTTPS) 설정, `docs/deploy/backing-service-k8s-result.md` 생성)
- [ ] Phase 6 / Step 1: 배포 완료 보고 출력
- [ ] 검증 프로토콜을 통과함
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (Dockerfile, K8s 매니페스트, *-result.md)
2. 산출물 내용 품질 검증 (컨테이너 빌드 성공, 컨테이너 실행 정상, K8s 배포 정상)
3. 이전 워크플로우(`/npd:develop`) 산출물과의 일관성 확인
4. Phase 5 / Step 3 Nginx Proxy → 외부 HTTPS 접근 가능 확인 (`curl -I https://{SSL_DOMAIN}`)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.
