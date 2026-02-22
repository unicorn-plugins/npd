# 서비스실행프로파일작성가이드

## 목적
백킹서비스설치결과서를 기반으로 각 서비스별 Gradle 실행 프로파일을 작성한다. application.yml의 하드코딩된 값을 환경변수로 전환하고, 실행 프로파일에 백킹서비스 연결 정보를 정확히 반영한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 백킹서비스 설치 결과서 | `(런타임 결정)` | 연결 정보 참조 |
| 서비스 application.yml | `(런타임 결정)` | 환경변수 매핑 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 서비스 실행 프로파일 | `{service-name}/.run/{service-name}.run.xml` |

## 방법론

**수행원칙**
- 설정 Manifest(src/main/resources/application*.yml)의 각 항목의 값은 하드코딩하지 않고 환경변수 처리
- '백킹서비스설치결과서'에 정의된 값과 일치

**수행순서**
- 준비:
  - 백킹서비스설치결과서 분석
- 실행:
  - 각 서비스별 서브에이젼트로 병렬 수행
  - 설정 Manifest 수정
    - 하드코딩 되어 있는 값이 있으면 환경변수로 변환
    - 특히, 데이터베이스, MQ 등의 연결 정보는 반드시 환경변수로 변환해야 함
    - 민감한 정보의 디퐅트값은 생략하거나 간략한 값으로 지정
  - '실행프로파일 작성 가이드'에 따라 서비스 실행프로파일 작성
  - 결과: {service-name}/.run

**실행프로파일 작성 가이드**
- {service-name}/.run/{service-name}.run.xml 파일로 작성
- Spring Boot가 아니고 **Gradle 실행 프로파일**이어야 함: '실행프로파일 예시' 참조
- 백킹서비스설치결과서에 정의된 값과 일치하게 작성
- 개발모드의 DDL_AUTO값은 update로 함
- JWT Secret Key는 모든 서비스가 동일해야 함
- application.yaml의 환경변수와 일치하도록 환경변수 설정
- application.yaml의 민감 정보는 기본값으로 지정하지 않고 실제 백킹서비스 정보로 지정
- 기존에 파일이 있으면 내용을 분석하여 항목 추가/수정/삭제

**실행프로파일 예시**
```xml
<component name="ProjectRunConfigurationManager">
  <configuration default="false" name="user-service" type="GradleRunConfiguration" factoryName="Gradle">
    <ExternalSystemSettings>
      <option name="env">
        <map>
          <entry key="ACCOUNT_LOCK_DURATION_MINUTES" value="30" />
          <entry key="CACHE_TTL" value="1800" />
          <entry key="DB_HOST" value="20.249.197.193" /> <!-- LoadBalancer External IP 사용 -->
          <entry key="DB_NAME" value="tripgen_user_db" />
          <entry key="DB_PASSWORD" value="tripgen_user_123" />
          <entry key="DB_PORT" value="5432" />
          <entry key="DB_USERNAME" value="tripgen_user" />
          <entry key="FILE_BASE_URL" value="http://localhost:8081" />
          <entry key="FILE_MAX_SIZE" value="5242880" />
          <entry key="FILE_UPLOAD_PATH" value="/app/uploads" />
          <entry key="JPA_DDL_AUTO" value="update" />
          <entry key="JPA_SHOW_SQL" value="true" />
          <entry key="JWT_ACCESS_TOKEN_EXPIRATION" value="86400" />
          <entry key="JWT_REFRESH_TOKEN_EXPIRATION" value="604800" />
          <entry key="JWT_SECRET" value="dev-jwt-secret-key-for-development-only" />
          <entry key="LOG_LEVEL_APP" value="DEBUG" />
          <entry key="LOG_LEVEL_ROOT" value="INFO" />
          <entry key="LOG_LEVEL_SECURITY" value="DEBUG" />
          <entry key="MAX_LOGIN_ATTEMPTS" value="5" />
          <entry key="PASSWORD_MIN_LENGTH" value="8" />
          <entry key="REDIS_DATABASE" value="0" />
          <entry key="REDIS_HOST" value="20.214.121.28" /> <!-- Redis LoadBalancer External IP 사용 -->
          <entry key="REDIS_PASSWORD" value="" />
          <entry key="REDIS_PORT" value="6379" />
          <entry key="SERVER_PORT" value="8081" />
          <entry key="SPRING_PROFILES_ACTIVE" value="dev" />
          <!-- MQ 사용하는 서비스의 경우 MQ 유형에 맞게 추가 -->
          <!-- RabbitMQ 예시 -->
          <entry key="RABBITMQ_HOST" value="20.xxx.xxx.xxx" />
          <entry key="RABBITMQ_PORT" value="5672" />
          <!-- Kafka 예시 -->
          <entry key="KAFKA_BOOTSTRAP_SERVERS" value="20.xxx.xxx.xxx:9092" />
          <!-- 기타 MQ의 경우 해당 MQ에 필요한 연결 정보를 환경변수로 추가 -->
        </map>
      </option>
      <option name="executionName" />
      <option name="externalProjectPath" value="$PROJECT_DIR$" />
      <option name="externalSystemIdString" value="GRADLE" />
      <option name="scriptParameters" value="" />
      <option name="taskDescriptions">
        <list />
      </option>
      <option name="taskNames">
        <list>
          <option value="user-service:bootRun" />
        </list>
      </option>
      <option name="vmOptions" />
    </ExternalSystemSettings>
    <ExternalSystemDebugServerProcess>true</ExternalSystemDebugServerProcess>
    <ExternalSystemReattachDebugProcess>true</ExternalSystemReattachDebugProcess>
    <EXTENSION ID="com.intellij.execution.ExternalSystemRunConfigurationJavaExtension">
      <extension name="net.ashald.envfile">
        <option name="IS_ENABLED" value="false" />
        <option name="IS_SUBST" value="false" />
        <option name="IS_PATH_MACRO_SUPPORTED" value="false" />
        <option name="IS_IGNORE_MISSING_FILES" value="false" />
        <option name="IS_ENABLE_EXPERIMENTAL_INTEGRATIONS" value="false" />
        <ENTRIES>
          <ENTRY IS_ENABLED="true" PARSER="runconfig" IS_EXECUTABLE="false" />
        </ENTRIES>
      </extension>
    </EXTENSION>
    <DebugAllEnabled>false</DebugAllEnabled>
    <RunAsTest>false</RunAsTest>
    <method v="2" />
  </configuration>
</component>
```

## 출력 형식

- 파일명: `{service-name}/.run/{service-name}.run.xml`
- Gradle 실행 프로파일 XML 형식 (Spring Boot 실행 구성 아님)
- 모든 연결 정보는 환경변수 `<entry key="..." value="..." />` 형태로 기재

## 품질 기준

- [ ] Gradle 실행 프로파일 형식으로 작성
- [ ] 백킹서비스 설치 결과서의 연결 정보와 일치
- [ ] application.yml 민감 정보 하드코딩 금지
- [ ] 환경변수와 실행 프로파일 간 불일치 없음

## 주의사항

- Spring Boot 실행 구성이 아닌 **Gradle 실행 프로파일**로 작성
- JWT Secret Key는 모든 서비스가 동일한 값을 사용해야 함
- 개발 환경의 JPA DDL_AUTO는 반드시 `update`로 설정
- 민감 정보의 기본값은 생략하거나 간략한 더미 값 사용 (application.yml 기준)
- 실행 프로파일에서는 실제 백킹서비스 연결 정보 사용
