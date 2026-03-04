# 백엔드 Jenkins 파이프라인 작성 가이드

## 목적
Jenkins + Kustomize 기반 백엔드 CI 파이프라인을 구축한다. CI/CD 분리 구조로, CI는 빌드·푸시·매니페스트 레포지토리 image tag 업데이트까지 수행하고, CD는 ArgoCD가 매니페스트 레포지토리 변경을 감지하여 자동 배포한다.

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
| Jenkins 스크립트 | `deployment/cicd/Jenkinsfile` (모노레포 시 `Jenkinsfile-backend`) |

## 방법론

### 사전 준비사항 확인
프롬프트의 '[실행정보]'섹션에서 아래정보를 확인
- {CLOUD}: 클라우드 서비스 (AWS/Azure/GCP) — 레지스트리 로그인 분기에 사용
- {IMG_REG}: container 컨테이너 이미지 레지스트리 주소
- {IMG_ORG}: container IMG_ORG
- {SYSTEM_NAME}: 시스템명 (rootProject.name)
- {JENKINS_CLOUD_NAME}: Jenkins에 설정한 k8s Cloud 이름
- {NAMESPACE}: 네임스페이스
- {JENKINS_GIT_CREDENTIALS}: 매니페스트 레포지토리 접근용 Jenkins Credential ID
- {MANIFEST_REPO_URL}: 매니페스트 레포지토리 URL

예시)
```
[실행정보]
- CLOUD: Azure
- SYSTEM_NAME: phonebill
- IMG_REG: docker.io
- IMG_ORG: phonebill
- JENKINS_CLOUD_NAME: k8s
- NAMESPACE: phonebill
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

### Jenkins 서버 환경 구성 안내
- Jenkins 설치 및 필수 플러그인 설치
  ```
  # Jenkins 필수 플러그인 목록
  - Kubernetes
  - Pipeline Utility Steps
  - Docker Pipeline
  - GitHub
  - SonarQube Scanner
  ```

- Jenkins Credentials 등록 방법 안내
  ```
  # Image Credentials
  # 레지스트리별 Username: Docker Hub → Docker Hub 사용자명, ACR → ACR 이름, ECR → AWS, GCR → _json_key
  # 상세 설정은 setup-cicd-tools.md의 Image Registry Credential 섹션 참조
  - Kind: Username with password
  - ID: imagereg-credentials
  - Username: {레지스트리 사용자명}
  - Password: {레지스트리 비밀번호}

  # Docker Hub Credentials (Rate Limit 해결용)
  - Kind: Username with password
  - ID: dockerhub-credentials
  - Username: {DOCKERHUB_USERNAME}
  - Password: {DOCKERHUB_PASSWORD}
  - 참고: Docker Hub 무료 계정 생성 (https://hub.docker.com)

  # SonarQube Token
  - Kind: Secret text
  - ID: sonarqube-token
  - Secret: {SonarQube토큰}
  ```

### Kustomize 디렉토리 구조 생성
- 프로젝트 루트에 CI/CD 디렉토리 생성
  ```
  mkdir -p deployment/cicd/kustomize/{base,overlays/{dev,staging,prod}}
  mkdir -p deployment/cicd/kustomize/base/{common,{SERVICE_NAME_1},{SERVICE_NAME_2},...}
  mkdir -p deployment/cicd/{config,scripts}
  ```
- 기존 k8s 매니페스트를 base로 복사
  ```
  # 기존 deployment/k8s/* 파일들을 base로 복사
  cp deployment/k8s/common/* deployment/cicd/kustomize/base/common/
  cp deployment/k8s/{SERVICE_NAME}/* deployment/cicd/kustomize/base/{SERVICE_NAME}/

  # 네임스페이스 하드코딩 제거
  find deployment/cicd/kustomize/base -name "*.yaml" -exec sed -i 's/namespace: .*//' {} \;
  ```

### Base Kustomization 작성
`deployment/cicd/kustomize/base/kustomization.yaml` 파일 생성 방법 안내

**⚠️ 중요: 리소스 누락 방지 가이드**
1. **디렉토리별 파일 확인**: 각 서비스 디렉토리의 모든 yaml 파일을 확인
2. **일관성 체크**: 모든 서비스가 동일한 파일 구조를 가지는지 확인 (deployment, service, configmap, secret)
3. **누락 검증**: `ls deployment/cicd/kustomize/base/{서비스명}/` 명령으로 실제 파일과 kustomization.yaml 리스트 비교
4. **명명 규칙 준수**: ConfigMap은 `cm-{서비스명}.yaml`, Secret은 `secret-{서비스명}.yaml` 패턴 확인

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  # Common resources
  - common/cm-common.yaml
  - common/secret-common.yaml
  - common/secret-imagepull.yaml
  - common/ingress.yaml

  # 각 서비스별 리소스 (누락 없이 모두 포함)
  # {서비스명1} (예: api-gateway)
  - {서비스명1}/deployment.yaml
  - {서비스명1}/service.yaml
  - {서비스명1}/cm-{서비스명1}.yaml      # ConfigMap이 있는 경우
  - {서비스명1}/secret-{서비스명1}.yaml  # Secret이 있는 경우

  # {서비스명2} (예: user-service)
  - {서비스명2}/deployment.yaml
  - {서비스명2}/service.yaml
  - {서비스명2}/cm-{서비스명2}.yaml      # ConfigMap이 있는 경우
  - {서비스명2}/secret-{서비스명2}.yaml  # Secret이 있는 경우

  # {서비스명3} (예: order-service)
  - {서비스명3}/deployment.yaml
  - {서비스명3}/service.yaml
  - {서비스명3}/cm-{서비스명3}.yaml      # ConfigMap이 있는 경우
  - {서비스명3}/secret-{서비스명3}.yaml  # Secret이 있는 경우

  # ... 추가 서비스들도 동일한 패턴으로 계속 작성


images:
  - name: {IMG_REG}/{IMG_ORG}/{서비스명1}
    newTag: latest
  - name: {IMG_REG}/{IMG_ORG}/{서비스명2}
    newTag: latest
  - name: {IMG_REG}/{IMG_ORG}/{서비스명3}
    newTag: latest
  # ... 각 서비스별로 image 항목 추가
```

**검증 명령어**:
```bash
# 각 서비스 디렉토리의 파일 확인
ls deployment/cicd/kustomize/base/*/

# kustomization.yaml 유효성 검사
kubectl kustomize deployment/cicd/kustomize/base/

# 누락된 리소스 확인
for dir in deployment/cicd/kustomize/base/*/; do
  service=$(basename "$dir")
  echo "=== $service ==="
  ls "$dir"*.yaml 2>/dev/null || echo "No YAML files found"
done
```

### 환경별 Patch 파일 생성
각 환경별로 필요한 patch 파일들을 생성합니다.
**중요원칙**:
- **base 매니페스트에 없는 항목은 추가 않함**
- **base 매니페스트와 항목이 일치해야 함**
- Secret 매니페스트에 'data'가 아닌 'stringData'사용

**1. ConfigMap Common Patch 파일 생성**
`deployment/cicd/kustomize/overlays/{환경}/cm-common-patch.yaml`

- base 매니페스트를 환경별로 복사
  ```
  cp deployment/cicd/kustomize/base/common/cm-common.yaml deployment/cicd/kustomize/overlays/{환경}/cm-common-patch.yaml
  ```

- SPRING_PROFILES_ACTIVE를 환경에 맞게 설정 (dev/staging/prod)
- DDL_AUTO 설정: dev는 "update", staging/prod는 "validate"
- JWT 토큰 유효시간은 prod에서 보안을 위해 짧게 설정

**2. Secret Common Patch 파일 생성**
`deployment/cicd/kustomize/overlays/{환경}/secret-common-patch.yaml`

- base 매니페스트를 환경별로 복사
  ```
  cp deployment/cicd/kustomize/base/common/secret-common.yaml deployment/cicd/kustomize/overlays/{환경}/secret-common-patch.yaml
  ```

**3. Ingress Patch 파일 생성**
`deployment/cicd/kustomize/overlays/{환경}/ingress-patch.yaml`
- base의 ingress.yaml을 환경별로 오버라이드
- **⚠️ 중요**: 개발환경 Ingress Host의 기본값은 base의 ingress.yaml과 **정확히 동일하게** 함
  - base에서 `host: phonebill-api.20.214.196.128.nip.io` 이면
  - dev에서도 `host: phonebill-api.20.214.196.128.nip.io` 로 동일하게 설정
  - **절대** `phonebill-dev-api.xxx` 처럼 변경하지 말 것
- Staging/Prod 환경별 도메인 설정: {SYSTEM_NAME}.도메인 형식
- service name을 '{서비스명}'으로 함.
- Staging/prod 환경은 HTTPS 강제 적용 및 SSL 인증서 설정
- staging/prod는 nginx.ingress.kubernetes.io/ssl-redirect: "true"
- dev는 nginx.ingress.kubernetes.io/ssl-redirect: "false"

**4. deployment Patch 파일 생성** ⚠️ **중요**
각 서비스별로 별도 파일 생성
`deployment/cicd/kustomize/overlays/{환경}/deployment-{서비스명}-patch.yaml`

**필수 포함 사항:**
- ✅ **replicas 설정**: 각 서비스별 Deployment의 replica 수를 환경별로 설정
  - dev: 모든 서비스 1 replica (리소스 절약)
  - staging: 모든 서비스 2 replicas
  - prod: 모든 서비스 3 replicas
- ✅ **resources 설정**: 각 서비스별 Deployment의 resources를 환경별로 설정
  - dev: requests(256m CPU, 256Mi Memory), limits(1024m CPU, 1024Mi Memory)
  - staging: requests(512m CPU, 512Mi Memory), limits(2048m CPU, 2048Mi Memory)
  - prod: requests(1024m CPU, 1024Mi Memory), limits(4096m CPU, 4096Mi Memory)

**작성 형식:**
- **Strategic Merge Patch 형식** 사용 (JSON Patch 아님)
- 각 서비스별로 별도의 Deployment 리소스로 분리하여 작성
- replicas와 resources를 **반드시 모두** 포함

**5. 서비스별 Secret Patch 파일 생성**
`deployment/cicd/kustomize/overlays/{환경}/secret-{서비스명}-patch.yaml`

- base 매니페스트를 환경별로 복사
  ```
  cp deployment/cicd/kustomize/base/{서비스명}/secret-{서비스명}.yaml deployment/cicd/kustomize/overlays/{환경}/secret-{서비스명}-patch.yaml
  ```

### 환경별 Overlay 작성
각 환경별로 `overlays/{환경}/kustomization.yaml` 생성
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: {NAMESPACE}

resources:
  - ../../base

patches:
  - path: cm-common-patch.yaml
    target:
      kind: ConfigMap
      name: cm-common
  - path: deployment-{서비스명}-patch.yaml
    target:
      kind: Deployment
      name: {서비스명}
  - path: ingress-patch.yaml
    target:
      kind: Ingress
      name: {SYSTEM_NAME}-ingress
  - path: secret-common-patch.yaml
    target:
      kind: Secret
      name: secret-common
  - path: secret-{서비스명}-patch.yaml
    target:
      kind: Secret
      name: secret-{서비스명}

images:
  - name: {IMG_REG}/{IMG_ORG}/{서비스명}
    newTag: latest

```

### 환경별 설정 파일 작성
`deployment/cicd/config/deploy_env_vars_{환경}` 파일 생성 방법

> **참고**: Jenkins는 인-클러스터 ServiceAccount로 K8s에 접근하므로 클라우드별 설정(resource_group, cluster_name 등)이 불필요합니다. GitHub Actions는 외부에서 실행되므로 클라우드별 추가 설정이 필요합니다.

```bash
# {환경} Environment Configuration
namespace={NAMESPACE}
```

### Jenkinsfile 작성
`deployment/cicd/Jenkinsfile` 파일 생성 방법을 안내합니다.

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


Jenkinsfile 예시:
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
        def props
        def imageTag = getImageTag()
        def environment = params.ENVIRONMENT ?: 'dev'
        def skipSonarQube = params.SKIP_SONARQUBE ?: 'true'
        def services = ['{서비스명1}', '{서비스명2}', '{서비스명3}']

        try {
            stage("Get Source") {
                checkout scm
                props = readProperties file: "deployment/cicd/config/deploy_env_vars_${environment}"
            }

            stage('Build') {
                container('gradle') {
                    sh """
                        chmod +x gradlew
                        ./gradlew build -x test
                    """
                }
            }

            stage('SonarQube Analysis & Quality Gate') {
                if (skipSonarQube == 'true') {
                    echo "⏭️ Skipping SonarQube Analysis (SKIP_SONARQUBE=${params.SKIP_SONARQUBE})"
                } else {
                    container('gradle') {
                        // 각 서비스별로 개별적으로 SonarQube 분석 및 Quality Gate 확인
                        services.each { service ->
                            withSonarQubeEnv('SonarQube') {
                                echo "🔍 Starting SonarQube analysis for ${service}..."

                                // 서비스별 테스트 및 SonarQube 분석
                                sh """
                                    ./gradlew :${service}:test :${service}:jacocoTestReport :${service}:sonar \\
                                        -Dsonar.projectKey={SYSTEM_NAME}-${service}-${environment} \\
                                        -Dsonar.projectName={SYSTEM_NAME}-${service}-${environment} \\
                                        -Dsonar.java.binaries=build/classes/java/main \\
                                        -Dsonar.coverage.jacoco.xmlReportPaths=build/reports/jacoco/test/jacocoTestReport.xml \\
                                        -Dsonar.exclusions=**/config/**,**/entity/**,**/dto/**,**/*Application.class,**/exception/**
                                """

                                echo "✅ SonarQube analysis completed for ${service}"
                            }

                            // 각 서비스별 Quality Gate 확인
                            timeout(time: 5, unit: 'MINUTES') {
                                echo "⏳ Waiting for Quality Gate result for ${service}..."
                                def qg = waitForQualityGate()
                                if (qg.status != 'OK') {
                                    error "❌ Quality Gate failed for ${service}: ${qg.status}"
                                } else {
                                    echo "✅ Quality Gate passed for ${service}"
                                }
                            }
                        }

                        echo "🎉 All services passed SonarQube Quality Gates!"
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

                            services.each { service ->
                                sh """
                                    podman build \\
                                        --build-arg BUILD_LIB_DIR="${service}/build/libs" \\
                                        --build-arg ARTIFACTORY_FILE="${service}.jar" \\
                                        -f deployment/container/Dockerfile-backend \\
                                        -t {IMG_REG}/{IMG_ORG}/${service}:${environment}-${imageTag} .

                                    podman push {IMG_REG}/{IMG_ORG}/${service}:${environment}-${imageTag}
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

                            # Kustomize 설치
                            curl -sL "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | sh
                            mv kustomize /usr/local/bin/ 2>/dev/null || export PATH=\$PATH:\$(pwd)

                            # 매니페스트 업데이트 (kustomize 방식)
                            cd {SYSTEM_NAME}/kustomize/overlays/${environment}

                            # 각 서비스별 이미지 태그 업데이트
                            # ⚠️ 이 서비스 목록은 Groovy 레벨의 services 리스트와 동일하게 유지해야 합니다
                            services="{서비스명1} {서비스명2} {서비스명3}"
                            for service in \$services; do
                                echo "Updating \$service image tag..."
                                kustomize edit set image {IMG_REG}/{IMG_ORG}/\$service={IMG_REG}/{IMG_ORG}/\$service:${environment}-${imageTag}
                            done

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

### Jenkins Pipeline Job 생성 방법 안내
- Jenkins 웹 UI에서 New Item > Pipeline 선택
- Pipeline script from SCM 설정 방법:
  ```
  SCM: Git
  Repository URL: {Git저장소URL}
  Branch: main (또는 develop)
  Script Path: deployment/cicd/Jenkinsfile
  ```
- Pipeline Parameters 설정:
  ```
  ENVIRONMENT: Choice Parameter (dev, staging, prod)
  IMAGE_TAG: String Parameter (default: latest)
  SKIP_SONARQUBE: String Parameter (default: true)
  ```

### SonarQube 프로젝트 설정 방법
- SonarQube에서 각 서비스별 프로젝트 생성
- Quality Gate 설정:
  > **참고**: 백엔드는 Coverage >= 80%를 적용합니다. 프론트엔드는 초기 단계에서 테스트 커버리지 확보가 어려워 70%로 완화합니다.
  ```
  Coverage: >= 80%
  Duplicated Lines: <= 3%
  Maintainability Rating: <= A
  Reliability Rating: <= A
  Security Rating: <= A
  ```

### 배포 실행 방법
- Jenkins 파이프라인 실행:
  ```
  1. Jenkins > {프로젝트명} > Build with Parameters
  2. ENVIRONMENT 선택 (dev/staging/prod)
  3. IMAGE_TAG 입력 (선택사항)
  4. SKIP_SONARQUBE 입력 (SonarQube 분석 건너뛰려면 "true", 실행하려면 "false")
  5. Build 클릭
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
  cd {MANIFEST_REPO}/{SYSTEM_NAME}/kustomize/overlays/{환경}
  kustomize edit set image {IMG_REG}/{IMG_ORG}/{서비스명}:{환경}-{이전태그}
  git add . && git commit -m "rollback: {서비스명} to {이전태그}" && git push origin main
  ```

## 출력 형식

### 📋 사전 준비 체크리스트
- [ ] settings.gradle에서 시스템명과 서비스명 확인 완료
- [ ] 루트 build.gradle에서 JDK버전 확인 완료

### 📂 Kustomize 구조 생성 체크리스트
- [ ] 디렉토리 구조 생성: `deployment/cicd/kustomize/{base,overlays/{dev,staging,prod}}`
- [ ] 서비스별 base 디렉토리 생성: `deployment/cicd/kustomize/base/{common,{서비스명들}}`
- [ ] 기존 k8s 매니페스트를 base로 복사 완료
- [ ] **리소스 누락 방지 검증 완료**:
  - [ ] `ls deployment/cicd/kustomize/base/*/` 명령으로 모든 서비스 디렉토리의 파일 확인
  - [ ] 각 서비스별 필수 파일 존재 확인 (deployment.yaml, service.yaml 필수)
  - [ ] ConfigMap 파일 존재 시 `cm-{서비스명}.yaml` 명명 규칙 준수 확인
  - [ ] Secret 파일 존재 시 `secret-{서비스명}.yaml` 명명 규칙 준수 확인
- [ ] Base kustomization.yaml 파일 생성 완료
  - [ ] 모든 서비스의 deployment.yaml, service.yaml 포함 확인
  - [ ] 존재하는 모든 ConfigMap 파일 포함 확인 (`cm-{서비스명}.yaml`)
  - [ ] 존재하는 모든 Secret 파일 포함 확인 (`secret-{서비스명}.yaml`)
- [ ] **검증 명령어 실행 완료**:
  - [ ] `kubectl kustomize deployment/cicd/kustomize/base/` 정상 실행 확인
  - [ ] 에러 메시지 없이 모든 리소스 출력 확인

### 🔧 환경별 Overlay 구성 체크리스트

#### 중요 체크 사항
- Base Kustomization에서 존재하지 않는 Secret 파일들 제거

#### 공통 체크 사항
- **base 매니페스트에 없는 항목을 추가하지 않았는지 체크**
- **base 매니페스트와 항목이 일치 하는지 체크**
- Secret 매니페스트에 'data'가 아닌 'stringData'사용했는지 체크
- **⚠️ Kustomize patch 방법 변경**: `patchesStrategicMerge` → `patches` (target 명시)

#### DEV 환경
- [ ] `overlays/dev/kustomization.yaml` 생성 완료
- [ ] `overlays/dev/cm-common-patch.yaml` 생성 완료 (dev 프로파일, update DDL)
- [ ] `overlays/dev/secret-common-patch.yaml` 생성 완료
- [ ] `overlays/dev/ingress-patch.yaml` 생성 완료 (**Host 기본값은 base의 ingress.yaml과 동일**)
- [ ] 각 서비스별 `overlays/dev/deployment-{서비스명}-patch.yaml` 생성 완료 (replicas, resources 지정)
- [ ] 각 서비스별 `overlays/dev/secret-{서비스명}-patch.yaml` 생성 완료

#### STAGING 환경
- [ ] `overlays/staging/kustomization.yaml` 생성 완료
- [ ] `overlays/staging/cm-common-patch.yaml` 생성 완료 (staging 프로파일, validate DDL)
- [ ] `overlays/staging/secret-common-patch.yaml` 생성 완료
- [ ] `overlays/staging/ingress-patch.yaml` 생성 완료 (staging 도메인, HTTPS, SSL 인증서)
- [ ] 각 서비스별 `overlays/staging/deployment-{서비스명}-patch.yaml` 생성 완료 (replicas, resources 지정)
- [ ] 각 서비스별 `overlays/staging/secret-{서비스명}-patch.yaml` 생성 완료

#### PROD 환경
- [ ] `overlays/prod/kustomization.yaml` 생성 완료
- [ ] `overlays/prod/cm-common-patch.yaml` 생성 완료 (prod 프로파일, validate DDL, 짧은 JWT)
- [ ] `overlays/prod/secret-common-patch.yaml` 생성 완료
- [ ] `overlays/prod/ingress-patch.yaml` 생성 완료 (prod 도메인, HTTPS, SSL 인증서)
- [ ] 각 서비스별 `overlays/prod/deployment-{서비스명}-patch.yaml` 생성 완료 (replicas, resources 지정)
- [ ] 각 서비스별 `overlays/prod/secret-{서비스명}-patch.yaml` 생성 완료

### ⚙️ 설정 및 스크립트 체크리스트
- [ ] 환경별 설정 파일 생성: `config/deploy_env_vars_{dev,staging,prod}`
- [ ] `Jenkinsfile` 생성 완료
- [ ] `Jenkinsfile` 주요 내용 확인
  - Pod Template, Build, SonarQube, Manifest Repository Update 단계 포함
  - gradle 컨테이너 이미지 이름에 올바른 JDK버전 사용: gradle:jdk{JDK버전}
  - 변수 참조 문법 확인: `${variable}` 사용, `\${variable}` 사용 금지
  - 모든 서비스명이 실제 프로젝트 서비스명으로 치환되었는지 확인
  - **파드 자동 정리 설정 확인**: podRetention: never(), idleMinutes: 1, terminationGracePeriodSeconds: 3
  - **try-catch-finally 블록 포함**: 예외 상황에서도 정리 로직 실행 보장
  - **매니페스트 레포지토리 업데이트 확인**: git container로 manifest repo clone 및 image tag 업데이트 후 push

## 품질 기준
- [ ] 시크릿 하드코딩 금지
- [ ] Podman 기반 빌드 구성
- [ ] 환경별 Kustomize overlay 구성

## 주의사항
- Secret 매니페스트에 `data`가 아닌 `stringData` 사용
- dev 환경 Ingress Host는 base의 ingress.yaml과 정확히 동일하게 설정 (변경 금지)
- Kustomize patch 방법: `patchesStrategicMerge` 대신 `patches` (target 명시) 사용
- Jenkins Groovy에서 bash 변수 전달 시 `\${variable}` 사용 금지, `${variable}` 사용
- Bash 배열 대신 공백 구분 문자열 사용 (POSIX 쉘 호환)
- podRetention: never() 는 문자열 'never'가 아닌 함수 호출 형태로 작성
