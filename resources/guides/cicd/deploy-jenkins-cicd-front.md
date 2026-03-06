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
| Jenkins 스크립트 | `deployment/cicd/Jenkinsfile-frontend` |

## 방법론

### 프롬프트 제공정보 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {CLOUD}: 클라우드 서비스 (AWS/Azure/GCP) — 레지스트리 로그인 분기에 사용
- {FRONTEND_FRAMEWORK}: 프론트엔드 프레임워크 (React / Vue / Flutter)
- {FRONTEND_SERVICE}: 프론트엔드 서비스명 (= {SERVICE_NAME})
- {IMG_REG}: container 컨테이너 이미지 레지스트리 주소
- {JENKINS_CLOUD_NAME}: Jenkins에 설정한 k8s Cloud 이름
- {JENKINS_GIT_CREDENTIALS}: 매니페스트 레포지토리 접근용 Jenkins Credential ID
- {MANIFEST_REPO_URL}: 매니페스트 레포지토리 URL

예시)
```
[실행정보]
- CLOUD: Azure
- FRONTEND_FRAMEWORK: React
- FRONTEND_SERVICE: phonebill-front
- IMG_REG: docker.io
- JENKINS_CLOUD_NAME: k8s
- JENKINS_GIT_CREDENTIALS: github-credentials
- MANIFEST_REPO_URL: https://github.com/org/manifest-repo.git
```

### 서비스명 확인
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

### SDK 버전 확인
프레임워크에 따라 빌드 컨테이너 이미지 태그에 사용할 SDK 버전 확인.

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

### 이미지명 확인
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

### Jenkinsfile 작성
`deployment/cicd/Jenkinsfile-frontend` 파일 생성 방법을 안내합니다.

주요 구성 요소:
- **Pod Template**: 빌드 컨테이너(Node.js 또는 Flutter), Podman(또는 AKS/GKE 환경에서는 Kaniko), Git 컨테이너
- **Build & Test**: 프레임워크별 빌드 및 검증 (React/Vue: npm, Flutter: flutter build web)
- **SonarQube Analysis**: 프론트엔드 코드 품질 분석 및 Quality Gate (JS/TS 또는 Dart)
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

**Jenkinsfile 템플릿**
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
          containers:
          - name: kaniko
            resources:
              requests:
                ephemeral-storage: "5Gi"
              limits:
                ephemeral-storage: "20Gi"
          - name: node
            resources:
              requests:
                ephemeral-storage: "2Gi"
              limits:
                ephemeral-storage: "10Gi"
    ''',
    containers: [
        // --- React / Vue (Node.js 기반) ---
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
        // --- Flutter Web ---
        // containerTemplate(
        //     name: 'flutter',
        //     image: 'ghcr.io/cirruslabs/flutter:{FLUTTER_VERSION}',
        //     ttyEnabled: true,
        //     command: 'cat',
        //     resourceRequestCpu: '400m',
        //     resourceRequestMemory: '1Gi',
        //     resourceLimitCpu: '2000m',
        //     resourceLimitMemory: '4Gi'
        // ),
        // --- 기본 (EKS 등) ---
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
        // --- AKS/GKE 환경 (privileged 컨테이너 차단 시) ---
        // AKS/GKE에서 privileged: true를 차단하므로 Kaniko 사용
        // containerTemplate(
        //     name: 'kaniko',
        //     image: 'gcr.io/kaniko-project/executor:debug',
        //     ttyEnabled: true,
        //     command: '/busybox/cat',
        //     resourceRequestCpu: '400m',
        //     resourceRequestMemory: '2Gi',
        //     resourceLimitCpu: '2000m',
        //     resourceLimitMemory: '4Gi'
        // ),
        containerTemplate(
            name: 'git',
            image: 'alpine/git:latest', // AKS/GKE 환경에서는 :latest 대신 특정 버전 사용 (예: 'alpine/git:2.47.2') — latest 태그 차단 정책
            command: 'cat',
            ttyEnabled: true,
            resourceRequestCpu: '100m',
            resourceRequestMemory: '256Mi',
            resourceLimitCpu: '300m',
            resourceLimitMemory: '512Mi'
        ),
        containerTemplate(
            name: 'sonar-scanner',
            image: 'sonarsource/sonar-scanner-cli:latest', // AKS/GKE 환경에서는 :latest 대신 :11 사용 (latest 태그 차단 정책)
            command: 'cat',
            ttyEnabled: true,
            resourceRequestCpu: '200m',
            resourceRequestMemory: '512Mi',
            resourceLimitCpu: '1000m',
            resourceLimitMemory: '2Gi'
        )
    ],
    volumes: [
        emptyDirVolume(mountPath: '/opt/sonar-scanner/.sonar/cache', memory: false),
        // --- React / Vue ---
        emptyDirVolume(mountPath: '/root/.npm', memory: false)
        // --- Flutter ---
        // emptyDirVolume(mountPath: '/root/.pub-cache', memory: false)
    ]
) {
    node(PIPELINE_ID) {
        def imageTag = getImageTag()
        def environment = params.ENVIRONMENT ?: 'dev'
        def skipSonarQube = params.SKIP_SONARQUBE ?: 'false'
        def sonarScannerHome = '/opt/sonar-scanner'

        try {
            stage("Get Source") {
                checkout scm
            }

            stage('Build & Test') {
                // --- React / Vue (Node.js 기반) ---
                container('node') {
                    sh """
                        npm ci
                        NODE_OPTIONS="--max-old-space-size=3072" npm run build
                        npm run lint || true
                    """
                }
                // --- Flutter Web ---
                // container('flutter') {
                //     sh """
                //         flutter pub get
                //         flutter build web --release
                //         flutter analyze || true
                //     """
                // }
            }

            stage('SonarQube Analysis & Quality Gate') {
                if (skipSonarQube == 'true') {
                    echo "⏭️ Skipping SonarQube Analysis (SKIP_SONARQUBE=${params.SKIP_SONARQUBE})"
                } else {
                    container('sonar-scanner') {
                        script {
                            try {
                                withSonarQubeEnv('SonarQube') {
                                    // --- React / Vue (JS/TS) ---
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
                                      -Dsonar.javascript.node.maxspace=2048
                                    """
                                    // --- Flutter (Dart) ---
                                    // sh """
                                    //   timeout 300 ${sonarScannerHome}/bin/sonar-scanner \\
                                    //   -Dsonar.projectKey={SERVICE_NAME}-${environment} \\
                                    //   -Dsonar.projectName={SERVICE_NAME}-${environment} \\
                                    //   -Dsonar.sources=lib \\
                                    //   -Dsonar.tests=test \\
                                    //   -Dsonar.test.inclusions=**/*_test.dart \\
                                    //   -Dsonar.exclusions=build/**,.dart_tool/**,.packages/** \\
                                    //   -Dsonar.scm.disabled=true \\
                                    //   -Dsonar.sourceEncoding=UTF-8
                                    // """
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

            // --- 기본 (EKS 등): Podman 방식 ---
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
                                    --platform linux/amd64 \\
                                    -f deployment/container/Dockerfile-frontend \\
                                    --build-arg PROJECT_FOLDER="{프론트엔드-디렉토리}" \\
                                    --build-arg BUILD_FOLDER="deployment/container" \\
                                    -t {IMG_NAME}:${environment}-${imageTag} .

                                podman push {IMG_NAME}:${environment}-${imageTag}
                            """
                        }
                    }
                }
            }
            // --- AKS/GKE 환경: Kaniko 방식 (privileged 컨테이너 차단 시) ---
            // stage('Build & Push Images') {
            //     timeout(time: 30, unit: 'MINUTES') {
            //         container('kaniko') {
            //             withCredentials([
            //                 usernamePassword(
            //                     credentialsId: 'imagereg-credentials',
            //                     usernameVariable: 'IMG_USERNAME',
            //                     passwordVariable: 'IMG_PASSWORD'
            //                 ),
            //                 usernamePassword(
            //                     credentialsId: 'dockerhub-credentials',
            //                     usernameVariable: 'DOCKERHUB_USERNAME',
            //                     passwordVariable: 'DOCKERHUB_PASSWORD'
            //                 )
            //             ]) {
            //                 // --- DockerHub / ACR / ECR: config.json에 직접 인증 ---
            //                 // sh """
            //                 //     echo '{"auths":{"https://index.docker.io/v1/":{"username":"'\$DOCKERHUB_USERNAME'","password":"'\$DOCKERHUB_PASSWORD'"},"{IMG_REG}":{"username":"'\$IMG_USERNAME'","password":"'\$IMG_PASSWORD'"}}}' > /kaniko/.docker/config.json
            //                 // """
            //                 // --- GCP Artifact Registry: GOOGLE_APPLICATION_CREDENTIALS 방식 ---
            //                 // SA JSON을 파일로 저장 후 GOOGLE_APPLICATION_CREDENTIALS 환경변수로 GCR 인증
            //                 // config.json에는 DockerHub 인증만 포함
            //                 // sh '''
            //                 //     printf '%s' "$IMG_PASSWORD" > /kaniko/sa.json
            //                 //     export GOOGLE_APPLICATION_CREDENTIALS=/kaniko/sa.json
            //                 //     printf '{"auths":{"https://index.docker.io/v1/":{"username":"%s","password":"%s"}}}' "$DOCKERHUB_USERNAME" "$DOCKERHUB_PASSWORD" > /kaniko/.docker/config.json
            //                 // '''
            //                 // sh """
            //                 //     export GOOGLE_APPLICATION_CREDENTIALS=/kaniko/sa.json
            //                 //     /kaniko/executor \\
            //                 //         --dockerfile=deployment/container/Dockerfile-frontend \\
            //                 //         --context=dir://. \\
            //                 //         --build-arg PROJECT_FOLDER="{프론트엔드-디렉토리}" \\
            //                 //         --build-arg BUILD_FOLDER="deployment/container" \\
            //                 //         --destination={IMG_NAME}:${environment}-${imageTag} \\
            //                 //         --cache=false
            //                 // """
            //             }
            //         }
            //     }
            // }

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

                            # Kustomize 바이너리 직접 다운로드 (alpine/git의 ash는 bash 스크립트 비호환)
                            wget -qO- "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.6.0/kustomize_v5.6.0_linux_amd64.tar.gz" | tar xz
                            mv kustomize /usr/local/bin/ 2>/dev/null || export PATH=\$PATH:\$(pwd)

                            # 매니페스트 업데이트 (kustomize 방식)
                            cd {FRONTEND_SERVICE}/kustomize/overlays/${environment}

                            echo "Updating {SERVICE_NAME} image tag..."
                            kustomize edit set image {IMG_NAME}={IMG_NAME}:${environment}-${imageTag}

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

### Jenkins Job 생성

Jenkinsfile 작성 후, Jenkins REST API를 사용하여 Job을 생성한다.

> **사전 조건**: Jenkins에 아래 크리덴셜이 등록되어 있어야 한다.
> - `dockerhub-credentials` (또는 `imagereg-credentials`): 이미지 레지스트리 로그인용
> - `{JENKINS_GIT_CREDENTIALS}`: 소스/매니페스트 레포지토리 Git 접근용

#### 1) Jenkins CRUMB 획득

```bash
JENKINS_URL="{JENKINS_URL}"
JENKINS_USER="{JENKINS_USER}"
JENKINS_TOKEN="{JENKINS_TOKEN}"

CRUMB=$(curl -s -c /tmp/jenkins-cookies.txt \
  -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
  "${JENKINS_URL}/crumbIssuer/api/json" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['crumb'])")
```

> **주의**: Crumb 발급 시 `-c` 옵션으로 저장한 쿠키 파일을 Job 생성 요청 시 반드시 `-b` 옵션으로 함께 전달해야 한다.
> Crumb 헤더만 보내고 쿠키를 누락하면 `403 No valid crumb was included in the request` 에러가 발생한다.

#### 2) Job 생성

```bash
JOB_NAME="{SYSTEM_NAME}-frontend"

# Job 존재 여부 확인 (이미 존재하면 생성 건너뜀)
HTTP_CHECK=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
  "${JENKINS_URL}/job/${JOB_NAME}/api/json")

if [ "$HTTP_CHECK" = "200" ]; then
  echo "Job '${JOB_NAME}' already exists. Skipping creation."
else

curl -s -o /dev/null -w "%{http_code}" \
  -b /tmp/jenkins-cookies.txt \
  -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
  -H "Jenkins-Crumb:${CRUMB}" \
  -H "Content-Type:application/xml" \
  -d @- \
  "${JENKINS_URL}/createItem?name=${JOB_NAME}" << 'XMLEOF'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>프론트엔드 CI 파이프라인</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>BRANCH</name>
          <defaultValue>main</defaultValue>
          <description>빌드 브랜치</description>
        </hudson.model.StringParameterDefinition>
        <hudson.model.ChoiceParameterDefinition>
          <name>ENVIRONMENT</name>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array"><string>dev</string><string>staging</string><string>prod</string></a>
          </choices>
          <description>배포 환경</description>
        </hudson.model.ChoiceParameterDefinition>
        <hudson.model.ChoiceParameterDefinition>
          <name>SKIP_SONARQUBE</name>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array"><string>false</string><string>true</string></a>
          </choices>
          <description>SonarQube 분석 스킵 여부</description>
        </hudson.model.ChoiceParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>{SOURCE_REPO_URL}</url>
          <credentialsId>{JENKINS_GIT_CREDENTIALS}</credentialsId>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/${BRANCH}</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
    </scm>
    <scriptPath>deployment/cicd/Jenkinsfile-frontend</scriptPath>
    <lightweight>true</lightweight>
  </definition>
</flow-definition>
XMLEOF

fi
```

> 응답 코드 `200`이면 Job 생성 성공. `400`이면 동일 이름의 Job이 이미 존재할 수 있다.

### 결과서 작성
`docs/cicd/deploy-jenkins-cicd-front-result.md` 파일 생성.
아래 템플릿에 실제 치환값을 채워 작성.

```markdown
# {FRONTEND_SERVICE} 프론트엔드 Jenkins CI 파이프라인 결과서

## 실행 환경 정보
| 항목 | 값 |
|------|-----|
| CLOUD | {값} |
| IMG_REG | {값} |
| IMG_NAME | {값} |
| JENKINS_CLOUD_NAME | {값} |
| MANIFEST_REPO_URL | {값} |
| JENKINS_GIT_CREDENTIALS | {값} |

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
| `deployment/cicd/Jenkinsfile-frontend` | Jenkins 파이프라인 스크립트 |

## 파이프라인 구성
| 항목 | 값 |
|------|-----|
| Job 이름 | {SYSTEM_NAME}-frontend |

Get Source → Build & Test → SonarQube Analysis → Build & Push Images → Update Manifest Repository → Pipeline Complete

## 변수 치환 내역
| 플레이스홀더 | 치환값 |
|-------------|--------|
| {FRONTEND_FRAMEWORK} | {값} |
| {FRONTEND_SERVICE} | {값} |
| {SERVICE_NAME} | {값} |
| {NODE_VERSION} 또는 {FLUTTER_VERSION} | {값} |
| {IMG_REG} | {값} |
| {IMG_NAME} | {값} |
| {JENKINS_CLOUD_NAME} | {값} |
| {JENKINS_GIT_CREDENTIALS} | {값} |
| {MANIFEST_REPO_URL} | {값} |

```

## 체크리스트

### 사전 준비
- [ ] 프레임워크 확인 완료 (React / Vue / Flutter)
- [ ] 서비스명 확인 완료 (React/Vue: package.json, Flutter: pubspec.yaml)
- [ ] 실행정보 섹션에서 CLOUD, IMG_REG 확인 완료
- [ ] K8s Deployment YAML에서 이미지명(IMG_NAME) 확인 완료

### 파이프라인 파일
- [ ] `Jenkinsfile-frontend` 생성 완료
- [ ] `Jenkinsfile-frontend` 주요 내용 확인
  - 프레임워크에 맞는 빌드 컨테이너 활성화 (React/Vue: `node`, Flutter: `flutter`)
  - 프레임워크에 맞는 Build & Test 블록 활성화, 나머지 주석 처리
  - 프레임워크에 맞는 SonarQube 설정 블록 활성화
  - 변수 참조 문법 확인: `${variable}` 사용, `\${variable}` 사용 금지
  - 서비스명이 실제 {SERVICE_NAME}으로 치환되었는지 확인
  - 파드 자동 정리 설정: `podRetention: never()`, `idleMinutes: 1`, `terminationGracePeriodSeconds: 3`
  - try-catch-finally 블록 포함 (예외 상황에서도 정리 로직 실행 보장)
  - 매니페스트 레포지토리 업데이트: git container로 manifest repo clone 및 image tag 업데이트 후 push
- [ ] Dockerfile 및 Nginx 설정 파일 생성 완료

### Job 생성
- [ ] Jenkins Job 생성 완료 (REST API 또는 UI)

### 품질
- [ ] 시크릿 하드코딩 금지
- [ ] Podman 기반 빌드 구성 (AKS/GKE 환경에서는 Kaniko 기반)

## 주의사항

**공통**
- Jenkins Groovy에서 bash 변수 전달 시 `\${variable}` 사용 금지, `${variable}` 사용
- `podRetention: never()`는 문자열 `'never'`가 아닌 함수 호출 형태로 작성
- `cleanWs()`는 Workspace Cleanup 플러그인 필요. 미설치 시 `No such DSL method 'cleanWs'` 에러 발생. `podRetention: never()`로 Pod 자동 정리 권장
- `deleteDir()` 사용 시 `node_modules` / `.dart_tool` 파일 권한 문제로 실패 가능. `podRetention: never()`에 의존하는 것이 안전
- 이 가이드는 **Scripted Pipeline** 방식. Declarative Pipeline으로 작성 시 문법 차이 주의
- Jenkinsfile 템플릿에서 프레임워크에 해당하는 블록만 활성화하고, 나머지는 주석 유지.
  `// ---` 주석 마커로 프레임워크별 블록 구분

**AKS / GKE 환경**
- AKS/GKE에서 `privileged: true`를 차단하므로 Podman 대신 **Kaniko** 사용
- AKS/GKE에서 `:latest` 태그를 차단하므로 모든 컨테이너 이미지에 **명시적 버전 태그** 사용 (예: `alpine/git:2.47.2`, `sonarsource/sonar-scanner-cli:11`)
- Kaniko는 Docker config.json으로 인증하며, 레지스트리 키는 `docker.io`가 아닌 **`https://index.docker.io/v1/`** 사용
- **GCP Artifact Registry**: SA JSON 키를 config.json password에 직접 넣으면 JSON 특수문자로 파싱 에러 발생. 반드시 **GOOGLE_APPLICATION_CREDENTIALS** 환경변수 방식 사용. SA JSON을 파일(`/kaniko/sa.json`)로 저장 후 `export GOOGLE_APPLICATION_CREDENTIALS=/kaniko/sa.json`으로 인증. config.json에는 DockerHub 인증만 포함
- **Kaniko ephemeral-storage**: Kaniko는 이미지 빌드 시 많은 임시 스토리지를 사용함. 기본 1Gi 제한 시 `Container kaniko exceeded its local ephemeral storage limit` 에러로 Pod Evicted 발생. yaml spec에서 kaniko 컨테이너에 `ephemeral-storage` requests/limits 설정 필요 (권장: requests 5Gi, limits 20Gi). 빌드 컨테이너(node/gradle/python)도 2Gi/10Gi 설정 권장
- Jenkins Cloud 설정에서 `jenkins-agent-listener` 서비스가 없으면 Jenkins tunnel을 **`jenkins:50000`**으로 변경

**React / Vue (Node.js)**
- Next.js 빌드는 메모리 소비가 크므로 node 컨테이너의 메모리 limit을 **4Gi 이상**으로 설정. 부족 시 `OOMKilled` 발생
- `NODE_OPTIONS="--max-old-space-size=3072"` 환경변수로 Node.js 힙 메모리 한도 확장 필요

**Flutter**
- Flutter 컨테이너 이미지(`ghcr.io/cirruslabs/flutter`)는 용량이 크므로 초기 Pull 시간 고려 필요
- SonarQube Dart 플러그인(`sonar-dart`)이 SonarQube 서버에 설치되어 있어야 분석 가능
- `flutter build web --release` 결과물은 `build/web/` 디렉토리에 생성됨. Dockerfile의 COPY 경로 확인 필요
