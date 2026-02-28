# 프론트엔드 컨테이너 실행방법 가이드

## 목적
프론트엔드 서비스의 컨테이너 이미지를 VM에서 실제로 컨테이너로 실행하고 정상 동작을 확인한다.
실행 결과를 보고서에 기록한다.

## 입력 (이전 단계 산출물)
| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 이미지 빌드 결과 | `deployment/container/build-image-front.md` | 푸시된 이미지 fullname 확인 |

## 출력 (이 단계 산출물)
| 산출물 | 파일 경로 |
|--------|----------|
| 컨테이너 실행 결과서 | `docs/deploy/run-container-front.md` |

## 방법론

### 서비스명 확인
프레임워크에 따라 서비스명 소스가 다르다.
- **React/Vue**: package.json의 "name" 필드값이 서비스명임.
  ```
  {
    "name": "tripgen-front",
    "private": true,
  ```
- **Flutter Web**: pubspec.yaml의 `name` 필드값이 서비스명임.
  ```yaml
  name: tripgen-front
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

접속 후 레지스트리 로그인은 아래 "컨테이너 레지스트리 로그인" 섹션을 참조

### 이미지 확인
`deployment/container/build-image.md`에서 푸시된 이미지 fullname을 확인한다.

예시)
```
docker push docker.io/hiondal/tripgen-front:latest
```
위 기록에서 `docker.io/hiondal/tripgen-front:latest`가 이미지 fullname이다.

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

### 런타임 환경변수 파일 생성
- runtime-env.js 파일을 읽어 그 안의 설정을 모두 포함
  - **React/Vue**: `public/runtime-env.js`
  - **Flutter Web**: `web/runtime-env.js`

  예제)
  ```
  window.__runtime_config__ = {
    API_GROUP: "/api/v1",
    // 서비스별 HOST — docker-compose 서비스명 사용
    MEMBER_HOST: "http://user-service:8080",
    AUTH_HOST: "http://auth-service:8081",
    LOCATION_HOST: "http://location-service:8082",
    TRIP_HOST: "http://trip-service:8083",
    AI_HOST: "http://ai-service:8084",
  };
  ```
- 'localhost'를 **docker-compose 서비스명**으로 변경하여 runtime-env.js 파일을 생성한다.
  - **React/Vue**: `~/{서비스명}/public/runtime-env.js`
  - **Flutter Web**: `~/{서비스명}/web/runtime-env.js`

### 컨테이너 실행
아래 명령으로 컨테이너를 실행한다.
shell 파일을 만들지 말고 command로 수행.
'-v'로 runtime-env.js파일을 볼륨 마운트하도록 명령어 작성.
`--network {ROOT}_default`로 docker-compose 네트워크에 참여시킨다.

```
IMAGE={build-image.md에서 확인한 이미지 fullname}
SERVER_PORT={FRONTEND_PORT}

docker pull ${IMAGE}
docker run -d --name {서비스명} --rm --network {ROOT}_default \
-p ${SERVER_PORT}:8080 \
-v ~/{서비스명}/public/runtime-env.js:/usr/share/nginx/html/runtime-env.js \
${IMAGE}
```

> **Flutter Web의 경우**: 볼륨 마운트의 호스트 측 경로만 다르다.
> `-v ~/{서비스명}/web/runtime-env.js:/usr/share/nginx/html/runtime-env.js`
> 컨테이너 내부 경로(`/usr/share/nginx/html/runtime-env.js`)는 동일하다.

### 컨테이너 실행 확인
아래 명령으로 프론트엔드 서비스의 컨테이너가 실행 되었는지 확인한다.
```
docker ps | grep {서비스명}
```

## 출력 형식

`docs/deploy/run-container-front.md` 결과 보고서 템플릿:

```markdown
# 프론트엔드 컨테이너 실행 결과서

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
| 포트 매핑 | {FRONTEND_PORT}:8080 |
| 네트워크 | {ROOT}_default |
| 상태 | Running |

## runtime-env.js 설정
```javascript
window.__runtime_config__ = {
  API_GROUP: "/api/v1",
  MEMBER_HOST: "http://{docker-compose 서비스명}:{포트}",
  // ... (실제 설정 기록)
};
```

## Health Check 결과
- [ ] `docker ps | grep {서비스명}` 확인: 컨테이너 실행 중
- [ ] 브라우저 접속 확인 (`http://{VM.IP}:{FRONTEND_PORT}`)

## 실행 명령어
```bash
{실제 실행에 사용한 docker run 명령 기록}
```
```

## 품질 기준
- [ ] `docker ps`로 프론트엔드 컨테이너가 `Up` 상태
- [ ] 브라우저에서 `http://{VM.IP}:{FRONTEND_PORT}` 접속 확인
- [ ] `docs/deploy/run-container-front.md`가 작성됨

## 주의사항
- VM에서 실제 컨테이너를 실행하고 정상 동작을 확인한다
- 백킹서비스가 먼저 기동되어 있어야 한다 (Step 3-0 참조)
- shell 파일을 만들지 말고 command로 수행
- runtime-env.js 볼륨 마운트를 반드시 포함하여 런타임 환경변수 주입
- 프론트엔드 컨테이너는 포트 {FRONTEND_PORT} -> 8080(nginx) 매핑으로 실행

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `docker: command not found` | Docker 미설치 | Step 1(배포 사전 준비)에서 Docker 설치 확인 |
| `permission denied` (docker) | 현재 유저가 docker 그룹에 미포함 | `sudo usermod -aG docker $USER` 후 재접속 |
| `network {ROOT}_default not found` | 백킹서비스 미기동 | Step 3-0에서 `docker compose up -d` 먼저 실행 |
| `port is already allocated` | 포트 충돌 | 해당 포트를 사용 중인 컨테이너 확인 후 중지 |
| 컨테이너 즉시 종료 (Exited) | 환경변수 누락 또는 잘못된 값 | `docker logs {서비스명}`으로 에러 확인 |
| 레지스트리 인증 실패 | 토큰 만료 또는 잘못된 인증 정보 | "컨테이너 레지스트리 로그인" 섹션 재수행 |
| 화면은 뜨나 API 호출 실패 | runtime-env.js의 호스트가 localhost | docker-compose 서비스명으로 치환 확인 |
| 403/404 (nginx) | 볼륨 마운트 경로 불일치 | React: `public/runtime-env.js`, Flutter: `web/runtime-env.js` 확인 |
