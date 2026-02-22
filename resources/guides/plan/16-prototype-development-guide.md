# 프로토타입 개발 가이드

## 목적

UI/UX 설계서를 기반으로 기본 HTML/JavaScript로 동작하는 프로토타입을 개발함.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| UI/UX 디자인 명세 | `docs/plan/design/uiux/uiux.md` | 사용자 플로우 → 화면 개발 순서, 와이어프레임 → HTML 매핑, 컴포넌트 → Web Components |
| 스타일 가이드 | `docs/plan/design/uiux/style-guide.md` | 컬러·타이포그래피·간격을 CSS 변수로 정의, 반응형 브레이크포인트 참조 |
| 유저스토리 | `docs/plan/design/userstory.md` | 샘플 데이터 구성, 화면별 기능 요구사항 참조 |
| 디자인 레퍼런스 | `docs/plan/design/uiux/references/` | 디자인 톤·레이아웃 참고 (있는 경우) |

## 개발 프로세스

> **핵심 원칙**: "개발 후 테스트"가 아니라 **"개발하면서 테스트"**. 화면 1개 개발 → Playwright로 즉시 테스트 → 통과 후 다음 화면.

### 1단계: 준비
1. UI/UX 설계서에서 사용자 플로우 확인 → 화면 개발 순서 결정
2. 스타일 가이드에서 컬러 팔레트, 타이포그래피, 간격 시스템 확인
3. 디자인 레퍼런스(있는 경우) 확인하여 디자인 톤·레이아웃 참고
4. `docs/plan/design/uiux/prototype/` 디렉토리 생성
5. Gemini API Key가 제공된 경우: `.npd/.env` 파일에 `GEMINI_API_KEY={키값}` 저장

### 2단계: 공통 파일 개발
1. `common.css` — 스타일가이드의 CSS 변수화 (컬러, 타이포그래피, 간격, 브레이크포인트)
2. `common.js` — 샘플 데이터, 화면 전환, localStorage 유틸리티

### 3단계: 화면별 개발-테스트 루프

#### 의존관계 분석 및 병렬 개발

UI/UX 설계서의 사용자 플로우를 분석하여 화면 간 의존관계를 파악하고, 독립적인 화면은 병렬로 개발함.

1. **의존관계 분석**: 사용자 플로우에서 화면 간 의존관계를 도출
   - 독립 화면: 다른 화면의 데이터/상태에 의존하지 않는 화면 (예: 로그인, 회원가입, 소개)
   - 의존 화면: 이전 화면의 결과가 필요한 화면 (예: 목록→상세, 장바구니→결제)
2. **개발 레벨 그룹핑**: 의존관계가 없는 화면끼리 같은 레벨로 그룹화
   ```
   Level 1: [로그인] [회원가입] [소개]     ← 병렬 개발
   Level 2: [메인홈] [마이페이지]           ← Level 1 완료 후 병렬 개발
   Level 3: [상세] [결제]                  ← Level 2 완료 후 병렬 개발
   ```
3. **병렬 개발**: 같은 레벨의 화면들을 병렬 에이전트로 동시 개발
4. **레벨 순차 진행**: 현재 레벨의 모든 화면 완료 후 다음 레벨로 진행

#### 화면 1개당 개발-테스트 사이클

```
[개발] → [Playwright 테스트] → 에러? → [수정] → [재테스트] → 통과 → [완료]
```

1. **개발**: UI/UX 설계서의 와이어프레임과 일대일 매핑하여 HTML 작성
2. **Playwright 즉시 테스트**:
   - `browser_navigate`로 해당 HTML 파일 열기 (file:// 프로토콜)
   - `browser_console_messages`로 콘솔 에러 확인
   - `browser_snapshot`으로 접근성 구조 확인
   - `browser_take_screenshot`으로 UI 렌더링 상태 확인
   - `browser_resize`(375, 812)로 모바일 반응형 확인
3. **수정**: 에러/UI 이슈 발견 시 수정 후 재테스트
4. **완료**: 테스트 통과 후 해당 화면 완료 처리

### 4단계: 통합 테스트 (Playwright 자동 검증)

모든 화면 개발 완료 후, Playwright로 전체 프로토타입을 자동 검증함.

1. **화면간 연결성 테스트**
   - 각 화면의 모든 링크/버튼을 `browser_click`으로 클릭
   - 올바른 페이지로 이동하는지 URL/제목 확인
2. **화면별 기능 동작 테스트**
   - 폼 입력(`browser_type`), 버튼 클릭, 모달/드롭다운 동작 확인
3. **데이터 일관성 테스트**
   - 화면 간 전달되는 샘플 데이터가 일치하는지 확인
4. **반응형 테스트**
   - 데스크톱(1280x800) → 태블릿(768x1024) → 모바일(375x812)
   - 각 뷰포트에서 레이아웃 깨짐 여부 확인
5. **콘솔 에러 전수 검사**
   - 모든 화면에서 `browser_console_messages(level="error")` 확인

### 5단계: 버그 수정 루프

4단계에서 발견된 실패 항목을 수정 → 재테스트 → 모두 통과할 때까지 반복.

1. 테스트결과.md의 실패/비정상 항목 확인
2. 해당 HTML 파일 수정
3. Playwright로 수정된 항목만 재테스트
4. 모든 항목 통과 시 완료, 미통과 시 1번으로 복귀

## 공통 파일 구조 가이드

> **주의**: 아래는 포함해야 할 **항목 목록**임. 구체적인 값은 반드시 스타일가이드(`style-guide.md`)와 유저스토리(`userstory.md`)에서 가져와 작성할 것.

### common.css 포함 항목

| 영역 | CSS 변수 항목 | 값 출처 |
|------|--------------|---------|
| 컬러 팔레트 | `--color-primary`, `--color-secondary`, `--color-accent`, `--color-success`, `--color-warning`, `--color-error`, `--color-info` | 스타일가이드 컬러 섹션 |
| 텍스트/배경 컬러 | `--color-text-primary`, `--color-text-secondary`, `--color-text-disabled`, `--color-bg-light`, `--color-bg-dark` | 스타일가이드 컬러 섹션 |
| 타이포그래피 | `--font-family`, `--font-size-h1`~`h3`, `--font-size-body1`~`body2`, `--font-size-caption` | 스타일가이드 타이포그래피 섹션 |
| 간격 시스템 | `--spacing-xs`~`xxl` | 스타일가이드 간격 섹션 |
| 브레이크포인트 | `--breakpoint-tablet`, `--breakpoint-desktop` | 스타일가이드 반응형 섹션 |

**필수 포함 스타일**:
- CSS 리셋 (`box-sizing: border-box`, margin/padding 초기화)
- Mobile First 컨테이너 레이아웃 (미디어 쿼리로 태블릿/데스크톱 확장)
- 접근성: `.sr-only` 클래스, `:focus-visible` 포커스 인디케이터

### common.js 포함 기능

#### 유틸리티 함수

| 기능 | 설명 | 비고 |
|------|------|------|
| 샘플 데이터 | 유저스토리 기반 가상 데이터 객체 | 유저스토리의 사용자/데이터와 일치시킬 것 |
| 화면 전환 | `navigateTo(filename, data)` — 페이지 이동 + 데이터 전달 | `localStorage` 사용 |
| 데이터 수신 | `getPageData()` / `clearPageData()` — 전달된 데이터 조회/삭제 | |
| 폼 자동 저장 | `saveFormData(formId)` / `restoreFormData(formId)` | 폼이 있는 화면에서 사용 |

#### Web Components (공통 UI 컴포넌트)

> **핵심**: 헤더, 푸터, 네비게이션 등 **반복되는 UI 요소는 Web Components로 정의**하여 중복을 제거하고 화면 간 일관성을 보장함. Web Components는 웹 표준(브라우저 내장 API)이므로 프레임워크가 아님.

`common.js`에 `customElements.define()`으로 공통 컴포넌트를 등록함:

| 컴포넌트 | 태그명 (예시) | 설명 |
|----------|-------------|------|
| 헤더 | `<app-header>` | 로고, 네비게이션 메뉴, 현재 페이지 하이라이트 |
| 푸터 | `<app-footer>` | 저작권, 링크 등 |
| 네비게이션 | `<app-nav>` | 탭바, 사이드바 등 (모바일/데스크톱 분기) |
| 기타 | 설계서 기반 | 카드, 모달, 알림 등 반복 사용되는 UI 요소 |

**장점**:
- 한 곳(`common.js`) 수정으로 모든 화면에 즉시 반영
- 각 화면은 고유 콘텐츠(`<main>`)에만 집중
- `file://` 프로토콜에서 동작 (별도 import 없이 `common.js`에 모두 정의)

### 화면 HTML 필수 구조

| 항목 | 필수 요소 |
|------|----------|
| 문서 선언 | `<!DOCTYPE html>`, `lang="ko"`, `charset="UTF-8"`, `viewport` 메타태그 |
| 스타일 연결 | `common.css` 링크 + 화면별 `<style>` 블록 |
| 공통 컴포넌트 | `<app-header>`, `<app-footer>` 등 Web Components 사용 (직접 HTML 작성 금지) |
| 화면 콘텐츠 | `<main role="main">` 안에 해당 화면 고유 콘텐츠만 작성 |
| 스크립트 연결 | `common.js` + 화면별 `<script>` (`DOMContentLoaded` 이벤트 내 초기화) |
| 접근성 | ARIA 레이블, 폼 `<label>` 연결, 이미지 `alt` 속성 |

## 이미지 생성 (Gemini API Key 제공 시)

프로토타입에 이미지가 필요한 경우 AI 이미지 생성 도구를 활용함.

- **도구 경로**: `resources/tools/customs/general/generate_image.py`
- **API Key 위치**: `.npd/.env` (`GEMINI_API_KEY={키값}`)
- **사용법**:
  ```bash
  python resources/tools/customs/general/generate_image.py \
    --prompt "이미지 설명" \
    --output-dir docs/plan/design/uiux/prototype/images \
    --output-name {파일명} \
    --api-key $(grep GEMINI_API_KEY .npd/.env | cut -d= -f2)
  ```
- **API Key 미제공 시**: 이미지 대신 placeholder 텍스트(`[이미지: {설명}]`) 사용

> **주의**: `.npd/` 디렉토리는 `.gitignore`에 포함되어야 함. API Key가 git에 업로드되지 않도록 할 것.

## 접근성 필수 사항

| 항목 | 구현 방법 |
|------|----------|
| 시맨틱 HTML | `<header>`, `<nav>`, `<main>`, `<footer>`, `<section>`, `<article>` 사용 |
| ARIA 레이블 | `role`, `aria-label`, `aria-describedby` 속성 적용 |
| 폼 레이블 | 모든 입력 필드에 `<label>` 연결 (`for`/`id` 매칭) |
| 대체 텍스트 | 모든 `<img>`에 `alt` 속성 |
| 포커스 인디케이터 | `:focus-visible` 스타일 유지 (제거 금지) |
| 키보드 접근 | Tab 순서 논리적 배치, Enter/Space로 동작 |
| 색상 대비 | 텍스트 4.5:1 이상, UI 컴포넌트 3:1 이상 |

## 출력 형식

- `docs/plan/design/uiux/prototype/common.js` — 공통 JavaScript
- `docs/plan/design/uiux/prototype/common.css` — 공통 CSS
- `docs/plan/design/uiux/prototype/{2자리번호}-{한글화면명}.html` — 각 화면 파일
- `docs/plan/design/uiux/prototype/테스트결과.md` — 통합 테스트 결과

## 품질 기준

### 완료 체크리스트
- [ ] common.css에 스타일가이드 CSS 변수 정의 완료
- [ ] common.js에 Web Components 공통 UI 정의 완료
- [ ] 모든 화면 HTML 파일 생성 완료
- [ ] 화면별 Playwright 테스트 통과 (콘솔 에러 0건)
- [ ] 반응형 확인 (모바일 375x812 / 태블릿 768x1024 / 데스크톱 1280x800)
- [ ] 화면간 연결성 테스트 통과
- [ ] 화면간 데이터 일관성 확인
- [ ] 접근성 필수 사항 준수 (시맨틱 HTML, ARIA, 폼 레이블, 포커스 인디케이터)
- [ ] UI/UX 설계서 와이어프레임과 일대일 매핑 확인
- [ ] 설계서에 없는 화면이 추가되지 않았는지 확인
- [ ] 통합 테스트 결과 `테스트결과.md` 작성 완료

### 정량 기준
- 콘솔 에러: 0건
- 반응형 뷰포트: 3종 (모바일/태블릿/데스크톱)
- 화면간 연결성: 전체 링크/버튼 테스트 통과
- 접근성: WCAG 2.1 AA 준수

### 화면별 기능 동작
| 기능 | 예상 결과 | 실제 결과 | 상태 |
|------|-----------|-----------|------|
| 버튼 클릭 | 다음 화면 이동 | - | - |
| 폼 입력 | 데이터 표시/검증 | - | - |
| 폼 자동 저장 | localStorage 저장/복원 | - | - |

### 화면 간 데이터 일관성
| 데이터 | 사용 화면 | 일관성 |
|--------|-----------|--------|

### 화면 간 연결성
| 출발 화면 | 연결 방법 | 도착 화면 | 상태 |
|-----------|----------|-----------|------|

### 스타일 검증
| 항목 | 확인 |
|------|------|
| CSS 변수가 스타일가이드와 일치하는가 | - |
| Mobile First로 작성되었는가 | - |
| 모바일(< 768px) 레이아웃 정상 | - |
| 태블릿(768px~1024px) 레이아웃 정상 | - |
| 데스크톱(> 1024px) 레이아웃 정상 | - |
| HTML에 사용된 CSS 클래스가 모두 정의되었는가 | - |

### 접근성 검증
| 항목 | 확인 |
|------|------|
| 시맨틱 HTML 태그 사용 | - |
| 폼 필드에 label 연결 | - |
| 이미지에 alt 속성 | - |
| 키보드만으로 전체 기능 동작 | - |
| 포커스 인디케이터 표시 | - |

## 파일 구조

| 유형 | 경로 | 명명규칙 |
|------|------|----------|
| 공통 CSS | `docs/plan/design/uiux/prototype/` | `common.css` |
| 공통 JS | `docs/plan/design/uiux/prototype/` | `common.js` |
| 화면 | `docs/plan/design/uiux/prototype/` | `{2자리번호}-{한글화면명}.html` |

## 작성 원칙

| 영역 | 규칙 |
|------|------|
| 개발 | HTML/JS만 사용 (프레임워크 금지), 서버 없이 동작, SPA 방식 금지 |
| 데이터 | 실제와 유사한 가상 데이터, 화면 간 일관성, localStorage로 데이터 전달 |
| 스타일 | 스타일가이드 CSS 변수화, Mobile First, 디자인 레퍼런스 참고 (있는 경우) |
| 접근성 | 시맨틱 HTML, ARIA 레이블, 폼 레이블, 포커스 인디케이터 |
| 테스트 | 브라우저 테스트 필수 (모바일/태블릿/데스크톱), 콘솔 에러 즉시 수정 |

## 주의사항

- HTML/JS만 사용 (프레임워크 금지)
- 서버 없이 동작 (파일을 브라우저에서 직접 열어 동작)
- SPA 방식 구현 금지 (화면별 파일 분리)
- 설계서에 없는 화면 추가 금지
- Mobile First 반응형 구현
- 스타일가이드의 컬러·타이포그래피·간격을 CSS 변수로 정확히 반영
- 디자인 레퍼런스가 있는 경우 디자인 톤·레이아웃 참고
- 샘플 데이터 일관성 유지 (모든 화면에서 동일 사용자·데이터)
- 접근성 필수 사항 준수
