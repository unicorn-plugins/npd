---
description: NPD create 스킬 실행
allowed-tools: Read, Write, Bash, Task
---

1. 우선 사용자에게 "NPD 플러그인이 설치된 로컬 절대 경로가 어디인가요?" 라고 질문하세요. (문맥상 알고 있다면 생략)
2. 사용자가 알려준 경로 하위의 "skills/create/SKILL.md" 파일을 읽고 실행하세요.
3. 실행 과정에서 프로젝트 셋업 시 생성되는 "AGENTS.md" 파일에 반드시 `NPD_PLUGIN_DIR: {사용자가_입력한_경로}` 형태의 플러그인 절대 경로를 기록하도록 강제하세요.
