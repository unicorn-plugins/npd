import glob
import os

target_commands = glob.glob('commands/*.md')
for fp in target_commands:
    bn = os.path.basename(fp)
    if bn in ['create.md', 'setup.md', 'prepare.md']: continue
    
    with open(fp, 'r', encoding='utf-8') as f:
        lines = f.read()
    
    if "읽어 `NPD_PLUGIN_DIR`" in lines:
        if bn == 'design-physical-architecture.md':
            new_text = """1. 현재 작업 중인 프로젝트의 `CLAUDE.md` 파일을 "view_file" 등으로 꼼꼼히 읽으세요.
2. 파일에서 `NPD_PLUGIN_DIR`의 위치를 파악할 뿐만 아니라, 그 안에 적힌 팀 행동원칙, 대화 가이드, 정직한 보고 등 "모든 지침"을 이번 작업 전체에 걸쳐 우선적으로 엄격히 준수하세요.
3. 파악한 경로를 기준으로 아래 가이드를 준수하여 진행하세요."""
            
            lines = lines.replace(
                "1. 현재 작업 중인 프로젝트의 `CLAUDE.md` 파일을 읽어 `NPD_PLUGIN_DIR` (플러그인 루트 경로)를 파악하세요.\n2. 해당 경로를 기준으로 아래 가이드를 준수하여 진행하세요.",
                new_text
            )
        else:
            new_text = """1. 현재 작업 중인 프로젝트의 `CLAUDE.md` 파일을 "view_file" 등으로 꼼꼼히 읽으세요.
2. 파일에서 `NPD_PLUGIN_DIR`의 위치를 파악할 뿐만 아니라, 그 안에 적힌 팀 행동원칙, 대화 가이드, 정직한 보고 등 "모든 프로젝트 지침"을 이번 작업 전체에 걸쳐 우선적으로 엄격히 준수하세요.
3. 파악한 플러그인 루트 경로 하위의 `skills/""" + bn.replace('.md', '') + """/SKILL.md` 파일을 읽고 지시사항을 실행하세요."""
            
            lines = lines.replace(
                "1. 현재 작업 중인 프로젝트의 `CLAUDE.md` 파일을 읽어 `NPD_PLUGIN_DIR` (플러그인 루트 경로)를 파악하세요.\n2. 파악한 플러그인 루트 경로 하위의 `skills/" + bn.replace('.md', '') + "/SKILL.md` 파일을 읽고 지시사항을 실행하세요.",
                new_text
            )
        
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(lines)


target_gemini = glob.glob('gemini-workflows/*.md')
for fp in target_gemini:
    bn = os.path.basename(fp)
    if bn in ['create.md', 'setup.md', 'prepare.md']: continue
    
    with open(fp, 'r', encoding='utf-8') as f:
        lines = f.read()
        
    old_text = "1. 현재 작업 중인 프로젝트의 \"CLAUDE.md\" 파일을 읽어 NPD_PLUGIN_DIR 경로를 파악하세요.\n2. 파악한 플러그인 루트 경로 하위의 \"skills/" + bn.replace('.md', '') + "/SKILL.md\" 문서를 \"view_file\" 로 꼼꼼히 읽으세요.\n3. \"SKILL.md\" 내부에 명시된"
    
    if old_text in lines:
        new_text = """1. 현재 작업 중인 프로젝트의 "CLAUDE.md" 파일을 읽으세요.
2. 파일에서 `NPD_PLUGIN_DIR`의 위치를 파악할 뿐만 아니라, 그 안에 적힌 페르소나, 목표, 대화 규칙 등 "모든 지침"을 이번 워크플로우 내내 엄격히 준수하세요.
3. 파악한 플러그인 루트 경로 하위의 "skills/""" + bn.replace('.md', '') + """/SKILL.md" 문서를 "view_file" 로 꼼꼼히 읽으세요.
4. "SKILL.md" 내부에 명시된"""
        
        lines = lines.replace(old_text, new_text)
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(lines)
            
print("CLAUDE.md comprehensive rule enforcing updated.")
