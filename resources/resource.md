# 로컬 리소스 카탈로그

npd 플러그인에 포함된 공유자원 목록.

[Top](#로컬-리소스-카탈로그)

---

## 리소스 분류 체계

| 유형 | 설명 | 디렉토리 |
|------|------|---------|
| 가이드 | 각 스킬 단계에서 참조하는 문서 | `resources/guides/` |
| 도구 | 커스텀 도구의 소스 및 사용법 카탈로그 | `resources/tools/` |

[Top](#로컬-리소스-카탈로그)

---

## 가이드 목록

| 2차 분류 | 가이드명 | 설명 | 상세 |
|---------|---------|------|------|
| setup | prepare | 로컬 개발 환경 구성 (기본/추가 설치 프로그램 안내) | [상세](guides/setup/prepare.md) |
| plan | think-prompt | 기획 단계 사고방식 및 접근법 가이드 | [상세](guides/plan/think-prompt.md) |
| design | architecture-patterns | 클라우드 아키텍처 패턴 (MSA, 레이어드 등) | [상세](guides/design/architecture-patterns.md) |
| design | architecture-highlevel | 상위수준 아키텍처 설계 | [상세](guides/design/architecture-highlevel.md) |
| design | logical-architecture-design | 논리 아키텍처 설계 | [상세](guides/design/logical-architecture-design.md) |
| design | sequence-outer-design | 외부 시퀀스 다이어그램 설계 | [상세](guides/design/sequence-outer-design.md) |
| design | sequence-inner-design | 내부 시퀀스 다이어그램 설계 | [상세](guides/design/sequence-inner-design.md) |
| design | api-design | REST API 설계 가이드 | [상세](guides/design/api-design.md) |
| design | class-design | 클래스 다이어그램 설계 | [상세](guides/design/class-design.md) |
| design | data-design | 데이터 모델 설계 | [상세](guides/design/data-design.md) |
| design | uiux-design | UI/UX 설계 가이드 | [상세](guides/design/uiux-design.md) |
| design | uiux-prototype | UI/UX 프로토타입 설계 | [상세](guides/design/uiux-prototype.md) |
| develop | dev-backend | Spring Boot 백엔드 개발 가이드 | [상세](guides/develop/dev-backend.md) |
| develop | dev-backend-testcode | 백엔드 테스트코드 작성 가이드 | [상세](guides/develop/dev-backend-testcode.md) |
| develop | dev-frontend | 프론트엔드 개발 가이드 | [상세](guides/develop/dev-frontend.md) |
| develop | test-backend | 백엔드 테스트 실행 가이드 | [상세](guides/develop/test-backend.md) |
| develop | database-plan | 데이터베이스 설계 및 계획 | [상세](guides/develop/database-plan.md) |
| develop | database-install | 데이터베이스 설치 가이드 | [상세](guides/develop/database-install.md) |
| deploy | build-image-back | 백엔드 Docker 이미지 빌드 | [상세](guides/deploy/build-image-back.md) |
| deploy | build-image-front | 프론트엔드 Docker 이미지 빌드 | [상세](guides/deploy/build-image-front.md) |
| deploy | run-container-guide-back | 백엔드 컨테이너 실행 가이드 | [상세](guides/deploy/run-container-guide-back.md) |
| deploy | run-container-guide-front | 프론트엔드 컨테이너 실행 가이드 | [상세](guides/deploy/run-container-guide-front.md) |
| deploy | deploy-k8s-back | 백엔드 Kubernetes 배포 | [상세](guides/deploy/deploy-k8s-back.md) |
| deploy | deploy-k8s-front | 프론트엔드 Kubernetes 배포 | [상세](guides/deploy/deploy-k8s-front.md) |
| deploy | deploy-actions-cicd-back | 백엔드 GitHub Actions CI/CD | [상세](guides/deploy/deploy-actions-cicd-back.md) |
| deploy | deploy-actions-cicd-front | 프론트엔드 GitHub Actions CI/CD | [상세](guides/deploy/deploy-actions-cicd-front.md) |
| tools | mermaid-guide | Mermaid 다이어그램 작성 가이드 | [상세](guides/tools/mermaid-guide.md) |
| tools | plantuml-guide | PlantUML 다이어그램 작성 가이드 | [상세](guides/tools/plantuml-guide.md) |

[Top](#로컬-리소스-카탈로그)

---

## 도구 목록

| 카테고리 | 도구명 | 설명 | 상세 |
|---------|--------|------|------|
| 커스텀 앱 | create_repo | GitHub REST API 기반 원격 저장소 생성 및 초기 푸시 (gh CLI 불요) | [상세](tools/create-repo.md) |
| 커스텀 앱 | generate_image | Gemini (Nano Banana) 모델 기반 이미지 생성 | [상세](tools/generate-image.md) |
| 커스텀 CLI | check-mermaid | Docker 기반 Mermaid 다이어그램 문법 검증 | [상세](tools/check-mermaid.md) |
| 커스텀 CLI | check-plantuml | Docker 기반 PlantUML 다이어그램 문법 검증 | [상세](tools/check-plantuml.md) |


[Top](#로컬-리소스-카탈로그)

---

## 도구 분류 체계

| 카테고리 | 설명 | 설치 주체 |
|---------|------|----------|
| 커스텀 앱 | 플러그인 자체 구현 프로그램 (Python 등) | 소스 포함 + 의존성 설치 |

[Top](#로컬-리소스-카탈로그)
