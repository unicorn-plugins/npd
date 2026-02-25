# 프론트엔드 프로젝트 초기화 가이드

## 목적

프로토타입과 API 설계서를 기반으로 프론트엔드 프로젝트를 초기화하고 기반 시스템을 구축한다.
페이지 구현 이전 단계로, 스타일 시스템·라우팅·상태 관리·API 클라이언트 골격을 완성하여 이후 개발이 일관된 기반 위에서 시작되도록 한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 프로토타입 | `docs/plan/design/uiux/prototype/` | 화면 구조(HTML), 스타일(CSS), 인터랙션(JS), API 연동 포인트 |
| 종합 개발 계획서 | `docs/develop/dev-plan.md` | 기술스택(섹션 10-5), 서비스 목록(섹션 1) |
| API 설계서 | `docs/design/api/*.yaml` | API 클라이언트 서비스 레이어, Prism Mock 설정 |

## 출력 (이 단계 산출물)

<!-- IF PLATFORM == REACT -->
| 산출물 | 파일 경로 |
|--------|----------|
| 프로젝트 골격 | `frontend/` |
| CSS 변수·테마 | `frontend/src/styles/` |
| 라우팅 설정 | `frontend/src/router/` |
| 상태 관리 스토어 | `frontend/src/store/` |
| API 클라이언트 | `frontend/src/services/api/` |
| 환경변수 예시 | `frontend/.env.example` |
<!-- ELIF PLATFORM == VUE -->
| 산출물 | 파일 경로 |
|--------|----------|
| 프로젝트 골격 | `frontend/` |
| CSS 변수·테마 | `frontend/src/styles/` |
| 라우팅 설정 | `frontend/src/router/` |
| 상태 관리 스토어 | `frontend/src/store/` |
| API 클라이언트 | `frontend/src/services/api/` |
| 환경변수 예시 | `frontend/.env.example` |
<!-- ELIF PLATFORM == FLUTTER -->
| 산출물 | 파일 경로 |
|--------|----------|
| 프로젝트 골격 | `frontend/` |
| 테마 시스템 | `frontend/lib/core/theme/` |
| 라우팅 설정 | `frontend/lib/routing/` |
| 상태 관리 Provider | `frontend/lib/features/` |
| API 클라이언트 | `frontend/lib/core/network/` |
| 의존성 명세 | `frontend/pubspec.yaml` |
<!-- ENDIF -->

## 방법론

### 작업 순서 개요

1. 기술스택 판별
2. 프로젝트 생성 및 폴더 구조 설정
3. 의존성 설치
4. 스타일 시스템 구축
5. 라우팅 시스템 구축
6. 상태 관리 시스템 구축
7. API 클라이언트 기본 설정
8. 실행 확인

---

### 1단계. 기술스택 판별

`docs/develop/dev-plan.md` 섹션 10-5의 기술스택 정보를 읽고 아래 키워드 매핑표로 플랫폼을 **자동 판별**한다.
사용자가 별도로 지정한 스택이 있으면 그것을 우선한다.

#### 판별 키워드 매핑표

| `dev-plan.md 섹션 10-5` 내 키워드 | 판별 결과 (`{PLATFORM}`) |
|-----------------------------------------|--------------------------|
| React, Next.js, Vite+React | `REACT` |
| Vue, Nuxt, Vite+Vue | `VUE` |
| Flutter, Dart, 모바일 앱 | `FLUTTER` |

판별 불가(키워드 없음 또는 복수 매핑) 시 사용자에게 직접 질문한다:

> "고수준 아키텍처 문서에서 프론트엔드 프레임워크를 확인하지 못했습니다. REACT / VUE / FLUTTER 중 어떤 플랫폼을 사용하시나요?"

판별이 완료되면 `{PLATFORM}` 변수를 확정하고 이후 모든 단계에서 해당 분기만 실행한다.

<!-- IF PLATFORM == REACT -->
**REACT 선택 시 추가 기술스택 기준:**

| 항목 | 기준 후보 | 비고 |
|------|----------|------|
| 빌드 도구 | Vite | 기본 권장 |
| 언어 | TypeScript | 기본 권장 |
| 라우팅 | react-router-dom v6 | 기본 권장 |
| 클라이언트 상태 관리 | Zustand / Redux Toolkit | 규모에 따라 선택 |
| 서버 상태 관리 | TanStack Query (React Query) / SWR | 기본 권장 |
| HTTP 클라이언트 | axios | 기본 권장 |
| 스타일링 | CSS Modules / Tailwind CSS / styled-components | style-guide.md 확인 후 결정 |
| 개발 서버 포트 | 3000 | 고정 |
<!-- ELIF PLATFORM == VUE -->
**VUE 선택 시 추가 기술스택 기준:**

| 항목 | 기준 후보 | 비고 |
|------|----------|------|
| 빌드 도구 | Vite | 기본 권장 |
| 언어 | TypeScript | 기본 권장 |
| 라우팅 | vue-router v4 | 기본 권장 |
| 클라이언트 상태 관리 | Pinia | 기본 권장 |
| 서버 상태 관리 | TanStack Query / SWR | 기본 권장 |
| HTTP 클라이언트 | axios | 기본 권장 |
| 스타일링 | CSS Modules / Tailwind CSS | style-guide.md 확인 후 결정 |
| 개발 서버 포트 | 3000 | 고정 |
<!-- ELIF PLATFORM == FLUTTER -->
**FLUTTER 선택 시 추가 기술스택 기준:**

| 항목 | 기준 후보 | 비고 |
|------|----------|------|
| 언어 | Dart | 고정 |
| 라우팅 | go_router | 기본 권장 |
| 상태 관리 | Riverpod | 기본 권장 |
| HTTP 클라이언트 | Dio | 기본 권장 |
| 토큰 저장 | flutter_secure_storage | localStorage 사용 불가 |
| 코드 생성 | build_runner + freezed | 기본 권장 |
<!-- ENDIF -->

기술스택이 결정되면 사용자에게 확인을 받고 다음 단계로 진행한다.

---

### 2단계. 프로젝트 생성 및 폴더 구조 설정

#### 2.1 프로젝트 생성

기존 `frontend/` 디렉토리가 있으면 그대로 유지하면서 작업한다.
없으면 선택한 플랫폼에 따라 생성한다.

<!-- IF PLATFORM == REACT -->
```bash
# Vite + React + TypeScript
npm create vite@latest frontend -- --template react-ts
```
<!-- ELIF PLATFORM == VUE -->
```bash
# Vite + Vue + TypeScript
npm create vite@latest frontend -- --template vue-ts
```
<!-- ELIF PLATFORM == FLUTTER -->
```bash
# Flutter 프로젝트 생성
# {ORG}: 조직 식별자 (예: com.example), {PROJECT_NAME}: 프로젝트명 (예: myapp)
flutter create --org {ORG} --project-name {PROJECT_NAME} frontend
```
<!-- ENDIF -->

#### 2.2 폴더 구조 생성

`프로토타입`의 메뉴 및 화면 계층을 기반으로 폴더를 구성한다.

<!-- IF PLATFORM == REACT -->
아래는 React 기준 참조 구조이며, 정보아키텍처에 맞게 조정한다.

```
frontend/
├── public/
│   └── runtime-env.js          # 런타임 환경변수
├── src/
│   ├── assets/                 # 이미지, 폰트 등 정적 자원
│   ├── components/             # 공통 UI 컴포넌트 (이 단계에서는 골격만)
│   │   └── common/
│   ├── layouts/                # 레이아웃 컴포넌트 (이 단계에서는 골격만)
│   ├── pages/                  # 페이지 컴포넌트 (이 단계에서는 빈 파일만)
│   │   └── NotFound.tsx
│   ├── router/                 # 라우팅 설정
│   │   └── index.tsx
│   ├── services/               # API 클라이언트 및 서비스 레이어
│   │   └── api/
│   │       ├── client.ts       # axios 인스턴스
│   │       └── config.ts       # baseURL, 헤더 등 공통 설정
│   ├── store/                  # 상태 관리
│   │   └── index.ts
│   ├── styles/                 # 전역 스타일
│   │   ├── variables.css       # CSS 변수
│   │   ├── reset.css           # CSS 리셋
│   │   └── global.css          # 전역 스타일
│   ├── types/                  # 타입 정의
│   │   └── api.ts
│   ├── hooks/                  # 커스텀 훅 (이 단계에서는 골격만)
│   ├── utils/                  # 유틸리티 함수
│   ├── App.tsx
│   └── main.tsx
├── .env.example
├── .env.local                  # 로컬 개발용 (gitignore)
├── vite.config.ts
├── tsconfig.json
└── package.json
```

`pages/` 하위 폴더는 `ia.md`의 메뉴 계층과 일치하도록 생성한다.
예시: `ia.md`에 대시보드·사용자·설정 메뉴가 있으면 `pages/dashboard/`, `pages/users/`, `pages/settings/`를 생성하고 각각 빈 `index.tsx`를 추가한다.
<!-- ELIF PLATFORM == VUE -->
아래는 Vue 기준 참조 구조이며, 정보아키텍처에 맞게 조정한다.

```
frontend/
├── public/
│   └── runtime-env.js          # 런타임 환경변수
├── src/
│   ├── assets/
│   ├── components/
│   │   └── common/
│   ├── layouts/
│   ├── views/                  # 페이지 컴포넌트 (이 단계에서는 빈 파일만)
│   │   └── NotFound.vue
│   ├── router/
│   │   └── index.ts
│   ├── services/
│   │   └── api/
│   │       ├── client.ts
│   │       └── config.ts
│   ├── stores/                 # Pinia 스토어
│   │   └── auth.ts
│   ├── styles/
│   │   ├── variables.css
│   │   ├── reset.css
│   │   └── global.css
│   ├── types/
│   │   └── api.ts
│   ├── composables/
│   ├── utils/
│   ├── App.vue
│   └── main.ts
├── .env.example
├── .env.local
├── vite.config.ts
├── tsconfig.json
└── package.json
```

`views/` 하위 폴더는 `ia.md`의 메뉴 계층과 일치하도록 생성한다.
<!-- ELIF PLATFORM == FLUTTER -->
아래는 Flutter feature-first 구조이며, `ia.md`의 화면 계층과 매핑된다.

```
frontend/
├── lib/
│   ├── core/                   # 공통 유틸, 상수, 테마, 네트워크
│   │   ├── constants/
│   │   ├── network/
│   │   │   ├── dio_client.dart         # Dio 인스턴스
│   │   │   └── api_config.dart         # baseURL, 헤더 등 공통 설정
│   │   ├── theme/
│   │   │   └── app_theme.dart          # ThemeData 정의
│   │   └── utils/
│   ├── shared/                 # 공유 위젯, 공유 모델
│   │   ├── widgets/
│   │   └── models/
│   ├── features/               # 기능별 모듈 (ia.md 화면 기준)
│   │   └── auth/               # 예시: 인증 기능
│   │       ├── data/           # Repository 구현체, 데이터 모델
│   │       ├── domain/         # Repository 인터페이스, UseCase
│   │       └── presentation/   # Provider, 화면 Widget
│   ├── routing/                # go_router 설정
│   │   └── app_router.dart
│   └── main.dart
├── web/                        # Flutter Web 전용
│   └── runtime-env.js          # 런타임 환경변수 (Web 빌드 전용)
├── pubspec.yaml
├── pubspec.lock
├── analysis_options.yaml
└── .env                        # 환경변수 (flutter_dotenv 사용 시)
```

`features/` 하위 폴더는 `ia.md`의 주요 기능(메뉴) 단위로 생성한다.
예시: `ia.md`에 인증·홈·프로필 화면이 있으면 `features/auth/`, `features/home/`, `features/profile/`을 생성하고 각각 `data/`, `domain/`, `presentation/` 하위 디렉토리를 추가한다.
<!-- ENDIF -->

#### 2.3 설정 파일 생성

<!-- IF PLATFORM == REACT -->
**vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
  },
})
```

**.env.example**

```dotenv
# API 서버 URL (runtime-env.js의 fallback용)
# 주 설정은 public/runtime-env.js에서 관리
# 이 값은 runtime-env.js가 로드되지 않았을 때만 사용됨
VITE_API_URL=http://localhost:4010

# 앱 환경
VITE_APP_ENV=development
```

**.env.local** (로컬 실행용, gitignore에 포함)

```dotenv
VITE_API_URL=http://localhost:4010
VITE_APP_ENV=development
```
<!-- ELIF PLATFORM == VUE -->
**vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
  },
})
```

**.env.example**

```dotenv
# API 서버 URL (runtime-env.js의 fallback용)
# 주 설정은 public/runtime-env.js에서 관리
VITE_API_URL=http://localhost:4010

# 앱 환경
VITE_APP_ENV=development
```

**.env.local** (로컬 실행용, gitignore에 포함)

```dotenv
VITE_API_URL=http://localhost:4010
VITE_APP_ENV=development
```
<!-- ELIF PLATFORM == FLUTTER -->
**analysis_options.yaml**

```yaml
include: package:flutter_lints/flutter.yaml

linter:
  rules:
    - prefer_const_constructors
    - prefer_const_literals_to_create_immutables
    - avoid_print
    - use_key_in_widget_constructors
```

**.env** (flutter_dotenv 사용 시, gitignore에 포함)

```dotenv
API_BASE_URL=http://localhost:8080
APP_ENV=development
```

**.env.example**

```dotenv
API_BASE_URL=http://localhost:8080
APP_ENV=development
```
<!-- ENDIF -->

---

### 3단계. 의존성 설치

<!-- IF PLATFORM == REACT -->
선택한 기술스택에 따라 필요한 패키지를 설치한다. 아래는 React + TypeScript 기준 예시이다.

```bash
cd frontend

# 라우팅
npm install react-router-dom

# 상태 관리 (Zustand + TanStack Query 조합 예시)
npm install zustand @tanstack/react-query

# HTTP 클라이언트
npm install axios

# 개발 의존성
npm install -D @types/node
```

Redux Toolkit을 선택한 경우:

```bash
npm install @reduxjs/toolkit react-redux
```

Tailwind CSS를 선택한 경우:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

설치 후 `npm run dev`를 실행하여 기본 화면이 로딩되는지 확인한다.
<!-- ELIF PLATFORM == VUE -->
선택한 기술스택에 따라 필요한 패키지를 설치한다. 아래는 Vue + TypeScript 기준 예시이다.

```bash
cd frontend

# 라우팅
npm install vue-router@4

# 상태 관리
npm install pinia

# 서버 상태 관리
npm install @tanstack/vue-query

# HTTP 클라이언트
npm install axios

# 개발 의존성
npm install -D @types/node
```

Tailwind CSS를 선택한 경우:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

설치 후 `npm run dev`를 실행하여 기본 화면이 로딩되는지 확인한다.
<!-- ELIF PLATFORM == FLUTTER -->
`pubspec.yaml`에 의존성을 추가하고 `flutter pub get`으로 설치한다.

**pubspec.yaml** (의존성 섹션)

```yaml
name: {PROJECT_NAME}
description: A Flutter project.
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter

  # 라우팅
  go_router: ^13.0.0

  # 상태 관리
  flutter_riverpod: ^2.5.0
  riverpod_annotation: ^2.3.0

  # HTTP 클라이언트
  dio: ^5.4.0

  # 토큰 저장 (localStorage 대체)
  flutter_secure_storage: ^9.0.0

  # 환경변수
  flutter_dotenv: ^5.1.0

  # 직렬화
  freezed_annotation: ^2.4.0
  json_annotation: ^4.8.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

  # 코드 생성
  build_runner: ^2.4.0
  freezed: ^2.4.0
  json_serializable: ^6.7.0
  riverpod_generator: ^2.3.0
```

```bash
cd frontend
flutter pub get
```

설치 후 `flutter analyze`를 실행하여 오류가 없는지 확인한다.
<!-- ENDIF -->

---

### 4단계. 스타일 시스템 구축

<!-- IF PLATFORM == REACT -->
`프로토타입`를 반드시 참조하여 아래 파일을 작성한다.
프로토타입에 정의된 컬러·타이포그래피·간격 값과 반드시 일치해야 한다.

#### 4.1 CSS 변수 정의 (`src/styles/variables.css`)

```css
:root {
  /* 컬러 팔레트 — style-guide.md 기준으로 실제 값 입력 */
  --color-primary: #YOUR_PRIMARY;
  --color-primary-hover: #YOUR_PRIMARY_HOVER;
  --color-secondary: #YOUR_SECONDARY;
  --color-background: #YOUR_BACKGROUND;
  --color-surface: #YOUR_SURFACE;
  --color-text-primary: #YOUR_TEXT_PRIMARY;
  --color-text-secondary: #YOUR_TEXT_SECONDARY;
  --color-border: #YOUR_BORDER;
  --color-error: #YOUR_ERROR;
  --color-success: #YOUR_SUCCESS;
  --color-warning: #YOUR_WARNING;

  /* 타이포그래피 — style-guide.md 기준으로 실제 값 입력 */
  --font-family-base: 'YOUR_FONT', sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-bold: 700;
  --line-height-base: 1.5;

  /* 간격 시스템 */
  --spacing-1: 4px;
  --spacing-2: 8px;
  --spacing-3: 12px;
  --spacing-4: 16px;
  --spacing-6: 24px;
  --spacing-8: 32px;
  --spacing-12: 48px;
  --spacing-16: 64px;

  /* 반응형 브레이크포인트 참조값 (JS에서 사용 시) */
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;

  /* 기타 */
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 16px;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
}
```

> 프로토타입에 정의된 실제 값으로 위 주석 자리를 교체한다. 임의 값 사용 금지.

#### 4.2 CSS 리셋 (`src/styles/reset.css`)

```css
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  -webkit-text-size-adjust: 100%;
}

body {
  font-family: var(--font-family-base);
  font-size: var(--font-size-md);
  color: var(--color-text-primary);
  background-color: var(--color-background);
  line-height: var(--line-height-base);
}

img, svg {
  display: block;
  max-width: 100%;
}

button {
  cursor: pointer;
  border: none;
  background: none;
  font: inherit;
}

a {
  color: inherit;
  text-decoration: none;
}
```

#### 4.3 전역 스타일 진입점 (`src/styles/global.css`)

```css
@import './reset.css';
@import './variables.css';
```

#### 4.4 `main.tsx`에서 전역 스타일 임포트

```typescript
import '@/styles/global.css'
```

Tailwind CSS 선택 시 `variables.css`의 값을 `tailwind.config.js`의 `theme.extend`에 반영하여 디자인 토큰을 통일한다.
<!-- ELIF PLATFORM == VUE -->
`프로토타입`를 반드시 참조하여 아래 파일을 작성한다.

#### 4.1 CSS 변수 정의 (`src/styles/variables.css`)

```css
:root {
  /* 컬러 팔레트 — style-guide.md 기준으로 실제 값 입력 */
  --color-primary: #YOUR_PRIMARY;
  --color-primary-hover: #YOUR_PRIMARY_HOVER;
  --color-secondary: #YOUR_SECONDARY;
  --color-background: #YOUR_BACKGROUND;
  --color-surface: #YOUR_SURFACE;
  --color-text-primary: #YOUR_TEXT_PRIMARY;
  --color-text-secondary: #YOUR_TEXT_SECONDARY;
  --color-border: #YOUR_BORDER;
  --color-error: #YOUR_ERROR;
  --color-success: #YOUR_SUCCESS;
  --color-warning: #YOUR_WARNING;

  /* 타이포그래피 */
  --font-family-base: 'YOUR_FONT', sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-bold: 700;
  --line-height-base: 1.5;

  /* 간격 시스템 */
  --spacing-1: 4px;
  --spacing-2: 8px;
  --spacing-3: 12px;
  --spacing-4: 16px;
  --spacing-6: 24px;
  --spacing-8: 32px;

  /* 기타 */
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 16px;
}
```

#### 4.2 CSS 리셋 (`src/styles/reset.css`)

```css
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-family-base);
  color: var(--color-text-primary);
  background-color: var(--color-background);
  line-height: var(--line-height-base);
}
```

#### 4.3 전역 스타일 진입점 (`src/styles/global.css`)

```css
@import './reset.css';
@import './variables.css';
```

#### 4.4 `main.ts`에서 전역 스타일 임포트

```typescript
import '@/styles/global.css'
```
<!-- ELIF PLATFORM == FLUTTER -->
`프로토타입`를 반드시 참조하여 ThemeData를 작성한다.
프로토타입에 정의된 컬러·타이포그래피 값을 Flutter ThemeData로 변환한다.

#### style-guide.md → Flutter ThemeData 매핑 기준

| style-guide.md 항목 | Flutter ThemeData 항목 |
|---------------------|------------------------|
| primary color | `ColorScheme.primary` |
| secondary color | `ColorScheme.secondary` |
| background color | `ColorScheme.surface` (또는 `scaffoldBackgroundColor`) |
| error color | `ColorScheme.error` |
| text primary | `TextTheme.bodyLarge.color` |
| text secondary | `TextTheme.bodyMedium.color` |
| font family | `TextTheme` 전반의 `fontFamily` |
| border radius | `CardTheme.shape`, `InputDecorationTheme.border` 등 |

#### 4.1 ThemeData 정의 (`lib/core/theme/app_theme.dart`)

```dart
import 'package:flutter/material.dart';

class AppTheme {
  // style-guide.md 기준으로 실제 값 입력 (임의 값 사용 금지)
  static const Color _primary = Color(0xFFYOUR_PRIMARY);
  static const Color _secondary = Color(0xFFYOUR_SECONDARY);
  static const Color _background = Color(0xFFYOUR_BACKGROUND);
  static const Color _surface = Color(0xFFYOUR_SURFACE);
  static const Color _error = Color(0xFFYOUR_ERROR);
  static const Color _textPrimary = Color(0xFFYOUR_TEXT_PRIMARY);
  static const Color _textSecondary = Color(0xFFYOUR_TEXT_SECONDARY);

  static ThemeData get lightTheme => ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.light(
          primary: _primary,
          secondary: _secondary,
          surface: _surface,
          error: _error,
          onPrimary: Colors.white,
          onSecondary: Colors.white,
          onSurface: _textPrimary,
          onError: Colors.white,
        ),
        scaffoldBackgroundColor: _background,
        textTheme: const TextTheme(
          // style-guide.md의 타이포그래피 기준으로 실제 값 입력
          displayLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
          headlineMedium: TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
          titleLarge: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
          bodyLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.normal),
          bodyMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.normal),
          labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        ).apply(
          // style-guide.md의 폰트 패밀리 기준으로 실제 값 입력
          fontFamily: 'YOUR_FONT',
          bodyColor: _textPrimary,
          displayColor: _textPrimary,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: _primary,
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: _primary,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
      );
}
```

#### 4.2 `main.dart`에 테마 적용

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'routing/app_router.dart';

void main() {
  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: '{PROJECT_NAME}',
      theme: AppTheme.lightTheme,
      routerConfig: appRouter,
    );
  }
}
```
<!-- ENDIF -->

---

### 5단계. 라우팅 시스템 구축

`프로토타입`의 메뉴 계층과 화면 목록을 기반으로 라우트를 정의한다.

<!-- IF PLATFORM == REACT -->
#### 5.1 라우터 설정 (`src/router/index.tsx`)

```typescript
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import NotFound from '@/pages/NotFound'

// ia.md 기반으로 라우트 추가
// 예시: ia.md에 대시보드(/), 사용자 목록(/users), 설정(/settings)이 있는 경우
const router = createBrowserRouter([
  {
    path: '/',
    // element: <MainLayout />,  // 레이아웃 컴포넌트 구현 후 연결
    children: [
      {
        index: true,
        // element: <DashboardPage />,  // 페이지 구현 단계에서 연결
        element: <div>Dashboard (placeholder)</div>,
      },
      // ia.md에 정의된 각 화면을 여기에 추가
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
])

export default function AppRouter() {
  return <RouterProvider router={router} />
}
```

#### 5.2 인증이 필요한 라우트 (인증 기능이 있는 경우)

```typescript
// src/router/PrivateRoute.tsx
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store'

interface PrivateRouteProps {
  children: React.ReactNode
}

export default function PrivateRoute({ children }: PrivateRouteProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}
```

#### 5.3 404 페이지 (`src/pages/NotFound.tsx`)

```typescript
export default function NotFound() {
  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h1>404</h1>
      <p>페이지를 찾을 수 없습니다.</p>
    </div>
  )
}
```

#### 5.4 `App.tsx`에 라우터 연결

```typescript
import AppRouter from '@/router'

export default function App() {
  return <AppRouter />
}
```
<!-- ELIF PLATFORM == VUE -->
#### 5.1 라우터 설정 (`src/router/index.ts`)

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// ia.md 기반으로 라우트 추가
const routes = [
  {
    path: '/',
    // component: () => import('@/layouts/MainLayout.vue'),  // 구현 후 연결
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/views/HomePage.vue'),
      },
      // ia.md에 정의된 각 화면을 여기에 추가
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 인증 가드 (인증 기능이 있는 경우)
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

#### 5.2 `main.ts`에 라우터 연결

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from '@/router'
import App from './App.vue'
import '@/styles/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```
<!-- ELIF PLATFORM == FLUTTER -->
#### 5.1 go_router 설정 (`lib/routing/app_router.dart`)

`ia.md`의 메뉴 계층과 화면 목록을 GoRoute로 매핑한다.

```dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// ia.md 기반으로 화면 경로 상수 정의
class AppRoutes {
  static const splash = '/';
  static const login = '/login';
  static const home = '/home';
  // ia.md에 정의된 각 화면 경로를 여기에 추가
}

// 인증 상태 Provider (6단계에서 구현)
// final authStateProvider = ...

final GoRouter appRouter = GoRouter(
  initialLocation: AppRoutes.splash,
  // redirect: 인증 가드 (인증 기능이 있는 경우)
  redirect: (BuildContext context, GoRouterState state) {
    // 예시 인증 가드 패턴 (authStateProvider 구현 후 연결)
    // final isAuthenticated = ref.read(authStateProvider).isAuthenticated;
    // final isGoingToLogin = state.matchedLocation == AppRoutes.login;
    // if (!isAuthenticated && !isGoingToLogin) return AppRoutes.login;
    // if (isAuthenticated && isGoingToLogin) return AppRoutes.home;
    return null;
  },
  routes: [
    GoRoute(
      path: AppRoutes.splash,
      builder: (context, state) => const Scaffold(
        body: Center(child: Text('Loading...')),  // 스플래시 화면 구현 후 교체
      ),
    ),
    GoRoute(
      path: AppRoutes.login,
      builder: (context, state) => const Scaffold(
        body: Center(child: Text('Login (placeholder)')),
      ),
    ),
    GoRoute(
      path: AppRoutes.home,
      builder: (context, state) => const Scaffold(
        body: Center(child: Text('Home (placeholder)')),
      ),
    ),
    // ia.md에 정의된 각 화면을 여기에 추가
  ],
  errorBuilder: (context, state) => Scaffold(
    body: Center(child: Text('페이지를 찾을 수 없습니다: ${state.error}')),
  ),
);
```

#### 5.2 Riverpod과 go_router 연동 (인증 가드 완성 패턴)

```dart
// lib/routing/app_router.dart (Riverpod 연동 시)
import 'package:flutter_riverpod/flutter_riverpod.dart';

// RouterProvider를 Riverpod으로 관리
final routerProvider = Provider<GoRouter>((ref) {
  // authStateProvider 구현 후 ref.watch로 연동
  // final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: AppRoutes.splash,
    redirect: (context, state) {
      // final isAuthenticated = authState.isAuthenticated;
      // final isGoingToLogin = state.matchedLocation == AppRoutes.login;
      // if (!isAuthenticated && !isGoingToLogin) return AppRoutes.login;
      // if (isAuthenticated && isGoingToLogin) return AppRoutes.home;
      return null;
    },
    routes: [/* 위와 동일 */],
  );
});
```
<!-- ENDIF -->

---

### 6단계. 상태 관리 시스템 구축

<!-- IF PLATFORM == REACT -->
기술스택 결정 시 선택한 라이브러리에 따라 아래 중 하나를 적용한다.

#### 6.1 Zustand 적용 예시

```typescript
// src/store/authStore.ts
import { create } from 'zustand'

interface AuthState {
  isAuthenticated: boolean
  token: string | null
  setToken: (token: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  token: null,
  setToken: (token) => set({ isAuthenticated: true, token }),
  clearAuth: () => set({ isAuthenticated: false, token: null }),
}))
```

```typescript
// src/store/uiStore.ts
import { create } from 'zustand'

interface UiState {
  isLoading: boolean
  setLoading: (loading: boolean) => void
}

export const useUiStore = create<UiState>((set) => ({
  isLoading: false,
  setLoading: (isLoading) => set({ isLoading }),
}))
```

```typescript
// src/store/index.ts
export { useAuthStore } from './authStore'
export { useUiStore } from './uiStore'
```

#### 6.2 Redux Toolkit 적용 예시

```typescript
// src/store/authSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface AuthState {
  isAuthenticated: boolean
  token: string | null
}

const initialState: AuthState = {
  isAuthenticated: false,
  token: null,
}

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setToken: (state, action: PayloadAction<string>) => {
      state.isAuthenticated = true
      state.token = action.payload
    },
    clearAuth: (state) => {
      state.isAuthenticated = false
      state.token = null
    },
  },
})

export const { setToken, clearAuth } = authSlice.actions
export default authSlice.reducer
```

```typescript
// src/store/index.ts
import { configureStore } from '@reduxjs/toolkit'
import authReducer from './authSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
```

```typescript
// src/main.tsx (Redux 사용 시 Provider 추가)
import { Provider } from 'react-redux'
import { store } from '@/store'
```

#### 6.3 TanStack Query 설정 (서버 상태 관리)

```typescript
// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,  // 5분
      retry: 1,
    },
  },
})

// App을 QueryClientProvider로 감싸기
```
<!-- ELIF PLATFORM == VUE -->
#### 6.1 Pinia 스토어 적용 예시

```typescript
// src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const isAuthenticated = computed(() => token.value !== null)

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function clearAuth() {
    token.value = null
    localStorage.removeItem('token')
  }

  // 앱 시작 시 토큰 복원
  function initialize() {
    const saved = localStorage.getItem('token')
    if (saved) token.value = saved
  }

  return { token, isAuthenticated, setToken, clearAuth, initialize }
})
```

```typescript
// src/stores/ui.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const isLoading = ref(false)

  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  return { isLoading, setLoading }
})
```

#### 6.2 TanStack Query 설정 (서버 상태 관리)

```typescript
// src/main.ts
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

app.use(VueQueryPlugin, { queryClient })
```
<!-- ELIF PLATFORM == FLUTTER -->
Riverpod을 사용하여 상태 관리를 구성한다. 인증 상태와 UI 로딩 상태를 기본 Provider로 구현한다.

#### 6.1 인증 상태 Provider (`lib/features/auth/presentation/auth_provider.dart`)

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

// 인증 상태 모델
class AuthState {
  final bool isAuthenticated;
  final String? token;

  const AuthState({
    this.isAuthenticated = false,
    this.token,
  });

  AuthState copyWith({bool? isAuthenticated, String? token}) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      token: token ?? this.token,
    );
  }
}

// 인증 상태 Notifier
class AuthNotifier extends AsyncNotifier<AuthState> {
  final _storage = const FlutterSecureStorage();

  @override
  Future<AuthState> build() async {
    // 앱 시작 시 저장된 토큰 복원
    final token = await _storage.read(key: 'auth_token');
    if (token != null) {
      return AuthState(isAuthenticated: true, token: token);
    }
    return const AuthState();
  }

  Future<void> setToken(String token) async {
    await _storage.write(key: 'auth_token', value: token);
    state = AsyncData(
      state.value?.copyWith(isAuthenticated: true, token: token) ??
          AuthState(isAuthenticated: true, token: token),
    );
  }

  Future<void> clearAuth() async {
    await _storage.delete(key: 'auth_token');
    state = const AsyncData(AuthState());
  }
}

// Provider 정의
final authProvider = AsyncNotifierProvider<AuthNotifier, AuthState>(
  AuthNotifier.new,
);
```

#### 6.2 UI 상태 Provider (`lib/shared/providers/ui_provider.dart`)

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

final isLoadingProvider = StateProvider<bool>((ref) => false);
```

#### 6.3 `main.dart`에 ProviderScope 적용 (4단계에서 이미 포함)

```dart
// ProviderScope는 main.dart에서 이미 runApp을 감싸고 있음 (4단계 참조)
// 각 위젯에서는 ConsumerWidget / ConsumerStatefulWidget을 사용:

class ExampleWidget extends ConsumerWidget {
  const ExampleWidget({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    return authState.when(
      data: (state) => Text(state.isAuthenticated ? '로그인됨' : '비로그인'),
      loading: () => const CircularProgressIndicator(),
      error: (e, _) => Text('오류: $e'),
    );
  }
}
```
<!-- ENDIF -->

---

### 7단계. API 클라이언트 기본 설정

<!-- IF PLATFORM == REACT -->
`API 설계서(docs/design/api/*.yaml)`를 참조하여 서비스 레이어를 구성한다.
런타임 환경변수(`runtime-env.js`)를 통해 서비스별 API 호스트를 관리한다.

#### 7.1 런타임 환경변수 설정

**`public/runtime-env.js` 파일 생성** (기본값 — Mock 서버)

```javascript
// public/runtime-env.js
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  // 서비스별 HOST는 high-level-architecture.md의 서비스 목록에서 생성
  // Mock 단계에서는 단일 Prism 서버: 모두 http://localhost:4010
  MEMBER_HOST: "http://localhost:4010",
  ORDER_HOST: "http://localhost:4010",
  // ... 프로젝트의 서비스 목록에 맞게 추가
};
```

**`index.html`에 script 태그 추가** (앱 번들보다 먼저 로드)

```html
<!-- index.html의 <head> 내부, 앱 스크립트보다 앞에 배치 -->
<script src="/runtime-env.js"></script>
```

**`src/config/runtime.ts` 헬퍼 생성**

```typescript
// src/config/runtime.ts
interface RuntimeConfig {
  API_GROUP: string;
  [key: string]: string;  // 서비스별 HOST 동적 키
}

export function getRuntimeConfig(): RuntimeConfig {
  return (window as any).__runtime_config__ ?? {
    API_GROUP: '/api/v1',
  };
}

export function getServiceHost(serviceName: string): string {
  const config = getRuntimeConfig();
  const key = `${serviceName.toUpperCase()}_HOST`;
  return config[key] ?? '';
}
```

> `runtime-env.js`는 빌드 결과물에 포함되지 않는 정적 파일이므로, 배포 환경에서 볼륨 마운트 또는 ConfigMap으로 교체할 수 있다.
> 빌드 타임 환경변수(`VITE_API_URL`)는 개발 편의를 위한 fallback으로만 유지한다.

#### 7.2 API 공통 설정 (`src/services/api/config.ts`)

```typescript
import { getRuntimeConfig } from '@/config/runtime'

// runtime-env.js에서 읽은 값 기반. VITE_API_URL은 fallback으로만 유지
const config = getRuntimeConfig()

export const API_CONFIG = {
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
  },
}

/** 서비스별 API 기본 URL 생성 */
export function getServiceBaseUrl(serviceName: string): string {
  const host = config[`${serviceName.toUpperCase()}_HOST`]
    ?? import.meta.env.VITE_API_URL
    ?? 'http://localhost:4010'
  return `${host}${config.API_GROUP}`
}
```

#### 7.3 Axios 클라이언트 (`src/services/api/client.ts`)

```typescript
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { API_CONFIG } from './config'

function createApiClient(config?: AxiosRequestConfig): AxiosInstance {
  const client = axios.create({
    ...API_CONFIG,
    ...config,
  })

  // 요청 인터셉터
  client.interceptors.request.use(
    (cfg) => {
      const token = localStorage.getItem('token')
      if (token) {
        cfg.headers.Authorization = `Bearer ${token}`
      }
      return cfg
    },
    (error) => Promise.reject(error),
  )

  // 응답 인터셉터
  client.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    },
  )

  return client
}

export const apiClient = createApiClient()
```

#### 7.4 API 타입 기본 정의 (`src/types/api.ts`)

```typescript
/** 공통 API 응답 래퍼 — api-mapping.md 기준으로 실제 응답 구조에 맞게 조정 */
export interface ApiResponse<T> {
  data: T
  message?: string
  status: number
}

/** 페이지네이션 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

/** 공통 에러 응답 */
export interface ApiError {
  code: string
  message: string
  details?: unknown
}
```

#### 7.5 서비스 레이어 골격 예시 (`src/services/api/exampleService.ts`)

api-mapping.md에 정의된 각 도메인별로 이 구조를 복제하여 생성한다.

```typescript
import { apiClient } from './client'
import type { ApiResponse } from '@/types/api'

// 타입 정의 — api-mapping.md 및 OpenAPI 명세 기반
export interface ExampleItem {
  id: string
  name: string
}

// 서비스 함수 — 이 단계에서는 골격만 작성
export const exampleService = {
  getList: () =>
    apiClient.get<ApiResponse<ExampleItem[]>>('/examples'),

  getById: (id: string) =>
    apiClient.get<ApiResponse<ExampleItem>>(`/examples/${id}`),
}
```
<!-- ELIF PLATFORM == VUE -->
`API 설계서(docs/design/api/*.yaml)`를 참조하여 서비스 레이어를 구성한다.
런타임 환경변수(`runtime-env.js`)를 통해 서비스별 API 호스트를 관리한다.

#### 7.1 런타임 환경변수 설정

React와 동일한 구조로 `public/runtime-env.js` + 헬퍼를 생성한다.

**`public/runtime-env.js` 파일 생성** (기본값 — Mock 서버)

```javascript
// public/runtime-env.js
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:4010",
  ORDER_HOST: "http://localhost:4010",
  // ... 프로젝트의 서비스 목록에 맞게 추가
};
```

**`index.html`에 script 태그 추가**

```html
<script src="/runtime-env.js"></script>
```

**`src/config/runtime.ts` 헬퍼 생성**

```typescript
// src/config/runtime.ts
interface RuntimeConfig {
  API_GROUP: string;
  [key: string]: string;
}

export function getRuntimeConfig(): RuntimeConfig {
  return (window as any).__runtime_config__ ?? {
    API_GROUP: '/api/v1',
  };
}

export function getServiceHost(serviceName: string): string {
  const config = getRuntimeConfig();
  const key = `${serviceName.toUpperCase()}_HOST`;
  return config[key] ?? '';
}
```

#### 7.2 API 공통 설정 (`src/services/api/config.ts`)

```typescript
import { getRuntimeConfig } from '@/config/runtime'

const config = getRuntimeConfig()

export const API_CONFIG = {
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
  },
}

export function getServiceBaseUrl(serviceName: string): string {
  const host = config[`${serviceName.toUpperCase()}_HOST`]
    ?? import.meta.env.VITE_API_URL
    ?? 'http://localhost:4010'
  return `${host}${config.API_GROUP}`
}
```

#### 7.3 Axios 클라이언트 (`src/services/api/client.ts`)

```typescript
import axios, { AxiosInstance } from 'axios'
import { API_CONFIG } from './config'

function createApiClient(): AxiosInstance {
  const client = axios.create(API_CONFIG)

  client.interceptors.request.use((cfg) => {
    const token = localStorage.getItem('token')
    if (token) cfg.headers.Authorization = `Bearer ${token}`
    return cfg
  })

  client.interceptors.response.use(
    (res) => res,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    },
  )

  return client
}

export const apiClient = createApiClient()
```

#### 7.4 API 타입 기본 정의 (`src/types/api.ts`)

```typescript
export interface ApiResponse<T> {
  data: T
  message?: string
  status: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface ApiError {
  code: string
  message: string
  details?: unknown
}
```

#### 7.5 서비스 레이어 골격 예시 (`src/services/api/exampleService.ts`)

```typescript
import { apiClient } from './client'
import type { ApiResponse } from '@/types/api'

export interface ExampleItem {
  id: string
  name: string
}

export const exampleService = {
  getList: () => apiClient.get<ApiResponse<ExampleItem[]>>('/examples'),
  getById: (id: string) => apiClient.get<ApiResponse<ExampleItem>>(`/examples/${id}`),
}
```
<!-- ELIF PLATFORM == FLUTTER -->
`API 설계서(docs/design/api/*.yaml)`를 참조하여 Dio 클라이언트와 서비스 레이어를 구성한다.
Flutter에서는 `localStorage`를 사용할 수 없으므로 `flutter_secure_storage`로 토큰을 관리한다.

#### 7.1 런타임 환경변수 설정 (Flutter Web 전용)

Flutter Web 빌드인 경우 `web/runtime-env.js` + Dart JS interop 헬퍼를 사용한다.
Flutter Mobile(네이티브) 빌드는 `runtime-env.js`를 사용할 수 없으므로 기존 `--dart-define` 방식을 유지한다.

**`web/runtime-env.js` 파일 생성** (Flutter Web 전용, 기본값 — Mock 서버)

```javascript
// web/runtime-env.js
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:4010",
  ORDER_HOST: "http://localhost:4010",
  // ... 프로젝트의 서비스 목록에 맞게 추가
};
```

**`web/index.html`에 script 태그 추가**

```html
<!-- web/index.html의 <head> 내부, Flutter 부트스트랩보다 앞에 배치 -->
<script src="runtime-env.js"></script>
```

**Dart JS interop 헬퍼** (`lib/core/config/runtime_config.dart`)

```dart
import 'dart:js_interop';

@JS('__runtime_config__')
external JSObject? get _runtimeConfig;

/// Flutter Web: window.__runtime_config__에서 값 읽기
/// Flutter Mobile: --dart-define fallback
class RuntimeConfig {
  static String get apiGroup =>
      _getProperty('API_GROUP') ??
      const String.fromEnvironment('API_GROUP', defaultValue: '/api/v1');

  static String getServiceHost(String serviceName) {
    final key = '${serviceName.toUpperCase()}_HOST';
    return _getProperty(key) ??
        const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:4010');
  }

  static String? _getProperty(String key) {
    final config = _runtimeConfig;
    if (config == null) return null;
    final value = config.getProperty(key.toJS);
    return value?.isA<JSString>() == true ? (value as JSString).toDart : null;
  }
}
```

> **플랫폼 분기**: Flutter Web 빌드는 `runtime-env.js`에서 값을 읽고, Flutter Mobile 빌드는 `--dart-define`으로 주입된 값을 사용한다. `RuntimeConfig` 헬퍼가 이 분기를 자동 처리한다.

#### 7.2 API 공통 설정 (`lib/core/network/api_config.dart`)

```dart
import 'runtime_config.dart';

class ApiConfig {
  /// 서비스별 API 기본 URL 생성
  /// Flutter Web: runtime-env.js에서 읽음
  /// Flutter Mobile: --dart-define에서 읽음
  static String getServiceBaseUrl(String serviceName) {
    return '${RuntimeConfig.getServiceHost(serviceName)}${RuntimeConfig.apiGroup}';
  }

  static const Duration timeout = Duration(seconds: 10);
  static const Map<String, String> defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
}
```

#### 7.4 Dio 클라이언트 (`lib/core/network/dio_client.dart`)

```dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'api_config.dart';

class DioClient {
  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

  DioClient() {
    _dio = Dio(
      BaseOptions(
        connectTimeout: ApiConfig.timeout,
        receiveTimeout: ApiConfig.timeout,
        headers: ApiConfig.defaultHeaders,
      ),
    );
    _setupInterceptors();
  }

  void _setupInterceptors() {
    // 요청 인터셉터: 토큰 자동 첨부
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: 'auth_token');
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          // 401 처리: 토큰 삭제 후 로그인 화면으로 이동
          if (error.response?.statusCode == 401) {
            await _storage.delete(key: 'auth_token');
            // 라우터 접근이 필요하면 navigatorKey 또는 Riverpod ref 활용
          }
          handler.next(error);
        },
      ),
    );
  }

  Dio get dio => _dio;
}

// Singleton 인스턴스
final dioClient = DioClient();
```

#### 7.4 API 타입 기본 정의 (`lib/core/network/api_response.dart`)

```dart
/// 공통 API 응답 래퍼 — api-mapping.md 기준으로 실제 응답 구조에 맞게 조정
class ApiResponse<T> {
  final T data;
  final String? message;
  final int status;

  const ApiResponse({
    required this.data,
    this.message,
    required this.status,
  });

  factory ApiResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic) fromJsonT,
  ) {
    return ApiResponse(
      data: fromJsonT(json['data']),
      message: json['message'] as String?,
      status: json['status'] as int,
    );
  }
}

/// 공통 에러 응답
class ApiError {
  final String code;
  final String message;
  final dynamic details;

  const ApiError({
    required this.code,
    required this.message,
    this.details,
  });

  factory ApiError.fromJson(Map<String, dynamic> json) {
    return ApiError(
      code: json['code'] as String,
      message: json['message'] as String,
      details: json['details'],
    );
  }
}
```

#### 7.5 서비스 레이어 골격 예시 (`lib/features/example/data/example_service.dart`)

api-mapping.md에 정의된 각 도메인별로 이 구조를 복제하여 생성한다.

```dart
import 'package:dio/dio.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/network/api_response.dart';

// 타입 정의 — api-mapping.md 및 OpenAPI 명세 기반
class ExampleItem {
  final String id;
  final String name;

  const ExampleItem({required this.id, required this.name});

  factory ExampleItem.fromJson(Map<String, dynamic> json) {
    return ExampleItem(
      id: json['id'] as String,
      name: json['name'] as String,
    );
  }
}

// 서비스 클래스 — 이 단계에서는 골격만 작성
class ExampleService {
  final Dio _dio = dioClient.dio;

  Future<List<ExampleItem>> getList() async {
    final response = await _dio.get('/examples');
    final apiResponse = ApiResponse.fromJson(
      response.data as Map<String, dynamic>,
      (data) => (data as List)
          .map((e) => ExampleItem.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
    return apiResponse.data;
  }

  Future<ExampleItem> getById(String id) async {
    final response = await _dio.get('/examples/$id');
    final apiResponse = ApiResponse.fromJson(
      response.data as Map<String, dynamic>,
      (data) => ExampleItem.fromJson(data as Map<String, dynamic>),
    );
    return apiResponse.data;
  }
}
```
<!-- ENDIF -->

---

### 8단계. 실행 확인

<!-- IF PLATFORM == REACT -->
#### 8.1 개발 서버 실행

```bash
cd frontend
npm run dev
```

브라우저에서 `http://localhost:3000`에 접속하여 기본 화면이 로딩되는지 확인한다.

#### 8.2 빌드 확인

```bash
npm run build
```

빌드 오류가 없는지 확인한다.

#### 8.3 Prism Mock 서버 연동 확인 (선택)

`backing-service-setup.md` 산출물의 docker-compose mock 프로파일이 실행 중인 경우:

```bash
# mock 프로파일 실행 (backing-service-setup.md 참조)
docker compose --profile mock up -d

# 브라우저 개발자도구 Network 탭에서 API 요청이
# http://localhost:4010 으로 향하는지 확인
```

환경변수 `.env.local`의 `VITE_API_URL=http://localhost:4010` 설정이 적용되어 있으면 자동으로 Prism Mock 서버로 요청이 전달된다.
<!-- ELIF PLATFORM == VUE -->
#### 8.1 개발 서버 실행

```bash
cd frontend
npm run dev
```

브라우저에서 `http://localhost:3000`에 접속하여 기본 화면이 로딩되는지 확인한다.

#### 8.2 빌드 확인

```bash
npm run build
```

빌드 오류가 없는지 확인한다.

#### 8.3 Prism Mock 서버 연동 확인 (선택)

```bash
docker compose --profile mock up -d
# Network 탭에서 API 요청이 http://localhost:4010 으로 향하는지 확인
```
<!-- ELIF PLATFORM == FLUTTER -->
#### 8.1 정적 분석

```bash
cd frontend
flutter analyze
```

분석 오류가 없는지 확인한다. 경고도 최소화하도록 수정한다.

#### 8.2 개발 실행

```bash
# 연결된 디바이스/에뮬레이터 목록 확인
flutter devices

# 특정 디바이스로 실행 (디바이스 ID는 위 명령으로 확인)
flutter run -d {DEVICE_ID}

# 에뮬레이터 자동 선택
flutter run
```

앱이 정상 실행되고 기본 화면(플레이스홀더)이 표시되는지 확인한다.

#### 8.3 빌드 확인

```bash
# Android APK 빌드
flutter build apk --debug

# iOS 빌드 (macOS에서만)
flutter build ios --no-codesign

# 웹 빌드 (웹 지원 시)
flutter build web
```

빌드 오류가 없는지 확인한다.

#### 8.4 테스트 실행

```bash
flutter test
```
<!-- ENDIF -->

---

## 출력 형식

<!-- IF PLATFORM == REACT -->
| 항목 | 경로 | 비고 |
|------|------|------|
| 전역 스타일 | `frontend/src/styles/` | style-guide.md 기반 CSS 변수 포함 |
| 라우터 | `frontend/src/router/index.tsx` | ia.md 기반 라우트 정의 |
| 상태 관리 스토어 | `frontend/src/store/` | auth, ui 슬라이스/스토어 포함 |
| API 클라이언트 | `frontend/src/services/api/client.ts` | baseURL 환경변수 관리 |
| 런타임 환경변수 | `frontend/public/runtime-env.js` | 서비스별 HOST 설정 |
| 런타임 설정 헬퍼 | `frontend/src/config/runtime.ts` | window.__runtime_config__ 읽기 |
| API 설정 | `frontend/src/services/api/config.ts` | runtime-env.js 기반 |
| 공통 타입 | `frontend/src/types/api.ts` | 응답 래퍼, 에러 타입 |
| 환경변수 예시 | `frontend/.env.example` | VITE_API_URL 포함 |
<!-- ELIF PLATFORM == VUE -->
| 항목 | 경로 | 비고 |
|------|------|------|
| 전역 스타일 | `frontend/src/styles/` | style-guide.md 기반 CSS 변수 포함 |
| 라우터 | `frontend/src/router/index.ts` | ia.md 기반 라우트 정의 |
| 상태 관리 스토어 | `frontend/src/stores/` | auth, ui Pinia 스토어 포함 |
| API 클라이언트 | `frontend/src/services/api/client.ts` | baseURL 환경변수 관리 |
| 런타임 환경변수 | `frontend/public/runtime-env.js` | 서비스별 HOST 설정 |
| 런타임 설정 헬퍼 | `frontend/src/config/runtime.ts` | window.__runtime_config__ 읽기 |
| API 설정 | `frontend/src/services/api/config.ts` | runtime-env.js 기반 |
| 공통 타입 | `frontend/src/types/api.ts` | 응답 래퍼, 에러 타입 |
| 환경변수 예시 | `frontend/.env.example` | VITE_API_URL 포함 |
<!-- ELIF PLATFORM == FLUTTER -->
| 항목 | 경로 | 비고 |
|------|------|------|
| 테마 시스템 | `frontend/lib/core/theme/app_theme.dart` | style-guide.md 기반 ThemeData |
| 라우터 | `frontend/lib/routing/app_router.dart` | ia.md 기반 GoRoute 정의 |
| 인증 Provider | `frontend/lib/features/auth/presentation/auth_provider.dart` | Riverpod AsyncNotifier |
| Dio 클라이언트 | `frontend/lib/core/network/dio_client.dart` | flutter_secure_storage 토큰 관리 |
| 런타임 환경변수 | `frontend/web/runtime-env.js` | 서비스별 HOST 설정 (Web 전용) |
| 런타임 설정 헬퍼 | `frontend/lib/core/config/runtime_config.dart` | JS interop / dart-define 분기 |
| API 설정 | `frontend/lib/core/network/api_config.dart` | runtime-env.js 기반 |
| 공통 타입 | `frontend/lib/core/network/api_response.dart` | 응답 래퍼, 에러 타입 |
| 의존성 명세 | `frontend/pubspec.yaml` | Riverpod, go_router, Dio 등 포함 |
<!-- ENDIF -->

## 품질 기준

<!-- IF PLATFORM == REACT -->
- [ ] 정보아키텍처(`ia.md`) 기반 폴더 구조와 라우트 정의
- [ ] CSS 변수가 `style-guide.md`의 컬러·타이포그래피·간격 값과 일치
- [ ] API 서비스별 HOST가 `public/runtime-env.js`로 관리됨 (`VITE_API_URL`은 fallback)
- [ ] `.env.example`에 `VITE_API_URL=http://localhost:4010` 포함
- [ ] `npm run dev` 성공 및 브라우저 로딩 확인
- [ ] `npm run build` 성공 (타입 오류·빌드 오류 없음)
- [ ] 페이지 컴포넌트 미구현 (placeholder만 존재)
<!-- ELIF PLATFORM == VUE -->
- [ ] 정보아키텍처(`ia.md`) 기반 폴더 구조와 라우트 정의
- [ ] CSS 변수가 `style-guide.md`의 컬러·타이포그래피·간격 값과 일치
- [ ] API 서비스별 HOST가 `public/runtime-env.js`로 관리됨 (`VITE_API_URL`은 fallback)
- [ ] `.env.example`에 `VITE_API_URL=http://localhost:4010` 포함
- [ ] `npm run dev` 성공 및 브라우저 로딩 확인
- [ ] `npm run build` 성공 (타입 오류·빌드 오류 없음)
- [ ] 페이지 컴포넌트 미구현 (placeholder만 존재)
<!-- ELIF PLATFORM == FLUTTER -->
- [ ] 정보아키텍처(`ia.md`) 기반 feature 폴더 구조와 GoRoute 정의
- [ ] `ThemeData`가 `style-guide.md`의 컬러·타이포그래피 값과 일치
- [ ] Dio baseURL이 `web/runtime-env.js`(Web) 또는 `--dart-define`(Mobile)으로 관리됨 (하드코딩 없음)
- [ ] `flutter_secure_storage`로 토큰 저장 (localStorage 미사용)
- [ ] `flutter analyze` 오류 없음
- [ ] `flutter run` 성공 및 기본 화면 표시 확인
- [ ] `flutter build apk --debug` 성공 (빌드 오류 없음)
- [ ] 화면 Widget 미구현 (placeholder Text만 존재)
<!-- ENDIF -->

## 주의사항

<!-- IF PLATFORM == REACT -->
- **이 단계에서 페이지를 구현하지 않는다.** 기반 시스템(스타일·라우팅·상태관리·API 클라이언트) 골격만 완성한다.
- Prism Mock 서버는 docker-compose의 mock 프로파일로 제공된다. 이 가이드에서 직접 설치하지 않고 `backing-service-setup.md`의 산출물을 사용한다.
- API 서비스 레이어는 `src/services/api/` 안에 도메인별로 분리하여 Mock → 실제 서버 전환 시 서비스 파일만 교체하거나 환경변수만 변경해도 동작하도록 설계한다.
- CSS 변수 값을 임의로 추정하지 않는다. 반드시 `style-guide.md`에서 확인한 값을 사용한다.
- 프로토타입 화면 분석이 필요한 경우 playwright MCP 도구를 활용하여 모바일 사이즈(예: 390×844)로 확인한다.
- 기존 `frontend/` 디렉토리가 있는 경우 기존 파일을 삭제하거나 덮어쓰지 않는다. 충돌 여부를 먼저 확인한다.
- 환경변수 파일(`.env.local`, `.env`)은 gitignore에 포함시키고, `.env.example`만 커밋한다.
<!-- ELIF PLATFORM == VUE -->
- **이 단계에서 페이지를 구현하지 않는다.** 기반 시스템(스타일·라우팅·상태관리·API 클라이언트) 골격만 완성한다.
- Prism Mock 서버는 docker-compose의 mock 프로파일로 제공된다. `backing-service-setup.md`의 산출물을 사용한다.
- CSS 변수 값을 임의로 추정하지 않는다. 반드시 `style-guide.md`에서 확인한 값을 사용한다.
- 기존 `frontend/` 디렉토리가 있는 경우 기존 파일을 삭제하거나 덮어쓰지 않는다.
- 환경변수 파일(`.env.local`, `.env`)은 gitignore에 포함시키고, `.env.example`만 커밋한다.
<!-- ELIF PLATFORM == FLUTTER -->
- **이 단계에서 화면 Widget을 구현하지 않는다.** 기반 시스템(테마·라우팅·상태관리·API 클라이언트) 골격만 완성한다.
- Flutter에서는 `localStorage`를 사용할 수 없다. 토큰 등 민감한 데이터는 반드시 `flutter_secure_storage`를 사용한다.
- `ThemeData` 값을 임의로 추정하지 않는다. 반드시 `style-guide.md`에서 확인한 값을 사용한다.
- `pubspec.yaml`의 의존성 버전은 최신 호환 버전을 확인 후 입력한다. `flutter pub outdated`로 최신 버전 확인 가능.
- `build_runner`를 사용하는 경우 코드 생성 명령을 실행한다: `dart run build_runner build --delete-conflicting-outputs`
- 기존 `frontend/` 디렉토리가 있는 경우 기존 파일을 삭제하거나 덮어쓰지 않는다. 충돌 여부를 먼저 확인한다.
- `.env` 파일은 gitignore에 포함시키고, `.env.example`만 커밋한다.
- 프로토타입 화면 분석이 필요한 경우 playwright MCP 도구를 활용하여 모바일 사이즈(예: 390×844)로 확인한다.
<!-- ENDIF -->
