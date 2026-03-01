# MQ 카테고리 가이드 — 배포 환경

## 목적

Self-hosted MQ 배포 healthcheck 및 Cloud Managed MQ 프로비저닝 가이드를 제공한다.
이 가이드는 `backing-service-container.md`의 보조 가이드이다.

---

## Part 1: Self-hosted MQ (VM docker-compose)

### Healthcheck 비교 테이블

| 확인 항목 | RabbitMQ | Kafka |
|-----------|----------|-------|
| **기동 확인 명령** | `docker compose exec rabbitmq rabbitmq-diagnostics -q ping` | `docker compose exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list` |
| **정상 응답** | 종료 코드 0 | 에러 없이 토픽 목록 출력 |
| **관리 콘솔** | `curl -u ${MQ_USER}:${MQ_PASSWORD} http://localhost:15672/api/healthchecks/node` → `{"status":"ok"}` | (없음) |
| **기본 포트** | 5672 (AMQP), 15672 (관리) | 9094 (EXTERNAL) |

### Docker 네트워크 호스트명

| MQ | docker-compose 서비스명 | 앱 컨테이너 호스트 |
|----|----------------------|------------------|
| RabbitMQ | `rabbitmq` | `rabbitmq` |
| Kafka | `kafka` | `kafka` |

### 결과 보고서 템플릿

#### RabbitMQ

```markdown
### RabbitMQ
| 항목 | 값 |
|------|---|
| Host (VM 내부) | localhost |
| Host (외부 접근) | {VM.IP} |
| AMQP Port | 5672 |
| Management UI | http://{VM.IP}:15672 |
| User | {ROOT} |
| Password | P@ssw0rd$ |
```

#### Kafka

```markdown
### Kafka
| 항목 | 값 |
|------|---|
| Bootstrap (VM 내부) | localhost:9094 |
| Bootstrap (docker 네트워크) | kafka:9092 |
| Bootstrap (외부 접근) | {VM.IP}:9094 |
```

### 트러블슈팅 (Self-hosted MQ)

| 증상 | 원인 | 해결 |
|------|------|------|
| RabbitMQ 관리 콘솔 접근 불가 | 포트 미오픈 또는 서비스 미기동 | VM 방화벽 규칙에 15672 포트 허용 확인 |
| Kafka `Connection refused` | 리스너 설정 오류 | `KAFKA_CFG_ADVERTISED_LISTENERS`의 EXTERNAL 주소 확인 |
| Kafka `TopicExistsException` | 토픽 중복 생성 | 기존 토픽 확인 후 중복 제거 |

---

## Part 2: Cloud Managed MQ 프로비저닝

### 프로비저닝 비교 테이블

| 항목 | Azure Service Bus | AWS SQS/SNS | GCP Pub/Sub |
|------|------------------|-------------|-------------|
| **프로비저닝 CLI** | `az servicebus namespace create` | `aws sqs create-queue` | `gcloud pubsub topics create` |
| **최소 Tier** | Basic ($0.05/백만 op) | Standard (종량제) | (종량제) |
| **인증 환경변수** | `AZURE_SERVICEBUS_CONNECTION_STRING` | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` + `AWS_REGION` | `GCP_PROJECT_ID` + `GOOGLE_APPLICATION_CREDENTIALS` |
| **Spring binder** | `spring-cloud-azure-stream-binder-servicebus` | `spring-cloud-stream-binder-sqs` | `spring-cloud-gcp-pubsub-stream-binder` |

### Azure Service Bus 프로비저닝 절차

```bash
# 1. 리소스 그룹 생성 (없는 경우)
az group create --name {ROOT}-rg --location koreacentral

# 2. Service Bus 네임스페이스 생성
az servicebus namespace create \
  --name {ROOT}-sb \
  --resource-group {ROOT}-rg \
  --location koreacentral \
  --sku Basic

# 3. 큐 생성 (서비스별)
az servicebus queue create \
  --name order-queue \
  --namespace-name {ROOT}-sb \
  --resource-group {ROOT}-rg

# 4. 연결 문자열 확인
az servicebus namespace authorization-rule keys list \
  --name RootManageSharedAccessKey \
  --namespace-name {ROOT}-sb \
  --resource-group {ROOT}-rg \
  --query primaryConnectionString -o tsv
```

### AWS SQS 프로비저닝 절차

```bash
# 1. SQS 큐 생성
aws sqs create-queue \
  --queue-name {ROOT}-order-queue \
  --region ap-northeast-2

# 2. SNS 토픽 생성 (Pub/Sub 패턴 시)
aws sns create-topic \
  --name {ROOT}-order-topic \
  --region ap-northeast-2

# 3. SNS → SQS 구독 설정
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-northeast-2:{ACCOUNT_ID}:{ROOT}-order-topic \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:ap-northeast-2:{ACCOUNT_ID}:{ROOT}-order-queue

# 4. 큐 URL 확인
aws sqs get-queue-url \
  --queue-name {ROOT}-order-queue \
  --region ap-northeast-2
```

### GCP Pub/Sub 프로비저닝 절차

```bash
# 1. 토픽 생성
gcloud pubsub topics create {ROOT}-order-topic \
  --project={GCP_PROJECT_ID}

# 2. 구독 생성
gcloud pubsub subscriptions create {ROOT}-order-sub \
  --topic={ROOT}-order-topic \
  --project={GCP_PROJECT_ID}

# 3. 서비스 계정 키 생성 (앱용)
gcloud iam service-accounts keys create credentials.json \
  --iam-account={ROOT}-app@{GCP_PROJECT_ID}.iam.gserviceaccount.com

# 4. 토픽 목록 확인
gcloud pubsub topics list --project={GCP_PROJECT_ID}
```

### .env 추가 변수 (Cloud MQ)

Cloud MQ 사용 시 `.env`에 아래 변수를 추가한다.

**Azure Service Bus:**
```dotenv
AZURE_SERVICEBUS_CONNECTION_STRING=Endpoint=sb://{ROOT}-sb.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=...
```

**AWS SQS:**
```dotenv
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-northeast-2
```

**GCP Pub/Sub:**
```dotenv
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### 상세 설정 참조

> 상세 binder 설정 및 Gradle 의존성은 단일 출처(Single Source of Truth)로 관리:
> `{PLUGIN_DIR}/resources/references/java-config-manifest-standard.md` 참조.

> MQ 설치 계획서 샘플:
> `{PLUGIN_DIR}/resources/samples/sample-MQ설치계획서.md` 참조.

---

## 주의사항

- Self-hosted MQ는 공개 Docker 이미지를 사용하므로 컨테이너 레지스트리 인증이 불필요하다.
- Cloud MQ 프로비저닝은 해당 Cloud CLI가 설치되고 인증된 상태에서 수행한다.
- Cloud MQ 연결 문자열/키는 민감 정보이므로 `.env`에만 저장하고 git에 커밋하지 않는다.
- Self-hosted MQ에서 Cloud MQ로 전환 시 코드 변경 없이 binder 의존성과 application-{profile}.yml 설정만 교체한다. 상세는 `java-config-manifest-standard.md` 참조.
