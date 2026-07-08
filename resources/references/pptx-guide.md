# PPT 작성 가이드 (pptx-build-guide)

## 0. 패턴 개요 (Spec Agent + Orchestrator Builder)

DMAP 표준 PPT 생성 패턴은 **2단계 분리 구조**임:

```
[사용자 요구]
     ↓
[pptx-spec-writer 에이전트]  ← 시각 명세 .md 작성 (패턴 A~F 매핑, 슬라이드별 콘텐츠/디자인 의도)
     ↓
[Builder Skill (오케스트레이터)]
  1. 본 가이드 로드
  2. spec.md 분석 → pptxgenjs 빌드 코드 작성
  3. node 실행 → .pptx 생성
  4. 파일 검증 + 사용자 보고
     ↓
[*.pptx 산출물]
```

**원칙**:
- 에이전트는 **명세만 산출** (실행 도구 비포함 → Cursor/Cowork 등 모든 런타임 호환)
- 오케스트레이터(스킬)가 **빌드+실행+검증** 수행 (Write + Bash 도구만 필요)
- 외부 변환 스킬(`anthropic-skills:pptx` 등) 의존 금지
- 빌더 스킬은 본 가이드 6절(코드 생성 시 필수 검증 규칙)을 **반드시 준수**

**런타임 요구사항**: `node ≥ 18`, `npm i pptxgenjs` (생성 플러그인의 setup 스킬에서 자동 설치)

---

## 생성된 이미지 임베딩 
- 스크립트에 아래 예와 같이 이미지 링크가 있으면 그 이미지를 페이지에 임베딩 
  ```
  ![AM 개요 다이어그램](images/am_overview_diagram.png)
  ```

## PPT 스타일시트

### 1. 컬러 팔레트

#### 메인 컬러

| 역할 | 컬러명 | HEX | 용도 |
|------|--------|-----|------|
| Primary | Dark Brown | `#2C2926` | 페이지 헤더, 레슨명 제목, 주요 텍스트 |
| Sub | Green | `#059669` | 강조 배지, 플로우 스텝 바, 보조 강조 |
| Accent Teal | Teal | `#0D9488` | 키워드 라벨, 섹션 구분 텍스트 |
| Text Body | Dark Gray | `#505060` | 본문 텍스트 |
| Text Secondary | Slate | `#59636E` | 설명 텍스트, 부가 정보 |
| Text Tertiary | Mid Gray | `#6B6B7B` | 캡션, 메타데이터 |
| Background (Master) | White | `#FFFFFF` | 슬라이드 마스터 배경 |
| Background (Content) | White | `#FFFFFF` | 콘텐츠 영역 배경 사각형 |

#### Accent 1~6 (테마 색상)

| Accent | HEX | 미리보기 |
|--------|-----|---------|
| Accent 1 | `#4472C4` | 🔵 Blue |
| Accent 2 | `#ED7D31` | 🟠 Orange |
| Accent 3 | `#A5A5A5` | ⚪ Gray |
| Accent 4 | `#FFC000` | 🟡 Gold |
| Accent 5 | `#5B9BD5` | 🔵 Light Blue |
| Accent 6 | `#70AD47` | 🟢 Green |

#### 플로우 다이어그램 스텝 컬러

| 용도 | HEX | 설명 |
|------|-----|------|
| 스텝 1 (시작/끝) | `#059669` | Green — Input/Output 바 |
| 스텝 2 (검색/조회) | `#0284C7` | Blue — RAG, 데이터 조회 단계 |
| 스텝 3 (구성/처리) | `#D97706` | Amber — Prompt 구성, 중간 처리 |
| 스텝 4 (핵심 실행) | `#DC2626` | Red — LLM 호출, 핵심 실행 |
| 스텝 5 (변환/출력) | `#7C3AED` | Purple — Output Parser, 변환 |

#### 카드 그리드 헤더 컬러

| 용도 | HEX | 설명 |
|------|-----|------|
| 카테고리 A | `#3776AB` | Python Blue — 소개/개요 카드 |
| 카테고리 B | `#1A6E36` | Dark Green — 구성 요소 카드 |
| 카테고리 C | `#C0530A` | Dark Orange — 기본 문법 카드 |
| 카테고리 D | `#1A5E7E` | Dark Teal — 환경/설정 카드 |
| 카테고리 E | `#8B1A1A` | Dark Red — 핵심/심화 카드 |

#### 보조 컬러

| 용도 | HEX | 설명 |
|------|-----|------|
| 카드 배경 | `#F5F5F7` | Light Gray — 정보 카드 배경 |
| 코드 블록 배경 | `#F5F5F7` | Light Gray — 회색 배경 코드 영역 |
| 정보 하이라이트 배경 | `#CCFBF1` | Light Teal — 핵심 포인트 강조 박스 |
| 구분선 | `#E2E8F0` | Light Gray — 섹션 구분 |
| 카드 테두리 | `#DDDDE0` | Cool Gray — 카드 경계선 |
| 비활성 화살표 | `#9CA3AF` | Gray — 화살표, 보조 기호 |

---

### 2. 타이포그래피

#### 서체 시스템

| 서체 | 용도 | 비고 |
|------|------|------|
| **Pretendard** | 주 서체 (타이틀, 헤더, 본문, 캡션) | Variable Weight 지원 |
| **맑은 고딕** | 폴백 한글 서체 | 시스템 미설치 시 대체 |
| **Arial** | 영문 폴백 | 범용 |

#### 텍스트 스타일 가이드

| 요소 | 서체 | 굵기 | 크기 | 색상 |
|------|------|------|------|------|
| 페이지 헤더 (제목) | **Pretendard** | Bold | 36pt | `#2C2926` |
| 서브타이틀 (부제) | **Pretendard** | Bold | 20pt | `#2C2926` |
| 섹션 헤더 | **Pretendard** | Bold | 28pt | `#2C2926` |
| 키워드 라벨 | **Pretendard** | Bold | 16pt | `#0D9488` |
| 본문 일반 텍스트 | **Pretendard** | Regular | 16pt | `#505060` |
| 본문 강조 텍스트 | **Pretendard** | Bold | 16pt | `#2C2926` |
| 카드 내 텍스트 | **Pretendard** | Regular | 14pt | `#59636E` |
| 밀집 콘텐츠 텍스트 | **Pretendard** | Regular | 12pt | `#59636E` |
| 코드 블록 텍스트 | **Pretendard** | Regular | 16-18pt | `#505060` (회색 배경 위) |
| 캡션 / 메타 | **Pretendard** | Regular | 12pt | `#6B6B7B` |

---

### 3. 레이아웃 가이드

#### 슬라이드 사양

| 항목 | 값 |
|------|------|
| 크기 | 1152 × 648pt (16:9) |
| 여백 (좌우) | 40pt |
| 여백 (상단) | 70pt (페이지 헤더 영역) |
| 마스터 배경 | `#FFFFFF` (White) |
| 콘텐츠 영역 | 흰색 배경 사각형 또는 카드로 구성 |
| 푸터 | "무단전재 및 배포 금지" + 페이지 번호 (마스터 요소) |
| 테마 | Office (커스텀) |

#### 슬라이드 마스터 구조

| 마스터 | 배경색 | 용도 |
|--------|--------|------|
| Master 1 | `#00BBFF` (Bright Cyan) | 타이틀 슬라이드 |
| Master 3 (Layout 6) | `#FFFFFF` (White) | 콘텐츠 슬라이드 (주 사용) |

#### 레이아웃 패턴

**패턴 A: 카드 그리드 (3열)**
- 상단 페이지 헤더 + 부제
- 3개의 동일 크기 카드 (`#F5F5F7` 배경, RoundRect)
- 각 카드 아래 상세 설명 텍스트
- 적합: 개념 비교, 핵심 가치 3가지 소개

**패턴 B: 다이어그램 + 설명 (2열)**
- 좌측: 도형/다이어그램 (무한루프, 도넛차트 등)
- 우측: 번호 목록 또는 참고 이미지
- 적합: 아키텍처 패턴, 구성 요소 관계도

**패턴 C: 플로우 다이어그램 + 코드 (2열)**
- 좌측: 컬러 코딩된 프로세스 플로우 (세로 방향)
  - 각 스텝은 다른 색상 바 사용 (`#059669`, `#0284C7`, `#D97706`, `#DC2626`, `#7C3AED`)
  - 흰색 배경 컨테이너(`#FFFFFF`) 위에 배치
- 우측: 회색 배경(`#F5F5F7`) 코드 블록 + 설명 텍스트
- 하단: 핵심 포인트 하이라이트 박스(`#CCFBF1`)
- 적합: 코드 파이프라인, 알고리즘 흐름

**패턴 D: 테이블 + 상세 섹션**
- 상단: 표 (헤더행 구분)
- 하단: 다크 배경(`#404155`) 배지 + 상세 설명
- 적합: 비교표, 제공사 개요

**패턴 E: 카드 그리드 (2×3 또는 2×2)**
- 각 카드는 색상 헤더 바 + 흰색 본문 영역
- 헤더 바 색상으로 카테고리 구분
- 카드 내 불릿 리스트 또는 코드 스니펫
- 적합: 다항목 개요, 분류별 정리

**패턴 F: 멀티 섹션 대시보드**
- 2~4개 독립 섹션으로 분할
- 각 섹션에 비교표, 턴 다이어그램, 아키텍처 등 혼합
- 적합: 종합 정리, 핵심 개념 + 실습 안내

---

### 4. 컴포넌트 스타일

#### 강조 배지

| 속성 | 값 |
|------|------|
| 형태 | RoundRect (둥근 모서리 사각형) |
| 배경색 | `#059669` |
| 텍스트 | White, 14pt, Bold |
| 용도 | 핵심 키워드 강조 (예: "WHY", "Process") |

#### 테이블 헤더 행

| 속성 | 값 |
|------|------|
| 배경색 | `#E2EEF9` (옅은 파란색) |
| 텍스트 | `#2C2926`, 12-13pt, Bold |
| 용도 | 모든 테이블의 헤더 행 (기존 `#2C2926` 다크 배경 대신 사용) |

> **변경**: 테이블 헤더를 어두운 배경(`#2C2926` + 흰색 텍스트) 대신 옅은 파란색 배경(`#E2EEF9`) + 진한 텍스트(`#2C2926`)로 통일

---

#### 정보 카드

| 속성 | 값 |
|------|------|
| 형태 | RoundRect |
| 배경색 | `#F5F5F7` (연한 회색) |
| 테두리 | `#DDDDE0` (Cool Gray) |
| 텍스트 | `#505060`, 16pt (제목 Bold, 본문 Regular) |
| 용도 | 개념 설명, 항목 나열 |

#### 카드 그리드 헤더

| 속성 | 값 |
|------|------|
| 형태 | RoundRect 상단 바 (카드 너비 × 38pt) |
| 배경색 | 카테고리별 컬러 (카드 그리드 헤더 컬러 참조) |
| 텍스트 | White, 14-16pt, Bold |
| 용도 | 카드 상단 카테고리 라벨 |

#### 플로우 스텝 바

| 속성 | 값 |
|------|------|
| 형태 | RoundRect (너비 380pt × 높이 48pt) |
| 배경색 | 스텝별 컬러 (플로우 다이어그램 스텝 컬러 참조) |
| 텍스트 | White, 16-18pt, Bold |
| 컨테이너 | 흰색 배경(`#FFFFFF`) 사각형 위에 배치 |
| 용도 | 프로세스 흐름도의 각 단계 |

#### 코드 블록

| 속성 | 값 |
|------|------|
| 형태 | RoundRect |
| 배경색 | `#F5F5F7` (Light Gray, 회색 배경 스타일) |
| 텍스트 | 16-18pt, 구문 하이라이팅 컬러 사용 |
| 구문 색상 | 문자열 `#A31515`, 키워드 `#0000FF`, 주석 `#008000` |
| 용도 | 코드 예시, API 호출 예시 |

#### 다크 배지

| 속성 | 값 |
|------|------|
| 형태 | RoundRect |
| 배경색 | `#404155` (Dark Slate) |
| 텍스트 | White, 16pt, Bold |
| 용도 | 카테고리명, 섹션 라벨 (예: "Groq API") |

#### 하이라이트 박스

| 속성 | 값 |
|------|------|
| 형태 | RoundRect |
| 배경색 | `#CCFBF1` (Light Teal) |
| 텍스트 | `#2C2926`, 14-16pt |
| 용도 | 핵심 포인트, 적합 사례 표시 |

#### 구분선

| 속성 | 값 |
|------|------|
| 두께 | 1pt |
| 색상 | `#E2E8F0` |
| 너비 | 전체 콘텐츠 영역 (1072pt) |

---

### 5. 디자인 규칙

#### 필수 준수 사항

- 마스터 배경(`#E7E6E6`)이 투과되므로 콘텐츠 슬라이드에는 반드시 흰색 배경 사각형 배치
- 페이지 헤더는 `#2C2926` Bold 36pt로 좌측 상단에 배치
- 모든 콘텐츠는 좌우 40pt 여백 안에 배치
- 본문 텍스트 최소 크기 **12pt** (가독성 보장) — 12pt 미만이 필요할 정도로 내용이 많으면 슬라이드를 분리할 것
- 하단 여백이 과도하게 남는 경우, 표·카드의 글자 크기를 키우거나 행 높이를 늘려 콘텐츠 영역을 균형있게 채울 것
- 플로우 다이어그램 각 스텝은 서로 다른 색상으로 구분
- 코드 블록은 회색 배경(`#F5F5F7`)에 구문 하이라이팅 적용
- 카드 그리드 사용 시 각 카드 헤더 바 색상으로 카테고리 구분

#### 테이블 배치 규칙

한 슬라이드에 **테이블이 2개 이상**일 때, 아래 기준으로 수직/좌우 배치를 결정:

| 조건 | 배치 | 이유 |
|------|------|------|
| 두 테이블 모두 **행 5개 이하** | **좌우 배치** (2열) | 짧은 표를 수직 나열하면 하단 여백 과도 |
| 한 쪽이라도 **행 6개 이상** | **수직 배치** (1열) | 좌우 배치 시 열 너비 부족으로 가독성 저하 |
| 테이블 **3개 이상** | **좌우 배치 우선** 검토 후, 불가 시 수직 | 공간 효율 극대화 |

**좌우 배치 시 규칙:**
- 콘텐츠 영역 너비(`CW`)를 2등분하고 중간 갭 0.2~0.3" 확보
- 각 테이블 위에 섹션 배지(제목)를 배치하여 구분
- 두 테이블의 상단 y좌표를 동일하게 맞춰 정렬
- 행 높이를 넉넉히(0.45~0.55") 잡아 12pt 이상 폰트와 여유 있는 패딩 확보

**코드 레벨 검증:**
```
테이블 개수 ≥ 2 AND 각 테이블 행 수 ≤ 5
→ 좌우 배치 필수 (수직 배치 시 NG)
```

#### 주의 사항

- 서로 다른 슬라이드 마스터 간 레이아웃 ID를 교차 참조하지 않을 것
- 푸터 영역에는 마스터 요소("무단전재 및 배포 금지", 페이지번호)가 있으므로 콘텐츠 배치 금지
- `#FFFFFF` 카드에는 `#DDDDE0` 테두리를 추가하여 시인성 확보
- 다크 배경 위 텍스트는 반드시 `#FFFFFF` 또는 밝은 색상 사용

---

### 6. 코드 생성 시 필수 검증 규칙

PPT 생성 스크립트(JavaScript/pptxgenjs) 작성 시, 아래 규칙을 **코드 레벨에서 강제**할 것.

#### 6-1. 최소 폰트 크기 강제 (12pt)

스크립트 상단에 아래 헬퍼 함수를 선언하고, 모든 `fontSize` 지정에 이 함수를 사용:

```javascript
const MIN_FONT = 12;
const fs12 = (size) => {
  if (size < MIN_FONT) throw new Error(`fontSize ${size} < ${MIN_FONT}pt 금지! 슬라이드를 분리할 것`);
  return size;
};
```

사용 예:
```javascript
// ✅ CORRECT — 헬퍼 함수 경유
{ fontSize: fs12(14), ... }

// ❌ WRONG — 직접 지정 (검증 우회)
{ fontSize: 10, ... }
```

**규칙**: `fontSize` 값을 직접 숫자로 쓰지 말고 반드시 `fs12()` 함수를 경유할 것.
12pt 미만이 필요한 상황이면 **폰트를 줄이지 말고 슬라이드를 분리**할 것.

#### 6-2. 하단 여백 검증

슬라이드 콘텐츠의 최하단 요소(푸터 제외)와 푸터 구분선 사이 빈 공간이 **1.0인치 이상**이면,
표·카드의 행 높이를 늘리거나 글자 크기를 키워 공간을 채울 것.

코드 작성 후 아래 체크를 수행:
```
최하단 콘텐츠 y좌표 + height = ?
푸터 구분선 y좌표 = ?
남는 공간 = 푸터 y - (콘텐츠 y + h)
→ 1.0인치 이상이면 NG → 행 높이/폰트 크기 확대 필요
```

#### 6-3. Shape 사용 규칙

도형 생성 시 반드시 `pptx.shapes` 상수 사용. `ShapeType` 객체 직접 import 금지.

```javascript
// ✅ CORRECT
slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1 });
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 0, y: 0, w: 5, h: 1, rectRadius: 0.1 });

// ❌ WRONG
import { ShapeType } from "pptxgenjs";
slide.addShape(ShapeType.rect, ...);
```

**규칙**: 도형은 `pptx.shapes.*`로만 참조. 자주 쓰는 항목:
- `pptx.shapes.RECTANGLE` — 콘텐츠 박스, 카드 배경
- `pptx.shapes.ROUNDED_RECTANGLE` — 배지, 라운드 카드
- `pptx.shapes.LINE` — 구분선
- `pptx.shapes.RIGHT_TRIANGLE` — 화살표 등 보조 도형

#### 6-4. 슬라이드 크기 정의

스크립트 시작부에서 반드시 `defineLayout("CUSTOM")` 사용:

```javascript
const pptx = new pptxgen();
pptx.defineLayout({ name: "CUSTOM", width: 16, height: 9 });
pptx.layout = "CUSTOM";
```

**규칙**: 16" × 9" (1152 × 648pt) 고정. `LAYOUT_WIDE` 등 프리셋 사용 금지.

#### 6-5. 슬라이드 함수 패턴

각 슬라이드는 `async function createSlideXX(pptx)` 형태로 분리:

```javascript
async function createSlide01(pptx) {
  const slide = pptx.addSlide({ masterName: "MASTER" });
  // ... 슬라이드 콘텐츠 작성
  return slide;
}
```

**규칙**:
- 슬라이드 함수는 반드시 `async`로 선언 (이미지 로드 비동기 처리)
- 함수명은 `createSlide` + 2자리 숫자(01, 02, …)
- 한 함수에 한 슬라이드만 작성
- `main()`에서 순차 호출

#### 6-6. 테이블 작성 규칙

행/열 구조 데이터는 반드시 `slide.addTable()` 사용. `addShape` + `addText`로 셀 수동 그리기 금지.

```javascript
// ✅ CORRECT
slide.addTable(
  [
    [{ text: "헤더1", options: { bold: true, fill: "059669", color: "FFFFFF" } }, { text: "헤더2", options: { bold: true } }],
    ["셀1", "셀2"],
  ],
  { x: 0.5, y: 1.0, w: 15, colW: [3, 12], fontSize: fs12(12), fontFace: "Pretendard" }
);

// ❌ WRONG — 수동 셀 그리기
slide.addShape(pptx.shapes.RECTANGLE, { x: 0.5, y: 1.0, w: 3, h: 0.5 });
slide.addText("헤더1", { x: 0.5, y: 1.0, w: 3, h: 0.5 });
```

**규칙**:
- 셀 옵션은 `{ text, options }` 객체로 지정
- `colW` 배열로 열 너비 명시
- 테이블 폰트도 `fs12()` 헬퍼 경유

#### 6-7. 이미지 임베딩 검증

스크립트에서 이미지 추가 전 파일 존재 여부 확인:

```javascript
const fs = require("fs");
function addImage(slide, imagePath, opts) {
  if (!fs.existsSync(imagePath)) {
    throw new Error(`이미지 파일 없음: ${imagePath}`);
  }
  slide.addImage({ path: imagePath, ...opts });
}
```

**규칙**:
- 이미지 경로는 빌드 스크립트 기준 상대 경로 또는 절대 경로
- 빌드 시점에 파일 존재 검증 후 임베딩
- 마크다운 스크립트의 `![](images/foo.png)` 경로와 일치

#### 6-8. 한글 폰트 처리

모든 텍스트의 `fontFace`는 `"Pretendard"`로 통일:

```javascript
const FONT = "Pretendard";
{ text: "안녕하세요", options: { fontFace: FONT, fontSize: fs12(14) } }
```

**규칙**: `Calibri`, `Arial`, `맑은 고딕` 등 직접 지정 금지. 시스템 폴백은 PPT 뷰어가 처리.

#### 6-9. 빌드 스크립트 진입점

빌드 스크립트는 단일 `main()` 함수에서 시작하고 에러 시 종료 코드 1로 종료:

```javascript
async function main() {
  const pptx = new pptxgen();
  pptx.defineLayout({ name: "CUSTOM", width: 16, height: 9 });
  pptx.layout = "CUSTOM";

  // 마스터 슬라이드 정의
  pptx.defineSlideMaster({ title: "MASTER", /* ... */ });

  // 슬라이드 생성 (순차)
  for (const fn of [createSlide01, createSlide02 /* ... */]) {
    await fn(pptx);
  }

  await pptx.writeFile({ fileName: "courseware.pptx" });
  console.log("✅ PPT 생성 완료");
}

main().catch((e) => {
  console.error("❌ PPT 생성 실패:", e);
  process.exit(1);
});
```

**규칙**:
- 진입점은 `main().catch(...)` 패턴
- 실패 시 `process.exit(1)`로 종료 (CI/검증에서 실패 인식)
- 성공 시 콘솔 로그 출력

#### 6-10. 생성 후 자가 검증 체크리스트

PPT 파일 생성 후, 다음 항목을 **반드시 확인**하고 통과해야 완료로 보고:

| # | 검증 항목 | 방법 | 합격 기준 |
|---|----------|------|----------|
| 1 | 최소 폰트 크기 | 스크립트 내 모든 fontSize 값 확인 | 12pt 이상 (fs12 경유) |
| 2 | 하단 여백 | 최하단 콘텐츠 ~ 푸터 간 거리 계산 | 1.0인치 미만 |
| 3 | 콘텐츠 누락 | markitdown으로 텍스트 추출 후 원본 대조 | 모든 항목 포함 |
| 4 | 이미지 임베딩 | 스크립트의 이미지 경로 존재 여부 | 파일 존재 확인 |
| 5 | 슬라이드 크기 | 1152 × 648pt (16" × 9") | 정확히 일치 |
| 6 | 폰트 | Pretendard 사용 | Calibri/Arial/맑은 고딕 금지 |
| 7 | Shape 참조 | `pptx.shapes.*` 사용 | `ShapeType` 직접 import 금지 |
| 8 | 슬라이드 함수 | `async function createSlideXX` 패턴 | 동기 함수·인라인 작성 금지 |
| 9 | 표 작성 | `slide.addTable()` 사용 | 셀 수동 그리기 금지 |
| 10 | 빌드 종료 코드 | `node build.js` 실행 후 `$?` 확인 | 0 (성공) |
| 11 | 출력 파일 | `.pptx` 파일 존재 및 크기 | 0바이트 초과 |