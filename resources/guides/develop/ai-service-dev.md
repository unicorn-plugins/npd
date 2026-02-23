# AI 서비스 구현 가이드

## 목적

AI 서비스 설계서를 기반으로 Python/FastAPI AI 서비스의 엔드포인트, 프롬프트, LLM 연동을 구현한다. `ai-service-env-setup.md`에서 확립한 프로젝트 골격 위에 실제 비즈니스 로직, LLM 클라이언트, 프롬프트 템플릿, API 라우터를 완성하는 단계이다.

---

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| AI 서비스 설계서 | `docs/design/ai-service-design.md` | 프롬프트 설계, 모델 선정, 아키텍처 확인 |
| AI 서비스 API 명세 | `docs/design/api/ai-*-api.yaml` | 엔드포인트 목록, 요청/응답 스키마 확인 |
| AI 내부 시퀀스 | `docs/design/sequence/inner/ai-*.puml` | 서비스 내부 처리 흐름 확인 |
| AI 클래스 설계 | `docs/design/class/ai-*.puml` | 클래스 시그니처, 의존성 방향 확인 |
| AI 서비스 프로젝트 골격 | `{service-name}/` | `ai-service-env-setup.md` 완료 산출물 |

---

## 출력 (이 단계 산출물)

| 산출물 | 경로 | 설명 |
|--------|------|------|
| Pydantic 스키마 | `{service-name}/models/` | 요청/응답 데이터 모델 |
| LLM 클라이언트 | `{service-name}/clients/` | LLM 제공자별 클라이언트 팩토리 |
| 프롬프트 템플릿 | `{service-name}/prompts/` | 기능별 프롬프트 파일 및 로더 |
| 비즈니스 로직 | `{service-name}/services/` | LLM 호출 + 캐싱 + 폴백 포함 서비스 |
| API 라우터 | `{service-name}/routers/` | FastAPI 라우터 (엔드포인트 구현) |
| 테스트 코드 | `{service-name}/tests/` | pytest 기반 단위·통합 테스트 |

---

## SKIP 조건

다음 두 조건 중 하나에 해당하면 이 단계 전체를 건너뛴다.

| 순서 | 조건 | 판단 방법 |
|:----:|------|---------|
| 1 | `docs/design/ai-service-design.md` 파일이 존재하지 않음 | 파일 존재 여부 확인 |
| 2 | 파일은 존재하나 결론이 "AI 서비스 불필요", "해당 없음", "AI 기능 미사용" 중 하나 | 설계서 서두·결론 섹션에서 해당 키워드 검색 |

---

## 방법론

### 1단계: 설계서 및 명세 분석

구현 전 아래 항목을 설계서와 명세에서 확인하고 메모한다.

```
[확인 항목]
- 엔드포인트 목록: api/ai-*-api.yaml 전체 경로·메서드·스키마
- 프롬프트 목록: ai-service-design.md 프롬프트 설계 섹션 (system/user/assistant 구조)
- 모델명: 설계서에 명시된 LLM 모델명 (예: gpt-4o, claude-3-5-sonnet-20241022)
- LangChain 사용 여부: RAG·Function Calling·Agent 포함 시 필수
- 캐싱 전략: Redis 캐싱 여부 및 TTL
- 스트리밍 여부: SSE(Server-Sent Events) 응답 필요 엔드포인트
- 폴백 전략: LLM 장애 시 기본 응답 방식
- Rate Limiting: 엔드포인트별 호출 제한
```

### 2단계: Pydantic 스키마 정의

API 명세(`ai-*-api.yaml`)의 각 엔드포인트 요청/응답 스키마를 Pydantic 모델로 정의한다.

**파일 구조**:

```
models/
├── __init__.py
├── base.py          # 공통 기반 모델 (ErrorResponse 등)
└── {feature}.py     # 기능별 요청/응답 모델
```

**`models/base.py`**:

```python
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
```

**`models/{feature}.py`** (API 명세 스키마를 그대로 옮긴다):

```python
from pydantic import BaseModel, Field


class TextAnalyzeRequest(BaseModel):
    text: str = Field(..., description="분석할 텍스트", max_length=10000)
    language: str = Field(default="ko", description="입력 텍스트 언어")


class TextAnalyzeResponse(BaseModel):
    summary: str
    keywords: list[str]
    sentiment: str
    tokens_used: int
```

> 필드명·타입·검증 규칙은 반드시 `ai-*-api.yaml` 스키마와 일치시킨다.

### 3단계: LLM 클라이언트 구현

LLM 제공자별로 클라이언트를 구현하고, 팩토리 함수로 제공자 분기를 관리한다.

**파일 구조**:

```
clients/
├── __init__.py
├── base.py          # 추상 기반 클라이언트
├── openai_client.py
├── anthropic_client.py
└── factory.py       # 제공자별 인스턴스 생성
```

**`clients/base.py`** (추상 인터페이스):

```python
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str:
        """LLM에 메시지를 전송하고 응답 문자열을 반환한다."""
        ...

    @abstractmethod
    async def chat_stream(self, messages: list[dict], **kwargs):
        """스트리밍 응답을 비동기 제너레이터로 반환한다."""
        ...
```

**`clients/openai_client.py`**:

```python
from openai import AsyncOpenAI

from clients.base import BaseLLMClient
from config import settings


class OpenAIClient(BaseLLMClient):
    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.llm_model_name  # 예: "gpt-4o"

    async def chat(self, messages: list[dict], max_tokens: int = 1024, **kwargs) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content

    async def chat_stream(self, messages: list[dict], max_tokens: int = 1024, **kwargs):
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta is not None:
                yield delta
```

**`clients/anthropic_client.py`**:

```python
import anthropic

from clients.base import BaseLLMClient
from config import settings


class AnthropicClient(BaseLLMClient):
    def __init__(self):
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model_name  # 예: "claude-3-5-sonnet-20241022"

    async def chat(self, messages: list[dict], max_tokens: int = 1024, **kwargs) -> str:
        # Anthropic API는 system 메시지를 별도 파라미터로 분리
        system_prompt = next(
            (m["content"] for m in messages if m["role"] == "system"), ""
        )
        user_messages = [m for m in messages if m["role"] != "system"]

        response = await self._client.messages.create(
            model=self._model,
            system=system_prompt,
            messages=user_messages,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.content[0].text

    async def chat_stream(self, messages: list[dict], max_tokens: int = 1024, **kwargs):
        system_prompt = next(
            (m["content"] for m in messages if m["role"] == "system"), ""
        )
        user_messages = [m for m in messages if m["role"] != "system"]

        async with self._client.messages.stream(
            model=self._model,
            system=system_prompt,
            messages=user_messages,
            max_tokens=max_tokens,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text
```

**`clients/factory.py`** (제공자 분기):

```python
from functools import lru_cache

from clients.base import BaseLLMClient
from config import settings


@lru_cache(maxsize=1)
def get_llm_client() -> BaseLLMClient:
    """설정의 LLM_PROVIDER 값에 따라 클라이언트 인스턴스를 반환한다."""
    provider = settings.llm_provider.lower()

    if provider == "openai":
        from clients.openai_client import OpenAIClient
        return OpenAIClient()
    elif provider == "anthropic":
        from clients.anthropic_client import AnthropicClient
        return AnthropicClient()
    elif provider == "google":
        from clients.google_client import GoogleClient
        return GoogleClient()
    else:
        raise ValueError(f"지원하지 않는 LLM 제공자입니다: {provider}")
```

**`config.py`에 추가할 LLM 관련 설정**:

```python
# LLM 설정 (설계서 모델 선정 기준으로 기본값 지정)
llm_provider: str = "openai"          # openai | anthropic | google
llm_model_name: str = "gpt-4o"        # 설계서 지정 모델명
llm_max_tokens: int = 1024
llm_temperature: float = 0.7

# AI 서비스 URL (다른 서비스가 이 AI 서비스를 호출할 때 사용)
ai_service_url: str = "http://localhost:8000"
```

**`.env.example`에 추가할 항목**:

```dotenv
# LLM 제공자 설정 (설계서 기준으로 주석 해제)
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-4o
LLM_MAX_TOKENS=1024
LLM_TEMPERATURE=0.7

# AI 서비스 URL (다른 서비스가 참조할 때 사용)
AI_SERVICE_URL=http://localhost:8000
```

### 4단계: 프롬프트 템플릿 작성

설계서의 프롬프트 설계를 파일로 관리한다. 템플릿 변수는 Jinja2 문법(`{{ variable }}`)을 사용하거나 LangChain `PromptTemplate`을 사용한다.

**파일 구조**:

```
prompts/
├── __init__.py
├── loader.py                  # 템플릿 로드 유틸리티
└── {feature}/
    ├── system.txt             # 시스템 프롬프트
    └── user.txt               # 유저 프롬프트 템플릿
```

**`prompts/{feature}/system.txt`** (설계서 system 프롬프트 그대로):

```
당신은 텍스트 분석 전문가입니다.
주어진 텍스트를 분석하여 핵심 요약, 주요 키워드, 감정 분석 결과를 JSON 형식으로 반환합니다.

응답 형식:
{
  "summary": "요약 내용",
  "keywords": ["키워드1", "키워드2"],
  "sentiment": "positive | negative | neutral"
}
```

**`prompts/{feature}/user.txt`** (Jinja2 변수 사용):

```
다음 텍스트를 분석해 주세요.

언어: {{ language }}
텍스트:
{{ text }}
```

**`prompts/loader.py`** (템플릿 로더):

```python
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_PROMPTS_DIR = Path(__file__).parent
_env = Environment(loader=FileSystemLoader(str(_PROMPTS_DIR)))


def load_system_prompt(feature: str) -> str:
    """feature 디렉토리의 system.txt를 읽어 반환한다."""
    path = _PROMPTS_DIR / feature / "system.txt"
    return path.read_text(encoding="utf-8").strip()


def render_user_prompt(feature: str, **variables) -> str:
    """feature 디렉토리의 user.txt를 Jinja2로 렌더링하여 반환한다."""
    template = _env.get_template(f"{feature}/user.txt")
    return template.render(**variables).strip()
```

**LangChain PromptTemplate 사용 시 (설계서에 LangChain 명시 시)**:

```python
from langchain_core.prompts import ChatPromptTemplate

analyze_prompt = ChatPromptTemplate.from_messages([
    ("system", "{system_prompt}"),
    ("human", "{user_prompt}"),
])
```

> 프롬프트 내용은 반드시 설계서의 프롬프트 설계 섹션과 일치시킨다. 임의로 내용을 변경하지 않는다.

### 5단계: 비즈니스 로직 서비스 구현

LLM 호출, 응답 파싱, 캐싱, 폴백을 서비스 계층에서 관리한다.

**파일 구조**:

```
services/
├── __init__.py
└── {feature}_service.py
```

**`services/{feature}_service.py`** (캐싱 + 폴백 포함):

```python
import hashlib
import json
import logging

from clients.factory import get_llm_client
from models.{feature} import TextAnalyzeRequest, TextAnalyzeResponse
from prompts.loader import load_system_prompt, render_user_prompt

logger = logging.getLogger(__name__)


class TextAnalyzeService:
    def __init__(self):
        self._llm = get_llm_client()
        self._system_prompt = load_system_prompt("text_analyze")

    async def analyze(self, request: TextAnalyzeRequest) -> TextAnalyzeResponse:
        # 1. 캐시 확인 (Redis 캐싱 전략 적용 시)
        cache_key = self._build_cache_key(request)
        cached = await self._get_cache(cache_key)
        if cached:
            return TextAnalyzeResponse(**cached)

        # 2. 프롬프트 구성
        user_prompt = render_user_prompt(
            "text_analyze",
            text=request.text,
            language=request.language,
        )
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # 3. LLM 호출 (폴백 포함)
        try:
            raw_response = await self._llm.chat(messages, max_tokens=1024)
            result = self._parse_response(raw_response)
        except Exception as exc:
            logger.error("LLM 호출 실패: %s", exc)
            result = self._fallback_response()

        # 4. 캐시 저장 (TTL: 3600초)
        await self._set_cache(cache_key, result.model_dump(), ttl=3600)

        return result

    def _build_cache_key(self, request: TextAnalyzeRequest) -> str:
        content = f"{request.text}:{request.language}"
        return "analyze:" + hashlib.md5(content.encode()).hexdigest()

    def _parse_response(self, raw: str) -> TextAnalyzeResponse:
        try:
            data = json.loads(raw)
            return TextAnalyzeResponse(**data, tokens_used=0)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("응답 파싱 실패, 폴백 사용: %s", exc)
            return self._fallback_response()

    def _fallback_response(self) -> TextAnalyzeResponse:
        return TextAnalyzeResponse(
            summary="분석에 실패했습니다. 잠시 후 다시 시도해 주세요.",
            keywords=[],
            sentiment="neutral",
            tokens_used=0,
        )

    async def _get_cache(self, key: str) -> dict | None:
        # Redis 연동 시 아래 구현으로 교체
        # return await redis_client.get(key)
        return None

    async def _set_cache(self, key: str, value: dict, ttl: int = 3600) -> None:
        # Redis 연동 시 아래 구현으로 교체
        # await redis_client.setex(key, ttl, json.dumps(value))
        pass
```

**Redis 캐시 연동 (설계서에 캐싱 명시 시)**:

```python
# clients/redis_client.py
import json

import redis.asyncio as aioredis

from config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def cache_get(key: str) -> dict | None:
    r = await get_redis()
    raw = await r.get(key)
    return json.loads(raw) if raw else None


async def cache_set(key: str, value: dict, ttl: int = 3600) -> None:
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value, ensure_ascii=False))
```

**토큰 수 제한 (비용 최적화)**:

```python
import tiktoken


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def truncate_to_token_limit(text: str, max_tokens: int = 8000, model: str = "gpt-4o") -> str:
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens])
```

### 6단계: API 라우터 구현

API 명세(`ai-*-api.yaml`)의 각 엔드포인트를 FastAPI 라우터로 구현한다.

**파일 구조**:

```
routers/
├── __init__.py
├── health.py
└── {feature}.py
```

**`routers/{feature}.py`**:

```python
import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from models.{feature} import TextAnalyzeRequest, TextAnalyzeResponse
from services.{feature}_service import TextAnalyzeService

router = APIRouter(prefix="/api/v1", tags=["{feature}"])
_service = TextAnalyzeService()
logger = logging.getLogger(__name__)


@router.post(
    "/analyze",
    response_model=TextAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="텍스트 분석",
    description="텍스트를 LLM으로 분석하여 요약, 키워드, 감정 결과를 반환한다.",
)
async def analyze_text(request: TextAnalyzeRequest) -> TextAnalyzeResponse:
    try:
        return await _service.analyze(request)
    except Exception as exc:
        logger.error("텍스트 분석 오류: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM 서비스 오류가 발생했습니다.",
        ) from exc


@router.post(
    "/analyze/stream",
    summary="텍스트 분석 (스트리밍)",
    description="스트리밍 응답이 필요한 엔드포인트. 설계서에 명시된 경우에만 구현한다.",
)
async def analyze_text_stream(request: TextAnalyzeRequest) -> StreamingResponse:
    from clients.factory import get_llm_client
    from prompts.loader import load_system_prompt, render_user_prompt

    llm = get_llm_client()
    system_prompt = load_system_prompt("{feature}")
    user_prompt = render_user_prompt("{feature}", text=request.text, language=request.language)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    async def event_stream():
        async for chunk in llm.chat_stream(messages):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

**`main.py`에 라우터 등록**:

```python
from routers.{feature} import router as {feature}_router

app.include_router({feature}_router)
```

### 7단계: 테스트 작성 (pytest)

**파일 구조**:

```
tests/
├── __init__.py
├── conftest.py               # 공통 픽스처 (TestClient, mock LLM)
├── test_routers/
│   └── test_{feature}.py     # 엔드포인트 통합 테스트
└── test_services/
    └── test_{feature}_service.py  # 서비스 단위 테스트
```

**`tests/conftest.py`** (LLM mock 포함):

```python
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
def mock_llm_response():
    """LLM 응답을 mock으로 교체하여 실제 API 호출 없이 테스트한다."""
    mock_response = '{"summary": "테스트 요약", "keywords": ["키워드1"], "sentiment": "positive"}'
    with patch("clients.factory.get_llm_client") as mock_factory:
        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response
        mock_factory.return_value = mock_client
        yield mock_client


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
```

**`tests/test_routers/test_{feature}.py`** (엔드포인트 테스트):

```python
import pytest


@pytest.mark.asyncio
async def test_analyze_success(async_client, mock_llm_response):
    response = await async_client.post(
        "/api/v1/analyze",
        json={"text": "테스트 텍스트입니다.", "language": "ko"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "summary" in body
    assert "keywords" in body
    assert "sentiment" in body


@pytest.mark.asyncio
async def test_analyze_invalid_input(async_client):
    response = await async_client.post(
        "/api/v1/analyze",
        json={"text": ""},   # 빈 문자열 — 검증 실패
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**`tests/test_services/test_{feature}_service.py`** (서비스 단위 테스트):

```python
from unittest.mock import AsyncMock

import pytest

from models.{feature} import TextAnalyzeRequest
from services.{feature}_service import TextAnalyzeService


@pytest.mark.asyncio
async def test_analyze_returns_fallback_on_llm_error():
    service = TextAnalyzeService()
    service._llm = AsyncMock()
    service._llm.chat.side_effect = RuntimeError("LLM 연결 오류")

    request = TextAnalyzeRequest(text="테스트", language="ko")
    result = await service.analyze(request)

    assert result.sentiment == "neutral"
    assert "실패" in result.summary
```

**테스트 실행**:

```bash
cd {service-name}
pytest tests/ -v
```

### 8단계: 실행 확인

**로컬 직접 실행**:

```bash
cd {service-name}
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**API 동작 확인**:

```bash
# 헬스체크
curl http://localhost:8000/health

# 구현된 엔드포인트 테스트
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "테스트 텍스트입니다.", "language": "ko"}'
```

**Docker Compose ai 프로파일로 실행**:

```bash
docker compose --profile ai up --build
```

**AI 서비스 URL 환경변수 확인**: 다른 서비스(백엔드 API 등)에서 AI 서비스를 호출할 때는 `AI_SERVICE_URL` 환경변수를 사용한다.

```dotenv
# backend/.env 또는 docker-compose.yml environment 블록
AI_SERVICE_URL=http://{service-name}:8000   # Docker 네트워크 내부 호출
# AI_SERVICE_URL=http://localhost:8000      # 로컬 직접 실행 시
```

---

## 출력 형식

이 단계 완료 후 아래 체크리스트를 작성하여 `docs/develop/ai-service-dev-checklist.md`에 저장한다.

```markdown
# AI 서비스 구현 체크리스트

> 서비스명: {service-name}
> 작성일: {날짜}
> 기준: docs/design/ai-service-design.md

## 완료 항목

### Pydantic 스키마
- [ ] SKIP 조건 확인 (설계서 존재 + AI 서비스 필요 판정)
- [ ] 모든 엔드포인트의 요청/응답 모델 정의 (api/ai-*-api.yaml 기준)
- [ ] 필드 검증 규칙 적용 (max_length, constraints 등)

### LLM 클라이언트
- [ ] BaseLLMClient 추상 인터페이스 구현
- [ ] 설계서 지정 LLM 제공자 클라이언트 구현
- [ ] 팩토리 함수로 제공자 분기 처리
- [ ] LLM API 키 하드코딩 없음 (.env 관리 확인)
- [ ] 스트리밍 클라이언트 구현 (설계서 스트리밍 명시 시)

### 프롬프트 템플릿
- [ ] 기능별 system.txt / user.txt 파일 작성
- [ ] 프롬프트 내용이 설계서 프롬프트 설계와 일치
- [ ] Jinja2 또는 LangChain PromptTemplate 로더 구현
- [ ] 변수 치환 정상 동작 확인

### 비즈니스 로직
- [ ] 설계서의 모든 기능에 대한 서비스 클래스 구현
- [ ] 캐싱 전략 구현 (Redis 또는 인메모리)
- [ ] 에러 핸들링 및 폴백 응답 구현
- [ ] 토큰 수 제한 적용 (비용 최적화)

### API 라우터
- [ ] 설계서 모든 엔드포인트 구현 (ai-*-api.yaml 기준)
- [ ] 라우터 prefix / tags 명세 일치
- [ ] 스트리밍 엔드포인트 구현 (설계서 스트리밍 명시 시)
- [ ] 에러 응답 상태 코드 명세 일치

### 테스트
- [ ] conftest.py: LLM mock 픽스처 구현
- [ ] 엔드포인트 성공/실패 케이스 테스트
- [ ] 서비스 단위 테스트 (LLM 오류 폴백 포함)
- [ ] pytest 전체 통과 확인

### 실행 검증
- [ ] uvicorn 직접 실행 시 모든 엔드포인트 정상 응답
- [ ] docker compose --profile ai up 정상 기동
- [ ] AI_SERVICE_URL 환경변수로 외부 호출 연동 확인
```

---

## 품질 기준

| 항목 | 기준 |
|------|------|
| 엔드포인트 완전성 | `ai-*-api.yaml`의 모든 경로·메서드 구현 |
| 프롬프트 일치 | 설계서 프롬프트 설계 섹션과 내용 동일 |
| LLM API 키 관리 | 코드 내 하드코딩 없음, `.env`로만 관리 |
| 에러 핸들링 | 모든 엔드포인트에 try-except 및 폴백 응답 구현 |
| 테스트 통과 | `pytest tests/ -v` 전체 PASS |
| 캐싱 적용 | 설계서 캐싱 전략 명시 시 Redis 연동 또는 인메모리 캐시 구현 |
| 스트리밍 응답 | 설계서 스트리밍 명시 엔드포인트에 SSE 구현 |

---

## 주의사항

- **LLM API 키 하드코딩 금지**: 키는 반드시 `.env`에서 `config.py` → `Settings` 클래스를 통해 읽는다. `os.environ["OPENAI_API_KEY"]` 직접 호출이나 문자열 리터럴 삽입은 금지된다.

- **테스트 시 LLM mock 필수**: 실제 LLM API를 호출하는 테스트는 CI 비용과 속도 문제를 유발한다. `conftest.py`의 `mock_llm_response` 픽스처로 교체하여 테스트한다. 프롬프트 품질 검증이 필요한 경우에만 별도 수동 테스트로 수행한다.

- **Rate Limiting 고려**: LLM API 제공자마다 분당 호출 제한(RPM)이 존재한다. 대량 요청이 예상되는 엔드포인트에는 `slowapi` 등 미들웨어로 Rate Limiting을 적용한다.

- **응답 캐싱 전략**: 동일 입력에 대한 반복 LLM 호출은 비용을 증가시킨다. 입력 해시를 캐시 키로 사용하고 Redis TTL(기본 3600초)로 만료를 관리한다. 실시간성이 필요한 엔드포인트는 캐싱에서 제외한다.

- **설계서 우선**: 이 가이드의 코드 예시는 일반적인 패턴을 보여준다. 설계서(`ai-service-design.md`)에 다른 클래스명, 메서드 시그니처, 프롬프트 구조가 명시된 경우 설계서를 따른다.

- **AI_SERVICE_URL 환경변수**: 다른 마이크로서비스(백엔드 API 등)에서 AI 서비스를 호출할 때 URL을 하드코딩하지 않고 `AI_SERVICE_URL` 환경변수로 관리한다. Docker Compose 내부 네트워크에서는 서비스명을 호스트로 사용한다 (예: `http://{service-name}:8000`).

- **LangChain 선택 기준**: 단순 LLM API 호출은 직접 클라이언트로 구현한다. RAG, Function Calling, Agent, 다단계 체인 등 복합 패턴이 설계서에 포함된 경우에만 LangChain을 사용한다. 불필요한 LangChain 의존성은 빌드 시간과 컨테이너 크기를 증가시킨다.
