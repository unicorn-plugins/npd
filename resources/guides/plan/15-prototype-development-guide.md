# 프로토타입 개발 가이드

## 목적

UI/UX 설계서를 기반으로 기본 HTML/JavaScript로 동작하는 프로토타입을 개발함.

## 개발 프로세스

### 1단계: 준비
1. `design/uiux/prototype` 디렉토리의 기존 파일 확인
2. 공통 JS/CSS 존재 여부 파악
3. 개발 범위 결정

### 2단계: 실행
1. 공통 파일 개발 (`common.js`, `common.css`)
2. 사용자 플로우 순서대로 화면 개발 (화면별 파일 분리, SPA 방식 금지)
3. 화면 간 전환 구현
4. 샘플 데이터 일관성 유지

### 3단계: 검토
- 작성원칙 준수 여부 확인
- 체크리스트 검토 및 수정

### 4단계: 테스트
- 브라우저 테스트
- 콘솔 에러 확인 및 수정
- 반응형 레이아웃 검증

## 공통 파일 템플릿

### common.js
```javascript
// 샘플 데이터
const sampleData = {
  user: { name: "홍길동", email: "hong@example.com" },
  items: [{ id: 1, name: "상품 A", price: 10000 }]
};

// 화면 전환
function navigateTo(screen, data) {
  const num = screen.toString().padStart(2, '0');
  window.location.href = `${num}-화면명.html`;
}
```

### common.css
```css
:root {
  --primary-color: #007bff;
  --font-family: 'Pretendard', sans-serif;
  --spacing-md: 16px;
}

/* Mobile First */
.container { padding: var(--spacing-md); }

@media (min-width: 768px) {
  .container { max-width: 768px; margin: 0 auto; }
}

@media (min-width: 1024px) {
  .container { max-width: 1200px; }
}
```

### 화면 파일 템플릿
```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{화면명}</title>
  <link rel="stylesheet" href="common.css">
</head>
<body>
  <div class="container">
    <header><!-- 헤더 --></header>
    <main><!-- 콘텐츠 --></main>
    <footer><!-- 푸터 --></footer>
  </div>
  <script src="common.js"></script>
  <script>
    // 화면별 스크립트
  </script>
</body>
</html>
```

## 체크리스트

### 화면별 기능 동작
| 기능 | 예상 결과 | 실제 결과 | 상태 |
|------|-----------|-----------|------|
| 버튼 클릭 | 다음 화면 이동 | - | - |
| 폼 입력 | 데이터 표시 | - | - |

### 화면간 데이터 일관성
| 데이터 | 사용 화면 | 일관성 |
|--------|-----------|--------|

### 화면간 연결성
| 출발 | 연결방법 | 도착 | 상태 |
|------|----------|------|------|

### 스타일시트 누락
HTML에 사용된 CSS 스타일 누락 여부 체크

## 파일 구조

| 유형 | 경로 | 명명규칙 |
|------|------|----------|
| 화면 | `design/uiux/prototype/` | `{2자리번호}-{한글화면명}.html` |
| 공통JS | `design/uiux/prototype/` | `common.js` |
| 공통CSS | `design/uiux/prototype/` | `common.css` |

## 작성 원칙

| 영역 | 규칙 |
|------|------|
| 개발 | HTML/JS만 사용 (프레임워크 금지), 서버 없이 동작, SPA 방식 금지 |
| 데이터 | 실제와 유사한 가상 데이터, 화면 간 일관성 |
| 스타일 | 스타일가이드 준수, Mobile First |
| 테스트 | 브라우저 테스트 필수, 에러 즉시 수정 |

## 주의사항

- HTML/JS만 사용 (프레임워크 금지)
- 서버 없이 동작
- SPA 방식 구현 금지
- 설계서에 없는 화면 추가 금지
- 화면별 파일 분리
- Mobile First
- 스타일가이드 준수
- 샘플 데이터 일관성 유지
