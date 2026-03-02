# AI 서비스 배포 가이드

## 목적
AI 서비스(Python FastAPI 기반)를 쿠버네티스에 배포하기 위한 매니페스트 파일 작성.
매니페스트 파일을 작성하고 실제 배포까지 수행.
수행한 명령어와 결과를 포함하여 배포 결과 레포트 생성.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 컨테이너 실행 결과 | `docs/deploy/run-container-ai-result.md` | 이미지명, 환경변수, 포트 정보 추출 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 배포 결과 | `docs/deploy/deploy-k8s-ai-result.md` |
| AI 서비스 매니페스트 파일 | `deployment/k8s/{서비스명}/*` |

## 방법론

### 실행정보 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {레지스트리유형}: 레지스트리 유형 (DockerHub / ECR / ACR / GCR)
- {REGISTRY_URL}: 이미지 레지스트리 URL
- {네임스페이스}: 배포할 네임스페이스
- {서비스 리소스}: 서비스별 파드수, CPU, 메모리 설정

> `{REGISTRY_URL}`은 SKILL.md의 `[실행정보]` 조립 규칙에서 레지스트리유형별로 자동 결정된다.

예시) ACR 환경
```
[실행정보]
- 레지스트리유형: ACR
- REGISTRY_URL: acrdigitalgarage01.azurecr.io/tripgen
- 네임스페이스: tripgen
- 서비스 리소스:
  - ai-service: 파드수=1, CPU=500m/2000m, 메모리=512Mi/2048Mi
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
- 컨테이너 실행 결과(`docs/deploy/run-container-ai-result.md`)의 `docker run` 명령에서 환경변수를 추출.
- `docker run -e KEY=VALUE` 패턴에서 환경변수명과 값을 추출.
- 보안이 필요한 환경변수(API 키, 암호 등)는 Secret 매니페스트로 작성: secret-{서비스명}.yaml
- 그 외 일반 환경변수 매니페스트 작성: cm-{서비스명}.yaml
- cm-common.yaml, secret-common.yaml에 있는 공통 환경변수는 중복 작성 금지

**Service 매니페스트 작성**
- name: {서비스명}
- port: 80
- targetPort: 컨테이너 실행 명령의 APP_PORT값 (기본값 8000)
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
  - Startup Probe: '/health'로 지정
  - Readiness Probe: '/health'로 지정
  - Liveness Probe: '/health'로 지정
  - initialDelaySeconds, periodSeconds, failureThreshold를 Probe에 맞게 적절히 지정

### Ingress 규칙 추가
- 기존 백엔드 Ingress에 AI 서비스 path 추가
- AI 서비스의 FastAPI router prefix를 확인하여 path 지정
- pathType: Prefix
- backend.service.name: {서비스명}
- backend.service.port.number: 80
- **중요**: rewrite-target 관련 annotation 설정 절대 하지 말것.

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

`docs/deploy/deploy-k8s-ai-result.md`에 아래 내용을 포함하여 작성:
- 배포 검증 결과 (체크리스트 항목별 확인 결과)
- 사전확인 실행 결과
- 매니페스트 적용 실행 결과
- 객체 생성 확인 결과

## 품질 기준

### 완료 체크리스트
- [ ] 객체이름 네이밍룰 준수 여부
- [ ] Secret 매니페스트에서 'data' 대신 'stringData'를 사용 했는가?
- [ ] 매니페스트 파일 안에 환경변수를 사용하지 않고 실제 값을 지정 했는가?
- [ ] Image명이 '{REGISTRY_URL}/{서비스명}:latest' 형식인지 재확인
- [ ] Probe endpoint가 '/health'로 지정되었는가? (Actuator 아님)
- [ ] 보안이 필요한 환경변수(API 키 등)는 Secret 매니페스트로 지정했는가?
- [ ] ConfigMap과 Secret은 'env'대신에 'envFrom'을 사용하였는가?
- [ ] 컨테이너 실행 검증 완료 후 배포
- [ ] (중요) 컨테이너 실행 명령 매핑 테이블로 누락된 환경변수 체크
  - **필수**: `docs/deploy/run-container-ai-result.md`의 `docker run` 명령에 지정된 **전체 환경변수를 빠짐없이 체크**
  - **체크 방법**:
    1. `docs/deploy/run-container-ai-result.md`의 `docker run -e` 옵션에서 **모든** 환경변수 추출
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
    ... (docker run 명령의 모든 환경변수 나열)
    ```
  - 누락된 환경변수가 발견되면 해당 ConfigMap/Secret에 추가

## 주의사항
- rewrite-target 관련 annotation 설정 절대 하지 말 것.
- 매니페스트 파일 안에 `${변수명}` 형태의 환경변수 사용 금지, 실제 값으로 지정할 것.
- Probe endpoint는 반드시 `/health` 사용 (Spring Boot Actuator의 `/actuator/health`가 아님).
- 환경변수는 `docs/deploy/run-container-ai-result.md`의 `docker run` 명령에서 추출.
- AI 서비스는 backend-to-backend 내부 서비스이므로 별도 CORS 설정 불필요.
