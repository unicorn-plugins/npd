# 프론트엔드 Mock 기반 개발 (Flutter)


## 목적

OpenAPI 명세 기반 Prism Mock 서버를 활용하여 백엔드 완성을 기다리지 않고 프론트엔드 페이지를 구현한다.
`frontend-env-setup-flutter.md`에서 구축한 프로젝트 골격 위에서 공통 컴포넌트와 페이지를 개발하고,
Mock API 연동이 완성된 상태로 실제 백엔드 전환을 준비한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 프로토타입 | `docs/plan/design/uiux/prototype/` | 화면 구조·컴포넌트 구현 기준 |
| OpenAPI 명세 | `docs/design/api/*.yaml` | Prism Mock 데이터 자동 생성 기준 |
| 종합 개발 계획서 | `docs/develop/dev-plan.md` | 페이지 우선순위(섹션 5) |
| 프론트엔드 프로젝트 골격 | `frontend/` | `frontend-env-setup-flutter.md` 산출물 |
| 행위 계약 테스트 | `test/design-contract/integration/*.spec.ts` | 프론트엔드↔백엔드 연동 시나리오 참조 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 공유 위젯 | `frontend/lib/shared/widgets/` |
| 피처별 화면 | `frontend/lib/features/<domain>/presentation/` |
| API 서비스 (Dio) | `frontend/lib/features/<domain>/data/datasources/` |
| Repository | `frontend/lib/features/<domain>/data/repositories/` |
| Riverpod Provider | `frontend/lib/features/<domain>/presentation/providers/` |
| Dart 모델 클래스 | `frontend/lib/features/<domain>/domain/models/` |

## 방법론

### 작업 순서 개요

1. 준비: 설계 문서 분석 및 Prism Mock 서버 기동 확인
2. 공통 컴포넌트/위젯 개발
3. API 서비스 함수 구현
4. 페이지별 구현 (dev-plan.md의 섹션5 참조)
5. 빌드 및 에러 해결

---

### 1단계. 준비

> **[체크포인트] 1단계 완료 조건**
> - 페이지 전수 목록 테이블 작성 완료 (1.2.1)
> - 레이아웃 그룹 분류 완료 (1.2.2)
> - Public/Protected 라우트 분류 완료 (1.2.3)
> - Prism Mock 서버 정상 기동 확인 (1.3)

#### 1.1 설계 문서 분석

아래 파일을 순서대로 읽어 전체 구조를 파악한다.

| 파일 | 파악할 내용 |
|------|-----------|
| `프로토타입(docs/plan/design/uiux/prototype/)` | 화면 목록, 컴포넌트 구성, 인터랙션, 페이지별 API 연동 포인트 |
| `docs/develop/dev-plan.md` 섹션 5 | 페이지 목록, 구현 우선순위 |
| `docs/design/api/*.yaml` | 엔드포인트, 요청/응답 스키마 |

OpenAPI 명세에서 각 엔드포인트의 응답 스키마를 파악하여 컴포넌트에 필요한 타입을 미리 정리한다.

#### 1.2 프로토타입 화면 분석

프로토타입을 playwright MCP로 각 화면을 모바일 사이즈(390×844)로 열어 확인한다.

```
구현 전 확인 항목:
- 각 화면의 레이아웃 구조 (헤더, 사이드바, 콘텐츠 영역)
- 반복 등장하는 공통 UI 패턴
- 모달, 폼, 테이블 등 복잡한 컴포넌트
```

#### 1.2.1 페이지 전수 목록 작성

프로토타입 디렉토리의 모든 HTML 파일을 열거하고, 각각을 구현 대상 페이지로 등록한다.

규칙:
- 프로토타입의 HTML 파일 1개 = 구현해야 할 페이지 1개 (예외 없음)
- `common.html`, `index.html`(목차용) 등 유틸리티 파일은 제외하되, 제외 사유를 명시
- dev-plan.md 섹션 5의 페이지 목록과 프로토타입 HTML 파일 목록을 대조하여 누락 페이지 식별

산출물:

| # | 프로토타입 HTML | 구현 페이지명 | 레이아웃 | 인증 필요 | 우선순위 |
|---|----------------|-------------|---------|----------|---------|
| 1 | login.html | LoginPage | AuthLayout | 불필요 | P1 |
| 2 | dashboard.html | DashboardPage | MainLayout | 필요 | P1 |
| ... | ... | ... | ... | ... | ... |

이 표의 모든 행이 구현 완료되어야 프론트엔드 개발이 완료된 것으로 간주한다.

#### 1.2.2 레이아웃 다양성 분석

프로토타입의 각 페이지별 레이아웃 구성 요소(헤더, 사이드바/드로어, 바텀 네비게이션, 푸터)를 분석한다.

확인 절차:
1. 각 프로토타입 페이지에서 상단(헤더/AppBar), 하단(BottomNav/Footer), 좌측(Sidebar/Drawer) 유무를 기록
2. 동일한 레이아웃 구성을 가진 페이지끼리 그룹핑
3. 서로 다른 레이아웃 그룹이 2개 이상이면 그룹별 레이아웃 컴포넌트를 생성

산출물:

| 레이아웃명 | 구성 요소 | 적용 페이지 |
|-----------|----------|-----------|
| MainLayout | Header + BottomNav + Content | Dashboard, List, Detail, ... |
| AuthLayout | Content only (centered) | Login, Register |
| PublicLayout | Header + Footer (BottomNav 없음) | 공개 프로필, ... |

MainLayout 하나만으로 모든 페이지를 커버할 수 있다고 가정하지 않는다.
프로토타입에서 레이아웃이 다른 페이지가 있으면 반드시 별도 레이아웃을 생성한다.

#### 1.2.3 라우팅 구조 분석

프로토타입의 각 페이지가 인증 필요/불필요인지 분석하여 라우팅 구조를 결정한다.

판단 기준:
- 로그인 없이 접근 가능해야 하는 페이지 → Public Route
- 로그인 후에만 접근 가능한 페이지 → Protected Route
- 프로토타입에 로그인 버튼 없이 바로 콘텐츠가 보이는 페이지 = Public
- 프로토타입의 flow-script에서 비인증 사용자가 접근하는 페이지 = Public

산출물:

| 라우트 그룹 | 페이지 | 레이아웃 |
|------------|--------|---------|
| Public Routes | Login, Register, 공개 프로필 | AuthLayout, PublicLayout |
| Protected Routes | Dashboard, List, Detail, Settings | MainLayout |

**라우팅 구조 코드 예시**:

```dart
// lib/core/router/app_router.dart
GoRouter(
  routes: [
    // Public Routes
    GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
    ShellRoute(
      builder: (_, __, child) => PublicLayout(child: child),
      routes: [
        GoRoute(path: '/profile/:nickname', builder: (_, state) => PublicProfileScreen(nickname: state.pathParameters['nickname']!)),
      ],
    ),
    // Protected Routes (redirect 로직으로 인증 체크)
    ShellRoute(
      redirect: (context, state) => isAuthenticated ? null : '/login',
      builder: (_, __, child) => MainLayout(child: child),
      routes: [
        GoRoute(path: '/dashboard', builder: (_, __) => const DashboardScreen()),
      ],
    ),
  ],
)
```

#### 1.3 Prism Mock 서버 기동 확인

`backing-service-setup.md`의 docker-compose에 `mock` 프로파일이 구성되어 있어야 한다.

```bash
# Prism Mock 서버 기동
docker compose --profile mock up -d

# 기동 확인
curl http://localhost:4010/<첫 번째 엔드포인트 경로>
```

Prism은 `docs/design/api/*.yaml` 파일을 읽어 OpenAPI 명세에 정의된 `example` 값 또는 스키마 타입 기반으로 Mock 응답을 자동 생성한다.
별도 Mock 데이터를 수동으로 작성할 필요 없다.

**프론트엔드 환경변수 확인 — MOCK == SINGLE (단일 Prism 인스턴스)**

**Flutter Web**: `frontend-env-setup-flutter.md`에서 생성된 `tools/generate-runtime-env.sh`가
Mock 단계에 적합한 `frontend/web/runtime-env.js`를 자동 생성한다.

Mock 단계에서는 모든 서비스 HOST가 Prism 서버(`http://localhost:4010`)를 가리켜야 한다.
`.env`의 `MOCK_MODE=true`(기본값)이면 `generate-runtime-env.sh`가 자동으로 모든 HOST를
`localhost:${MOCK_PORT}`(기본 4010)로 설정하므로 별도 조치 불요.

확인:

```bash
cat frontend/web/runtime-env.js
# 모든 *_HOST 값이 http://localhost:4010인지 확인
```

**Flutter Mobile (네이티브)**: `runtime-env.js`를 사용할 수 없으므로 기존 `--dart-define` 방식을 유지한다.

```bash
flutter run --dart-define=API_BASE_URL=http://localhost:4010
```

코드에서는 `RuntimeConfig` 헬퍼(`frontend-env-setup-flutter.md`에서 생성)가 Web/Mobile 분기를 자동 처리한다.

> **[DEFERRED] MOCK == MULTI**: 서비스별 Prism 인스턴스를 개별 포트에서 실행하는 멀티 Prism 패턴은 이번 범위에서 제외한다.
> MOCK == MULTI support will be added when `backing-service-setup.md` is updated to support per-service Prism instances.

#### 1.4 이미지 생성 도구

프론트엔드 구현 중 필요한 이미지(아이콘, 일러스트, 배너, 플레이스홀더 등)는 Nano Banana(Gemini) 이미지 생성 도구를 활용하여 생성한다.
`.env` 파일의 `GEMINI_API_KEY` 값을 `--api-key` 옵션에 전달한다.

```bash
# 이미지 생성 사용법
python {PLUGIN_DIR}/resources/tools/customs/general/generate_image.py \
  --prompt "생성할 이미지 설명" \
  --output-dir frontend/lib/assets/images \
  --output-name 파일명 \
  --api-key <GEMINI_API_KEY>
```

이미지가 필요한 경우(로고, 아이콘, 배경, 일러스트 등) 이 도구를 사용하여 생성한다.
외부 이미지 URL에 의존하거나 빈 placeholder를 남기지 않는다.

---

### 2단계. 공통 컴포넌트/위젯 개발

> **[체크포인트] 2단계 완료 조건**
> - 프로토타입 공통 자산 전수 추출 테이블 작성 완료
> - 공통 UI 컴포넌트/위젯 전체 구현 완료
> - 인터랙션 패턴(toggle/checkbox 등) 프로토타입 일치 확인
> - 네비게이션 라벨·아이콘·순서 프로토타입 일치 확인

#### 프로토타입 공통 자산 전수 추출

프로토타입의 공통 파일(common.js, common.css 등)을 분석하여 공통 컴포넌트/위젯 목록을 작성한다.

절차:
1. `prototype/common.js` (또는 동등 파일)에서 정의된 웹 컴포넌트(Custom Elements) 목록 추출
2. `prototype/common.css` (또는 동등 파일)에서 공통 UI 패턴(toggle switch, card, badge 등) 식별
3. 각 공통 요소를 프레임워크 컴포넌트로 매핑

산출물:

| 프로토타입 공통 요소 | 타입 | 프레임워크 컴포넌트명 | 사용 페이지 |
|-------------------|------|-------------------|-----------|
| <app-header> | Web Component | Header / AppHeader | 전체 |
| <app-nav> | Web Component | BottomNav / AppBottomNav | MainLayout 하위 |
| <app-footer> | Web Component | Footer / AppFooter | PublicLayout |
| .toggle-switch | CSS Pattern | ToggleSwitch / AppToggle | Settings |
| ... | ... | ... | ... |

이 표의 모든 항목이 구현 완료되어야 공통 컴포넌트 개발이 완료된 것으로 간주한다.
프로토타입 common 파일에 정의된 요소를 누락하면 해당 요소를 사용하는 모든 페이지에서
불일치가 발생하므로 전수 추출이 필수.

#### 2.1 컴포넌트 분류 기준

프로토타입 분석 결과를 바탕으로 컴포넌트를 분류한다.

| 분류 | 경로 | 기준 |
|------|------|------|
| 공유 위젯 (Atomic) | `lib/shared/widgets/` | 2개 이상 feature에서 재사용되는 기본 위젯 |
| 공유 레이아웃 | `lib/shared/layouts/` | 앱 전체 골격 (AppBar, BottomNav, Drawer) |
| 피처 내 공통 | `lib/features/<domain>/presentation/widgets/` | 해당 도메인 내 반복 복합 위젯 |

단일 화면에서만 쓰이는 컴포넌트/위젯은 해당 화면 폴더 안에 둔다.
공통 분리는 실제로 재사용이 확인될 때만 수행한다.

#### 2.2 UI 원자 컴포넌트/위젯

프로토타입에서 반복 등장하는 UI 요소를 구현한다.

스타일은 `ThemeData`와 `Theme.of(context)`를 통해 적용한다. 하드코딩된 색상·폰트 크기 사용을 금지한다.

```dart
// lib/shared/widgets/app_button.dart 예시
import 'package:flutter/material.dart';

enum AppButtonVariant { primary, secondary, danger }
enum AppButtonSize { sm, md, lg }

class AppButton extends StatelessWidget {
  const AppButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.variant = AppButtonVariant.primary,
    this.size = AppButtonSize.md,
    this.isLoading = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final AppButtonVariant variant;
  final AppButtonSize size;
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = switch (variant) {
      AppButtonVariant.primary   => theme.colorScheme.primary,
      AppButtonVariant.secondary => theme.colorScheme.secondary,
      AppButtonVariant.danger    => theme.colorScheme.error,
    };
    final padding = switch (size) {
      AppButtonSize.sm => const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      AppButtonSize.md => const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      AppButtonSize.lg => const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
    };

    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        padding: padding,
      ),
      onPressed: isLoading ? null : onPressed,
      child: isLoading
          ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
          : Text(label),
    );
  }
}
```

**우선 구현 대상** (프로토타입 분석 후 실제 등장하는 것만):

```
AppButton, AppTextField, AppDropdown, AppCheckbox
AppModal / AppBottomSheet
AppDataTable (정렬, 페이지네이션 포함)
AppLoadingIndicator / AppSkeleton
AppSnackBar / AppAlertDialog
AppBadge / AppTag
```

**인터랙션 패턴 정확 반영 규칙**:

프로토타입에서 사용하는 폼 요소와 인터랙션을 그대로 반영한다. 유사하지만 다른 요소로 대체하지 않는다.

| 프로토타입 요소 | 올바른 구현 | 잘못된 구현 (금지) |
|---------------|-----------|-----------------|
| Toggle Switch | ToggleSwitch 컴포넌트 | Checkbox |
| Radio Button Group | RadioGroup 컴포넌트 | Select/Dropdown |
| Range Slider | Slider 컴포넌트 | Number Input |
| Date Picker | DatePicker 컴포넌트 | Text Input |

추가 준수 사항:
- 프로토타입에 debounce가 적용된 입력 필드 → 동일한 debounce 시간(ms) 적용
- 프로토타입에 애니메이션/전환 효과 → 동일한 애니메이션 구현 (fade, slide 등)
- 프로토타입에 비활성화(disabled) 상태 표시 → 동일한 조건에서 비활성화 처리

**위젯 분류 기준 (Atomic Design 매핑)**:

| Atomic | Flutter 분류 | 예시 |
|--------|------------|------|
| Atom | `shared/widgets/` | AppButton, AppTextField |
| Molecule | `shared/widgets/` 또는 feature/widgets/ | SearchBar, FormField |
| Organism | `features/<domain>/presentation/widgets/` | UserListTile, ProductCard |

#### 2.3 레이아웃 컴포넌트/위젯

```dart
// lib/shared/layouts/main_layout.dart 예시
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class MainLayout extends StatelessWidget {
  const MainLayout({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('앱 이름'),
        actions: [/* 헤더 액션 버튼 */],
      ),
      drawer: const AppDrawer(),
      body: child,
      bottomNavigationBar: const AppBottomNavigationBar(),
    );
  }
}
```

레이아웃 구현 후 `lib/core/router/app_router.dart`의 `ShellRoute`에 등록한다.

```dart
// lib/core/router/app_router.dart 예시 (go_router ShellRoute)
ShellRoute(
  builder: (context, state, child) => MainLayout(child: child),
  routes: [
    GoRoute(path: '/users', builder: (_, __) => const UsersListScreen()),
    // 추가 라우트...
  ],
),
```

**네비게이션 라벨/아이콘 정확 반영 규칙**:

네비게이션 요소(Header, Sidebar, BottomNav, TabBar)의 라벨, 아이콘, 순서를
프로토타입과 정확히 일치시킨다.

확인 절차:
1. 프로토타입의 네비게이션에서 각 항목의 라벨 텍스트를 정확히 추출
2. 프로토타입의 네비게이션에서 각 항목의 아이콘(아이콘명 또는 SVG)을 식별
3. 항목의 표시 순서를 프로토타입과 동일하게 유지

산출물 예시:

| 위치 | 순서 | 라벨 (프로토타입 원문) | 아이콘 | 라우트 |
|------|------|---------------------|--------|--------|
| BottomNav | 1 | 홈 | home | /dashboard |
| BottomNav | 2 | 목록 | list | /items |
| BottomNav | 3 | 작성 | edit | /items/new |
| BottomNav | 4 | 프로필 | person | /profile |

라벨을 임의로 변경하지 않는다 (예: "목록"을 "TIL"로, "프로필"을 "설정"으로 변경 금지).

---

### 3단계. API 서비스 함수 구현

> **[체크포인트] 3단계 완료 조건**
> - 모든 도메인 타입/모델이 OpenAPI 스키마와 1:1 매핑 검증 완료
> - 서비스 함수가 모든 엔드포인트를 커버
> - 상태 관리 훅/스토어/프로바이더 구현 완료

`frontend-env-setup-flutter.md`에서 생성한 Dio 클라이언트를 활용하여 Repository + DataSource 패턴으로 구현한다.

#### 3.1 도메인 모델 클래스 (freezed + json_serializable)

`docs/design/api/*.yaml`의 스키마를 Dart 모델 클래스로 변환한다.

```dart
// lib/features/users/domain/models/user.dart 예시
import 'package:freezed_annotation/freezed_annotation.dart';

part 'user.freezed.dart';
part 'user.g.dart';

@freezed
class User with _$User {
  const factory User({
    required String id,
    required String name,
    required String email,
    required String role,   // 'admin' | 'member'
    required String createdAt,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}

// lib/features/users/domain/models/user_list_params.dart
class UserListParams {
  const UserListParams({this.page = 1, this.pageSize = 20, this.search});
  final int page;
  final int pageSize;
  final String? search;

  Map<String, dynamic> toQueryParameters() => {
    'page': page,
    'pageSize': pageSize,
    if (search != null) 'search': search,
  };
}
```

모델 생성 후 코드 생성을 실행한다.

```bash
dart run build_runner build --delete-conflicting-outputs
```

모델 클래스는 OpenAPI 명세의 `components/schemas`를 그대로 반영한다. 임의로 추정하지 않는다.

**모델 완전 매핑 검증 규칙**:

OpenAPI 스키마의 모든 필드가 Dart 모델 클래스(freezed)에 빠짐없이 반영되었는지 검증한다.

절차:
1. OpenAPI yaml에서 각 스키마의 필드 목록을 추출
2. freezed 모델 클래스의 필드 목록과 1:1 대조
3. 누락된 필드가 있으면 추가 (optional 필드 포함)
4. 모델에만 존재하고 OpenAPI에 없는 필드는 삭제 또는 별도 클라이언트 전용 모델로 분리

검증 산출물 (각 스키마별):

| OpenAPI 필드 | 타입 | Dart 모델 반영 여부 |
|-------------|------|-------------------|
| id | string | O |
| name | string | O |
| githubUrl | string? | X → 추가 필요 |

required/optional 구분도 OpenAPI 명세를 정확히 따른다.
OpenAPI에서 required가 아닌 필드는 Dart 모델에서도 nullable(?)로 선언한다.

#### 3.2 DataSource (Dio 기반 API 호출)

```dart
// lib/features/users/data/datasources/users_remote_datasource.dart 예시
import 'package:dio/dio.dart';
import '../../domain/models/user.dart';

class UsersRemoteDataSource {
  UsersRemoteDataSource(this._dio);
  final Dio _dio;

  Future<List<User>> getList(UserListParams params) async {
    final response = await _dio.get(
      '/users',
      queryParameters: params.toQueryParameters(),
    );
    final items = response.data['items'] as List;
    return items.map((e) => User.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<User> getById(String id) async {
    final response = await _dio.get('/users/$id');
    return User.fromJson(response.data['data'] as Map<String, dynamic>);
  }

  Future<User> create(Map<String, dynamic> data) async {
    final response = await _dio.post('/users', data: data);
    return User.fromJson(response.data['data'] as Map<String, dynamic>);
  }

  Future<User> update(String id, Map<String, dynamic> data) async {
    final response = await _dio.put('/users/$id', data: data);
    return User.fromJson(response.data['data'] as Map<String, dynamic>);
  }

  Future<void> delete(String id) async {
    await _dio.delete('/users/$id');
  }
}
```

#### 3.3 Repository 패턴

```dart
// lib/features/users/data/repositories/users_repository_impl.dart 예시
import '../../domain/models/user.dart';
import '../datasources/users_remote_datasource.dart';

abstract interface class UsersRepository {
  Future<List<User>> getList(UserListParams params);
  Future<User> getById(String id);
  Future<User> create(Map<String, dynamic> data);
  Future<User> update(String id, Map<String, dynamic> data);
  Future<void> delete(String id);
}

class UsersRepositoryImpl implements UsersRepository {
  UsersRepositoryImpl(this._dataSource);
  final UsersRemoteDataSource _dataSource;

  @override
  Future<List<User>> getList(UserListParams params) =>
      _dataSource.getList(params);

  @override
  Future<User> getById(String id) => _dataSource.getById(id);

  @override
  Future<User> create(Map<String, dynamic> data) => _dataSource.create(data);

  @override
  Future<User> update(String id, Map<String, dynamic> data) =>
      _dataSource.update(id, data);

  @override
  Future<void> delete(String id) => _dataSource.delete(id);
}
```

#### 3.4 Riverpod Provider (상태 관리)

```dart
// lib/features/users/presentation/providers/users_provider.dart 예시
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/datasources/users_remote_datasource.dart';
import '../../data/repositories/users_repository_impl.dart';
import '../../domain/models/user.dart';
import '../../../../core/network/dio_client.dart';

// DataSource Provider
final usersDataSourceProvider = Provider((ref) {
  return UsersRemoteDataSource(ref.watch(dioProvider));
});

// Repository Provider
final usersRepositoryProvider = Provider<UsersRepository>((ref) {
  return UsersRepositoryImpl(ref.watch(usersDataSourceProvider));
});

// 목록 조회 FutureProvider
final userListProvider = FutureProvider.family<List<User>, UserListParams>(
  (ref, params) => ref.watch(usersRepositoryProvider).getList(params),
);

// 단건 조회 FutureProvider
final userDetailProvider = FutureProvider.family<User, String>(
  (ref, id) => ref.watch(usersRepositoryProvider).getById(id),
);

// CRUD 뮤테이션 AsyncNotifier
class UsersNotifier extends AsyncNotifier<List<User>> {
  @override
  Future<List<User>> build() {
    return ref.watch(usersRepositoryProvider).getList(const UserListParams());
  }

  Future<void> createUser(Map<String, dynamic> data) async {
    await ref.read(usersRepositoryProvider).create(data);
    ref.invalidateSelf();  // 목록 갱신
  }

  Future<void> deleteUser(String id) async {
    await ref.read(usersRepositoryProvider).delete(id);
    ref.invalidateSelf();
  }
}

final usersNotifierProvider =
    AsyncNotifierProvider<UsersNotifier, List<User>>(UsersNotifier.new);
```

---

### 4단계. 페이지별 구현

> **[체크포인트] 4단계 완료 조건**
> - dev-plan.md 섹션 5의 모든 페이지 구현 완료
> - CRUD 수정 모드가 필요한 폼 페이지에서 Create/Update 분기 동작
> - 유저 플로우 Mock 범위 검증 통과 (4.5 산출물 기준)
> - Prism Mock 연동 확인 완료 (4.3)

#### 4.1 구현 순서 결정

`docs/develop/dev-plan.md` 섹션 5의 우선순위를 기준으로 구현 순서를 정한다.

```
구현 순서 원칙:
1. `dev-plan.md`의 '5. 프론트엔드 범위'의 우선순위대로 개발
동일 우선순위 내에서는 프로토타입의 화면 목록 순서를 따른다.
```

구현 전 각 페이지에 대해 아래를 확인한다.

| 확인 항목 | 참조 파일 |
|----------|---------|
| 이 페이지의 설명 | `docs/develop/dev-plan.md` 섹션 5 |
| 사용하는 API 엔드포인트 | `docs/design/api/*.yaml` |
| 화면 구성 및 인터랙션 | `프로토타입(docs/plan/design/uiux/prototype/)` |
| 요청/응답 스키마 | `docs/design/api/*.yaml` |

#### 4.2 페이지/화면 구현 패턴

Flutter 화면은 `ConsumerWidget` 또는 `ConsumerStatefulWidget`을 기본으로 한다.
`go_router`로 라우팅하며 `ShellRoute`의 `MainLayout`에 자동으로 포함된다.

```dart
// lib/features/users/presentation/screens/users_list_screen.dart 예시
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/users_provider.dart';
import '../../domain/models/user.dart';
import '../../../../shared/widgets/app_loading_indicator.dart';

class UsersListScreen extends ConsumerWidget {
  const UsersListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncUsers = ref.watch(usersNotifierProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('사용자 목록')),
      body: asyncUsers.when(
        loading: () => const AppLoadingIndicator(),
        error: (e, _) => Center(child: Text('데이터를 불러올 수 없습니다: $e')),
        data: (users) => ListView.builder(
          itemCount: users.length,
          itemBuilder: (context, index) {
            final user = users[index];
            return ListTile(
              title: Text(user.name),
              subtitle: Text(user.email),
              trailing: Text(user.role),
              onTap: () => context.go('/users/${user.id}'),
            );
          },
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/users/new'),
        child: const Icon(Icons.add),
      ),
    );
  }
}
```

화면 구현 후 `lib/core/router/app_router.dart`의 `ShellRoute.routes`에 `GoRoute`를 추가한다.

```dart
GoRoute(
  path: '/users',
  builder: (_, __) => const UsersListScreen(),
  routes: [
    GoRoute(
      path: ':id',
      builder: (_, state) => UserDetailScreen(id: state.pathParameters['id']!),
    ),
    GoRoute(
      path: 'new',
      builder: (_, __) => const UserFormScreen(),
    ),
  ],
),
```

**CRUD 수정(Edit) 모드 구현 규칙**:

프로토타입에서 "수정" 버튼이나 편집 기능이 있는 페이지는,
작성(Create) 폼을 재사용하여 수정(Update) 모드를 구현한다.

패턴:
1. 상세 페이지에 수정 버튼이 있는지 프로토타입에서 확인
2. 수정 버튼 클릭 시 작성 폼 페이지로 이동하되, 기존 데이터를 로드
3. 폼 페이지는 "생성 모드"(새 데이터)와 "수정 모드"(기존 데이터 편집)를 구분
4. 수정 모드에서는 기존 데이터를 API로 조회하여 폼 필드에 채움

```dart
// lib/features/items/presentation/screens/item_form_screen.dart
class ItemFormScreen extends ConsumerStatefulWidget {
  const ItemFormScreen({super.key, this.editId});
  final String? editId;

  @override
  ConsumerState<ItemFormScreen> createState() => _ItemFormScreenState();
}

class _ItemFormScreenState extends ConsumerState<ItemFormScreen> {
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  bool get isEditMode => widget.editId != null;

  @override
  void initState() {
    super.initState();
    if (isEditMode) {
      // 수정 모드: 기존 데이터를 로드하여 폼 필드에 채움
      ref.listenManual(
        itemDetailProvider(widget.editId!),
        (_, next) => next.whenData((item) {
          _titleController.text = item.title;
          _contentController.text = item.content;
        }),
      );
    }
  }

  Future<void> _handleSubmit() async {
    final data = {'title': _titleController.text, 'content': _contentController.text};
    final notifier = ref.read(itemsNotifierProvider.notifier);
    if (isEditMode) {
      await notifier.updateItem(widget.editId!, data);
    } else {
      await notifier.createItem(data);
    }
    if (mounted) context.go('/items');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(isEditMode ? '수정' : '작성')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          AppTextField(controller: _titleController, label: '제목'),
          AppTextField(controller: _contentController, label: '내용'),
          AppButton(label: isEditMode ? '수정' : '작성', onPressed: _handleSubmit),
        ]),
      ),
    );
  }

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    super.dispose();
  }
}
```

**go_router에서 editId 전달**:

```dart
// lib/core/router/app_router.dart
GoRoute(
  path: '/items/new',
  builder: (_, __) => const ItemFormScreen(),
),
GoRoute(
  path: '/items/:id/edit',
  builder: (_, state) => ItemFormScreen(editId: state.pathParameters['id']),
),
```

#### 4.3 Prism Mock 연동 확인

각 페이지/화면 구현 완료 후 확인한다.

```
확인 항목:
- flutter run 시 콘솔에서 요청 URL이 http://localhost:4010 으로 출력되는지
  (Dio interceptor 로그 또는 flutter_inspector 활용)
- 응답 상태 코드가 200인지 (Dio 인터셉터에서 로깅)
- 화면에 데이터가 정상 표시되는지
- 콘솔(flutter logs)에 에러가 없는지
```

#### 4.4 Prism 한계와 stub 데이터 보완

Prism은 stateless(상태 비보존)이므로 아래 시나리오는 동작하지 않는다.

| 시나리오 | 문제 | 보완 방법 |
|----------|------|---------|
| 생성 후 목록 즉시 반영 | Prism은 POST를 받아도 GET 응답이 변하지 않음 | `UsersNotifier.createUser()` 내 `ref.invalidateSelf()` 호출 |
| 로그인 후 토큰 유지 | Prism은 인증 상태를 저장하지 않음 | 로그인 응답의 mock 토큰을 `flutter_secure_storage`에 수동 저장하는 stub 로직 추가 |
| 삭제 후 목록 갱신 | 동일 | `deleteUser()` 내 `ref.invalidateSelf()` 호출 |
| 복잡한 필터/정렬 결과 | Prism은 쿼리 파라미터를 무시 | Provider에서 클라이언트 사이드 필터링 임시 구현 |

stub 데이터는 `lib/core/stubs/` 폴더에 모아 실제 API 전환 시 일괄 제거한다.

> **소셜 로그인(OAuth) 구현 시**: Mobile(Custom URL Scheme)과 Web(브라우저 리다이렉트) 방식이 다름.
> 전체 구현 패턴(AuthService, AndroidManifest, Info.plist 등)은 `{PLUGIN_DIR}/resources/guides/develop/oauth-guide.md` 섹션 4-3 참조.

```dart
// lib/core/stubs/auth_stub.dart 예시
// 실제 백엔드 전환 시 이 파일 삭제
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthStub {
  static const _storage = FlutterSecureStorage();

  static Future<void> saveMockToken() async {
    await _storage.write(
      key: 'auth_token',
      value: 'mock-jwt-token-for-development',
    );
  }
}
```

#### 4.5 유저 플로우 Mock 범위 검증

프로토타입에 flow-script(유저 플로우 정의)가 있으면, Mock 범위 내에서
UI 네비게이션 경로가 정상 동작하는지 검증한다.

> Prism은 stateless Mock 서버이므로 진정한 End-to-End 검증
> (인증 기반 접근 제어, 상태 의존 분기 등)은 불가능하다.
> 이 단계의 "유저 플로우 검증"은 **Mock 범위 내에서의 UI 네비게이션 경로 검증**으로 한정한다.

절차:
1. 프로토타입의 flow-script 파일(flow-script.html 등)을 분석하여 유저 여정 목록 추출
2. 각 여정의 시작 페이지 → 경유 페이지 → 종료 페이지 경로를 기록
3. 구현된 앱에서 각 여정을 순서대로 수행하며 페이지 전환이 정상 동작하는지 확인

산출물:

| 여정 # | 시작 | 경유 | 종료 | 검증 결과 |
|--------|------|------|------|----------|
| 1 | Login | → Dashboard | → Item Detail | Pass/Fail |
| 2 | Dashboard | → Settings | → Edit Profile | Pass/Fail |
| ... | ... | ... | ... | ... |

검증 항목 (각 여정별, Mock 범위):
- [ ] 시작 페이지에서 다음 페이지로의 네비게이션 링크/버튼 존재
- [ ] 각 경유 페이지가 정상 렌더링 (Mock 데이터 기준)
- [ ] 라우트 전환이 정상 동작 (페이지 컴포넌트가 렌더링됨)
- [ ] 뒤로 가기(Back) 시 이전 페이지로 복귀

검증 제외 항목 (실제 백엔드 통합 시 검증):
- 인증 기반 접근 제어 (미인증 시 리디렉트)
- 상태 의존 UI 분기 (데이터 유무에 따른 빈 상태/목록 표시)
- CRUD 후 목록 갱신 반영 (Prism stateless 제약)

flow-script가 없는 프로토타입의 경우, 프로토타입 페이지 간 링크/버튼을 추적하여
주요 유저 여정을 도출한다.

---

### 5단계. 빌드 및 에러 해결

페이지/화면 구현이 모두 완료되면 빌드를 실행하여 타입 오류·빌드 오류를 해결한다.

```bash
cd frontend

# 정적 분석 (타입·린트 오류 확인)
flutter analyze

# 코드 생성 산출물 갱신 (freezed, json_serializable)
dart run build_runner build --delete-conflicting-outputs

# 앱 빌드 검증
# Android
flutter build apk --dart-define=API_BASE_URL=http://localhost:4010
# iOS (macOS에서만)
flutter build ios --dart-define=API_BASE_URL=http://localhost:4010
# Web (웹 지원 시)
flutter build web --dart-define=API_BASE_URL=http://localhost:4010
```

`flutter analyze` 결과에 오류가 없어야 한다. 경고(warning)는 허용하지 않는다 (품질 기준 참조).

---

## 출력 형식

### 폴더 구조

```
frontend/lib/
├── core/
│   ├── config/
│   │   └── app_config.dart       # AppConfig.apiBaseUrl 등 환경 설정
│   ├── network/
│   │   └── dio_client.dart       # (frontend-env-setup-flutter.md 산출물, 수정 금지)
│   ├── router/
│   │   └── app_router.dart       # go_router 설정 (ShellRoute 포함)
│   └── stubs/                    # Prism 한계 보완용 (실제 전환 시 삭제)
│       └── auth_stub.dart
├── shared/
│   ├── widgets/                  # 2개 이상 feature에서 재사용되는 공유 위젯
│   │   ├── app_button.dart
│   │   ├── app_text_field.dart
│   │   ├── app_loading_indicator.dart
│   │   ├── app_data_table.dart
│   │   └── ...
│   └── layouts/
│       └── main_layout.dart      # ShellRoute 레이아웃
└── features/
    └── <domain>/
        ├── domain/
        │   └── models/
        │       └── <domain_model>.dart   # freezed 모델
        ├── data/
        │   ├── datasources/
        │   │   └── <domain>_remote_datasource.dart
        │   └── repositories/
        │       └── <domain>_repository_impl.dart
        └── presentation/
            ├── screens/
            │   ├── <domain>_list_screen.dart
            │   ├── <domain>_detail_screen.dart
            │   └── <domain>_form_screen.dart
            ├── providers/
            │   └── <domain>_provider.dart   # Riverpod Provider
            └── widgets/                     # 해당 도메인 전용 복합 위젯
```

### 페이지별 구현 체크리스트 템플릿

각 페이지/화면 구현 시 아래 체크리스트를 사용한다.

```
## 화면명: _______________

### 준비
- [ ] 우선순위 확인 (dev-plan.md 섹션 5)
- [ ] API 엔드포인트 확인 (OpenAPI yaml)
- [ ] 화면 구성 확인 (프로토타입)
- [ ] 요청/응답 스키마 확인 (OpenAPI yaml)
- [ ] 프로토타입 화면 확인 (playwright — 모바일 사이즈 390×844)
- [ ] 이 화면의 레이아웃 그룹 확인 (1.2.2 산출물)
- [ ] 이 화면의 라우트 그룹 확인 (Public/Protected)
- [ ] 수정 모드 필요 여부 확인 (상세→수정 버튼 유무)

### 구현
- [ ] Dart 모델 클래스 생성 (lib/features/<domain>/domain/models/)
- [ ] dart run build_runner build 실행 (freezed/json_serializable 코드 생성)
- [ ] DataSource 구현 (lib/features/<domain>/data/datasources/)
- [ ] Repository 구현 (lib/features/<domain>/data/repositories/)
- [ ] Riverpod Provider 구현 (lib/features/<domain>/presentation/providers/)
- [ ] Screen 위젯 구현 (lib/features/<domain>/presentation/screens/)
- [ ] go_router에 라우트 등록 (lib/core/router/app_router.dart)

### 검증
- [ ] flutter analyze 오류 없음
- [ ] Prism Mock 서버 응답 확인 (Dio 로그 or flutter_inspector, http://localhost:4010)
- [ ] 화면 정상 렌더링 확인
- [ ] flutter logs에 에러 없음
- [ ] 프로토타입 화면과 일치 확인 (모바일/태블릿)
- [ ] 인터랙션 패턴 일치 확인 (toggle/checkbox 등)
- [ ] 네비게이션 라벨/아이콘 프로토타입 일치 확인
- [ ] API 응답 모델의 모든 필드가 UI에 반영되는지 확인
```

---

## 품질 기준

- [ ] 모든 화면이 Prism Mock API(localhost:4010) 기반으로 정상 동작
- [ ] DataSource의 엔드포인트가 `API 설계서(docs/design/api/*.yaml)`와 정확히 일치
- [ ] `web/runtime-env.js`(Web) 또는 `--dart-define`(Mobile) 변경만으로 Mock → 실제 서버 전환 가능한 구조
- [ ] `flutter analyze` 결과 오류(error) 0건, 경고(warning) 0건
- [ ] `dart run build_runner build` 성공 (freezed/json_serializable 코드 최신 상태)
- [ ] `flutter build apk` (또는 대상 플랫폼 빌드) 성공
- [ ] ThemeData 기반 스타일링 (하드코딩된 색상·폰트 크기 없음)
  → 검증 방법: 아래 ThemeData 하드코딩 검증 절차 참조
- [ ] Prism stub 데이터가 `lib/core/stubs/`에 분리됨
- [ ] dev-plan.md 섹션 5의 페이지 전체 구현
- [ ] **TODO/FIXME/HACK 0건**: `grep -rn "TODO\|FIXME\|HACK" frontend/lib/` 결과가 0건
- [ ] **런타임 동작 확인**: `flutter run -d chrome --web-port 3000` 실행 후 주요 화면 접근 및 Mock API 호출 정상 동작
- [ ] 프로토타입 HTML 파일 전수가 화면으로 구현됨 (1.2.1 산출물 테이블 기준)
- [ ] 프로토타입과 다른 레이아웃이 필요한 화면에 별도 레이아웃 적용 (1.2.2 산출물 기준)
- [ ] Public/Protected 라우트 구분이 프로토타입 분석 결과와 일치 (1.2.3 산출물 기준)
- [ ] 프로토타입 common 파일의 모든 공통 요소가 위젯으로 구현됨 (공통 자산 전수 추출 산출물 기준)
- [ ] OpenAPI 스키마의 모든 필드가 Dart 모델 클래스에 반영됨 (3.1 검증 산출물 기준)
- [ ] 네비게이션(BottomNav/AppBar/Drawer) 라벨·아이콘이 프로토타입과 일치
- [ ] 프로토타입의 인터랙션 패턴(toggle/checkbox/radio 구분, debounce 등)이 정확히 반영됨
- [ ] CRUD 수정 모드가 필요한 폼 화면에서 기존 데이터 로드 및 업데이트 정상 동작
- [ ] 유저 플로우 Mock 범위 검증 통과 (4.5 산출물 기준)

**ThemeData 하드코딩 검증 절차** (빌드 성공 후 실행):

```bash
# 하드코딩된 색상값이 theme 접근 없이 직접 사용되는지 검증
grep -rn 'Color(0x\|Colors\.' frontend/lib/ | grep -v 'theme\|Theme' | grep -v 'test/'
# 결과가 0건이어야 함
```

> **참고**: `Color(0x` 패턴의 괄호는 쉘에서 이스케이프가 필요할 수 있음.
> `grep -rn 'Color\(0x' ...` 형태로 실행 환경에 따라 조정.

## 주의사항

- **TODO/FIXME/HACK 금지**: 모든 코드는 완전하게 구현한다. "TODO: 나중에 구현", "FIXME: 임시 처리" 등의 미완성 마커를 남기지 않는다. 구현이 어려운 부분이 있으면 우회하지 말고 근본 원인을 해결한다.
- **런타임 에러 워크어라운드 금지**: 런타임 에러 발생 시 콘솔 에러를 무시하거나, 기능을 비활성화하거나, 하드코딩 값으로 대체하는 등의 우회 해결을 금지한다. 반드시 근본 원인을 분석하고 정상 동작하도록 수정한다.
- **런타임 동작 검증 필수**: 빌드 성공만으로는 완료가 아니다. 개발 서버를 실행하여 브라우저에서 주요 페이지가 오류 없이 동작하고, Mock API 호출이 정상 반환되는지 확인해야 한다.
- **Prism Mock 서버는 `docker compose --profile mock up -d`로 기동한다.** 직접 Prism을 설치하거나 별도 실행하지 않는다.
- **DataSource를 Screen/Widget에서 직접 호출하지 않는다.** 반드시 Riverpod Provider → Repository → DataSource 계층을 통해 사용한다. 이 구조가 Mock → 실제 전환 시 변경 범위를 최소화한다.
- `freezed`/`json_serializable` 모델을 수정하면 반드시 `dart run build_runner build`를 재실행한다.
- Prism이 OpenAPI 명세의 `example` 값을 우선 반환하므로, 명세의 `example`을 보강하면 Mock 품질이 향상된다.
- `frontend-env-setup-flutter.md`에서 생성한 `dio_client.dart`는 이 단계에서 수정하지 않는다. API URL 변경은 `web/runtime-env.js`(Web) 또는 `--dart-define`(Mobile)으로 처리한다.
- 프로토타입 화면 분석은 playwright MCP를 이용하여 모바일 사이즈(390×844)로 확인한다.
- stub 데이터는 실제 API 전환 시 전량 제거 대상이다. `lib/core/stubs/` 폴더에 격리한다.
