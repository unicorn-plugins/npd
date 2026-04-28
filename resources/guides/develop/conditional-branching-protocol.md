# 가이드 문서 조건 분기 프로토콜

> 본 가이드는 `skills/develop/SKILL.md > 가이드 문서 조건 분기 프로토콜`에서 호출됨.
> 가이드 문서(.md) 내 조건 지시문 처리 규칙과 지원 변수 명세를 정의.

## 입력

- 호출 가이드 문서(.md)에 포함된 `<!-- IF VAR == VALUE -->` ~ `<!-- ENDIF -->` 블록
- `{PROJECT_DIR}/AGENTS.md > ## 워크플로우 진행상황 > ### develop > 지원 변수` 섹션
- 판별 소스 문서(설계서·docker-compose.yml·사용자 응답)

## 문법

```
<!-- IF {VARIABLE} == {VALUE} -->
... 이 값일 때만 실행할 내용 ...
<!-- ELIF {VARIABLE} == {OTHER_VALUE} -->
... 다른 값일 때만 실행할 내용 ...
<!-- ENDIF -->
```

## 해석 규칙

1. 에이전트는 가이드 실행 시작 시 변수 값을 결정. 결정 순서:
   a. **AGENTS.md 우선 조회**: `{PROJECT_DIR}/AGENTS.md`의 `## 워크플로우 진행상황 > ### develop > 지원 변수` 항목에서 해당 변수 값을 먼저 조회
   b. **판별 소스 사용**: AGENTS.md에 값이 없으면 아래 `지원 변수` 표의 판별 소스(설계서·docker-compose.yml·사용자 선택 등)에서 결정
   c. **결정 후 저장**: 새로 결정된 값은 즉시 `AGENTS.md`의 `### develop > 지원 변수` 섹션에 기록하여 이후 가이드 실행에서 재사용
2. 결정된 변수 값과 일치하는 IF/ELIF 블록의 내용만 실행
3. 일치하지 않는 블록은 완전히 건너뜀 (읽지도 실행하지도 않음)
4. 변수 값이 결정되지 않은 경우 사용자에게 질문하여 결정하고, 결과를 AGENTS.md에 저장

## 지원 변수

| 변수 | 가능한 값 | 판별 소스 | 결정 시점 |
|------|-----------|-----------|----------|
| PLATFORM | REACT, VUE, FLUTTER | `docs/design/high-level-architecture.md` 기술스택 섹션 | Phase 1 / Step 4 (프론트엔드 초기화) 시작 시 |
| FRONTEND_PORT | 3000 | PLATFORM에서 파생 (React/Vue/Flutter 모두 3000 통일) | PLATFORM 결정 직후 |
| MOCK | SINGLE | `docker-compose.yml` Prism 서비스 수 | Phase 1 / Step 3 완료 후 |
| TEST_MODE | AUTO, MANUAL | Phase 0 / Step 5에서 사용자 선택 | Phase 0 / Step 5 |

> 결정된 모든 지원 변수는 `AGENTS.md`의 `## 워크플로우 진행상황 > ### develop > 지원 변수` 섹션에 저장되며, 이후 모든 가이드 실행 시 해당 섹션을 우선 조회.

## 플랫폼 판별 키워드 매핑

AGENTS.md에서 `PLATFORM` 값을 읽지 못한 경우에만,
에이전트는 `docs/design/high-level-architecture.md`의 기술스택 섹션에서 아래 키워드를 탐색하여 `PLATFORM` 값을 결정.

| 키워드 in high-level-architecture.md | 판별 결과 |
|--------------------------------------|-----------|
| React, Next.js, Vite+React | `REACT` |
| Vue, Nuxt, Vite+Vue | `VUE` |
| Flutter, Dart, 모바일 앱 | `FLUTTER` |

- 복수 매칭 또는 매칭 없음 시 사용자에게 질문하여 결정
- 결정된 `{PLATFORM}` 값은 이후 모든 가이드에서 조건 분기에 사용

## 산출물

- `AGENTS.md > ### develop > 지원 변수`에 결정된 변수 값 저장 (PLATFORM, FRONTEND_PORT, MOCK, TEST_MODE 중 결정된 것)
- 호출 가이드 문서의 IF/ELIF 블록 중 일치하는 분기만 실행
