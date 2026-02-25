# 프론트엔드 Mock 기반 개발 (Vue)


## 목적

OpenAPI 명세 기반 Prism Mock 서버를 활용하여 백엔드 완성을 기다리지 않고 프론트엔드 페이지를 구현한다.
`frontend-env-setup-vue.md`에서 구축한 프로젝트 골격 위에서 공통 컴포넌트와 페이지를 개발하고,
Mock API 연동이 완성된 상태로 실제 백엔드 전환을 준비한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 프로토타입 | `docs/plan/design/uiux/prototype/` | 화면 구조·컴포넌트 구현 기준 |
| OpenAPI 명세 | `docs/design/api/*.yaml` | Prism Mock 데이터 자동 생성 기준 |
| 종합 개발 계획서 | `docs/develop/dev-plan.md` | 페이지 우선순위(섹션 5) |
| 프론트엔드 프로젝트 골격 | `frontend/` | `frontend-env-setup-vue.md` 산출물 |
| 행위 계약 테스트 | `test/design-contract/integration/*.spec.ts` | 프론트엔드↔백엔드 연동 시나리오 참조 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 공통 컴포넌트 | `frontend/src/components/` |
| 레이아웃 컴포넌트 | `frontend/src/layouts/` |
| API 서비스 함수 | `frontend/src/services/api/` |
| Pinia 스토어 | `frontend/src/stores/` |
| 페이지 컴포넌트 | `frontend/src/views/` |

## 방법론

### 작업 순서 개요

1. 준비: 설계 문서 분석 및 Prism Mock 서버 기동 확인
2. 공통 컴포넌트/위젯 개발
3. 페이지별 구현 (dev-plan.md의 섹션5 참조)
4. 빌드 및 에러 해결

---

### 1단계. 준비

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

`frontend-env-setup-vue.md`에서 이미 생성되었다면 그대로 사용한다.

> **[DEFERRED] MOCK == MULTI**: 서비스별 Prism 인스턴스를 개별 포트에서 실행하는 멀티 Prism 패턴은 이번 범위에서 제외한다.
> MOCK == MULTI support will be added when `backing-service-setup.md` is updated to support per-service Prism instances.

---

### 2단계. 공통 컴포넌트/위젯 개발

#### 2.1 컴포넌트 분류 기준

프로토타입 분석 결과를 바탕으로 컴포넌트를 분류한다.

| 분류 | 경로 | 기준 |
|------|------|------|
| UI 원자 컴포넌트 | `src/components/common/` | 2개 이상 화면에서 재사용되는 범용 UI |
| 레이아웃 | `src/layouts/` | 페이지 골격 (헤더, 사이드바, 푸터) |
| 도메인 공통 | `src/components/<domain>/` | 특정 도메인에서 반복되는 복합 컴포넌트 |

단일 화면에서만 쓰이는 컴포넌트/위젯은 해당 화면 폴더 안에 둔다.
공통 분리는 실제로 재사용이 확인될 때만 수행한다.

#### 2.2 UI 원자 컴포넌트/위젯

프로토타입에서 반복 등장하는 UI 요소를 구현한다.

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

#### 2.3 레이아웃 컴포넌트/위젯

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

---

### 3단계. API 서비스 함수 구현

`frontend-env-setup-vue.md`에서 생성한 `src/services/api/client.ts`의 axios 인스턴스를 활용하여
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

---

### 4단계. 페이지별 구현

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

#### 4.3 Prism Mock 연동 확인

각 페이지/화면 구현 완료 후 확인한다.

```
확인 항목 (브라우저 개발자도구 Network 탭):
- 요청이 http://localhost:4010 으로 전송되는지
- 응답 상태 코드가 200인지
- 응답 데이터가 화면에 정상 렌더링되는지
- 콘솔 에러가 없는지
```

#### 4.4 Prism 한계와 stub 데이터 보완

Prism은 stateless(상태 비보존)이므로 아래 시나리오는 동작하지 않는다.

| 시나리오 | 문제 | 보완 방법 |
|----------|------|---------|
| 생성 후 목록 즉시 반영 | Prism은 POST를 받아도 GET 응답이 변하지 않음 | 뮤테이션 성공 후 Pinia 스토어 `fetchUsers()` 재호출 + 낙관적 업데이트 |
| 로그인 후 토큰 유지 | Prism은 인증 상태를 저장하지 않음 | 로그인 서비스 함수에서 Prism 응답의 토큰을 `localStorage`에 수동 저장하는 stub 로직 추가 |
| 삭제 후 목록 갱신 | 동일 | 삭제 액션 완료 후 스토어 재조회 |
| 복잡한 필터/정렬 결과 | Prism은 쿼리 파라미터를 무시 | 스토어에서 클라이언트 사이드 필터링 임시 구현 |

stub 데이터는 `src/services/api/stubs/` 폴더에 모아 실제 API 전환 시 일괄 제거한다.

---

### 5단계. 빌드 및 에러 해결

페이지/화면 구현이 모두 완료되면 빌드를 실행하여 타입 오류·빌드 오류를 해결한다.

```bash
cd frontend
npm run build
```

빌드 오류 발생 시 원인을 파악하고 프로덕션 코드를 수정한다. 타입 오류가 있으면 타입 정의를 OpenAPI 명세와 대조하여 수정한다.

---

## 출력 형식

### 폴더 구조

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
│       ├── client.ts        # (frontend-env-setup-vue.md 산출물, 수정 금지)
│       ├── <domain>Service.ts
│       └── stubs/           # Prism 한계 보완용 (실제 전환 시 삭제)
└── types/
    ├── api.ts
    └── <domain>.ts
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
- [ ] 프로토타입 화면과 일치 확인
```

---

## 품질 기준

- [ ] 모든 화면이 Prism Mock API(localhost:4010) 기반으로 정상 동작
- [ ] API 서비스 함수의 엔드포인트가 `API 설계서(docs/design/api/*.yaml)`와 정확히 일치
- [ ] `public/runtime-env.js` 변경만으로 Mock → 실제 서버 전환 가능한 구조
- [ ] 반응형 UI 구현 (모바일/태블릿/데스크톱)
- [ ] `npm run build` 성공 (타입 오류·빌드 오류 없음)
- [ ] CSS 변수가 `style-guide.md` 기준 값과 일치 (하드코딩 없음)
- [ ] Prism stub 데이터가 `src/services/api/stubs/`에 분리됨
- [ ] dev-plan.md 섹션 5의 페이지 전체 구현
- [ ] **TODO/FIXME/HACK 0건**: `grep -rn "TODO\|FIXME\|HACK" frontend/src/` 결과가 0건
- [ ] **런타임 동작 확인**: `npm run dev` 실행 후 브라우저에서 주요 페이지 접근 및 Mock API 호출 정상 동작

## 주의사항

- **TODO/FIXME/HACK 금지**: 모든 코드는 완전하게 구현한다. "TODO: 나중에 구현", "FIXME: 임시 처리" 등의 미완성 마커를 남기지 않는다. 구현이 어려운 부분이 있으면 우회하지 말고 근본 원인을 해결한다.
- **런타임 에러 워크어라운드 금지**: 런타임 에러 발생 시 콘솔 에러를 무시하거나, 기능을 비활성화하거나, 하드코딩 값으로 대체하는 등의 우회 해결을 금지한다. 반드시 근본 원인을 분석하고 정상 동작하도록 수정한다.
- **런타임 동작 검증 필수**: 빌드 성공만으로는 완료가 아니다. 개발 서버를 실행하여 브라우저에서 주요 페이지가 오류 없이 동작하고, Mock API 호출이 정상 반환되는지 확인해야 한다.
- **Prism Mock 서버는 `docker compose --profile mock up -d`로 기동한다.** 직접 Prism을 설치하거나 별도 실행하지 않는다.
- **API 서비스 레이어(`src/services/api/`)를 View 컴포넌트에서 직접 import하지 않는다.** 반드시 Pinia 스토어를 통해 사용한다. 이 구조가 Mock → 실제 전환 시 변경 범위를 최소화한다.
- Prism이 OpenAPI 명세의 `example` 값을 우선 반환하므로, 명세에 `example`이 없으면 타입 기반 자동 생성 값이 반환된다.
- `frontend-env-setup-vue.md`에서 생성한 `client.ts`는 이 단계에서 수정하지 않는다. API URL 변경은 `public/runtime-env.js` 파일만으로 처리한다.
- 프로토타입 화면 분석은 playwright MCP를 이용하여 모바일 사이즈(390×844)로 확인한다.
- stub 데이터는 실제 API 전환 시 전량 제거 대상이다. `stubs/` 폴더에 격리한다.
