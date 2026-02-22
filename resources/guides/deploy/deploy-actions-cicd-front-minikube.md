# 프론트엔드 GitHub Actions 파이프라인 작성 가이드 (Minikube/Generic K8s)

## 목적
GitHub Actions + Kustomize 기반 CI/CD 파이프라인 구축 가이드 작성. Docker Hub를 이미지 레지스트리로 사용. SSH 터널링을 통한 Minikube 클러스터 배포. 환경별(dev/staging/prod) 매니페스트 관리 및 자동 배포 구현. SonarQube 코드 품질 분석과 Quality Gate 포함. Node.js 기반 빌드 및 컨테이너 이미지 생성.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| K8s/Minikube 클러스터 | `(런타임 결정)` | SSH 터널링 배포 대상 |
| Docker Hub 정보 | `(런타임 결정)` | 이미지 푸시 대상 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| CI/CD 파이프라인 가이드 | `deployment/cicd/actions-pipeline-guide.md` |
| GitHub Actions 워크플로우 | `.github/workflows/frontend-cicd.yaml` |
| GitHub Actions 전용 Kustomize 매니페스트 | `.github/kustomize/*` |

## 방법론

- 사전 준비사항 확인
  프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
  - {SYSTEM_NAME}: 시스템명 (phonebill)
  - {IMG_REG}: 이미지 레지스트리 (docker.io)
  - {IMG_ORG}: 이미지 Organization (Docker Hub 사용자명)
  - {NAMESPACE}: Namespace명
  - {VM_IP}: Minikube가 설치된 VM의 Public IP
  - {VM_USER}: VM 접속 사용자명
  - {MINIKUBE_IP}: Minikube 클러스터 IP (기본값: 192.168.49.2)
  예시)
  ```
  [실행정보]
  - SYSTEM_NAME: phonebill
  - IMG_REG: docker.io
  - IMG_ORG: hiondal
  - NAMESPACE: phonebill
  - VM_IP: 52.231.227.173
  - VM_USER: azureuser
  - MINIKUBE_IP: 192.168.49.2
  ```

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
    ```
    Repository Settings > Secrets and variables > Actions > Repository secrets에 등록
    ```

    - Docker Hub 인증정보
      Docker Hub 패스워드 작성 방법 안내
      - DockerHub(https://hub.docker.com)에 로그인
      - 우측 상단 프로필 아이콘 클릭 후 Account Settings를 선택
      - 좌측메뉴에서 'Personal Access Tokens' 클릭하여 생성
      ```
      DOCKERHUB_USERNAME: {Docker Hub 사용자명}
      DOCKERHUB_PASSWORD: {Docker Hub Access Token}
      ```

    - VM SSH 접속 정보 (Minikube 배포용)
      ```
      VM_IP: {VM의 Public IP 주소}
      VM_USER: {VM 접속 사용자명}
      VM_SSH_KEY: {VM 접속용 SSH 개인키 내용 전체}
      ```
      **VM_SSH_KEY 작성 방법:**
      ```bash
      # 로컬에서 SSH 개인키 내용 확인
      cat ~/.ssh/id_rsa
      # 또는
      cat ~/.ssh/{your-key-name}.pem

      # 출력된 내용 전체를 복사하여 Secret에 등록
      # -----BEGIN OPENSSH PRIVATE KEY----- 부터
      # -----END OPENSSH PRIVATE KEY----- 까지 전체
      ```

    - KUBECONFIG 설정
      Minikube 클러스터의 kubeconfig 파일 내용을 등록
      ```
      KUBECONFIG: {kubeconfig 파일 내용 전체}
      ```
      **KUBECONFIG 작성 방법:**
      ```bash
      # Local에서 kubeconfig 내용 확인
      kubectl config view --minify --flatten

      # 출력된 내용 전체를 복사하여 Secret에 등록
      # (base64 인코딩 없이 원본 그대로 등록)
      ```

    - SonarQube URL과 인증 토큰 (선택사항)
      SONAR_HOST_URL 구하는 방법과 SONAR_TOKEN 작성법 안내.
      SONAR_HOST_URL: 아래 명령 수행 후 http://{External IP}를 지정.
      k get svc -n sonarqube
      예) http://20.249.187.69

      SONAR_TOKEN 값은 아래와 같이 작성
      - SonarQube 로그인 후 우측 상단 'Administrator' > My Account 클릭
      - Security 탭 선택 후 토큰 생성

      ```
      SONAR_TOKEN: {SonarQube토큰}
      SONAR_HOST_URL: {SonarQube서버URL}
      ```

  - GitHub Repository Variables 설정
    ```
    # Workflow 제어 변수
    Repository Settings > Secrets and variables > Actions > Variables > Repository variables에 등록

    ENVIRONMENT: dev (기본값: dev/staging/prod)
    SKIP_SONARQUBE: true (기본값: true/false)
    ```

    **사용 방법:**
    - **자동 실행**: Push/PR 시 Variables에 설정된 값 사용
    - **수동 실행**: Actions 탭 > "Frontend CI/CD (Generic K8s)" > "Run workflow" 버튼 클릭
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
  npm install --save-dev eslint-plugin-react
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
    mkdir -p .github/scripts
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

  metadata:
    name: {SERVICE_NAME}-base

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
    - base에서 `host: {SERVICE_NAME}.{VM_IP}.nip.io` 이면
    - dev에서도 `host: {SERVICE_NAME}.{VM_IP}.nip.io` 로 동일하게 설정
    - **절대** `{SERVICE_NAME}-dev.xxx` 처럼 변경하지 말 것
  - Staging/Prod 환경별 도메인 설정: {SERVICE_NAME}-{환경}.도메인 형식

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

  주요 구성 요소:
  - **Build & Test**: Node.js 기반 빌드 및 단위 테스트, ESLint 검사
  - **SonarQube Analysis**: 프론트엔드 코드 품질 분석 및 Quality Gate (vars.SKIP_SONARQUBE로 제어)
  - **Container Build & Push**: Docker Hub에 이미지 빌드 및 푸시
  - **SSH Tunnel & Deploy**: SSH 터널링을 통한 Minikube 클러스터 배포

  ```yaml
  name: Frontend CI/CD (Generic K8s)

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

  env:
    IMG_REG: {IMG_REG}
    IMG_ORG: {IMG_ORG}
    IMAGE_NAME: {SERVICE_NAME}
    NAMESPACE: {NAMESPACE}

    # SSH 터널링용
    MINIKUBE_IP: "{MINIKUBE_IP}"

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
          uses: actions/setup-node@v3
          with:
            node-version: '{NODE_VERSION}'
            cache: 'npm'

        - name: Determine environment
          id: determine_env
          run: |
            ENVIRONMENT="${{ vars.ENVIRONMENT || 'dev' }}"
            echo "environment=$ENVIRONMENT" >> $GITHUB_OUTPUT

        - name: Install dependencies
          run: npm ci

        - name: Build and Test
          run: |
            npm run build
            npm run lint

        - name: SonarQube Analysis & Quality Gate
          if: ${{ vars.SKIP_SONARQUBE != 'true' }}
          env:
            GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
            SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
            SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
          run: |
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

        - name: Set up Docker Buildx
          uses: docker/setup-buildx-action@v3

        - name: Login to Docker Hub
          uses: docker/login-action@v3
          with:
            username: ${{ secrets.DOCKERHUB_USERNAME }}
            password: ${{ secrets.DOCKERHUB_PASSWORD }}

        - name: Build and push Docker image
          uses: docker/build-push-action@v5
          with:
            context: .
            file: deployment/container/Dockerfile-frontend
            push: true
            tags: |
              ${{ env.IMG_REG }}/${{ env.IMG_ORG }}/${{ env.IMAGE_NAME }}:${{ needs.build.outputs.environment }}-${{ needs.build.outputs.image_tag }}
              ${{ env.IMG_REG }}/${{ env.IMG_ORG }}/${{ env.IMAGE_NAME }}:${{ needs.build.outputs.environment }}-latest
            build-args: |
              PROJECT_FOLDER=.
              BUILD_FOLDER=deployment/container
              EXPORT_PORT=8080

    deploy:
      name: Deploy to Kubernetes
      needs: [build, release]
      runs-on: ubuntu-latest

      steps:
        - name: Check out code
          uses: actions/checkout@v4

        - name: Set environment variables
          run: |
            echo "IMAGE_TAG=${{ needs.build.outputs.image_tag }}" >> $GITHUB_ENV
            echo "ENVIRONMENT=${{ needs.build.outputs.environment }}" >> $GITHUB_ENV

        - name: Setup SSH key
          run: |
            mkdir -p ~/.ssh
            echo "${{ secrets.VM_SSH_KEY }}" > ~/.ssh/vm_key
            chmod 600 ~/.ssh/vm_key
            ssh-keyscan -H ${{ secrets.VM_IP }} >> ~/.ssh/known_hosts 2>/dev/null || true

        - name: Create SSH tunnel to Minikube
          run: |
            ssh -i ~/.ssh/vm_key \
                -o StrictHostKeyChecking=no \
                -o ServerAliveInterval=60 \
                -L 8443:${{ env.MINIKUBE_IP }}:8443 \
                ${{ secrets.VM_USER }}@${{ secrets.VM_IP }} -N &

            sleep 5
            echo "✅ SSH tunnel established"

        - name: Setup kubectl
          uses: azure/setup-kubectl@v3

        - name: Configure kubectl via KUBECONFIG
          run: |
            mkdir -p $HOME/.kube
            echo "${{ secrets.KUBECONFIG }}" > $HOME/.kube/config
            chmod 600 $HOME/.kube/config

            # server 주소를 localhost:8443으로 변경 (SSH 터널 통해 접근)
            sed -i 's|server:.*|server: https://127.0.0.1:8443|g' $HOME/.kube/config

        - name: Verify cluster connection
          run: |
            kubectl cluster-info
            kubectl get nodes

        - name: Create namespace
          run: |
            kubectl create namespace ${{ env.NAMESPACE }} --dry-run=client -o yaml | kubectl apply -f -

        - name: Create image pull secret
          run: |
            kubectl create secret docker-registry dockerhub-secret \
              --docker-server=${{ env.IMG_REG }} \
              --docker-username=${{ secrets.DOCKERHUB_USERNAME }} \
              --docker-password=${{ secrets.DOCKERHUB_PASSWORD }} \
              --namespace=${{ env.NAMESPACE }} \
              --dry-run=client -o yaml | kubectl apply -f -

        - name: Install Kustomize
          run: |
            curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
            sudo mv kustomize /usr/local/bin/

        - name: Update Kustomize images and deploy
          run: |
            cd .github/kustomize/overlays/${{ env.ENVIRONMENT }}

            kustomize edit set image \
              ${{ env.IMG_REG }}/${{ env.IMG_ORG }}/${{ env.IMAGE_NAME }}:${{ env.ENVIRONMENT }}-${{ env.IMAGE_TAG }}

            kubectl apply -k .

        - name: Wait for deployments to be ready
          run: |
            echo "Waiting for deployments to be ready..."
            kubectl -n ${{ env.NAMESPACE }} wait --for=condition=available deployment/${{ env.IMAGE_NAME }} --timeout=300s

        - name: Show deployment status
          run: |
            kubectl -n ${{ env.NAMESPACE }} get pods -o wide
            kubectl -n ${{ env.NAMESPACE }} get svc

        - name: Cleanup SSH tunnel
          if: always()
          run: |
            pkill -f "ssh.*8443" || true

  ```

- SonarQube 프로젝트 설정 방법 작성
  - SonarQube에서 프론트엔드 프로젝트 생성
  - 프로젝트 키: `{SERVICE_NAME}-{환경}`
  - 언어: JavaScript/TypeScript
  - Quality Gate 설정:
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
  - kubectl을 이용한 롤백:
    ```bash
    # 특정 버전으로 롤백
    kubectl rollout undo deployment/{SERVICE_NAME} -n {NAMESPACE} --to-revision=2

    # 롤백 상태 확인
    kubectl rollout status deployment/{SERVICE_NAME} -n {NAMESPACE}
    ```
  - 수동 스크립트를 이용한 롤백:
    ```bash
    # 이전 안정 버전 이미지 태그로 배포
    ./.github/scripts/deploy-actions-frontend.sh {환경} {이전태그}
    ```

## 출력 형식

- 가이드: `deployment/cicd/actions-pipeline-guide.md`
- GitHub Actions 워크플로우: `.github/workflows/frontend-cicd.yaml`
- GitHub Actions 전용 Kustomize 매니페스트: `.github/kustomize/*`

## 품질 기준

- [ ] SSH 터널링 설정 포함
- [ ] 시크릿 하드코딩 금지

## 주의사항

GitHub Actions CI/CD 파이프라인 구축 작업을 누락 없이 진행하기 위한 체크리스트입니다.

### 사전 준비 체크리스트
- [ ] package.json에서 시스템명과 서비스명 확인 완료
- [ ] 실행정보 섹션에서 Docker Hub 사용자명, VM IP, Namespace 확인 완료

### GitHub Secrets 설정 체크리스트
- [ ] DOCKERHUB_USERNAME: Docker Hub 사용자명
- [ ] DOCKERHUB_PASSWORD: Docker Hub Access Token
- [ ] VM_IP: VM Public IP 주소
- [ ] VM_USER: VM 접속 사용자명
- [ ] VM_SSH_KEY: VM SSH 개인키 전체 내용
- [ ] KUBECONFIG: kubeconfig 파일 내용 (base64 인코딩 없이)
- [ ] SONAR_TOKEN: SonarQube 토큰 (선택사항)
- [ ] SONAR_HOST_URL: SonarQube 서버 URL (선택사항)

### GitHub Variables 설정 체크리스트
- [ ] ENVIRONMENT: dev (기본값)
- [ ] SKIP_SONARQUBE: true (기본값)

### GitHub Actions 전용 Kustomize 구조 생성 체크리스트
- [ ] 디렉토리 구조 생성: `.github/kustomize/{base,overlays/{dev,staging,prod}}`
- [ ] 기존 k8s 매니페스트를 base로 복사 완료
- [ ] **리소스 누락 방지 검증 완료**:
  - [ ] `ls .github/kustomize/base/` 명령으로 모든 파일 확인
  - [ ] 필수 파일 존재 확인 (deployment.yaml, service.yaml, configmap.yaml, ingress.yaml 필수)
- [ ] Base kustomization.yaml 파일 생성 완료
  - [ ] 모든 리소스 파일 포함 확인
  - [ ] 이미지 경로가 {IMG_REG}/{IMG_ORG}/{SERVICE_NAME} 형식인지 확인
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
- [ ] `.github/kustomize/overlays/staging/ingress-patch.yaml` 생성 완료 (staging 도메인)
- [ ] `.github/kustomize/overlays/staging/deployment-patch.yaml` 생성 완료 (replicas=2, staging 리소스)

#### PROD 환경
- [ ] `.github/kustomize/overlays/prod/kustomization.yaml` 생성 완료
- [ ] `.github/kustomize/overlays/prod/configmap-patch.yaml` 생성 완료 (운영 API 엔드포인트)
- [ ] `.github/kustomize/overlays/prod/ingress-patch.yaml` 생성 완료 (prod 도메인)
- [ ] `.github/kustomize/overlays/prod/deployment-patch.yaml` 생성 완료 (replicas=3, prod 리소스)

### GitHub Actions 설정 및 스크립트 체크리스트
- [ ] GitHub Actions 워크플로우 파일 `.github/workflows/frontend-cicd.yaml` 생성 완료
- [ ] 워크플로우 주요 내용 확인
  - Build, SonarQube, Docker Build & Push, SSH Tunnel, Deploy 단계 포함
  - Node.js 버전 확인: `node-version: '{NODE_VERSION}'`
  - 변수 참조 문법 확인: `${{ needs.build.outputs.* }}` 사용
  - 서비스명이 실제 프로젝트 서비스명으로 치환되었는지 확인
  - **vars.ENVIRONMENT, vars.SKIP_SONARQUBE 사용 확인**
  - **SSH 터널링 및 KUBECONFIG 설정 확인**
  - **Docker Hub pull secret 생성 단계 확인**

- [ ] 수동 배포 스크립트 `.github/scripts/deploy-actions-frontend.sh` 생성 완료
- [ ] 스크립트 실행 권한 설정 완료 (`chmod +x .github/scripts/*.sh`)
