# Phase 0 사전 설정·진행 모드 가이드

> 본 가이드는 `skills/develop/SKILL.md > Phase 0`에서 호출됨.
> 6개 Step의 사용자 입력 수집·환경변수 검증·진행 모드 결정 절차를 정의.

## 입력

- `docs/design/high-level-architecture.md` (Step 1, Step 2, Step 4 판별 소스)
- `docs/design/ai-service-design.md` (Step 4 존재 여부 판별)
- 프로젝트 루트 `.env`, `.env.example` (Step 2~4 크리덴셜 적재 위치)

## 공통 원칙

- **자동 진행 보장**: Phase 1 이후 실행 중 사용자 입력이 필요한 항목을 본 Phase에서 사전에 모두 수집
- **'나중에 설정' 옵션**: 크리덴셜 미발급 시 `.env.example`에 키만 빈 값으로 추가하고 후속 Step에서 코드 구현만 진행
- **저장 위치 분리**:
  - 크리덴셜·시크릿 → `{PROJECT_DIR}/.env` (Git 미커밋)
  - 키 템플릿 → `{PROJECT_DIR}/.env.example` (Git 커밋)
  - 진행 모드·개발 범위·지원 변수 → `{PROJECT_DIR}/AGENTS.md > ## 워크플로우 진행상황 > ### develop`

---

## Step 1. 개발 범위 결정

`docs/design/high-level-architecture.md`의 **"14. 구현 로드맵 > 14.1 개발 단계"** 섹션을 읽어 프로젝트별 개발 단계를 추출.

1. 해당 섹션의 테이블(단계, 기간, 주요 산출물, 마일스톤)을 파싱
2. 추출된 단계 목록을 사용자에게 표시하고 이번에 구현할 범위를 선택받음

<!--ASK_USER-->
{"title":"개발 범위 선택","questions":[
  {"question":"HighLevel 아키텍처 정의서(14.1 개발 단계)에서 이번에 구현할 단계를 선택해 주세요.\n\n{추출된 Phase 테이블 표시}\n\n(복수 선택 가능)","type":"checkbox","options":["{Phase 1: 주요산출물 — 마일스톤}","{Phase 2: 주요산출물 — 마일스톤}","{Phase N: ...}"]}
]}
<!--/ASK_USER-->

> **범위 결정 효과**: 선택된 Phase의 **주요 산출물·마일스톤**이 이후 모든 Step의 개발 범위가 됨.
> - Phase 1 / Step 1 (AI 개발 키트 컴파일)은 선택된 Phase 범위 내의 기능만 계획에 포함
> - Phase 1 ~ Phase 4의 각 작업도 선택 범위에 해당하는 기능만 구현
> - 선택하지 않은 Phase의 기능은 모든 Step에서 제외

**저장**: 선택 결과를 `AGENTS.md > ### develop > 개발 범위`에 기록.

---

## Step 2. OAuth2 크리덴셜 확인 (조건부)

1. `docs/design/high-level-architecture.md`의 `보안 요구사항 > 인증/인가` 항목을 읽음
2. 인증 방식을 판별:
   - `JWT`, `토큰 기반`, `자체 인증` → **JWT 인증** → 이 Step 건너뜀
   - `OAuth2`, `소셜 로그인`, `Google`, `카카오`, `네이버`, `OIDC`, `Federated` → **OAuth2 인증** → 아래 진행
   - `JWT` + `OAuth2/소셜` 모두 언급 → **하이브리드** → 아래 진행
3. OAuth2/하이브리드인 경우, `{PROJECT_DIR}/.env` 파일에 해당 Provider의 크리덴셜이 이미 설정되어 있는지 확인
4. 크리덴셜이 없으면 사용자에게 요청:

<!--ASK_USER-->
{"title":"OAuth2 소셜 로그인 크리덴셜 요청","questions":[
  {"question":"설계서에 OAuth2 소셜 로그인({식별된 Provider 목록})이 정의되어 있습니다.\n\n통합 테스트를 위해 각 Provider의 **Client ID**와 **Client Secret**이 필요합니다.\n아직 발급받지 않으셨다면, 아래 가이드를 참조하여 등록해 주세요:\n\nProvider별 앱 등록 가이드: {NPD_PLUGIN_DIR}/resources/guides/develop/oauth-guide.md\n\n{Provider별 필요 환경변수 목록 표시}\n\n크리덴셜을 입력해 주세요. (아직 미발급이면 '나중에 설정'을 선택하세요)","type":"text"}
]}
<!--/ASK_USER-->

5. 사용자가 크리덴셜을 제공하면 `.env` 파일에 반영
6. '나중에 설정'을 선택한 경우: `.env.example`에 해당 환경변수 키를 빈 값으로 추가

> **참조 문서**: `{NPD_PLUGIN_DIR}/resources/guides/develop/oauth-guide.md` — GitHub/Google/Kakao 앱 등록 절차, 필요 환경변수, Redirect URI 패턴, Spring Boot + 프론트엔드(React/Vue/Flutter) 구현 전체 패턴

---

## Step 3. Gemini API Key 확인

1. `{PROJECT_DIR}/.env` 파일에 `GEMINI_API_KEY`가 이미 설정되어 있는지 확인
2. 설정되어 있지 않으면 사용자에게 요청:

<!--ASK_USER-->
{"title":"Gemini API Key 요청 (이미지 생성용)","questions":[
  {"question":"프론트엔드 개발 시 필요한 이미지(아이콘, 일러스트, 배너 등)를 Nano Banana(Gemini) 도구로 생성합니다.\n\nGemini API Key를 입력해 주세요.\n(Google AI Studio에서 발급: https://aistudio.google.com/apikey)\n\n아직 미발급이면 '나중에 설정'을 선택하세요.","type":"text"}
]}
<!--/ASK_USER-->

3. 사용자가 API Key를 제공하면 `.env` 파일에 `GEMINI_API_KEY={입력값}`을 추가
4. `.env.example`에 `GEMINI_API_KEY=` 항목을 추가 (이미 있으면 생략)

---

## Step 4. AI 서비스 크리덴셜 확인 (조건부)

1. `docs/design/ai-service-design.md`의 존재 여부를 확인
2. 미존재 시 → AI 서비스 없음 → 이 Step 건너뜀
3. 존재 시 다음을 식별:
   - LLM 제공자 및 모델명 (예: OpenAI/gpt-4o, Anthropic/claude-3-5-sonnet 등)
   - 웹검색 Tool 사용 여부 (Tavily 등)
   - RAG 사용 여부 및 벡터 DB 종류 (ChromaDB, Qdrant 등)
   - LangSmith 모니터링 사용 여부
4. `{PROJECT_DIR}/.env` 파일에 해당 키가 이미 설정되어 있는지 확인
5. 누락된 크리덴셜이 있으면 사용자에게 요청:

<!--ASK_USER-->
{"title":"AI 서비스 크리덴셜 요청","questions":[
  {"question":"설계서에 다음 AI 서비스 연동이 정의되어 있습니다:\n\n{식별된 LLM 제공자/모델, Tool, RAG 등 목록}\n\n아래 크리덴셜을 입력해 주세요 (미발급 항목은 비워두면 됩니다):\n\n**필수:**\n- {LLM 제공자} API Key (예: OPENAI_API_KEY)\n\n**선택 (해당 시):**\n- Tavily API Key (웹검색 Tool 사용 시)\n- LangSmith API Key (LLM 호출 모니터링)\n- Vector DB 접속 정보 (RAG 사용 시)\n\n크리덴셜을 입력하거나 '나중에 설정'을 선택하세요.","type":"text"}
]}
<!--/ASK_USER-->

6. 사용자가 크리덴셜을 제공하면 `.env` 파일에 반영
7. '나중에 설정'을 선택한 경우: `.env.example`에 해당 환경변수 키를 빈 값으로 추가

---

## Step 5. 테스트 모드 선택

<!--ASK_USER-->
{"title":"테스트 모드 선택","questions":[
  {"question":"브라우저 테스트(Phase 4)를 어떻게 진행할까요?","type":"radio","options":["자동 테스트 (AI가 Playwright Test Suite로 자동 수행)","수동 테스트 (사람이 브라우저에서 직접 테스트, AI가 수정 지원)"]}
]}
<!--/ASK_USER-->

**저장**: 선택 결과(`AUTO` 또는 `MANUAL`)를 `AGENTS.md > ### develop > 지원 변수 > TEST_MODE`에 기록.

---

## Step 6. 진행 모드 선택

<!--ASK_USER-->
{"title":"진행 모드 선택","questions":[
  {"question":"각 단계 완료 후 승인을 받고 진행할까요, 자동으로 진행할까요?","type":"radio","options":["단계별 승인","자동 진행"]}
]}
<!--/ASK_USER-->

- **단계별 승인** 선택 시 → 각 스텝 완료 후 아래 ASK_USER로 승인 요청을 표시하고 응답에 따라 분기:
  - **승인** → 다음 스텝 진행
  - **재작업 요청** → 사용자 피드백을 받아 현재 스텝 재수행
  - **중단** → 현재까지 산출물 보존 후 스킬 종료
- **자동 진행** 선택 시 → 승인 없이 연속 실행

승인 요청 ASK_USER 형식:

<!--ASK_USER-->
{"title":"단계 승인","questions":[
  {"question":"{완료된 스텝명} 단계가 완료되었습니다. 결과 파일({생성된 파일 경로})을 검토하고 {다음 스텝명} 단계로 계속 진행할 지 승인해 주십시오.","type":"radio","options":["승인","재작업 요청","중단"]}
]}
<!--/ASK_USER-->

**저장**: 선택 결과를 `AGENTS.md > ### develop > 진행 모드`에 기록.

---

## 산출물

- `AGENTS.md > ## 워크플로우 진행상황 > ### develop` 섹션:
  - `진행 모드: {단계별 승인|자동 진행}`
  - `개발 범위: {선택된 Phase 목록}`
  - `지원 변수 > TEST_MODE: {AUTO|MANUAL}`
- `{PROJECT_DIR}/.env`: 사용자가 직접 제공한 크리덴셜 (OAuth2/Gemini/AI LLM)
- `{PROJECT_DIR}/.env.example`: 누락된 크리덴셜의 키 등록 (빈 값)
