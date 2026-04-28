# MQ 카테고리 가이드 — 로컬 개발 환경

## 목적

MQ 제품 선택 시 docker-compose 구성 차이점 및 Cloud MQ 전환 전략을 제공한다.
이 가이드는 `backing-service-setup.md`의 보조 가이드이다.

---

## Self-hosted MQ 비교 테이블

로컬 개발 환경에서 docker-compose로 구동 가능한 Self-hosted MQ 비교.

| 설정 항목 | RabbitMQ | Kafka (KRaft) |
|-----------|----------|---------------|
| **image** | `rabbitmq:3-management` | `bitnami/kafka:3.7` |
| **메시징 포트** | 5672 | 9094 (EXTERNAL) |
| **관리 포트** | 15672 | (없음) |
| **데이터 볼륨 경로** | `/var/lib/rabbitmq` | `/bitnami/kafka` |
| **계정 환경변수** | `RABBITMQ_DEFAULT_USER` / `RABBITMQ_DEFAULT_PASS` | (PLAINTEXT, 인증 없음) |
| **Healthcheck** | `rabbitmq-diagnostics -q ping` | `kafka-topics.sh --bootstrap-server localhost:9092 --list` |
| **Spring binder** | `spring-cloud-stream-binder-rabbit` | `spring-cloud-stream-binder-kafka` |

### .env 변수 비교

| 변수 | RabbitMQ | Kafka |
|------|----------|-------|
| `MQ_USER` | `{ROOT}` | (불필요) |
| `MQ_PASSWORD` | `P@ssw0rd$` | (불필요) |
| `MQ_PORT` | 5672 | — |
| `MQ_MGMT_PORT` | 15672 | — |
| `MQ_HOST` | localhost | — |
| `MQ_VHOST` | `/` | — |
| `KAFKA_PORT` | — | 9094 |

---

## Self-hosted MQ docker-compose.yml 스니펫

### RabbitMQ

```yaml
  rabbitmq:
    image: rabbitmq:3-management
    environment:
      RABBITMQ_DEFAULT_USER: ${MQ_USER}
      RABBITMQ_DEFAULT_PASS: ${MQ_PASSWORD}
      RABBITMQ_DEFAULT_VHOST: ${MQ_VHOST:-/}
    ports:
      - "${MQ_PORT:-5672}:5672"
      - "${MQ_MGMT_PORT:-15672}:15672"
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 15s
      timeout: 10s
      retries: 5
```

### Kafka (KRaft 모드)

```yaml
  kafka:
    image: bitnami/kafka:3.7
    environment:
      KAFKA_CFG_NODE_ID: 1
      KAFKA_CFG_PROCESS_ROLES: broker,controller
      KAFKA_CFG_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_CFG_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093,EXTERNAL://:9094
      KAFKA_CFG_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,EXTERNAL://localhost:${KAFKA_PORT:-9094}
      KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_CFG_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CFG_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      ALLOW_PLAINTEXT_LISTENER: "yes"
    ports:
      - "${KAFKA_PORT:-9094}:9094"
    volumes:
      - kafka-data:/bitnami/kafka
    healthcheck:
      test: ["CMD-SHELL", "kafka-topics.sh --bootstrap-server localhost:9092 --list"]
      interval: 15s
      timeout: 10s
      retries: 5
```

> Kafka는 KRaft 모드(Zookeeper 없음)로 구성한다.

**volumes 선언:**

```yaml
volumes:
  rabbitmq-data:   # RabbitMQ 사용 시
  kafka-data:      # Kafka 사용 시
```

---

## Cloud Managed MQ 전환 가이드

### 전환 전략: Spring Cloud Stream 추상화

> 로컬 개발 시 Self-hosted MQ(RabbitMQ/Kafka)를 사용하고,
> 운영 배포 시 Cloud MQ로 전환한다.
> **코드 변경 없이** binder 의존성 + `application-{profile}.yml` 설정만 교체한다.

Spring Cloud Stream은 메시지 브로커를 추상화하는 프레임워크이다.
`@StreamListener`, `Function`, `Consumer`, `Supplier` 인터페이스로 비즈니스 로직을 작성하면,
binder 교체만으로 다른 MQ 제품으로 전환할 수 있다.

### 로컬 → 운영 전환 매핑

| 로컬 개발 (docker-compose) | 운영 Cloud 서비스 | 전환 방법 |
|---------------------------|------------------|----------|
| RabbitMQ | Azure Service Bus | binder → `spring-cloud-azure-stream-binder-servicebus` |
| RabbitMQ | AWS SQS | binder → `spring-cloud-stream-binder-sqs` (커뮤니티) |
| Kafka | Azure Event Hub | binder → `spring-cloud-stream-binder-kafka` + Event Hub Kafka endpoint |
| Kafka | GCP Pub/Sub | binder → `spring-cloud-gcp-pubsub-stream-binder` |
| Kafka | AWS Kinesis | binder → `spring-cloud-stream-binder-kinesis` |

### Cloud MQ별 개요

| 항목 | Azure Service Bus | AWS SQS | GCP Pub/Sub |
|------|------------------|---------|-------------|
| **로컬 개발 대리** | RabbitMQ | RabbitMQ | Kafka |
| **프로비저닝 CLI** | `az servicebus namespace create` | `aws sqs create-queue` | `gcloud pubsub topics create` |
| **인증 환경변수** | `AZURE_SERVICEBUS_CONNECTION_STRING` | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` + `AWS_REGION` | `GCP_PROJECT_ID` + `GOOGLE_APPLICATION_CREDENTIALS` |
| **최소 Tier** | Basic ($0.05/백만 op) | Standard (종량제) | (종량제) |
| **로컬 에뮬레이터** | 없음 | LocalStack (제한적) | Pub/Sub Emulator (제한적) |

### Cloud MQ별 설정 참조

> 상세 binder 설정 및 Gradle 의존성은 단일 출처(Single Source of Truth)로 관리:
> `{NPD_PLUGIN_DIR}/resources/references/java-config-manifest-standard.md` 참조.
> 카테고리 가이드에서는 전환 전략 개념과 간략 매핑만 기술하고, 상세 설정은 위 참조 문서로 위임한다.

### Cloud MQ별 운영 프로비저닝

> Cloud MQ 프로비저닝 절차:
> `{NPD_PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-mq-container.md` 참조.

---

## 기동 확인 명령

| 서비스 | 확인 명령 | 정상 응답 |
|--------|----------|----------|
| RabbitMQ | `docker compose exec rabbitmq rabbitmq-diagnostics -q ping` | 종료 코드 0 |
| RabbitMQ 관리 콘솔 | `http://localhost:15672` (브라우저) | 로그인 화면 |
| Kafka | `docker compose exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list` | 에러 없이 토픽 목록 출력 |

---

## 주의사항

- **자격 증명 통일 규칙**: MQ_USER는 AGENTS.md의 `{ROOT}` 값, MQ_PASSWORD는 `P@ssw0rd$`로 통일한다.
- **MQ 포함 조건 엄수**: dev-plan.md 섹션 10-2에서 MQ 불필요로 판정된 경우 MQ 서비스를 임의로 추가하지 않는다.
- **Cloud MQ 로컬 개발**: Cloud MQ는 docker-compose로 에뮬레이션이 어렵다. 로컬에서는 Self-hosted MQ(RabbitMQ/Kafka)를 대리로 사용하고, Spring Cloud Stream binder 교체로 운영 전환한다.
- **Kafka 이미지**: `bitnami/kafka:3.7`을 사용한다. 최신 stable 버전은 Docker Hub에서 확인한다.
