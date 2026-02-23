# 프론트엔드 프로젝트 초기화 가이드

## 목적

UI/UX 설계서와 정보아키텍처를 기반으로 프론트엔드 프로젝트를 초기화하고 기반 시스템을 구축한다.
페이지 구현 이전 단계로, 스타일 시스템·라우팅·상태 관리·API 클라이언트 골격을 완성하여 이후 개발이 일관된 기반 위에서 시작되도록 한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| UI/UX 설계서 | `docs/design/frontend/uiux-design.md` | 화면 구조 파악 |
| 스타일가이드 | `docs/design/frontend/style-guide.md` | CSS 변수·테마 기준 |
| 정보아키텍처 | `docs/design/frontend/ia.md` | 폴더 구조·라우트 기준 |
| API 매핑설계서 | `docs/design/frontend/api-mapping.md` | API 클라이언트 서비스 레이어 설계 기준 |
| 고수준 아키텍처 | `docs/design/high-level-architecture.md` | 기술스택 확인 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 프로젝트 골격 | `frontend/` |
| CSS 변수·테마 | `frontend/src/styles/` |
| 라우팅 설정 | `frontend/src/router/` |
| 상태 관리 스토어 | `frontend/src/store/` |
| API 클라이언트 | `frontend/src/services/api/` |
| 환경변수 예시 | `frontend/.env.example` |

## 방법론

### 작업 순서 개요

1. 기술스택 결정
2. 프로젝트 생성 및 폴더 구조 설정
3. 의존성 설치
4. 스타일 시스템 구축
5. 라우팅 시스템 구축
6. 상태 관리 시스템 구축
7. API 클라이언트 기본 설정
8. 실행 확인

---

### 1단계. 기술스택 결정

`docs/design/high-level-architecture.md`에서 프론트엔드 기술스택을 먼저 확인한다.
사용자가 별도로 지정한 스택이 있으면 그것을 우선한다. 명시가 없으면 아래 기준으로 결정한다.

| 항목 | 기준 후보 | 비고 |
|------|----------|------|
| 프레임워크 | React / Vue / Svelte | high-level-architecture.md 우선 |
| 빌드 도구 | Vite | 기본 권장 |
| 언어 | TypeScript | 기본 권장 |
| 라우팅 | react-router-dom v6 / vue-router v4 | 프레임워크에 따라 선택 |
| 클라이언트 상태 관리 | Zustand / Redux Toolkit / Pinia | 규모에 따라 선택 |
| 서버 상태 관리 | TanStack Query (React Query) / SWR | 기본 권장 |
| HTTP 클라이언트 | axios | 기본 권장 |
| 스타일링 | CSS Modules / Tailwind CSS / styled-components | style-guide.md 확인 후 결정 |
| 개발 서버 포트 | 3000 | 고정 |

기술스택이 결정되면 사용자에게 확인을 받고 다음 단계로 진행한다.

---

### 2단계. 프로젝트 생성 및 폴더 구조 설정

#### 2.1 프로젝트 생성

기존 `frontend/` 디렉토리가 있으면 그대로 유지하면서 작업한다.
없으면 선택한 빌드 도구로 생성한다.

```bash
# Vite + React + TypeScript 예시
npm create vite@latest frontend -- --template react-ts

# Vite + Vue + TypeScript 예시
npm create vite@latest frontend -- --template vue-ts
```

#### 2.2 폴더 구조 생성

`docs/design/frontend/ia.md`의 메뉴 및 화면 계층을 기반으로 폴더를 구성한다.
아래는 React 기준 참조 구조이며, 정보아키텍처에 맞게 조정한다.

```
frontend/
├── public/
│   └── runtime-env.js          # 런타임 환경변수 (선택)
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

#### 2.3 설정 파일 생성

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
# API 서버 URL
# 개발 중 Prism Mock 서버 사용 시: http://localhost:4010
# 실제 백엔드 서버 사용 시: http://localhost:8080 (또는 해당 URL)
VITE_API_URL=http://localhost:4010

# 앱 환경
VITE_APP_ENV=development
```

**.env.local** (로컬 실행용, gitignore에 포함)

```dotenv
VITE_API_URL=http://localhost:4010
VITE_APP_ENV=development
```

---

### 3단계. 의존성 설치

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

---

### 4단계. 스타일 시스템 구축

`docs/design/frontend/style-guide.md`를 반드시 참조하여 아래 파일을 작성한다.
style-guide.md에 정의된 컬러·타이포그래피·간격 값과 반드시 일치해야 한다.

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

> style-guide.md에 정의된 실제 값으로 위 주석 자리를 교체한다. 임의 값 사용 금지.

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

---

### 5단계. 라우팅 시스템 구축

`docs/design/frontend/ia.md`의 메뉴 계층과 화면 목록을 기반으로 라우트를 정의한다.

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

---

### 6단계. 상태 관리 시스템 구축

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

---

### 7단계. API 클라이언트 기본 설정

`docs/design/frontend/api-mapping.md`를 참조하여 서비스 레이어를 구성한다.
Prism Mock 서버(http://localhost:4010)와 연동할 수 있도록 환경변수로 baseURL을 관리한다.

#### 7.1 API 공통 설정 (`src/services/api/config.ts`)

```typescript
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:4010',
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
  },
}
```

#### 7.2 Axios 클라이언트 (`src/services/api/client.ts`)

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

#### 7.3 API 타입 기본 정의 (`src/types/api.ts`)

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

#### 7.4 서비스 레이어 골격 예시 (`src/services/api/exampleService.ts`)

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

---

### 8단계. 실행 확인

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

---

## 출력 형식

| 항목 | 경로 | 비고 |
|------|------|------|
| 전역 스타일 | `frontend/src/styles/` | style-guide.md 기반 CSS 변수 포함 |
| 라우터 | `frontend/src/router/index.tsx` | ia.md 기반 라우트 정의 |
| 상태 관리 스토어 | `frontend/src/store/` | auth, ui 슬라이스/스토어 포함 |
| API 클라이언트 | `frontend/src/services/api/client.ts` | baseURL 환경변수 관리 |
| API 설정 | `frontend/src/services/api/config.ts` | VITE_API_URL 기반 |
| 공통 타입 | `frontend/src/types/api.ts` | 응답 래퍼, 에러 타입 |
| 환경변수 예시 | `frontend/.env.example` | VITE_API_URL 포함 |

## 품질 기준

- [ ] 정보아키텍처(`ia.md`) 기반 폴더 구조와 라우트 정의
- [ ] CSS 변수가 `style-guide.md`의 컬러·타이포그래피·간격 값과 일치
- [ ] API 클라이언트 baseURL이 `VITE_API_URL` 환경변수로 관리됨 (하드코딩 없음)
- [ ] `.env.example`에 `VITE_API_URL=http://localhost:4010` 포함
- [ ] `npm run dev` 성공 및 브라우저 로딩 확인
- [ ] `npm run build` 성공 (타입 오류·빌드 오류 없음)
- [ ] 페이지 컴포넌트 미구현 (placeholder만 존재)

## 주의사항

- **이 단계에서 페이지를 구현하지 않는다.** 기반 시스템(스타일·라우팅·상태관리·API 클라이언트) 골격만 완성한다.
- Prism Mock 서버는 docker-compose의 mock 프로파일로 제공된다. 이 가이드에서 직접 설치하지 않고 `backing-service-setup.md`의 산출물을 사용한다.
- API 서비스 레이어는 `src/services/api/` 안에 도메인별로 분리하여 Mock → 실제 서버 전환 시 서비스 파일만 교체하거나 환경변수만 변경해도 동작하도록 설계한다.
- CSS 변수 값을 임의로 추정하지 않는다. 반드시 `style-guide.md`에서 확인한 값을 사용한다.
- 프로토타입 화면 분석이 필요한 경우 playwright MCP 도구를 활용하여 모바일 사이즈(예: 390×844)로 확인한다.
- 기존 `frontend/` 디렉토리가 있는 경우 기존 파일을 삭제하거나 덮어쓰지 않는다. 충돌 여부를 먼저 확인한다.
- 환경변수 파일(`.env.local`, `.env`)은 gitignore에 포함시키고, `.env.example`만 커밋한다.
