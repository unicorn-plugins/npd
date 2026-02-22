---
name: develop
description: 개발 단계 AI 협업 — 백엔드·프론트엔드·AI엔지니어·QA가 협업하여 코드 생성 및 테스트 수행
type: orchestrator
user-invocable: true
allowed-tools: Read, Write, Bash, Task
---

# Develop

[NPD Develop 활성화]

## 목표

백엔드개발자·프론트엔드개발자·AI엔지니어·QA가 협업하여
빌드 환경 구성 → 백킹서비스 설정 → 백엔드 → 프론트엔드 → AI기능 → 테스트 순서로 개발을 수행함.

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

## Step 0. 진행 모드 선택

개발 워크플로우 시작 전, 각 단계별 승인 여부를 선택합니다.

<!--ASK_USER-->
{"title":"진행 모드 선택","questions":[
  {"question":"각 단계 완료 후 승인을 받고 진행할까요, 자동으로 진행할까요?","type":"radio","options":["단계별 승인","자동 진행"]}
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

## 워크플로우

### Step 1. Gradle Wrapper 생성 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/develop/gradle-wrapper.md` 참조
- **TASK**: Java 버전을 확인하고 호환되는 Gradle Wrapper를 자동 생성
- **EXPECTED OUTCOME**: `gradlew`, `gradlew.bat`, `gradle/wrapper/` 생성

### Step 2. 공통 모듈 개발 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/develop/dev-backend.md` 참조
- **TASK**: 모노레포 구조에 맞게 백엔드 공통 모듈(예외처리, 응답 포맷, 공통 설정)을 개발. settings.gradle, 루트 build.gradle, 서비스별 build.gradle 작성 포함
- **EXPECTED OUTCOME**: `backend/src/main/java/.../common/` 공통 모듈 코드 생성

### Step 3. 데이터베이스 설정 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/develop/database-plan.md`, `resources/guides/develop/database-install.md` 참조
- **TASK**: 데이터베이스 설치 계획서를 작성하고, 데이터 설계서 기반으로 JPA 엔티티와 레포지토리를 구현하며 데이터베이스 설정을 완료
- **EXPECTED OUTCOME**: DB 설치 계획서, 엔티티 클래스, 레포지토리 인터페이스, application.yml DB 설정 생성

### Step 4. MQ 설정 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/develop/mq-plan.md`, `resources/guides/develop/mq-install.md` 참조
- **TASK**: 외부시퀀스설계서에서 비동기 통신이 필요한 곳을 파악하고, MQ 설치 계획서를 작성한 후 MQ를 설치
- **EXPECTED OUTCOME**: MQ 설치 계획서, MQ 설치 결과서, MQ 연결 문자열 파일 생성
- **SKIP 조건**: 외부시퀀스설계서에 비동기 통신(MQ)이 없으면 이 단계를 건너뜀

### Step 5. 백엔드 API 개발 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/develop/dev-backend.md`, `resources/guides/develop/dev-backend-testcode.md` 참조
- **TASK**: API 설계서 기반으로 컨트롤러·서비스·레포지토리 레이어를 구현하고 단위 테스트 작성. SecurityConfig, JWT 인증처리, SwaggerConfig 클래스 포함
- **EXPECTED OUTCOME**: API 엔드포인트 구현 코드 및 단위 테스트 코드 생성

### Step 6. 서비스 실행 프로파일 작성 → Agent: backend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/develop/make-run-profile.md` 참조
- **TASK**: 각 서비스별 IntelliJ 실행 프로파일(.run.xml)을 작성하고 설정 Manifest와의 일치 여부를 검증
- **EXPECTED OUTCOME**: `{service-name}/.run/{service-name}.run.xml` 생성

### Step 7. 프론트엔드 개발 → Agent: frontend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/develop/dev-frontend.md` 참조
- **TASK**: UI/UX 설계서 기반으로 프론트엔드 컴포넌트를 구현하고 백엔드 API와 연동. 기술스택 결정 → 초기 설정 → 기반 시스템 → API 연동 → 공통 컴포넌트 → 페이지별 구현 순서로 진행
- **EXPECTED OUTCOME**: 프론트엔드 컴포넌트 코드 및 API 연동 코드 생성

### Step 8. AI 기능 구현 → Agent: ai-engineer (`/oh-my-claudecode:ralph` 활용)

- **TASK**: AI 연동 설계서 기반으로 AI API 연동 코드와 프롬프트를 구현
- **EXPECTED OUTCOME**: `src/ai/` AI 연동 코드 생성

### Step 9. 테스트 및 버그 수정 → Agent: qa-engineer (`/oh-my-claudecode:ultraqa` 활용)

- **GUIDE**: `resources/guides/develop/test-backend.md` 참조
- **TASK**: 구현된 백엔드 API와 프론트엔드 UI를 테스트하고 버그를 리포트. 실행 프로파일과 설정 Manifest 일치 여부 사전 검증 후 테스트 수행
- **EXPECTED OUTCOME**: `test-report.md` 생성 (테스트 통과 여부 및 버그 목록 포함)

### Step 10. 개발 완료 보고

```
## 개발 완료

### 구현된 기능
- Gradle Wrapper: {버전}
- 백엔드 API: {엔드포인트 수}개
- 프론트엔드 컴포넌트: {컴포넌트 수}개
- AI 기능: {기능 수}개
- 테스트 통과율: {비율}
- 실행 프로파일: {서비스 수}개 서비스

### 백킹서비스 설정
- 데이터베이스: {DB 종류 및 수}
- 캐시: {캐시 종류}
- MQ: {MQ 종류} (해당 시)

### 다음 단계
`/npd:deploy` 로 배포를 시작하세요.
```

## 완료 조건

- [ ] 모든 워크플로우 단계가 정상 완료됨
- [ ] Gradle Wrapper가 생성되고 검증됨
- [ ] 백엔드 API 구현 및 단위 테스트 코드가 생성됨
- [ ] 서비스 실행 프로파일이 작성되고 설정 Manifest와 일치함
- [ ] 프론트엔드 컴포넌트가 구현됨
- [ ] AI 기능이 구현됨
- [ ] QA 테스트 리포트(`docs/test/test-report.md`)가 생성됨
- [ ] 검증 프로토콜을 통과함
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (Gradle Wrapper, 백엔드 코드, 프론트엔드 코드, AI 코드, 실행 프로파일, 테스트 리포트)
2. 산출물 내용 품질 검증 (단위 테스트 통과, API 응답 정상, 빌드 성공)
3. 이전 Phase 산출물과의 일관성 확인 (설계 산출물 → 구현 코드 연계)
4. 설정 일관성 검증 (application.yml 환경변수 ↔ 실행 프로파일 ↔ 백킹서비스 설치 결과)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.
