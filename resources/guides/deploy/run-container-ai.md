# AI 서비스 컨테이너 실행방법 가이드

## 목적
AI 서비스(Python FastAPI 기반)의 컨테이너 이미지를 VM에서 실제로 컨테이너로 실행하고 정상 동작을 확인한다.
실행 결과를 보고서에 기록한다.

## 입력 (이전 단계 산출물)
| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 이미지 빌드 결과 | `deployment/container/build-image-ai.md` | 푸시된 이미지 fullname 확인 |

## 출력 (이 단계 산출물)
| 산출물 | 파일 경로 |
|--------|----------|
| 컨테이너 실행 결과서 | `docs/deploy/run-container-ai.md` |

## 방법론

### 서비스명 확인
AI 서비스 디렉토리의 `pyproject.toml` 파일에서 서비스명을 확인한다.

```toml
[tool.poetry]
name = "ai-service"
```

`[tool.poetry] name` 필드값이 서비스명이다. `pyproject.toml`이 없는 경우 AI 서비스 디렉토리명을 서비스명으로 사용한다.

### VM 원격 실행
이 가이드의 모든 명령은 VM에 SSH 접속하여 실행한다.

**방법 1: Host alias 사용 (권장)**
```
ssh {VM.HOST}
```

**방법 2: Key 직접 지정 (Host alias 미설정 시 fallback)**
```
chmod 400 {VM.KEY파일}
ssh -i {VM.KEY파일} {VM.USERID}@{VM.IP}
```

- 접속 후 레지스트리 로그인은 아래 "컨테이너 레지스트리 로그인" 섹션을 참조

### 이미지 확인
`deployment/container/build-image.md`에서 푸시된 이미지 fullname을 확인한다.

예시)
```
docker push docker.io/hiondal/ai-service:latest
```
위 기록에서 `docker.io/hiondal/ai-service:latest`가 이미지 fullname이다.

### 컨테이너 레지스트리 로그인

#### Cloud 인증 (VM 환경)

VM에서 레지스트리 로그인 전, 해당 Cloud의 CLI 인증이 필요하다.

- **AWS (ECR 사용 시)**:
  - 권장: EC2 Instance Profile (IAM Role 연결) — 별도 인증 불필요
  - 대안: 로컬의 `~/.aws/credentials`를 VM에 복사
    ```bash
    scp ~/.aws/credentials {사용자}@{VM-IP}:~/.aws/credentials
    ```

- **Azure (ACR 사용 시)**:
  - 권장: Managed Identity — 별도 인증 불필요
  - 대안: `az login` 후 credentials 복사

- **GCP (GCR 사용 시)**:
  - 권장: Service Account (Workload Identity) — 별도 인증 불필요
  - 대안: `gcloud auth` credentials 복사

#### 레지스트리 로그인

> VM에서 실행한다.

`[실행정보]`의 `레지스트리유형`에 따라 로그인한다.

- **DockerHub:**
```bash
docker login -u ${IMG_ID} -p ${IMG_PW} docker.io
```

- **ECR:**
```bash
aws ecr get-login-password --region ${ECR_REGION} \
  | docker login --username AWS --password-stdin \
    ${ECR_ACCOUNT}.dkr.ecr.${ECR_REGION}.amazonaws.com
```

- **ACR:**
```bash
az acr login --name ${ACR명}
```

- **GCR:**
```bash
gcloud auth configure-docker ${GCR_REGION}-docker.pkg.dev
```

### 컨테이너 실행

- 환경변수 파일 확인

  Step 3 PREV_ACTION에서 로컬 `.env` 파일이 VM의 `~/workspace/{ROOT}/.env`로 복사되어 있다.
  `.env` 파일에서 `APP_PORT` 값을 확인한다. 기본값은 8000이다.

  ```bash
  # .env 파일에서 APP_PORT 확인
  grep '^APP_PORT=' ~/workspace/{ROOT}/.env || echo "APP_PORT=8000"
  ```

- 아래 명령으로 컨테이너를 실행한다.
  - shell 파일을 만들지 말고 command로 수행한다.
  - `--env-file`로 `.env` 파일을 전달하여 환경변수를 일괄 주입한다.
  - 중요) `--network {ROOT}_default`로 docker-compose 네트워크에 참여시킨다.
    - 백킹서비스 접속 호스트는 docker-compose 서비스명을 사용한다 (예: `DB_HOST=postgres`, `REDIS_HOST=redis`).
    - `.env`의 호스트 값이 `localhost`나 IP인 경우, docker-compose 서비스명으로 치환해야 한다.

  ```
  IMAGE={build-image.md에서 확인한 이미지 fullname}
  APP_PORT=$(grep '^APP_PORT=' ~/workspace/{ROOT}/.env | cut -d= -f2 || echo 8000)

  docker pull ${IMAGE}
  docker run -d --name {서비스명} --rm --network {ROOT}_default \
  -p ${APP_PORT}:${APP_PORT} \
  --env-file ~/workspace/{ROOT}/.env \
  ${IMAGE}
  ```

  > `.env`의 백킹서비스 호스트(DB_HOST, REDIS_HOST 등)가 `localhost`나 VM IP로 되어 있는 경우, 컨테이너 실행 전에 docker-compose 서비스명으로 치환한다:
  > ```bash
  > sed -i 's/DB_HOST=.*/DB_HOST=postgres/' ~/workspace/{ROOT}/.env
  > sed -i 's/REDIS_HOST=.*/REDIS_HOST=redis/' ~/workspace/{ROOT}/.env
  > ```

### 컨테이너 실행 확인
아래 명령으로 AI 서비스 컨테이너가 실행 되었는지 확인한다.
```
docker ps | grep {서비스명}
```

헬스체크 확인:
```
wget -qO- http://localhost:{APP_PORT}/health
# 기대 응답: {"status":"ok"}
```

## 출력 형식

`docs/deploy/run-container-ai.md` 결과 보고서 템플릿:

```markdown
# AI 서비스 컨테이너 실행 결과서

## 구성 환경
- 환경: docker run (VM 컨테이너 배포)
- VM: {VM.HOST} ({VM.IP})
- 실행 일시: YYYY-MM-DD

## VM 접속 방법
```
ssh {VM.HOST}
```

## 실행된 컨테이너

| 항목 | 값 |
|------|---|
| 서비스명 | {서비스명} |
| 이미지 | {이미지 fullname} |
| 포트 매핑 | {APP_PORT}:{APP_PORT} |
| 네트워크 | {ROOT}_default |
| 상태 | Running |

## 환경변수 설정
| 변수 | 값 |
|------|---|
| LLM_PROVIDER | {값} |
| LLM_MODEL_NAME | {값} |
| APP_PORT | {값} |

## Health Check 결과
- [ ] `docker ps | grep {서비스명}` 확인: 컨테이너 실행 중
- [ ] `wget -qO- http://localhost:{APP_PORT}/health` 정상 응답 (`{"status":"ok"}`)

## 실행 명령어
```bash
{실제 실행에 사용한 docker run 명령 기록}
```
```

## 품질 기준
- [ ] `docker ps`로 AI 서비스 컨테이너가 `Up` 상태
- [ ] `wget -qO- http://localhost:{APP_PORT}/health` 정상 응답
- [ ] `docs/deploy/run-container-ai-result.md`가 작성됨

## 주의사항
- VM에서 실제 컨테이너를 실행하고 정상 동작을 확인한다
- 백킹서비스가 먼저 기동되어 있어야 한다 (Step 3-0 참조)
- shell 파일을 만들지 말고 command로 수행
- 환경변수는 로컬 `.env` 파일을 VM에 복사하여 `--env-file`로 주입 (PREV_ACTION에서 `scp`로 전송됨)
- `.env`의 백킹서비스 호스트(DB_HOST, REDIS_HOST 등)는 docker-compose 서비스명으로 치환 필요
- 포트 환경변수는 `APP_PORT` (기본값 8000). 백엔드의 `SERVER_PORT`와 다름에 주의
- Health check endpoint는 `/health` (Spring Boot Actuator의 `/actuator/health`가 아님)
- CORS는 FastAPI 미들웨어로 처리되므로 별도 CORS 환경변수 설정 불필요 (backend-to-backend 내부 서비스)

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `docker: command not found` | Docker 미설치 | Step 1(배포 사전 준비)에서 Docker 설치 확인 |
| `permission denied` (docker) | 현재 유저가 docker 그룹에 미포함 | `sudo usermod -aG docker $USER` 후 재접속 |
| `network {ROOT}_default not found` | 백킹서비스 미기동 | Step 3-0에서 `docker compose up -d` 먼저 실행 |
| `port is already allocated` | 포트 충돌 | 해당 포트를 사용 중인 컨테이너 확인 후 중지 |
| 컨테이너 즉시 종료 (Exited) | 환경변수 누락 또는 잘못된 값 | `docker logs {서비스명}`으로 에러 확인 |
| 레지스트리 인증 실패 | 토큰 만료 또는 잘못된 인증 정보 | "컨테이너 레지스트리 로그인" 섹션 재수행 |
| `/health` 503 응답 | LLM API Key 미설정 | `.env` 파일의 LLM API Key 환경변수 값 확인 |
| 모듈 import 에러 | Python 의존성 이미지 빌드 실패 | Dockerfile 및 `docker logs` 확인 |
