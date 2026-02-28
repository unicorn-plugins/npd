# 백엔드 컨테이너 실행방법 가이드

## 목적
백엔드 각 서비스들의 컨테이너 이미지를 VM에서 실제로 컨테이너로 실행하고 정상 동작을 확인한다.
실행 결과를 보고서에 기록한다.

## 입력 (이전 단계 산출물)
| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 이미지 빌드 결과 | `deployment/container/build-image.md` | 푸시된 이미지 fullname 확인 |

## 출력 (이 단계 산출물)
| 산출물 | 파일 경로 |
|--------|----------|
| 컨테이너 실행 결과서 | `docs/deploy/run-container-back-result.md` |

## 방법론

### 시스템명과 서비스명 확인
settings.gradle에서 확인.
- 시스템명: rootProject.name
- 서비스명: include 'common'하위의 include문 뒤의 값임

예시) include 'common'하위의 4개가 서비스명임.
```
rootProject.name = 'tripgen'

include 'common'
include 'user-service'
include 'location-service'
include 'ai-service'
include 'trip-service'
```

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
docker push docker.io/hiondal/user-service:latest
```
위 기록에서 `docker.io/hiondal/user-service:latest`가 이미지 fullname이다.

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

> `settings.gradle`의 `include` 목록에서 `common`을 제외한 각 서비스마다 아래 절차를 반복하여 `docker run` 명령을 실행한다.

- 환경변수 확인

  `{서비스명}/.run/{서비스명}.run.xml` 을 읽어 각 서비스의 환경변수 찾음.
  "env.map"의 각 entry의 key와 value가 환경변수임.

  예제) SERVER_PORT=8081, DB_HOST=20.249.137.175가 환경변수임
  ```
  <component name="ProjectRunConfigurationManager">
    <configuration default="false" name="ai-service" type="GradleRunConfiguration" factoryName="Gradle">
      <ExternalSystemSettings>
        <option name="env">
          <map>
            <entry key="SERVER_PORT" value="8084" />
            <entry key="DB_HOST" value="20.249.137.175" />
  ```

- 아래 명령으로 컨테이너를 실행한다.
  - shell 파일을 만들지 말고 command로 수행.
  - 모든 환경변수에 대해 '-e' 파라미터로 환경변수값을 넘긴다.
  - 중요) `--network {ROOT}_default`로 docker-compose 네트워크에 참여시킨다.
    - 백킹서비스 접속 호스트는 `localhost`나 VM IP가 아닌 **docker-compose 서비스명**을 사용한다.
    - 예: `DB_HOST=postgres`, `REDIS_HOST=redis`, `MQ_HOST=rabbitmq`
    - `.run.xml`의 `DB_HOST` 값이 localhost나 IP인 경우 서비스명으로 치환한다.
  - 중요) CORS 설정 환경변수에 프론트엔드 주소 추가
    - 'ALLOWED_ORIGINS' 포함된 환경변수가 CORS 설정 환경변수임.
    - 이 환경변수의 값에 'http://{VM.IP}:{FRONTEND_PORT}'번 추가

  ```
  IMAGE={build-image.md에서 확인한 이미지 fullname}
  SERVER_PORT={환경변수의 SERVER_PORT값}

  docker pull ${IMAGE}
  docker run -d --name {서비스명} --rm --network {ROOT}_default \
  -p ${SERVER_PORT}:${SERVER_PORT} \
  -e {환경변수 KEY}={환경변수 VALUE} \
  ${IMAGE}
  ```

### 컨테이너 실행 확인
아래 명령으로 모든 서비스의 컨테이너가 실행 되었는지 확인한다.
```
docker ps | grep {서비스명}
```

## 출력 형식

`docs/deploy/run-container-back-result.md` 결과 보고서 템플릿:

```markdown
# 백엔드 컨테이너 실행 결과서

## 구성 환경
- 환경: docker run (VM 컨테이너 배포)
- VM: {VM.HOST} ({VM.IP})
- 실행 일시: YYYY-MM-DD

## VM 접속 방법
```
ssh {VM.HOST}
```

## 실행된 컨테이너

| 서비스명 | 이미지 | 포트 매핑 | 네트워크 | 상태 |
|---------|--------|----------|---------|------|
| {서비스명} | {이미지 fullname} | {SERVER_PORT}:{SERVER_PORT} | {ROOT}_default | Running |

## Health Check 결과
- [ ] `docker ps | grep {서비스명}` 확인: 컨테이너 실행 중
- [ ] 각 서비스 API 응답 확인 (`curl http://localhost:{SERVER_PORT}/actuator/health`)

## 실행 명령어
```bash
{실제 실행에 사용한 docker run 명령 기록}
```
```

## 품질 기준
- [ ] `docker ps`로 모든 서비스 컨테이너가 `Up` 상태
- [ ] 각 서비스 `/actuator/health` 정상 응답
- [ ] `docs/deploy/run-container-back-result.md`가 작성됨

## 주의사항
- VM에서 실제 컨테이너를 실행하고 정상 동작을 확인한다
- 백킹서비스가 먼저 기동되어 있어야 한다 (Step 3-0 참조)
- shell 파일을 만들지 말고 command로 수행
- CORS 설정 환경변수에 프론트엔드 VM 주소(`http://{VM.IP}:{FRONTEND_PORT}`) 반드시 추가

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `docker: command not found` | Docker 미설치 | Step 1(배포 사전 준비)에서 Docker 설치 확인 |
| `permission denied` (docker) | 현재 유저가 docker 그룹에 미포함 | `sudo usermod -aG docker $USER` 후 재접속 |
| `network {ROOT}_default not found` | 백킹서비스 미기동 | Step 3-0에서 `docker compose up -d` 먼저 실행 |
| `port is already allocated` | 포트 충돌 | 해당 포트를 사용 중인 컨테이너 확인 후 중지 |
| 컨테이너 즉시 종료 (Exited) | 환경변수 누락 또는 잘못된 값 | `docker logs {서비스명}`으로 에러 확인 |
| 레지스트리 인증 실패 | 토큰 만료 또는 잘못된 인증 정보 | "컨테이너 레지스트리 로그인" 섹션 재수행 |
| DB 접속 실패 | DB_HOST가 localhost 또는 VM IP | docker-compose 서비스명으로 치환 (예: `DB_HOST=postgres`) |
| CORS 에러 (브라우저) | ALLOWED_ORIGINS 미설정 | `http://{VM.IP}:{FRONTEND_PORT}` 추가 확인 |
