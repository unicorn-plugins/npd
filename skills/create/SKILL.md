---
name: create
description: 새 프로젝트 생성 — 프로젝트 디렉토리 초기화, AGENTS.md 생성, GitHub 레포 자동 생성
type: orchestrator
user-invocable: true
---

# Create

[NPD Create 활성화]

## 목표

사용자로부터 MVP 비즈니스 도메인과 프로젝트 디렉토리를 입력받아
프로젝트 디렉토리를 초기화하고, MVP 비즈니스 도메인에 기반하여  
프로젝트에 도메인 컨텍스트 파일(`.npd/domain-context.yaml`)을 생성하며, GitHub 레포를 자동 생성함.
이후 단계(plan/design/develop)에서는 기존 `domain-expert` 에이전트가 이 컨텍스트 파일을 참조하여 도메인 특화 자문을 수행함.

## 활성화 조건

사용자가 `/npd:create` 호출 시 또는 "새 프로젝트 생성", "프로젝트 만들어줘" 키워드 감지 시.

## 작업 환경 변수 로드
AGENTS.md 파일에서 `## 환경변수` 섹션의 환경변수 로딩.
로딩 실패 시 사용자에게 `/npd:create`을 먼저 수행하라고 안내하고 종료.

## 진행상황 업데이트 및 재개
`{PROJECT_DIR}/AGENTS.md`에 각 Phase 완료 시 저장. 최종 완료 시 `Done`으로 표기.

```md
## 워크플로우 진행상황
- {skill-name}: Phase3
```

진행상황 정보가 있는 경우 마지막 완료 단계 이후부터 자동 재개.

## 워크플로우

### Phase 1. MVP 비즈니스 도메인 입력

가장 먼저 MVP 비즈니스 도메인을 입력받습니다.

<!--ASK_USER-->
{"title":"MVP 비즈니스 도메인","questions":[
  {"question":"만들고자 하는 서비스의 MVP 비즈니스 도메인을 구체적으로 입력해주세요.<br>업종을 입력하시면 됩니다.(예: 온라인쇼핑몰, 건강관리, 온라인교육, 공공행정서비스)","type":"text"}
]}
<!--/ASK_USER-->

### Phase 2. 프로젝트 디렉토리 입력

MVP 비즈니스 도메인 기반으로 적절한 프로젝트 디렉토리명을 영문 kebab-case로 추천합니다.

예시:
- "온라인쇼핑몰" → `~/workspace/online-shopping`
- "중고 도서 거래" → `~/workspace/used-book-market`

<!--ASK_USER-->
{"title":"프로젝트 디렉토리","questions":[
  {"question":"프로젝트 디렉토리를 입력해주세요.","description":"비즈니스 도메인에 따른 추천 디렉토리: ~/workspace/{추천명}\n기본값: ~/workspace/{추천명}","type":"text"}
]}
<!--/ASK_USER-->

- 사용자가 입력하지 않으면 추천 디렉토리를 기본값으로 사용
- 이미 존재하는 디렉토리인 경우 사용자에게 확인 후 진행

### Phase 3. 프로젝트 디렉토리 생성

프로젝트 디렉토리와 기본 파일만 생성합니다.
하위 구조는 이후 단계에서 기술스택이 결정된 후 생성합니다.

**프로젝트 디렉토리 구조:**
```
{프로젝트 디렉토리}/
├── .gitignore
└── AGENTS.md
```

**.gitignore 기본 내용** (Spring Boot, Node.js, Python 공통):
```gitignore
# Java / Spring Boot
*.class
*.jar
*.war
build/
!gradle/wrapper/gradle-wrapper.jar
.gradle/
target/

# Node.js
node_modules/
dist/
.next/

# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/

# IDE
.idea/
.vscode/
*.iml
*.swp

# OS
.DS_Store
Thumbs.db

# Env
.env

# Others
.dmap/
.omc/
.temp/
```

### Phase 4. AGENTS.md, CLAUDE.md 생성

#### NPD 플러그인 디렉토리 경로 설정
`{프로젝트 디렉토리}/AGENTS.md` 파일에 `{NPD_PLUGIN_DIR}` 변수가 설정되어 있는지 확인함.
미설정 시 아래 수행 
사용자에게 NPD 플러그인 디렉토리 경로를 입력받아 생성하는 프로젝트 디렉토리의 AGENTS.md의 `{NPD_PLUGIN_DIR}` 변수에 설정합니다. 
<!--ASK_USER-->
{"title":"NPD 플러그인 디렉토리","questions":[
  {"question":"NPD 플러그인 디렉토리 경로를 입력해주세요.(~/path1/path2 형식 사용)","type":"text"}
]}
<!--/ASK_USER-->

#### 프로젝트 디렉토리에 AGENTS.md를 생성합니다.
- NPD 플러그인의 `agents/*/agentcard.yaml`을 읽어 멤버 정보를 구성합니다.
- '## MVP > 비즈니스 도메인'을 기록합니다.  

**AGENTS.md 구조:**

````markdown
# 팀 소개

## 목표
{MVP 주제 정의 단계에서 정의}

## MVP
- 비즈니스 도메인: {MVP 비즈니스 도메인}
- MVP 주제: {MVP 주제 정의 단계에서 정의}

## 팀 행동원칙
- 'M'사상을 믿고 실천한다. : Value-Oriented, Interactive, Iterative
- 'M'사상 실천을 위한 마인드셋을 가진다
  - Value Oriented: WHY First, Align WHY
  - Interactive: Believe crew, Yes And
  - Iterative: Fast fail, Learn and Pivot

## 멤버
```
{역할}
- 프로파일: {이름}/{별명}/{성별}/{나이}
- 성향: {style 정보}
- 경력: {background 정보}

...반복...
```

## 대화 가이드
- 언어: 특별한 언급이 없는 경우 한국어를 사용
- 호칭: 실명 사용하지 않고 닉네임으로 호칭
- 질문: 프롬프트가 'q:'로 시작하면 질문을 의미함
  - Fact와 Opinion으로 나누어 답변
  - Fact는 출처 링크를 표시

## 최적안 도출
프롬프트가 'o:'로 시작하면 최적안 도출을 의미함
1. 각자의 생각을 얘기함
2. 의견을 종합하여 동일한 건 한 개만 남기고 비슷한 건 합침
3. 최적안 후보 5개를 선정함
4. 각 최적안 후보 5개에 대해 평가함
5. 최적안 1개를 선정함
6. `1)번 ~ 5)번` 과정을 3번 반복함
7. 최종으로 선정된 최적안을 제시함

## Git 연동
- "pull" 명령어 입력 시 Git pull 명령을 수행하고 충돌이 있을 때 최신 파일로 병합 수행  
- "push" 또는 "푸시" 명령어 입력 시 git add, commit, push를 수행 
- Commit Message는 한글로 함

## URL링크 참조
- URL링크는 WebFetch가 아닌 'curl {URL} > .temp/{filename}'명령으로 저장하여 참조함  
- 동일한 파일이 있으면 덮어 씀 

## 마크다운 작성 가이드
- 문서 작성 시 명사체(명사형 종결어미) 사용
  - 예시: "~한다" → "~함", "~이다" → "~임", "~된다" → "~됨"
  - 예시: "지원한다" → "지원", "사용할 수 있다" → "사용 가능"
- 한 줄은 120자 이내로 작성, 긴 문장은 적절히 줄바꿈
- 줄바끔 시 문장 끝에 스페이스 2개 + 줄바꿈
- 빈 줄(`\n\n`) 없이 줄바꿈하는 모든 경우, 줄 끝에 스페이스 2개 필수 (없으면 렌더링 시 한 줄로 합쳐짐)
- 간결하고 객관적인 기술 문서 스타일 유지

## 정직한 보고 규칙
### 핵심 원칙
- **실행하지 않은 것을 완료라고 보고하지 않는다**
- 문서 작성 ≠ 작업 완료. 문서는 실제 결과를 기록하는 것이지, 문서를 쓰면 완료가 되는 것이 아님
- 코드 작성 ≠ 동작 확인. 빌드 통과는 "코드가 컴파일된다"일 뿐, "서비스가 동작한다"가 아님

### 보고 시 체크리스트
1. 이 단계의 "완료 기준"이 무엇인지 먼저 확인
2. 그 기준을 실제로 충족했는지 증거(로그, 응답, 스크린샷) 확인

## Lessons Learned
> skill/agent 실행 중 확인된 시행착오와 교훈을 기록한다.
> 모든 에이전트는 작업 전 이 섹션을 반드시 참고한다.

### 기록 규칙
- 실행 중 시행착오 발생 시 Notepad Working Memory에 즉시 기록한다 (`notepad_write_working` 도구 호출)
  - 형식: `{agent명}: {문제 요약}. {해결 방법}. {관련 파일}`
- 반복 검증된 핵심 교훈만 이 섹션(AGENTS.md)에 승격한다 (Edit 도구로 추가)
  - 형식: `- [HIGH/MED] {교훈 한 줄} — {출처: agent명/단계명}`
- 최대 20항목 유지, 넘으면 오래된 MED부터 정리
- 기존 항목과 중복되는 내용은 기록하지 않음

### 교훈 목록
- [HIGH] `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 - 공통

## 백엔드 서비스 기동/중지
python3 {NPD_PLUGIN_DIR}/resources/tools/customs/general/run-backend.py [{service-name}] {OPTIONS}
OPTIONS:
```
# 전체 서비스 시작 (서비스 간 5초 delay, 기존 실행 중인 서비스는 자동 중지)
--config-dir . --delay 5

# 백그라운드로 전체 서비스 시작
--config-dir . --delay 5 > /dev/null 2>&1 &

# 개별 서비스 시작 (기존 실행 중이면 자동 중지 후 재시작)
{service-name}

# 전체 서비스 중지
--stop

# 개별 서비스 중지
--stop {service-name}

# 서비스 목록 확인
--list
```

## 프론트엔드 서비스 기동/중지
python3 {NPD_PLUGIN_DIR}/resources/tools/customs/general/run-frontend.py [{service-name}] {OPTIONS}

```
# 프론트엔드 개발 서버 시작
start

# 기존 포트 점유 프로세스를 강제 종료 후 시작
start --force

# 백그라운드로 시작
start --background

# 프론트엔드 개발 서버 중지
stop

# 프론트엔드 개발 서버 상태 확인
status

# 프로젝트 루트 지정
--project-dir /path/to/project start
```

## Advisor 활용 규칙
- Advisor 모델은 Opus 가장 최신 버전으로 설정  
- 실제 작업을 시작하기 전에 먼저 Advisor를 호출
- 작업 진행 중 Advisor의 자문이 필요하면 호출. 단, 최대 3번까지만 호출
- 작업 완료 후 한번 더 Advisor를 호출
- Advisor의 응답은 최대 200자를 초과하지 않게 함 

## 환경변수
- AI_RUNTIME: Claude Code / Claude Cowork / Cursor / Codex / Antigravity 중 하나
- NPD_PLUGIN_DIR: "{NPD_PLUGIN_DIR}"
- PROJECT_DIR: {프로젝트 디렉토리}

````

**멤버 구성 규칙:**
- NPD 플러그인의 `agents/*/agentcard.yaml`에서 `persona.profile`과 `persona.style`, `persona.background`를 읽어 구성
- `{역할}` = `persona.profile.role`
- `{이름}` = `persona.profile.name`
- `{별명}` = `persona.profile.nickname`
- `{성별}` = `persona.profile.gender`
- `{나이}` = `persona.profile.age`
- `{style 정보}` = `persona.style` (첫 줄만 요약)
- `{background 정보}` = `persona.background` (첫 줄만 요약)

#### 프로젝트 디렉토리에 CLAUDE.md를 생성합니다.
아래 내용으로 CLAUDE.md 생성
```
@AGENTS.md
```

### Phase 5: NPD 플러그인 디렉토리 접근 권한 셋팅 

NPD 플러그인 디렉토리에 대한 에이전트의 Read/Write/Edit/Bash 권한을 설정하여 개발 및 검증 과정에서 파일 생성/수정/실행 가능하도록 함.
`{프로젝트 디렉토리}/.claude/settings.local.json` 파일의 "permissions" 섹션에 아래 권한 추가:  
```
"permissions": {
  "allow": [
    "Read({NPD_PLUGIN_DIR}/**)",
    "Write({NPD_PLUGIN_DIR}/**)",
    "Edit({NPD_PLUGIN_DIR}/**)",
    "Bash(python {NPD_PLUGIN_DIR}/**)",
    "Bash(python3 {NPD_PLUGIN_DIR}/**)"
  ],
  "additionalDirectories": [
    "{NPD_PLUGIN_DIR}"
  ]
}
```

### Phase 6. GitHub 레포 생성 (선택)

<!--ASK_USER-->
{"title":"GitHub 레포 생성","questions":[
  {"question":"GitHub 원격 저장소를 생성할까요?","type":"radio","options":["생성","건너뛰기"]}
]}
<!--/ASK_USER-->

**생성** 선택 시:

**6-1. Organization 입력**

<!--ASK_USER-->
{"title":"GitHub Organization","questions":[
  {"question":"GitHub Organization을 입력해주세요. 비워두면 개인 계정(username)에 생성됩니다.","type":"text"}
]}
<!--/ASK_USER-->

- 사용자가 입력하지 않거나 빈 값이면 → `--org` 옵션 없이 개인 계정에 생성
- 사용자가 Organization을 입력하면 → `--org {입력값}` 옵션으로 해당 Organization에 생성

**6-2. 공개/비공개 선택**

<!--ASK_USER-->
{"title":"저장소 공개 설정","questions":[
  {"question":"저장소를 공개(Public)로 생성할까요, 비공개(Private)로 생성할까요?","type":"radio","options":["Public","Private"]}
]}
<!--/ASK_USER-->

- **Public** 선택 시 → `--private` 옵션 없이 공개 저장소로 생성
- **Private** 선택 시 → `--private` 옵션으로 비공개 저장소로 생성

**6-3. 레포 생성 실행**

1. `{NPD_PLUGIN_DIR}/resources/tools/customs/git/create_repo.py` 도구 존재 여부 확인
2. 환경변수 `GITHUB_TOKEN` 설정 여부 확인
3. 레포 생성 실행
   ```
   python3 {NPD_PLUGIN_DIR}/resources/tools/customs/git/create_repo.py --name {project} --org {org} --private --token {GITHUB_TOKEN}
   ```
4. 생성된 레포 URL 보고

**건너뛰기** 선택 시 → Phase 7로 이동

### Phase 7. 완료 보고

```
## 프로젝트 생성 완료

- 프로젝트 디렉토리: {프로젝트 디렉토리}
- MVP 비즈니스 도메인: {MVP 비즈니스 도메인}
- GitHub 레포: {URL 또는 "미생성"}
- GitHub Organization: {Organization명 또는 "개인 계정"}
- 저장소 공개 설정: {Public 또는 Private}

### 다음 단계
새로운 대화창에서 `{PROJECT_DIR}`폴더를 선택한 후 `/npd:plan`으로 기획을 시작하세요.
```

## 완료 조건

- [ ] 모든 워크플로우 단계가 정상 완료됨
- [ ] 프로젝트 디렉토리 및 .gitignore, AGENTS.md, AGENTS.md가 생성됨

## 상태 정리
완료 시 임시 상태 파일 정리. 산출물은 유지.

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 기존 프로젝트 디렉토리를 확인 없이 덮어쓰지 않을 것 |
| 2 | GitHub 토큰을 코드나 파일에 하드코딩하지 않을 것 |
| 3 | 기술스택(백엔드/프론트엔드)을 create 단계에서 질문하지 않을 것 |
