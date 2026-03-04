"""
마크다운 파일에서 빈 줄 없이 줄바꿈되는 부분을 찾아 줄 끝에 스페이스 2개를 추가하는 스크립트.

사용법:
    python fix-trailing-spaces.py <파일경로>

예시:
    python fix-trailing-spaces.py resources/references/create-cicd-tools.md
"""

import re
import sys
import os


def is_list_item(s):
    """리스트 항목인지 확인 (블록인용 내부 포함)"""
    s = s.strip()
    while s.startswith('>'):
        s = s[1:].lstrip()
    if re.match(r'^[-*+] ', s):
        return True
    if re.match(r'^\d+[.)]\s', s):
        return True
    return False


def is_code_fence(s):
    """코드펜스(```)인지 확인 (블록인용 내부 포함)"""
    s = s.strip()
    while s.startswith('>'):
        s = s[1:].lstrip()
    return s.startswith('```')


def is_blank_bq(s):
    """빈 블록인용 줄인지 확인 (> 만 있는 줄)"""
    return s.strip() == '>' or s.strip() == ''


def fix_trailing_spaces(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_code_block = False
    in_bq_code_block = False
    changes = []

    for i in range(len(lines) - 1):
        line = lines[i]
        next_line = lines[i + 1]
        stripped = line.rstrip('\n')

        # 일반 코드블록 토글
        if not in_bq_code_block and stripped.lstrip().startswith('```') and not stripped.lstrip().startswith('> '):
            in_code_block = not in_code_block
            continue

        # 블록인용 내부 코드블록 토글
        if is_code_fence(stripped) and stripped.strip().startswith('>'):
            in_bq_code_block = not in_bq_code_block
            continue

        if in_code_block or in_bq_code_block:
            continue

        # 빈 줄 스킵
        if stripped.strip() == '':
            continue

        # 다음 줄이 빈 줄이면 스킵 (빈 줄이 줄바꿈 역할)
        if next_line.strip() == '':
            continue

        # 이미 스페이스 2개로 끝나면 스킵
        if stripped.endswith('  '):
            continue

        # 헤딩 스킵
        if stripped.lstrip().startswith('#'):
            continue

        # 테이블 행 스킵
        if stripped.lstrip().startswith('|'):
            continue

        # 수평선 스킵
        if re.match(r'^-{3,}$', stripped.strip()):
            continue

        # 이미지 줄 스킵
        if stripped.lstrip().startswith('!['):
            continue

        # 리스트 항목 스킵
        if is_list_item(stripped):
            continue

        # 빈 블록인용 줄 스킵 (> 만 있는 줄)
        if is_blank_bq(stripped):
            continue

        # 다음 줄이 코드펜스면 스킵 (코드블록은 블록 레벨 요소)
        if is_code_fence(next_line.rstrip('\n')):
            continue

        # 다음 줄이 이미지면 스킵
        next_stripped = next_line.strip()
        while next_stripped.startswith('>'):
            next_stripped = next_stripped[1:].lstrip()
        if next_stripped.startswith('!['):
            continue

        # 이 줄에 trailing 스페이스 2개 추가 필요
        changes.append((i + 1, stripped))
        lines[i] = stripped + '  \n'

    print(f'Total changes: {len(changes)}')
    for lineno, content in changes:
        preview = content if len(content) <= 90 else '...' + content[-87:]
        print(f'  L{lineno}: {preview}')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print('\nDone.')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python fix-trailing-spaces.py <filepath>')
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.isabs(filepath):
        filepath = os.path.join(os.getcwd(), filepath)

    if not os.path.isfile(filepath):
        print(f'Error: file not found: {filepath}')
        sys.exit(1)

    fix_trailing_spaces(filepath)
