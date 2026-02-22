---
name: create
description: 새 프로젝트 생성 — 프로젝트 디렉토리 초기화, 도메인 컨텍스트 생성, GitHub 레포 자동 생성
type: orchestrator
user-invocable: true
allowed-tools: Read, Write, Bash, Task
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
.env.local

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

### Step 6. GitHub 레포 생성 (선택)

<!--ASK_USER-->
{"title":"GitHub 레포 생성","questions":[
  {"question":"GitHub 원격 저장소를 생성할까요?","type":"radio","options":["생성","건너뛰기"]}
]}
<!--/ASK_USER-->

**생성** 선택 시:
1. `resources/tools/customs/git/create_repo.py` 도구 존재 여부 확인
2. 환경변수 `GITHUB_TOKEN` 설정 여부 확인
3. 공개/비공개 여부 확인 후 레포 생성 실행
4. 생성된 레포 URL 보고

**건너뛰기** 선택 시 → Step 7로 이동

### Step 7. 완료 보고

```
## 프로젝트 생성 완료

- 프로젝트 디렉토리: {프로젝트 디렉토리}
- MVP 주제: {MVP 주제}
- 도메인: {추론된 도메인}
- 도메인 컨텍스트: {프로젝트 디렉토리}/.npd/domain-context.yaml
- GitHub 레포: {URL 또는 "미생성"}

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
