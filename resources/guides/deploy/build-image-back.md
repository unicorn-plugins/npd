# 백엔드 컨테이너이미지 작성가이드

## 목적
백엔드 각 서비스의 컨테이너 이미지를 생성하고, 실제 빌드 수행 및 검증까지 완료한다. 수행한 명령어를 포함하여 컨테이너 이미지 작성 과정을 결과 파일에 기록한다.

## 입력 (이전 단계 산출물)
| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 기술스택 정보 | `CLAUDE.md` | 베이스 이미지 및 빌드 도구 결정 |
| 프로젝트 구조 | `(런타임 결정)` | 서비스명 확인 |

## 출력 (이 단계 산출물)
| 산출물 | 파일 경로 |
|--------|----------|
| 컨테이너 이미지 빌드 가이드 | `deployment/container/build-image.md` |
| 백엔드 Dockerfile | `deployment/container/Dockerfile-backend` |
| .dockerignore | `.dockerignore` |

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
| Spring Boot (Gradle) | `./gradlew bootJar` | `eclipse-temurin:{version}-jdk-alpine` | `eclipse-temurin:{version}-jre-alpine` | `{서비스명}/build/libs/{서비스명}.jar` |
| Spring Boot (Maven) | `./mvnw package` | `eclipse-temurin:{version}-jdk-alpine` | `eclipse-temurin:{version}-jre-alpine` | `{서비스명}/target/{서비스명}.jar` |

> `{version}`은 CLAUDE.md의 Java 버전 정보를 참조하여 결정한다 (예: 17, 21, 23).

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

#### Gradle 분기
```
./gradlew clean bootJar -x test
```

#### Maven 분기
```
./mvnw clean package -DskipTests
```

### .dockerignore 생성

프로젝트 루트에 아래 내용으로 `.dockerignore` 파일을 생성한다.
```
.git
.gitignore
*.md
.env*
.idea/
.vscode/
**/node_modules
**/target
**/build
**/__pycache__
deployment/
!deployment/container/
```

> `deployment/container/`는 Dockerfile이 위치하는 경로이므로 제외하지 않는다.

### Dockerfile 생성

아래 내용으로 `deployment/container/Dockerfile-backend` 생성.

#### Gradle 분기
```dockerfile
# Build stage - 호스트에서 빌드된 JAR를 복사
FROM eclipse-temurin:{version}-jdk-alpine AS builder
ARG BUILD_LIB_DIR
ARG ARTIFACTORY_FILE
COPY ${BUILD_LIB_DIR}/${ARTIFACTORY_FILE} app.jar

# Run stage
FROM eclipse-temurin:{version}-jre-alpine
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

> `{version}`은 CLAUDE.md의 Java 버전으로 치환한다 (예: `eclipse-temurin:21-jdk-alpine`).

#### Maven 분기
Gradle 분기와 동일한 Dockerfile을 사용한다. 차이점은 빌드 명령(`./mvnw`)과 산출물 경로(`target/`)뿐이며, Dockerfile의 `BUILD_LIB_DIR` ARG로 흡수된다.

### 컨테이너 이미지 생성

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
  -t ${service}:latest .
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
  -t ${service}:latest .
```

### 생성된 이미지 검증

#### 1. 이미지 존재 및 크기 확인
```
docker images | grep {서비스명}
```
> JVM 기반 이미지는 일반적으로 200~400MB 범위가 적정. 1GB 초과 시 .dockerignore 및 멀티스테이지 빌드를 점검한다.

#### 2. 컨테이너 기동 테스트 (선택)
```
docker run --rm -d --name {서비스명}-test -p 0:8080 {서비스명}:latest
# 10초 대기 후 컨테이너 상태 확인
sleep 10
docker ps | grep {서비스명}-test
docker stop {서비스명}-test
```

#### 3. 이미지 보안 스캔 (선택)
```
# trivy 설치 시
trivy image --severity HIGH,CRITICAL {서비스명}:latest
```

## 출력 형식
`deployment/container/build-image.md` 파일에 수행한 명령어를 포함하여 컨테이너 이미지 작성 과정을 단계별로 기록한다.

## 품질 기준
- [ ] `.dockerignore` 파일이 프로젝트 루트에 생성되었는가?
- [ ] Dockerfile이 멀티스테이지 빌드로 구성되어 있는가?
- [ ] 실행 스테이지의 베이스 이미지가 `eclipse-temurin:{version}-jre-alpine` 계열인가?
- [ ] 비루트 사용자(`appuser`)로 실행하도록 설정되어 있는가?
- [ ] 모든 서비스의 이미지 빌드가 성공했는가?
- [ ] 이미지 크기가 합리적인가? (JVM: 200~400MB 범위)
- [ ] 빌드 실패 상태로 다음 단계 미진행

## 트러블슈팅
| 증상 | 원인 | 해결 |
|------|------|------|
| `./gradlew: Permission denied` | gradlew 실행 권한 없음 | `chmod +x gradlew` |
| `./mvnw: Permission denied` | mvnw 실행 권한 없음 | `chmod +x mvnw` |
| `Could not resolve dependencies` | 의존성 다운로드 실패 | 네트워크 확인, 프록시 설정 확인, `./gradlew --refresh-dependencies` |
| `no match for platform` | 플랫폼 불일치 | `--platform linux/amd64` 확인. Apple Silicon은 로컬 테스트 시 `--platform linux/arm64` 사용 가능 |
| `COPY failed: file not found` | 빌드 산출물 경로 오류 | Gradle: `build/libs/` 확인, Maven: `target/` 확인 |
| 이미지 크기 과다 (>1GB) | `.dockerignore` 미설정 또는 불필요 파일 포함 | `.dockerignore` 확인, 실행 스테이지에 JDK 대신 JRE 사용 확인 |

## 주의사항
- shell 파일을 생성하지 말고 command로 직접 수행
- 각 서비스는 서브에이전트를 생성하여 병렬로 빌드
- 빌드 실패 시 반드시 원인을 파악하고 해결한 후 다음 단계 진행
- Dockerfile의 ARG 이름(`BUILD_LIB_DIR`, `ARTIFACTORY_FILE`)은 CI/CD 파이프라인 가이드와 공유되므로 변경 금지
- 이미지 태그는 로컬 빌드 시 `:latest`를 사용. CI/CD 환경에서의 태그 전략은 CI/CD 파이프라인 가이드에서 관리
