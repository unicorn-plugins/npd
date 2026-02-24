# AI 서비스 컨테이너 실행방법 가이드

## 목적
AI 서비스(Python FastAPI 기반)의 컨테이너 이미지를 컨테이너로 실행하는 가이드를 작성한다. 실제 컨테이너 실행은 하지 않으며, 수행할 명령어를 포함하여 컨테이너 실행 가이드를 결과 파일에 생성한다.

## 입력 (이전 단계 산출물)
| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| Docker 이미지 | `(런타임 결정)` | 컨테이너 실행 대상 |

## 출력 (이 단계 산출물)
| 산출물 | 파일 경로 |
|--------|----------|
| 컨테이너 실행 가이드 | `deployment/container/run-container-guide.md` |

## 방법론

### 실행정보 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인한다.

**공통 항목:**
- {레지스트리유형}: 이미지 레지스트리 유형 (`DockerHub`, `ECR`, `ACR`, `GCR`)
- {REGISTRY_URL}: 이미지 레지스트리 전체 경로 (유형별 조립됨)
- {VM.KEY파일}: VM 접속하는 Private Key파일 경로
- {VM.USERID}: VM 접속하는 OS 유저명
- {VM.IP}: VM IP

**유형별 추가 항목:**
| 유형 | 추가 항목 |
|------|----------|
| DockerHub | IMG_REG, IMG_ORG, IMG_ID, IMG_PW |
| ECR | ECR_ACCOUNT, ECR_REGION |
| ACR | ACR명 |
| GCR | GCR_PROJECT, GCR_REGION, GCR_REPO |

#### Docker Hub 예시
```
[실행정보]
- 레지스트리유형: DockerHub
- IMG_REG: docker.io
- IMG_ORG: hiondal
- IMG_ID: hiondal
- IMG_PW: dckr_pat_xxxxx
- REGISTRY_URL: docker.io/hiondal
- VM
  - KEY파일: ~/home/bastion-dg0500
  - USERID: azureuser
  - IP: 4.230.5.6
```

#### AWS ECR 예시
```
[실행정보]
- 레지스트리유형: ECR
- ECR_ACCOUNT: 123456789012
- ECR_REGION: ap-northeast-2
- REGISTRY_URL: 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/tripgen
- VM
  - KEY파일: ~/home/bastion-dg0500
  - USERID: azureuser
  - IP: 4.230.5.6
```

#### Azure ACR 예시
```
[실행정보]
- 레지스트리유형: ACR
- ACR명: acrdigitalgarage01
- REGISTRY_URL: acrdigitalgarage01.azurecr.io/tripgen
- VM
  - KEY파일: ~/home/bastion-dg0500
  - USERID: azureuser
  - IP: 4.230.5.6
```

#### Google GCR 예시
```
[실행정보]
- 레지스트리유형: GCR
- GCR_PROJECT: my-project-id
- GCR_REGION: asia-northeast3
- GCR_REPO: my-repo
- REGISTRY_URL: asia-northeast3-docker.pkg.dev/my-project-id/my-repo
- VM
  - KEY파일: ~/home/bastion-dg0500
  - USERID: azureuser
  - IP: 4.230.5.6
```

### REGISTRY_URL 변수 정의
`[실행정보]`의 `REGISTRY_URL` 값을 사용한다. 이후 태그/푸시/실행/재배포 명령에서 `{REGISTRY_URL}/{서비스명}:latest` 형식으로 통합 사용한다.

| 유형 | REGISTRY_URL 조립 규칙 |
|------|----------------------|
| DockerHub | `docker.io/{IMG_ORG}` |
| ECR | `{ECR_ACCOUNT}.dkr.ecr.{ECR_REGION}.amazonaws.com/{ROOT}` |
| ACR | `{ACR명}.azurecr.io/{ROOT}` |
| GCR | `{GCR_REGION}-docker.pkg.dev/{GCR_PROJECT}/{GCR_REPO}` |

### 서비스명 확인
AI 서비스 디렉토리의 `pyproject.toml` 파일에서 서비스명을 확인한다.

```toml
[tool.poetry]
name = "ai-service"
```

`[tool.poetry] name` 필드값이 서비스명이다. `pyproject.toml`이 없는 경우 AI 서비스 디렉토리명을 서비스명으로 사용한다.

### VM 접속 방법 안내
- Linux/Mac은 기본 터미널을 실행하고 Window는 Window Terminal을 실행하도록 안내
- 터미널에서 아래 명령으로 VM에 접속하도록 안내

  최초 한번 Private key파일의 모드를 변경.
  ```
  chmod 400 {VM.KEY파일}
  ```

  private key를 이용하여 접속.
  ```
  ssh -i {VM.KEY파일} {VM.USERID}@{VM.IP}
  ```
- 접속 후 레지스트리 로그인은 아래 "컨테이너 레지스트리 로그인 방법 안내" 섹션을 참조

### Git Repository 클론 안내
- workspace 디렉토리 생성 및 이동
  ```
  mkdir -p ~/home/workspace
  cd ~/home/workspace
  ```
- 소스 Clone
  ```
  git clone {원격 Git Repository 주소}
  ```
- 프로젝트 디렉토리로 이동
  ```
  cd {ROOT}
  ```

### 어플리케이션 빌드 및 컨테이너 이미지 생성 방법 안내
`deployment/container/build-image.md` 파일을 열어 가이드대로 수행하도록 안내

### 컨테이너 레지스트리 로그인 방법 안내

`[실행정보]`의 `레지스트리유형`에 따라 해당하는 로그인 방법을 안내한다.

#### Docker Hub
```
docker login docker.io -u {IMG_ID} -p {IMG_PW}
```

#### AWS ECR
사전 요구사항: `aws` CLI가 설치되어 있어야 한다.

ECR 인증 토큰을 발급받아 로그인한다.
```
aws ecr get-login-password --region {ECR_REGION} | docker login --username AWS --password-stdin {ECR_ACCOUNT}.dkr.ecr.{ECR_REGION}.amazonaws.com
```

> **주의**: ECR 인증 토큰은 **12시간** 후 만료된다. 만료 시 위 명령을 다시 실행하여 재인증한다.

#### Azure ACR
사전 요구사항: `az` CLI가 설치되어 있어야 한다.

아래 명령으로 {ACR명}의 인증정보를 구한다.
'username'이 ID이고 'passwords[0].value'가 암호임.
```
az acr credential show --name {ACR명}
```

예시) ID=dg0200cr, 암호={암호}
```
$ az acr credential show --name dg0200cr
{
  "passwords": [
    {
      "name": "password",
      "value": "{암호}"
    },
    {
      "name": "password2",
      "value": "{암호2}"
    }
  ],
  "username": "dg0200cr"
}
```

아래와 같이 로그인 명령을 작성한다.
```
docker login {ACR명}.azurecr.io -u {ID} -p {암호}
```

#### Google GCR (Artifact Registry)
사전 요구사항: `gcloud` CLI가 설치되어 있어야 한다.

gcloud 인증을 통해 Docker를 설정한다.
```
gcloud auth configure-docker {GCR_REGION}-docker.pkg.dev
```

또는 서비스 계정 JSON 키를 사용하는 경우:
```
cat {서비스계정키.json} | docker login -u _json_key --password-stdin https://{GCR_REGION}-docker.pkg.dev
```

### 컨테이너 이미지 태그 및 푸시 방법 안내

Docker Tag 명령으로 이미지를 tag하는 명령을 작성한다.
```
docker tag {서비스명}:latest {REGISTRY_URL}/{서비스명}:latest
```

이미지 푸시 명령을 작성한다.
```
docker push {REGISTRY_URL}/{서비스명}:latest
```

### 컨테이너 실행 명령 생성
- 환경변수 확인

  AI 서비스 디렉토리의 `.env.example` 파일을 읽어 환경변수를 추출한다.
  `^[A-Z_]+=` 패턴에 매칭되는 라인에서 환경변수를 추출하고, `#`으로 시작하는 주석 라인은 제외한다.

  예제) `.env.example`에서 추출
  ```
  APP_ENV=development
  APP_PORT=8000
  LOG_LEVEL=INFO
  LLM_PROVIDER=openai
  LLM_MODEL_NAME=gpt-4o
  OPENAI_API_KEY=your-openai-api-key-here
  ```

  위에서 `APP_PORT`가 포트 환경변수이며, 기본값은 8000이다.

- 아래 명령으로 컨테이너를 실행하는 명령을 생성한다.
  - shell 파일을 만들지 말고 command로 수행하는 방법 안내.
  - `.env.example`에서 추출한 모든 환경변수에 대해 '-e' 파라미터로 환경변수값을 넘긴다.
  - 주석 처리된(`#` 접두사) 환경변수는 선택적이므로, 실제 사용 여부를 확인 후 필요한 것만 포함한다.

  ```
  APP_PORT={환경변수의 APP_PORT값, 기본 8000}

  docker run -d --name {서비스명} --rm -p ${APP_PORT}:${APP_PORT} \
  -e APP_ENV={값} \
  -e APP_PORT=${APP_PORT} \
  -e LLM_PROVIDER={값} \
  -e OPENAI_API_KEY={값} \
  {REGISTRY_URL}/{서비스명}:latest
  ```

### 실행된 컨테이너 확인 방법 작성
아래 명령으로 AI 서비스 컨테이너가 실행 되었는지 확인하는 방법을 안내.
```
docker ps | grep {서비스명}
```

헬스체크 확인:
```
wget -qO- http://localhost:{APP_PORT}/health
# 기대 응답: {"status":"ok"}
```

### 재배포 방법 작성
- 로컬에서 수정된 소스 푸시
- VM 접속
- 디렉토리 이동 및 소스 내려받기
  ```
  cd ~/home/workspace/{ROOT}
  ```
  ```
  git pull
  ```
- 컨테이너 이미지 재생성

  `deployment/container/build-image.md` 파일을 열어 가이드대로 수행

- 레지스트리 재인증 (필요 시)

  > **AWS ECR 사용 시**: ECR 토큰은 **12시간** 후 만료되므로, 재배포 전 토큰 유효 여부를 확인하고 만료된 경우 "컨테이너 레지스트리 로그인 방법 안내"의 AWS ECR 섹션을 참조하여 재인증한다.

- 컨테이너 이미지 태그 및 푸시
  ```
  docker tag {서비스명}:latest {REGISTRY_URL}/{서비스명}:latest
  docker push {REGISTRY_URL}/{서비스명}:latest
  ```

- 컨테이너 중지
  ```
  docker stop {서비스명}
  ```
- 컨테이너 이미지 삭제
  ```
  docker rmi {REGISTRY_URL}/{서비스명}:latest
  ```

- 컨테이너 재실행

  위 "컨테이너 실행 명령 생성" 섹션의 `docker run` 명령을 그대로 실행한다.

## 출력 형식
`deployment/container/run-container-guide.md` 파일에 수행할 명령어를 포함하여 컨테이너 실행 가이드를 단계별로 기록한다.

## 품질 기준
- [ ] 컨테이너 정상 실행 확인
- [ ] 로컬 검증 없이 K8s 배포 미진행

## 주의사항
- 실제 컨테이너 실행은 하지 않고 가이드 문서만 생성
- shell 파일을 만들지 말고 command로 수행하는 방법으로 안내
- `.run/*.run.xml`은 Java/IntelliJ 전용이므로 사용하지 않음. `.env.example`에서 환경변수를 추출
- 환경변수 파싱: `^[A-Z_]+=` 패턴 라인 추출, `#` 주석 라인 제외
- 포트 환경변수는 `APP_PORT` (기본값 8000). 백엔드의 `SERVER_PORT`와 다름에 주의
- Health check endpoint는 `/health` (Spring Boot Actuator의 `/actuator/health`가 아님)
- CORS는 FastAPI 미들웨어로 처리되므로 별도 CORS 환경변수 설정 불필요 (backend-to-backend 내부 서비스)
