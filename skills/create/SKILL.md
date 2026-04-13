---
name: create
description: 새 프로젝트 생성 — 프로젝트 디렉토리 초기화, 도메인 컨텍스트 생성, GitHub 레포 자동 생성
type: orchestrator
user-invocable: true
---

# Create

[NPD Create 활성화]

## 목표

사용자로부터 MVP 주제와 프로젝트 디렉토리를 입력받아
프로젝트 디렉토리를 초기화하고, MVP 주제로 도메인을 자동 추론하여
프로젝트에 도메인 컨텍스트 파일(`.npd/domain-context.yaml`)을 생성하며, GitHub 레포를 자동 생성함.
이후 단계(plan/design/develop)에서는 기존 `domain-expert` 에이전트가 이 컨텍스트 파일을 참조하여 도메인 특화 자문을 수행함.

## 활성화 조건

사용자가 `/npd:create` 호출 시 또는 "새 프로젝트 생성", "프로젝트 만들어줘" 키워드 감지 시.

## 워크플로우

### Step 1. MVP 주제 입력

가장 먼저 MVP 주제를 입력받습니다.

<!--ASK_USER-->
{"title":"MVP 주제","questions":[
  {"question":"만들고자 하는 서비스의 MVP 주제를 입력해주세요. (예: 당뇨 환자 식단 관리 앱, 중고 도서 거래 플랫폼)","type":"text"}
]}
<!--/ASK_USER-->

### Step 2. 프로젝트 디렉토리 입력

MVP 주제를 기반으로 적절한 프로젝트 디렉토리명을 영문 kebab-case로 추천합니다.

예시:
- "당뇨 환자 식단 관리 앱" → `~/workspace/diabetes-diet-app`
- "중고 도서 거래 플랫폼" → `~/workspace/used-book-market`

<!--ASK_USER-->
{"title":"프로젝트 디렉토리","questions":[
  {"question":"프로젝트 디렉토리를 입력해주세요.","description":"MVP 주제에 따른 추천 디렉토리: ~/workspace/{추천명}\n기본값: ~/workspace/{추천명}","type":"text"}
]}
<!--/ASK_USER-->

- 사용자가 입력하지 않으면 추천 디렉토리를 기본값으로 사용
- 이미 존재하는 디렉토리인 경우 사용자에게 확인 후 진행

### Step 3. 도메인 추론 및 도메인 컨텍스트 생성

MVP 주제를 분석하여 도메인을 추론하고, 프로젝트에 도메인 컨텍스트 파일을 생성합니다.
기존 NPD `domain-expert` 에이전트를 그대로 활용하되, 프로젝트별 도메인 특화 정보를 컨텍스트 파일로 제공합니다.

**3-1. 도메인 추론**

MVP 주제에서 핵심 도메인을 한 단어로 추론합니다.
- 예: "당뇨 환자 식단 관리 앱" → `healthcare`
- 예: "중고 도서 거래 플랫폼" → `commerce`

추론 결과:
- 도메인명 (영문 한 단어)
- 전문 지식 목록
- 관련 규제/표준

**3-2. 프로젝트명 추출**

프로젝트 디렉토리 경로에서 마지막 디렉토리명을 `{project}`로 추출합니다.
- 예: `~/workspace/diabetes-diet-app` → `{project}` = `diabetes-diet-app`
- 예: `~/workspace/used-book-market` → `{project}` = `used-book-market`

**3-3. 도메인 컨텍스트 파일 생성**

프로젝트 디렉토리의 `.npd/domain-context.yaml`에 도메인 특화 정보를 생성합니다.
이후 단계에서 `domain-expert` 에이전트 호출 시 이 파일을 프롬프트에 주입하여 도메인 특화 자문을 수행합니다.

**domain-context.yaml 구조:**
```yaml
# 프로젝트 도메인 컨텍스트
# 이 파일은 NPD의 domain-expert 에이전트가 참조하는 도메인 특화 정보입니다.

project: "{project}"
mvp_topic: "{MVP 주제}"
domain:
  name: "{도메인명}"           # 예: healthcare, commerce, fintech, education
  description: "{도메인 설명}"  # 예: 만성질환 환자 건강관리 서비스 도메인

background: |
  {도메인 특화 경력 및 전문성}
  # 예(healthcare): 서울대학교병원 내분비내과 임상연구 코디네이터 경력. 디지털 헬스케어 스타트업 3곳 자문.
  #   만성질환 관리 프로그램 설계 경험. 식약처 디지털 치료기기 인허가 프로세스 숙지.

expertise:
  - "{전문 지식 1}"
  - "{전문 지식 2}"
  - "{전문 지식 3}"

regulations:
  - name: "{규제/표준명}"
    description: "{설명}"
  - name: "{규제/표준명}"
    description: "{설명}"
```

**규칙:**
- 도메인을 너무 광범위하게 정의하지 않을 것 (예: "IT" 같은 범용 도메인 금지)
- 규제/표준은 해당 도메인에서 실제로 적용되는 것만 포함
- 이 파일은 프로젝트에 속하므로 플러그인 소스를 수정하지 않음

### Step 4. 프로젝트 디렉토리 생성

프로젝트 디렉토리와 기본 파일만 생성합니다.
하위 구조는 이후 단계에서 기술스택이 결정된 후 생성합니다.

**4-1. 프로젝트 디렉토리 구조:**
```
{프로젝트 디렉토리}/
├── .npd/
│   └── domain-context.yaml
├── .gitignore
└── CLAUDE.md
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

### Step 5. CLAUDE.md 생성

프로젝트 디렉토리에 CLAUDE.md를 생성합니다.
NPD 플러그인의 `agents/*/agentcard.yaml`을 읽어 멤버 정보를 구성합니다.

**CLAUDE.md 구조:**

````markdown
# 스쿼드 소개
## 플러그인 설정
- NPD_PLUGIN_DIR: "{NPD_PLUGIN_DIR}"

## 목표
{MVP 주제} 을/를 위한 {서비스명} 개발

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
- 반복 검증된 핵심 교훈만 이 섹션(CLAUDE.md)에 승격한다 (Edit 도구로 추가)
  - 형식: `- [HIGH/MED] {교훈 한 줄} — {출처: agent명/단계명}`
- 최대 20항목 유지, 넘으면 오래된 MED부터 정리
- 기존 항목과 중복되는 내용은 기록하지 않음

### 스킬부스팅 규칙
SKILL.md 또는 대화에서 아래 키워드가 나오면 **반드시 Skill 도구를 호출**하여 해당 스킬을 실행한다.
텍스트 출력으로 대체하거나, 키워드를 무시하는 것은 금지한다.

| 키워드 (어느 형태든 매칭) | Skill 도구 호출 |
|--------------------------|----------------|
| `/plan`, `plan 모드`, `plan 스킬` | `Skill("oh-my-claudecode:plan")` |
| `/ralplan`, `ralplan 모드`, `ralplan 스킬` | `Skill("oh-my-claudecode:ralplan")` |
| `/ralph`, `ralph 모드`, `ralph 스킬` | `Skill("oh-my-claudecode:ralph")` |
| `/build-fix`, `build-fix 모드` | `Skill("oh-my-claudecode:build-fix")` |
| `/ultraqa`, `ultraqa 모드`, `ultraqa 스킬` | `Skill("oh-my-claudecode:ultraqa")` |
| `/review`, `review 모드` | `Skill("oh-my-claudecode:review")` |
| `/analyze`, `analyze 모드` | `Skill("oh-my-claudecode:analyze")` |
| `/code-review`, `code-review 모드` | `Skill("oh-my-claudecode:code-review")` |
| `/security-review`, `security-review 모드` | `Skill("oh-my-claudecode:security-review")` |
| `ulw` | `Skill("oh-my-claudecode:ultrawork")` |

### 교훈 목록
- [HIGH] `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 - 공통

## PLUGIN_DIR 변수 해석 
**`{NPD_PLUGIN_DIR}`**: NPD 플러그인 루트 디렉토리의 절대 경로
오케스트레이터는 실행 시작 시 다음 순서로 `{NPD_PLUGIN_DIR}`를 결정
1. `~/.claude/plugins/cache/npd/npd/` 하위에서 최신 버전 디렉토리를 탐색
2. 해당 디렉토리의 절대 경로를 `{NPD_PLUGIN_DIR}`에 바인딩
3. 이후 모든 `{NPD_PLUGIN_DIR}/resources/...` 경로를 절대 경로로 치환하여 파일을 읽음

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

### Step 6. 플러그인 디렉토리 접근 권한 셋팅 

플러그인 디렉토리에 대한 에이전트의 Read/Write/Edit/Bash 권한을 설정하여 개발 및 검증 과정에서 파일 생성/수정/실행 가능하도록 함.
`~/.claude/settings.json` 파일의 "permissions" 섹션에 아래 권한 추가:  
```
"permissions": {
  "allow": [
    "Read({사용자홈}/.claude/plugins/**)",
    "Write({사용자홈}/.claude/plugins/**)",
    "Edit({사용자홈}/.claude/plugins/**)",
    "Bash(python {사용자홈}/.claude/plugins/**)",
    "Bash(python3 {사용자홈}/.claude/plugins/**)"
  ],
  "additionalDirectories": [
    "{사용자홈}/.claude/plugins"
  ]
}
```

### Step 7. GitHub 레포 생성 (선택)

<!--ASK_USER-->
{"title":"GitHub 레포 생성","questions":[
  {"question":"GitHub 원격 저장소를 생성할까요?","type":"radio","options":["생성","건너뛰기"]}
]}
<!--/ASK_USER-->

**생성** 선택 시:

**7-1. Organization 입력**

<!--ASK_USER-->
{"title":"GitHub Organization","questions":[
  {"question":"GitHub Organization을 입력해주세요. 비워두면 개인 계정(username)에 생성됩니다.","type":"text"}
]}
<!--/ASK_USER-->

- 사용자가 입력하지 않거나 빈 값이면 → `--org` 옵션 없이 개인 계정에 생성
- 사용자가 Organization을 입력하면 → `--org {입력값}` 옵션으로 해당 Organization에 생성

**7-2. 공개/비공개 선택**

<!--ASK_USER-->
{"title":"저장소 공개 설정","questions":[
  {"question":"저장소를 공개(Public)로 생성할까요, 비공개(Private)로 생성할까요?","type":"radio","options":["Public","Private"]}
]}
<!--/ASK_USER-->

- **Public** 선택 시 → `--private` 옵션 없이 공개 저장소로 생성
- **Private** 선택 시 → `--private` 옵션으로 비공개 저장소로 생성

**7-3. 레포 생성 실행**

1. `{NPD_PLUGIN_DIR}/resources/tools/customs/git/create_repo.py` 도구 존재 여부 확인
2. 환경변수 `GITHUB_TOKEN` 설정 여부 확인
3. 레포 생성 실행
   ```
   python3 {NPD_PLUGIN_DIR}/resources/tools/customs/git/create_repo.py --name {project} --org {org} --private --token {GITHUB_TOKEN}
   ```
4. 생성된 레포 URL 보고

**건너뛰기** 선택 시 → Step 7로 이동

### Step 8. 완료 보고

```
## 프로젝트 생성 완료

- 프로젝트 디렉토리: {프로젝트 디렉토리}
- MVP 주제: {MVP 주제}
- 도메인: {추론된 도메인}
- 도메인 컨텍스트: {프로젝트 디렉토리}/.npd/domain-context.yaml
- GitHub 레포: {URL 또는 "미생성"}
- GitHub Organization: {Organization명 또는 "개인 계정"}
- 저장소 공개 설정: {Public 또는 Private}

### 다음 단계
`/npd:plan` 으로 기획을 시작하세요.
```

## 완료 조건

- [ ] 모든 워크플로우 단계가 정상 완료됨
- [ ] 프로젝트 디렉토리 및 .gitignore, CLAUDE.md가 생성됨
- [ ] `.npd/domain-context.yaml` 도메인 컨텍스트 파일이 생성됨
- [ ] 검증 프로토콜을 통과함
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (프로젝트 디렉토리, .gitignore, CLAUDE.md, .npd/domain-context.yaml)
2. 산출물 내용 품질 검증 (CLAUDE.md 멤버 정보, domain-context.yaml 도메인 특화 정보)
3. 이전 Phase 산출물과의 일관성 확인

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | MVP 주제를 가장 먼저 입력받을 것 |
| 2 | MVP 주제를 기반으로 프로젝트 디렉토리명을 영문 kebab-case로 추천할 것 |
| 3 | 기술스택은 create 단계에서 수집하지 않을 것 (plan/design 단계에서 결정) |
| 4 | MVP 주제로 도메인을 반드시 추론하여 프로젝트에 `.npd/domain-context.yaml`을 생성할 것 |
| 5 | 프로젝트 디렉토리, .gitignore, CLAUDE.md를 반드시 생성할 것 |
| 6 | CLAUDE.md를 프로젝트 루트에 반드시 생성할 것 |
| 7 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 기존 프로젝트 디렉토리를 확인 없이 덮어쓰지 않을 것 |
| 2 | GitHub 토큰을 코드나 파일에 하드코딩하지 않을 것 |
| 3 | 기술스택(백엔드/프론트엔드)을 create 단계에서 질문하지 않을 것 |

## 검증 체크리스트

- [ ] MVP 주제가 가장 먼저 수집되는가
- [ ] MVP 주제 기반으로 프로젝트 디렉토리명이 추천되는가
- [ ] 프로젝트 디렉토리 기본값이 ~/workspace/{추천명} 인가
- [ ] 도메인 추론과 domain-context.yaml 생성이 하나의 Step에서 수행되는가
- [ ] 프로젝트 디렉토리 및 .gitignore 생성 완료
- [ ] CLAUDE.md 생성 완료
- [ ] `.npd/domain-context.yaml` 생성 완료
- [ ] 기술스택을 질문하지 않는가
- [ ] 완료 보고에 다음 단계 안내 포함
