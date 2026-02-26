# AI 서비스 배포 가이드 (Minikube)

## 목적
AI 서비스(Python FastAPI 기반)를 Minikube 쿠버네티스에 배포하기 위한 매니페스트 파일 작성.
매니페스트 파일 작성까지만 하고 실제 배포는 수행방법만 가이드.
수행한 명령어를 포함하여 배포 가이드 레포트 생성.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| Docker 이미지 | `(런타임 결정)` | 배포 대상 이미지 |
| 서비스 포트 정보 | `(런타임 결정)` | Service/Ingress 설정 |
| Minikube/VM 정보 | `(런타임 결정)` | SSH 터널링 대상 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 배포방법 가이드 | `deployment/k8s/deploy-k8s-guide.md` |
| AI 서비스 매니페스트 파일 | `deployment/k8s/{서비스명}/*` |

## 방법론

### 실행정보 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {IMG_REG}: 컨테이너 이미지 레지스트리 주소
- {IMG_ORG}: 컨테이너 이미지 Organization 주소
- {BACKEND_HOST}: Backend 게이트웨이의 Ingress Host 주소
- {FRONTEND_HOST}: 프론트엔드 Ingress Host 주소
- {네임스페이스}: 배포할 네임스페이스
- {파드수}: 생성할 파드수
- {리소스(CPU)}: 요청값/최대값
- {리소스(메모리)}: 요청값/최대값

예시)
```
[실행정보]
- IMG_REG: docker.io
- IMG_ORG: hiondal
- BACKEND_HOST: tripgen-api.72.155.72.236.nip.io
- FRONTEND_HOST: tripgen.72.155.72.236.nip.io
- 네임스페이스: tripgen
- 파드수: 1
- 리소스(CPU): 256m/1024m
- 리소스(메모리): 256Mi/1024Mi
```

### 서비스명 확인
AI 서비스 디렉토리의 `pyproject.toml` 파일에서 서비스명을 확인한다.

```toml
[tool.poetry]
name = "ai-service"
```

`[tool.poetry] name` 필드값이 서비스명이다. `pyproject.toml`이 없는 경우 AI 서비스 디렉토리명을 서비스명으로 사용한다.

### 매니페스트 작성 주의사항
- namespace는 명시: {네임스페이스}값 이용
- 매니페스트 파일 안에 환경변수를 사용하지 말고 실제 값을 지정
  예) host: "tripgen.${INGRESS_IP}.nip.io" => host: "tripgen.4.1.2.3.nip.io"
- Secret 매니페스트에서 'data' 대신 'stringData'를 사용
- 객체이름 네이밍룰
  - 서비스별 ConfigMap: cm-{서비스명}
  - 서비스별 Secret: secret-{서비스명}
  - Service: {서비스명}
  - Deployment: {서비스명}

### AI 서비스 매니페스트 작성 (`deployment/k8s/{서비스명}/` 디렉토리 하위)

**ConfigMap과 Secret 매니페스트 작성**
- 프로젝트 루트 `.env.example`의 AI 서비스 섹션에서 환경변수를 추출.
- `^[A-Z_]+=` 패턴에 매칭되는 라인에서 환경변수를 추출하고, `#`으로 시작하는 주석 라인은 제외.
- 주석 처리된(`#` 접두사) 환경변수는 선택적이므로, 실제 사용 여부를 확인 후 필요한 것만 포함.
- 보안이 필요한 환경변수(API 키, 암호 등)는 Secret 매니페스트로 작성: secret-{서비스명}.yaml
- 그 외 일반 환경변수 매니페스트 작성: cm-{서비스명}.yaml
- cm-common.yaml, secret-common.yaml에 있는 공통 환경변수는 중복 작성 금지

**Service 매니페스트 작성**
- name: {서비스명}
- port: 80
- targetPort: `.env.example`의 APP_PORT값 (기본값 8000)
- type: ClusterIP

**Deployment 매니페스트 작성**
- name: {서비스명}
- replicas: {파드수}
- ImagePullPolicy: Always
- ImagePullSecrets: {ROOT}
- image: {IMG_REG}/{IMG_ORG}/{서비스명}:latest
- ConfigMap과 Secret은 'env'대신에 'envFrom'을 사용하여 지정
- envFrom:
  - configMapRef: 공통 ConfigMap 'cm-common'과 각 서비스 ConfigMap 'cm-{서비스명}'을 지정
  - secretRef: 공통 Secret 'secret-common'과 각 서비스 Secret 'secret-{서비스명}'을 지정
- resources:
  - {리소스(CPU)}: 요청값/최대값
  - {리소스(메모리)}: 요청값/최대값
- Probe:
  - Startup Probe: '/health'로 지정
  - Readiness Probe: '/health'로 지정
  - Liveness Probe: '/health'로 지정
  - initialDelaySeconds, periodSeconds, failureThreshold를 Probe에 맞게 적절히 지정

### Ingress 규칙 추가
- 기존 백엔드 Ingress에 AI 서비스 path 추가
- AI 서비스의 FastAPI router prefix를 확인하여 path 지정
- ingressClassName: nginx
- host: {BACKEND_HOST}
- pathType: Prefix
- backend.service.name: {서비스명}
- backend.service.port.number: 80
- **중요**: annotation에 'nginx.ingress.kubernetes.io/rewrite-target' 설정 절대 하지 말것.

### 배포 가이드 작성
- 배포가이드 검증 결과
- 사전확인 방법 가이드
  - namespace 존재 확인
    ```
    kubectl get ns {네임스페이스}
    ```
- 매니페스트 적용 가이드
  ```
  kubectl apply -f deployment/k8s -R
  ```
- 객체 생성 확인 가이드

## 출력 형식

`deployment/k8s/deploy-k8s-guide.md`에 아래 내용을 포함하여 작성:
- 배포가이드 검증 결과 (체크리스트 항목별 확인 결과)
- 사전확인 명령어
- 매니페스트 적용 명령어
- 객체 생성 확인 명령어

## 품질 기준

### 완료 체크리스트
- [ ] SSH 터널링 설정 포함
- [ ] 객체이름 네이밍룰 준수 여부
- [ ] Secret 매니페스트에서 'data' 대신 'stringData'를 사용 했는가?
- [ ] 매니페스트 파일 안에 환경변수를 사용하지 않고 실제 값을 지정 했는가?
- [ ] Image명이 '{IMG_REG}/{IMG_ORG}/{서비스명}:latest' 형식인지 재확인
- [ ] Probe endpoint가 '/health'로 지정되었는가? (Actuator 아님)
- [ ] 보안이 필요한 환경변수(API 키 등)는 Secret 매니페스트로 지정했는가?
- [ ] ConfigMap과 Secret은 'env'대신에 'envFrom'을 사용하였는가?
- [ ] 컨테이너 실행 검증 완료 후 배포
- [ ] (중요) .env.example 매핑 테이블로 누락된 환경변수 체크
  - **필수**: `.env.example` 파일에 정의된 **전체 환경변수를 빠짐없이 체크**
  - **체크 방법**:
    1. `.env.example` 파일에서 `^[A-Z_]+=` 패턴 라인의 **모든** 환경변수 추출
    2. 추출된 환경변수 **전체**를 대상으로 매핑 테이블 작성
    3. 서비스명 | 환경변수 | 지정 객체명 | 환경변수값 컬럼으로 **전체 환경변수** 체크
  - **매핑 테이블 예시**:
    ```
    ai-service | APP_ENV | cm-ai-service | production
    ai-service | APP_PORT | cm-ai-service | 8000
    ai-service | LOG_LEVEL | cm-ai-service | INFO
    ai-service | LLM_PROVIDER | cm-ai-service | openai
    ai-service | LLM_MODEL_NAME | cm-ai-service | gpt-4o
    ai-service | OPENAI_API_KEY | secret-ai-service | (실제값)
    ... (.env.example의 모든 환경변수 나열)
    ```
  - 누락된 환경변수가 발견되면 해당 ConfigMap/Secret에 추가

## 주의사항
- annotation에 `nginx.ingress.kubernetes.io/rewrite-target` 설정 절대 하지 말 것.
- 매니페스트 파일 안에 `${변수명}` 형태의 환경변수 사용 금지, 실제 값으로 지정할 것.
- Probe endpoint는 반드시 `/health` 사용 (Spring Boot Actuator의 `/actuator/health`가 아님).
- 환경변수는 `.env.example`에서 추출 (`.run/*.run.xml`은 Java/IntelliJ 전용이므로 사용하지 않음).
- Minikube 환경에서는 SSH 터널링 설정이 필요하므로 배포 가이드에 반드시 포함할 것.
- AI 서비스는 backend-to-backend 내부 서비스이므로 별도 CORS 설정 불필요.
