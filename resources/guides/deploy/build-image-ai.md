# AI 서비스 컨테이너이미지 작성가이드

## 목적
AI 서비스(Python FastAPI 기반)의 컨테이너 이미지를 생성하고, 실제 빌드 수행 및 검증까지 완료한다. 수행한 명령어를 포함하여 컨테이너 이미지 작성 과정을 결과 파일에 기록한다.

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
| .dockerignore | `.dockerignore` (기존 파일에 AI 서비스 항목 추가) |

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

### .dockerignore 항목 추가

기존 `.dockerignore` 파일에 아래 AI 서비스 관련 항목을 추가한다 (이미 있는 항목은 중복 추가하지 않음).
```
.venv/
__pycache__/
.pytest_cache/
chroma_db/
*.pyc
.env*
```

> `deployment/container/`는 Dockerfile이 위치하는 경로이므로 제외하지 않는다.

### Dockerfile 생성

아래 내용으로 `deployment/container/Dockerfile-ai` 생성.

#### poetry 분기 (기본)
```dockerfile
# Build stage
FROM python:3.11-slim AS builder
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
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
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

> Python 버전은 CLAUDE.md의 기술스택 정보에 따라 변경할 수 있다 (예: `python:3.12-slim`).

**핵심 설계 결정**:
- `ENTRYPOINT ["sh", "-c"]` + `CMD ["uvicorn main:app --host 0.0.0.0 --port ${APP_PORT:-8000}"]`: 기존 백엔드 Dockerfile과 동일한 셸 확장 패턴. `APP_PORT` 환경변수를 런타임에 치환.
- `HEALTHCHECK`: `wget --spider http://localhost:8000/health` 사용. Docker 단독 실행 시 헬스 확인용.
- ML 모델 파일은 이미지에 포함하지 않음 (LLM API 호출 방식).

### 컨테이너 이미지 생성

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

### 생성된 이미지 검증

#### 1. 이미지 존재 및 크기 확인
```
docker images | grep {서비스명}
```
> Python FastAPI 이미지는 일반적으로 200~500MB 범위가 적정. 1GB 초과 시 .dockerignore 및 의존성을 점검한다.

#### 2. 컨테이너 기동 테스트 (선택)
```
docker run --rm -d --name {서비스명}-test -p 0:8000 {서비스명}:latest
# 10초 대기 후 컨테이너 상태 확인
sleep 10
docker ps | grep {서비스명}-test
# 헬스 확인
wget -qO- http://localhost:8000/health
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
- [ ] `.dockerignore` 파일에 AI 서비스 관련 항목(`.venv/`, `__pycache__/`, `.pytest_cache/`, `chroma_db/`, `.env*`)이 포함되었는가?
- [ ] Dockerfile이 멀티스테이지 빌드로 구성되어 있는가?
- [ ] 빌드 스테이지에서 poetry(또는 pip)로 의존성을 설치하는가?
- [ ] 비루트 사용자(`k8s`)로 실행하도록 설정되어 있는가?
- [ ] ENTRYPOINT+CMD 셸 확장 패턴이 적용되었는가? (`ENTRYPOINT ["sh", "-c"]` + `CMD ["uvicorn ..."]`)
- [ ] HEALTHCHECK가 포함되었는가? (`wget --spider http://localhost:8000/health`)
- [ ] 이미지 빌드가 성공했는가?
- [ ] 이미지 크기가 합리적인가? (Python: 200~500MB)
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

## 주의사항
- shell 파일을 생성하지 말고 command로 직접 수행
- 빌드 실패 시 반드시 원인을 파악하고 해결한 후 다음 단계 진행
- Dockerfile의 ARG 이름(`PROJECT_FOLDER`, `EXPORT_PORT`)은 프론트엔드 가이드와 유사한 패턴
- 이미지 태그는 로컬 빌드 시 `:latest`를 사용. CI/CD 환경에서의 태그 전략은 CI/CD 파이프라인 가이드에서 관리
- ML 모델 파일은 이미지에 포함하지 않음 (LLM API 호출 방식). 모델 파일이 존재하는 경우 `.dockerignore`로 제외
