import os, glob

create_content = """---
description: NPD create 스킬 실행
allowed-tools: Read, Write, Bash, Task
---

1. 우선 사용자에게 "NPD 플러그인이 설치된 로컬 절대 경로가 어디인가요?" 라고 질문하세요. (문맥상 알고 있다면 생략)
2. 사용자가 알려준 경로 하위의 "skills/create/SKILL.md" 파일을 읽고 실행하세요.
3. 실행 과정에서 프로젝트 셋업 시 생성되는 "CLAUDE.md" 파일에 반드시 `NPD_PLUGIN_DIR: {사용자가_입력한_경로}` 형태의 플러그인 절대 경로를 기록하도록 강제하세요.
"""

with open('commands/create.md', 'w', encoding='utf-8') as f: f.write(create_content)

for cmd in ['setup', 'prepare']:
    cmd_name = 'setup' if cmd == 'setup' else 'prepare'
    content = f"""---
description: NPD {cmd_name} 스킬 실행
allowed-tools: Read, Write, Bash, Task
---

1. 우선 사용자에게 "NPD 플러그인이 설치된 절대 경로가 어디인가요?" 라고 질문하세요. (문맥상 알고 있다면 생략)
2. 사용자가 알려준 경로 하위의 `skills/{cmd_name}/SKILL.md` 파일을 읽고 실행하세요.
"""
    with open(f'commands/{cmd}.md', 'w', encoding='utf-8') as f: f.write(content)

desc_map = {
    'add-ext-skill': '외부호출 스킬(ext-{플러그인}) 추가 유틸리티',
    'remove-ext-skill': '외부호출 스킬(ext-{플러그인}) 삭제 유틸리티',
    'ext-github-release-manager': 'github-release-manager 외부 플러그인 연동',
    'design-physical-architecture': '물리 아키텍처 설계',
    'help': 'NPD help 스킬 실행',
    'deploy': 'NPD deploy 스킬 실행',
    'design': 'NPD design 스킬 실행',
    'develop': 'NPD develop 스킬 실행',
    'plan': 'NPD plan 스킬 실행',
    'cicd': 'NPD cicd 스킬 실행'
}

for filepath in glob.glob('commands/*.md'):
    basename = os.path.basename(filepath)
    if basename in ['create.md', 'setup.md', 'prepare.md']: continue
    cmd_name = basename.replace('.md', '')
    desc = desc_map.get(cmd_name, f'NPD {cmd_name} 스킬 실행')
    
    if basename == 'design-physical-architecture.md':
        content = f"""---
description: {desc}
---

### 물리 아키텍처 설계 Agent: architect (`/ralph` 활용)
1. 현재 작업 중인 프로젝트의 `CLAUDE.md` 파일을 읽어 `NPD_PLUGIN_DIR` (플러그인 루트 경로)를 파악하세요.
2. 해당 경로를 기준으로 아래 가이드를 준수하여 진행하세요.

- **GUIDE**: `{{NPD_PLUGIN_DIR}}/resources/guides/design/physical-architecture-design.md` 준수
- **TASK**: 주요/운영 환경별 K8s 인프라/네트워크 컴포넌트 구성과 Mermaid 다이어그램을 포함하여 문서를 설계 및 작성. 
- **EXPECTED OUTCOME**: `docs/design/physical/physical-architecture.md`, `physical-architecture-dev.md`, `physical-architecture-prod.md`, `physical-architecture-dev.mmd`, `physical-architecture-prod.mmd`, `network-dev.mmd`, `network-prod.mmd`

## 활성화 조건

사용자가 "물리 아키텍처 설계", "물리 아키텍처 설계 해줘", "물리 아키텍처 부탁해" 키워드를 언급할 때.

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구 호출 필수 (텍스트 출력 금지) |

## 완료 조건

- [ ] 물리 아키텍처 설계서(`docs/design/physical/`) 작성 완료
"""
    else:
        content = f"""---
description: {desc}
allowed-tools: Read, Write, Bash, Task
---

1. 현재 작업 중인 프로젝트의 `CLAUDE.md` 파일을 읽어 `NPD_PLUGIN_DIR` (플러그인 루트 경로)를 파악하세요.
2. 파악한 플러그인 루트 경로 하위의 `skills/{cmd_name}/SKILL.md` 파일을 읽고 지시사항을 실행하세요.
"""
    with open(filepath, 'w', encoding='utf-8') as f: f.write(content)

print("Update completed.")
