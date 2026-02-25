# 실행 프로파일 작성 가이드

## 목적

백킹서비스 설치 결과를 기반으로 각 서비스별 IntelliJ Gradle 실행 프로파일을 작성하고, application.yml의 환경변수를 매핑한다. Phase 2(API 계약 기반 병렬 개발) 진입 전에 완료해야 하는 게이트 단계이다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 백킹서비스 설치 결과서 | `docs/develop/backing-service-result.md` | DB/Cache/MQ 연결 정보 참조 |
| 서비스별 application.yml | `{service-name}/src/main/resources/application.yml` | 환경변수 목록 추출 |
| Docker Compose 파일 | `./docker-compose.yml` | 서비스 포트·호스트 매핑 확인 |
| .env.example | `./.env.example` | 환경변수 기본값 참조 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 서비스별 실행 프로파일 | `{service-name}/.run/{service-name}.run.xml` |

## 방법론

### 작성 원칙

- **Gradle 실행 프로파일**: Spring Boot 실행 구성이 아닌 Gradle 실행 프로파일로 작성
- **환경변수 기반 설정**: application.yml의 하드코딩된 값을 모두 환경변수로 전환
- **백킹서비스 일치**: 실행 프로파일의 연결 정보가 `backing-service-result.md`와 정확히 일치
- **서비스별 병렬 작성**: 서비스 간 독립적이므로 병렬 수행 가능

### 작성 순서

**준비**: 백킹서비스 설치 결과서 분석, 서비스별 application.yml 환경변수 확인

**실행** (서비스별 병렬):

1. **환경변수 목록 추출**
   - application.yml에서 `${ENV_VAR:default}` 패턴의 환경변수 전체 목록 추출
   - 하드코딩된 민감 정보(DB 비밀번호, API 키 등)가 있으면 환경변수로 전환

2. **연결 정보 매핑**
   - `backing-service-result.md`에서 호스트, 포트, 인증정보 추출
   - docker-compose 환경: `localhost` + 매핑된 포트
   - `.env.example`의 기본값과 대조하여 불일치 확인

3. **Gradle 실행 프로파일 XML 작성**
   - `{service-name}/.run/` 디렉토리 생성
   - `{service-name}.run.xml` 작성 (아래 출력 형식 참조)
   - 기존 파일이 있으면 내용을 분석하여 항목 추가/수정/삭제

4. **환경변수 일치 검증**
   - application.yml의 모든 `${ENV_VAR}` 가 실행 프로파일에 존재하는지 확인
   - 실행 프로파일의 DB/Cache/MQ 연결값이 `backing-service-result.md`와 일치하는지 확인

**검토**: application.yml ↔ 실행 프로파일 환경변수 일치 여부 확인

### 검증 방법

- application.yml의 `${}` 환경변수 수 == 실행 프로파일의 `<entry>` 수
- DB/Cache/MQ 연결 정보가 `backing-service-result.md`와 일치
- JWT_SECRET 값이 모든 서비스에서 동일

### 병렬 처리 가이드

- 서비스별로 독립 작성 가능 → 서브에이전트 병렬 수행
- 공통 환경변수(JWT_SECRET, REDIS_HOST 등)는 동일 값으로 통일

## 출력 형식

### Gradle 실행 프로파일 XML 템플릿

```xml
<component name="ProjectRunConfigurationManager">
  <configuration default="false" name="{service-name}" type="GradleRunConfiguration" factoryName="Gradle">
    <ExternalSystemSettings>
      <option name="env">
        <map>
          <!-- 서버 설정 -->
          <entry key="SERVER_PORT" value="{port}" />
          <entry key="SPRING_PROFILES_ACTIVE" value="dev" />

          <!-- 데이터베이스 -->
          <entry key="DB_HOST" value="{db-host}" />
          <entry key="DB_PORT" value="{db-port}" />
          <entry key="DB_NAME" value="{db-name}" />
          <entry key="DB_USERNAME" value="{db-user}" />
          <entry key="DB_PASSWORD" value="{db-password}" />

          <!-- JPA -->
          <entry key="JPA_DDL_AUTO" value="update" />
          <entry key="JPA_SHOW_SQL" value="true" />

          <!-- Redis (캐시 사용 서비스) -->
          <entry key="REDIS_HOST" value="{redis-host}" />
          <entry key="REDIS_PORT" value="{redis-port}" />
          <entry key="REDIS_PASSWORD" value="{redis-password}" />
          <entry key="REDIS_DATABASE" value="0" />

          <!-- JWT (인증 사용 서비스) -->
          <entry key="JWT_SECRET" value="{jwt-secret}" />
          <entry key="JWT_ACCESS_TOKEN_EXPIRATION" value="86400" />
          <entry key="JWT_REFRESH_TOKEN_EXPIRATION" value="604800" />

          <!-- MQ (비동기 통신 서비스만, MQ 유형에 맞게 선택) -->
          <!-- RabbitMQ -->
          <entry key="RABBITMQ_HOST" value="{mq-host}" />
          <entry key="RABBITMQ_PORT" value="5672" />
          <!-- Kafka -->
          <entry key="KAFKA_BOOTSTRAP_SERVERS" value="{kafka-host}:9092" />

          <!-- 로깅 -->
          <entry key="LOG_LEVEL_ROOT" value="INFO" />
          <entry key="LOG_LEVEL_APP" value="DEBUG" />
          <entry key="LOG_FILE_PATH" value="logs/{service-name}.log" />
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
          <option value="{service-name}:bootRun" />
        </list>
      </option>
      <option name="vmOptions" />
    </ExternalSystemSettings>
    <ExternalSystemDebugServerProcess>true</ExternalSystemDebugServerProcess>
    <ExternalSystemReattachDebugProcess>true</ExternalSystemReattachDebugProcess>
    <DebugAllEnabled>false</DebugAllEnabled>
    <RunAsTest>false</RunAsTest>
    <method v="2" />
  </configuration>
</component>
```

### 환경변수 카테고리별 필수 항목

| 카테고리 | 환경변수 | 적용 조건 |
|---------|---------|----------|
| 서버 | SERVER_PORT, SPRING_PROFILES_ACTIVE | 모든 서비스 |
| DB | DB_HOST, DB_PORT, DB_NAME, DB_USERNAME, DB_PASSWORD | DB 사용 서비스 |
| JPA | JPA_DDL_AUTO, JPA_SHOW_SQL | DB 사용 서비스 |
| Redis | REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DATABASE | 캐시 사용 서비스 |
| JWT | JWT_SECRET, JWT_ACCESS_TOKEN_EXPIRATION, JWT_REFRESH_TOKEN_EXPIRATION | 인증 사용 서비스 |
| MQ | MQ 유형별 연결 환경변수 | 비동기 통신 서비스만 |
| 로깅 | LOG_LEVEL_ROOT, LOG_LEVEL_APP, LOG_FILE_PATH | 모든 서비스 |

## 품질 기준

- [ ] Gradle 실행 프로파일 형식으로 작성 (Spring Boot 실행 구성 아님)
- [ ] 백킹서비스 설치 결과서의 연결 정보와 정확히 일치
- [ ] application.yml의 모든 `${}` 환경변수가 실행 프로파일에 매핑됨
- [ ] 환경변수와 실행 프로파일 간 불일치 없음
- [ ] JWT_SECRET 값이 모든 서비스에서 동일
- [ ] 개발 환경 JPA_DDL_AUTO가 `update`로 설정됨
- [ ] 민감 정보가 application.yml에 하드코딩되지 않음

## 주의사항

- **Gradle 실행 프로파일**로 작성 (Spring Boot 실행 구성이 아님)
- JWT Secret Key는 모든 서비스가 **동일한 값**을 사용해야 함
- 개발 환경의 JPA DDL_AUTO는 반드시 `update`로 설정
- application.yml의 민감 정보 기본값은 생략하거나 간략한 더미 값 사용
- 실행 프로파일에서는 **실제 백킹서비스 연결 정보** 사용
- docker-compose 환경에서는 호스트가 `localhost`
- MQ 환경변수는 설계서에 비동기 통신이 명시된 서비스에만 포함
- 기존 `.run/` 파일이 있으면 분석 후 항목 추가/수정/삭제 (덮어쓰기 금지)
