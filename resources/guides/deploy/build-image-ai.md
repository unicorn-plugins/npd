# AI 서비스 컨테이너이미지 작성가이드

## 목적
AI 서비스(Python FastAPI 기반)의 컨테이너 이미지를 생성하고 이미지 레지스트리에 푸시한다.   
수행한 명령어를 포함하여 컨테이너 이미지 작성 과정을 결과 파일에 기록한다.

## 입력 (이전 단계 산출물)
| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 기술스택 정보 | `CLAUDE.md` | 베이스 이미지 결정 (Python 버전) |
| AI 서비스 소스 | `(런타임 결정)` | 빌드 대상 |

## 출력 (이 단계 산출물)
| 산출물 | 파일 경로 |
|--------|----------|
| 컨테이너 이미지 빌드 가이드 | `deployment/container/build-image.md` |
| AI 서비스 Dockerfile | `deployment/container/Dockerfile-ai` |

## 방법론

### 서비스명 확인

AI 서비스 디렉토리의 `pyproject.toml` 파일에서 서비스명을 확인한다.

```toml
[tool.poetry]
name = "ai-service"
```

`[tool.poetry] name` 필드값이 서비스명이다. `pyproject.toml`이 없는 경우 AI 서비스 디렉토리명을 서비스명으로 사용한다.

### 의존성 파일 확인

AI 서비스 디렉토리에서 의존성 관리 방식을 확인한다.

| 파일 | 의존성 도구 | 설치 방법 |
|------|-----------|----------|
| `pyproject.toml` (poetry) | poetry | `poetry install --no-root` |
| `requirements.txt` | pip | `pip install --no-cache-dir -r requirements.txt` |

`pyproject.toml`이 존재하면 poetry를 우선 사용한다.

### Dockerfile 생성

아래 내용으로 `deployment/container/Dockerfile-ai` 생성.

#### poetry 분기 (기본)
```dockerfile
# Build stage
FROM python:{version}-slim AS builder
ARG PROJECT_FOLDER
WORKDIR /app

COPY ${PROJECT_FOLDER}/pyproject.toml ${PROJECT_FOLDER}/poetry.lock* ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-dev

COPY ${PROJECT_FOLDER} .

# Run stage
FROM python:3.11-slim
ARG EXPORT_PORT=8000
ENV USERNAME=k8s
ENV APP_HOME=/home/${USERNAME}/app

RUN adduser --system --group ${USERNAME} && \
    mkdir -p ${APP_HOME} && \
    chown ${USERNAME}:${USERNAME} ${APP_HOME}

WORKDIR ${APP_HOME}
COPY --from=builder /usr/local/lib/python{version}/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app .
RUN chown -R ${USERNAME}:${USERNAME} ${APP_HOME}

USER ${USERNAME}

EXPOSE ${EXPORT_PORT}

# HEALTHCHECK: Docker 단독 실행 시 헬스 확인용. K8s 환경에서는 Probe가 우선함.
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

ENTRYPOINT [ "sh", "-c" ]
CMD ["uvicorn main:app --host 0.0.0.0 --port ${APP_PORT:-8000}"]
```

#### pip 분기 (pyproject.toml 없이 requirements.txt만 있는 경우)
```dockerfile
# Build stage에서 poetry 대신 pip 사용
COPY ${PROJECT_FOLDER}/requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Run stage에서 COPY 변경
COPY --from=builder /install /usr/local
```

> Python 버전은 CLAUDE.md의 `### develop > 기술스택 > Python` 버전을 참조하여 결정한다. 기술스택 정보가 없으면 기본값 `python:3.11-slim`을 사용한다.

**핵심 설계 결정**:
- `ENTRYPOINT ["sh", "-c"]` + `CMD ["uvicorn main:app --host 0.0.0.0 --port ${APP_PORT:-8000}"]`: 기존 백엔드 Dockerfile과 동일한 셸 확장 패턴. `APP_PORT` 환경변수를 런타임에 치환.
- `HEALTHCHECK`: `wget --spider http://localhost:8000/health` 사용. Docker 단독 실행 시 헬스 확인용.
- ML 모델 파일은 이미지에 포함하지 않음 (LLM API 호출 방식).

### 컨테이너 이미지 생성

> VM에서 실행한다.

아래 명령으로 서비스 빌드. shell 파일을 생성하지 말고 command로 수행.

```
DOCKER_FILE=deployment/container/Dockerfile-ai
service={서비스명}

docker build \
  --platform linux/amd64 \
  --build-arg PROJECT_FOLDER="{ai-서비스-디렉토리}" \
  --build-arg EXPORT_PORT="8000" \
  -f ${DOCKER_FILE} \
  -t ${service}:latest .
```

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
`deployment/container/build-image.md` 파일에 수행한 명령어를 포함하여 컨테이너 이미지 작성 과정을 단계별로 기록한다.

## 품질 기준
- [ ] Dockerfile이 멀티스테이지 빌드로 구성되어 있는가?
- [ ] 빌드 스테이지에서 poetry(또는 pip)로 의존성을 설치하는가?
- [ ] 비루트 사용자(`k8s`)로 실행하도록 설정되어 있는가?
- [ ] ENTRYPOINT+CMD 셸 확장 패턴이 적용되었는가? (`ENTRYPOINT ["sh", "-c"]` + `CMD ["uvicorn ..."]`)
- [ ] HEALTHCHECK가 포함되었는가? (`wget --spider http://localhost:8000/health`)
- [ ] 이미지 빌드가 성공했는가?
- [ ] 레지스트리 로그인이 성공했는가?
- [ ] (ECR/GCR) 리포지토리 존재 확인 및 자동 생성이 정상 수행되었는가?
- [ ] 이미지가 레지스트리에 푸시되었는가?
- [ ] 빌드 실패 상태로 다음 단계 미진행

## 트러블슈팅
| 증상 | 원인 | 해결 |
|------|------|------|
| `poetry.lock not found` | poetry.lock 미생성 | `poetry lock` 실행 후 재빌드 |
| `pip install` 실패 | 의존성 충돌 | `pip install --no-cache-dir` 확인, 버전 호환성 점검 |
| `no match for platform` | 플랫폼 불일치 | `--platform linux/amd64` 확인 |
| `COPY failed: file not found` | PROJECT_FOLDER 경로 오류 | AI 서비스 디렉토리 경로 확인 |
| 이미지 크기 과다 (>1GB) | `.dockerignore` 미설정 또는 불필요 파일 포함 | `.dockerignore` 확인, `.venv/` 제외 확인 |
| `ModuleNotFoundError` at runtime | 의존성 누락 | pyproject.toml/requirements.txt 확인, 빌드 스테이지에서 설치 여부 점검 |
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
- Dockerfile의 ARG 이름(`PROJECT_FOLDER`, `EXPORT_PORT`)은 프론트엔드 가이드와 유사한 패턴
- 이미지 태그는 로컬 빌드 시 `:latest`를 사용. CI/CD 환경에서의 태그 전략은 CI/CD 파이프라인 가이드에서 관리
- ML 모델 파일은 이미지에 포함하지 않음 (LLM API 호출 방식). 모델 파일이 존재하는 경우 `.dockerignore`로 제외
- VM에서 빌드 시 Docker가 설치되어 있어야 한다 (Python 설치는 불필요)
- VM 최소 스펙: 4GB RAM 이상 권장 (메모리 부족 시 OOM으로 SSH 끊김 발생)
