#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IntelliJ Gradle 실행 프로파일(.run.xml) 기반 Spring Boot 서비스 실행기

IntelliJ의 .run/*.run.xml 파일을 파싱하여 환경변수를 추출하고
./gradlew {service}:bootRun 명령을 실행합니다.
로그는 {config-dir}/logs/{service-name}.log 에 저장됩니다.

Usage:
  # 전체 서비스 시작 (서비스 간 5초 delay)
  python3 tools/run-intellij-service-profile.py --config-dir . --delay 5

  # 백그라운드로 전체 서비스 시작
  nohup python3 tools/run-intellij-service-profile.py --config-dir . --delay 5 > /dev/null 2>&1 &

  # 개별 서비스 시작
  python3 tools/run-intellij-service-profile.py auth
  nohup python3 tools/run-intellij-service-profile.py schedule > logs/schedule.log 2>&1 &

  # 서비스 목록 확인
  python3 tools/run-intellij-service-profile.py --list
"""

import argparse
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

# Windows에서 한글 출력을 위한 UTF-8 설정
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


# ─────────────────────────────────────────────
# XML 파싱
# ─────────────────────────────────────────────

def parse_run_xml(xml_path: Path) -> dict:
    """
    .run.xml 파일을 파싱하여 서비스 실행 정보를 반환합니다.

    Returns:
        {
            'name': str,           # 서비스 이름 (configuration name 속성)
            'tasks': list[str],    # Gradle 태스크 목록 (예: ['auth:bootRun'])
            'env': dict[str, str], # 환경변수 원본 값 (${VAR} 미확장)
            'xml_path': Path,
        }
    """
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        raise ValueError(f"XML 파싱 오류 ({xml_path}): {e}")

    root = tree.getroot()
    config = root.find('configuration')
    if config is None:
        raise ValueError(f"<configuration> 요소를 찾을 수 없습니다: {xml_path}")

    service_name = config.get('name', xml_path.stem.replace('.run', ''))

    # 환경변수 추출: <option name="env"><map><entry key="..." value="..." />
    env = {}
    env_map = config.find('.//option[@name="env"]/map')
    if env_map is not None:
        for entry in env_map.findall('entry'):
            key = entry.get('key')
            value = entry.get('value', '')
            if key:
                env[key] = value

    # Gradle 태스크 추출: <option name="taskNames"><list><option value="auth:bootRun" />
    tasks = []
    task_list = config.find('.//option[@name="taskNames"]/list')
    if task_list is not None:
        for opt in task_list.findall('option'):
            val = opt.get('value')
            if val:
                tasks.append(val)

    return {
        'name': service_name,
        'tasks': tasks,
        'env': env,
        'xml_path': xml_path,
    }


# ─────────────────────────────────────────────
# 환경변수 처리
# ─────────────────────────────────────────────

_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')


def resolve_env(raw_env: dict, config_dir: Path) -> dict:
    """
    .run.xml 의 환경변수 값을 확장합니다.

    처리 규칙:
    - ${VAR}  → OS 환경변수 VAR 값으로 치환 (없으면 빈 문자열)
    - $PROJECT_DIR$ → config_dir 절대 경로로 치환
    - 그 외 리터럴 값은 그대로 사용
    """
    base_env = os.environ.copy()
    resolved = {}

    for key, value in raw_env.items():
        # $PROJECT_DIR$ 처리
        value = value.replace('$PROJECT_DIR$', str(config_dir))

        # ${VAR} 치환
        def replacer(m):
            var_name = m.group(1)
            val = base_env.get(var_name)
            if val is None:
                print(f"  [WARN] ${{{var_name}}} is not set, defaulting to empty string",
                      file=sys.stderr)
                return ''
            return val

        value = _VAR_PATTERN.sub(replacer, value)
        resolved[key] = value

    return resolved


def build_process_env(raw_env: dict, config_dir: Path) -> dict:
    """OS 환경변수에 .run.xml 환경변수를 오버레이하여 반환합니다."""
    merged = os.environ.copy()
    merged.update(resolve_env(raw_env, config_dir))
    return merged


# ─────────────────────────────────────────────
# Gradle 실행기 탐색
# ─────────────────────────────────────────────

def find_gradlew(config_dir: Path) -> list:
    """
    OS에 맞는 Gradle wrapper 명령을 반환합니다.

    Returns:
        list: subprocess cmd 앞부분 (예: ['./gradlew'] 또는 ['cmd', '/c', 'gradlew.bat'])
    """
    if sys.platform == "win32":
        gradlew_bat = config_dir / 'gradlew.bat'
        if gradlew_bat.exists():
            return ['cmd', '/c', str(gradlew_bat)]
        raise FileNotFoundError(
            f"gradlew.bat을 찾을 수 없습니다: {config_dir}\n"
            f"프로젝트 루트에 Gradle wrapper가 존재하는지 확인하세요."
        )
    else:
        gradlew = config_dir / 'gradlew'
        if gradlew.exists():
            gradlew.chmod(gradlew.stat().st_mode | 0o111)  # +x 보장
            return [str(gradlew)]
        raise FileNotFoundError(
            f"gradlew를 찾을 수 없습니다: {config_dir}\n"
            f"프로젝트 루트에 Gradle wrapper가 존재하는지 확인하세요."
        )


# ─────────────────────────────────────────────
# 서비스 탐색
# ─────────────────────────────────────────────

def find_all_run_xml(config_dir: Path) -> list:
    """
    config_dir 하위의 모든 *.run.xml 파일을 탐색합니다.
    탐색 패턴: {config_dir}/*/.run/*.run.xml
    """
    run_files = []
    for service_dir in sorted(config_dir.iterdir()):
        if not service_dir.is_dir() or service_dir.name.startswith('.'):
            continue
        run_dir = service_dir / '.run'
        if not run_dir.is_dir():
            continue
        for xml_file in sorted(run_dir.glob('*.run.xml')):
            run_files.append(xml_file)
    return run_files


def find_service_xml(config_dir: Path, service_name: str) -> Path:
    """
    특정 서비스의 .run.xml 경로를 반환합니다.
    우선순위:
      1. {config_dir}/{service_name}/.run/{service_name}.run.xml
      2. 전체 탐색 후 name 속성 일치
    """
    # 직접 경로
    direct = config_dir / service_name / '.run' / f'{service_name}.run.xml'
    if direct.exists():
        return direct

    # 전체 탐색
    for xml_file in find_all_run_xml(config_dir):
        try:
            info = parse_run_xml(xml_file)
            if info['name'] == service_name:
                return xml_file
        except ValueError:
            continue

    raise FileNotFoundError(
        f"서비스 '{service_name}'의 .run.xml 파일을 찾을 수 없습니다. "
        f"(탐색 위치: {config_dir})"
    )


# ─────────────────────────────────────────────
# 서비스 시작
# ─────────────────────────────────────────────

def start_service(service_info: dict, config_dir: Path, log_file: str = None) -> subprocess.Popen:
    """
    서비스를 백그라운드 프로세스로 시작합니다.

    Args:
        service_info: parse_run_xml() 반환값
        config_dir:   프로젝트 루트 디렉토리
        log_file:     로그 파일 경로 (None 이면 logs/{name}.log 자동 생성)

    Returns:
        subprocess.Popen 객체
    """
    name = service_info['name']
    tasks = service_info['tasks']

    if not tasks:
        raise ValueError(f"'{name}': taskNames 가 비어 있습니다.")

    gradlew_cmd = find_gradlew(config_dir)
    cmd = gradlew_cmd + tasks
    env = build_process_env(service_info['env'], config_dir)

    # 로그 디렉토리/파일 결정
    logs_dir = config_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = Path(log_file) if log_file else logs_dir / f'{name}.log'

    port = service_info['env'].get('SERVER_PORT', '?')
    print(f"[START] {name}  port={port}")
    print(f"        cmd : {' '.join(cmd)}")
    print(f"        log : {log_path}")

    lf = open(log_path, 'wb')
    proc = subprocess.Popen(
        cmd,
        env=env,
        cwd=str(config_dir),
        stdout=lf,
        stderr=subprocess.STDOUT,
    )
    lf.close()

    print(f"        pid : {proc.pid}")
    return proc


# ─────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="IntelliJ Gradle 실행 프로파일 기반 Spring Boot 서비스 실행기",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'service',
        nargs='?',
        metavar='SERVICE',
        help='시작할 서비스 이름 (생략 시 전체 서비스 시작)',
    )
    parser.add_argument(
        '--config-dir',
        default='.',
        metavar='DIR',
        help='프로젝트 루트 디렉토리 (default: 현재 디렉토리)',
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=0,
        metavar='SEC',
        help='서비스 간 시작 지연 시간(초) (default: 0)',
    )
    parser.add_argument(
        '--log-file',
        metavar='PATH',
        help='로그 파일 경로 (개별 서비스 시작 시 사용)',
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='발견된 서비스 목록만 출력하고 종료',
    )

    args = parser.parse_args()
    config_dir = Path(args.config_dir).resolve()

    if not config_dir.is_dir():
        print(f"오류: 디렉토리를 찾을 수 없습니다: {config_dir}", file=sys.stderr)
        sys.exit(1)

    # ── 목록 출력 모드 ──
    if args.list:
        xml_files = find_all_run_xml(config_dir)
        if not xml_files:
            print(f"서비스를 찾을 수 없습니다: {config_dir}")
            return
        print(f"발견된 서비스 ({len(xml_files)}개) — {config_dir}")
        for xml_file in xml_files:
            try:
                info = parse_run_xml(xml_file)
                port = info['env'].get('SERVER_PORT', '?')
                tasks = ', '.join(info['tasks']) or '(없음)'
                print(f"  %-20s port=%-6s task=%s" % (info['name'], port, tasks))
            except ValueError as e:
                print(f"  [파싱 오류] {xml_file.name}: {e}")
        return

    # ── 개별 서비스 모드 ──
    if args.service:
        try:
            xml_path = find_service_xml(config_dir, args.service)
            service_info = parse_run_xml(xml_path)
            start_service(service_info, config_dir, args.log_file)
        except (FileNotFoundError, ValueError) as e:
            print(f"오류: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # ── 전체 서비스 모드 ──
    xml_files = find_all_run_xml(config_dir)
    if not xml_files:
        print(
            f"오류: {config_dir} 에서 .run.xml 파일을 찾을 수 없습니다.\n"
            f"  탐색 패턴: {{config-dir}}/*/.run/*.run.xml",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"전체 서비스 시작: {len(xml_files)}개  delay={args.delay}초")
    print()

    started = []
    try:
        for i, xml_file in enumerate(xml_files):
            try:
                service_info = parse_run_xml(xml_file)
                proc = start_service(service_info, config_dir)
                started.append((service_info['name'], proc))
            except (ValueError, OSError) as e:
                print(f"[SKIP] {xml_file.name}: {e}", file=sys.stderr)

            if args.delay > 0 and i < len(xml_files) - 1:
                print(f"       {args.delay}초 대기 중...")
                time.sleep(args.delay)
            print()
    except KeyboardInterrupt:
        print(f"\n[INTERRUPT] 시작된 서비스 {len(started)}개를 종료합니다...")
        for name, proc in started:
            proc.terminate()
            print(f"  {name} (PID {proc.pid}) 종료")
        sys.exit(130)

    print("─" * 50)
    print(f"시작 완료: {len(started)}/{len(xml_files)}개")
    for name, proc in started:
        print(f"  {name:20s} PID {proc.pid}")
    print()
    print("서비스 종료:")
    print("  Linux/Mac : kill $(pgrep -f run-intellij-service-profile.py) && pkill -f 'java.*spring'")
    print("  Windows   : netstat -ano | findstr :{PORT}  →  Stop-Process -Id {PID} -Force")


if __name__ == '__main__':
    main()
