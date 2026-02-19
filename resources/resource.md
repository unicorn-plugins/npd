# 로컬 리소스 카탈로그

npd 플러그인에 포함된 공유자원 목록. clauding-guide에서 복사하여 npd 도메인에 맞게 관리.

---

## 가이드 목록

### plan 스킬 참조 가이드

| 가이드명 | 경로 | 설명 | 사용 에이전트 |
|---------|------|------|-------------|
| think-prompt | `guides/plan/think-prompt.md` | 기획 단계 사고방식 및 접근법 가이드 | product-owner, service-planner |

### design 스킬 참조 가이드

| 가이드명 | 경로 | 설명 | 사용 에이전트 |
|---------|------|------|-------------|
| architecture-patterns | `guides/design/architecture-patterns.md` | 클라우드 아키텍처 패턴 (MSA, 레이어드 등) | architect |
| architecture-highlevel | `guides/design/architecture-highlevel.md` | 상위수준 아키텍처 설계 | architect |
| logical-architecture-design | `guides/design/logical-architecture-design.md` | 논리 아키텍처 설계 | architect |
| sequence-outer-design | `guides/design/sequence-outer-design.md` | 외부 시퀀스 다이어그램 설계 | architect |
| sequence-inner-design | `guides/design/sequence-inner-design.md` | 내부 시퀀스 다이어그램 설계 | architect |
| api-design | `guides/design/api-design.md` | REST API 설계 가이드 | architect |
| class-design | `guides/design/class-design.md` | 클래스 다이어그램 설계 | architect |
| data-design | `guides/design/data-design.md` | 데이터 모델 설계 | architect |
| uiux-design | `guides/design/uiux-design.md` | UI/UX 설계 가이드 | service-planner |
| uiux-prototype | `guides/design/uiux-prototype.md` | UI/UX 프로토타입 설계 | service-planner |

### develop 스킬 참조 가이드

| 가이드명 | 경로 | 설명 | 사용 에이전트 |
|---------|------|------|-------------|
| dev-backend | `guides/develop/dev-backend.md` | Spring Boot 백엔드 개발 가이드 | backend-developer |
| dev-backend-testcode | `guides/develop/dev-backend-testcode.md` | 백엔드 테스트코드 작성 가이드 | backend-developer, qa-engineer |
| dev-frontend | `guides/develop/dev-frontend.md` | 프론트엔드 개발 가이드 | frontend-developer |
| test-backend | `guides/develop/test-backend.md` | 백엔드 테스트 실행 가이드 | qa-engineer |
| database-plan | `guides/develop/database-plan.md` | 데이터베이스 설계 및 계획 | backend-developer |
| database-install | `guides/develop/database-install.md` | 데이터베이스 설치 가이드 | backend-developer |
| mermaid-guide | `guides/tools/mermaid-guide.md` | Mermaid 다이어그램 작성 가이드 | architect, ai-engineer |
| plantuml-guide | `guides/tools/plantuml-guide.md` | PlantUML 다이어그램 작성 가이드 | architect |

### deploy 스킬 참조 가이드

| 가이드명 | 경로 | 설명 | 사용 에이전트 |
|---------|------|------|-------------|
| build-image-back | `guides/deploy/build-image-back.md` | 백엔드 Docker 이미지 빌드 | devops-engineer |
| build-image-front | `guides/deploy/build-image-front.md` | 프론트엔드 Docker 이미지 빌드 | devops-engineer |
| run-container-guide-back | `guides/deploy/run-container-guide-back.md` | 백엔드 컨테이너 실행 가이드 | devops-engineer |
| run-container-guide-front | `guides/deploy/run-container-guide-front.md` | 프론트엔드 컨테이너 실행 가이드 | devops-engineer |
| deploy-k8s-back | `guides/deploy/deploy-k8s-back.md` | 백엔드 Kubernetes 배포 | devops-engineer |
| deploy-k8s-front | `guides/deploy/deploy-k8s-front.md` | 프론트엔드 Kubernetes 배포 | devops-engineer |
| deploy-actions-cicd-back | `guides/deploy/deploy-actions-cicd-back.md` | 백엔드 GitHub Actions CI/CD | devops-engineer |
| deploy-actions-cicd-front | `guides/deploy/deploy-actions-cicd-front.md` | 프론트엔드 GitHub Actions CI/CD | devops-engineer |
