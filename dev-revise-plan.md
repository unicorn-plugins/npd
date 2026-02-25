# NPD Develop 스킬 변경 계획서

## 1. 변경 목적 및 배경

### 1.1 문제 인식

현재 develop SKILL.md 워크플로우는 설계 단계에서 생성된 **96개 이상의 설계 문서**를 각 에이전트가 직접 탐색·참조하는 구조이다. 이로 인해:

- **컨텍스트 분산**: 에이전트마다 설계 산출물을 독립적으로 해석하여 불일치 발생 위험
- **Sprint 분할의 비효율**: Step 3-1(백엔드 API 구현) 내부에서 Sprint 단위로 분할하지만, AI 에이전트에게 Sprint 경계는 불필요한 복잡성
- **검증 지연**: 시퀀스 설계서의 alt/else 분기가 테스트 케이스로 변환되지 않아, 통합 단계(Step 4)에서야 행위 불일치가 발견됨
- **설계-개발 경계 부재**: 설계 산출물을 "그대로" 읽는 구조라서, 설계 변경 시 모든 가이드의 입력이 영향을 받음

### 1.2 해결 방향

"AI 코딩 시대의 설계 원칙" 논의 결론에 따라:

1. **설계→개발 경계에서 "AI 개발 키트"로 1회 컴파일** — 이후 Step에서는 키트만 참조
2. **Sprint 분할 제거** — 서비스 1개 = 작업 단위, 의존관계 기반 순서만 유지
3. **시퀀스→테스트 변환** — 설계 시퀀스의 alt/else 분기를 test spec의 it() 케이스로 1:1 변환
4. **검증 게이트에서 design-contract test spec 자동 실행** — 코딩 직후 행위 계약 준수 여부 즉시 검증

---

## 2. 변경 원칙

| # | 원칙 | 설명 |
|---|------|------|
| P1 | 설계 산출물 보존 | PlantUML, Mermaid, MD 원본은 변경하지 않음. 사람 리뷰용으로 유지 |
| P2 | 1회 변환, N회 참조 | Step 1에서 설계→키트 변환을 1번만 수행. 이후 Step은 키트만 참조 |
| P3 | 서비스 단위 작업 | Sprint 분할 제거. 서비스 1개를 하나의 작업 단위로 완결 |
| P4 | 행위 계약 선행 | 코딩 전에 시퀀스→테스트 변환 완료. 코딩은 테스트를 통과시키는 행위 |
| P5 | 기존 계약 재활용 | api/*.yaml, *-schema.psql, package-structure.md, prototype/*.html+css는 이미 AI 친화적이므로 그대로 활용 |
| P6 | 최소 변경 | 가이드 문서의 "방법론" 섹션은 최대한 유지. "입력" 섹션만 키트 참조로 교체 |

---

## 3. SKILL.md 변경 상세

### 3.1 전체 구조 변경 개요 (Before/After)

```
[Before]                                    [After]
Step 0. 개발 범위 및 진행 모드 선택          Step 0. 개발 범위 및 진행 모드 선택 (유지)
Step 1. 종합 개발 계획 수립                  Step 1. AI 개발 키트 컴파일 ← 핵심 변경
Step 2. Phase 1 — 환경 구성                  Step 2. 환경 구성 (유지, 입력만 변경)
Step 3. Phase 2 — API 계약 기반 병렬 개발    Step 3. 서비스 단위 병렬 개발 ← Sprint 제거
Step 4. Phase 3 — 통합 연동                  Step 4. 통합 연동 (유지, 검증 강화)
Step 5. Phase 4 — 테스트 및 QA              Step 5. 테스트 및 QA (유지)
Step 6. 개발 완료 보고                       Step 6. 개발 완료 보고 (유지)
```

### 3.2 Step 0 — 변경 없음

현재 Step 0(개발 범위 및 진행 모드 선택)은 그대로 유지한다. Phase 선택, 진행 모드 선택 로직에 변경 사항 없음.

### 3.3 Step 1 — 핵심 변경: "종합 개발 계획 수립" → "AI 개발 키트 컴파일"

#### Before (현재 SKILL.md 166-176행)

```markdown
### Step 1. 종합 개발 계획 수립 → Agent: backend-developer + frontend-developer + ai-engineer (병렬) + architect (리뷰)
- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/dev-plan.md`
- **INPUT**: Step 0-1에서 선택된 개발 단계(Phase) 범위
- **TASK**: 설계 산출물 분석 → 선택된 Phase 범위 내 기능만 추출 → 3개 에이전트가 담당 영역 분담 작성 → architect 리뷰 → 종합 개발 계획서 통합
- **EXPECTED OUTCOME**: `dev-plan.md`
```

#### After (변경안)

```markdown
### Step 1. AI 개발 키트 컴파일 → Agent: architect (주도) + backend-developer + frontend-developer + ai-engineer (병렬 검증)

Step 1은 두 단계로 구성된다:

#### Step 1-1. 종합 개발 계획 수립 (기존과 동일)
- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/dev-plan.md`
- **INPUT**: Step 0-1에서 선택된 개발 단계(Phase) 범위
- **TASK**: 기존과 동일 — 3개 에이전트 분담 작성 → architect 통합 리뷰
- **EXPECTED OUTCOME**: `docs/develop/dev-plan.md`

#### Step 1-2. 행위 계약 테스트 생성 (신규)
- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/design-contract-compile.md` ← 신규 가이드
- **INPUT**:
  - `docs/develop/dev-plan.md` (Step 1-1 산출물)
  - `docs/design/sequence/inner/*.puml` (내부 시퀀스)
  - `docs/design/sequence/outer/*.puml` (외부 시퀀스)
  - `docs/design/api/*.yaml` (API 명세)
- **TASK**:
  1. dev-plan.md를 통합 맥락 문서로 확장 (아키텍처 결정사항, 서비스 간 의존관계 시각화 추가)
  2. 시퀀스 설계서의 alt/else 분기를 test spec의 describe/it 구조로 1:1 변환
  3. API 명세의 요청/응답 스키마를 assertion으로 변환
- **EXPECTED OUTCOME** (AI 개발 키트):
  - `docs/develop/dev-plan.md` (확장된 통합 맥락)
  - `test/design-contract/*.spec.ts` (행위 계약 테스트) ← 신규 산출물
- **SKIP 조건 결정**: AI 서비스 설계서 미존재 시, AI 관련 test spec 생성 건너뜀

> **이후 모든 Step의 입력**:
> - `docs/develop/dev-plan.md` (통합 맥락)
> - `docs/design/api/*.yaml` (백엔드 계약 — 이미 존재, 그대로)
> - `docs/design/database/*-schema.psql` 또는 `docs/design/database/*.md` (DB 계약 — 이미 존재, 그대로)
> - `docs/design/class/package-structure.md` (패키지 구조 — 이미 존재, 그대로)
> - `docs/plan/.../prototype/*.html+css` (프론트엔드 계약 — 이미 존재, 그대로)
> - `test/design-contract/*.spec.ts` (행위 계약 — 신규)
```

**변경 포인트:**
1. 기존 dev-plan.md 생성 로직은 Step 1-1로 보존
2. Step 1-2를 신규 추가하여 시퀀스→테스트 변환 수행
3. "AI 개발 키트"의 정의를 SKILL.md 상단에 명시

### 3.4 Step 2 — 최소 변경: 입력 참조만 교체

#### 변경 내용

Step 2-1 ~ 2-5의 각 하위 Step에서:

**Before**: 각 가이드가 `docs/design/` 하위 설계 문서를 직접 참조

**After**: `docs/develop/dev-plan.md`(통합 맥락)를 1차 입력으로, 상세 정보가 필요한 경우에만 원본 설계 문서 참조

변경 대상 라인 (SKILL.md 내):
- Step 2-1 (180-185행): GUIDE 유지, TASK 설명에 "dev-plan.md 기반" 추가
- Step 2-2 (187-196행): 변경 없음 (이미 설계서 직접 참조가 적절)
- Step 2-3 (198-202행): 변경 없음
- Step 2-4 (204-209행): 변경 없음
- Step 2-5 (213-218행): 변경 없음

> Step 2는 환경 구성 단계이므로 AI 개발 키트의 영향이 적다. 가이드 문서의 입력 섹션만 일부 조정.

### 3.5 Step 3 — 구조 변경: Sprint 분할 제거 + 행위 계약 테스트 활용

#### Before (현재 SKILL.md 220-308행)

```
Step 3. Phase 2 — API 계약 기반 병렬 개발
  3-1. 백엔드 API 구현 (내부적으로 Sprint 분할)
  3-2. 프론트엔드 Mock 기반 개발
  3-3. AI 서비스 구현
  3-4. Phase 2 완료 독립 검증
```

#### After (변경안)

```
Step 3. 서비스 단위 병렬 개발
  3-1. 백엔드 API 구현 (Sprint 분할 제거, 서비스 1개 = 작업 단위)
       - 신규: 각 서비스 구현 완료 후 design-contract test spec 실행
  3-2. 프론트엔드 Mock 기반 개발 (기존과 동일)
  3-3. AI 서비스 구현 (기존과 동일)
  3-4. Phase 2 완료 독립 검증 (design-contract test 실행 추가)
```

**Step 3-1 변경 상세 (SKILL.md 251-256행):**

```markdown
#### Step 3-1. 백엔드 API 구현 → Agent: backend-developer

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/backend-api-dev.md`
- **INPUT** (변경):
  - `docs/develop/dev-plan.md` (통합 맥락 — 서비스 목록, 의존관계, 개발 순서)
  - `docs/design/api/{service-name}-api.yaml` (API 계약)
  - `docs/design/database/{service-name}.md` (DB 계약)
  - `docs/design/class/package-structure.md` (패키지 구조)
  - `test/design-contract/{service-name}/*.spec.ts` (행위 계약) ← 신규 입력
- **TASK**:
  - API 설계서 + 행위 계약 테스트 기반 컨트롤러·서비스·레포지토리 구현 + 단위 테스트
  - **Sprint 분할 제거**: 서비스 1개를 하나의 작업 단위로 완결. 의존관계 기반 순서만 유지
  - **서비스 구현 완료 후**: `test/design-contract/{service-name}/*.spec.ts` 실행하여 행위 계약 준수 확인
- **EXPECTED OUTCOME**: 서비스별 API 코드 + 테스트 코드 + design-contract test PASS
- **병렬**: 서비스 간 의존성 분석 후 독립 서비스는 병렬 구현 (서브에이전트 활용)
```

**Step 3-4 변경 상세 (SKILL.md 303-308행):**

검증 항목에 design-contract test 실행 추가:

```markdown
#### Step 3-4. Phase 2 완료 독립 검증 → Agent: qa-engineer

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/verification-gate.md` (Part 1)
- **TASK**: 기존 검증 항목 + **design-contract test 전체 실행**
  - 기존: 산출물 존재 → TODO/FIXME → API 명세 대조 → 스키마 필드 대조 → 빌드+테스트 → 기동+헬스체크
  - 추가: `test/design-contract/` 하위 전체 test spec 실행 → 행위 계약 위반 0건 확인
- **게이트**: 기존 조건 + design-contract test 전체 PASS 시 Step 4 진입
```

### 3.6 Step 4 — 최소 변경: 검증 게이트 강화

#### Step 4-4 변경 (SKILL.md 337-343행)

```markdown
#### Step 4-4. Phase 3 완료 독립 검증 → Agent: architect

- **GUIDE**: `{PLUGIN_DIR}/resources/guides/develop/verification-gate.md` (Part 2)
- **TASK**: 기존 검증 항목 + **design-contract test 통합 환경 재실행**
  - 기존: Mock 잔존 확인 → 서비스 기동 → 통합 테스트 → BE↔AI 연동 → FE→BE 연동 → API 스키마 동적 검증 → Playwright 유저 시나리오
  - 추가: 통합 환경(실제 서비스 기동 상태)에서 design-contract test 재실행
    → Mock 환경에서 PASS했던 행위 계약이 실제 환경에서도 PASS하는지 확인
```

### 3.7 Step 5, 6 — 변경 없음

Step 5(테스트 및 QA)와 Step 6(개발 완료 보고)는 변경하지 않는다. design-contract test는 이미 Step 3-4, 4-4에서 검증 완료.

### 3.8 SKILL.md 상단에 추가할 새 섹션: "AI 개발 키트 정의"

SKILL.md의 `## 목표` 섹션 아래, `## 선행 조건` 위에 삽입:

```markdown
## AI 개발 키트

설계→개발 경계에서 1회 컴파일되는 개발 입력 세트. Step 1에서 생성되며 이후 모든 Step의 유일한 입력이다.

| 구성 요소 | 경로 | 원본 | 역할 |
|-----------|------|------|------|
| 통합 맥락 | `docs/develop/dev-plan.md` | 전체 설계 산출물 분석 결과 | 전체 그림 + 아키텍처 결정사항 |
| 백엔드 계약 | `docs/design/api/*.yaml` | 이미 존재 (변환 불요) | API 엔드포인트·스키마 정의 |
| DB 계약 | `docs/design/database/*.md` | 이미 존재 (변환 불요) | 테이블·인덱스·관계 정의 |
| 패키지 구조 | `docs/design/class/package-structure.md` | 이미 존재 (변환 불요) | 서비스별 패키지 레이아웃 |
| 프론트엔드 계약 | `docs/plan/.../prototype/*.html+css` | 이미 존재 (변환 불요) | UI 레이아웃·스타일 정의 |
| 행위 계약 | `test/design-contract/*.spec.ts` | 시퀀스 설계서에서 변환 | alt/else 분기 → it() 테스트 케이스 |

> **원칙**: **Step 2 이후의 에이전트**는 `docs/design/sequence/`, `docs/design/class/*.puml` 등 원본 설계 문서를 직접 읽지 않는다.
> 필요한 정보는 모두 AI 개발 키트에 포함되어 있다. 원본이 필요한 경우는 키트에 누락이 있는 것이므로 Step 1을 보완한다.
> **단, Step 1(AI 개발 키트 컴파일)은 변환 단계이므로 원본 설계 문서 읽기가 필수이다.** 이 단계에서만 원본을 읽어 키트로 변환한다.
```

### 3.9 SKILL.md 완료 조건 섹션 추가 항목

SKILL.md 440-459행의 완료 조건에 추가:

```markdown
- [ ] AI 개발 키트 생성 완료 (`docs/develop/dev-plan.md` 확장 + `test/design-contract/*.spec.ts`)
- [ ] design-contract test 전체 PASS (Phase 2 완료 검증 시)
- [ ] design-contract test 통합 환경 재실행 PASS (Phase 3 완료 검증 시)
```

---

## 4. 가이드 문서 변경 상세

### 4.1 `dev-plan.md` (종합 개발 계획 수립 가이드) — 확장 변경

**현재 파일**: `resources/guides/develop/dev-plan.md` (161줄)

**변경 필요 여부**: **확장 필요** (기존 내용 유지 + 출력 형식 확장)

**변경 내용:**

#### 4.1.1 출력 형식 확장

기존 `## 출력 형식` 섹션(79-142행)의 마크다운 템플릿에 다음 섹션 추가:

```markdown
## 7. 아키텍처 결정사항 (ADR 요약)  ← 신규

| 결정 | 선택지 | 결정 사유 | 영향 범위 |
|------|--------|----------|----------|
| {결정 제목} | {A안/B안} | {근거} | {영향받는 서비스} |

## 8. 서비스별 입력 파일 매핑  ← 신규

| 서비스 | API 명세 | DB 설계 | 패키지 구조 | 행위 계약 테스트 |
|--------|---------|---------|-----------|----------------|
| {service-name} | `api/{service-name}-api.yaml` | `database/{service-name}.md` | `class/package-structure.md` #{section} | `test/design-contract/{service-name}/` |

## 9. 테스트 시나리오 (유저스토리 기반)  ← 기존 Phase 4 섹션을 구조화

| TC-ID | 유저스토리 | 시나리오 | 검증 포인트 | 관련 시퀀스 |
|-------|-----------|---------|-----------|-----------|
| TC-01 | {US-ID} | {시나리오 설명} | {기대 결과} | {sequence 파일명} |
```

#### 4.1.2 품질 기준 추가 (153행 이후)

```markdown
- [ ] **서비스별 입력 파일 매핑(섹션 8)이 모든 서비스에 대해 완성**
- [ ] **테스트 시나리오(섹션 9)가 유저스토리 Must Have 전체를 커버**
```

### 4.2 `design-contract-compile.md` — 신규 생성

**신규 파일**: `resources/guides/develop/design-contract-compile.md`

**목적**: 시퀀스 설계서의 alt/else 분기를 test spec으로 1:1 변환하는 가이드

**전체 구조:**

```markdown
# 행위 계약 테스트 생성 가이드

## 목적

PlantUML 시퀀스 설계서의 alt/else 분기와 API 명세의 요청/응답 스키마를
TypeScript 테스트 코드(design-contract test spec)로 변환한다.
이 테스트는 이후 모든 개발·검증 단계에서 "행위 계약"으로 활용된다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 종합 개발 계획서 | `docs/develop/dev-plan.md` | 서비스 목록, 테스트 시나리오 |
| 내부 시퀀스 설계서 | `docs/design/sequence/inner/*.puml` | alt/else 분기 추출 |
| 외부 시퀀스 설계서 | `docs/design/sequence/outer/*.puml` | 서비스 간 호출 시나리오 추출 |
| API 설계서 | `docs/design/api/*.yaml` | 엔드포인트, 요청/응답 스키마 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 서비스별 행위 계약 테스트 | `test/design-contract/{service-name}/*.spec.ts` |
| 외부 연동 행위 계약 테스트 | `test/design-contract/integration/*.spec.ts` |
| 테스트 프로젝트 설정 | `test/design-contract/package.json`, `tsconfig.json` |

## 방법론

### 변환 규칙

#### 규칙 1: 시퀀스 파일 → describe 블록

각 PlantUML 시퀀스 파일을 하나의 `describe` 블록으로 매핑한다.

```
[PlantUML]                           [TypeScript Test]
@startuml                            describe('{시퀀스 title}', () => {
title 로그인 플로우                      // ...
...                                  })
@enduml
```

#### 규칙 2: `== 섹션명 ==` → 중첩 describe

PlantUML의 `== 섹션명 ==` 구분자를 중첩 describe로 매핑한다.

```
[PlantUML]                           [TypeScript Test]
== 로그인 처리 ==                     describe('로그인 처리', () => {
  ...                                   // ...
                                     })
```

#### 규칙 3: alt/else 분기 → it() 테스트 케이스

각 alt 블록의 **각 분기**를 독립된 it() 케이스로 변환한다.

```
[PlantUML]                           [TypeScript Test]
alt 인증 성공                         it('인증 성공 시 JWT 토큰과 200 반환', async () => {
  UserService -> UserService :          const res = await request(app)
    JWT 토큰 생성                          .post('/api/v1/users/auth/login')
  UserService -> Gateway :                .send({ userId: 'valid', password: 'valid' })
    200 OK {token, userId, profile}      .expect(200);
                                        expect(res.body).toHaveProperty('token');
                                        expect(res.body).toHaveProperty('userId');
                                        expect(res.body).toHaveProperty('profile');
                                     });
else 인증 실패                        it('인증 실패 시 401 반환', async () => {
  UserService -> Gateway :              const res = await request(app)
    401 Unauthorized                       .post('/api/v1/users/auth/login')
                                           .send({ userId: 'wrong', password: 'wrong' })
                                           .expect(401);
                                        expect(res.body).toHaveProperty('error');
                                     });
```

#### 규칙 4: 중첩 alt → 중첩 describe + it

```
[PlantUML]                           [TypeScript Test]
alt 인증 실패                         describe('인증 실패', () => {
  ...                                   it('일반 실패 시 401 반환', ...);
  alt 5회 연속 실패                      it('5회 연속 실패 시 계정 잠금 423 반환', async () => {
    UserService -> Gateway :                const res = await request(app)
      423 Locked                               .post('/api/v1/users/auth/login')
  end                                          .send({...})
end                                            .expect(423);
                                            expect(res.body.error).toContain('잠금');
                                        });
                                     });
```

#### 규칙 5: loop → 반복 시나리오 테스트

```
[PlantUML]                           [TypeScript Test]
loop 각 구간별 경로 계산              it('복수 구간 경로 계산 시 구간 수만큼 결과 반환', async () => {
  RouteCalculator -> MCPProvider :      const places = [placeId1, placeId2, placeId3];
    getDirections(...)                  const res = await request(app)
end                                        .post('/api/.../routes/calculate')
                                           .send({ places, ... })
                                           .expect(200);
                                        // 구간 수 = places.length - 1
                                        expect(res.body.routes).toHaveLength(places.length - 1);
                                     });
```

#### 규칙 6: API 명세 응답 스키마 → assertion

OpenAPI yaml의 response schema를 테스트의 assertion으로 변환한다.

```
[OpenAPI yaml]                       [TypeScript Test]
responses:                           it('응답 스키마가 API 명세와 일치', async () => {
  200:                                  const res = await request(app)
    content:                               .get('/api/v1/trips')
      application/json:                    .expect(200);
        schema:                         // 필드 존재 확인
          properties:                   expect(res.body).toHaveProperty('totalDistance');
            totalDistance:              expect(res.body).toHaveProperty('totalDuration');
              type: number              expect(res.body).toHaveProperty('routes');
            totalDuration:              // 타입 확인
              type: number              expect(typeof res.body.totalDistance).toBe('number');
            routes:                     expect(Array.isArray(res.body.routes)).toBe(true);
              type: array            });
```

#### 규칙 7: 오류 처리 시퀀스 → 에러 시나리오 테스트

```
[PlantUML]                           [TypeScript Test]
alt MCP API 오류 발생                 describe('오류 처리', () => {
  MCPProvider --> RouteCalculator :      it('외부 API 오류 시 폴백 응답 반환', async () => {
    API Error                              // 외부 서비스 Mock을 에러로 설정
  RouteCalculator -> RouteCalculator :     const res = await request(app)
    폴백 전략 실행                             .post('/api/.../routes/calculate')
  RouteController --> User :                   .send({...});
    206 Partial Content or 500             expect([206, 500]).toContain(res.status);
end                                     });
                                     });
```

### 테스트 프로젝트 초기화

```bash
mkdir -p test/design-contract
cd test/design-contract
npm init -y
npm install -D typescript @types/node jest ts-jest @types/jest supertest @types/supertest
```

`test/design-contract/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true,
    "outDir": "./dist",
    "rootDir": "./src"
  }
}
```

`test/design-contract/jest.config.ts`:
```typescript
export default {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/*.spec.ts'],
};
```

### 출력 디렉토리 구조

```
test/design-contract/
├── package.json
├── tsconfig.json
├── jest.config.ts
├── {service-name-1}/
│   ├── {feature-1}.spec.ts        ← 내부 시퀀스 기반
│   └── {feature-2}.spec.ts
├── {service-name-2}/
│   └── ...
└── integration/
    ├── {flow-1}.spec.ts           ← 외부 시퀀스 기반
    └── {flow-2}.spec.ts
```

### 검증 방법

```bash
cd test/design-contract
npx jest --verbose
```

- 전체 PASS 확인 (이 시점에서는 API 서버 미구현이므로 모든 테스트가 FAIL이어야 정상)
- **컴파일 성공** + **테스트 구조 정합성**만 검증
- 실제 PASS 검증은 Step 3 이후 서비스 구현 완료 시

### 품질 기준

- [ ] 모든 시퀀스 설계서의 alt/else 분기가 it() 케이스로 변환됨
- [ ] API 명세의 모든 엔드포인트에 대한 응답 스키마 assertion이 존재
- [ ] 테스트 코드 `npx tsc --noEmit` 성공 (타입 오류 없음)
- [ ] 시퀀스 파일 수 >= describe 블록 수 (1:1 이상 매핑)
- [ ] alt/else 분기 수 = it() 케이스 수 (정확히 1:1)
```

### 4.3 `backend-api-dev.md` (백엔드 API 구현 가이드) — 입력 + Sprint 제거 변경

**현재 파일**: `resources/guides/develop/backend-api-dev.md` (612줄)

**변경 필요 여부**: **변경 필요**

**변경 내용:**

#### 4.3.1 입력 섹션 변경 (1-20행)

**Before**: 입력 테이블에 `내부 시퀀스 설계서`, `클래스 설계서` 등 원본 설계 문서 직접 참조

**After**:

```markdown
## 입력 (이전 단계 산출물)

| 산출물 | 탐색 방법 | 활용 방법 |
|--------|----------|----------|
| 종합 개발 계획서 (통합 맥락) | `docs/develop/dev-plan.md` | 서비스 목록, 개발 순서, 의존성, 아키텍처 결정사항 |
| API 설계서 | `docs/design/api/` 하위 `*.yaml` | 엔드포인트 구현 기준 |
| 데이터 설계서 | `docs/design/database/` 하위 `*.md` | 엔티티 필드, 관계, 인덱스 |
| 패키지 구조 | `docs/design/class/package-structure.md` | 패키지 레이아웃 |
| 행위 계약 테스트 | `test/design-contract/{service-name}/` | **구현 목표 — 이 테스트를 PASS시키는 것이 구현 완료 기준** |
| Gradle 환경 | `settings.gradle`, `build.gradle` | 빌드 구성 |
| 백킹서비스 연결 정보 | `.env.example` | DB/Redis/MQ 연결 설정 |
| 보안·JWT·Swagger 표준 | `{PLUGIN_DIR}/resources/references/java-security-jwt-swagger.md` | JWT 인증, Swagger 설정 표준 |
| 테스트 코드 가이드 | `{PLUGIN_DIR}/resources/references/java-test-guide.md` | 단위 테스트 작성 표준 |
| 서비스 실행기 | `{PLUGIN_DIR}/resources/tools/customs/general/run-intellij-service-profile.py` | 서비스 기동 검증 |
```

**삭제되는 입력**:
- `내부 시퀀스 설계서` (`docs/design/sequence/inner/`) → dev-plan.md + design-contract test로 대체
- `클래스 설계서` (`docs/design/class/*.puml`) → package-structure.md + dev-plan.md로 대체

#### 4.3.2 Sprint 분할 관련 내용 제거

현재 `backend-api-dev.md`에는 명시적 Sprint 분할 로직은 없으나, `### 병렬 처리 가이드` 섹션(445-458행)에서 서비스 간 의존성 분석 후 병렬 구현을 안내하고 있다. 이 부분은 유지하되, **Sprint 단위 분할이 아닌 서비스 단위 병렬**임을 명확히 한다.

#### 4.3.3 서비스 구현 완료 기준에 design-contract test 추가

`## 품질 기준` 섹션(584-611행) 마지막에 추가:

```markdown
- [ ] **design-contract test PASS**: `cd test/design-contract && npx jest --testPathPattern="{service-name}" --verbose` 결과 전체 PASS
```

`#### 5단계: 컴파일 및 에러 해결` 섹션(390-403행) 이후에 **6단계** 전에 삽입:

```markdown
#### 5-b단계: 행위 계약 테스트 실행

서비스 기동 후 design-contract test를 실행하여 시퀀스 설계서의 행위 계약 준수를 확인한다.

```bash
# 서비스 기동 (6단계에서 수행하는 기동과 동일)
python3 {PLUGIN_DIR}/resources/tools/customs/general/run-intellij-service-profile.py {service-name}

# 행위 계약 테스트 실행
cd test/design-contract
npx jest --testPathPattern="{service-name}" --verbose
```

- 전체 PASS가 구현 완료 기준
- FAIL 시: 프로덕션 코드를 수정하여 테스트를 통과시킴 (테스트 코드 수정 금지)
- 테스트가 설계 의도와 다르다고 판단되면, 오케스트레이터에 보고하여 Step 1-2 재수행 요청
```

#### 4.3.4 내부 시퀀스 참조 제거

현재 `#### 2단계: 서비스 레이어 구현` 섹션(94-129행)에서:

**Before** (96행):
```
내부 시퀀스 설계서(`docs/design/sequence/inner/` 하위 — 준비 단계에서 식별한 파일)의 흐름을 그대로 반영한다.
```

**After**:
```
dev-plan.md의 서비스별 내부 흐름 설명과 design-contract test의 시나리오를 기반으로 구현한다.
행위 계약 테스트(test/design-contract/{service-name}/*.spec.ts)의 각 it() 케이스가 곧 구현해야 할 행위 목록이다.
```

#### 4.3.5 준비 단계의 설계 산출물 탐색 절차 간소화

**Before** (49-61행): `docs/design/api/`, `docs/design/sequence/inner/`, `docs/design/class/`, `docs/design/database/` 4개 디렉토리를 순차 탐색

**After**:
```
**설계 산출물 탐색 절차:**
1. `docs/develop/dev-plan.md`를 읽어 서비스 목록, 입력 파일 매핑(섹션 8) 확인
2. 매핑 테이블에 명시된 파일만 로드:
   - API 명세: docs/design/api/{service-name}-api.yaml
   - DB 설계: docs/design/database/{service-name}.md
   - 패키지 구조: docs/design/class/package-structure.md
3. 행위 계약 테스트 확인: test/design-contract/{service-name}/*.spec.ts
4. 누락 파일이 있으면 오케스트레이터에 보고 (직접 탐색하지 않음)
```

### 4.4 `frontend-dev.md` (프론트엔드 개발 가이드) — 입력 변경

**현재 파일**: `resources/guides/develop/frontend-dev.md` (1,379줄)

**변경 필요 여부**: **최소 변경** (입력 섹션만)

**변경 내용:**

입력 테이블(12-19행)에 행위 계약 테스트 추가:

```markdown
| 행위 계약 테스트 | `test/design-contract/integration/*.spec.ts` | 프론트엔드↔백엔드 연동 시나리오 참조 |
```

나머지 방법론(2단계~5단계)은 변경 불요. 프론트엔드는 Prism Mock 기반 개발이므로 design-contract test의 직접적 영향이 적다. 통합 단계(Step 4-1)에서 활용.

### 4.5 `frontend-integration.md` (프론트엔드 실제 API 연동 가이드) — 입력 변경

**현재 파일**: `resources/guides/develop/frontend-integration.md`

**변경 필요 여부**: **최소 변경**

입력 테이블에 추가:

```markdown
| 행위 계약 테스트 | `test/design-contract/integration/*.spec.ts` | 연동 시나리오별 기대 동작 확인 |
```

### 4.6 `verification-gate.md` (개발 검증 게이트 가이드) — 검증 항목 추가

**현재 파일**: `resources/guides/develop/verification-gate.md` (859줄)

**변경 필요 여부**: **변경 필요** (검증 항목 추가)

**변경 내용:**

#### 4.6.1 Part 1 (Phase 2 완료 검증) — 검증 항목 추가

현재 Part 1의 검증 절차(136-327행)에 **항목 8 추가** (항목 7 뒤):

```markdown
#### 8. design-contract 행위 계약 테스트 실행

Step 1-2에서 생성된 행위 계약 테스트를 전체 실행하여,
구현된 코드가 시퀀스 설계서의 행위 계약을 준수하는지 검증한다.

**사전 조건**: 항목 7의 서비스 기동이 완료된 상태

```bash
echo "=== design-contract 행위 계약 테스트 ==="
cd test/design-contract
npm ci
npx jest --verbose 2>&1 | tee ../../.temp/design-contract-test-output.log
echo "Exit code: $?"
grep -E "Tests:|Test Suites:" ../../.temp/design-contract-test-output.log
```

- 전체 test suite PASS이어야 PASS
- FAIL 시: FAIL된 테스트명과 에러 메시지를 기록하고 FAIL
- FAIL 테스트의 원인 분류:
  - **구현 누락**: 시퀀스의 alt/else 분기에 해당하는 로직이 구현되지 않음 → backend-developer에게 수정 지시
  - **응답 스키마 불일치**: API 응답 필드가 설계서와 다름 → backend-developer에게 수정 지시
  - **테스트 오류**: 테스트 자체의 assertion이 설계서와 다름 → 오케스트레이터에 보고하여 Step 1-2 재수행
- **실제 jest 출력의 결과 라인을 증거로 캡처한다**
```

게이트 판정 테이블에 항목 8 추가:

```markdown
| 8 | design-contract 테스트 | PASS/FAIL | jest 결과: X suites, Y tests, 0 failed |
```

#### 4.6.2 Part 2 (Phase 3 완료 검증) — 검증 항목 추가

현재 Part 2의 검증 절차(362-627행) 항목 5 이후에 **항목 6 추가**:

```markdown
#### 6. design-contract 행위 계약 테스트 통합 환경 재실행

Mock 환경이 아닌 **실제 서비스 간 연동 환경**에서 design-contract test를 재실행한다.
(Phase 2에서는 각 서비스가 독립 기동 상태에서 테스트했으나, 여기서는 전체 서비스가 연동된 상태에서 재검증)

```bash
echo "=== design-contract 테스트 (통합 환경) ==="
cd test/design-contract
npx jest --verbose 2>&1 | tee ../../.temp/design-contract-integration-output.log
echo "Exit code: $?"
```

- 전체 PASS이어야 PASS
- Phase 2에서 PASS했으나 여기서 FAIL이면: 서비스 간 연동 설정 문제 (CORS, 인증 토큰 전파 등)
```

#### 4.6.3 Part 3 (최종 완료 검증) — 검증 항목 추가

Part 3의 `#### 4. 전체 테스트 스위트 최종 실행` 섹션에 **4-e 추가**:

```markdown
**4-e. design-contract 행위 계약 테스트**
```bash
cd test/design-contract && npx jest --verbose 2>&1 | tee .temp/design-contract-final-output.log
echo "=== design-contract Exit Code: $? ==="
```
- 전체 PASS이어야 PASS
```

### 4.7 `test-qa.md` (종합 테스트 및 QA 가이드) — 최소 변경

**현재 파일**: `resources/guides/develop/test-qa.md` (583줄)

**변경 필요 여부**: **최소 변경**

**변경 내용:**

#### 4.7.1 입력 테이블에 design-contract test 추가 (7-21행)

```markdown
| 행위 계약 테스트 | `test/design-contract/*.spec.ts` | 시퀀스 기반 행위 계약 검증 대상 |
```

#### 4.7.2 Part 3 종합 테스트 스위트에 design-contract 추가 (357-374행)

`### 3-1. 전체 테스트 스위트 실행` 섹션의 실행 순서에 추가:

```bash
# 5. design-contract 행위 계약 테스트
cd test/design-contract && npx jest --verbose
```

#### 4.7.3 종합 테스트 리포트 템플릿에 추가 (386-460행)

`## 2. 테스트 결과 요약` 테이블에 행 추가:

```markdown
| design-contract 테스트 | {N} | {N} | 0 | 100% |
```

### 4.8 나머지 가이드 문서 — 변경 없음

| 가이드 | 변경 필요 여부 | 사유 |
|--------|-------------|------|
| `backend-env-setup.md` | 변경 없음 | 환경 구성은 설계 문서 직접 참조가 적절 |
| `backing-service-setup.md` | 변경 없음 | docker-compose 구성은 데이터 설계서 직접 참조 필요 |
| `frontend-env-setup.md` | 변경 없음 | 프로젝트 초기화는 high-level-architecture.md 참조 |
| `ai-service-env-setup.md` | 변경 없음 | AI 프로젝트 초기화는 ai-service-design.md 직접 참조 |
| `ai-service-dev.md` | **변경 필요** | 입력에 design-contract test 추가 + 시퀀스 직접 참조(`sequence/inner/ai-*.puml`) 제거 → dev-plan.md + design-contract test로 대체. P2 원칙 일관 적용 |
| `backend-ai-integration.md` | **변경 필요** | 입력에 design-contract test 추가 + 외부 시퀀스 직접 참조(`sequence/outer/*.puml`) 제거 → dev-plan.md + design-contract test로 대체. P2 원칙 일관 적용 |
| `run-profile.md` | 변경 없음 | 환경변수 매핑은 키트와 무관 |

---

## 5. 에이전트 정의 변경 상세

### 5.1 변경 필요 여부: **변경 불필요**

현재 모든 에이전트 AGENT.md의 작업 수행 원칙:

```
1. SKILL.md가 지정한 가이드(GUIDE 필드)를 읽고 그 방법론을 따른다
2. 가이드의 `## 입력`으로 컨텍스트를 파악하고, `## 출력`으로 산출물을 생성한다
3. 가이드가 없는 참여 작업(리뷰, 투표, 발산 등)은 SKILL.md의 TASK 지시를 따른다
```

이 구조는 가이드 문서의 입력/출력이 변경되면 에이전트가 자동으로 따르므로, 에이전트 정의 자체를 변경할 필요가 없다. SKILL.md의 Step과 가이드 문서의 입력 섹션을 변경하면 충분하다.

---

## 6. 표준/참조 문서 변경 상세

### 6.1 변경 필요 여부: **변경 불필요**

| 문서 | 변경 여부 | 사유 |
|------|----------|------|
| `standard_comment.md` | 불필요 | 주석 표준은 키트와 무관 |
| `standard_package_structure.md` | 불필요 | 패키지 구조 표준은 그대로 유지 |
| `standard_testcode.md` | 불필요 | 단위 테스트 표준은 그대로 유지 |
| `java-security-jwt-swagger.md` | 불필요 | 보안 참조는 그대로 유지 |
| `java-test-guide.md` | 불필요 | 테스트 가이드는 그대로 유지 |
| `java-build-gradle-standard.md` | 불필요 | 빌드 표준은 그대로 유지 |
| `java-config-manifest-standard.md` | 불필요 | 설정 표준은 그대로 유지 |

### 6.2 신규 참조 문서 검토

design-contract test는 TypeScript/Jest 기반이므로, 별도의 참조 문서를 작성할지 검토:

- **결론: 불필요** — `design-contract-compile.md` 가이드 내에 Jest 설정과 작성 규칙을 포함시키므로, 별도 참조 문서는 불요

---

## 7. 신규 산출물 정의

### 7.1 AI 개발 키트 구성 요소

```
📦 AI 개발 키트 (Step 1 완료 시 생성)
│
├── docs/develop/dev-plan.md              ← 확장된 통합 맥락
│   기존 내용 + 아키텍처 결정사항(ADR) + 서비스별 입력 파일 매핑 + 테스트 시나리오
│
├── docs/design/api/*.yaml (N개)          ← 백엔드 계약 (이미 존재, 변환 불요)
│   OpenAPI 3.0 명세. 엔드포인트, 요청/응답 스키마
│
├── docs/design/database/*.md             ← DB 계약 (이미 존재, 변환 불요)
│   테이블 DDL, 인덱스, 관계, 제약조건
│
├── docs/design/class/package-structure.md ← 패키지 구조 (이미 존재, 변환 불요)
│   서비스별 패키지 레이아웃
│
├── docs/plan/.../prototype/*.html+css    ← 프론트엔드 계약 (이미 존재, 변환 불요)
│   HTML/CSS 프로토타입
│
└── test/design-contract/                 ← 🆕 행위 계약 (시퀀스→테스트 변환)
    ├── package.json
    ├── tsconfig.json
    ├── jest.config.ts
    ├── {service-name-1}/
    │   ├── route-calculation.spec.ts     ← 내부 시퀀스 기반
    │   └── login-flow.spec.ts
    ├── {service-name-2}/
    │   └── ...
    └── integration/
        ├── login-flow.spec.ts            ← 외부 시퀀스 기반
        └── ...
```

### 7.2 시퀀스→테스트 변환 규칙 요약

| PlantUML 요소 | TypeScript Test 매핑 | 비고 |
|--------------|---------------------|------|
| `@startuml` ~ `@enduml` | 파일 1개 (`.spec.ts`) | 시퀀스 파일 1:1 |
| `title {제목}` | 최상위 `describe('{제목}')` | |
| `== {섹션명} ==` | 중첩 `describe('{섹션명}')` | |
| `alt {조건}` | `it('{조건} 시 {기대 결과}')` | alt의 첫 분기 |
| `else {조건}` | `it('{조건} 시 {기대 결과}')` | else 분기 |
| `end` | `})` (describe 또는 it 닫기) | |
| `loop {설명}` | `it('{설명} 반복 시나리오')` | 반복 횟수 검증 |
| `opt {조건}` | `it('{조건} 옵션 활성화 시')` | 선택적 행위 |
| `note right` | assertion의 상세 조건으로 활용 | 주석에서 기대값 추출 |
| `{Actor} -> {Participant} : {메시지}` | API 호출 assertion | HTTP 메서드+경로+기대 응답 |
| Response의 `{field1, field2}` | `expect(res.body).toHaveProperty('{field}')` | 필드 존재 확인 |
| Response의 `200 OK`, `401`, `423` 등 | `.expect({status_code})` | HTTP 상태 코드 검증 |
| `activate`/`deactivate` | 변환 불요 | 시각적 요소 — 테스트 매핑 대상 아님 |
| `group {라벨}` | 변환 불요 | 시각적 그룹핑 요소 |
| 중첩 `alt` (3단계 이상) | `describe` 재귀 중첩 | 중첩 깊이에 관계없이 동일 규칙을 재귀적으로 적용 |

### 7.3 변환 예시 (sample-시퀀스설계서(외부).puml 기반)

**입력**: `sample-시퀀스설계서(외부).puml` — 로그인 플로우

**출력**: `test/design-contract/user-service/login-flow.spec.ts`

```typescript
import request from 'supertest';

const BASE_URL = process.env.USER_SERVICE_URL || 'http://localhost:8081';

describe('로그인 플로우 - 외부 시퀀스', () => {

  describe('로그인 처리', () => {

    it('인증 성공 시 200 OK와 token, userId, profile 반환', async () => {
      const res = await request(BASE_URL)
        .post('/api/v1/users/auth/login')
        .send({ userId: 'testuser', password: 'validpassword' })
        .expect(200);

      expect(res.body).toHaveProperty('token');
      expect(res.body).toHaveProperty('userId');
      expect(res.body).toHaveProperty('profile');
    });

    it('인증 실패 시 401 Unauthorized 반환', async () => {
      const res = await request(BASE_URL)
        .post('/api/v1/users/auth/login')
        .send({ userId: 'wronguser', password: 'wrongpassword' })
        .expect(401);

      expect(res.body).toHaveProperty('error');
    });

    describe('인증 실패 - 계정 잠금', () => {
      it('5회 연속 실패 시 423 Locked 반환', async () => {
        // 5회 연속 실패 시도
        for (let i = 0; i < 5; i++) {
          await request(BASE_URL)
            .post('/api/v1/users/auth/login')
            .send({ userId: 'lockuser', password: 'wrong' });
        }

        const res = await request(BASE_URL)
          .post('/api/v1/users/auth/login')
          .send({ userId: 'lockuser', password: 'wrong' })
          .expect(423);

        expect(res.body.error).toMatch(/잠금/);
      });
    });
  });

  describe('로그인 상태 확인', () => {

    it('유효한 토큰으로 프로필 조회 시 200 OK와 사용자 정보 반환', async () => {
      // 먼저 로그인하여 토큰 획득
      const loginRes = await request(BASE_URL)
        .post('/api/v1/users/auth/login')
        .send({ userId: 'testuser', password: 'validpassword' })
        .expect(200);

      const token = loginRes.body.token;

      const res = await request(BASE_URL)
        .get('/api/v1/users/profile')
        .set('Authorization', `Bearer ${token}`)
        .expect(200);

      expect(res.body).toHaveProperty('userId');
      expect(res.body).toHaveProperty('name');
      expect(res.body).toHaveProperty('email');
      expect(res.body).toHaveProperty('avatar');
    });

    it('무효한 토큰으로 프로필 조회 시 401 Unauthorized 반환', async () => {
      await request(BASE_URL)
        .get('/api/v1/users/profile')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401);
    });
  });

  describe('로그아웃 처리', () => {

    it('로그아웃 성공 시 200 OK 반환', async () => {
      // 로그인
      const loginRes = await request(BASE_URL)
        .post('/api/v1/users/auth/login')
        .send({ userId: 'testuser', password: 'validpassword' })
        .expect(200);

      const token = loginRes.body.token;

      // 로그아웃
      const res = await request(BASE_URL)
        .post('/api/v1/users/auth/logout')
        .set('Authorization', `Bearer ${token}`)
        .expect(200);

      expect(res.body).toHaveProperty('message');
    });
  });
});
```

---

## 8. 검증 게이트 강화 상세

### 8.1 design-contract test spec 활용 방법

#### 8.1.1 Phase 2 완료 검증 (Step 3-4) — qa-engineer

```
검증 순서:
  기존 항목 1~7 → 신규 항목 8 (design-contract test)

항목 8 실행 조건:
  - 항목 7(서비스 기동 + 헬스체크) PASS 후 실행
  - 모든 백엔드 서비스가 기동된 상태에서 실행
  - AI 서비스가 있으면 ai 프로파일도 기동

실행 명령:
  cd test/design-contract && npx jest --verbose

판정:
  - 전체 PASS → 항목 8 PASS
  - 1건이라도 FAIL → 항목 8 FAIL
    → FAIL된 테스트의 describe/it 경로로 원인 서비스 식별
    → 해당 서비스의 backend-developer에게 수정 지시
    → 수정 후 항목 8만 재실행 (항목 1~7 재실행 불요)
```

#### 8.1.2 Phase 3 완료 검증 (Step 4-4) — architect

```
검증 순서:
  기존 항목 1~5 → 신규 항목 6 (design-contract test 통합 환경)

항목 6 실행 조건:
  - 항목 5(FE→BE 연동) PASS 후 실행
  - Mock이 아닌 실제 서비스 간 연동 상태
  - 프론트엔드도 실제 백엔드에 연결된 상태

실행 명령:
  cd test/design-contract && npx jest --verbose

Phase 2 대비 추가 검증 의의:
  - Phase 2에서는 각 서비스가 독립 기동 (외부 호출은 Mock)
  - Phase 3에서는 전 서비스 연동 기동 (실제 서비스 간 호출)
  - CORS, 인증 토큰 전파, 서비스 간 타임아웃 등 연동 이슈를 이 단계에서 검출
```

#### 8.1.3 최종 완료 검증 (Step 5-3) — architect

```
검증 순서:
  기존 항목 1~5 중 항목 4 내부에 design-contract test 포함

실행 위치: 항목 4-e

이 시점에서는 E2E 테스트, 통합 테스트도 모두 PASS한 상태이므로,
design-contract test가 FAIL할 가능성은 극히 낮음.
최종 방어선으로서의 역할.
```

### 8.2 design-contract test FAIL 시 수정 워크플로우

```
1. qa-engineer/architect가 FAIL 항목 보고
   → FAIL 테스트명, 에러 메시지, 기대값 vs 실제값

2. 오케스트레이터가 원인 분류:
   a) 구현 누락/오류 → 해당 서비스의 개발 에이전트에 수정 지시
   b) 테스트 오류 (설계서 오해석) → Step 1-2 재수행 (해당 시퀀스만)
   c) 설계 변경 필요 → PO/Architect와 협의 후 설계 수정 → Step 1-2 재수행

3. 수정 완료 후 FAIL 항목만 재검증:
   npx jest --testNamePattern="{실패한 테스트명}"

4. 전체 PASS 확인 후 게이트 통과
```

---

## 9. 변경 영향도 분석

### 9.1 파일별 변경 규모

| 파일 | 변경 유형 | 변경 크기 (추정) | 위험도 |
|------|---------|----------------|-------|
| `skills/develop/SKILL.md` | 구조 변경 | ~80줄 추가/수정 (479줄 중) | 높음 |
| `guides/develop/dev-plan.md` | 확장 | ~40줄 추가 (161줄 → ~200줄) | 낮음 |
| `guides/develop/design-contract-compile.md` | **신규 생성** | ~300줄 | 높음 |
| `guides/develop/backend-api-dev.md` | 입력 변경 + Sprint 제거 | ~50줄 수정 (612줄 중) | 중간 |
| `guides/develop/verification-gate.md` | 검증 항목 추가 | ~80줄 추가 (859줄 → ~940줄) | 중간 |
| `guides/develop/test-qa.md` | 최소 추가 | ~15줄 추가 (583줄 중) | 낮음 |
| `guides/develop/frontend-dev.md` | 입력 1줄 추가 | ~1줄 (1379줄 중) | 최소 |
| `guides/develop/frontend-integration.md` | 입력 1줄 추가 | ~1줄 | 최소 |
| `guides/develop/ai-service-dev.md` | 입력 1줄 추가 | ~1줄 | 최소 |
| `guides/develop/backend-ai-integration.md` | 입력 1줄 추가 | ~1줄 | 최소 |

### 9.2 변경 요약

- **신규 파일**: 1개 (`design-contract-compile.md`)
- **구조 변경 파일**: 1개 (`SKILL.md`)
- **내용 변경 파일**: 3개 (`dev-plan.md`, `backend-api-dev.md`, `verification-gate.md`)
- **최소 변경 파일**: 5개 (입력 테이블에 1줄 추가)
- **변경 없음 파일**: 8개 (에이전트 5개, 표준/참조 3개 + 기타 가이드)

### 9.3 하위 호환성

- **기존 프로젝트에 미치는 영향**: 없음. AI 개발 키트는 추가 산출물이며, 기존 설계 문서를 변경하지 않음
- **에이전트 호환성**: 에이전트 AGENT.md가 가이드의 입력/출력을 따르는 구조이므로, 가이드 변경이 자동 반영됨
- **롤백 용이성**: SKILL.md의 Step 1을 원래 구조로 복원하면 전체 롤백 가능

---

## 10. 구현 순서 (작업 계획)

### Phase A: 핵심 신규 가이드 작성 (의존관계 없음)

| 순서 | 작업 | 대상 파일 | 산출물 |
|------|------|---------|-------|
| A-1 | design-contract-compile.md 신규 작성 | `resources/guides/develop/design-contract-compile.md` | 완전한 가이드 문서 (~300줄) |

### Phase B: SKILL.md 구조 변경 (A 완료 후)

| 순서 | 작업 | 대상 파일 | 변경 위치 |
|------|------|---------|----------|
| B-1 | "AI 개발 키트" 정의 섹션 추가 | `SKILL.md` | `## 목표` 아래, `## 선행 조건` 위 |
| B-2 | Step 1을 Step 1-1 + 1-2로 분할 | `SKILL.md` | 164-176행 |
| B-3 | Step 3-1 입력/태스크 변경 (Sprint 제거) | `SKILL.md` | 251-256행 |
| B-4 | Step 3-4 검증 항목 추가 | `SKILL.md` | 303-308행 |
| B-5 | Step 4-4 검증 항목 추가 | `SKILL.md` | 337-343행 |
| B-6 | 완료 조건에 design-contract test 추가 | `SKILL.md` | 440-459행 |

### Phase C: 가이드 문서 변경 (A, B와 병렬 가능)

| 순서 | 작업 | 대상 파일 | 변경 내용 |
|------|------|---------|----------|
| C-1 | dev-plan.md 출력 형식 확장 | `dev-plan.md` | 섹션 7, 8, 9 추가 |
| C-2 | backend-api-dev.md 입력 변경 | `backend-api-dev.md` | 입력 테이블 교체, 준비 절차 간소화, 5-b단계 추가 |
| C-3 | verification-gate.md 검증 항목 추가 | `verification-gate.md` | Part 1 항목 8, Part 2 항목 6, Part 3 항목 4-e |
| C-4 | test-qa.md 최소 변경 | `test-qa.md` | 입력 + 테스트 스위트 + 리포트 템플릿 |
| C-5 | 5개 가이드 입력 1줄 추가 | `frontend-dev.md`, `frontend-integration.md`, `ai-service-dev.md`, `backend-ai-integration.md` | 입력 테이블에 행위 계약 테스트 행 추가 |

### Phase D: 검증 (B, C 완료 후)

| 순서 | 작업 | 검증 방법 |
|------|------|----------|
| D-1 | SKILL.md 구조 일관성 검증 | Step 번호 연속성, GUIDE 경로 정합성, EXPECTED OUTCOME 일관성 |
| D-2 | 가이드 간 입력/출력 체인 검증 | Step N의 출력이 Step N+1의 입력으로 올바르게 연결되는지 |
| D-3 | design-contract-compile.md 변환 규칙 검증 | sample 시퀀스 파일로 변환 시뮬레이션 |

### 작업 의존관계 다이어그램

```
A-1 ──────────────────────────────────→ D-3
  ↓                ↓
B-1 → B-2 → B-3 → B-4 → B-5 → B-6 ──→ D-1
                                         ↓
C-1 ──→ C-2 ─┐                         D-2
A-1 ──→ C-3 ─┤ ──────────────────────→ D-2
        C-4 ─┤ (C-4, C-5는 독립 병렬)
        C-5 ─┘
```

> **의존관계 보정**: C-2는 C-1(dev-plan.md 섹션 8 참조)에 의존. C-3는 A-1(design-contract test 구조 참조)에 의존. C-4, C-5는 독립적으로 병렬 가능.

**추정 총 작업량**: 가이드 신규 1개(~300줄) + SKILL.md 수정(~80줄) + 가이드 수정 6개(~160줄) + 최소 수정 3개(~3줄) = **약 545줄의 변경**

---

## 부록: 합의 리뷰 결과

### A. Architect 리뷰

- **판정**: APPROVE_WITH_COMMENTS (8/10)
- **MAJOR 4건** (모두 계획서에 반영 완료):
  1. `activate`/`deactivate` 등 시각적 PlantUML 요소를 변환 규칙 테이블에 "변환 불요"로 명시 → **섹션 7.2에 반영**
  2. 3단계 이상 중첩 alt에 대해 "재귀적으로 동일 규칙 적용" 명시 → **섹션 7.2에 반영**
  3. AI 개발 키트 원칙에 Step 1 예외 명시 ("변환 단계이므로 원본 읽기 필수") → **섹션 3.8에 반영**
  4. 구조 정합성 자동 검증 방법 구체화 필요 → **design-contract-compile.md 작성 시 검증 스크립트 포함 예정**
- **MINOR 5건**: Sprint "제거"→"방지 원칙 명문화" 표현 수정 권고, Phase C 의존관계 보정(**섹션 10에 반영**), integration 테스트 제외 명시, note 요소 활용 분류, 에이전트 호환성 판단 정확 확인
- **INFO 2건**: ai-service-dev.md/backend-ai-integration.md 시퀀스 참조 비대칭(**섹션 4.8에 반영**), CI/CD 영향 언급 부재

### B. Critic 평가

- **판정**: APPROVE (89/100)
- **점수 상세**:

| 기준 | 점수 | 근거 |
|------|------|------|
| 완전성 | 17/20 | 변경 대상 파일 모두 식별, 라인 번호 정확. ai-service-dev.md 시퀀스 참조 누락 → 반영 완료 |
| 일관성 | 18/20 | 용어 일관, P2 원칙과 시퀀스 참조 잔존 간 경미 모순 → 반영 완료 |
| 실행 가능성 | 19/20 | 모든 변경에 파일 경로/라인 번호/Before-After 제공, 실행자 추측 불필요 |
| 위험 관리 | 16/20 | 영향도 분석·롤백 용이성 명시. CI/CD 영향은 deploy 스킬 범위 |
| 최소성 | 19/20 | P6 원칙 준수, 에이전트/표준/참조 문서 변경 불필요 판단 정확 |

- **검증 결과**: 계획서의 모든 파일 참조와 라인 번호가 실제 파일과 일치함을 확인
