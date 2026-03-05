# 백엔드 GitHub Actions 파이프라인 작성 가이드

## 목적
GitHub Actions 기반 CI 파이프라인을 구축한다. CI/CD 분리 구조로, CI는 빌드·푸시·매니페스트 레포지토리 image tag 업데이트까지 수행하고, CD는 ArgoCD가 매니페스트 레포지토리 변경을 감지하여 자동 배포한다. AWS EKS(ECR), Azure AKS(ACR), GCP GKE(Artifact Registry) 전 클라우드를 지원한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 컨테이너 레지스트리 | `(런타임 결정)` | 이미지 푸시 대상 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| CI/CD 파이프라인 결과서 | `deployment/cicd/deploy-actions-cicd-back-result.md` |
| GitHub Actions 워크플로우 | `.github/workflows/backend-cicd.yaml` |

## 방법론

- 사전 준비사항 확인
  프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
  - {SYSTEM_NAME}: 시스템명 (rootProject.name)
  - {CLOUD}: 클라우드 서비스 (AWS/Azure/GCP)
  - {IMG_REG}: 컨테이너 이미지 레지스트리 주소
  - {MANIFEST_REPO_URL}: 매니페스트 레포지토리 URL
  - {MANIFEST_SECRET_GIT_USERNAME}: 매니페스트 레포지토리 접근용 GitHub Secret (Username)
  - {MANIFEST_SECRET_GIT_PASSWORD}: 매니페스트 레포지토리 접근용 GitHub Secret (Password/Token)

  클라우드별 추가 변수:
  - AWS: {ECR_ACCOUNT}, {ECR_REGION}, {EKS_CLUSTER}
  - Azure: {ACR_NAME}, {RESOURCE_GROUP}, {AKS_CLUSTER}
  - GCP: {GCR_REGION}, {GCR_PROJECT}, {GCR_REPO}, {GKE_CLUSTER}, {GKE_ZONE}

- 시스템명과 서비스명 확인
  settings.gradle에서 확인.
  - {SYSTEM_NAME}: rootProject.name
  - {SERVICE_NAMES}: include 'common'하위의 include문 뒤의 값임

  예시) include 'common'하위의 서비스명들.
  ```
  rootProject.name = 'phonebill'

  include 'common'
  include 'api-gateway'
  include 'user-service'
  include 'order-service'
  include 'payment-service'
  ```

- 이미지명 확인
  각 서비스의 `deployment/k8s/{서비스명}/` Deployment YAML에서 컨테이너 이미지명 추출.
  - Deployment YAML의 `image:` 필드에서 태그(`:latest` 등)를 제거하여 `{IMG_NAME}` 확보
  - CI 파이프라인에서 `{IMG_NAME}` 뒤에 새 태그(`${environment}-${imageTag}`)를 붙여 빌드·푸시
  - 매니페스트 레포지토리도 동일한 새 태그로 업데이트

  예시) 각 서비스별 Deployment YAML:

  | 서비스명 | Deployment YAML `image:` 필드 | {IMG_NAME} (태그 제거) |
  |---------|-------------------------------|----------------------|
  | {서비스명1} | `docker.io/phonebill/{서비스명1}:latest` | `docker.io/phonebill/{서비스명1}` |
  | {서비스명2} | `docker.io/phonebill/{서비스명2}:latest` | `docker.io/phonebill/{서비스명2}` |

  → 빌드 태그 예: `docker.io/phonebill/{서비스명1}:dev-20260305143022`

- JDK버전 확인
  루트 build.gradle에서 JDK 버전 확인.
  {JDK_VERSION}: 'java' 섹션에서 JDK 버전 확인. 아래 예에서는 21임.
  ```
  java {
      toolchain {
          languageVersion = JavaLanguageVersion.of(21)
      }
  }
  ```

- GitHub Actions 워크플로우 작성
  `.github/workflows/backend-cicd.yaml` 파일 생성 방법을 안내합니다.

  > **⚠️ 주의**: 아래 YAML 코드 블록은 마크다운 리스트 내에 있어 2칸 들여쓰기가 포함되어 있습니다. 파일로 생성할 때 **앞의 2칸 들여쓰기를 제거**하세요. `name:`이 컬럼 0에서 시작해야 합니다.

  주요 구성 요소:
  - **Build & Test**: Gradle 기반 빌드 및 단위 테스트
  - **SonarQube Analysis**: 코드 품질 분석 및 Quality Gate
  - **Container Build & Push**: 환경별 이미지 태그로 빌드 및 푸시
  - **Update Manifest Repository: 매니페스트 레포지토리 image tag 업데이트 (ArgoCD GitOps)**

  ```yaml
  name: Backend Services CI/CD

  on:
    push:
      branches: [ main, develop ]
      paths:
        - '{서비스명1}/**'
        - '{서비스명2}/**'
        - '{서비스명3}/**'
        - '{서비스명N}/**'
        - 'common/**'
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
        SERVICE:
          description: 'Target service (all = 전체 배포)'
          required: false
          default: 'all'
          type: choice
          options:
            - all
            - '{서비스명1}'
            - '{서비스명2}'
            - '{서비스명3}'
            - '{서비스명N}'

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

        - name: Set up JDK {버전}
          uses: actions/setup-java@v4
          with:
            java-version: '{JDK버전}'
            distribution: 'temurin'
            cache: 'gradle'

        - name: Determine environment
          id: determine_env
          run: |
            # Use input parameter or default to 'dev'
            ENVIRONMENT="${{ github.event.inputs.ENVIRONMENT || vars.ENVIRONMENT || 'dev' }}"
            echo "environment=$ENVIRONMENT" >> $GITHUB_OUTPUT

        - name: Grant execute permission for gradlew
          run: chmod +x gradlew

        - name: Build with Gradle
          run: |
            ./gradlew build -x test

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
              echo "Skipping SonarQube Analysis (SKIP_SONARQUBE=$SKIP_SONARQUBE)"
              exit 0
            fi

            # Define services array
            services=({SERVICE_NAME1} {SERVICE_NAME2} {SERVICE_NAME3} {SERVICE_NAMEN})

            # Run tests, coverage reports, and SonarQube analysis for each service
            for service in "${services[@]}"; do
              ./gradlew :$service:test :$service:jacocoTestReport :$service:sonar \
                -Dsonar.projectKey={SYSTEM_NAME}-$service-${{ steps.determine_env.outputs.environment }} \
                -Dsonar.projectName={SYSTEM_NAME}-$service-${{ steps.determine_env.outputs.environment }} \
                -Dsonar.host.url=$SONAR_HOST_URL \
                -Dsonar.token=$SONAR_TOKEN \
                -Dsonar.java.binaries=build/classes/java/main \
                -Dsonar.coverage.jacoco.xmlReportPaths=build/reports/jacoco/test/jacocoTestReport.xml \
                -Dsonar.exclusions=**/config/**,**/entity/**,**/dto/**,**/*Application.class,**/exception/**
            done

        - name: Upload build artifacts
          uses: actions/upload-artifact@v4
          with:
            name: app-builds
            path: |
              {SERVICE_NAME1}/build/libs/*.jar
              {SERVICE_NAME2}/build/libs/*.jar
              {SERVICE_NAME3}/build/libs/*.jar
              {SERVICE_NAMEN}/build/libs/*.jar

        - name: Set outputs
          id: set_outputs
          run: |
            # Generate timestamp for image tag
            IMAGE_TAG=$(date +%Y%m%d%H%M%S)
            echo "image_tag=$IMAGE_TAG" >> $GITHUB_OUTPUT
            echo "environment=${{ steps.determine_env.outputs.environment }}" >> $GITHUB_OUTPUT

    release:
      name: Build and Push Docker Images
      needs: build
      runs-on: ubuntu-latest

      steps:
        - name: Check out code
          uses: actions/checkout@v4

        - name: Download build artifacts
          uses: actions/download-artifact@v4
          with:
            name: app-builds

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
          if: ${{ env.CLOUD == 'AWS' }}
          uses: aws-actions/configure-aws-credentials@v4
          with:
            aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
            aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
            aws-region: ${{ vars.ECR_REGION }}   # GitHub Repository Variable: ECR_REGION

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
            gcloud auth configure-docker ${{ vars.GCR_REGION }}-docker.pkg.dev  # GitHub Repository Variable: GCR_REGION

        - name: Build and push Docker images
          run: |
            # 서비스명과 이미지명 병렬 배열 (K8s Deployment YAML에서 추출한 이미지명)
            services=({서비스명1} {서비스명2} {서비스명3} {서비스명N})
            img_names=({이미지명1} {이미지명2} {이미지명3} {이미지명N})
            TARGET_SERVICE="${{ github.event.inputs.SERVICE || 'all' }}"

            # Build and push each service image
            for i in "${!services[@]}"; do
              service="${services[$i]}"
              img_name="${img_names[$i]}"

              # all이 아니면 선택한 서비스만 처리
              if [[ "$TARGET_SERVICE" != "all" && "$service" != "$TARGET_SERVICE" ]]; then
                continue
              fi

              echo "Building and pushing $service ($img_name)..."
              docker build \
                --platform linux/amd64 \
                --build-arg BUILD_LIB_DIR="$service/build/libs" \
                --build-arg ARTIFACTORY_FILE="$service.jar" \
                -f deployment/container/Dockerfile-backend \
                -t $img_name:${{ needs.build.outputs.environment }}-${{ needs.build.outputs.image_tag }} .

              docker push $img_name:${{ needs.build.outputs.environment }}-${{ needs.build.outputs.image_tag }}
            done

    update-manifest:
      name: Update Manifest Repository
      needs: [build, release]
      runs-on: ubuntu-latest

      steps:
      - name: Set image tag environment variable
        run: |
          echo "IMAGE_TAG=${{ needs.build.outputs.image_tag }}" >> $GITHUB_ENV
          echo "ENVIRONMENT=${{ needs.build.outputs.environment }}" >> $GITHUB_ENV

      - name: Update Manifest Repository
        # ⚠️ 필수 치환 안내:
        #   아래 secrets.GIT_USERNAME, secrets.GIT_PASSWORD는 기본 Secret 이름입니다.
        #   [실행정보]의 MANIFEST_SECRET_GIT_USERNAME / MANIFEST_SECRET_GIT_PASSWORD 값이
        #   다른 이름이면 해당 이름으로 치환하세요.
        #   예) MANIFEST_SECRET_GIT_USERNAME=MY_GIT_USER이면
        #       ${{ secrets.GIT_USERNAME }} → ${{ secrets.MY_GIT_USER }}로 변경
        run: |
          # 매니페스트 레포지토리 클론
          REPO_URL=$(echo "{MANIFEST_REPO_URL}" | sed 's|https://||')
          git clone https://${{ secrets.GIT_USERNAME }}:${{ secrets.GIT_PASSWORD }}@${REPO_URL} manifest-repo
          cd manifest-repo

          curl -sL "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.6.0/kustomize_v5.6.0_linux_amd64.tar.gz" | tar xz
          sudo mv kustomize /usr/local/bin/

          # 매니페스트 업데이트
          cd {SYSTEM_NAME}/kustomize/overlays/${{ env.ENVIRONMENT }}

          # 각 서비스별 이미지 태그 업데이트 (K8s Deployment YAML에서 추출한 이미지명)
          services=({서비스명1} {서비스명2} {서비스명3} {서비스명N})
          img_names=({이미지명1} {이미지명2} {이미지명3} {이미지명N})
          TARGET_SERVICE="${{ github.event.inputs.SERVICE || 'all' }}"

          for i in "${!services[@]}"; do
            service="${services[$i]}"
            img_name="${img_names[$i]}"
            if [[ "$TARGET_SERVICE" != "all" && "$service" != "$TARGET_SERVICE" ]]; then
              continue
            fi
            kustomize edit set image $img_name=$img_name:${{ env.ENVIRONMENT }}-${{ env.IMAGE_TAG }}
          done

          # Git 설정 및 푸시
          cd ../../../..
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add .
          git commit -m "Update {SYSTEM_NAME} ${{ env.ENVIRONMENT }} images to ${{ env.ENVIRONMENT }}-${{ env.IMAGE_TAG }}"
          git push origin main

          echo "매니페스트 업데이트 완료. ArgoCD가 자동으로 배포합니다."

  ```

### 결과서 작성
`deployment/cicd/deploy-actions-cicd-back-result.md` 파일 생성.
아래 템플릿에 실제 치환값을 채워 작성.

```markdown
# {SYSTEM_NAME} 백엔드 GitHub Actions CI 파이프라인 결과서

## 실행 환경 정보
| 항목 | 값 |
|------|-----|
| CLOUD | {값} |
| IMG_REG | {값} |
| IMG_NAME (서비스별) | {값} |
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
| SYSTEM_NAME | {값} |
| SERVICE_NAMES | {값} |
| JDK_VERSION | {값} |

## 생성 파일
| 파일 | 설명 |
|------|------|
| `.github/workflows/backend-cicd.yaml` | GitHub Actions 워크플로우 |

## 파이프라인 구성
Build and Test → SonarQube Analysis → Build and Push Docker Images → Update Manifest Repository

## 변수 치환 내역
| 플레이스홀더 | 치환값 |
|-------------|--------|
| {SYSTEM_NAME} | {값} |
| {SERVICE_NAMES} | {값} |
| {JDK_VERSION} | {값} |
| {IMG_REG} | {값} |
| {IMG_NAME} (서비스별) | {값} |
| {MANIFEST_REPO_URL} | {값} |
| {MANIFEST_SECRET_GIT_USERNAME} | {값} |
| {MANIFEST_SECRET_GIT_PASSWORD} | {값} |
```

## 출력 형식

- 결과서: `deployment/cicd/deploy-actions-cicd-back-result.md`
- GitHub Actions 워크플로우: `.github/workflows/backend-cicd.yaml`

## 품질 기준

- [ ] CI/CD 분리 원칙 준수 (CI: 빌드·푸시·매니페스트 tag 업데이트, CD: ArgoCD 자동 배포)
- [ ] 시크릿 하드코딩 금지
- [ ] 매니페스트 레포지토리 업데이트 정상 동작 확인

## 주의사항

GitHub Actions CI 파이프라인 구축 작업을 누락 없이 진행하기 위한 체크리스트입니다.

### 사전 준비 체크리스트
- [ ] settings.gradle에서 시스템명과 서비스명 확인 완료
- [ ] 실행정보 섹션에서 CLOUD, IMG_REG 확인 완료
- [ ] K8s Deployment YAML에서 이미지명(IMG_NAME) 확인 완료
- [ ] MANIFEST_REPO_URL, MANIFEST_SECRET_GIT_USERNAME, MANIFEST_SECRET_GIT_PASSWORD 확인 완료

### GitHub Actions 설정 및 스크립트 체크리스트
- [ ] GitHub Actions 워크플로우 파일 `.github/workflows/backend-cicd.yaml` 생성 완료
- [ ] 워크플로우 주요 내용 확인
  - Build, SonarQube, Docker Build & Push, Update Manifest Repository 단계 포함
  - JDK 버전 확인: `java-version: '{JDK버전}'`
  - 변수 참조 문법 확인: `${{ needs.build.outputs.* }}` 사용
  - 모든 서비스명이 실제 프로젝트 서비스명으로 치환되었는지 확인
  - **환경 변수 SKIP_SONARQUBE 처리 확인**: 기본값 'true', 조건부 실행
  - **클라우드별 조건부 registry login 확인**: CLOUD 변수 기반 (AWS/Azure/GCP)
  - **플레이스홀더 사용 확인**: {IMG_REG}, {IMG_NAME}, {SYSTEM_NAME}, {SERVICE_NAMES} 등
- [ ] 매니페스트 레포지토리 업데이트 job (update-manifest) 정상 동작 확인
- [ ] ArgoCD가 매니페스트 레포지토리 변경을 감지하여 자동 배포되는지 확인
