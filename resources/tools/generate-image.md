# generate_image


- [generate\_image](#generate_image)
  - [기본 정보](#기본-정보)
  - [설치 정보](#설치-정보)
  - [환경 변수](#환경-변수)
  - [명령어](#명령어)
  - [사용 예시](#사용-예시)

---

## 기본 정보

| 항목 | 값 |
|------|---|
| 도구명 | generate_image |
| 카테고리 | 커스텀 앱 |
| 설명 | Gemini (Nano Banana) 모델 기반 이미지 생성 도구 |
| 소스 경로 | `resources/tools/customs/general/generate_image.py` |

[Top](#generate_image)

---

## 설치 정보

| 항목 | 값 |
|------|---|
| 설치 방법 | 소스 파일 포함 (의존성 설치 필요) |
| 의존성 설치 | `pip install python-dotenv google-genai` |
| 검증 명령 | `python tools/general/generate_image.py --help` |
| 필수 여부 | 선택 |

[Top](#generate_image)

---

## 환경 변수

| 변수명 | 필수 | 설명 | 기본값 |
|--------|:----:|------|--------|
| `GEMINI_API_KEY` | 필수 | Google Gemini API Key | - |

> 환경 변수 파일 위치: `tools/.env`
> 또는 `--api-key` 파라미터로 직접 전달 가능.

[Top](#generate_image)

---

## 명령어

| 파라미터 | 필수 | 설명 | 기본값 |
|---------|:----:|------|--------|
| `--prompt` | 택1 | 이미지 생성 프롬프트 텍스트 | - |
| `--prompt-file` | 택1 | 프롬프트가 담긴 파일 경로 | - |
| `--output-dir` | 선택 | 출력 디렉토리 | `.` (현재 디렉토리) |
| `--output-name` | 선택 | 출력 파일명 (확장자 제외) | `generated_image` |
| `--api-key` | 선택 | Gemini API Key (환경 변수 대체) | - |

> `--prompt`와 `--prompt-file`은 상호 배타적 (둘 중 하나 필수).

[Top](#generate_image)

---

## 사용 예시

```bash
# 프롬프트 직접 입력
python tools/general/generate_image.py --prompt "아침 바다를 걷는 여성"

# 프롬프트 파일 사용
python tools/general/generate_image.py --prompt-file prompt.txt --output-dir ./images

# 출력 파일명 지정
python tools/general/generate_image.py --prompt "sunset beach" --output-dir ./results --output-name beach_sunset

# API Key 직접 전달
python tools/general/generate_image.py --prompt "테스트" --api-key YOUR_API_KEY
```

> 기본 시스템 프롬프트: 흰색 배경(#FFFFFF), 한글 텍스트 우선,
> 고유명사(SKILL.md, Haiku 등)만 영문 허용.

[Top](#generate_image)
