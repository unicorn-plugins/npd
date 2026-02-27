# 프론트엔드 프로젝트 초기화 가이드 (Vue)

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

| 산출물 | 파일 경로 |
|--------|----------|
| 프로젝트 골격 | `frontend/` |
| CSS 변수·테마 | `frontend/src/styles/` |
| 라우팅 설정 | `frontend/src/router/` |
| 상태 관리 스토어 | `frontend/src/store/` |
| API 클라이언트 | `frontend/src/services/api/` |

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

기술스택이 결정되면 사용자에게 확인을 받고 다음 단계로 진행한다.

---

### 2단계. 프로젝트 생성 및 폴더 구조 설정

#### 2.1 프로젝트 생성

기존 `frontend/` 디렉토리가 있으면 그대로 유지하면서 작업한다.
없으면 선택한 플랫폼에 따라 생성한다.

```bash
# Vite + Vue + TypeScript
npm create vite@latest frontend -- --template vue-ts
```

#### 2.2 폴더 구조 생성

`프로토타입`의 메뉴 및 화면 계층을 기반으로 폴더를 구성한다.

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
├── vite.config.ts
├── tsconfig.json
└── package.json
```

`views/` 하위 폴더는 `ia.md`의 메뉴 계층과 일치하도록 생성한다.

#### 2.3 설정 파일 생성

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

> **환경변수 관리**: 프론트엔드 환경변수는 `public/runtime-env.js`에서 런타임으로 주입한다. `.env.example`이나 `.env.local` 파일은 별도로 생성하지 않는다. API URL 등의 설정은 `runtime-env.js` → 하드코딩 fallback(`'http://localhost:4010'`) 순서로 적용된다.

---

### 3단계. 의존성 설치

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

---

### 4단계. 스타일 시스템 구축

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

---

### 5단계. 라우팅 시스템 구축

`프로토타입`의 메뉴 계층과 화면 목록을 기반으로 라우트를 정의한다.

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

---

### 6단계. 상태 관리 시스템 구축

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

---

### 7단계. API 클라이언트 기본 설정

`API 설계서(docs/design/api/*.yaml)`를 참조하여 서비스 레이어를 구성한다.
런타임 환경변수(`runtime-env.js`)를 통해 서비스별 API 호스트를 관리한다.

#### 7.1 런타임 환경변수 자동 생성 (`tools/generate-runtime-env.sh`)

React와 동일한 구조로 `public/runtime-env.js`를 ROOT `.env`에서 자동 생성한다.
에이전트는 프로젝트의 서비스 구성을 분석하여 `tools/generate-runtime-env.sh`를 **동적으로 생성**한다.

**스크립트 생성 절차**:

1. ROOT `.env` 파일과 `docs/develop/dev-plan.md` (섹션 1: 서비스 목록)을 읽어 프로젝트에 필요한 환경변수 목록을 파악한다.
2. 아래 템플릿 구조를 기반으로 `tools/generate-runtime-env.sh`를 생성한다.
3. 변수 매핑 규칙:
   - `{SERVICE_NAME}_SERVICE_PORT` → `{SERVICE_NAME}_HOST: "http://localhost:${PORT}"`
   - OAuth2 크리덴셜 (`KAKAO_CLIENT_ID` 등) → 동일 키로 전달
   - `APP_ENV` → 기본값 `"development"`
   - `API_GROUP` → 기본값 `"/api/v1"`
4. Mock 단계 대응: `.env`의 `MOCK_MODE=true|false`를 읽어 분기. `MOCK_MODE=true`이면 모든 HOST를 `localhost:${MOCK_PORT}`(기본 4010)로 설정.

**스크립트 템플릿** (프로젝트의 실제 서비스 목록에 맞게 동적 구성):

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${1:-$PROJECT_ROOT/.env}"
OUTPUT_FILE="$PROJECT_ROOT/frontend/public/runtime-env.js"

if [ ! -f "$ENV_FILE" ]; then
  echo "WARN: .env not found ($ENV_FILE), using defaults"
fi

get_env() {
  local key="$1" default="$2"
  if [ -f "$ENV_FILE" ]; then
    local value
    value=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2- | tr -d '\r')
    echo "${value:-$default}"
  else
    echo "$default"
  fi
}

MOCK_MODE=$(get_env "MOCK_MODE" "true")
MOCK_PORT=$(get_env "MOCK_PORT" "4010")

# === 아래는 프로젝트의 서비스 목록에 맞게 동적 생성 ===
# dev-plan.md 섹션 1의 서비스 목록과 .env의 변수를 분석하여 작성한다.
# 예시:
# MEMBER_PORT=$(get_env "MEMBER_SERVICE_PORT" "8081")
# ORDER_PORT=$(get_env "ORDER_SERVICE_PORT" "8082")

if [ "$MOCK_MODE" = "true" ]; then
  cat > "$OUTPUT_FILE" <<EOF
window.__runtime_config__ = {
  APP_ENV: "development",
  API_GROUP: "/api/v1",
  // 서비스별 HOST — 프로젝트의 서비스 목록에 맞게 동적 생성
  // 예시:
  // MEMBER_HOST: "http://localhost:${MOCK_PORT}",
  // ORDER_HOST: "http://localhost:${MOCK_PORT}",
};
EOF
else
  cat > "$OUTPUT_FILE" <<EOF
window.__runtime_config__ = {
  APP_ENV: "$(get_env 'APP_ENV' 'development')",
  API_GROUP: "$(get_env 'API_GROUP' '/api/v1')",
  // 서비스별 HOST — 프로젝트의 서비스 목록에 맞게 동적 생성
  // 예시:
  // MEMBER_HOST: "http://localhost:${MEMBER_PORT}",
  // ORDER_HOST: "http://localhost:${ORDER_PORT}",
};
EOF
fi

echo "OK: $OUTPUT_FILE generated (MOCK_MODE=$MOCK_MODE)"
```

> 에이전트는 위 템플릿을 참고하되, **프로젝트의 실제 서비스 목록과 `.env` 변수에 맞게 변수 읽기 부분과 cat 블록의 내용을 동적으로 구성**한다.

#### 7.1a `package.json` scripts 변경

`frontend/package.json`의 `scripts`에 `predev`와 `prebuild`를 추가한다.

```json
{
  "scripts": {
    "predev": "bash ../tools/generate-runtime-env.sh",
    "dev": "vite",
    "prebuild": "bash ../tools/generate-runtime-env.sh",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint ."
  }
}
```

> `predev`/`prebuild`는 npm의 lifecycle hook으로, `npm run dev` 또는 `npm run build` 실행 시 자동으로 먼저 실행된다.
> Mock/실제 전환은 `.env`의 `MOCK_MODE=true|false`만 변경하면 된다. `package.json` 수정은 불요.

#### 7.1b `index.html` script 태그 추가

```html
<script src="/runtime-env.js"></script>
```

#### 7.1c 초기 실행 확인

```bash
bash tools/generate-runtime-env.sh
cat frontend/public/runtime-env.js
```

#### 7.1d `src/config/runtime.ts` 헬퍼 생성

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

```bash
docker compose --profile mock up -d
# Network 탭에서 API 요청이 http://localhost:4010 으로 향하는지 확인
```

---

## 출력 형식

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
| 런타임 환경변수 | `frontend/public/runtime-env.js` | 서비스별 HOST 설정 |

## 품질 기준

- [ ] 정보아키텍처(`ia.md`) 기반 폴더 구조와 라우트 정의
- [ ] CSS 변수가 `style-guide.md`의 컬러·타이포그래피·간격 값과 일치
- [ ] API 서비스별 HOST가 `public/runtime-env.js`로 관리됨 (`VITE_API_URL`은 fallback)
- [ ] `public/runtime-env.js`에 API_URL 설정 포함
- [ ] `npm run dev` 성공 및 브라우저 로딩 확인
- [ ] `npm run build` 성공 (타입 오류·빌드 오류 없음)
- [ ] 페이지 컴포넌트 미구현 (placeholder만 존재)

## 주의사항

- **이 단계에서 페이지를 구현하지 않는다.** 기반 시스템(스타일·라우팅·상태관리·API 클라이언트) 골격만 완성한다.
- Prism Mock 서버는 docker-compose의 mock 프로파일로 제공된다. `backing-service-setup.md`의 산출물을 사용한다.
- CSS 변수 값을 임의로 추정하지 않는다. 반드시 `style-guide.md`에서 확인한 값을 사용한다.
- 기존 `frontend/` 디렉토리가 있는 경우 기존 파일을 삭제하거나 덮어쓰지 않는다.
- 환경변수는 `public/runtime-env.js`로 관리한다. 프론트엔드 디렉토리에 별도 `.env` 파일을 생성하지 않는다.
