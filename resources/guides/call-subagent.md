# 서브에이전트 호출 가이드

## 개요

런타임별로 서브에이전트를 호출하는 방식이 다름.  
`{PROJECT_DIR}/AGENTS.md`의 `AI_RUNTIME` 값을 확인하여 해당 런타임의 호출 방식을 사용할 것.

| AI_RUNTIME | 호출 방식 |
|------------|----------|
| Claude Code | `Agent` 도구 (subagent_type 파라미터) |
| Claude Cowork | `Agent` 도구 (Claude Code와 동일) |
| Cursor | `cursor/task` ACP 엔드포인트 (네이티브 에이전트) |
| Antigravity | `spawn_agent` 네이티브 도구 |
| Codex | `spawn_agent` 네이티브 도구 |

> **주의**: `claude -p --agent ...` 형태의 Bash 명령은 어떤 런타임에서도 사용하지 않음.

---

## 0. AI_RUNTIME 자동 감지 (스킬 호출 시 필수)

스킬이 호출될 때마다 아래 순서로 현재 런타임을 감지하고 `{PROJECT_DIR}/AGENTS.md`의 `AI_RUNTIME` 값을 업데이트.

### 감지 규칙 (우선순위 순)

| 우선순위 | 감지 조건 | AI_RUNTIME 값 |
|---------|-----------|--------------|
| 1 | `Agent` 도구가 도구 목록에 존재 | `Claude Code` |
| 2 | 시스템 컨텍스트에 "Cowork" 언급 | `Claude Cowork` |
| 3 | `spawn_agent` 도구가 도구 목록에 존재 (Google 환경) | `Antigravity` |
| 4 | `spawn_agent` 도구가 도구 목록에 존재 (OpenAI 환경) | `Codex` |
| 5 | `cursor/task` 엔드포인트 또는 Cursor 특화 도구 존재 | `Cursor` |
| 6 | 감지 불가 | 기존 AGENTS.md 값 유지 |

### 업데이트 절차

```
1. {PROJECT_DIR}/AGENTS.md 읽기
2. 위 감지 규칙으로 현재 런타임 판별
3. 감지값 ≠ 기존 AI_RUNTIME 이면 → Edit 도구로 AGENTS.md 업데이트
4. 감지값 == 기존 값이면 → 스킵 (불필요한 파일 수정 방지)
```

---

## 1. Claude Code / Claude Cowork

`Agent` 도구를 사용하여 서브에이전트 호출.

```
Agent(
  subagent_type = "{FQN}",          // 예: abra:scenario-analyst:scenario-analyst
  model         = "{tier 매핑 결과}", // 예: sonnet
  prompt        = "{조립된 프롬프트}"
)
```

- `subagent_type`: SKILL.md의 FQN 테이블 값
- `model`: `gateway/runtime-mapping.yaml`의 tier → model 매핑 결과
- `prompt`: `combine-prompt.md` 절차에 따라 조립한 최종 프롬프트

**병렬 호출**: 독립적인 에이전트는 단일 메시지에 여러 `Agent` 도구 호출로 동시 실행 가능.

---

## 2. Cursor

Cursor ACP(Agent Communication Protocol)의 `cursor/task` 엔드포인트를 통해 네이티브 에이전트 호출.

```json
POST /cursor/task
{
  "toolCallId": "{고유 ID}",
  "description": "{에이전트 역할 한 줄 설명}",
  "prompt": "{조립된 프롬프트}",
  "subagentType": "unspecified",
  "model": "{tier 매핑 결과}"
}
```

**응답 처리**:
```json
{
  "outcome": {
    "outcome": "completed",
    "agentId": "agent_abc",
    "durationMs": 5000
  }
}
```

- `subagentType`은 일반 에이전트 위임 시 `"unspecified"` 사용
- 이전에 생성된 에이전트를 재개할 경우 `agentId` 파라미터 전달

**클라우드 에이전트 위임** (대화 중 백그라운드 실행):
```bash
& {에이전트에게 위임할 태스크 설명}
```

---

## 3. Antigravity

`spawn_agent` 네이티브 도구를 사용하여 서브에이전트 호출.

```
spawn_agent(
  message = """
Your task is to perform the following. Follow the instructions below exactly.

<agent-instructions>
{조립된 프롬프트}
</agent-instructions>

Execute this now. Output ONLY the structured response following the format
specified in the instructions above.
"""
)
```

**주의사항**:
- 재귀 방지: 서브에이전트에게 "추가 서브에이전트를 생성하지 말 것"을 명시
- 병렬 실행 시 "다른 에이전트가 동시에 작업 중임"을 각 에이전트에게 고지
- 완료 후 `close_agent`로 에이전트 종료

**병렬 호출** (독립 작업):
```
spawn_agent(message="...")  // 에이전트 A
spawn_agent(message="...")  // 에이전트 B (동시 실행)
wait(agents=[A, B])         // 모든 결과 수집 후 진행
```

---

## 4. OpenAI Codex

`spawn_agent` 네이티브 도구를 사용 (Antigravity와 동일 패턴).

```
spawn_agent(
  message = """
Your task is to perform the following. Follow the instructions below exactly.

<agent-instructions>
{조립된 프롬프트}
</agent-instructions>

Execute this now. Output ONLY the structured response following the format
specified in the instructions above.
"""
)
```

**스레드 기반 고급 제어** (App Server API 사용 시):
```json
POST thread/start
{ "model": "gpt-5.4", "cwd": "/path/to/project" }
→ { "thread": { "id": "thr_abc123" } }
```

**주의사항**:
- `close_agent`로 완료된 에이전트 반드시 종료
- `wait_agent`의 `timeout_ms`는 예상 소요 시간 기준으로 여유 있게 설정
- 재귀 방지: 서브에이전트에게 추가 에이전트 생성 금지 명시

---

## 5. 도구명 매핑표

스킬 내 도구 참조명과 런타임별 실제 도구명 매핑:

| 스킬 참조명 | Claude Code / Cowork | Cursor | Antigravity / Codex |
|------------|----------------------|--------|---------------------|
| `Agent` 호출 | `Agent` 도구 | `cursor/task` | `spawn_agent` |
| 병렬 에이전트 | 단일 메시지 다중 `Agent` | 다중 `cursor/task` | 다중 `spawn_agent` + `wait` |
| `TodoWrite` | `TodoWrite` | `TodoWrite` | `update_plan` |
| `Bash` | `Bash` | `Bash` | 네이티브 셸 도구 |
| `Read/Write/Edit` | 동일 | 동일 | 네이티브 파일 도구 |

---
