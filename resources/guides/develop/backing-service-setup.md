# 백킹서비스 로컬 구성 가이드

## 목적

개발 환경에서 애플리케이션이 필요로 하는 백킹서비스(DB, Cache, MQ, Mock 서버)를
프로젝트 루트 단일 `docker-compose.yml`로 구성하고 기동한다.
Docker Compose profiles를 활용하여 선택적 서비스(Mock)를 분리한다.
원격/클라우드 환경 전환은 application.yml 설정 변경으로 대응한다.

---

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 개발 계획서 | `docs/develop/dev-plan.md` | 백킹서비스 요구사항 확인 |
| 데이터 설계서 | `docs/design/database/*.md` | DB 종류·스키마명 확인 |
| 캐시 설계서 | `docs/design/database/cache-db-design.md` | Redis 설정 확인 |
| 외부 시퀀스 설계서 | `docs/design/sequence/outer/` | MQ 필요 여부 판별 |
| OpenAPI 명세 | `docs/design/api/*.yaml` | Prism Mock 서버 마운트 대상 |

---

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 | 설명 |
|--------|----------|------|
| Docker Compose 파일 | `./docker-compose.yml` | 프로젝트 루트 단일 파일 |
| 환경변수 템플릿 | `./.env.example` | 민감 정보 제외 템플릿 |
| 백킹서비스 결과서 | `docs/develop/backing-service-result.md` | 연결 정보 기록 |

---

## 방법론

### Step 1. 설계서 분석

아래 항목을 설계서에서 확인하고 결과를 기록한다.

| 확인 항목 | 확인 위치 | 판단 결과 |
|----------|----------|----------|
| DB 종류 및 서비스별 database 명 | `docs/design/database/*.md` | (작성) |
| Cache 사용 여부 및 설정 | `docs/design/database/cache-db-design.md` | (작성) |
| 비동기 MQ 통신 존재 여부 | `docs/design/sequence/outer/` | (작성) |
| OpenAPI yaml 파일 목록 | `docs/design/api/*.yaml` | (작성) |

### Step 2. docker-compose.yml 작성

프로젝트 루트에 `docker-compose.yml`을 아래 규칙에 따라 작성한다.

**서비스 구성 규칙**

| 서비스 | 프로파일 | 포함 조건 |
|--------|---------|----------|
| postgres (또는 mysql/mariadb) | 없음 (기본 기동) | DB 설계서 존재 시 항상 포함 |
| redis | 없음 (기본 기동) | 캐시 설계서 존재 시 항상 포함 |
| rabbitmq (또는 kafka) | 없음 (기본 기동) | 외부 시퀀스 설계서에 비동기 통신 명시 시만 포함 |
| prism-mock | `mock` | OpenAPI yaml 파일 존재 시 포함 |

**기본 기동 서비스** (프로파일 없음, `docker compose up -d` 시 항상 기동)

> **DB 구성 원칙**: PostgreSQL 단일 인스턴스에 서비스별 database를 분리한다. 초기화 스크립트(`docker/postgres/init/`)로 서비스별 database를 자동 생성한다.

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

**MQ 서비스** (외부 시퀀스 설계서에 비동기 통신이 명시된 경우만 추가)

```yaml
  # 비동기 통신이 설계서에 명시된 경우에만 포함
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

Kafka를 사용하는 경우 rabbitmq 대신 아래 kafka 구성으로 교체한다.

```yaml
  # Kafka (비동기 통신이 Kafka로 설계된 경우)
  kafka:
    image: bitnamilegacy/kafka:3.7
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

> Kafka는 KRaft 모드(Zookeeper 없음)로 구성한다. `volumes`에 `kafka-data:`를 추가 선언한다.

**mock 프로파일** (Prism Mock 서버)

```yaml
  prism-mock:
    image: stoplight/prism:latest
    profiles: ["mock"]
    command: mock -h 0.0.0.0 /api/merged-api.yaml
    volumes:
      - ./docs/design/api:/api:ro
    ports:
      - "${MOCK_PORT:-4010}:4010"
```

> OpenAPI yaml 파일이 여러 개인 경우 하나로 머지하거나 개별 파일명을 지정한다.
> 단일 서비스 yaml이라면 `command`의 파일명을 해당 yaml로 지정한다.
> 예: `command: mock -h 0.0.0.0 /api/order-api.yaml`

**volumes 선언**

```yaml
volumes:
  postgres-data:
  redis-data:
  rabbitmq-data:   # RabbitMQ 포함 시만 선언
  kafka-data:      # Kafka 포함 시만 선언
```

### Step 3. 다중 DB (서비스별 database 분리)

PostgreSQL 단일 인스턴스에 서비스별 database를 분리하는 경우,
초기화 스크립트를 사용한다.

```yaml
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d:ro
```

> `POSTGRES_DB`를 생략하면 `POSTGRES_USER` 값과 동일한 이름의 기본 DB가 생성된다.
> 서비스별 database는 아래 init 스크립트로 생성한다.

`docker/postgres/init/01-create-databases.sql` 예시:

```sql
-- 서비스별 database 생성 (설계서 기반으로 작성)
-- database명은 서비스명과 동일 (_db 접미사 없음)
CREATE DATABASE order;
CREATE DATABASE inventory;
CREATE DATABASE "user";  -- 예약어인 경우 큰따옴표 사용

-- DB_USER는 CLAUDE.md의 ROOT 값 사용
GRANT ALL PRIVILEGES ON DATABASE order TO {ROOT};
GRANT ALL PRIVILEGES ON DATABASE inventory TO {ROOT};
GRANT ALL PRIVILEGES ON DATABASE "user" TO {ROOT};
```

> **네이밍 규칙**: database명은 서비스명과 동일하게 사용하며 `_db` 접미사를 붙이지 않는다.
> DB_USER는 CLAUDE.md의 `{ROOT}` 값, DB_PASSWORD는 `P@ssw0rd$`를 사용한다.
> 테이블은 생성하지 않는다. JPA `ddl-auto=update` 또는 Flyway/Liquibase로 자동 생성된다.

### Step 4. .env.example 작성

`.env.example` 파일을 프로젝트 루트에 생성한다. 실제 값은 공백 또는 예시 값으로 작성한다.

```dotenv
# ===========================
# Database (CLAUDE.md의 ROOT 값 참조)
# 서비스별 DB는 docker/postgres/init/ 스크립트로 자동 생성
# ===========================
DB_USER={ROOT}
DB_PASSWORD=P@ssw0rd$
DB_PORT=5432
DB_HOST=localhost

# ===========================
# Redis
# ===========================
REDIS_PORT=6379
REDIS_HOST=localhost

# ===========================
# RabbitMQ (MQ 포함 시, CLAUDE.md의 ROOT 값 참조)
# ===========================
MQ_USER={ROOT}
MQ_PASSWORD=P@ssw0rd$
MQ_PORT=5672
MQ_MGMT_PORT=15672
MQ_HOST=localhost
MQ_VHOST=/

# ===========================
# Kafka (Kafka 사용 시, RabbitMQ 대신)
# ===========================
# KAFKA_PORT=9094

# ===========================
# Prism Mock (mock 프로파일)
# ===========================
MOCK_PORT=4010

```

> `.env.example`을 복사하여 `.env`를 생성하고 실제 값을 채운다.
> `.env`는 `.gitignore`에 반드시 추가한다.

### Step 5. docker compose 기동

**.env 준비**

```bash
cp .env.example .env
# .env 파일을 열어 실제 값 입력
```

**기본 서비스만 기동** (DB, Cache, 필요 시 MQ)

```bash
docker compose up -d
```

**mock 프로파일 포함 기동** (Prism Mock 서버 추가)

```bash
docker compose --profile mock up -d
```

**상태 확인**

```bash
docker compose ps
docker compose logs -f
```

**서비스 중지**

```bash
docker compose down
# 볼륨까지 삭제하려면
docker compose down -v
```

### Step 6. 기동 후 연결 확인

| 서비스 | 확인 명령 | 정상 응답 |
|--------|----------|----------|
| PostgreSQL | `docker compose exec postgres pg_isready -U ${DB_USER}` | `/var/run/postgresql:5432 - accepting connections` |
| Redis | `docker compose exec redis redis-cli ping` | `PONG` |
| RabbitMQ | `http://localhost:15672` (브라우저) | 관리 콘솔 접속 |
| Prism Mock | `curl http://localhost:4010/` | HTTP 응답 확인 |

### Step 7. 설치 결과서 작성

설치 완료 후 `docs/develop/backing-service-result.md`를 작성한다.

작성 항목:

- 구성 환경 (docker-compose)
- 각 서비스 연결 정보 (host, port, 계정, database명)
- 활성화된 프로파일
- 기동 명령어
- 연결 확인 결과

---

## 출력 형식

### docker-compose.yml 전체 예시 구조

```yaml
# docker-compose.yml
# 프로젝트 루트에 위치. 기본 서비스는 프로파일 없이 항상 기동.
# mock 프로파일: docker compose --profile mock up -d

services:

  # -------------------------------------------------------
  # 기본 서비스 (항상 기동)
  # -------------------------------------------------------
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d:ro   # 서비스별 DB 자동 생성
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MQ는 외부 시퀀스 설계서에 비동기 통신이 명시된 경우에만 포함
  # --- RabbitMQ 사용 시 ---
  # rabbitmq:
  #   image: rabbitmq:3-management
  #   environment:
  #     RABBITMQ_DEFAULT_USER: ${MQ_USER}
  #     RABBITMQ_DEFAULT_PASS: ${MQ_PASSWORD}
  #     RABBITMQ_DEFAULT_VHOST: ${MQ_VHOST:-/}
  #   ports:
  #     - "${MQ_PORT:-5672}:5672"
  #     - "${MQ_MGMT_PORT:-15672}:15672"
  #   volumes:
  #     - rabbitmq-data:/var/lib/rabbitmq
  #   healthcheck:
  #     test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
  #     interval: 15s
  #     timeout: 10s
  #     retries: 5

  # --- Kafka 사용 시 (KRaft 모드, Zookeeper 불필요) ---
  # kafka:
  #   image: bitnamilegacy/kafka:3.7
  #   environment:
  #     KAFKA_CFG_NODE_ID: 1
  #     KAFKA_CFG_PROCESS_ROLES: broker,controller
  #     KAFKA_CFG_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
  #     KAFKA_CFG_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093,EXTERNAL://:9094
  #     KAFKA_CFG_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,EXTERNAL://localhost:${KAFKA_PORT:-9094}
  #     KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,EXTERNAL:PLAINTEXT
  #     KAFKA_CFG_CONTROLLER_LISTENER_NAMES: CONTROLLER
  #     KAFKA_CFG_INTER_BROKER_LISTENER_NAME: PLAINTEXT
  #     ALLOW_PLAINTEXT_LISTENER: "yes"
  #   ports:
  #     - "${KAFKA_PORT:-9094}:9094"
  #   volumes:
  #     - kafka-data:/bitnami/kafka
  #   healthcheck:
  #     test: ["CMD-SHELL", "kafka-topics.sh --bootstrap-server localhost:9092 --list"]
  #     interval: 15s
  #     timeout: 10s
  #     retries: 5

  # -------------------------------------------------------
  # mock 프로파일: Prism Mock 서버
  # 기동: docker compose --profile mock up -d
  # -------------------------------------------------------
  prism-mock:
    image: stoplight/prism:latest
    profiles: ["mock"]
    command: mock -h 0.0.0.0 /api/merged-api.yaml
    volumes:
      - ./docs/design/api:/api:ro
    ports:
      - "${MOCK_PORT:-4010}:4010"

volumes:
  postgres-data:
  redis-data:
  # rabbitmq-data:   # RabbitMQ 포함 시만 선언
  # kafka-data:      # Kafka 포함 시만 선언
```

### backing-service-result.md 작성 예시

```markdown
# 백킹서비스 설치 결과서

## 구성 환경
- 환경: docker-compose (로컬 개발)
- 기동 일시: YYYY-MM-DD
- 활성화 프로파일: (기본) / mock

## 서비스 연결 정보

### PostgreSQL
| 항목 | 값 |
|------|---|
| Host | localhost |
| Port | 5432 |
| Database | 서비스별 database (init 스크립트로 자동 생성, _db 접미사 없음) |
| User | {ROOT} (CLAUDE.md 참조) |
| Password | P@ssw0rd$ |
| JDBC URL | jdbc:postgresql://localhost:5432/{서비스명} |

### Redis
| 항목 | 값 |
|------|---|
| Host | localhost |
| Port | 6379 |
| Connection | redis://localhost:6379 |

### RabbitMQ (해당 시)
| 항목 | 값 |
|------|---|
| Host | localhost |
| AMQP Port | 5672 |
| Management UI | http://localhost:15672 |
| User | {ROOT} (CLAUDE.md 참조) |
| Password | P@ssw0rd$ |

### Prism Mock (mock 프로파일)
| 항목 | 값 |
|------|---|
| Base URL | http://localhost:4010 |
| OpenAPI 명세 | docs/design/api/*.yaml |

## 기동 명령어

\`\`\`bash
docker compose up -d                         # 기본 서비스
docker compose --profile mock up -d          # + Mock 서버
\`\`\`

## 연결 확인 결과
- [ ] PostgreSQL: pg_isready 정상
- [ ] Redis: PONG 확인
- [ ] RabbitMQ: 관리 콘솔 접속 (해당 시)
- [ ] Prism Mock: HTTP 응답 확인 (mock 프로파일 시)
```

---

## 품질 기준

- [ ] 모든 설정값이 환경변수(`${VAR}`)로 처리됨
- [ ] 민감 정보(비밀번호, 토큰)가 docker-compose.yml에 하드코딩되지 않음
- [ ] `.env.example`이 작성되고 `.env`가 `.gitignore`에 등록됨
- [ ] 서비스별 database가 분리 구성됨 (단일 PostgreSQL 인스턴스, 다중 database)
- [ ] MQ 서비스는 외부 시퀀스 설계서에 비동기 통신이 명시된 경우에만 포함됨
- [ ] `docker compose ps`로 모든 기본 서비스가 `healthy` 상태임
- [ ] Prism Mock 서버가 OpenAPI yaml 기반으로 정상 응답을 반환함
- [ ] `docs/develop/backing-service-result.md`가 작성됨

---

## 주의사항

- **자격 증명 통일 규칙**:
  - DB_USER / MQ_USER: CLAUDE.md의 `{ROOT}` 값을 사용한다.
  - DB_PASSWORD / MQ_PASSWORD: `P@ssw0rd$`로 통일한다.
  - database명: 서비스명과 동일하게 사용하며 `_db` 접미사를 붙이지 않는다. init 스크립트로 생성한다.
- **테이블 생성 금지**: 데이터베이스(스키마)만 생성하고 테이블은 생성하지 않는다.
  애플리케이션의 JPA `ddl-auto=update` 또는 마이그레이션 도구(Flyway/Liquibase)로 자동 생성된다.
- **포트 충돌 방지**: 기본 포트(5432, 6379, 5672, 4010)가 로컬에서 이미 사용 중인 경우
  `.env`에서 포트를 변경한다. (예: `DB_PORT=15432`)
- **Prism Mock 파일 마운트**: `docs/design/api/` 디렉토리 전체를 읽기 전용으로 마운트한다.
  yaml 파일이 여러 개인 경우 단일 파일로 머지하거나 `command`에 파일명을 명시한다.
- **MQ 포함 조건 엄수**: 외부 시퀀스 설계서에 비동기 메시지 흐름이 명시되지 않은 경우
  MQ 서비스를 임의로 추가하지 않는다.
- **볼륨 초기화**: 데이터를 완전히 초기화하려면 `docker compose down -v`로 볼륨을 함께 삭제한다.
- **gitignore 필수 등록**: `.env` 파일은 반드시 `.gitignore`에 추가한다.
  `.env.example`만 형상 관리한다.
