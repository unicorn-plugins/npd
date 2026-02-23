# AI 서비스 설계 가이드

## 목적

논리 아키텍처에서 식별된 AI 서비스의 상세 설계를 수행함. AI 활용 기회 우선순위화, LLM API 연동, 프롬프트 설계, 모델 선정, RAG/Function Calling/MCP 적용, AI 기능 아키텍처 정의, 비용·성능 최적화, 모니터링·품질 관리 전략을 포함함.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 논리 아키텍처 설계서 | `docs/design/logical-architecture.md` | AI 서비스 경계·통신 확인 |
| 핵심솔루션 | `docs/plan/think/핵심솔루션.md` | AI 활용 기회 식별 |
| 유저스토리 | `docs/plan/design/userstory.md` | AI 기능-유저스토리 매핑 |
| 시퀀스 설계서 | `docs/design/sequence/` | AI 호출 흐름 확인 |
| 클래스 설계서 | `docs/design/class/` | AI 클라이언트 클래스 확인 |
| HighLevel 아키텍처 | `docs/design/high-level-architecture.md` | AI 인프라 일치성 확인 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| AI 서비스 설계서 | `docs/design/ai-service-design.md` |

## 방법론

### 1. 준비

- 논리 아키텍처에서 AI 서비스의 경계, 책임, 통신 방식을 확인
- 핵심솔루션과 유저스토리에서 AI가 관여하는 기능을 목록화
- 시퀀스 설계서에서 AI 호출 흐름을 파악

### 2. 실행

#### 2.1 AI 기능 확인 및 우선순위 정리

> **참고**: AI 서비스의 식별과 경계 정의는 논리 아키텍처 설계(Step 2)에서 이미 완료되었으며, 이후 Step 3~8에서 ai-engineer가 참여하여 AI 관련 설계가 반영되었습니다. 이 단계에서는 이전 단계의 결과를 취합하고 우선순위를 정리합니다.

**수행 내용**:

1. `docs/design/logical-architecture.md`에서 식별된 AI 서비스 및 기능 목록 확인
2. 시퀀스 설계서, API 설계서, 클래스 설계서에 반영된 AI 기능 교차 검증
3. 아래 기준으로 우선순위 정리:

| 우선순위 | 기준 |
|:--------:|------|
| **P1 (MVP 필수)** | 핵심 가치 제안에 직결, 기술 복잡도 낮음~중간, ROI 명확 |
| **P2 (MVP 선택)** | 가치 기여하나 핵심은 아님, 구현 여건에 따라 포함 |
| **P3 (향후 확장)** | 기술 성숙도 부족 또는 MVP 일정 초과 |

#### 2.2 AI 기술 아키텍처 설계

AI 서비스의 내부 아키텍처를 설계합니다.

**기반 프레임워크**: LangChain (기본) — `init_chat_model`로 LLM 제공자를 추상화하고, LCEL로 체인을 구성한다. RAG·Function Calling·Agent 등 복합 패턴도 LangChain 생태계 내에서 통합한다.

| 구성요소 | 설명 |
|---------|------|
| LangChain Core | LLM 호출, 체인 구성, 프롬프트 템플릿 |
| LangGraph | 복잡한 AI 워크플로우 (다단계 추론, 상태 관리, 분기/반복) |
| LangSmith | 프롬프트 디버깅, 트레이싱, 모니터링 (선택) |

**2.2.1 LLM API 연동 설계**

사용할 LLM 제공자와 연동 방식을 정의합니다. LangChain의 LLM 추상화를 통해 제공자 전환을 용이하게 합니다.

```
[설계 항목]
- LLM 제공자: OpenAI / Anthropic (Claude) / Google (Gemini) / Azure OpenAI / Groq 등
- LangChain 연동: init_chat_model (model_provider로 제공자 자동 선택) — ChatOpenAI / ChatAnthropic / ChatGoogleGenerativeAI 등 자동 매핑
- API 엔드포인트: 베이스 URL, 배포 이름 (Azure의 경우)
- 인증 방식: API Key / Managed Identity / OAuth
- SDK: LangChain 통합 SDK (langchain-openai / langchain-anthropic / langchain-google-genai 등)
- API 버전: 사용할 API 버전 명시

[LLM Provider 비교 설계 항목]
| 비교 항목 | OpenAI (GPT-4o) | Anthropic (Claude) | Google (Gemini) | Groq |
|----------|:-:|:-:|:-:|:-:|
| 입력 토큰 단가 ($/1M) | | | | |
| 출력 토큰 단가 ($/1M) | | | | |
| 컨텍스트 윈도우 | | | | |
| Rate Limit (RPM/TPM) | | | | |
| 응답 레이턴시 (체감) | | | | |
| 특화 기능 | | | | |
| 멀티모달 지원 | | | | |
| Function Calling 방식 | tools | tools | function_declarations | tools |
| 스트리밍 지원 | O | O | O | O |
```

**2.2.2 프롬프트 엔지니어링 설계**

각 AI 기능별 프롬프트를 설계합니다.

```
[프롬프트 설계 항목]
- 프롬프트 ID 및 버전: {기능명}-{역할}-v{버전} (예: brif-pro-system-v1.0)
- 시스템 프롬프트: AI 역할, 규칙, 출력 형식 정의
- 사용자 프롬프트 템플릿: 변수({{variable}}) 기반 동적 데이터 주입
- 프롬프트 기법: Zero-shot / Few-shot / Chain-of-Thought 선택 및 근거
- 출력 형식: JSON / 자연어 / 구조화 텍스트
- 파라미터: temperature, max_tokens, top_p 등
- 변수 정의표: 각 변수의 소스, 타입, 예시

[프롬프트 기법 선택 가이드라인]
| 기법 | 적용 시점 | 장점 | 단점 |
|------|---------|------|------|
| Zero-shot | 범용 태스크, 대형 모델 사용 시 | 비용 최소, 프롬프트 간결 | 복잡한 추론에 약함 |
| Few-shot | 특정 출력 형식 보장 필요 시 | 출력 일관성 높음 | 토큰 소비 증가 |
| Chain-of-Thought | 다단계 추론, 수학/논리 문제 | 정확도 향상 | 레이턴시·토큰 증가 |
| System prompt + 구조화 | JSON 출력 강제 필요 시 | 파싱 안정성 | 모델별 지원 차이 |

[파라미터 튜닝 가이드라인]
| 파라미터 | 낮은 값 (0~0.3) | 중간 값 (0.5~0.7) | 높은 값 (0.8~1.0) |
|---------|:-:|:-:|:-:|
| temperature | 분류, 추출, JSON 파싱 | 요약, Q&A | 창작, 브레인스토밍 |
| top_p | 결정론적 출력 | 균형 | 다양한 표현 |
```

**프롬프트 관리 전략**:
- 프롬프트 저장소: 코드 내 하드코딩 금지. 외부 저장소(Blob Storage, DB 등) 권장
- 버전 관리: 프롬프트 변경 시 버전 번호 증가
- 무중단 업데이트: 코드 배포 없이 프롬프트 교체 가능한 구조
- A/B 테스트: variant 프롬프트 동시 운영 지원 구조

**2.2.3 모델 선정**

각 AI 기능별 최적 모델을 선정합니다.

```
[모델 선정 기준]
- 품질: 기능 요구사항을 충족하는 최소 모델 선택 (비용 최적화)
- 레이턴시: 사용자 응답 시간 요구사항 충족 여부
- 비용: 토큰 단가 (입력/출력 별도), 예상 월간 비용
- 제약: 토큰 한도, Rate Limit, 리전 가용성

[선정 결과 형식]
| 기능 | 모델 | 선정 근거 | 입력 단가 | 출력 단가 | 예상 레이턴시 |
|------|------|---------|----------|----------|------------|
```

**모델 폴백 체인**: 주 모델 장애 시 대체 모델 또는 비AI 폴백 정의

**2.2.4 RAG (Retrieval-Augmented Generation) 설계** (해당 시)

외부 지식이 필요한 AI 기능에 대해 RAG 파이프라인을 설계합니다.

```
[RAG 설계 항목]
- 인덱싱 파이프라인:
  - 데이터 소스: {문서, DB, API 등}
  - 문서 로더: {PyMuPDF, Docling, 웹 크롤러 등}
  - 청킹 전략: {고정 크기 / 시맨틱 / 재귀적 분할}
  - 임베딩 모델: {OpenAI text-embedding-3-small / Cohere 등}
  - 벡터 DB: {Chroma / Pinecone / pgvector / Azure AI Search 등}
- 검색 파이프라인:
  - 검색 방식: {시맨틱 검색 / 하이브리드(Dense+BM25) / 리랭킹}
  - Top-K: {검색 결과 수}
  - 쿼리 최적화: {Multi-Query / HyDE / 쿼리 재작성}
- GraphRAG 검토:
  - 적용 여부: {엔티티 간 관계 추론이 필요한 경우 검토}
  - 지식 그래프 구축: {엔티티 추출 → 관계 추출 → 그래프 저장소(Neo4j 등)}
  - 검색 방식: {로컬 검색(엔티티 중심) / 글로벌 검색(커뮤니티 요약) / 하이브리드}
  - 벡터 RAG vs GraphRAG 판단 기준: 단순 유사도 검색이면 벡터 RAG, 다단계 관계 추론이 필요하면 GraphRAG
- 평가 지표: {RAGAS — Faithfulness, Answer Relevancy, Context Precision}
- 인덱싱 주기: {실시간 / 배치 / 이벤트 기반}

[RAG 품질 튜닝 전략]
| 튜닝 영역 | 기법 | 적용 시점 |
|----------|------|---------|
| 청킹 | 고정 크기 (RecursiveCharacterTextSplitter) | 기본, 범용 |
| 청킹 | 시맨틱 청킹 (SemanticChunker) | 문서 구조가 불규칙할 때 |
| 임베딩 | 다국어 모델 (multilingual-e5) | 한국어 문서 처리 시 |
| 검색 | Dense 검색 (벡터 유사도) | 기본 |
| 검색 | 하이브리드 (Dense + BM25) | 키워드 정확도 필요 시 |
| 검색 | 리랭킹 (Cross-encoder) | 검색 정밀도 향상 필요 시 |
| 쿼리 | Multi-Query | 질문이 모호할 때 |
| 쿼리 | HyDE (가설 문서 임베딩) | 질문-문서 간 의미 갭이 클 때 |
| 평가 | RAGAS (Faithfulness, Answer Relevancy, Context Precision) | RAG 품질 정량 평가 |
```

**2.2.5 Function Calling 설계** (해당 시)

LLM이 외부 도구를 호출해야 하는 기능에 대해 설계합니다.

```
[Function Calling 설계 항목]
- 도구 정의: {함수명, 설명, 파라미터 스키마}
- 호출 방식: {순차 / 병렬 / 자동 선택}
- LLM 제공자별 구현:
  - OpenAI: tools + tool_choice 파라미터
  - Claude: tools 배열 + tool_use 응답
  - Gemini: function_declarations
- 보안: 도구 실행 권한 범위 제한, 입력 검증

[FC 호출 패턴 비교]
| 패턴 | 설명 | 적용 시점 |
|------|------|---------|
| 순차 호출 | 도구 결과를 다음 호출의 입력으로 사용 | 의존적 도구 체인 |
| 병렬 호출 | LLM이 다수 도구를 동시 호출 요청 | 독립적 도구 조합 |
| 스트리밍 FC | 도구 호출 결과를 스트리밍으로 반환 | 실시간 UX |

[Provider별 FC 차이점]
| 항목 | OpenAI | Claude | Gemini |
|------|--------|--------|--------|
| 파라미터 | tools + tool_choice | tools 배열 | function_declarations |
| 응답 형식 | tool_calls[] | tool_use content block | functionCall |
| 병렬 호출 | parallel_tool_calls=true | 자동 병렬 | automatic_function_calling |
| 고유 기능 | 커스텀 도구 스키마 | 서버 사이드 도구 | 자동 함수 호출 |
```

**2.2.6 MCP (Model Context Protocol) 설계** (해당 시)

표준화된 도구 연동이 필요한 경우 MCP 아키텍처를 설계합니다.

```
[MCP 설계 항목]
- 아키텍처: Host-Client-Server 구조
- 전송 방식: Stdio / SSE / Streamable HTTP
- Primitives: Tools, Resources, Prompts 정의
- MCP 서버 목록: {서버명, 제공 도구, 프로토콜}
- 인증/인가: OAuth 2.1 적용 여부
- 프로토콜: JSON-RPC 2.0
- 고급 기능:
  - Sampling: 서버가 클라이언트를 통해 LLM 호출 요청
  - Elicitation: 서버가 사용자에게 추가 정보 요청
  - Roots: 파일 시스템 루트 경로 제한
- SDK: MCP Python SDK (mcp[cli])
- 인증/인가 상세: OAuth 2.1 플로우 적용 방식
```

**2.2.7 MAS (Multi-Agent System) 설계** (해당 시)

복수 AI 에이전트 협업이 필요한 기능에 대해 설계합니다.

```
[MAS 설계 항목]
- 아키텍처 패턴: {Orchestrator / Choreography / Hierarchical}
- 에이전트 정의: {역할, 도구, 모델}
- 상태 관리: {LangGraph Checkpointer / 외부 DB}
- 내부 통신: {직접 호출 / 메시지 큐 / 이벤트}
- 외부 통신: {API / MCP}
- 프레임워크: {LangGraph / AutoGen / CrewAI / 직접 구현}

[MAS 아키텍처 패턴 비교]
| 패턴 | 설명 | 적용 시점 |
|------|------|---------|
| Orchestrator (중앙 관리) | 하나의 에이전트가 다른 에이전트를 지휘 | 명확한 단계별 워크플로우 |
| Choreography (자율 협업) | 에이전트들이 메시지 기반으로 자율 협업 | 이벤트 기반, 느슨한 결합 |
| Hierarchical (계층적) | 계층별 역할 분리 (관리자 → 실행자) | 복잡한 다단계 작업 |

[LangGraph 워크플로우 설계 항목]
- 상태(State) 정의: TypedDict 기반 그래프 상태
- 노드(Node) 정의: 각 처리 단계
- 엣지(Edge) 정의: 노드 간 전이 조건
- 조건부 분기: should_continue 함수 정의
- Checkpointer: MemorySaver / SqliteSaver / PostgresSaver
- Human-in-the-Loop: interrupt_before / interrupt_after
```

**2.2.8 멀티턴 대화 설계** (해당 시)

대화형 AI 기능에 대해 세션 관리 및 컨텍스트 유지 전략을 설계합니다.

```
[멀티턴 대화 설계 항목]
- 대화 관리 방식: 클라이언트 사이드 / 서버 사이드
  - 클라이언트: 프론트엔드가 전체 대화 이력을 전송 (Stateless 서버)
  - 서버: 세션 ID로 서버가 대화 이력 관리 (Redis/DB 저장)
- 컨텍스트 윈도우 전략:
  - 슬라이딩 윈도우: 최근 N턴만 유지
  - 요약 윈도우: 오래된 대화를 LLM으로 요약 후 컨텍스트에 포함
  - 토큰 기반: 총 토큰 수 제한 내에서 관리
- 세션 저장소: Redis / DB / In-memory
- 세션 TTL: 비활성 세션 만료 시간
```

**2.2.9 멀티모달 AI 설계** (해당 시)

이미지, 문서, 음성 등 다양한 입력을 처리하는 AI 기능을 설계합니다.

```
[멀티모달 AI 설계 항목]
- VLM (Vision Language Model): (해당 시)
  - 이미지 분석 대상: {이미지 유형, 분석 목적}
  - 모델: GPT-4o / Gemini Vision / Qwen-VL 등
  - 입력 형식: Base64 / URL / File upload
  - 출력 형식: 구조화 JSON / 자연어 설명

- PDF/문서 처리: (해당 시)
  - 처리 방식: 규칙 기반(PyMuPDF) / AI 기반(IBM Docling)
  - 추출 대상: 텍스트 / 테이블 / 이미지
  - 출력 형식: Markdown / JSON
  - RAG 인덱싱과의 통합: PDF → 청킹 → 임베딩 파이프라인

- STT (Speech-to-Text): (해당 시)
  - API: OpenAI Whisper / Google STT / 로컬 모델
  - 화자 분리(Diarization): 필요 여부
  - 지원 언어 및 파일 형식

- TTS (Text-to-Speech): (해당 시)
  - API: OpenAI TTS / Google TTS / 로컬 모델
  - 음성 모델: 사용할 음성 선택
  - 스트리밍 지원 여부
```

**2.2.10 외부 데이터 소스 통합 설계** (해당 시)

웹검색, YouTube 등 외부 실시간 데이터 소스와의 통합을 설계합니다.

```
[외부 데이터 소스 설계 항목]
- 웹검색: (해당 시)
  - 검색 API: Tavily / DuckDuckGo / Google Custom Search
  - Agent 통합: LangGraph 기반 멀티소스 Agent
  - 캐싱: 검색 결과 캐싱 TTL
  - 안정성: 재시도/폴백/Circuit Breaker

- YouTube/동영상: (해당 시)
  - 트랜스크립트 추출 / 요약
  - 데이터 소스로 RAG 통합

- 멀티소스 RAG:
  - 복수 데이터 소스 조합 전략
  - 소스별 가중치 / 우선순위
```

**2.2.11 Local LLM 설계** (해당 시)

온프레미스 또는 프라이버시 요구사항이 있는 경우 Local LLM 옵션을 설계합니다.

> **참고**: Local LLM은 설계 전용 섹션이며, 개발 가이드에서는 `init_chat_model(model_provider="ollama")`를 통한 연동만 간략히 안내한다 (별도 구현 단계 없음). 인프라 세팅이 프로젝트마다 크게 달라 범용 개발 가이드화가 어렵기 때문이다.

```
[Local LLM 설계 항목] (해당 시)
- 적용 시점: 데이터 프라이버시 / 오프라인 / 비용 절감 요구 시
- 런타임: Ollama / vLLM / llama.cpp
- 모델 선택: 용도별 모델 (코드 생성, 한국어 특화 등)
- 양자화: 4-bit / 8-bit GPTQ/GGUF
- 하드웨어: GPU VRAM 요구사항
- LangChain 연동: init_chat_model(model_provider="ollama")
- 성능 최적화: GPU 레이어, 컨텍스트 크기 지정 등
```

#### 2.3 AI API 설계

AI 서비스가 제공하는 내부 API를 설계합니다.

```
[API 설계 항목]
- 엔드포인트: {HTTP Method} {Path}
- 요청 스키마: JSON 형식, 필수/선택 필드
- 응답 스키마: JSON 형식, AI 생성 결과 + 메타데이터(source, model_used)
- 요청 헤더: trace_id 전파, 사용자 티어, 타임아웃 힌트
- 타임아웃: 기능별 타임아웃 설정 (LLM 모델 성능 고려)
- 비동기 처리: 호출자 ↔ AI 서비스 간 비동기 통신 방식
```

#### 2.4 에러 핸들링 및 복원력 설계

```
[에러 분류 및 처리 전략]
- HTTP 429 (Rate Limit): 즉시 폴백, 재시도 없음
- HTTP 500/503 (서버 오류): 지수 백오프 재시도 (최대 N회) → Circuit Breaker
- HTTP 400 (잘못된 요청): 재시도 없음, 로깅 후 폴백
- Timeout: 즉시 폴백 (사용자 대기 최소화)
- JSON 파싱 실패: 폴백 + 프롬프트 검토 알림

[Circuit Breaker 설정]
- slidingWindowSize: {윈도우 크기}
- failureRateThreshold: {실패율 임계값 %}
- waitDurationInOpenState: {대기 시간}
- permittedCallsInHalfOpenState: {테스트 호출 수}

[폴백 전략]
- 템플릿 기반 폴백: AI 없이 규칙 기반 응답 생성
- 캐시 폴백: 이전 AI 응답 재사용
- Graceful Degradation: 기능 축소 제공 + 사용자 안내 메시지
```

#### 2.5 비용 및 성능 최적화 설계

```
[토큰 사용량 예측]
| 기능 | 모델 | 입력 tokens | 출력 tokens | 일 호출 수 | 월간 비용 |
|------|------|:-----------:|:-----------:|:----------:|:--------:|

[비용 최적화 전략]
- 응답 캐싱: 동일 입력 조건의 AI 응답 캐싱 (키 설계, TTL)
- 배치 처리: 복수 항목을 단일 API 호출로 처리
- 최소 적합 모델: 각 기능에 충분한 최소 모델 선택
- 프롬프트 최적화: 불필요한 토큰 제거, 시스템 프롬프트 공유
- Azure OpenAI Prompt Caching: 동일 prefix 자동 할인 (해당 시)

[성능 최적화 전략]
- 레이턴시 목표: 기능별 p95 응답시간 목표
- 스트리밍: 사용자 체감 응답 속도 개선 (SSE)
- 비동기 호출: 논블로킹 I/O (asyncio, WebClient 등)
- 사전 생성: 스케줄러 기반 AI 응답 미리 생성
```

#### 2.6 모니터링 및 품질 관리 설계

```
[모니터링 지표]
| 지표 | 설명 | 목표값 | Alert 기준 |
|------|------|:------:|----------|
| AI 응답 성공률 | 폴백 제외 AI 생성 비율 | > 95% | < 90% |
| 평균 응답 레이턴시 | AI 전체 응답시간 | p95 < {N}초 | p95 > {N}초 |
| Circuit Breaker 상태 | Open 전환 횟수 | 0회/일 | Open 발생 |
| 토큰 사용량 | 일일 모델별 소비량 | 예산 내 | 90% 초과 |
| 파싱 실패율 | AI 응답 스키마 불일치 | < 1% | > 5% |

[품질 추적]
- 프롬프트 버전별 성능 비교 (레이턴시, 성공률, 토큰 효율)
- A/B 테스트: 프롬프트 변경 시 점진적 배포 및 비교 평가
- 사용자 행동 기반 품질 신호 (클릭률, 완료율 등 간접 지표)

[장애 대응 시나리오]
| 시나리오 | 감지 방법 | 자동 대응 | 수동 대응 |
|---------|---------|---------|---------|
```

#### 2.7 AI 서비스 구조 설계

AI 서비스의 내부 디렉토리 구조와 컴포넌트를 설계합니다.

```
[서비스 구조 예시]
{service-name}/
├── main.py                    # 앱 진입점
├── routers/                   # API 라우터
├── services/                  # 비즈니스 로직
├── clients/                   # 외부 API 클라이언트 (LLM, 벡터 DB 등)
├── models/                    # 요청/응답 모델 (Pydantic 등)
├── prompts/                   # 프롬프트 템플릿 로더
├── cache/                     # 응답 캐시
├── fallback/                  # 폴백 로직
├── rag/                       # RAG 파이프라인 (해당 시)
│   ├── indexer.py
│   ├── retriever.py
│   └── embeddings.py
├── tools/                     # Function Calling 도구 정의 (해당 시)
├── agents/                    # MAS 에이전트 정의 (해당 시)
├── workflows/                 # LangGraph 워크플로우 (해당 시)
├── mcp_server/                # MCP 서버 (해당 시)
├── multimodal/                # VLM/STT/TTS 처리 (해당 시)
├── conversation/              # 멀티턴 대화 관리 (해당 시)
├── external/                  # 외부 데이터 소스 (웹검색 등, 해당 시)
└── config.py                  # 설정
```

#### 2.8 HighLevel 아키텍처 일치성 검증

AI 서비스 설계가 기존 산출물과 일치하는지 검증합니다.

```
[검증 항목]
| 기존 산출물 항목 | 본 설계서 구현 | 일치 여부 |
|---------------|-------------|:--------:|
```

### 3. 검토

- 모든 AI 기능이 유저스토리와 매핑되는지 확인
- 논리 아키텍처의 AI 서비스 경계와 일치하는지 확인
- 폴백 전략이 모든 장애 시나리오를 커버하는지 확인
- 비용 예측이 예산 범위 내인지 확인
- HighLevel 아키텍처 정의서와 일치성 검증

## 출력 형식

```markdown
# AI 서비스 설계서

> 작성자: {닉네임} ({역할})
> 작성일: {날짜}
> 근거: {참조 산출물 목록}

## 1. AI 기능 확인 및 우선순위
### 1.1 이전 단계 식별 AI 기능 목록
### 1.2 우선순위 정리 (P1/P2/P3)
### 1.3 MVP vs 향후 확장 구분

## 2. AI 모델 선정
### 2.1 기능별 모델 매핑
### 2.2 모델 선정 근거
### 2.3 LLM API 배포 설정

## 3. AI API 연동 설계
### 3.1 LLM API 엔드포인트
### 3.2 요청/응답 스키마
### 3.3 Rate Limiting 및 토큰 사용량 관리
### 3.4 에러 핸들링 및 재시도 전략
### 3.5 비용 최적화 전략

## 4. 프롬프트 설계
### 4.1 {기능1} 프롬프트
### 4.2 {기능2} 프롬프트
### 4.N 프롬프트 버전 관리 전략

## 5. AI 기능 아키텍처
### 5.1 AI 파이프라인 전체 흐름도 (Mermaid)
### 5.2 {기능1} AI 흐름 (Mermaid Sequence)
### 5.N AI 서비스 구조

## 6. RAG 설계 (해당 시)
### 6.1 인덱싱 파이프라인
### 6.2 검색 파이프라인
### 6.3 평가 및 튜닝

## 7. Function Calling 설계 (해당 시)
### 7.1 도구 정의 및 호출 패턴
### 7.2 Provider별 구현 방식

## 8. MCP 설계 (해당 시)
### 8.1 MCP 서버 정의 (Tools, Resources, Prompts)
### 8.2 전송 방식 및 인증

## 9. MAS 설계 (해당 시)
### 9.1 에이전트 정의 및 아키텍처 패턴
### 9.2 LangGraph 워크플로우

## 10. 멀티턴 대화 설계 (해당 시)

## 11. 멀티모달 AI 설계 (해당 시)
### 11.1 VLM / PDF / STT / TTS

## 12. 외부 데이터 소스 통합 설계 (해당 시)
### 12.1 웹검색 / YouTube / 멀티소스 RAG

## 13. Local LLM 설계 (해당 시)

## 14. 성능 및 비용 최적화
### 14.1 토큰 사용량 예측
### 14.2 캐싱 전략 상세
### 14.3 배치 처리 가능 영역

## 15. 모니터링 및 품질 관리
### 15.1 AI 응답 품질 모니터링 지표
### 15.2 프롬프트 성능 추적
### 15.3 A/B 테스트 전략
### 15.4 장애 대응 시나리오

## 16. HighLevel 아키텍처 일치성 검증

## 17. 구현 우선순위 및 일정
```

## 품질 기준

### 완료 체크리스트
- [ ] 모든 AI 기능이 유저스토리 ID와 매핑됨
- [ ] 논리 아키텍처의 AI 서비스 경계와 일치
- [ ] 모델 선정 근거가 명확함 (비용, 레이턴시, 품질)
- [ ] 모든 프롬프트에 버전 ID가 부여됨
- [ ] 모든 AI API에 요청/응답 스키마가 정의됨
- [ ] 폴백 전략이 모든 장애 시나리오를 커버함
- [ ] 비용 예측이 예산 범위 내임
- [ ] Circuit Breaker 설정이 명시됨
- [ ] 모니터링 지표와 Alert 기준이 정의됨
- [ ] HighLevel 아키텍처 정의서와 일치성 검증 완료
- [ ] RAG/FC/MCP/MAS 해당 시 설계 포함
- [ ] 멀티턴 대화 설계 포함 (해당 시)
- [ ] 멀티모달 AI 설계 포함 (VLM/PDF/STT/TTS — 해당 시)
- [ ] 외부 데이터 소스 통합 설계 포함 (웹검색/YouTube — 해당 시)
- [ ] Local LLM 설계 포함 (해당 시)
- [ ] LLM Provider 비교표 작성 완료
- [ ] 프롬프트 기법 선택 근거 명시

## 주의사항

- **"AI를 위한 AI" 금지**: 측정 가능한 사용자 가치가 있는 AI 기능만 설계
- **최소 적합 모델 원칙**: 기능 요구사항을 충족하는 가장 저렴한 모델 선택
- **폴백 필수**: AI 장애 시에도 서비스 연속성 보장 (비AI 폴백)
- **프롬프트 하드코딩 금지**: 외부 저장소 기반 관리 권장
- **비용 통제**: Rate Limiting + 토큰 사용량 모니터링 필수
- 설계 공통 원칙: `{PLUGIN_DIR}/resources/guides/design/common-principles.md` 준용
