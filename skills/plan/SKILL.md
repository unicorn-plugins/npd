---
name: plan
description: 기획 단계 AI 협업 — 18단계 서비스 기획 워크플로우 (MVP정의 → 고객분석 → 시장조사 → 고객경험 → 문제가설 → 솔루션 → 비즈니스모델 → 이벤트스토밍 → 유저스토리 → UI/UX → 프로토타입 → 플로우 스크립트)
type: orchestrator
user-invocable: true
allowed-tools: Read, Write, Task, Bash, WebSearch
---

# Plan

[NPD Plan 활성화]

## 목표

PO·서비스기획자·도메인전문가·아키텍트·AI엔지니어가 협업하여
6단계 18스텝의 완전한 서비스 기획을 수행함.
MVP 정의부터 프로토타입까지 체계적으로 산출물을 생성하며,
각 단계의 산출물이 다음 단계의 컨텍스트로 누적 연결됨.

## 활성화 조건

사용자가 `/npd:plan` 호출 시 또는 "기획 시작", "기획해줘", "서비스 기획" 키워드 감지 시.

## 선행 조건

- `/npd:create` 완료 (프로젝트 디렉토리 및 CLAUDE.md 존재)
- `.npd/domain-context.yaml` 존재 (도메인 컨텍스트)

## 에이전트 호출 규칙

| 에이전트 | FQN |
|----------|-----|
| product-owner | `npd:product-owner:product-owner` |
| service-planner | `npd:service-planner:service-planner` |
| architect | `npd:architect:architect` |
| domain-expert | `npd:domain-expert:domain-expert` |
| ai-engineer | `npd:ai-engineer:ai-engineer` |

### 프롬프트 조립

1. `agents/{agent-name}/`에서 3파일 로드 (AGENT.md + agentcard.yaml + tools.yaml)
2. `gateway/runtime-mapping.yaml` 참조하여 구체화:
   - **모델 구체화**: agentcard.yaml의 `tier` → `tier_mapping`에서 모델 결정
   - **툴 구체화**: tools.yaml의 추상 도구 → `tool_mapping`에서 실제 도구 결정
   - **금지액션 구체화**: agentcard.yaml의 `forbidden_actions` → `action_mapping`에서 제외할 실제 도구 결정
   - **최종 도구** = (구체화된 도구) - (제외 도구)
3. **도메인 컨텍스트 주입**: `domain-expert` 에이전트 호출 시 프로젝트의 `.npd/domain-context.yaml`을 읽어 프롬프트에 포함. 도메인명, 배경(background), 전문성(expertise), 규제/표준(regulations) 정보를 동적 컨텍스트로 주입하여 도메인 특화 자문을 수행
4. 프롬프트 조립: 공통 정적(runtime-mapping) → 에이전트별 정적(3파일) → 인격(persona) → 도메인 컨텍스트(domain-expert만) → 동적(작업 지시)
5. `Task(subagent_type=FQN, model=구체화된 모델, prompt=조립된 프롬프트)` 호출

## Step 0. 진행 모드 선택

기획 워크플로우 시작 전, 각 단계별 승인 여부를 선택합니다.

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

## 워크플로우 개요

```
1단계: 정의 (MVP정의 + 고객분석 + 시장조사)
   ↓
2단계: 문제 발견 (고객경험단계 + 고객경험조사 + 여정맵 + 문제가설 + 방향성)
   ↓
3단계: 솔루션 (아이디어발상 + 솔루션선정)
   ↓
4단계: 비즈니스 모델 (비즈니스모델 + 발표자료)
   ↓
5단계: 제품 설계 (이벤트스토밍 + 유저스토리 + UI/UX설계)
   ↓
6단계: 프로토타입 + 플로우 스크립트
```

---

## 1단계: 정의 (Define)

### Step 1. MVP 주제 정의 → Agent: product-owner (`/oh-my-claudecode:plan` 활용)

- **GUIDE**: `resources/guides/plan/01-mvp-definition-guide.md` 참조
- **TASK**: CLAUDE.md의 MVP 주제를 기반으로 구체적인 비즈니스 도메인을 정의하고, MVP 후보를 시장 잠재력·사용자 pain points·실현 가능성·경쟁 우위 4가지 팩터로 평가하여 최종 MVP 주제를 확정
- **EXPECTED OUTCOME**: `docs/plan/define/MVP정의.md` 생성
  - MVP 주제 명확한 정의
  - 선정 이유 (4가지 팩터 평가표 — 각 팩터 5점 만점)
  - 목표 비즈니스 도메인
- **MUST DO**: MVP는 최소한의 핵심 기능에 집중. 3-6개월 내 개발 가능한 규모. 시장 검증이 가능한 범위로 정의. MVP 후보 2개 이상 비교 평가
- **MUST NOT DO**: 기술 구현 방법을 이 단계에서 결정하지 않을 것
- **CONTEXT**: CLAUDE.md의 프로젝트 정보 및 MVP 주제
- **POST-ACTION**: 프로젝트 CLAUDE.md의 `## 목표` 섹션 다음에 `## MVP 주제` 섹션을 추가하고, 확정된 MVP 주제와 한 줄 설명을 기록

### Step 2. 고객 분석 → Agent: service-planner (`/oh-my-claudecode:plan` 활용)

- **GUIDE**: `resources/guides/plan/02-customer-analysis-guide.md` 참조
- **TASK**: JTBD(Jobs To Be Done) 프레임워크를 사용하여 타겟 고객 유형을 정의. 사용자 세그먼트(3-5개)를 식별하고, 각 세그먼트의 인구통계·행동 패턴·현재 상황을 정리하며, 주요 Job과 관련 Jobs, 원하는 결과를 도출
- **EXPECTED OUTCOME**: `docs/plan/define/고객분석.md` 생성
  - 타겟 고객 유형 (JTBD 형식: 사용자 세그먼트 + 달성하려는 job)
  - 사용자 세그먼트 3-5개 (인구통계, 행동 패턴, 현재 상황)
  - Job to be Done (주요 job, 관련 jobs, 원하는 결과)
- **MUST DO**: "job to be done"은 구체적으로. 솔루션이 아닌 고객 목표에 집중. 고객 관점에서 작성
- **MUST NOT DO**: 기업 관점에서 작성하지 않을 것. 기능 중심이 아닌 목표 중심으로 작성
- **CONTEXT**: `docs/plan/define/MVP정의.md`
- **POST-ACTION**: 프로젝트 CLAUDE.md의 `## MVP 주제` 섹션 다음에 `## 고객유형` 섹션을 추가하고, 선정된 고객유형과 최우선 고객 세그먼트를 기록

### Step 3. 시장 조사 → Agent: domain-expert (`/oh-my-claudecode:plan` 활용)

> **도메인 컨텍스트 주입**: `domain-expert` 호출 시 프로젝트의 `.npd/domain-context.yaml`을 읽어 프롬프트에 포함하여 도메인 특화 자문을 수행합니다.

- **GUIDE**: `resources/guides/plan/03-market-research-guide.md` 참조
- **TASK**: MVP 주제와 타겟 고객에 대한 철저한 시장 조사 수행. 시장 규모(TAM/SAM/SOM), 경쟁 환경 분석(3-5개 경쟁사), 고객 트렌드, 규제·법적 환경, SWOT 분석, 시장 진입 전략 권고를 포함
- **EXPECTED OUTCOME**: `docs/plan/define/시장조사.md` 생성
  - 시장 규모 및 성장 (TAM, SAM, SOM, CAGR, 5개년 전망)
  - 경쟁 환경 분석 (3-5개 경쟁사 강점/약점/점유율)
  - 고객 트렌드 (소비자 행동 변화, 기술 혁신 영향)
  - 규제 및 법적 환경
  - SWOT 분석
  - 시장 진입 전략 권고 (차별화 포인트, 리스크 완화, GTM 타임라인)
- **MUST DO**: 실제 데이터와 통계 기반 분석. 출처 인용. WebSearch를 적극 활용하여 최신 정보 반영
- **MUST NOT DO**: 추측에 기반한 분석 금지. 출처 없는 주장 금지
- **CONTEXT**: `docs/plan/define/MVP정의.md`, `docs/plan/define/고객분석.md`

---

## 2단계: 문제 발견 및 방향성 (Discover)

### Step 4. 고객경험 단계 정의 → Agent: service-planner (`/oh-my-claudecode:plan` 활용)

- **GUIDE**: `resources/guides/plan/04-customer-journey-stages-guide.md` 참조
- **TASK**: MVP 주제와 고객유형을 기반으로 현재 고객이 겪는 경험 단계(5-7개)를 정의. 문제 인식부터 해결/관리까지 전체 흐름을 커버하는 순차적 단계를 도출
- **EXPECTED OUTCOME**: `docs/plan/define/고객경험단계.md` 생성
  - 고객경험 단계 (화살표로 연결, 예: `니즈 인식 -> 방법 탐색 -> 수집 -> 분류/정리 -> 활용 -> 최적화/관리`)
  - 단계별 설명 (주요 행동, 좋은 생각/느낌, 주요 Pain Points)
  - 단계 도출 근거
- **MUST DO**: 5-7개 단계로 간결하게. 고객 관점의 행동 중심으로 작성
- **MUST NOT DO**: 기업 프로세스가 아닌 고객 행동 흐름으로 작성할 것
- **CONTEXT**: `docs/plan/define/MVP정의.md`, `docs/plan/define/고객분석.md`, `docs/plan/define/시장조사.md`

### Step 5. 고객 경험 조사 → Agent: service-planner × 3 병렬 (`/oh-my-claudecode:ralph` 활용)

**조사 규모 설정**: Step 5 시작 전, 고객 경험 조사의 규모를 사용자로부터 입력받습니다.

<!--ASK_USER-->
{"title":"고객 경험 조사 규모 설정","questions":[
  {"question":"고객경험 인터뷰 대상자 수를 입력해 주세요. (기본값: 10명)","type":"text","placeholder":"10"},
  {"question":"관찰 조사 횟수를 입력해 주세요. (기본값: 10회)","type":"text","placeholder":"10"},
  {"question":"체험 테스트 횟수를 입력해 주세요. (기본값: 10회)","type":"text","placeholder":"10"}
]}
<!--/ASK_USER-->

> 사용자가 입력한 값을 각각 `{인터뷰수}`, `{관찰수}`, `{체험수}`로 사용합니다. 미입력 시 기본값 10을 적용합니다.

- **GUIDE**: `resources/guides/plan/05-customer-experience-guide.md` 참조
- **실행 방식**: 3가지 조사를 서브에이전트로 **병렬 수행**한 후, 인터뷰 결과 취합을 순차 수행합니다.

```
┌─────────────────────────────────────────────────┐
│  Step 5 시작 (조사 규모 입력 완료)                │
│                                                   │
│  ┌───────────┐ ┌───────────┐ ┌───────────────┐   │
│  │ 5-A 관찰  │ │ 5-B 체험  │ │ 5-C 인터뷰    │   │
│  │ (병렬)    │ │ (병렬)    │ │ (병렬)        │   │
│  └─────┬─────┘ └─────┬─────┘ └──────┬────────┘   │
│        └──────────────┼──────────────┘             │
│                       ▼                            │
│            ┌────────────────────┐                  │
│            │ 5-D 인터뷰 취합   │                  │
│            │ (5-C 완료 후 순차) │                  │
│            └────────────────────┘                  │
└─────────────────────────────────────────────────┘
```

#### Step 5-A. 관찰 조사 (병렬) → Agent: service-planner

- **TASK**: 고객경험 단계를 기준으로 {관찰수}회의 관찰 조사를 수행하여 고객 행동 데이터를 생성
- **EXPECTED OUTCOME**: `docs/plan/define/관찰결과.md` — 관찰 {관찰수}회 결과 (고객경험 단계별 관찰 행동, 어려움, 특이사항, Pain Point 및 니즈 분석, 행동 패턴 분석)
- **MUST DO**: {관찰수}회 모두 생략하지 않고 제공. 고객경험 단계별로 데이터 구조화. 구체적이고 현실적인 데이터
- **MUST NOT DO**: 조사 결과를 추상적으로 요약하지 않을 것
- **CONTEXT**: `docs/plan/define/고객분석.md`, `docs/plan/define/고객경험단계.md`

#### Step 5-B. 체험 조사 (병렬) → Agent: service-planner

- **TASK**: 고객경험 단계를 기준으로 {체험수}회의 체험 테스트를 수행하여 사용자 경험 데이터를 생성
- **EXPECTED OUTCOME**: `docs/plan/define/체험결과.md` — 체험 {체험수}회 결과 (고객경험 단계별 경험 내용, 긍정/부정 측면, 만족도)
- **MUST DO**: {체험수}회 모두 생략하지 않고 제공. 고객경험 단계별로 데이터 구조화. 구체적이고 현실적인 데이터
- **MUST NOT DO**: 조사 결과를 추상적으로 요약하지 않을 것
- **CONTEXT**: `docs/plan/define/고객분석.md`, `docs/plan/define/고객경험단계.md`

#### Step 5-C. 고객경험 인터뷰 (병렬) → Agent: service-planner

- **TASK**: 고객경험 단계를 기준으로 {인터뷰수}명 대상 심층 인터뷰를 수행하여 개별 인터뷰 결과를 생성
- **EXPECTED OUTCOME**: `docs/plan/define/고객경험인터뷰결과.md` — 인터뷰 {인터뷰수}명 개별 결과 (고객경험 단계별 행동·생각·긍정적 느낌·부정적 느낌)
- **MUST DO**: {인터뷰수}명 모두 생략하지 않고 제공. 고객경험 단계별로 데이터 구조화. 구체적이고 현실적인 데이터
- **MUST NOT DO**: 조사 결과를 추상적으로 요약하지 않을 것. Pain point와 니즈를 혼동하지 않을 것
- **CONTEXT**: `docs/plan/define/고객분석.md`, `docs/plan/define/고객경험단계.md`

#### Step 5-D. 인터뷰 결과 취합 (5-C 완료 후 순차) → Agent: service-planner

- **TASK**: 5-C에서 생성된 개별 인터뷰 결과를 종합 분석하여 핵심 인사이트를 도출
- **EXPECTED OUTCOME**: `docs/plan/define/고객경험인터뷰결과취합.md` — 인터뷰 종합 분석 (핵심 인사이트, Pain Points, Needs, 기대 가치)
- **MUST DO**: 개별 인터뷰 데이터를 누락 없이 반영. 패턴과 공통점 식별
- **MUST NOT DO**: 개별 결과를 무시하고 일반화하지 않을 것
- **CONTEXT**: `docs/plan/define/고객경험인터뷰결과.md`, `docs/plan/define/고객분석.md`, `docs/plan/define/고객경험단계.md`

> **실행 지침**: Step 5-A, 5-B, 5-C를 `Task(run_in_background=true)`로 동시에 실행합니다. 3개 모두 완료되면 5-D를 순차 실행합니다. 모든 서브스텝이 완료되어야 Step 5 완료로 간주합니다.

### Step 6. 고객 여정 맵 작성 → Agent: service-planner (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/plan/06-journey-mapping-guide.md` 참조
- **TASK**: 고객경험 단계를 X축으로, 경험 조사 데이터를 기반으로 완전한 User Journey Map을 작성. 페르소나 정의, 단계별 행동·생각·감정·터치포인트·Pain Points·Gain Points 분석, 감정 곡선, 핵심 인사이트, 기회 영역 도출
- **EXPECTED OUTCOME**: 2개 파일 생성
  - `docs/plan/define/유저저니맵.md` — 페르소나, 여정 맵 상세, 감정 곡선, 핵심 인사이트, 기회 영역
  - `docs/plan/define/유저저니맵.svg` — 시각화된 여정 맵
- **MUST DO**: 고객경험 단계를 X축으로 사용. 실제 고객 데이터 기반 작성. 감정 곡선 포함
- **MUST NOT DO**: 추측에 기반한 여정 맵 작성 금지
- **CONTEXT**: `docs/plan/define/고객경험단계.md`, `docs/plan/define/관찰결과.md`, `docs/plan/define/체험결과.md`, `docs/plan/define/고객경험인터뷰결과.md`, `docs/plan/define/고객경험인터뷰결과취합.md`

### Step 7. 문제 가설 정의 → 전체 팀 협업 (발산-수렴-선택 패턴)

> **도메인 컨텍스트 주입**: `domain-expert` 호출 시 프로젝트의 `.npd/domain-context.yaml`을 읽어 프롬프트에 포함합니다.

- **GUIDE**: `resources/guides/plan/07-problem-hypothesis-guide.md` 참조
- **실행 방식**: 5개 서브스텝을 순차/병렬 조합으로 수행합니다.

```
┌──────────────────────────────────────────────────────────────┐
│  Step 7 시작                                                  │
│                                                                │
│  ── 7-1. 문제가설 정의 (발산-수렴-선택) ──                     │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                          │
│  │ PO │ │ SP │ │ DE │ │ AR │ │ AI │  ← 5WHY 병렬 (5명)        │
│  └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘                          │
│    └───────┼──────┼──────┼──────┘                              │
│              ▼                                                 │
│     ┌─────────────────┐                                       │
│     │ SP: 수렴 (합치기)│                                       │
│     └────────┬────────┘                                       │
│              ▼                                                 │
│     ┌─────────────────┐                                       │
│     │ PO: 선택 (확정) │ → 문제가설.md                          │
│     └────────┬────────┘                                       │
│              ▼                                                 │
│  ── 7-2. 문제 검증 인터뷰 (병렬) ──                            │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                          │
│  │ PO │ │ SP │ │ DE │ │ AR │ │ AI │  ← 인터뷰 병렬 (5명)      │
│  └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘                          │
│    └───────┼──────┼──────┼──────┘                              │
│              ▼                                                 │
│  ── 7-3. 인터뷰 결과 취합 ──                                   │
│     ┌─────────────────┐                                       │
│     │ SP: 결과 취합    │ → 문제검증인터뷰결과취합.md             │
│     └────────┬────────┘                                       │
│              ▼                                                 │
│  ── 7-4. 문제가설 피보팅 ──                                    │
│     ┌─────────────────┐                                       │
│     │ PO: 가설 수정    │ → 문제가설.md (덮어쓰기)               │
│     └────────┬────────┘                                       │
│              ▼                                                 │
│  ── 7-5. 비즈니스 가치 도출 (발산-수렴-선택) ──                 │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                          │
│  │ PO │ │ SP │ │ DE │ │ AR │ │ AI │  ← 발산 병렬 (5명)        │
│  └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘                          │
│    └───────┼──────┼──────┼──────┘                              │
│              ▼                                                 │
│     ┌─────────────────┐                                       │
│     │ SP: 수렴 (합치기)│                                       │
│     └────────┬────────┘                                       │
│              ▼                                                 │
│     ┌─────────────────┐                                       │
│     │ PO: 선택 (확정) │ → 비즈니스가치.md                      │
│     └─────────────────┘                                       │
└──────────────────────────────────────────────────────────────┘

PO=product-owner, SP=service-planner, DE=domain-expert, AR=architect, AI=ai-engineer
```

#### Step 7-1. 문제가설 정의 (발산-수렴-선택)

**7-1a. 발산 — 5WHY 수행 (병렬)** → Agent: product-owner, service-planner, domain-expert, architect, ai-engineer

- **TASK**: 각 팀원이 자신의 전문 관점에서 가장 큰 현상문제 3개를 도출하고 각각 5WHY로 근본원인을 분석. 사용자 심리적·제도/시스템적·맥락적·커뮤니케이션 측면에서 검토
- **EXPECTED OUTCOME**: 팀원별 5WHY 분석 결과 (팀원당 문제 3개 × 5WHY)
- **MUST DO**: 5WHY는 각 단계에서 "질문 + 응답" 형식으로 작성. 각 팀원의 전문성을 반영한 관점 차별화. 문제는 고객 관점에서 작성
- **MUST NOT DO**: 솔루션을 포함하지 않을 것
- **CONTEXT**: `docs/plan/define/고객분석.md`, `docs/plan/define/유저저니맵.md`, 고객 경험 조사 데이터 전체
- **실행**: 5개 에이전트를 `Task(run_in_background=true)`로 동시 실행

**7-1b. 수렴 — 유사 항목 합치기 (순차)** → Agent: service-planner

- **TASK**: 7-1a에서 도출된 5명의 5WHY 결과를 취합하고, 유사한 문제와 근본원인을 그룹핑하여 정리. 다층적 근본원인(심리적·제도/시스템적·맥락적·커뮤니케이션) 관점으로 재구조화
- **EXPECTED OUTCOME**: 수렴된 문제가설 후보 목록 (그룹핑된 문제 + 근본원인 + 출처 팀원 표기)
- **MUST DO**: 모든 팀원의 결과를 누락 없이 반영. 유사도 기준 명시
- **CONTEXT**: 7-1a 결과

**7-1c. 선택 — 최종 문제가설 확정 (순차)** → Agent: product-owner

- **TASK**: 수렴된 후보 중 가장 중요한 핵심 문제 3개와 근본원인을 선정하고 최종 문제가설로 확정
- **EXPECTED OUTCOME**: `docs/plan/define/문제가설.md` — 문제 3개, 5WHY 분석, 다층적 근본원인 검토, 핵심 근본원인 선정
- **MUST DO**: 선정 근거를 명확히 기술. 영향력·빈도·심각도 관점에서 평가
- **CONTEXT**: 7-1b 수렴 결과

#### Step 7-2. 문제 검증 인터뷰 (병렬) → Agent: product-owner, service-planner, domain-expert, architect, ai-engineer

**인터뷰 규모 설정**: Step 7-2 시작 전, 문제검증 인터뷰 대상자 수를 사용자로부터 입력받습니다.

<!--ASK_USER-->
{"title":"문제검증 인터뷰 규모 설정","questions":[
  {"question":"문제검증 인터뷰 대상자 수를 입력해 주세요. (기본값: 10명)","type":"text","placeholder":"10"}
]}
<!--/ASK_USER-->

> 사용자가 입력한 값을 `{문제검증인터뷰수}`로 사용합니다. 미입력 시 기본값 10을 적용합니다.

- **TASK**: 7-1c에서 확정된 문제가설을 기반으로 {문제검증인터뷰수}명 대상 문제검증 인터뷰를 5명이 분담하여 병렬 수행. 각 문제의 중요도/불편도 5점 만점 평가, 근본원인 동의 여부 조사
- **EXPECTED OUTCOME**: `docs/plan/define/문제검증인터뷰결과.md` — {문제검증인터뷰수}명 개별 인터뷰 결과 (중요도/불편도/근본원인 동의여부)
- **MUST DO**: {문제검증인터뷰수}명 인터뷰 결과를 개별 제공. 인터뷰 대상자를 5명으로 균등 분배
- **MUST NOT DO**: 인터뷰 결과를 종합 요약만 하지 않을 것
- **CONTEXT**: `docs/plan/define/문제가설.md`, `docs/plan/define/고객분석.md`
- **실행**: 5개 에이전트를 `Task(run_in_background=true)`로 동시 실행, 각 에이전트가 분담된 인터뷰 수만큼 수행 후 결과를 하나의 파일로 병합

#### Step 7-3. 인터뷰 결과 취합 (순차) → Agent: service-planner

- **TASK**: 7-2에서 수집된 전체 인터뷰 결과를 종합 분석. 문제별 중요도/불편도 평균, 근본원인 동의율 집계, 핵심 인사이트 도출
- **EXPECTED OUTCOME**: `docs/plan/define/문제검증인터뷰결과취합.md` — 인터뷰 결과 종합 취합 (문제별 통계, 근본원인 검증 결과, 핵심 인사이트)
- **MUST DO**: 정량 데이터(평균, 동의율)와 정성 데이터(주요 의견) 모두 포함
- **CONTEXT**: `docs/plan/define/문제검증인터뷰결과.md`

#### Step 7-4. 문제가설 피보팅 (순차) → Agent: product-owner

- **TASK**: 7-3의 인터뷰 결과 취합을 반영하여 문제가설을 수정. 검증 결과 중요도/불편도가 낮거나 근본원인 동의율이 낮은 항목을 조정하고, 인터뷰에서 새로 발견된 문제를 반영
- **EXPECTED OUTCOME**: `docs/plan/define/문제가설.md` — 피보팅된 문제가설 (기존 파일 덮어쓰기). 변경 사항과 피보팅 근거를 파일 상단에 명시
- **MUST DO**: 피보팅 전후 변경 내역을 명확히 기술. 검증 데이터 기반 의사결정
- **MUST NOT DO**: 검증 결과를 무시하고 기존 가설을 유지하지 않을 것
- **CONTEXT**: `docs/plan/define/문제가설.md` (7-1c 버전), `docs/plan/define/문제검증인터뷰결과취합.md`

#### Step 7-5. 비즈니스 가치 도출 (발산-수렴-선택)

**7-5a. 발산 — 가치 도출 (병렬)** → Agent: product-owner, service-planner, domain-expert, architect, ai-engineer

- **TASK**: 피보팅된 문제가설의 근본원인 해소 시 고객·회사 각각의 비즈니스 가치를 자신의 전문 관점에서 도출
- **EXPECTED OUTCOME**: 팀원별 비즈니스 가치 후보 (고객 측면 + 회사 측면)
- **MUST DO**: 각 팀원의 전문성을 반영한 관점 차별화. 정량적 가치와 정성적 가치 모두 포함
- **CONTEXT**: `docs/plan/define/문제가설.md` (피보팅 버전), `docs/plan/define/문제검증인터뷰결과취합.md`
- **실행**: 5개 에이전트를 `Task(run_in_background=true)`로 동시 실행

**7-5b. 수렴 — 유사 항목 합치기 (순차)** → Agent: service-planner

- **TASK**: 5명의 비즈니스 가치 후보를 취합하고 유사한 가치를 그룹핑하여 정리
- **EXPECTED OUTCOME**: 수렴된 비즈니스 가치 후보 목록 (고객 측면 + 회사 측면, 출처 팀원 표기)
- **MUST DO**: 모든 팀원의 결과를 누락 없이 반영
- **CONTEXT**: 7-5a 결과

**7-5c. 선택 — 최종 비즈니스 가치 확정 (순차)** → Agent: product-owner

- **TASK**: 수렴된 후보 중 고객·회사 각각 가장 중요한 비즈니스 가치 3개 이하를 선정하여 확정
- **EXPECTED OUTCOME**: `docs/plan/define/비즈니스가치.md` — 고객/회사 측면 비즈니스 가치 (각 3개 이하, 선정 근거 포함)
- **MUST DO**: 선정 근거를 명확히 기술. 측정 가능한 지표와 연결
- **CONTEXT**: 7-5b 수렴 결과

> **전체 산출물**: `문제가설.md` (피보팅 최종본), `문제검증인터뷰결과.md`, `문제검증인터뷰결과취합.md`, `비즈니스가치.md`

### Step 8. 방향성 정의 → Agent: product-owner (`/oh-my-claudecode:plan` 활용)

- **GUIDE**: `resources/guides/plan/08-direction-setting-guide.md` 참조
- **TASK**: 2단계 작업을 수행
  1. **킹핀 문제 발견**: 검증된 문제들을 영향력·빈도·심각도·근본성·해결가능성 5가지 기준(각 5점)으로 평가하고, 문제 간 인과관계를 분석하여 킹핀 문제(해결하면 다른 문제들이 연쇄 해결되는 핵심 문제) 선정
  2. **Needs Statement 작성**: `'<고객유형>는 <목적>을 위하여 <원하는 것>이 필요하다.'` 형식으로 한 문장의 방향성 정의. 기능이 아닌 경험으로 표현
- **EXPECTED OUTCOME**: 2개 파일 생성
  - `docs/plan/think/킹핀문제.md` — 검증된 문제 리스트, 인과관계, 5가지 기준 평가, 킹핀 문제 선정
  - `docs/plan/think/문제해결방향성.md` — Needs Statement, 상세 설명 (고객유형, 목적, 원하는 것)
- **MUST DO**: 킹핀 문제는 객관적 데이터 기반 결정. Needs Statement는 솔루션이 아닌 방향성. 하나의 문장으로 표현
- **MUST NOT DO**: 감정적 판단으로 킹핀 문제 결정 금지. 구체적 솔루션을 방향성에 포함 금지
- **CONTEXT**: `docs/plan/define/문제가설.md`, `docs/plan/define/문제검증인터뷰결과취합.md`, `docs/plan/define/비즈니스가치.md`, `docs/plan/define/고객분석.md`

---

## 3단계: 솔루션 (Solution)

### Step 9. 아이디어 발상 → Agent: product-owner, service-planner(리드), domain-expert, architect, ai-engineer, backend-developer, frontend-developer, qa-engineer, devops-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/plan/09-ideation-guide.md` 참조
- **TASK**: 2단계 작업을 수행
  1. **솔루션 탐색 (병렬)**: 모든 팀원(9명)이 SCAMPER 기법과 Steal & Synthesize 기법을 활용하여 각자 Big Idea 3개, Little Win Idea 2개, Crazy Idea 1개를 도출. 각자의 전문성을 내려놓고 사용자 입장에서 아이디어 발상
  2. **솔루션 수렴 (순차, service-planner)**: 아이디어 유사도 평가표(기능 유사도 70%, 경험 유사도 30%)를 작성하고 유사도 0.7 이상인 아이디어를 합쳐 솔루션 후보 정리
- **EXPECTED OUTCOME**: 2개 파일 생성
  - `docs/plan/think/솔루션탐색.md` — 팀원별 아이디어 표 (Big Idea/Little Win Idea/Crazy Idea)
  - `docs/plan/think/솔루션후보.md` — 유사도 평가 후 수렴된 솔루션 후보 (각 후보 상세 설명)
- **MUST DO**: SCAMPER 7가지 관점 체계적 적용. Steal & Synthesize로 타 산업 사례 최소 3개 분석. 아이디어 설명은 최대한 자세하게
- **MUST NOT DO**: 초기 생성 시 자기 검열 금지. 유사도 0.7 미만 아이디어를 강제 합치지 않을 것
- **CONTEXT**: `docs/plan/define/문제가설.md`, `docs/plan/think/킹핀문제.md`, `docs/plan/think/문제해결방향성.md`, 고객 경험 조사 데이터
- **실행**: 솔루션 탐색은 9개 에이전트를 `Task(run_in_background=true)`로 동시 실행, 솔루션 수렴은 service-planner가 순차 수행

### Step 10. 솔루션 선정 → Agent: product-owner(리드), service-planner, domain-expert, architect, ai-engineer, backend-developer, frontend-developer, qa-engineer, devops-engineer (`/oh-my-claudecode:plan` 활용)

- **GUIDE**: `resources/guides/plan/10-solution-selection-guide.md` 참조
- **TASK**: 2단계 작업을 수행
  1. **우선순위 평가 — 투표 (병렬)**: 모든 팀원(9명)이 각각 비즈니스 가치(B) 3표, 실현 가능성(F) 3표를 투표
  2. **솔루션 선정 — 우선순위 매트릭스 (순차, product-owner)**: 투표 결과를 집계하고 X축=실현가능성, Y축=비즈니스 영향도의 2x2 매트릭스(No Brainers/Bit Bets/Utilities/Unwise)로 시각화하고 핵심 솔루션 3개 이하 선정
- **EXPECTED OUTCOME**: 3개 파일 생성
  - `docs/plan/think/솔루션평가.md` — 투표 결과 집계표
  - `docs/plan/think/솔루션우선순위평가.svg` — 우선순위 매트릭스 SVG
  - `docs/plan/think/핵심솔루션.md` — 선정된 핵심 솔루션 (3개 이하, 상세 설명 포함)
- **MUST DO**: No Brainers 영역 아이디어 우선 선정. 핵심 솔루션 3개 이하. SVG 파일로 매트릭스 생성
- **MUST NOT DO**: 투표 없이 직감으로 선정 금지
- **CONTEXT**: `docs/plan/think/솔루션후보.md`
- **실행**: 투표는 9개 에이전트를 `Task(run_in_background=true)`로 동시 실행, 집계 및 선정은 product-owner가 순차 수행

---

## 4단계: 비즈니스 모델 (Business Model)

### Step 11. 비즈니스 모델 설계 → Agent: product-owner (`/oh-my-claudecode:plan` 활용)

- **GUIDE**: `resources/guides/plan/11-business-modeling-guide.md` 참조
- **TASK**: Lean Canvas 프레임워크를 사용하여 체계적인 비즈니스 모델 설계. Problem, Customer Segments, UVP, Solution, Channels, Revenue Streams, Cost Structure, Key Metrics(AARRR), Unfair Advantage 9개 영역과 경쟁 분석, Go-to-Market 전략, 재무 계획(3개년 손익계산서, BEP) 포함
- **EXPECTED OUTCOME**: `docs/plan/think/비즈니스모델.md` 생성
  - Lean Canvas 9개 영역 전체
  - 가격 전략, LTV, 수익 전망(3개년)
  - 비용 구조(고정비/변동비), BEP
  - Key Metrics (CAC, ARPU, MRR, Churn, 바이럴 계수)
  - 경쟁 매트릭스 및 포지셔닝
  - Go-to-Market 전략 (Pre-launch/Launch/Post-launch)
  - 재무 계획 (3개년 손익계산서, 자금 조달 계획)
- **MUST DO**: Lean Canvas 9개 영역 모두 작성. 수익 모델은 구체적이고 측정 가능하게. BEP 시점 명시
- **MUST NOT DO**: 비현실적인 재무 추정 금지. Unfair Advantage에 일반적 기능을 작성 금지
- **CONTEXT**: `docs/plan/think/핵심솔루션.md`, `docs/plan/define/고객분석.md`, `docs/plan/define/문제가설.md`

### Step 12. 발표자료 스크립트 → Agent: service-planner (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/plan/12-presentation-guide.md` 참조
- **TASK**: 비즈니스 모델을 기반으로 서비스 기획서 발표자료 스크립트 작성. 린캔버스 9영역 + 경쟁 분석 + GTM 전략 + 재무 계획을 10-15장으로 구성. 각 장표별 핵심 메시지 3개 이하
- **EXPECTED OUTCOME**: `docs/plan/think/서비스기획서스크립트.md` 생성
  - 10-15장 슬라이드 스크립트
  - 각 장표 핵심 메시지 3개 이하
  - 장표 간 `---` 구분
  - 장표별 비주얼 제안 (차트·그래프·다이어그램) 포함
- **MUST DO**: 문제 → 솔루션 → 가치의 스토리텔링 흐름. 데이터 기반 주장 뒷받침. 비주얼 중심 — 텍스트 최소화하고 비주얼로 설명
- **MUST NOT DO**: 텍스트 과다 금지. 슬라이드당 핵심 메시지 3개 초과 금지. 데이터 없는 추상적 주장 금지
- **CONTEXT**: `docs/plan/think/비즈니스모델.md`

---

## 5단계: 제품 설계 (Product Design)

### Step 13. 이벤트 스토밍 → Agent: architect(리드), product-owner, service-planner, domain-expert, ai-engineer, backend-developer, frontend-developer, qa-engineer, devops-engineer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/plan/13-event-storming-guide.md` 참조
- **실행 방식**: 3단계(초안-리뷰-반영)로 수행합니다.

#### Step 13-1. 초안 작성 (순차) → Agent: architect

- **TASK**: DDD(Domain-Driven Design)의 Event Storming 기법으로 핵심 솔루션의 시스템 이벤트 흐름을 분석하고 PlantUML 시퀀스 다이어그램으로 작성
  1. 주요 유저플로우 식별 (5-10개)
  2. 유저플로우 간 연결도 작성
  3. 각 유저플로우별 시퀀스 다이어그램 작성 (이벤트 스토밍 요소 명시: [이벤트], [커맨드], [정책/규칙], [데이터])
  4. 마이크로서비스 정의 (이벤트 클러스터링 → Aggregate 식별 → 바운디드 컨텍스트 → 컨텍스트 맵핑 → 분할/병합 결정)
- **EXPECTED OUTCOME**: 다수 파일 생성
  - `docs/plan/think/es/userflow.puml` — 유저플로우 연결도
  - `docs/plan/think/es/{순번}-{유저플로우명}.puml` — 각 유저플로우 시퀀스 다이어그램
- **MUST DO**: `!theme mono` 사용. 한국어로 작성. 참여자는 Actor/내부서비스/외부시스템으로 구성. 외부시스템은 `(E){시스템명}` 표시. 이벤트는 과거형, 커맨드는 명령형. **각 `.puml` 파일 생성 즉시 `bash tools/diagram/check-plantuml.sh {파일경로}`로 PlantUML 문법 검사 수행** (`resources/tools/check-plantuml.md` 참조)
- **MUST NOT DO**: 내부서비스·외부시스템 내부 플로우는 표시하지 않을 것. 문법 검사 미통과 파일을 남기지 않을 것
- **CONTEXT**: `docs/plan/think/핵심솔루션.md`, `docs/plan/define/고객분석.md`, `docs/plan/define/시장조사.md`, `docs/plan/define/유저저니맵.md`

#### Step 13-2. 팀 리뷰 (병렬) → Agent: product-owner, service-planner, domain-expert, ai-engineer, backend-developer, frontend-developer, qa-engineer, devops-engineer

- **TASK**: 13-1에서 작성된 이벤트 스토밍 초안을 각자의 전문성 관점에서 리뷰하고 의견을 제시
  - **product-owner**: 비즈니스 가치·MVP 범위 관점에서 누락된 유저플로우나 이벤트 확인
  - **service-planner**: 사용자 경험·서비스 흐름 관점에서 유저플로우 완성도 검토
  - **domain-expert**: 도메인 규칙·규제·업계 관행 관점에서 정책/규칙 검증
  - **ai-engineer**: AI 기회 발굴 — AI/ML 적용 가능한 이벤트·데이터 흐름 식별, AI 자동화·지능화 기회 제안
  - **backend-developer**: 백엔드 구현 가능성·API 설계·데이터 처리 관점에서 기술적 타당성 검토
  - **frontend-developer**: 사용자 인터랙션·화면 흐름 관점에서 프론트엔드 구현 이슈 식별
  - **qa-engineer**: 테스트 용이성·예외 시나리오·경계값 관점에서 누락된 케이스 식별
  - **devops-engineer**: 배포·운영·확장성 관점에서 서비스 분할 및 인프라 이슈 검토
- **EXPECTED OUTCOME**: `docs/plan/think/es/리뷰의견.md` — 팀원별 리뷰 의견 (관점, 의견, 수정 제안)
- **MUST DO**: 각 팀원은 자신의 전문성 관점에서만 의견 제시. 구체적인 수정 제안 포함
- **CONTEXT**: `docs/plan/think/es/userflow.puml`, `docs/plan/think/es/*.puml`
- **실행**: 8개 에이전트를 `Task(run_in_background=true)`로 동시 실행

#### Step 13-3. 의견 반영 및 업데이트 (순차) → Agent: architect

- **TASK**: 13-2에서 수집된 팀 리뷰 의견을 검토하고, 타당한 의견을 반영하여 이벤트 스토밍 산출물 업데이트
- **EXPECTED OUTCOME**: 기존 `docs/plan/think/es/*.puml` 파일 업데이트 (반영 사항 주석 추가)
- **MUST DO**: 각 의견에 대한 반영/미반영 판단 근거를 `docs/plan/think/es/리뷰반영결과.md`에 기록. 특히 ai-engineer의 AI 기회 발굴 의견을 별도 섹션으로 정리
- **CONTEXT**: `docs/plan/think/es/리뷰의견.md`, 기존 이벤트 스토밍 산출물

### Step 14. 유저스토리 작성 → Agent: service-planner(리드), product-owner, architect, ai-engineer, domain-expert (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/plan/14-user-stories-guide.md` 참조
- **실행 방식**: 3단계(초안-리뷰-반영)로 수행합니다.

#### Step 14-1. 초안 작성 (순차) → Agent: service-planner

- **TASK**: 이벤트 스토밍 결과를 기반으로 체계적인 유저스토리 작성
  - 유저플로우 → Epic 변환
  - 이벤트 → User Story 변환 (`{사용자유형}으로서 | 나는, {목적}을 위해 | {이벤트/결과}를 원한다.`)
  - 커맨드 → 시나리오/Task 변환
  - 정책/규칙 → Acceptance Criteria 변환
  - UFR(User Functional Requirement) 포맷: `UFR-{서비스약어}-{번호}`
  - 시나리오 기반 상세 요구사항 ([입력 요구사항], [검증 요구사항], [처리 결과])
  - 우선순위 표기: M(Must)/S(Should)/C(Could) + Story Points(피보나치)
  - Feature Story Map, 우선순위 매트릭스, 스프린트 계획
  - 비기능적 요구사항 (성능, 보안, 사용성, 확장성)
  - Definition of Done, 리스크 및 의존성
- **EXPECTED OUTCOME**: `docs/plan/design/userstory.md` 생성
  - 마이크로서비스별 유저스토리 (최소 20개 UFR)
  - 사용자 역할 정의
  - Feature Story Map
  - 우선순위 매트릭스 (Must/Should/Could/Won't Have)
  - 스프린트 계획 (MVP 기준)
  - 비기능적 요구사항, Definition of Done, 리스크
- **MUST DO**: UFR 포맷 준수. 일련번호 010부터 10씩 증가. 최소 20개 이상 UFR. INVEST 원칙 준수. Event Storming 결과와 체계적 연계
- **MUST NOT DO**: 이벤트 스토밍 결과 없이 유저스토리 작성 금지. Should Have를 Must Have로 격상 금지
- **CONTEXT**: `docs/plan/think/es/*.puml`, `docs/plan/think/핵심솔루션.md`, `docs/plan/define/고객분석.md`

#### Step 14-2. 검토 (병렬) → Agent: product-owner, architect, ai-engineer, domain-expert

- **TASK**: 14-1에서 작성된 유저스토리 초안을 각자의 전문성 관점에서 검토하고 의견을 제시
  - **product-owner**: MVP 범위·비즈니스 우선순위 관점에서 우선순위(M/S/C) 적절성 검토, 누락된 비즈니스 요구사항 식별
  - **architect**: 기술 실현 가능성·시스템 아키텍처 관점에서 Story Points 적절성 검토, 기술적 의존성·제약 사항 식별
  - **ai-engineer**: AI/ML 적용 가능한 유저스토리 식별, AI 기능 관련 UFR 누락 여부 확인, AI 연동 요구사항 보완 제안
  - **domain-expert**: 도메인 규칙·규제·업계 관행 관점에서 Acceptance Criteria 검증, 도메인 특화 요구사항 누락 확인
- **EXPECTED OUTCOME**: `docs/plan/design/userstory-리뷰의견.md` — 검토자별 의견 (관점, 의견, 수정 제안)
- **MUST DO**: 각 검토자는 자신의 전문성 관점에서만 의견 제시. 구체적인 수정 제안 포함
- **CONTEXT**: `docs/plan/design/userstory.md`, `docs/plan/think/es/*.puml`
- **실행**: 4개 에이전트를 `Task(run_in_background=true)`로 동시 실행

#### Step 14-3. 의견 반영 및 업데이트 (순차) → Agent: service-planner

- **TASK**: 14-2에서 수집된 검토 의견을 반영하여 유저스토리 업데이트
- **EXPECTED OUTCOME**: `docs/plan/design/userstory.md` 업데이트 (기존 파일 덮어쓰기)
- **MUST DO**: 각 의견에 대한 반영/미반영 판단 근거를 `docs/plan/design/userstory-리뷰반영결과.md`에 기록. 최종 UFR 개수가 최소 20개 이상 유지되는지 확인
- **CONTEXT**: `docs/plan/design/userstory-리뷰의견.md`, 기존 유저스토리

### Step 15. UI/UX 설계 → Agent: service-planner (`/oh-my-claudecode:ralph` 활용)

<!--ASK_USER-->
{"title":"디자인 레퍼런스 입력 (선택)","questions":[
  {"question":"참고할 디자인 레퍼런스(추천: https://wwit.design)가 있으시면 제공해 주세요. URL, 이미지 경로, 이미지 붙여넣기 모두 가능합니다. 없으면 '없음'을 입력해 주세요.","type":"text","placeholder":"없음"}
]}
<!--/ASK_USER-->

- 사용자가 **URL을 제공한 경우**: 아래 레퍼런스 분석 워크플로우 실행 후 UI/UX 설계 진행
- 사용자가 **이미지를 제공한 경우**: `docs/plan/design/uiux/references/`에 저장하고 Vision 에이전트로 디자인 분석
- 사용자가 '없음' 또는 미응답 시: 레퍼런스 없이 진행

#### Step 15-R. 레퍼런스 사이트 디자인 분석 (URL 제공 시에만 실행)

1. **Playwright로 사이트 접속 및 스크린샷 촬영**
   - 데스크톱 뷰포트(1280x800)로 주요 페이지 스크린샷 촬영
   - 모바일 뷰포트(375x812)로 동일 페이지 스크린샷 촬영
   - 스크린샷을 `docs/plan/design/uiux/references/`에 저장
2. **Playwright accessibility snapshot으로 페이지 구조 파악**
   - 네비게이션 구조, 컴포넌트 계층, 폼 요소 등 구조 정보 수집
3. **Vision 에이전트로 디자인 분석**
   - 촬영된 스크린샷을 `oh-my-claudecode:vision` 에이전트에 전달
   - 분석 항목: 컬러 팔레트, 레이아웃 패턴, 타이포그래피, 컴포넌트 스타일, 간격 시스템, 인터랙션 패턴
4. **분석 결과 정리**
   - `docs/plan/design/uiux/references/레퍼런스분석.md`에 분석 결과 저장
   - 이 파일을 후속 UI/UX 설계의 CONTEXT에 포함

- **GUIDE**: `resources/guides/plan/15-uiux-design-guide.md` 참조
- **TASK**: 유저스토리를 기반으로 상세한 UI/UX 디자인 명세 작성 (레퍼런스 분석 결과가 있는 경우 디자인 톤·레이아웃·컴포넌트 스타일을 참고하여 반영)
  - 디자인 원칙 (핵심 원칙 5개, 디자인 언어)
  - 정보 아키텍처 (사이트맵, 네비게이션 구조)
  - 사용자 플로우 (각 기능별 화면 흐름도)
  - 와이어프레임 (최소 5개 주요 화면, ASCII 아트)
  - 컴포넌트 라이브러리 (버튼, 폼, 카드, 네비게이션, 피드백)
  - 접근성 (WCAG 2.1 AA)
  - 스타일 가이드 (컬러 팔레트, 타이포그래피, 간격 시스템, 아이콘, 반응형)
  - 인터랙션 디자인 (애니메이션, 마이크로 인터랙션)
- **EXPECTED OUTCOME**: 2개 파일 생성
  - `docs/plan/design/uiux/uiux.md` — UI/UX 디자인 명세 전체
  - `docs/plan/design/uiux/style-guide.md` — 스타일 가이드
- **MUST DO**: Mobile First 접근. 최소 5개 주요 화면 와이어프레임. 유저스토리와 일대일 매핑. 컴포넌트 일관성 보장
- **MUST NOT DO**: 유저스토리에 없는 화면 디자인 금지. 스타일 가이드 없이 UI 설계 금지
- **CONTEXT**: `docs/plan/design/userstory.md`, `docs/plan/design/uiux/references/레퍼런스분석.md` (있는 경우)

---

## 6단계: 프로토타입 (Prototype)

### Step 16. 프로토타입 개발 → Agent: frontend-developer (`/oh-my-claudecode:ralph` 활용)

<!--ASK_USER-->
{"title":"이미지 생성용 Gemini API Key (선택)","questions":[
  {"question":"프로토타입에 이미지가 필요한 경우 AI로 생성할 수 있습니다. Gemini API Key를 입력해 주세요. 없으면 '없음'을 입력하세요. (https://aistudio.google.com/apikey 에서 발급)","type":"text","placeholder":"없음"}
]}
<!--/ASK_USER-->

- 사용자가 API Key를 제공한 경우: `.npd/.env` 파일에 `GEMINI_API_KEY={입력값}` 저장 (`.npd/`는 `.gitignore`에 포함되어 git에 업로드되지 않음)
- 사용자가 '없음' 또는 미응답 시: 이미지 없이 진행 (placeholder 텍스트 사용)

- **GUIDE**: `resources/guides/plan/16-prototype-development-guide.md` 참조
- **CONTEXT**: `docs/plan/design/uiux/uiux.md`, `docs/plan/design/uiux/style-guide.md`, `docs/plan/design/userstory.md`
- **EXPECTED OUTCOME**: `docs/plan/design/uiux/prototype/` 디렉토리에 파일 생성
  - `common.js` — 공통 JavaScript (Web Components 공통 UI, 샘플 데이터, 화면 전환, localStorage 유틸리티)
  - `common.css` — 공통 CSS (스타일가이드 CSS 변수화, Mobile First)
  - `{2자리번호}-{한글화면명}.html` — 각 화면 파일 (공통 UI는 Web Components 사용, `<main>` 안에 고유 콘텐츠만 작성)
- **MUST DO**: HTML/JS만 사용 (프레임워크 금지, Web Components는 웹 표준으로 허용). 서버 없이 동작. 스타일가이드 준수. Mobile First. Playwright로 화면별 즉시 테스트
- **MUST NOT DO**: SPA 방식 구현 금지. 설계서에 없는 화면 추가 금지

#### Step 16-1. 공통 파일 개발 (순차)

- **TASK**: 스타일가이드를 기반으로 공통 파일 개발
  1. `common.css` — 스타일가이드의 컬러·타이포그래피·간격을 CSS 변수로 정의, Mobile First 레이아웃, 접근성 유틸리티
  2. `common.js` — Web Components로 공통 UI 컴포넌트 정의 (헤더, 푸터, 네비게이션 등), 샘플 데이터, 화면 전환, localStorage 기반 데이터 전달, 폼 자동 저장/복원

#### Step 16-2. 화면별 개발-테스트 루프 (ralph 활용)

##### 의존관계 분석 및 병렬 개발

UI/UX 설계서의 사용자 플로우를 분석하여 화면 간 의존관계를 파악하고, 독립적인 화면은 병렬로 개발함.

1. **의존관계 분석**: 사용자 플로우에서 화면 간 의존관계를 도출
   - 독립 화면: 다른 화면의 데이터/상태에 의존하지 않는 화면 (예: 로그인, 회원가입, 소개)
   - 의존 화면: 이전 화면의 결과가 필요한 화면 (예: 목록→상세, 장바구니→결제)
2. **개발 레벨 그룹핑**: 의존관계가 없는 화면끼리 같은 레벨로 그룹화
   ```
   Level 1: [로그인] [회원가입] [소개]     ← 병렬 개발
   Level 2: [메인홈] [마이페이지]           ← Level 1 완료 후 병렬 개발
   Level 3: [상세] [결제]                  ← Level 2 완료 후 병렬 개발
   ```
3. **병렬 개발**: 같은 레벨의 화면들을 병렬 에이전트로 동시 개발 → 각 에이전트가 개발-테스트 사이클 수행
4. **레벨 순차 진행**: 현재 레벨의 모든 화면 완료 후 다음 레벨로 진행

##### 화면 1개당 개발-테스트 사이클

1. **개발**: UI/UX 설계서의 와이어프레임과 일대일 매핑하여 HTML 작성
2. **Playwright 즉시 테스트**:
   - `browser_navigate`로 해당 HTML 파일 열기
   - `browser_console_messages`로 콘솔 에러 확인 → 에러 있으면 즉시 수정
   - `browser_snapshot`으로 접근성 구조 확인
   - `browser_take_screenshot`으로 UI 렌더링 상태 확인 (캡처 이미지는 `.temp` 디렉토리에 저장)
   - 모바일 뷰포트(`browser_resize` 375x812)로 반응형 확인 (캡처 이미지는 `.temp` 디렉토리에 저장)
3. **수정**: 에러/UI 이슈 발견 시 수정 후 재테스트
4. **완료**: 테스트 통과 후 해당 화면 완료 처리

#### Step 16-3. 통합 테스트 (Playwright 자동 검증)

모든 화면 개발 완료 후, Playwright로 전체 프로토타입을 자동 검증함.

> **캡처 이미지 저장 경로**: 통합 테스트 중 촬영하는 모든 스크린샷은 `.temp` 디렉토리에 저장합니다.

1. **화면간 연결성 테스트**: 각 화면의 모든 링크/버튼을 `browser_click`으로 클릭 → 올바른 페이지로 이동하는지 확인
2. **화면별 기능 동작 테스트**: 폼 입력(`browser_type`), 버튼 클릭, 모달/드롭다운 동작 확인
3. **데이터 일관성 테스트**: 화면 간 전달되는 샘플 데이터가 일치하는지 확인
4. **반응형 테스트**: 데스크톱(1280x800) → 태블릿(768x1024) → 모바일(375x812)로 뷰포트 변경하며 레이아웃 확인 (각 뷰포트 스크린샷은 `.temp` 디렉토리에 저장)
5. **콘솔 에러 전수 검사**: 모든 화면에서 `browser_console_messages` 에러 레벨 확인

테스트 결과를 `docs/plan/design/uiux/prototype/테스트결과.md`에 기록:
```
### 화면별 기능 동작
| 화면 | 기능/액션 | 예상 결과 | 실제 결과 | 상태 |
### 화면간 연결성
| 출발화면 | 연결방법 | 도착화면 | 상태 |
### 화면간 데이터 일관성
| 데이터 | 사용 화면 | 일관성 |
```

#### Step 16-4. 버그 수정 루프 (ralph 활용)

Step 16-3에서 발견된 실패 항목을 수정 → 재테스트 → 모두 통과할 때까지 반복함.

1. 테스트결과.md의 실패/비정상 항목 확인
2. 해당 HTML 파일 수정
3. Playwright로 수정된 항목만 재테스트
4. 모든 항목 통과 시 완료, 미통과 시 1번으로 복귀

### Step 17. 사용자 플로우 프리젠테이션 → Agent: frontend-developer (`/oh-my-claudecode:ralph` 활용)

- **GUIDE**: `resources/guides/plan/17-flow-presentation-guide.md` 참조
- **TASK**: 프로토타입 화면 스크린샷을 캡처하고, 사용자 플로우 순서대로 화면을 보여주는 인터랙티브 HTML 프리젠테이션을 개발
  1. **화면 캡처**: Playwright로 각 프로토타입 화면에 접속하여 스크린샷 촬영. 각 이미지에 일련번호와 한글 자막 오버레이를 주입 (하단 고정, 빨간 구분선 + 다크 그라디언트 배경 + 흰색 제목 + 회색 설명)
  2. **플로우 구성**: 테스트결과.md의 화면간 연결성 데이터를 분석하여 주요 사용자 플로우를 도출 (예: 신규 온보딩, 일정 모니터링, 브리핑 확인, 장소 추가, 설정/구독 등 3-5개 플로우)
  3. **프리젠테이션 개발**: 3단 레이아웃(좌측 스텝 리스트 / 중앙 폰 프레임 스크린샷 / 우측 나레이션 패널)의 인터랙티브 HTML 파일 작성
     - 플로우 탭으로 플로우 간 전환
     - 키보드(←/→) 및 클릭으로 스텝 이동
     - 각 스텝별 사용자 액션 설명 + 나레이션 텍스트 포함
     - 진행 추적 (방문 스텝 체크마크, 프로그레스 바)
     - 프로토타입과 동일한 다크 테마
     - 반응형 대응 (데스크톱 3단 / 태블릿 2단 / 모바일 1단)
  4. **Playwright 검증**: 프리젠테이션 파일을 브라우저에서 열어 정상 로드, 네비게이션 동작, 스크린샷 표시를 확인
- **EXPECTED OUTCOME**: 2가지 산출물 생성
  - `docs/plan/design/uiux/prototype/screenshots/{번호}-{화면명}.png` — 자막 포함 화면별 스크린샷
  - `docs/plan/design/uiux/prototype/flow-script.html` — 사용자 플로우 인터랙티브 프리젠테이션
- **MUST DO**: 프로토타입의 모든 화면(14개)을 스크린샷으로 포함. 화면간 연결성 데이터 기반으로 플로우 구성. 각 스텝마다 나레이션 텍스트 포함. Playwright로 최종 검증
- **MUST NOT DO**: 프로토타입에 없는 화면을 포함하지 않을 것. 화면간 연결성 데이터에 없는 플로우를 임의로 만들지 않을 것
- **CONTEXT**: `docs/plan/design/uiux/prototype/테스트결과.md`, `docs/plan/design/uiux/uiux.md`, `docs/plan/design/uiux/prototype/*.html`

### Step 18. 기획 완료 보고

```
## 기획 완료

### 생성된 산출물

#### define/ (정의 단계)
- docs/plan/define/MVP정의.md — MVP 주제 정의
- docs/plan/define/고객분석.md — 고객 분석 (JTBD)
- docs/plan/define/시장조사.md — 시장 조사
- docs/plan/define/고객경험단계.md — 고객경험 단계
- docs/plan/define/관찰결과.md — 관찰 조사 결과
- docs/plan/define/체험결과.md — 체험 조사 결과
- docs/plan/define/고객경험인터뷰결과.md — 고객 경험 인터뷰 결과
- docs/plan/define/고객경험인터뷰결과취합.md — 인터뷰 결과 취합
- docs/plan/define/유저저니맵.md — 고객 여정 맵
- docs/plan/define/유저저니맵.svg — 고객 여정 맵 시각화
- docs/plan/define/문제가설.md — 문제 가설 및 5WHY 분석
- docs/plan/define/문제검증인터뷰결과.md — 문제 검증 인터뷰
- docs/plan/define/문제검증인터뷰결과취합.md — 문제 검증 취합
- docs/plan/define/비즈니스가치.md — 비즈니스 가치

#### think/ (사고 단계)
- docs/plan/think/킹핀문제.md — 킹핀 문제 분석
- docs/plan/think/문제해결방향성.md — Needs Statement
- docs/plan/think/솔루션탐색.md — 솔루션 탐색 (팀원별)
- docs/plan/think/솔루션후보.md — 솔루션 후보 (수렴)
- docs/plan/think/솔루션평가.md — 솔루션 투표 평가
- docs/plan/think/솔루션우선순위평가.svg — 우선순위 매트릭스
- docs/plan/think/핵심솔루션.md — 핵심 솔루션
- docs/plan/think/비즈니스모델.md — 비즈니스 모델 (Lean Canvas)
- docs/plan/think/서비스기획서스크립트.md — 발표자료 스크립트
- docs/plan/think/es/userflow.puml — 유저플로우 연결도
- docs/plan/think/es/{순번}-{유저플로우명}.puml — 시퀀스 다이어그램

#### design/ (설계 단계)
- docs/plan/design/userstory.md — 유저스토리
- docs/plan/design/uiux/uiux.md — UI/UX 설계
- docs/plan/design/uiux/style-guide.md — 스타일 가이드
- docs/plan/design/uiux/prototype/*.html — 프로토타입
- docs/plan/design/uiux/prototype/screenshots/*.png — 화면 캡처 (자막 포함)
- docs/plan/design/uiux/prototype/flow-script.html — 사용자 플로우 프리젠테이션

### 다음 단계
`/npd:design` 으로 기술 설계를 시작하세요.
```

---

## 실행 지침

### 순차적 처리
- 다음 단계로 넘어가기 전에 각 스텝을 완료합니다
- 이전 산출물을 다음 스텝의 CONTEXT로 전달합니다
- 진행하기 전에 산출물 파일 생성을 검증합니다

### 진행 상황 보고
각 스텝 완료 후:
- 완료된 스텝 이름
- 생성된 파일 목록
- 다음 스텝 미리보기

### 부분 실행 지원
특정 단계만 실행 가능:
- "1-2단계만 실행해줘" (정의 + 문제 발견)
- "5단계부터 시작해줘" (제품 설계부터)
- "유저스토리만 작성해줘" → Step 14만 실행

### 에러 처리
스텝 실패 시:
1. 에러를 명확히 보고
2. 사용자에게 설명/입력 요청
3. 실패한 스텝 재시도
4. 중단된 지점부터 계속

---

## 완료 조건

- [ ] 모든 워크플로우 단계(6단계 18스텝)가 정상 완료됨
- [ ] 산출물이 `docs/plan/` 하위 디렉토리(define/think/design/)에 생성됨
- [ ] 프로토타입이 `docs/plan/design/uiux/prototype/`에 생성됨
- [ ] 검증 프로토콜을 통과함
- [ ] 에러 0건

## 검증 프로토콜

1. 산출물 파일 존재 확인 (define/, think/, design/ 하위 전체 파일)
2. 산출물 내용 품질 검증 (고객 조사 사용자 입력 규모 충족, UFR 20개 이상, Lean Canvas 9영역)
3. 이전 Phase 산출물과의 일관성 확인 (각 Step의 CONTEXT 체인 연결)

## 상태 정리

완료 시 임시 상태 파일 정리. 산출물은 유지.

## 취소

사용자가 "cancelomc" 또는 "stopomc" 요청 시 현재 단계를 안전하게 중단하고 진행 상태를 보고함.

## 재개

마지막 완료된 Step부터 재시작. 이전 산출물이 존재하면 해당 단계는 건너뜀.
재개 시에도 반드시 **Step 0. 진행 모드 선택**(단계별 승인/자동 진행)을 먼저 수행한 후 이어서 진행.

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | 워크플로우 시작 전 진행 모드(단계별 승인/자동 진행)를 반드시 선택하게 할 것 |
| 2 | '단계별 승인' 모드 시 각 스텝 완료 후 승인 요청을 표시하고 사용자 승인 후 다음 스텝을 진행할 것 |
| 3 | `domain-expert` 에이전트를 시장 조사 및 문제 가설 검토에 반드시 참여시키되, `.npd/domain-context.yaml`을 프롬프트에 주입할 것 |
| 4 | 기획 산출물은 `docs/plan/` 하위 디렉토리(define/think/design/)에 저장할 것 |
| 5 | 각 스텝의 산출물이 다음 스텝의 CONTEXT로 연결되도록 할 것 |
| 6 | 고객 경험 조사는 사용자가 입력한 인터뷰수/관찰수/체험수만큼 생략하지 않고 모두 제공할 것 |
| 7 | 유저스토리는 최소 20개 이상 UFR로 작성할 것 |
| 8 | 이벤트 스토밍은 PlantUML 시퀀스 다이어그램으로 작성할 것 |
| 9 | 프로토타입은 HTML/JS로 화면별 파일 분리하여 작성할 것 |
| 10 | 프로토타입 완료 후 화면 캡처 + 사용자 플로우 프리젠테이션을 생성할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 기획 단계에서 백엔드/프론트엔드 코드를 작성하지 않을 것 (프로토타입 HTML 제외) |
| 2 | 고객 경험 조사 데이터를 축약·생략하지 않을 것 |
| 3 | 솔루션을 문제 가설이나 방향성에 포함하지 않을 것 |
| 4 | 기술 구현 방법을 기획 단계에서 확정하지 않을 것 |

## 검증 체크리스트

### 1단계: 정의
- [ ] MVP정의.md 생성 완료
- [ ] 고객분석.md 생성 완료 (JTBD 형식)
- [ ] 시장조사.md 생성 완료 (TAM/SAM/SOM, SWOT 포함)

### 2단계: 문제 발견
- [ ] 고객경험단계.md 생성 완료 (5-7개 단계)
- [ ] 고객 경험 조사 4개 파일 생성 완료 (사용자 입력 규모대로 모두 제공)
- [ ] 유저저니맵.md + .svg 생성 완료
- [ ] 문제가설.md + 문제검증 결과 + 비즈니스가치 생성 완료

### 3단계: 솔루션
- [ ] 솔루션탐색.md + 솔루션후보.md 생성 완료
- [ ] 솔루션평가.md + 우선순위평가.svg + 핵심솔루션.md 생성 완료

### 4단계: 비즈니스 모델
- [ ] 비즈니스모델.md 생성 완료 (Lean Canvas 9영역)
- [ ] 서비스기획서스크립트.md 생성 완료

### 5단계: 제품 설계
- [ ] 이벤트 스토밍 .puml 파일 생성 완료
- [ ] userstory.md 생성 완료 (UFR 20개 이상)
- [ ] uiux.md + style-guide.md 생성 완료

### 6단계: 프로토타입 + 플로우 스크립트
- [ ] prototype/ 디렉토리에 HTML 파일 생성 완료
- [ ] prototype/screenshots/ 에 자막 포함 스크린샷 생성 완료
- [ ] prototype/flow-script.html 사용자 플로우 프리젠테이션 생성 완료
- [ ] 완료 보고에 다음 단계(/npd:design) 안내 포함
