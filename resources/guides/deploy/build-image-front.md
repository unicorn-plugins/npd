# 프론트엔드 컨테이너이미지 작성가이드

## 목적
프론트엔드 서비스의 컨테이너 이미지를 생성하고 이미지 레지스트리에 푸시한다. 수행한 명령어를 포함하여 컨테이너 이미지 작성 과정을 결과 파일에 기록한다.

## 입력 (이전 단계 산출물)
| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 기술스택 정보 | `CLAUDE.md` | 빌드 도구 및 프레임워크 결정 |
| 프론트엔드 소스 | `(런타임 결정)` | 빌드 대상 |

## 출력 (이 단계 산출물)
| 산출물 | 파일 경로 |
|--------|----------|
| 컨테이너 이미지 빌드 결과 | `docs/deploy/build-image-front.md` |
| 프론트엔드 Dockerfile | `deployment/container/Dockerfile-frontend` |
| nginx 설정 파일 | `deployment/container/nginx.conf` |
| .dockerignore | `.dockerignore` |

## 방법론

### 기술스택 확인 및 분기

CLAUDE.md의 기술스택 정보를 확인하여 아래 결정 트리를 따른다.

```
1. CLAUDE.md에서 프론트엔드 프레임워크 확인
2. IF package.json의 dependencies에 "react" + devDependencies에 "vite" → [Vite/React 분기]
3. IF package.json의 dependencies에 "vue" → [Vue 분기]
4. IF pubspec.yaml 존재 + dependencies에 "flutter" → [Flutter Web 분기]
5. 해당 없으면 사용자에게 확인
```

| 기술스택 | 빌드 명령 | 빌드 결과 경로 | 서빙 방식 |
|----------|----------|---------------|----------|
| Vite (React/Vue) | `npm run build` | `dist` | nginx 정적 서빙 |
| Vue CLI | `npm run build` | `dist` | nginx 정적 서빙 |
| Flutter Web | `flutter build web --release` | `build/web` | nginx 정적 서빙 |

> Next.js(SSR), Angular 등 서버사이드 렌더링이 필요한 프레임워크는 별도 가이드에서 다룬다. Flutter Web은 아래 Flutter Web 분기를 참조한다.

### 서비스명 확인

프레임워크에 따라 서비스명 소스가 다르다.

- **React/Vue**: package.json의 `"name"` 필드값이 서비스명이다.
  ```json
  {
    "name": "tripgen-front",
    "private": true
  }
  ```
- **Flutter Web**: pubspec.yaml의 `name` 필드값이 서비스명이다.
  ```yaml
  name: tripgen-front
  description: TripGen Frontend
  ```

### 패키지 의존성 동기화

- **React/Vue**:
  package.json과 package-lock.json을 일치시킨다.
  ```
  npm install
  ```

- **Flutter Web**:
  pubspec.yaml의 의존성을 설치한다.
  ```
  flutter pub get
  ```

### .dockerignore 생성

프로젝트 루트에 아래 내용으로 `.dockerignore` 파일을 생성한다.
백엔드·프론트엔드·AI 서비스 공통으로 사용한다.
```
.git
.gitignore
*.md
.env*
.idea/
.vscode/
node_modules
dist
**/target
**/build
**/__pycache__
*.pyc
.dart_tool/
.packages
.venv/
.pytest_cache/
chroma_db/
deployment/
!deployment/container/
```

> `deployment/container/`는 Dockerfile과 nginx.conf가 위치하는 경로이므로 제외하지 않는다.

### nginx.conf 파일 생성

아래 내용으로 `deployment/container/nginx.conf` 파일을 생성한다.
```nginx
server {
    listen 8080;
    server_name localhost;

    # 프록시 버퍼 설정
    client_max_body_size 100M;
    proxy_buffer_size 128k;
    proxy_buffers 4 256k;
    proxy_busy_buffers_size 256k;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;

        # 정적 파일 캐시
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {
            expires 1y;
            add_header Cache-Control "public, no-transform";
        }
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 'healthy\n';
        add_header Content-Type text/plain;
    }

    # Error pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

### Dockerfile 생성 (React/Vue)

아래 내용으로 `deployment/container/Dockerfile-frontend` 생성.

```dockerfile
# Build stage
FROM node:{version}-alpine AS builder
ARG PROJECT_FOLDER
WORKDIR /app

# 의존성 설치 (레이어 캐싱 최적화: package 파일만 먼저 복사)
COPY ${PROJECT_FOLDER}/package*.json ./
RUN npm ci

# 애플리케이션 빌드
COPY ${PROJECT_FOLDER} .
RUN npm run build

# Run stage
FROM nginx:stable-alpine

ARG BUILD_FOLDER

# 빌드 결과물 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx 설정 파일 복사
COPY ${BUILD_FOLDER}/nginx.conf /etc/nginx/conf.d/default.conf

# 권한 설정
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 8080

# HEALTHCHECK: Docker 단독 실행 시 헬스 확인용. K8s 환경에서는 Probe가 우선함.
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

> **Vite/Vue 공통**: 두 프레임워크 모두 `npm run build` 결과가 `dist/` 디렉토리에 생성되므로 동일한 Dockerfile을 사용한다.
> `{version}`은 CLAUDE.md의 `### develop > 기술스택 > Node.js` 버전을 참조하여 결정한다. 기술스택 정보가 없으면 기본값 `20`을 사용한다.
> **rollup 플랫폼 오류 발생 시**: 트러블슈팅 섹션의 "rollup platform-specific 오류" 항목을 참고한다.

### Dockerfile 생성 (Flutter Web)

Flutter Web 프로젝트인 경우 아래 내용으로 `deployment/container/Dockerfile-frontend` 생성.

```dockerfile
# Build stage
FROM ghcr.io/cirruslabs/flutter:stable AS builder
ARG PROJECT_FOLDER
WORKDIR /app

# 의존성 설치 (레이어 캐싱 최적화: pubspec 파일만 먼저 복사)
COPY ${PROJECT_FOLDER}/pubspec.yaml ${PROJECT_FOLDER}/pubspec.lock ./
RUN flutter pub get

# 애플리케이션 빌드
# --web-renderer 옵션: html(경량, ~가벼운 번들) 또는 canvaskit(기본, 고품질 렌더링 ~2MB 추가)
# 경량 빌드가 필요하면 --web-renderer html 추가
COPY ${PROJECT_FOLDER} .
RUN flutter build web --release

# Run stage
FROM nginx:stable-alpine

ARG BUILD_FOLDER

# 빌드 결과물 복사
COPY --from=builder /app/build/web /usr/share/nginx/html

# nginx 설정 파일 복사
COPY ${BUILD_FOLDER}/nginx.conf /etc/nginx/conf.d/default.conf

# 권한 설정
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 8080

# HEALTHCHECK: Docker 단독 실행 시 헬스 확인용. K8s 환경에서는 Probe가 우선함.
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

> **React/Vue Dockerfile과의 차이점**: 빌드 스테이지 이미지(`ghcr.io/cirruslabs/flutter:stable`), 의존성 파일(`pubspec.yaml`/`pubspec.lock`), 빌드 명령(`flutter build web --release`), 빌드 결과 경로(`build/web`). 실행 스테이지는 동일하다.
> **Flutter Web 빌드 시간**: Flutter SDK 이미지(~2GB)로 인해 최초 빌드가 React/Vue 대비 느릴 수 있다. Docker 레이어 캐싱이 적용되면 이후 빌드는 빨라진다.

### 컨테이너 이미지 생성

> VM에서 실행한다.

아래 명령으로 서비스 빌드. shell 파일을 생성하지 말고 command로 수행.
```
DOCKER_FILE=deployment/container/Dockerfile-frontend

docker build \
  --platform linux/amd64 \
  --build-arg PROJECT_FOLDER="{프론트엔드-디렉토리}" \
  --build-arg BUILD_FOLDER="deployment/container" \
  -f ${DOCKER_FILE} \
  -t {서비스명}:latest .
```

> **Flutter Web의 경우**: 동일한 명령을 사용한다. Dockerfile 내부에서 Flutter SDK 빌드가 수행되므로 호스트에 Flutter SDK가 설치되어 있지 않아도 된다.

### 이미지 레지스트리 푸시

빌드된 이미지를 `[실행정보]`의 레지스트리에 태그하고 푸시한다.

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

#### 리포지토리 자동 생성 (ECR / GCR)

ECR과 GCR은 푸시 전 리포지토리가 존재해야 한다. 존재 여부를 확인하고 없으면 생성한다.
DockerHub와 ACR은 푸시 시 자동 생성되므로 별도 작업 불필요.

- **ECR:**
```bash
REPO_NAME="${ROOT}/${service}"
aws ecr describe-repositories \
  --repository-names ${REPO_NAME} \
  --region ${ECR_REGION} 2>/dev/null \
|| aws ecr create-repository \
  --repository-name ${REPO_NAME} \
  --region ${ECR_REGION} \
  --image-scanning-configuration scanOnPush=true
```

- **GCR** (최초 1회):
```bash
gcloud artifacts repositories describe ${GCR_REPO} \
  --location=${GCR_REGION} \
  --project=${GCR_PROJECT} 2>/dev/null \
|| gcloud artifacts repositories create ${GCR_REPO} \
  --repository-format=docker \
  --location=${GCR_REGION} \
  --project=${GCR_PROJECT}
```

#### 이미지 태그 및 푸시

> VM에서 실행한다.

```bash
service={서비스명}
docker tag ${service}:latest ${REGISTRY_URL}/${service}:latest
docker push ${REGISTRY_URL}/${service}:latest
```

> `${REGISTRY_URL}`은 `[실행정보]`에서 조립된 값을 사용한다.
> `${ROOT}`는 CLAUDE.md의 시스템명을 참조한다.

## 출력 형식
`docs/deploy/build-image-front.md` 파일에 수행한 명령어를 포함하여 컨테이너 이미지 작성 과정을 단계별로 기록한다.

## 품질 기준
- [ ] `.dockerignore` 파일이 프로젝트 루트에 생성되었는가?
- [ ] Dockerfile이 멀티스테이지 빌드로 구성되어 있는가?
- [ ] 실행 스테이지가 `nginx:stable-alpine` 계열인가?
- [ ] 비루트 사용자(`nginx`)로 실행하도록 설정되어 있는가?
- [ ] `npm ci`가 한 번만 실행되는가? (이중 설치 금지)
- [ ] (Flutter Web) `flutter pub get`이 한 번만 실행되는가? (이중 설치 금지)
- [ ] (Flutter Web) 빌드 결과물 경로가 `build/web`인가?
- [ ] 빌드 결과물만 최종 이미지에 복사되는가?
- [ ] nginx listen 포트(8080)와 EXPOSE 포트(8080)가 일치하는가?
- [ ] 이미지 빌드가 성공했는가?
- [ ] 레지스트리 로그인이 성공했는가?
- [ ] (ECR/GCR) 리포지토리 존재 확인 및 자동 생성이 정상 수행되었는가?
- [ ] 이미지가 레지스트리에 푸시되었는가?
- [ ] 빌드 실패 상태로 다음 단계 미진행

## 트러블슈팅
| 증상 | 원인 | 해결 |
|------|------|------|
| `npm ci` 실패 (ERESOLVE) | 의존성 충돌 | `npm ci --legacy-peer-deps` 시도 |
| `npm run build` 실패 (메모리) | Node.js 힙 메모리 부족 | Dockerfile에 `ENV NODE_OPTIONS=--max-old-space-size=4096` 추가 |
| rollup platform-specific 오류 | 호스트/컨테이너 플랫폼 불일치 | `RUN npm ci` 뒤에 `RUN npm rebuild` 추가 |
| nginx 403 Forbidden | 빌드 결과물 경로 오류 | 빌드 결과가 `dist/`에 생성되는지 확인, `ls /usr/share/nginx/html` 검증 |
| 컨테이너 즉시 종료 | nginx 설정 오류 | `docker logs {서비스명}` 확인, `nginx -t`로 설정 검증 |
| SPA 라우팅 404 | try_files 미설정 | nginx.conf에 `try_files $uri $uri/ /index.html` 확인 |
| `flutter pub get` 실패 | pubspec.lock 불일치 또는 SDK 버전 비호환 | Dockerfile의 Flutter 이미지 태그를 프로젝트 SDK 버전에 맞게 조정 |
| `COPY pubspec.lock` 실패 | pubspec.lock이 버전 관리에 미포함 | Flutter 앱 프로젝트는 `pubspec.lock`을 반드시 커밋 (`flutter create`로 생성 시 기본 포함됨) |
| `flutter build web` 실패 | web 지원 미활성화 | 프로젝트에서 `flutter create --platforms web .`으로 web 지원 추가 |
| nginx 403 (Flutter) | 빌드 결과물 경로 오류 | 빌드 결과가 `build/web/`에 생성되는지 확인, `ls /usr/share/nginx/html` 검증 |
| Flutter 빌드 결과물 용량 과대 | canvaskit 렌더러 기본 사용 | `flutter build web --release --web-renderer html` 시도 또는 canvaskit 유지 시 이미지 크기 100MB 초과 허용 |
| `denied: requested access to the resource is denied` | 레지스트리 인증 실패 | 레지스트리 로그인 상태 확인, 토큰/권한 점검 |
| `repository does not exist` (ECR) | ECR 리포지토리 미생성 | `aws ecr describe-repositories` 확인 후 `create-repository` 실행 |
| `docker push` 타임아웃 | 네트워크 또는 이미지 크기 문제 | 네트워크 확인, 이미지 크기 최적화 |
| SSH 연결 끊김 (빌드 중 갑자기 종료) | VM 메모리 부족 (OOM Killer) | VM 스펙 업그레이드 (최소 4GB 권장, t3a.xlarge 16GB 검증됨) |
| `docker push` 시 `use of closed network connection` | 로컬 → Cloud 레지스트리 네트워크 불안정 | 동일 Cloud 내부 VM에서 push 수행 |
| VM에서 `docker: command not found` | Docker 미설치 | VM에 Docker 설치: `sudo yum install -y docker && sudo systemctl start docker` (Amazon Linux) |
| 빌드 시간이 과도하게 길다 | VM 최초 빌드 시 Docker 레이어 캐시 없음 | 정상 동작임. 2회차부터 캐시 적용. BuildKit 활성화: `DOCKER_BUILDKIT=1 docker build ...` |

## 주의사항
- shell 파일을 생성하지 말고 command로 직접 수행
- 빌드 실패 시 반드시 원인을 파악하고 해결한 후 다음 단계 진행
- Dockerfile의 ARG 이름(`PROJECT_FOLDER`, `BUILD_FOLDER`)은 CI/CD 파이프라인 가이드와 공유되므로 변경 금지
- 이미지 태그는 로컬 빌드 시 `:latest`를 사용. CI/CD 환경에서의 태그 전략은 CI/CD 파이프라인 가이드에서 관리
- VM에서 빌드 시 Docker가 설치되어 있어야 한다 (Node.js/Flutter 설치는 불필요)
- VM 최소 스펙: 4GB RAM 이상 권장 (메모리 부족 시 OOM으로 SSH 끊김 발생)
