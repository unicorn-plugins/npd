---
description: 물리아키텍처 설계
---

### 물리 아키텍처 설계 → Agent: architect (`/ralph` 활용)
- **GUIDE**: `resources/guides/design/physical-architecture-design.md` 참조
- **TASK**: 개발·운영 환경별 K8s 인프라·네트워크·배포 구조를 Mermaid 다이어그램과 함께 설계하고 문법 검증 수행. 
- **EXPECTED OUTCOME**: `docs/design/physical/physical-architecture.md`, `physical-architecture-dev.md`, `physical-architecture-prod.md`, `physical-architecture-dev.mmd`, `physical-architecture-prod.mmd`, `network-dev.mmd`, `network-prod.mmd`

## 활성화 조건

사용자가 "물리 아키텍처 설계", "물리 아키텍처 설계 해줘", "물리 아키텍처 만들어줘" 키워드 감지 시.

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |

## 완료 조건

- [ ] 물리 아키텍처 설계서(`docs/design/physical/`)가 생성됨

