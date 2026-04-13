# 백엔드-AI 서비스 연동 가이드

## 목적

백엔드 서비스에서 AI 서비스를 호출하는 연동 코드를 구현하고, 장애 격리 패턴(Circuit Breaker, Fallback)을 설정한다.

## 입력 (이전 단계 산출물)

| 산출물 | 탐색 방법 | 활용 방법 |
|--------|----------|----------|
| 백엔드 API 코드 | `{service-name}/src/main/java/.../` | 연동 코드를 추가할 서비스 레이어 위치 확인 (backend-api-dev.md 산출물) |
| AI 서비스 실제 코드 | AI 서비스 router/controller 코드 (어노테이션/패턴 기반 탐색) | AI 서비스 엔드포인트, 요청/응답 스펙 확인 (ai-service-dev.md 산출물) |
| AI 서비스 설계서 | `docs/design/ai-service-design.md` | 연동 설계, 장애 격리 패턴, SKIP 여부 판단 기준 |
| 종합 개발 계획서 (통합 맥락) | `docs/develop/dev-plan.md` | BE↔AI 연동 시나리오, 의존관계 |
| 행위 계약 테스트 | `test/design-contract/integration/*.spec.ts` | BE↔AI 연동 행위 계약 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 (Layered) | 파일 경로 (Clean) |
|--------|----------|----------|
| AI 서비스 클라이언트 인터페이스 | `.../client/AiServiceClient.java` | `.../biz/usecase/out/AiServiceCaller.java` |
| HTTP 클라이언트 구현체 | `.../client/AiServiceClientImpl.java` | `.../infra/gateway/client/AiServiceClient.java` |
| Circuit Breaker 설정 | `{service-name}/src/main/resources/application.yml` (resilience4j 섹션) | 동일 |
| 통합 테스트 코드 | `.../client/AiServiceClientTest.java` | `.../infra/gateway/client/AiServiceClientTest.java` |

> 경로의 `...`는 `{service-name}/src/main/java/com/{ORG}/{ROOT}/{service-name}` (테스트는 `src/test/java/...`)을 의미한다.

## 방법론

### SKIP 조건

아래 조건 중 하나라도 해당하면 이 가이드 전체를 건너뛴다.

1. **`docs/design/ai-service-design.md` 파일이 존재하지 않음** → 전체 SKIP
2. **파일이 존재하나 "AI 서비스 불필요", "해당 없음", "AI 기능 미사용" 등의 결론이 기재됨** → 전체 SKIP

SKIP 여부 확인 절차:
```bash
# 1. 파일 존재 여부 확인
ls docs/design/ai-service-design.md

# 2. 파일 내용에서 SKIP 결론 키워드 검색
grep -i "불필요\|해당 없음\|미사용\|skip" docs/design/ai-service-design.md
```

---

### 작성 원칙

- **Java 패키지 그룹명 표준**: 모든 소스 코드의 패키지는 `com.{ORG}.{ROOT}.{service-name}` 형식을 사용한다. `{ORG}`, `{ROOT}` 값은 `CLAUDE.md`에서 읽으며, 설계서에 다른 패키지명이 있더라도 이 표준으로 강제 통일한다.
- **행위 계약 테스트 준수**: `test/design-contract/integration/*.spec.ts`의 BE↔AI 연동 시나리오를 기반으로 구현하고, `docs/develop/dev-plan.md`의 서비스 간 의존관계를 참조한다
- **장애 격리 패턴 적용**: `ai-service-design.md`에 지정된 Circuit Breaker, Fallback 전략 준수
- **타임아웃 필수 설정**: LLM 응답 지연이 30초 이상 발생할 수 있으므로 connectTimeout/readTimeout 명시
- **환경변수 관리**: AI 서비스 URL은 하드코딩 금지, `AI_SERVICE_URL` 환경변수로 관리
- **개발주석표준** 준수: 모든 클래스·메서드에 표준 Javadoc 주석 작성 (`{NPD_PLUGIN_DIR}/resources/references/standard_comment.md` 참조)

### 작성 순서

**준비**

- `docs/design/ai-service-design.md`에서 SKIP 조건 확인 (위 SKIP 조건 절차 수행)
- 설계 산출물 탐색 절차:
  ```
  1. docs/develop/dev-plan.md를 읽어 서비스 목록, 입력 파일 매핑(섹션 8) 확인
  2. 매핑 테이블에 명시된 파일만 로드:
     - AI 서비스 설계: docs/design/ai-service-design.md
  3. AI 서비스 router/controller 탐색 (어노테이션/패턴 기반):
     ```
     grep -rn "app\.get\|app\.post\|router\.\|@app\.route\|@router\." --include="*.py" --include="*.ts" --include="*.js" .
     ```
  4. 행위 계약 테스트 확인: test/design-contract/integration/*.spec.ts
  4. 누락 파일이 있으면 오케스트레이터에 보고 (직접 탐색하지 않음)
  ```
- 위에서 탐색한 AI 서비스 router/controller 코드에서 엔드포인트 경로, 요청/응답 DTO 스펙 파악
- `test/design-contract/integration/*.spec.ts`에서 BE↔AI 연동 시나리오의 기대 동작 확인
- `build.gradle`에 resilience4j 의존성 추가 여부 확인

**실행**

#### 1단계: resilience4j 의존성 추가

`{service-name}/build.gradle`에 의존성을 추가한다.

```groovy
// {service-name}/build.gradle
dependencies {
    // 기존 의존성 유지 ...

    // Circuit Breaker (resilience4j)
    implementation 'io.github.resilience4j:resilience4j-spring-boot3:2.2.0'
    implementation 'org.springframework.boot:spring-boot-starter-aop'

    // FeignClient 사용 시 (선택)
    implementation 'org.springframework.cloud:spring-cloud-starter-openfeign'

    // 통합 테스트 모킹 (WireMock)
    testImplementation 'org.wiremock:wiremock-standalone:3.3.1'
}
```

Spring Cloud OpenFeign을 사용하는 경우 `build.gradle` 최상단의 `dependencyManagement` 블록에 BOM을 추가한다:

```groovy
dependencyManagement {
    imports {
        mavenBom "org.springframework.cloud:spring-cloud-dependencies:2023.0.1"
    }
}
```

#### 2단계: AI 서비스 클라이언트 인터페이스 정의

준비 단계에서 탐색한 AI 서비스 router/controller의 실제 엔드포인트를 기반으로 클라이언트 인터페이스를 작성한다.

```java
/**
 * AI 서비스 클라이언트 인터페이스
 * AI 서비스 호출 계약을 정의한다.
 *
 * @see docs/design/ai-service-design.md
 */
public interface AiServiceClient {

    /**
     * AI 서비스에 분석 요청을 전송한다.
     *
     * @param request AI 분석 요청 DTO
     * @return AI 분석 결과 DTO
     */
    AiAnalysisResponse analyze(AiAnalysisRequest request);
}
```

요청/응답 DTO는 AI 서비스 router/controller가 실제로 수신/반환하는 필드명과 타입을 그대로 맞춘다:

```java
/**
 * AI 서비스 분석 요청 DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiAnalysisRequest {
    private String inputText;
    private String modelType;
    // AI 서비스 router의 실제 요청 필드 그대로 반영
}

/**
 * AI 서비스 분석 응답 DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiAnalysisResponse {
    private String result;
    private Double confidence;
    // AI 서비스 router의 실제 응답 필드 그대로 반영
}
```

#### 3단계: HTTP 클라이언트 구현

**옵션 A — FeignClient (선언적, Spring Cloud 사용 시 권장):**

```java
/**
 * AI 서비스 FeignClient 구현체
 * resilience4j Circuit Breaker와 연동된다.
 */
@FeignClient(
    name = "ai-service",
    url = "${ai.service.url}",
    configuration = AiServiceFeignConfig.class,
    fallback = AiServiceClientFallback.class
)
public interface AiServiceFeignClient extends AiServiceClient {

    /**
     * AI 분석 엔드포인트 호출
     */
    @PostMapping("/api/v1/analyze")
    @Override
    AiAnalysisResponse analyze(@RequestBody AiAnalysisRequest request);
}
```

FeignClient 설정 클래스:

```java
/**
 * AI 서비스 FeignClient 설정
 * 타임아웃 및 로그 레벨을 설정한다.
 */
@Configuration
public class AiServiceFeignConfig {

    /**
     * FeignClient 요청 옵션 설정
     * LLM 응답 지연(30초 이상)을 고려하여 readTimeout을 넉넉히 설정한다.
     */
    @Bean
    public Request.Options requestOptions() {
        return new Request.Options(
            5000,  TimeUnit.MILLISECONDS,   // connectTimeout: 5초
            60000, TimeUnit.MILLISECONDS,   // readTimeout: 60초 (LLM 응답 지연 고려)
            true                            // followRedirects
        );
    }

    @Bean
    public Logger.Level feignLoggerLevel() {
        return Logger.Level.BASIC;
    }
}
```

`@EnableFeignClients`를 메인 애플리케이션 또는 설정 클래스에 추가한다:

```java
@SpringBootApplication
@EnableFeignClients(basePackages = "com.{ORG}.{ROOT}.{service-name}.client")  // CLAUDE.md의 ORG, ROOT 값 참조
public class {ServiceName}Application {
    public static void main(String[] args) {
        SpringApplication.run({ServiceName}Application.class, args);
    }
}
```

---

**옵션 B — WebClient (리액티브 또는 FeignClient 미사용 시):**

```java
/**
 * AI 서비스 WebClient 구현체
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class AiServiceWebClientImpl implements AiServiceClient {

    private final WebClient webClient;
    private final CircuitBreakerRegistry circuitBreakerRegistry;

    /**
     * AI 분석 요청을 동기 방식으로 호출한다.
     * Circuit Breaker를 적용하여 장애 시 Fallback을 반환한다.
     */
    @Override
    public AiAnalysisResponse analyze(AiAnalysisRequest request) {
        CircuitBreaker circuitBreaker = circuitBreakerRegistry.circuitBreaker("ai-service");
        return CircuitBreaker.decorateSupplier(circuitBreaker,
            () -> callAiService(request)
        ).get();
    }

    private AiAnalysisResponse callAiService(AiAnalysisRequest request) {
        return webClient.post()
            .uri("/api/v1/analyze")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(AiAnalysisResponse.class)
            .timeout(Duration.ofSeconds(60))   // LLM 응답 지연 60초 허용
            .block();
    }
}
```

WebClient Bean 설정:

```java
/**
 * AI 서비스 WebClient 설정
 */
@Configuration
public class AiServiceWebClientConfig {

    @Value("${ai.service.url}")
    private String aiServiceUrl;

    /**
     * AI 서비스 전용 WebClient Bean
     * connectTimeout 5초, readTimeout 60초 적용
     */
    @Bean
    public WebClient aiServiceWebClient() {
        HttpClient httpClient = HttpClient.create()
            .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 5000)          // connectTimeout: 5초
            .responseTimeout(Duration.ofSeconds(60))                      // readTimeout: 60초
            .doOnConnected(conn ->
                conn.addHandlerLast(new ReadTimeoutHandler(60, TimeUnit.SECONDS))
                    .addHandlerLast(new WriteTimeoutHandler(10, TimeUnit.SECONDS))
            );

        return WebClient.builder()
            .baseUrl(aiServiceUrl)
            .clientConnector(new ReactorClientHttpConnector(httpClient))
            .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
            .build();
    }
}
```

#### 4단계: Circuit Breaker 설정

`{service-name}/src/main/resources/application.yml`에 resilience4j 설정을 추가한다.

```yaml
# AI 서비스 URL (환경변수로 관리)
ai:
  service:
    url: ${AI_SERVICE_URL:http://localhost:8081}

# resilience4j Circuit Breaker 설정
resilience4j:
  circuitbreaker:
    instances:
      ai-service:
        # 실패율 임계값: 50% 이상 실패 시 회로 오픈
        failureRateThreshold: 50
        # 느린 응답 임계값: 30초 이상 소요 시 느린 호출로 간주
        slowCallDurationThreshold: 30s
        # 느린 응답 비율 임계값: 80% 이상 느린 호출 시 회로 오픈
        slowCallRateThreshold: 80
        # 회로 오픈 상태 유지 시간: 30초 후 Half-Open 전환
        waitDurationInOpenState: 30s
        # Sliding Window 크기 (호출 횟수 기준)
        slidingWindowSize: 10
        # Half-Open 상태에서 허용할 시험 호출 횟수
        permittedNumberOfCallsInHalfOpenState: 3
        # 최소 호출 횟수 (통계 수집 시작 기준)
        minimumNumberOfCalls: 5
        # 예외 기록 대상 (AI 서비스 호출 실패 예외)
        recordExceptions:
          - java.io.IOException
          - java.util.concurrent.TimeoutException
          - feign.FeignException
          - org.springframework.web.reactive.function.client.WebClientResponseException

  timelimiter:
    instances:
      ai-service:
        # 타임아웃: 65초 (readTimeout 60초보다 5초 여유)
        timeoutDuration: 65s
        cancelRunningFuture: true
```

#### 5단계: Fallback 로직 구현

AI 서비스 장애 시 반환할 기본 응답을 구현한다. `ai-service-design.md`의 Fallback 전략을 우선 적용하고, 미지정 시 아래 패턴을 적용한다.

**FeignClient Fallback 구현체:**

```java
/**
 * AI 서비스 FeignClient Fallback 구현체
 * Circuit Breaker가 회로를 오픈하거나 예외 발생 시 호출된다.
 *
 * Fallback 전략 우선순위:
 * 1. ai-service-design.md에 Fallback 전략 명시된 경우 해당 전략 적용
 * 2. 미지정 시 아래 기본 응답 반환
 */
@Component
@Slf4j
public class AiServiceClientFallback implements AiServiceClient {

    /**
     * AI 분석 Fallback: 기본 응답 반환
     * 실제 AI 결과 없이 안전한 기본값을 반환한다.
     */
    @Override
    public AiAnalysisResponse analyze(AiAnalysisRequest request) {
        log.warn("[AI Fallback] AI 서비스 호출 실패, 기본 응답 반환. input={}", request.getInputText());
        return AiAnalysisResponse.builder()
            .result("AI 서비스를 일시적으로 사용할 수 없습니다.")
            .confidence(0.0)
            .build();
    }
}
```

**Fallback 패턴 3가지 (요구사항에 따라 선택):**

| 패턴 | 사용 시점 | 구현 예시 |
|------|---------|---------|
| 기본 응답 반환 | AI 결과 없어도 서비스 지속 가능 | `result = "분석 불가"`, `confidence = 0.0` 반환 |
| 캐시된 응답 반환 | 이전 결과 재사용 허용 | Redis/로컬 캐시에서 동일 입력의 이전 결과 조회 후 반환 |
| 에러 메시지 반환 | AI 결과가 필수이며 없으면 오류 처리 | `throw new AiServiceUnavailableException("AI 서비스 장애")` |

캐시 기반 Fallback 예시:

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class AiServiceClientFallbackWithCache implements AiServiceClient {

    private final AiResponseCacheRepository cacheRepository;

    @Override
    public AiAnalysisResponse analyze(AiAnalysisRequest request) {
        log.warn("[AI Fallback] AI 서비스 호출 실패, 캐시 조회. input={}", request.getInputText());
        return cacheRepository.findByInputText(request.getInputText())
            .map(cached -> {
                log.info("[AI Fallback] 캐시 응답 반환");
                return cached;
            })
            .orElseGet(() -> {
                log.warn("[AI Fallback] 캐시 없음, 기본 응답 반환");
                return AiAnalysisResponse.builder()
                    .result("AI 서비스를 일시적으로 사용할 수 없습니다.")
                    .confidence(0.0)
                    .build();
            });
    }
}
```

#### 6단계: 통합 테스트 작성

WireMock으로 AI 서비스를 모킹하여 통합 테스트를 작성한다.

```java
/**
 * AI 서비스 클라이언트 통합 테스트
 * WireMock으로 AI 서비스를 모킹하여 호출 성공, 실패, Fallback 동작을 검증한다.
 */
@SpringBootTest
@AutoConfigureWireMock(port = 0)   // 랜덤 포트 WireMock 서버 기동
@ActiveProfiles("test")
class AiServiceClientTest {

    @Autowired
    private AiServiceClient aiServiceClient;

    /**
     * 정상 케이스: AI 서비스 호출 성공
     */
    @Test
    @DisplayName("AI 서비스 호출 - 정상 응답 반환")
    void analyze_success() {
        // given
        stubFor(post(urlEqualTo("/api/v1/analyze"))
            .willReturn(aResponse()
                .withStatus(200)
                .withHeader("Content-Type", "application/json")
                .withBody("""
                    {
                      "result": "분석 완료",
                      "confidence": 0.95
                    }
                    """)));

        AiAnalysisRequest request = AiAnalysisRequest.builder()
            .inputText("테스트 입력")
            .build();

        // when
        AiAnalysisResponse response = aiServiceClient.analyze(request);

        // then
        assertThat(response).isNotNull();
        assertThat(response.getResult()).isEqualTo("분석 완료");
        assertThat(response.getConfidence()).isEqualTo(0.95);
    }

    /**
     * Fallback 케이스: AI 서비스 500 오류 시 Fallback 동작 확인
     */
    @Test
    @DisplayName("AI 서비스 호출 - 500 오류 시 Fallback 반환")
    void analyze_serverError_returnsFallback() {
        // given
        stubFor(post(urlEqualTo("/api/v1/analyze"))
            .willReturn(aResponse()
                .withStatus(500)
                .withBody("Internal Server Error")));

        AiAnalysisRequest request = AiAnalysisRequest.builder()
            .inputText("테스트 입력")
            .build();

        // when
        AiAnalysisResponse response = aiServiceClient.analyze(request);

        // then: Fallback 응답 확인
        assertThat(response).isNotNull();
        assertThat(response.getResult()).isEqualTo("AI 서비스를 일시적으로 사용할 수 없습니다.");
        assertThat(response.getConfidence()).isEqualTo(0.0);
    }

    /**
     * 타임아웃 케이스: AI 서비스 응답 지연 시 타임아웃 처리 확인
     */
    @Test
    @DisplayName("AI 서비스 호출 - 타임아웃 시 Fallback 반환")
    void analyze_timeout_returnsFallback() {
        // given: 응답을 70초 지연 (타임아웃 65초 초과)
        stubFor(post(urlEqualTo("/api/v1/analyze"))
            .willReturn(aResponse()
                .withStatus(200)
                .withFixedDelay(70000)));

        AiAnalysisRequest request = AiAnalysisRequest.builder()
            .inputText("테스트 입력")
            .build();

        // when
        AiAnalysisResponse response = aiServiceClient.analyze(request);

        // then: Fallback 응답 확인
        assertThat(response).isNotNull();
        assertThat(response.getConfidence()).isEqualTo(0.0);
    }
}
```

WireMock을 위한 테스트 설정(`{service-name}/src/test/resources/application.yml`):

```yaml
ai:
  service:
    url: ${AI_SERVICE_URL:http://localhost:${wiremock.server.port}}

resilience4j:
  circuitbreaker:
    instances:
      ai-service:
        failureRateThreshold: 50
        waitDurationInOpenState: 5s    # 테스트에서는 짧게 설정
        slidingWindowSize: 5
        minimumNumberOfCalls: 2
  timelimiter:
    instances:
      ai-service:
        timeoutDuration: 5s            # 테스트에서는 짧게 설정
```

#### 7단계: 컴파일 및 테스트 실행

```bash
# 서비스 컴파일 검증
./gradlew {service-name}:compileJava

# 통합 테스트 실행
./gradlew {service-name}:test --tests "*AiServiceClientTest*"

# 전체 테스트 실행
./gradlew {service-name}:test

# Windows에서는 gradlew.bat 사용
.\gradlew.bat {service-name}:compileJava
```

**검토**
- AI 서비스 정상 호출 시 200 응답 수신 확인
- AI 서비스 500 오류 시 Fallback 응답 반환 확인
- 타임아웃 발생 시 Fallback 동작 확인
- Circuit Breaker 회로 오픈/클로즈 전환 확인

---

### 검증 방법

```bash
# 컴파일 검증
./gradlew {service-name}:compileJava

# 통합 테스트 실행
./gradlew {service-name}:test

# 테스트 결과 리포트
# {service-name}/build/reports/tests/test/index.html
```

## 출력 형식

### 패키지 구조 예시

> 패키지 구조 표준: `{NPD_PLUGIN_DIR}/resources/references/standard_package_structure.md`
> `{ORG}`, `{ROOT}` 값은 `CLAUDE.md`에서 읽는다.

**Layered 아키텍처**

```
{service-name}/src/main/java/com/{ORG}/{ROOT}/{service-name}/
├── client/                                   ← AI 서비스 클라이언트
│   ├── AiServiceClient.java                 ← 클라이언트 인터페이스
│   ├── AiServiceFeignClient.java            ← FeignClient 구현 (옵션 A)
│   ├── AiServiceWebClientImpl.java          ← WebClient 구현 (옵션 B)
│   └── AiServiceClientFallback.java         ← Fallback 구현체
├── config/                                   ← AI 관련 설정 (기존 config/ 하위에 추가)
│   ├── AiServiceFeignConfig.java            ← FeignClient 타임아웃 설정 (옵션 A)
│   └── AiServiceWebClientConfig.java        ← WebClient Bean 설정 (옵션 B)
└── dto/
    ├── request/
    │   └── AiAnalysisRequest.java           ← AI 요청 DTO
    └── response/
        └── AiAnalysisResponse.java          ← AI 응답 DTO

{service-name}/src/test/java/com/{ORG}/{ROOT}/{service-name}/
└── client/
    └── AiServiceClientTest.java             ← WireMock 통합 테스트
```

**Clean 아키텍처** (`biz/infra` 구조)

```
{service-name}/src/main/java/com/{ORG}/{ROOT}/{service-name}/
├── biz/
│   ├── usecase/out/
│   │   └── AiServiceCaller.java             ← 아웃바운드 UseCase 인터페이스
│   └── dto/
│       ├── request/
│       │   └── AiAnalysisRequest.java       ← AI 요청 DTO
│       └── response/
│           └── AiAnalysisResponse.java      ← AI 응답 DTO
└── infra/
    ├── config/
    │   ├── AiServiceFeignConfig.java        ← FeignClient 타임아웃 설정 (옵션 A)
    │   └── AiServiceWebClientConfig.java    ← WebClient Bean 설정 (옵션 B)
    └── gateway/
        └── client/                          ← 외부 서비스 호출
            ├── AiServiceClient.java         ← FeignClient 구현 (옵션 A)
            ├── AiServiceWebClientImpl.java  ← WebClient 구현 (옵션 B)
            └── AiServiceClientFallback.java ← Fallback 구현체

{service-name}/src/test/java/com/{ORG}/{ROOT}/{service-name}/
└── infra/gateway/
    └── client/
        └── AiServiceClientTest.java         ← WireMock 통합 테스트
```

### 연동 구성 체크리스트

```
[ ] resilience4j 의존성 추가 (build.gradle)
[ ] AiServiceClient 인터페이스 정의
[ ] HTTP 클라이언트 구현 (FeignClient 또는 WebClient 중 선택)
[ ] connectTimeout 설정 (권장: 5초)
[ ] readTimeout 설정 (권장: 60초 이상 — LLM 응답 지연 고려)
[ ] Circuit Breaker 설정 추가 (application.yml — resilience4j 섹션)
    [ ] failureRateThreshold 설정
    [ ] waitDurationInOpenState 설정
    [ ] slidingWindowSize 설정
[ ] Fallback 구현체 작성
[ ] AI_SERVICE_URL 환경변수 바인딩 (application.yml: ${AI_SERVICE_URL:...})
[ ] WireMock 통합 테스트 작성 (정상/오류/타임아웃 케이스)
[ ] 컴파일 성공 확인
[ ] 통합 테스트 전체 통과 확인
```

## 품질 기준

- [ ] AI 서비스 정상 호출 성공 (WireMock 통합 테스트 통과)
- [ ] Circuit Breaker 동작 확인 (500 오류 시 Fallback 반환)
- [ ] Fallback 응답 정상 반환 (오류/타임아웃 케이스 모두 통과)
- [ ] 타임아웃 설정 적용 확인 (connectTimeout, readTimeout)
- [ ] `{service-name}:compileJava` 성공
- [ ] 통합 테스트 전체 통과
- [ ] AI_SERVICE_URL 환경변수 바인딩 확인 (하드코딩 없음)

## 주의사항

- AI 서비스가 존재하지 않거나 불필요한 경우 이 가이드 전체를 SKIP (위 SKIP 조건 절차 수행)
- AI 서비스 URL은 하드코딩 금지. `AI_SERVICE_URL` 환경변수로 관리:
  ```yaml
  ai:
    service:
      url: ${AI_SERVICE_URL:http://localhost:8081}
  ```
- 타임아웃 설정 필수: LLM 응답은 30초 이상 소요될 수 있으므로 readTimeout을 반드시 60초 이상으로 설정
- resilience4j `timeoutDuration`은 readTimeout보다 5~10초 길게 설정하여 타임아웃 충돌 방지
- FeignClient와 WebClient 중 하나만 선택. FeignClient는 Spring Cloud 의존성이 추가되므로 `dev-plan.md`의 기술 스택 확인 후 결정
- Fallback 전략은 `ai-service-design.md`에 명시된 전략을 우선 적용
- 테스트 설정(`application-test.yml`)의 `waitDurationInOpenState`, `timeoutDuration`은 실제값보다 짧게 설정하여 테스트 실행 시간 단축
- 참조: 개발주석표준 — `{NPD_PLUGIN_DIR}/resources/references/standard_comment.md`
- 참조: 테스트코드표준 — `{NPD_PLUGIN_DIR}/resources/references/standard_testcode.md`
- `{NPD_PLUGIN_DIR}` = `~/.claude/plugins/cache/npd/npd/{version}/`
