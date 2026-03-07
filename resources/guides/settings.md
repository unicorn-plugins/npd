# NPD 사전 설정 파일 (Settings)

각 스킬(create, plan, design, develop, deploy, cicd)이 사용자에게 묻는 모든 질문을
이 파일에 미리 기록하면, **자동 진행 모드로 질문 없이 워크플로우를 실행**할 수 있음.

## 사용 방법

1. 이 파일을 프로젝트 루트에 `.npd/settings.yaml`로 복사
2. 각 항목의 값을 프로젝트에 맞게 수정
3. 빈 값(`""`, `~`)은 해당 스킬 실행 시 사용자에게 질문하거나 기본값 적용
4. 스킬 오케스트레이터는 `<!--ASK_USER-->` 처리 전 `.npd/settings.yaml`을 먼저 확인하고,
   값이 존재하면 질문을 건너뛰고 해당 값을 사용

---

## 설정 파일 구조 (`.npd/settings.yaml`)

```yaml
# ============================================================
# NPD 사전 설정 (Pre-configured Settings)
# ============================================================
# 각 스킬이 사용자에게 묻는 질문의 답을 미리 제공함.
# 값이 비어있으면(~) 실행 시 질문하거나 기본값 적용.
# ============================================================

# ------------------------------------------------------------
# 공통 설정
# ------------------------------------------------------------
common:
  # 진행 모드: "자동 진행" | "단계별 승인"
  # - 자동 진행: 모든 단계를 승인 없이 연속 실행
  # - 단계별 승인: 각 단계 완료 후 승인/재작업/중단 선택
  progress_mode: "자동 진행"

# ------------------------------------------------------------
# plan: 기획 단계
# ------------------------------------------------------------
plan:
  # 고객 경험 조사 규모 (Step 5)
  customer_research:
    # 고객경험 인터뷰 대상자 수 (기본값: 10)
    interview_count: 10
    # 관찰 조사 횟수 (기본값: 10)
    observation_count: 10
    # 체험 테스트 횟수 (기본값: 10)
    experience_count: 10

  # 문제검증 인터뷰 대상자 수 (Step 7-2, 기본값: 10)
  problem_validation_interview_count: 10

  # 디자인 레퍼런스 URL (Step 15, 비워두면 레퍼런스 없이 진행)
  # 예: "https://wwit.design", 이미지 경로도 가능
  design_reference: ""

  # 이미지 생성용 Gemini API Key (Step 16)
  # 프로토타입 이미지 AI 생성에 사용
  # https://aistudio.google.com/apikey 에서 발급
  # 비워두면 placeholder 텍스트로 대체
  gemini_api_key: ""

# ------------------------------------------------------------
# design: 기술 설계 단계
# ------------------------------------------------------------
design:
  # 패키지 네이밍 정보 (Step 0-1-1)
  package_naming:
    # 회사/조직명 (예: unicorn)
    # → com.{org}.{root}.{서비스명}
    org: ""
    # 대표 시스템명 / Root Project명 (예: lifesub)
    # → com.{org}.{root}.{서비스명}
    root: ""

  # Cloud 서비스 (Step 0-1-2): "AWS" | "Azure" | "GCP"
  cloud: ""

  # 마이크로서비스별 설계 아키텍처 패턴 (Step 5-0b)
  # 자동 진행 모드에서는 architect가 서비스 특성 분석 후 자율 결정
  # 단계별 승인 모드에서만 사용자 선택
  # 형식: {서비스영문명}: "Layered Architecture" | "Clean Architecture"
  # 예:
  #   member-service: "Layered Architecture"
  #   travel-service: "Clean Architecture"
  #   recommendation-service: "Clean Architecture"
  architecture_patterns: {}

# ------------------------------------------------------------
# develop: 개발 단계
# ------------------------------------------------------------
develop:
  # 개발 범위 (Step 0-1)
  # HighLevel 아키텍처 정의서의 14.1 개발 단계에서 이번에 구현할 Phase 번호 목록
  # 예: [1] (Phase 1만), [1, 2] (Phase 1+2)
  # 비워두면 실행 시 질문
  dev_phases: []

  # OAuth2 소셜 로그인 크리덴셜 (Step 0-2-1, 조건부)
  # 설계서에 OAuth2/소셜 로그인이 정의된 경우에만 필요
  # 비워두면 "나중에 설정"으로 처리
  oauth2:
    # Provider별 크리덴셜 (예: google, kakao, naver)
    # google:
    #   client_id: ""
    #   client_secret: ""
    # kakao:
    #   client_id: ""
    #   client_secret: ""
    providers: {}

  # Gemini API Key (Step 0-2-2)
  # 프론트엔드 이미지 생성용 (아이콘, 일러스트, 배너 등)
  # plan 단계와 동일한 키 사용 가능
  # 비워두면 CSS/SVG 기반 대체 구현
  gemini_api_key: ""

  # AI 서비스 크리덴셜 (Step 0-2-3, 조건부)
  # AI 서비스 설계서가 존재하는 경우에만 필요
  # 비워두면 "나중에 설정"으로 처리
  ai_credentials:
    # LLM 제공자 API Key (예: OPENAI_API_KEY, ANTHROPIC_API_KEY)
    llm_api_key: ""
    # Tavily API Key (웹검색 Tool 사용 시)
    tavily_api_key: ""
    # LangSmith API Key (LLM 호출 모니터링)
    langsmith_api_key: ""
    # Vector DB 접속 정보 (RAG 사용 시)
    vector_db_url: ""

  # 테스트 모드 (Step 0-2-4)
  # "자동 테스트" | "수동 테스트"
  # - 자동 테스트: AI가 Playwright Test Suite로 자동 수행
  # - 수동 테스트: 사람이 브라우저에서 직접 테스트, AI가 수정 지원
  # 자동 진행 모드에서는 "자동 테스트"로 강제 설정
  test_mode: "자동 테스트"

# ------------------------------------------------------------
# deploy: 배포 단계
# ------------------------------------------------------------
deploy:
  # 시작 Step (Step 0)
  # "Step 1" | "Step 2" | "Step 3" | "Step 4" | "Step 5"
  start_step: "Step 1"

  # Cloud 서비스: "AWS" | "Azure" | "GCP"
  # design 단계에서 설정한 값을 자동 참조 (CLAUDE.md에서 읽음)
  # 여기서 별도 설정 시 이 값 우선
  cloud: ""

  # 이미지 레지스트리 설정
  registry:
    # 레지스트리 유형: "Docker Hub" | "AWS ECR" | "Azure ACR" | "Google GCR"
    type: ""

    # Docker Hub 선택 시
    dockerhub:
      org_or_username: ""
      access_token: ""

    # AWS ECR 선택 시
    ecr:
      region: "ap-northeast-2"
      account_id: ""

    # Azure ACR 선택 시
    acr:
      name: ""

    # Google GCR (Artifact Registry) 선택 시
    gcr:
      project_id: ""
      region: "asia-northeast3"
      repo_name: ""

  # VM 설정
  vm:
    # ~/.ssh/config의 Host alias (비워두면 자동 감지 후 질문)
    ssh_host: ""

  # K8s 클러스터 설정
  k8s:
    # kubectx 컨텍스트명 (비워두면 자동 감지 후 질문)
    context: ""
    # 네임스페이스 (기본값: {ROOT} 시스템명)
    namespace: ""

  # K8s 배포 리소스 설정
  resources:
    # 모든 서비스 기본값
    default:
      replicas: 2
      cpu: "0.25/1"        # 요청값/최대값 (단위: core)
      memory: "256/1024"   # 요청값/최대값 (단위: MB)
    # 서비스별 예외 설정 (기본값과 다른 서비스만 기록)
    # 예:
    #   ai-service:
    #     replicas: 1
    #     cpu: "0.5/2"
    #     memory: "512/2048"
    overrides: {}

  # SSL 도메인 (Step 4 POST_ACTION)
  # 비워두면 Nginx server_name에서 자동 감지
  ssl_domain: ""

# ------------------------------------------------------------
# cicd: CI/CD 파이프라인 구성
# ------------------------------------------------------------
cicd:
  # CI 도구: "Jenkins" | "GitHub Actions"
  ci_tool: ""

  # 배포 환경 (복수 선택 가능)
  # ["dev"] | ["dev", "staging"] | ["dev", "staging", "prod"]
  environments:
    - "dev"

  # Jenkins 설정 (ci_tool이 "Jenkins"인 경우)
  jenkins:
    # Kubernetes Cloud 이름 (기본값: K8s 클러스터명)
    cloud_name: ""
    # 매니페스트 레포지토리 접근용 Jenkins Credential ID
    git_credentials: "github-credentials"

  # ArgoCD Git 인증 정보 (매니페스트 레포지토리 접근용)
  argocd:
    git_username: ""
    git_token: ""

  # hosts 파일 등록 완료 여부: true | false
  # true로 설정하면 hosts 등록 확인 질문 건너뜀
  hosts_registered: false
  
```

---

## 항목별 상세 설명

### common (공통)

| 항목 | 사용 스킬 | 설명 |
|------|----------|------|
| `progress_mode` | 전체 | 모든 스킬의 Step 0에서 묻는 진행 모드. "자동 진행" 설정 시 질문 없이 연속 실행 |

### create (프로젝트 생성)

| 항목 | Step | 설명 |
|------|------|------|
| `mvp_topic` | 1 | MVP 주제 (필수 입력) |
| `project_dir` | 2 | 프로젝트 디렉토리 경로 |
| `github.create_repo` | 6 | GitHub 레포 생성 여부 |
| `github.organization` | 6-1 | GitHub Organization명 |
| `github.visibility` | 6-2 | Public/Private 선택 |

### plan (기획)

| 항목 | Step | 설명 |
|------|------|------|
| `customer_research.*` | 5 | 고객 경험 조사 규모 (인터뷰/관찰/체험 횟수) |
| `problem_validation_interview_count` | 7-2 | 문제검증 인터뷰 대상자 수 |
| `design_reference` | 15 | UI/UX 디자인 레퍼런스 URL |
| `gemini_api_key` | 16 | 프로토타입 이미지 생성용 Gemini API Key |

### design (기술 설계)

| 항목 | Step | 설명 |
|------|------|------|
| `package_naming.org` | 0-1-1 | Java 패키지 회사/조직명 |
| `package_naming.root` | 0-1-1 | 대표 시스템명 |
| `cloud` | 0-1-2 | Cloud 서비스 (AWS/Azure/GCP) |
| `architecture_patterns` | 5-0b | 마이크로서비스별 설계 아키텍처 패턴 |

### develop (개발)

| 항목 | Step | 설명 |
|------|------|------|
| `dev_phases` | 0-1 | 이번에 구현할 개발 Phase 번호 목록 |
| `oauth2.providers` | 0-2-1 | OAuth2 소셜 로그인 크리덴셜 |
| `gemini_api_key` | 0-2-2 | 프론트엔드 이미지 생성용 Gemini API Key |
| `ai_credentials.*` | 0-2-3 | AI 서비스 크리덴셜 (LLM/Tavily/LangSmith 등) |
| `test_mode` | 0-2-4 | 브라우저 테스트 모드 (자동/수동) |

### deploy (배포)

| 항목 | Step | 설명 |
|------|------|------|
| `start_step` | 0 | 시작 Step 선택 |
| `cloud` | 1-1 | Cloud 서비스 |
| `registry.*` | 배포환경 선택 | 이미지 레지스트리 유형 및 상세 정보 |
| `vm.ssh_host` | 1-5 | 배포 대상 VM의 SSH Host alias |
| `k8s.context` | 3차 | K8s 클러스터 컨텍스트명 |
| `k8s.namespace` | 3차 | K8s 네임스페이스 |
| `resources.*` | 4차 | K8s 배포 리소스 설정 (파드수/CPU/메모리) |
| `ssl_domain` | Step 4 POST | SSL 도메인 |

### cicd (CI/CD 파이프라인)

| 항목 | Step | 설명 |
|------|------|------|
| `ci_tool` | 0-2 | CI 도구 (Jenkins/GitHub Actions) |
| `environments` | 0-6 | 배포 환경 목록 (dev/staging/prod) |
| `jenkins.*` | 2.5 | Jenkins Cloud Name, Git Credentials |
| `argocd.*` | 2 | ArgoCD 매니페스트 레포 Git 인증 정보 |
| `hosts_registered` | 0-0 | hosts 파일 등록 완료 여부 |

---

## 최소 필수 항목

전체 워크플로우(create → plan → design → develop → deploy → cicd)를
자동으로 실행하기 위한 **최소 필수 입력 항목**:

| 항목 | 필수 시점 | 비고 |
|------|----------|------|
| `create.mvp_topic` | create | MVP 주제가 없으면 시작 불가 |
| `design.package_naming.org` | design | Java 패키지명 생성에 필수 |
| `design.package_naming.root` | design | Java 패키지명 생성에 필수 |
| `design.cloud` | design, deploy | Cloud 서비스 미선택 시 질문 발생 |
| `deploy.registry.type` | deploy | 이미지 레지스트리 미선택 시 질문 발생 |
| `deploy.registry.{유형별 상세}` | deploy | 선택한 레지스트리의 상세 정보 |
| `cicd.ci_tool` | cicd | CI 도구 미선택 시 질문 발생 |
| `cicd.argocd.git_username` | cicd | ArgoCD 인증 필수 |
| `cicd.argocd.git_token` | cicd | ArgoCD 인증 필수 |

나머지 항목은 기본값이 존재하거나, 자동 감지가 가능하여 비워둘 수 있음.
