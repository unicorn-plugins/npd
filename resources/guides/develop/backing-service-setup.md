# 백킹서비스 로컬 구성 가이드

## 목적

개발 환경에서 애플리케이션이 필요로 하는 백킹서비스(DB, Cache, MQ, Mock 서버, AI 서비스)를
프로젝트 루트 단일 `docker-compose.yml`로 구성하고 기동한다.
Docker Compose profiles를 활용하여 선택적 서비스(Mock, AI)를 분리하고,
K8s 환경 분기 시 helm chart 기반 설치를 수행한다.

---

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 개발 계획서 | `docs/develop/dev-plan.md` | 백킹서비스 요구사항 확인 |
| 데이터 설계서 | `docs/design/database/*.md` | DB 종류·스키마명 확인 |
| 캐시 설계서 | `docs/design/database/cache-db-design.md` | Redis 설정 확인 |
| 외부 시퀀스 설계서 | `docs/design/sequence/outer/` | MQ 필요 여부 판별 |
| OpenAPI 명세 | `docs/design/api/*.yaml` | Prism Mock 서버 마운트 대상 |
| AI 서비스 설계서 | `docs/design/ai-service-design.md` | AI 서비스 컨테이너 포함 여부 판별 |

---

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 | 설명 |
|--------|----------|------|
| Docker Compose 파일 | `./docker-compose.yml` | 프로젝트 루트 단일 파일 |
| 환경변수 템플릿 | `./.env.example` | 민감 정보 제외 템플릿 |
| 백킹서비스 결과서 | `docs/develop/backing-service-result.md` | 연결 정보 기록 |

---

## 방법론

### Step 0. 환경 선택

사용자에게 다음을 질문하여 환경을 결정한다.

```
[ASK_USER] 백킹서비스를 어느 환경에 구성하시겠습니까?
  1) docker-compose (로컬 기본, 권장)
  2) minikube (로컬 K8s)
  3) K8s 클러스터 (원격 클러스터)
```

- 응답이 **1**이면 → [Step 1. docker-compose 분기](#step-1-docker-compose-분기) 수행
- 응답이 **2 또는 3**이면 → [Step 2. K8s 분기](#step-2-k8s-분기) 수행

---

### Step 1. docker-compose 분기

#### 1-1. 설계서 분석

아래 항목을 설계서에서 확인하고 결과를 기록한다.

| 확인 항목 | 확인 위치 | 판단 결과 |
|----------|----------|----------|
| DB 종류 및 서비스별 database 명 | `docs/design/database/*.md` | (작성) |
| Cache 사용 여부 및 설정 | `docs/design/database/cache-db-design.md` | (작성) |
| 비동기 MQ 통신 존재 여부 | `docs/design/sequence/outer/` | (작성) |
| OpenAPI yaml 파일 목록 | `docs/design/api/*.yaml` | (작성) |
| AI 서비스 존재 여부 | `docs/design/ai-service-design.md` | (작성) |

#### 1-2. docker-compose.yml 작성

프로젝트 루트에 `docker-compose.yml`을 아래 규칙에 따라 작성한다.

**서비스 구성 규칙**

| 서비스 | 프로파일 | 포함 조건 |
|--------|---------|----------|
| postgres (또는 mysql/mariadb) | 없음 (기본 기동) | DB 설계서 존재 시 항상 포함 |
| redis | 없음 (기본 기동) | 캐시 설계서 존재 시 항상 포함 |
| rabbitmq (또는 kafka) | 없음 (기본 기동) | 외부 시퀀스 설계서에 비동기 통신 명시 시만 포함 |
| prism-mock | `mock` | OpenAPI yaml 파일 존재 시 포함 |
| ai-service | `ai` | AI 서비스 설계서 존재 시 포함 |

**기본 기동 서비스** (프로파일 없음, `docker compose up -d` 시 항상 기동)

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
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

> Kafka를 사용하는 경우 rabbitmq 대신 kafka + zookeeper 조합으로 교체한다.

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

**ai 프로파일** (AI 서비스, `ai-service/Dockerfile` 존재 시)

```yaml
  ai-service:
    profiles: ["ai"]
    build:
      context: ./ai-service
      dockerfile: Dockerfile
    env_file: .env
    ports:
      - "${AI_SERVICE_PORT:-8100}:8000"
    depends_on:
      - postgres
      - redis
```

**volumes 선언**

```yaml
volumes:
  postgres-data:
  redis-data:
  rabbitmq-data:   # MQ 포함 시만 선언
```

#### 1-3. 다중 DB (서비스별 database 분리)

PostgreSQL 단일 인스턴스에 서비스별 database를 분리하는 경우,
초기화 스크립트를 사용한다.

```yaml
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ${DB_NAME}          # 기본 DB (최초 생성)
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d:ro
```

`docker/postgres/init/01-create-databases.sql` 예시:

```sql
-- 서비스별 database 생성 (설계서 기반으로 작성)
CREATE DATABASE order_db;
CREATE DATABASE inventory_db;
CREATE DATABASE user_db;

GRANT ALL PRIVILEGES ON DATABASE order_db TO ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE user_db TO ${DB_USER};
```

> 테이블은 생성하지 않는다. JPA `ddl-auto=update` 또는 Flyway/Liquibase로 자동 생성된다.

#### 1-4. .env.example 작성

`.env.example` 파일을 프로젝트 루트에 생성한다. 실제 값은 공백 또는 예시 값으로 작성한다.

```dotenv
# ===========================
# Database
# ===========================
DB_NAME=app_db
DB_USER=appuser
DB_PASSWORD=
DB_PORT=5432
DB_HOST=localhost

# ===========================
# Redis
# ===========================
REDIS_PORT=6379
REDIS_HOST=localhost

# ===========================
# RabbitMQ (MQ 포함 시)
# ===========================
MQ_USER=mquser
MQ_PASSWORD=
MQ_PORT=5672
MQ_MGMT_PORT=15672
MQ_HOST=localhost
MQ_VHOST=/

# ===========================
# Prism Mock (mock 프로파일)
# ===========================
MOCK_PORT=4010

# ===========================
# AI Service (ai 프로파일)
# ===========================
AI_SERVICE_PORT=8100
```

> `.env.example`을 복사하여 `.env`를 생성하고 실제 값을 채운다.
> `.env`는 `.gitignore`에 반드시 추가한다.

#### 1-5. docker compose 기동

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

**ai 프로파일 포함 기동** (AI 서비스 컨테이너 추가)

```bash
docker compose --profile ai up -d
```

**모든 프로파일 기동**

```bash
docker compose --profile mock --profile ai up -d
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

#### 1-6. 기동 후 연결 확인

| 서비스 | 확인 명령 | 정상 응답 |
|--------|----------|----------|
| PostgreSQL | `docker compose exec postgres pg_isready -U ${DB_USER}` | `/var/run/postgresql:5432 - accepting connections` |
| Redis | `docker compose exec redis redis-cli ping` | `PONG` |
| RabbitMQ | `http://localhost:15672` (브라우저) | 관리 콘솔 접속 |
| Prism Mock | `curl http://localhost:4010/` | HTTP 응답 확인 |
| AI Service | `curl http://localhost:8100/health` | `{"status":"ok"}` 또는 유사 응답 |

---

### Step 2. K8s 분기

minikube 또는 원격 K8s 클러스터에 helm chart로 설치한다.

#### 2-1. 네임스페이스 준비

```bash
kubectl create namespace backing-services
```

#### 2-2. PostgreSQL 설치 (Bitnami)

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install postgres bitnami/postgresql \
  --namespace backing-services \
  --set auth.database=${DB_NAME} \
  --set auth.username=${DB_USER} \
  --set auth.password=${DB_PASSWORD} \
  --set primary.service.type=LoadBalancer
```

#### 2-3. Redis 설치 (Bitnami)

```bash
helm install redis bitnami/redis \
  --namespace backing-services \
  --set auth.enabled=false \
  --set master.service.type=LoadBalancer \
  --set architecture=standalone
```

#### 2-4. RabbitMQ 설치 (설계서에 MQ 명시 시만)

```bash
helm install rabbitmq bitnami/rabbitmq \
  --namespace backing-services \
  --set auth.username=${MQ_USER} \
  --set auth.password=${MQ_PASSWORD} \
  --set service.type=LoadBalancer
```

#### 2-5. 연결 주소 확인 (LoadBalancer)

```bash
kubectl get svc -n backing-services
```

> minikube 환경에서는 `minikube tunnel`을 별도 터미널에서 실행한 후 EXTERNAL-IP를 확인한다.

```bash
# minikube 전용
minikube tunnel
```

#### 2-6. K8s 환경에서의 Prism Mock

K8s 환경에서 Prism Mock이 필요한 경우 별도 Deployment와 Service를 배포한다.

```yaml
# k8s/prism-mock.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prism-mock
  namespace: backing-services
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prism-mock
  template:
    metadata:
      labels:
        app: prism-mock
    spec:
      containers:
        - name: prism
          image: stoplight/prism:latest
          args: ["mock", "-h", "0.0.0.0", "/api/merged-api.yaml"]
          ports:
            - containerPort: 4010
          volumeMounts:
            - name: api-spec
              mountPath: /api
      volumes:
        - name: api-spec
          configMap:
            name: api-spec-cm
---
apiVersion: v1
kind: Service
metadata:
  name: prism-mock
  namespace: backing-services
spec:
  type: LoadBalancer
  selector:
    app: prism-mock
  ports:
    - port: 4010
      targetPort: 4010
```

```bash
# OpenAPI yaml을 ConfigMap으로 생성
kubectl create configmap api-spec-cm \
  --from-file=merged-api.yaml=docs/design/api/merged-api.yaml \
  -n backing-services

kubectl apply -f k8s/prism-mock.yaml
```

---

### Step 3. 설치 결과서 작성

설치 완료 후 `docs/develop/backing-service-result.md`를 작성한다.

작성 항목:

- 구성 환경 (docker-compose / minikube / K8s)
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
# ai  프로파일: docker compose --profile ai up -d

services:

  # -------------------------------------------------------
  # 기본 서비스 (항상 기동)
  # -------------------------------------------------------
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ${DB_NAME}
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

  # MQ는 외부 시퀀스 설계서에 비동기 통신이 명시된 경우에만 포함
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

  # -------------------------------------------------------
  # ai 프로파일: AI 서비스 컨테이너
  # 기동: docker compose --profile ai up -d
  # ai-service-env-setup.md와 연계하여 구성
  # -------------------------------------------------------
  ai-service:
    profiles: ["ai"]
    build:
      context: ./ai-service
      dockerfile: Dockerfile
    env_file: .env
    ports:
      - "${AI_SERVICE_PORT:-8100}:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres-data:
  redis-data:
  # rabbitmq-data:   # MQ 포함 시만 선언
```

### backing-service-result.md 작성 예시

```markdown
# 백킹서비스 설치 결과서

## 구성 환경
- 환경: docker-compose
- 기동 일시: YYYY-MM-DD
- 활성화 프로파일: (기본) / mock / ai

## 서비스 연결 정보

### PostgreSQL
| 항목 | 값 |
|------|---|
| Host | localhost |
| Port | 5432 |
| Database | app_db (기본), order_db, inventory_db ... |
| User | appuser |
| JDBC URL | jdbc:postgresql://localhost:5432/{db_name} |

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
| User | mquser |

### Prism Mock (mock 프로파일)
| 항목 | 값 |
|------|---|
| Base URL | http://localhost:4010 |
| OpenAPI 명세 | docs/design/api/*.yaml |

### AI Service (ai 프로파일)
| 항목 | 값 |
|------|---|
| Base URL | http://localhost:8100 |

## 기동 명령어

\`\`\`bash
docker compose up -d                              # 기본 서비스
docker compose --profile mock up -d              # + Mock 서버
docker compose --profile ai up -d               # + AI 서비스
docker compose --profile mock --profile ai up -d # 전체
\`\`\`

## 연결 확인 결과
- [ ] PostgreSQL: pg_isready 정상
- [ ] Redis: PONG 확인
- [ ] RabbitMQ: 관리 콘솔 접속 (해당 시)
- [ ] Prism Mock: HTTP 응답 확인 (mock 프로파일 시)
- [ ] AI Service: /health 응답 확인 (ai 프로파일 시)
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

- **테이블 생성 금지**: 데이터베이스(스키마)만 생성하고 테이블은 생성하지 않는다.
  애플리케이션의 JPA `ddl-auto=update` 또는 마이그레이션 도구(Flyway/Liquibase)로 자동 생성된다.
- **포트 충돌 방지**: 기본 포트(5432, 6379, 5672, 4010)가 로컬에서 이미 사용 중인 경우
  `.env`에서 포트를 변경한다. (예: `DB_PORT=15432`)
- **Prism Mock 파일 마운트**: `docs/design/api/` 디렉토리 전체를 읽기 전용으로 마운트한다.
  yaml 파일이 여러 개인 경우 단일 파일로 머지하거나 `command`에 파일명을 명시한다.
- **AI 서비스 연계**: AI 서비스 컨테이너(`ai` 프로파일)는 `ai-service-env-setup.md`의
  환경 구성 절차와 연계하여 진행한다. `ai-service/Dockerfile`이 존재해야 빌드 가능하다.
- **MQ 포함 조건 엄수**: 외부 시퀀스 설계서에 비동기 메시지 흐름이 명시되지 않은 경우
  MQ 서비스를 임의로 추가하지 않는다.
- **볼륨 초기화**: 데이터를 완전히 초기화하려면 `docker compose down -v`로 볼륨을 함께 삭제한다.
- **K8s 환경 데이터 영속성**: minikube 재시작 후 PVC 데이터가 유실될 수 있으므로
  개발 데이터는 별도로 백업한다.
- **gitignore 필수 등록**: `.env` 파일은 반드시 `.gitignore`에 추가한다.
  `.env.example`만 형상 관리한다.
