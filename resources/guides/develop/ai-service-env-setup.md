# AI 서비스 프로젝트 초기화 가이드

## 목적

종합 개발 계획서를 기반으로 Python/FastAPI 프로젝트를 초기화하고, Router→Service→Repository 계층 구조와 LangChain 패턴이 적용된 기본 골격을 설정한다. 이 단계에서는 비즈니스 로직을 구현하지 않으며, 실행 가능한 프로젝트 구조 확립에 집중한다.

---

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 종합 개발 계획서 | `docs/develop/dev-plan.md` | AI 서비스 범위·엔드포인트(섹션 4) |
| AI 서비스 구조 정보 | `docs/develop/dev-plan.md` 섹션 10-4 | 주요 클래스, 의존성 방향, LLM 제공자, 포트 |
| 기술스택 정보 | `docs/develop/dev-plan.md` 섹션 10-5 | Python 버전 |

---

## 출력 (이 단계 산출물)

| 산출물 | 경로 | 설명 |
|--------|------|------|
| 프로젝트 골격 | `{service-name}/` | 설계서 지정 디렉토리 구조 |
| 의존성 파일 | `pyproject.toml` 또는 `requirements.txt` | 런타임·개발 의존성 |
| FastAPI 앱 | `main.py`, `routers/`, `config.py` | 앱 진입점, 라우터, 설정 |
| 환경변수 템플릿 | 루트 `.env.example` AI 서비스 섹션 | LLM API 키 등 환경변수 목록 |
| Dockerfile | `Dockerfile` | 로컬 개발용 컨테이너 이미지 |
| Compose 등록 | `docker-compose.yml` | `ai` 프로파일에 서비스 추가 |

---

## SKIP 조건

다음 두 조건 중 하나에 해당하면 이 단계 전체를 건너뛴다.

| 순서 | 조건 | 판단 방법 |
|:----:|------|---------|
| 1 | `docs/design/ai-service-design.md` 파일이 존재하지 않음 | 파일 존재 여부 확인 |
| 2 | 파일은 존재하나 결론이 "AI 서비스 불필요", "해당 없음", "AI 기능 미사용" 중 하나 | 설계서 서두·결론 섹션에서 해당 키워드 검색 |

---

## 방법론

### 1단계: 설계서 분석

설계서에서 아래 항목을 먼저 확인하고 메모한다.

```
[확인 항목]
- service-name: 서비스 디렉토리명 (예: ai-service, recommendation-service)
- Python 버전: `dev-plan.md`의 '10-5. 기술스택 정보' 기준
- 포트: 설계서 또는 아키텍처 명세 기준 (기본 8000)
- LLM 제공자: OpenAI / Anthropic / Google 등
- RAG 여부: rag/ 디렉토리 필요 여부
- Function Calling 여부: tools/ 디렉토리 필요 여부
- MAS 여부: agents/ 디렉토리 필요 여부
- 추가 클라이언트: 벡터 DB, 외부 API 등
```

### 2단계: 프로젝트 디렉토리 생성

설계서에서 확인한 `service-name`으로 루트 디렉토리를 생성한다.

```bash
# 프로젝트 루트에서 실행
mkdir -p {service-name}
cd {service-name}
```

**기본 디렉토리 구조** (설계서 2.7절 구조 기준):

```
{service-name}/
├── main.py                    # FastAPI 앱 진입점
├── config.py                  # 환경변수 기반 설정 (Pydantic Settings)
├── Dockerfile                 # 로컬 개발용 컨테이너 이미지
├── pyproject.toml             # 의존성 및 프로젝트 메타데이터 (poetry 사용 시)
├── requirements.txt           # 의존성 목록 (pip 사용 시)
├── routers/                   # API 라우터 (엔드포인트 정의)
│   ├── __init__.py
│   └── health.py              # /health 엔드포인트
├── services/                  # 비즈니스 로직 (스텁)
│   └── __init__.py
├── clients/                   # LLM·외부 API 클라이언트 (스텁)
│   └── __init__.py
├── models/                    # Pydantic 요청/응답 모델
│   └── __init__.py
├── prompts/                   # 프롬프트 템플릿 로더 (스텁)
│   └── __init__.py
├── cache/                     # 응답 캐시 (스텁)
│   └── __init__.py
└── fallback/                  # 폴백 로직 (스텁)
    └── __init__.py
```

**설계서에 명시된 경우만 추가하는 디렉토리**:

```
├── rag/                       # RAG 파이프라인 (설계서 6절 해당 시)
│   ├── __init__.py
│   ├── indexer.py
│   ├── retriever.py
│   └── embeddings.py
├── tools/                     # Function Calling 도구 정의 (설계서 7절 해당 시)
│   └── __init__.py
└── agents/                    # MAS 에이전트 정의 (설계서 7절 MAS 해당 시)
    └── __init__.py
```

### 3단계: Python 가상환경 설정

**poetry 사용 (권장)**:

```bash
# pyproject.toml 초기화
poetry init --no-interaction \
  --name "{service-name}" \
  --python "^{python-version}"
```

**pip + venv 사용 (대안)**:

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate        # Windows
```

### 4단계: 의존성 정의 및 설치

설계서에서 확인한 LLM 제공자와 옵션에 따라 의존성을 선택한다.

**기본 의존성 (모든 AI 서비스 공통)**:

```toml
# pyproject.toml — [tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.115"
uvicorn = {extras = ["standard"], version = "^0.34"}
pydantic = "^2.10"
pydantic-settings = "^2.7"
httpx = "^0.28"
python-dotenv = "^1.0"
```

**LLM 제공자별 의존성 (설계서 기준으로 선택)**:

| 제공자 | 패키지 | LangChain 통합 패키지 |
|--------|--------|----------------------|
| OpenAI | `openai` | `langchain-openai` |
| Anthropic | `anthropic` | `langchain-anthropic` |
| Google Gemini | `google-generativeai` | `langchain-google-genai` |
| Azure OpenAI | `openai` | `langchain-openai` |

**LangChain 기반 의존성**:

```toml
langchain = "^0.3"
langchain-core = "^0.3"
langchain-openai = "^0.3"      # 제공자에 맞춰 교체
langgraph = "^0.2"             # MAS/복합 워크플로우 해당 시
langsmith = "^0.2"             # LangSmith 모니터링 사용 시
```

**RAG 의존성 (설계서 6절 해당 시)**:

```toml
chromadb = "^0.6"              # 벡터 DB (설계서 지정 DB로 교체)
tiktoken = "^0.9"              # 토큰 카운터
```

**개발 의존성**:

```toml
# [tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.25"
httpx = "^0.28"                # TestClient용 (기본 의존성과 공유)
```

**설치 실행**:

```bash
# poetry
poetry install

# pip
pip install -r requirements.txt
```

### 5단계: 기본 설정 파일 작성

**루트 `.env.example`에 AI 서비스 섹션 추가**:

프로젝트 루트의 `.env.example` 파일에 아래 AI 서비스 관련 환경변수를 추가한다 (이미 `backing-service-setup.md`에서 주석 처리된 섹션이 있으면 주석을 해제하고 값을 채운다):

```dotenv
# ===========================
# AI Service ({service-name})
# ===========================
APP_ENV=development
APP_PORT=8000
LOG_LEVEL=INFO

# LLM 설정 (init_chat_model에서 사용)
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-4o
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# LLM API (설계서 LLM 제공자에 맞춰 항목 조정)
OPENAI_API_KEY=your-openai-api-key-here
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
# AZURE_OPENAI_API_KEY=your-azure-key-here
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# 웹검색 Tool (해당 시)
# TAVILY_API_KEY=your-tavily-api-key-here

# LangSmith (선택)
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=your-langsmith-key-here
# LANGCHAIN_PROJECT={service-name}

# RAG / 벡터 DB (해당 시)
# VECTOR_DB_URL=http://localhost:6333
```

**`config.py`**:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 앱 설정
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    # LLM 설정 (init_chat_model에서 사용)
    llm_provider: str = "openai"
    llm_model_name: str = "gpt-4o"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # LLM API (설계서 LLM 제공자에 맞춰 필드 조정)
    openai_api_key: str = ""
    # anthropic_api_key: str = ""

    # 웹검색 Tool (해당 시)
    tavily_api_key: str = ""

    # LangSmith (선택)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = ""


settings = Settings()
```

**`.gitignore`에 추가**:

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

### 6단계: FastAPI 앱 및 헬스체크 엔드포인트 작성

**`routers/health.py`**:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}
```

**`main.py`**:

```python
from fastapi import FastAPI

from config import settings
from routers.health import router as health_router

app = FastAPI(
    title="{service-name}",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
)

# 라우터 등록
app.include_router(health_router)

# TODO: 설계서 API 명세(ai-*-api.yaml)를 기반으로 라우터 추가
# from routers.{feature} import router as {feature}_router
# app.include_router({feature}_router, prefix="/api/v1")
```

헬스체크 응답 확인:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
curl http://localhost:8000/health
# 기대 응답: {"status":"ok"}
```

### 7단계: Dockerfile 작성 및 docker-compose ai 프로파일 등록

**`Dockerfile`** (로컬 개발용):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 파일 복사 및 설치
COPY pyproject.toml ./
# poetry 사용 시
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root

# pip 사용 시 (위 RUN 블록 대신)
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`docker-compose.yml`에 ai 프로파일 추가** (기존 파일에 병합):

```yaml
services:
  # 기존 서비스들은 그대로 유지 ...

  {service-name}:
    build:
      context: ./{service-name}
      dockerfile: Dockerfile
    profiles:
      - ai
    ports:
      - "{port}:8000"
    env_file:
      - ./.env
    environment:
      - APP_ENV=development
    # 다른 서비스(DB 등)가 먼저 기동되어야 하는 경우
    # depends_on:
    #   - postgres
    restart: unless-stopped
```

> `{port}`는 `dev-plan.md`의 '10-4. AI 서비스 구조'에서 AI 서비스에 할당된 포트로 교체한다.

### 8단계: 실행 확인

**로컬 직접 실행**:

```bash
cd {service-name}
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Docker Compose ai 프로파일로 실행**:

```bash
docker compose --profile ai up --build
```

**헬스체크 확인**:

```bash
curl http://localhost:{port}/health
# 기대 응답: {"status":"ok"}
```

---

## 출력 형식

이 단계 완료 후 아래 체크리스트를 작성하여 `docs/develop/ai-service-env-setup-checklist.md`에 저장한다.

```markdown
# AI 서비스 초기화 체크리스트

> 서비스명: {service-name}
> 작성일: {날짜}
> 기준: docs/design/ai-service-design.md

## 완료 항목
- [ ] SKIP 조건 확인 (설계서 존재 + AI 서비스 필요 판정)
- [ ] 프로젝트 디렉토리 생성 (설계서 2.7절 구조 일치)
- [ ] 가상환경 설정 완료 (poetry 또는 venv)
- [ ] 의존성 정의 및 설치 완료 (pyproject.toml 또는 requirements.txt)
- [ ] 루트 .env.example에 AI 서비스 환경변수 섹션 추가 완료
- [ ] config.py 작성 완료 (Pydantic Settings 기반)
- [ ] main.py 작성 완료 (FastAPI 앱 + 라우터 등록)
- [ ] /health 엔드포인트 응답 정상 확인
- [ ] Dockerfile 빌드 성공
- [ ] docker-compose.yml ai 프로파일에 서비스 등록
- [ ] docker compose --profile ai up으로 기동 확인
- [ ] LLM API 키 하드코딩 없음 (루트 .env 관리 확인)

## RAG 관련 (설계서 6절 해당 시)
- [ ] rag/ 디렉토리 생성 (indexer.py, retriever.py, embeddings.py 스텁)
- [ ] 벡터 DB 의존성 추가

## Function Calling 관련 (설계서 7절 해당 시)
- [ ] tools/ 디렉토리 생성

## MAS 관련 (설계서 7절 MAS 해당 시)
- [ ] agents/ 디렉토리 생성
- [ ] langgraph 의존성 추가
```

---

## 품질 기준

| 항목 | 기준 |
|------|------|
| FastAPI 앱 구조 | 설계서 2.7절 서비스 구조와 디렉토리 일치 |
| /health 엔드포인트 | `{"status": "ok"}` 응답 정상 반환 |
| Dockerfile 빌드 | `docker build` 오류 없이 완료 |
| ai 프로파일 기동 | `docker compose --profile ai up` 서비스 정상 기동 |
| LLM API 키 관리 | 코드 내 하드코딩 없음, 루트 .env로만 관리 |
| .env 버전 관리 | 루트 .gitignore 등록 확인, 루트 .env.example에 AI 서비스 섹션 포함 |
| 의존성 파일 | 설계서 LLM 제공자 반영, LangChain 의존성 포함 |

---

## 주의사항

- **LLM API 키 하드코딩 금지**: 키는 반드시 루트 `.env`에서 관리하고 코드에 직접 기재하지 않는다. 루트 `.env.example`의 AI 서비스 섹션에 키 이름만 포함하고 실제 값은 제외한다.

- **비즈니스 로직 구현 금지**: 이 단계에서는 프로젝트 골격만 설정한다. `services/`, `clients/`, `prompts/` 등 하위 디렉토리에는 `__init__.py`만 생성하고 실제 구현은 개발 단계에서 수행한다.

- **docker-compose.yml ai 프로파일**: Dockerfile은 `{service-name}/` 하위에 위치하고, `docker-compose.yml`의 `ai` 프로파일에 등록한다. `backing-service-setup.md`에서 DB 등 외부 의존 서비스가 정의된 경우 `depends_on`으로 연결한다.

- **포트 충돌 방지**: 서비스 포트는 `dev-plan.md`의 '10-4. AI 서비스 구조'에서 AI 서비스에 할당된 포트를 사용한다. 다른 서비스와 겹치지 않도록 확인한다.

- **Python 버전 일치**: `pyproject.toml`의 Python 버전 제약과 `Dockerfile`의 베이스 이미지 버전을 `dev-plan.md`의 '10-5. 기술스택 정보'와 일치시킨다.

- **LangChain 기반 통일**: 모든 AI 서비스는 LangChain의 `init_chat_model`을 사용하여 LLM 제공자를 추상화한다. 단순 호출이든 복합 패턴(RAG, Function Calling, Agent)이든 동일한 LangChain 기반 구조를 적용한다.

- **설계서 우선**: 이 가이드의 디렉토리 구조와 의존성은 기본 예시다. 실제 `ai-service-design.md`에 다른 구조나 프레임워크가 명시된 경우 설계서를 따른다.
