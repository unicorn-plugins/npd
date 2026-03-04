# 프론트엔드 Jenkins 파이프라인 작성 가이드

## 목적
Jenkins + Kustomize 기반 프론트엔드 CI 파이프라인을 구축한다. CI/CD 분리 구조로, CI는 빌드·푸시·매니페스트 레포지토리 image tag 업데이트까지 수행하고, CD는 ArgoCD가 매니페스트 레포지토리 변경을 감지하여 자동 배포한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| Jenkins 인증 정보 | `(런타임 결정)` | 파이프라인 설정 |
| 컨테이너 레지스트리 | `(런타임 결정)` | 이미지 푸시 대상 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 파이프라인 결과서 | `deployment/cicd/deploy-jenkins-cicd-front-result.md` |
| Jenkins 스크립트 | `deployment/cicd/Jenkinsfile-frontend` |

## 방법론

### 프롬프트 제공정보 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {CLOUD}: 클라우드 서비스 (AWS/Azure/GCP) — 레지스트리 로그인 분기에 사용
- {FRONTEND_SERVICE}: 프론트엔드 서비스명 (= {SERVICE_NAME}, package.json의 name 필드)
- {IMG_REG}: container 컨테이너 이미지 레지스트리 주소
- {IMG_ORG}: container IMG_ORG
- {JENKINS_CLOUD_NAME}: Jenkins에 설정한 k8s Cloud 이름
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

### Jenkinsfile 작성
`deployment/cicd/Jenkinsfile-frontend` 파일 생성 방법을 안내합니다.

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
        def imageTag = getImageTag()
        def environment = params.ENVIRONMENT ?: 'dev'
        def skipSonarQube = params.SKIP_SONARQUBE ?: 'true'
        def sonarScannerHome = '/opt/sonar-scanner'

        try {
            stage("Get Source") {
                checkout scm
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

### 결과서 작성
`deployment/cicd/deploy-jenkins-cicd-front-result.md` 파일 생성.
아래 템플릿에 실제 치환값을 채워 작성.

```markdown
# {FRONTEND_SERVICE} 프론트엔드 Jenkins CI 파이프라인 결과서

## 실행 환경 정보
| 항목 | 값 |
|------|-----|
| CLOUD | {값} |
| IMG_REG | {값} |
| IMG_ORG | {값} |
| JENKINS_CLOUD_NAME | {값} |
| MANIFEST_REPO_URL | {값} |
| JENKINS_GIT_CREDENTIALS | {값} |

## 서비스 정보
| 항목 | 값 |
|------|-----|
| FRONTEND_SERVICE | {값} |
| SERVICE_NAME | {값} |
| NODE_VERSION | {값} |

## 생성 파일
| 파일 | 설명 |
|------|------|
| `deployment/cicd/Jenkinsfile-frontend` | Jenkins 파이프라인 스크립트 |

## 파이프라인 구성
Get Source → Build & Test → SonarQube Analysis → Build & Push Images → Update Manifest Repository → Pipeline Complete

## 변수 치환 내역
| 플레이스홀더 | 치환값 |
|-------------|--------|
| {FRONTEND_SERVICE} | {값} |
| {SERVICE_NAME} | {값} |
| {NODE_VERSION} | {값} |
| {IMG_REG} | {값} |
| {IMG_ORG} | {값} |
| {JENKINS_CLOUD_NAME} | {값} |
| {JENKINS_GIT_CREDENTIALS} | {값} |
| {MANIFEST_REPO_URL} | {값} |
```

## 출력 형식

### 📋 사전 준비 체크리스트
- [ ] package.json에서 프로젝트명 확인 완료
- [ ] 실행정보 섹션에서 CLOUD, IMG_REG, IMG_ORG 확인 완료
### ⚙️ 설정 및 스크립트 체크리스트
- [ ] `Jenkinsfile-frontend` 생성 완료
- [ ] `Jenkinsfile-frontend` 주요 내용 확인
  - 변수 참조 문법 확인: `${variable}` 사용, `\${variable}` 사용 금지
  - 서비스명이 실제 {SERVICE_NAME}으로 치환되었는지 확인
  - **파드 자동 정리 설정 확인**: podRetention: never(), idleMinutes: 1, terminationGracePeriodSeconds: 3
  - **try-catch-finally 블록 포함**: 예외 상황에서도 정리 로직 실행 보장
  - **매니페스트 레포지토리 업데이트 확인**: git container로 manifest repo clone 및 image tag 업데이트 후 push
- [ ] Dockerfile 및 Nginx 설정 파일 생성 완료

## 품질 기준
- [ ] 시크릿 하드코딩 금지
- [ ] Podman 기반 빌드 구성

## 주의사항
- Jenkins Groovy에서 bash 변수 전달 시 `\${variable}` 사용 금지, `${variable}` 사용
- podRetention: never() 는 문자열 'never'가 아닌 함수 호출 형태로 작성
