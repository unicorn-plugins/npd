#!/usr/bin/env python3
"""스킬·에이전트 원본(.agents/)에서 도구별 생성물을 만드는 동기화 스크립트.

원본(손으로 고치는 파일)
  .agents/skills/<이름>/SKILL.md      스킬 원본. 표준 6키 + metadata.claude(Claude 확장 키)
  .agents/agents/<이름>.md            에이전트 원본. 8섹션 본문 + name/description/tier/permissions
  .agents/agents/_mapping.toml        범주(tier·permissions) → 도구별 값 매핑표

생성물(스크립트가 덮어씀. 직접 고치지 않음. 본문은 복제하지 않고 원본을 가리키는 포인터만 담음)
  .claude/skills/<이름>/SKILL.md      Claude Code 래퍼. Claude 확장 프론트매터 + 원본 본문 동적 주입
  .claude/agents/<이름>.md            Claude Code(및 Cursor 호환 모드) 서브에이전트. 원본을 읽고 따르라는 포인터
  .codex/agents/<이름>.toml           Codex 커스텀 에이전트. developer_instructions 가 원본 포인터
  .codex/config.toml                  위 TOML을 등록하는 [agents.<이름>] 구간(마커 사이만 관리)

사용법
  python scripts/sync-agents.py           생성물 갱신
  python scripts/sync-agents.py --check   생성물이 최신인지만 검사(다르면 종료 코드 1)

표준 라이브러리만 사용함(Python 3.11+, tomllib).
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILLS_SRC = ROOT / ".agents" / "skills"
AGENTS_SRC = ROOT / ".agents" / "agents"
MAPPING_FILE = AGENTS_SRC / "_mapping.toml"
CLAUDE_SKILLS = ROOT / ".claude" / "skills"
CLAUDE_AGENTS = ROOT / ".claude" / "agents"
CODEX_AGENTS = ROOT / ".codex" / "agents"
CODEX_CONFIG = ROOT / ".codex" / "config.toml"

# 예전 판이 만들던 생성물 위치. 남아 있으면 지움(원본 폴더에 생성물이 섞이지 않게)
STALE_GLOBS = [(AGENTS_SRC, "*.toml")]

MARK_BEGIN = "# >>> sync-agents (자동 생성 구간 시작 — 손으로 고치지 않음)"
MARK_END = "# <<< sync-agents (자동 생성 구간 끝)"

# Agent Skills 공개 표준의 허용 키. 원본 SKILL.md 프론트매터는 이 6키만 가짐
STANDARD_SKILL_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

SECTIONS = "[목표] · [역할] · [맥락] · [입력] · [처리] · [출력] · [제약조건] · [예시]"


# --------------------------------------------------------------------------- 파서
def split_frontmatter(text: str) -> tuple[list[str], str]:
    """'---' 울타리 사이의 줄 목록과 본문을 돌려줌. 프론트매터가 없으면 ([], text)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return [], text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1 :])
    raise ValueError("프론트매터 닫는 '---'가 없음")


def parse_yaml_lite(lines: list[str]) -> dict:
    """들여쓰기 기반의 아주 작은 YAML 부분집합 파서.

    지원: `key: 값`(스칼라, 원문 그대로 보존) · `key:`(하위 맵). 목록·여러 줄 스칼라는 지원하지 않음.
    값은 따옴표를 벗기지 않고 원문을 그대로 보존함(생성물에 같은 표기로 다시 씀).
    """
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"들여쓰기 오류: {raw!r}")
        parent = stack[-1][1]
        key, sep, value = raw.strip().partition(":")
        if not sep:
            raise ValueError(f"'key: value' 형식이 아님: {raw!r}")
        value = value.strip()
        if value == "":
            child: dict = {}
            parent[key.strip()] = child
            stack.append((indent, child))
        else:
            parent[key.strip()] = value
    return root


def unquote(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def toml_basic_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_multiline(value: str) -> str:
    """여러 줄 문자열. 리터럴(''')이 안전하면 그것을, 아니면 기본 문자열(\"\"\")을 씀."""
    if "'''" not in value:
        return "'''\n" + value.rstrip("\n") + "\n'''"
    escaped = value.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    return '"""\n' + escaped.rstrip("\n") + '\n"""'


# --------------------------------------------------------------------------- 생성기
def gen_skill_wrapper(name: str, meta: dict) -> str:
    """Claude Code용 래퍼 SKILL.md. 표준 키 + metadata.claude 의 확장 키를 프론트매터로 올림."""
    extra_keys = set(meta) - STANDARD_SKILL_KEYS
    if extra_keys:
        raise ValueError(f"[{name}] 원본 SKILL.md에 표준 외 키가 있음: {sorted(extra_keys)} → metadata.claude 아래로 옮길 것")
    claude_ext = {}
    metadata = meta.get("metadata")
    if isinstance(metadata, dict) and isinstance(metadata.get("claude"), dict):
        claude_ext = metadata["claude"]

    fm = [f"name: {meta.get('name', name)}", f"description: {meta['description']}"]
    if "allowed-tools" in meta:
        fm.append(f"allowed-tools: {meta['allowed-tools']}")
    for k, v in claude_ext.items():
        if k in ("name", "description"):
            continue
        fm.append(f"{k}: {v}")

    src_rel = f".agents/skills/{name}/SKILL.md"
    src_dir = f"${{CLAUDE_PROJECT_DIR}}/.agents/skills/{name}"
    body = f"""<!-- scripts/sync-agents.py 가 만든 Claude Code 래퍼임. 원본: {src_rel}
     이 파일을 직접 고치지 않음. 원본을 고친 뒤 `python scripts/sync-agents.py` 를 다시 실행함 -->

> **이 스킬의 원본은 `{src_rel}`이며 아래에 그대로 주입됨.**
> 본문에서 `{{스킬 디렉토리}}` · `<스킬 디렉터리>` · "이 SKILL.md가 위치한 디렉토리"는 모두
> `{src_dir}` 를 뜻함(`prompts/` · `guides/` · `shell/` · `templates/`가 그 아래에 있음).
> 인자: $ARGUMENTS

!`cat "{src_dir}/SKILL.md"`
"""
    return "---\n" + "\n".join(fm) + "\n---\n" + body


def pointer_text(name: str, read_hint: str) -> str:
    """에이전트 생성물에 넣는 공통 포인터 본문. 8섹션 지침은 원본 1곳에만 두고 여기서는 복제하지 않음."""
    src_rel = f".agents/agents/{name}.md"
    return (
        f"당신은 design-agentic-ai 팀의 에이전트 `{name}`임.\n"
        f"\n"
        f"**지침 원본은 프로젝트 루트의 `{src_rel}` 한 파일이며, 이 파일에는 복제하지 않음.**\n"
        f"작업을 시작하기 전에 반드시 {read_hint} 그 파일 전체를 읽고, 거기 적힌 8섹션\n"
        f"({SECTIONS})을 요약·축약 없이 그대로 따름.\n"
        f"원본을 읽지 못하면 작업을 시작하지 않고 그 사실을 먼저 보고함.\n"
        f"프로젝트 공통 규칙(`AGENTS.md`의 마크다운 작성 가이드 · 정직한 보고 규칙)도 함께 지킴.\n"
    )


def gen_claude_agent(name: str, meta: dict, mapping: dict) -> str:
    model = mapping["claude"]["model"][unquote(meta["tier"])]
    fm = [f"name: {meta.get('name', name)}", f"description: {meta['description']}", f"model: {model}"]
    header = (
        f"<!-- scripts/sync-agents.py 가 만든 생성물임. 지침 원본: .agents/agents/{name}.md\n"
        f"     이 파일을 직접 고치지 않음. 원본을 고친 뒤 `python scripts/sync-agents.py` 를 다시 실행함 -->\n\n"
    )
    return "---\n" + "\n".join(fm) + "\n---\n" + header + pointer_text(name, "Read 도구로")


def gen_codex_agent(name: str, meta: dict, mapping: dict) -> str:
    tier = unquote(meta["tier"])
    perm = unquote(meta["permissions"])
    codex = mapping["codex"]
    lines = [
        f"# scripts/sync-agents.py 가 만든 Codex 커스텀 에이전트 정의임. 지침 원본: .agents/agents/{name}.md",
        "# 이 파일을 직접 고치지 않음. 원본 또는 .agents/agents/_mapping.toml 을 고친 뒤 스크립트를 다시 실행함",
        f"name = {toml_basic_string(meta.get('name', name))}",
        f"description = {toml_basic_string(unquote(meta['description']))}",
        f"model = {toml_basic_string(codex['model'][tier])}",
        f"model_reasoning_effort = {toml_basic_string(codex['reasoning_effort'][tier])}",
        f"sandbox_mode = {toml_basic_string(codex['sandbox_mode'][perm])}",
        f"developer_instructions = {toml_multiline(pointer_text(name, '파일 읽기 도구로(작업 디렉토리는 프로젝트 루트임)'))}",
        "",
    ]
    return "\n".join(lines)


def gen_codex_config_block(agents: list[tuple[str, dict]]) -> str:
    lines = [MARK_BEGIN,
             "# .codex/agents/<이름>.toml 을 Codex 커스텀 에이전트로 등록함.",
             "# 2026-09-03 실측: .codex/agents/ 드롭인·[agents.*] 인라인 정의는 인식되지 않고 config_file 등록만 동작함.",
             "# config_file 의 상대경로는 이 파일(.codex/config.toml) 기준으로 풀림."]
    for name, meta in agents:
        lines += [
            "",
            f"[agents.{name}]",
            f"description = {toml_basic_string(unquote(meta['description']))}",
            f'config_file = "agents/{name}.toml"',
        ]
    lines.append(MARK_END)
    return "\n".join(lines) + "\n"


def merge_codex_config(existing: str | None, block: str) -> str:
    if existing is None:
        head = ("# Codex 프로젝트 설정. 아래 마커 사이는 scripts/sync-agents.py 가 관리함.\n"
                "# 마커 밖에는 팀 공용 설정을 자유롭게 추가할 수 있음.\n\n")
        return head + block
    if MARK_BEGIN in existing and MARK_END in existing:
        pre, _, rest = existing.partition(MARK_BEGIN)
        _, _, post = rest.partition(MARK_END)
        post = post.lstrip("\n")
        return pre + block + ("\n" + post if post else "")
    sep = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    return existing + sep + block


# --------------------------------------------------------------------------- 실행
def load_mapping() -> dict:
    with MAPPING_FILE.open("rb") as f:
        return tomllib.load(f)


def collect_outputs() -> dict[pathlib.Path, str]:
    mapping = load_mapping()
    outputs: dict[pathlib.Path, str] = {}

    # 스킬 → Claude 래퍼
    for skill_md in sorted(SKILLS_SRC.glob("*/SKILL.md")):
        name = skill_md.parent.name
        fm_lines, _ = split_frontmatter(skill_md.read_text(encoding="utf-8"))
        meta = parse_yaml_lite(fm_lines)
        if "description" not in meta:
            raise ValueError(f"[{name}] SKILL.md 에 description 이 없음")
        outputs[CLAUDE_SKILLS / name / "SKILL.md"] = gen_skill_wrapper(name, meta)

    # 에이전트 → Claude md(포인터) · Codex toml(포인터) · Codex config 구간
    agents: list[tuple[str, dict]] = []
    for agent_md in sorted(AGENTS_SRC.glob("*.md")):
        if agent_md.name.startswith("_") or agent_md.name.upper() == "README.MD":
            continue
        name = agent_md.stem
        fm_lines, body = split_frontmatter(agent_md.read_text(encoding="utf-8"))
        meta = parse_yaml_lite(fm_lines)
        for required in ("description", "tier", "permissions"):
            if required not in meta:
                raise ValueError(f"[{name}] 에이전트 원본 프론트매터에 {required} 가 없음")
        if unquote(meta.get("name", name)) != name:
            raise ValueError(f"[{name}] 파일명과 name 필드가 다름: {meta.get('name')}")
        if "[역할]" not in body:
            raise ValueError(f"[{name}] 원본 본문에 [역할] 절이 없음(8섹션 표준 확인)")
        outputs[CLAUDE_AGENTS / f"{name}.md"] = gen_claude_agent(name, meta, mapping)
        outputs[CODEX_AGENTS / f"{name}.toml"] = gen_codex_agent(name, meta, mapping)
        agents.append((name, meta))

    existing = CODEX_CONFIG.read_text(encoding="utf-8") if CODEX_CONFIG.exists() else None
    outputs[CODEX_CONFIG] = merge_codex_config(existing, gen_codex_config_block(agents))
    return outputs


def find_stale() -> list[pathlib.Path]:
    return [p for base, pattern in STALE_GLOBS for p in sorted(base.glob(pattern)) if p.name != "_mapping.toml"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="생성물이 최신인지만 검사(다르면 1)")
    args = ap.parse_args()

    outputs = collect_outputs()
    rel = lambda p: p.relative_to(ROOT).as_posix()

    changed: list[pathlib.Path] = []
    for path, content in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            changed.append(path)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")

    stale = find_stale()
    if not args.check:
        for p in stale:
            p.unlink()

    if args.check:
        if changed or stale:
            print("생성물이 원본과 어긋남(스크립트를 다시 실행할 것):")
            for p in changed:
                print(f"  - 갱신 필요: {rel(p)}")
            for p in stale:
                print(f"  - 옛 위치 생성물 잔존: {rel(p)}")
            return 1
        print(f"검사 통과: 생성물 {len(outputs)}건이 모두 최신임")
        return 0
    print(f"생성물 {len(outputs)}건 중 {len(changed)}건 갱신, 옛 위치 생성물 {len(stale)}건 제거:")
    for p in changed:
        print(f"  - {rel(p)}")
    for p in stale:
        print(f"  - 제거: {rel(p)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
