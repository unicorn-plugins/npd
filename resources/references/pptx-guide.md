# 제안서 스타일 PPT 작성 가이드 (proposal-pptx-build-guide)

## 0. 패턴 개요 (Spec Agent + Orchestrator Builder)

제안서형 PPT 생성은 **2단계 분리 구조**를 따름:

```
[사용자 요구]
     ↓
[pptx-spec-writer 에이전트]  ← 시각 명세 .md 작성 (패턴 A~E 매핑, 슬라이드별 콘텐츠/디자인 의도)
     ↓
[Builder Skill (오케스트레이터)]
  1. 본 가이드 로드
  2. spec.md 분석 → pptxgenjs 빌드 코드 작성
  3. node 실행 → .pptx 생성 → 개체 틀 번호 정리(6-14)
  4. 붙여넣기 호환 점검(6-13) + 파일 검증 + 사용자 보고
     ↓
[*.pptx 산출물]
```

**원칙**:
- 에이전트는 **명세만 산출** (실행 도구 비포함 → Cursor/Cowork 등 모든 런타임 호환)
- 오케스트레이터(스킬)가 **빌드+실행+검증** 수행 (Write + Bash 도구만 필요)
- 외부 변환 스킬 의존 금지
- 빌더 스킬은 본 가이드 6절(코드 생성 시 필수 검증 규칙)을 **반드시 준수**

**런타임 요구사항**: `node ≥ 18`, `npm i pptxgenjs`  
**미리보기 요구사항**: LibreOffice(`soffice`), `pip install pymupdf`

---

## 대상 덱 붙여넣기 호환 (필수)

새로 만드는 모든 덱은 **강의 본 덱에 슬라이드를 복사-붙여넣기해도 모양이 그대로 유지**되어야 함.  
기준 덱: `~/Documents/강의/신한카드/신한카드 하이브리드AI_W01~W04.pptx` (콘텐츠 레이아웃 `내용_단쪽`)

### 왜 필요한가
- PowerPoint의 기본 붙여넣기(Ctrl+V = **대상 테마 사용**)는 붙여 넣는 슬라이드를  
  **이름이 같은 대상 덱 레이아웃**에 연결함. 같은 이름이 없으면 원본 레이아웃을 대상 덱에 새로 복사해 넣음
- 실제 사례: 이전 pptxgenjs 덱의 `MASTER`, `DEFAULT` 레이아웃이 본 덱 마스터에 섞여 들어가 있음
- 기존 가이드 형식(경로 표시 + 48pt 제목 + 밑줄 + 「n / m」 쪽 표시)은 본 덱의 제목, 구분선, 쪽 번호와  
  겹쳐서, 붙여 넣을 때마다 손으로 고쳐야 했음

### 호환 규칙 7가지

| # | 규칙 | 지키지 않으면 |
|---|------|--------------|
| 1 | 슬라이드 크기 16″ × 9″ (14630400 × 8229600 EMU) | 붙여 넣을 때 도형이 늘어나거나 줄어듦 |
| 2 | 콘텐츠 레이아웃 이름을 정확히 **`내용_단쪽`** 으로 지음 (`defineSlideMaster({ title: "내용_단쪽" })`) | 본 덱에 `MASTER` 같은 낯선 레이아웃이 추가됨 |
| 3 | 모든 콘텐츠 슬라이드를 `addSlide({ masterName: "내용_단쪽" })`로 만듦 | `masterName`을 빼면 `DEFAULT` 레이아웃이 따라 들어감 |
| 4 | 장 제목은 텍스트 상자가 아니라 **제목 개체 틀**(`placeholder: "title"`)에 넣음 | 본 덱 제목의 서식과 위치를 따르지 않고 따로 놂 |
| 5 | 쪽 번호는 레이아웃의 `slideNumber`로만 표시함. 「1 / 19」 같은 글자 쪽 표시 금지 | 붙여 넣은 뒤 쪽 번호가 두 개가 됨 |
| 6 | 경로 표시(breadcrumb), 제목 밑줄, 「무단전재 및 배포 금지」 문구를 슬라이드에 직접 그리지 않음 | 본 덱 레이아웃의 구분선이나 문구와 겹침 |
| 7 | 모든 색은 HEX 직접 지정, 모든 글자에 `fontFace` 직접 지정 (테마 색과 테마 글꼴 금지) | 본 덱 테마 글꼴이 Calibri라 글꼴이 바뀌고, 테마 색이 다른 색으로 바뀜 |

### 기준 덱 `내용_단쪽` 레이아웃 실측값 (2026-10-04)

| 요소 | 위치 x, y (인치) | 크기 w × h (인치) | 서식 | 비고 |
|------|------------------|-------------------|------|------|
| 제목 개체 틀 | 0.557, 0.109 | 15.025 × 0.906 | Pretendard 32pt Bold `#2C2926`, 왼쪽 정렬 | `type="title"` |
| 제목 아래 구분선 | 0.556, 0.95 | 14.888 × 0 | `#E2E8F0`, 1.5pt | 레이아웃 소유 |
| 쪽 번호 | 11.913, 8.517 | 3.6 × 0.25 | Pretendard 16pt `#6B6B7B`, 오른쪽 정렬 | `type="sldNum"` |
| 「무단전재 및 배포 금지」 | 0.4875, 8.517 | 1.675 × 0.27 | Pretendard 12pt 회색 | 기준 덱 마스터 소유 |

### 붙여넣기 절차 (사람이 수행)
1. 새 덱에서 슬라이드 선택 → Ctrl+C
2. 본 덱에서 넣을 위치 앞 슬라이드 선택 → Ctrl+V (붙여넣기 옵션 **대상 테마 사용**)
3. 보기 → 슬라이드 마스터에서 `MASTER`나 `DEFAULT` 같은 새 레이아웃이 생기지 않았는지 확인

---

## 미리보기와 렌더링 검증 (PowerPoint COM 금지)

- 슬라이드를 그림으로 확인할 때는 **LibreOffice headless만 사용**함
  ```
  python scripts/render-pptx.py {덱}.pptx --out {출력폴더}
  ```
  → `{출력폴더}/{덱}.pdf` + `slide-1.png ...` 생성
- **PowerPoint COM 자동화 금지**: `New-Object -ComObject PowerPoint.Application`, `win32com`, `comtypes`,  
  `Slide.Export()` 등으로 PowerPoint를 띄우는 스크립트를 만들지 않음
  - 이유: PowerPoint는 컴퓨터 전체에서 한 프로세스만 실행됨. 스크립트가 사용자가 열어 둔 창에 붙어
    작업이 섞이고, 마지막 `Quit()`가 사용자 창까지 닫아 크래시처럼 보임. 도구 시간 초과로 중간에 끊기면
    숨은 POWERPNT.EXE가 남아 다음 실행이 먹통이 됨
- 직접 `soffice`를 부를 때도 전용 임시 프로필(`-env:UserInstallation=file:///...`)을 붙여  
  사용자가 열어 둔 LibreOffice 창과 섞이지 않게 함
- LibreOffice 렌더링은 PowerPoint에 비해 글꼴과 줄바꿈이 조금 다를 수 있음. "PowerPoint에서 확인함"이라고 보고하지 않고  
  "LibreOffice 미리보기로 확인함"이라고 보고함

---

## 생성된 이미지 임베딩
- 스크립트에 아래 예와 같이 이미지 링크가 있으면 그 이미지를 페이지에 임베딩
  ```
  ![서비스 방향성 다이어그램](images/service_direction.png)
  ```
- 벤치마크나 결과물 화면 캡처는 동일 비율로 정렬하여 그리드 배치하고, 필 라벨로 화면명을 표기

---

## PPT 스타일시트

> 이 스타일은 표준 컨설팅 제안서(딥 네이비 + 브라이트 블루) 디자인 언어를 기준으로 함.
> 흰색 배경 위에 컬러 헤더 바, 넘버 배지, 틴트 카드를 배치하는 정갈한 코퍼레이트 톤.

### 1. 컬러 팔레트

#### 메인 컬러

| 역할 | 컬러명 | HEX | 용도 |
|------|--------|-----|------|
| Title | Charcoal | `#2C2926` | 장 제목 (기준 덱 `내용_단쪽` 제목색) |
| Lead | Black | `#000000` | 리드문(제목 아래 한 문장) |
| Primary | Deep Navy | `#1E2A5C` | 헤더 바(좌), 넘버 배지, 주요 텍스트 |
| Sub | Bright Blue | `#2E74C6` | 강조 헤더 바, 배지, 불릿 |
| Text Body | Ink | `#2B3242` | 본문 텍스트 |
| Text Secondary | Slate | `#4A5364` | 설명과 부연 텍스트 |
| Text Tertiary | Sub Gray | `#7C8598` | 캡션, 출처, 메타데이터 |
| Background (Master) | White | `#FFFFFF` | 슬라이드 마스터 배경 |
| Background (Content) | White | `#FFFFFF` | 콘텐츠 영역 배경 사각형 |

#### 보조 컬러와 배경 컬러

| 용도 | HEX | 설명 |
|------|-----|------|
| 틴트 박스 배경 | `#EEF3FA` | Light Blue — 요약 카드와 정보 카드 배경 |
| 대체 행/카드 배경 | `#F5F8FC` | Pale Blue — 리스트 항목, 표 짝수행 |
| 테이블 헤더 행 | `#E2EEF9` | Soft Blue — 표 헤더행 배경 |
| 다크 배지 | `#404155` | Dark Slate — 섹션 라벨, WHAT 라벨 |
| 카드 테두리 / 구분선 | `#D9E0EC` | Cool Gray — 카드 경계, 헤더 언더라인 바탕 |
| 미세 구분선 | `#EDF0F6` | Light Gray — 표 행 구분, 리스트 구분 |
| 출처 구분선 | `#E9ECF3` | Light Gray — 출처 줄 위 라인 |
| 제목 아래 구분선 | `#E2E8F0` | 레이아웃 소유 — 슬라이드에 직접 그리지 않음 |

#### 헤더 바 색

| 용도 | 값 | 설명 |
|------|-----|------|
| 강조 헤더 바 | `#2E74C6` 단색 | 우측 강조 섹션(추진 전략, 주요 결과물 등) |
| 단색 헤더 바 | `#1E2A5C` | 좌측 기본 섹션(목적 등) |

- pptxgenjs는 그라디언트 채우기를 지원하지 않음 → 헤더 바는 단색만 사용
- 표지와 구분 슬라이드는 새 덱에서 만들지 않음 (3절 패턴 E 참조)

---

### 2. 타이포그래피

#### 서체 시스템

| 서체 | 용도 | 비고 |
|------|------|------|
| **Pretendard** | 주 서체 (제목, 헤더, 본문, 캡션) | Variable Weight, 한/영 통합 |
| **Arial** | 영문 폴백 | 범용 |

#### 텍스트 스타일 가이드

| 요소 | 서체 | 굵기 | 크기 | 색상 |
|------|------|------|------|------|
| 장 제목 (제목 개체 틀) | **Pretendard** | Bold | 32pt | `#2C2926` |
| 리드문 (제목 아래 한 문장) | **Pretendard SemiBold** | SemiBold | 18pt | `#000000` |
| 섹션 헤더 바 텍스트 | **Pretendard** | Bold | 24pt | `#FFFFFF` |
| 섹션 헤더(본문) | **Pretendard** | Bold | 24pt | `#1E2A5C` |
| 본문 강조 텍스트 | **Pretendard** | Bold | 21pt | `#2B3242` |
| 본문 일반 텍스트 | **Pretendard** | Regular | 18pt | `#3B4557` |
| 카드 내 텍스트 | **Pretendard** | Regular | 16pt | `#4A5364` |
| 캡션 / 출처 | **Pretendard** | Regular | 14pt | `#7C8598` |

- 섹션 헤더(본문)는 장 제목(32pt)보다 작아야 위계가 섬 → 24pt
- 경로 표시(breadcrumb)는 쓰지 않음 (붙여넣기 호환 규칙 6)

#### 굵기 스케일
`Regular 400`, `SemiBold 600`, `Bold 700`, `ExtraBold 800`

---

### 3. 레이아웃 가이드

#### 슬라이드 사양

| 항목 | 값 |
|------|------|
| 크기 | 16″ × 9″ (1152 × 648pt, 16:9) |
| 레이아웃 이름 | `내용_단쪽` (붙여넣기 호환 규칙 2) |
| 콘텐츠 왼쪽 끝 x | 0.557″ (제목 개체 틀과 같은 선) |
| 콘텐츠 폭 | 14.9″ (오른쪽 끝 15.457″) |
| 마스터 배경 | `#FFFFFF` (White) |
| 콘텐츠 영역 | 흰색 배경 위 카드/헤더 바로 구성 |
| 푸터 | 좌측 「무단전재 및 배포 금지」 + 우측 쪽 번호 — **레이아웃 요소, 슬라이드에 그리지 않음** |

#### 세로 영역 구분 (모든 콘텐츠 슬라이드 공통)

```
y 0.109 ~ 1.015″  ① 장 제목      제목 개체 틀 (32pt Bold #2C2926) — 레이아웃이 위치와 서식 소유
y 0.95″           ② 제목 구분선   레이아웃 소유 (#E2E8F0) — 슬라이드에 그리지 않음
y 1.259 ~ 1.679″  ③ 리드문(선택)  한 문장 요약 (Pretendard SemiBold 18pt #000000, 한 줄)
y 1.90 ~ 7.95″    ④ 본문         카드, 표, 도식 (리드문이 없으면 1.45″부터 시작 가능)
y 8.08″           ⑤ 출처 구분선   전폭 #E9ECF3 1pt (출처가 있을 때만)
y 8.14 ~ 8.46″    ⑥ 출처 문구     Pretendard 14pt #7C8598, 반드시 한 줄
y 8.5″ 아래        ⑦ 푸터 영역     「무단전재 및 배포 금지」 + 쪽 번호 — 레이아웃 소유, 콘텐츠 배치 금지
```

- 출처 문구가 한 줄을 넘으면 「무단전재 및 배포 금지」 문구와 겹침  
  → 140자 이하로 줄이거나, 12pt + 전폭(14.9″)으로 바꿈 (12pt는 출처 문구에만 허용)
- 본문 아래 끝은 7.95″를 넘지 않음 (출처 구분선과 최소 0.1″ 간격)

#### 레이아웃 패턴

**패턴 A: 목적 / 추진 전략 (2단 헤더 바)**
- 좌측: 단색 네이비 헤더 바(`목적`) + 틴트 박스 요약(이탤릭 Bold 강조)
- 우측: 그라디언트 헤더 바(`추진 전략`) + 넘버 스퀘어 배지 항목 리스트
- 적합: 제안의 목적과 핵심 전략 압축, 방향성 개요

**패턴 B: WHY / HOW / WHAT (3행: 목표, 방안, 결과)**
- 좌측: 그라디언트 헤더 바 아래 3개 행
  - WHY(목표) = 네이비 라벨 셀, HOW(수행 방안) = 블루 라벨 셀, WHAT(핵심 결과) = 다크 슬레이트 라벨 셀
  - 각 라벨 셀은 영문 대문자 + 한글 부제
- 우측: `주요 결과물 예시` 헤더 바 + 결과물 캡처(필 라벨 부착)
- 적합: 수행 단계별 상세, 과업 정의

**패턴 C: 벤치마크 카드 (사례 분석)**
- 좌측: `소개`와 `주요 기능` 틴트 카드 (불릿 리스트)
- 우측: 화면 캡처 2×2 그리드 (동일 비율, 하단 캡션)
- 적합: 경쟁 사례와 선진 사례 분석, 서비스 비교

**패턴 D: 데이터 테이블**
- 좌측: 다크 배지(섹션 라벨) + 표 (헤더행 `#E2EEF9`, 짝수행 `#F5F8FC`)
- 우측: 규칙과 산정식 넘버 리스트 (틴트 박스)
- 적합: 기능점수 산정, 비교표, 제공사 개요

**패턴 E: 섹션 구분 / 목차 (파트 전환)**
- 섹션 간지는 **새 덱에서 만들지 않음**. 본 덱의 간지 레이아웃 `Section명_한 줄 입력`(배경 그림과  
  저작권 문구 포함)으로 본 덱 안에서 직접 추가함 — 새 덱에서 흉내 내면 붙여 넣을 때 레이아웃이 따로 들어감
- 새 덱 스크립트에는 간지 위치만 `<!-- 간지: {섹션명} -->` 주석으로 표시
- 목차는 `내용_단쪽` 콘텐츠 슬라이드로 작성 (흰 배경에 번호 + 하위 항목 3열)
- 적합: 파트 도입, 목차, 챕터 전환

---

### 4. 컴포넌트 스타일

#### 섹션 헤더 바

| 속성 | 값 |
|------|------|
| 형태 | Rectangle (라운드 6px) |
| 배경 | 단색 `#1E2A5C` 또는 `#2E74C6` (그라디언트 금지) |
| 텍스트 | White, 24pt, Bold, 가운데 정렬 |
| 용도 | 좌/우 섹션 구분(목적과 추진전략, 목표와 결과물 등) |

#### 넘버 스퀘어 배지

| 속성 | 값 |
|------|------|
| 형태 | RoundRect (약 34~44px 정사각, radius 5~6px) |
| 배경 | `#2E74C6`(기본) / `#1E2A5C` / `#404155` |
| 텍스트 | White, Bold |
| 용도 | 순서, 단계, 핵심 항목 번호 |

#### 틴트 정보 박스

| 속성 | 값 |
|------|------|
| 형태 | RoundRect (radius 8~12px) |
| 배경 | `#EEF3FA` (요약) / `#F5F8FC` (리스트 항목) |
| 테두리 | `#D9E0EC` |
| 텍스트 | 제목 `#1E2A5C` Bold, 본문 `#3B4557` Regular |
| 용도 | 개념 요약, 항목 나열, 카드 |

#### 필 라벨

| 속성 | 값 |
|------|------|
| 형태 | Pill (radius 999) |
| 배경 | `#EEF3FA`, 테두리 `#C3CEE0` |
| 텍스트 | `#1E2A5C`, Bold |
| 용도 | 화면 캡처, 이미지, 카테고리 라벨 |

#### 다크 배지

| 속성 | 값 |
|------|------|
| 형태 | RoundRect |
| 배경 | `#404155` (Dark Slate) |
| 텍스트 | White, Bold |
| 용도 | 테이블 섹션 라벨, 카테고리명 |

#### 데이터 테이블

| 속성 | 값 |
|------|------|
| 헤더 행 | 배경 `#E2EEF9`, 텍스트 `#1E2A5C` Bold |
| 본문 행 | 흰색 / `#F5F8FC` 교차, 텍스트 `#3B4557` |
| 행 구분선 | `#EDF0F6` |
| 행 높이 | 0.45~0.55″ (14pt 이상 + 여유 패딩) |

#### 인용 콜아웃

| 속성 | 값 |
|------|------|
| 형태 | 좌측 5px `#2E74C6` 바 + 이탤릭 텍스트 |
| 텍스트 | `#1E2A5C`, Bold, Italic |
| 용도 | 기대 효과나 핵심 메시지 강조 |

#### 출처 줄

| 속성 | 값 |
|------|------|
| 구분선 | x 0.557″, y 8.08″, 전폭 14.9″, `#E9ECF3` 1pt |
| 문구 | x 0.557″, y 8.14″, h 0.42″, Pretendard 14pt `#7C8598`, 여백 0, 한 줄 |
| 용도 | 근거와 출처 표기. 제목 밑줄(언더라인 룰)은 레이아웃 구분선으로 대체되어 쓰지 않음 |

---

### 5. 디자인 규칙

#### 필수 준수 사항

- 콘텐츠는 반드시 **흰색 배경** 위, x 0.557″ ~ 15.457″ 안에 배치
- 장 제목은 **제목 개체 틀**에만 넣음. 제목 밑줄과 경로 표시를 슬라이드에 그리지 않음
- 「대상 덱 붙여넣기 호환」 절의 규칙 7가지를 모든 슬라이드에 적용
- 본문 텍스트 최소 크기 **14pt** — 14pt 미만이 필요할 정도면 슬라이드를 분리할 것
- 하단 여백이 **1.0인치 이상** 남으면 표와 카드의 글자/행 높이를 키워 균형있게 채울 것
- 헤더 바, 배지, 박스는 **지정 팔레트 내 컬러**만 사용
- 흰 카드에는 `#D9E0EC` 테두리를 추가하여 시인성 확보
- 다크(네이비/슬레이트) 배경 위 텍스트는 반드시 **흰색/밝은색**
- 화면 캡처는 동일 비율과 정렬로 그리드 배치하고 필 라벨로 화면명 표기
- 푸터 영역(y 8.5″ 아래, 고정 문구와 쪽 번호)에는 콘텐츠 배치 금지

#### 가운뎃점(·) 대신 뜻을 씀

가운뎃점은 '그리고', '와/과', '또는', '및', 구분선처럼 여러 뜻으로 읽혀서, 읽는 사람마다 해석이 달라짐.  
그래서 슬라이드 글(제목, 리드문, 본문, 칩, 표, 발표자 노트)에는 가운뎃점을 쓰지 않고 **뜻하는 말을 그대로** 씀.

| 뜻 | 쓰는 말 | 바꾸기 전 → 바꾼 뒤 |
|----|---------|--------------------|
| 둘 다 | 와/과, 및, 그리고 | 노드 타입`·`관계 → 노드 타입과 관계 |
| 셋 이상 나열 | 쉼표(,) | organization `·` person `·` geo → organization, person, geo |
| 둘 중 하나 | 또는, ~이거나 | FK 0 `·` 1개 → FK가 0개 또는 1개 |
| 동작 둘 중 하나 | ~하거나 | 조회`·`집계하면 → 조회하거나 집계하면 |
| 덧붙임 설명 | 괄호 | 설계 시 `·` 사전 1회 → 설계 시(사전 1회) |
| 서로 다른 문장 잇기 | 마침표로 끊음 | A 함 `·` B 함 → A 함. B 함 |

- **예외**: 코드, 파일명, 명령, 원문 그대로 옮기는 고유명사에 들어 있는 가운뎃점은 그대로 둠
- 화살표(→), 더하기(+)처럼 뜻이 하나로 정해진 기호는 계속 써도 됨
- 빌드 뒤 6-12 체크리스트 17번으로 남은 가운뎃점을 찾음
- PPT 스크립트(.md)와 이 가이드 같은 마크다운 문서도 같은 기준을 따름(AGENTS.md Lessons Learned)

#### 테이블 배치 규칙

한 슬라이드에 **테이블이 2개 이상**일 때:

| 조건 | 배치 | 이유 |
|------|------|------|
| 두 테이블 모두 **행 5개 이하** | **좌우 배치** (2열) | 짧은 표를 수직 나열하면 하단 여백 과도 |
| 한 쪽이라도 **행 6개 이상** | **수직 배치** (1열) | 좌우 배치 시 열 너비 부족으로 가독성 저하 |
| 테이블 **3개 이상** | **좌우 배치 우선** 검토 후, 불가 시 수직 | 공간 효율 극대화 |

**좌우 배치 시 규칙:**
- 콘텐츠 영역 너비(`CW`)를 2등분하고 중간 갭 0.2~0.3″ 확보
- 각 테이블 위에 다크 배지(섹션 제목)를 배치하여 구분
- 두 테이블의 상단 y좌표를 동일하게 정렬
- 행 높이를 넉넉히(0.45~0.55″) 잡아 14pt 이상 폰트와 여유 패딩 확보

---

### 6. 코드 생성 시 필수 검증 규칙

PPT 생성 스크립트(JavaScript/pptxgenjs) 작성 시, 아래 규칙을 **코드 레벨에서 강제**할 것.

#### 6-1. 팔레트 상수화

```javascript
const C = {
  title:  "2C2926",  lead:   "000000",
  navy:   "1E2A5C",  blue:   "2E74C6",  ink:    "2B3242",
  slate:  "4A5364",  sub:    "7C8598",
  tint:   "EEF3FA",  altRow: "F5F8FC",  tableHead: "E2EEF9",
  dark:   "404155",  border: "D9E0EC",  line:   "EDF0F6",
  titleLine: "E2E8F0", footLine: "E9ECF3", pageNum: "6B6B7B",
};
```

**규칙**: 색상 리터럴을 슬라이드마다 반복 입력하지 말고 `C.*` 상수 사용.  
`pptx.SchemeColor`(테마 색)는 쓰지 않음 — 붙여 넣으면 본 덱 테마 색으로 바뀜 (붙여넣기 호환 규칙 7).

#### 6-2. 최소 폰트 크기 강제 (14pt)

```javascript
const MIN_FONT = 14;
const fsMin = (size) => {
  if (size < MIN_FONT) throw new Error(`fontSize ${size} < ${MIN_FONT}pt 금지! 슬라이드를 분리할 것`);
  return size;
};
```

**규칙**: `fontSize` 값을 직접 숫자로 쓰지 말고 반드시 `fsMin()` 함수를 경유할 것.  
예외: 본 덱 실측값을 옮긴 레이아웃 요소(「무단전재」 12pt)와 140자 초과 출처 문구(12pt)만 숫자 직접 지정 허용.

#### 6-3. 헤더 바 헬퍼

```javascript
// 단색 헤더 바 (pptxgenjs는 그라디언트 미지원)
function headerBar(slide, { x, y, w, text, accent = false }) {
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h: 0.5, rectRadius: 0.06,
    fill: { color: accent ? C.blue : C.navy },
    line: { type: "none" },
  });
  slide.addText(text, { x, y, w, h: 0.5, align: "center", color: "FFFFFF",
    bold: true, fontSize: fsMin(24), fontFace: FONT });
}
```

**규칙**: 섹션 헤더 바는 헬퍼로 생성. `accent:true` 는 우측 강조 섹션(추진 전략, 주요 결과물 등).

#### 6-4. 넘버 배지 헬퍼

```javascript
function numBadge(slide, { x, y, n, color = C.blue, size = 0.4 }) {
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x, y, w: size, h: size, rectRadius: 0.05, fill: { color }, line: { type: "none" },
  });
  slide.addText(String(n), { x, y, w: size, h: size, align: "center", valign: "middle",
    color: "FFFFFF", bold: true, fontSize: fsMin(18), fontFace: FONT });
}
```

#### 6-5. `내용_단쪽` 레이아웃 정의 + 페이지 헤더와 출처 헬퍼

```javascript
const LAYOUT = "내용_단쪽";              // 본 덱 레이아웃 이름과 글자 하나까지 같아야 함
const X0 = 0.557, CW = 14.9;            // 콘텐츠 왼쪽 끝과 폭 (제목 개체 틀과 같은 선)
const BODY_TOP = 1.90, BODY_BOTTOM = 7.95;

// 본 덱 `내용_단쪽` 실측값을 그대로 옮김 — 미리보기에서도 본 덱과 같은 모양이 나옴
function defineContentLayout(pptx) {
  pptx.defineSlideMaster({
    title: LAYOUT,
    background: { color: "FFFFFF" },
    objects: [
      { line: { x: 0.556, y: 0.95, w: 14.888, h: 0, line: { color: C.titleLine, width: 1.5 } } },
      { text: { text: "무단전재 및 배포 금지",
          options: { x: 0.4875, y: 8.517, w: 1.675, h: 0.27,
                     fontFace: FONT, fontSize: 12, color: "A6A6A6", margin: 0 } } },
      { placeholder: { options: { name: "title", type: "title", x: X0, y: 0.109, w: 15.025, h: 0.906,
          fontFace: FONT, fontSize: 32, bold: true, color: C.title, margin: 0, align: "left", valign: "middle" },
          text: "" } },
    ],
    slideNumber: { x: 11.913, y: 8.517, w: 3.6, h: 0.25,
                   fontFace: FONT, fontSize: 16, color: C.pageNum, align: "right" },
  });
}

// 장 제목(제목 개체 틀) + 리드문(선택)
function pageHeader(slide, { title, lead }) {
  slide.addText(title, { placeholder: "title" });
  if (lead) {
    slide.addText(lead, { x: X0, y: 1.259, w: CW, h: 0.42, margin: 0, isTextBox: true,
      fontFace: "Pretendard SemiBold", fontSize: fsMin(18), color: C.lead });
  }
}

// 출처 줄 — 한 줄을 넘으면 「무단전재」 문구와 겹치므로 140자 초과는 12pt (출처에만 허용하는 예외)
function sourceLine(slide, text) {
  slide.addShape(pptx.shapes.LINE, { x: X0, y: 8.08, w: CW, h: 0, line: { color: C.footLine, width: 1 } });
  slide.addText(text, { x: X0, y: 8.14, w: CW, h: 0.42, margin: 0, valign: "top", isTextBox: true,
    fontFace: FONT, fontSize: text.length > 140 ? 12 : 14, color: C.sub });
}
```

**규칙**:
- 제목 개체 틀, 쪽 번호, 제목 구분선, 「무단전재」 문구는 레이아웃에만 둠. 슬라이드에서 다시 그리지 않음
- 본문 도형은 `BODY_TOP` ~ `BODY_BOTTOM`(1.90″ ~ 7.95″) 안에만 배치 (리드문이 없으면 1.45″부터 가능)
- placeholder 옵션에 `align: "left"`를 빼면 제목이 가운데 정렬됨 (2026-10-04 실측)

#### 6-6. Shape 사용 규칙

```javascript
// ✅ CORRECT
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08 });
// ❌ WRONG
import { ShapeType } from "pptxgenjs";
```

**규칙**: 도형은 `pptx.shapes.*` 로만 참조. 자주 쓰는 항목:
- `RECTANGLE` — 콘텐츠 박스, 언더라인, 카드 배경
- `ROUNDED_RECTANGLE` — 헤더 바, 배지, 라운드 카드
- `LINE` — 구분선

#### 6-7. 슬라이드 크기 정의

```javascript
const pptx = new pptxgen();
pptx.defineLayout({ name: "CUSTOM", width: 16, height: 9 });
pptx.layout = "CUSTOM";
```

**규칙**: 16″ × 9″ (1152 × 648pt) 고정. `LAYOUT_WIDE` 등 프리셋 금지.

#### 6-8. 슬라이드 함수 패턴

```javascript
async function createSlide01(pptx) {
  const slide = pptx.addSlide({ masterName: LAYOUT });
  pageHeader(slide, { title: "컬러 시스템", lead: "팔레트는 네이비 중심, 블루는 강조에만 씀" });
  // ... 슬라이드 콘텐츠 (y 1.90″ ~ 7.95″)
  sourceLine(slide, "출처: 디자인 시스템 v2 §2");
  return slide;
}
```

**규칙**: 슬라이드 함수는 `async function createSlideXX(pptx)` 형태, 한 함수에 한 슬라이드, `main()`에서 순차 호출.  
`addSlide()`에는 반드시 `masterName: LAYOUT`를 넘김 — 빠지면 `DEFAULT` 레이아웃이 붙여넣기 때 본 덱에 따라 들어감.

#### 6-9. 테이블 작성 규칙

```javascript
slide.addTable(
  [
    [ { text: "점수", options: { fill: C.tableHead, color: C.navy, bold: true } },
      { text: "유형", options: { fill: C.tableHead, color: C.navy, bold: true } } ],
    ["7.5", "EIF"],
  ],
  { x: 0.55, y: 1.9, w: 9, colW: [2, 7], fontSize: fsMin(14), fontFace: FONT,
    rowH: 0.5, border: { type: "solid", color: C.line, pt: 1 } }
);
```

**규칙**: 행/열 구조 데이터는 `slide.addTable()` 사용 — `addShape`+`addText` 수동 셀 그리기 금지. 헤더행 fill 은 `C.tableHead`.

#### 6-10. 한글 폰트 처리

```javascript
const FONT = "Pretendard";
{ text: "안녕하세요", options: { fontFace: FONT, fontSize: fsMin(18) } }
```

**규칙**: `Calibri`, `Arial`, `맑은 고딕` 등 직접 지정 금지. 시스템 폴백은 PPT 뷰어가 처리.

#### 6-11. 빌드 스크립트 진입점

```javascript
let pptx;   // 헬퍼(headerBar, sourceLine 등)가 pptx.shapes를 쓰므로 모듈 범위에 둠

async function main() {
  pptx = new pptxgen();
  pptx.defineLayout({ name: "CUSTOM", width: 16, height: 9 });
  pptx.layout = "CUSTOM";
  defineContentLayout(pptx);   // 6-5 — 레이아웃 이름 "내용_단쪽"

  for (const fn of [createSlide01, createSlide02 /* ... */]) {
    await fn(pptx);
  }

  await pptx.writeFile({ fileName: "proposal.pptx" });
  console.log("✅ PPT 생성 완료");
}

main().catch((e) => { console.error("❌ PPT 생성 실패:", e); process.exit(1); });
```

**규칙**: 진입점은 `main().catch(...)` 패턴, 실패 시 `process.exit(1)`, 성공 시 콘솔 로그 출력.

#### 6-12. 생성 후 자가 검증 체크리스트

| # | 검증 항목 | 방법 | 합격 기준 |
|---|----------|------|----------|
| 1 | 최소 폰트 크기 | 스크립트 내 모든 fontSize 값 확인 | 14pt 이상 (fsMin 경유, 6-2 예외 제외) |
| 2 | 하단 여백 | 최하단 콘텐츠 ~ 푸터 간 거리 계산 | 1.0인치 미만 |
| 3 | 콘텐츠 누락 | 텍스트 추출 후 원본 대조 | 모든 항목 포함 |
| 4 | 이미지 임베딩 | 스크립트의 이미지 경로 존재 여부 | 파일 존재 확인 |
| 5 | 슬라이드 크기 | 1152 × 648pt (16″ × 9″) | 정확히 일치 |
| 6 | 폰트 | Pretendard 사용 | Calibri/Arial/맑은 고딕 금지 |
| 7 | 컬러 팔레트 | 지정 HEX만 사용 (C.* 상수) | 임의 색상 금지 |
| 8 | 페이지 헤더 | 제목은 제목 개체 틀, 리드문은 y 1.259″ | 경로 표시, 제목 밑줄, 「n / m」 쪽 표시 없음 |
| 9 | Shape 참조 | `pptx.shapes.*` 사용 | `ShapeType` 직접 import 금지 |
| 10 | 슬라이드 함수 | `async function createSlideXX` 패턴 | 동기 함수와 인라인 작성 금지 |
| 11 | 표 작성 | `slide.addTable()` + 헤더행 `#E2EEF9` | 셀 수동 그리기 금지 |
| 12 | 빌드 종료 코드 | `node build.js` 실행 후 `$?` 확인 | 0 (성공) |
| 13 | 출력 파일 | `.pptx` 파일 존재 및 크기 | 0바이트 초과 |
| 14 | 붙여넣기 호환 | 아래 점검 코드 실행 | `OK` 출력 |
| 15 | 출처 줄 | 미리보기에서 출처 문구 줄 수 확인 | 한 줄 (「무단전재」 문구와 겹치지 않음) |
| 16 | 개체 틀 번호 | 6-14 실행 여부 | 제목 `<p:ph type="title"/>`, 쪽 번호 `idx="4"` |
| 17 | 가운뎃점 | 완성된 덱의 본문과 발표자 노트에서 `·` 검색 | 0건(코드, 파일명, 고유명사 원문은 제외) — 5절 「가운뎃점(·) 대신 뜻을 씀」 |

#### 6-13. 붙여넣기 호환 점검 코드

```python
# python check_paste.py {덱}.pptx — 본 덱에 붙여 넣기 전 점검
import sys
from pptx import Presentation
p = Presentation(sys.argv[1])
err = []
if (p.slide_width, p.slide_height) != (14630400, 8229600):
    err.append("슬라이드 크기가 16x9인치가 아님")
for i, s in enumerate(p.slides, 1):
    if s.slide_layout.name != "내용_단쪽":
        err.append(f"{i}쪽 레이아웃 이름: {s.slide_layout.name}")
    if s.shapes.title is None or not s.shapes.title.text.strip():
        err.append(f"{i}쪽 제목 개체 틀 비었음")
    for sh in s.shapes:
        if sh.has_text_frame and " / " in sh.text_frame.text and sh.top > 7_500_000 and len(sh.text_frame.text) < 10:
            err.append(f"{i}쪽 글자 쪽 표시 의심: {sh.text_frame.text}")
xml = "".join(s._element.xml for s in p.slides)
if "schemeClr" in xml:
    err.append("테마 색(schemeClr) 사용")
print("\n".join(err) or "OK")
```

- 「제목 개체 틀 비었음」이 나오면 6-14 개체 틀 번호 정리를 빠뜨린 것임  
  (python-pptx는 번호 0번 제목만 제목으로 인식함)

#### 6-14. 개체 틀 번호 정리 (빌드 직후 필수)

pptxgenjs는 제목 개체 틀을 `idx="102"`, 쪽 번호를 `idx="4294967295"`로 씀.  
본 덱 `내용_단쪽`은 제목 번호 없음(0번), 쪽 번호 `idx="4"`라서, 번호까지 같게 맞춰 두어야  
붙여 넣을 때 개체 틀이 확실히 짝지어짐.

```python
# python fix_ph.py {덱}.pptx — pptxgenjs가 쓴 개체 틀 번호를 본 덱 `내용_단쪽`과 같게 맞춤
import re, shutil, sys, zipfile
src = sys.argv[1]
tmp = src + ".tmp"
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if re.match(r"ppt/(slides|slideLayouts)/slide(Layout)?\d+\.xml$", item.filename):
            x = data.decode("utf8")
            x = re.sub(r'<p:ph\s+idx="\d+"\s+type="title"[^>]*/>', '<p:ph type="title"/>', x)
            x = re.sub(r'<p:ph type="sldNum" sz="quarter" idx="\d+"/>', '<p:ph type="sldNum" idx="4"/>', x)
            data = x.encode("utf8")
        zout.writestr(item, data)
shutil.move(tmp, src)
print("개체 틀 번호 정리 완료:", src)
```

**빌드 순서**: `node build.js` → `python fix_ph.py {덱}.pptx` → `python check_paste.py {덱}.pptx`(OK 확인)  
→ `python scripts/render-pptx.py {덱}.pptx`(미리보기)
