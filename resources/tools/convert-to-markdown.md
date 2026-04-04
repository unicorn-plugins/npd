# convert-to-markdown


- [convert-to-markdown](#convert-to-markdown)
  - [기본 정보](#기본-정보)
  - [설치 정보](#설치-정보)
  - [환경 변수](#환경-변수)
  - [명령어](#명령어)
  - [변환 동작](#변환-동작)
  - [사용 예시](#사용-예시)

---

## 기본 정보

| 항목 | 값 |
|------|---|
| 도구명 | convert-to-markdown |
| 카테고리 | 커스텀 앱 |
| 설명 | Office 문서(pptx, docx, xlsx)를 Markdown으로 변환하는 도구. 이미지 추출 후 Groq VLM으로 설명 자동 생성 |
| 소스 경로 | `resources/tools/customs/general/convert-to-markdown.py` |

[Top](#convert-to-markdown)

---

## 설치 정보

| 항목 | 값 |
|------|---|
| 설치 방법 | 소스 파일 포함 (의존성 설치 필요) |
| 의존성 설치 | `pip install python-dotenv python-pptx python-docx openpyxl groq Pillow` |
| 검증 명령 | `python tools/general/convert-to-markdown.py --help` |
| 필수 여부 | 선택 |

[Top](#convert-to-markdown)

---

## 환경 변수

| 변수명 | 필수 | 설명 | 기본값 |
|--------|:----:|------|--------|
| `GROQ_API_KEY` | 선택 | Groq API Key (이미지 설명 생성에 필요) | - |

> 환경 변수 파일 위치: `tools/.env`  
> 미설정 시 이미지 설명은 `(GROQ_API_KEY 미설정 - 이미지 설명 생략)`으로 대체됨.

**VLM 모델:** `meta-llama/llama-4-scout-17b-16e-instruct` (Groq)

[Top](#convert-to-markdown)

---

## 명령어

```bash
python tools/general/convert-to-markdown.py [input_dir] [output_dir]
```

| 인자 | 필수 | 설명 | 기본값 |
|------|:----:|------|--------|
| `input_dir` | 선택 | 변환할 Office 문서가 있는 디렉토리 | `resources/references` |
| `output_dir` | 선택 | 변환된 Markdown 파일 출력 디렉토리 | `resources/references/markdown` |

**지원 형식:**

| 확장자 | 설명 |
|--------|------|
| `.pptx` | PowerPoint 프레젠테이션 |
| `.docx` | Word 문서 |
| `.xlsx` | Excel 스프레드시트 |

[Top](#convert-to-markdown)

---

## 변환 동작

**공통 동작:**
- 입력 디렉토리의 지원 형식 파일을 일괄 변환
- 추출된 이미지는 `{output_dir}/images/{파일명}/` 에 저장
- Markdown 내 이미지 참조는 상대 경로(`images/{파일명}/...`) 사용

**이미지 필터링:**

| 조건 | 처리 |
|------|------|
| 150×150px 미만 또는 5KB 미만 | 아이콘/장식으로 간주, VLM 분석 생략 |
| 4MB 초과 | JPEG로 자동 리사이즈 후 분석 |
| 분석 가능한 이미지 | Groq VLM으로 한국어 설명 생성 |

**포맷별 변환 규칙:**

| 형식 | 변환 규칙 |
|------|----------|
| PPTX | 슬라이드별 섹션(`## 슬라이드 N`) 생성, 폰트 크기 기반 헤딩 변환(24pt→`###`, 18pt→`####`), 테이블·이미지 포함 |
| DOCX | Word 스타일 기반 헤딩 변환(`Heading 1`→`##` 등), 인라인 이미지 위치 추적, Bold/Italic 인라인 서식 유지 |
| XLSX | 시트별 섹션(`## {시트명}`) 생성, 전체 셀 데이터를 Markdown 테이블로 변환, 시트 내 이미지 포함 |

**Rate limit 처리:**  
Groq API 429 응답 시 최대 3회 재시도, 15초 간격으로 대기.

[Top](#convert-to-markdown)

---

## 사용 예시

```bash
# 기본값으로 실행 (resources/references → resources/references/markdown)
python tools/general/convert-to-markdown.py

# 입력/출력 디렉토리 직접 지정
python tools/general/convert-to-markdown.py ./docs ./docs/md

# GROQ_API_KEY 없이 실행 (이미지 설명 생략)
python tools/general/convert-to-markdown.py
# 경고: GROQ_API_KEY가 설정되지 않았습니다. 이미지 설명이 생략됩니다.
```

**출력 구조 예시 (sample.pptx 변환 시):**

```
output_dir/
├── sample.md
└── images/
    └── sample/
        ├── slide01_img01.png
        ├── slide01_img02.jpg
        └── slide02_img01.png
```

**실행 결과 출력 예시:**

```
변환 중: sample.pptx ...
    [VLM] slide01_img01.png 분석 중... 완료
    [SKIP] slide01_img02.png (아이콘/장식)
-> sample.md (이미지 2개)

완료: 1개 문서 변환, 총 이미지 1개 처리, 0개 오류
```

[Top](#convert-to-markdown)
