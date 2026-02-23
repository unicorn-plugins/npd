# Java Build Gradle 표준

## 루트 build.gradle 표준
```
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.3.0' apply false
    id 'io.spring.dependency-management' version '1.1.6' apply false
    id 'io.freefair.lombok' version '8.10' apply false
}

group = 'com.{ORG}.{ROOT}'  // CLAUDE.md의 ORG, ROOT 값 참조
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
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }

    configurations {
        compileOnly {
            extendsFrom annotationProcessor
        }
    }

    tasks.named('test') {
        useJUnitPlatform()
    }

    // Common versions for all subprojects
    ext {
        jjwtVersion = '0.12.5'
        springdocVersion = '2.5.0'
        mapstructVersion = '1.5.5.Final'
        commonsLang3Version = '3.14.0'
        commonsIoVersion = '2.16.1'
        hypersistenceVersion = '3.7.3'
        openaiVersion = '0.18.2'
        feignJacksonVersion = '13.1'
    }
}

// Configure all subprojects with Spring dependency management
subprojects {
    apply plugin: 'io.spring.dependency-management'

    dependencyManagement {
        imports {
            mavenBom "org.springframework.cloud:spring-cloud-dependencies:2023.0.2"
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
        implementation "org.springdoc:springdoc-openapi-starter-webmvc-ui:${springdocVersion}"

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

### Build.gradle 구성 최적화 원칙
- **중앙 버전 관리**: 루트 build.gradle의 `ext` 블록에서 모든 외부 라이브러리 버전 통일 관리
- **Spring Boot BOM 활용**: Spring Boot/Cloud에서 관리하는 라이브러리는 버전 명시 불필요 (자동 호환성 보장)
- **Common 모듈 설정**: `java-library` + Spring Boot 플러그인 조합, `bootJar` 비활성화로 일반 jar 생성
- **서비스별 최적화**: 공통 의존성(API 문서화, 테스트 등)은 루트에서 일괄 적용
- **JWT 버전 통일**: 라이브러리 버전 변경시 API 호환성 확인 필수 (`parserBuilder()` → `parser()`)
- **dependency-management 적용**: 모든 서브프로젝트에 Spring BOM 적용으로 버전 충돌 방지

## 참조
- 이 파일은 `resources/guides/develop/backend-env-setup.md`에서 참조됩니다.
