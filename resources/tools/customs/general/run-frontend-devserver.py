#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프론트엔드 개발 서버 실행기

프로젝트의 프론트엔드 플랫폼(React/Vue/Flutter)을 자동 감지하여
개발 서버를 시작·중지하고, 현재 상태를 확인합니다.

Usage:
  # 프론트엔드 개발 서버 시작
  python3 tools/run-frontend-devserver.py start

  # 기존 포트 점유 프로세스를 강제 종료 후 시작
  python3 tools/run-frontend-devserver.py start --force

  # 백그라운드로 시작
  python3 tools/run-frontend-devserver.py start --background

  # 프론트엔드 개발 서버 중지
  python3 tools/run-frontend-devserver.py stop

  # 프론트엔드 개발 서버 상태 확인
  python3 tools/run-frontend-devserver.py status

  # 프로젝트 루트 지정
  python3 tools/run-frontend-devserver.py --project-dir /path/to/project start
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

# Windows에서 한글 출력을 위한 UTF-8 설정
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


# ─────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────

DEFAULT_PORT = 3000
PID_FILE_NAME = '.frontend-devserver.pid'


# ─────────────────────────────────────────────
# 플랫폼 감지
# ─────────────────────────────────────────────

def detect_platform(frontend_dir: Path) -> str:
    """
    프론트엔드 디렉토리의 플랫폼을 감지합니다.

    Returns:
        'react' | 'vue' | 'flutter' | 'unknown'
    """
    # Flutter: pubspec.yaml 존재
    if (frontend_dir / 'pubspec.yaml').exists():
        return 'flutter'

    # Node.js: package.json 존재
    pkg_json = frontend_dir / 'package.json'
    if pkg_json.exists():
        try:
            with open(pkg_json, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
            if 'vue' in deps:
                return 'vue'
            if 'react' in deps or 'react-dom' in deps:
                return 'react'
            # package.json은 있지만 프레임워크 특정 불가 → npm 기반으로 처리
            return 'react'
        except (json.JSONDecodeError, OSError):
            return 'react'

    return 'unknown'


# ─────────────────────────────────────────────
# .env 파일에서 포트 읽기
# ─────────────────────────────────────────────

def read_port_from_env(project_dir: Path) -> int:
    """
    프로젝트 루트의 .env 파일에서 FRONTEND_PORT 값을 읽습니다.
    없으면 기본값(3000)을 반환합니다.
    """
    env_file = project_dir / '.env'
    if not env_file.exists():
        return DEFAULT_PORT

    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or '=' not in line:
                    continue
                key, _, value = line.partition('=')
                if key.strip() == 'FRONTEND_PORT':
                    value = value.strip().strip('"').strip("'")
                    try:
                        return int(value)
                    except ValueError:
                        pass
    except OSError:
        pass

    return DEFAULT_PORT


# ─────────────────────────────────────────────
# 프로세스 탐지 및 중지
# ─────────────────────────────────────────────

def find_pid_by_port(port: int) -> list:
    """
    특정 포트를 LISTEN 중인 프로세스의 PID 목록을 반환합니다.
    """
    pids = []
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ['netstat', '-ano', '-p', 'TCP'],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.splitlines():
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if parts:
                        pid = int(parts[-1])
                        if pid > 0 and pid not in pids:
                            pids.append(pid)
        else:
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if line.isdigit():
                    pid = int(line)
                    if pid > 0 and pid not in pids:
                        pids.append(pid)
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return pids


def get_process_name(pid: int) -> str:
    """
    PID로 프로세스 이름을 조회합니다.
    """
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.strip().splitlines():
                parts = line.strip('"').split('","')
                if len(parts) >= 2:
                    return parts[0]
        else:
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'comm='],
                capture_output=True, text=True, timeout=5,
            )
            name = result.stdout.strip()
            if name:
                return name
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return 'unknown'


def stop_pid(pid: int, timeout: int = 5) -> bool:
    """
    PID를 graceful 종료(SIGTERM) 시도 후, 실패 시 강제 종료(SIGKILL/taskkill)합니다.

    Returns:
        True: 종료 성공, False: 종료 실패
    """
    try:
        if sys.platform == "win32":
            # Windows: taskkill /T로 자식 프로세스까지 종료
            subprocess.run(
                ['taskkill', '/PID', str(pid), '/T', '/F'],
                capture_output=True, timeout=timeout,
            )
        else:
            os.kill(pid, signal.SIGTERM)
            # graceful 종료 대기
            for _ in range(timeout * 10):
                time.sleep(0.1)
                try:
                    os.kill(pid, 0)
                except OSError:
                    return True
            # 아직 살아있으면 강제 종료
            os.kill(pid, signal.SIGKILL)

        # 종료 확인
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
            return False
        except OSError:
            return True
    except (OSError, subprocess.TimeoutExpired):
        return True


def stop_port_processes(port: int) -> bool:
    """
    특정 포트를 사용 중인 모든 프로세스를 중지합니다.

    Returns:
        True: 모두 중지 성공 또는 실행 중이 아님, False: 일부 중지 실패
    """
    pids = find_pid_by_port(port)
    if not pids:
        return True

    all_stopped = True
    for pid in pids:
        proc_name = get_process_name(pid)
        print(f"  포트 {port}에서 실행 중인 프로세스 발견: PID {pid} ({proc_name})")
        print(f"  PID {pid} 종료 중...")
        if stop_pid(pid):
            print(f"  PID {pid} 종료 완료")
        else:
            print(f"  PID {pid} 종료 실패", file=sys.stderr)
            all_stopped = False
    return all_stopped


# ─────────────────────────────────────────────
# PID 파일 관리
# ─────────────────────────────────────────────

def get_pid_file(project_dir: Path) -> Path:
    """PID 파일 경로를 반환합니다."""
    return project_dir / 'logs' / PID_FILE_NAME


def save_pid(project_dir: Path, pid: int, port: int, platform: str):
    """PID 정보를 파일에 저장합니다."""
    pid_file = get_pid_file(project_dir)
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    data = {
        'pid': pid,
        'port': port,
        'platform': platform,
        'started_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    with open(pid_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def load_pid(project_dir: Path) -> dict:
    """저장된 PID 정보를 읽습니다. 없으면 None 반환."""
    pid_file = get_pid_file(project_dir)
    if not pid_file.exists():
        return None
    try:
        with open(pid_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def remove_pid_file(project_dir: Path):
    """PID 파일을 삭제합니다."""
    pid_file = get_pid_file(project_dir)
    if pid_file.exists():
        pid_file.unlink()


def is_process_alive(pid: int) -> bool:
    """프로세스가 실행 중인지 확인합니다."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}', '/NH'],
                capture_output=True, text=True, timeout=5,
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (OSError, subprocess.TimeoutExpired):
        return False


# ─────────────────────────────────────────────
# 프론트엔드 디렉토리 탐색
# ─────────────────────────────────────────────

def find_frontend_dir(project_dir: Path) -> Path:
    """
    프론트엔드 디렉토리를 탐색합니다.
    우선순위: frontend/ → client/ → web/ → 프로젝트 루트
    """
    candidates = ['frontend', 'client', 'web']
    for name in candidates:
        candidate = project_dir / name
        if candidate.is_dir():
            # package.json 또는 pubspec.yaml이 있는지 확인
            if (candidate / 'package.json').exists() or (candidate / 'pubspec.yaml').exists():
                return candidate

    # 프로젝트 루트에 package.json이 있는 경우 (모노레포가 아닌 경우)
    if (project_dir / 'package.json').exists():
        return project_dir

    # 기본값: frontend/
    return project_dir / 'frontend'


# ─────────────────────────────────────────────
# npm 존재 확인
# ─────────────────────────────────────────────

def find_npm() -> list:
    """
    OS에 맞는 npm 명령을 반환합니다.
    """
    if sys.platform == "win32":
        return ['cmd', '/c', 'npm']
    else:
        return ['npm']


def find_flutter() -> list:
    """
    OS에 맞는 flutter 명령을 반환합니다.
    """
    if sys.platform == "win32":
        return ['cmd', '/c', 'flutter']
    else:
        return ['flutter']


# ─────────────────────────────────────────────
# 액션: start
# ─────────────────────────────────────────────

def action_start(project_dir: Path, frontend_dir: Path, port: int,
                 platform: str, force: bool, background: bool):
    """프론트엔드 개발 서버를 시작합니다."""

    print(f"[START] 프론트엔드 개발 서버")
    print(f"        platform : {platform}")
    print(f"        port     : {port}")
    print(f"        dir      : {frontend_dir}")

    # 기존 포트 점유 확인
    existing_pids = find_pid_by_port(port)
    if existing_pids:
        if force:
            print(f"\n[FORCE] 포트 {port}에서 실행 중인 프로세스를 강제 종료합니다.")
            if not stop_port_processes(port):
                print(f"오류: 포트 {port}의 기존 프로세스를 종료할 수 없습니다.", file=sys.stderr)
                sys.exit(1)
            print()
        else:
            print(f"\n오류: 포트 {port}에서 이미 프로세스가 실행 중입니다. (PID: {existing_pids})")
            print(f"  --force 옵션으로 강제 종료 후 시작할 수 있습니다:")
            print(f"  python3 tools/run-frontend-devserver.py start --force")
            sys.exit(1)

    # 저장된 PID 파일 정리
    saved = load_pid(project_dir)
    if saved and not is_process_alive(saved.get('pid', 0)):
        remove_pid_file(project_dir)

    # 로그 디렉토리 생성
    logs_dir = project_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / 'frontend.log'

    # 플랫폼별 시작 명령 구성
    if platform == 'flutter':
        cmd = find_flutter() + ['run', '-d', 'web-server', '--web-port', str(port)]
    else:
        # React / Vue (npm run dev)
        cmd = find_npm() + ['run', 'dev']

    print(f"        cmd      : {' '.join(cmd)}")
    print(f"        log      : {log_path}")

    if background:
        # 백그라운드 실행
        lf = open(log_path, 'wb')
        proc = subprocess.Popen(
            cmd,
            cwd=str(frontend_dir),
            stdout=lf,
            stderr=subprocess.STDOUT,
            env={**os.environ},
        )
        lf.close()

        # PID 저장
        save_pid(project_dir, proc.pid, port, platform)

        print(f"        pid      : {proc.pid}")
        print()
        print(f"백그라운드로 시작되었습니다.")
        print(f"  상태 확인 : python3 tools/run-frontend-devserver.py status")
        print(f"  로그 확인 : tail -f {log_path}")
        print(f"  중지      : python3 tools/run-frontend-devserver.py stop")
    else:
        # 포그라운드 실행 (Ctrl+C로 종료)
        print()
        print(f"포그라운드 모드로 시작합니다. (Ctrl+C로 종료)")
        print("─" * 50)

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(frontend_dir),
                env={**os.environ},
            )
            # PID 저장
            save_pid(project_dir, proc.pid, port, platform)
            proc.wait()
        except KeyboardInterrupt:
            print(f"\n[INTERRUPT] 프론트엔드 서버를 종료합니다...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        finally:
            remove_pid_file(project_dir)
            # 포트에 남아있는 프로세스 정리
            stop_port_processes(port)


# ─────────────────────────────────────────────
# 액션: stop
# ─────────────────────────────────────────────

def action_stop(project_dir: Path, port: int):
    """프론트엔드 개발 서버를 중지합니다."""

    print(f"[STOP] 프론트엔드 개발 서버  port={port}")

    stopped = False

    # 1. 저장된 PID로 종료 시도
    saved = load_pid(project_dir)
    if saved:
        pid = saved.get('pid', 0)
        if is_process_alive(pid):
            print(f"  저장된 PID {pid} 종료 중...")
            if stop_pid(pid):
                print(f"  PID {pid} 종료 완료")
                stopped = True
            else:
                print(f"  PID {pid} 종료 실패", file=sys.stderr)
        remove_pid_file(project_dir)

    # 2. 포트 기반으로 남은 프로세스 종료
    remaining_pids = find_pid_by_port(port)
    if remaining_pids:
        print(f"  포트 {port}에서 추가 프로세스 발견: PID {remaining_pids}")
        if stop_port_processes(port):
            stopped = True
        else:
            print(f"  일부 프로세스 종료 실패", file=sys.stderr)
            sys.exit(1)

    if stopped:
        print()
        print(f"프론트엔드 서버가 중지되었습니다.")
    else:
        print()
        print(f"실행 중인 프론트엔드 서버를 찾을 수 없습니다. (port={port})")


# ─────────────────────────────────────────────
# 액션: status
# ─────────────────────────────────────────────

def action_status(project_dir: Path, frontend_dir: Path, port: int, platform: str):
    """프론트엔드 개발 서버의 상태를 표시합니다."""

    print(f"프론트엔드 개발 서버 상태")
    print("─" * 50)
    print(f"  platform      : {platform}")
    print(f"  port          : {port}")
    print(f"  frontend dir  : {frontend_dir}")

    # PID 파일 확인
    saved = load_pid(project_dir)
    if saved:
        pid = saved.get('pid', 0)
        alive = is_process_alive(pid)
        print(f"  saved PID     : {pid} ({'실행 중' if alive else '종료됨'})")
        print(f"  started at    : {saved.get('started_at', '?')}")
        if not alive:
            remove_pid_file(project_dir)
    else:
        print(f"  saved PID     : 없음")

    # 포트 상태 확인
    pids = find_pid_by_port(port)
    if pids:
        print(f"  port {port}     : 사용 중")
        for pid in pids:
            proc_name = get_process_name(pid)
            print(f"                  PID {pid} ({proc_name})")
        print()
        print(f"상태: 실행 중 ●")
    else:
        print(f"  port {port}     : 미사용")
        print()
        print(f"상태: 중지됨 ○")

    # 로그 파일 정보
    log_path = project_dir / 'logs' / 'frontend.log'
    if log_path.exists():
        size_kb = log_path.stat().st_size / 1024
        print(f"  로그 파일     : {log_path} ({size_kb:.1f} KB)")


# ─────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="프론트엔드 개발 서버 실행기 (React/Vue/Flutter 자동 감지)",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'action',
        choices=['start', 'stop', 'status'],
        help='수행할 작업 (start: 시작, stop: 중지, status: 상태 확인)',
    )
    parser.add_argument(
        '--project-dir',
        default='.',
        metavar='DIR',
        help='프로젝트 루트 디렉토리 (default: 현재 디렉토리)',
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='기존 포트 점유 프로세스를 강제 종료 후 시작 (start 시에만 유효)',
    )
    parser.add_argument(
        '--background',
        action='store_true',
        help='백그라운드로 실행 (start 시에만 유효)',
    )
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        metavar='PORT',
        help='포트 번호 (미지정 시 .env의 FRONTEND_PORT 또는 3000)',
    )

    args = parser.parse_args()
    project_dir = Path(args.project_dir).resolve()

    if not project_dir.is_dir():
        print(f"오류: 디렉토리를 찾을 수 없습니다: {project_dir}", file=sys.stderr)
        sys.exit(1)

    # 프론트엔드 디렉토리 탐색
    frontend_dir = find_frontend_dir(project_dir)

    # 플랫폼 감지
    platform = detect_platform(frontend_dir)
    if platform == 'unknown' and args.action == 'start':
        print(
            f"오류: 프론트엔드 프로젝트를 찾을 수 없습니다.\n"
            f"  탐색 위치: {frontend_dir}\n"
            f"  package.json 또는 pubspec.yaml이 존재하는지 확인하세요.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 포트 결정
    port = args.port if args.port else read_port_from_env(project_dir)

    # 액션 실행
    if args.action == 'start':
        action_start(project_dir, frontend_dir, port, platform, args.force, args.background)
    elif args.action == 'stop':
        action_stop(project_dir, port)
    elif args.action == 'status':
        action_status(project_dir, frontend_dir, port, platform)


if __name__ == '__main__':
    main()
