# 프론트엔드 프로젝트 초기화 가이드 (Flutter)

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
| 테마 시스템 | `frontend/lib/core/theme/` |
| 라우팅 설정 | `frontend/lib/routing/` |
| 상태 관리 Provider | `frontend/lib/features/` |
| API 클라이언트 | `frontend/lib/core/network/` |
| 의존성 명세 | `frontend/pubspec.yaml` |

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

**FLUTTER 선택 시 추가 기술스택 기준:**

| 항목 | 기준 후보 | 비고 |
|------|----------|------|
| 언어 | Dart | 고정 |
| 라우팅 | go_router | 기본 권장 |
| 상태 관리 | Riverpod | 기본 권장 |
| HTTP 클라이언트 | Dio | 기본 권장 |
| 토큰 저장 | flutter_secure_storage | localStorage 사용 불가 |
| 코드 생성 | build_runner + freezed | 기본 권장 |

기술스택이 결정되면 사용자에게 확인을 받고 다음 단계로 진행한다.

---

### 2단계. 프로젝트 생성 및 폴더 구조 설정

#### 2.1 프로젝트 생성

기존 `frontend/` 디렉토리가 있으면 그대로 유지하면서 작업한다.
없으면 선택한 플랫폼에 따라 생성한다.

```bash
# Flutter 프로젝트 생성
# {ORG}: 조직 식별자 (예: com.example), {PROJECT_NAME}: 프로젝트명 (예: myapp)
flutter create --org {ORG} --project-name {PROJECT_NAME} frontend
```

#### 2.2 폴더 구조 생성

`프로토타입`의 메뉴 및 화면 계층을 기반으로 폴더를 구성한다.

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

#### 2.3 설정 파일 생성

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

---

### 3단계. 의존성 설치

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

---

### 4단계. 스타일 시스템 구축

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

---

### 5단계. 라우팅 시스템 구축

`프로토타입`의 메뉴 계층과 화면 목록을 기반으로 라우트를 정의한다.

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

---

### 6단계. 상태 관리 시스템 구축

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

---

### 7단계. API 클라이언트 기본 설정

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

---

### 8단계. 실행 확인

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

---

## 출력 형식

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

## 품질 기준

- [ ] 정보아키텍처(`ia.md`) 기반 feature 폴더 구조와 GoRoute 정의
- [ ] `ThemeData`가 `style-guide.md`의 컬러·타이포그래피 값과 일치
- [ ] Dio baseURL이 `web/runtime-env.js`(Web) 또는 `--dart-define`(Mobile)으로 관리됨 (하드코딩 없음)
- [ ] `flutter_secure_storage`로 토큰 저장 (localStorage 미사용)
- [ ] `flutter analyze` 오류 없음
- [ ] `flutter run --web-port 3000` 성공 및 기본 화면 표시 확인
- [ ] `flutter build apk --debug` 성공 (빌드 오류 없음)
- [ ] 화면 Widget 미구현 (placeholder Text만 존재)

## 주의사항

- **이 단계에서 화면 Widget을 구현하지 않는다.** 기반 시스템(테마·라우팅·상태관리·API 클라이언트) 골격만 완성한다.
- Flutter에서는 `localStorage`를 사용할 수 없다. 토큰 등 민감한 데이터는 반드시 `flutter_secure_storage`를 사용한다.
- `ThemeData` 값을 임의로 추정하지 않는다. 반드시 `style-guide.md`에서 확인한 값을 사용한다.
- `pubspec.yaml`의 의존성 버전은 최신 호환 버전을 확인 후 입력한다. `flutter pub outdated`로 최신 버전 확인 가능.
- `build_runner`를 사용하는 경우 코드 생성 명령을 실행한다: `dart run build_runner build --delete-conflicting-outputs`
- 기존 `frontend/` 디렉토리가 있는 경우 기존 파일을 삭제하거나 덮어쓰지 않는다. 충돌 여부를 먼저 확인한다.
- `.env` 파일은 gitignore에 포함시키고, `.env.example`만 커밋한다.
- 프로토타입 화면 분석이 필요한 경우 playwright MCP 도구를 활용하여 모바일 사이즈(예: 390×844)로 확인한다.
