# 클래스설계가이드

## 목적
API 설계서와 내부 시퀀스 설계서를 기반으로, 마이크로서비스 아키텍처에 맞는 서비스별 클래스 설계서를 작성한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| API 설계서 | `docs/design/api/` | Controller 클래스 메소드 매핑 |
| 내부 시퀀스 | `docs/design/sequence/inner/` | 레이어별 클래스 도출 |
| 이벤트 스토밍 | `docs/plan/think/es/*.puml` | 도메인 모델 확인 |
| 클래스 설계서 예제 | `{PLUGIN_DIR}/resources/samples/sample-클래스설계서.puml` | 참조 |
| AI 서비스 설계서 | `docs/design/ai-service-design.md` | AI 클래스 구조 참조 (Step 9 완료 후 생성됨 — 설계 시점에는 논리 아키텍처의 AI 섹션을 참조) |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 공통 컴포넌트 | `docs/design/class/common-base.puml` |
| 서비스별 상세 클래스 | `docs/design/class/{service-name}.puml` |
| 서비스별 요약 클래스 | `docs/design/class/{service-name}-simple.puml` |
| 패키지 구조도 | `docs/design/class/package-structure.md` |

service-name은 영어로 작성 (예: profile, location, itinerary)
 
## 방법론

### 작성원칙
- **유저스토리와 매칭**되어야 함. **불필요한 추가 설계 금지**
- API설계서와 일관성 있게 설계. Controller에 API를 누락하지 말고 모두 설계
  - Controller 클래스는 API로 정의하지 않은 메소드 생성 안함. 단, 필요한 Private 메소드는 추가함
  - {service-name}-simple.puml파일에 Note로 Controller 클래스 메소드와 API 매핑표 작성: {Methond}: {API Path} {API 제목}
    예) login: /login 로그인
- 내부시퀀스설계서와 일관성 있게 설계
- 각 서비스별 지정된 {설계 아키텍처 패턴}을 적용
- Clean아키텍처 적용 시 Port/Adapter라는 용어 대신 Clean 아키텍처에 맞는 용어(Usecase, Controller, Gateway 등) 사용
- 클래스의 프라퍼티와 메소드를 모두 기술할 것. 단 "Getter/Setter 메소드"는 작성하지 않음
- 클래스 간의 관계를 표현: Generalization, Realization, Dependency, Association, Aggregation, Composition
- **마이크로서비스 아키텍처 기반 설계**

### AI 서비스 클래스 설계 원칙 (Python/FastAPI)

AI Pipeline 서비스의 클래스는 ai-engineer가 직접 설계하며, 다음 원칙을 준수한다:

- **기술 스택**: Python/FastAPI 기반, Pydantic 모델 사용
- **핵심 클래스 구조**:
  - `Router`: FastAPI 라우터 (Controller 역할)
  - `PromptBuilder`: 프롬프트 템플릿 조합 및 변수 바인딩
  - `LLMClient`: LLM API 호출 (비동기, 재시도, 서킷브레이커)
  - `ResponseParser`: LLM 응답 파싱 및 검증
  - `CacheManager`: AI 응답 캐시 관리
- **Pydantic 모델**: 요청/응답 스키마를 Pydantic BaseModel로 정의
- **PlantUML 표현**: Python 클래스는 `<<dataclass>>` 또는 `<<pydantic>>` 스테레오타입 사용

### 작성순서
- 1단계: 공통 컴포넌트 설계 (순차적)
  - 결과: common-base.puml

- 2단계: 서비스별 병렬 설계 (병렬 실행)
  - 1단계 공통 컴포넌트 참조
  - '!include'는 사용하지 말고 필요한 인터페이스 직접 정의
  - 클래스 설계 후 프라퍼티와 메소드를 생략한 간단한 클래스설계서도 추가로 작성
  - AI Pipeline 서비스: ai-engineer가 Python/FastAPI 기반 클래스를 설계 (architect의 Spring Boot 서비스와 병렬)
  - 결과:
    - {service-name}.puml
    - {service-name}-simple.puml

  - 병렬 처리 기준
    - 서비스 간 의존성이 없는 경우: 모든 서비스 동시 실행
    - 의존성이 있는 경우: 의존성 그룹별로 묶어서 실행
      - 예: A→B 의존 시, A 완료 후 B 실행
      - 독립 서비스 C,D는 A,B와 병렬 실행

- 3단계: 통합 및 검증 (순차적)
  - '패키지구조표준'(`{PLUGIN_DIR}/resources/standards/standard_package_structure.md`)의 예시를 참조하여 모든 클래스와 파일이 포함된 패키지 구조도를 작성
    (plantuml 스크립트가 아니라 트리구조 텍스트로 작성)
  - 인터페이스 일치성 검증
  - 명명 규칙 통일성 확인
  - 의존성 검증
  - 크로스 서비스 참조 검증
  - **PlantUML 스크립트 파일 검사 실행**

## 품질 기준

- [ ] `!theme mono` 사용
- [ ] API 설계서/내부 시퀀스와 일관성 확인
- [ ] PlantUML 문법 검사 통과
- [ ] ORM 설정 코드 미포함
- [ ] AI Pipeline 서비스 클래스가 Python/FastAPI 기반으로 설계됨
- [ ] AI 클래스가 논리 아키텍처의 AI 서비스 정의와 일치

## 주의사항

- 설계 공통 원칙: `{PLUGIN_DIR}/resources/guides/design/common-principles.md` 준용
- 유저스토리에 없는 클래스/메소드 추가 금지
- Controller 클래스는 API 정의 기준으로만 메소드 생성 (Private 메소드 예외)
- `!include` 사용 금지 — 필요한 인터페이스는 각 파일에 직접 정의
- Clean 아키텍처 적용 시 Port/Adapter 용어 미사용
- Getter/Setter 메소드 작성 금지
- 서비스 간 크로스 참조 금지 (마이크로서비스 독립성 유지)
