# 백엔드 배포 가이드

## 목적
백엔드 서비스를 쿠버네티스에 배포하기 위한 매니페스트 파일 작성.
매니페스트 파일을 작성하고 실제 배포까지 수행.
수행한 명령어와 결과를 포함하여 배포 결과 레포트 생성.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 컨테이너 실행 결과 | `docs/deploy/run-container-back-result.md` | 이미지명, 환경변수, 포트 정보 추출 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 배포 결과 | `docs/deploy/deploy-k8s-back-result.md` |
| 공통 매니페스트 파일 | `deployment/k8s/common/*` |
| 서비스별 매니페스트 파일 | `deployment/k8s/{서비스명}/*` |

## 방법론

### 실행정보 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {레지스트리유형}: 레지스트리 유형 (DockerHub / ECR / ACR / GCR)
- {REGISTRY_URL}: 이미지 레지스트리 URL (레지스트리유형에 따라 자동 조립됨)
- {네임스페이스}: 배포할 네임스페이스
- {서비스 리소스}: 서비스별 파드수, CPU, 메모리 설정

> `{REGISTRY_URL}`은 SKILL.md의 `[실행정보]` 조립 규칙에서 레지스트리유형별로 자동 결정된다.
> - DockerHub: `docker.io/{IMG_ORG}`
> - ECR: `{ECR_ACCOUNT}.dkr.ecr.{ECR_REGION}.amazonaws.com/{ROOT}`
> - ACR: `{ACR명}.azurecr.io/{ROOT}`
> - GCR: `{GCR_REGION}-docker.pkg.dev/{GCR_PROJECT}/{GCR_REPO}`

예시) ACR 환경
```
[실행정보]
- 레지스트리유형: ACR
- ACR명: acrdigitalgarage01
- REGISTRY_URL: acrdigitalgarage01.azurecr.io/tripgen
- 네임스페이스: tripgen
- 서비스 리소스:
  - member-service: 파드수=2, CPU=250m/1000m, 메모리=256Mi/1024Mi
  - location-service: 파드수=2, CPU=250m/1000m, 메모리=256Mi/1024Mi
```

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

### 매니페스트 작성 주의사항
- namespace는 명시: {네임스페이스}값 이용
- Database와 Redis의 Host명은 Service 객체 이름으로 함
- 공통 Secret의 JWT_SECRET 값은 반드시 openssl명령으로 생성하여 지정
- 매니페스트 파일 안에 환경변수를 사용하지 말고 실제 값을 지정
  예) host: "tripgen.${INGRESS_IP}.nip.io" => host: "tripgen.4.1.2.3.nip.io"
- Secret 매니페스트에서 'data' 대신 'stringData'를 사용
- 객체이름 네이밍룰
  - 공통 ConfigMap: cm-common
  - 공통 Secret: secret-common
  - 서비스별 ConfigMap: cm-{서비스명}
  - 서비스별 Secret: secret-{서비스명}
  - Ingress: {ROOT}
  - Service: {서비스명}
  - Deployment: {서비스명}

### 공통 매니페스트 작성 (`deployment/k8s/common/` 디렉토리 하위)

**Image Pull Secret 매니페스트 작성: secret-imagepull.yaml**
- name: {ROOT}
- `[실행정보]`의 `레지스트리유형`에 따라 USERNAME과 PASSWORD를 아래 명령으로 구한다:

| 레지스트리유형 | USERNAME 취득 | PASSWORD 취득 |
|--------------|--------------|--------------|
| DockerHub | `[실행정보]`의 `IMG_ID` 값 | `[실행정보]`의 `IMG_PW` 값 |
| ECR | `AWS` | `aws ecr get-login-password --region {ECR_REGION}` |
| ACR | `az acr credential show -n {ACR명} --query "username" -o tsv` | `az acr credential show -n {ACR명} --query "passwords[0].value" -o tsv` |
| GCR | `_json_key` | `gcloud auth print-access-token` |

- USERNAME과 PASSWORD의 실제 값을 매니페스트에 지정

**Ingress 매니페스트 작성: ingress.yaml**
- host: api.{SSL_DOMAIN}
  > 백엔드 API 전용 서브도메인. 프론트엔드 Ingress(`{SSL_DOMAIN}`)와 host를 분리하여 충돌을 방지한다.
- `ingressClassName` 또는 annotation은 CLOUD에 따라 설정:

  | CLOUD | ingressClassName | annotation | 비고 |
  |-------|-----------------|------------|------|
  | AWS | `alb` | - | IngressClass 수동 생성 필요 (`create-k8s.md` 참조) |
  | Azure | `webapprouting.kubernetes.azure.com` | - | AKS Automatic에 자동 내장 |
  | GCP | (지정하지 않음) | `kubernetes.io/ingress.class: "gce"` | GKE Autopilot에 자동 내장 |

- API Gateway 서비스가 없는 경우 Ingress에서 각 백엔드 서비스 연결
  - path: 각 서비스 별 Controller 클래스의 '@RequestMapping'과 클래스 내 메소드의 매핑정보를 읽어 지정
  - pathType: Prefix
  - backend.service.name: {서비스명}
  - backend.service.port.number: 80
- API Gateway 서비스가 있는 경우
  - path: /
  - pathType: Prefix
  - backend.service.name: {API Gateway 서비스명}
  - backend.service.port.number: {API Gateway 포트}
- **중요**: rewrite-target 관련 annotation 설정 절대 하지 말것.

**공통 ConfigMap과 Secret 매니페스트 작성**
- 컨테이너 실행 결과(`docs/deploy/run-container-back-result.md`)의 `docker run` 명령에서 공통된 환경변수를 추출.
- 보안이 필요한 환경변수(암호, 인증토큰 등)는 Secret 매니페스트로 작성: secret-common.yaml(name:cm-common)
- 그 외 일반 환경변수 매니페스트 작성: cm-common.yaml(name:secret-common)
- Redis HOST명은 IP가 아닌 Service 객체명으로 함.
  아래 명령으로 'redis'가 포함된 서비스 객체를 찾고 'ClusterIP'유형인 서비스명을 Host명으로 사용
  ```
  kubectl get svc | grep redis
  ```
- REDIS_DATABASE는 각 서비스별 ConfigMap에 지정
- 주의) Database는 공통 ConfigMap/Secret으로 작성 금지
- 공통 ConfigMap에 CORS_ALLOWED_ORIGINS 설정: 'http://localhost:8081,http://localhost:8082,http://localhost:8083,http://localhost:8084,https://{SSL_DOMAIN}'
  > `{SSL_DOMAIN}`은 Web Server VM의 `/etc/nginx/sites-available/default`에서 `server_name` 값으로 확인한다 (예: `mydomain.com`, `{ID}.{VM Public IP}.nip.io` 등)

### 서비스별 매니페스트 작성 (`deployment/k8s/{서비스명}/` 디렉토리 하위)

**ConfigMap과 Secret 매니페스트 작성**
- 컨테이너 실행 결과(`docs/deploy/run-container-back-result.md`)의 `docker run` 명령에서 환경변수를 추출.
- cm-common.yaml과 secret-common.yaml에 있는 공통 환경변수는 중복해서 작성하면 안됨
- 보안이 필요한 환경변수(암호, 인증토큰 등)는 Secret 매니페스트로 작성: secret-{서비스명}.yaml(name:cm-{서비스명})
- 그 외 일반 환경변수 매니페스트 작성: cm-{서비스명}.yaml(name:secret-{서비스명})
- Database HOST명은 IP가 아닌 Service 객체명으로 함.
  아래 명령으로 '{서비스명}'과 'db'가 포함된 서비스 객체를 찾고 'ClusterIP'유형인 서비스명을 Host명으로 사용
  ```
  kubectl get svc | grep {서비스명}
  ```
- REDIS_DATABASE는 컨테이너 실행 명령에 지정된 값으로 서비스별 ConfigMap에 지정

**Service 매니페스트 작성**
- API Gateway 서비스가 없는 경우
  - name: {서비스명}
  - port: 80
  - targetPort: 컨테이너 실행 명령의 SERVER_PORT값
  - type: ClusterIP
- API Gateway 서비스가 있는 경우
  - name: {API Gateway 서비스명}
  - port: {API Gateway 포트}
  - targetPort: {API Gateway 포트}
  - type: ClusterIP

**Deployment 매니페스트 작성**
- name: {서비스명}
- replicas: {서비스 리소스}에서 해당 서비스의 파드수
- ImagePullPolicy: Always
- ImagePullSecrets: {ROOT}
- image: {REGISTRY_URL}/{서비스명}:latest
- ConfigMap과 Secret은 'env'대신에 'envFrom'을 사용하여 지정
- envFrom:
  - configMapRef: 공통 ConfigMap 'cm-common'과 각 서비스 ConfigMap 'cm-{서비스명}'을 지정
  - secretRef: 공통 Secret 'secret-common'과 각 서비스 Secret 'secret-{서비스명}'을 지정
- resources: {서비스 리소스}에서 해당 서비스의 CPU/메모리 값 적용
- Probe:
  - Startup Probe: Actuator '/actuator/health'로 지정
  - Readiness Probe: Actuator '/actuator/health/rediness'로 지정
  - Liveness Probe: Actuator '/actuator/health/liveness'로 지정
  - initialDelaySeconds, periodSeconds, failureThreshold를 Probe에 맞게 적절히 지정

### 배포 실행 및 결과 작성
- 배포 검증 결과
- 사전확인 실행
  - Cloud CLI 로그인 상태 확인 (`레지스트리유형`에 따라):

    | 레지스트리유형 | 확인 명령어 |
    |--------------|-----------|
    | DockerHub | `docker login` (이미 로그인 상태이면 생략) |
    | ECR | `aws sts get-caller-identity` |
    | ACR | `az account show` |
    | GCR | `gcloud auth list` |

  - K8s 클러스터 연결 확인:
    ```
    kubectl cluster-info
    ```
  - namespace 존재 확인
    ```
    kubectl get ns {네임스페이스}
    ```
- 매니페스트 적용 실행
  ```
  kubectl apply -f deployment/k8s/common
  kubectl apply -f deployment/k8s/{서비스명}
  ```
- 객체 생성 확인 실행

### Nginx Web Server Proxy 설정

K8s 매니페스트 배포 후, 외부 HTTPS 접근을 위해 Nginx Web Server의 프록시 설정을 수행한다.

> **참고**: Web Server 설치 가이드: `{PLUGIN_DIR}/resources/references/create-k8s.md` > [Web서버 설치](https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-k8s.md#web%EC%84%9C%EB%B2%84-%EC%84%A4%EC%B9%98)

#### 사전 조건

- **SSL 인증서가 이미 발급되고 Nginx SSL 설정이 완료된 상태**를 전제한다. 미완료 시 `create-k8s.md` > "SSL 설정" 섹션을 먼저 수행한다.
- 초기 설정 시 `proxy_pass`는 주석 처리되어 있고, `PROXY_TARGET` 변수도 주석 처리 상태이다 (`create-k8s.md` 참조).

#### 사전 확인

> **주의**: Agent(서브에이전트)는 `AskUserQuestion`을 사용할 수 없다. 사용자에게 묻는 모든 작업은 SKILL.md의 POST_ACTION(배포 스킬 레벨)에서 처리하고, 가이드는 이미 수집된 변수(`{WEB_SERVER_SSH_HOST}`, `{SSL_DOMAIN}`)만 참조한다.

아래 변수는 SKILL.md POST_ACTION에서 사용자에게 확인받아 `[실행정보]`에 추가된 상태를 전제한다:
- `{WEB_SERVER_SSH_HOST}`: `~/.ssh/config`에서 선택한 VM SSH Host alias (K8s 관리 VM과 동일)
- `{SSL_DOMAIN}`: VM의 SSL 인증서 도메인 (예: `mydomain.com`, `{ID}.{VM Public IP}.nip.io` 등)

#### 프록시 설정

Web Server VM에 SSH 접속하여 아래 절차를 수행한다:

1. **Ingress ADDRESS 확인** (로컬에서):
   ```bash
   kubectl get ing -n {K8S_NAMESPACE}
   ```
   출력의 ADDRESS 값을 `{INGRESS_ADDRESS}`로 사용한다.

2. **Nginx conf 재생성** (Web Server VM에서):
   `create-k8s.md`의 "SSL Proxying 테스트" 절차와 동일하게, `SERVER_NAME`과 `PROXY_TARGET` 변수를 설정한 후 `cat heredoc`으로 `/etc/nginx/sites-available/default` 전체를 재생성한다. 이때 `proxy_pass`를 주석 없이 활성화한다.
   ```bash
   SERVER_NAME="{SSL_DOMAIN}"
   PROXY_TARGET="http://{INGRESS_ADDRESS}"

   cat << EOF | sudo tee /etc/nginx/sites-available/default
   # 80 → 443 리다이렉트
   server {
     listen 80;
     server_name ${SERVER_NAME};
     return 301 https://\$host\$request_uri;
   }
   # 443 Proxy
   server {
     listen 443 ssl;
     server_name ${SERVER_NAME};
     ssl_certificate /etc/letsencrypt/live/${SERVER_NAME}/fullchain.pem;
     ssl_certificate_key /etc/letsencrypt/live/${SERVER_NAME}/privkey.pem;
     ssl_protocols TLSv1.2 TLSv1.3;
     ssl_ciphers HIGH:!aNULL:!MD5;
     root /var/www/html;
     index index.html;
     location / {
       proxy_pass ${PROXY_TARGET};
       proxy_ssl_verify off;
       proxy_buffer_size 64k;
       proxy_buffers 4 64k;
       proxy_busy_buffers_size 64k;
       proxy_set_header Host \$host;
       proxy_set_header X-Real-IP \$remote_addr;
       proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto \$scheme;
     }
   }
   EOF
   ```

3. **Nginx 재시작** (Web Server VM에서):
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

4. **접속 확인**: 브라우저에서 `https://{SSL_DOMAIN}` 접속하여 정상 동작 확인

## 출력 형식

`docs/deploy/deploy-k8s-back-result.md`에 아래 내용을 포함하여 작성:
- 배포 검증 결과 (체크리스트 항목별 확인 결과)
- 사전확인 실행 결과
- 매니페스트 적용 실행 결과
- 객체 생성 확인 결과

## 품질 기준

### 완료 체크리스트
- [ ] 객체이름 네이밍룰 준수 여부
- [ ] Redis Host명을 ClusterIP 타입의 Service 객체로 했는가?
  `kubectl get svc | grep redis` 명령으로 재확인
- [ ] Database Host명을 ClusterIP타입의 Service 객체로 했는가?
  `kubectl get svc | grep {서비스명}` 명령으로 재확인
- [ ] Secret 매니페스트에서 'data' 대신 'stringData'를 사용 했는가?
- [ ] JWT_SECRET을 openssl 명령으로 생성해서 지정했는가?
- [ ] 매니페스트 파일 안에 환경변수를 사용하지 않고 실제 값을 지정 했는가?
- [ ] Image Pull Secret에 USERNAME과 PASSWORD의 실제 값을 매니페스트에 지정 했는가?
- [ ] Image명이 '{REGISTRY_URL}/{서비스명}:latest' 형식인지 재확인
- [ ] Ingress host가 `api.{SSL_DOMAIN}` 형식인지 확인
- [ ] ingressClassName이 CLOUD에 맞게 설정되었는지 확인 (AWS: `alb`, Azure: `webapprouting.kubernetes.azure.com`, GCP: annotation `gce`)
- [ ] Ingress 매니페스트의 각 서비스 backend.service.port.number와 Service 매니페스트의 port가 "80"으로 동일한가?
- [ ] Ingress의 path는 각 서비스 별 Controller 클래스의 '@RequestMapping'과 클래스 내 메소드의 매핑정보를 읽어 지정했는가?
- [ ] 보안이 필요한 환경변수는 Secret 매니페스트로 지정했는가?
- [ ] REDIS_DATABASE는 각 서비스마다 다르게 지정했는가?
- [ ] ConfigMap과 Secret은 'env'대신에 'envFrom'을 사용하였는가?
- [ ] 컨테이너 실행 검증 완료 후 배포
- [ ] (중요) 컨테이너 실행 명령 매핑 테이블로 누락된 환경변수 체크
  - **필수**: `docs/deploy/run-container-back-result.md`의 `docker run` 명령에 지정된 **전체 환경변수를 빠짐없이 체크**
  - **체크 방법**:
    1. 각 서비스의 `docker run` 명령에서 `-e 환경변수명=값` 형태로 지정된 **모든** 환경변수 추출
    2. 추출된 환경변수 **전체**를 대상으로 매핑 테이블 작성 (일부만 하면 안됨)
    3. 서비스명 | 환경변수 | 지정 객체명 | 환경변수값 컬럼으로 **전체 환경변수** 체크
  - **매핑 테이블 예시** (전체 환경변수 기준):
    ```
    user-service | SERVER_PORT | cm-user-service | 8081
    user-service | DB_HOST | secret-user-service | user-db-service
    user-service | DB_PASSWORD | secret-user-service | tripgen_user_123
    user-service | REDIS_DATABASE | cm-user-service | 0
    user-service | JWT_SECRET | secret-common | (base64 encoded)
    user-service | CACHE_TTL | cm-user-service | 1800
    location-service | SERVER_PORT | cm-location-service | 8082
    location-service | GOOGLE_API_KEY | secret-location-service | (base64 encoded)
    location-service | REDIS_DATABASE | cm-location-service | 1
    ai-service | CLAUDE_API_KEY | secret-ai-service | (base64 encoded)
    ai-service | SERVER_PORT | cm-ai-service | 8084
    ... (docker run 명령의 모든 환경변수 나열)
    ```
  - **주의**: 일부 환경변수만 체크하면 누락 발생, 반드시 **docker run 명령 전체** 환경변수 대상으로 수행
  - 누락된 환경변수가 발견되면 해당 ConfigMap/Secret에 추가

## 주의사항
- Ingress Host는 `api.{SSL_DOMAIN}`을 사용할 것. 프론트엔드 Ingress host(`{SSL_DOMAIN}`)와 겹치지 않도록 주의.
- rewrite-target 관련 annotation 설정 절대 하지 말 것.
- Database는 공통 ConfigMap/Secret으로 작성 금지.
- 매니페스트 파일 안에 `${변수명}` 형태의 환경변수 사용 금지, 실제 값으로 지정할 것.
