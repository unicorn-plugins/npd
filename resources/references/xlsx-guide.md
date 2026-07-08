# XLSX 작성 가이드 (xlsx-build-guide)

## 0. 패턴 개요 (Builder Skill 단독 — 1단계)

XLSX는 데이터 구조(시트·행·열·셀) 자체가 곧 명세이므로 별도 spec-writer 에이전트를 두지 않음.
**빌더 스킬이 입력 데이터를 받아 openpyxl 빌드 코드를 직접 작성·실행**함.

```
[입력 데이터]                            ← 표/리스트(JSON·CSV·마크다운 표 등) 또는
   (사용자 제공 또는                       선행 에이전트의 구조화 산출물
    선행 에이전트 산출물)
        ↓
[Builder Skill (오케스트레이터)]
  1. 본 가이드 로드
  2. 입력 데이터 → openpyxl 빌드 코드 작성
  3. python 실행 → .xlsx 생성
  4. 파일 검증 + 사용자 보고
        ↓
[*.xlsx 산출물]
```

**원칙**:
- **별도 spec-writer 에이전트 없음** — 입력 데이터가 곧 명세
- 오케스트레이터(스킬)가 빌드+실행+검증 (Write + Bash)
- 외부 변환 스킬(`anthropic-skills:xlsx` 등) 의존 금지
- 빌더 스킬은 본 가이드 4절(코드 생성 시 필수 검증 규칙)을 **반드시 준수**

**런타임 요구사항**: `python ≥ 3.9`, `pip install openpyxl` (생성 플러그인의 setup 스킬에서 자동 설치)

---

## 1. 입력 형식 규약

빌더 스킬이 받을 입력 형태는 다음 중 하나임:

| 입력 유형 | 권장 사용 케이스 | 예시 |
|----------|-----------------|------|
| 마크다운 표 | 단일 시트, 사람이 작성한 명세 | 강의계획서, 보고 양식 |
| JSON 객체 배열 | 다중 시트, 프로그램 산출물 | `[{"sheet": "M1", "rows": [...]}]` |
| CSV 파일 경로 | 대용량 단일 시트 | `data/sales-2026.csv` |
| Python dict | 시트별 구조화 데이터 + 메타 | `{"sheets": {"summary": {...}, "detail": {...}}}` |

**필수 메타정보** (입력에 포함되거나 빌더가 추론해야 함):
- 시트 이름과 순서
- 헤더 행 위치 (보통 1행)
- 각 컬럼의 데이터 타입 (텍스트/숫자/날짜/수식)
- 병합 셀 범위 (있는 경우)
- 인쇄 영역·열 너비 등 레이아웃 힌트

---

## 2. 빌드 환경

### 2-1. 의존성 설치
```bash
pip install openpyxl
# (선택) 차트·이미지 사용 시: pip install pillow
```

### 2-2. 권장 폴더 구조
```
output/{산출물명}/
├── build.py              # 빌더 스킬이 작성하는 빌드 코드
├── input/                # 입력 데이터 (옵션)
│   └── data.json
└── result.xlsx           # 빌드 산출물
```

### 2-3. 실행
```bash
cd output/{산출물명} && python build.py
```

---

## 3. 스타일 규약

### 3-1. 컬러 팔레트 (DMAP 표준)

| 역할 | HEX | 용도 |
|------|-----|------|
| 헤더 배경 | `#1F4E79` | 시트 헤더 행 |
| 헤더 글자 | `#FFFFFF` | 시트 헤더 텍스트 |
| 강조 1 | `#2E75B6` | 카테고리·소제목 |
| 강조 2 | `#5B9BD5` | 서브 카테고리 |
| 본문 배경 | `#FFFFFF` | 데이터 셀 |
| 본문 글자 | `#212121` | 데이터 텍스트 |
| 보조 배경 | `#F2F2F2` | 줄무늬 짝수 행 |
| 테두리 | `#BFBFBF` | 셀 경계선 |
| 합계/요약 | `#FFF2CC` | 합계 행 배경 |

### 3-2. 폰트 체계

| 용도 | 폰트 | 크기 | 굵기 |
|------|------|------|------|
| 시트 제목 | 맑은 고딕 | 14pt | Bold |
| 헤더 행 | 맑은 고딕 | 11pt | Bold (white) |
| 본문 | 맑은 고딕 | 10pt | Regular |
| 합계/요약 | 맑은 고딕 | 11pt | Bold |
| 숫자 셀 | Consolas | 10pt | Regular |

### 3-3. 정렬 규칙
- 텍스트: 좌측 정렬 (`Alignment(horizontal="left", vertical="center")`)
- 숫자/날짜: 우측 정렬
- 헤더: 가운데 정렬
- 줄바꿈 필요 셀: `wrap_text=True`

---

## 4. 코드 생성 시 필수 검증 규칙

### 4-1. 셀 주소 정확성

**MUST**: `ws["A1"]` 또는 `ws.cell(row=1, column=1)` 둘 중 하나로 일관되게 사용. 혼용 금지.

```python
# ✅ 권장
ws["A1"] = "제목"
ws.cell(row=2, column=1, value="데이터")  # 다른 함수 내에서 일관되게

# ❌ 금지: 동일 함수 내 혼용
ws["A1"] = "x"
ws.cell(row=1, column=2, value="y")  # 한 함수 내 혼용 시 가독성 저하
```

### 4-2. 병합 셀 1회 호출

**MUST**: 동일 범위에 `merge_cells` 중복 호출 금지. 병합 후 좌상단 셀에만 값 할당.

```python
# ✅ 권장
ws.merge_cells("A1:D1")
ws["A1"] = "통합 헤더"
ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

# ❌ 금지: 병합 후 다른 셀에 값 할당 → 무시됨
ws.merge_cells("A1:D1")
ws["B1"] = "x"   # 무시됨
```

### 4-3. 스타일 객체 재사용

**MUST**: `Font`, `Fill`, `Alignment`, `Border` 객체를 모듈 상단에서 1회 정의하고 재사용.
셀별 신규 생성 시 메모리·파일 크기 폭증.

```python
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# ✅ 모듈 상단에서 1회 정의
HEADER_FONT = Font(name="맑은 고딕", size=11, bold=True, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
THIN = Side(border_style="thin", color="BFBFBF")
BORDER_ALL = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

# 사용
for col in range(1, 6):
    cell = ws.cell(row=1, column=col)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = HEADER_ALIGN
    cell.border = BORDER_ALL
```

### 4-4. 수식 작성 규칙

**MUST**: 수식은 반드시 `=`로 시작하는 문자열. 셀 참조는 영문 대문자.

```python
# ✅ 권장
ws["E10"] = "=SUM(E2:E9)"
ws["F2"] = "=B2*C2"

# ❌ 금지
ws["E10"] = "SUM(E2:E9)"   # = 누락 → 텍스트로 저장됨
ws["F2"] = "=b2*c2"        # 소문자 셀 참조 → 일부 환경에서 오작동
```

### 4-5. 인쇄 설정

**MUST**: 가로 비율 인쇄가 필요한 시트는 `page_setup.fitToWidth=1` 명시. 인쇄 영역도 지정.

```python
# ✅ 권장
ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
ws.page_setup.paperSize = ws.PAPERSIZE_A4
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.print_area = "A1:F50"
```

### 4-6. 한글 폰트 명시

**MUST**: 한글 데이터가 있는 셀에 폰트를 명시하지 않으면 환경별 렌더링 차이 발생.
모든 텍스트 셀에 `Font(name="맑은 고딕")` 또는 `Font(name="Pretendard")` 명시.

```python
# ✅ 권장
DEFAULT_FONT = Font(name="맑은 고딕", size=10)
for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
    for cell in row:
        if cell.value is not None and cell.font.name in (None, "Calibri"):
            cell.font = DEFAULT_FONT
```

### 4-7. 열 너비·행 높이 설정

**MUST**: 데이터 길이에 따라 열 너비를 자동 또는 수동 지정. 헤더 행은 최소 25pt.

```python
# ✅ 권장
ws.column_dimensions["A"].width = 30
ws.column_dimensions["B"].width = 15
ws.row_dimensions[1].height = 30   # 헤더 행
```

### 4-8. 빌드 스크립트 진입점

**MUST**: `if __name__ == "__main__":` 블록에서 예외 처리 + 종료 코드 명시.

```python
import sys
from pathlib import Path
from openpyxl import Workbook

def build():
    wb = Workbook()
    # ... 빌드 로직 ...
    output = Path(__file__).parent / "result.xlsx"
    wb.save(str(output))
    print(f"[OK] saved: {output} ({output.stat().st_size:,} bytes)")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(build())
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
```

### 4-9. 자가 검증 체크리스트

빌드 코드 작성 후 다음 11항을 모두 확인:

- [ ] 모든 시트가 의도한 이름·순서로 생성됨
- [ ] 헤더 행에 폰트·배경·정렬·테두리 적용
- [ ] 병합 셀이 의도한 범위로만 1회 적용됨
- [ ] 모든 수식이 `=`로 시작, 결과 정상 계산됨 (Excel에서 확인)
- [ ] 한글 셀에 한글 폰트 적용됨
- [ ] 열 너비·행 높이 설정됨 (자동 잘림 없음)
- [ ] 인쇄 영역·방향·용지 크기 설정됨 (필요 시)
- [ ] 줄무늬·합계 행 등 가독성 스타일 적용됨
- [ ] 빌드 스크립트 종료 코드 0
- [ ] 결과 `.xlsx` 파일 0바이트 초과
- [ ] Excel/LibreOffice에서 열어 시각적 검증 통과

---

## 5. 빌더 스킬 호출 흐름 (예제)

```markdown
### Phase X. XLSX 파일 생성 (Build & Verify)

오케스트레이터가 외부 스킬 위임 없이 직접 수행:

1. **가이드 로드**: `{DMAP_PLUGIN_DIR}/resources/guides/office/xlsx-build-guide.md` 읽기
2. **입력 분석**: 사용자 제공 데이터 또는 선행 에이전트 산출물 파싱
3. **빌드 코드 작성**: Write 도구로 `output/{산출물명}/build.py` 생성
   - openpyxl 사용
   - **반드시 본 가이드 4절 검증 규칙 9항 모두 준수**
   - 스타일 객체 재사용, 병합 셀 1회 호출, 한글 폰트 명시 등
4. **빌드 실행**: Bash로 `cd output/{산출물명} && python build.py` 실행
   → `output/{산출물명}/result.xlsx` 생성
5. **검증**:
   - 빌드 종료 코드 0 확인
   - `.xlsx` 파일 존재 및 0바이트 초과 확인
   - 실패 시 에러 분석 → 코드 수정 → 재실행 (최대 3회)
6. **사용자 보고**: 절대 경로, 파일 크기, 시트 수, 빌드 스크립트 경로
```

---

## 6. 트러블슈팅

### 6-1. 멀티 인덱스 헤더 (2단 헤더)

```python
# 1행: 대분류 (병합), 2행: 소분류
ws.merge_cells("B1:D1"); ws["B1"] = "매출"
ws.merge_cells("E1:G1"); ws["E1"] = "비용"
ws["B2"] = "1Q"; ws["C2"] = "2Q"; ws["D2"] = "3Q"
ws["E2"] = "1Q"; ws["F2"] = "2Q"; ws["G2"] = "3Q"
# 데이터는 3행부터
```

### 6-2. 한글 깨짐
- `wb.save()` 시 파일명에 한글 사용 시 OS 인코딩 의존 → `pathlib.Path` 사용 권장
- 셀 폰트가 None이면 Excel 기본 폰트(Calibri)로 표시 → 한글 폰트 명시 필수

### 6-3. 차트 추가 (선택)
```python
from openpyxl.chart import BarChart, Reference

chart = BarChart()
data = Reference(ws, min_col=2, min_row=1, max_col=4, max_row=10)
cats = Reference(ws, min_col=1, min_row=2, max_row=10)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, "F1")
```

### 6-4. Windows 경로
- 항상 `pathlib.Path` 또는 forward-slash(`/`) 사용
- 백슬래시 직접 사용 시 이스케이프 필요

### 6-5. Excel 호환성
- 수식은 Excel에서 한 번 열어 저장하면 결과값이 캐시됨 (LibreOffice는 자동 계산)
- `data_only=True`로 다시 로드해야 결과값 조회 가능
