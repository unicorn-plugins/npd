# RDB 카테고리 가이드 — VM 배포 환경

## 목적

PostgreSQL 외 RDB(MySQL, MariaDB)를 VM docker-compose로 배포할 때의 차이점을 제공한다.
이 가이드는 `backing-service-deploy.md`의 보조 가이드이다.

---

## Healthcheck 비교 테이블

| 확인 항목 | PostgreSQL (기본) | MySQL | MariaDB |
|-----------|------------------|-------|---------|
| **기동 확인 명령** | `docker compose exec postgres pg_isready -U ${DB_USER}` | `docker compose exec mysql mysqladmin ping -h localhost` | `docker compose exec mariadb healthcheck.sh --connect` |
| **정상 응답** | `accepting connections` | `mysqld is alive` | 종료 코드 0 |
| **DB 목록 확인** | `docker compose exec postgres psql -U ${DB_USER} -l` | `docker compose exec mysql mysql -u${DB_USER} -p${DB_PASSWORD} -e "SHOW DATABASES;"` | `docker compose exec mariadb mariadb -u${DB_USER} -p${DB_PASSWORD} -e "SHOW DATABASES;"` |
| **기본 포트** | 5432 | 3306 | 3306 |

---

## Docker 네트워크 호스트명 매핑

`docker run`으로 실행하는 앱 컨테이너에서 백킹서비스에 접근할 때 사용하는 호스트명:

| RDB | docker-compose 서비스명 | 앱 컨테이너의 DB_HOST |
|-----|----------------------|---------------------|
| PostgreSQL | `postgres` | `postgres` |
| MySQL | `mysql` | `mysql` |
| MariaDB | `mariadb` | `mariadb` |

> 앱 컨테이너는 `--network {ROOT}_default`로 docker-compose 네트워크에 참여해야 한다.
> `localhost`가 아닌 서비스명을 호스트로 사용한다.

---

## 결과 보고서 템플릿 (제품별)

### MySQL

```markdown
### MySQL
| 항목 | 값 |
|------|---|
| Host (VM 내부) | localhost |
| Host (외부 접근) | {VM.IP} |
| Port | 3306 |
| Database | 서비스별 database (init 스크립트로 자동 생성) |
| User | {ROOT} |
| Password | P@ssw0rd$ |
| JDBC URL (VM 내부) | jdbc:mysql://localhost:3306/{서비스명} |
| JDBC URL (외부 접근) | jdbc:mysql://{VM.IP}:3306/{서비스명} |
```

### MariaDB

```markdown
### MariaDB
| 항목 | 값 |
|------|---|
| Host (VM 내부) | localhost |
| Host (외부 접근) | {VM.IP} |
| Port | 3306 |
| Database | 서비스별 database (init 스크립트로 자동 생성) |
| User | {ROOT} |
| Password | P@ssw0rd$ |
| JDBC URL (VM 내부) | jdbc:mariadb://localhost:3306/{서비스명} |
| JDBC URL (외부 접근) | jdbc:mariadb://{VM.IP}:3306/{서비스명} |
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| MySQL `Access denied for user` | 사용자 권한 미부여 | init 스크립트에 `GRANT ALL PRIVILEGES` + `FLUSH PRIVILEGES;` 확인 |
| MySQL `Can't connect to local MySQL server` | 소켓 연결 문제 | `-h 127.0.0.1` 또는 `-h localhost` 사용, 포트 확인 |
| MariaDB `ERROR 1045 (28000)` | 비밀번호 불일치 | `.env`의 `DB_ROOT_PASSWORD`와 `DB_PASSWORD` 확인 |
| init 스크립트 미실행 | 볼륨에 이전 데이터 존재 | `docker compose down -v` 후 재기동 (볼륨 삭제) |
| `port is already allocated` (3306) | 포트 충돌 | `.env`에서 `DB_PORT=13306`으로 변경 |
| MySQL/MariaDB 한글 깨짐 | 문자셋 미설정 | `MYSQL_CHARSET=utf8mb4` 환경변수 추가 또는 my.cnf 마운트 |

---

## 주의사항

- docker-compose.yml은 develop 단계에서 이미 생성되어 git에 포함됨. VM에서 새로 작성하지 않는다.
- `.env` 파일은 VM에서만 존재하며 git에 커밋하지 않는다.
- MySQL/MariaDB의 기본 포트(3306)는 PostgreSQL(5432)과 다르므로, `.env`의 `DB_PORT` 값을 확인한다.
