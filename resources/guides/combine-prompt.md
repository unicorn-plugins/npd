# 프롬프트 조립 가이드

에이전트 호출 시 프롬프트를 조립하는 공통 절차.

## 입력

- **FQN**: SKILL.md의 FQN 테이블에서 확인 (예: `arcana:bd:bd`)
- **사용자 메시지**: 사용자가 입력한 요청

## 조립 절차

### 1단계: 3파일 로드

FQN에서 에이전트 디렉토리를 도출하여 `{NPD_PLUGIN_DIR}/agents/{에이젼트 디렉토리}/` 하위에서 다음 3파일을 로드한다.  

| 파일 | 용도 |
|------|------|
| `AGENT.md` | 프롬프트 본문 (WHY + HOW) |
| `agentcard.yaml` | tier 확인 + persona 정보 |
| `tools.yaml` | 도구 목록 + 제약 조건 |

### 2단계: runtime-mapping 구체화

`{NPD_PLUGIN_DIR}/gateway/runtime-mapping.yaml`을 참조하여 추상 값을 구체 값으로 변환한다:

**모델 구체화**
- agentcard.yaml의 `tier` 값을 `tier_mapping`으로 변환 (우선순위 순서):
  1. `tier_mapping.{에이전트명}.sub_roles.{세부역할명}.{TIER}.model` (세부역할 지정 시)
  2. `tier_mapping.{에이전트명}.{TIER}.model` (에이전트별 예외)
  3. `tier_mapping.default.{TIER}.model` (전역 기본값)
- 예: `tier: MEDIUM` → `claude-sonnet-4-6`

**도구 구체화**
- tools.yaml의 각 추상 도구를 `tool_mapping.{도구명}`으로 변환
- 예: `image_generate` → `tools/generate-image-bridge.py`

**금지액션 구체화**
- agentcard.yaml의 `forbidden_actions` 각 항목을 `action_mapping.{액션}`으로 변환
- 예: `code_execute` → `["Bash"]` 제외

**최종 도구 산출**
```
최종 도구 = (구체화된 도구) - (금지액션에서 도출된 제외 도구)
```

### 3단계: 프롬프트 합성

3파일(AGENT.md + agentcard.yaml + tools.yaml)을 하나의 프롬프트로 합친다.

**세부역할 워크플로우 처리** (agentcard.yaml에 `sub_roles`가 있는 경우):

AGENT.md의 `## 워크플로우` 섹션에 `### {세부역할명}` 서브섹션이 존재할 때,
호출 컨텍스트에 따라 워크플로우 범위를 결정한다:

| 호출 컨텍스트 | 워크플로우 범위 |
|--------------|---------------|
| 특정 세부역할 지정 | 해당 `### {세부역할명}` 서브섹션만 포함 |
| 세부역할 미지정 | `## 워크플로우` 전체 포함 (모든 세부역할 서브섹션) |

**폴백 로직** (3단계):
1. 호출 시 세부역할이 지정되었으면 → 해당 `### {세부역할명}` 서브섹션만 추출하여 프롬프트에 포함
2. 세부역할 미지정이면 → AGENT.md의 `## 워크플로우` 전체를 프롬프트에 포함
3. sub_roles가 없는 에이전트 → 기존과 동일 (워크플로우 전체 포함)

**(중요) domain-expoert 에이젼트 호출 시 반드시 도메인 컨텍스트 주입**:    
`domain-expert` 에이전트 호출 시 `{PROJECT_DIR}/.npd/domain-context.yaml`을 읽어 프롬프트에 포함.   
도메인명, 배경(background), 전문성(expertise), 규제/표준(regulations) 정보를 동적 컨텍스트로 주입하여 도메인 특화 자문을 수행

### 4단계: 인격 주입

agentcard.yaml에 `persona` 섹션이 존재하면, 다음 템플릿으로 인격을 주입한다:

```
당신은 {persona.profile.nickname}입니다.
답변 시 별명 '{persona.profile.nickname}'를 표시하세요.
{persona.style}.
{persona.background}.
```

### 5단계: 프롬프트 구성 완료

최종 프롬프트는 다음 순서로 구성한다.
정적 블록을 앞에 배치하여 반복 호출 시 프롬프트 캐싱이 적용되도록 한다.

```
[정적 — 캐싱 대상]
1. 공통 정적       : runtime-mapping에서 도출된 공통 설정
2. 에이전트별 정적  : 3파일(AGENT.md + agentcard.yaml + tools.yaml) 합성 결과 + 인격 주입

[동적]
3. 사용자 메시지   : 매 호출마다 달라지는 입력 (항상 마지막)
```
