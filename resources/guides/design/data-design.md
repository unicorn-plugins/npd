# 데이터설계가이드

## 목적
클래스 설계서의 Entity 정의를 기반으로 서비스별 독립 데이터베이스 설계서, ERD, 스키마 스크립트, 캐시 DB 설계서를 작성한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 클래스 설계서 | `docs/design/class/` | Entity-테이블 매핑 |
| 논리 아키텍처 | `docs/design/logical-architecture.md` | 캐시 대상 서비스 파악 |
| 데이터베이스설계서 예제 | `{PLUGIN_DIR}/resources/samples/sample-데이터설계서.puml` | 참조 |
| 캐시DB설계서 예제 | `{PLUGIN_DIR}/resources/samples/sample-cache-db-design.md` | 참조 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 데이터 설계서 | `docs/design/database/{service-name}.md` (시작 부분에 '데이터설계 요약' 포함) |
| ERD | `docs/design/database/{service-name}-erd.puml` |
| DB 스키마 스크립트 | `docs/design/database/{service-name}-schema.md` |
| 캐시 DB 설계서 | `docs/design/database/cache-db-design.md` (Redis database 할당표 포함) |
service-name은 영어로 작성

## 방법론

### 작성원칙
- **클래스설계서의 각 서비스별 Entity정의와 일치**해야 함. **불필요한 추가 설계 금지**
- '데이터독립성원칙'에 따라 각 서비스마다 데이터베이스를 분리
- '캐시DB분리원칙'에 따라 Redis database 번호로 서비스별 캐시 영역을 분리
- 기본 DBMS: PostgreSQL. 서비스별 다른 DBMS 사용 시 스키마 문법을 해당 DBMS에 맞게 조정
- AI 서비스 관련 데이터 저장소를 포함하여 설계 (ai-engineer 검토 대상):
  - **벡터 DB** (RAG 적용 시): 임베딩 스키마, 인덱스 설정, 유사도 검색 파라미터
  - **프롬프트 저장소**: 프롬프트 템플릿 버전 관리 테이블
  - **AI 응답 캐시**: Redis DB에 AI 응답 캐시 키 패턴(`ai:response:{기능}:{해시}`) 및 TTL 정책

### 작성순서
- 준비:
  - 클래스설계서 분석 및 이해
  - 논리아키텍처의 '3.1 캐싱 전략 (Cache-Aside)' 섹션에서 캐싱 사용 서비스 파악 
- 실행:
  - '병렬처리' 안내에 따라 각 서비스별 병렬 수행
  - 데이터설계서 작성
    - 캐시 사용 시 서비스별 캐시 설계 포함 (캐시 대상, 키 패턴, TTL 정책)
    - 시작 부분에 '데이터설계 요약' 제공
    - 결과: {service-name}.md
  - ERD 작성
    - 결과: {service-name}-erd.puml
    - **PlantUML 스크립트 파일 생성 즉시 검사 실행**: 'PlantUML 문법 검사  가이드' 준용
  - 데이터베이스 스키마 스크립트 작성
    - 실행 가능한 SQL 스크립트 작성
    - 결과: {service-name}-schema.psql
  - 캐시DB 설계서 작성
    - '캐시DB분리원칙'에 따라 Redis database 할당표 작성
    - 결과: cache-db-design.md
- 검토:
  - '작성원칙' 준수 검토

### 병렬처리
Agent 1~N: 각 서비스별 데이터베이스 설계
- 서비스별 독립적인 스키마 설계
- Entity 클래스와 1:1 매핑
- 서비스 간 데이터 공유 금지
- FK 관계는 서비스 내부에서만 설정

### 데이터독립성원칙
- **데이터 소유권**: 각 서비스가 자신의 데이터 완전 소유
- **크로스 서비스 조인 금지**: 서비스 간 DB 조인 불가
- **이벤트 기반 동기화**: 필요시 이벤트/메시지로 데이터 동기화
- **캐시 활용**: 타 서비스 데이터는 캐시로만 참조

### 캐시DB분리원칙
- **논리적 분리 방식**: Redis database 번호(0~15)를 사용하여 서비스별 캐시 영역 분리
- **공통 캐시 분리**: 여러 서비스가 공유하는 데이터는 별도의 공통 Redis database에 저장
- **database 할당 규칙**:
  - DB 0: 공통 영역 (세션, 인증 토큰, 공유 설정 등)
  - DB 1~14: 서비스별 전용 캐시 (서비스당 1개 DB 할당)
  - 이 중 1개 DB를 AI Pipeline 서비스 전용 캐시로 할당 (AI 응답 캐시, 프롬프트 캐시)
  - DB 15: 예비 영역
- **Key Naming Convention**: `{domain}:{entity}:{id}` 형식 권장
  - 예시: `user:session:abc123`, `product:catalog:PRD001`
- **격리 원칙**: 각 서비스는 자신에게 할당된 database만 접근하며, 타 서비스 database 직접 참조 금지
- **공통 데이터 접근**: 공통 영역(DB 0) 데이터가 필요한 경우에만 해당 database 접근 허용
- **설정 예시**:
```yaml
  # 서비스별 application.yml 설정
  spring:
    data:
      redis:
        host: ${REDIS_HOST:localhost}
        port: ${REDIS_PORT:6379}
        database: ${REDIS_DATABASE:1}  # 서비스별 할당된 DB 번호
```

## 품질 기준

- [ ] 클래스 설계서 Entity와 일치
- [ ] 서비스별 독립 DB
- [ ] PlantUML 문법 검사 통과
- [ ] 서비스 간 FK 관계 없음
- [ ] 유저스토리에 없는 테이블 미추가
- [ ] AI 관련 데이터 저장소(벡터 DB, 프롬프트 저장소, AI 응답 캐시) 설계 포함 (AI 서비스 존재 시)

## 주의사항

- 설계 공통 원칙: `{PLUGIN_DIR}/resources/guides/design/common-principles.md` 준용
- 클래스 설계서 Entity 이외의 테이블 추가 금지
- 서비스 간 DB 조인 및 FK 참조 금지
- Redis Cluster 모드 사용 시 database 번호 대신 Key Prefix 방식으로 전환
- 공통 영역(DB 0) 데이터 변경 시 영향도 분석 필수
