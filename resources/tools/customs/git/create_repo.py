#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 원격 저장소 생성 및 초기 푸시 스크립트
gh CLI 없이 GitHub REST API를 사용하여 저장소를 생성합니다.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Windows에서 한글 및 이모지 출력을 위한 UTF-8 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def print_error(message):
    """에러 메시지 출력"""
    print(f"❌ 오류: {message}", file=sys.stderr)


def print_success(message):
    """성공 메시지 출력"""
    print(f"✅ {message}")


def print_info(message):
    """정보 메시지 출력"""
    print(f"ℹ️  {message}")


def validate_git_installed():
    """Git이 설치되어 있는지 확인"""
    try:
        subprocess.run(
            ["git", "--version"],
            capture_output=True,
            check=True,
            text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("Git이 설치되어 있지 않습니다. https://git-scm.com 에서 설치해주세요.")
        return False


def get_github_token(args_token):
    """
    GitHub Personal Access Token 가져오기
    우선순위: 1) --token 인자, 2) GITHUB_TOKEN 환경변수
    """
    if args_token:
        return args_token

    # 환경변수 확인
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token

    print_error("GitHub Personal Access Token을 찾을 수 없습니다.")
    print_info("다음 중 하나의 방법으로 토큰을 제공해주세요:")
    print_info("  1. --token 인자 사용: python create_repo.py --token YOUR_TOKEN")
    print_info("  2. 환경변수 설정: set GITHUB_TOKEN=YOUR_TOKEN (Windows)")
    print_info("")
    print_info("토큰 생성 방법: https://github.com/settings/tokens")
    print_info("필요한 권한: repo (전체 저장소 제어)")
    return None


def validate_repo_name(name):
    """저장소 이름 유효성 검사"""
    if not name:
        print_error("저장소 이름은 필수입니다.")
        return False

    # GitHub 저장소 이름 규칙: 영문, 숫자, 하이픈, 언더스코어
    # 하이픈으로 시작하거나 끝날 수 없음
    if name.startswith("-") or name.endswith("-"):
        print_error("저장소 이름은 하이픈(-)으로 시작하거나 끝날 수 없습니다.")
        return False

    return True


def create_github_repo(token, name, description, private, org=None):
    """
    GitHub REST API를 사용하여 원격 저장소 생성

    Returns:
        dict: 생성된 저장소 정보 (clone_url, html_url 등 포함)
        None: 실패 시
    """
    # API 엔드포인트 결정
    if org:
        url = f"https://api.github.com/orgs/{org}/repos"
    else:
        url = "https://api.github.com/user/repos"

    # 요청 데이터
    data = {
        "name": name,
        "description": description,
        "private": private
    }

    # HTTP 요청 준비
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get("message", "알 수 없는 오류")

            if e.code == 422 and "already exists" in error_msg.lower():
                print_error(f"저장소 '{name}'이(가) 이미 존재합니다.")
                print_info("다른 이름을 사용하거나 기존 저장소를 삭제해주세요.")
            elif e.code == 401:
                print_error("인증 실패: 토큰이 유효하지 않습니다.")
            elif e.code == 404 and org:
                print_error(f"조직 '{org}'을(를) 찾을 수 없거나 접근 권한이 없습니다.")
            else:
                print_error(f"GitHub API 오류 ({e.code}): {error_msg}")
        except json.JSONDecodeError:
            print_error(f"GitHub API 오류 ({e.code}): {error_body}")
        return None
    except urllib.error.URLError as e:
        print_error(f"네트워크 오류: {e.reason}")
        print_info("인터넷 연결을 확인해주세요.")
        return None
    except Exception as e:
        print_error(f"예상치 못한 오류: {e}")
        return None


def is_git_repo(directory):
    """디렉토리가 Git 저장소인지 확인"""
    git_dir = Path(directory) / ".git"
    return git_dir.exists()


def init_git_repo(directory):
    """Git 저장소 초기화"""
    try:
        result = subprocess.run(
            ["git", "init"],
            cwd=directory,
            capture_output=True,
            check=True,
            text=True
        )
        print_success(f"Git 저장소 초기화 완료: {directory}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Git 초기화 실패: {e.stderr}")
        return False


def get_current_branch(directory):
    """현재 브랜치 이름 가져오기"""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=directory,
            capture_output=True,
            check=True,
            text=True
        )
        branch = result.stdout.strip()
        # 브랜치가 없으면 (초기 상태) main 사용
        return branch if branch else "main"
    except subprocess.CalledProcessError:
        return "main"


def has_commits(directory):
    """커밋이 존재하는지 확인"""
    try:
        subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=directory,
            capture_output=True,
            check=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_remote_url(directory, remote_name="origin"):
    """원격 저장소 URL 가져오기"""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", remote_name],
            cwd=directory,
            capture_output=True,
            check=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def sanitize_remote_url(url):
    """
    원격 URL에서 토큰 제거 (보안)
    https://TOKEN@github.com/... → https://github.com/...
    """
    import re
    # 토큰 패턴: https://TOKEN@github.com 형태
    pattern = r'https://[^@]+@github\.com/'
    if re.search(pattern, url):
        sanitized = re.sub(r'https://[^@]+@', 'https://', url)
        print_info(f"⚠️  보안: 원격 URL에서 토큰을 제거했습니다.")
        return sanitized
    return url


def add_remote(directory, remote_url, remote_name="origin"):
    """원격 저장소 추가 또는 업데이트"""
    # 보안: URL에서 토큰 제거
    remote_url = sanitize_remote_url(remote_url)

    existing_url = get_remote_url(directory, remote_name)

    if existing_url:
        print_info(f"원격 저장소 '{remote_name}'이(가) 이미 존재합니다: {existing_url}")

        if existing_url == remote_url:
            print_success("URL이 동일하여 변경하지 않습니다.")
            return True

        # 사용자에게 확인
        print_info(f"새 URL로 업데이트: {remote_url}")
        try:
            response = input("계속하시겠습니까? (y/N): ").strip().lower()
            if response not in ["y", "yes"]:
                print_info("원격 저장소 업데이트를 취소했습니다.")
                return False
        except (KeyboardInterrupt, EOFError):
            print()
            print_info("원격 저장소 업데이트를 취소했습니다.")
            return False

        # 기존 원격 저장소 제거
        try:
            subprocess.run(
                ["git", "remote", "remove", remote_name],
                cwd=directory,
                capture_output=True,
                check=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print_error(f"기존 원격 저장소 제거 실패: {e.stderr}")
            return False

    # 원격 저장소 추가
    try:
        subprocess.run(
            ["git", "remote", "add", remote_name, remote_url],
            cwd=directory,
            capture_output=True,
            check=True,
            text=True
        )
        print_success(f"원격 저장소 '{remote_name}' 추가 완료: {remote_url}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"원격 저장소 추가 실패: {e.stderr}")
        return False


def create_initial_commit(directory):
    """초기 커밋 생성"""
    try:
        # 모든 파일 스테이징
        subprocess.run(
            ["git", "add", "."],
            cwd=directory,
            capture_output=True,
            check=True,
            text=True
        )

        # 스테이징된 파일이 있는지 확인
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=directory,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # 스테이징된 파일이 없으면 빈 커밋 생성
            print_info("스테이징된 파일이 없어 빈 커밋을 생성합니다.")
            subprocess.run(
                ["git", "commit", "--allow-empty", "-m", "Initial commit"],
                cwd=directory,
                capture_output=True,
                check=True,
                text=True
            )
        else:
            # 일반 커밋
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=directory,
                capture_output=True,
                check=True,
                text=True
            )

        print_success("초기 커밋 생성 완료")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"커밋 생성 실패: {e.stderr}")
        return False


def push_to_remote(directory, branch, remote_name="origin", token=None):
    """
    원격 저장소로 푸시
    토큰이 제공되면 일회성으로 사용 (원격 URL에 저장하지 않음)
    """
    try:
        print_info(f"원격 저장소로 푸시 중: {remote_name}/{branch}")

        # 토큰이 있으면 일회성 URL 생성
        if token:
            # 현재 원격 URL 가져오기
            remote_url = get_remote_url(directory, remote_name)
            if not remote_url:
                print_error(f"원격 저장소 '{remote_name}'을(를) 찾을 수 없습니다.")
                return False

            # 토큰을 포함한 일회성 URL 생성
            # https://github.com/... → https://TOKEN@github.com/...
            if remote_url.startswith("https://github.com/"):
                push_url = remote_url.replace("https://github.com/", f"https://{token}@github.com/")
            else:
                push_url = remote_name  # SSH 등 다른 프로토콜

            # 일회성 URL로 푸시
            result = subprocess.run(
                ["git", "push", "-u", push_url, branch],
                cwd=directory,
                capture_output=True,
                check=True,
                text=True
            )
        else:
            # 토큰 없으면 일반 푸시 (credential helper 사용)
            result = subprocess.run(
                ["git", "push", "-u", remote_name, branch],
                cwd=directory,
                capture_output=True,
                check=True,
                text=True
            )

        print_success(f"원격 저장소로 푸시 완료: {remote_name}/{branch}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"푸시 실패: {e.stderr}")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="GitHub 원격 저장소 생성 및 초기 푸시",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python create_repo.py --name my-project --desc "내 프로젝트"
  python create_repo.py --name my-project --private --token ghp_xxxxx
  python create_repo.py --name my-project --org my-org --dir ./my-project
  python create_repo.py --name my-project --no-push
        """
    )

    parser.add_argument(
        "--name",
        required=True,
        help="저장소 이름 (필수)"
    )
    parser.add_argument(
        "--desc",
        default="",
        help="저장소 설명 (선택, 기본값: 빈 문자열)"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="비공개 저장소로 생성 (기본값: 공개)"
    )
    parser.add_argument(
        "--token",
        help="GitHub Personal Access Token (선택, GITHUB_TOKEN 환경변수 사용 가능)"
    )
    parser.add_argument(
        "--org",
        help="조직 이름 (선택, 기본값: 개인 계정)"
    )
    parser.add_argument(
        "--dir",
        default=".",
        help="로컬 디렉토리 경로 (기본값: 현재 디렉토리)"
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="초기 푸시 건너뛰기 (원격 저장소 생성 및 origin 추가만 수행)"
    )

    args = parser.parse_args()

    # 1. Git 설치 확인
    if not validate_git_installed():
        return 1

    # 2. 저장소 이름 유효성 검사
    if not validate_repo_name(args.name):
        return 1

    # 3. GitHub 토큰 가져오기
    token = get_github_token(args.token)
    if not token:
        return 1

    # 4. 디렉토리 경로 정규화
    directory = Path(args.dir).resolve()
    if not directory.exists():
        print_error(f"디렉토리를 찾을 수 없습니다: {directory}")
        return 1

    print_info(f"작업 디렉토리: {directory}")

    # 5. GitHub에 원격 저장소 생성
    print_info(f"GitHub에 저장소 생성 중: {args.name}")
    repo_info = create_github_repo(
        token=token,
        name=args.name,
        description=args.desc,
        private=args.private,
        org=args.org
    )

    if not repo_info:
        return 1

    clone_url = repo_info["clone_url"]
    html_url = repo_info["html_url"]

    print_success(f"GitHub 저장소 생성 완료: {html_url}")

    # 6. Git 저장소 초기화 (필요시)
    if not is_git_repo(directory):
        print_info("Git 저장소가 아닙니다. 초기화합니다.")
        if not init_git_repo(directory):
            return 1

    # 7. 원격 저장소 추가
    if not add_remote(directory, clone_url):
        return 1

    # 8. 초기 푸시 (--no-push 옵션이 없을 때만)
    if not args.no_push:
        # 커밋이 없으면 생성
        if not has_commits(directory):
            print_info("커밋이 없습니다. 초기 커밋을 생성합니다.")
            if not create_initial_commit(directory):
                return 1

        # 현재 브랜치 확인
        branch = get_current_branch(directory)

        # 푸시 (토큰을 일회성으로 사용)
        if not push_to_remote(directory, branch, token=token):
            return 1

        print_success(f"🎉 모든 작업이 완료되었습니다!")
        print_info(f"저장소 URL: {html_url}")
    else:
        print_success("원격 저장소 생성 및 origin 추가가 완료되었습니다.")
        print_info(f"저장소 URL: {html_url}")
        print_info("푸시는 수동으로 수행해주세요: git push -u origin main")

    return 0


if __name__ == "__main__":
    sys.exit(main())
