# 프론트엔드 개발 가이드

> **플랫폼 참조**: 이 가이드는 `frontend-env-setup.md`에서 결정된 `{PLATFORM}` 값을 기준으로 분기한다.
> `{PLATFORM}` 값은 `REACT` / `VUE` / `FLUTTER` 중 하나이며, 각 단계의 코드 예시는 해당 플랫폼 블록만 적용한다.

## 목적

OpenAPI 명세 기반 Prism Mock 서버를 활용하여 백엔드 완성을 기다리지 않고 프론트엔드 페이지를 구현한다.
`frontend-env-setup.md`에서 구축한 프로젝트 골격 위에서 공통 컴포넌트와 페이지를 개발하고,
Mock API 연동이 완성된 상태로 실제 백엔드 전환을 준비한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| OpenAPI 명세 | `docs/design/api/*.yaml` | Prism Mock 데이터 자동 생성 기준 |
| UI/UX 설계서 | `docs/design/frontend/uiux-design.md` | 화면 구조·컴포넌트 구현 기준 |
| API 매핑설계서 | `docs/design/frontend/api-mapping.md` | 페이지-API 연동 기준 |
| 유저스토리 | `docs/plan/design/userstory.md` | 페이지 구현 우선순위 결정 |
| 프론트엔드 프로젝트 골격 | `frontend/` | `frontend-env-setup.md` 산출물 |

## 출력 (이 단계 산출물)

<!-- IF PLATFORM == REACT -->
| 산출물 | 파일 경로 |
|--------|----------|
| 공통 컴포넌트 | `frontend/src/components/` |
| 레이아웃 컴포넌트 | `frontend/src/layouts/` |
| API 서비스 함수 | `frontend/src/services/api/` |
| React Query 훅 | `frontend/src/hooks/` |
| 페이지 컴포넌트 | `frontend/src/pages/` |
<!-- ELIF PLATFORM == VUE -->
| 산출물 | 파일 경로 |
|--------|----------|
| 공통 컴포넌트 | `frontend/src/components/` |
| 레이아웃 컴포넌트 | `frontend/src/layouts/` |
| API 서비스 함수 | `frontend/src/services/api/` |
| Pinia 스토어 | `frontend/src/stores/` |
| 페이지 컴포넌트 | `frontend/src/views/` |
<!-- ELIF PLATFORM == FLUTTER -->
| 산출물 | 파일 경로 |
|--------|----------|
| 공유 위젯 | `frontend/lib/shared/widgets/` |
| 피처별 화면 | `frontend/lib/features/<domain>/presentation/` |
| API 서비스 (Dio) | `frontend/lib/features/<domain>/data/datasources/` |
| Repository | `frontend/lib/features/<domain>/data/repositories/` |
| Riverpod Provider | `frontend/lib/features/<domain>/presentation/providers/` |
| Dart 모델 클래스 | `frontend/lib/features/<domain>/domain/models/` |
<!-- ENDIF -->

## 방법론

### 작업 순서 개요

1. 준비: 설계 문서 분석 및 Prism Mock 서버 기동 확인
2. 공통 컴포넌트/위젯 개발
3. 페이지별 구현 (유저스토리 우선순위 순)
4. 빌드 및 에러 해결

---

### 1단계. 준비

#### 1.1 설계 문서 분석

아래 파일을 순서대로 읽어 전체 구조를 파악한다.

| 파일 | 파악할 내용 |
|------|-----------|
| `docs/design/frontend/uiux-design.md` | 화면 목록, 컴포넌트 구성, 인터랙션 |
| `docs/design/frontend/api-mapping.md` | 페이지별 사용 API 엔드포인트 |
| `docs/plan/design/userstory.md` | Must Have / Should Have 우선순위 |
| `docs/design/api/*.yaml` | 엔드포인트, 요청/응답 스키마 |

OpenAPI 명세에서 각 엔드포인트의 응답 스키마를 파악하여 컴포넌트에 필요한 타입을 미리 정리한다.

#### 1.2 프로토타입 화면 분석

UI/UX 설계서에 프로토타입 URL이 있으면 playwright MCP로 각 화면을 모바일 사이즈(390×844)로 열어 확인한다.

```
구현 전 확인 항목:
- 각 화면의 레이아웃 구조 (헤더, 사이드바, 콘텐츠 영역)
- 반복 등장하는 공통 UI 패턴
- 모달, 폼, 테이블 등 복잡한 컴포넌트
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

<!-- IF PLATFORM == REACT -->
`frontend/public/runtime-env.js`에 아래 설정이 있는지 확인한다.

```javascript
// public/runtime-env.js (Mock 단계)
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:4010",
  ORDER_HOST: "http://localhost:4010",
  // ... Prism이 모든 API를 대리하므로 동일 포트
};
```

`frontend-env-setup.md`에서 이미 생성되었다면 그대로 사용한다.
단일 Prism 서버(SINGLE)를 사용하므로 모든 서비스 HOST를 `http://localhost:4010`으로 설정한다.
<!-- ELIF PLATFORM == VUE -->
`frontend/public/runtime-env.js`에 아래 설정이 있는지 확인한다.

```javascript
// public/runtime-env.js (Mock 단계)
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:4010",
  ORDER_HOST: "http://localhost:4010",
  // ... Prism이 모든 API를 대리하므로 동일 포트
};
```

`frontend-env-setup.md`에서 이미 생성되었다면 그대로 사용한다.
<!-- ELIF PLATFORM == FLUTTER -->
**Flutter Web**: `web/runtime-env.js`에 아래 설정이 있는지 확인한다.

```javascript
// web/runtime-env.js (Mock 단계)
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://localhost:4010",
  ORDER_HOST: "http://localhost:4010",
  // ... Prism이 모든 API를 대리하므로 동일 포트
};
```

`frontend-env-setup.md`에서 이미 생성되었다면 그대로 사용한다.

**Flutter Mobile (네이티브)**: `runtime-env.js`를 사용할 수 없으므로 기존 `--dart-define` 방식을 유지한다.

```bash
flutter run --dart-define=API_BASE_URL=http://localhost:4010
```

코드에서는 `RuntimeConfig` 헬퍼(`frontend-env-setup.md`에서 생성)가 Web/Mobile 분기를 자동 처리한다.
<!-- ENDIF -->

> **[DEFERRED] MOCK == MULTI**: 서비스별 Prism 인스턴스를 개별 포트에서 실행하는 멀티 Prism 패턴은 이번 범위에서 제외한다.
> MOCK == MULTI support will be added when `backing-service-setup.md` is updated to support per-service Prism instances.

---

### 2단계. 공통 컴포넌트/위젯 개발

#### 2.1 컴포넌트 분류 기준

UI/UX 설계서와 프로토타입 분석 결과를 바탕으로 컴포넌트를 분류한다.

<!-- IF PLATFORM == REACT -->
| 분류 | 경로 | 기준 |
|------|------|------|
| UI 원자 컴포넌트 | `src/components/common/` | 2개 이상 화면에서 재사용되는 범용 UI |
| 레이아웃 | `src/layouts/` | 페이지 골격 (헤더, 사이드바, 푸터) |
| 도메인 공통 | `src/components/<domain>/` | 특정 도메인에서 반복되는 복합 컴포넌트 |
<!-- ELIF PLATFORM == VUE -->
| 분류 | 경로 | 기준 |
|------|------|------|
| UI 원자 컴포넌트 | `src/components/common/` | 2개 이상 화면에서 재사용되는 범용 UI |
| 레이아웃 | `src/layouts/` | 페이지 골격 (헤더, 사이드바, 푸터) |
| 도메인 공통 | `src/components/<domain>/` | 특정 도메인에서 반복되는 복합 컴포넌트 |
<!-- ELIF PLATFORM == FLUTTER -->
| 분류 | 경로 | 기준 |
|------|------|------|
| 공유 위젯 (Atomic) | `lib/shared/widgets/` | 2개 이상 feature에서 재사용되는 기본 위젯 |
| 공유 레이아웃 | `lib/shared/layouts/` | 앱 전체 골격 (AppBar, BottomNav, Drawer) |
| 피처 내 공통 | `lib/features/<domain>/presentation/widgets/` | 해당 도메인 내 반복 복합 위젯 |
<!-- ENDIF -->

단일 화면에서만 쓰이는 컴포넌트/위젯은 해당 화면 폴더 안에 둔다.
공통 분리는 실제로 재사용이 확인될 때만 수행한다.

#### 2.2 UI 원자 컴포넌트/위젯

프로토타입에서 반복 등장하는 UI 요소를 구현한다.

<!-- IF PLATFORM == REACT -->
스타일은 반드시 `style-guide.md` 기반 CSS 변수를 사용한다.

```typescript
// src/components/common/Button.tsx 예시
import styles from './Button.module.css'

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
  children: React.ReactNode
}

export default function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  onClick,
  children,
}: ButtonProps) {
  return (
    <button
      className={`${styles.button} ${styles[variant]} ${styles[size]}`}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading ? <span className={styles.spinner} /> : children}
    </button>
  )
}
```

**우선 구현 대상** (프로토타입 분석 후 실제 등장하는 것만):

```
Button, Input, Select, Checkbox, Radio
Modal / Dialog
Table (정렬, 페이지네이션 포함)
Loading / Skeleton
Toast / Alert
Badge / Tag
```
<!-- ELIF PLATFORM == VUE -->
스타일은 반드시 `style-guide.md` 기반 CSS 변수를 사용한다. `<style scoped>` + CSS 변수 조합을 표준으로 한다.

```vue
<!-- src/components/common/AppButton.vue 예시 -->
<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
})

defineEmits<{ click: [] }>()
</script>

<template>
  <button
    :class="['btn', `btn--${variant}`, `btn--${size}`]"
    :disabled="disabled || loading"
    @click="$emit('click')"
  >
    <span v-if="loading" class="spinner" />
    <slot v-else />
  </button>
</template>

<style scoped>
.btn { /* CSS 변수 기반 스타일 */ }
</style>
```

**우선 구현 대상** (프로토타입 분석 후 실제 등장하는 것만):

```
AppButton, AppInput, AppSelect, AppCheckbox
AppModal / AppDialog
AppTable (정렬, 페이지네이션 포함)
AppLoading / AppSkeleton
AppToast / AppAlert
AppBadge / AppTag
```
<!-- ELIF PLATFORM == FLUTTER -->
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

**위젯 분류 기준 (Atomic Design 매핑)**:

| Atomic | Flutter 분류 | 예시 |
|--------|------------|------|
| Atom | `shared/widgets/` | AppButton, AppTextField |
| Molecule | `shared/widgets/` 또는 feature/widgets/ | SearchBar, FormField |
| Organism | `features/<domain>/presentation/widgets/` | UserListTile, ProductCard |
<!-- ENDIF -->

#### 2.3 레이아웃 컴포넌트/위젯

UI/UX 설계서의 레이아웃 구조를 기반으로 구현한다.

<!-- IF PLATFORM == REACT -->
```typescript
// src/layouts/MainLayout.tsx 예시
import { Outlet } from 'react-router-dom'
import Header from '@/components/common/Header'
import Sidebar from '@/components/common/Sidebar'
import styles from './MainLayout.module.css'

export default function MainLayout() {
  return (
    <div className={styles.layout}>
      <Header />
      <div className={styles.body}>
        <Sidebar />
        <main className={styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

레이아웃 구현 후 `src/router/index.tsx`에서 페이지 라우트를 레이아웃으로 감싼다.
<!-- ELIF PLATFORM == VUE -->
```vue
<!-- src/layouts/MainLayout.vue 예시 -->
<script setup lang="ts">
import AppHeader from '@/components/common/AppHeader.vue'
import AppSidebar from '@/components/common/AppSidebar.vue'
</script>

<template>
  <div class="layout">
    <AppHeader />
    <div class="layout__body">
      <AppSidebar />
      <main class="layout__content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
```

레이아웃 구현 후 `src/router/index.ts`에서 페이지 라우트를 레이아웃으로 감싼다.
<!-- ELIF PLATFORM == FLUTTER -->
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
<!-- ENDIF -->

---

### 3단계. API 서비스 함수 구현

<!-- IF PLATFORM == REACT -->
`frontend-env-setup.md`에서 생성한 `src/services/api/client.ts`의 axios 인스턴스를 활용하여
도메인별 서비스 함수를 구현한다.

#### 3.1 도메인 타입 정의

`docs/design/api/*.yaml`의 스키마를 TypeScript 인터페이스로 변환한다.

```typescript
// src/types/<domain>.ts 예시 (users 도메인)
export interface User {
  id: string
  name: string
  email: string
  role: 'admin' | 'member'
  createdAt: string
}

export interface CreateUserRequest {
  name: string
  email: string
  role: 'admin' | 'member'
}

export interface UserListParams {
  page?: number
  pageSize?: number
  search?: string
}
```

타입은 OpenAPI 명세의 `components/schemas`를 그대로 반영한다. 임의로 추정하지 않는다.

#### 3.2 서비스 함수 패턴

**런타임 설정 분기 구조**: `public/runtime-env.js`의 서비스별 HOST만 변경하면 Mock → 실제 서버 전환이 완료된다.
서비스 함수 자체는 변경하지 않아도 된다. API 클라이언트는 `getRuntimeConfig()`에서 서비스별 HOST를 읽는다.

```typescript
// src/services/api/usersService.ts 예시
import { apiClient } from './client'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type { User, CreateUserRequest, UserListParams } from '@/types/users'

export const usersService = {
  // 목록 조회
  getList: (params?: UserListParams) =>
    apiClient.get<PaginatedResponse<User>>('/users', { params }),

  // 단건 조회
  getById: (id: string) =>
    apiClient.get<ApiResponse<User>>(`/users/${id}`),

  // 생성
  create: (data: CreateUserRequest) =>
    apiClient.post<ApiResponse<User>>('/users', data),

  // 수정
  update: (id: string, data: Partial<CreateUserRequest>) =>
    apiClient.put<ApiResponse<User>>(`/users/${id}`, data),

  // 삭제
  delete: (id: string) =>
    apiClient.delete<ApiResponse<void>>(`/users/${id}`),
}
```

모든 엔드포인트는 `api-mapping.md`에 정의된 것과 정확히 일치해야 한다.

#### 3.3 React Query 훅

서비스 함수를 TanStack Query 훅으로 래핑하여 페이지에서 사용한다.

```typescript
// src/hooks/useUsers.ts 예시
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersService } from '@/services/api/usersService'
import type { UserListParams, CreateUserRequest } from '@/types/users'

// 목록 조회 훅
export function useUserList(params?: UserListParams) {
  return useQuery({
    queryKey: ['users', params],
    queryFn: () => usersService.getList(params).then((res) => res.data),
  })
}

// 단건 조회 훅
export function useUser(id: string) {
  return useQuery({
    queryKey: ['users', id],
    queryFn: () => usersService.getById(id).then((res) => res.data),
    enabled: !!id,
  })
}

// 생성 뮤테이션 훅
export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateUserRequest) =>
      usersService.create(data).then((res) => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}
```
<!-- ELIF PLATFORM == VUE -->
`frontend-env-setup.md`에서 생성한 `src/services/api/client.ts`의 axios 인스턴스를 활용하여
도메인별 서비스 함수를 구현한다.

#### 3.1 도메인 타입 정의

`docs/design/api/*.yaml`의 스키마를 TypeScript 인터페이스로 변환한다.

```typescript
// src/types/<domain>.ts 예시 (users 도메인)
export interface User {
  id: string
  name: string
  email: string
  role: 'admin' | 'member'
  createdAt: string
}

export interface CreateUserRequest {
  name: string
  email: string
  role: 'admin' | 'member'
}

export interface UserListParams {
  page?: number
  pageSize?: number
  search?: string
}
```

#### 3.2 서비스 함수 패턴

```typescript
// src/services/api/usersService.ts 예시 (Vue도 axios 동일 패턴)
import { apiClient } from './client'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type { User, CreateUserRequest, UserListParams } from '@/types/users'

export const usersService = {
  getList: (params?: UserListParams) =>
    apiClient.get<PaginatedResponse<User>>('/users', { params }),
  getById: (id: string) =>
    apiClient.get<ApiResponse<User>>(`/users/${id}`),
  create: (data: CreateUserRequest) =>
    apiClient.post<ApiResponse<User>>('/users', data),
  update: (id: string, data: Partial<CreateUserRequest>) =>
    apiClient.put<ApiResponse<User>>(`/users/${id}`, data),
  delete: (id: string) =>
    apiClient.delete<ApiResponse<void>>(`/users/${id}`),
}
```

#### 3.3 Pinia 스토어 (상태 관리)

```typescript
// src/stores/usersStore.ts 예시
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usersService } from '@/services/api/usersService'
import type { User, UserListParams } from '@/types/users'

export const useUsersStore = defineStore('users', () => {
  const users = ref<User[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchUsers(params?: UserListParams) {
    isLoading.value = true
    error.value = null
    try {
      const res = await usersService.getList(params)
      users.value = res.data.items
    } catch (e) {
      error.value = '데이터를 불러올 수 없습니다.'
    } finally {
      isLoading.value = false
    }
  }

  async function createUser(data: Parameters<typeof usersService.create>[0]) {
    await usersService.create(data)
    await fetchUsers()  // 목록 갱신
  }

  return { users, isLoading, error, fetchUsers, createUser }
})
```
<!-- ELIF PLATFORM == FLUTTER -->
`frontend-env-setup.md`에서 생성한 Dio 클라이언트를 활용하여 Repository + DataSource 패턴으로 구현한다.

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
<!-- ENDIF -->

---

### 4단계. 페이지별 구현

#### 4.1 구현 순서 결정

`docs/plan/design/userstory.md`의 우선순위를 기준으로 구현 순서를 정한다.

```
구현 순서 원칙:
1. Must Have 유저스토리 → 2. Should Have 유저스토리
동일 우선순위 내에서는 UI/UX 설계서의 화면 목록 순서를 따른다.
```

구현 전 각 페이지에 대해 아래를 확인한다.

| 확인 항목 | 참조 파일 |
|----------|---------|
| 이 페이지의 유저스토리 | `docs/plan/design/userstory.md` |
| 사용하는 API 엔드포인트 | `docs/design/frontend/api-mapping.md` |
| 화면 구성 및 인터랙션 | `docs/design/frontend/uiux-design.md` |
| 요청/응답 스키마 | `docs/design/api/*.yaml` |

#### 4.2 페이지/화면 구현 패턴

<!-- IF PLATFORM == REACT -->
```typescript
// src/pages/users/UsersListPage.tsx 예시
import { useState } from 'react'
import { useUserList } from '@/hooks/useUsers'
import Table from '@/components/common/Table'
import Loading from '@/components/common/Loading'
import styles from './UsersListPage.module.css'

export default function UsersListPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading, isError } = useUserList({ page, pageSize: 20 })

  if (isLoading) return <Loading />
  if (isError) return <div>데이터를 불러올 수 없습니다.</div>

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>사용자 목록</h1>
      <Table
        columns={columns}
        data={data?.items ?? []}
        total={data?.total ?? 0}
        page={page}
        onPageChange={setPage}
      />
    </div>
  )
}
```

페이지 구현 후 `src/router/index.tsx`에서 placeholder를 실제 페이지 컴포넌트로 교체한다.
<!-- ELIF PLATFORM == VUE -->
```vue
<!-- src/views/users/UsersListView.vue 예시 -->
<script setup lang="ts">
import { onMounted } from 'vue'
import { useUsersStore } from '@/stores/usersStore'
import AppTable from '@/components/common/AppTable.vue'
import AppLoading from '@/components/common/AppLoading.vue'

const store = useUsersStore()

onMounted(() => store.fetchUsers())
</script>

<template>
  <div class="users-list">
    <h1>사용자 목록</h1>
    <AppLoading v-if="store.isLoading" />
    <p v-else-if="store.error">{{ store.error }}</p>
    <AppTable v-else :data="store.users" :columns="columns" />
  </div>
</template>
```

페이지 구현 후 `src/router/index.ts`에서 라우트를 등록한다.
<!-- ELIF PLATFORM == FLUTTER -->
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
<!-- ENDIF -->

#### 4.3 Prism Mock 연동 확인

각 페이지/화면 구현 완료 후 확인한다.

<!-- IF PLATFORM == REACT -->
```
확인 항목 (브라우저 개발자도구 Network 탭):
- 요청이 http://localhost:4010 으로 전송되는지
- 응답 상태 코드가 200인지
- 응답 데이터가 화면에 정상 렌더링되는지
- 콘솔 에러가 없는지
```
<!-- ELIF PLATFORM == VUE -->
```
확인 항목 (브라우저 개발자도구 Network 탭):
- 요청이 http://localhost:4010 으로 전송되는지
- 응답 상태 코드가 200인지
- 응답 데이터가 화면에 정상 렌더링되는지
- 콘솔 에러가 없는지
```
<!-- ELIF PLATFORM == FLUTTER -->
```
확인 항목:
- flutter run 시 콘솔에서 요청 URL이 http://localhost:4010 으로 출력되는지
  (Dio interceptor 로그 또는 flutter_inspector 활용)
- 응답 상태 코드가 200인지 (Dio 인터셉터에서 로깅)
- 화면에 데이터가 정상 표시되는지
- 콘솔(flutter logs)에 에러가 없는지
```
<!-- ENDIF -->

#### 4.4 Prism 한계와 stub 데이터 보완

Prism은 stateless(상태 비보존)이므로 아래 시나리오는 동작하지 않는다.

<!-- IF PLATFORM == REACT -->
| 시나리오 | 문제 | 보완 방법 |
|----------|------|---------|
| 생성 후 목록 즉시 반영 | Prism은 POST를 받아도 GET 응답이 변하지 않음 | 뮤테이션 성공 후 `queryClient.invalidateQueries` 호출 + 낙관적 업데이트 |
| 로그인 후 토큰 유지 | Prism은 인증 상태를 저장하지 않음 | 로그인 서비스 함수에서 Prism 응답의 토큰을 `localStorage`에 수동 저장하는 stub 로직 추가 |
| 삭제 후 목록 갱신 | 동일 | 삭제 뮤테이션 `onSuccess`에서 쿼리 무효화 |
| 복잡한 필터/정렬 결과 | Prism은 쿼리 파라미터를 무시하고 동일 응답 반환 | 프론트엔드에서 클라이언트 사이드 필터링 임시 구현 |

stub 데이터는 `src/services/api/stubs/` 폴더에 모아 실제 API 전환 시 일괄 제거한다.

```typescript
// src/services/api/stubs/authStub.ts 예시
// 실제 백엔드 전환 시 이 파일 삭제
export const mockLoginResponse = {
  token: 'mock-jwt-token-for-development',
  user: { id: '1', name: '테스트 사용자', email: 'test@example.com' },
}
```
<!-- ELIF PLATFORM == VUE -->
| 시나리오 | 문제 | 보완 방법 |
|----------|------|---------|
| 생성 후 목록 즉시 반영 | Prism은 POST를 받아도 GET 응답이 변하지 않음 | 뮤테이션 성공 후 Pinia 스토어 `fetchUsers()` 재호출 + 낙관적 업데이트 |
| 로그인 후 토큰 유지 | Prism은 인증 상태를 저장하지 않음 | 로그인 서비스 함수에서 Prism 응답의 토큰을 `localStorage`에 수동 저장하는 stub 로직 추가 |
| 삭제 후 목록 갱신 | 동일 | 삭제 액션 완료 후 스토어 재조회 |
| 복잡한 필터/정렬 결과 | Prism은 쿼리 파라미터를 무시 | 스토어에서 클라이언트 사이드 필터링 임시 구현 |

stub 데이터는 `src/services/api/stubs/` 폴더에 모아 실제 API 전환 시 일괄 제거한다.
<!-- ELIF PLATFORM == FLUTTER -->
| 시나리오 | 문제 | 보완 방법 |
|----------|------|---------|
| 생성 후 목록 즉시 반영 | Prism은 POST를 받아도 GET 응답이 변하지 않음 | `UsersNotifier.createUser()` 내 `ref.invalidateSelf()` 호출 |
| 로그인 후 토큰 유지 | Prism은 인증 상태를 저장하지 않음 | 로그인 응답의 mock 토큰을 `flutter_secure_storage`에 수동 저장하는 stub 로직 추가 |
| 삭제 후 목록 갱신 | 동일 | `deleteUser()` 내 `ref.invalidateSelf()` 호출 |
| 복잡한 필터/정렬 결과 | Prism은 쿼리 파라미터를 무시 | Provider에서 클라이언트 사이드 필터링 임시 구현 |

stub 데이터는 `lib/core/stubs/` 폴더에 모아 실제 API 전환 시 일괄 제거한다.

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
<!-- ENDIF -->

---

### 5단계. 빌드 및 에러 해결

페이지/화면 구현이 모두 완료되면 빌드를 실행하여 타입 오류·빌드 오류를 해결한다.

<!-- IF PLATFORM == REACT -->
```bash
cd frontend
npm run build
```

빌드 오류 발생 시 원인을 파악하고 프로덕션 코드를 수정한다. 타입 오류가 있으면 타입 정의를 OpenAPI 명세와 대조하여 수정한다.
<!-- ELIF PLATFORM == VUE -->
```bash
cd frontend
npm run build
```

빌드 오류 발생 시 원인을 파악하고 프로덕션 코드를 수정한다. 타입 오류가 있으면 타입 정의를 OpenAPI 명세와 대조하여 수정한다.
<!-- ELIF PLATFORM == FLUTTER -->
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
<!-- ENDIF -->

---

## 출력 형식

### 폴더 구조

<!-- IF PLATFORM == REACT -->
```
frontend/src/
├── components/
│   ├── common/              # 2개 이상 화면에서 재사용되는 UI 원자 컴포넌트
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   ├── Table.tsx
│   │   ├── Loading.tsx
│   │   └── ...
│   └── <domain>/            # 도메인 공통 복합 컴포넌트
├── layouts/
│   ├── MainLayout.tsx
│   └── AuthLayout.tsx       # 인증 페이지용 (필요 시)
├── pages/
│   └── <domain>/
│       ├── <Domain>ListPage.tsx
│       ├── <Domain>DetailPage.tsx
│       └── <Domain>FormPage.tsx
├── hooks/
│   └── use<Domain>.ts       # TanStack Query 훅
├── services/
│   └── api/
│       ├── client.ts        # (frontend-env-setup.md 산출물, 수정 금지)
│       ├── config.ts        # (frontend-env-setup.md 산출물, 수정 금지)
│       ├── <domain>Service.ts
│       └── stubs/           # Prism 한계 보완용 (실제 전환 시 삭제)
└── types/
    ├── api.ts               # (frontend-env-setup.md 산출물)
    └── <domain>.ts          # 도메인별 타입
```
<!-- ELIF PLATFORM == VUE -->
```
frontend/src/
├── components/
│   ├── common/              # 2개 이상 화면에서 재사용되는 UI 원자 컴포넌트
│   │   ├── AppButton.vue
│   │   ├── AppInput.vue
│   │   ├── AppModal.vue
│   │   ├── AppTable.vue
│   │   ├── AppLoading.vue
│   │   └── ...
│   └── <domain>/            # 도메인 공통 복합 컴포넌트
├── layouts/
│   ├── MainLayout.vue
│   └── AuthLayout.vue       # 인증 페이지용 (필요 시)
├── views/
│   └── <domain>/
│       ├── <Domain>ListView.vue
│       ├── <Domain>DetailView.vue
│       └── <Domain>FormView.vue
├── stores/
│   └── <domain>Store.ts     # Pinia 스토어
├── services/
│   └── api/
│       ├── client.ts        # (frontend-env-setup.md 산출물, 수정 금지)
│       ├── <domain>Service.ts
│       └── stubs/           # Prism 한계 보완용 (실제 전환 시 삭제)
└── types/
    ├── api.ts
    └── <domain>.ts
```
<!-- ELIF PLATFORM == FLUTTER -->
```
frontend/lib/
├── core/
│   ├── config/
│   │   └── app_config.dart       # AppConfig.apiBaseUrl 등 환경 설정
│   ├── network/
│   │   └── dio_client.dart       # (frontend-env-setup.md 산출물, 수정 금지)
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
<!-- ENDIF -->

### 페이지별 구현 체크리스트 템플릿

각 페이지/화면 구현 시 아래 체크리스트를 사용한다.

<!-- IF PLATFORM == REACT -->
```
## 페이지명: _______________

### 준비
- [ ] 유저스토리 확인 (userstory.md)
- [ ] API 엔드포인트 확인 (api-mapping.md)
- [ ] 화면 구성 확인 (uiux-design.md)
- [ ] 요청/응답 스키마 확인 (OpenAPI yaml)
- [ ] 프로토타입 화면 확인 (playwright)

### 구현
- [ ] 도메인 타입 정의 (src/types/<domain>.ts)
- [ ] 서비스 함수 구현 (src/services/api/<domain>Service.ts)
- [ ] React Query 훅 구현 (src/hooks/use<Domain>.ts)
- [ ] 페이지 컴포넌트 구현 (src/pages/<domain>/)
- [ ] 라우터에 페이지 연결 (src/router/index.tsx)

### 검증
- [ ] Prism Mock 서버 응답 Network 탭 확인 (http://localhost:4010)
- [ ] 화면 정상 렌더링 확인
- [ ] 콘솔 에러 없음 확인
- [ ] 반응형 레이아웃 확인 (모바일/데스크톱)
- [ ] UI/UX 설계서 화면과 일치 확인
```
<!-- ELIF PLATFORM == VUE -->
```
## 화면명: _______________

### 준비
- [ ] 유저스토리 확인 (userstory.md)
- [ ] API 엔드포인트 확인 (api-mapping.md)
- [ ] 화면 구성 확인 (uiux-design.md)
- [ ] 요청/응답 스키마 확인 (OpenAPI yaml)
- [ ] 프로토타입 화면 확인 (playwright)

### 구현
- [ ] 도메인 타입 정의 (src/types/<domain>.ts)
- [ ] 서비스 함수 구현 (src/services/api/<domain>Service.ts)
- [ ] Pinia 스토어 구현 (src/stores/<domain>Store.ts)
- [ ] View 컴포넌트 구현 (src/views/<domain>/)
- [ ] 라우터에 View 연결 (src/router/index.ts)

### 검증
- [ ] Prism Mock 서버 응답 Network 탭 확인 (http://localhost:4010)
- [ ] 화면 정상 렌더링 확인
- [ ] 콘솔 에러 없음 확인
- [ ] 반응형 레이아웃 확인 (모바일/데스크톱)
- [ ] UI/UX 설계서 화면과 일치 확인
```
<!-- ELIF PLATFORM == FLUTTER -->
```
## 화면명: _______________

### 준비
- [ ] 유저스토리 확인 (userstory.md)
- [ ] API 엔드포인트 확인 (api-mapping.md)
- [ ] 화면 구성 확인 (uiux-design.md)
- [ ] 요청/응답 스키마 확인 (OpenAPI yaml)
- [ ] 프로토타입 화면 확인 (playwright — 모바일 사이즈 390×844)

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
- [ ] UI/UX 설계서 화면과 일치 확인 (모바일/태블릿)
```
<!-- ENDIF -->

---

## 품질 기준

<!-- IF PLATFORM == REACT -->
- [ ] 모든 페이지가 Prism Mock API(localhost:4010) 기반으로 정상 동작
- [ ] API 서비스 함수의 엔드포인트가 `api-mapping.md`와 정확히 일치
- [ ] `public/runtime-env.js` 변경만으로 Mock → 실제 서버 전환 가능한 구조
- [ ] 반응형 UI 구현 (모바일/태블릿/데스크톱)
- [ ] `npm run build` 성공 (타입 오류·빌드 오류 없음)
- [ ] CSS 변수가 `style-guide.md` 기준 값과 일치 (하드코딩 없음)
- [ ] Prism stub 데이터가 `src/services/api/stubs/`에 분리됨
- [ ] 유저스토리 Must Have 항목 전체 구현
- [ ] **TODO/FIXME/HACK 0건**: `grep -rn "TODO\|FIXME\|HACK" frontend/src/` 결과가 0건
- [ ] **런타임 동작 확인**: `npm run dev` 실행 후 브라우저에서 주요 페이지 접근 및 Mock API 호출 정상 동작
<!-- ELIF PLATFORM == VUE -->
- [ ] 모든 화면이 Prism Mock API(localhost:4010) 기반으로 정상 동작
- [ ] API 서비스 함수의 엔드포인트가 `api-mapping.md`와 정확히 일치
- [ ] `public/runtime-env.js` 변경만으로 Mock → 실제 서버 전환 가능한 구조
- [ ] 반응형 UI 구현 (모바일/태블릿/데스크톱)
- [ ] `npm run build` 성공 (타입 오류·빌드 오류 없음)
- [ ] CSS 변수가 `style-guide.md` 기준 값과 일치 (하드코딩 없음)
- [ ] Prism stub 데이터가 `src/services/api/stubs/`에 분리됨
- [ ] 유저스토리 Must Have 항목 전체 구현
- [ ] **TODO/FIXME/HACK 0건**: `grep -rn "TODO\|FIXME\|HACK" frontend/src/` 결과가 0건
- [ ] **런타임 동작 확인**: `npm run dev` 실행 후 브라우저에서 주요 페이지 접근 및 Mock API 호출 정상 동작
<!-- ELIF PLATFORM == FLUTTER -->
- [ ] 모든 화면이 Prism Mock API(localhost:4010) 기반으로 정상 동작
- [ ] DataSource의 엔드포인트가 `api-mapping.md`와 정확히 일치
- [ ] `web/runtime-env.js`(Web) 또는 `--dart-define`(Mobile) 변경만으로 Mock → 실제 서버 전환 가능한 구조
- [ ] `flutter analyze` 결과 오류(error) 0건, 경고(warning) 0건
- [ ] `dart run build_runner build` 성공 (freezed/json_serializable 코드 최신 상태)
- [ ] `flutter build apk` (또는 대상 플랫폼 빌드) 성공
- [ ] ThemeData 기반 스타일링 (하드코딩된 색상·폰트 크기 없음)
- [ ] Prism stub 데이터가 `lib/core/stubs/`에 분리됨
- [ ] 유저스토리 Must Have 항목 전체 구현
- [ ] **TODO/FIXME/HACK 0건**: `grep -rn "TODO\|FIXME\|HACK" frontend/lib/` 결과가 0건
- [ ] **런타임 동작 확인**: `flutter run -d chrome` 실행 후 주요 화면 접근 및 Mock API 호출 정상 동작
<!-- ENDIF -->

## 주의사항

- **TODO/FIXME/HACK 금지**: 모든 코드는 완전하게 구현한다. "TODO: 나중에 구현", "FIXME: 임시 처리" 등의 미완성 마커를 남기지 않는다. 구현이 어려운 부분이 있으면 우회하지 말고 근본 원인을 해결한다.
- **런타임 에러 워크어라운드 금지**: 런타임 에러 발생 시 콘솔 에러를 무시하거나, 기능을 비활성화하거나, 하드코딩 값으로 대체하는 등의 우회 해결을 금지한다. 반드시 근본 원인을 분석하고 정상 동작하도록 수정한다.
- **런타임 동작 검증 필수**: 빌드 성공만으로는 완료가 아니다. 개발 서버를 실행하여 브라우저에서 주요 페이지가 오류 없이 동작하고, Mock API 호출이 정상 반환되는지 확인해야 한다.

<!-- IF PLATFORM == REACT -->
- **Prism Mock 서버는 `docker compose --profile mock up -d`로 기동한다.** 직접 Prism을 설치하거나 별도 실행하지 않는다.
- **API 서비스 레이어(`src/services/api/`)를 페이지 컴포넌트에서 직접 import하지 않는다.** 반드시 React Query 훅을 통해 사용한다. 이 구조가 Mock → 실제 전환 시 변경 범위를 최소화한다.
- Prism이 OpenAPI 명세의 `example` 값을 우선 반환하므로, 명세에 `example`이 없으면 타입 기반 자동 생성 값이 반환된다. 명세의 `example`을 보강하면 Mock 품질이 향상된다.
- `frontend-env-setup.md`에서 생성한 `client.ts`, `config.ts`는 이 단계에서 수정하지 않는다. API URL 변경은 `public/runtime-env.js` 파일만으로 처리한다.
- 프로토타입 화면 분석은 playwright MCP를 이용하여 모바일 사이즈(390×844)로 확인한다.
- 기존 파일을 삭제하거나 덮어쓰기 전에 반드시 충돌 여부를 확인한다.
- stub 데이터는 실제 API 전환 시 전량 제거 대상이다. stub 로직이 프로덕션 비즈니스 로직과 혼용되지 않도록 `stubs/` 폴더에 격리한다.
<!-- ELIF PLATFORM == VUE -->
- **Prism Mock 서버는 `docker compose --profile mock up -d`로 기동한다.** 직접 Prism을 설치하거나 별도 실행하지 않는다.
- **API 서비스 레이어(`src/services/api/`)를 View 컴포넌트에서 직접 import하지 않는다.** 반드시 Pinia 스토어를 통해 사용한다. 이 구조가 Mock → 실제 전환 시 변경 범위를 최소화한다.
- Prism이 OpenAPI 명세의 `example` 값을 우선 반환하므로, 명세에 `example`이 없으면 타입 기반 자동 생성 값이 반환된다.
- `frontend-env-setup.md`에서 생성한 `client.ts`는 이 단계에서 수정하지 않는다. API URL 변경은 `public/runtime-env.js` 파일만으로 처리한다.
- 프로토타입 화면 분석은 playwright MCP를 이용하여 모바일 사이즈(390×844)로 확인한다.
- stub 데이터는 실제 API 전환 시 전량 제거 대상이다. `stubs/` 폴더에 격리한다.
<!-- ELIF PLATFORM == FLUTTER -->
- **Prism Mock 서버는 `docker compose --profile mock up -d`로 기동한다.** 직접 Prism을 설치하거나 별도 실행하지 않는다.
- **DataSource를 Screen/Widget에서 직접 호출하지 않는다.** 반드시 Riverpod Provider → Repository → DataSource 계층을 통해 사용한다. 이 구조가 Mock → 실제 전환 시 변경 범위를 최소화한다.
- `freezed`/`json_serializable` 모델을 수정하면 반드시 `dart run build_runner build`를 재실행한다.
- Prism이 OpenAPI 명세의 `example` 값을 우선 반환하므로, 명세의 `example`을 보강하면 Mock 품질이 향상된다.
- `frontend-env-setup.md`에서 생성한 `dio_client.dart`는 이 단계에서 수정하지 않는다. API URL 변경은 `web/runtime-env.js`(Web) 또는 `--dart-define`(Mobile)으로 처리한다.
- 프로토타입 화면 분석은 playwright MCP를 이용하여 모바일 사이즈(390×844)로 확인한다.
- stub 데이터는 실제 API 전환 시 전량 제거 대상이다. `lib/core/stubs/` 폴더에 격리한다.
<!-- ENDIF -->
