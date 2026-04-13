# NPD: remove-ext-skill 스킬 워크플로우

> [!NOTE]
> 이 워크플로우는 NPD remove-ext-skill 단계를 실행합니다.

## 실행 지침
1. 현재 작업 중인 프로젝트의 "CLAUDE.md" 파일을 읽으세요.
2. 파일에서 `NPD_PLUGIN_DIR`의 위치를 파악할 뿐만 아니라, 그 안에 적힌 페르소나, 목표, 대화 규칙 등 "모든 지침"을 이번 워크플로우 내내 엄격히 준수하세요.
3. 파악한 플러그인 루트 경로 하위의 "skills/remove-ext-skill/SKILL.md" 문서를 "view_file" 로 꼼꼼히 읽으세요.
4. "SKILL.md" 내부에 명시된 단계를 Gemini 네이티브 도구(예: "run_command", "write_to_file", "ask_question")로 번역하여 현재 프로젝트에 수행하세요.
