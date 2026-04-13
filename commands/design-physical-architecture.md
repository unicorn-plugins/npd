---
description: 물리 아키텍처 설계
---

### 물리 아키텍처 설계 Agent: architect (`/ralph` 활용)
1. 현재 작업 중인 프로젝트의 `CLAUDE.md` 파일을 "view_file" 등으로 꼼꼼히 읽으세요.
2. 파일에서 `NPD_PLUGIN_DIR`의 위치를 파악할 뿐만 아니라, 그 안에 적힌 팀 행동원칙, 대화 가이드, 정직한 보고 등 "모든 지침"을 이번 작업 전체에 걸쳐 우선적으로 엄격히 준수하세요.
3. 파악한 경로를 기준으로 아래 가이드를 준수하여 진행하세요.

- **GUIDE**: `{NPD_PLUGIN_DIR}/resources/guides/design/physical-architecture-design.md` 준수
- **TASK**: 주요/운영 환경별 K8s 인프라/네트워크 컴포넌트 구성과 Mermaid 다이어그램을 포함하여 문서를 설계 및 작성. 
- **EXPECTED OUTCOME**: `docs/design/physical/physical-architecture.md`, `physical-architecture-dev.md`, `physical-architecture-prod.md`, `physical-architecture-dev.mmd`, `physical-architecture-prod.mmd`, `network-dev.mmd`, `network-prod.mmd`

## 활성화 조건

사용자가 "물리 아키텍처 설계", "물리 아키텍처 설계 해줘", "물리 아키텍처 부탁해" 키워드를 언급할 때.

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구 호출 필수 (텍스트 출력 금지) |

## 완료 조건

- [ ] 물리 아키텍처 설계서(`docs/design/physical/`) 작성 완료
