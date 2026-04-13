# NPD 프로젝트의 Gemini 환경 전환 검토 결과

## 1. 개요
현재 `npd` 프로젝트는 Claude Code 기반의 플러그인(명령어 및 에이전트 협업 체계)으로 작성되어 있습니다. 검토 결과, Gemini 환경(특히 현재 제공되는 Advanced Agentic Coding 및 워크플로우 체계)으로의 **전환은 충분히 가능하며, 아키텍처 및 도구 매핑 측면에서 높은 호환성을 보입니다.**

## 2. 주요 구성요소별 전환 방안 검토

### 2.1. 명령어 및 워크플로우 (Commands & Workflows)
- **현재 (Claude)**: `commands/` 폴더 하위에 `/npd:create`, `/npd:plan` 등의 명령어를 정의하여 사용.
- **Gemini 전환 방안**: 
  - Gemini의 **글로벌 워크플로우(Global Workflows)** 기능으로 1:1 매핑이 가능합니다. (`/orchestrate`, `/plan`, `/setup` 등)
  - `commands/` 하위의 마크다운 파일들을 Gemini의 워크플로우 마크다운 형식으로 변환하여, 사용자가 Gemini 채팅창에서 슬래시 명령어(`/npd-create`)를 통해 호출할 수 있도록 구성하면 됩니다.

### 2.2. 에이전트 협업 체계 (Agent Orchestration)
- **현재 (Claude)**: PO, 기획자, 아키텍트 등 멀티 에이전트가 `Task` 도구 등을 통해 서로 핸드오프하며 파이프라인(기획 $\rightarrow$ 설계 $\rightarrow$ 개발 $\rightarrow$ 배포)을 수행.
- **Gemini 전환 방안**: 
  - Gemini의 `/coordinate`, `/orchestrate` 워크플로우 패턴과 동일합니다. 
  - 서브에이전트를 생성하거나, Gemini CLI를 통해 에이전트를 병렬로 띄우고 MCP 메모리를 통해 컨텍스트를 공유하는 방식으로 에이전트 간 협업을 구현할 수 있습니다.

### 2.3. 모델 티어링 및 도구 매핑 (Runtime & Tools Mapping)
`gateway/runtime-mapping.yaml`에 정의된 런타임 규칙은 Gemini의 도구(Tool) 및 모델로 다음과 같이 대체할 수 있습니다.

- **모델 (LLM)**:
  - `HEAVY`/`HIGH` (현재 Claude Opus) $\rightarrow$ `Gemini 1.5 Pro` 또는 `Gemini 3.1 Pro (High)`
  - `MEDIUM` (현재 Claude Sonnet) $\rightarrow$ `Gemini 1.5 Flash` 또는 `Gemini 1.5 Pro`
- **핵심 도구 매핑 (Action -> Gemini API)**:
  - `file_write` (Write/Edit) $\rightarrow$ `write_to_file`, `replace_file_content`, `multi_replace_file_content`
  - `file_delete` / `code_execute` (Bash) $\rightarrow$ `run_command`
  - `network_access` (WebFetch/WebSearch) $\rightarrow$ `read_url_content`, `search_web`
  - `user_interact` (AskUserQuestion) $\rightarrow$ `ask_question` (채팅 응답을 통한 직접 피드백)

### 2.4. MCP 서버 통신 및 컨텍스트 연동
- **현재**: `context7`, `github_create_repo` 등 외부 MCP 혹은 Custom 도구를 통해 지식을 참조하고 레포를 생성.
- **Gemini 전환 방안**:
  - Gemini 역시 네이티브하게 **MCP 클라이언트**를 지원하므로, 기존 구축된 `.claude` 설정이나 MCP 설정 파일을 Gemini의 Tooling 환경에 맞춰 연결하기만 하면 동일하게 작동합니다. (`/tools` 워크플로우를 통한 MCP 제어 지원)

## 3. 마이그레이션 과제 및 진행 절차 제안

1. **디렉토리 구조 및 설정 파일 변경**: `.claude` 및 `.claude-plugin` 의존성을 제거하고, 이를 Gemini Agent 전용 설정(`prompt`, `workflows` 디렉토리 등)으로 개편.
2. **도구 호출 프롬프트 마이그레이션**: 에이전트들이 사용하는 도구(Tool)의 파라미터 규격(Schema)이 다르기 때문에, 프롬프트나 `agents/` 폴더 하위의 지시문들을 Gemini APi(`write_to_file`, `run_command` 등)에 맞게 재작성.
3. **워크플로우 테스트**: 체인 형태로 이어지는 기획-설계-개발 과정을 Gemini CLI나 Workflow 마크다운 문서로 연결해 파이프라인 테스트 수행.

## 4. 결론
NPD 프로젝트의 아키텍처 사상은 Gemini 에이전트 개발팀에서 지향하는 **Advanced Agentic Coding** 및 **Workflow** 사상과 놀라울 정도로 일치합니다. 코드 생태계 및 도구 API의 차이만 극복하도록 프롬프트 및 설정 파일 수정 작업을 거치면 Gemini 기반 플랫폼으로 성공적으로 이식할 수 있습니다.
