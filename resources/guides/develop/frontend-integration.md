# 프론트엔드 실제 API 연동 가이드

## 목적

Mock API(Prism)를 실제 백엔드 API로 전환하고 E2E 동작을 확인한다.
`frontend-dev.md`에서 구현한 Mock 연동 상태의 코드를 그대로 유지하면서
환경변수 전환 및 인증 흐름 연동으로 실제 서비스 가능한 상태를 완성한다.

> **플랫폼 판별**: 이 가이드는 `PLATFORM` 변수(`REACT` / `VUE` / `FLUTTER`)에 따라
> 분기 블록(`<!-- IF PLATFORM == X -->`)을 적용한다.
> 현재 프로젝트의 플랫폼은 `docs/develop/frontend-dev-result.md` 또는 설계 문서를 참조한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 프론트엔드 코드 (Mock 연동 완료) | `frontend/` | `frontend-dev.md` 산출물 |
| 백엔드 API 서버 | 실행 중인 서버 | `backend-api-dev.md` 산출물 |
| 백엔드 연결 정보 | `docs/develop/backing-service-result.md` | 실제 API URL, 포트, CORS 설정 확인 |
| OpenAPI 명세 | `docs/design/api/*.yaml` | 인증 엔드포인트 스키마 확인 |
| 행위 계약 테스트 | `test/design-contract/integration/*.spec.ts` | 연동 시나리오별 기대 동작 확인 |

## 출력 (이 단계 산출물)

<!-- IF PLATFORM == REACT -->

| 산출물 | 파일 경로 |
|--------|----------|
| 환경 설정 파일 (실제 API URL) | `frontend/.env.local` |
| API 클라이언트 (인증 인터셉터 포함) | `frontend/src/services/api/client.ts` |
| 인증 서비스 함수 | `frontend/src/services/api/authService.ts` |
| 인증 상태 관리 | `frontend/src/store/authStore.ts` |
| 프론트엔드 코드 (실제 API 연동 완료) | `frontend/` |

<!-- ELIF PLATFORM == VUE -->

| 산출물 | 파일 경로 |
|--------|----------|
| 환경 설정 파일 (실제 API URL) | `frontend/.env.local` |
| API 클라이언트 (인증 인터셉터 포함) | `frontend/src/services/api/client.ts` |
| 인증 서비스 함수 | `frontend/src/services/api/authService.ts` |
| 인증 상태 관리 | `frontend/src/stores/authStore.ts` |
| 프론트엔드 코드 (실제 API 연동 완료) | `frontend/` |

<!-- ELIF PLATFORM == FLUTTER -->

| 산출물 | 파일 경로 |
|--------|----------|
| 환경 설정 (dart-define / flavor) | `--dart-define=API_URL=...` 또는 `lib/core/config/env.dart` |
| Dio HTTP 클라이언트 (인터셉터 포함) | `lib/core/network/dio_client.dart` |
| 토큰 보안 저장소 | `lib/core/storage/secure_storage.dart` |
| 인증 서비스 함수 | `lib/features/auth/data/auth_service.dart` |
| 인증 상태 관리 (Riverpod) | `lib/features/auth/presentation/auth_notifier.dart` |
| 라우터 인증 가드 | `lib/core/router/app_router.dart` |
| Flutter 앱 (실제 API 연동 완료) | `lib/` |

<!-- ENDIF -->

## 방법론

### 작업 순서 개요

1. 준비: 백엔드 API 실행 확인 및 연결 정보 파악
2. 환경변수 전환 (Mock → 실제 API URL)
3. 인증 흐름 연동 (JWT 로그인 → 저장 → 헤더 주입 → 갱신)
4. CORS / 네이티브 네트워크 보안 설정
5. 페이지별 실제 API 연동 테스트
6. 에러 케이스 처리 확인

---

### 1단계. 준비

#### 1.1 백엔드 API 실행 확인

`docs/develop/backing-service-result.md`를 읽어 아래 항목을 파악한다.

| 파악할 항목 | 확인 방법 |
|-----------|---------|
| 백엔드 API URL과 포트 | `backing-service-result.md`에서 확인 |
| CORS 허용 Origins | 백엔드 SecurityConfig에서 허용된 Origin 목록 확인 |
| 인증 방식 | OpenAPI 명세 `securitySchemes` 항목 확인 |
| 로그인 엔드포인트 | `docs/design/api/*.yaml` - POST /auth/login 등 |
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
cat frontend/.env.local
# VITE_API_URL=http://localhost:4010  <-- 현재 Mock URL
```

---

### 2단계. 환경변수 전환

<!-- IF PLATFORM == REACT -->

#### 2.1 runtime-env.js 값 교체

`frontend/public/runtime-env.js` 파일에서 서비스별 HOST를 실제 백엔드 URL로 변경한다.

```javascript
// public/runtime-env.js (실제 백엔드 연동)
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:8081",
  ORDER_HOST: "http://localhost:8082",
  RECOMMEND_HOST: "http://localhost:8083",
  // ... 서비스별 실제 포트 (backing-service-result.md 참조)
};
```

URL은 `backing-service-result.md`에 기록된 실제 백엔드 주소를 사용한다.

**환경 분기 관리 원칙**: `runtime-env.js`만 변경하면 Mock ↔ 실제 전환이 완료된다.
Mock 환경으로 복귀하려면 HOST를 `http://localhost:4010`으로 되돌린다.

```javascript
// Mock 환경으로 복귀 시
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:4010",
  ORDER_HOST: "http://localhost:4010",
  // ... 모든 HOST를 Prism 서버로 복귀
};
```

> **브라우저 캐시 주의**: `runtime-env.js`가 캐싱되면 변경이 반영되지 않을 수 있다.
> 개발 서버에서는 Vite가 자동으로 처리하지만, nginx 배포 시에는 `Cache-Control: no-cache` 설정이 필요하다.

#### 2.2 전환 후 즉시 확인

`runtime-env.js` 변경 후 Vite 개발 서버를 재시작하고 Network 탭에서 요청 URL을 확인한다.

```bash
cd frontend
npm run dev
```

브라우저 개발자도구 Network 탭에서 API 요청이 실제 백엔드 URL로 전송되는지 확인한다.

<!-- ELIF PLATFORM == VUE -->

#### 2.1 runtime-env.js 값 교체

`frontend/public/runtime-env.js` 파일에서 서비스별 HOST를 실제 백엔드 URL로 변경한다.

```javascript
// public/runtime-env.js (실제 백엔드 연동)
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:8081",
  ORDER_HOST: "http://localhost:8082",
  RECOMMEND_HOST: "http://localhost:8083",
  // ... 서비스별 실제 포트 (backing-service-result.md 참조)
};
```

**환경 분기 관리 원칙**: `runtime-env.js`만 변경하면 Mock ↔ 실제 전환이 완료된다.

#### 2.2 전환 후 즉시 확인

```bash
cd frontend
npm run dev
```

브라우저 개발자도구 Network 탭에서 API 요청이 실제 백엔드 URL로 전송되는지 확인한다.

<!-- ELIF PLATFORM == FLUTTER -->

#### 2.1 런타임 설정 전환

**Flutter Web**: `web/runtime-env.js` 파일에서 서비스별 HOST를 실제 백엔드 URL로 변경한다.

```javascript
// web/runtime-env.js (실제 백엔드 연동)
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:8081",
  ORDER_HOST: "http://localhost:8082",
  RECOMMEND_HOST: "http://localhost:8083",
  // ... 서비스별 실제 포트 (backing-service-result.md 참조)
};
```

**Flutter Mobile (네이티브)**: `--dart-define` 값을 변경한다.

```bash
# Mock 환경 (Prism 서버)
flutter run --dart-define=API_BASE_URL=http://localhost:4010

# 실제 백엔드 환경
flutter run --dart-define=API_BASE_URL=http://localhost:8080

# 운영 환경
flutter run --dart-define=API_BASE_URL=https://api.example.com
```

`RuntimeConfig` 헬퍼(`frontend-env-setup.md`에서 생성)가 Flutter Web은 `runtime-env.js`에서, Flutter Mobile은 `--dart-define`에서 자동으로 값을 읽는다.

> **[DEFERRED]** 멀티 Mock 포트(서비스별 Prism 인스턴스) → 실제 API 게이트웨이 단일 URL
> 전환 시나리오는 `backing-service-setup.md`에 MOCK == MULTI 지원이 추가될 때
> 이 섹션과 함께 업데이트된다.

#### 2.2 전환 후 즉시 확인

```bash
# Flutter Web: runtime-env.js 변경 후 재시작
flutter run -d chrome

# Flutter Mobile: --dart-define으로 실행
flutter run --dart-define=API_BASE_URL=http://localhost:8080
```

Flutter DevTools 또는 Dio 로그 인터셉터(5단계 참조)를 통해 요청 URL이
실제 백엔드로 전송되는지 확인한다.

<!-- ENDIF -->

---

### 3단계. 인증 흐름 연동

#### 3.1 JWT 인증 흐름 개요

<!-- IF PLATFORM == REACT -->

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

<!-- ELIF PLATFORM == VUE -->

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

<!-- ELIF PLATFORM == FLUTTER -->

```
로그인 화면 제출
  → POST /auth/login (email, password)
  → 응답: { accessToken, refreshToken }
  → accessToken → flutter_secure_storage 저장 (Keychain/Keystore 암호화)
  → refreshToken → flutter_secure_storage 저장
  → API 요청마다 Dio 요청 인터셉터가 Authorization: Bearer {accessToken} 헤더 주입
  → accessToken 만료(401) → QueuedInterceptorsWrapper로 동시 요청 큐잉
  → refreshToken으로 재발급 시도 (한 번만 실행)
  → 재발급 성공 → 큐에 쌓인 모든 요청 재시도
  → 재발급 실패 → secure_storage 전체 초기화 → go_router redirect로 로그인 화면 이동
```

<!-- ENDIF -->

#### 3.2 API 클라이언트 인터셉터 구성

<!-- IF PLATFORM == REACT -->

`frontend-env-setup.md`에서 생성된 `src/services/api/client.ts`에 인증 인터셉터를 추가한다.

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

// 요청 인터셉터: 모든 요청에 JWT 헤더 자동 주입
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

const subscribeTokenRefresh = (callback: (token: string) => void) => {
  refreshSubscribers.push(callback)
}

const onTokenRefreshed = (newToken: string) => {
  refreshSubscribers.forEach((callback) => callback(newToken))
  refreshSubscribers = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      if (isRefreshing) {
        // 이미 갱신 중이면 갱신 완료 후 재시도
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            resolve(apiClient(originalRequest))
          })
        })
      }

      isRefreshing = true

      try {
        const refreshToken = localStorage.getItem('refreshToken')
        if (!refreshToken) throw new Error('No refresh token')

        // 토큰 갱신 엔드포인트 (OpenAPI 명세에 따라 URL 조정)
        const { data } = await axios.post(`${API_URL}/auth/refresh`, {
          refreshToken,
        })

        const newAccessToken = data.accessToken
        localStorage.setItem('accessToken', newAccessToken)

        if (data.refreshToken) {
          localStorage.setItem('refreshToken', data.refreshToken)
        }

        onTokenRefreshed(newAccessToken)
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(originalRequest)
      } catch {
        // 갱신 실패: 로그아웃 처리 후 로그인 리다이렉트
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

갱신 엔드포인트 경로(`/auth/refresh`)는 OpenAPI 명세와 `backing-service-result.md`를 기준으로 맞춘다.

<!-- ELIF PLATFORM == VUE -->

`frontend-env-setup.md`에서 생성된 `src/services/api/client.ts`에 인증 인터셉터를 추가한다.

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

<!-- ELIF PLATFORM == FLUTTER -->

`lib/core/network/dio_client.dart`에 Dio 클라이언트와 인증 인터셉터를 구성한다.

**패키지 추가** (`pubspec.yaml`):

```yaml
dependencies:
  dio: ^5.4.0
  flutter_secure_storage: ^9.0.0
  riverpod: ^2.5.0
  flutter_riverpod: ^2.5.0
  go_router: ^13.0.0
```

**토큰 보안 저장소** (`lib/core/storage/secure_storage.dart`):

```dart
// lib/core/storage/secure_storage.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorage {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  static const _keyAccessToken = 'accessToken';
  static const _keyRefreshToken = 'refreshToken';

  static Future<String?> readAccessToken() =>
      _storage.read(key: _keyAccessToken);

  static Future<String?> readRefreshToken() =>
      _storage.read(key: _keyRefreshToken);

  static Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(key: _keyAccessToken, value: accessToken);
    await _storage.write(key: _keyRefreshToken, value: refreshToken);
  }

  static Future<void> deleteAll() => _storage.deleteAll();
}
```

**Dio 클라이언트 + `QueuedInterceptorsWrapper`** (`lib/core/network/dio_client.dart`):

```dart
// lib/core/network/dio_client.dart
import 'package:dio/dio.dart';
import '../config/env.dart';
import '../storage/secure_storage.dart';

// QueuedInterceptorsWrapper: 동시에 여러 401 요청이 들어올 때
// 토큰 갱신이 한 번만 실행되도록 보장 (React의 isRefreshing 패턴과 동일 역할)
class AuthInterceptor extends QueuedInterceptorsWrapper {
  final Dio _dio;

  AuthInterceptor(this._dio);

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await SecureStorage.readAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      final refreshToken = await SecureStorage.readRefreshToken();
      if (refreshToken == null) {
        await SecureStorage.deleteAll();
        // go_router redirect guard가 로그인 화면으로 이동시킴 (3.4 참조)
        handler.reject(err);
        return;
      }

      try {
        // 토큰 갱신 요청 (인터셉터 우회를 위해 별도 Dio 인스턴스 사용)
        final refreshDio = Dio(BaseOptions(baseUrl: Env.apiUrl));
        final response = await refreshDio.post(
          '/auth/refresh',
          data: {'refreshToken': refreshToken},
        );

        final newAccessToken = response.data['accessToken'] as String;
        final newRefreshToken =
            response.data['refreshToken'] as String? ?? refreshToken;

        await SecureStorage.saveTokens(
          accessToken: newAccessToken,
          refreshToken: newRefreshToken,
        );

        // 원래 요청에 새 토큰 주입 후 재시도
        err.requestOptions.headers['Authorization'] = 'Bearer $newAccessToken';
        final retryResponse = await _dio.fetch(err.requestOptions);
        handler.resolve(retryResponse);
      } on DioException {
        // 갱신 실패: secure storage 초기화 후 로그인으로 이동
        await SecureStorage.deleteAll();
        handler.reject(err);
      }
    } else {
      handler.next(err);
    }
  }
}

Dio createDioClient() {
  final dio = Dio(
    BaseOptions(
      baseUrl: Env.apiUrl,
      headers: {'Content-Type': 'application/json'},
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
    ),
  );

  dio.interceptors.add(AuthInterceptor(dio));
  return dio;
}
```

<!-- ENDIF -->

#### 3.3 인증 서비스 함수

<!-- IF PLATFORM == REACT -->

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

엔드포인트 경로는 OpenAPI 명세 `docs/design/api/*.yaml`의 실제 경로와 일치해야 한다.

<!-- ELIF PLATFORM == VUE -->

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

<!-- ELIF PLATFORM == FLUTTER -->

```dart
// lib/features/auth/data/auth_service.dart
import 'package:dio/dio.dart';

class AuthService {
  final Dio _dio;

  AuthService(this._dio);

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await _dio.post(
      '/auth/login',
      data: {'email': email, 'password': password},
    );
    // response.data: { accessToken, refreshToken, user: { id, name, email, role } }
    return response.data as Map<String, dynamic>;
  }

  Future<void> logout() async {
    await _dio.post('/auth/logout');
  }

  Future<Map<String, dynamic>> refresh(String refreshToken) async {
    final response = await _dio.post(
      '/auth/refresh',
      data: {'refreshToken': refreshToken},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> me() async {
    final response = await _dio.get('/auth/me');
    return response.data as Map<String, dynamic>;
  }
}
```

엔드포인트 경로는 OpenAPI 명세 `docs/design/api/*.yaml`의 실제 경로와 일치해야 한다.

<!-- ENDIF -->

#### 3.4 인증 상태 관리

인증 상태(사용자 정보, 토큰 유무)를 컴포넌트에서 일관되게 사용하기 위해 상태 관리를 구현한다.

<!-- IF PLATFORM == REACT -->

```typescript
// src/store/authStore.ts
// Zustand 또는 Context API 중 프로젝트 설정에 따라 선택
import { create } from 'zustand'
import { authService, type LoginRequest } from '@/services/api/authService'

interface AuthState {
  user: { id: string; name: string; email: string; role: string } | null
  isAuthenticated: boolean
  login: (data: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  initialize: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,

  login: async (data) => {
    const res = await authService.login(data)
    const { accessToken, refreshToken, user } = res.data
    localStorage.setItem('accessToken', accessToken)
    localStorage.setItem('refreshToken', refreshToken)
    set({ user, isAuthenticated: true })
  },

  logout: async () => {
    try {
      await authService.logout()
    } finally {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      set({ user: null, isAuthenticated: false })
    }
  },

  initialize: async () => {
    const token = localStorage.getItem('accessToken')
    if (!token) return
    try {
      const res = await authService.me()
      set({ user: res.data, isAuthenticated: true })
    } catch {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
    }
  },
}))
```

앱 진입점(`src/main.tsx` 또는 `App.tsx`)에서 `initialize()`를 호출하여 새로고침 시 인증 상태를 복원한다.

```typescript
// src/App.tsx (또는 최상위 컴포넌트)
import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'

export default function App() {
  const initialize = useAuthStore((state) => state.initialize)

  useEffect(() => {
    initialize()
  }, [initialize])

  // ... 라우터 렌더링
}
```

<!-- ELIF PLATFORM == VUE -->

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

<!-- ELIF PLATFORM == FLUTTER -->

Riverpod `AsyncNotifier` 기반으로 인증 상태를 관리한다.

```dart
// lib/features/auth/presentation/auth_notifier.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/storage/secure_storage.dart';
import '../data/auth_service.dart';
import '../../../core/network/dio_client.dart';

// 사용자 모델
class UserModel {
  final String id;
  final String name;
  final String email;
  final String role;

  const UserModel({
    required this.id,
    required this.name,
    required this.email,
    required this.role,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
        id: json['id'] as String,
        name: json['name'] as String,
        email: json['email'] as String,
        role: json['role'] as String,
      );
}

// AuthNotifier: AsyncNotifier<UserModel?> — null이면 미인증
class AuthNotifier extends AsyncNotifier<UserModel?> {
  late final AuthService _authService;

  @override
  Future<UserModel?> build() async {
    _authService = AuthService(ref.read(dioClientProvider));
    // 앱 시작 시 저장된 토큰으로 사용자 정보 복원
    return await _initialize();
  }

  Future<UserModel?> _initialize() async {
    final token = await SecureStorage.readAccessToken();
    if (token == null) return null;
    try {
      final data = await _authService.me();
      return UserModel.fromJson(data['user'] as Map<String, dynamic>);
    } catch (_) {
      await SecureStorage.deleteAll();
      return null;
    }
  }

  Future<void> login({
    required String email,
    required String password,
  }) async {
    state = const AsyncLoading();
    try {
      final data = await _authService.login(email: email, password: password);
      await SecureStorage.saveTokens(
        accessToken: data['accessToken'] as String,
        refreshToken: data['refreshToken'] as String,
      );
      final user = UserModel.fromJson(data['user'] as Map<String, dynamic>);
      state = AsyncData(user);
    } catch (e, st) {
      state = AsyncError(e, st);
    }
  }

  Future<void> logout() async {
    try {
      await _authService.logout();
    } finally {
      await SecureStorage.deleteAll();
      state = const AsyncData(null);
    }
  }
}

// Provider 선언
final dioClientProvider = Provider((ref) => createDioClient());
final authNotifierProvider =
    AsyncNotifierProvider<AuthNotifier, UserModel?>(() => AuthNotifier());
```

`go_router` redirect guard로 인증 필요 라우트를 보호하고,
인증 실패(401 갱신 실패) 시 자동으로 로그인 화면으로 이동시킨다.

```dart
// lib/core/router/app_router.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/auth_notifier.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    // redirect guard: 인증 상태 변화 시 자동 재평가
    redirect: (context, state) {
      final authState = ref.read(authNotifierProvider);

      // 로딩 중이면 splash 유지
      if (authState.isLoading) return '/splash';

      final isAuthenticated = authState.valueOrNull != null;
      final isLoginPage = state.matchedLocation == '/login';

      if (!isAuthenticated && !isLoginPage) return '/login';
      if (isAuthenticated && isLoginPage) return '/';
      return null;
    },
    refreshListenable: _AuthStateNotifier(ref),
    routes: [
      GoRoute(path: '/splash', builder: (_, __) => const SplashScreen()),
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
      // ... 기타 라우트
    ],
  );
});

// GoRouter.refreshListenable 용 어댑터
class _AuthStateNotifier extends ChangeNotifier {
  _AuthStateNotifier(Ref ref) {
    ref.listen(authNotifierProvider, (_, __) => notifyListeners());
  }
}
```

앱 진입점(`lib/main.dart`)에서 `ProviderScope`로 Riverpod를 초기화하고,
splash 화면에서 토큰 검증을 수행한다.

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/router/app_router.dart';

void main() {
  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      routerConfig: router,
    );
  }
}
```

<!-- ENDIF -->

#### 3.5 stub 데이터 제거

<!-- IF PLATFORM == REACT -->

`frontend-dev.md`에서 Prism 한계 보완용으로 작성한 `src/services/api/stubs/authStub.ts` 등의 stub 로직을 실제 인증 서비스로 교체한다.

```bash
# stub 파일 목록 확인
ls frontend/src/services/api/stubs/
```

각 stub 파일을 열어 해당 로직을 실제 서비스 함수 호출로 교체한다.
stub 파일 자체는 삭제하지 않고 비워두거나 주석 처리하여 Mock 환경 복귀 시 참고 가능하게 보존한다.

<!-- ELIF PLATFORM == VUE -->

`frontend-dev.md`에서 작성한 stub 로직을 실제 인증 서비스로 교체한다.

```bash
# stub 파일 목록 확인
ls frontend/src/services/api/stubs/
```

각 stub 파일을 열어 해당 로직을 실제 서비스 함수 호출로 교체한다.
stub 파일은 삭제하지 않고 주석 처리하여 Mock 복귀 시 참고 가능하게 보존한다.

<!-- ELIF PLATFORM == FLUTTER -->

`frontend-dev.md`에서 작성한 stub 데이터 소스 클래스를 실제 서비스로 교체한다.

```dart
// stub Repository를 실제 Repository로 교체 예시
// 변경 전: lib/features/auth/data/auth_repository_stub.dart
// 변경 후: lib/features/auth/data/auth_repository.dart (Dio 기반)
```

stub 환경에서 저장된 임시 보안 데이터를 초기화한다.

```dart
// 앱 내 개발자 설정 화면 또는 로그에서 아래 호출
await SecureStorage.deleteAll();
// 이후 재로그인하면 실제 토큰이 secure_storage에 저장됨
```

stub 파일은 삭제하지 않고 주석 처리하여 Mock 환경 복귀 시 참고 가능하게 보존한다.

<!-- ENDIF -->

---

### 4단계. 네트워크 보안 / CORS 설정

<!-- IF PLATFORM == REACT -->

#### 4.1 브라우저에서 CORS 오류 확인

브라우저 콘솔에서 아래와 같은 메시지가 보이면 CORS 문제다.

```
Access to XMLHttpRequest at 'http://localhost:8080/...' from origin
'http://localhost:5173' has been blocked by CORS policy
```

#### 4.2 백엔드 CORS 설정 확인 (Spring Boot 기준)

백엔드 `SecurityConfig.java` (또는 `CorsConfig.java`)에서 프론트엔드 Origin이 허용되어 있는지 확인한다.

```java
// 백엔드 SecurityConfig.java 확인 항목
.cors(cors -> cors.configurationSource(request -> {
    CorsConfiguration config = new CorsConfiguration();
    config.setAllowedOrigins(List.of(
        "http://localhost:5173",   // Vite 개발 서버 기본 포트
        "http://localhost:3000"    // 추가 포트 (필요시)
    ));
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
    config.setAllowedHeaders(List.of("*"));
    config.setAllowCredentials(true);
    return config;
}))
```

확인 항목:

```
- [ ] allowedOrigins에 http://localhost:5173 포함 여부
- [ ] allowedMethods에 필요한 HTTP 메서드 포함 여부
- [ ] allowCredentials(true) 설정 (쿠키/Authorization 헤더 사용 시 필수)
- [ ] allowedHeaders에 Authorization 헤더 허용 여부
```

CORS 설정 변경 후 백엔드 서버를 재시작한다.

#### 4.3 Vite 프록시로 임시 우회 (선택)

백엔드 CORS 설정 변경이 어려운 경우 `vite.config.ts`에 프록시를 설정하여 개발 중 CORS를 우회할 수 있다.

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api/, '')  // prefix 제거가 필요한 경우
      },
    },
  },
})
```

프록시 사용 시 `VITE_API_URL`을 `/api`로 변경한다.

```dotenv
# vite.config.ts 프록시 사용 시
VITE_API_URL=/api
```

프록시는 개발 환경에서만 동작한다. 프로덕션 배포 시에는 실제 CORS 설정 또는 리버스 프록시(Nginx)를 사용한다.

<!-- ELIF PLATFORM == VUE -->

#### 4.1 브라우저에서 CORS 오류 확인

브라우저 콘솔에서 아래 메시지가 보이면 CORS 문제다.

```
Access to XMLHttpRequest at 'http://localhost:8080/...' from origin
'http://localhost:5173' has been blocked by CORS policy
```

#### 4.2 백엔드 CORS 설정 확인 (Spring Boot 기준)

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

#### 4.3 Vite 프록시로 임시 우회 (선택)

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

<!-- ELIF PLATFORM == FLUTTER -->

#### 4.1 Flutter 네이티브 앱의 CORS 미적용

> **Flutter(네이티브 앱)는 CORS 설정이 불필요하다.**
> 브라우저의 Same-Origin Policy는 WebView가 아닌 네이티브 HTTP 클라이언트(Dio)에는
> 적용되지 않는다. CORS 관련 오류가 발생하면 네트워크 보안 정책(아래)을 먼저 점검한다.

#### 4.2 Android 네트워크 보안 설정 (HTTP 허용)

개발 환경에서 HTTP(비암호화) 백엔드에 접근하려면 `AndroidManifest.xml`에 cleartext를 허용한다.

```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<application
    android:usesCleartextTraffic="true"
    ...>
```

또는 네트워크 보안 설정 파일을 사용한다 (더 세밀한 제어):

```xml
<!-- android/app/src/main/res/xml/network_security_config.xml -->
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
  <domain-config cleartextTrafficPermitted="true">
    <domain includeSubdomains="true">localhost</domain>
    <domain includeSubdomains="true">10.0.2.2</domain><!-- 에뮬레이터에서 호스트 접근 -->
  </domain-config>
</network-security-config>
```

```xml
<!-- AndroidManifest.xml에서 참조 -->
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
```

> 프로덕션 빌드에서는 `usesCleartextTraffic="false"`로 되돌리고 HTTPS를 사용한다.

#### 4.3 iOS App Transport Security (ATS) 설정

개발 환경에서 HTTP 백엔드에 접근하려면 `Info.plist`에 ATS 예외를 추가한다.

```xml
<!-- ios/Runner/Info.plist -->
<key>NSAppTransportSecurity</key>
<dict>
  <key>NSAllowsLocalNetworking</key>
  <true/>
  <!-- 또는 특정 도메인만 허용 -->
  <key>NSExceptionDomains</key>
  <dict>
    <key>localhost</key>
    <dict>
      <key>NSExceptionAllowsInsecureHTTPLoads</key>
      <true/>
    </dict>
  </dict>
</dict>
```

> 프로덕션 빌드에서는 ATS 예외를 제거하고 HTTPS를 사용한다.

<!-- ENDIF -->

---

### 5단계. 페이지별 실제 API 연동 테스트

#### 5.1 테스트 순서

`frontend-dev.md`에서 구현한 페이지 순서(유저스토리 우선순위)와 동일한 순서로 테스트한다.

```
테스트 순서 원칙:
1. 로그인 페이지 (인증 흐름 기반이므로 최우선)
2. Must Have 유저스토리 페이지 (목록 → 상세 → 생성 순)
3. Should Have 유저스토리 페이지
```

#### 5.2 페이지별 연동 테스트 절차

<!-- IF PLATFORM == REACT -->

각 페이지에 대해 아래 절차를 반복한다.

```
1. 브라우저에서 해당 페이지 접근
2. 개발자도구 Network 탭 열기 (XHR/Fetch 필터 적용)
3. 페이지 로드 시 발생하는 API 요청 확인:
   - 요청 URL이 실제 백엔드 URL인지 확인
   - 응답 상태 코드가 200인지 확인
   - Authorization 헤더가 요청에 포함되는지 확인 (인증 필요 API)
4. 화면에 실제 데이터가 렌더링되는지 확인
5. CRUD 동작 테스트 (생성, 수정, 삭제 후 목록 갱신 확인)
```

<!-- ELIF PLATFORM == VUE -->

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

<!-- ELIF PLATFORM == FLUTTER -->

각 화면에 대해 아래 절차를 반복한다.

**방법 A: Dio 로그 인터셉터**

`createDioClient()`에 로그 인터셉터를 추가하여 요청/응답을 콘솔에서 확인한다.

```dart
// lib/core/network/dio_client.dart 수정
import 'package:dio/dio.dart';

Dio createDioClient() {
  final dio = Dio(/* ... */);

  // 개발 환경에서만 로그 인터셉터 추가
  assert(() {
    dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
      requestHeader: true,
      responseHeader: false,
    ));
    return true;
  }());

  dio.interceptors.add(AuthInterceptor(dio));
  return dio;
}
```

터미널에서 각 요청의 URL, 헤더, 응답 상태를 확인한다.

**방법 B: Flutter DevTools Network 탭**

```bash
# 디버그 모드로 앱 실행
flutter run

# 별도 터미널에서 DevTools 실행
flutter pub global activate devtools
flutter pub global run devtools
```

Chrome에서 `http://localhost:9100`(DevTools URL)을 열고,
Network 탭에서 요청 URL, Authorization 헤더, 응답 상태 코드를 확인한다.

테스트 절차:
```
1. 해당 화면으로 이동
2. Dio 로그 또는 DevTools Network 탭에서 API 요청 확인:
   - 요청 URL이 실제 백엔드 URL인지 확인
   - 응답 상태 코드가 200인지 확인
   - Authorization: Bearer {token} 헤더 포함 여부 확인 (인증 필요 API)
3. 화면에 실제 데이터가 렌더링되는지 확인
4. CRUD 동작 테스트 (생성, 수정, 삭제 후 목록 갱신 확인)
```

<!-- ENDIF -->

#### 5.3 에러 케이스 처리 확인

<!-- IF PLATFORM == REACT -->

**401 Unauthorized 처리**: 토큰 만료 상황을 재현하여 흐름을 확인한다.

```bash
# localStorage에서 토큰을 만료된 값으로 교체하여 401 시뮬레이션
# 브라우저 콘솔에서 실행
localStorage.setItem('accessToken', 'expired-token')
```

확인 흐름:
1. 만료 토큰으로 API 요청 → 백엔드에서 401 반환
2. 응답 인터셉터에서 refreshToken으로 재발급 시도
3. 재발급 성공 → 원래 요청 재시도 → 정상 응답
4. 재발급 실패 → localStorage 초기화 → `/login` 리다이렉트

**403 Forbidden 처리**: 권한 없는 리소스 접근 시 안내 메시지를 확인한다.

```typescript
// src/services/api/client.ts 에러 핸들링 추가 (403 전용)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 403) {
      // 권한 없음 안내 (Toast 또는 별도 에러 페이지)
      // Toast 컴포넌트가 있으면: showToast('접근 권한이 없습니다.', 'error')
      // 없으면: window.location.href = '/forbidden'
    }
    // ... 기존 401 처리 로직
  },
)
```

**네트워크 에러 처리**: 백엔드 서버가 응답하지 않는 상황을 확인한다.

```typescript
// 응답 인터셉터 마지막 catch에서 네트워크 에러 분기
if (!error.response) {
  // 네트워크 오류 (서버 미응답, 타임아웃)
  // showToast('서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.', 'error')
}
```

<!-- ELIF PLATFORM == VUE -->

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

<!-- ELIF PLATFORM == FLUTTER -->

**401 Unauthorized 처리**: secure_storage의 토큰을 만료 값으로 교체하여 흐름을 확인한다.

```dart
// 개발자 설정 화면 또는 디버그 버튼에서 실행
await SecureStorage.saveTokens(
  accessToken: 'expired-token',
  refreshToken: 'valid-refresh-token',
);
```

확인 흐름:
1. 만료 accessToken으로 API 요청 → 백엔드에서 401 반환
2. `QueuedInterceptorsWrapper.onError`에서 refreshToken으로 갱신 시도
3. 갱신 성공 → secure_storage에 새 토큰 저장 → 원래 요청 재시도
4. 갱신 실패 → `SecureStorage.deleteAll()` → `authNotifierProvider` 상태 null → go_router redirect → 로그인 화면

**403 Forbidden 처리**:

```dart
// lib/core/network/dio_client.dart AuthInterceptor.onError에 추가
if (err.response?.statusCode == 403) {
  // ScaffoldMessenger 또는 전역 알림으로 안내
  // GlobalSnackbar.show('접근 권한이 없습니다.');
}
```

**네트워크 에러 처리**:

```dart
// DioExceptionType.connectionTimeout, receiveTimeout, connectionError 분기
if (err.type == DioExceptionType.connectionTimeout ||
    err.type == DioExceptionType.connectionError) {
  // GlobalSnackbar.show('서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.');
}
```

<!-- ENDIF -->

---

## 출력 형식

### 환경 설정 파일 구조

<!-- IF PLATFORM == REACT -->

```javascript
// frontend/public/runtime-env.js
// =====================================================
// API HOST 환경 분기
// Mock 환경:  모든 HOST = http://localhost:4010
// 실제 환경:  서비스별 HOST = http://localhost:{포트}
// =====================================================
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:8081",
  ORDER_HOST: "http://localhost:8082",
  // ... 서비스별 실제 포트
};
```

<!-- ELIF PLATFORM == VUE -->

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

<!-- ELIF PLATFORM == FLUTTER -->

**Flutter Web**: `web/runtime-env.js`를 변경한다.

```javascript
// web/runtime-env.js
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:8081",
  ORDER_HOST: "http://localhost:8082",
  // ... 서비스별 실제 포트
};
```

**Flutter Mobile**: `--dart-define`을 사용한다.

```bash
flutter run --dart-define=API_BASE_URL=http://localhost:8080
```

<!-- ENDIF -->

### 실제 API 연동 체크리스트 템플릿

전환 완료 후 아래 체크리스트를 작성한다.

<!-- IF PLATFORM == REACT -->

```
## 실제 API 연동 체크리스트 (React)

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
- [ ] 새로고침 후 로그인 상태 복원 (initialize() 호출 확인)

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

### Mock 환경 복귀 확인
- [ ] VITE_API_URL=http://localhost:4010 으로 변경 시 Mock 서버 정상 동작 확인
- [ ] docker compose --profile mock up -d 으로 Mock 서버 기동 가능 확인
```

<!-- ELIF PLATFORM == VUE -->

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

### Mock 환경 복귀 확인
- [ ] VITE_API_URL=http://localhost:4010 으로 변경 시 Mock 서버 정상 동작 확인
```

<!-- ELIF PLATFORM == FLUTTER -->

```
## 실제 API 연동 체크리스트 (Flutter)

### 환경 전환
- [ ] --dart-define=API_URL=http://localhost:8080 으로 앱 실행
- [ ] Dio 로그 인터셉터에서 요청 URL이 실제 백엔드 URL인지 확인
- [ ] (DEFERRED) 멀티 Mock 포트 → 단일 게이트웨이 전환 시나리오는 별도 업데이트

### 네이티브 네트워크 보안
- [ ] Android: AndroidManifest.xml usesCleartextTraffic 또는 network_security_config 설정 (개발용)
- [ ] iOS: Info.plist NSAppTransportSecurity ATS 예외 설정 (개발용, HTTP 사용 시)
- [ ] 에뮬레이터에서 10.0.2.2(Android) / 127.0.0.1(iOS Simulator) 로 백엔드 접근 확인

### 인증 흐름
- [ ] 로그인 API 호출 성공 (POST /auth/login)
- [ ] accessToken이 flutter_secure_storage에 저장됨 (Keychain/Keystore 암호화)
- [ ] refreshToken이 flutter_secure_storage에 저장됨
- [ ] 인증 필요 API 요청에 Authorization: Bearer {token} 헤더 자동 포함 (Dio onRequest 인터셉터)
- [ ] 토큰 만료(401) → QueuedInterceptorsWrapper가 동시 요청을 큐잉하여 갱신 한 번만 실행
- [ ] 갱신 성공 → 큐에 쌓인 요청 일괄 재시도
- [ ] 갱신 실패 → SecureStorage.deleteAll() → go_router redirect → 로그인 화면
- [ ] 앱 재시작 후 AuthNotifier.build()에서 토큰 검증 → 인증 상태 복원

### 페이지별 API 연동
- [ ] 로그인 화면: 실제 인증 성공
- [ ] 목록 화면들: 실제 데이터 렌더링
- [ ] 상세 화면들: 실제 단건 조회 동작
- [ ] 생성/수정 폼: 실제 저장 후 목록 갱신
- [ ] 삭제: 실제 삭제 후 목록 갱신

### 에러 케이스
- [ ] 401 처리: 토큰 갱신 또는 로그인 화면 이동
- [ ] 403 처리: 권한 없음 안내 메시지
- [ ] 네트워크 에러(connectionTimeout 등): 서버 연결 불가 안내 메시지

### Mock 환경 복귀 확인
- [ ] --dart-define=API_URL=http://localhost:4010 으로 변경 시 Mock 서버 정상 동작 확인
- [ ] SecureStorage.deleteAll() 후 재로그인으로 Mock 토큰 발급 확인
```

<!-- ENDIF -->

---

## 품질 기준

<!-- IF PLATFORM == REACT -->

- [ ] 모든 페이지가 실제 백엔드 API 기반으로 정상 동작
- [ ] JWT 인증 흐름 정상 (로그인 → 토큰 저장 → API 호출 → 토큰 갱신)
- [ ] CORS 에러 없음
- [ ] 401/403/네트워크 에러 각각 적절한 사용자 안내 메시지 출력
- [ ] `public/runtime-env.js` 변경만으로 Mock ↔ 실제 API 즉시 전환 가능
- [ ] `npm run build` 성공 (타입 오류·빌드 오류 없음)

<!-- ELIF PLATFORM == VUE -->

- [ ] 모든 페이지가 실제 백엔드 API 기반으로 정상 동작
- [ ] JWT 인증 흐름 정상 (로그인 → 토큰 저장 → API 호출 → 토큰 갱신)
- [ ] CORS 에러 없음
- [ ] 401/403/네트워크 에러 각각 적절한 사용자 안내 메시지 출력
- [ ] `public/runtime-env.js` 변경만으로 Mock ↔ 실제 API 즉시 전환 가능
- [ ] Pinia 상태 관리 및 Vue Router 가드 정상 동작
- [ ] `npm run build` 성공 (타입 오류·빌드 오류 없음)

<!-- ELIF PLATFORM == FLUTTER -->

- [ ] 모든 화면이 실제 백엔드 API 기반으로 정상 동작
- [ ] JWT 인증 흐름 정상 (로그인 → secure_storage 저장 → API 호출 → 토큰 갱신)
- [ ] CORS 불필요 (네이티브 앱). Android/iOS 네트워크 보안 설정 적용 완료
- [ ] 401/403/네트워크 에러 각각 적절한 사용자 안내 메시지 출력
- [ ] `web/runtime-env.js`(Web) 또는 `--dart-define`(Mobile) 전환만으로 Mock ↔ 실제 API 즉시 전환 가능
- [ ] Riverpod AuthNotifier + go_router redirect guard 정상 동작
- [ ] `flutter build apk --debug` 및 `flutter build ios --debug` 성공 (컴파일 오류 없음)

<!-- ENDIF -->

## 주의사항

<!-- IF PLATFORM == REACT -->

- **Mock 서버 코드와 설정은 삭제하지 않는다.** `docker compose --profile mock`으로 Mock 환경 복귀가 가능해야 한다.
- **CORS 문제 발생 시 프론트엔드 코드를 수정하지 않는다.** 백엔드 SecurityConfig의 `allowedOrigins`에 프론트엔드 Origin을 추가하는 것이 올바른 해결 방법이다. 개발 편의상 Vite 프록시를 사용할 수 있으나 프로덕션 CORS 설정은 반드시 백엔드에서 처리한다.
- **Mock → 실제 전환은 `public/runtime-env.js` 변경만으로 완료되어야 한다.** API 서비스 함수(`src/services/api/<domain>Service.ts`)나 React Query 훅을 수정할 필요가 없는 구조가 정상 상태다.
- 토큰 갱신 엔드포인트 경로(`/auth/refresh`)는 반드시 OpenAPI 명세와 일치해야 한다. 임의로 추정하지 않는다.
- `isRefreshing` 플래그는 동시에 여러 요청이 401을 받았을 때 토큰 갱신이 중복 실행되지 않도록 한다. 이 로직을 단순화하면 갱신 경쟁 조건이 발생할 수 있다.
- 기존 파일(`client.ts`)에 인터셉터를 추가할 때 `frontend-env-setup.md`에서 설정된 기존 로직을 덮어쓰지 않도록 주의한다.

<!-- ELIF PLATFORM == VUE -->

- **Mock 서버 코드와 설정은 삭제하지 않는다.**
- **CORS 문제 발생 시 Vue 코드를 수정하지 않는다.** 백엔드 SecurityConfig에서 Origin을 허용한다.
- **Mock → 실제 전환은 `public/runtime-env.js` 변경만으로 완료되어야 한다.**
- 토큰 갱신 엔드포인트 경로는 반드시 OpenAPI 명세와 일치해야 한다.
- Pinia 스토어의 `initialize()`는 앱 마운트 전 한 번만 호출해야 한다. 중복 호출 시 불필요한 `/auth/me` 요청이 발생한다.
- Vue Router beforeEach 가드에서 Pinia 스토어에 접근할 때 `useAuthStore()`가 `createPinia()` 이후에 호출되는지 확인한다.

<!-- ELIF PLATFORM == FLUTTER -->

- **Mock 서버 코드와 설정은 삭제하지 않는다.** `web/runtime-env.js`(Web) 또는 `--dart-define`(Mobile) 변경으로 Mock 환경 복귀가 가능해야 한다.
- **Flutter 네이티브 앱은 CORS 설정이 필요 없다.** 브라우저 Same-Origin Policy는 적용되지 않는다. 네트워크 오류 발생 시 Android cleartext / iOS ATS 설정을 먼저 확인한다.
- **에뮬레이터에서 localhost 접근**: Android 에뮬레이터는 `10.0.2.2`를, iOS Simulator는 `127.0.0.1`을 사용하여 호스트 백엔드에 접근한다.
- **`QueuedInterceptorsWrapper`는 동시 401 요청 시 갱신이 한 번만 실행되도록 보장한다.** 일반 `InterceptorsWrapper`로 교체하면 갱신 경쟁 조건이 발생할 수 있다.
- 토큰 갱신 요청은 `AuthInterceptor`가 적용된 Dio가 아닌 별도 `Dio` 인스턴스로 보내야 한다. 그렇지 않으면 갱신 요청 자체가 다시 401을 받아 무한 루프가 발생한다.
- `flutter_secure_storage`는 Android Keystore / iOS Keychain을 사용하므로 앱 삭제 시 데이터가 초기화된다. 재설치 후 토큰 없음 상태(null)로 정상 처리되는지 확인한다.
- 프로덕션 빌드에서는 Android `usesCleartextTraffic="false"`, iOS ATS 예외 제거 후 HTTPS를 사용한다.

<!-- ENDIF -->
