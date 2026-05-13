# Java Build Gradle 표준

## 버전 관리 원칙

> **프로젝트 생성 시 에이전트는 아래 절차로 최신 stable 버전을 조회하여 적용한다.**
> 이 레퍼런스에 적힌 고정 버전을 그대로 복사하지 않는다.

### 버전 조회 방법

1. **Spring Boot**: [Spring Initializr](https://start.spring.io)에서 최신 GA(stable) 버전 확인
2. **Gradle 플러그인**: [Gradle Plugin Portal](https://plugins.gradle.org)에서 각 플러그인 최신 버전 확인
3. **라이브러리**: [Maven Central](https://search.maven.org)에서 최신 stable 버전 확인 (RC/SNAPSHOT 제외)
4. **Spring Cloud**: [Spring Cloud Release Train](https://spring.io/projects/spring-cloud) 페이지에서 사용 중인 Spring Boot 버전과 호환되는 릴리스 트레인 확인

### 버전 조회 결과 기록

조회한 버전은 `gradle/libs.versions.toml`에 기록하여 한 곳에서 관리한다 (아래 Version Catalog 섹션 참조).

---

## Gradle Version Catalog (`gradle/libs.versions.toml`)

프로젝트 루트에 `gradle/libs.versions.toml` 파일을 생성하여 **모든 버전을 한 곳에서** 관리한다.

```toml
[versions]
# ============================================================
# 필수 코어 (모든 프로젝트 공통)
# 에이전트가 프로젝트 생성 시 최신 stable 버전을 조회하여 기입
# ============================================================
spring-boot = "{최신 stable 조회}"          # https://start.spring.io
dependency-management = "{최신 stable 조회}" # https://plugins.gradle.org/plugin/io.spring.dependency-management
lombok-plugin = "{최신 stable 조회}"         # https://plugins.gradle.org/plugin/io.freefair.lombok
spring-cloud = "{최신 stable 조회}"          # Spring Boot 버전과 호환되는 릴리스 트레인
java = "{high-level-architecture.md의 Java 버전}"  # 예: "17", "21", "23"

# ============================================================
# 선택 라이브러리 — 설계 산출물에서 필요한 것만 추가
# 아래 전체를 복사하지 않는다. 프로젝트에 필요한 항목만 선택한다.
# ============================================================
# [판단 기준] 설계 산출물 → 필요 라이브러리:
#   high-level-architecture.md 인증방식=JWT        → jjwt
#   API 설계서에 Swagger/OpenAPI 명세 존재         → springdoc
#   클래스 설계서에 DTO↔Entity 매핑 클래스 존재     → mapstruct
#   클래스 설계서에 Apache Commons 유틸 사용       → commons-lang3, commons-io
#   데이터 설계서에 JSON 컬럼/Hibernate 확장 사용   → hypersistence
#   high-level-architecture.md에 AI/LLM 연동 존재  → openai (또는 해당 AI SDK)
#   시퀀스 설계서에 서비스 간 Feign 호출 존재       → feign-jackson
#   기타 설계서에 명시된 외부 라이브러리            → Maven Central에서 조회하여 추가

# --- 선택 항목 예시 (필요한 것만 주석 해제하여 사용) ---
# jjwt = "{최신 stable 조회}"               # io.jsonwebtoken
# springdoc = "{최신 stable 조회}"          # org.springdoc
# mapstruct = "{최신 stable 조회}"          # org.mapstruct
# commons-lang3 = "{최신 stable 조회}"      # org.apache.commons
# commons-io = "{최신 stable 조회}"         # commons-io
# hypersistence = "{최신 stable 조회}"      # io.hypersistence
# openai = "{최신 stable 조회}"             # com.theokanning.openai-gpt3-java
# feign-jackson = "{최신 stable 조회}"      # io.github.openfeign

[libraries]
# ============================================================
# 선택 라이브러리의 [libraries] 정의 — [versions]에 추가한 항목만 아래에 정의
# ============================================================
# jjwt-api = { module = "io.jsonwebtoken:jjwt-api", version.ref = "jjwt" }
# jjwt-impl = { module = "io.jsonwebtoken:jjwt-impl", version.ref = "jjwt" }
# jjwt-jackson = { module = "io.jsonwebtoken:jjwt-jackson", version.ref = "jjwt" }
# springdoc-webmvc = { module = "org.springdoc:springdoc-openapi-starter-webmvc-ui", version.ref = "springdoc" }
# mapstruct = { module = "org.mapstruct:mapstruct", version.ref = "mapstruct" }
# mapstruct-processor = { module = "org.mapstruct:mapstruct-processor", version.ref = "mapstruct" }
# commons-lang3 = { module = "org.apache.commons:commons-lang3", version.ref = "commons-lang3" }
# commons-io = { module = "commons-io:commons-io", version.ref = "commons-io" }
# hypersistence = { module = "io.hypersistence:hypersistence-utils-hibernate-63", version.ref = "hypersistence" }
# openai = { module = "com.theokanning.openai-gpt3-java:service", version.ref = "openai" }
# feign-jackson = { module = "io.github.openfeign:feign-jackson", version.ref = "feign-jackson" }

[plugins]
spring-boot = { id = "org.springframework.boot", version.ref = "spring-boot" }
dependency-management = { id = "io.spring.dependency-management", version.ref = "dependency-management" }
lombok = { id = "io.freefair.lombok", version.ref = "lombok-plugin" }
```

> **주의**:
> - `[versions]` 섹션의 `"{최신 stable 조회}"` 플레이스홀더를 실제 버전으로 교체해야 한다. 그대로 남기면 빌드가 실패한다.
> - 선택 라이브러리는 **설계 산출물을 분석한 후 필요한 항목만** 주석 해제한다. 전체를 무조건 추가하지 않는다.

---

## 루트 build.gradle 표준

Version Catalog를 참조하여 플러그인과 의존성 버전을 관리한다.

```
plugins {
    id 'java'
    alias(libs.plugins.spring.boot) apply false
    alias(libs.plugins.dependency.management) apply false
    alias(libs.plugins.lombok) apply false
}

group = 'com.{ORG}.{ROOT}'  // AGENTS.md의 ORG, ROOT 값 참조
version = '1.0.0'

allprojects {
    repositories {
        mavenCentral()
        gradlePluginPortal()
    }
}

subprojects {
    apply plugin: 'java'
    apply plugin: 'io.freefair.lombok'

    java {
        sourceCompatibility = JavaVersion.toVersion(libs.versions.java.get())
        targetCompatibility = JavaVersion.toVersion(libs.versions.java.get())
    }

    configurations {
        compileOnly {
            extendsFrom annotationProcessor
        }
    }

    tasks.named('test') {
        useJUnitPlatform()
    }
}

// Configure all subprojects with Spring dependency management
subprojects {
    apply plugin: 'io.spring.dependency-management'

    dependencyManagement {
        imports {
            mavenBom "org.springframework.cloud:spring-cloud-dependencies:${libs.versions.spring.cloud.get()}"
        }
    }
}

// Configure only service modules (exclude common)
configure(subprojects.findAll { it.name != 'common' }) {
    apply plugin: 'org.springframework.boot'

    dependencies {
        // Common module dependency
        implementation project(':common')

        // Actuator for health checks and monitoring
        implementation 'org.springframework.boot:spring-boot-starter-actuator'

        // API Documentation (common across all services)
        implementation libs.springdoc.webmvc

        // Testing
        testImplementation 'org.springframework.boot:spring-boot-starter-test'
        testImplementation 'org.springframework.security:spring-security-test'
        testImplementation 'org.testcontainers:junit-jupiter'
        testImplementation 'org.mockito:mockito-junit-jupiter'

        // Configuration Processor
        annotationProcessor 'org.springframework.boot:spring-boot-configuration-processor'
    }
}

// Java version consistency check for all modules
tasks.register('checkJavaVersion') {
    doLast {
        println "Java Version: ${System.getProperty('java.version')}"
        println "Java Home: ${System.getProperty('java.home')}"
    }
}

// Clean task for all subprojects
tasks.register('cleanAll') {
    dependsOn subprojects.collect { it.tasks.named('clean') }
    description = 'Clean all subprojects'
}

// Build task for all subprojects
tasks.register('buildAll') {
    dependsOn subprojects.collect { it.tasks.named('build') }
    description = 'Build all subprojects'
}
```

## 서비스별 build.gradle 패턴

- 최상위 build.gradle에 정의한 설정은 각 마이크로서비스의 build.gradle에 **중복하여 정의하지 않도록** 함
- 각 서비스의 실행 jar 파일명은 서비스명과 동일하게 함
- common 모듈은 `java-library` + Spring Boot 플러그인 조합, `bootJar` 비활성화로 일반 jar 생성
- common을 제외한 각 서비스에서 공통으로 사용되는 설정과 Dependency는 루트 build.gradle에 지정

### 서비스별 build.gradle에서 Version Catalog 사용 예시

```
dependencies {
    // Version Catalog 참조 — 버전 번호를 직접 적지 않는다
    implementation libs.jjwt.api
    runtimeOnly libs.jjwt.impl
    runtimeOnly libs.jjwt.jackson
    implementation libs.mapstruct
    annotationProcessor libs.mapstruct.processor
    implementation libs.commons.lang3
}
```

### Build.gradle 구성 최적화 원칙
- **중앙 버전 관리**: `gradle/libs.versions.toml`에서 모든 외부 라이브러리 버전 통일 관리
- **Spring Boot BOM 활용**: Spring Boot/Cloud에서 관리하는 라이브러리는 버전 명시 불필요 (자동 호환성 보장)
- **Version Catalog 필수**: `ext` 블록 대신 `libs.versions.toml`을 사용하여 버전을 한 곳에서 관리
- **Common 모듈 설정**: `java-library` + Spring Boot 플러그인 조합, `bootJar` 비활성화로 일반 jar 생성
- **서비스별 최적화**: 공통 의존성(API 문서화, 테스트 등)은 루트에서 일괄 적용
- **JWT 버전 통일**: 라이브러리 버전 변경시 API 호환성 확인 필수 (`parserBuilder()` → `parser()`)
- **dependency-management 적용**: 모든 서브프로젝트에 Spring BOM 적용으로 버전 충돌 방지

## 참조
- 이 파일은 `resources/guides/develop/backend-env-setup.md`에서 참조됩니다.
- Gradle Version Catalog 공식 문서: https://docs.gradle.org/current/userguide/platforms.html
