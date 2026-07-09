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
  3. node 실행 → .pptx 생성
  4. 파일 검증 + 사용자 보고
     ↓
[*.pptx 산출물]
```

**원칙**:
- 에이전트는 **명세만 산출** (실행 도구 비포함 → Cursor/Cowork 등 모든 런타임 호환)
- 오케스트레이터(스킬)가 **빌드+실행+검증** 수행 (Write + Bash 도구만 필요)
- 외부 변환 스킬 의존 금지
- 빌더 스킬은 본 가이드 6절(코드 생성 시 필수 검증 규칙)을 **반드시 준수**

**런타임 요구사항**: `node ≥ 18`, `npm i pptxgenjs`

---

## 생성된 이미지 임베딩
- 스크립트에 아래 예와 같이 이미지 링크가 있으면 그 이미지를 페이지에 임베딩
  ```
  ![서비스 방향성 다이어그램](images/service_direction.png)
  ```
- 벤치마크·결과물 화면 캡처는 동일 비율로 정렬하여 그리드 배치하고, 필 라벨로 화면명을 표기

---

## PPT 스타일시트

> 이 스타일은 표준 컨설팅 제안서(딥 네이비 + 브라이트 블루) 디자인 언어를 기준으로 함.
> 흰색 배경 위에 컬러 헤더 바·넘버 배지·틴트 카드를 배치하는 정갈한 코퍼레이트 톤.

### 1. 컬러 팔레트

#### 메인 컬러

| 역할 | 컬러명 | HEX | 용도 |
|------|--------|-----|------|
| Primary | Deep Navy | `#1E2A5C` | 페이지 제목, 헤더 바(좌), 넘버 배지, 주요 텍스트 |
| Sub | Bright Blue | `#2E74C6` | 강조 헤더 바, 배지, 언더라인 액센트, 불릿 |
| Text Body | Ink | `#2B3242` | 본문 텍스트 |
| Text Secondary | Slate | `#4A5364` | 설명·부연 텍스트 |
| Text Tertiary | Sub Gray | `#7C8598` | 캡션, breadcrumb, 메타데이터 |
| Background (Master) | White | `#FFFFFF` | 슬라이드 마스터 배경 |
| Background (Content) | White | `#FFFFFF` | 콘텐츠 영역 배경 사각형 |

#### 보조 · 배경 컬러

| 용도 | HEX | 설명 |
|------|-----|------|
| 틴트 박스 배경 | `#EEF3FA` | Light Blue — 요약·정보 카드 배경 |
| 대체 행/카드 배경 | `#F5F8FC` | Pale Blue — 리스트 항목, 표 짝수행 |
| 테이블 헤더 행 | `#E2EEF9` | Soft Blue — 표 헤더행 배경 |
| 다크 배지 | `#404155` | Dark Slate — 섹션 라벨, WHAT 라벨 |
| 카드 테두리 / 구분선 | `#D9E0EC` | Cool Gray — 카드 경계, 헤더 언더라인 바탕 |
| 미세 구분선 | `#EDF0F6` | Light Gray — 표 행 구분, 리스트 구분 |
| 푸터 구분선 | `#E9ECF3` | Light Gray — 하단 푸터 상단 라인 |

#### 헤더 바 그라디언트

| 용도 | 값 | 설명 |
|------|-----|------|
| 강조 헤더 바 | `linear-gradient(90deg, #1E2A5C → #2E74C6)` | 우측 강조 섹션(추진 전략, 주요 결과물 등) |
| 단색 헤더 바 | `#1E2A5C` | 좌측 기본 섹션(목적 등) |
| 표지 / 구분 슬라이드 | `linear-gradient(120deg, #141D40 → #1E2A5C → #2E5AA8)` | 타이틀·파트 구분 배경 |

---

### 2. 타이포그래피

#### 서체 시스템

| 서체 | 용도 | 비고 |
|------|------|------|
| **Pretendard** | 주 서체 (제목, 헤더, 본문, 캡션) | Variable Weight, 한/영 통합 |
| **맑은 고딕** | 폴백 한글 서체 | 시스템 미설치 시 대체 |
| **Arial** | 영문 폴백 | 범용 |

#### 텍스트 스타일 가이드

| 요소 | 서체 | 굵기 | 크기 | 색상 |
|------|------|------|------|------|
| 페이지 제목 | **Pretendard** | ExtraBold(800) | 40pt | `#1E2A5C` |
| 섹션 헤더 바 텍스트 | **Pretendard** | Bold | 20pt | `#FFFFFF` |
| 섹션 헤더(본문) | **Pretendard** | Bold | 28pt | `#1E2A5C` |
| breadcrumb (경로) | **Pretendard** | SemiBold | 13pt | `#7C8598` |
| 본문 강조 텍스트 | **Pretendard** | Bold | 18pt | `#2B3242` |
| 본문 일반 텍스트 | **Pretendard** | Regular | 16pt | `#3B4557` |
| 카드 내 텍스트 | **Pretendard** | Regular | 14pt | `#4A5364` |
| 캡션 / 메타 | **Pretendard** | Regular | 12pt | `#7C8598` |

#### 굵기 스케일
`Regular 400` · `SemiBold 600` · `Bold 700` · `ExtraBold 800`

---

### 3. 레이아웃 가이드

#### 슬라이드 사양

| 항목 | 값 |
|------|------|
| 크기 | 1152 × 648pt (16:9) |
| 여백 (좌우) | 40pt |
| 여백 (상단) | 70pt (페이지 헤더 영역) |
| 마스터 배경 | `#FFFFFF` (White) |
| 콘텐츠 영역 | 흰색 배경 위 카드/헤더 바로 구성 |
| 푸터 | 좌측 고정 문구 + 우측 파트/페이지 번호 (마스터 요소) |

#### 페이지 헤더 구조 (모든 콘텐츠 슬라이드 공통)

```
① breadcrumb    : "Ⅰ. 디자인 시스템 › 2. 컬러"   (13pt, #7C8598)
② 페이지 제목    : "컬러 시스템"                  (40pt Bold, #1E2A5C)
③ 언더라인 룰    : 전폭 3pt #D9E0EC 위에 좌측 150px #2E74C6 액센트 세그먼트
④ (선택) 리드문  : 한 문장 요약                   (16pt, #4A5364)
```

#### 레이아웃 패턴

**패턴 A: 목적 / 추진 전략 (2단 헤더 바)**
- 좌측: 단색 네이비 헤더 바(`목적`) + 틴트 박스 요약(이탤릭 Bold 강조)
- 우측: 그라디언트 헤더 바(`추진 전략`) + 넘버 스퀘어 배지 항목 리스트
- 적합: 제안의 목적과 핵심 전략 압축, 방향성 개요

**패턴 B: WHY / HOW / WHAT (3행 목표·방안·결과)**
- 좌측: 그라디언트 헤더 바 아래 3개 행
  - WHY(목표) = 네이비 라벨 셀, HOW(수행 방안) = 블루 라벨 셀, WHAT(핵심 결과) = 다크 슬레이트 라벨 셀
  - 각 라벨 셀은 영문 대문자 + 한글 부제
- 우측: `주요 결과물 예시` 헤더 바 + 결과물 캡처(필 라벨 부착)
- 적합: 수행 단계별 상세, 과업 정의

**패턴 C: 벤치마크 카드 (사례 분석)**
- 좌측: `소개`·`주요 기능` 틴트 카드 (불릿 리스트)
- 우측: 화면 캡처 2×2 그리드 (동일 비율, 하단 캡션)
- 적합: 경쟁·선진 사례 분석, 서비스 비교

**패턴 D: 데이터 테이블**
- 좌측: 다크 배지(섹션 라벨) + 표 (헤더행 `#E2EEF9`, 짝수행 `#F5F8FC`)
- 우측: 규칙·산정식 넘버 리스트 (틴트 박스)
- 적합: 기능점수 산정, 비교표, 제공사 개요

**패턴 E: 섹션 구분 / 목차 (파트 전환)**
- 네이비 그라디언트 배경 + 대형 로마자 워터마크(rgba 0.05) + 파트 타이틀
- 목차는 흰 배경에 로마자 + 하위 항목 3열
- 적합: 파트 도입, 목차, 챕터 전환

---

### 4. 컴포넌트 스타일

#### 섹션 헤더 바

| 속성 | 값 |
|------|------|
| 형태 | Rectangle (라운드 6px) |
| 배경 | 단색 `#1E2A5C` 또는 `linear-gradient(90deg,#1E2A5C,#2E74C6)` |
| 텍스트 | White, 20pt, Bold, 가운데 정렬 |
| 용도 | 좌/우 섹션 구분(목적·추진전략, 목표·결과물 등) |

#### 넘버 스퀘어 배지

| 속성 | 값 |
|------|------|
| 형태 | RoundRect (약 34~44px 정사각, radius 5~6px) |
| 배경 | `#2E74C6`(기본) / `#1E2A5C` / `#404155` |
| 텍스트 | White, Bold |
| 용도 | 순서·단계·핵심 항목 번호 |

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
| 용도 | 화면 캡처·이미지·카테고리 라벨 |

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
| 행 높이 | 0.45~0.55″ (12pt 이상 + 여유 패딩) |

#### 인용 콜아웃

| 속성 | 값 |
|------|------|
| 형태 | 좌측 5px `#2E74C6` 바 + 이탤릭 텍스트 |
| 텍스트 | `#1E2A5C`, Bold, Italic |
| 용도 | 기대 효과·핵심 메시지 강조 |

#### 페이지 제목 언더라인

| 속성 | 값 |
|------|------|
| 바탕 | 전폭 3pt `#D9E0EC` |
| 액센트 | 좌측 150px 세그먼트 `#2E74C6` |
| 용도 | 모든 페이지 제목 하단 구분 |

---

### 5. 디자인 규칙

#### 필수 준수 사항

- 콘텐츠는 반드시 **흰색 배경** 위, 좌우 40pt 여백 안에 배치
- 페이지 제목은 `#1E2A5C` ExtraBold 40pt로 좌측 상단에 배치하고 언더라인 룰을 둠
- breadcrumb(경로)는 제목 위 13pt `#7C8598`로 표기
- 본문 텍스트 최소 크기 **12pt** — 12pt 미만이 필요할 정도면 슬라이드를 분리할 것
- 하단 여백이 **1.0인치 이상** 남으면 표·카드의 글자/행 높이를 키워 균형있게 채울 것
- 헤더 바·배지·박스는 **지정 팔레트 내 컬러**만 사용
- 흰 카드에는 `#D9E0EC` 테두리를 추가하여 시인성 확보
- 다크(네이비/슬레이트) 배경 위 텍스트는 반드시 **흰색/밝은색**
- 화면 캡처는 동일 비율·정렬로 그리드 배치하고 필 라벨로 화면명 표기
- 푸터 영역(고정 문구·페이지 번호)에는 콘텐츠 배치 금지

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
- 행 높이를 넉넉히(0.45~0.55″) 잡아 12pt 이상 폰트와 여유 패딩 확보

---

### 6. 코드 생성 시 필수 검증 규칙

PPT 생성 스크립트(JavaScript/pptxgenjs) 작성 시, 아래 규칙을 **코드 레벨에서 강제**할 것.

#### 6-1. 팔레트 상수화

```javascript
const C = {
  navy:   "1E2A5C",  blue:   "2E74C6",  ink:    "2B3242",
  slate:  "4A5364",  sub:    "7C8598",
  tint:   "EEF3FA",  altRow: "F5F8FC",  tableHead: "E2EEF9",
  dark:   "404155",  border: "D9E0EC",  line:   "EDF0F6",
};
```

**규칙**: 색상 리터럴을 슬라이드마다 반복 입력하지 말고 `C.*` 상수 사용.

#### 6-2. 최소 폰트 크기 강제 (12pt)

```javascript
const MIN_FONT = 12;
const fs12 = (size) => {
  if (size < MIN_FONT) throw new Error(`fontSize ${size} < ${MIN_FONT}pt 금지! 슬라이드를 분리할 것`);
  return size;
};
```

**규칙**: `fontSize` 값을 직접 숫자로 쓰지 말고 반드시 `fs12()` 함수를 경유할 것.

#### 6-3. 헤더 바 헬퍼

```javascript
// 단색 / 그라디언트 헤더 바
function headerBar(slide, { x, y, w, text, accent = false }) {
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h: 0.5, rectRadius: 0.06,
    fill: accent
      ? { type: "gradient", stops: [{ color: C.navy, position: 0 }, { color: C.blue, position: 100 }], angle: 0 }
      : { color: C.navy },
    line: { type: "none" },
  });
  slide.addText(text, { x, y, w, h: 0.5, align: "center", color: "FFFFFF",
    bold: true, fontSize: fs12(20), fontFace: FONT });
}
```

**규칙**: 섹션 헤더 바는 헬퍼로 생성. `accent:true` 는 우측 강조 섹션(추진 전략·주요 결과물 등).

#### 6-4. 넘버 배지 헬퍼

```javascript
function numBadge(slide, { x, y, n, color = C.blue, size = 0.4 }) {
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x, y, w: size, h: size, rectRadius: 0.05, fill: { color }, line: { type: "none" },
  });
  slide.addText(String(n), { x, y, w: size, h: size, align: "center", valign: "middle",
    color: "FFFFFF", bold: true, fontSize: fs12(16), fontFace: FONT });
}
```

#### 6-5. 페이지 헤더(제목 + 언더라인) 헬퍼

```javascript
function pageHeader(slide, { crumb, title }) {
  slide.addText(crumb, { x: 0.55, y: 0.45, w: 12, h: 0.3, color: C.sub, fontSize: fs12(13), fontFace: FONT });
  slide.addText(title, { x: 0.55, y: 0.72, w: 14, h: 0.7, color: C.navy, bold: true, fontSize: fs12(40), fontFace: FONT });
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0.55, y: 1.55, w: 14.9, h: 0.04, fill: { color: C.border }, line: { type: "none" } });
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0.55, y: 1.55, w: 2.1,  h: 0.04, fill: { color: C.blue },   line: { type: "none" } });
}
```

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
  const slide = pptx.addSlide({ masterName: "MASTER" });
  pageHeader(slide, { crumb: "Ⅰ. 디자인 시스템 › 2. 컬러", title: "컬러 시스템" });
  // ... 슬라이드 콘텐츠
  return slide;
}
```

**규칙**: 슬라이드 함수는 `async function createSlideXX(pptx)` 형태, 한 함수에 한 슬라이드, `main()`에서 순차 호출.

#### 6-9. 테이블 작성 규칙

```javascript
slide.addTable(
  [
    [ { text: "점수", options: { fill: C.tableHead, color: C.navy, bold: true } },
      { text: "유형", options: { fill: C.tableHead, color: C.navy, bold: true } } ],
    ["7.5", "EIF"],
  ],
  { x: 0.55, y: 1.9, w: 9, colW: [2, 7], fontSize: fs12(12), fontFace: FONT,
    rowH: 0.5, border: { type: "solid", color: C.line, pt: 1 } }
);
```

**규칙**: 행/열 구조 데이터는 `slide.addTable()` 사용 — `addShape`+`addText` 수동 셀 그리기 금지. 헤더행 fill 은 `C.tableHead`.

#### 6-10. 한글 폰트 처리

```javascript
const FONT = "Pretendard";
{ text: "안녕하세요", options: { fontFace: FONT, fontSize: fs12(16) } }
```

**규칙**: `Calibri`, `Arial`, `맑은 고딕` 등 직접 지정 금지. 시스템 폴백은 PPT 뷰어가 처리.

#### 6-11. 빌드 스크립트 진입점

```javascript
async function main() {
  const pptx = new pptxgen();
  pptx.defineLayout({ name: "CUSTOM", width: 16, height: 9 });
  pptx.layout = "CUSTOM";
  pptx.defineSlideMaster({ title: "MASTER", background: { color: "FFFFFF" } /* + 푸터 요소 */ });

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
| 1 | 최소 폰트 크기 | 스크립트 내 모든 fontSize 값 확인 | 12pt 이상 (fs12 경유) |
| 2 | 하단 여백 | 최하단 콘텐츠 ~ 푸터 간 거리 계산 | 1.0인치 미만 |
| 3 | 콘텐츠 누락 | 텍스트 추출 후 원본 대조 | 모든 항목 포함 |
| 4 | 이미지 임베딩 | 스크립트의 이미지 경로 존재 여부 | 파일 존재 확인 |
| 5 | 슬라이드 크기 | 1152 × 648pt (16″ × 9″) | 정확히 일치 |
| 6 | 폰트 | Pretendard 사용 | Calibri/Arial/맑은 고딕 금지 |
| 7 | 컬러 팔레트 | 지정 HEX만 사용 (C.* 상수) | 임의 색상 금지 |
| 8 | 페이지 헤더 | breadcrumb + 제목 + 언더라인 룰 | 전 슬라이드 일관 |
| 9 | Shape 참조 | `pptx.shapes.*` 사용 | `ShapeType` 직접 import 금지 |
| 10 | 슬라이드 함수 | `async function createSlideXX` 패턴 | 동기 함수·인라인 작성 금지 |
| 11 | 표 작성 | `slide.addTable()` + 헤더행 `#E2EEF9` | 셀 수동 그리기 금지 |
| 12 | 빌드 종료 코드 | `node build.js` 실행 후 `$?` 확인 | 0 (성공) |
| 13 | 출력 파일 | `.pptx` 파일 존재 및 크기 | 0바이트 초과 |
