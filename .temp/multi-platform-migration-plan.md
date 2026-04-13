# Claude & Gemini 크로스 플랫폼 지원 수정 계획

## 1. 개요
NPD 프로젝트를 기존 **Claude Code** 뿐만 아니라 **Gemini Advanced Agentic Workflow** 환경에서도 동일하게 동작할 수 있도록 범용적인 "에이전트 플러그인" 아키텍처로 개편합니다. 코어 로직(명령어 프롬프트, 에이전트 페르소나 설계 등)은 공유하면서 플랫폼 종속적인 부분(도구 이름, 디렉토리 해석 방식, 진입점)을 분리 및 추상화하는 것이 목표입니다.

## 2. 각 영역별 수정 계획

### 2.1. CLAUDE.md 호환성 개선
Claude는 기본적으로 `CLAUDE.md`를 시스템 컨텍스트로 불러오며, Gemini 역시 워크플로우 실행 시 로컬의 마크다운 가이드라인을 참조할 수 있습니다. 이를 양쪽에서 모두 올바르게 해석하도록 내용을 확장합니다.

*   **현재 문제**: `{NPD_PLUGIN_DIR}`가 `~/.claude/plugins/cache/npd/npd/`로 하드코딩되어 있어 Gemini 환경에 맞지 않음.
*   **수정 방향**:
    *   Claude와 Gemini 양쪽의 런타임 환경 해석 방식을 모두 명시.
    *   **경로 해석 추상화**: "플랫폼별 플러그인 루트 디렉토리 결정 방식" 단락으로 개편.
        *   *(Claude)*: `~/.claude/plugins/cache/...` 탐색 후 바인딩
        *   *(Gemini)*: `<appDataDir>` 또는 활성화된 `[workspace/npd]`의 절대 경로를 플러그인 루트로 바인딩하도록 명시
    *   Gemini 특화 지침(예: "tool 호출 시 run_command 대신 write_to_file을 선호할 것" 등 플랫폼별 베스트 프랙티스)을 추가 작성하여 Gemini가 읽었을 때도 최적의 도구를 선택하게 유도.

### 2.2. 게이트웨이 및 도구 추상화 (Gateway & Tools Adapter)
플랫폼마다 제공하는 Native Tool의 명칭과 스펙이 다릅니다. 이 차이를 흡수할 어댑터를 구성합니다.

*   **설정 파일 분리 및 병합**: 
    *   기존 `gateway/runtime-mapping.yaml`에 `platform: base`를 두고, 플랫폼별 설정(`claude`, `gemini`)을 오버라이드할 수 있게 구조 변경.
*   **액션 $\leftrightarrow$ 도구 동적 매핑**:
    *   `file_write` 액션 실행 시:
        *   Claude 환경 인식 시 $\rightarrow$ `Write`, `Edit` 도구 사용 지시
        *   Gemini 환경 인식 시 $\rightarrow$ `write_to_file`, `replace_file_content` 도구 사용 지시
    *   `code_execute` 액션 실행 시:
        *   Claude $\rightarrow$ `Bash`
        *   Gemini $\rightarrow$ `run_command`

### 2.3. 명령어 브릿지 파일 및 진입점(Entrypoint) 분리
핵심 지시문은 공통 영역에 두고, 각 환경에서 이를 호출(Include)하는 방식으로 변경합니다.

*   **공통 프롬프트 분리**: `commands/` 내부의 마크다운 프롬프트를 플랫폼 독립적인 `templates/core-prompts/` 등의 하위 디렉토리로 이동.
*   **Claude 진입점 유지**: 기존 `commands/*.md`는 `templates/core-prompts/`의 파일을 그대로 Load하는 래퍼(Wrapper)로 구성.
*   **Gemini 진입점 신설**: `.gemini/workflows/` (또는 글로벌 워크플로우 연결 파일)를 신규 생성하여 Gemini 사용자가 `/npd-create` 등의 명령어를 쓸 수 있게 하고, 이 역시 `templates/core-prompts/`를 로드하여 동일한 AI 프롬프트를 제공.

### 2.4. 에이전트 핸드오프(Task Delegation) 호환성 확보
에이전트가 다른 에이전트(예: Architect $\rightarrow$ Backend Dev)를 호출할 때:
*   Claude: `Task` Tool 등을 이용해 서브 에이전트 파생
*   Gemini: `/coordinate`, `/orchestrate` 등의 마크다운 워크플로우를 통한 에이전트 위임 방식 사용. 이에 따라 에이전트 페르소나 카드(`agentcard.yaml`)에 위임 시 사용할 각 플랫폼별 커맨드를 구분해서 명시.

## 3. 마이그레이션 단계별 로드맵 (실행 절차)

*   **Phase 1: 컨텍스트 가이드라인 업데이트**
    *   `CLAUDE.md` 파일 수정 (Gemini의 Context / Workspace 변수 지원 내용 포함)
*   **Phase 2: 환경별 Config 분리**
    *   `gateway/runtime-mapping.yaml`을 리팩토링하여 플랫폼별 툴/티어 배열 지원
*   **Phase 3: 코어 프롬프트 템플릿화**
    *   `commands/*.md` 파일을 공통 템플릿으로 분리하고 각 플랫폼에 맞는 래퍼 껍데기 구축
*   **Phase 4: 테스트 및 검증**
    *   Claude 환경과 Gemini 환경 모두에서 `/npd:setup` 및 `/npd:create` 시나리오 교차 검증

이 계획을 승인해주시면, Phase 1 단계인 `CLAUDE.md` 수정 작업부터 곧바로 진행할 수 있습니다.
