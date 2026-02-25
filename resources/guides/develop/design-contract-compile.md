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

3단계 이상도 재귀적으로 동일 규칙을 적용한다.

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

### 변환 불요 요소

- `activate`/`deactivate`: 시각적 요소 -- 테스트 매핑 대상 아님
- `group`: 시각적 그룹핑 요소 -- 테스트 매핑 대상 아님

### note 요소 활용 분류

- 요청 파라미터를 포함하는 note → `.send()` 데이터로 변환
- 응답 필드를 포함하는 note → `.expect()` assertion으로 변환
- 설계 의도/비즈니스 규칙 note → 테스트 코드의 JSDoc 주석으로 변환

### 변환 규칙 요약 테이블

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
| `activate`/`deactivate` | 변환 불요 | 시각적 요소 -- 테스트 매핑 대상 아님 |
| `group {라벨}` | 변환 불요 | 시각적 그룹핑 요소 |
| 중첩 `alt` (3단계 이상) | `describe` 재귀 중첩 | 중첩 깊이에 관계없이 동일 규칙을 재귀적으로 적용 |

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
npx tsc --noEmit
npx jest --verbose
```

- **컴파일 성공**: `npx tsc --noEmit` 이 오류 없이 완료
- **테스트 구조 정합성**: 이 시점에서는 API 서버 미구현이므로 모든 테스트가 FAIL이어야 정상
- 실제 PASS 검증은 Step 3 이후 서비스 구현 완료 시

#### 구조 정합성 자동 검증 스크립트

시퀀스 설계서와 테스트 코드 간의 1:1 매핑을 자동 검증한다.

- 시퀀스 파일 수 vs describe 블록 수 카운팅
  - `docs/design/sequence/**/*.puml` 파일 수 >= 최상위 `describe` 블록 수
- alt/else 분기 수 vs it() 케이스 수 카운팅
  - 시퀀스 파일 내 `alt` + `else` 키워드 수 = `it()` 케이스 수

## 변환 예시

### 입력: 로그인 플로우 외부 시퀀스

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

## 품질 기준

- [ ] 모든 시퀀스 설계서의 alt/else 분기가 it() 케이스로 변환됨
- [ ] API 명세의 모든 엔드포인트에 대한 응답 스키마 assertion이 존재
- [ ] 테스트 코드 `npx tsc --noEmit` 성공 (타입 오류 없음)
- [ ] 시퀀스 파일 수 >= describe 블록 수 (1:1 이상 매핑)
- [ ] alt/else 분기 수 = it() 케이스 수 (정확히 1:1)

## 주의사항

- 설계서에 존재하지 않는 분기를 임의로 추가하지 않는다
- 테스트 이름은 `{조건} 시 {기대 결과}` 형식을 따른다
- 모든 API 호출은 supertest 기반으로 작성한다
- 서비스 URL은 환경변수로 주입 가능하도록 한다
