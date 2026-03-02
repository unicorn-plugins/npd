# 프론트엔드 배포 가이드

## 목적
프론트엔드 서비스를 쿠버네티스에 배포하기 위한 매니페스트 파일 작성.
매니페스트 파일을 작성하고 실제 배포까지 수행.
수행한 명령어와 결과를 포함하여 배포 결과 레포트 생성.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 컨테이너 실행 결과 | `docs/deploy/run-container-front-result.md` | 이미지명, 포트 정보 추출 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 배포 결과 | `docs/deploy/deploy-k8s-front-result.md` |
| 프론트엔드 매니페스트 파일 | `deployment/k8s/{서비스명}/*` |

## 방법론

### 실행정보 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {ROOT}: 대표 시스템명 (CLAUDE.md 참조)
- {레지스트리유형}: 레지스트리 유형 (DockerHub / ECR / ACR / GCR)
- {REGISTRY_URL}: 이미지 레지스트리 URL
- {네임스페이스}: 배포할 네임스페이스
- {서비스 리소스}: 서비스별 파드수, CPU, 메모리 설정
- {SSL_DOMAIN}: Web Server의 SSL 도메인 (예: `mydomain.com`, `{ID}.{VM Public IP}.nip.io` 등)

> `{REGISTRY_URL}`은 SKILL.md의 `[실행정보]` 조립 규칙에서 레지스트리유형별로 자동 결정된다.

예시) ACR 환경
```
[실행정보]
- 시스템명: tripgen
- 레지스트리유형: ACR
- REGISTRY_URL: acrdigitalgarage01.azurecr.io/tripgen
- 네임스페이스: tripgen
- 서비스 리소스:
  - tripgen-front: 파드수=2, CPU=250m/500m, 메모리=128Mi/256Mi
- SSL_DOMAIN: tripgen.20.214.196.128.nip.io
```

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

### 매니페스트 작성 주의사항
- namespace는 명시: {네임스페이스}값 이용
- 객체이름 네이밍룰
  - Ingress: {서비스명}
  - ConfigMap: cm-{서비스명}
  - Service: {서비스명}
  - Secret: {서비스명}
  - Deployment: {서비스명}

### 매니페스트 작성 (`deployment/k8s/{서비스명}` 디렉토리 하위)

**ConfigMap 매니페스트 작성**
- `docs/deploy/run-container-front-result.md`의 `runtime-env.js 설정` 섹션과 동일한 내용으로 구성
- 파일명 `runtime-env.js`를 키로 하고 파일 내용을 값으로 하는 ConfigMap 매니페스트 작성
  단, 각 서비스별 HOST 값을 `https://api.{SSL_DOMAIN}`으로 변경
  예시)
  ```
  MEMBER_HOST: 'http://member-service:8081'
  -> MEMBER_HOST: 'https://api.tripgen.20.214.196.128.nip.io'
  ```

**Ingress 매니페스트 작성**
- `ingressClassName` 또는 annotation은 CLOUD에 따라 설정:

  | CLOUD | ingressClassName | annotation | 비고 |
  |-------|-----------------|------------|------|
  | AWS | `alb` | - | IngressClass 수동 생성 필요 (`create-k8s.md` 참조) |
  | Azure | `webapprouting.kubernetes.azure.com` | - | AKS Automatic에 자동 내장 |
  | GCP | (지정하지 않음) | `kubernetes.io/ingress.class: "gce"` | GKE Autopilot에 자동 내장 |

- host: {SSL_DOMAIN}
  > `{SSL_DOMAIN}`은 Web Server VM의 SSL 인증서 도메인이다 (예: `mydomain.com`, `{ID}.{VM Public IP}.nip.io` 등)
  > **주의**: host를 지정하지 않거나 다른 Ingress와 동일한 host를 사용하면 충돌이 발생하여 Ingress 객체가 생성되지 않을 수 있다. 프론트엔드 Ingress host는 반드시 Web Server의 `server_name`과 동일한 `{SSL_DOMAIN}` 값을 사용해야 한다.
  **잘못된 예**: tripgen.임의IP.nip.io ❌
  **올바른 예**: tripgen.20.214.196.128.nip.io ✅
- path: '/'
- pathType: Prefix
- backend.service.name: {서비스명}
- backend.service.port.number: 8080

**Service 매니페스트 작성**
- name: {서비스명}
- port: 8080
- targetPort: 8080
- type: ClusterIP

**Deployment 매니페스트 작성**
- name: {서비스명}
- replicas: {서비스 리소스}에서 해당 서비스의 파드수
- ImagePullPolicy: Always
- ImagePullSecrets: {ROOT}
- image: {REGISTRY_URL}/{서비스명}:latest
- resources: {서비스 리소스}에서 해당 서비스의 CPU/메모리 값 적용
- Probe:
  - Startup Probe: '/health'로 지정
  - Readiness Probe: '/health'로 지정
  - Liveness Probe: Actuator '/health'로 지정
  - initialDelaySeconds, periodSeconds, failureThreshold를 Probe에 맞게 적절히 지정
- volume mount
  - ConfigMap cm-{서비스명}를 '/usr/share/nginx/html/runtime-env.js'로 마운트

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
  kubectl apply -f deployment/k8s/{서비스명}
  ```
- 객체 생성 확인 실행

## 출력 형식

`docs/deploy/deploy-k8s-front-result.md`에 아래 내용을 포함하여 작성:
- 배포 검증 결과 (체크리스트 항목별 확인 결과)
- 사전확인 실행 결과
- 매니페스트 적용 실행 결과
- 객체 생성 확인 결과

## 품질 기준

### 완료 체크리스트
- [ ] 객체이름 네이밍룰 준수 여부
- [ ] Ingress host가 `{SSL_DOMAIN}` 형식인지 확인
- [ ] ingressClassName이 CLOUD에 맞게 설정되었는지 확인 (AWS: `alb`, Azure: `webapprouting.kubernetes.azure.com`, GCP: annotation `gce`)
- [ ] Ingress 매니페스트의 서비스 backend.service.port.number와 Service 매니페스트의 port가 "8080"으로 동일한가?
- [ ] Service 매니페스트의 targetPort가 8080인가?
- [ ] Image명이 '{REGISTRY_URL}/{서비스명}:latest' 형식인지 재확인
- [ ] ConfigMap 'cm-{서비스명}'의 data 내용 확인
  - key는 runtime-env.js인가?
  - value가 `docs/deploy/run-container-front-result.md`의 `runtime-env.js 설정` 섹션과 동일한 구조인가?
  - value에 각 서비스별 HOST가 `https://api.{SSL_DOMAIN}`으로 변경되었는가?

## 주의사항
- Ingress Host는 `{SSL_DOMAIN}`을 사용할 것. 백엔드 Ingress host(`api.{SSL_DOMAIN}`)와 겹치지 않도록 주의.
- ConfigMap의 백엔드 API 주소는 반드시 `https://api.{SSL_DOMAIN}`으로 변경할 것. localhost 그대로 남기면 안됨.
