# 프론트엔드 GitHub Actions 파이프라인 작성 가이드

## 목적
GitHub Actions 기반 CI 파이프라인을 구축한다. CI/CD 분리 구조로, CI는 빌드·푸시·매니페스트 레포지토리 image tag 업데이트까지 수행하고, CD는 ArgoCD가 매니페스트 레포지토리 변경을 감지하여 자동 배포한다. AWS EKS(ECR), Azure AKS(ACR), GCP GKE(Artifact Registry) 전 클라우드를 지원한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 컨테이너 레지스트리 | `(런타임 결정)` | 이미지 푸시 대상 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| CI/CD 파이프라인 결과서 | `deployment/cicd/deploy-actions-cicd-front-result.md` |
| GitHub Actions 워크플로우 | `.github/workflows/frontend-cicd.yaml` |

## 방법론

- 사전 준비사항 확인
  프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
  - {FRONTEND_FRAMEWORK}: 프론트엔드 프레임워크 (React / Vue / Flutter)
  - {FRONTEND_SERVICE}: 프론트엔드 서비스명 (= {SERVICE_NAME})
  - {CLOUD}: 클라우드 서비스 (AWS/Azure/GCP)
  - {IMG_REG}: 컨테이너 이미지 레지스트리 주소
  - {MANIFEST_REPO_URL}: 매니페스트 레포지토리 URL
  - {MANIFEST_SECRET_GIT_USERNAME}: 매니페스트 레포지토리 접근용 GitHub Secret (Username)
  - {MANIFEST_SECRET_GIT_PASSWORD}: 매니페스트 레포지토리 접근용 GitHub Secret (Password/Token)

  클라우드별 추가 변수:
  - AWS: {ECR_ACCOUNT}, {ECR_REGION}, {EKS_CLUSTER}
  - Azure: {ACR_NAME}, {RESOURCE_GROUP}, {AKS_CLUSTER}
  - GCP: {GCR_REGION}, {GCR_PROJECT}, {GCR_REPO}, {GKE_CLUSTER}, {GKE_ZONE}

- 서비스명 확인
  프레임워크에 따라 서비스명 확인 파일이 다름.

  **React / Vue**
  - {SERVICE_NAME}: `package.json`의 `"name"` 필드

  ```json
  {
    "name": "phonebill-front"
  }
  ```

  **Flutter**
  - {SERVICE_NAME}: `pubspec.yaml`의 `name` 필드

  ```yaml
  name: phonebill-front
  ```

- SDK 버전 확인
  프레임워크에 따라 빌드에 사용할 SDK 버전 확인.

  **React / Vue (Node.js)**
  - {NODE_VERSION}: `package.json`의 `"engines"` 섹션에서 확인. 없으면 `20` 사용.

  ```json
  {
    "engines": {
      "node": "20.x"
    }
  }
  ```

  **Flutter**
  - {FLUTTER_VERSION}: `pubspec.yaml`의 `environment.flutter` 또는 프로젝트에서 사용 중인 Flutter SDK 버전 확인.
    없으면 `stable` 사용.

  ```yaml
  environment:
    flutter: ">=3.24.0"
  ```

- 이미지명 확인
  `deployment/k8s/{SERVICE_NAME}/` Deployment YAML에서 컨테이너 이미지명 추출.
  - Deployment YAML의 `image:` 필드에서 태그(`:latest` 등)를 제거하여 `{IMG_NAME}` 확보
  - CI 파이프라인에서 `{IMG_NAME}` 뒤에 새 태그(`${environment}-${imageTag}`)를 붙여 빌드·푸시
  - 매니페스트 레포지토리도 동일한 새 태그로 업데이트

  예시) `deployment/k8s/phonebill-front/` Deployment YAML:
  ```yaml
  image: docker.io/phonebill/phonebill-front:latest
  ```
  → {IMG_NAME} = `docker.io/phonebill/phonebill-front` (`:latest` 태그 제거)
  → 빌드 태그: `docker.io/phonebill/phonebill-front:dev-20260305143022`

- GitHub Actions 워크플로우 작성
  `.github/workflows/frontend-cicd.yaml` 파일 생성 방법을 안내합니다.

  > **⚠️ 주의**: 아래 YAML 코드 블록은 마크다운 리스트 내에 있어 2칸 들여쓰기가 포함되어 있습니다. 파일로 생성할 때 **앞의 2칸 들여쓰기를 제거**하세요. `name:`이 컬럼 0에서 시작해야 합니다.

  주요 구성 요소:
  - **Build & Test**: 프레임워크별 빌드 및 검증 (React/Vue: npm, Flutter: flutter build web)
  - **SonarQube Analysis**: 프론트엔드 코드 품질 분석 및 Quality Gate (JS/TS 또는 Dart)
  - **Container Build & Push**: 환경별 이미지 태그로 빌드 및 푸시
  - **Update Manifest Repository**: 매니페스트 레포지토리 image tag 업데이트 (ArgoCD GitOps)

  ```yaml
  name: Frontend CI/CD

  on:
    push:
      branches: [ main, develop ]
      paths:
        # --- React / Vue ---
        - 'src/**'
        - 'public/**'
        - 'package*.json'
        - 'tsconfig*.json'
        - 'vite.config.ts'
        - 'index.html'
        # --- Flutter ---
        # - 'lib/**'
        # - 'web/**'
        # - 'pubspec.*'
        # - 'analysis_options.yaml'
        # --- 공통 ---
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

        # --- React / Vue (Node.js) ---
        - name: Set up Node.js {NODE_VERSION}
          uses: actions/setup-node@v4
          with:
            node-version: '{NODE_VERSION}'
            cache: 'npm'
        # --- Flutter ---
        # - name: Set up Flutter {FLUTTER_VERSION}
        #   uses: subosito/flutter-action@v2
        #   with:
        #     flutter-version: '{FLUTTER_VERSION}'
        #     cache: true

        - name: Determine environment
          id: determine_env
          run: |
            ENVIRONMENT="${{ github.event.inputs.ENVIRONMENT || vars.ENVIRONMENT || 'dev' }}"
            echo "environment=$ENVIRONMENT" >> $GITHUB_OUTPUT

        # --- React / Vue (Node.js) ---
        - name: Install dependencies
          run: npm ci

        - name: Build and Test
          run: |
            # npx로 직접 실행하여 prebuild 훅(generate-runtime-env.sh 등) 스킵
            # CI에서는 K8s ConfigMap이 runtime-env.js를 덮어쓰므로 생성 불필요
            NODE_OPTIONS="--max-old-space-size=3072" npx next build
            npm run lint || true
        # --- Flutter ---
        # - name: Install dependencies
        #   run: flutter pub get
        #
        # - name: Build and Test
        #   run: |
        #     flutter build web --release
        #     flutter analyze || true

        - name: Add SonarQube host entry
          run: echo "${{ secrets.SONAR_HOST_IP }} mysonar.io" | sudo tee -a /etc/hosts

        - name: SonarQube Analysis & Quality Gate
          continue-on-error: true
          env:
            GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
            SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
            SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
          run: |
            # Check if SonarQube should be skipped
            SKIP_SONARQUBE="${{ github.event.inputs.SKIP_SONARQUBE || 'false' }}"

            if [[ "$SKIP_SONARQUBE" == "true" ]]; then
              echo "⏭️ Skipping SonarQube Analysis (SKIP_SONARQUBE=$SKIP_SONARQUBE)"
              exit 0
            fi

            # --- React / Vue (JS/TS) ---
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
              -Dsonar.javascript.node.maxspace=2048 \
              -Dsonar.host.url=$SONAR_HOST_URL \
              -Dsonar.token=$SONAR_TOKEN
            # --- Flutter (Dart) ---
            # npm install -g sonarqube-scanner
            # sonar-scanner \
            #   -Dsonar.projectKey={SERVICE_NAME}-${{ steps.determine_env.outputs.environment }} \
            #   -Dsonar.projectName={SERVICE_NAME}-${{ steps.determine_env.outputs.environment }} \
            #   -Dsonar.sources=lib \
            #   -Dsonar.tests=test \
            #   -Dsonar.test.inclusions=**/*_test.dart \
            #   -Dsonar.exclusions=build/**,.dart_tool/**,.packages/** \
            #   -Dsonar.scm.disabled=true \
            #   -Dsonar.sourceEncoding=UTF-8 \
            #   -Dsonar.host.url=$SONAR_HOST_URL \
            #   -Dsonar.token=$SONAR_TOKEN

        # --- React / Vue ---
        - name: Upload build artifacts
          uses: actions/upload-artifact@v4
          with:
            name: dist
            path: dist/
        # --- Flutter ---
        # - name: Upload build artifacts
        #   uses: actions/upload-artifact@v4
        #   with:
        #     name: dist
        #     path: build/web/

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

        # --- React / Vue ---
        - name: Download build artifacts
          uses: actions/download-artifact@v4
          with:
            name: dist
            path: dist/
        # --- Flutter ---
        # - name: Download build artifacts
        #   uses: actions/download-artifact@v4
        #   with:
        #     name: dist
        #     path: build/web/

        - name: Set environment variables from build job
          run: |
            echo "REGISTRY=${{ vars.REGISTRY }}" >> $GITHUB_ENV
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
          if: ${{ contains(env.REGISTRY, 'amazonaws.com') }}
          uses: aws-actions/configure-aws-credentials@v4
          with:
            aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
            aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
            aws-region: ${{ vars.ECR_REGION }}

        - name: Login to Amazon ECR
          if: ${{ contains(env.REGISTRY, 'amazonaws.com') }}
          run: |
            aws ecr get-login-password --region ${{ vars.ECR_REGION }} | docker login --username AWS --password-stdin ${{ env.REGISTRY }}

        # === Azure ACR ===
        # (CLOUD == Azure일 때 사용)
        - name: Login to Azure Container Registry
          if: ${{ contains(env.REGISTRY, 'azurecr.io') }}
          uses: docker/login-action@v3
          with:
            registry: ${{ env.REGISTRY }}
            username: ${{ secrets.ACR_USERNAME }}
            password: ${{ secrets.ACR_PASSWORD }}

        # === GCP Artifact Registry ===
        # (CLOUD == GCP일 때 사용)
        - name: Authenticate to Google Cloud
          if: ${{ contains(env.REGISTRY, 'pkg.dev') }}
          uses: google-github-actions/auth@v2
          with:
            credentials_json: ${{ secrets.GCP_SA_KEY }}

        - name: Login to Google Artifact Registry
          if: ${{ contains(env.REGISTRY, 'pkg.dev') }}
          run: |
            gcloud auth configure-docker ${{ vars.GCR_REGION }}-docker.pkg.dev

        - name: Build and push Docker image
          run: |
            docker build \
              --platform linux/amd64 \
              -f deployment/container/Dockerfile-frontend \
              --build-arg PROJECT_FOLDER="{프론트엔드-디렉토리}" \
              --build-arg BUILD_FOLDER="deployment/container" \
              -t {IMG_NAME}:${{ needs.build.outputs.environment }}-${{ needs.build.outputs.image_tag }} .

            docker push {IMG_NAME}:${{ needs.build.outputs.environment }}-${{ needs.build.outputs.image_tag }}

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
          # x-access-token 방식으로 PAT 인증 (특수문자 이슈 방지)
          MANIFEST_REPO_PATH=$(echo "{MANIFEST_REPO_URL}" | sed 's|https://github.com/||')
          git clone https://x-access-token:${{ secrets.GIT_PASSWORD }}@github.com/${MANIFEST_REPO_PATH} manifest-repo
          cd manifest-repo

          curl -sL "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.6.0/kustomize_v5.6.0_linux_amd64.tar.gz" | tar xz
          sudo mv kustomize /usr/local/bin/

          cd {FRONTEND_SERVICE}/kustomize/overlays/${{ env.ENVIRONMENT }}
          kustomize edit set image {IMG_NAME}={IMG_NAME}:${{ env.ENVIRONMENT }}-${{ env.IMAGE_TAG }}

          cd ../../../..
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add .
          git commit -m "Update {SERVICE_NAME} ${{ env.ENVIRONMENT }} image to ${{ env.ENVIRONMENT }}-${{ env.IMAGE_TAG }}"
          git push origin main

          echo "매니페스트 업데이트 완료. ArgoCD가 자동으로 배포합니다."

  ```

### 결과서 작성
`deployment/cicd/deploy-actions-cicd-front-result.md` 파일 생성.
아래 템플릿에 실제 치환값을 채워 작성.

```markdown
# {FRONTEND_SERVICE} 프론트엔드 GitHub Actions CI 파이프라인 결과서

## 실행 환경 정보
| 항목 | 값 |
|------|-----|
| CLOUD | {값} |
| IMG_REG | {값} |
| IMG_NAME | {값} |
| MANIFEST_REPO_URL | {값} |
| MANIFEST_SECRET_GIT_USERNAME | {값} |
| MANIFEST_SECRET_GIT_PASSWORD | {값} |

## 클라우드별 추가 정보
(해당 클라우드 섹션만 기재)

**AWS:**
| 항목 | 값 |
|------|-----|
| ECR_ACCOUNT | {값} |
| ECR_REGION | {값} |

**Azure:**
| 항목 | 값 |
|------|-----|
| ACR_NAME | {값} |
| RESOURCE_GROUP | {값} |

**GCP:**
| 항목 | 값 |
|------|-----|
| GCR_REGION | {값} |
| GCR_PROJECT | {값} |
| GCR_REPO | {값} |

## 서비스 정보
| 항목 | 값 |
|------|-----|
| FRONTEND_FRAMEWORK | {React / Vue / Flutter} |
| FRONTEND_SERVICE | {값} |
| SERVICE_NAME | {값} |
| NODE_VERSION 또는 FLUTTER_VERSION | {값} |

## 생성 파일
| 파일 | 설명 |
|------|------|
| `.github/workflows/frontend-cicd.yaml` | GitHub Actions 워크플로우 |

## 파이프라인 구성
Build and Test → SonarQube Analysis → Build and Push Docker Image → Update Manifest Repository

## 변수 치환 내역
| 플레이스홀더 | 치환값 |
|-------------|--------|
| {FRONTEND_FRAMEWORK} | {값} |
| {FRONTEND_SERVICE} | {값} |
| {SERVICE_NAME} | {값} |
| {NODE_VERSION} 또는 {FLUTTER_VERSION} | {값} |
| {IMG_REG} | {값} |
| {IMG_NAME} | {값} |
| {MANIFEST_REPO_URL} | {값} |
| {MANIFEST_SECRET_GIT_USERNAME} | {값} |
| {MANIFEST_SECRET_GIT_PASSWORD} | {값} |
```

## 출력 형식

- 결과서: `deployment/cicd/deploy-actions-cicd-front-result.md`
- GitHub Actions 워크플로우: `.github/workflows/frontend-cicd.yaml`

## 품질 기준

- [ ] CI/CD 분리 원칙 준수 (CI: 빌드·푸시·매니페스트 tag 업데이트, CD: ArgoCD 자동 배포)
- [ ] 시크릿 하드코딩 금지
- [ ] 매니페스트 레포지토리 업데이트 정상 동작 확인

## 주의사항

GitHub Actions CI 파이프라인 구축 작업을 누락 없이 진행하기 위한 체크리스트입니다.

### 사전 준비 체크리스트
- [ ] 프레임워크 확인 완료 (React / Vue / Flutter)
- [ ] 서비스명 확인 완료 (React/Vue: package.json, Flutter: pubspec.yaml)
- [ ] 실행정보 섹션에서 CLOUD, IMG_REG 확인 완료
- [ ] K8s Deployment YAML에서 이미지명(IMG_NAME) 확인 완료
- [ ] MANIFEST_REPO_URL, MANIFEST_SECRET_GIT_USERNAME, MANIFEST_SECRET_GIT_PASSWORD 확인 완료

### GitHub Actions 설정 및 스크립트 체크리스트
- [ ] GitHub Actions 워크플로우 파일 `.github/workflows/frontend-cicd.yaml` 생성 완료
- [ ] 워크플로우 주요 내용 확인
  - 프레임워크에 맞는 SDK 설정 활성화 (React/Vue: `actions/setup-node`, Flutter: `subosito/flutter-action`)
  - 프레임워크에 맞는 Build & Test, SonarQube, artifact 블록 활성화, 나머지 주석 처리
  - Build, SonarQube, Docker Build & Push, Update Frontend Manifest Repository 단계 포함
  - 변수 참조 문법 확인: `${{ needs.build.outputs.* }}` 사용
  - 서비스명이 실제 프로젝트 서비스명으로 치환되었는지 확인
  - **github.event.inputs.SKIP_SONARQUBE 기반 조건부 실행 확인**
  - **클라우드별 조건부 registry login 확인**: CLOUD 변수 기반 (AWS/Azure/GCP)
  - **플레이스홀더 사용 확인**: {IMG_REG}, {IMG_NAME}, {SERVICE_NAME} 등
- [ ] 매니페스트 레포지토리 업데이트 job (update-manifest) 정상 동작 확인
- [ ] ArgoCD가 매니페스트 레포지토리 변경을 감지하여 자동 배포되는지 확인
