# High Level 아키텍처 정의 가이드

## 목적

모든 설계 산출물을 종합하여 시스템 전체를 조망하는 HighLevel 아키텍처 정의서를 작성함. 논리/물리/개발/보안 아키텍처를 통합하고 주요 기술 의사결정(ADR)을 기록함.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 아키텍처 패턴 선정 설계서 | `docs/design/pattern-definition.md` | 참조 |
| 논리 아키텍처 설계서 | `docs/design/logical-architecture.md` | 참조 |
| 외부 시퀀스 다이어그램 | `docs/design/sequence/outer/{유저 플로우명}.puml` | 참조 | 
| 내부 시퀀스 다이어그램 | `docs/design/sequence/inner/{서비스명}-{시나리오}.puml` | 참조 |
| 클래스설계서 | `docs/design/class/{service-name}-simple.puml` | 참조 |
| 패키지 구조도 | `docs/design/class/package-structure.md` | 참조 |
| 데이터설계서 | `docs/design/database/{service-name}.md` (시작 부분에 '데이터설계 요약' 포함) |
| 캐시 DB 설계서 | `docs/design/database/cache-db-design.md` (Redis database 할당표 포함) |
| 유저스토리 | `docs/plan/design/userstory.md` | 아키텍처 범위 확인 |
| UI/UX 설계서(기획 산출물) | `docs/plan/design/uiux/uiux.md` | 참조 | 
| HighLevel아키텍처정의서템플릿 | `{PLUGIN_DIR}/resources/templates/highlevel-architecture-template.md` | 작성 템플릿 |
| High Level 아키텍처 정의서 예제 | `{PLUGIN_DIR}/resources/samples/sample-highlevel아키텍처정의서.md` | 참조 |
| AI 서비스 설계서 | `docs/design/ai-service-design.md` | AI 아키텍처 섹션 참조 (Step 9 완료 후 생성됨) |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| HighLevel 아키텍처 정의서 | `docs/design/high-level-architecture.md` |

## 방법론

### 1. 준비

- 입력 산출물을 분석 및 이해합니다.

### 2. 실행

'HighLevel아키텍처정의서템플릿'을 이용하여 작성합니다.

#### 섹션별 작성 가이드

**1. 개요 (Executive Summary)**
- 1.2 아키텍처 범위 및 경계: 유저스토리, 논리아키텍처, 외부시퀀스설계서와 일치하게 작성

**4. 논리 아키텍처 (Logical View)**
- 시스템 컨텍스트 다이어그램: 논리아키텍처 경로 지정
- 4.2.2 바운디드 컨텍스트: mermaid 형식으로 작성

**5. 프로세스 아키텍처 (Process View)**
- 5.1.1 핵심 사용자 여정: '유저스토리'와 'UI/UX 설계서(기획 산출물)' 참조하여 mermaid 형식으로 작성
- 5.1.2 시스템 간 통합 프로세스: '외부시퀀스설계'의 경로 지정

**6. 개발 아키텍처 (Development View)**
- 6.1.1 백엔드 기술스택: 핵심서비스는 Spring Boot를 우선 고려, AI 구현 서비스는 파이썬 우선 고려
- 6.1.2 프론트엔드 기술스택: 유저스토리와 UI/UX 설계서(기획 산출물) 참조하여 최적안 추천
- 6.2 서비스별 개발 아키텍처 패턴: 클래스설계서에 적용된 '설계 아키텍처 패턴'과 일치(Layered 또는 Clean Architecture)
- 6.3 개발 가이드라인:
  - 코딩표준: '개발주석표준' 주소 링크 - https://github.com/unicorn-plugins/npd/blob/main/resources/standards/standard_comment.md
  - 테스트 전략: '테스트코드표준' 주소 링크 - https://github.com/unicorn-plugins/npd/blob/main/resources/standards/standard_testcode.md

**7. 물리 아키텍처 (Physical View)**
- 7.1 클라우드 아키텍처 패턴: '아키텍처패턴'과 일치하게 작성
- 7.2 인프라스트럭처 구성: {CLOUD}에 제시된 클라우드 제공자에 기준하여 작성

**8. 기술 스택 아키텍처**
- 작성원칙 참조하여 작성: {CLOUD}플랫폼에 최적화된 제품/서비스로 구성, GA된 최신 버전 사용

**9. AI/ML 아키텍처**
- 9.1.1 AI 서비스/모델 매핑: 논리아키텍처, 외부시퀀스설계, AI 서비스 설계서와 일치하게 작성
- 9.1.2 AI 서비스 아키텍처 개요: AI 서비스 설계서의 아키텍처 다이어그램 참조
- 9.2 프롬프트 관리 전략: AI 서비스 설계서의 프롬프트 설계 섹션 참조
- 9.3 AI 비용/성능 최적화: AI 서비스 설계서의 비용·성능 최적화 섹션 참조

**10. 개발 운영 (DevOps)**
- 10.1.1 지속적 통합 (CI): Jenkins, GitHub Actions, {CLOUD} 관리형 서비스 중 적절한것 추천
- 10.1.2 지속적 배포 (CD): ArgoCD, {CLOUD} 관리형 서비스 중 적절한 것 추천
- 10.2 컨테이너 오케스트레이션: {CLOUD}플랫폼에 맞게 작성

**11. 보안 아키텍처**
- {CLOUD} 플랫폼에 맞게 작성

**12. 품질 속성 구현 전략**
- '아키텍처패턴'과 '데이터설계서'와 일치하게 작성

**13. 아키텍처 의사결정 기록 (ADR)**
- 설계 과정의 주요 아키텍처 의사결정 작성 (후보, 장단점, 의사결정 이유 등)

**16. 부록**
- 16.3 관련 문서: 참고자료의 산출물명과 파일 경로 명시

### 3. 검토

- 작성원칙 준수 검토
- 수정 사항 선택 및 반영

## 출력 형식
'HighLevel아키텍처정의서템플릿' 참조 

## 품질 기준

### 완료 체크리스트
- [ ] 모든 설계 산출물과 일치 확인
- [ ] ADR (Architecture Decision Records) 필수 포함
- [ ] 기존 설계 산출물과 모순 없음
- [ ] {CLOUD}플랫폼에 최적화된 기술 스택 선정
- [ ] 개발언어/프레임워크/AI모델은 GA된 최신 버전 사용

## 주의사항
- 설계 공통 원칙: `{PLUGIN_DIR}/resources/guides/design/common-principles.md` 준용
- {CLOUD}플랫폼에 최적화된 제품/서비스로 구성
- 개발언어, 개발 프레임워크, AI모델은 `{PLUGIN_DIR}/resources/references/제품버전참조.md`를 참조하여 GA된 최신 버전 사용
- 유저스토리, 논리아키텍처, 외부시퀀스설계서 간 일관성 유지

