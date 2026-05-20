# 프론트엔드 실제 API 연동 (Vue)

## 목적

Mock API(Prism)를 실제 백엔드 API로 전환하고 E2E 동작을 확인한다.
`frontend-dev-vue.md`에서 구현한 Mock 연동 상태의 코드를 그대로 유지하면서
환경변수 전환 및 인증 흐름 연동으로 실제 서비스 가능한 상태를 완성한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 프론트엔드 코드 (Mock 연동 완료) | `frontend/` | `frontend-dev-vue.md` 산출물 |
| 백엔드 API 서버 | 실행 중인 서버 | `backend-api-dev.md` 산출물 |
| 백엔드 연결 정보 | `docs/develop/backing-service-result.md` | 실제 API URL, 포트, CORS 설정 확인 |
| 백엔드 인증 Controller | 실제 인증 관련 Controller/Router 코드 | 인증 엔드포인트 경로·스키마 확인 |
| 행위 계약 테스트 | `test/design-contract/integration/*.spec.ts` | 연동 시나리오별 기대 동작 확인 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 환경 설정 파일 (실제 API URL) | `frontend/public/runtime-env.js` |
| API 클라이언트 (인증 인터셉터 포함) | `frontend/src/services/api/client.ts` |
| 인증 서비스 함수 | `frontend/src/services/api/authService.ts` |
| 인증 상태 관리 | `frontend/src/stores/authStore.ts` |
| 프론트엔드 코드 (실제 API 연동 완료) | `frontend/` |

## 방법론

### 작업 순서 개요

1. 준비: 백엔드 API 실행 확인 및 연결 정보 파악
2. API 타입 동기화: 백엔드 controller/router 실제 코드 기반 TypeScript 타입 갱신
3. 환경변수 전환 (Mock → 실제 API URL)
4. 인증 흐름 연동 (JWT 로그인 → 저장 → 헤더 주입 → 갱신)
5. CORS / 네이티브 네트워크 보안 설정
6. 페이지별 실제 API 연동 테스트
7. 에러 케이스 처리 확인

---

### 1단계. 준비

#### 1.1 백엔드 API 실행 확인

`docs/develop/backing-service-result.md`를 읽어 아래 항목을 파악한다.

| 파악할 항목 | 확인 방법 |
|-----------|---------|
| 백엔드 API URL과 포트 | `backing-service-result.md`에서 확인 |
| CORS 허용 Origins | 백엔드 SecurityConfig에서 허용된 Origin 목록 확인 |
| 인증 방식 | 백엔드 인증 Controller의 SecurityConfig 및 어노테이션 확인 |
| 로그인 엔드포인트 | 백엔드 인증 Controller에서 `@PostMapping` 경로 확인 |
| 토큰 갱신 엔드포인트 | POST /auth/refresh 또는 유사 엔드포인트 |

백엔드 서버가 실제로 응답하는지 확인한다.

```bash
# 백엔드 헬스체크 (URL은 backing-service-result.md 기준으로 변경)
curl http://localhost:8080/actuator/health
# 또는
curl http://localhost:8080/api/health
```

응답이 없으면 백엔드 API 서버가 기동 중인지 확인한 후 진행한다.

#### 1.2 현재 Mock 환경 상태 확인

```bash
# Mock 서버가 실행 중이면 그대로 둔다 (개발 환경 분기를 위해 유지)
docker compose --profile mock ps

# 프론트엔드 현재 환경변수 확인
bash tools/generate-runtime-env.sh && cat frontend/public/runtime-env.js
# .env의 MOCK_MODE 설정에 따라 runtime-env.js가 자동 생성되었는지 확인
# MOCK_MODE=false이면 실제 서비스 포트가, MOCK_MODE=true이면 localhost:4010이 반영됨
```

---

### 2단계. API 타입 동기화

백엔드 controller와 AI 서비스 router의 **실제 구현 코드**를 읽어 프론트엔드 TypeScript 타입/인터페이스를 동기화한다.
문서가 아닌 실제 코드가 source of truth이므로, controller/router 코드를 직접 확인하여 동기화한다.

#### 2.1 실제 API 구현 파악

백엔드와 AI 서비스의 실제 코드를 읽어 엔드포인트 경로, 요청/응답 필드명·타입을 파악한다.

```bash
# Spring Boot controller 찾기 (어노테이션 기반)
grep -rn "@RestController\|@Controller" --include="*.java" --include="*.kt" .
# 엔드포인트 매핑 찾기
grep -rn "@RequestMapping\|@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping" --include="*.java" --include="*.kt" .
# AI 서비스 router 찾기 (FastAPI/Express/Flask 등)
grep -rn "app\.get\|app\.post\|router\.\|@app\.route\|@router\." --include="*.py" --include="*.ts" --include="*.js" .
```

확인 항목:
- 어노테이션/데코레이터에 정의된 실제 엔드포인트 경로
- 요청/응답 DTO 클래스의 필드명, 타입, 필수 여부 (controller가 참조하는 DTO를 추적하여 확인)
- AI 서비스 router의 경로 및 응답 구조

파악한 내용을 프론트엔드의 기존 타입과 대조하여 불일치 항목을 도출한다.

대조 확인 항목:
- 필드명 변경 (예: `userName` → `username`)
- 필드 타입 변경 (예: `string` → `number`)
- 필드 추가/삭제
- 응답 구조 변경 (예: 래핑 객체 추가 `{ data: {...}, meta: {...} }`)
- 엔드포인트 경로 변경

#### 2.2 TypeScript 타입 갱신

프론트엔드 코드에서 API 요청/응답에 사용하는 타입을 갱신한다.

```bash
# 타입 정의 파일 위치 확인
ls frontend/src/services/api/*Service.ts
ls frontend/src/types/
```

갱신 대상:
- `src/services/api/*Service.ts` — 각 서비스 함수의 요청/응답 인터페이스
- `src/types/*.ts` — 공유 타입 정의 (존재 시)

#### 2.3 컴포넌트 코드 갱신

타입 변경에 따라 해당 타입을 참조하는 Vue 컴포넌트(`*.vue`)와 Composable 코드도 함께 수정한다.

```bash
# 변경된 필드명을 사용하는 코드 검색
grep -rn "userName" frontend/src/
```

#### 2.4 타입 정합성 검증

```bash
cd frontend
npx vue-tsc --noEmit
```

타입 오류가 0건이어야 다음 단계로 진행한다.

---

### 3단계. 환경변수 전환

#### 3.1 generate-runtime-env.sh로 자동 전환

`tools/generate-runtime-env.sh`를 실행하면 ROOT/.env에 정의된 실제 서비스 포트를 읽어
`frontend/public/runtime-env.js`가 자동 생성된다.

```bash
# .env의 MOCK_MODE=false 확인 후 실행
bash tools/generate-runtime-env.sh

# 또는 npm run dev가 predev 스크립트를 통해 자동 실행
npm run dev
```

생성된 파일을 확인하여 HOST가 실제 백엔드 포트와 일치하는지 검증한다:

```bash
cat frontend/public/runtime-env.js
# MEMBER_HOST: "http://localhost:8081" 등 실제 포트가 반영되었는지 확인
```

**Mock 환경으로 복귀**: `.env`에서 `MOCK_MODE=true`로 변경한 뒤 `npm run dev`를 재시작하면
`generate-runtime-env.sh`가 `predev`에서 자동 실행되어 모든 HOST가 `localhost:4010`으로 복귀한다.

#### 3.2 전환 후 즉시 확인

`.env`의 `MOCK_MODE=false` 설정 후 Vite 개발 서버를 재시작하고 Network 탭에서 요청 URL을 확인한다.

```bash
cd frontend
npm run dev
```

브라우저 개발자도구 Network 탭에서 API 요청이 실제 백엔드 URL로 전송되는지 확인한다.

---

### 4단계. 인증 흐름 연동

#### 4.1 JWT 인증 흐름 개요

```
로그인 폼 제출
  → POST /auth/login (email, password)
  → 응답: { accessToken, refreshToken }
  → accessToken → localStorage 저장
  → refreshToken → localStorage 저장 (또는 httpOnly 쿠키)
  → API 요청마다 Authorization: Bearer {accessToken} 헤더 자동 주입
  → accessToken 만료(401) → refreshToken으로 재발급 시도
  → 재발급 성공 → 새 accessToken 저장 후 원래 요청 재시도
  → 재발급 실패 → localStorage 초기화 후 로그인 페이지로 리다이렉트
```

#### 4.2 API 클라이언트 인터셉터 구성

`frontend-env-setup-vue.md`에서 생성된 `src/services/api/client.ts`에 인증 인터셉터를 추가한다.

```typescript
// src/services/api/client.ts
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
})

// 요청 인터셉터: JWT 헤더 자동 주입
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 응답 인터셉터: 401 처리 및 토큰 갱신
let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshSubscribers.push((newToken) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            resolve(apiClient(originalRequest))
          })
        })
      }

      isRefreshing = true

      try {
        const refreshToken = localStorage.getItem('refreshToken')
        if (!refreshToken) throw new Error('No refresh token')

        const { data } = await axios.post(`${API_URL}/auth/refresh`, {
          refreshToken,
        })

        const newAccessToken = data.accessToken
        localStorage.setItem('accessToken', newAccessToken)
        if (data.refreshToken) {
          localStorage.setItem('refreshToken', data.refreshToken)
        }

        refreshSubscribers.forEach((cb) => cb(newAccessToken))
        refreshSubscribers = []

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(originalRequest)
      } catch {
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
        window.location.href = '/login'
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)
```

#### 4.3 인증 서비스 함수

```typescript
// src/services/api/authService.ts
import { apiClient } from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  refreshToken: string
  user: {
    id: string
    name: string
    email: string
    role: string
  }
}

export const authService = {
  login: (data: LoginRequest) =>
    apiClient.post<LoginResponse>('/auth/login', data),

  logout: () =>
    apiClient.post('/auth/logout'),

  refresh: (refreshToken: string) =>
    apiClient.post<Pick<LoginResponse, 'accessToken' | 'refreshToken'>>(
      '/auth/refresh',
      { refreshToken },
    ),

  me: () =>
    apiClient.get<LoginResponse['user']>('/auth/me'),
}
```

#### 4.4 인증 상태 관리

인증 상태(사용자 정보, 토큰 유무)를 컴포넌트에서 일관되게 사용하기 위해 상태 관리를 구현한다.

Vue 3 Composition API + Pinia 스토어로 인증 상태를 관리한다.

```typescript
// src/stores/authStore.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService, type LoginRequest } from '@/services/api/authService'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<{ id: string; name: string; email: string; role: string } | null>(null)
  const isAuthenticated = computed(() => user.value !== null)

  async function login(data: LoginRequest) {
    const res = await authService.login(data)
    const { accessToken, refreshToken, user: userData } = res.data
    localStorage.setItem('accessToken', accessToken)
    localStorage.setItem('refreshToken', refreshToken)
    user.value = userData
  }

  async function logout() {
    try {
      await authService.logout()
    } finally {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      user.value = null
    }
  }

  async function initialize() {
    const token = localStorage.getItem('accessToken')
    if (!token) return
    try {
      const res = await authService.me()
      user.value = res.data
    } catch {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
    }
  }

  return { user, isAuthenticated, login, logout, initialize }
})
```

앱 진입점(`src/main.ts`)에서 `initialize()`를 호출하여 새로고침 시 인증 상태를 복원한다.

```typescript
// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// 앱 마운트 전 인증 상태 복원
const { useAuthStore } = await import('@/stores/authStore')
const authStore = useAuthStore()
await authStore.initialize()

app.mount('#app')
```

Vue Router 네비게이션 가드로 인증 필요 라우트를 보호한다.

```typescript
// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/LoginView.vue') },
    {
      path: '/',
      meta: { requiresAuth: true },
      component: () => import('@/views/HomeView.vue'),
    },
    // ... 기타 라우트
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return '/login'
  }
})

export default router
```

#### 4.5 Mock 상수 일괄 제거

Phase 2(`frontend-dev-vue.md`)에서 페이지 컴포넌트에 임시로 작성된 모든 `MOCK_*`·`SAMPLE_*`·`FAKE_*` 명명 상수를 실제 데이터 페치 컴포저블(`use<Domain><Op>()`) 또는 Pinia 스토어로 교체한다. 단순 인증 스텁만 다루는 것이 아니라, 페이지가 렌더링에 사용하는 **모든 도메인 데이터 상수**를 대상으로 한다.

##### 4.5.1 인벤토리 작성

먼저 프로젝트 전체에서 Mock 상수 위치를 정확히 식별한다.

```bash
# 페이지·컴포넌트 안에 박힌 도메인 데이터 상수 검출
grep -rn "^\s*const MOCK_\|^\s*const SAMPLE_\|^\s*const FAKE_" frontend/src/ 2>/dev/null

# stubs/ 디렉토리 내 파일 목록 (Phase 2에서 작성된 모든 stub)
ls frontend/src/services/api/stubs/ 2>/dev/null
```

결과를 `docs/develop/mock-inventory.md`에 표로 정리한다.

| 파일:라인 | 상수명 | 데이터 종류 | 교체 후 호출할 컴포저블·스토어·서비스 함수 |
|----------|--------|------------|-----------------------------------------|
| `src/pages/<page>.vue:N` | `MOCK_<NAME>` | 목록·상세·통계·설정 등 | `use<Domain><Op>()` 또는 `use<Domain>Store()` |
| `src/components/<Comp>.vue:N` | `SAMPLE_<NAME>` | 컴포넌트 기본 데이터 | `use<Domain><Op>()` |

##### 4.5.2 페이지별 교체

인벤토리의 각 항목에 대해 다음을 수행한다.

1. 해당 페이지의 import에서 `MOCK_*` 상수 import 제거
2. `<script setup>` 본문에서 `const data = MOCK_X` 패턴을 `const { data, isLoading, error } = use<Domain><Op>(...)` 또는 Pinia 스토어 호출로 교체
3. 로딩·에러 상태 UI 추가 (Phase 2에서 누락된 경우)
4. 빈 응답·페이징 처리 추가
5. 상수 정의 코드(파일 상단의 배열 리터럴) 삭제

##### 4.5.3 stub 디렉토리 정리

`frontend/src/services/api/stubs/` 내 파일들은 다음 중 하나로 처리한다.

- **삭제**: Prism Mock 한계 보완용이었고 실제 API 응답이 동등하면 삭제
- **보존**: Mock 환경 복귀에 필요하면 보존하되, **페이지 컴포넌트에서 직접 import 금지**. `runtime-env.js`의 환경 분기로만 활성화한다

##### 4.5.4 검증

```bash
# 모든 MOCK_* 잔존이 0건이어야 함 (stubs/ 디렉토리 제외)
grep -rn "MOCK_\|SAMPLE_\|FAKE_" frontend/src/pages/ frontend/src/components/ 2>/dev/null | grep -v stubs/

# 빌드 통과 확인
cd frontend && npm run build

# 실 API만으로 동작 확인 (Mock 서버 중단 상태에서)
docker compose --profile mock down
cd frontend && npm run dev
# → 브라우저에서 모든 페이지가 실제 백엔드 응답으로 렌더링되는지 확인
```

> **예외 사유 표기**: 의도적으로 잔존시키는 상수가 있다면 같은 줄에 `// ALLOW: 사유` 주석을 붙여 grep 결과에서 인식 가능하게 한다.

---

### 5단계. 네트워크 보안 / CORS 설정

#### 5.1 브라우저에서 CORS 오류 확인

브라우저 콘솔에서 아래 메시지가 보이면 CORS 문제다.

```
Access to XMLHttpRequest at 'http://localhost:8080/...' from origin
'http://localhost:5173' has been blocked by CORS policy
```

#### 5.2 백엔드 CORS 설정 확인 (Spring Boot 기준)

백엔드 `SecurityConfig.java`에서 프론트엔드 Origin이 허용되어 있는지 확인한다.

```java
config.setAllowedOrigins(List.of(
    "http://localhost:5173",   // Vite 개발 서버 기본 포트
    "http://localhost:3000"
));
config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
config.setAllowedHeaders(List.of("*"));
config.setAllowCredentials(true);
```

확인 항목:

```
- [ ] allowedOrigins에 http://localhost:5173 포함 여부
- [ ] allowCredentials(true) 설정
- [ ] allowedHeaders에 Authorization 헤더 허용 여부
```

#### 5.3 Vite 프록시로 임시 우회 (선택)

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
```

프록시 사용 시 `VITE_API_URL=/api`로 설정한다.

---

### 6단계. 페이지별 실제 API 연동 테스트

#### 6.1 테스트 순서

`frontend-dev-vue.md`에서 구현한 페이지 순서(유저스토리 우선순위)와 동일한 순서로 테스트한다.

```
테스트 순서 원칙:
1. 로그인 페이지 (인증 흐름 기반이므로 최우선)
2. Must Have 유저스토리 페이지 (목록 → 상세 → 생성 순)
3. Should Have 유저스토리 페이지
```

#### 6.2 페이지별 연동 테스트 절차

각 페이지에 대해 아래 절차를 반복한다.

```
1. 브라우저에서 해당 페이지 접근
2. 개발자도구 Network 탭 열기 (XHR/Fetch 필터 적용)
3. 페이지 로드 시 발생하는 API 요청 확인:
   - 요청 URL이 실제 백엔드 URL인지 확인
   - 응답 상태 코드가 200인지 확인
   - Authorization 헤더가 요청에 포함되는지 확인
4. 화면에 실제 데이터가 렌더링되는지 확인
5. CRUD 동작 테스트 (생성, 수정, 삭제 후 목록 갱신 확인)
```

#### 6.3 에러 케이스 처리 확인

**401 Unauthorized 처리**:

```bash
# 브라우저 콘솔에서 실행
localStorage.setItem('accessToken', 'expired-token')
```

확인 흐름:
1. 만료 토큰으로 API 요청 → 401 반환
2. 응답 인터셉터에서 refreshToken으로 재발급 시도
3. 재발급 성공 → 원래 요청 재시도
4. 재발급 실패 → localStorage 초기화 → `/login` 리다이렉트

**403 / 네트워크 에러 처리**:

```typescript
// src/services/api/client.ts
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 403) {
      // showNotification('접근 권한이 없습니다.')
    }
    if (!error.response) {
      // showNotification('서버에 연결할 수 없습니다.')
    }
    // ... 401 처리 로직
  },
)
```

---

## 출력 형식

### 환경 설정 파일 구조

```javascript
// frontend/public/runtime-env.js
// =====================================================
// API HOST 환경 분기 (React와 동일 구조)
// =====================================================
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:8081",
  ORDER_HOST: "http://localhost:8082",
  // ... 서비스별 실제 포트
};
```

### 실제 API 연동 체크리스트 템플릿

전환 완료 후 아래 체크리스트를 작성한다.

```
## 실제 API 연동 체크리스트 (Vue)

### 환경 전환
- [ ] VITE_API_URL을 실제 백엔드 URL로 변경
- [ ] Vite 개발 서버 재시작
- [ ] Network 탭에서 요청이 실제 백엔드 URL로 전송되는지 확인

### CORS 확인
- [ ] 브라우저 콘솔에 CORS 오류 없음
- [ ] (오류 있을 시) 백엔드 SecurityConfig allowedOrigins에 localhost:5173 추가 확인

### 인증 흐름
- [ ] 로그인 API 호출 성공 (POST /auth/login)
- [ ] accessToken이 localStorage에 저장됨
- [ ] refreshToken이 localStorage에 저장됨
- [ ] 인증 필요 API 요청에 Authorization: Bearer {token} 헤더 자동 포함
- [ ] 토큰 만료(401) → 갱신 시도 → 성공 시 원래 요청 재시도 동작 확인
- [ ] 갱신 실패 → 로그인 리다이렉트 동작 확인
- [ ] Pinia authStore.initialize() 호출로 새로고침 후 상태 복원 확인
- [ ] Vue Router beforeEach 가드: 미인증 시 /login 리다이렉트 확인

### 페이지별 API 연동
- [ ] 로그인 페이지: 실제 인증 성공
- [ ] 목록 페이지들: 실제 데이터 렌더링
- [ ] 상세 페이지들: 실제 단건 조회 동작
- [ ] 생성/수정 폼: 실제 저장 후 목록 갱신
- [ ] 삭제: 실제 삭제 후 목록 갱신

### 에러 케이스
- [ ] 401 처리: 토큰 갱신 또는 로그인 리다이렉트
- [ ] 403 처리: 권한 없음 안내 메시지
- [ ] 네트워크 에러: 서버 연결 불가 안내 메시지

### Mock 상수 제거
- [ ] `docs/develop/mock-inventory.md` 작성 완료 (Phase 2에서 만든 모든 `MOCK_*`·`SAMPLE_*`·`FAKE_*` 위치 정리)
- [ ] 페이지·컴포넌트 내 `MOCK_*`·`SAMPLE_*`·`FAKE_*` 상수 0건 (grep으로 검증, `stubs/` 디렉토리 제외)
- [ ] Prism Mock 서버 중단(`docker compose --profile mock down`) 상태에서 모든 페이지 정상 동작
- [ ] 로딩·에러·빈 응답 UI가 모든 페이지에 적용됨
- [ ] 의도적 잔존 상수는 같은 줄에 `// ALLOW: 사유` 주석 표기

### Mock 환경 복귀 확인
- [ ] VITE_API_URL=http://localhost:4010 으로 변경 시 Mock 서버 정상 동작 확인
```

---

## 품질 기준

- [ ] 모든 페이지가 실제 백엔드 API 기반으로 정상 동작
- [ ] JWT 인증 흐름 정상 (로그인 → 토큰 저장 → API 호출 → 토큰 갱신)
- [ ] CORS 에러 없음
- [ ] 401/403/네트워크 에러 각각 적절한 사용자 안내 메시지 출력
- [ ] `public/runtime-env.js` 변경만으로 Mock ↔ 실제 API 즉시 전환 가능
- [ ] Pinia 상태 관리 및 Vue Router 가드 정상 동작
- [ ] `npm run build` 성공 (타입 오류·빌드 오류 없음)
- [ ] **페이지·컴포넌트 내 `MOCK_*`·`SAMPLE_*`·`FAKE_*` 명명 상수 0건** (grep 게이트, `stubs/` 디렉토리 제외): `grep -rn "MOCK_\|SAMPLE_\|FAKE_" frontend/src/pages/ frontend/src/components/ 2>/dev/null \| grep -v stubs/ \| grep -v "ALLOW:"` 결과가 0건이어야 한다
- [ ] **Prism Mock 서버 중단 상태에서 모든 페이지 정상 동작** (실 API만으로 데이터 렌더링 확인)

## 주의사항

- **Mock 서버 코드와 설정은 삭제하지 않는다.**
- **페이지 컴포넌트의 Mock 상수는 모두 제거한다.** Mock 서버는 보존하되, 페이지·컴포넌트 내 도메인 데이터 리터럴(`MOCK_*`·`SAMPLE_*`·`FAKE_*` 명명 상수)은 0건이어야 한다. Mock 환경 복귀는 `runtime-env.js`의 환경 분기와 Prism Mock 서버 조합으로만 이루어진다 (페이지 코드는 어느 환경에서도 동일한 컴포저블·스토어 호출 경로를 유지).
- **CORS 문제 발생 시 Vue 코드를 수정하지 않는다.** 백엔드 SecurityConfig에서 Origin을 허용한다.
- **Mock → 실제 전환은 `public/runtime-env.js` 변경만으로 완료되어야 한다.**
- 토큰 갱신 엔드포인트 경로는 반드시 백엔드 인증 Controller의 실제 경로와 일치해야 한다.
- Pinia 스토어의 `initialize()`는 앱 마운트 전 한 번만 호출해야 한다. 중복 호출 시 불필요한 `/auth/me` 요청이 발생한다.
- Vue Router beforeEach 가드에서 Pinia 스토어에 접근할 때 `useAuthStore()`가 `createPinia()` 이후에 호출되는지 확인한다.
