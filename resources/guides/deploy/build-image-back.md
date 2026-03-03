# 백엔드 컨테이너이미지 작성가이드

## 목적
백엔드 각 서비스의 컨테이너 이미지를 생성하고 이미지 레지스트리에 푸시한다.   
수행한 명령어를 포함하여 컨테이너 이미지 작성 과정을 결과 파일에 기록한다.

## 입력 (이전 단계 산출물)
| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 기술스택 정보 | `CLAUDE.md` | 베이스 이미지 및 빌드 도구 결정 |
| 프로젝트 구조 | `(런타임 결정)` | 서비스명 확인 |

## 출력 (이 단계 산출물)
| 산출물 | 파일 경로 |
|--------|----------|
| 컨테이너 이미지 빌드 가이드 | `docs/deploy/build-image-back.md` |
| 백엔드 Dockerfile | `deployment/container/Dockerfile-backend` |

## 방법론

### 기술스택 확인 및 분기

CLAUDE.md의 기술스택 정보를 확인하여 아래 결정 트리를 따른다.

```
1. CLAUDE.md에서 백엔드 빌드 도구 확인
2. IF build.gradle 또는 build.gradle.kts 존재 → [Gradle 분기]
3. IF pom.xml 존재 → [Maven 분기]
4. 해당 없으면 사용자에게 확인
```

| 기술스택 | 빌드 도구 | 베이스 이미지 (빌드) | 베이스 이미지 (실행) | 빌드 산출물 |
|----------|----------|---------------------|---------------------|------------|
| Spring Boot (Gradle) | `./gradlew bootJar` | `amazoncorretto:{version}-alpine3.21-jdk` | `amazoncorretto:{version}-alpine3.21-jdk` | `{서비스명}/build/libs/{서비스명}.jar` |
| Spring Boot (Maven) | `./mvnw package` | `amazoncorretto:{version}-alpine3.21-jdk` | `amazoncorretto:{version}-alpine3.21-jdk` | `{서비스명}/target/{서비스명}.jar` |

> `{version}`은 CLAUDE.md의 `### develop > 기술스택 > Java` 버전을 참조하여 결정한다. 기술스택 정보가 없으면 기본값 `21`을 사용한다.
> Amazon Corretto는 AWS 환경에서 검증된 OpenJDK 배포판으로, eclipse-temurin alpine 대비 호환성이 우수하다.

### 서비스명 확인

#### Gradle 분기
settings.gradle(또는 settings.gradle.kts)에서 확인.

예시) `include` 하위의 4개가 서비스명임.
```
rootProject.name = 'tripgen'

include 'common'
include 'user-service'
include 'location-service'
include 'ai-service'
include 'trip-service'
```

#### Maven 분기
루트 pom.xml의 `<modules>` 섹션에서 확인.

예시)
```xml
<modules>
    <module>common</module>
    <module>user-service</module>
    <module>location-service</module>
    <module>ai-service</module>
    <module>trip-service</module>
</modules>
```

### 실행Jar 파일 설정

#### Gradle 분기
실행Jar 파일명을 서비스명과 일치하도록 각 서비스의 build.gradle에 설정한다.
```
bootJar {
    archiveFileName = '{서비스명}.jar'
}
```

#### Maven 분기
실행Jar 파일명을 서비스명과 일치하도록 각 서비스의 pom.xml에 설정한다.
```xml
<build>
    <finalName>{서비스명}</finalName>
</build>
```

### 애플리케이션 빌드

> VM에서 실행한다.

#### Gradle 분기
```
./gradlew clean bootJar -x test
```

#### Maven 분기
```
./mvnw clean package -DskipTests
```

### Dockerfile 생성

아래 내용으로 `deployment/container/Dockerfile-backend` 생성.

#### Gradle 분기
```dockerfile
# Build stage - 호스트에서 빌드된 JAR를 복사
FROM amazoncorretto:{version}-alpine3.21-jdk AS builder
ARG BUILD_LIB_DIR
ARG ARTIFACTORY_FILE
COPY ${BUILD_LIB_DIR}/${ARTIFACTORY_FILE} app.jar

# Run stage
FROM amazoncorretto:{version}-alpine3.21-jdk
ENV USERNAME=appuser
ENV ARTIFACTORY_HOME=/home/${USERNAME}
ENV JAVA_OPTS=""

# 비루트 사용자 생성
RUN adduser -S -G root ${USERNAME} && \
    mkdir -p ${ARTIFACTORY_HOME} && \
    chown ${USERNAME}:root ${ARTIFACTORY_HOME}

WORKDIR ${ARTIFACTORY_HOME}
COPY --from=builder app.jar app.jar
RUN chown ${USERNAME}:root app.jar

USER ${USERNAME}

EXPOSE 8080

# HEALTHCHECK: Docker 단독 실행 시 헬스 확인용. K8s 환경에서는 Probe가 우선함.
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

ENTRYPOINT [ "sh", "-c" ]
CMD ["java ${JAVA_OPTS} -jar app.jar"]
```

> `{version}`은 CLAUDE.md의 `### develop > 기술스택 > Java` 버전을 참조하여 치환한다. 기본값: `amazoncorretto:21-alpine3.21-jdk`.

#### Maven 분기
Gradle 분기와 동일한 Dockerfile을 사용한다. 차이점은 빌드 명령(`./mvnw`)과 산출물 경로(`target/`)뿐이며, Dockerfile의 `BUILD_LIB_DIR` ARG로 흡수된다.

### 컨테이너 이미지 생성

> VM에서 실행한다.

아래 명령으로 각 서비스 빌드. shell 파일을 생성하지 말고 command로 수행.
서브에이젼트를 생성하여 병렬로 수행.

#### Gradle 분기
```
DOCKER_FILE=deployment/container/Dockerfile-backend
service={서비스명}

docker build \
  --platform linux/amd64 \
  --build-arg BUILD_LIB_DIR="${service}/build/libs" \
  --build-arg ARTIFACTORY_FILE="${service}.jar" \
  -f ${DOCKER_FILE} \
  -t ${service}:v1.0.0 .
```

#### Maven 분기
```
DOCKER_FILE=deployment/container/Dockerfile-backend
service={서비스명}

docker build \
  --platform linux/amd64 \
  --build-arg BUILD_LIB_DIR="${service}/target" \
  --build-arg ARTIFACTORY_FILE="${service}.jar" \
  -f ${DOCKER_FILE} \
  -t ${service}:v1.0.0 .
```

### 이미지 레지스트리 푸시

빌드된 이미지를 `[실행정보]`의 레지스트리에 태그하고 푸시한다.
레지스트리 로그인은 최초 1회, 태그 및 푸시는 각 서비스별로 수행한다.

#### Cloud 인증 (VM 환경)

VM에서 레지스트리 로그인 전, 해당 Cloud의 CLI 인증이 필요하다.

- **AWS (ECR 사용 시)**:
  - 권장: EC2 Instance Profile (IAM Role 연결) — 별도 인증 불필요
  - 대안: 로컬의 `~/.aws/credentials`를 VM에 복사
    ```bash
    scp ~/.aws/credentials {사용자}@{VM-IP}:~/.aws/credentials
    ```

- **Azure (ACR 사용 시)**:
  - 권장: Managed Identity — 별도 인증 불필요
  - 대안: `az login` 후 credentials 복사

- **GCP (GCR 사용 시)**:
  - 권장: Service Account (Workload Identity) — 별도 인증 불필요
  - 대안: `gcloud auth` credentials 복사

#### 레지스트리 로그인

> VM에서 실행한다.

`[실행정보]`의 `레지스트리유형`에 따라 로그인한다.

- **DockerHub:**
```bash
docker login -u ${IMG_ID} -p ${IMG_PW} docker.io
```

- **ECR:**
```bash
aws ecr get-login-password --region ${ECR_REGION} \
  | docker login --username AWS --password-stdin \
    ${ECR_ACCOUNT}.dkr.ecr.${ECR_REGION}.amazonaws.com
```

- **ACR:**
```bash
az acr login --name ${ACR명}
```

- **GCR:**
```bash
gcloud auth configure-docker ${GCR_REGION}-docker.pkg.dev
```

#### 리포지토리 자동 생성 (ECR / GCR)

ECR과 GCR은 푸시 전 리포지토리가 존재해야 한다. 존재 여부를 확인하고 없으면 생성한다.
DockerHub와 ACR은 푸시 시 자동 생성되므로 별도 작업 불필요.

- **ECR** (서비스별 실행):
```bash
REPO_NAME="${ROOT}/${service}"
aws ecr describe-repositories \
  --repository-names ${REPO_NAME} \
  --region ${ECR_REGION} 2>/dev/null \
|| aws ecr create-repository \
  --repository-name ${REPO_NAME} \
  --region ${ECR_REGION} \
  --image-scanning-configuration scanOnPush=true
```

- **GCR** (최초 1회):
```bash
gcloud artifacts repositories describe ${GCR_REPO} \
  --location=${GCR_REGION} \
  --project=${GCR_PROJECT} 2>/dev/null \
|| gcloud artifacts repositories create ${GCR_REPO} \
  --repository-format=docker \
  --location=${GCR_REGION} \
  --project=${GCR_PROJECT}
```

#### 이미지 태그 및 푸시

> VM에서 실행한다.

각 서비스별로 수행한다. 서브에이전트를 활용하여 병렬 실행 가능.
```bash
service={서비스명}
docker tag ${service}:v1.0.0 ${REGISTRY_URL}/${service}:v1.0.0
docker push ${REGISTRY_URL}/${service}:v1.0.0
```

> `${REGISTRY_URL}`은 `[실행정보]`에서 조립된 값을 사용한다.
> `${ROOT}`는 CLAUDE.md의 시스템명을 참조한다.
> AKS 환경에서는 `:latest` 태그가 Deployment Safeguards 정책에 의해 차단되므로 시맨틱 버전 태그(`v1.0.0`)를 사용한다.

## 출력 형식
`docs/deploy/build-image-back.md` 파일에 수행한 명령어를 포함하여 컨테이너 이미지 작성 과정을 단계별로 기록한다.

## 품질 기준
- [ ] Dockerfile이 멀티스테이지 빌드로 구성되어 있는가?
- [ ] 실행 스테이지의 베이스 이미지가 `amazoncorretto:{version}-alpine3.21-jdk` 계열인가?
- [ ] 비루트 사용자(`appuser`)로 실행하도록 설정되어 있는가?
- [ ] 모든 서비스의 이미지 빌드가 성공했는가?
- [ ] 레지스트리 로그인이 성공했는가?
- [ ] (ECR/GCR) 리포지토리 존재 확인 및 자동 생성이 정상 수행되었는가?
- [ ] 모든 서비스 이미지가 레지스트리에 푸시되었는가?
- [ ] 빌드 실패 상태로 다음 단계 미진행

## 트러블슈팅
| 증상 | 원인 | 해결 |
|------|------|------|
| `./gradlew: Permission denied` | gradlew 실행 권한 없음 | `chmod +x gradlew` |
| `./mvnw: Permission denied` | mvnw 실행 권한 없음 | `chmod +x mvnw` |
| `Could not resolve dependencies` | 의존성 다운로드 실패 | 네트워크 확인, 프록시 설정 확인, `./gradlew --refresh-dependencies` |
| `no match for platform` | 플랫폼 불일치 | `--platform linux/amd64` 확인. Apple Silicon은 로컬 테스트 시 `--platform linux/arm64` 사용 가능 |
| `COPY failed: file not found` | 빌드 산출물 경로 오류 | Gradle: `build/libs/` 확인, Maven: `target/` 확인 |
| `denied: requested access to the resource is denied` | 레지스트리 인증 실패 | 레지스트리 로그인 상태 확인, 토큰/권한 점검 |
| `repository does not exist` (ECR) | ECR 리포지토리 미생성 | `aws ecr describe-repositories` 확인 후 `create-repository` 실행 |
| `docker push` 타임아웃 | 네트워크 또는 이미지 크기 문제 | 네트워크 확인, 이미지 크기 최적화 |
| SSH 연결 끊김 (빌드 중 갑자기 종료) | VM 메모리 부족 (OOM Killer) | VM 스펙 업그레이드 (최소 4GB 권장, t3a.xlarge 16GB 검증됨) |
| `docker push` 시 `use of closed network connection` | 로컬 → Cloud 레지스트리 네트워크 불안정 | 동일 Cloud 내부 VM에서 push 수행 |
| VM에서 `docker: command not found` | Docker 미설치 | VM에 Docker 설치: `sudo yum install -y docker && sudo systemctl start docker` (Amazon Linux) |
| 빌드 시간이 과도하게 길다 | VM 최초 빌드 시 Docker 레이어 캐시 없음 | 정상 동작임. 2회차부터 캐시 적용. BuildKit 활성화: `DOCKER_BUILDKIT=1 docker build ...` |

## 주의사항
- shell 파일을 생성하지 말고 command로 직접 수행
- 각 서비스는 서브에이전트를 생성하여 병렬로 빌드
- 빌드 실패 시 반드시 원인을 파악하고 해결한 후 다음 단계 진행
- Dockerfile의 ARG 이름(`BUILD_LIB_DIR`, `ARTIFACTORY_FILE`)은 CI/CD 파이프라인 가이드와 공유되므로 변경 금지
- 이미지 태그는 `:v1.0.0`을 사용한다. AKS Deployment Safeguards가 `:latest` 태그를 차단하므로 시맨틱 버전 태그를 부여한다. CI/CD 환경에서의 태그 전략은 CI/CD 파이프라인 가이드에서 관리
- VM에서 빌드 시 Docker와 JDK가 설치되어 있어야 한다
- VM 최소 스펙: 4GB RAM 이상 권장 (메모리 부족 시 OOM으로 SSH 끊김 발생)
