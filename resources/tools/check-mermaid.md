# check-mermaid


- [check-mermaid](#check-mermaid)
  - [기본 정보](#기본-정보)
  - [컨테이너 실행 가이드](#컨테이너-실행-가이드)
  - [설치 정보](#설치-정보)
  - [사용 예시](#사용-예시)

---

## 기본 정보

| 항목 | 값 |
|------|---|
| 도구명 | check-mermaid |
| 카테고리 | 커스텀 CLI |
| 설명 | Docker 기반 Mermaid 다이어그램 문법 검증 도구 |
| 소스 경로 | `resources/tools/customs/diagram/check-mermaid.sh` |

[Top](#check-mermaid)

---

## 컨테이너 실행 가이드

스크립트가 Mermaid CLI Docker 컨테이너를 자동으로 관리함.
별도의 사전 설정 없이 스크립트 실행만으로 컨테이너 생성부터 검증까지 수행.
PlantUML과 달리 Chromium 설치 등 추가 설정이 필요하나 모두 자동 처리됨.

**자동 관리 동작:**

| 컨테이너 상태 | 스크립트 동작 |
|--------------|-------------|
| 실행 중 | 그대로 사용 |
| 중지 상태 | 자동 재시작 (`docker start`) |
| 미존재 | 3단계 자동 설정 수행 (아래 참조) |

**미존재 시 자동 설정 절차:**

1. 컨테이너 생성: `docker run -d --name mermaid-cli -u root -p 48080:8080 ...`
2. Chromium 및 의존성 설치: `chromium`, `chromium-chromedriver`, `nss`, `freetype` 등
3. Puppeteer 설정 파일 생성: `/tmp/puppeteer-config.json`

**수동 컨테이너 관리 (필요 시):**

| 명령 | 설명 |
|------|------|
| `docker ps --filter "name=mermaid-cli"` | 실행 상태 확인 |
| `docker stop mermaid-cli` | 컨테이너 중지 |
| `docker rm mermaid-cli` | 컨테이너 삭제 |
| `docker logs mermaid-cli` | 로그 확인 |

[Top](#check-mermaid)

---

## 설치 정보

| 항목 | 값 |
|------|---|
| 설치 방법 | 소스 파일 포함 (별도 설치 불요) |
| 필수 여부 | 선택 |
| 의존성 | Docker (컨테이너는 스크립트가 자동 생성/설정) |

**검증 명령:**

```bash
docker ps --filter "name=mermaid-cli"
```

[Top](#check-mermaid)

---

## 사용 예시

```bash
# Mermaid 파일 문법 검증
bash tools/diagram/check-mermaid.sh diagram.mmd

# 성공 시: "Success: Mermaid syntax is valid!"
# 실패 시: 에러 상세 (Parse error, Syntax error 등) 출력
```

**종료 코드:**

| 코드 | 의미 |
|------|------|
| 0 | 문법 검증 통과 |
| 1 | 문법 오류 또는 컨테이너 생성/설정 실패 |

[Top](#check-mermaid)
