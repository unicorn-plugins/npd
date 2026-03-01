# NoSQL 카테고리 가이드 — VM 배포 환경

## 목적

MongoDB를 VM docker-compose로 배포할 때의 설정 및 healthcheck를 제공한다.
이 가이드는 `backing-service-deploy.md`의 보조 가이드이다.

---

## Healthcheck 테이블

> 현재 MongoDB 단일 제품이며, 향후 제품 추가 시 열(column)을 확장한다.

| 확인 항목 | MongoDB |
|-----------|---------|
| **기동 확인 명령** | `docker compose exec mongo mongosh --eval "db.adminCommand('ping')"` |
| **정상 응답** | `{ ok: 1 }` |
| **DB 목록 확인** | `docker compose exec mongo mongosh -u ${MONGO_USER} -p ${MONGO_PASSWORD} --authenticationDatabase admin --eval "db.adminCommand({listDatabases: 1})"` |
| **기본 포트** | 27017 |

---

## Docker 네트워크 호스트명

| NoSQL | docker-compose 서비스명 | 앱 컨테이너의 MONGO_HOST |
|-------|----------------------|------------------------|
| MongoDB | `mongo` | `mongo` |

> 앱 컨테이너는 `--network {ROOT}_default`로 docker-compose 네트워크에 참여해야 한다.
> `localhost`가 아닌 서비스명(`mongo`)을 호스트로 사용한다.

---

## 결과 보고서 템플릿

```markdown
### MongoDB
| 항목 | 값 |
|------|---|
| Host (VM 내부) | localhost |
| Host (외부 접근) | {VM.IP} |
| Port | 27017 |
| Database | 서비스별 database (init 스크립트로 자동 생성) |
| User | {ROOT} |
| Password | P@ssw0rd$ |
| Connection URI (VM 내부) | mongodb://{ROOT}:P@ssw0rd$@localhost:27017/{서비스명}?authSource=admin |
| Connection URI (외부 접근) | mongodb://{ROOT}:P@ssw0rd$@{VM.IP}:27017/{서비스명}?authSource=admin |
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `MongoServerError: Authentication failed` | 사용자/비밀번호 불일치 | `.env`의 `MONGO_USER`/`MONGO_PASSWORD` 확인. `?authSource=admin` URI 파라미터 확인 |
| `connect ECONNREFUSED 127.0.0.1:27017` | MongoDB 서비스 미기동 | `docker compose ps`로 상태 확인, `docker compose logs mongo` |
| init 스크립트 미실행 | 볼륨에 이전 데이터 존재 | `docker compose down -v` 후 재기동 (볼륨 삭제) |
| `port is already allocated` (27017) | 포트 충돌 | `.env`에서 `MONGO_PORT=27018`로 변경 |
| `mongosh: command not found` | mongo:7 이전 이미지 사용 | `mongo:7` 이상 이미지 사용 확인 (이전 버전은 `mongo` 명령) |
| 외부 접근 불가 | VM 방화벽 미오픈 | VM 방화벽 규칙에 27017 포트 허용 확인 |

---

## 주의사항

- docker-compose.yml은 develop 단계에서 이미 생성되어 git에 포함됨. VM에서 새로 작성하지 않는다.
- `.env` 파일은 VM에서만 존재하며 git에 커밋하지 않는다.
- MongoDB 인증이 활성화된 상태이므로, 접속 시 `?authSource=admin`을 URI에 반드시 포함해야 한다.
- 데이터 초기화(`docker compose down -v`)는 볼륨을 삭제하므로 기존 데이터가 모두 사라진다.
