# check-plantuml


- [check-plantuml](#check-plantuml)
  - [기본 정보](#기본-정보)
  - [컨테이너 실행 가이드](#컨테이너-실행-가이드)
  - [설치 정보](#설치-정보)
  - [사용 예시](#사용-예시)

---

## 기본 정보

| 항목 | 값 |
|------|---|
| 도구명 | check-plantuml |
| 카테고리 | 커스텀 CLI |
| 설명 | Docker 기반 PlantUML 다이어그램 문법 검증 도구 |
| 소스 경로 | `resources/tools/customs/diagram/check-plantuml.sh` |

[Top](#check-plantuml)

---

## 컨테이너 실행 가이드

스크립트가 PlantUML Docker 컨테이너를 자동으로 관리함.
별도의 사전 설정 없이 스크립트 실행만으로 컨테이너 생성부터 검증까지 수행.

**자동 관리 동작:**

| 컨테이너 상태 | 스크립트 동작 |
|--------------|-------------|
| 실행 중 | 그대로 사용 |
| 중지 상태 | 자동 재시작 (`docker start`) |
| 미존재 | 자동 생성 및 시작 (`docker run -d --name plantuml -p 38080:8080 plantuml/plantuml-server:jetty`) |

**수동 컨테이너 관리 (필요 시):**

| 명령 | 설명 |
|------|------|
| `docker ps --filter "name=plantuml"` | 실행 상태 확인 |
| `docker stop plantuml` | 컨테이너 중지 |
| `docker rm plantuml` | 컨테이너 삭제 |
| `docker logs plantuml` | 로그 확인 |

[Top](#check-plantuml)

---

## 설치 정보

| 항목 | 값 |
|------|---|
| 설치 방법 | 소스 파일 포함 (별도 설치 불요) |
| 필수 여부 | 선택 |
| 의존성 | Docker (컨테이너는 스크립트가 자동 생성) |

**검증 명령:**

```bash
docker ps --filter "name=plantuml"
```

[Top](#check-plantuml)

---

## 사용 예시

```bash
# PlantUML 파일 문법 검증
bash tools/diagram/check-plantuml.sh diagram.puml

# 검증 절차:
# 1. 파일을 Docker 컨테이너에 복사
# 2. PlantUML JAR로 -checkonly 실행
# 3. Error line 상세 출력
# 4. 임시 파일 정리
```

**종료 코드:**

| 코드 | 의미 |
|------|------|
| 0 | 문법 검증 통과 |
| 1 | 문법 오류 또는 컨테이너 생성 실패 |

[Top](#check-plantuml)
