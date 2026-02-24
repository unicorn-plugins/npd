# 프론트엔드 컨테이너이미지 작성가이드

## 목적
프론트엔드 서비스의 컨테이너 이미지를 생성하고, 실제 빌드 수행 및 검증까지 완료한다. 수행한 명령어를 포함하여 컨테이너 이미지 작성 과정을 결과 파일에 기록한다.

## 입력 (이전 단계 산출물)
| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 기술스택 정보 | `CLAUDE.md` | 빌드 도구 및 프레임워크 결정 |
| 프론트엔드 소스 | `(런타임 결정)` | 빌드 대상 |

## 출력 (이 단계 산출물)
| 산출물 | 파일 경로 |
|--------|----------|
| 컨테이너 이미지 빌드 가이드 | `deployment/container/build-image.md` |
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
```
.git
.gitignore
*.md
.env*
node_modules
dist
build
.dart_tool/
.packages
.idea/
.vscode/
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

### Dockerfile 생성

아래 내용으로 `deployment/container/Dockerfile-frontend` 생성.

```dockerfile
# Build stage
FROM node:20-alpine AS builder
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

아래 명령으로 서비스 빌드. shell 파일을 생성하지 말고 command로 수행.
```
DOCKER_FILE=deployment/container/Dockerfile-frontend

docker build \
  --platform linux/amd64 \
  --build-arg PROJECT_FOLDER="." \
  --build-arg BUILD_FOLDER="deployment/container" \
  -f ${DOCKER_FILE} \
  -t {서비스명}:latest .
```

> **Flutter Web의 경우**: 동일한 명령을 사용한다. Dockerfile 내부에서 Flutter SDK 빌드가 수행되므로 호스트에 Flutter SDK가 설치되어 있지 않아도 된다.

### 생성된 이미지 검증

#### 1. 이미지 존재 및 크기 확인
```
docker images | grep {서비스명}
```
> nginx + 정적 파일 이미지는 일반적으로 50~100MB 범위가 적정. 200MB 초과 시 .dockerignore 및 빌드 결과물을 점검한다.

#### 2. 컨테이너 기동 테스트 (선택)
```
docker run --rm -d --name {서비스명}-test -p 0:8080 {서비스명}:latest
# 5초 대기 후 컨테이너 상태 확인
sleep 5
docker ps | grep {서비스명}-test
# 헬스 확인
wget -qO- http://localhost:8080/health
docker stop {서비스명}-test
```

#### 3. 이미지 보안 스캔 (선택)
```
# trivy 설치 시
trivy image --severity HIGH,CRITICAL {서비스명}:latest
```

## 출력 형식
`deployment/container/build-image.md` 파일에 수행한 명령어를 포함하여 컨테이너 이미지 작성 과정을 단계별로 기록한다.

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
- [ ] 이미지 크기가 합리적인가? (nginx+정적파일: 50~100MB)
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

## 주의사항
- shell 파일을 생성하지 말고 command로 직접 수행
- 빌드 실패 시 반드시 원인을 파악하고 해결한 후 다음 단계 진행
- Dockerfile의 ARG 이름(`PROJECT_FOLDER`, `BUILD_FOLDER`)은 CI/CD 파이프라인 가이드와 공유되므로 변경 금지
- 이미지 태그는 로컬 빌드 시 `:latest`를 사용. CI/CD 환경에서의 태그 전략은 CI/CD 파이프라인 가이드에서 관리
