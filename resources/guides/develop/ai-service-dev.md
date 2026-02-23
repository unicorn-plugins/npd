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
| LLM 클라이언트 | `{service-name}/clients/` | LangChain 기반 LLM 팩토리 |
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
- LangChain 패턴 확인: RAG·Function Calling·Agent·LangGraph 사용 여부
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

LangChain의 `init_chat_model`을 사용하여 LLM 제공자를 추상화한다. 단일 팩토리 함수로 OpenAI, Anthropic, Google, Groq 등 모든 제공자를 지원하며, LCEL(LangChain Expression Language)로 체인을 구성한다.

**파일 구조**:

```
clients/
├── __init__.py
└── llm.py           # LangChain 기반 LLM 팩토리
```

**`clients/llm.py`** (LangChain 통합 LLM 팩토리):

```python
from functools import lru_cache

from langchain.chat_models import init_chat_model

from config import settings


@lru_cache(maxsize=1)
def get_llm():
    """설정의 LLM_PROVIDER / LLM_MODEL_NAME에 따라 LangChain ChatModel을 반환한다.

    init_chat_model은 model_provider 값에 따라 내부적으로 적절한 ChatModel
    (ChatOpenAI, ChatAnthropic, ChatGoogleGenerativeAI, ChatGroq 등)을 생성한다.
    각 제공자의 API 키는 환경변수에서 자동으로 읽는다:
      - openai: OPENAI_API_KEY
      - anthropic: ANTHROPIC_API_KEY
      - google_genai: GOOGLE_API_KEY
      - groq: GROQ_API_KEY
    """
    return init_chat_model(
        model=settings.llm_model_name,
        model_provider=settings.llm_provider,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )
```

**지원 제공자 및 model_provider 값**:

| LLM 제공자 | `LLM_PROVIDER` 값 | 필요 패키지 | 예시 모델 |
|------------|-------------------|------------|----------|
| OpenAI | `openai` | `langchain-openai` | gpt-4o, gpt-4o-mini |
| Anthropic | `anthropic` | `langchain-anthropic` | claude-sonnet-4-20250514 |
| Google Gemini | `google_genai` | `langchain-google-genai` | gemini-2.0-flash |
| Groq | `groq` | `langchain-groq` | llama-3.3-70b-versatile |

> `init_chat_model`은 각 제공자의 system 메시지 처리(Anthropic의 system 파라미터 분리, Google의 system_instruction 등)를 내부적으로 자동 처리한다.

**LCEL 체인 구성**:

LangChain Expression Language(LCEL)를 사용하여 프롬프트 → LLM → 파서 체인을 구성한다.

```python
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from clients.llm import get_llm


def create_analyze_chain():
    """텍스트 분석 LCEL 체인을 생성한다."""
    # 1. 프롬프트 템플릿
    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        ("human", "{user_input}"),
    ])

    # 2. LLM 모델 (init_chat_model로 생성)
    llm = get_llm()

    # 3. 출력 파서
    parser = JsonOutputParser()  # JSON 출력 시
    # parser = StrOutputParser()  # 자연어 출력 시

    # 4. LCEL 체인 합성 (Runnable 인터페이스)
    chain = prompt | llm | parser
    return chain


# 사용 예시
async def run_chain():
    chain = create_analyze_chain()
    result = await chain.ainvoke({
        "system_prompt": "텍스트를 분석하여 JSON으로 반환하세요.",
        "user_input": "분석할 텍스트...",
    })
    return result
```

**Runnable 합성 패턴**:

```python
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# 전처리 → LLM → 후처리 체인
chain = (
    RunnablePassthrough.assign(
        preprocessed=RunnableLambda(lambda x: preprocess(x["input"]))
    )
    | prompt
    | llm
    | parser
)
```

**`config.py`에 추가할 LLM 관련 설정**:

```python
# LLM 설정 (설계서 모델 선정 기준으로 기본값 지정)
llm_provider: str = "openai"          # openai | anthropic | google_genai | groq
llm_model_name: str = "gpt-4o"        # 설계서 지정 모델명
llm_max_tokens: int = 1024
llm_temperature: float = 0.7

# LLM API 키 (사용할 제공자의 키만 설정 — LangChain이 환경변수에서 자동 로드)
openai_api_key: str = ""
anthropic_api_key: str = ""
google_api_key: str = ""
groq_api_key: str = ""

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

# LLM API 키 (사용할 제공자의 키만 설정)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
GROQ_API_KEY=

# AI 서비스 URL (다른 서비스가 참조할 때 사용)
AI_SERVICE_URL=http://localhost:8000
```

> LangChain 의존성은 `pyproject.toml`에 `langchain`, `langchain-core` 및 사용할 제공자 패키지(`langchain-openai`, `langchain-anthropic`, `langchain-google-genai`, `langchain-groq` 중 해당 패키지)를 추가한다.


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

**LangChain PromptTemplate 사용 시**:

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

from clients.llm import get_llm
from models.{feature} import TextAnalyzeRequest, TextAnalyzeResponse
from prompts.loader import load_system_prompt, render_user_prompt

logger = logging.getLogger(__name__)


class TextAnalyzeService:
    def __init__(self):
        self._llm = get_llm()
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
            response = await self._llm.ainvoke(messages)
            raw_response = response.content
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

### 5.1단계: 멀티턴 대화 서비스 구현 (해당 시)

설계서에 대화형 AI 기능(챗봇 등)이 포함된 경우, 세션 관리 및 대화 이력 유지를 구현한다.

**파일 구조**:

```
conversation/
├── __init__.py
├── session_store.py    # 세션 저장소 (Redis / In-memory)
└── conversation_service.py
```

**`conversation/session_store.py`** (Redis 기반 세션 저장소):

```python
import json

import redis.asyncio as aioredis

from config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def get_history(session_id: str) -> list[dict]:
    r = await get_redis()
    raw = await r.get(f"chat:{session_id}")
    return json.loads(raw) if raw else []


async def save_history(session_id: str, history: list[dict], ttl: int = 3600) -> None:
    r = await get_redis()
    await r.setex(f"chat:{session_id}", ttl, json.dumps(history, ensure_ascii=False))
```

**`conversation/conversation_service.py`** (슬라이딩 윈도우 + 세션 관리):

```python
import logging

from clients.llm import get_llm
from conversation.session_store import get_history, save_history
from prompts.loader import load_system_prompt

logger = logging.getLogger(__name__)

MAX_TURNS = 10  # 슬라이딩 윈도우 크기 (설계서 기준)


class ConversationService:
    def __init__(self, feature: str):
        self._llm = get_llm()
        self._system_prompt = load_system_prompt(feature)

    async def chat(self, session_id: str, user_message: str) -> str:
        # 1. 대화 이력 조회
        history = await get_history(session_id)

        # 2. 슬라이딩 윈도우 적용 (최근 N턴만 유지)
        if len(history) > MAX_TURNS * 2:
            history = history[-(MAX_TURNS * 2):]

        # 3. 메시지 구성
        messages = [{"role": "system", "content": self._system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        # 4. LLM 호출
        try:
            result = await self._llm.ainvoke(messages)
            response = result.content
        except Exception as exc:
            logger.error("LLM 호출 실패: %s", exc)
            response = "죄송합니다. 일시적인 오류가 발생했습니다."

        # 5. 이력 업데이트 및 저장
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": response})
        await save_history(session_id, history)

        return response
```

### 5.2단계: RAG 파이프라인 구현 (해당 시)

설계서에 RAG가 포함된 경우, 문서 인덱싱 → 검색 → 생성 파이프라인을 구현한다.

**파일 구조**:

```
rag/
├── __init__.py
├── indexer.py       # 문서 인덱싱 (Load → Split → Embed → Store)
├── retriever.py     # 검색 (Dense / 하이브리드 / 리랭킹)
└── embeddings.py    # 임베딩 모델 설정
```

**`rag/indexer.py`** (문서 인덱싱 파이프라인):

```python
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings


def create_index(file_path: str, collection_name: str) -> Chroma:
    """문서를 로드하고 벡터 DB에 인덱싱한다."""
    # 1. Load: 문서 로더 (설계서 데이터 소스 참조)
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()

    # 2. Split: 청킹 (설계서 청킹 전략 참조)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(documents)

    # 3. Embed + Store: 임베딩 → 벡터 DB 저장
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openai_api_key,
    )
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory="./chroma_db",
    )
    return vectorstore
```

**`rag/retriever.py`** (검색 파이프라인):

```python
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers import EnsembleRetriever

from config import settings


def get_dense_retriever(collection_name: str, top_k: int = 5):
    """Dense(벡터) 검색 리트리버를 반환한다."""
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openai_api_key,
    )
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory="./chroma_db",
    )
    return vectorstore.as_retriever(search_kwargs={"k": top_k})


def get_hybrid_retriever(collection_name: str, documents: list, top_k: int = 5):
    """하이브리드 (Dense + BM25) 검색 리트리버를 반환한다."""
    dense = get_dense_retriever(collection_name, top_k)
    bm25 = BM25Retriever.from_documents(documents, k=top_k)
    return EnsembleRetriever(
        retrievers=[dense, bm25],
        weights=[0.5, 0.5],
    )
```

**`services/{feature}_rag_service.py`** (LCEL 체인으로 RAG 생성):

```python
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from clients.llm import get_llm
from rag.retriever import get_dense_retriever


def create_rag_chain(collection_name: str):
    retriever = get_dense_retriever(collection_name)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "다음 컨텍스트를 참고하여 질문에 답하세요.\n\n{context}"),
        ("human", "{question}"),
    ])
    llm = get_llm()

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)
```

### 5.3단계: Function Calling 구현 (해당 시)

설계서에 Function Calling이 포함된 경우, 도구 정의 및 호출 로직을 구현한다.

**파일 구조**:

```
tools/
├── __init__.py
└── {feature}_tools.py
```

**방식 A: LangChain @tool 데코레이터** (권장 — LangChain 사용 시):

```python
from langchain_core.tools import tool


@tool
def search_location(query: str, category: str = "all") -> str:
    """위치 정보를 검색한다.

    Args:
        query: 검색 키워드
        category: 카테고리 필터 (all, restaurant, hotel, attraction)

    Returns:
        검색 결과 JSON 문자열
    """
    # 실제 API 호출 로직
    return f"'{query}' 검색 결과: ..."


@tool
def get_weather(city: str) -> str:
    """도시의 현재 날씨를 조회한다.

    Args:
        city: 도시명

    Returns:
        날씨 정보 JSON 문자열
    """
    return f"{city} 날씨: 맑음, 20°C"
```

### 5.4단계: LangGraph 워크플로우 구현 (해당 시)

설계서에 복잡한 AI 워크플로우(다단계 추론, 상태 분기, 반복)가 포함된 경우, LangGraph StateGraph를 구현한다.

**파일 구조**:

```
workflows/
├── __init__.py
└── {feature}_graph.py
```

**`workflows/{feature}_graph.py`** (StateGraph 기본 패턴):

```python
from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    """그래프 상태 정의 (설계서 State 항목 참조)."""
    messages: list[dict]
    next_action: str
    result: str | None


async def analyze_node(state: AgentState) -> AgentState:
    """분석 노드: LLM으로 입력을 분석한다."""
    # LLM 호출 로직
    state["next_action"] = "generate"
    return state


async def generate_node(state: AgentState) -> AgentState:
    """생성 노드: 분석 결과를 기반으로 응답을 생성한다."""
    state["result"] = "생성된 결과"
    return state


def should_continue(state: AgentState) -> str:
    """조건 분기: 다음 노드를 결정한다."""
    if state["next_action"] == "generate":
        return "generate"
    return END


def create_workflow():
    """LangGraph 워크플로우를 생성한다."""
    graph = StateGraph(AgentState)

    # 노드 추가
    graph.add_node("analyze", analyze_node)
    graph.add_node("generate", generate_node)

    # 엣지 정의
    graph.set_entry_point("analyze")
    graph.add_conditional_edges("analyze", should_continue)
    graph.add_edge("generate", END)

    # Checkpointer (대화 이력 보존용)
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# 사용 예시
async def run_workflow(input_data: dict):
    app = create_workflow()
    config = {"configurable": {"thread_id": "session-1"}}
    result = await app.ainvoke(
        {"messages": [input_data], "next_action": "", "result": None},
        config=config,
    )
    return result["result"]
```

### 5.5단계: MCP 서버 구현 (해당 시)

설계서에 MCP(Model Context Protocol) 서버가 포함된 경우, FastMCP 기반으로 구현한다.

**파일 구조**:

```
mcp_server/
├── __init__.py
└── server.py
```

**`mcp_server/server.py`** (FastMCP 기반):

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ai-service-mcp")


@mcp.tool()
async def search_knowledge(query: str) -> str:
    """지식 베이스에서 관련 정보를 검색한다.

    Args:
        query: 검색 질의
    """
    # RAG 검색 또는 DB 조회 로직
    return f"'{query}' 관련 검색 결과..."


@mcp.resource("config://settings")
async def get_settings() -> str:
    """AI 서비스의 현재 설정을 반환한다."""
    return "현재 모델: gpt-4o, temperature: 0.7"


@mcp.prompt()
async def analyze_prompt(topic: str) -> str:
    """주제에 맞는 분석 프롬프트를 생성한다.

    Args:
        topic: 분석 주제
    """
    return f"{topic}에 대해 상세히 분석해 주세요."
```

**실행**:

```bash
# 개발 모드 (Inspector UI)
mcp dev mcp_server/server.py

# Claude Desktop 연동
mcp install mcp_server/server.py
```

> MCP SDK 설치: `pip install "mcp[cli]"`

### 5.6단계: 멀티모달 처리 구현 (해당 시)

설계서에 이미지 분석(VLM), PDF 처리, STT/TTS가 포함된 경우 구현한다.

**파일 구조**:

```
multimodal/
├── __init__.py
├── vlm.py           # 이미지 분석
├── pdf_processor.py # PDF 텍스트/테이블 추출
├── stt.py           # 음성→텍스트
└── tts.py           # 텍스트→음성
```

**`multimodal/vlm.py`** (VLM — 이미지 분석):

```python
import base64

from openai import AsyncOpenAI

from config import settings


async def analyze_image(image_path: str, prompt: str) -> str:
    """이미지를 분석하여 결과를 반환한다 (GPT-4o Vision)."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{image_data}"
                }},
            ],
        }],
        max_tokens=1024,
    )
    return response.choices[0].message.content
```

**`multimodal/pdf_processor.py`** (PDF 텍스트 추출):

```python
import pymupdf  # PyMuPDF


def extract_text_from_pdf(file_path: str) -> str:
    """PDF에서 텍스트를 추출한다."""
    doc = pymupdf.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text


def extract_tables_from_pdf(file_path: str) -> list[list]:
    """PDF에서 테이블을 추출한다."""
    doc = pymupdf.open(file_path)
    tables = []
    for page in doc:
        page_tables = page.find_tables()
        for table in page_tables:
            tables.append(table.extract())
    doc.close()
    return tables
```

**`multimodal/stt.py`** (STT — 음성→텍스트):

```python
from openai import AsyncOpenAI

from config import settings


async def transcribe(audio_path: str, language: str = "ko") -> str:
    """음성 파일을 텍스트로 변환한다 (Whisper API)."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    with open(audio_path, "rb") as f:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language=language,
        )
    return transcript.text
```

### 5.7단계: 외부 데이터 소스 통합 구현 (해당 시)

설계서에 웹검색, YouTube 등 외부 데이터 소스 통합이 포함된 경우 구현한다.

**파일 구조**:

```
external/
├── __init__.py
├── web_search.py    # 웹검색 도구
└── youtube.py       # YouTube 트랜스크립트 추출
```

**`external/web_search.py`** (LangChain 도구 기반):

```python
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.tools.tavily_search import TavilySearchResults

from config import settings


def get_search_tool(provider: str = "tavily"):
    """웹검색 도구를 반환한다."""
    if provider == "tavily":
        return TavilySearchResults(
            max_results=5,
            api_key=settings.tavily_api_key,
        )
    elif provider == "duckduckgo":
        return DuckDuckGoSearchResults(max_results=5)
    else:
        raise ValueError(f"지원하지 않는 검색 제공자: {provider}")
```

**`external/youtube.py`** (YouTube 트랜스크립트):

```python
from youtube_transcript_api import YouTubeTranscriptApi


def get_transcript(video_id: str, language: str = "ko") -> str:
    """YouTube 동영상의 트랜스크립트를 추출한다."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language, "en"])
        return " ".join(entry["text"] for entry in transcript)
    except Exception:
        return ""
```

**LangGraph 기반 멀티소스 Agent 예시**:

```python
from langgraph.graph import END, StateGraph

from external.web_search import get_search_tool


async def search_node(state):
    tool = get_search_tool("tavily")
    results = await tool.ainvoke(state["query"])
    state["search_results"] = results
    return state


async def synthesize_node(state):
    # 검색 결과를 LLM으로 종합
    state["answer"] = "종합된 답변..."
    return state


def create_search_agent():
    graph = StateGraph(dict)
    graph.add_node("search", search_node)
    graph.add_node("synthesize", synthesize_node)
    graph.set_entry_point("search")
    graph.add_edge("search", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()
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
    from clients.llm import get_llm
    from prompts.loader import load_system_prompt, render_user_prompt

    llm = get_llm()
    system_prompt = load_system_prompt("{feature}")
    user_prompt = render_user_prompt("{feature}", text=request.text, language=request.language)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    async def event_stream():
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield f"data: {chunk.content}\n\n"
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
    with patch("clients.llm.get_llm") as mock_factory:
        mock_llm = AsyncMock()
        mock_result = AsyncMock()
        mock_result.content = mock_response
        mock_llm.ainvoke.return_value = mock_result
        mock_factory.return_value = mock_llm
        yield mock_llm


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
    service._llm.ainvoke.side_effect = RuntimeError("LLM 연결 오류")

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

**신규 패턴별 테스트 가이드라인** (해당 시):

설계서에 포함된 신규 패턴에 대해 아래 테스트를 추가한다.

```
[추가 테스트 패턴]
- 멀티턴 대화: 세션 유지 확인, 슬라이딩 윈도우 동작 확인, 세션 만료 테스트
- RAG: 검색 결과 relevancy 테스트, 인덱싱 파이프라인 테스트, 빈 결과 처리
- Function Calling: 도구 호출 정확성 테스트, 파라미터 검증, 알 수 없는 도구 처리
- LangGraph: 상태 전이 테스트, 조건 분기 테스트, Checkpointer 동작 확인
- MCP: 서버 도구 실행 테스트, 리소스 반환 테스트
- 멀티모달: VLM 이미지 분석 결과 형식 확인, PDF 텍스트 추출 정확성, STT 결과 검증
- 외부 데이터: 웹검색 결과 캐싱 테스트, API 장애 시 폴백 테스트
```

**멀티턴 대화 테스트 예시**:

```python
@pytest.mark.asyncio
async def test_conversation_sliding_window():
    """슬라이딩 윈도우가 MAX_TURNS 이상에서 정상 작동하는지 확인한다."""
    service = ConversationService("chat")
    from unittest.mock import MagicMock
    service._llm = AsyncMock()
    mock_msg = MagicMock()
    mock_msg.content = "응답"
    service._llm.ainvoke.return_value = mock_msg

    session_id = "test-session"
    # MAX_TURNS * 2 이상의 메시지를 전송하여 윈도우 동작 확인
    for i in range(15):
        await service.chat(session_id, f"메시지 {i}")

    # LLM에 전달된 메시지 수가 MAX_TURNS * 2 + 1(system) 이하인지 확인
    last_call_messages = service._llm.ainvoke.call_args[0][0]
    assert len(last_call_messages) <= 10 * 2 + 1 + 1  # system + window + new
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
- [ ] LangChain init_chat_model 기반 get_llm() 팩토리 구현
- [ ] LLM_PROVIDER / LLM_MODEL_NAME 환경변수 설정
- [ ] LLM API 키 하드코딩 없음 (.env 관리 확인)
- [ ] LCEL 체인 구성 확인 (프롬프트 → LLM → 파서)

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

### 스트리밍 (해당 시)
- [ ] LangChain astream() 기반 SSE 스트리밍 구현

### 멀티턴 대화 (해당 시)
- [ ] 세션 관리 구현 (Redis 또는 인메모리)
- [ ] 슬라이딩 윈도우 동작 확인

### RAG 파이프라인 (해당 시)
- [ ] 인덱싱 파이프라인 구현 (Load → Split → Embed → Store)
- [ ] 검색 파이프라인 구현 (Dense 또는 하이브리드)
- [ ] RAGAS 평가 실행 (Faithfulness, Answer Relevancy)

### Function Calling (해당 시)
- [ ] 도구 정의 및 호출 정확성 확인
- [ ] 병렬/순차 호출 패턴 테스트

### LangGraph (해당 시)
- [ ] StateGraph 구성 및 상태 전이 확인
- [ ] Checkpointer 동작 확인

### MCP (해당 시)
- [ ] MCP 서버 도구 실행 확인
- [ ] Claude 연동 테스트

### 멀티모달 (해당 시)
- [ ] VLM / PDF / STT / TTS 파이프라인 동작 확인

### 외부 데이터 소스 (해당 시)
- [ ] 웹검색 도구 연동 확인
- [ ] YouTube 트랜스크립트 추출 확인
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

- **LangChain 기반 프레임워크**: LLM 클라이언트는 LangChain의 `init_chat_model`을 기반으로 구현한다. 제공자별 직접 클라이언트 구현은 불필요하다. RAG, Function Calling, Agent, LangGraph 등 복합 패턴도 LangChain 생태계 내에서 통합한다.
