---
name: develop
description: 개발 단계 AI 협업 — 백엔드·프론트엔드·AI엔지니어·QA가 API 계약 기반 병렬 개발 수행
type: orchestrator
user-invocable: true
allowed-tools: Read, Write, Bash, Task
---

# Develop

[NPD Develop 활성화]

## 목표

백엔드개발자·프론트엔드개발자·AI엔지니어·QA가 협업하여
API 계약(OpenAPI 명세) 기반 병렬 개발 전략으로 개발을 수행함.

- **Phase 1**: 환경 구성 (백엔드/프론트엔드/AI/백킹서비스 병렬 초기화)
- **Phase 2**: API 계약 기반 병렬 개발 (BE API + FE Mock + AI 서비스 동시 진행)
- **Phase 3**: 통합 연동 (Mock→실제 API 전환, BE↔AI 연동)
- **Phase 4**: 종합 테스트 및 QA

## 선행 조건

- `/npd:design` 완료 (`docs/design/` 산출물 존재)

## 에이전트 호출 규칙

| 에이전트 | FQN |
|----------|-----|
| backend-developer | `npd:backend-developer:backend-developer` |
| frontend-developer | `npd:frontend-developer:frontend-developer` |
| ai-engineer | `npd:ai-engineer:ai-engineer` |
| qa-engineer | `npd:qa-engineer:qa-engineer` |

### 프롬프트 조립

1. `agents/{agent-name}/`에서 3파일 로드 (AGENT.md + agentcard.yaml + tools.yaml)
2. `gateway/runtime-mapping.yaml` 참조하여 구체화:
   - **모델 구체화**: agentcard.yaml의 `tier` → `tier_mapping`에서 모델 결정
   - **툴 구체화**: tools.yaml의 추상 도구 → `tool_mapping`에서 실제 도구 결정
   - **금지액션 구체화**: agentcard.yaml의 `forbidden_actions` → `action_mapping`에서 제외할 실제 도구 결정
   - **최종 도구** = (구체화된 도구) - (제외 도구)
3. 프롬프트 조립: 공통 정적(runtime-mapping) → 에이전트별 정적(3파일) → 인격(persona) → 동적(작업 지시)
4. `Task(subagent_type=FQN, model=구체화된 모델, prompt=조립된 프롬프트)` 호출

## 리소스 경로 규칙

본 스킬의 가이드·참조·샘플·도구 파일은 NPD 플러그인 디렉토리에 위치합니다.
프로젝트 작업 디렉토리와 플러그인 디렉토리가 다르므로, 아래 변수를 사용합니다.

**`{PLUGIN_DIR}`**: NPD 플러그인 루트 디렉토리의 절대 경로

### 경로 해석 규칙

오케스트레이터는 실행 시작 시 다음 순서로 `{PLUGIN_DIR}`를 결정합니다:

1. `~/.claude/plugins/cache/npd/npd/` 하위에서 최신 버전 디렉토리를 탐색
2. 해당 디렉토리의 절대 경로를 `{PLUGIN_DIR}`에 바인딩
3. 이후 모든 `{PLUGIN_DIR}/resources/...` 경로를 절대 경로로 치환하여 파일을 읽음

### 에이전트에 전달 시

1. 가이드 파일(`{PLUGIN_DIR}/resources/guides/develop/...`)은 Read로 읽어 프롬프트에 포함
2. 가이드 내에서 참조하는 플러그인 리소스(`{PLUGIN_DIR}/resources/references/...`, `{PLUGIN_DIR}/resources/standards/...` 등)는 `{PLUGIN_DIR}`를 절대 경로로 치환하여 에이전트에게 전달하여 에이전트가 직접 읽을 수 있도록 함

## 공통 참조 리소스

모든 Step에서 아래 표준을 준수:

- **개발주석표준**: `{PLUGIN_DIR}/resources/standards/standard_comment.md`
- **테스트코드표준**: `{PLUGIN_DIR}/resources/standards/standard_testcode.md`
- **패키지구조표준**: `{PLUGIN_DIR}/resources/standards/standard_package_structure.md`
- **병렬 처리 전략**: `{PLUGIN_DIR}/resources/guides/design/common-principles.md`

## Step 0. 진행 모드 선택

개발 워크플로우 시작 전, 진행 모드와 백킹서비스 환경을 선택합니다.

<!--ASK_USER-->
{"title":"진행 모드 선택","questions":[
  {"question":"각 단계 완료 후 승인을 받고 진행할까요, 자동으로 진행할까요?","type":"radio","options":["단계별 승인","자동 진행"]},
  {"question":"백킹서비스 환경을 선택해 주세요.","type":"radio","options":["docker-compose (로컬, 권장)","minikube","K8s 클러스터"]}
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

- **자동 진행** 선택 시 → 승인 없이 연속 실행

---

## 워크플로우

### Step 1. 종합 개발 계획 수립 → Agent: backend-developer + frontend-developer + ai-engineer (병렬) + architect (리뷰)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/dev-plan.md`
- **TASK**: 설계 산출물 분석 → 3개 에이전트가 담당 영역 분담 작성 → architect 리뷰 → 종합 개발 계획서 통합
  - **backend-developer**: 마이크로서비스 목록, 서비스 간 의존관계, 백킹서비스 요구사항, 백엔드 개발 순서
  - **frontend-developer**: 프론트엔드 범위, 페이지 목록, API 매핑, 프론트엔드 개발 순서
  - **ai-engineer**: AI 서비스 존재 여부·범위, AI 엔드포인트 목록, AI 개발 순서
  - **architect (리뷰)**: 3개 영역 통합, Phase별 작업 할당 최적화, 의존관계 검증
- **EXPECTED OUTCOME**: `docs/develop/dev-plan.md`
- **SKIP 조건 결정**: AI 서비스 설계서(`docs/design/ai-service-design.md`) 미존재 또는 "AI 불필요" 결론 시, 이후 AI 관련 Step(2-4, 3-3, 4-2)을 SKIP으로 표시

### Step 2. Phase 1 — 환경 구성

#### Step 2-1. 백엔드 환경 구성 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backend-env-setup.md`
- **참조**: `{PLUGIN_DIR}/resources/references/java-build-gradle-standard.md`, `{PLUGIN_DIR}/resources/references/java-config-manifest-standard.md`
- **TASK**: Gradle Wrapper 생성 + 멀티모듈 build.gradle 구성 + 공통 모듈 개발
- **EXPECTED OUTCOME**: `gradlew`, `settings.gradle`, `build.gradle`(루트/서비스별), `application.yml`(서비스별), common 모듈 코드
- **주의**: application.yml의 환경변수는 placeholder만 작성 (실제 값은 Step 2-2의 .env.example에서 정의)

#### Step 2-2. 백킹서비스 + Mock 서버 로컬 구성 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backing-service-setup.md`
- **TASK**: 데이터설계서 기반 프로젝트 루트 단일 `docker-compose.yml` 작성 → DB/Cache/MQ + Prism Mock 서버 구성
- **EXPECTED OUTCOME**: `./docker-compose.yml`, `.env.example`, `docs/develop/backing-service-result.md`
- **docker-compose 서비스 구성**:
  - 기본 서비스 (항상 기동): DB, Cache, MQ(설계서 명시 시만)
  - mock 프로파일: Prism Mock 서버 (`docker compose --profile mock up`)
  - ai 프로파일: AI 서비스 컨테이너 (`docker compose --profile ai up`, AI 서비스 존재 시만)
- **사용자 선택**: Step 0에서 선택한 백킹서비스 환경에 따라 분기

#### Step 2-3. 프론트엔드 프로젝트 초기화 → Agent: frontend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/frontend-env-setup.md`
- **TASK**: 기술스택 결정 → 프로젝트 생성 → 기반 시스템(스타일/라우팅/상태관리) 구축 → Prism Mock 서버 연동 준비
- **EXPECTED OUTCOME**: `frontend/` 프로젝트 골격, `npm run dev` 실행 확인

#### Step 2-4. AI 서비스 프로젝트 초기화 → Agent: ai-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/ai-service-env-setup.md`
- **TASK**: Python/FastAPI 프로젝트 생성 → 의존성 설치 → 기본 구조 설정 → docker-compose ai 프로파일에 등록
- **EXPECTED OUTCOME**: `ai-service/` 프로젝트 골격, uvicorn 실행 확인
- **SKIP 조건**: Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **Step 2-1 ~ 2-4는 병렬 실행**: 4개 에이전트가 동시에 작업. Step 2-1과 2-2의 환경변수 정합성은 placeholder 방식으로 해결 (각자 독립 작성, 값은 .env.example에서 통일)

#### Step 2-5. 실행 프로파일 작성 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/run-profile.md`
- **TASK**: 백킹서비스 연결 정보(Step 2-2) + application.yml(Step 2-1) 기반 실행 프로파일 작성
- **EXPECTED OUTCOME**: `{service-name}/.run/{service-name}.run.xml` (서비스별)
- **선행 조건**: Step 2-1, Step 2-2 완료 필수 (Phase 2 진입 전 게이트)

### Step 3. Phase 2 — API 계약 기반 병렬 개발

#### Step 3-1. 백엔드 API 구현 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backend-api-dev.md`
- **참조**: `{PLUGIN_DIR}/resources/references/java-security-jwt-swagger.md`, `{PLUGIN_DIR}/resources/references/java-test-guide.md`
- **TASK**: API 설계서 기반 컨트롤러·서비스·레포지토리 구현 + 단위 테스트
- **EXPECTED OUTCOME**: 서비스별 API 코드 + 테스트 코드
- **병렬**: 서비스 간 의존성 분석 후 독립 서비스는 병렬 구현

#### Step 3-2. Prism Mock API 기반 프론트엔드 개발 → Agent: frontend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/frontend-dev.md`
- **TASK**: docker-compose의 Prism Mock 서버 활용 → 페이지별 구현
- **EXPECTED OUTCOME**: 프론트엔드 컴포넌트 + Prism Mock 연동 코드
- **Prism 실행**: `docker compose --profile mock up` (Step 2-2에서 구성)

#### Step 3-3. AI 서비스 구현 → Agent: ai-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/ai-service-dev.md`
- **TASK**: AI 서비스 설계서 기반 엔드포인트 구현, 프롬프트 작성, LLM 연동
- **EXPECTED OUTCOME**: AI 서비스 API 코드
- **SKIP 조건**: Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **Step 3-1 ~ 3-3은 병렬 실행**: 백엔드는 실제 API 구현, 프론트엔드는 Prism Mock으로 독립 개발, AI는 별도 서비스로 독립 개발

### Step 4. Phase 3 — 통합 연동

#### Step 4-1. 프론트엔드 실제 API 연동 → Agent: frontend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/frontend-integration.md`
- **TASK**: Prism Mock → 실제 백엔드 API 전환, E2E 동작 확인
- **EXPECTED OUTCOME**: 실제 API 연동 완료 코드

#### Step 4-2. 백엔드 ↔ AI 서비스 연동 → Agent: backend-developer + ai-engineer

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backend-ai-integration.md`
- **TASK**: 백엔드에서 AI 서비스 호출 코드 구현, Circuit Breaker/Fallback 설정
- **EXPECTED OUTCOME**: 연동 코드 + 통합 테스트
- **SKIP 조건**: Step 1에서 AI SKIP으로 결정된 경우 건너뜀

> **Step 4-1, 4-2는 병렬 실행 가능** (단, 4-1은 Step 3-1 완료 필요, 4-2는 Step 3-1 + 3-3 완료 필요)

### Step 5. Phase 4 — 테스트 및 QA → Agent: qa-engineer (`/oh-my-claudecode:ultraqa` 활용)

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/test-qa.md`
- **TASK**: API 테스트(curl), 프론트엔드 테스트, 통합 시나리오 테스트, 버그 리포트
- **EXPECTED OUTCOME**: `docs/develop/test-report.md`

### Step 6. 개발 완료 보고

```
## 개발 완료

### 구현된 기능
- 백엔드 API: {엔드포인트 수}개 ({서비스 수}개 서비스)
- 프론트엔드 컴포넌트: {컴포넌트 수}개 ({페이지 수}개 페이지)
- AI 기능: {기능 수}개 (해당 시)
- 테스트 통과율: {비율}

### 백킹서비스 설정
- 데이터베이스: {DB 종류 및 수}
- 캐시: {캐시 종류}
- MQ: {MQ 종류} (해당 시)
- Mock 서버: Prism (docker-compose --profile mock)

### 다음 단계
`/npd:deploy` 로 배포를 시작하세요.
```

---

## 완료 조건

- [ ] 종합 개발 계획서(`docs/develop/dev-plan.md`)가 생성됨
- [ ] 백엔드 환경 구성 완료 (Gradle Wrapper, build.gradle, common 모듈)
- [ ] 백킹서비스 로컬 구성 완료 (docker-compose.yml, .env.example)
- [ ] 프론트엔드 프로젝트 초기화 완료
- [ ] AI 서비스 프로젝트 초기화 완료 (해당 시)
- [ ] 실행 프로파일 작성 완료
- [ ] 백엔드 API 구현 및 단위 테스트 코드 생성됨
- [ ] 프론트엔드 Prism Mock 기반 구현 완료
- [ ] AI 서비스 구현 완료 (해당 시)
- [ ] 프론트엔드 실제 API 연동 완료
- [ ] 백엔드-AI 연동 완료 (해당 시)
- [ ] QA 테스트 리포트(`docs/develop/test-report.md`)가 생성됨
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (개발 계획서, 백엔드 코드, 프론트엔드 코드, AI 코드, 실행 프로파일, 테스트 리포트)
2. 산출물 내용 품질 검증 (단위 테스트 통과, API 응답 정상, 빌드 성공)
3. 이전 Phase 산출물과의 일관성 확인 (설계 산출물 → 구현 코드 연계)
4. 설정 일관성 검증 (application.yml 환경변수 ↔ 실행 프로파일 ↔ .env.example ↔ docker-compose.yml)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.
