# Java 설정 Manifest 표준

## 설정 Manifest 원칙

- common모듈은 작성하지 않음
- application.yml에 작성
- 하드코딩하지 않고 환경변수 사용
  특히, 데이터베이스, MQ 등의 연결 정보는 반드시 환경변수로 변환해야 함
- spring.application.name은 서비스명과 동일하게 함
- Redis Database는 각 서비스마다 다르게 설정
- 민감한 정보의 디폴트값은 생략하거나 간략한 값으로 지정
- JWT Secret Key는 모든 서비스가 동일해야 함
- MQ는 Spring Cloud Stream으로 추상화하여 binder 교체만으로 로컬/클라우드 전환 가능하게 함
- **`server.servlet.context-path`를 사용하지 않는다** — 서비스별 경로 접두사는 API Gateway(라우팅 규칙)에서 관리하며, 각 서비스는 루트(`/`)에서 시작하는 API를 제공한다. context-path를 설정하면 Actuator, Swagger UI, 내부 통신 경로가 모두 영향을 받아 운영 복잡도가 증가한다.
- 아래 각 섹션의 표준을 준수하여 설정

## application.yml 표준 설정

### JWT
```
# JWT
jwt:
  secret: ${JWT_SECRET:}
  access-token-validity: ${JWT_ACCESS_TOKEN_VALIDITY:1800}
  refresh-token-validity: ${JWT_ACCESS_TOKEN_VALIDITY:86400}
```

### CORS
```
# CORS Configuration
cors:
  allowed-origins: ${CORS_ALLOWED_ORIGINS:}
```

### Actuator
```
# Actuator
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
      base-path: /actuator
  endpoint:
    health:
      show-details: always
      show-components: always
  health:
    livenessState:
      enabled: true
    readinessState:
      enabled: true
```

### OpenAPI Documentation
```
# OpenAPI Documentation
springdoc:
  api-docs:
    path: /v3/api-docs
  swagger-ui:
    path: /swagger-ui.html
    tags-sorter: alpha
    operations-sorter: alpha
  show-actuator: false
```

### Logging
```
# Logging
logging:
  level:
    root: ${LOG_LEVEL_ROOT:INFO}
    com.{ORG}.{ROOT}: ${LOG_LEVEL_APP:DEBUG}  # CLAUDE.md의 ORG, ROOT 값 참조
    org.springframework.web: ${LOG_LEVEL_WEB:INFO}
    org.hibernate.SQL: ${LOG_LEVEL_SQL:INFO}
    org.hibernate.type: ${LOG_LEVEL_SQL_TYPE:INFO}
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} - %msg%n"
    file: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
  file:
    name: ${LOG_FILE_PATH:logs/{서비스명}.log}
  logback:
    rollingpolicy:
      file-name-pattern: ${LOG_ROLLING_FILE_PATTERN:logs/{서비스명}.%d{yyyy-MM-dd}.%i.log}
      max-file-size: ${LOG_MAX_FILE_SIZE:100MB}
      max-history: ${LOG_MAX_HISTORY:30}
      total-size-cap: ${LOG_TOTAL_SIZE_CAP:1GB}
```

## DB/Redis 설정 예제
```
spring:
  datasource:
    url: jdbc:${DB_KIND:postgresql}://${DB_HOST:localhost}:${DB_PORT:5432}/${DB_NAME:{서비스명}}
    username: ${DB_USER:{ROOT}}
    password: ${DB_PASSWORD:P@ssw0rd$}
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
      leak-detection-threshold: 60000
  # JPA 설정
  jpa:
    show-sql: ${SHOW_SQL:true}
    properties:
      hibernate:
        format_sql: true
        use_sql_comments: true
    hibernate:
      ddl-auto: ${DDL_AUTO:update}

  # Redis 설정
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      timeout: 2000ms
      lettuce:
        pool:
          max-active: 8
          max-idle: 8
          min-idle: 0
          max-wait: -1ms
      database: ${REDIS_DATABASE:0}
```

> - `DB_NAME`: 서비스명과 동일 (_db 접미사 없음). 각 서비스가 자신의 database명을 지정한다.
> - `DB_USER` / `DB_PASSWORD`: backing-service-setup.md의 자격 증명 규칙을 따른다.
> - `REDIS_PASSWORD`: 로컬 개발 환경에서는 인증 없이 구성하므로 생략한다.
> - `REDIS_DATABASE`: 각 서비스마다 다른 번호를 사용한다 (0, 1, 2, ...).

## MQ 설정 예제 (Spring Cloud Stream)

MQ는 **Spring Cloud Stream**으로 추상화하여 로컬 개발(Kafka/RabbitMQ)과 클라우드 운영(Azure Event Hub 등)을 설정 변경만으로 전환한다.

### 추상화 구조

```
애플리케이션 코드 (함수형 바인딩: Consumer/Supplier/Function)
       ↓ 추상화 계층
   Spring Cloud Stream
       ↓ binder 선택 (application.yml 설정)
  ┌──────────┬──────────────┬───────────────────┐
  │ Kafka    │ RabbitMQ     │ Azure Event Hub   │
  │ binder   │ binder       │ binder            │
  └──────────┴──────────────┴───────────────────┘
```

> **핵심 원칙**: 애플리케이션 코드는 binder에 의존하지 않는다. MQ 전환 시 코드 변경 없이 의존성 + 설정만 교체한다.

### 지원 Binder 리스트

**공식 (Spring 팀 유지보수)**

| Binder | 대상 MQ | Gradle 의존성 |
|--------|---------|--------------|
| Kafka | Apache Kafka | `org.springframework.cloud:spring-cloud-stream-binder-kafka` |
| Kafka Streams | Apache Kafka (네이티브 스트림) | `org.springframework.cloud:spring-cloud-stream-binder-kafka-streams` |
| RabbitMQ | RabbitMQ | `org.springframework.cloud:spring-cloud-stream-binder-rabbit` |
| Pulsar | Apache Pulsar | `org.springframework.cloud:spring-cloud-stream-binder-pulsar` |
| Amazon Kinesis | AWS Kinesis | `org.springframework.cloud:spring-cloud-stream-binder-kinesis` |

**벤더 유지보수 (각 클라우드 벤더가 관리)**

| Binder | 대상 Cloud MQ | Gradle 의존성 | 벤더 |
|--------|-------------|--------------|------|
| Azure Event Hub | Azure Event Hubs | `com.azure.spring:spring-cloud-azure-stream-binder-eventhubs` | Microsoft |
| Azure Service Bus | Azure Service Bus | `com.azure.spring:spring-cloud-azure-stream-binder-servicebus` | Microsoft |
| Google Pub/Sub | Google Cloud Pub/Sub | `com.google.cloud:spring-cloud-gcp-pubsub-stream-binder` | Google |
| Solace PubSub+ | Solace PubSub+ | `com.solace.spring.cloud:spring-cloud-stream-binder-solace` | Solace |
| Apache RocketMQ | Apache RocketMQ | `com.alibaba.cloud:spring-cloud-starter-stream-rocketmq` | Alibaba |
| AWS SQS | Amazon SQS | `de.idealo.spring:spring-cloud-stream-binder-sqs` | 커뮤니티 |

### 로컬 → 운영 전환 매핑

| 로컬 개발 (docker-compose) | 운영 클라우드 서비스 | 전환 방법 |
|---------------------------|-------------------|----------|
| Kafka | Azure Event Hub | binder + 설정 교체 |
| Kafka | AWS Kinesis | binder + 설정 교체 |
| Kafka | Google Pub/Sub | binder + 설정 교체 |
| RabbitMQ | Azure Service Bus | binder + 설정 교체 |
| RabbitMQ | Solace PubSub+ | binder + 설정 교체 |
| RabbitMQ | AWS SQS | binder + 설정 교체 |

> 모든 경우 **애플리케이션 코드는 변경 없이** 의존성(binder jar) + `application-{profile}.yml` 설정만 교체한다.

### Gradle 의존성 구성

로컬 개발용 binder와 운영용 binder를 프로파일로 분리 관리한다.

```groovy
// === 로컬 개발 binder (택 1) ===
// Kafka binder (로컬 개발 기본)
implementation 'org.springframework.cloud:spring-cloud-stream-binder-kafka'

// RabbitMQ binder (RabbitMQ 사용 시)
// implementation 'org.springframework.cloud:spring-cloud-stream-binder-rabbit'

// === 운영 binder (클라우드 MQ 사용 시 택 1 추가) ===
// Azure Event Hub
// implementation 'com.azure.spring:spring-cloud-azure-stream-binder-eventhubs'

// Azure Service Bus
// implementation 'com.azure.spring:spring-cloud-azure-stream-binder-servicebus'

// Google Pub/Sub
// implementation 'com.google.cloud:spring-cloud-gcp-pubsub-stream-binder'

// AWS Kinesis
// implementation 'org.springframework.cloud:spring-cloud-stream-binder-kinesis'

// AWS SQS
// implementation 'de.idealo.spring:spring-cloud-stream-binder-sqs'

// Solace PubSub+
// implementation 'com.solace.spring.cloud:spring-cloud-stream-binder-solace'
```

### 로컬 개발 설정

#### application.yml (Kafka)

```yaml
spring:
  cloud:
    stream:
      default-binder: kafka
      kafka:
        binder:
          brokers: ${KAFKA_BROKERS:localhost:9094}
          auto-create-topics: true
      bindings:
        # 예시: 주문 이벤트 발행/구독
        orderEvent-out-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
        orderEvent-in-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
          group: ${spring.application.name}
```

#### application.yml (RabbitMQ)

```yaml
spring:
  cloud:
    stream:
      default-binder: rabbit
      rabbit:
        binder:
          addresses: ${MQ_HOST:localhost}:${MQ_PORT:5672}
          user: ${MQ_USER:{ROOT}}
          password: ${MQ_PASSWORD:P@ssw0rd$}
      bindings:
        orderEvent-out-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
        orderEvent-in-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
          group: ${spring.application.name}
```

### 운영 환경 설정 (application-prod.yml)

> **공통 원칙**: `bindings` 섹션(destination, group)은 로컬과 동일하게 유지한다. binder 설정만 교체한다.

#### Azure Event Hub

```yaml
spring:
  cloud:
    stream:
      default-binder: eventhubs
      eventhubs:
        binder:
          connection-string: ${AZURE_EVENTHUB_CONNECTION_STRING}
          checkpoint-storage-account: ${AZURE_STORAGE_ACCOUNT}
          checkpoint-access-key: ${AZURE_STORAGE_ACCESS_KEY}
          checkpoint-container: ${AZURE_CHECKPOINT_CONTAINER:checkpoint}
      bindings:
        orderEvent-out-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
        orderEvent-in-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
          group: ${spring.application.name}
```

#### Azure Service Bus

```yaml
spring:
  cloud:
    stream:
      default-binder: servicebus
      servicebus:
        binder:
          connection-string: ${AZURE_SERVICEBUS_CONNECTION_STRING}
      bindings:
        orderEvent-out-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
          producer:
            entity-type: topic    # topic 또는 queue
        orderEvent-in-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
          group: ${spring.application.name}
          consumer:
            entity-type: topic
```

#### Google Pub/Sub

```yaml
spring:
  cloud:
    stream:
      default-binder: pubsub
      gcp:
        pubsub:
          project-id: ${GCP_PROJECT_ID}
          credentials:
            location: ${GCP_CREDENTIALS_PATH}
      bindings:
        orderEvent-out-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
        orderEvent-in-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
          group: ${spring.application.name}
```

#### AWS Kinesis

```yaml
spring:
  cloud:
    stream:
      default-binder: kinesis
      kinesis:
        binder:
          auto-create-stream: true
          checkpoint:
            table: ${AWS_KINESIS_CHECKPOINT_TABLE:checkpoint}
      bindings:
        orderEvent-out-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
        orderEvent-in-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
          group: ${spring.application.name}
  # AWS 자격 증명
  cloud:
    aws:
      region:
        static: ${AWS_REGION:ap-northeast-2}
      credentials:
        access-key: ${AWS_ACCESS_KEY}
        secret-key: ${AWS_SECRET_KEY}
```

#### AWS SQS

```yaml
spring:
  cloud:
    stream:
      default-binder: sqs
      sqs:
        binder:
          region: ${AWS_REGION:ap-northeast-2}
      bindings:
        orderEvent-out-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
        orderEvent-in-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
          group: ${spring.application.name}
  # AWS 자격 증명
  cloud:
    aws:
      credentials:
        access-key: ${AWS_ACCESS_KEY}
        secret-key: ${AWS_SECRET_KEY}
```

#### Solace PubSub+

```yaml
spring:
  cloud:
    stream:
      default-binder: solace
      solace:
        binder:
          host: ${SOLACE_HOST}
          msg-vpn: ${SOLACE_MSG_VPN:default}
          client-username: ${SOLACE_USERNAME}
          client-password: ${SOLACE_PASSWORD}
      bindings:
        orderEvent-out-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
        orderEvent-in-0:
          destination: ${MQ_ORDER_TOPIC:order-events}
          group: ${spring.application.name}
```

> - **로컬 개발**: docker-compose의 Kafka 또는 RabbitMQ를 사용한다 (backing-service-setup.md 참조).
> - **운영 전환**: `spring.profiles.active=prod`로 프로파일을 변경하고, binder 의존성을 추가한다.
> - **bindings 정의는 동일**: binder가 바뀌어도 destination/group 설정은 그대로 유지된다.
> - **클라우드 자격 증명**: 환경변수로 주입하며, 하드코딩하지 않는다.
> - 배포 시 binder 전환 방법은 배포 가이드를 참조한다.

## 참조
- 이 파일은 `resources/guides/develop/backend-env-setup.md`에서 참조됩니다.
