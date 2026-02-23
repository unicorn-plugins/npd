# 종합 테스트 및 QA 가이드

## 목적

구현된 전체 시스템(백엔드, 프론트엔드, AI 서비스)을 종합 테스트하고 버그를 리포트한다. MVP Must Have 기능 전체가 정상 동작함을 확인하는 최종 검증 단계이다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 구현된 백엔드 코드 | `{service-name}/src/` | 테스트 대상 |
| 구현된 프론트엔드 코드 | `frontend/` | 테스트 대상 |
| 구현된 AI 서비스 코드 | `ai-service/` | 테스트 대상 (존재 시) |
| 유저스토리 | `docs/plan/design/userstory.md` | 테스트 범위·시나리오 결정 |
| API 설계서 | `docs/design/api/*.yaml` | API 명세 확인 |
| 서비스 실행 프로파일 | `{service-name}/.run/{service-name}.run.xml` | 실행 환경 확인 |
| 백킹서비스 설치 결과서 | `docs/develop/backing-service-result.md` | 연결 정보 확인 |
| Docker Compose 파일 | `./docker-compose.yml` | 백킹서비스 기동 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 종합 테스트 리포트 | `docs/develop/test-report.md` |

## 방법론

### 테스트 원칙

- **MVP Must Have 전체 커버**: 유저스토리의 Must Have 기능 전체를 테스트
- **유저스토리 기반 시나리오**: 단위 API 테스트가 아닌 사용자 시나리오 기반 통합 테스트
- **환경변수 일치 검증**: 설정 Manifest ↔ 실행 프로파일 일치 사전 검증
- **서비스 의존 순서 준수**: 의존관계를 고려한 순서대로 테스트

### 테스트 순서

#### 준비: 환경 검증

1. **백킹서비스 실행 확인**
   ```bash
   docker compose up -d
   docker compose ps    # 모든 서비스 running 확인
   ```

2. **설정 Manifest ↔ 실행 프로파일 일치 검증**
   - 각 서비스의 `application.yml`에서 `${}` 환경변수 목록 추출
   - 대응하는 `.run/{service-name}.run.xml`의 `<entry>` 목록과 비교
   - 불일치 항목 발견 시 실행 프로파일 수정

3. **서비스 시작** (아래 '서비스 시작/중지 방법' 참조)

4. **헬스체크 확인**
   ```bash
   # 백엔드 서비스별 헬스체크
   curl -s http://localhost:{port}/actuator/health

   # AI 서비스 헬스체크 (존재 시)
   curl -s http://localhost:8000/health

   # 프론트엔드 개발 서버
   curl -s http://localhost:5173/
   ```

#### 실행: 단계별 테스트

**1단계. 백엔드 API 테스트**

- 서비스 의존관계를 고려한 순서로 테스트
- 각 서비스의 Controller에서 API 엔드포인트·DTO 확인
- `curl` 명령으로 각 API 호출 및 응답 확인
  ```bash
  # 예시: POST API 테스트
  curl -X POST http://localhost:{port}/{path} \
    -H "Content-Type: application/json" \
    -d '{"field": "value"}'

  # 예시: 인증이 필요한 API (JWT 토큰 사용)
  curl -X GET http://localhost:{port}/{path} \
    -H "Authorization: Bearer {token}"
  ```
- API 설계서(`*.yaml`)의 요청/응답 스키마와 실제 응답 비교
- 오류 발견 시:
  1. 코드 수정
  2. 컴파일: `./gradlew {service-name}:compileJava`
  3. 서비스 재시작 (아래 서비스 중지 → 시작 참조)
  4. 재테스트

**2단계. 프론트엔드 동작 테스트**

- 브라우저에서 각 페이지 접근 및 동작 확인
- 실제 API 연동 상태 확인 (Network 탭에서 요청/응답 검증)
- 인증 흐름 확인 (로그인 → 토큰 저장 → API 호출 → 토큰 갱신)
- 반응형 UI 확인 (다양한 뷰포트 크기)

**3단계. AI 서비스 테스트 (존재 시)**

- AI 서비스 API 직접 호출 테스트
  ```bash
  curl -X POST http://localhost:8000/{ai-endpoint} \
    -H "Content-Type: application/json" \
    -d '{"prompt": "test input"}'
  ```
- 백엔드 → AI 서비스 연동 테스트
- Circuit Breaker / Fallback 동작 확인 (AI 서비스 중지 후 백엔드 호출)

**4단계. 통합 시나리오 테스트**

- 유저스토리의 Must Have 기능별 E2E 시나리오 수행
- 프론트엔드 → 백엔드 → DB → (AI 서비스) 전체 흐름 확인
- 에러 케이스 시나리오 (잘못된 입력, 인증 만료, 네트워크 오류 등)

**5단계. 버그 수정 및 재테스트**

- 발견된 버그 목록화
- 우선순위별 수정 (Critical → Major → Minor)
- 수정 후 영향받는 기능 재테스트

#### 검토: 최종 확인

- MVP Must Have 기능 전체 동작 확인
- 테스트 리포트 작성 완료
- 미해결 버그 목록 정리 (있는 경우)

### 서비스 시작/중지 방법

#### 서비스 시작

1. IntelliJ 서비스 실행기를 `tools/` 디렉토리에 다운로드
   ```bash
   mkdir -p tools
   # run-intellij-service-profile.py 다운로드
   ```

2. 전체 서비스 시작 (서비스 간 지연 포함)
   ```bash
   nohup python3 tools/run-intellij-service-profile.py --config-dir . --delay 5 > /dev/null 2>&1 &
   ```

3. 개별 서비스 시작
   ```bash
   nohup python3 tools/run-intellij-service-profile.py {service-name} > logs/{service-name}.log 2>&1 &
   echo "Started {service-name} with PID: $!"
   ```

4. 서비스 시작 확인
   ```bash
   # 각 서비스의 actuator/health 엔드포인트 확인
   curl -s http://localhost:{port}/actuator/health
   ```

#### 서비스 중지

**Linux/Mac:**
```bash
# 실행기 프로세스 중지
kill $(pgrep -f run-intellij-service-profile.py)

# Java(Spring Boot) 프로세스 전체 중지
pkill -f 'java.*spring'
```

**Windows:**
```bash
# 포트로 프로세스 찾기
netstat -ano | findstr :{PORT}

# 프로세스 종료
powershell "Stop-Process -Id {PID} -Force"
```

#### AI 서비스 시작/중지

```bash
# Docker Compose ai 프로파일로 시작
docker compose --profile ai up -d

# 또는 직접 실행
cd ai-service && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 중지
docker compose --profile ai down
```

#### 프론트엔드 개발 서버 시작

```bash
cd frontend && npm run dev
```

### 검증 방법

- 유저스토리의 Must Have 기능 전체 테스트 여부
- 테스트 리포트에 성공/실패 목록 포함 여부
- 발견된 버그 전체 수정 완료 여부

## 출력 형식

### 종합 테스트 리포트 템플릿

```markdown
# 종합 테스트 리포트

## 1. 테스트 환경

| 항목 | 값 |
|------|-----|
| 테스트 일시 | {YYYY-MM-DD} |
| 백킹서비스 환경 | docker-compose / minikube / K8s |
| 백엔드 서비스 수 | {N}개 |
| 프론트엔드 프레임워크 | {React/Vue} |
| AI 서비스 | {포함/미포함} |

## 2. 백엔드 API 테스트 결과

| 서비스 | 엔드포인트 | 메서드 | 결과 | 비고 |
|--------|----------|--------|------|------|
| {service} | {path} | {GET/POST/...} | {PASS/FAIL} | {설명} |

## 3. 프론트엔드 테스트 결과

| 페이지 | 주요 기능 | API 연동 | UI 동작 | 결과 |
|--------|----------|---------|---------|------|
| {page} | {기능} | {정상/오류} | {정상/오류} | {PASS/FAIL} |

## 4. AI 서비스 테스트 결과 (해당 시)

| 엔드포인트 | 입력 | 기대 결과 | 실제 결과 | 결과 |
|-----------|------|----------|----------|------|
| {endpoint} | {input} | {expected} | {actual} | {PASS/FAIL} |

## 5. 통합 시나리오 테스트

| 유저스토리 | 시나리오 | 결과 | 비고 |
|-----------|---------|------|------|
| {US-ID} {제목} | {시나리오 설명} | {PASS/FAIL} | {설명} |

## 6. 발견된 버그 및 수정 내역

| ID | 심각도 | 서비스 | 설명 | 수정 여부 | 비고 |
|----|--------|--------|------|----------|------|
| BUG-{N} | {Critical/Major/Minor} | {서비스명} | {버그 설명} | {수정완료/미해결} | {설명} |

## 7. 최종 요약

- 전체 테스트 수: {N}
- 성공: {N} / 실패: {N}
- MVP Must Have 커버리지: {N}/{M} ({%})
- 미해결 버그: {N}건
```

## 품질 기준

- [ ] MVP Must Have 기능 전체 테스트 수행
- [ ] 설정 Manifest ↔ 실행 프로파일 일치 사전 검증 완료
- [ ] 테스트 리포트에 성공/실패 목록 포함
- [ ] 발견된 버그 전체 수정 완료
- [ ] 통합 시나리오 테스트(유저스토리 기반) 수행
- [ ] 테스트 리포트 경로: `docs/develop/test-report.md`

## 주의사항

- 서비스 시작은 반드시 **python 프로그램**(run-intellij-service-profile.py) 이용
- 백킹서비스(`docker compose up -d`)가 실행 중이어야 함
- 설정 Manifest(`application.yml`)의 민감 정보는 하드코딩하지 않고 환경변수 처리
- 설정 Manifest 수정 시 실행 프로파일도 함께 업데이트 (run-profile.md 가이드 참조)
- 실행 결과 로그는 `logs/` 디렉토리 하위에 생성
- 소스 수정 후 반드시 컴파일(`./gradlew {service-name}:compileJava`) 후 서비스 재시작
- AI 서비스 테스트 시 LLM API 호출 비용 주의 (가능하면 mock 활용)
- 테스트 리포트 경로는 기존 `docs/test/test-report.md`가 아닌 `docs/develop/test-report.md`로 통일
