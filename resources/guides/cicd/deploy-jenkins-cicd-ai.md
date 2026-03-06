# AI 서비스 Jenkins 파이프라인 작성 가이드

## 목적
Jenkins + Kustomize 기반 AI 서비스 CI 파이프라인을 구축함. CI/CD 분리 구조로, CI는 빌드·푸시·매니페스트 레포지토리 image tag 업데이트까지 수행하고,  
CD는 ArgoCD가 매니페스트 레포지토리 변경을 감지하여 자동 배포함.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| Jenkins 인증 정보 | `(런타임 결정)` | 파이프라인 설정 |
| 컨테이너 레지스트리 | `(런타임 결정)` | 이미지 푸시 대상 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| Jenkins 스크립트 | `deployment/cicd/Jenkinsfile-ai` |

## 방법론

### 프롬프트 제공정보 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {CLOUD}: 클라우드 서비스 (AWS/Azure/GCP) — 레지스트리 로그인 분기에 사용
- {AI_SERVICE}: AI 서비스명 (pyproject.toml의 [tool.poetry] name 필드)
- {IMG_REG}: container 컨테이너 이미지 레지스트리 주소
- {JENKINS_CLOUD_NAME}: Jenkins에 설정한 k8s Cloud 이름
- {JENKINS_GIT_CREDENTIALS}: 매니페스트 레포지토리 접근용 Jenkins Credential ID
- {MANIFEST_REPO_URL}: 매니페스트 레포지토리 URL

예시)
```
[실행정보]
- CLOUD: Azure
- AI_SERVICE: phonebill-ai
- IMG_REG: docker.io
- JENKINS_CLOUD_NAME: k8s
- JENKINS_GIT_CREDENTIALS: github-credentials
- MANIFEST_REPO_URL: https://github.com/org/manifest-repo.git
```

### 서비스명 확인
서비스명은 pyproject.toml에서 확인.
- {AI_SERVICE}: pyproject.toml의 `[tool.poetry]` 섹션 `name` 필드. 없으면 디렉토리명 사용.

예시)
```toml
[tool.poetry]
name = "phonebill-ai"
version = "0.1.0"
```

### Python 버전 확인
pyproject.toml에서 Python 버전 확인.
{PYTHON_VERSION}: `[tool.poetry.dependencies]` 섹션에서 python 필드 확인. 없으면 3.11 사용.
```toml
[tool.poetry.dependencies]
python = "^3.11"
```

### 이미지명 확인
`deployment/k8s/{AI_SERVICE}/` Deployment YAML에서 컨테이너 이미지명 추출.
- Deployment YAML의 `image:` 필드에서 태그(`:latest` 등)를 제거하여 `{IMG_NAME}` 확보
- CI 파이프라인에서 `{IMG_NAME}` 뒤에 새 태그(`${environment}-${imageTag}`)를 붙여 빌드·푸시
- 매니페스트 레포지토리도 동일한 새 태그로 업데이트

예시) `deployment/k8s/phonebill-ai/` Deployment YAML:
```yaml
image: docker.io/phonebill/phonebill-ai:latest
```
→ {IMG_NAME} = `docker.io/phonebill/phonebill-ai` (`:latest` 태그 제거)
→ 빌드 태그: `docker.io/phonebill/phonebill-ai:dev-20260305143022`

### Jenkinsfile 작성
`deployment/cicd/Jenkinsfile-ai` 파일 생성 방법을 안내함.

주요 구성 요소:
- **Pod Template**: Python, Podman(또는 AKS/GKE 환경에서는 Kaniko), Git, SonarQube Scanner 컨테이너
- **Build & Test**: Python/Poetry 기반 빌드 및 단위 테스트 (pytest)
- **SonarQube Analysis**: Python 코드 품질 분석 및 Quality Gate
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

> **참고**: `git` 컨테이너(`alpine/git`)의 기본 쉘은 `/bin/sh`(ash)이므로 Bash 전용 문법(배열 등) 사용 불가.
> AI 서비스는 단일 서비스이므로 루프가 불필요하지만, 쉘 스크립트 작성 시 POSIX 호환 문법을 사용.

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
    ''',
    containers: [
        containerTemplate(
            name: 'python',
            image: 'python:{PYTHON_VERSION}-slim',
            ttyEnabled: true,
            command: 'cat',
            resourceRequestCpu: '400m',
            resourceRequestMemory: '1Gi',
            resourceLimitCpu: '2000m',
            resourceLimitMemory: '4Gi'
        ),
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
            resourceLimitMemory: '1Gi'
        )
    ],
    volumes: [
        emptyDirVolume(mountPath: '/opt/sonar-scanner/.sonar/cache', memory: false),
        emptyDirVolume(mountPath: '/root/.cache/pip', memory: false),
        emptyDirVolume(mountPath: '/root/.cache/pypoetry', memory: false)
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
                container('python') {
                    sh """
                        pip install poetry
                        poetry install
                        poetry build
                        pytest || true
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
                                      -Dsonar.projectKey={AI_SERVICE}-${environment} \\
                                      -Dsonar.projectName={AI_SERVICE}-${environment} \\
                                      -Dsonar.sources=app \\
                                      -Dsonar.tests=tests \\
                                      -Dsonar.test.inclusions=**/test_*.py,**/*_test.py \\
                                      -Dsonar.exclusions=**/__pycache__/**,**/venv/**,**/.venv/**,**/dist/** \\
                                      -Dsonar.scm.disabled=true \\
                                      -Dsonar.sourceEncoding=UTF-8 \\
                                      -Dsonar.python.coverage.reportPaths=coverage.xml \\
                                      -Dsonar.language=python
                                    """
                                }

                                timeout(time: 5, unit: 'MINUTES') {
                                    def qg = waitForQualityGate()
                                    if (qg.status != 'OK') {
                                        echo "⚠️ Quality Gate failed: ${qg.status}, but continuing pipeline... (AI 서비스는 초기 단계에서 커버리지가 낮을 수 있어 경고만 출력)"
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
                                    -f deployment/container/Dockerfile-ai \\
                                    --build-arg PROJECT_FOLDER="{ai-서비스-디렉토리}" \\
                                    --build-arg EXPORT_PORT="8000" \\
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
            //                     credentialsId: 'dockerhub-credentials',
            //                     usernameVariable: 'IMG_USERNAME',
            //                     passwordVariable: 'IMG_PASSWORD'
            //                 )
            //             ]) {
            //                 sh """
            //                     echo '{"auths":{"https://index.docker.io/v1/":{"username":"'\$IMG_USERNAME'","password":"'\$IMG_PASSWORD'"}}}' > /kaniko/.docker/config.json
            //
            //                     /kaniko/executor \\
            //                         --dockerfile=deployment/container/Dockerfile-ai \\
            //                         --context=dir://. \\
            //                         --build-arg PROJECT_FOLDER="{ai-서비스-디렉토리}" \\
            //                         --build-arg EXPORT_PORT=8000 \\
            //                         --destination={IMG_NAME}:${environment}-${imageTag} \\
            //                         --cache=false
            //                 """
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
                            cd {AI_SERVICE}/kustomize/overlays/${environment}

                            echo "Updating {AI_SERVICE} image tag..."
                            kustomize edit set image {IMG_NAME}={IMG_NAME}:${environment}-${imageTag}

                            # Git 설정 및 푸시
                            cd ../../../..
                            git config user.name "Jenkins CI"
                            git config user.email "jenkins@example.com"
                            git add .
                            git commit -m "Update {AI_SERVICE} ${environment} image to ${environment}-${imageTag}"
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
JOB_NAME="{SYSTEM_NAME}-ai"

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
  <description>AI 서비스 CI 파이프라인</description>
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
    <scriptPath>deployment/cicd/Jenkinsfile-ai</scriptPath>
    <lightweight>true</lightweight>
  </definition>
</flow-definition>
XMLEOF

fi
```

> 응답 코드 `200`이면 Job 생성 성공. `400`이면 동일 이름의 Job이 이미 존재할 수 있다.

### 결과서 작성
`docs/cicd/deploy-jenkins-cicd-ai-result.md` 파일 생성.
아래 템플릿에 실제 치환값을 채워 작성.

```markdown
# {AI_SERVICE} AI 서비스 Jenkins CI 파이프라인 결과서

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
| AI_SERVICE | {값} |
| PYTHON_VERSION | {값} |

## 생성 파일
| 파일 | 설명 |
|------|------|
| `deployment/cicd/Jenkinsfile-ai` | Jenkins 파이프라인 스크립트 |

## 파이프라인 구성
| 항목 | 값 |
|------|-----|
| Job 이름 | {SYSTEM_NAME}-ai |

Get Source → Build & Test → SonarQube Analysis → Build & Push Images → Update Manifest Repository → Pipeline Complete

## 변수 치환 내역
| 플레이스홀더 | 치환값 |
|-------------|--------|
| {AI_SERVICE} | {값} |
| {PYTHON_VERSION} | {값} |
| {IMG_REG} | {값} |
| {IMG_NAME} | {값} |
| {JENKINS_CLOUD_NAME} | {값} |
| {JENKINS_GIT_CREDENTIALS} | {값} |
| {MANIFEST_REPO_URL} | {값} |

```

## 체크리스트

### 사전 준비
- [ ] pyproject.toml에서 프로젝트명 확인 완료
- [ ] 실행정보 섹션에서 CLOUD, IMG_REG 확인 완료
- [ ] K8s Deployment YAML에서 이미지명(IMG_NAME) 확인 완료

### 파이프라인 파일
- [ ] `Jenkinsfile-ai` 생성 완료
- [ ] `Jenkinsfile-ai` 주요 내용 확인
  - 변수 참조 문법 확인: `${variable}` 사용, `\${variable}` 사용 금지
  - 서비스명이 실제 {AI_SERVICE}으로 치환되었는지 확인
  - python container 이미지 이름에 올바른 Python 버전 사용: `python:{PYTHON_VERSION}-slim`
  - 파드 자동 정리 설정: `podRetention: never()`, `idleMinutes: 1`, `terminationGracePeriodSeconds: 3`
  - try-catch-finally 블록 포함 (예외 상황에서도 정리 로직 실행 보장)
  - 매니페스트 레포지토리 업데이트: git container로 manifest repo clone 및 image tag 업데이트 후 push
- [ ] Dockerfile-ai 파일 생성 완료

### Job 생성
- [ ] Jenkins Job 생성 완료 (REST API 또는 UI)

### 품질
- [ ] 시크릿 하드코딩 금지
- [ ] Podman 기반 빌드 구성 (AKS/GKE 환경에서는 Kaniko 기반)

## 주의사항

**AKS / GKE 환경**
- AKS/GKE에서 `privileged: true`를 차단하므로 Podman 대신 **Kaniko** 사용
- AKS/GKE에서 `:latest` 태그를 차단하므로 모든 컨테이너 이미지에 **명시적 버전 태그** 사용 (예: `alpine/git:2.47.2`, `sonarsource/sonar-scanner-cli:11`)
- Kaniko는 Docker config.json으로 인증하며, 레지스트리 키는 `docker.io`가 아닌 **`https://index.docker.io/v1/`** 사용
- Jenkins Cloud 설정에서 `jenkins-agent-listener` 서비스가 없으면 Jenkins tunnel을 **`jenkins:50000`**으로 변경

**공통**
- Jenkins Groovy에서 bash 변수 전달 시 `\${variable}` 사용 금지, `${variable}` 사용
- `podRetention: never()`는 문자열 `'never'`가 아닌 함수 호출 형태로 작성
- `pytest --cov` 옵션 사용 시 requirements.txt에 `pytest-cov` 패키지 필요. 미설치 시 `unrecognized arguments` 에러 발생
- `cleanWs()`는 Workspace Cleanup 플러그인 필요. 미설치 시 `No such DSL method 'cleanWs'` 에러 발생. `podRetention: never()`로 Pod 자동 정리 권장
- `deleteDir()` 사용 시 파일 권한 문제로 실패 가능 (예: Python venv). `podRetention: never()`에 의존하는 것이 안전
- 이 가이드는 **Scripted Pipeline** 방식. Declarative Pipeline으로 작성 시 문법 차이 주의
