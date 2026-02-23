# 백엔드 API 구현 가이드

## 목적

API 설계서 기반으로 서비스별 컨트롤러·서비스·레포지토리 레이어를 구현하고 단위 테스트를 작성한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 종합 개발 계획서 | `docs/develop/dev-plan.md` | 서비스 목록, 개발 순서, 의존성 |
| API 설계서 | `docs/design/api/{service-name}-api.yaml` | 엔드포인트 구현 기준 |
| 내부 시퀀스 설계서 | `docs/design/sequence/inner/{service-name}-*.puml` | 레이어 간 호출 흐름 |
| 클래스 설계서 | `docs/design/class/{service-name}.puml` | 클래스 구조 및 관계 |
| 데이터 설계서 | `docs/design/database/{service-name}.md` | 엔티티 필드, 관계, 인덱스 |
| Gradle 환경 | `settings.gradle`, `build.gradle`, `{service-name}/build.gradle` | 빌드 구성 (backend-env-setup.md 산출물) |
| 백킹서비스 연결 정보 | `.env.example` | DB/Redis/MQ 연결 설정 (backing-service-setup.md 산출물) |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| API 구현 코드 | `{service-name}/src/main/java/.../{service-name}/` |
| 단위 테스트 코드 | `{service-name}/src/test/java/.../{service-name}/` |

## 방법론

### 작성 원칙

- **개발주석표준** 준수: 모든 클래스·메서드에 표준 Javadoc 주석 작성 (`{PLUGIN_DIR}/resources/standards/standard_comment.md` 참조)
- **API 설계서 일관성**: `{service-name}-api.yaml`의 모든 엔드포인트를 누락 없이 Controller에 구현
- **설계 아키텍처 패턴 적용**: 서비스별로 지정된 패턴을 적용
  - **Layered 아키텍처**: Service 레이어에 Interface 사용 (`{ServiceName}Service` 인터페이스 + `{ServiceName}ServiceImpl` 구현체)
  - **Clean 아키텍처**: Port/Adapter 용어 대신 Clean 아키텍처 고유 용어 사용 (UseCase, Repository Port 등)
- **내부 시퀀스 설계서 일치**: `inner/{service-name}-*.puml`과 레이어 간 호출 흐름이 일치하도록 구현
- **클래스 설계서 일관성**: `{service-name}.puml`의 클래스 구조·관계를 그대로 반영
- **SecurityConfig/JWT/Swagger**: `{PLUGIN_DIR}/resources/references/java-security-jwt-swagger.md` (R3) 기반 구현
- **단위 테스트**: `{PLUGIN_DIR}/resources/references/java-test-guide.md` (R4) 기반 — Mockito 사용, 병렬 테스트 전략 적용

### 작성 순서

**준비**

- 서비스별 설계 산출물 분석: API 설계서, 내부 시퀀스, 클래스 설계서, 데이터 설계서 순서로 파악
- 서비스 간 의존성 분석: `dev-plan.md` 기반으로 독립 서비스와 의존 서비스를 구분 (병렬 처리 가이드 참조)
- 패키지 구조도 작성: `클래스설계서`와 일치하도록 모든 클래스·파일을 포함한 트리구조 텍스트로 작성
  - 결과 파일: `docs/develop/dev/{service-name}-package-structure.md`

**실행 (서비스별 반복)**

#### 1단계: JPA 엔티티 + 레포지토리 구현

데이터 설계서(`docs/design/database/{service-name}.md`)와 클래스 설계서 기반으로 구현한다.

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
- 내부 시퀀스 설계서에 나타나는 조회 조건을 `findBy...`, `@Query` 등으로 구현
- 복잡한 쿼리는 `@Query(value = "...", nativeQuery = true)` 또는 JPQL 사용

#### 2단계: 서비스 레이어 구현

내부 시퀀스 설계서(`docs/design/sequence/inner/{service-name}-*.puml`)의 흐름을 그대로 반영한다.

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
application/usecase/{CreateEntityUseCase}.java   ← UseCase 인터페이스
application/usecase/impl/{CreateEntityUseCaseImpl}.java
domain/port/{EntityRepositoryPort}.java          ← Repository Port 인터페이스
infrastructure/adapter/{EntityRepositoryAdapter}.java ← Port 구현체
```

**서비스 구현 공통 사항:**
- 트랜잭션 경계: 읽기 전용은 `@Transactional(readOnly = true)`, 쓰기는 `@Transactional`
- 비즈니스 예외: common 모듈의 커스텀 예외 클래스 사용 (`BusinessException`, `ResourceNotFoundException` 등)
- DTO 변환: MapStruct 또는 수동 변환 메서드 사용 (클래스 설계서 지정 방법 준수)

#### 3단계: 컨트롤러 구현

API 설계서(`docs/design/api/{service-name}-api.yaml`)의 모든 엔드포인트를 누락 없이 구현한다.

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

**SecurityConfig/JWT/SwaggerConfig 구현 (R3 참조):**

R3(`{PLUGIN_DIR}/resources/references/java-security-jwt-swagger.md`)의 예제를 그대로 적용한다.

- `SecurityConfig`: CSRF 비활성화, CORS 설정, Stateless 세션, JWT 필터 등록, 공개 경로(`/actuator/**`, `/swagger-ui/**`, `/v3/api-docs/**`, `/health`) 허용
- `JwtAuthenticationFilter`: `OncePerRequestFilter` 구현, Bearer 토큰 추출 및 `JwtTokenProvider`로 검증
- `JwtTokenProvider`: `@Component`, `${jwt.secret}` 주입, 토큰 검증·파싱 메서드 구현
- `UserPrincipal`: `userId`, `username`, `authority` 필드를 갖는 인증 Principal 객체
- `SwaggerConfig`: Bearer Authentication 보안 스킴, 서버 URL 설정 포함

**패키지 배치:**
```
{service-name}/src/main/java/.../
├── config/
│   ├── SecurityConfig.java
│   └── SwaggerConfig.java
└── security/
    ├── JwtAuthenticationFilter.java
    ├── JwtTokenProvider.java
    └── UserPrincipal.java
```

#### 4단계: 단위 테스트 작성

R4(`{PLUGIN_DIR}/resources/references/java-test-guide.md`) 및 테스트코드표준(`{PLUGIN_DIR}/resources/standards/standard_testcode.md`)을 준용한다.

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
```

## 출력 형식

### 서비스별 패키지 구조 예시

**Layered 아키텍처 적용 서비스:**
```
{service-name}/src/main/java/com/{company}/{system}/{service-name}/
├── config/
│   ├── SecurityConfig.java          ← Spring Security 설정 (R3)
│   └── SwaggerConfig.java           ← OpenAPI 문서 설정 (R3)
├── controller/
│   └── {ServiceName}Controller.java ← REST 컨트롤러
├── service/
│   ├── {ServiceName}Service.java    ← 서비스 인터페이스
│   └── impl/
│       └── {ServiceName}ServiceImpl.java
├── repository/
│   └── {EntityName}Repository.java  ← JPA 레포지토리
├── domain/
│   └── {EntityName}.java            ← JPA 엔티티
├── dto/
│   ├── request/
│   │   └── {EntityName}CreateRequest.java
│   └── response/
│       └── {EntityName}Response.java
├── security/
│   ├── JwtAuthenticationFilter.java ← JWT 인증 필터 (R3)
│   ├── JwtTokenProvider.java        ← JWT 토큰 제공자 (R3)
│   └── UserPrincipal.java           ← 인증 사용자 정보 (R3)
└── exception/
    └── {ServiceName}Exception.java  ← 서비스 커스텀 예외

{service-name}/src/test/java/com/{company}/{system}/{service-name}/
├── controller/
│   └── {ServiceName}ControllerTest.java
├── service/
│   └── {ServiceName}ServiceImplTest.java
└── repository/
    └── {EntityName}RepositoryTest.java
```

**Clean 아키텍처 적용 서비스:**
```
{service-name}/src/main/java/com/{company}/{system}/{service-name}/
├── config/
│   ├── SecurityConfig.java
│   └── SwaggerConfig.java
├── application/
│   └── usecase/
│       ├── {CreateEntity}UseCase.java       ← UseCase 인터페이스
│       └── impl/
│           └── {CreateEntity}UseCaseImpl.java
├── domain/
│   ├── model/
│   │   └── {EntityName}.java                ← 도메인 모델
│   └── port/
│       └── {EntityName}RepositoryPort.java  ← Repository Port
├── infrastructure/
│   ├── adapter/
│   │   └── {EntityName}RepositoryAdapter.java ← Port 구현체
│   ├── entity/
│   │   └── {EntityName}Entity.java          ← JPA 엔티티
│   └── repository/
│       └── {EntityName}JpaRepository.java
├── presentation/
│   └── {ServiceName}Controller.java
└── security/
    ├── JwtAuthenticationFilter.java
    ├── JwtTokenProvider.java
    └── UserPrincipal.java
```

## 품질 기준

- [ ] API 설계서(`{service-name}-api.yaml`)의 모든 엔드포인트 구현 (누락 없음)
- [ ] 단위 테스트 작성 완료 (테스트코드표준 + R4 준수)
- [ ] 모든 서비스 `compileJava` 성공
- [ ] 단위 테스트 전체 통과
- [ ] SecurityConfig, JWT 인증처리, SwaggerConfig 포함 (R3 기반)
- [ ] 개발주석표준에 맞는 Javadoc 주석 작성
- [ ] 서비스별 아키텍처 패턴(Layered/Clean) 일관성 유지

## 주의사항

- 설계 아키텍처 패턴(Layered/Clean)은 서비스별로 다를 수 있으므로 `dev-plan.md`에서 서비스별 패턴을 반드시 확인
- SecurityConfig의 공개 경로 설정은 API 설계서의 인증 요구 여부를 기준으로 조정
- 테스트 설정 Manifest(`src/test/resources/application.yml`)의 값은 환경변수 처리 (하드코딩 금지)
- 테스트 실패 시 테스트 코드를 우회하는 방식이 아닌 프로덕션 코드의 로직을 수정하여 해결
- 참조: 개발주석표준 — `{PLUGIN_DIR}/resources/standards/standard_comment.md`
- 참조: 테스트코드표준 — `{PLUGIN_DIR}/resources/standards/standard_testcode.md`
- 참조: SecurityConfig/JWT/Swagger 예제 (R3) — `{PLUGIN_DIR}/resources/references/java-security-jwt-swagger.md`
- 참조: 테스트 가이드 (R4) — `{PLUGIN_DIR}/resources/references/java-test-guide.md`
- `{PLUGIN_DIR}` = `~/.claude/plugins/cache/npd/npd/{version}/`
