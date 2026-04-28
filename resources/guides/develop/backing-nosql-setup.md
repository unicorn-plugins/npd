# NoSQL 카테고리 가이드 — 로컬 개발 환경

## 목적

MongoDB 사용 시 docker-compose 구성 방법을 제공한다.
이 가이드는 `backing-service-setup.md`의 보조 가이드로, 설계서에서 MongoDB 사용이 명시된 경우에만 참조한다.

---

## 제품 비교 테이블

> 현재 MongoDB 단일 제품이며, 향후 제품 추가 시 열(column)을 확장한다.

| 설정 항목 | MongoDB |
|-----------|---------|
| **image** | `mongo:7` |
| **기본 포트** | 27017 |
| **데이터 볼륨 경로** | `/data/db` |
| **Root 계정 환경변수** | `MONGO_INITDB_ROOT_USERNAME` / `MONGO_INITDB_ROOT_PASSWORD` |
| **Init 마운트 경로** | `/docker-entrypoint-initdb.d:ro` |
| **Init 스크립트 디렉토리** | `docker/mongo/init/` |
| **Init 스크립트 언어** | JavaScript (`.js`) |
| **Healthcheck 명령** | `mongosh --eval "db.adminCommand('ping')"` |
| **볼륨명** | `mongo-data` |

### .env 변수

| 변수 | MongoDB |
|------|---------|
| `MONGO_PORT` | 27017 |
| `MONGO_USER` | `{ROOT}` |
| `MONGO_PASSWORD` | `P@ssw0rd$` |

### application.yml (Spring Boot) MongoDB 설정

| 설정 항목 | MongoDB |
|-----------|---------|
| **Connection URI** | `mongodb://${MONGO_USER}:${MONGO_PASSWORD}@${MONGO_HOST}:${MONGO_PORT}/${DB_NAME}?authSource=admin` |
| **Spring Boot 의존성** | `implementation 'org.springframework.boot:spring-boot-starter-data-mongodb'` |
| **application.yml 키** | `spring.data.mongodb.uri` |

---

## docker-compose.yml 스니펫

`backing-service-setup.md`의 docker-compose.yml에 아래 서비스를 **추가**한다.
(RDB 서비스를 교체하는 것이 아니라, RDB와 함께 사용하는 경우가 일반적이다.)

```yaml
  mongo:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    ports:
      - "${MONGO_PORT:-27017}:27017"
    volumes:
      - mongo-data:/data/db
      - ./docker/mongo/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5
```

**volumes 선언 추가:**

```yaml
volumes:
  mongo-data:
```

---

## 다중 DB 초기화 스크립트 (JavaScript)

MongoDB는 JavaScript 기반 init 스크립트를 사용한다.

`docker/mongo/init/01-create-databases.js`:
```javascript
// 서비스별 database 생성 (설계서 기반으로 작성)
// MongoDB는 use 명령으로 database를 생성/전환한다

// 서비스별 database 사용자 생성
const databases = ['order', 'inventory', 'user'];

databases.forEach(function(dbName) {
  db = db.getSiblingDB(dbName);
  db.createUser({
    user: process.env.MONGO_INITDB_ROOT_USERNAME || 'admin',
    pwd: process.env.MONGO_INITDB_ROOT_PASSWORD || 'password',
    roles: [{ role: 'readWrite', db: dbName }]
  });
  // 빈 컬렉션 생성으로 database 확정
  db.createCollection('_init');
  db.getCollection('_init').drop();
});

print('=== MongoDB init complete: databases created ===');
```

> **참고**: MongoDB는 데이터가 삽입될 때 database가 실제로 생성된다.
> init 스크립트에서 `createCollection` + `drop`으로 database를 명시적으로 확정한다.

---

## .env.example 추가 변수

MongoDB 사용 시 `.env.example`에 아래 변수를 추가한다.

```dotenv
# ===========================
# MongoDB (NoSQL 사용 시)
# ===========================
MONGO_USER={ROOT}
MONGO_PASSWORD=P@ssw0rd$
MONGO_PORT=27017
MONGO_HOST=localhost
```

---

## 기동 확인 명령

| 서비스 | 확인 명령 | 정상 응답 |
|--------|----------|----------|
| MongoDB | `docker compose exec mongo mongosh --eval "db.adminCommand('ping')"` | `{ ok: 1 }` |

**서비스별 database 확인:**

```bash
docker compose exec mongo mongosh -u ${MONGO_USER} -p ${MONGO_PASSWORD} --authenticationDatabase admin --eval "db.adminCommand({listDatabases: 1})"
```

---

## PostgreSQL과의 공존 참고

하나의 docker-compose.yml에 PostgreSQL + MongoDB를 함께 구성하는 경우:

- PostgreSQL은 RDB 서비스용, MongoDB는 NoSQL 서비스용으로 역할을 분리한다.
- 각 서비스의 application.yml에서 사용하는 DB 종류에 맞는 설정을 적용한다.
- `.env`에 PostgreSQL 변수(DB_*)와 MongoDB 변수(MONGO_*)를 모두 포함한다.
- volumes에 `postgres-data:`와 `mongo-data:`를 모두 선언한다.

```yaml
# docker-compose.yml 예시 (공존)
services:
  postgres:
    image: postgres:16
    # ... (기존 설정 유지)

  mongo:
    image: mongo:7
    # ... (위 스니펫 참조)

volumes:
  postgres-data:
  mongo-data:
```

---

## 주의사항

- **자격 증명 통일 규칙**: MONGO_USER는 AGENTS.md의 `{ROOT}` 값, MONGO_PASSWORD는 `P@ssw0rd$`로 통일한다.
- **인증 활성화**: `MONGO_INITDB_ROOT_USERNAME`/`MONGO_INITDB_ROOT_PASSWORD`를 설정하면 MongoDB 인증이 자동 활성화된다. 접속 시 `?authSource=admin`을 URI에 포함해야 한다.
- **포트 충돌 방지**: MongoDB 기본 포트(27017)가 로컬에서 이미 사용 중인 경우 `.env`에서 변경한다.
- **볼륨 초기화**: MongoDB 데이터를 완전히 초기화하려면 `docker compose down -v`로 볼륨을 함께 삭제한다.
