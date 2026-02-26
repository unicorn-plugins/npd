# 패키지 구조 표준

## 패키지 그룹명 규칙

```
com.{ORG}.{ROOT}.{SERVICE}
```

| 변수 | 설명 | 예시 |
|------|------|------|
| `{ORG}` | 회사 또는 조직명 | `unicorn`, `travelplanner` |
| `{ROOT}` | Root Project 명 | `lifesub`, `travel` |
| `{SERVICE}` | 서비스명 (Root Project의 서브 프로젝트) | `member`, `auth`, `schedule` |

- `{ORG}`, `{ROOT}` 값은 프로젝트 루트의 **`CLAUDE.md`**에서 읽는다
- 설계서(클래스 설계서, 패키지 구조 등)에 다른 패키지명이 있더라도 이 표준으로 강제 통일한다

예: `com.unicorn.lifesub.member`, `com.unicorn.lifesub.common`

---

## Layered 아키텍처 패키지 구조

```
{service-name}/src/main/java/com/{ORG}/{ROOT}/{service-name}/
├── {ServiceName}Application.java
├── config/                        ← Spring 설정
│   ├── SecurityConfig.java
│   ├── SwaggerConfig.java
│   ├── jwt/                       ← [JWT 인증 시] JWT 인증 관련
│   │   ├── JwtAuthenticationFilter.java
│   │   ├── JwtTokenProvider.java
│   │   ├── CustomUserDetailsService.java
│   │   └── UserPrincipal.java
│   └── oauth2/                    ← [OAuth2 인증 시] 소셜 로그인 관련
│       ├── CustomOAuth2UserService.java
│       ├── OAuth2SuccessHandler.java
│       ├── OAuth2FailureHandler.java
│       └── OAuth2UserPrincipal.java
├── controller/                    ← REST 컨트롤러
│   └── {ServiceName}Controller.java
├── dto/                           ← 요청/응답 DTO
│   ├── request/
│   │   └── {Entity}CreateRequest.java
│   └── response/
│       └── {Entity}Response.java
├── service/                       ← 서비스 인터페이스 + 구현체
│   ├── {ServiceName}Service.java
│   └── {ServiceName}ServiceImpl.java
├── domain/                        ← 도메인 모델
│   └── {EntityName}.java
├── repository/                    ← 데이터 접근
│   ├── entity/                    ← JPA 엔티티
│   │   └── {EntityName}Entity.java
│   └── jpa/                       ← JPA Repository
│       └── {EntityName}Repository.java
└── exception/                     ← [optional] 서비스 고유 예외
    └── {ServiceName}Exception.java
```

### Layered 패키지 규칙

- **config/jwt/**: JWT 인증 시 Security 관련 클래스를 `config/jwt/` 하위에 배치 (독립 `security/` 패키지 사용 금지)
- **config/oauth2/**: OAuth2/OIDC 소셜 로그인 시 관련 클래스를 `config/oauth2/` 하위에 배치. JWT+OAuth2 하이브리드인 경우 `config/jwt/`와 `config/oauth2/` 모두 사용
- 인증 방식은 `docs/design/high-level-architecture.md`의 `보안 요구사항 > 인증/인가` 항목에서 확인
- **service/**: 인터페이스와 구현체를 같은 패키지에 평탄 배치 (`impl/` 하위 패키지 사용 금지)
- **domain/**: 순수 도메인 모델 배치. JPA 엔티티는 `repository/entity/`에 분리
- **repository/entity/**: JPA `@Entity` 클래스 배치. `repository/jpa/`에 Repository 인터페이스 배치
- **dto/request/, dto/response/**: DTO를 용도별로 분류
- **exception/**: [optional] 서비스 고유 예외가 필요한 경우에만 생성. common 모듈의 공통 예외를 우선 사용

### Layered 예시

```
com.unicorn.lifesub.member
 ├── MemberApplication.java
 ├── config/
 │   ├── SecurityConfig.java
 │   ├── SwaggerConfig.java
 │   └── jwt/
 │       ├── JwtAuthenticationFilter.java
 │       ├── JwtTokenProvider.java
 │       ├── CustomUserDetailsService.java
 │       └── UserPrincipal.java
 ├── controller/
 │   └── MemberController.java
 ├── dto/
 │   ├── request/
 │   │   ├── LoginRequest.java
 │   │   └── LogoutRequest.java
 │   └── response/
 │       └── LogoutResponse.java
 ├── service/
 │   ├── MemberService.java
 │   └── MemberServiceImpl.java
 ├── domain/
 │   └── Member.java
 ├── repository/
 │   ├── entity/
 │   │   └── MemberEntity.java
 │   └── jpa/
 │       └── MemberRepository.java
 └── exception/
     └── MemberException.java
```

---

## Clean 아키텍처 패키지 구조

> Clean 아키텍처 적용 시 Port/Adapter 용어를 사용하지 않고, Clean 아키텍처 고유 용어(UseCase, Gateway 등)를 사용한다.

```
{service-name}/src/main/java/com/{ORG}/{ROOT}/{service-name}/
├── biz/                           ← 비즈니스 계층
│   ├── usecase/                   ← UseCase 인터페이스
│   │   ├── in/                    ← 인바운드 UseCase (Controller → Service)
│   │   │   └── {Action}UseCase.java
│   │   └── out/                   ← 아웃바운드 UseCase (Service → Gateway)
│   │       └── {Entity}Reader.java
│   ├── service/                   ← UseCase 구현체
│   │   └── {ServiceName}Service.java
│   ├── domain/                    ← 도메인 모델
│   │   └── {EntityName}.java
│   └── dto/                       ← 비즈니스 DTO
│       ├── request/
│       │   └── {Entity}Request.java
│       └── response/
│           └── {Entity}Response.java
├── infra/                         ← 인프라 계층
│   ├── {ServiceName}Application.java
│   ├── controller/                ← REST 컨트롤러
│   │   └── {ServiceName}Controller.java
│   ├── config/                    ← Spring 설정
│   │   ├── SecurityConfig.java
│   │   ├── SwaggerConfig.java
│   │   ├── jwt/                   ← [JWT 인증 시]
│   │   │   ├── JwtAuthenticationFilter.java
│   │   │   ├── JwtTokenProvider.java
│   │   │   ├── CustomUserDetailsService.java
│   │   │   └── UserPrincipal.java
│   │   └── oauth2/                ← [OAuth2 인증 시]
│   │       ├── CustomOAuth2UserService.java
│   │       ├── OAuth2SuccessHandler.java
│   │       ├── OAuth2FailureHandler.java
│   │       └── OAuth2UserPrincipal.java
│   └── gateway/                   ← 외부 연동 (DB, 외부 API 등)
│       ├── entity/
│       │   └── {EntityName}Entity.java
│       ├── repository/
│       │   └── {EntityName}JpaRepository.java
│       ├── {EntityName}Gateway.java
│       └── client/                ← [optional] 외부 서비스 호출
│           └── {ExternalService}Client.java
└── exception/                     ← [optional] 서비스 고유 예외
    └── {ServiceName}Exception.java
```

### Clean 패키지 규칙

- **biz/**: 비즈니스 로직. 프레임워크 의존성 없음 (순수 Java)
- **infra/**: 프레임워크·외부 시스템 의존. Spring, JPA 등 사용
- **usecase/in/**: Controller가 호출하는 인바운드 UseCase 인터페이스
- **usecase/out/**: Service가 호출하는 아웃바운드 UseCase 인터페이스 (데이터 읽기/쓰기)
- **gateway/**: 아웃바운드 UseCase 구현체. DB 접근, 외부 API 호출 등
- **gateway/client/**: [optional] 외부 서비스(AI 서비스 등) HTTP 호출 클래스
- **infra/config/jwt/**: JWT 인증 시 사용. **infra/config/oauth2/**: OAuth2 인증 시 사용. 하이브리드는 둘 다 사용
- **Port/Adapter 용어 사용 금지**: `domain/port/`, `infrastructure/adapter/` 대신 `usecase/out/`, `gateway/` 사용

### Clean 예시

```
com.unicorn.lifesub.mysub
 ├── biz/
 │   ├── dto/
 │   │   ├── request/
 │   │   │   └── SubscribeRequest.java
 │   │   └── response/
 │   │       ├── CategoryResponse.java
 │   │       ├── ServiceListResponse.java
 │   │       ├── MySubResponse.java
 │   │       ├── SubDetailResponse.java
 │   │       └── TotalFeeResponse.java
 │   ├── service/
 │   │   ├── FeeLevel.java
 │   │   └── MySubscriptionService.java
 │   ├── usecase/
 │   │   ├── in/
 │   │   │   ├── CancelSubscriptionUseCase.java
 │   │   │   ├── CategoryUseCase.java
 │   │   │   ├── MySubscriptionsUseCase.java
 │   │   │   ├── SubscribeUseCase.java
 │   │   │   ├── SubscriptionDetailUseCase.java
 │   │   │   └── TotalFeeUseCase.java
 │   │   └── out/
 │   │       ├── MySubscriptionReader.java
 │   │       ├── MySubscriptionWriter.java
 │   │       └── SubscriptionReader.java
 │   └── domain/
 │       ├── Category.java
 │       ├── MySubscription.java
 │       └── Subscription.java
 └── infra/
     ├── MySubApplication.java
     ├── controller/
     │   ├── CategoryController.java
     │   ├── MySubController.java
     │   └── ServiceController.java
     ├── config/
     │   ├── DataLoader.java
     │   ├── SecurityConfig.java
     │   ├── SwaggerConfig.java
     │   └── jwt/
     │       ├── JwtAuthenticationFilter.java
     │       ├── JwtTokenProvider.java
     │       ├── CustomUserDetailsService.java
     │       └── UserPrincipal.java
     └── gateway/
         ├── entity/
         │   ├── CategoryEntity.java
         │   ├── MySubscriptionEntity.java
         │   └── SubscriptionEntity.java
         ├── repository/
         │   ├── CategoryJpaRepository.java
         │   ├── MySubscriptionJpaRepository.java
         │   └── SubscriptionJpaRepository.java
         ├── MySubscriptionGateway.java
         └── SubscriptionGateway.java
```

---

## common 모듈 패키지 구조

```
common/src/main/java/com/{ORG}/{ROOT}/common/
├── dto/                           ← 공통 DTO
│   └── ApiResponse.java
├── entity/                        ← 공통 엔티티 (BaseTimeEntity 등)
│   └── BaseTimeEntity.java
├── config/                        ← 공통 설정
│   └── JpaConfig.java
├── util/                          ← 공통 유틸리티
├── exception/                     ← 공통 예외
│   ├── ErrorCode.java
│   ├── BusinessException.java
│   └── InfraException.java
└── aop/                           ← [optional] 공통 AOP
    └── LoggingAspect.java
```

---

## 테스트 패키지 구조

테스트 코드는 프로덕션 코드와 **동일한 패키지 구조**를 미러링한다.

```
{service-name}/src/test/java/com/{ORG}/{ROOT}/{service-name}/
├── controller/
│   └── {ServiceName}ControllerTest.java
├── service/
│   └── {ServiceName}ServiceImplTest.java
└── repository/
    └── jpa/
        └── {EntityName}RepositoryTest.java
```

Clean 아키텍처의 경우:
```
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
