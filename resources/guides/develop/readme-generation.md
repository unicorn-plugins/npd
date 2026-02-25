# README.md 생성 가이드

## 목적

개발 완료된 프로젝트의 README.md를 자동 생성한다.
기존 산출물(개발 계획서, 아키텍처 정의서, API 명세, docker-compose 등)에서 정보를 추출하여
프로젝트 루트에 표준 README.md를 작성한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 종합 개발 계획서 | `docs/develop/dev-plan.md` | 서비스 개요, 핵심 기능, 서비스 목록 추출 |
| HighLevel 아키텍처 | `docs/design/high-level-architecture.md` | 기술 스택, 아키텍처 다이어그램, 시스템 구성도 추출 |
| API 명세 | `docs/design/api/*.yaml` | 서비스별 주요 엔드포인트 요약 |
| 환경변수 템플릿 | `./.env.example` | 필요 환경변수 목록 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| README 파일 | `README.md` |

## 방법론

### 작성 원칙

- **산출물 기반**: 모든 내용은 기존 산출물에서 추출하며, 임의로 생성하지 않는다
- **실행 가능**: 시작하기 섹션은 복사-붙여넣기만으로 서비스를 기동할 수 있어야 한다
- **간결성**: 각 섹션은 핵심만 기술하고, 상세 내용은 docs/ 하위 문서로 링크한다
- **플랫폼 분기**: 프론트엔드 실행 방법은 프로젝트의 PLATFORM(React/Vue/Flutter)에 맞는 것만 표시한다

### 정보 추출 순서

#### 1. 프로젝트 개요 추출

`docs/develop/dev-plan.md`에서:
- 서비스명
- 한 줄 소개
- 핵심 기능 목록 (bullet)

#### 2. 기술 스택 추출

`docs/design/high-level-architecture.md`의 기술스택 섹션에서:
- 백엔드 (언어, 프레임워크, 빌드 도구)
- 프론트엔드 (프레임워크, 상태관리, 스타일링)
- AI 서비스 (해당 시: 프레임워크, LLM 제공자)
- 인프라 (DB, Cache, MQ, 컨테이너)

#### 3. 시작하기 정보 추출

`./.env.example`에서:
- 사전 요구사항 (Java, Node.js, Docker 등 — 기술스택에서 유추)
- 환경변수 설정 방법 (`.env.example` → `.env` 복사 후 값 입력)

`./docker-compose.yml`에서:
- 백킹서비스 기동 명령

실행 프로파일에서:
- 백엔드 서비스 기동 명령

프론트엔드 프로젝트에서:
- 프론트엔드 기동 명령 (PLATFORM에 따라 분기)

#### 4. API 엔드포인트 요약

`docs/design/api/*.yaml`에서:
- 서비스별 엔드포인트 테이블 (Method, Path, 설명)
- 전체를 나열하지 않고 서비스당 주요 5개 이내로 요약
- 상세는 `docs/design/api/` 링크로 안내

#### 5. 아키텍처 요약

`docs/design/high-level-architecture.md`에서:
- 시스템 구성도 (Mermaid 다이어그램이 있으면 그대로 삽입)
- 없으면 서비스 간 관계를 텍스트로 간략 기술

## 출력 형식

```markdown
# {서비스명}

> {한 줄 소개}

## 주요 기능

- {기능 1}
- {기능 2}
- ...

## 기술 스택

| 영역 | 기술 |
|------|------|
| 백엔드 | {Java 17, Spring Boot 3.x, Gradle} |
| 프론트엔드 | {React 18, TypeScript, Tailwind CSS} |
| AI 서비스 | {Python 3.11, FastAPI, LangChain} |
| 데이터베이스 | {PostgreSQL 16} |
| 캐시 | {Redis 7} |
| 컨테이너 | {Docker Compose} |

## 시작하기

### 로컬 수행

#### 사전 요구사항

- Java {version}
- Node.js {version}
- Docker & Docker Compose
- Python {version} (AI 서비스 해당 시)

#### 실행

```bash
# 1. 백킹서비스 기동
docker compose up -d

# 2. 백엔드 서비스 기동
python3 tools/run-intellij-service-profile.py --config-dir . --delay 5

# 3. 프론트엔드 기동
<!-- IF PLATFORM == REACT -->
cd frontend && npm run dev
<!-- ELIF PLATFORM == VUE -->
cd frontend && npm run dev
<!-- ELIF PLATFORM == FLUTTER -->
cd frontend && flutter run -d web-server
<!-- ENDIF -->

# 4. AI 서비스 기동 (해당 시)
docker compose --profile ai up -d
```

#### 중지

```bash
# 백킹서비스 + AI 서비스 중지
docker compose down

# 백엔드 서비스 중지
python3 tools/run-intellij-service-profile.py --stop

# 프론트엔드 중지
<!-- IF PLATFORM == REACT -->
# 실행 중인 터미널에서 Ctrl+C
<!-- ELIF PLATFORM == VUE -->
# 실행 중인 터미널에서 Ctrl+C
<!-- ELIF PLATFORM == FLUTTER -->
# 실행 중인 터미널에서 'q' 입력
<!-- ENDIF -->
```

## 라이선스

This project is proprietary and confidential.
```

## 품질 기준

### 완료 체크리스트
- [ ] `README.md`가 프로젝트 루트에 생성됨
- [ ] 프로젝트 소개 및 주요 기능이 dev-plan.md 기반으로 작성됨
- [ ] 기술 스택이 high-level-architecture.md 기반으로 정확하게 나열됨
- [ ] 프로젝트 구조가 실제 디렉토리와 일치
- [ ] 시작하기 섹션의 명령이 실제 실행 가능
- [ ] 환경변수 목록이 .env.example과 일치
- [ ] API 엔드포인트가 API 명세와 일치
- [ ] AI 서비스 섹션은 해당 시에만 포함
- [ ] 프론트엔드 기동 명령이 PLATFORM에 맞게 분기됨

## 주의사항

- 기존 `README.md`가 있으면 덮어쓰지 말고 사용자에게 확인할 것
- docs/ 하위 문서 링크는 상대 경로 사용
- Mermaid 다이어그램 삽입 시 ```mermaid 코드 블록 사용
- .env 파일의 실제 값(비밀번호, API 키 등)을 README에 포함하지 않을 것
- AI 서비스가 없는 프로젝트는 관련 섹션을 모두 제외할 것
