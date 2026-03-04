# 프론트엔드 Jenkins 파이프라인 작성 가이드

## 목적
Jenkins + Kustomize 기반 프론트엔드 CI 파이프라인을 구축한다. CI/CD 분리 구조로, CI는 빌드·푸시·매니페스트 레포지토리 image tag 업데이트까지 수행하고, CD는 ArgoCD가 매니페스트 레포지토리 변경을 감지하여 자동 배포한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| K8s 클러스터 정보 | `(런타임 결정)` | 배포 대상 |
| Jenkins 인증 정보 | `(런타임 결정)` | 파이프라인 설정 |
| 컨테이너 레지스트리 | `(런타임 결정)` | 이미지 푸시 대상 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 파이프라인 가이드 | `deployment/cicd/jenkins-pipeline-guide.md` |
| 환경별 설정 파일 | `deployment/cicd/config/*` |
| Kustomize 파일 | `deployment/cicd/kustomize/*` |
| Jenkins 스크립트 | `deployment/cicd/Jenkinsfile` (모노레포 시 `Jenkinsfile-frontend`) |

## 방법론

### 프롬프트 제공정보 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {CLOUD}: 클라우드 서비스 (AWS/Azure/GCP) — 레지스트리 로그인 분기에 사용
- {FRONTEND_SERVICE}: 프론트엔드 서비스명 (= {SERVICE_NAME}, package.json의 name 필드)
- {IMG_REG}: container 컨테이너 이미지 레지스트리 주소
- {IMG_ORG}: container IMG_ORG
- {JENKINS_CLOUD_NAME}: Jenkins에 설정한 k8s Cloud 이름
- {NAMESPACE}: 네임스페이스
- {JENKINS_GIT_CREDENTIALS}: 매니페스트 레포지토리 접근용 Jenkins Credential ID
- {MANIFEST_REPO_URL}: 매니페스트 레포지토리 URL

예시)
```
[실행정보]
- CLOUD: Azure
- FRONTEND_SERVICE: phonebill-front
- IMG_REG: docker.io
- IMG_ORG: phonebill
- JENKINS_CLOUD_NAME: k8s
- NAMESPACE: phonebill
- JENKINS_GIT_CREDENTIALS: github-credentials
- MANIFEST_REPO_URL: https://github.com/org/manifest-repo.git
```

### 사전 준비사항 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {CLOUD}: 클라우드 서비스 (AWS/Azure/GCP) — 레지스트리 로그인 분기에 사용
- {FRONTEND_SERVICE}: 프론트엔드 서비스명 (= {SERVICE_NAME}, package.json의 name 필드)
- {IMG_REG}: container 컨테이너 이미지 레지스트리 주소
- {IMG_ORG}: container IMG_ORG
- {JENKINS_CLOUD_NAME}: Jenkins에 설정한 k8s Cloud 이름
- {NAMESPACE}: 네임스페이스
- {JENKINS_GIT_CREDENTIALS}: 매니페스트 레포지토리 접근용 Jenkins Credential ID
- {MANIFEST_REPO_URL}: 매니페스트 레포지토리 URL

예시)
```
[실행정보]
- CLOUD: Azure
- FRONTEND_SERVICE: phonebill-front
- IMG_REG: docker.io
- IMG_ORG: phonebill
- JENKINS_CLOUD_NAME: k8s
- NAMESPACE: phonebill
- JENKINS_GIT_CREDENTIALS: github-credentials
- MANIFEST_REPO_URL: https://github.com/org/manifest-repo.git
```

### 서비스명 확인
서비스명은 package.json에서 확인.
- {SERVICE_NAME}: package.json의 "name" 필드

예시)
```json
{
  ...
  "name": "phonebill-front",
  ...
}
```

### Node.js 버전 확인
package.json에서 Node.js 버전 확인.
{NODE_VERSION}: "engines" 섹션에서 Node.js 버전 확인. 없으면 20 버전 사용.
```json
{
  "engines": {
    "node": "20.x"
  }
}
```

### Jenkins 서버 환경 구성 안내
- Jenkins 설치 및 필수 플러그인

Jenkins 필수 플러그인 목록:
```
- Kubernetes
- Pipeline Utility Steps
- Docker Pipeline
- GitHub
- SonarQube Scanner
```

- Jenkins Credentials 등록

  - Image Credentials
  ```
  # 레지스트리별 Username: Docker Hub → Docker Hub 사용자명, ACR → ACR 이름, ECR → AWS, GCR → _json_key
  # 상세 설정은 setup-cicd-tools.md의 Image Registry Credential 섹션 참조
  - Kind: Username with password
  - ID: imagereg-credentials
  - Username: {레지스트리 사용자명}
  - Password: {레지스트리 비밀번호}
  ```

  - Docker Hub Credentials (Rate Limit 해결용)
  ```
  - Kind: Username with password
  - ID: dockerhub-credentials
  - Username: {DOCKERHUB_USERNAME}
  - Password: {DOCKERHUB_PASSWORD}
  참고: Docker Hub 무료 계정 생성 (https://hub.docker.com)
  ```

  - SonarQube Token
  ```
  - Kind: Secret text
  - ID: sonarqube-token
  - Secret: {SonarQube토큰}
  ```

### ESLint 설정 파일 작성
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

### Kustomize 디렉토리 구조 생성
- 프로젝트 루트에 CI/CD 디렉토리 생성
  ```
  mkdir -p deployment/cicd/kustomize/{base,overlays/{dev,staging,prod}}
  mkdir -p deployment/cicd/kustomize/base
  mkdir -p deployment/cicd/{config,scripts}
  ```
- 기존 k8s 매니페스트를 base로 복사
  ```
  # 기존 deployment/k8s/* 파일들을 base로 복사
  cp deployment/k8s/* deployment/cicd/kustomize/base/

  # 네임스페이스 하드코딩 제거
  find deployment/cicd/kustomize/base -name "*.yaml" -exec sed -i 's/namespace: .*//' {} \;
  ```

### Base Kustomization 작성
`deployment/cicd/kustomize/base/kustomization.yaml` 파일 생성 방법 안내

**⚠️ 중요: 리소스 누락 방지 가이드**
1. **디렉토리별 파일 확인**: base 디렉토리의 모든 yaml 파일을 확인
2. **일관성 체크**: 모든 리소스가 동일한 파일 구조를 가지는지 확인
3. **누락 검증**: `ls deployment/cicd/kustomize/base/` 명령으로 실제 파일과 kustomization.yaml 리스트 비교
4. **명명 규칙 준수**: ConfigMap은 `configmap.yaml`, Service는 `service.yaml` 패턴 확인

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
ls deployment/cicd/kustomize/base/

# kustomization.yaml 유효성 검사
kubectl kustomize deployment/cicd/kustomize/base/
```

### 환경별 Patch 파일 생성
각 환경별로 필요한 patch 파일들을 생성합니다.
**중요원칙**:
- **base 매니페스트에 없는 항목은 추가 않함**
- **base 매니페스트와 항목이 일치해야 함**

**1. ConfigMap Patch 파일 생성**
`deployment/cicd/kustomize/overlays/{환경}/configmap-patch.yaml`

- base 매니페스트를 환경별로 복사
  ```
  cp deployment/cicd/kustomize/base/configmap.yaml deployment/cicd/kustomize/overlays/{환경}/configmap-patch.yaml
  ```

- 환경별 API 엔드포인트 설정
- dev: 개발 API 서버 주소, staging/prod: 운영 API 서버 주소

**2. Ingress Patch 파일 생성**
`deployment/cicd/kustomize/overlays/{환경}/ingress-patch.yaml`
- base의 ingress.yaml을 환경별로 오버라이드
- **⚠️ 중요**: 개발환경 Ingress Host의 기본값은 base의 ingress.yaml과 **정확히 동일하게** 함
- Staging/Prod 환경별 도메인 설정: {SERVICE_NAME}-{환경}.도메인 형식
- Staging/prod 환경은 HTTPS 강제 적용 및 SSL 인증서 설정
- staging/prod는 nginx.ingress.kubernetes.io/ssl-redirect: "true"
- dev는 nginx.ingress.kubernetes.io/ssl-redirect: "false"

**3. Deployment Patch 파일 생성** ⚠️ **중요**
`deployment/cicd/kustomize/overlays/{환경}/deployment-patch.yaml`

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

### 환경별 Overlay 작성
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

### 환경별 설정 파일 작성
`deployment/cicd/config/deploy_env_vars_{환경}` 파일 생성 방법
```bash
# {환경} Environment Configuration
namespace={NAMESPACE}
```

### Jenkinsfile 작성
`deployment/cicd/Jenkinsfile` 파일 생성 방법을 안내합니다.

주요 구성 요소:
- **Pod Template**: Node.js, Podman, Git 컨테이너
- **Build & Test**: Node.js 기반 빌드 및 단위 테스트
- **SonarQube Analysis**: 프론트엔드 코드 품질 분석 및 Quality Gate
- **Container Build & Push**: 30분 timeout 설정과 함께 환경별 이미지 태그로 빌드 및 푸시
- **Manifest Repository Update**: 매니페스트 레포지토리 image tag 업데이트 (ArgoCD GitOps)
- **Pod Cleanup**: 파이프라인 완료 시 에이전트 파드 자동 정리

**⚠️ 중요: Pod 자동 정리 설정**
에이전트 파드가 파이프라인 완료 시 즉시 정리되도록 다음 설정들이 적용됨:
- **podRetention: never()**: 파이프라인 완료 시 파드 즉시 삭제 (문법 주의: 문자열 'never' 아님)
- **idleMinutes: 1**: 유휴 시간 1분으로 설정하여 빠른 정리
- **terminationGracePeriodSeconds: 3**: 파드 종료 시 3초 내 강제 종료
- **restartPolicy: Never**: 파드 재시작 방지
- **try-catch-finally**: 예외 발생 시에도 정리 로직 실행 보장

**⚠️ 중요: 변수 참조 문법 및 충돌 해결**
Jenkins Groovy에서 bash shell로 변수 전달 시:
- **올바른 문법**: `${variable}` (Groovy 문자열 보간)
- **잘못된 문법**: `\${variable}` (bash 특수문자 이스케이프로 인한 "syntax error: bad substitution" 오류)

> **참고**: `git` 컨테이너(`alpine/git`)의 기본 쉘은 `/bin/sh`(ash)이므로 Bash 전용 문법(배열 등) 사용 불가. 프론트엔드는 단일 서비스이므로 루프가 불필요하지만, 쉘 스크립트 작성 시 POSIX 호환 문법을 사용하세요.

```groovy
def PIPELINE_ID = "${env.BUILD_NUMBER}"

def getImageTag() {
    def dateFormat = new java.text.SimpleDateFormat('yyyyMMddHHmmss')
    def currentDate = new Date()
    return dateFormat.format(currentDate)
}

podTemplate(
    cloud: '{JENKINS_CLOUD_NAME}',
    label: "${PIPELINE_ID}",
    serviceAccount: 'jenkins',
    slaveConnectTimeout: 300,
    idleMinutes: 1,
    activeDeadlineSeconds: 3600,
    podRetention: never(),  // 파드 자동 정리 옵션: never(), onFailure(), always(), default()
    yaml: '''
        spec:
          terminationGracePeriodSeconds: 3
          restartPolicy: Never
    ''',
    containers: [
        containerTemplate(
            name: 'node',
            image: 'node:{NODE_VERSION}-slim',
            ttyEnabled: true,
            command: 'cat',
            resourceRequestCpu: '400m',
            resourceRequestMemory: '1Gi',
            resourceLimitCpu: '2000m',
            resourceLimitMemory: '4Gi'
        ),
        containerTemplate(
            name: 'podman',
            image: "mgoltzsche/podman",
            ttyEnabled: true,
            command: 'cat',
            privileged: true,
            resourceRequestCpu: '400m',
            resourceRequestMemory: '2Gi',
            resourceLimitCpu: '2000m',
            resourceLimitMemory: '4Gi'
        ),
        containerTemplate(
            name: 'git',
            image: 'alpine/git:latest',
            command: 'cat',
            ttyEnabled: true,
            resourceRequestCpu: '100m',
            resourceRequestMemory: '256Mi',
            resourceLimitCpu: '300m',
            resourceLimitMemory: '512Mi'
        ),
        containerTemplate(
            name: 'sonar-scanner',
            image: 'sonarsource/sonar-scanner-cli:latest',
            command: 'cat',
            ttyEnabled: true,
            resourceRequestCpu: '200m',
            resourceRequestMemory: '512Mi',
            resourceLimitCpu: '1000m',
            resourceLimitMemory: '1Gi'
        )
    ],
    volumes: [
        emptyDirVolume(mountPath: '/opt/sonar-scanner/.sonar/cache', memory: false),
        emptyDirVolume(mountPath: '/root/.npm', memory: false)
    ]
) {
    node(PIPELINE_ID) {
        def props
        def imageTag = getImageTag()
        def environment = params.ENVIRONMENT ?: 'dev'
        def skipSonarQube = params.SKIP_SONARQUBE ?: 'true'
        def sonarScannerHome = '/opt/sonar-scanner'

        try {
            stage("Get Source") {
                checkout scm
                props = readProperties file: "deployment/cicd/config/deploy_env_vars_${environment}"
            }

            stage('Build & Test') {
                container('node') {
                    sh """
                        npm ci
                        npm run build
                        npm run lint
                    """
                }
            }

            stage('SonarQube Analysis & Quality Gate') {
                if (skipSonarQube == 'true') {
                    echo "⏭️ Skipping SonarQube Analysis (SKIP_SONARQUBE=${params.SKIP_SONARQUBE})"
                } else {
                    container('sonar-scanner') {
                        script {
                            try {
                                withSonarQubeEnv('SonarQube') {
                                    sh """
                                      timeout 300 ${sonarScannerHome}/bin/sonar-scanner \\
                                      -Dsonar.projectKey={SERVICE_NAME}-${environment} \\
                                      -Dsonar.projectName={SERVICE_NAME}-${environment} \\
                                      -Dsonar.sources=src \\
                                      -Dsonar.tests=src \\
                                      -Dsonar.test.inclusions=**/*.test.ts,**/*.test.tsx,**/*.spec.ts,**/*.spec.tsx \\
                                      -Dsonar.exclusions=node_modules/**,dist/**,build/**,coverage/**,**/*.config.js,**/*.config.ts,scripts/** \\
                                      -Dsonar.scm.disabled=true \\
                                      -Dsonar.sourceEncoding=UTF-8 \\
                                      -Dsonar.typescript.tsconfigPaths=tsconfig.json \\
                                      -Dsonar.javascript.lcov.reportPaths=coverage/lcov.info \\
                                      -Dsonar.javascript.node.maxspace=4096
                                    """
                                }

                                timeout(time: 5, unit: 'MINUTES') {
                                    def qg = waitForQualityGate()
                                    if (qg.status != 'OK') {
                                        echo "⚠️ Quality Gate failed: ${qg.status}, but continuing pipeline... (프론트엔드는 초기 단계에서 커버리지가 낮을 수 있어 경고만 출력)"
                                    }
                                }
                            } catch (Exception e) {
                                echo "⚠️ SonarQube analysis failed: ${e.getMessage()}, but continuing pipeline..."
                            }
                        }
                    }
                }
            }

            stage('Build & Push Images') {
                timeout(time: 30, unit: 'MINUTES') {
                    container('podman') {
                        withCredentials([
                            usernamePassword(
                                credentialsId: 'imagereg-credentials',
                                usernameVariable: 'IMG_USERNAME',
                                passwordVariable: 'IMG_PASSWORD'
                            ),
                            usernamePassword(
                                credentialsId: 'dockerhub-credentials',
                                usernameVariable: 'DOCKERHUB_USERNAME',
                                passwordVariable: 'DOCKERHUB_PASSWORD'
                            )
                        ]) {
                            // Docker Hub 로그인 (rate limit 해결)
                            sh "podman login docker.io --username \$DOCKERHUB_USERNAME --password \$DOCKERHUB_PASSWORD"

                            // 이미지 레지스트리 로그인 (클라우드별 조건 분기)
                            // [실행정보]의 CLOUD 값에 따라 해당하는 섹션만 사용
                            // --- DockerHub (CLOUD 무관, 레지스트리유형=DockerHub) ---
                            sh "podman login {IMG_REG} --username \$IMG_USERNAME --password \$IMG_PASSWORD"

                            // --- AWS ECR (CLOUD=AWS, 레지스트리유형=ECR) ---
                            // sh "aws ecr get-login-password --region {ECR_REGION} | podman login --username AWS --password-stdin {IMG_REG}"

                            // --- Azure ACR (CLOUD=Azure, 레지스트리유형=ACR) ---
                            // sh "podman login {IMG_REG} --username \$IMG_USERNAME --password \$IMG_PASSWORD"

                            // --- GCP Artifact Registry (CLOUD=GCP, 레지스트리유형=GCR) ---
                            // sh "gcloud auth configure-docker {GCR_REGION}-docker.pkg.dev --quiet"
                            // sh "gcloud auth print-access-token | podman login -u oauth2accesstoken --password-stdin {GCR_REGION}-docker.pkg.dev"

                            sh """
                                podman build \\
                                    -f deployment/container/Dockerfile-frontend \\
                                    --build-arg PROJECT_FOLDER="." \\
                                    --build-arg BUILD_FOLDER="deployment/container" \\
                                    -t {IMG_REG}/{IMG_ORG}/{SERVICE_NAME}:${environment}-${imageTag} .

                                podman push {IMG_REG}/{IMG_ORG}/{SERVICE_NAME}:${environment}-${imageTag}
                            """
                        }
                    }
                }
            }

            stage('Update Manifest Repository') {
                container('git') {
                    withCredentials([usernamePassword(
                        credentialsId: '{JENKINS_GIT_CREDENTIALS}',
                        usernameVariable: 'GIT_USERNAME',
                        passwordVariable: 'GIT_TOKEN'
                    )]) {
                        sh """
                            # 매니페스트 레포지토리 클론
                            REPO_URL=\$(echo "{MANIFEST_REPO_URL}" | sed 's|https://||')
                            git clone https://\${GIT_USERNAME}:\${GIT_TOKEN}@\${REPO_URL} manifest-repo
                            cd manifest-repo

                            # Kustomize 설치
                            curl -sL "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | sh
                            mv kustomize /usr/local/bin/ 2>/dev/null || export PATH=\$PATH:\$(pwd)

                            # 매니페스트 업데이트 (kustomize 방식)
                            cd {FRONTEND_SERVICE}/kustomize/overlays/${environment}

                            echo "Updating {SERVICE_NAME} image tag..."
                            kustomize edit set image {IMG_REG}/{IMG_ORG}/{SERVICE_NAME}={IMG_REG}/{IMG_ORG}/{SERVICE_NAME}:${environment}-${imageTag}

                            # Git 설정 및 푸시
                            cd ../../../..
                            git config user.name "Jenkins CI"
                            git config user.email "jenkins@example.com"
                            git add .
                            git commit -m "Update {SERVICE_NAME} ${environment} image to ${environment}-${imageTag}"
                            git push origin main

                            echo "매니페스트 업데이트 완료. ArgoCD가 자동으로 배포합니다."
                        """
                    }
                }
            }

            // 파이프라인 완료 로그 (Scripted Pipeline 방식)
            stage('Pipeline Complete') {
                echo "🧹 Pipeline completed. Pod cleanup handled by Jenkins Kubernetes Plugin."

                // 성공/실패 여부 로깅
                if (currentBuild.result == null || currentBuild.result == 'SUCCESS') {
                    echo "✅ Pipeline completed successfully!"
                } else {
                    echo "❌ Pipeline failed with result: ${currentBuild.result}"
                }
            }

        } catch (Exception e) {
            currentBuild.result = 'FAILURE'
            echo "❌ Pipeline failed with exception: ${e.getMessage()}"
            throw e
        } finally {
            echo "🧹 Cleaning up resources and preparing for pod termination..."
            echo "Pod will be terminated in 3 seconds due to terminationGracePeriodSeconds: 3"
        }
    }
}
```

### Jenkins Pipeline Job 생성 안내

- Pipeline Job 설정
1. Jenkins 웹 UI에서 **New Item > Pipeline** 선택
2. **Pipeline script from SCM** 설정:
   ```
   SCM: Git
   Repository URL: {Git저장소URL}
   Branch: main (또는 develop)
   Script Path: deployment/cicd/Jenkinsfile
   ```

- Pipeline Parameters 설정
```
ENVIRONMENT: Choice Parameter
- Choices: dev, staging, prod
- Default: dev
- Description: 배포 환경 선택

IMAGE_TAG: String Parameter
- Default: latest
- Description: 컨테이너 이미지 태그 (선택사항)

SKIP_SONARQUBE: String Parameter
- Default: true
- Description: SonarQube 코드 분석 스킵 여부 (true/false)
```

### SonarQube 프로젝트 설정 안내

- SonarQube 프로젝트 생성
  - SonarQube에서 프론트엔드 프로젝트 생성
  - 프로젝트 키: `{SERVICE_NAME}-{환경}`
  - 언어: JavaScript/TypeScript

- Quality Gate 설정
  > **참고**: 프론트엔드는 초기 단계에서 테스트 커버리지 확보가 어려워 백엔드(80%)보다 완화된 70%를 적용합니다. Quality Gate 실패 시에도 경고만 출력하고 파이프라인을 계속 진행합니다.
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

### 배포 실행 방법
- Jenkins 파이프라인 실행:
  ```
  1. Jenkins > {프로젝트명} > Build with Parameters
  2. ENVIRONMENT 선택 (dev/staging/prod)
  3. IMAGE_TAG 입력 (선택사항)
  4. Build 클릭
  ```
- 배포 상태 확인:
  ```
  kubectl get pods -n {NAMESPACE}
  kubectl get services -n {NAMESPACE}
  kubectl get ingress -n {NAMESPACE}
  ```

### 롤백 방법
- 이전 버전으로 롤백:
  ```bash
  # 특정 버전으로 롤백
  # 매니페스트 레포지토리에서 이전 커밋으로 되돌리기 (ArgoCD가 자동 감지하여 배포)
  cd {MANIFEST_REPO}
  git log --oneline -5   # 되돌릴 커밋 확인
  git revert HEAD --no-edit
  git push origin main
  ```
- 이미지 태그 기반 롤백:
  ```bash
  # 매니페스트 레포에서 이전 안정 버전 이미지 태그로 업데이트 후 push (ArgoCD 자동 반영)
  cd {MANIFEST_REPO}/{FRONTEND_SERVICE}/kustomize/overlays/{환경}
  kustomize edit set image {IMG_REG}/{IMG_ORG}/{SERVICE_NAME}:{환경}-{이전태그}
  git add . && git commit -m "rollback: {SERVICE_NAME} to {이전태그}" && git push origin main
  ```

## 출력 형식

### 📋 사전 준비 체크리스트
- [ ] package.json에서 프로젝트명 확인 완료
- [ ] 실행정보 섹션에서 CLOUD, IMG_REG, IMG_ORG, NAMESPACE 확인 완료
- [ ] **ESLint 설정 파일 `.eslintrc.cjs` 생성 완료**
- [ ] **package.json lint 스크립트 max-warnings 20으로 수정 완료**

### 📂 Kustomize 구조 생성 체크리스트
- [ ] 디렉토리 구조 생성: `deployment/cicd/kustomize/{base,overlays/{dev,staging,prod}}`
- [ ] 기존 k8s 매니페스트를 base로 복사 완료
- [ ] 네임스페이스 하드코딩 제거 완료
- [ ] **리소스 누락 방지 검증 완료**:
  - [ ] `ls deployment/cicd/kustomize/base/` 명령으로 모든 파일 확인
  - [ ] 필수 파일 존재 확인 (deployment.yaml, service.yaml, configmap.yaml, ingress.yaml 필수)
- [ ] Base kustomization.yaml 파일 생성 완료
  - [ ] 모든 리소스 파일 포함 확인
- [ ] **검증 명령어 실행 완료**:
  - [ ] `kubectl kustomize deployment/cicd/kustomize/base/` 정상 실행 확인
  - [ ] 에러 메시지 없이 모든 리소스 출력 확인

### 🔧 환경별 Overlay 구성 체크리스트

#### 공통 체크 사항
- **base 매니페스트에 없는 항목을 추가하지 않았는지 체크**
- **base 매니페스트와 항목이 일치 하는지 체크**
- **⚠️ Kustomize patch 방법**: `patches` (target 명시)

#### DEV 환경
- [ ] `overlays/dev/kustomization.yaml` 생성 완료
- [ ] `overlays/dev/configmap-patch.yaml` 생성 완료 (개발 API 엔드포인트)
- [ ] `overlays/dev/ingress-patch.yaml` 생성 완료 (**Host 기본값은 base의 ingress.yaml과 동일**)
- [ ] `overlays/dev/deployment-patch.yaml` 생성 완료 (replicas=1, dev 리소스)

#### STAGING 환경
- [ ] `overlays/staging/kustomization.yaml` 생성 완료
- [ ] `overlays/staging/configmap-patch.yaml` 생성 완료 (스테이징 API 엔드포인트)
- [ ] `overlays/staging/ingress-patch.yaml` 생성 완료 (staging 도메인, HTTPS)
- [ ] `overlays/staging/deployment-patch.yaml` 생성 완료 (replicas=2, staging 리소스)

#### PROD 환경
- [ ] `overlays/prod/kustomization.yaml` 생성 완료
- [ ] `overlays/prod/configmap-patch.yaml` 생성 완료 (운영 API 엔드포인트)
- [ ] `overlays/prod/ingress-patch.yaml` 생성 완료 (prod 도메인, HTTPS, SSL 인증서)
- [ ] `overlays/prod/deployment-patch.yaml` 생성 완료 (replicas=3, prod 리소스)

### ⚙️ 설정 및 스크립트 체크리스트
- [ ] 환경별 설정 파일 생성: `config/deploy_env_vars_{dev,staging,prod}`
- [ ] `Jenkinsfile` 생성 완료
- [ ] `Jenkinsfile` 주요 내용 확인
  - 변수 참조 문법 확인: `${variable}` 사용, `\${variable}` 사용 금지
  - 서비스명이 실제 {SERVICE_NAME}으로 치환되었는지 확인
  - **파드 자동 정리 설정 확인**: podRetention: never(), idleMinutes: 1, terminationGracePeriodSeconds: 3
  - **try-catch-finally 블록 포함**: 예외 상황에서도 정리 로직 실행 보장
  - **매니페스트 레포지토리 업데이트 확인**: git container로 manifest repo clone 및 image tag 업데이트 후 push
- [ ] Dockerfile 및 Nginx 설정 파일 생성 완료

## 품질 기준
- [ ] 시크릿 하드코딩 금지
- [ ] Podman 기반 빌드 구성
- [ ] 환경별 Kustomize overlay 구성

## 주의사항
- dev 환경 Ingress Host는 base의 ingress.yaml과 정확히 동일하게 설정 (변경 금지)
- Kustomize patch 방법: `patchesStrategicMerge` 대신 `patches` (target 명시) 사용
- Jenkins Groovy에서 bash 변수 전달 시 `\${variable}` 사용 금지, `${variable}` 사용
- ES 모듈 프로젝트에서 ESLint 설정 파일은 `.eslintrc.cjs` 확장자 사용
- podRetention: never() 는 문자열 'never'가 아닌 함수 호출 형태로 작성
