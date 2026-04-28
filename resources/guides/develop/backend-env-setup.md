# 백엔드 환경 구성 가이드

## 목적

Gradle Wrapper 생성, 멀티모듈 build.gradle 구성, 서비스별 application.yml 작성, 공통 모듈 개발을 수행한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 종합 개발 계획서 | `docs/develop/dev-plan.md` | 서비스 목록, 아키텍처 패턴(섹션 1) |
| 공통 모듈 구성 정보 | `docs/develop/dev-plan.md` 섹션 10-1 | 공통 컴포넌트 (BaseEntity, 예외처리, 공통 DTO 등) |
| 기술스택 정보 | `docs/develop/dev-plan.md` 섹션 10-5 | SpringBoot/Java 버전, 빌드 도구 |
| 패키지 구조 | `docs/design/class/package-structure.md` | 패키지 구조 |
| Gradle 빌드 표준 | `{NPD_PLUGIN_DIR}/resources/references/java-build-gradle-standard.md` | Gradle 멀티모듈 구성 표준 |
| 설정 Manifest 표준 | `{NPD_PLUGIN_DIR}/resources/references/java-config-manifest-standard.md` | application.yml 작성 표준 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| Gradle Wrapper | `gradlew`, `gradlew.bat`, `gradle/wrapper/` |
| settings.gradle | `settings.gradle` |
| 루트 build.gradle | `build.gradle` |
| 서비스별 build.gradle | `{service-name}/build.gradle` |
| 서비스별 application.yml | `{service-name}/src/main/resources/application.yml` |
| 공통 모듈 | `common/src/main/java/.../common/` |

## 방법론

### 작성 원칙

- **Java 패키지 그룹명 표준**: `com.{ORG}.{ROOT}` 형식을 강제 적용한다 (`{NPD_PLUGIN_DIR}/resources/references/standard_package_structure.md` 참조)
  - `{ORG}`, `{ROOT}` 값은 프로젝트 루트의 `AGENTS.md`에서 읽는다
  - 설계서(클래스 설계서, 패키지 구조 등)에 다른 패키지명이 있더라도 이 표준으로 통일한다
  - 루트 `build.gradle`의 `group` 값: `'com.{ORG}.{ROOT}'`
  - 소스 코드 패키지 루트: `com/{ORG}/{ROOT}/{service-name}/`
  - 예: AGENTS.md에 `ORG=travelplanner`, `ROOT=travel` → `com.travelplanner.travel`
- Java 버전 호환 Gradle Wrapper (`gradle-wrapper.md`의 매핑 테이블 적용)
- 루트 build.gradle 표준 준수: `{NPD_PLUGIN_DIR}/resources/references/java-build-gradle-standard.md` 참조
- 설정 Manifest 표준 준수: `{NPD_PLUGIN_DIR}/resources/references/java-config-manifest-standard.md` 참조
- application.yml 환경변수는 placeholder만 작성 (실제 값은 .env.example에서 정의)

### 작성 순서

**준비**
- Java 버전 확인: `java -version`
- 설계 산출물 분석: 서비스 목록, 기술스택(SpringBoot/Java 버전)

**실행**

#### 1단계: Gradle Wrapper 생성 (Java 버전 → Gradle 버전 매핑)

Java 버전에 맞는 Gradle 버전 선택:
- Java 23 → Gradle 8.10.2+
- Java 21 → Gradle 8.5+
- Java 17 → Gradle 7.5+
- Java 11 → Gradle 7.0+
- Java 8 → Gradle 6.0+

시스템 Gradle이 설치되어 있으면:
```bash
gradle wrapper --gradle-version {VERSION}
```

Gradle이 없으면 수동 생성:

**1-1. 디렉토리 생성**
```bash
mkdir -p gradle/wrapper
```

**1-2. gradle-wrapper.properties 파일 생성**
```properties
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-{VERSION}-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
```

**1-3. gradle-wrapper.jar 다운로드**
```bash
curl -L -o gradle/wrapper/gradle-wrapper.jar \
  https://raw.githubusercontent.com/gradle/gradle/v{VERSION}/gradle/wrapper/gradle-wrapper.jar
```

**1-4. gradlew 스크립트 다운로드 및 실행 권한 부여**
```bash
# Linux/Mac
curl -L -o gradlew https://raw.githubusercontent.com/gradle/gradle/v{VERSION}/gradlew
chmod +x gradlew

# Windows
curl -L -o gradlew.bat https://raw.githubusercontent.com/gradle/gradle/v{VERSION}/gradlew.bat
```

#### 2단계: settings.gradle 작성 (서비스 목록 기반)

dev-plan.md의 서비스 목록을 기반으로 rootProject.name과 include를 작성한다.

```groovy
rootProject.name = '{project-name}'

include 'common'
include '{service-name-1}'
include '{service-name-2}'
// 서비스 목록 추가
```

#### 3단계: Version Catalog + 루트 build.gradle 작성

`{NPD_PLUGIN_DIR}/resources/references/java-build-gradle-standard.md` 표준 형식에 따라 작성한다.

**3-a. `gradle/libs.versions.toml` 생성 (Version Catalog):**

모든 플러그인·라이브러리 버전을 이 파일에서 관리한다. `ext` 블록에 버전을 하드코딩하지 않는다.

```bash
mkdir -p gradle
```

- `java-build-gradle-standard.md`의 Version Catalog 템플릿에서 **필수 코어** 항목을 복사한다
- **선택 라이브러리**는 설계 산출물을 분석하여 필요한 항목만 주석 해제한다 (전체 복사 금지, 판단 기준은 표준 파일 참조)
- **`"{최신 stable 조회}"` 플레이스홀더를 실제 버전으로 교체한다**:
  - Spring Boot → [Spring Initializr](https://start.spring.io)에서 최신 GA 버전 확인
  - Gradle 플러그인 → [Gradle Plugin Portal](https://plugins.gradle.org)에서 확인
  - 라이브러리 → [Maven Central](https://search.maven.org)에서 최신 stable 확인 (RC/SNAPSHOT 제외)
  - Spring Cloud → Spring Boot 버전과 호환되는 릴리스 트레인 확인
- **플레이스홀더를 남겨둔 채 커밋하면 빌드가 실패한다**

**3-b. 루트 build.gradle 작성:**

Version Catalog의 `alias(libs.plugins.*)`, `libs.*` 참조를 사용한다.

**group 값 설정 (필수):**
```groovy
// AGENTS.md에서 ORG, ROOT 값을 읽어 설정
group = 'com.{ORG}.{ROOT}'
```
> 설계서에 다른 group 값이 명시되어 있어도 AGENTS.md의 `{ORG}.{ROOT}` 기반으로 덮어쓴다.

#### 4단계: 서비스별 build.gradle 작성

서비스 아키텍처 패턴(Layered, Hexagonal 등)에 맞는 의존성을 포함하여 각 서비스 모듈의 build.gradle을 작성한다.

#### 5단계: 서비스별 application.yml 작성

`{NPD_PLUGIN_DIR}/resources/references/java-config-manifest-standard.md` 표준 형식에 따라 작성한다. 환경변수는 실제 값 대신 placeholder로만 기재한다.

```yaml
# 예시 — 실제 값 하드코딩 금지
spring:
  datasource:
    url: ${DB_URL}
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}

# Logging — java-config-manifest-standard.md 표준
logging:
  file:
    name: ${LOG_FILE_PATH:logs/{서비스명}.log}
  logback:
    rollingpolicy:
      file-name-pattern: ${LOG_ROLLING_FILE_PATTERN:logs/{서비스명}.%d{yyyy-MM-dd}.%i.log}
      max-file-size: ${LOG_MAX_FILE_SIZE:100MB}
      max-history: ${LOG_MAX_HISTORY:30}
      total-size-cap: ${LOG_TOTAL_SIZE_CAP:1GB}
```

#### 6단계: 공통 모듈 개발

`docs/develop/dev-plan.md` 섹션 10-1(공통 모듈 구성)을 기반으로 common 모듈의 공통 컴포넌트(베이스 클래스, 공통 유틸, 예외 처리 등)를 구현한다.

#### 7단계: 공통 모듈 컴파일 검증

```bash
./gradlew common:compileJava
```

**검토**
- 빌드 성공 여부 확인
- 표준 준수 여부 검토

### 검증 방법

```bash
# Gradle Wrapper 동작 검증
./gradlew --version

# 공통 모듈 컴파일 검증
./gradlew common:compileJava
```

## 출력 형식

- **Gradle Wrapper**: `gradle/wrapper/gradle-wrapper.properties`, `gradle-wrapper.jar`, `gradlew`, `gradlew.bat`
- **settings.gradle**: `rootProject.name` + `include` 서비스 목록
- **gradle/libs.versions.toml**: Version Catalog (모든 버전 중앙 관리, 플레이스홀더 없이 실제 버전 기입 완료)
- **build.gradle**: `java-build-gradle-standard.md` 표준 형식 (Version Catalog 참조, `ext` 블록 버전 하드코딩 없음)
- **application.yml**: `java-config-manifest-standard.md` 표준 형식

## 품질 기준

- [ ] Java 버전에 맞는 Gradle 버전 자동 결정
- [ ] gradlew 실행 권한 부여
- [ ] `./gradlew --version` 검증 통과
- [ ] settings.gradle에 모든 서비스가 include
- [ ] `gradle/libs.versions.toml` 존재하고 플레이스홀더 없이 실제 버전 기입 완료
- [ ] 루트 build.gradle이 Version Catalog 참조 (`alias(libs.plugins.*)`, `libs.*`) 사용
- [ ] 서비스별 application.yml이 설정 Manifest 표준 준수
- [ ] 환경변수 placeholder 사용 (하드코딩 금지)
- [ ] 공통 모듈 compileJava 성공

## 주의사항

- SpringBoot/Java 버전은 `dev-plan.md`의 '10-5. 기술스택 정보' 참조
- `{VERSION}`을 실제 버전 번호로 교체 (예: 8.10.2)
- Windows에서는 `./gradlew` 대신 `.\gradlew.bat` 사용
- application.yml의 환경변수 실제 값은 이 단계에서 설정하지 않음 (backing-service-setup.md 단계에서 .env.example로 통일)
- 참조 파일 경로는 `{NPD_PLUGIN_DIR}`을 절대 경로로 치환하여 사용
