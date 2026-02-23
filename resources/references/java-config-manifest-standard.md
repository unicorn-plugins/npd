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
    com.{회사/조직명}.{시스템명}: ${LOG_LEVEL_APP:DEBUG}
    org.springframework.web: ${LOG_LEVEL_WEB:INFO}
    org.hibernate.SQL: ${LOG_LEVEL_SQL:INFO}
    org.hibernate.type: ${LOG_LEVEL_SQL_TYPE:INFO}
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} - %msg%n"
    file: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
  file:
    name: ${LOG_FILE_PATH:logs/{서비스명}.log}
```

## DB/Redis 설정 예제
```
spring:
  datasource:
    url: jdbc:${DB_KIND:postgresql}://${DB_HOST:localhost}:${DB_PORT:5432}/${DB_NAME:}
    username: ${DB_USERNAME:}
    password: ${DB_PASSWORD:}
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
      password: ${REDIS_PASSWORD:}
      timeout: 2000ms
      lettuce:
        pool:
          max-active: 8
          max-idle: 8
          min-idle: 0
          max-wait: -1ms
      database: ${REDIS_DATABASE:}
```

## 참조
- 이 파일은 `resources/guides/develop/backend-env-setup.md`에서 참조됩니다.
