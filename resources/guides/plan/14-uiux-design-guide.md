# UI/UX 설계 가이드

## 목적

유저스토리를 기반으로 상세한 UI/UX 디자인 명세를 작성함.

## UI/UX 디자인 명세 구성

### 1. 디자인 원칙
- 핵심 원칙 5개 정의
- 디자인 언어: 톤 앤 매너, 브랜드 키워드

### 2. 정보 아키텍처
- **사이트맵**: 트리 구조로 전체 화면 계층 표현
- **네비게이션 구조**: 주 네비게이션, 부 네비게이션, 푸터 네비게이션

### 3. 사용자 플로우
각 기능별 화면 흐름도:
```
시작 → [화면 1] → [화면 2] → [화면 3] → 완료
```

### 4. 와이어프레임 (최소 5개 주요 화면)
ASCII 아트 기반 와이어프레임:
```
+----------------------------------------+
|  [로고]     [메뉴] [메뉴] [메뉴]          |
+----------------------------------------+
|     [{영역명}]                          |
|     - {요소 1}                          |
|     - {요소 2}                          |
+----------------------------------------+
|     [{메인 컨텐츠 영역}]                 |
+----------------------------------------+
|  {푸터}                                |
+----------------------------------------+
```

### 5. 컴포넌트 라이브러리

#### 버튼
- Primary Button, Secondary Button, Text Button
- 크기, 색상, 사용 케이스 정의

#### 폼 요소
- Input Field (타입, 상태: default/focus/error/disabled)
- Dropdown, Checkbox/Radio, Date Picker, File Upload

#### 카드
- Content Card, Product Card, User Card

#### 네비게이션
- Top Navigation Bar, Sidebar, Breadcrumb, Pagination

#### 피드백
- Toast/Snackbar, Modal/Dialog, Alert/Error Messages, Loading Spinner

### 6. 접근성 (WCAG 2.1 AA)
- [ ] 키보드 네비게이션 지원
- [ ] 스크린 리더 호환
- [ ] 색상 대비율 >= 4.5:1 (텍스트), >= 3:1 (UI 컴포넌트)
- [ ] 이미지 대체 텍스트
- [ ] ARIA 레이블
- [ ] 폼 레이블
- [ ] 포커스 인디케이터

## 스타일 가이드 구성

### 컬러 팔레트
```
Primary Color: #{HEX}
Secondary Color: #{HEX}
Accent Color: #{HEX}

텍스트: Primary #{HEX}, Secondary #{HEX}, Disabled #{HEX}
배경: Light #{HEX}, Dark #{HEX}
상태: Success #{HEX}, Warning #{HEX}, Error #{HEX}, Info #{HEX}
```

### 타이포그래피
```
Font Family: {폰트명}
H1: {크기}px, {굵기}, {행간}
H2: {크기}px, {굵기}, {행간}
H3: {크기}px, {굵기}, {행간}
Body 1: {크기}px, {굵기}, {행간}
Body 2: {크기}px, {굵기}, {행간}
```

### 간격 시스템
```
XS: 4px  / S: 8px  / M: 16px / L: 24px / XL: 32px / XXL: 48px
```

### 반응형 브레이크포인트
```
모바일: < 768px (단일 컬럼, 햄버거 메뉴, 터치 타겟 최소 44x44px)
태블릿: 768px - 1024px (2단 컬럼, 사이드바 또는 탭)
데스크톱: > 1024px (다단 컬럼, 전체 메뉴바)
```

### 인터랙션 디자인
- Duration: 300ms (기본)
- Easing: ease-in-out
- 버튼 클릭, 폼 입력, 페이지 전환, 로딩 상태 효과 정의

## 주의사항

- Mobile First 접근
- 최소 5개 이상 주요 화면 와이어프레임
- ASCII 아트 기반 와이어프레임 사용
- 컴포넌트 라이브러리 완전히 정의
- 모든 컴포넌트에 일관성 보장
- 스타일 가이드 구체적으로 (HEX 코드, px 단위)
- 접근성 WCAG 2.1 AA 이상 준수
- 유저스토리와 일대일 매핑
- 유저스토리에 없는 화면 디자인 금지
