# 백엔드 API 구현 가이드

## 목적

API 설계서 기반으로 서비스별 컨트롤러·서비스·레포지토리 레이어를 구현하고 단위 테스트를 작성한다.

## 입력 (이전 단계 산출물)

| 산출물 | 탐색 방법 | 활용 방법 |
|--------|----------|----------|
| 종합 개발 계획서 (통합 맥락) | `docs/develop/dev-plan.md` | 서비스 목록, 개발 순서, 의존성, 아키텍처 결정사항 |
| API 설계서 | `docs/design/api/` 하위 `*.yaml` | 엔드포인트 구현 기준 |
| 데이터 설계서 | `docs/design/database/` 하위 `*.md` | 엔티티 필드, 관계, 인덱스 |
| 패키지 구조 | `docs/design/class/package-structure.md` | 패키지 레이아웃 |
| 행위 계약 테스트 | `test/design-contract/{service-name}/` | **행위 참고 자료** — alt/else 분기를 참고하여 구현 시 누락 방지 |
| Gradle 환경 | `settings.gradle`, `build.gradle` | 빌드 구성 |
| 백킹서비스 연결 정보 | `.env.example` | DB/Redis/MQ 연결 설정 |
| 보안·JWT·Swagger 표준 | `{PLUGIN_DIR}/resources/references/java-security-jwt-swagger.md` | JWT 인증, Swagger 설정 표준 |
| 테스트 코드 가이드 | `{PLUGIN_DIR}/resources/references/java-test-guide.md` | 단위 테스트 작성 표준 |
| 서비스 실행기 | `{PLUGIN_DIR}/resources/tools/customs/general/run-backend.py` | 서비스 기동 검증 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| API 구현 코드 | `{service-name}/src/main/java/.../{service-name}/` |
| 단위 테스트 코드 | `{service-name}/src/test/java/.../{service-name}/` |

## 방법론

### 작성 원칙

- **Java 패키지 그룹명 표준**: 모든 소스 코드의 패키지는 `com.{ORG}.{ROOT}.{service-name}` 형식을 사용한다 (`{PLUGIN_DIR}/resources/references/standard_package_structure.md` 참조). `{ORG}`, `{ROOT}` 값은 `CLAUDE.md`에서 읽으며, 설계서에 다른 패키지명이 있더라도 이 표준으로 강제 통일한다.
- **개발주석표준** 준수: 모든 클래스·메서드에 표준 Javadoc 주석 작성 (`{PLUGIN_DIR}/resources/references/standard_comment.md` 참조)
- **API 설계서 일관성**: API 설계서(`docs/design/api/` 하위 — 준비 단계에서 식별한 파일)의 모든 엔드포인트를 누락 없이 Controller에 구현
- **설계 아키텍처 패턴 적용**: 서비스별로 지정된 패턴을 적용
  - **Layered 아키텍처**: Service 레이어에 Interface 사용 (`{ServiceName}Service` 인터페이스 + `{ServiceName}ServiceImpl` 구현체)
  - **Clean 아키텍처**: Port/Adapter 용어 대신 Clean 아키텍처 고유 용어 사용 (UseCase, Gateway 등)
- **행위 계약 참고**: 행위 계약 테스트(`test/design-contract/{service-name}/`)의 각 it() 케이스를 참고하여 구현 시 alt/else 분기를 누락하지 않도록 한다 (테스트 실행은 불요)
- **인증 방식은 설계서에서 확인 후 적용**: `docs/develop/dev-plan.md` 섹션 10-3의 인증 방식 및 API 설계서의 `components/securitySchemes`에서 인증 방식을 식별한다
  - **JWT 인증**: `{PLUGIN_DIR}/resources/references/java-security-jwt-swagger.md` (R3) 기반 구현
  - **OAuth2/OIDC (소셜 로그인 — Google, 카카오, 네이버 등)**: Spring Security OAuth2 Client 기반 구현
  - 설계서에 인증 방식이 명시되지 않은 경우 클래스 설계서의 Security 관련 클래스를 확인하여 판단
- **단위 테스트**: `{PLUGIN_DIR}/resources/references/java-test-guide.md` (R4) 기반 — Mockito 사용, 병렬 테스트 전략 적용

### 작성 순서

**준비**

**설계 산출물 탐색 절차:**
```
1. docs/develop/dev-plan.md를 읽어 서비스 목록, 입력 파일 매핑(섹션 8) 확인
2. 매핑 테이블에 명시된 파일만 로드:
   - API 명세: docs/design/api/{service-name}-api.yaml
   - DB 설계: docs/design/database/{service-name}.md
   - 패키지 구조: docs/design/class/package-structure.md
3. 행위 계약 테스트 확인: test/design-contract/{service-name}/*.spec.ts
4. 누락 파일이 있으면 오케스트레이터에 보고 (직접 탐색하지 않음)
```

- 서비스별 설계 산출물 분석: API 설계서, 데이터 설계서, 행위 계약 테스트 순서로 파악
- 서비스 간 의존성 분석: `dev-plan.md` 기반으로 독립 서비스와 의존 서비스를 구분 (병렬 처리 가이드 참조)
- 패키지 구조도 작성: `클래스설계서`와 일치하도록 모든 클래스·파일을 포함한 트리구조 텍스트로 작성
  - 결과 파일: `docs/develop/dev/{service-name}-package-structure.md`

**실행 (서비스별 반복)**

#### 1단계: JPA 엔티티 + 레포지토리 구현

데이터 설계서(`docs/design/database/` 하위 — 준비 단계에서 식별한 파일)와 클래스 설계서 기반으로 구현한다.

**엔티티 작성 기준:**
- `@Entity`, `@Table(name = "...")` 명시
- PK는 `@GeneratedValue(strategy = GenerationType.IDENTITY)` 또는 설계서 지정 전략 적용
- 연관관계 매핑: 설계서의 ERD 관계(1:N, N:M 등)를 `@OneToMany`, `@ManyToOne`, `@ManyToMany`로 구현
- Auditing 공통 필드(`createdAt`, `updatedAt`)는 common 모듈의 BaseEntity 상속
- `@Column` 제약조건(`nullable`, `length`, `unique`)은 데이터 설계서의 제약조건과 일치

```
{service-name}/src/main/java/.../
└── domain/
    ├── {EntityName}.java          ← @Entity 클래스
    └── {EntityName}Repository.java ← JpaRepository 확장 인터페이스
```

**레포지토리 작성 기준:**
- `JpaRepository<{Entity}, {IdType}>` 상속
- 행위 계약 테스트의 시나리오에 나타나는 조회 조건을 `findBy...`, `@Query` 등으로 구현
- 복잡한 쿼리는 `@Query(value = "...", nativeQuery = true)` 또는 JPQL 사용

#### 2단계: 서비스 레이어 구현

dev-plan.md의 서비스별 내부 흐름 설명과 design-contract test의 시나리오를 참고하여 구현한다.
행위 계약 테스트(test/design-contract/{service-name}/*.spec.ts)의 각 it() 케이스를 참고하여 구현해야 할 행위 목록을 파악한다.

**Layered 아키텍처 적용 시:**
```java
// 인터페이스 (필수)
public interface {ServiceName}Service {
    {ResponseDto} create{Entity}({RequestDto} request);
    {ResponseDto} get{Entity}(Long id);
    // API 설계서의 비즈니스 오퍼레이션 목록
}

// 구현체
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class {ServiceName}ServiceImpl implements {ServiceName}Service {
    private final {EntityName}Repository {entityName}Repository;
    // ...
}
```

**Clean 아키텍처 적용 시:**
```
biz/usecase/in/{CreateEntityUseCase}.java        ← 인바운드 UseCase 인터페이스
biz/service/{ServiceName}Service.java            ← UseCase 구현체
biz/usecase/out/{EntityReader}.java              ← 아웃바운드 UseCase 인터페이스
infra/gateway/{EntityGateway}.java               ← 아웃바운드 구현체
```
> Port/Adapter 용어 사용 금지 — `패키지구조표준`(`{PLUGIN_DIR}/resources/references/standard_package_structure.md`) 준수

**서비스 구현 공통 사항:**
- 트랜잭션 경계: 읽기 전용은 `@Transactional(readOnly = true)`, 쓰기는 `@Transactional`
- 비즈니스 예외: common 모듈의 커스텀 예외 클래스 사용 (`BusinessException`, `ResourceNotFoundException` 등)
- DTO 변환: MapStruct 또는 수동 변환 메서드 사용 (클래스 설계서 지정 방법 준수)

#### 3단계: 컨트롤러 구현

API 설계서(`docs/design/api/` 하위 — 준비 단계에서 식별한 파일)의 모든 엔드포인트를 누락 없이 구현한다.

**컨트롤러 작성 기준:**
```java
/**
 * {서비스명} API 컨트롤러
 * {API 설계서의 서비스 설명}
 */
@RestController
@RequestMapping("/api/v1/{resource}")
@RequiredArgsConstructor
@Tag(name = "{서비스명}", description = "{API 설계서의 태그 설명}")
public class {ServiceName}Controller {

    private final {ServiceName}Service {serviceName}Service;

    /**
     * {API 설계서의 operationId 및 summary}
     */
    @Operation(summary = "...", description = "...")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "인증 필요"),
        @ApiResponse(responseCode = "404", description = "리소스 없음")
    })
    @PostMapping
    public ResponseEntity<{ResponseDto}> create(
            @Valid @RequestBody {RequestDto} request,
            @AuthenticationPrincipal UserPrincipal userPrincipal) {
        return ResponseEntity.ok({serviceName}Service.create(request));
    }
}
```

**SecurityConfig/인증/SwaggerConfig 구현:**

먼저 인증 방식을 식별한다:
1. `docs/develop/dev-plan.md` 섹션 10-3의 인증 방식 확인
2. API 설계서(`docs/design/api/*.yaml`)의 `components/securitySchemes` 확인
3. `docs/develop/dev-plan.md` 섹션 10-3의 Security 클래스 목록 확인

**[JWT 인증인 경우]**

R3(`{PLUGIN_DIR}/resources/references/java-security-jwt-swagger.md`)의 예제를 적용한다.

- `SecurityConfig`: CSRF 비활성화, CORS 설정, Stateless 세션, JWT 필터 등록, 공개 경로(`/actuator/**`, `/swagger-ui/**`, `/v3/api-docs/**`, `/health`) 허용
- `JwtAuthenticationFilter`: `OncePerRequestFilter` 구현, Bearer 토큰 추출 및 `JwtTokenProvider`로 검증
- `JwtTokenProvider`: `@Component`, `${jwt.secret}` 주입, 토큰 검증·파싱 메서드 구현
- `UserPrincipal`: `userId`, `username`, `authority` 필드를 갖는 인증 Principal 객체
- `SwaggerConfig`: Bearer Authentication 보안 스킴, 서버 URL 설정 포함

**CORS 설정 필수 준수사항:**
- CORS Origin은 반드시 `@Value("${cors.allowed-origins:...}")`로 환경변수 주입해야 한다 — `List.of("http://localhost:*")` 같은 **하드코딩 금지**
- `application.yml`에 `cors.allowed-origins: ${CORS_ALLOWED_ORIGINS:}` 항목을 반드시 포함한다 (`java-config-manifest-standard.md` 표준)
- 공통 모듈로 분리하더라도 환경변수 주입 구조(`@Value`)는 R3 예제와 동일하게 유지할 것
- 운영 환경에서 `CORS_ALLOWED_ORIGINS` 환경변수로 허용 도메인을 제어할 수 있어야 한다

패키지 배치:
```
config/
├── SecurityConfig.java
├── SwaggerConfig.java
└── jwt/
    ├── JwtAuthenticationFilter.java
    ├── JwtTokenProvider.java
    ├── CustomUserDetailsService.java
    └── UserPrincipal.java
```

**[OAuth2/OIDC 소셜 로그인인 경우]** (Google, 카카오, 네이버 등)

> **전제 조건**: OAuth2 Provider의 Client ID/Secret이 `.env`에 설정되어 있어야 통합 테스트가 가능하다.
> 오케스트레이터(SKILL.md)가 Step 3 진입 전에 사용자에게 크리덴셜을 요청하므로, 이 가이드 실행 시점에는 이미 `.env`에 설정되어 있거나 "코드 구현만 진행" 지시를 받은 상태이다.
> - 크리덴셜이 `.env`에 있으면: 코드 구현 + 통합 테스트 모두 수행
> - "코드 구현만 진행" 지시를 받으면: 코드 구현만 수행, 통합 테스트는 SKIP하고 결과에 "OAuth2 크리덴셜 미설정으로 통합 테스트 생략" 기재
>
> Provider별 앱 등록 및 전체 구현 패턴 가이드: `{PLUGIN_DIR}/resources/guides/develop/oauth-guide.md`
> — GitHub/Google/Kakao OAuth App 설정, Spring Boot + 프론트엔드(React/Vue/Flutter) 구현 전체 패턴 포함

Spring Security OAuth2 Client (`spring-boot-starter-oauth2-client`) 기반으로 구현한다. 설계서에 명시된 Provider만 구현한다.

- `SecurityConfig`: OAuth2 Login 설정, `oauth2Login()` → `userInfoEndpoint()` → `userService()` 체인 구성, 로그인 성공/실패 핸들러 등록, 공개 경로 허용
- `OAuth2UserService` 구현: Provider별 사용자 정보 매핑 (`registrationId`로 분기)
- `OAuth2SuccessHandler`: 인증 성공 후 JWT 발급 또는 세션 생성 (설계서 기준)
- `SwaggerConfig`: OAuth2 Authorization Code 보안 스킴 설정

`application.yml` 설정:
```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          google:   # 설계서에 Google 로그인이 있는 경우
            client-id: ${GOOGLE_CLIENT_ID}
            client-secret: ${GOOGLE_CLIENT_SECRET}
            scope: openid, profile, email
          kakao:    # 설계서에 카카오 로그인이 있는 경우
            client-id: ${KAKAO_CLIENT_ID}
            client-secret: ${KAKAO_CLIENT_SECRET}
            authorization-grant-type: authorization_code
            redirect-uri: "{baseUrl}/login/oauth2/code/kakao"
            client-authentication-method: client_secret_post
          naver:    # 설계서에 네이버 로그인이 있는 경우
            client-id: ${NAVER_CLIENT_ID}
            client-secret: ${NAVER_CLIENT_SECRET}
            authorization-grant-type: authorization_code
            redirect-uri: "{baseUrl}/login/oauth2/code/naver"
        provider:
          kakao:
            authorization-uri: https://kauth.kakao.com/oauth/authorize
            token-uri: https://kauth.kakao.com/oauth/token
            user-info-uri: https://kapi.kakao.com/v2/user/me
            user-name-attribute: id
          naver:
            authorization-uri: https://nid.naver.com/oauth2.0/authorize
            token-uri: https://nid.naver.com/oauth2.0/token
            user-info-uri: https://openapi.naver.com/v1/nid/me
            user-name-attribute: response
```

패키지 배치:
```
config/
├── SecurityConfig.java
├── SwaggerConfig.java
└── oauth2/
    ├── CustomOAuth2UserService.java
    ├── OAuth2SuccessHandler.java
    ├── OAuth2FailureHandler.java
    └── OAuth2UserPrincipal.java
```

**[JWT + OAuth2 하이브리드인 경우]** (소셜 로그인 후 자체 JWT 발급)

OAuth2 인증 성공 후 자체 JWT를 발급하는 패턴. 위 두 설정을 조합한다.

- `OAuth2SuccessHandler`에서 `JwtTokenProvider`를 사용해 JWT 발급
- API 호출은 JWT로 인증 (Bearer 토큰), 로그인은 OAuth2로 처리

패키지 배치:
```
config/
├── SecurityConfig.java
├── SwaggerConfig.java
├── jwt/
│   ├── JwtAuthenticationFilter.java
│   ├── JwtTokenProvider.java
│   └── UserPrincipal.java
└── oauth2/
    ├── CustomOAuth2UserService.java
    ├── OAuth2SuccessHandler.java     ← JwtTokenProvider 주입하여 토큰 발급
    └── OAuth2FailureHandler.java
```

> 패키지 구조 표준: `{PLUGIN_DIR}/resources/references/standard_package_structure.md` 준수

#### 4단계: 단위 테스트 작성

R4(`{PLUGIN_DIR}/resources/references/java-test-guide.md`) 및 테스트코드표준(`{PLUGIN_DIR}/resources/references/standard_testcode.md`)을 준용한다.

**Mockito 사용 원칙:**
- 외부 의존성(Repository, 외부 서비스)은 `@Mock`으로 모킹
- 테스트 대상 클래스는 `@InjectMocks`로 주입
- `@ExtendWith(MockitoExtension.class)` 사용 (Spring Context 불필요)
- `given(...).willReturn(...)` 스타일의 BDD Mockito 사용 권장

**서비스 레이어 테스트 예시:**
```java
@ExtendWith(MockitoExtension.class)
class {ServiceName}ServiceImplTest {

    @Mock
    private {EntityName}Repository {entityName}Repository;

    @InjectMocks
    private {ServiceName}ServiceImpl {serviceName}Service;

    /**
     * 정상 케이스: {엔티티} 생성 성공
     */
    @Test
    @DisplayName("{엔티티} 생성 - 정상 케이스")
    void create{Entity}_success() {
        // given
        {RequestDto} request = {RequestDto}.builder()...build();
        {Entity} saved = {Entity}.builder()...build();
        given({entityName}Repository.save(any())).willReturn(saved);

        // when
        {ResponseDto} result = {serviceName}Service.create{Entity}(request);

        // then
        assertThat(result).isNotNull();
        assertThat(result.getId()).isEqualTo(saved.getId());
        verify({entityName}Repository, times(1)).save(any());
    }

    /**
     * 예외 케이스: 존재하지 않는 {엔티티} 조회
     */
    @Test
    @DisplayName("{엔티티} 조회 - 존재하지 않으면 예외 발생")
    void get{Entity}_notFound_throwsException() {
        // given
        given({entityName}Repository.findById(anyLong())).willReturn(Optional.empty());

        // when & then
        assertThatThrownBy(() -> {serviceName}Service.get{Entity}(1L))
            .isInstanceOf(ResourceNotFoundException.class);
    }
}
```

**컨트롤러 레이어 테스트 예시:**
```java
@WebMvcTest({ServiceName}Controller.class)
@Import(SecurityConfig.class)
class {ServiceName}ControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private {ServiceName}Service {serviceName}Service;

    @MockBean
    private JwtTokenProvider jwtTokenProvider;

    @Test
    @DisplayName("POST /api/v1/{resource} - 생성 성공 200")
    void create_success() throws Exception {
        // given
        {ResponseDto} response = {ResponseDto}.builder()...build();
        given({serviceName}Service.create(any())).willReturn(response);

        // when & then
        mockMvc.perform(post("/api/v1/{resource}")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request))
                .header("Authorization", "Bearer {test-token}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(response.getId()));
    }
}
```

**서브에이전트 병렬 테스트 전략 (R4 기반):**
- 서비스가 2개 이상이면 서비스별로 서브에이전트를 할당하여 테스트 코드를 동시에 작성
- 테스트 설정 Manifest(`src/test/resources/application.yml`) 값은 환경변수 처리 (하드코딩 금지)
- 테스트 실패 시 오류 해결 후 전체 성공할 때까지 재수행

**테스트 파일 네이밍:**
- 클래스: `{TargetClass}Test.java`
- 메서드: `{메서드명}_{시나리오}_{기대결과}()` 형식
- 패키지: 프로덕션 코드와 동일한 패키지 구조 유지

#### 5단계: 컴파일 및 에러 해결

```bash
# 서비스별 컴파일 검증
./gradlew {service-name}:compileJava

# 단위 테스트 실행
./gradlew {service-name}:test

# Windows에서는 gradlew.bat 사용
.\gradlew.bat {service-name}:compileJava
```

컴파일 에러 발생 시 에러 메시지를 분석하여 해결하고 재컴파일한다. 테스트 실패 시 프로덕션 코드의 로직을 수정하여 해결한다 (테스트 코드를 우회하는 방식 금지).

**검토**
- 컴파일 성공 여부 확인
- 단위 테스트 전체 통과 여부 확인
- API 설계서 엔드포인트 누락 여부 확인

#### 참고: 행위 계약 테스트 활용

> **이 단계는 실행하지 않는다.** 행위 계약 테스트는 참고 자료로만 활용한다.

`test/design-contract/{service-name}/*.spec.ts`의 it() 케이스를 참고하여:
- 구현해야 할 API 행위(alt/else 분기)가 누락되지 않았는지 확인
- 각 분기의 기대 HTTP 상태코드와 응답 구조를 참조

실제 검증은 Step 4(API 테스트 + 브라우저 테스트)에서 수행한다.

#### 6단계: 서비스 기동 검증

컴파일과 단위 테스트를 통과해도 런타임에 빈 주입 실패, 설정 누락 등의 오류가 발생할 수 있다. `run-backend.py`를 사용하여 실제 서비스 기동을 확인한다.

이 도구는 IntelliJ `.run/*.run.xml` 실행 프로파일에서 환경변수(DB 접속 정보, 포트 등)를 추출하여 `gradlew bootRun`에 주입한다. `./gradlew bootRun`을 직접 실행하면 환경변수가 누락되므로 반드시 이 도구를 사용한다.

**서비스 기동:**
```bash
# 개별 서비스 기동
python3 {PLUGIN_DIR}/resources/tools/customs/general/run-backend.py {service-name}
```

**기동 확인:**
```bash
curl -s http://localhost:{port}/actuator/health
# {"status":"UP"} 응답 확인
```

**기동 실패 시:** 로그(`logs/{service-name}.log`)에서 에러를 분석하여 코드 수정 후 재시도한다.

**서비스 중지:**
```bash
# 개별 서비스 중지
python3 {PLUGIN_DIR}/resources/tools/customs/general/run-backend.py --stop {service-name}

# 전체 서비스 중지
python3 {PLUGIN_DIR}/resources/tools/customs/general/run-backend.py --stop
```

### 병렬 처리 가이드

`dev-plan.md`의 서비스 목록을 분석하여 의존 관계를 파악한다.

- **독립 서비스**: 다른 서비스의 API를 직접 호출하지 않는 서비스 → 서브에이전트로 병렬 구현
- **의존 서비스**: 선행 서비스의 API를 호출하거나 공유 도메인 모델을 사용하는 서비스 → 선행 서비스 컴파일 성공 후 구현 시작

```
예시 (3개 서비스, user-service가 공통 의존):
  [user-service] ──완료 후──→ [order-service]
  [product-service] ──────────────────────────→ (병렬)
```

의존성 분석 방법은 `common-principles.md`의 의존성 분석 가이드를 적용한다.

### 검증 방법

```bash
# 전체 서비스 컴파일 검증
./gradlew compileJava

# 특정 서비스 테스트
./gradlew {service-name}:test

# 테스트 결과 리포트 확인
# {service-name}/build/reports/tests/test/index.html

# 서비스 기동 검증 (run-backend.py 사용)
python3 {PLUGIN_DIR}/resources/tools/customs/general/run-backend.py {service-name}
curl -s http://localhost:{port}/actuator/health
```

## 출력 형식

### 서비스별 패키지 구조 예시

> 패키지 구조는 `{PLUGIN_DIR}/resources/references/standard_package_structure.md`를 준수한다.

**Layered 아키텍처 적용 서비스:**
```
{service-name}/src/main/java/com/{ORG}/{ROOT}/{service-name}/
├── {ServiceName}Application.java
├── config/
│   ├── SecurityConfig.java          ← Spring Security 설정
│   ├── SwaggerConfig.java           ← OpenAPI 문서 설정
│   ├── jwt/                         ← [JWT 인증 시] JWT 인증 관련 (R3)
│   │   ├── JwtAuthenticationFilter.java
│   │   ├── JwtTokenProvider.java
│   │   ├── CustomUserDetailsService.java
│   │   └── UserPrincipal.java
│   └── oauth2/                      ← [OAuth2 인증 시] 소셜 로그인 관련
│       ├── CustomOAuth2UserService.java
│       ├── OAuth2SuccessHandler.java
│       ├── OAuth2FailureHandler.java
│       └── OAuth2UserPrincipal.java
├── controller/
│   └── {ServiceName}Controller.java ← REST 컨트롤러
├── dto/
│   ├── request/
│   │   └── {EntityName}CreateRequest.java
│   └── response/
│       └── {EntityName}Response.java
├── service/
│   ├── {ServiceName}Service.java    ← 서비스 인터페이스
│   └── {ServiceName}ServiceImpl.java ← 구현체 (impl/ 하위 패키지 사용 금지)
├── domain/
│   └── {EntityName}.java            ← 도메인 모델
├── repository/
│   ├── entity/
│   │   └── {EntityName}Entity.java  ← JPA 엔티티
│   └── jpa/
│       └── {EntityName}Repository.java ← JPA 레포지토리
└── exception/                       ← [optional] 서비스 고유 예외
    └── {ServiceName}Exception.java

{service-name}/src/test/java/com/{ORG}/{ROOT}/{service-name}/
├── controller/
│   └── {ServiceName}ControllerTest.java
├── service/
│   └── {ServiceName}ServiceImplTest.java
└── repository/
    └── jpa/
        └── {EntityName}RepositoryTest.java
```

**Clean 아키텍처 적용 서비스:**
```
{service-name}/src/main/java/com/{ORG}/{ROOT}/{service-name}/
├── biz/                             ← 비즈니스 계층
│   ├── usecase/
│   │   ├── in/                      ← 인바운드 UseCase
│   │   │   └── {Action}UseCase.java
│   │   └── out/                     ← 아웃바운드 UseCase
│   │       └── {Entity}Reader.java
│   ├── service/
│   │   └── {ServiceName}Service.java ← UseCase 구현체
│   ├── domain/
│   │   └── {EntityName}.java        ← 도메인 모델
│   └── dto/
│       ├── request/
│       │   └── {Entity}Request.java
│       └── response/
│           └── {Entity}Response.java
├── infra/                           ← 인프라 계층
│   ├── {ServiceName}Application.java
│   ├── controller/
│   │   └── {ServiceName}Controller.java
│   ├── config/
│   │   ├── SecurityConfig.java
│   │   ├── SwaggerConfig.java
│   │   ├── jwt/                     ← [JWT 인증 시]
│   │   │   ├── JwtAuthenticationFilter.java
│   │   │   ├── JwtTokenProvider.java
│   │   │   ├── CustomUserDetailsService.java
│   │   │   └── UserPrincipal.java
│   │   └── oauth2/                  ← [OAuth2 인증 시]
│   │       ├── CustomOAuth2UserService.java
│   │       ├── OAuth2SuccessHandler.java
│   │       ├── OAuth2FailureHandler.java
│   │       └── OAuth2UserPrincipal.java
│   └── gateway/                     ← 외부 연동 (Port/Adapter 용어 금지)
│       ├── entity/
│       │   └── {EntityName}Entity.java
│       ├── repository/
│       │   └── {EntityName}JpaRepository.java
│       └── {EntityName}Gateway.java
└── exception/                       ← [optional] 서비스 고유 예외

{service-name}/src/test/java/com/{ORG}/{ROOT}/{service-name}/
├── biz/
│   └── service/
│       └── {ServiceName}ServiceTest.java
└── infra/
    ├── controller/
    │   └── {ServiceName}ControllerTest.java
    └── gateway/
        └── {EntityName}GatewayTest.java
```

## 품질 기준

- [ ] API 설계서(준비 단계에서 식별한 파일)의 모든 엔드포인트 구현 (누락 없음)
- [ ] 단위 테스트 작성 완료 (테스트코드표준 + R4 준수)
- [ ] 모든 서비스 `compileJava` 성공
- [ ] 단위 테스트 전체 통과
- [ ] 서비스 기동 확인 (`actuator/health` UP 응답)
- [ ] SecurityConfig, 인증 처리(설계서 기반 — JWT/OAuth2/하이브리드), SwaggerConfig 포함
- [ ] 개발주석표준에 맞는 Javadoc 주석 작성
- [ ] 서비스별 아키텍처 패턴(Layered/Clean) 일관성 유지
- [ ] **TODO/FIXME/HACK 0건**: `grep -rn "TODO\|FIXME\|HACK" {service-name}/src/` 결과가 0건이어야 한다
- [ ] **핵심 API 실호출 검증**: 서비스 기동 후 최소 1개 핵심 API에 `curl` 호출하여 정상 응답(2xx) 확인
- [ ] **행위 계약 참고 확인**: `test/design-contract/{service-name}/*.spec.ts`의 it() 케이스 목록과 구현된 API 행위를 대조하여 누락 없음을 확인

## 주의사항

- **TODO/FIXME/HACK 금지**: 모든 코드는 완전하게 구현한다. "TODO: 나중에 구현", "FIXME: 임시 처리" 등의 미완성 마커를 남기지 않는다. 구현이 어려운 부분이 있으면 우회하지 말고 근본 원인을 해결한다
- **런타임 에러 워크어라운드 금지**: 런타임 에러 발생 시 try-catch로 삼키거나, 기능을 비활성화하거나, 하드코딩 값으로 대체하는 등의 우회 해결을 금지한다. 반드시 근본 원인을 분석하고 정상 동작하도록 수정한다
- **서비스 기동 검증 필수**: 컴파일과 단위 테스트 통과만으로는 완료가 아니다. `run-backend.py`로 실제 기동하여 `actuator/health`가 UP 응답을 반환해야 한다
- 설계 아키텍처 패턴(Layered/Clean)은 서비스별로 다를 수 있으므로 `dev-plan.md`에서 서비스별 패턴을 반드시 확인
- SecurityConfig의 공개 경로 설정은 API 설계서의 인증 요구 여부를 기준으로 조정
- 테스트 설정 Manifest(`src/test/resources/application.yml`)의 값은 환경변수 처리 (하드코딩 금지)
- 테스트 실패 시 테스트 코드를 우회하는 방식이 아닌 프로덕션 코드의 로직을 수정하여 해결
- 참조: 개발주석표준 — `{PLUGIN_DIR}/resources/references/standard_comment.md`
- 참조: 테스트코드표준 — `{PLUGIN_DIR}/resources/references/standard_testcode.md`
- 인증 방식은 설계서(`high-level-architecture.md` 보안 요구사항 + API 설계서 securitySchemes)에서 확인 후 적용. 무조건 JWT로 구현하지 않을 것
- 참조: SecurityConfig/JWT/Swagger 예제 (R3) — `{PLUGIN_DIR}/resources/references/java-security-jwt-swagger.md` (JWT 인증인 경우만 적용)
- 참조: 테스트 가이드 (R4) — `{PLUGIN_DIR}/resources/references/java-test-guide.md`
- `{PLUGIN_DIR}` = `~/.claude/plugins/cache/npd/npd/{version}/`
