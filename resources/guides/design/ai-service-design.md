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

**기반 프레임워크**: LangChain (기본) — RAG·Function Calling·Agent 등 복합 패턴 적용 시 필수. 단순 LLM API 호출은 직접 구현 허용.

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
- LangChain 연동: ChatOpenAI / ChatAnthropic / ChatGoogleGenerativeAI 등
- API 엔드포인트: 베이스 URL, 배포 이름 (Azure의 경우)
- 인증 방식: API Key / Managed Identity / OAuth
- SDK: LangChain 통합 SDK (langchain-openai / langchain-anthropic / langchain-google-genai 등)
- API 버전: 사용할 API 버전 명시
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

## 7. Function Calling / MCP / MAS 설계 (해당 시)

## 8. 성능 및 비용 최적화
### 8.1 토큰 사용량 예측
### 8.2 캐싱 전략 상세
### 8.3 배치 처리 가능 영역

## 9. 모니터링 및 품질 관리
### 9.1 AI 응답 품질 모니터링 지표
### 9.2 프롬프트 성능 추적
### 9.3 A/B 테스트 전략
### 9.4 장애 대응 시나리오

## 10. HighLevel 아키텍처 일치성 검증

## 11. 구현 우선순위 및 일정
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

## 주의사항

- **"AI를 위한 AI" 금지**: 측정 가능한 사용자 가치가 있는 AI 기능만 설계
- **최소 적합 모델 원칙**: 기능 요구사항을 충족하는 가장 저렴한 모델 선택
- **폴백 필수**: AI 장애 시에도 서비스 연속성 보장 (비AI 폴백)
- **프롬프트 하드코딩 금지**: 외부 저장소 기반 관리 권장
- **비용 통제**: Rate Limiting + 토큰 사용량 모니터링 필수
- 설계 공통 원칙: `{PLUGIN_DIR}/resources/guides/design/common-principles.md` 준용
