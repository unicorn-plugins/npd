# VM 백킹서비스 배포 가이드

## 목적

VM에서 애플리케이션이 의존하는 백킹서비스(DB, Redis, MQ)를 docker-compose로 기동한다.
실제 기동까지 수행하며, 결과를 보고서에 기록한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| Docker Compose 파일 | `./docker-compose.yml` | VM에서 백킹서비스 기동 |
| 환경변수 템플릿 | `./.env.example` | `.env` 생성 원본 |
| DB 초기화 스크립트 | `docker/{db-product}/init/*` | 서비스별 DB 자동 생성 (PostgreSQL: `.sql`, MongoDB: `.js`) |
| 개발 환경 백킹서비스 결과서 | `docs/develop/backing-service-result.md` | 연결 정보 참조 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 백킹서비스 배포 결과서 | `docs/deploy/backing-service-result.md` |

## 방법론

### 실행정보 확인

프롬프트의 `[실행정보]` 섹션에서 아래 VM 접속 정보를 확인한다.

| 항목 | 설명 |
|------|------|
| {VM.HOST} | VM SSH Host alias (~/.ssh/config에 등록된 이름) |
| {VM.IP} | VM IP 주소 |
| {VM.USERID} | VM 접속 OS 유저명 |
| {VM.KEY파일} | VM 접속 Private Key 파일 경로 |

> **레지스트리 인증 불필요**: 백킹서비스는 공개 Docker 이미지(postgres, redis, rabbitmq 등)를 사용하므로
> `[실행정보]`의 레지스트리 관련 변수(REGISTRY_URL, IMG_ID 등)는 이 가이드에서 사용하지 않는다.

### VM 접속

Step 1(배포 사전 준비)에서 `~/.ssh/config`가 설정된 경우 Host alias로 간편하게 접속한다.

**방법 1: Host alias 사용 (권장)**
```
ssh {VM.HOST}
```

**방법 2: Key 직접 지정 (Host alias 미설정 시 fallback)**
```
chmod 400 {VM.KEY파일}
ssh -i {VM.KEY파일} {VM.USERID}@{VM.IP}
```

### Git Clone/Pull

VM에서 프로젝트 소스를 준비한다.

**최초 clone (프로젝트가 없는 경우)**
```
mkdir -p ~/workspace
cd ~/workspace
git clone {원격 Git Repository 주소}
cd {ROOT}
```

**이후 pull (프로젝트가 이미 있는 경우)**
```
cd ~/workspace/{ROOT}
git pull
```

### .env 준비

`.env.example`을 복사하여 `.env`를 생성하고, VM 환경에 맞게 값을 조정한다.

```
cp .env.example .env
```

> **왜 복사가 필요한가?** Git에는 `.env.example`(템플릿)만 추적하고, `.env`는 `.gitignore`에 등록되어 있다.
> `docker compose`는 `.env` 파일만 자동 인식하므로(`.env.example`은 읽지 않음), VM에 `git clone` 직후에는 `.env`가 없어 복사가 필요하다.

**조정 항목 확인**:

| 항목 | 기본값 | VM 환경 조정 |
|------|--------|-------------|
| DB_HOST | localhost | docker-compose에서 미참조. VM 네이티브 프로세스용 참고값 |
| REDIS_HOST | localhost | docker-compose에서 미참조. VM 네이티브 프로세스용 참고값 |
| MQ_HOST | localhost | docker-compose에서 미참조. VM 네이티브 프로세스용 참고값 |
| DB_PORT | 5432 | VM에서 포트 충돌 시 변경 (예: 15432) |
| REDIS_PORT | 6379 | VM에서 포트 충돌 시 변경 |

> **컨테이너 앱의 접속 호스트**: `DB_HOST`, `REDIS_HOST`, `MQ_HOST`는 `docker-compose.yml`에서 참조하지 않는다.
> Step 3-1에서 `docker run`으로 실행하는 앱 컨테이너는 `localhost`로 백킹서비스에 접근할 수 없다(컨테이너 내부의 `localhost`는 자기 자신).
> 앱 컨테이너는 docker-compose 네트워크에 참여(`--network`)하고, 서비스명(`postgres`, `redis` 등)을 호스트로 사용해야 한다.
> 자세한 내용은 아래 "Docker 네트워크 확인" 섹션 참조.

> `.env`에 `MOCK_PORT` 관련 설정이 있어도 mock 프로파일을 사용하지 않으므로 무시된다.

### docker compose 사전 검증

```
docker compose version
```

미설치 시:
```
sudo apt-get install -y docker-compose-plugin
```

### docker compose up (mock 제외)

기본 서비스만 기동한다.

```
docker compose up -d
```

> **명시적 금지**: `--profile mock` 사용 금지. deploy 환경에서 Prism Mock 서버는 불필요하다.

상태 확인:
```
docker compose ps
```

모든 서비스의 STATUS가 `healthy` 또는 `Up`인지 확인한다.

### Docker 네트워크 확인

`docker compose up -d` 실행 시 `{ROOT}_default` 네트워크가 자동 생성된다.

```
docker network ls | grep default
```

이 네트워크는 Step 3-1에서 앱 컨테이너가 백킹서비스에 접근할 때 사용된다.

> **중요**: `docker run`으로 실행되는 앱 컨테이너는 독립 네트워크에서 실행되므로 `localhost`로 백킹서비스에 접근할 수 없다.
> `--network {ROOT}_default` 옵션으로 docker-compose 네트워크에 참여시키고,
> docker-compose 서비스명(`postgres`, `redis`, `rabbitmq` 등)을 호스트명으로 사용해야 한다.

| 접근 주체 | DB_HOST | REDIS_HOST | 비고 |
|-----------|---------|------------|------|
| VM 네이티브 프로세스 | localhost | localhost | 포트 매핑으로 접근 |
| docker run 앱 컨테이너 | postgres | redis | `--network {ROOT}_default` 필수 |
| 외부 (개발 PC 등) | {VM.IP} | {VM.IP} | VM 방화벽 허용 필요 |

### Health Check

서비스별 정상 동작을 확인한다.

| 서비스 | 확인 명령 | 정상 응답 |
|--------|----------|----------|
| PostgreSQL | `docker compose exec postgres pg_isready -U ${DB_USER}` | `accepting connections` |
| Redis | `docker compose exec redis redis-cli ping` | `PONG` |
| RabbitMQ (해당 시) | `curl -u ${MQ_USER}:${MQ_PASSWORD} http://localhost:15672/api/healthchecks/node` | `{"status":"ok"}` |
| Kafka (해당 시) | `docker compose exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list` | 에러 없이 토픽 목록 출력 |

> **MySQL/MariaDB healthcheck**: `{PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-rdb-container.md` 참조
> **MongoDB healthcheck**: `{PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-nosql-container.md` 참조
> **Cloud MQ 프로비저닝**: `{PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-mq-container.md` 참조

**서비스별 database 확인** (PostgreSQL):
```
docker compose exec postgres psql -U ${DB_USER} -l
```
init 스크립트로 생성된 서비스별 database가 목록에 존재하는지 확인한다.

> **대안 DB 사용 시**: MySQL/MariaDB/MongoDB의 database 확인 명령은 해당 카테고리 가이드 참조.
> - RDB: `{PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-rdb-container.md`
> - NoSQL: `{PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-nosql-container.md`

### 재구성 절차

백킹서비스는 일반적으로 한번 기동 후 지속 운영한다. 재구성이 필요한 경우 아래를 따른다.

- **`.env` 변경 시** (포트, 비밀번호 등 수정):
  ```
  docker compose down
  docker compose up -d
  ```

- **`docker-compose.yml` 변경 시** (`git pull`로 업데이트 반영 후):
  ```
  docker compose down
  docker compose up -d
  ```

- **데이터 초기화가 필요한 경우** (볼륨 삭제 주의):
  ```
  docker compose down -v
  docker compose up -d
  ```

### 결과 보고서 작성

Health Check 완료 후 `docs/deploy/backing-service-result.md`를 작성한다.
선택된 제품에 맞게 연결 정보를 작성한다. 제품별 보고서 템플릿은 해당 카테고리 가이드 참조:
- RDB (MySQL/MariaDB): `{PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-rdb-container.md`
- NoSQL (MongoDB): `{PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-nosql-container.md`
- MQ (Cloud MQ): `{PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-mq-container.md`

## 출력 형식

`docs/deploy/backing-service-result.md` 결과 보고서 템플릿:

```markdown
# 백킹서비스 배포 결과서

## 구성 환경
- 환경: docker-compose (VM 배포)
- VM: {VM.HOST} ({VM.IP})
- 기동 일시: YYYY-MM-DD

## VM 접속 방법
```
ssh {VM.HOST}
```

## 서비스 연결 정보

### PostgreSQL
| 항목 | 값 |
|------|---|
| Host (VM 내부) | localhost |
| Host (외부 접근) | {VM.IP} |
| Port | 5432 |
| Database | 서비스별 database (init 스크립트로 자동 생성) |
| User | {ROOT} |
| Password | P@ssw0rd$ |
| JDBC URL (VM 내부) | jdbc:postgresql://localhost:5432/{서비스명} |
| JDBC URL (외부 접근) | jdbc:postgresql://{VM.IP}:5432/{서비스명} |

### Redis
| 항목 | 값 |
|------|---|
| Host (VM 내부) | localhost |
| Host (외부 접근) | {VM.IP} |
| Port | 6379 |
| Connection (VM 내부) | redis://localhost:6379 |
| Connection (외부 접근) | redis://{VM.IP}:6379 |

### RabbitMQ (해당 시)
| 항목 | 값 |
|------|---|
| Host (VM 내부) | localhost |
| Host (외부 접근) | {VM.IP} |
| AMQP Port | 5672 |
| Management UI | http://{VM.IP}:15672 |
| User | {ROOT} |
| Password | P@ssw0rd$ |

## Docker 네트워크

| 항목 | 값 |
|------|---|
| 네트워크명 | {ROOT}_default (docker compose 자동 생성) |
| 앱 컨테이너 참여 방법 | `docker run --network {ROOT}_default ...` |
| 백킹서비스 호스트명 | postgres, redis, rabbitmq (docker-compose 서비스명) |

> 앱 컨테이너에서 `localhost`가 아닌 **서비스명**을 호스트로 사용해야 한다.
> 예: `DB_HOST=postgres`, `REDIS_HOST=redis`

## 기동 명령어

```bash
# VM 접속
ssh {VM.HOST}

# 프로젝트 디렉토리 이동
cd ~/workspace/{ROOT}

# 백킹서비스 기동
docker compose up -d
```

## Health Check 결과
- [ ] PostgreSQL: pg_isready 정상 (accepting connections)
- [ ] Redis: PONG 확인
- [ ] RabbitMQ: 관리 콘솔 접속 (해당 시)
- [ ] 서비스별 database 존재 확인
```

## 품질 기준

- [ ] `docker compose ps`로 모든 기본 서비스가 `healthy` 상태
- [ ] 서비스별 database가 init 스크립트로 자동 생성됨
- [ ] mock 프로파일이 기동되지 않음 (`--profile mock` 미사용)
- [ ] `docs/deploy/backing-service-result.md`가 작성됨
- [ ] `.env` 파일이 VM에 생성되고 git에 커밋되지 않음

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `docker compose: command not found` | compose 플러그인 미설치 | `sudo apt-get install -y docker-compose-plugin` |
| `permission denied` (docker) | 현재 유저가 docker 그룹에 미포함 | `sudo usermod -aG docker $USER` 후 재접속 |
| `port is already allocated` | 포트 충돌 | `.env`에서 해당 포트 변경 (예: `DB_PORT=15432`) |
| PostgreSQL `FATAL: role "xxx" does not exist` | DB_USER 불일치 | `.env`의 `DB_USER`와 init 스크립트의 GRANT 대상이 일치하는지 확인 |
| init 스크립트 미실행 | 볼륨에 이전 데이터 존재 | `docker compose down -v` 후 재기동 (볼륨 삭제) |
| Redis 연결 거부 | Redis 서비스 미기동 | `docker compose ps`로 상태 확인, `docker compose logs redis` |
| RabbitMQ 관리 콘솔 접근 불가 | 포트 미오픈 또는 서비스 미기동 | VM 방화벽 규칙에 15672 포트 허용 확인 |

## 주의사항

- docker-compose.yml은 develop 단계에서 이미 생성되어 git에 포함됨. VM에서 새로 작성하지 않는다.
- Prism Mock 서버는 deploy 환경에서 기동하지 않는다 (`--profile mock` 사용 금지).
- 백킹서비스는 공개 Docker 이미지(postgres:16, redis:7-alpine 등)를 사용하므로 컨테이너 레지스트리 인증이 불필요하다.
- `.env` 파일은 VM에서만 존재하며 git에 커밋하지 않는다.
- 포트 충돌 방지: VM에 이미 다른 서비스가 5432/6379 등을 사용 중이면 `.env`에서 포트를 변경한다.
- 데이터 초기화(`docker compose down -v`)는 볼륨을 삭제하므로 기존 데이터가 모두 사라진다. 주의하여 사용한다.
- **컨테이너 네트워크**: `docker run`으로 실행하는 앱 컨테이너는 반드시 `--network {ROOT}_default`로 docker-compose 네트워크에 참여해야 백킹서비스에 접근 가능하다. `localhost`가 아닌 서비스명(`postgres`, `redis`)을 호스트로 사용한다.
