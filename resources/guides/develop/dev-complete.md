# 개발 완료 가이드

> 본 가이드는 `skills/develop/SKILL.md > Phase 5 / Step 1`에서 호출됨.
> 서비스 중지·실행 도구 복사·README 생성·실행 가이드 출력의 종료 절차를 정의.

## 입력

- Phase 4 완료 산출물 (final-report.md, e2etest 레포트, 코드 산출물 일체)
- `{NPD_PLUGIN_DIR}/resources/tools/customs/general/run-backend.py`
- `{NPD_PLUGIN_DIR}/resources/tools/customs/general/run-frontend.py`
- `{NPD_PLUGIN_DIR}/resources/guides/develop/readme-generation.md` (README 생성 가이드)

## 절차

### 1. 서비스 중지

기동 중인 백엔드·프론트엔드·백킹서비스·AI 서비스를 모두 중지.

- 프론트엔드 중지: `python3 tools/run-frontend.py stop`
- 백엔드: 프로세스 종료
- 백킹서비스: `docker compose down`
- AI 서비스 (해당 시): `docker compose --profile ai down`

### 2. 실행 도구 복사

아래 도구를 프로젝트 루트 `tools/`로 복사.

- `{NPD_PLUGIN_DIR}/resources/tools/customs/general/run-backend.py` → `tools/run-backend.py`
- `{NPD_PLUGIN_DIR}/resources/tools/customs/general/run-frontend.py` → `tools/run-frontend.py`

**EXPECTED OUTCOME**: `tools/run-backend.py`, `tools/run-frontend.py`

### 3. README.md 생성

오케스트레이터가 직접 가이드에 따라 프로젝트 루트에 `README.md`를 생성.

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/develop/readme-generation.md`
- **EXPECTED OUTCOME**: `{PROJECT_DIR}/README.md`

### 4. 축하 메시지

개발이 성공적으로 완료되었다는 감성적 축하 메시지를 사용자에게 전달.

### 5. 실행 가이드 출력

아래 템플릿을 사용자에게 출력 (프론트엔드는 프로젝트에서 사용하는 플랫폼만 표시).

```
### 실행 가이드

#### 1. 백킹서비스 기동
​```bash
docker compose up -d
docker compose ps
​```

#### 2. 백엔드 서비스 기동
​```bash
python3 tools/run-backend.py --config-dir . --delay 5
curl -s http://localhost:{port}/actuator/health
​```

#### 3. 프론트엔드 기동
​```bash
python3 tools/run-frontend.py start --background --force   # 백그라운드 시작 (포트 점유 시 강제 종료)
python3 tools/run-frontend.py status                       # 상태 확인
python3 tools/run-frontend.py stop                         # 중지
​```

#### 4. AI 서비스 기동 (해당 시)
​```bash
docker compose --profile ai up -d
curl -s http://localhost:8000/health
​```

#### 5. 서비스 중지
​```bash
docker compose down
​```
```

### 6. 다음 단계 안내

`/npd:deploy` 로 배포를 시작할 수 있음을 안내.

## 산출물

- `tools/run-backend.py`, `tools/run-frontend.py` (실행 도구)
- `{PROJECT_DIR}/README.md` (프로젝트 README)
- 사용자에게 표시되는 축하 메시지 + 실행 가이드 + 다음 단계 안내
