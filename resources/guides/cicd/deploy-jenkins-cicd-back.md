# 백엔드 Jenkins 파이프라인 작성 가이드

## 목적
Jenkins + Kustomize 기반 백엔드 CI 파이프라인을 구축한다. CI/CD 분리 구조로, CI는 빌드·푸시·매니페스트 레포지토리 image tag 업데이트까지 수행하고, CD는 ArgoCD가 매니페스트 레포지토리 변경을 감지하여 자동 배포한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| Jenkins 인증 정보 | `(런타임 결정)` | 파이프라인 설정 |
| 컨테이너 레지스트리 | `(런타임 결정)` | 이미지 푸시 대상 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| Jenkins 스크립트 | `deployment/cicd/Jenkinsfile/Jenkinsfile-backend` |

## 방법론

### 사전 준비사항 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {CLOUD}: 클라우드 서비스 (AWS/Azure/GCP) — 레지스트리 로그인 분기에 사용
- {IMG_REG}: container 컨테이너 이미지 레지스트리 주소
- {SYSTEM_NAME}: 시스템명 (rootProject.name)
- {JENKINS_CLOUD_NAME}: Jenkins에 설정한 k8s Cloud 이름
- {JENKINS_GIT_CREDENTIALS}: 매니페스트 레포지토리 접근용 Jenkins Credential ID
- {MANIFEST_REPO_URL}: 매니페스트 레포지토리 URL

예시)
```
[실행정보]
- CLOUD: Azure
- SYSTEM_NAME: phonebill
- IMG_REG: docker.io
- JENKINS_CLOUD_NAME: k8s
- JENKINS_GIT_CREDENTIALS: github-credentials
- MANIFEST_REPO_URL: https://github.com/org/manifest-repo.git
```

### 시스템명과 서비스명 확인
settings.gradle에서 확인.
- {SYSTEM_NAME}: rootProject.name
- {SERVICE_NAMES}: include 'common'하위의 include문 뒤의 값임

예시) include 'common'하위의 서비스명들.
```
rootProject.name = 'myproject'

include 'common'
include 'api-gateway'
include 'user-service'
include 'order-service'
include 'payment-service'
```

### 이미지명 확인
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

### JDK버전 확인
루트 build.gradle에서 JDK 버전 확인.
{JDK_VERSION}: 'java' 섹션에서 JDK 버전 확인. 아래 예에서는 21임.
```
java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}
```

### Jenkinsfile 작성
`deployment/cicd/Jenkinsfile-backend` 파일 생성 방법을 안내합니다.

주요 구성 요소:
- **Pod Template**: Gradle, Podman, Git 컨테이너
- **Build**: Gradle 기반 빌드 (테스트 제외)
- **SonarQube Analysis & Quality Gate**: 항상 표시되는 단계, 내부에서 조건부 실행으로 테스트, 코드 품질 분석, Quality Gate 처리
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

**쉘 호환성 문제 해결**:
- Jenkins 컨테이너에서 기본 쉘이 `/bin/sh` (dash)인 경우 Bash 배열 문법 `()` 미지원
- **"syntax error: unexpected '('" 에러 발생** - Bash 배열 문법을 인식하지 못함
- **해결책**: Bash 배열 대신 공백 구분 문자열 사용 (모든 POSIX 쉘에서 호환)
- 변경 전: `svc_list=(service1 service2)` → `for service in "\${svc_list[@]}"`
- 변경 후: `services="service1 service2"` → `for service in \$services`


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
            name: 'podman',
            image: "mgoltzsche/podman",
            ttyEnabled: true,
            command: 'cat',
            privileged: true,
            resourceRequestCpu: '500m',
            resourceRequestMemory: '2Gi',
            resourceLimitCpu: '2000m',
            resourceLimitMemory: '4Gi'
        ),
        containerTemplate(
            name: 'gradle',
            image: 'gradle:jdk{JDK버전}',
            ttyEnabled: true,
            command: 'cat',
            resourceRequestCpu: '500m',
            resourceRequestMemory: '1Gi',
            resourceLimitCpu: '1000m',
            resourceLimitMemory: '2Gi',
            envVars: [
                envVar(key: 'DOCKER_HOST', value: 'unix:///run/podman/podman.sock'),
                envVar(key: 'TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE', value: '/run/podman/podman.sock'),
                envVar(key: 'TESTCONTAINERS_RYUK_DISABLED', value: 'true')
            ]
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
        )
    ],
    volumes: [
        emptyDirVolume(mountPath: '/home/gradle/.gradle', memory: false),
        emptyDirVolume(mountPath: '/run/podman', memory: false)
    ]
) {
    node(PIPELINE_ID) {
        def imageTag = getImageTag()
        def environment = params.ENVIRONMENT ?: 'dev'
        def skipSonarQube = params.SKIP_SONARQUBE ?: 'false'
        def targetService = params.SERVICE ?: 'all'
        def imageMap = [
            '{서비스명1}': '{이미지명1}',
            '{서비스명2}': '{이미지명2}',
            '{서비스명3}': '{이미지명3}'
        ]
        def targetMap = (targetService == 'all') ? imageMap : imageMap.subMap([targetService])

        try {
            stage("Get Source") {
                checkout scm
            }

            stage('Build') {
                container('gradle') {
                    sh "chmod +x gradlew"
                    if (targetService == 'all') {
                        sh "./gradlew build -x test"
                    } else {
                        sh "./gradlew :${targetService}:build -x test"
                    }
                }
            }

            stage('SonarQube Analysis & Quality Gate') {
                if (skipSonarQube == 'true') {
                    echo "Skipping SonarQube Analysis (SKIP_SONARQUBE=${params.SKIP_SONARQUBE})"
                } else {
                    container('gradle') {
                        script {
                            try {
                                // 각 서비스별로 개별적으로 SonarQube 분석 및 Quality Gate 확인
                                targetMap.keySet().each { service ->
                                    withSonarQubeEnv('SonarQube') {
                                        // 서비스별 테스트 및 SonarQube 분석
                                        sh """
                                            ./gradlew :${service}:test :${service}:jacocoTestReport :${service}:sonar \\
                                                -Dsonar.projectKey={SYSTEM_NAME}-${service}-${environment} \\
                                                -Dsonar.projectName={SYSTEM_NAME}-${service}-${environment} \\
                                                -Dsonar.java.binaries=build/classes/java/main \\
                                                -Dsonar.coverage.jacoco.xmlReportPaths=build/reports/jacoco/test/jacocoTestReport.xml \\
                                                -Dsonar.exclusions=**/config/**,**/entity/**,**/dto/**,**/*Application.class,**/exception/**
                                        """
                                    }

                                    // 각 서비스별 Quality Gate 확인
                                    timeout(time: 5, unit: 'MINUTES') {
                                        def qg = waitForQualityGate()
                                        if (qg.status != 'OK') {
                                            echo "Quality Gate failed for ${service}: ${qg.status}, but continuing pipeline..."
                                        }
                                    }
                                }
                            } catch (Exception e) {
                                echo "SonarQube analysis failed: ${e.getMessage()}, but continuing pipeline..."
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

                            targetMap.each { service, imgName ->
                                sh """
                                    podman build \\
                                        --platform linux/amd64 \\
                                        --build-arg BUILD_LIB_DIR="${service}/build/libs" \\
                                        --build-arg ARTIFACTORY_FILE="${service}.jar" \\
                                        -f deployment/container/Dockerfile-backend \\
                                        -t ${imgName}:${environment}-${imageTag} .

                                    podman push ${imgName}:${environment}-${imageTag}
                                """
                            }
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

                            # Kustomize 바이너리 직접 다운로드 (alpine/git의 ash는 bash 스크립트 비호환)
                            wget -qO- "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.6.0/kustomize_v5.6.0_linux_amd64.tar.gz" | tar xz
                            mv kustomize /usr/local/bin/ 2>/dev/null || export PATH=\$PATH:\$(pwd)

                            # 매니페스트 업데이트 (kustomize 방식)
                            cd {SYSTEM_NAME}/kustomize/overlays/${environment}

                            # 각 서비스별 이미지 태그 업데이트
                            ${targetMap.collect { svc, img -> "kustomize edit set image ${img}=${img}:${environment}-${imageTag}" }.join('\n                            ')}

                            # Git 설정 및 푸시
                            cd ../../../..
                            git config user.name "Jenkins CI"
                            git config user.email "jenkins@example.com"
                            git add .
                            git commit -m "Update {SYSTEM_NAME} ${environment} images to ${environment}-${imageTag}"
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

#### 2) Job 생성

```bash
JOB_NAME="{SYSTEM_NAME}-backend"

curl -s -o /dev/null -w "%{http_code}" \
  -b /tmp/jenkins-cookies.txt \
  -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
  -H "Jenkins-Crumb:${CRUMB}" \
  -H "Content-Type:application/xml" \
  -d @- \
  "${JENKINS_URL}/createItem?name=${JOB_NAME}" << 'XMLEOF'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>백엔드 CI 파이프라인</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.ChoiceParameterDefinition>
          <name>SERVICE</name>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array"><string>all</string><string>{서비스명1}</string><string>{서비스명2}</string><string>{서비스명3}</string></a>
          </choices>
          <description>빌드할 서비스 선택</description>
        </hudson.model.ChoiceParameterDefinition>
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
          <name>*/main</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
    </scm>
    <scriptPath>deployment/cicd/Jenkinsfile-backend</scriptPath>
    <lightweight>true</lightweight>
  </definition>
</flow-definition>
XMLEOF
```

> 응답 코드 `200`이면 Job 생성 성공.

### 결과서 작성
`docs/cicd/deploy-jenkins-cicd-back-result.md` 파일 생성.
아래 템플릿에 실제 치환값을 채워 작성.

```markdown
# {SYSTEM_NAME} 백엔드 Jenkins CI 파이프라인 결과서

## 실행 환경 정보
| 항목 | 값 |
|------|-----|
| CLOUD | {값} |
| IMG_REG | {값} |
| JENKINS_CLOUD_NAME | {값} |
| MANIFEST_REPO_URL | {값} |
| JENKINS_GIT_CREDENTIALS | {값} |

## 서비스 정보
| 항목 | 값 |
|------|-----|
| SYSTEM_NAME | {값} |
| SERVICE_NAMES | {값} |
| JDK_VERSION | {값} |

## 생성 파일
| 파일 | 설명 |
|------|------|
| `deployment/cicd/Jenkinsfile-backend` | Jenkins 파이프라인 스크립트 |

## 파이프라인 구성
| 항목 | 값 |
|------|-----|
| Job 이름 | {SYSTEM_NAME}-backend |

Get Source → Build & Test → SonarQube Analysis → Build & Push Images → Update Manifest Repository → Pipeline Complete

## 변수 치환 내역
| 플레이스홀더 | 치환값 |
|-------------|--------|
| {SYSTEM_NAME} | {값} |
| {SERVICE_NAMES} | {값} |
| {JDK_VERSION} | {값} |
| {IMG_REG} | {값} |
| {IMG_NAME} (서비스별) | {값} |
| {JENKINS_CLOUD_NAME} | {값} |
| {JENKINS_GIT_CREDENTIALS} | {값} |
| {MANIFEST_REPO_URL} | {값} |

```

## 체크리스트

### 사전 준비
- [ ] settings.gradle에서 시스템명과 서비스명 확인 완료
- [ ] 루트 build.gradle에서 JDK버전 확인 완료

### 파이프라인 파일
- [ ] `Jenkinsfile-backend` 생성 완료
- [ ] `Jenkinsfile-backend` 주요 내용 확인
  - Pod Template, Build, SonarQube, Manifest Repository Update 단계 포함
  - gradle 컨테이너 이미지 이름에 올바른 JDK버전 사용: `gradle:jdk{JDK버전}`
  - 변수 참조 문법 확인: `${variable}` 사용, `\${variable}` 사용 금지
  - 모든 서비스명이 실제 프로젝트 서비스명으로 치환되었는지 확인
  - 파드 자동 정리 설정: `podRetention: never()`, `idleMinutes: 1`, `terminationGracePeriodSeconds: 3`
  - try-catch-finally 블록 포함 (예외 상황에서도 정리 로직 실행 보장)
  - 매니페스트 레포지토리 업데이트: git container로 manifest repo clone 및 image tag 업데이트 후 push

### Job 생성
- [ ] Jenkins Job 생성 완료 (REST API 또는 UI)

### 품질
- [ ] 시크릿 하드코딩 금지
- [ ] Podman 기반 빌드 구성

## 주의사항
- Jenkins Groovy에서 bash 변수 전달 시 `\${variable}` 사용 금지, `${variable}` 사용
- Bash 배열 대신 공백 구분 문자열 사용 (POSIX 쉘 호환)
- `podRetention: never()`는 문자열 `'never'`가 아닌 함수 호출 형태로 작성
- `cleanWs()`는 Workspace Cleanup 플러그인 필요. 미설치 시 `No such DSL method 'cleanWs'` 에러 발생. `podRetention: never()`로 Pod 자동 정리 권장
- `deleteDir()` 사용 시 파일 권한 문제로 실패 가능. `podRetention: never()`에 의존하는 것이 안전
- 이 가이드는 **Scripted Pipeline** 방식. Declarative Pipeline으로 작성 시 문법 차이 주의
