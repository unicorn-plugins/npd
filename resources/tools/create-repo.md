# create_repo


- [create_repo](#create_repo)
  - [기본 정보](#기본-정보)
  - [설치 정보](#설치-정보)
  - [명령어](#명령어)
  - [사용 예시](#사용-예시)

---

## 기본 정보

| 항목 | 값 |
|------|---|
| 도구명 | create_repo |
| 카테고리 | 커스텀 앱 |
| 설명 | GitHub REST API 기반 원격 저장소 생성 및 초기 푸시 (gh CLI 불요) |
| 소스 경로 | `resources/tools/customs/git/create_repo.py` |

[Top](#create_repo)

---

## 설치 정보

| 항목 | 값 |
|------|---|
| 설치 방법 | 소스 파일 포함 (별도 설치 불요) |
| 의존성 설치 | 없음 (Python 표준 라이브러리만 사용) |
| 검증 명령 | `python resources/tools/customs/git/create_repo.py --help` |
| 필수 여부 | 선택 |

**사전 요구사항:**

| 항목 | 최소 버전 | 비고 |
|------|----------|------|
| Python | 3.7+ | 표준 라이브러리만 사용 (urllib, subprocess) |
| Git | 2.0+ | 로컬 저장소 초기화 및 푸시에 필요 |
| GitHub PAT | - | `repo` 권한 필수. 발급: https://github.com/settings/tokens |

[Top](#create_repo)

---

## 명령어

| 파라미터 | 필수 | 설명 | 기본값 |
|---------|:----:|------|--------|
| `--name` | 필수 | 저장소 이름 | - |
| `--token` | 택1 | GitHub Personal Access Token | `GITHUB_TOKEN` 환경변수 |
| `--desc` | 선택 | 저장소 설명 | `""` (빈 문자열) |
| `--private` | 선택 | 비공개 저장소로 생성 | `False` (공개) |
| `--org` | 선택 | 조직 이름 (미지정 시 개인 계정) | - |
| `--dir` | 선택 | 로컬 디렉토리 경로 | `.` (현재 디렉토리) |
| `--no-push` | 선택 | 초기 푸시 건너뛰기 | `False` |

> `--token`과 `GITHUB_TOKEN` 환경변수 중 하나 필수.
> 우선순위: `--token` 인자 > `GITHUB_TOKEN` 환경변수.

**실행 흐름:**

1. 입력 검증 (토큰, 저장소 이름)
2. GitHub REST API로 원격 저장소 생성
3. 로컬 디렉토리가 Git 저장소가 아니면 `git init`
4. `git remote add origin <clone_url>`
5. 커밋 없으면 초기 커밋 생성
6. `git push -u origin <branch>`

[Top](#create_repo)

---

## 사용 예시

```bash
# 공개 저장소 생성 + 초기 푸시
python create_repo.py --name my-project --token ghp_xxxxx

# 설명 추가
python create_repo.py --name my-project --desc "프로젝트 설명" --token ghp_xxxxx

# 비공개 저장소
python create_repo.py --name my-project --private --token ghp_xxxxx

# 조직 저장소
python create_repo.py --name my-project --org my-company --token ghp_xxxxx

# 특정 디렉토리 지정
python create_repo.py --name my-project --dir C:\path\to\project --token ghp_xxxxx

# 원격 저장소만 생성 (푸시 건너뛰기)
python create_repo.py --name my-project --no-push --token ghp_xxxxx

# 환경변수로 토큰 설정 (Windows CMD)
set GITHUB_TOKEN=ghp_xxxxx
python create_repo.py --name my-project
```

[Top](#create_repo)
