# API 테스트
## 목적
구현된 백엔드 API, AI 서비스 API에 대해 curl을 이용하여 정상 동작을 테스트 함  

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 개발계획서 | `docs/develop/dev-plan.md` 섹션 9 | 인증방식 참조 |
| 구현된 백엔드 코드 | `{service-name}/src/` | 테스트 대상 |
| 구현된 AI 서비스 코드 | `ai-service/` | 테스트 대상 (존재 시) |
| API 설계서 | `docs/design/api/*.yaml` | 통합 테스트 케이스 결정 |
| 백킹서비스 설치결과서 | `docs/develop/backing-service-result.md` | DB접근정보 취득 |
| 서비스 실행 프로파일 | `{service-name}/.run/{service-name}.run.xml` | 실행 환경 확인 |
| 서비스 실행기 | `{PLUGIN_DIR}/resources/tools/customs/general/run-backend.py` | 백엔드 서비스 실행 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| API 테스트 결과 | `docs/develop/api-test-result.md` |
| 샘플 데이터 | `{service}/src/test/resources/data/` |

---

## 방법론

각 백엔드/AI 서비스의 API 호출이 정상적으로 동작하는지 검증한다.

### API 목록
어노테이션/패턴 기반으로 Controller와 Router를 탐색하여 API 목록을 정리한다.
```bash
# Spring Boot controller 찾기
grep -rn "@RestController\|@Controller" --include="*.java" --include="*.kt" .
# 엔드포인트 매핑 찾기 (클래스 레벨 @RequestMapping + 메서드 레벨 매핑 모두 확인)
grep -rn "@RequestMapping\|@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping" --include="*.java" --include="*.kt" .
# AI 서비스 router 찾기 (FastAPI/Express/Flask 등)
grep -rn "app\.get\|app\.post\|router\.\|@app\.route\|@router\." --include="*.py" --include="*.ts" --include="*.js" .
```
탐색된 controller/router의 각 엔드포인트를 아래 형식으로 정리한다.
```
# API 목록
## {Service Name}
| ID | 엔드포인트 | 메서드 | 설명 | 입력 | 응답 |
|----|-----------|--------|---------|------|----------|------|
| API-{NNN} | {path} | {GET/POST/...} | {API 설명} | {요청 데이터 구조} | {HTTP 상태코드 + 응답 구조} |
```
'API 테스트 결과'파일에 저장

### 샘플 데이터 작성

**DB인증정보** 취득: 백킹서비스 설치결과서(backing-service-result.md)에서 각 DB 접근 정보 구함  

**절차:**
1. 위 API 목록에서 탐색된 **Controller/Router 클래스**를 읽어 각 API의 요청 데이터 구조를 분석하고, 참조하는 DTO 클래스를 추적하여 테스트에 필요한 데이터를 식별한다
2. 컬럼명/테이블명은 **JPA가 생성한 실제 스키마**를 확인한다. 
3. 서비스별 SQL seed 스크립트를 작성한다:
   - `{service}/src/test/resources/data/seed.sql` — 기본 테스트 데이터
   - 테이블 TRUNCATE → INSERT 순서로 작성 (멱등성 보장)
4. API 요청에 사용할 JSON fixture를 작성한다:
   - `{service}/src/test/resources/data/request/{endpoint-name}.json`
5. 인증 토큰 생성을 위한 테스트용 사용자 데이터를 포함한다

**샘플 데이터 구조:**
```
{service}/src/test/resources/data/
├── seed.sql                          # DB 초기 데이터
├── request/
│   ├── create-{resource}.json        # POST 요청 바디
│   └── update-{resource}.json        # PUT 요청 바디
└── expected/
    └── {resource}-response.json      # 기대 응답 구조
```

### 빌드 사전 확인
- 서비스 기동 전 빌드 성공을 확인한다 (빌드 실패 상태에서 서비스 기동을 방지)
```bash
# 백엔드 빌드 확인
./gradlew clean build 2>&1 | tail -10
echo "Exit code: $?"
```
- BUILD SUCCESSFUL 확인 후 서비스 기동 진행
- 빌드 실패 시: 에러 수정 후 재빌드 (서비스 기동 불요)

### 인증 토큰 획득 (OAuth2/소셜 로그인 프로젝트)

OAuth2 소셜 로그인은 외부 Provider(Google, 카카오 등) 리디렉트가 필요하므로 AI 에이전트가 직접 수행할 수 없다.
아래 방법으로 테스트용 JWT 토큰을 획득한다.

**1단계: 인증 방식 확인**
- 개발계획서 `docs/develop/dev-plan.md`에서 인증서비스의 인증 방식을 확인한다
- JWT 자체 로그인만 사용하는 경우 → 일반 로그인 API(`POST /api/auth/login`)로 토큰 획득 → **이 섹션 건너뜀**
- OAuth2/소셜 로그인 사용 시 → 아래 2단계 진행

**2단계: 테스트 전용 로그인 엔드포인트 구현**

인증 담당 서비스에 `@Profile("dev")` 조건의 테스트 전용 컨트롤러를 추가한다:

```java
@Profile("dev")
@RestController
@RequestMapping("/api/test")
public class TestAuthController {

    private final JwtTokenProvider tokenProvider; // 프로젝트의 토큰 생성 클래스

    public TestAuthController(JwtTokenProvider tokenProvider) {
        this.tokenProvider = tokenProvider;
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, String>> testLogin(@RequestBody Map<String, String> request) {
        String userId = request.get("userId");
        // seed.sql에 등록된 테스트 사용자로 JWT 토큰 발급
        String token = tokenProvider.createToken(userId);
        return ResponseEntity.ok(Map.of("accessToken", token));
    }
}
```

- `@Profile("dev")` → 개발 환경에서만 활성화, 프로덕션에 노출되지 않음
- seed.sql에 테스트용 사용자 데이터가 미리 등록되어 있어야 함

**3단계: 토큰 획득 및 사용**

```bash
# 테스트 토큰 획득
TOKEN=$(curl -s -X POST http://localhost:{auth_port}/api/test/login \
  -H 'Content-Type: application/json' \
  -d '{"userId": "test-user-01"}' | jq -r '.accessToken')

# 인증이 필요한 API 호출 시 토큰 사용
curl -X GET http://localhost:{port}/api/v1/{resource} \
  -H "Authorization: Bearer $TOKEN"
```

- 이후 모든 인증 필요 API 테스트에 `Authorization: Bearer $TOKEN` 헤더를 포함한다

### 테스트 실행
- 백킹 서비스 동시 기동
```bash
# 백킹서비스 기동
docker compose up -d
```
- 백엔드 서비스 시작: `{PLUGIN_DIR}/resources/tools/customs/general/run-backend.py` 이용 
- 필요시 AI 서비스 시작 
- 각 API 테스트 수행: API의 의존 관계를 분석하여 병렬 또는 순차 수행   
  예시)
  ```
  curl -X 'POST' \
   'http://localhost:8081/api/v1/users/login' \
   -H 'accept: */*' \
   -H 'Content-Type: application/json' \
   -d '{
   "username": "trip01",
   "password": "P@ssw0rd$",
   "rememberMe": true
  }'
  ```
- 테스트 결과 확인 및 Fix
  - 전체 PASS 확인
  - 실패 시: 실패 원인 분석 → 구현 코드 수정 → 재실행
  - 모든 테스트 PASS 될 때까지 반복

- 테스트 결과 등록: 'API 테스트 결과'파일에 저장

---

## 출력 형식

### api-test-result.md 작성 템플릿

```markdown
# API 테스트 결과

## 테스트 환경
- 테스트 일시: YYYY-MM-DD HH:MM
- 백킹서비스: docker compose (로컬)
- 백엔드 서비스: run-backend.py 기동

## API 목록

### {Service Name}
| ID | 엔드포인트 | 메서드 | 설명 | 결과 | 상태코드 | 비고 |
|----|-----------|--------|------|------|----------|------|
| API-001 | /api/v1/{resource} | POST | {설명} | PASS/FAIL | 201 | |
| API-002 | /api/v1/{resource}/{id} | GET | {설명} | PASS/FAIL | 200 | |

## 테스트 상세

### API-001: POST /api/v1/{resource}
**요청:**
\`\`\`bash
curl -X POST http://localhost:{port}/api/v1/{resource} \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $TOKEN' \
  -d @{service}/src/test/resources/data/request/create-{resource}.json
\`\`\`

**응답:** {상태코드}
\`\`\`json
{실제 응답 바디}
\`\`\`

**판정:** PASS / FAIL (사유: ...)

## 요약
- 전체 API 수: N개
- PASS: N개
- FAIL: N개
- PASS율: 100%
```

---

## 품질 기준

- [ ] Controller 레이어의 모든 API 엔드포인트가 테스트 목록에 포함됨 (누락 없음)
- [ ] 각 API의 정상 케이스(2xx) 응답이 확인됨
- [ ] 인증 필요 API에 대해 토큰 포함 호출이 수행됨
- [ ] seed.sql이 멱등하게 작성됨 (TRUNCATE → INSERT 순서)
- [ ] JSON fixture 파일이 API 설계서의 요청 스키마와 일치함
- [ ] 전체 API 테스트 PASS율 100%
- [ ] `docs/develop/api-test-result.md`가 위 템플릿 형식으로 작성됨
- [ ] 샘플 데이터가 `{service}/src/test/resources/data/` 하위에 정리됨

---

## 주의사항

- **빌드 실패 시 서비스 기동 금지**: `./gradlew clean build` 성공 확인 후 서비스를 기동한다. 빌드 실패 상태에서 테스트를 시도하지 않는다
- **서비스 기동은 반드시 run-backend.py 사용**: `./gradlew bootRun` 직접 실행 시 환경변수가 누락되므로 반드시 실행 프로파일 도구를 사용한다
- **테스트 실패 시 우회 금지**: API 응답이 기대와 다를 경우 테스트 기대값을 변경하지 말고 구현 코드를 수정한다
- **JPA 스키마 확인 필수**: seed.sql 작성 시 엔티티 클래스의 `@Column`, `@Table` 어노테이션이 아닌 JPA가 실제 생성한 테이블/컬럼명을 확인한다 (네이밍 전략에 따라 camelCase → snake_case 변환될 수 있음)
- **OAuth2 프로젝트의 토큰 획득**: 테스트 전용 엔드포인트(`@Profile("dev")`)를 통해 토큰을 획득한다. 외부 Provider 리디렉트는 AI 에이전트가 수행할 수 없다
- **API 의존 순서 준수**: 참조 관계가 있는 API는 선행 API를 먼저 호출한다 (예: 사용자 생성 → 주문 생성)
