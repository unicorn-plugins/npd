# RDB 카테고리 가이드 — 로컬 개발 환경

## 목적

PostgreSQL 외 RDB(MySQL, MariaDB) 선택 시 docker-compose 구성 차이점을 제공한다.
이 가이드는 `backing-service-setup.md`의 보조 가이드로, 기본 제품(PostgreSQL) 대신 MySQL 또는 MariaDB를 사용하는 경우에만 참조한다.

---

## 제품 비교 테이블

### docker-compose 서비스 설정 비교

| 설정 항목 | PostgreSQL (기본) | MySQL | MariaDB |
|-----------|------------------|-------|---------|
| **image** | `postgres:16` | `mysql:8.0` | `mariadb:11` |
| **기본 포트** | 5432 | 3306 | 3306 |
| **데이터 볼륨 경로** | `/var/lib/postgresql/data` | `/var/lib/mysql` | `/var/lib/mysql` |
| **Root 계정 환경변수** | `POSTGRES_USER` / `POSTGRES_PASSWORD` | `MYSQL_ROOT_PASSWORD` | `MARIADB_ROOT_PASSWORD` |
| **일반 사용자 환경변수** | (Root = User) | `MYSQL_USER` / `MYSQL_PASSWORD` | `MARIADB_USER` / `MARIADB_PASSWORD` |
| **단일 DB 자동 생성** | `POSTGRES_DB` (생략 시 USER명) | `MYSQL_DATABASE` | `MARIADB_DATABASE` |
| **다중 DB 생성 방법** | init script (`.sql`) | init script (`.sql`) | init script (`.sql`) |
| **Init 마운트 경로** | `/docker-entrypoint-initdb.d:ro` | `/docker-entrypoint-initdb.d:ro` | `/docker-entrypoint-initdb.d:ro` |
| **Init 스크립트 디렉토리** | `docker/postgres/init/` | `docker/mysql/init/` | `docker/mariadb/init/` |
| **Healthcheck 명령** | `pg_isready -U ${DB_USER}` | `mysqladmin ping -h localhost` | `healthcheck.sh --connect` |
| **볼륨명** | `postgres-data` | `mysql-data` | `mariadb-data` |

### .env 변수 비교

| 변수 | PostgreSQL | MySQL | MariaDB |
|------|-----------|-------|---------|
| `DB_PORT` | 5432 | 3306 | 3306 |
| `DB_USER` | `{ROOT}` | `{ROOT}` | `{ROOT}` |
| `DB_PASSWORD` | `P@ssw0rd$` | `P@ssw0rd$` | `P@ssw0rd$` |
| `DB_ROOT_PASSWORD` | (불필요, USER=ROOT) | `P@ssw0rd$` (필수) | `P@ssw0rd$` (필수) |

> MySQL/MariaDB는 Root 계정과 일반 사용자 계정이 분리된다.
> `DB_ROOT_PASSWORD`는 Root 비밀번호, `DB_USER`/`DB_PASSWORD`는 애플리케이션용 일반 사용자이다.

### application.yml (Spring Boot) JDBC 설정 비교

> **주의**: `java-config-manifest-standard.md`의 DB 설정 예제는 PostgreSQL 기준이다 (`driver-class-name: org.postgresql.Driver` 하드코딩).
> MySQL/MariaDB 사용 시 아래 테이블의 Driver 클래스, JDBC URL 패턴, Hibernate Dialect, Gradle 의존성으로 교체한다.

| 설정 항목 | PostgreSQL | MySQL | MariaDB |
|-----------|-----------|-------|---------|
| **JDBC URL 패턴** | `jdbc:postgresql://${DB_HOST}:${DB_PORT}/{DB_NAME}` | `jdbc:mysql://${DB_HOST}:${DB_PORT}/{DB_NAME}` | `jdbc:mariadb://${DB_HOST}:${DB_PORT}/{DB_NAME}` |
| **Driver 클래스** | `org.postgresql.Driver` | `com.mysql.cj.jdbc.Driver` | `org.mariadb.jdbc.Driver` |
| **Hibernate Dialect** | `PostgreSQLDialect` | `MySQLDialect` | `MariaDBDialect` |
| **Gradle 의존성** | `runtimeOnly 'org.postgresql:postgresql'` | `runtimeOnly 'com.mysql:mysql-connector-j'` | `runtimeOnly 'org.mariadb.jdbc:mariadb-java-client'` |

---

## 제품별 docker-compose.yml 스니펫

### MySQL

`backing-service-setup.md`의 postgres 서비스 블록을 아래로 교체한다.

```yaml
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    ports:
      - "${DB_PORT:-3306}:3306"
    volumes:
      - mysql-data:/var/lib/mysql
      - ./docker/mysql/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
```

> `MYSQL_DATABASE`를 생략하면 단일 DB가 자동 생성되지 않는다.
> 서비스별 database는 init 스크립트로 생성한다.

### MariaDB

```yaml
  mariadb:
    image: mariadb:11
    environment:
      MARIADB_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MARIADB_USER: ${DB_USER}
      MARIADB_PASSWORD: ${DB_PASSWORD}
    ports:
      - "${DB_PORT:-3306}:3306"
    volumes:
      - mariadb-data:/var/lib/mysql
      - ./docker/mariadb/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect"]
      interval: 10s
      timeout: 5s
      retries: 5
```

**volumes 선언 추가:**

```yaml
volumes:
  mysql-data:    # MySQL 사용 시
  mariadb-data:  # MariaDB 사용 시
```

---

## 제품별 다중 DB 초기화 스크립트

### PostgreSQL (기본 — 참조용)

`docker/postgres/init/01-create-databases.sql`:
```sql
CREATE DATABASE order;
CREATE DATABASE inventory;
CREATE DATABASE "user";  -- 예약어는 큰따옴표

GRANT ALL PRIVILEGES ON DATABASE order TO {ROOT};
GRANT ALL PRIVILEGES ON DATABASE inventory TO {ROOT};
GRANT ALL PRIVILEGES ON DATABASE "user" TO {ROOT};
```

### MySQL

`docker/mysql/init/01-create-databases.sql`:
```sql
CREATE DATABASE IF NOT EXISTS `order`;
CREATE DATABASE IF NOT EXISTS `inventory`;
CREATE DATABASE IF NOT EXISTS `user`;  -- 예약어는 백틱

GRANT ALL PRIVILEGES ON `order`.* TO '{ROOT}'@'%';
GRANT ALL PRIVILEGES ON `inventory`.* TO '{ROOT}'@'%';
GRANT ALL PRIVILEGES ON `user`.* TO '{ROOT}'@'%';
FLUSH PRIVILEGES;
```

### MariaDB

`docker/mariadb/init/01-create-databases.sql`:
```sql
CREATE DATABASE IF NOT EXISTS `order`;
CREATE DATABASE IF NOT EXISTS `inventory`;
CREATE DATABASE IF NOT EXISTS `user`;  -- 예약어는 백틱

GRANT ALL PRIVILEGES ON `order`.* TO '{ROOT}'@'%';
GRANT ALL PRIVILEGES ON `inventory`.* TO '{ROOT}'@'%';
GRANT ALL PRIVILEGES ON `user`.* TO '{ROOT}'@'%';
FLUSH PRIVILEGES;
```

> MySQL과 MariaDB의 init script 문법은 동일하다. `FLUSH PRIVILEGES;`를 반드시 포함한다.

### 초기화 스크립트 문법 비교

| 항목 | PostgreSQL | MySQL | MariaDB |
|------|-----------|-------|---------|
| **DB 생성** | `CREATE DATABASE order;` | `` CREATE DATABASE IF NOT EXISTS `order`; `` | `` CREATE DATABASE IF NOT EXISTS `order`; `` |
| **권한 부여** | `GRANT ALL PRIVILEGES ON DATABASE order TO {ROOT};` | `` GRANT ALL PRIVILEGES ON `order`.* TO '{ROOT}'@'%'; `` | `` GRANT ALL PRIVILEGES ON `order`.* TO '{ROOT}'@'%'; `` |
| **예약어 처리** | `"user"` (큰따옴표) | `` `user` `` (백틱) | `` `user` `` (백틱) |
| **반영 명령** | (자동) | `FLUSH PRIVILEGES;` | `FLUSH PRIVILEGES;` |

---

## 제품별 .env.example 추가 변수

MySQL/MariaDB 사용 시 `.env.example`에 아래 변수를 추가한다.

```dotenv
# ===========================
# Database (MySQL/MariaDB)
# ===========================
DB_USER={ROOT}
DB_PASSWORD=P@ssw0rd$
DB_ROOT_PASSWORD=P@ssw0rd$
DB_PORT=3306
DB_HOST=localhost
```

> PostgreSQL의 `DB_PORT=5432`를 `DB_PORT=3306`으로 변경한다.
> `DB_ROOT_PASSWORD`를 추가한다 (MySQL/MariaDB Root 계정 비밀번호).

---

## 제품별 기동 확인 명령

| 서비스 | 확인 명령 | 정상 응답 |
|--------|----------|----------|
| PostgreSQL | `docker compose exec postgres pg_isready -U ${DB_USER}` | `accepting connections` |
| MySQL | `docker compose exec mysql mysqladmin ping -h localhost` | `mysqld is alive` |
| MariaDB | `docker compose exec mariadb healthcheck.sh --connect` | 종료 코드 0 |

**서비스별 database 확인:**

| 서비스 | 확인 명령 |
|--------|----------|
| PostgreSQL | `docker compose exec postgres psql -U ${DB_USER} -l` |
| MySQL | `docker compose exec mysql mysql -u${DB_USER} -p${DB_PASSWORD} -e "SHOW DATABASES;"` |
| MariaDB | `docker compose exec mariadb mariadb -u${DB_USER} -p${DB_PASSWORD} -e "SHOW DATABASES;"` |

---

## 주의사항

- **자격 증명 통일 규칙**: DB_USER는 AGENTS.md의 `{ROOT}` 값, DB_PASSWORD/DB_ROOT_PASSWORD는 `P@ssw0rd$`로 통일한다.
- **테이블 생성 금지**: 데이터베이스(스키마)만 생성한다. 테이블은 JPA `ddl-auto=update` 또는 Flyway/Liquibase로 자동 생성된다.
- **포트 충돌 방지**: MySQL/MariaDB 기본 포트(3306)가 로컬에서 이미 사용 중인 경우 `.env`에서 변경한다.
- **MySQL/MariaDB 문자셋**: 기본 문자셋이 `utf8mb4`인지 확인한다 (MySQL 8.0+, MariaDB 10.3+ 기본값).
