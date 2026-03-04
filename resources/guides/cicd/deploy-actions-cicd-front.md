# 프론트엔드 GitHub Actions 파이프라인 작성 가이드

## 목적
GitHub Actions 기반 CI 파이프라인을 구축한다. CI/CD 분리 구조로, CI는 빌드·푸시·매니페스트 레포지토리 image tag 업데이트까지 수행하고, CD는 ArgoCD가 매니페스트 레포지토리 변경을 감지하여 자동 배포한다. AWS EKS(ECR), Azure AKS(ACR), GCP GKE(Artifact Registry) 전 클라우드를 지원한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| K8s 클러스터 정보 | `(런타임 결정)` | 배포 대상 |
| 컨테이너 레지스트리 | `(런타임 결정)` | 이미지 푸시 대상 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| CI/CD 파이프라인 가이드 | `deployment/cicd/actions-pipeline-guide.md` |
| GitHub Actions 워크플로우 | `.github/workflows/frontend-cicd.yaml` |
| GitHub Actions 전용 Kustomize 매니페스트 | `.github/kustomize/*` |
| GitHub Actions 전용 환경별 설정 파일 | `.github/config/*` |

## 방법론

- 사전 준비사항 확인
  프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
  - {FRONTEND_SERVICE}: 프론트엔드 서비스명 (= {SERVICE_NAME}, package.json의 name 필드)
  - {CLOUD}: 클라우드 서비스 (AWS/Azure/GCP)
  - {IMG_REG}: 컨테이너 이미지 레지스트리 주소
  - {IMG_ORG}: 이미지 조직명
  - {NAMESPACE}: Namespace명
  - {MANIFEST_REPO_URL}: 매니페스트 레포지토리 URL
  - {MANIFEST_SECRET_GIT_USERNAME}: 매니페스트 레포지토리 접근용 GitHub Secret (Username)
  - {MANIFEST_SECRET_GIT_PASSWORD}: 매니페스트 레포지토리 접근용 GitHub Secret (Password/Token)

  클라우드별 추가 변수:
  - AWS: {ECR_ACCOUNT}, {ECR_REGION}, {EKS_CLUSTER}
  - Azure: {ACR_NAME}, {RESOURCE_GROUP}, {AKS_CLUSTER}
  - GCP: {GCR_REGION}, {GCR_PROJECT}, {GCR_REPO}, {GKE_CLUSTER}, {GKE_ZONE}

- 서비스명 확인
  package.json에서 확인.
  - {SERVICE_NAME}: package.json의 "name" 필드
  예시)
  ```json
  {
    ...
    "name": "phonebill-front",
    ...
  }
  ```

- Node.js 버전 확인
  package.json에서 Node.js 버전 확인.
  {NODE_VERSION}: "engines" 섹션에서 Node.js 버전 확인. 없으면 20 버전 사용.
  ```json
  {
    "engines": {
      "node": "20.x"
    }
  }
  ```

- GitHub 저장소 환경 구성 안내
  - GitHub Repository Secrets 설정
    - 클라우드별 인증정보 설정
    ```
    Repository Settings > Secrets and variables > Actions > Repository secrets에 등록
    ```

    **AWS (CLOUD=AWS):**
    ```
    AWS_ACCESS_KEY_ID: {AWS 액세스 키 ID}
    AWS_SECRET_ACCESS_KEY: {AWS 시크릿 액세스 키}
    ```

    **Azure (CLOUD=Azure):**
    ```
    # Azure Service Principal
    AZURE_CREDENTIALS:
    {
      "clientId": "{클라이언트ID}",
      "clientSecret": "{클라이언트시크릿}",
      "subscriptionId": "{구독ID}",
      "tenantId": "{테넌트ID}"
    }
    ```

    - ACR Credentials (Azure)
      Credential 구하는 방법 안내
      az acr credential show --name {acr 이름}
      예) az acr credential show --name acrdigitalgarage01
      ```
      ACR_USERNAME: {ACR_NAME}
      ACR_PASSWORD: {ACR패스워드}
      ```

    **GCP (CLOUD=GCP):**
    ```
    GCP_SA_KEY: {GCP 서비스 계정 키 JSON}
    ```

    **공통 (매니페스트 레포지토리 접근용):**
    ```
    MANIFEST_SECRET_GIT_USERNAME: {GitHub 사용자명을 저장한 Secret명}
    MANIFEST_SECRET_GIT_PASSWORD: {GitHub Token을 저장한 Secret명}
    ```

    - SonarQube URL과 인증 토큰
      SONAR_HOST_URL 구하는 방법과 SONAR_TOKEN 작성법 안내
      SONAR_HOST_URL: 아래 명령 수행 후 http://{External IP}를 지정
      k get svc -n sonarqube
      예) http://20.249.187.69

      SONAR_TOKEN 값은 아래와 같이 작성
      - SonarQube 로그인 후 우측 상단 'Administrator' > My Account 클릭
      - Security 탭 선택 후 토큰 생성

      ```
      SONAR_TOKEN: {SonarQube토큰}
      SONAR_HOST_URL: {SonarQube서버URL}
      ```

    - Docker Hub (Rate Limit 해결용)
      Docker Hub 패스워드 작성 방법 안내
      - DockerHub(https://hub.docker.com)에 로그인
      - 우측 상단 프로필 아이콘 클릭 후 Account Settings를 선택
      - 좌측메뉴에서 'Personal Access Tokens' 클릭하여 생성
      ```
      DOCKERHUB_USERNAME: {Docker Hub 사용자명}
      DOCKERHUB_PASSWORD: {Docker Hub 패스워드}
      ```

  - GitHub Repository Variables 설정
    ```
    # Workflow 제어 변수
    Repository Settings > Secrets and variables > Actions > Variables > Repository variables에 등록

    CLOUD: Azure (클라우드 서비스: AWS/Azure/GCP)
    REGISTRY: {IMG_REG} (컨테이너 이미지 레지스트리 주소)
    IMAGE_ORG: {IMG_ORG} (이미지 조직명)
    ENVIRONMENT: dev (기본값: dev/staging/prod)
    SKIP_SONARQUBE: true (기본값: true/false)
    ```

    **사용 방법:**
    - **자동 실행**: Push/PR 시 Variables에 설정된 값 사용
    - **수동 실행**: Actions 탭 > "Frontend CI/CD" > "Run workflow" 버튼 클릭
    - **변수 변경**: Repository Settings에서 Variables 값 수정

- ESLint 설정 파일 작성
  TypeScript React 프로젝트를 위한 `.eslintrc.cjs` 파일을 프로젝트 루트에 생성합니다.

  **⚠️ 중요**: ES 모듈 프로젝트에서는 `.eslintrc.cjs` 확장자 사용 필수

  ```javascript
  module.exports = {
    root: true,
    env: {
      browser: true,
      es2020: true,
      node: true
    },
    extends: [
      'eslint:recommended',
      'plugin:@typescript-eslint/recommended',
      'plugin:react-hooks/recommended'
    ],
    ignorePatterns: [
      'dist',
      '.eslintrc.cjs',
      'node_modules',
      'build',
      'coverage'
    ],
    parser: '@typescript-eslint/parser',
    parserOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      ecmaFeatures: {
        jsx: true
      }
    },
    plugins: [
      'react-refresh',
      '@typescript-eslint'
    ],
    rules: {
      // React 관련 규칙
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],

      // TypeScript 관련 규칙
      '@typescript-eslint/no-unused-vars': ['error', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_'
      }],
      '@typescript-eslint/no-explicit-any': 'warn',

      // 일반 규칙
      'no-unused-vars': 'off', // TypeScript 규칙을 사용

      // Hooks 규칙
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn'
    },
    overrides: [
      {
        files: ['**/*.test.ts', '**/*.test.tsx', '**/*.spec.ts', '**/*.spec.tsx'],
        env: {
          jest: true
        }
      }
    ]
  }
  ```

  **필수 ESLint 관련 devDependencies 설치**:
  ```bash
  npm install --save-dev eslint-plugin-react-refresh @typescript-eslint/parser @typescript-eslint/eslint-plugin eslint-plugin-react-hooks
  ```

  **package.json lint 스크립트 수정** (max-warnings 20으로 설정):
  ```json
  {
    "scripts": {
      "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 20"
    }
  }
  ```

- GitHub Actions 전용 Kustomize 디렉토리 구조 생성
  - GitHub Actions 전용 Kustomize 디렉토리 생성
    ```bash
    mkdir -p .github/kustomize/{base,overlays/{dev,staging,prod}}
    mkdir -p .github/kustomize/base
    mkdir -p .github/{config,scripts}
    ```
  - 기존 k8s 매니페스트를 base로 복사
    ```bash
    # 기존 deployment/k8s/* 파일들을 base로 복사
    cp deployment/k8s/* .github/kustomize/base/

    # 네임스페이스 하드코딩 제거
    find .github/kustomize/base -name "*.yaml" -exec sed -i 's/namespace: .*//' {} \;
    ```

- Base Kustomization 작성
  `.github/kustomize/base/kustomization.yaml` 파일 생성

  **⚠️ 중요: 리소스 누락 방지 가이드**
  1. **디렉토리별 파일 확인**: base 디렉토리의 모든 yaml 파일을 확인
  2. **일관성 체크**: 모든 리소스가 동일한 파일 구조를 가지는지 확인
  3. **누락 검증**: `ls .github/kustomize/base/` 명령으로 실제 파일과 kustomization.yaml 리스트 비교
  4. **명명 규칙 준수**: ConfigMap은 `configmap.yaml` 또는 `cm-{SERVICE_NAME}.yaml`, Service는 `service.yaml` 패턴 확인

  ```yaml
  apiVersion: kustomize.config.k8s.io/v1beta1
  kind: Kustomization

  resources:
    # Frontend resources
    - deployment.yaml
    - service.yaml
    - configmap.yaml
    - ingress.yaml

  images:
    - name: {IMG_REG}/{IMG_ORG}/{SERVICE_NAME}
      newTag: latest
  ```

  **검증 명령어**:
  ```bash
  # base 디렉토리의 파일 확인
  ls .github/kustomize/base/

  # kustomization.yaml 유효성 검사
  kubectl kustomize .github/kustomize/base/
  ```

- 환경별 Patch 파일 생성
  각 환경별로 필요한 patch 파일들을 생성합니다.
  **중요원칙**:
  - **base 매니페스트에 없는 항목은 추가 안함**
  - **base 매니페스트와 항목이 일치해야 함**

  **1. ConfigMap Patch 파일 생성**
  `.github/kustomize/overlays/{ENVIRONMENT}/configmap-patch.yaml`

  - base 매니페스트를 환경별로 복사
    ```
    cp .github/kustomize/base/configmap.yaml .github/kustomize/overlays/{ENVIRONMENT}/configmap-patch.yaml
    ```

  - 환경별 API 엔드포인트 설정
  - dev: 개발 API 서버 주소, staging/prod: 운영 API 서버 주소

  **2. Ingress Patch 파일 생성**
  `.github/kustomize/overlays/{ENVIRONMENT}/ingress-patch.yaml`
  - base의 ingress.yaml을 환경별로 오버라이드
  - **⚠️ 중요**: 개발환경 Ingress Host의 기본값은 base의 ingress.yaml과 **정확히 동일하게** 함
    - base에서 `host: {SERVICE_NAME}.20.214.196.128.nip.io` 이면
    - dev에서도 `host: {SERVICE_NAME}.20.214.196.128.nip.io` 로 동일하게 설정
    - **절대** `{SERVICE_NAME}-dev.xxx` 처럼 변경하지 말 것
  - Staging/Prod 환경별 도메인 설정: {SERVICE_NAME}-{환경}.도메인 형식
  - Staging/prod 환경은 HTTPS 강제 적용 및 SSL 인증서 설정
  - staging/prod는 nginx.ingress.kubernetes.io/ssl-redirect: "true"
  - dev는 nginx.ingress.kubernetes.io/ssl-redirect: "false"

  **3. Deployment Patch 파일 생성** ⚠️ **중요**
  `.github/kustomize/overlays/{ENVIRONMENT}/deployment-patch.yaml`

  **필수 포함 사항:**
  - ✅ **replicas 설정**: Deployment의 replica 수를 환경별로 설정
    - dev: 1 replica (리소스 절약)
    - staging: 2 replicas
    - prod: 3 replicas
  - ✅ **resources 설정**: Deployment의 resources를 환경별로 설정
    - dev: requests(256m CPU, 256Mi Memory), limits(1024m CPU, 1024Mi Memory)
    - staging: requests(512m CPU, 512Mi Memory), limits(2048m CPU, 2048Mi Memory)
    - prod: requests(1024m CPU, 1024Mi Memory), limits(4096m CPU, 4096Mi Memory)

  **작성 형식:**
  - **Strategic Merge Patch 형식** 사용 (JSON Patch 아님)
  - replicas와 resources를 **반드시 모두** 포함

- 환경별 Overlay 작성
  각 환경별로 `overlays/{환경}/kustomization.yaml` 생성
  ```yaml
  apiVersion: kustomize.config.k8s.io/v1beta1
  kind: Kustomization

  namespace: {NAMESPACE}

  resources:
    - ../../base

  patches:
    - path: configmap-patch.yaml
      target:
        kind: ConfigMap
        name: cm-{SERVICE_NAME}
    - path: deployment-patch.yaml
      target:
        kind: Deployment
        name: {SERVICE_NAME}
    - path: ingress-patch.yaml
      target:
        kind: Ingress
        name: {SERVICE_NAME}

  images:
    - name: {IMG_REG}/{IMG_ORG}/{SERVICE_NAME}
      newTag: latest

  ```

- GitHub Actions 워크플로우 작성
  `.github/workflows/frontend-cicd.yaml` 파일 생성 방법을 안내합니다.

  > **⚠️ 주의**: 아래 YAML 코드 블록은 마크다운 리스트 내에 있어 2칸 들여쓰기가 포함되어 있습니다. 파일로 생성할 때 **앞의 2칸 들여쓰기를 제거**하세요. `name:`이 컬럼 0에서 시작해야 합니다.

  주요 구성 요소:
  - **Build & Test**: Node.js 기반 빌드 및 단위 테스트, ESLint 검사
  - **SonarQube Analysis**: 프론트엔드 코드 품질 분석 및 Quality Gate
  - **Container Build & Push**: 환경별 이미지 태그로 빌드 및 푸시
  - **Update Manifest Repository**: 매니페스트 레포지토리 image tag 업데이트 (ArgoCD GitOps)

  ```yaml
  name: Frontend CI/CD

  on:
    push:
      branches: [ main, develop ]
      paths:
        - 'src/**'
        - 'public/**'
        - 'package*.json'
        - 'tsconfig*.json'
        - 'vite.config.ts'
        - 'index.html'
        - '.github/**'
    pull_request:
      branches: [ main ]
    workflow_dispatch:
      inputs:
        ENVIRONMENT:
          description: 'Target environment'
          required: true
          default: 'dev'
          type: choice
          options:
            - dev
            - staging
            - prod
        SKIP_SONARQUBE:
          description: 'Skip SonarQube Analysis'
          required: false
          default: 'true'
          type: choice
          options:
            - 'true'
            - 'false'

  env:
    # ⚠️ 필수 치환: 'Azure' 기본값을 [실행정보]의 CLOUD 값으로 치환하세요.
    # Repository Variables에 CLOUD를 반드시 설정해야 합니다. 미설정 시 Azure로 동작합니다.
    CLOUD: ${{ vars.CLOUD || 'Azure' }}
    REGISTRY: ${{ vars.REGISTRY }}
    IMAGE_ORG: ${{ vars.IMAGE_ORG }}

  jobs:
    build:
      name: Build and Test
      runs-on: ubuntu-latest
      outputs:
        image_tag: ${{ steps.set_outputs.outputs.image_tag }}
        environment: ${{ steps.set_outputs.outputs.environment }}

      steps:
        - name: Check out code
          uses: actions/checkout@v4

        - name: Set up Node.js {NODE_VERSION}
          uses: actions/setup-node@v4
          with:
            node-version: '{NODE_VERSION}'
            cache: 'npm'

        - name: Determine environment
          id: determine_env
          run: |
            ENVIRONMENT="${{ github.event.inputs.ENVIRONMENT || vars.ENVIRONMENT || 'dev' }}"
            echo "environment=$ENVIRONMENT" >> $GITHUB_OUTPUT

        - name: Load environment variables
          id: env_vars
          run: |
            ENV=${{ steps.determine_env.outputs.environment }}
            CLOUD="${{ vars.CLOUD || 'Azure' }}"

            # Initialize variables with defaults
            REGISTRY="${{ vars.REGISTRY }}"
            IMAGE_ORG="${{ vars.IMAGE_ORG }}"

            # Cloud-specific defaults
            # Azure
            RESOURCE_GROUP="${{ vars.RESOURCE_GROUP }}"
            AKS_CLUSTER="${{ vars.AKS_CLUSTER }}"
            # AWS
            ECR_REGION="${{ vars.ECR_REGION }}"
            EKS_CLUSTER="${{ vars.EKS_CLUSTER }}"
            # GCP
            GCR_REGION="${{ vars.GCR_REGION }}"
            GKE_CLUSTER="${{ vars.GKE_CLUSTER }}"
            GKE_ZONE="${{ vars.GKE_ZONE }}"

            # Read environment variables from .github/config file
            if [[ -f ".github/config/deploy_env_vars_${ENV}" ]]; then
              while IFS= read -r line || [[ -n "$line" ]]; do
                # Skip comments and empty lines
                [[ "$line" =~ ^#.*$ ]] && continue
                [[ -z "$line" ]] && continue

                # Extract key-value pairs
                key=$(echo "$line" | cut -d '=' -f1)
                value=$(echo "$line" | cut -d '=' -f2-)

                # Override defaults if found in config
                case "$key" in
                  # Azure
                  "resource_group") RESOURCE_GROUP="$value" ;;
                  "cluster_name") AKS_CLUSTER="$value" ;;
                  # AWS
                  "ecr_region") ECR_REGION="$value" ;;
                  "eks_cluster") EKS_CLUSTER="$value" ;;
                  # GCP
                  "gcr_region") GCR_REGION="$value" ;;
                  "gke_cluster") GKE_CLUSTER="$value" ;;
                  "gke_zone") GKE_ZONE="$value" ;;
                esac
              done < ".github/config/deploy_env_vars_${ENV}"
            fi

            # Export common variables
            echo "REGISTRY=$REGISTRY" >> $GITHUB_ENV
            echo "IMAGE_ORG=$IMAGE_ORG" >> $GITHUB_ENV

            # Export cloud-specific variables
            if [[ "$CLOUD" == "Azure" ]]; then
              echo "RESOURCE_GROUP=$RESOURCE_GROUP" >> $GITHUB_ENV
              echo "AKS_CLUSTER=$AKS_CLUSTER" >> $GITHUB_ENV
            elif [[ "$CLOUD" == "AWS" ]]; then
              echo "ECR_REGION=$ECR_REGION" >> $GITHUB_ENV
              echo "EKS_CLUSTER=$EKS_CLUSTER" >> $GITHUB_ENV
            elif [[ "$CLOUD" == "GCP" ]]; then
              echo "GCR_REGION=$GCR_REGION" >> $GITHUB_ENV
              echo "GKE_CLUSTER=$GKE_CLUSTER" >> $GITHUB_ENV
              echo "GKE_ZONE=$GKE_ZONE" >> $GITHUB_ENV
            fi

        - name: Install dependencies
          run: npm ci

        - name: Build and Test
          run: |
            npm run build
            npm run lint

        - name: SonarQube Analysis & Quality Gate
          env:
            GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
            SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
            SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
          run: |
            # Check if SonarQube should be skipped
            SKIP_SONARQUBE="${{ github.event.inputs.SKIP_SONARQUBE || 'true' }}"

            if [[ "$SKIP_SONARQUBE" == "true" ]]; then
              echo "⏭️ Skipping SonarQube Analysis (SKIP_SONARQUBE=$SKIP_SONARQUBE)"
              exit 0
            fi

            npm install -g sonarqube-scanner
            sonar-scanner \
              -Dsonar.projectKey={SERVICE_NAME}-${{ steps.determine_env.outputs.environment }} \
              -Dsonar.projectName={SERVICE_NAME}-${{ steps.determine_env.outputs.environment }} \
              -Dsonar.sources=src \
              -Dsonar.tests=src \
              -Dsonar.test.inclusions=**/*.test.ts,**/*.test.tsx,**/*.spec.ts,**/*.spec.tsx \
              -Dsonar.exclusions=node_modules/**,dist/**,build/**,coverage/**,**/*.config.js,**/*.config.ts,scripts/** \
              -Dsonar.scm.disabled=true \
              -Dsonar.sourceEncoding=UTF-8 \
              -Dsonar.typescript.tsconfigPaths=tsconfig.json \
              -Dsonar.javascript.lcov.reportPaths=coverage/lcov.info \
              -Dsonar.javascript.node.maxspace=4096 \
              -Dsonar.host.url=$SONAR_HOST_URL \
              -Dsonar.token=$SONAR_TOKEN

        - name: Upload build artifacts
          uses: actions/upload-artifact@v4
          with:
            name: dist
            path: dist/

        - name: Set outputs
          id: set_outputs
          run: |
            # Generate timestamp for image tag
            IMAGE_TAG=$(date +%Y%m%d%H%M%S)
            echo "image_tag=$IMAGE_TAG" >> $GITHUB_OUTPUT
            echo "environment=${{ steps.determine_env.outputs.environment }}" >> $GITHUB_OUTPUT

    release:
      name: Build and Push Docker Image
      needs: build
      runs-on: ubuntu-latest

      steps:
        - name: Check out code
          uses: actions/checkout@v4

        - name: Download build artifacts
          uses: actions/download-artifact@v4
          with:
            name: dist
            path: dist/

        - name: Set environment variables from build job
          run: |
            echo "REGISTRY=${{ vars.REGISTRY }}" >> $GITHUB_ENV
            echo "IMAGE_ORG=${{ vars.IMAGE_ORG }}" >> $GITHUB_ENV
            echo "ENVIRONMENT=${{ needs.build.outputs.environment }}" >> $GITHUB_ENV
            echo "IMAGE_TAG=${{ needs.build.outputs.image_tag }}" >> $GITHUB_ENV

        - name: Set up Docker Buildx
          uses: docker/setup-buildx-action@v3

        - name: Login to Docker Hub (prevent rate limit)
          uses: docker/login-action@v3
          with:
            username: ${{ secrets.DOCKERHUB_USERNAME }}
            password: ${{ secrets.DOCKERHUB_PASSWORD }}

        # Cloud-conditional registry login
        # === AWS ECR ===
        # (CLOUD == AWS일 때 사용)
        - name: Configure AWS credentials
          if: ${{ env.CLOUD == 'AWS' }}
          uses: aws-actions/configure-aws-credentials@v4
          with:
            aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
            aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
            aws-region: ${{ vars.ECR_REGION }}

        - name: Login to Amazon ECR
          if: ${{ env.CLOUD == 'AWS' }}
          run: |
            aws ecr get-login-password --region ${{ vars.ECR_REGION }} | docker login --username AWS --password-stdin ${{ env.REGISTRY }}

        # === Azure ACR ===
        # (CLOUD == Azure일 때 사용)
        - name: Login to Azure Container Registry
          if: ${{ env.CLOUD == 'Azure' }}
          uses: docker/login-action@v3
          with:
            registry: ${{ env.REGISTRY }}
            username: ${{ secrets.ACR_USERNAME }}
            password: ${{ secrets.ACR_PASSWORD }}

        # === GCP Artifact Registry ===
        # (CLOUD == GCP일 때 사용)
        - name: Authenticate to Google Cloud
          if: ${{ env.CLOUD == 'GCP' }}
          uses: google-github-actions/auth@v2
          with:
            credentials_json: ${{ secrets.GCP_SA_KEY }}

        - name: Login to Google Artifact Registry
          if: ${{ env.CLOUD == 'GCP' }}
          run: |
            gcloud auth configure-docker ${{ vars.GCR_REGION }}-docker.pkg.dev

        - name: Build and push Docker image
          run: |
            docker build \
              -f deployment/container/Dockerfile-frontend \
              --build-arg PROJECT_FOLDER="." \
              --build-arg BUILD_FOLDER="deployment/container" \
              -t ${{ env.REGISTRY }}/${{ env.IMAGE_ORG }}/{SERVICE_NAME}:${{ needs.build.outputs.environment }}-${{ needs.build.outputs.image_tag }} .

            docker push ${{ env.REGISTRY }}/${{ env.IMAGE_ORG }}/{SERVICE_NAME}:${{ needs.build.outputs.environment }}-${{ needs.build.outputs.image_tag }}

    update-manifest:
      name: Update Frontend Manifest Repository
      needs: [build, release]
      runs-on: ubuntu-latest

      steps:
      - name: Set image tag environment variable
        run: |
          echo "IMAGE_TAG=${{ needs.build.outputs.image_tag }}" >> $GITHUB_ENV
          echo "ENVIRONMENT=${{ needs.build.outputs.environment }}" >> $GITHUB_ENV

      - name: Update Frontend Manifest Repository
        # ⚠️ 필수 치환 안내:
        #   아래 secrets.GIT_USERNAME, secrets.GIT_PASSWORD는 기본 Secret 이름입니다.
        #   [실행정보]의 MANIFEST_SECRET_GIT_USERNAME / MANIFEST_SECRET_GIT_PASSWORD 값이
        #   다른 이름이면 해당 이름으로 치환하세요.
        #   예) MANIFEST_SECRET_GIT_USERNAME=MY_GIT_USER이면
        #       ${{ secrets.GIT_USERNAME }} → ${{ secrets.MY_GIT_USER }}로 변경
        run: |
          REPO_URL=$(echo "{MANIFEST_REPO_URL}" | sed 's|https://||')
          git clone https://${{ secrets.GIT_USERNAME }}:${{ secrets.GIT_PASSWORD }}@${REPO_URL} manifest-repo
          cd manifest-repo

          curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
          sudo mv kustomize /usr/local/bin/

          cd {FRONTEND_SERVICE}/kustomize/overlays/${{ env.ENVIRONMENT }}
          kustomize edit set image ${{ env.REGISTRY }}/${{ env.IMAGE_ORG }}/{SERVICE_NAME}=${{ env.REGISTRY }}/${{ env.IMAGE_ORG }}/{SERVICE_NAME}:${{ env.ENVIRONMENT }}-${{ env.IMAGE_TAG }}

          cd ../../../..
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add .
          git commit -m "Update {SERVICE_NAME} ${{ env.ENVIRONMENT }} image to ${{ env.ENVIRONMENT }}-${{ env.IMAGE_TAG }}"
          git push origin main

          echo "매니페스트 업데이트 완료. ArgoCD가 자동으로 배포합니다."

  ```

- GitHub Actions 전용 환경별 설정 파일 작성
  `.github/config/deploy_env_vars_{환경}` 파일 생성 방법

  환경별 설정 파일을 CLOUD에 맞게 작성합니다. 각 환경(dev/staging/prod)별로 동일 형식의 파일을 생성합니다.

  **Azure (CLOUD=Azure):**
  **.github/config/deploy_env_vars_{환경}**
  ```bash
  # {환경} Environment Configuration (Azure)
  resource_group={RESOURCE_GROUP}
  cluster_name={AKS_CLUSTER}
  ```

  **AWS (CLOUD=AWS):**
  **.github/config/deploy_env_vars_{환경}**
  ```bash
  # {환경} Environment Configuration (AWS)
  ecr_region={ECR_REGION}
  eks_cluster={EKS_CLUSTER}
  ```

  **GCP (CLOUD=GCP):**
  **.github/config/deploy_env_vars_{환경}**
  ```bash
  # {환경} Environment Configuration (GCP)
  gcr_region={GCR_REGION}
  gke_cluster={GKE_CLUSTER}
  gke_zone={GKE_ZONE}
  ```

  **참고**: Jenkins config 파일에는 `namespace`가 포함되지만, GitHub Actions에서는 namespace가 Kustomize overlay의 `kustomization.yaml`에서 관리되므로 config 파일에 포함하지 않습니다. replicas, resources 등도 동일하게 Kustomize patch 파일에서 관리됩니다.

- SonarQube 프로젝트 설정 방법 작성
  - SonarQube에서 프론트엔드 프로젝트 생성
  - 프로젝트 키: `{SERVICE_NAME}-{환경}`
  - 언어: JavaScript/TypeScript
  - Quality Gate 설정:
    > **참고**: 프론트엔드는 초기 단계에서 테스트 커버리지 확보가 어려워 백엔드(80%)보다 완화된 70%를 적용합니다.
    ```
    Coverage: >= 70%
    Duplicated Lines: <= 3%
    Maintainability Rating: <= A
    Reliability Rating: <= A
    Security Rating: <= A
    Code Smells: <= 50
    Bugs: = 0
    Vulnerabilities: = 0
    ```

- 롤백 방법 작성
  - GitHub Actions에서 이전 버전으로 롤백:
    ```bash
    # 이전 워크플로우 실행으로 롤백
    1. GitHub > Actions > 성공한 이전 워크플로우 선택
    2. Re-run all jobs 클릭
    ```
  - 매니페스트 레포지토리를 이용한 롤백 (GitOps):
    ```bash
    # 매니페스트 레포에서 이전 커밋으로 되돌리기 (ArgoCD가 자동 감지하여 배포)
    cd {MANIFEST_REPO}
    git log --oneline -5   # 되돌릴 커밋 확인
    git revert HEAD --no-edit
    git push origin main
    ```
  - 이미지 태그 기반 롤백 (GitOps):
    ```bash
    # 매니페스트 레포에서 이전 안정 버전 이미지 태그로 업데이트 후 push (ArgoCD 자동 반영)
    cd {MANIFEST_REPO}/{FRONTEND_SERVICE}/kustomize/overlays/{환경}
    kustomize edit set image {IMG_REG}/{IMG_ORG}/{SERVICE_NAME}:{환경}-{이전태그}
    git add . && git commit -m "rollback: {SERVICE_NAME} to {이전태그}" && git push origin main
    ```

## 출력 형식

- 가이드: `deployment/cicd/actions-pipeline-guide.md`
- GitHub Actions 워크플로우: `.github/workflows/frontend-cicd.yaml`
- GitHub Actions 전용 Kustomize 매니페스트: `.github/kustomize/*`
- GitHub Actions 전용 환경별 설정 파일: `.github/config/*`

## 품질 기준

- [ ] CI/CD 분리 원칙 준수 (CI: 빌드·푸시·매니페스트 tag 업데이트, CD: ArgoCD 자동 배포)
- [ ] 시크릿 하드코딩 금지
- [ ] 환경별 Kustomize overlay 구성
- [ ] 매니페스트 레포지토리 업데이트 정상 동작 확인

## 주의사항

GitHub Actions CI 파이프라인 구축 작업을 누락 없이 진행하기 위한 체크리스트입니다.

### 사전 준비 체크리스트
- [ ] package.json에서 시스템명과 서비스명 확인 완료
- [ ] 실행정보 섹션에서 CLOUD, IMG_REG, IMG_ORG, NAMESPACE 확인 완료
- [ ] MANIFEST_REPO_URL, MANIFEST_SECRET_GIT_USERNAME, MANIFEST_SECRET_GIT_PASSWORD 확인 완료

### GitHub Actions 전용 Kustomize 구조 생성 체크리스트
- [ ] 디렉토리 구조 생성: `.github/kustomize/{base,overlays/{dev,staging,prod}}`
- [ ] 기존 k8s 매니페스트를 base로 복사 완료
- [ ] **리소스 누락 방지 검증 완료**:
  - [ ] `ls .github/kustomize/base/` 명령으로 모든 파일 확인
  - [ ] 필수 파일 존재 확인 (deployment.yaml, service.yaml, configmap.yaml, ingress.yaml 필수)
- [ ] Base kustomization.yaml 파일 생성 완료
  - [ ] 모든 리소스 파일 포함 확인
- [ ] **검증 명령어 실행 완료**:
  - [ ] `kubectl kustomize .github/kustomize/base/` 정상 실행 확인
  - [ ] 에러 메시지 없이 모든 리소스 출력 확인

### GitHub Actions 전용 환경별 Overlay 구성 체크리스트
#### 공통 체크 사항
- **base 매니페스트에 없는 항목을 추가하지 않았는지 체크**
- **base 매니페스트와 항목이 일치 하는지 체크**
- **⚠️ Kustomize patch 방법 변경**: `patchesStrategicMerge` → `patches` (target 명시)

#### DEV 환경
- [ ] `.github/kustomize/overlays/dev/kustomization.yaml` 생성 완료
- [ ] `.github/kustomize/overlays/dev/configmap-patch.yaml` 생성 완료 (개발 API 엔드포인트)
- [ ] `.github/kustomize/overlays/dev/ingress-patch.yaml` 생성 완료 (**Host 기본값은 base의 ingress.yaml과 동일**)
- [ ] `.github/kustomize/overlays/dev/deployment-patch.yaml` 생성 완료 (replicas=1, dev 리소스)

#### STAGING 환경
- [ ] `.github/kustomize/overlays/staging/kustomization.yaml` 생성 완료
- [ ] `.github/kustomize/overlays/staging/configmap-patch.yaml` 생성 완료 (스테이징 API 엔드포인트)
- [ ] `.github/kustomize/overlays/staging/ingress-patch.yaml` 생성 완료 (staging 도메인, HTTPS, SSL 인증서)
- [ ] `.github/kustomize/overlays/staging/deployment-patch.yaml` 생성 완료 (replicas=2, staging 리소스)

#### PROD 환경
- [ ] `.github/kustomize/overlays/prod/kustomization.yaml` 생성 완료
- [ ] `.github/kustomize/overlays/prod/configmap-patch.yaml` 생성 완료 (운영 API 엔드포인트)
- [ ] `.github/kustomize/overlays/prod/ingress-patch.yaml` 생성 완료 (prod 도메인, HTTPS, SSL 인증서)
- [ ] `.github/kustomize/overlays/prod/deployment-patch.yaml` 생성 완료 (replicas=3, prod 리소스)

### GitHub Actions 설정 및 스크립트 체크리스트
- [ ] GitHub Actions 워크플로우 파일 `.github/workflows/frontend-cicd.yaml` 생성 완료
- [ ] 워크플로우 주요 내용 확인
  - Build, SonarQube, Docker Build & Push, Update Frontend Manifest Repository 단계 포함
  - Node.js 버전 확인: `node-version: '{NODE_VERSION}'`
  - 변수 참조 문법 확인: `${{ needs.build.outputs.* }}` 사용
  - 서비스명이 실제 프로젝트 서비스명으로 치환되었는지 확인
  - **github.event.inputs.SKIP_SONARQUBE 기반 조건부 실행 확인**
  - **클라우드별 조건부 registry login 확인**: CLOUD 변수 기반 (AWS/Azure/GCP)
  - **플레이스홀더 사용 확인**: {IMG_REG}, {IMG_ORG}, {SERVICE_NAME} 등
- [ ] Repository Variables 설정 확인: CLOUD, REGISTRY, IMAGE_ORG
- [ ] Repository Secrets 설정 확인
  - AWS: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
  - Azure: ACR_USERNAME, ACR_PASSWORD, AZURE_CREDENTIALS
  - GCP: GCP_SA_KEY
  - 공통: GIT_USERNAME, GIT_PASSWORD (또는 [실행정보]의 MANIFEST_SECRET_GIT_* 이름), SONAR_TOKEN, SONAR_HOST_URL, DOCKERHUB_USERNAME, DOCKERHUB_PASSWORD
- [ ] 매니페스트 레포지토리 업데이트 job (update-manifest) 정상 동작 확인
- [ ] ArgoCD가 매니페스트 레포지토리 변경을 감지하여 자동 배포되는지 확인
