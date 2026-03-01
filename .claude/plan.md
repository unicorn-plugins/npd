# run-container-guide 실행 전환 계획

## 배경 및 목표

### 문제
3개 가이드 파일(`run-container-guide-back.md`, `run-container-guide-front.md`, `run-container-guide-ai.md`)이 "가이드 문서만 생성하고 실제 컨테이너 실행은 하지 않는다"로 되어 있으나, `skills/deploy/SKILL.md` Step 3에서는 "컨테이너를 실행하고 정상 동작을 확인한다"를 기대한다. 이 불일치를 해소한다.

### 목표
3개 가이드를 "가이드 문서 생성" 모드에서 "VM에서 실제 컨테이너 실행 + 결과 보고서 작성" 모드로 전환한다.

### 참조 패턴
`backing-service-deploy.md`가 이미 "실제 실행" 패턴을 따르고 있으므로 구조를 참조한다.

---

## Phase 1. 공통 변경 패턴 (3개 파일 동시 적용)

3개 파일에 동일하게 적용되는 변경사항이다. 병렬 작업 가능.

### 1-1. 목적 섹션 변경

**Before:**
```
## 목적
{서비스}의 컨테이너 이미지를 컨테이너로 실행하는 가이드를 작성한다.
실제 컨테이너 실행은 하지 않으며, 수행할 명령어를 포함하여 컨테이너 실행 가이드를 결과 파일에 생성한다.
```

**After:**
```
## 목적
{서비스}의 컨테이너 이미지를 VM에서 실제로 컨테이너로 실행하고 정상 동작을 확인한다.
실행 결과를 보고서에 기록한다.
```

### 1-2. 출력 섹션 변경

**Before:**
```
## 출력 (이 단계 산출물)
| 산출물 | 파일 경로 |
|--------|----------|
| 컨테이너 실행 가이드 | `deployment/container/run-container-guide.md` |
```

**After (파일별 다름 -- Phase 2 참조):**
```
## 출력 (이 단계 산출물)
| 산출물 | 파일 경로 |
|--------|----------|
| 컨테이너 실행 결과서 | `docs/deploy/run-container-{type}-result.md` |
```

출력 파일명 결정:
| 가이드 | 결과 보고서 파일명 |
|--------|-------------------|
| run-container-guide-back.md | `docs/deploy/run-container-back-result.md` |
| run-container-guide-front.md | `docs/deploy/run-container-front-result.md` |
| run-container-guide-ai.md | `docs/deploy/run-container-ai-result.md` |

### 1-3. VM 접속 방법: "안내" -> "실제 접속"

backing-service-deploy.md 패턴을 적용한다.

**Before:**
```
### VM 접속 방법 안내
- Linux/Mac은 기본 터미널을 실행하고 Window는 Window Terminal을 실행하도록 안내
- 터미널에서 아래 명령으로 VM에 접속하도록 안내

  최초 한번 Private key파일의 모드를 변경.
  ```
  chmod 400 {VM.KEY파일}
  ```

  private key를 이용하여 접속.
  ```
  ssh -i {VM.KEY파일} {VM.USERID}@{VM.IP}
  ```
```

**After:**
```
### VM 접속

Step 1(배포 사전 준비)에서 `~/.ssh/config`가 설정된 경우 Host alias로 간편하게 접속한다.

**방법 1: Host alias 사용 (권장)**
```
ssh {VM.HOST}
```

**방법 2: Key 직접 지정 (Host alias 미설정 시 fallback)**
```
chmod 400 {VM.KEY파일}
ssh -i {VM.KEY파일} {VM.USERID}@{VM.IP}
```
```

### 1-4. 실행정보 확인 섹션: VM.HOST 항목 추가

**Before (공통 항목):**
```
- {VM.KEY파일}: VM 접속하는 Private Key파일 경로
- {VM.USERID}: VM 접속하는 OS 유저명
- {VM.IP}: VM IP
```

**After:**
```
- {VM.HOST}: VM SSH Host alias (~/.ssh/config에 등록된 이름)
- {VM.KEY파일}: VM 접속하는 Private Key파일 경로
- {VM.USERID}: VM 접속하는 OS 유저명
- {VM.IP}: VM IP
```

또한 각 파일의 4개 `[실행정보]` 예시 블록(DockerHub/ECR/ACR/GCR)의 VM 섹션에도 HOST 라인을 추가한다:
```
- VM
  - HOST: myvm
  - KEY파일: ~/home/bastion-dg0500
  - USERID: azureuser
  - IP: 4.230.5.6
```

> Architect 리뷰 반영: SKILL.md의 `[실행정보]` 조립 규칙에 이미 HOST 포함. 예시와 항목 목록 일치 필요.

### 1-5. Git Repository 클론: "안내" -> "실제 실행"

**Before:**
```
### Git Repository 클론 안내
- workspace 디렉토리 생성 및 이동
  ...
- 소스 Clone
  ...
```

**After:**
```
### Git Clone/Pull

VM에서 프로젝트 소스를 준비한다.

**최초 clone (프로젝트가 없는 경우)**
```
mkdir -p ~/workspace
cd ~/workspace
git clone {원격 Git Repository 주소}
cd {ROOT}
```

**이후 pull (프로젝트가 이미 있는 경우)**
```
cd ~/workspace/{ROOT}
git pull
```
```

### 1-6. 각 "방법 안내/작성" 섹션명 -> "실행" 패턴으로 변경

| Before 섹션명 | After 섹션명 |
|--------------|-------------|
| 어플리케이션 빌드 및 컨테이너 이미지 생성 방법 안내 | 컨테이너 이미지 빌드 |
| 컨테이너 레지스트리 로그인 방법 안내 | 컨테이너 레지스트리 로그인 |
| 컨테이너 이미지 태그 및 푸시 방법 안내 | 컨테이너 이미지 태그 및 푸시 |
| 컨테이너 실행 명령 생성 | 컨테이너 실행 |
| 실행된 컨테이너 확인 방법 작성 | 컨테이너 실행 확인 |
| 재배포 방법 작성 | 재배포 절차 |
| 컨테이너 이미지 생성 방법 안내 (front 전용) | 컨테이너 이미지 빌드 |
| 런타임 환경변수 파일 생성 방법 안내 (front) | 런타임 환경변수 파일 생성 |

각 섹션의 본문에서 "안내", "작성", "생성"이라는 표현을 "실행", "수행", "확인"으로 전환한다. 기존 명령어 스니펫은 그대로 유지하되, **"아래 명령으로 수행하도록 안내"** 를 **"아래 명령을 실행한다"** 로 변경한다.

### 1-7. 출력 형식 섹션 변경

**Before:**
```
## 출력 형식
`deployment/container/run-container-guide.md` 파일에 수행할 명령어를 포함하여 컨테이너 실행 가이드를 단계별로 기록한다.
```

**After:**
```
## 출력 형식

`docs/deploy/run-container-{type}-result.md` 결과 보고서 템플릿:

```markdown
# {서비스 유형} 컨테이너 실행 결과서

## 구성 환경
- 환경: docker run (VM 컨테이너 배포)
- VM: {VM.HOST} ({VM.IP})
- 실행 일시: YYYY-MM-DD

## VM 접속 방법
```
ssh {VM.HOST}
```

## 실행된 컨테이너

| 항목 | 값 |
|------|---|
| 서비스명 | {서비스명} |
| 이미지 | {REGISTRY_URL}/{서비스명}:latest |
| 포트 매핑 | {호스트포트}:{컨테이너포트} |
| 네트워크 | {ROOT}_default |
| 상태 | Running |

## Health Check 결과
- [ ] `docker ps` 확인: 컨테이너 실행 중
- [ ] {서비스별 추가 헬스체크}

## 실행 명령어
```bash
{실제 실행에 사용한 docker run 명령 기록}
```

## 재배포 명령어
```bash
{재배포 시 사용할 명령 시퀀스}
```
```
```

### 1-8. 품질 기준 섹션 정합성 확보

**Before:**
```
## 품질 기준
- [ ] 컨테이너 정상 실행 확인
- [ ] 로컬 검증 없이 K8s 배포 미진행
```

**After:**
```
## 품질 기준
- [ ] `docker ps`로 컨테이너가 `Up` 상태
- [ ] {서비스별 헬스체크} 정상 응답
- [ ] `docs/deploy/run-container-{type}-result.md`가 작성됨
```

### 1-9. 주의사항 섹션 변경

**Before:**
```
## 주의사항
- 실제 컨테이너 실행은 하지 않고 가이드 문서만 생성
```

**After:**
```
## 주의사항
- VM에서 실제 컨테이너를 실행하고 정상 동작을 확인한다
- 백킹서비스가 먼저 기동되어 있어야 한다 (Step 3-0 참조)
```

나머지 주의사항(shell 파일 금지, CORS, runtime-env.js 등)은 그대로 유지.

### 1-10. 트러블슈팅 섹션 추가

backing-service-deploy.md 패턴을 참조하여 공통 트러블슈팅을 추가한다.

```
## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `docker: command not found` | Docker 미설치 | Step 1(배포 사전 준비)에서 Docker 설치 확인 |
| `permission denied` (docker) | 현재 유저가 docker 그룹에 미포함 | `sudo usermod -aG docker $USER` 후 재접속 |
| `network {ROOT}_default not found` | 백킹서비스 미기동 | Step 3-0에서 `docker compose up -d` 먼저 실행 |
| `port is already allocated` | 포트 충돌 | 해당 포트를 사용 중인 컨테이너 확인 후 중지 |
| 컨테이너 즉시 종료 (Exited) | 환경변수 누락 또는 잘못된 값 | `docker logs {서비스명}`으로 에러 확인 |
| 레지스트리 인증 실패 | 토큰 만료 또는 잘못된 인증 정보 | "컨테이너 레지스트리 로그인" 섹션 재수행 |
```

---

## Phase 2. 파일별 고유 변경

### 2-1. run-container-guide-back.md 고유 변경

- **출력 파일**: `docs/deploy/run-container-back-result.md`
- **"컨테이너 실행 명령 생성" -> "컨테이너 실행"**: 본문의 "명령을 생성한다"를 "명령을 실행한다"로 변경. 기존 docker run 템플릿은 유지.
- **CORS 관련 주의사항 유지**: `ALLOWED_ORIGINS`에 `http://{VM.IP}:3000` 추가 로직 그대로 유지
- **`--network {ROOT}_default`**: 유지 (이미 있음)
- **`.run/*.run.xml` 환경변수 추출 로직**: 유지 (back 고유)
- **settings.gradle 서비스명 추출**: 유지 (back 고유)
- **Health Check 추가**: 결과서 템플릿에 서비스별 헬스체크 포함
  ```
  ## Health Check 결과
  - [ ] `docker ps | grep {서비스명}` 확인: 컨테이너 실행 중
  - [ ] 각 서비스 API 응답 확인 (curl http://localhost:{SERVER_PORT}/actuator/health)
  ```
- **파일별 트러블슈팅 추가**:
  | 증상 | 원인 | 해결 |
  |------|------|------|
  | DB 접속 실패 | DB_HOST가 localhost 또는 VM IP | docker-compose 서비스명으로 치환 (예: `DB_HOST=postgres`) |
  | CORS 에러 (브라우저) | ALLOWED_ORIGINS 미설정 | `http://{VM.IP}:3000` 추가 확인 |

### 2-2. run-container-guide-front.md 고유 변경

- **출력 파일**: `docs/deploy/run-container-front-result.md`
- **"컨테이너 실행 명령 생성" -> "컨테이너 실행"**: 동일 패턴 적용
- **runtime-env.js 볼륨 마운트**: 유지 (front 고유). "생성 방법 안내" -> "생성 및 배치"로 변경
- **runtime-env.js 생성**: "방법 안내"에서 실제 파일 생성으로 전환. VM에서 `localhost`를 `{VM.IP}`로 치환한 runtime-env.js를 실제 생성.
- **포트 3000 -> 8080(nginx) 매핑**: 유지
- **package.json/pubspec.yaml 서비스명 추출**: 유지 (front 고유)
- **Health Check 추가**:
  ```
  ## Health Check 결과
  - [ ] `docker ps | grep {서비스명}` 확인: 컨테이너 실행 중
  - [ ] 브라우저 접속 확인 (http://{VM.IP}:3000)
  ```
- **파일별 트러블슈팅 추가**:
  | 증상 | 원인 | 해결 |
  |------|------|------|
  | 화면은 뜨나 API 호출 실패 | runtime-env.js의 호스트가 localhost | `{VM.IP}`로 치환 확인 |
  | 403/404 (nginx) | 볼륨 마운트 경로 불일치 | React: `public/runtime-env.js`, Flutter: `web/runtime-env.js` 확인 |

### 2-3. run-container-guide-ai.md 고유 변경

- **출력 파일**: `docs/deploy/run-container-ai-result.md`
- **"컨테이너 실행 명령 생성" -> "컨테이너 실행"**: 동일 패턴 적용
- **`.env.example` 환경변수 추출**: 유지 (ai 고유)
- **`pyproject.toml` 서비스명 추출**: 유지 (ai 고유)
- **Health Check**: 기존 `/health` 엔드포인트 확인을 "안내"에서 "실제 실행"으로 전환
  ```
  ## Health Check 결과
  - [ ] `docker ps | grep {서비스명}` 확인: 컨테이너 실행 중
  - [ ] `wget -qO- http://localhost:{APP_PORT}/health` 정상 응답 (`{"status":"ok"}`)
  ```
- **파일별 트러블슈팅 추가**:
  | 증상 | 원인 | 해결 |
  |------|------|------|
  | `/health` 503 응답 | LLM API Key 미설정 | `-e OPENAI_API_KEY=...` 확인 |
  | 모듈 import 에러 | Python 의존성 이미지 빌드 실패 | Dockerfile 및 `docker logs` 확인 |

---

## Phase 3. 결과 보고서 템플릿 상세

### 3-1. 공통 템플릿 구조

```markdown
# {서비스유형} 컨테이너 실행 결과서

## 구성 환경
- 환경: docker run (VM 컨테이너 배포)
- VM: {VM.HOST} ({VM.IP})
- 실행 일시: YYYY-MM-DD

## VM 접속 방법
```
ssh {VM.HOST}
```

## 실행된 컨테이너

| 항목 | 값 |
|------|---|
| 서비스명 | {서비스명} |
| 이미지 | {REGISTRY_URL}/{서비스명}:latest |
| 포트 매핑 | {호스트포트}:{컨테이너포트} |
| 네트워크 | {ROOT}_default |
| 상태 | Running |

## Health Check 결과
{서비스별 상이 -- Phase 2 참조}

## 실행 명령어
```bash
{실제 사용한 docker run 명령 전문}
```

## 재배포 명령어
```bash
# VM 접속
ssh {VM.HOST}

# 소스 업데이트
cd ~/workspace/{ROOT}
git pull

# 이미지 재빌드 (build-image.md 참조)
# 이미지 태그 & 푸시
docker tag {서비스명}:latest {REGISTRY_URL}/{서비스명}:latest
docker push {REGISTRY_URL}/{서비스명}:latest

# 컨테이너 중지 & 이미지 삭제
docker stop {서비스명}
docker rmi {REGISTRY_URL}/{서비스명}:latest

# 컨테이너 재실행
{docker run 명령 반복}
```
```

### 3-2. 백엔드 추가 항목
- 서비스별(common 제외) 각 컨테이너 정보를 테이블로 나열
- CORS 설정값 기록

### 3-3. 프론트엔드 추가 항목
- runtime-env.js 내용 기록
- 브라우저 접속 URL 기록

### 3-4. AI 추가 항목
- Health check 엔드포인트 및 응답 기록
- LLM Provider/Model 설정값 기록

---

## Phase 4. SKILL.md 수정

### 분석 결과: 소규모 수정 필요

SKILL.md Step 3의 현재 기술:
```
#### TASK: 백엔드·프론트엔드·AI 병렬 컨테이너 실행
3개 서비스를 서브에이전트로 병렬 실행한다. 각 에이전트는 해당 가이드를 참조하여 컨테이너를 실행하고 정상 동작을 확인한다.
```

이 기술은 이미 "실제 실행"을 기대하고 있으므로, 가이드가 실행 모드로 전환되면 SKILL.md와 정합성이 맞는다.

### 4-1. POST_ACTION 본문 텍스트 수정

**위치**: SKILL.md 411행

```
Before: Step 3 완료 후, VM에서 생성된 산출물(결과 보고서, 컨테이너 실행 가이드 등)을 원격 저장소에 반영하고 로컬과 동기화한다.
After:  Step 3 완료 후, VM에서 생성된 산출물(결과 보고서, 컨테이너 실행 결과서 등)을 원격 저장소에 반영하고 로컬과 동기화한다.
```

### 4-2. POST_ACTION 커밋 메시지 변경

결과 보고서 파일명이 변경되므로 커밋 메시지도 업데이트가 필요하다.

**위치**: SKILL.md 415행 및 424행

```
Before: "deploy: Step 3 산출물 (backing-service-result, run-container-guide)"
After:  "deploy: Step 3 산출물 (backing-service-result, run-container-result)"
```

### 4-3. EXPECTED OUTCOME 상세화

**위치**: SKILL.md 407행

```
Before: - **EXPECTED OUTCOME**: 백엔드·프론트엔드·AI 서비스 컨테이너 정상 실행 확인
After:  - **EXPECTED OUTCOME**: 백엔드·프론트엔드·AI 서비스 컨테이너 정상 실행 확인, `docs/deploy/run-container-{back,front,ai}-result.md` 작성
```

### 4-4. 완료 조건 섹션에 run-container 결과서 추가

**위치**: SKILL.md 515행 부근 (완료 조건 체크리스트)

```
추가: - [ ] 컨테이너 실행 검증 완료 (`docs/deploy/run-container-{back,front,ai}-result.md` 생성)
```

> Architect 리뷰 반영: 완료 조건은 전체 스킬의 종료 판정 기준이므로, 결과서 존재 여부를 체크해야 한다.

---

## Phase 5. resource.md 수정

### 분석 결과: 수정 필요

현재 `resources/resource.md`에 아래 항목이 누락되어 있다:

| 누락 항목 | 추가할 행 |
|-----------|----------|
| run-container-guide-ai | `deploy | run-container-guide-ai | AI 서비스 컨테이너 VM 실행 및 검증 | [상세](guides/deploy/run-container-guide-ai.md)` |
| build-image-ai | `deploy | build-image-ai | AI 서비스 Docker 이미지 빌드 | [상세](guides/deploy/build-image-ai.md)` |
| backing-service-deploy | `deploy | backing-service-deploy | VM 백킹서비스 배포 | [상세](guides/deploy/backing-service-deploy.md)` |

또한 기존 항목의 설명도 업데이트:

| 가이드명 | Before 설명 | After 설명 |
|---------|------------|-----------|
| run-container-guide-back | 백엔드 컨테이너 실행 가이드 | 백엔드 컨테이너 VM 실행 및 검증 |
| run-container-guide-front | 프론트엔드 컨테이너 실행 가이드 | 프론트엔드 컨테이너 VM 실행 및 검증 |

---

## Phase 6. 변경 영역 요약 매트릭스

| 섹션 | back | front | ai | 변경 유형 |
|------|:----:|:-----:|:--:|----------|
| 목적 | O | O | O | 공통 |
| 출력 | O | O | O | 공통 (파일명만 다름) |
| 실행정보 확인 (VM.HOST 추가) | O | O | O | 공통 |
| VM 접속 | O | O | O | 공통 |
| Git Clone/Pull | O | O | O | 공통 |
| 섹션명 "안내/작성/생성" -> "실행" | O | O | O | 공통 |
| 출력 형식 (결과 보고서 템플릿) | O | O | O | 공통 구조 + 파일별 상세 |
| 품질 기준 | O | O | O | 공통 구조 + 파일별 헬스체크 |
| 주의사항 | O | O | O | 공통 |
| 트러블슈팅 | O | O | O | 공통 + 파일별 추가 |
| 서비스명 확인 | - | - | - | 변경 없음 (각 파일 고유 유지) |
| 환경변수 추출 | - | - | - | 변경 없음 (각 파일 고유 유지) |
| CORS 설정 | O | - | - | back 고유 유지 |
| runtime-env.js | - | O | - | front 고유 (안내->실행 전환) |
| /health 엔드포인트 | - | - | O | ai 고유 (안내->실행 전환) |

---

## Phase 7. 작업 순서 및 병렬화

```
Phase A (병렬 가능 -- 3개 파일 동시 수정):
  ├── [A-1] run-container-guide-back.md 수정
  ├── [A-2] run-container-guide-front.md 수정
  └── [A-3] run-container-guide-ai.md 수정

Phase B (Phase A 완료 후, 순차):
  ├── [B-1] SKILL.md POST_ACTION 커밋 메시지 수정 + EXPECTED OUTCOME 상세화
  └── [B-2] resource.md 누락 항목 추가 및 설명 업데이트

Phase C (검증):
  └── [C-1] 전체 정합성 검증
```

---

## Phase 8. 검증 계획

### 8-1. 정적 검증 (코드 리뷰)

| 검증 항목 | 방법 |
|-----------|------|
| "가이드 문서만 생성" 문구 완전 제거 확인 | 3개 파일에서 "가이드 문서만 생성", "실제 컨테이너 실행은 하지 않" 등의 문구 grep |
| "안내", "작성", "생성" 섹션명 전환 확인 | 섹션 헤더에 "안내", "방법 작성"이 남아있지 않은지 확인 |
| VM.HOST 항목 추가 확인 | 3개 파일의 실행정보 확인 섹션에 VM.HOST 존재 확인 |
| 결과 보고서 출력 경로 확인 | `docs/deploy/run-container-{type}-result.md` 형식 확인 |
| SKILL.md 커밋 메시지 정합성 | POST_ACTION의 커밋 메시지가 새 산출물 파일명 반영 확인 |
| resource.md 누락 항목 추가 확인 | 가이드 목록 테이블에 누락된 3개 항목 존재 확인 |

### 8-1b. 본문 내 상호 참조 업데이트 검증

| 검증 항목 | 방법 |
|-----------|------|
| 섹션명 변경 후 본문 참조 업데이트 | 3개 파일에서 `"컨테이너 레지스트리 로그인 방법 안내"`, `"컨테이너 실행 명령 생성"` 등 구 섹션명이 남아있지 않은지 grep |
| 본문 표현 전환 완전성 | 3개 파일에서 "안내", "방법 안내", "방법 작성" 등의 표현이 본문(섹션명이 아닌) 내에서 전환되었는지 grep |

> Critic 리뷰 반영: 섹션 리네임 후 본문 참조 텍스트 정합성 확인 필요.

### 8-2. 기존 명령어 보존 확인

| 검증 항목 | 방법 |
|-----------|------|
| docker run 명령 템플릿 | 3개 파일의 docker run 스니펫이 원본과 동일한지 diff |
| 환경변수 추출 로직 | back: `.run/*.run.xml`, front: `runtime-env.js`, ai: `.env.example` 로직 유지 확인 |
| 네트워크 설정 | `--network {ROOT}_default` 유지 확인 |
| 레지스트리 로그인 명령 | 4개 유형(DockerHub/ECR/ACR/GCR) 명령 유지 확인 |

### 8-3. SKILL.md 워크플로우 정합성

| 검증 항목 | 방법 |
|-----------|------|
| Step 3 EXPECTED OUTCOME과 가이드 출력 일치 | 가이드 출력 파일명이 EXPECTED OUTCOME에 반영 확인 |
| POST_ACTION 커밋 대상에 새 결과 파일 포함 | `git add -A`이므로 자동 포함되지만 커밋 메시지 확인 |

---

## 수정 대상 파일 목록

| # | 파일 경로 | 변경 규모 |
|---|----------|----------|
| 1 | `resources/guides/deploy/run-container-guide-back.md` | 대 (전면 전환) |
| 2 | `resources/guides/deploy/run-container-guide-front.md` | 대 (전면 전환) |
| 3 | `resources/guides/deploy/run-container-guide-ai.md` | 대 (전면 전환) |
| 4 | `skills/deploy/SKILL.md` | 소 (커밋 메시지 + EXPECTED OUTCOME 2곳) |
| 5 | `resources/resource.md` | 소 (3행 추가 + 2행 설명 수정) |

총 5개 파일, 예상 복잡도: MEDIUM

---

## 설계 원칙 준수 확인

- [x] 기존 명령어/스니펫 최대한 보존 (실행 방식만 전환)
- [x] backing-service-deploy.md 패턴 참조하되 맹목적 복사 않음
- [x] 각 파일의 고유 로직(환경변수 추출, 볼륨 마운트 등) 그대로 유지
- [x] 결과 보고서 템플릿 추가
