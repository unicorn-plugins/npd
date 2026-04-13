# K8s 백킹서비스 배포 가이드

## 목적

K8s 클러스터(EKS/AKS/GKE)에서 애플리케이션이 의존하는 백킹서비스(DB, Redis, MQ)를 Helm 차트 또는 raw manifest로 설치한다.
실제 설치까지 수행하며, 결과를 보고서에 기록한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| K8s 클러스터 접속 설정 | `~/.kube/config` | kubectl로 클러스터 접속 |
| 개발 환경 백킹서비스 결과서 | `docs/develop/backing-service-container-result.md` | DB 이름, 계정 정보 참조 |
| 레퍼런스: Helm 설치 방법 | `{NPD_PLUGIN_DIR}/resources/references/install-backing-service-k8s.md` | values.yaml 예시 참조 |
| 레퍼런스: 클러스터 생성 | `{NPD_PLUGIN_DIR}/resources/references/create-k8s.md` | CLI 도구 설치 참조 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 백킹서비스 배포 결과서 | `docs/deploy/backing-service-k8s-result.md` |

## 방법론

### 실행정보 확인

프롬프트의 `[실행정보]` 섹션에서 아래 K8s 관련 정보를 확인한다.

| 항목 | 설명 |
|------|------|
| {CLOUD} | 클라우드 유형 (AWS/Azure/GCP) -- `[실행정보]`의 레지스트리 유형(ECR→AWS, ACR→Azure, GCR→GCP)으로 간접 식별 |
| {K8S_CLUSTER} | K8s 클러스터 이름 -- `[실행정보]`의 `K8S.CLUSTER` 필드 |
| {K8S_NAMESPACE} | 백킹서비스 및 애플리케이션을 배포할 네임스페이스 (기본: 프로젝트명) -- `[실행정보]`의 `K8S.NAMESPACE` 필드 |

> `{CLOUD}` 값은 `[실행정보]`의 레지스트리 유형으로 판단한다: ECR → AWS, ACR → Azure, GCR → GCP.
> VM 접속 정보(VM.HOST 등)는 이 가이드에서 사용하지 않는다.
> kubectl/helm 명령은 로컬에서 수행한다.

### 사전 조건 확인

kubectl, helm CLI가 설치되어 있고 클러스터에 접속 가능한지 확인한다.

```bash
kubectl version --client
helm version
kubectl get nodes
```

> 미설치 시 `{NPD_PLUGIN_DIR}/resources/references/create-k8s.md`의 "CLOUD CLI 설치" 섹션을 참조하여 설치한다.

### Bitnami Helm repo 추가

```bash
helm repo ls | grep bitnami || helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### Namespace 생성

```bash
kubectl create ns {K8S_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
kubens {K8S_NAMESPACE}
```

> `kubens`가 설치되어 있지 않은 경우 아래 명령으로 대체한다:
> ```bash
> kubectl config set-context --current --namespace={K8S_NAMESPACE}
> ```

### 클라우드별 StorageClass 확인

```bash
kubectl get sc
```

아래 테이블을 참고하여 values.yaml의 `storageClass` 값을 클라우드에 맞게 설정한다.

| 클라우드 | 일반 | 고성능 | 비고 |
|---------|------|-------|------|
| AWS EKS | `gp2-eks-auto` | - | EKS Auto Mode 전용 (수동 생성 필요, 아래 참조) |
| Azure AKS | `managed` | `managed-premium` | AKS Automatic 기본 제공 |
| GCP GKE | `standard-rwo` | `premium-rwo` | GKE Autopilot 기본 제공 |

> 교육/실습 환경에서는 일반 StorageClass를 사용한다.

**[AWS EKS] StorageClass 생성**

EKS Auto Mode는 기본 `gp2` StorageClass의 in-tree provisioner(`kubernetes.io/aws-ebs`)를 지원하지 않습니다.
아래 명령으로 `gp2-eks-auto` StorageClass를 생성합니다. (이미 생성되어 있으면 생략)

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp2-eks-auto
provisioner: ebs.csi.eks.amazonaws.com
parameters:
  type: gp3
  fsType: ext4
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true
EOF
```

### [AWS EKS] ALB 설정

> {CLOUD} == AWS인 경우에만 수행.

**ALB Subnet 태그 등록**

`create-k8s.md`의 'ALB 설정' 섹션을 이미 수행했다면 이 단계는 건너뜀.

Subnet 목록 확인:
```bash
aws ec2 describe-subnets \
  --subnet-ids $(aws eks describe-cluster --name ${EKS_NAME} \
  --query "cluster.resourcesVpcConfig.subnetIds" --output text) \
  --query "Subnets[*].{ID:SubnetId,AZ:AvailabilityZone,Public:MapPublicIpOnLaunch}" \
  --output table
```

위 결과의 모든 Subnet ID를 아래 명령에 넣어 태그 등록:
```bash
aws ec2 create-tags \
  --resources {subnet-1} {subnet-2} {subnet-3} {subnet-4} \
  --tags Key=kubernetes.io/role/elb,Value=1
```

**IngressClass 생성 (alb)**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: alb
  annotations:
    ingressclass.kubernetes.io/is-default-class: "true"
spec:
  controller: eks.amazonaws.com/alb
EOF
```

확인:
```bash
kubectl get ingressclass
```

### AKS 환경: Deployment Safeguards 및 이미지 정책

AKS에는 다음 정책이 기본 활성화되어 있어 Helm 차트 설치가 차단될 수 있다.

1. **[Deployment Safeguards](https://learn.microsoft.com/en-us/azure/aks/deployment-safeguards)**:
   Bitnami Helm 차트는 ClusterIP Service와 Headless Service를 동일한 selector로 생성하므로,
   `UniqueServiceSelector` Gatekeeper 정책에 의해 차단됨
2. **이미지 태그 정책**: `latest` 태그가 차단됨. 모든 이미지에 명시적 버전 태그 필요

> **AWS EKS / GCP GKE**에는 이 정책이 기본 활성화되어 있지 않으므로, Helm 설치가 가능하다.

**AKS 해결 방법**: **raw 매니페스트(StatefulSet + 단일 Service)로 대체 설치**한다.
- Deployment Safeguards 우회: 단일 Service만 생성하여 `UniqueServiceSelector` 정책 회피
- 이미지 태그: 모든 이미지에 명시적 버전 태그 지정 (`:latest`, `:management` 등 금지)

> AKS에서는 아래 "백킹서비스별 Helm 설치" 섹션 대신 **"AKS 환경: Raw 매니페스트 설치"** 섹션을 따른다.

### 백킹서비스별 Helm 설치

프로젝트에서 사용하는 백킹서비스만 설치한다.
`docs/develop/backing-service-container-result.md`의 서비스 목록을 참고하여 필요한 것만 선택 설치한다.

지원 서비스 목록:

| 서비스 | 설치 방식 | 릴리즈명 예시 | 참고 버전 | 레퍼런스 섹션 |
|--------|----------|-------------|----------|-------------|
| MongoDB | Helm `bitnami/mongodb` | `mongo` | 14.3.2 | install-backing-service-k8s.md > 1) MongoDB |
| PostgreSQL | Helm `bitnami/postgresql` | `postgres` | 14.3.2 | install-backing-service-k8s.md > 2) Postgres |
| Redis | Helm `bitnami/redis` | `redis` | 18.4.0 | install-backing-service-k8s.md > 3) Redis |
| RabbitMQ | Raw manifest (StatefulSet + Service) | `rabbitmq` | - | install-backing-service-k8s.md > 4) RabbitMQ |
| Kafka | Helm `bitnami/kafka` | `kafka` | 29.3.14 | install-backing-service-k8s.md > 5) Kafka |
| MySQL/MariaDB | Helm `bitnami/mysql` 또는 `bitnami/mariadb` | `mysql` | (레퍼런스에 추후 추가) | (values.yaml 예시는 레퍼런스에 추후 추가) |

> **참고 버전 안내**: 위 버전(MongoDB 14.3.2, PostgreSQL 14.3.2, Redis 18.4.0, Kafka 29.3.14)은 기존 레퍼런스 문서에서 검증된 버전이다. 최신 버전 확인은 `helm search repo bitnami/{차트명} --versions` 명령을 사용한다.

> **중요**: 2025년 9월 이후 `docker.io/bitnami/*` 이미지는 삭제되었다. 반드시 `bitnamilegacy/*` 이미지를 사용해야 한다. 아래 각 서비스의 values.yaml에 이미지 오버라이드가 명시되어 있다.

> **인증 정보 일관성**: `docs/develop/backing-service-container-result.md`의 연결 정보(DB명, 유저명, 패스워드)를 읽어 아래 values.yaml에 동일하게 적용한다.
> 개발 환경과 배포 환경의 인증 정보가 일치해야 애플리케이션 설정 변경 없이 배포할 수 있다.

각 서비스 설치 절차는 다음과 같다.

#### MongoDB

```bash
mkdir -p ~/install/mongodb && cd ~/install/mongodb
```

`values.yaml`을 작성한다. 실습/교육 환경에서는 `architecture: standalone`으로 Pod를 1개만 생성한다.

```yaml
# 교육/실습 환경: standalone (Pod 1개, 비용 절감)
architecture: standalone

# 인증 설정 (docs/develop/backing-service-container-result.md 참조)
auth:
  enabled: true
  rootUser: root
  rootPassword: "{결과서의 Password}"
  database: "{결과서의 Database}"
  username: "{결과서의 User}"
  password: "{결과서의 Password}"

# 리소스 설정
resources:
  limits:
    cpu: 1
    memory: 2Gi
  requests:
    cpu: 0.5
    memory: 1Gi

# 스토리지 설정
persistence:
  enabled: true
  storageClass: "managed"  # Azure AKS. EKS: "gp2-eks-auto", GKE: "standard-rwo"
  size: 10Gi

# 네트워크 설정
service:
  type: ClusterIP
  ports:
    mongodb: 27017

# image: bitnami -> bitnamilegacy (2025.09 이후 필수)
image:
  registry: docker.io
  repository: bitnamilegacy/mongodb
```

설치:
```bash
helm upgrade -i mongo -f values.yaml bitnami/mongodb --version 14.3.2
```

Pod Running 확인 (완료되면 CTRL-C):
```bash
kubectl get po -w
```

#### PostgreSQL

```bash
mkdir -p ~/install/postgres && cd ~/install/postgres
```

`values.yaml`을 작성한다. 실습/교육 환경에서는 `architecture: standalone`으로 Pod를 1개만 생성한다.

```yaml
# 교육/실습 환경: standalone (Pod 1개, 비용 절감)
architecture: standalone

# 글로벌 설정
global:
  postgresql:
    auth:
      postgresPassword: "{결과서의 Password}"
      database: "{결과서의 Database}"
      username: "{결과서의 User}"
      password: "{결과서의 Password}"
  storageClass: "managed"  # Azure AKS. EKS: "gp2-eks-auto", GKE: "standard-rwo"

# Primary 설정
primary:
  persistence:
    enabled: true
    storageClass: "managed"  # Azure AKS. EKS: "gp2-eks-auto", GKE: "standard-rwo"
    size: 10Gi

  resources:
    limits:
      memory: "2Gi"
      cpu: "1"
    requests:
      memory: "1Gi"
      cpu: "0.5"

  # 다중 DB/스키마 초기화 (필요 시 주석 해제)
  # global.postgresql.auth.database는 1개 DB만 생성한다.
  # 여러 DB나 커스텀 스키마가 필요하면 initdb 스크립트로 생성한다.
  # Spring JPA DDL_AUTO=update는 테이블만 자동 생성하며, 스키마는 생성하지 않는다.
  initdb:
    scripts:
      init-databases.sh: |
        #!/bin/bash
        set -e
        # docs/develop/backing-service-container-result.md의 DB/스키마 목록 참조
        # 예: DB별로 CREATE DATABASE + CREATE SCHEMA 수행
        # DATABASES="recommendation payment"
        # SCHEMAS="lunchpick_member:member lunchpick_recommendation:recommendation lunchpick_payment:payment"
        for db in ${DATABASES:-}; do
          echo "Creating database: $db"
          psql -v ON_ERROR_STOP=1 -U postgres -c "SELECT 1 FROM pg_database WHERE datname='$db'" | grep -q 1 || \
            psql -v ON_ERROR_STOP=1 -U postgres -c "CREATE DATABASE $db OWNER ${POSTGRES_USER:-lunchpick};"
        done
        for entry in ${SCHEMAS:-}; do
          schema="${entry%%:*}"
          db="${entry##*:}"
          echo "Creating schema: $schema in database: $db"
          psql -v ON_ERROR_STOP=1 -U postgres -d "$db" -c "CREATE SCHEMA IF NOT EXISTS $schema;"
          psql -v ON_ERROR_STOP=1 -U postgres -d "$db" -c "GRANT ALL ON SCHEMA $schema TO ${POSTGRES_USER:-lunchpick};"
        done

# 네트워크 설정
service:
  type: ClusterIP
  ports:
    postgresql: 5432

# image: bitnami -> bitnamilegacy (2025.09 이후 필수)
image:
  registry: docker.io
  repository: bitnamilegacy/postgresql
```

설치:
```bash
helm upgrade -i postgres -f values.yaml bitnami/postgresql --version 14.3.2
```

Pod Running 확인 (완료되면 CTRL-C):
```bash
kubectl get po -w
```

#### Redis

```bash
mkdir -p ~/install/redis && cd ~/install/redis
```

`values.yaml`을 작성한다. 실습/교육 환경에서는 `architecture: standalone`으로 Pod를 1개만 생성한다.

```yaml
# 교육/실습 환경: standalone (Pod 1개, 비용 절감)
architecture: standalone

# 인증 설정 (docs/develop/backing-service-container-result.md 참조)
auth:
  enabled: true
  password: "{결과서의 Password}"

master:
  persistence:
    enabled: true
    storageClass: "managed"  # Azure AKS. EKS: "gp2-eks-auto", GKE: "standard-rwo"
    size: 10Gi

  resources:
    limits:
      memory: "2Gi"
      cpu: "1"
    requests:
      memory: "1Gi"
      cpu: "0.5"

service:
  type: ClusterIP
  ports:
    redis: 6379

# image: bitnami -> bitnamilegacy (2025.09 이후 필수)
image:
  registry: docker.io
  repository: bitnamilegacy/redis
```

설치:
```bash
helm upgrade -i redis -f values.yaml bitnami/redis --version 18.4.0
```

Pod Running 확인 (완료되면 CTRL-C):
```bash
kubectl get po -w
```

#### RabbitMQ

RabbitMQ는 Helm 차트 대신 raw K8s manifest(StatefulSet + Service)로 설치한다.

```bash
mkdir -p ~/install/rabbitmq && cd ~/install/rabbitmq
```

`deploy.yaml`을 작성한다.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: rabbitmq
  labels:
    app: rabbitmq
spec:
  serviceName: rabbitmq
  selector:
    matchLabels:
      app: rabbitmq
  replicas: 1
  template:
    metadata:
      name: rabbitmq
      labels:
        app: rabbitmq
    spec:
      serviceAccountName: default
      containers:
      - name: rabbitmq
        image: rabbitmq:3.13-management
        imagePullPolicy: IfNotPresent
        env:
        - name: RABBITMQ_DEFAULT_USER
          value: "{결과서의 User}"        # docs/develop/backing-service-container-result.md 참조
        - name: RABBITMQ_DEFAULT_PASS
          value: "{결과서의 Password}"     # docs/develop/backing-service-container-result.md 참조
        ports:
        - name: amqp
          containerPort: 5672
        - name: management
          containerPort: 15672
        resources:
          requests:
            cpu: 128m
            memory: 128Mi
          limits:
            cpu: 1
            memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: rabbitmq
spec:
  type: ClusterIP
  selector:
    app: rabbitmq
  ports:
  - name: amqp
    port: 5672
    targetPort: 5672
  - name: management
    port: 15672
    targetPort: 15672
```

설치:
```bash
kubectl apply -f deploy.yaml
```

Pod Running 확인 (완료되면 CTRL-C):
```bash
kubectl get po -w
```

#### Kafka

```bash
mkdir -p ~/install/kafka && cd ~/install/kafka
```

`values.yaml`을 작성한다. KRaft 모드(ZooKeeper 없음)로 설치한다.

```yaml
# KRaft 모드 (ZooKeeper 없음)
kraft:
  enabled: true

# 글로벌 스토리지 설정
global:
  storageClass: "managed"  # Azure AKS. EKS: "gp2-eks-auto", GKE: "standard-rwo"

# 인증 비활성화 (교육/실습 환경)
auth:
  clientProtocol: plaintext
  interBrokerProtocol: plaintext
  sasl:
    enabled: false
  tls:
    enabled: false

# 리스너 설정
listeners:
  client:
    containerPort: 9092
    protocol: PLAINTEXT
    name: CLIENT
  controller:
    name: CONTROLLER
    containerPort: 9093
    protocol: PLAINTEXT
  interbroker:
    containerPort: 9094
    protocol: PLAINTEXT
    name: INTERNAL

# Controller (교육/실습: 1 replica)
controller:
  replicaCount: 1
  heapOpts: "-Xmx1g -Xms1g"
  persistence:
    enabled: true
    size: 10Gi
  resources:
    limits:
      memory: 2Gi
      cpu: 1
    requests:
      memory: 1Gi
      cpu: 1

# Broker (교육/실습: 1 replica)
broker:
  replicaCount: 1
  heapOpts: "-Xmx1g -Xms1g"
  persistence:
    enabled: true
    size: 10Gi
  resources:
    limits:
      memory: 2Gi
      cpu: 1
    requests:
      memory: 1Gi
      cpu: 1

deleteTopicEnable: true
autoCreateTopicsEnable: false

# RBAC (autoDiscovery 등에 필요)
rbac:
  create: true

# image: bitnami -> bitnamilegacy (2025.09 이후 필수)
image:
  registry: docker.io
  repository: bitnamilegacy/kafka
```

> **교육/실습 환경 설정**: 레퍼런스 문서는 broker 2 replica이지만, 비용 절감을 위해 1 replica로 줄였다. `externalAccess`(LoadBalancer)도 제거하고 port-forward로 대체한다.

설치:
```bash
helm upgrade -i kafka -f values.yaml bitnami/kafka --version 29.3.14
```

Pod Running 확인 (완료되면 CTRL-C):
```bash
kubectl get po -w
```

### AKS 환경: Raw 매니페스트 설치

> **AKS({CLOUD}=Azure)인 경우에만** 이 섹션을 사용한다.
> AWS EKS / GCP GKE는 위의 "백킹서비스별 Helm 설치" 섹션을 따른다.

AKS의 Deployment Safeguards 및 이미지 태그 정책으로 인해,
Helm 차트 대신 raw 매니페스트(StatefulSet + 단일 Service)로 설치한다.

- 모든 이미지에 **명시적 버전 태그** 지정 (`:latest` 금지)
- Service는 **단일 ClusterIP**만 생성 (Headless Service 없음 → UniqueServiceSelector 정책 회피)
- PVC는 `volumeClaimTemplates`로 자동 생성

#### MongoDB (AKS)

```bash
mkdir -p ~/install/mongodb && cd ~/install/mongodb
```

`deploy.yaml`을 작성한다.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongo
  labels:
    app: mongo
spec:
  serviceName: mongo
  replicas: 1
  selector:
    matchLabels:
      app: mongo
  template:
    metadata:
      labels:
        app: mongo
    spec:
      containers:
      - name: mongodb
        image: bitnamilegacy/mongodb:7.0
        imagePullPolicy: IfNotPresent
        env:
        - name: MONGODB_ROOT_USER
          value: "root"
        - name: MONGODB_ROOT_PASSWORD
          value: "{결과서의 Password}"
        - name: MONGODB_DATABASE
          value: "{결과서의 Database}"
        - name: MONGODB_USERNAME
          value: "{결과서의 User}"
        - name: MONGODB_PASSWORD
          value: "{결과서의 Password}"
        ports:
        - containerPort: 27017
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1
            memory: 2Gi
        volumeMounts:
        - name: data
          mountPath: /bitnami/mongodb
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: "managed"
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mongo-mongodb
spec:
  type: ClusterIP
  selector:
    app: mongo
  ports:
  - port: 27017
    targetPort: 27017
```

설치:
```bash
kubectl apply -f deploy.yaml
```

#### PostgreSQL (AKS)

```bash
mkdir -p ~/install/postgres && cd ~/install/postgres
```

`deploy.yaml`을 작성한다.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  labels:
    app: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgresql
        image: bitnamilegacy/postgresql:16
        imagePullPolicy: IfNotPresent
        env:
        - name: POSTGRESQL_POSTGRES_PASSWORD
          value: "{결과서의 Password}"
        - name: POSTGRESQL_DATABASE
          value: "{결과서의 Database}"
        - name: POSTGRESQL_USERNAME
          value: "{결과서의 User}"
        - name: POSTGRESQL_PASSWORD
          value: "{결과서의 Password}"
        ports:
        - containerPort: 5432
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1
            memory: 2Gi
        volumeMounts:
        - name: data
          mountPath: /bitnami/postgresql
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: "managed"
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-postgresql
spec:
  type: ClusterIP
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

> **다중 DB/스키마 초기화**: Helm의 `initdb.scripts`와 달리, raw 매니페스트에서는 Pod 기동 후 수동으로 생성한다.
> ```bash
> kubectl exec -it sts/postgres-0 -- psql -U postgres -c "CREATE DATABASE {DB명} OWNER {User};"
> kubectl exec -it sts/postgres-0 -- psql -U postgres -d {DB명} -c "CREATE SCHEMA IF NOT EXISTS {스키마명};"
> ```

설치:
```bash
kubectl apply -f deploy.yaml
```

#### Redis (AKS)

```bash
mkdir -p ~/install/redis && cd ~/install/redis
```

`deploy.yaml`을 작성한다.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  labels:
    app: redis
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: bitnamilegacy/redis:7.2
        imagePullPolicy: IfNotPresent
        command: ["redis-server"]
        args: ["--requirepass", "{결과서의 Password}"]
        ports:
        - containerPort: 6379
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1
            memory: 2Gi
        volumeMounts:
        - name: data
          mountPath: /bitnami/redis/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: "managed"
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis-master
spec:
  type: ClusterIP
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

설치:
```bash
kubectl apply -f deploy.yaml
```

#### RabbitMQ (AKS)

RabbitMQ는 EKS/GKE에서도 raw 매니페스트로 설치하므로 동일하되, **이미지 태그를 명시적 버전으로 지정**한다.

```bash
mkdir -p ~/install/rabbitmq && cd ~/install/rabbitmq
```

위 "백킹서비스별 Helm 설치 > RabbitMQ" 섹션의 `deploy.yaml`을 그대로 사용한다.
이미지는 `rabbitmq:3.13-management`로 명시적 버전 태그가 지정되어 있음.

설치:
```bash
kubectl apply -f deploy.yaml
```

#### Kafka (AKS)

```bash
mkdir -p ~/install/kafka && cd ~/install/kafka
```

`deploy.yaml`을 작성한다. KRaft 모드(ZooKeeper 없음), controller + broker 결합 구성.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
  labels:
    app: kafka
spec:
  serviceName: kafka
  replicas: 1
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
      - name: kafka
        image: bitnamilegacy/kafka:3.7
        imagePullPolicy: IfNotPresent
        env:
        - name: KAFKA_CFG_NODE_ID
          value: "0"
        - name: KAFKA_CFG_PROCESS_ROLES
          value: "controller,broker"
        - name: KAFKA_CFG_CONTROLLER_QUORUM_VOTERS
          value: "0@kafka-0.kafka:9093"
        - name: KAFKA_CFG_LISTENERS
          value: "PLAINTEXT://:9092,CONTROLLER://:9093"
        - name: KAFKA_CFG_ADVERTISED_LISTENERS
          value: "PLAINTEXT://kafka:9092"
        - name: KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP
          value: "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT"
        - name: KAFKA_CFG_CONTROLLER_LISTENER_NAMES
          value: "CONTROLLER"
        - name: KAFKA_CFG_INTER_BROKER_LISTENER_NAME
          value: "PLAINTEXT"
        - name: KAFKA_KRAFT_CLUSTER_ID
          value: "MkU3OEVBNTcwNTJENDM2Qk"
        - name: KAFKA_CFG_AUTO_CREATE_TOPICS_ENABLE
          value: "false"
        - name: KAFKA_CFG_DELETE_TOPIC_ENABLE
          value: "true"
        - name: KAFKA_HEAP_OPTS
          value: "-Xmx1g -Xms1g"
        ports:
        - name: client
          containerPort: 9092
        - name: controller
          containerPort: 9093
        resources:
          requests:
            cpu: 1
            memory: 1Gi
          limits:
            cpu: 1
            memory: 2Gi
        volumeMounts:
        - name: data
          mountPath: /bitnami/kafka
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: "managed"
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: kafka
spec:
  type: ClusterIP
  selector:
    app: kafka
  ports:
  - name: client
    port: 9092
    targetPort: 9092
```

설치:
```bash
kubectl apply -f deploy.yaml
```

#### AKS Raw 매니페스트 재구성 / 삭제

```bash
# 재설치 (deploy.yaml 변경 시)
kubectl apply -f deploy.yaml

# 완전 삭제 (데이터 포함)
kubectl delete -f deploy.yaml
kubectl delete pvc -l app={서비스명}   # 예: app=mongo, app=postgres, app=redis, app=kafka
```

### Health Check

서비스별 정상 동작을 확인한다.

> **주의**: Bitnami Helm 차트는 StatefulSet으로 배포된다. `deploy/`가 아닌 `sts/`로 리소스를 지정하고, Pod 이름에 `-0` 인덱스를 붙인다.
> AKS raw 매니페스트는 StatefulSet 이름이 다르므로 Pod 이름도 다르다 (아래 표 참조).

**EKS/GKE (Helm 설치):**

| 서비스 | 확인 명령 | 정상 응답 |
|--------|----------|----------|
| PostgreSQL | `kubectl exec -it sts/postgres-postgresql-0 -- pg_isready -U postgres` | `accepting connections` |
| MongoDB | `kubectl exec -it sts/mongo-mongodb-0 -- mongosh --eval "db.adminCommand('ping')"` | `{ ok: 1 }` |
| Redis | `kubectl exec -it sts/redis-master-0 -- redis-cli -a $REDIS_PASSWORD ping` | `PONG` |
| RabbitMQ | `kubectl exec -it sts/rabbitmq-0 -- rabbitmqctl status` | `Status of node rabbit@rabbitmq-0 ...` |
| Kafka | `kubectl exec -it kafka-broker-0 -- kafka-broker-api-versions.sh --bootstrap-server localhost:9092` | 버전 목록 출력 (에러 없음) |

**AKS (Raw 매니페스트 설치):**

| 서비스 | 확인 명령 | 정상 응답 |
|--------|----------|----------|
| PostgreSQL | `kubectl exec -it postgres-0 -- pg_isready -U postgres` | `accepting connections` |
| MongoDB | `kubectl exec -it mongo-0 -- mongosh --eval "db.adminCommand('ping')"` | `{ ok: 1 }` |
| Redis | `kubectl exec -it redis-0 -- redis-cli -a $REDIS_PASSWORD ping` | `PONG` |
| RabbitMQ | `kubectl exec -it rabbitmq-0 -- rabbitmqctl status` | `Status of node rabbit@rabbitmq-0 ...` |
| Kafka | `kubectl exec -it kafka-0 -- kafka-broker-api-versions.sh --bootstrap-server localhost:9092` | 버전 목록 출력 (에러 없음) |

**서비스별 database 확인** (PostgreSQL):
```bash
# EKS/GKE (Helm)
kubectl exec -it sts/postgres-postgresql-0 -- psql -U postgres -l
# AKS (Raw 매니페스트)
kubectl exec -it postgres-0 -- psql -U postgres -l
```

init 스크립트 또는 values.yaml에 지정한 database가 목록에 존재하는지 확인한다.

### 외부 접속 확인 (port-forward)

`kubectl port-forward`로 로컬에서 각 백킹서비스에 접속하여 정상 동작을 확인한다.

```bash
# PostgreSQL
kubectl port-forward svc/postgres-postgresql 5432:5432

# MongoDB
kubectl port-forward svc/mongo-mongodb 27017:27017

# Redis
kubectl port-forward svc/redis-master 6379:6379

# RabbitMQ (AMQP + Management Console)
kubectl port-forward svc/rabbitmq 5672:5672
kubectl port-forward svc/rabbitmq 15672:15672   # 브라우저에서 http://localhost:15672 접속

# Kafka
kubectl port-forward svc/kafka 9092:9092
```

> K8s 내부의 앱 Pod에서는 ClusterIP 서비스 DNS로 접근한다 (예: `postgres-postgresql.{K8S_NAMESPACE}.svc.cluster.local`).

### 앱 Pod에서의 접속 정보

VM docker-compose와 달리 K8s에서는 서비스 DNS 이름으로 접속한다.
백킹서비스와 애플리케이션은 동일 네임스페이스에 배포하므로, 앱에서는 서비스명만으로 접속 가능하다.

| 서비스 | K8s 내부 호스트 (동일 네임스페이스) | FQDN | 포트 |
|--------|----------------------------------|------|------|
| PostgreSQL | `postgres-postgresql` | `postgres-postgresql.{K8S_NAMESPACE}.svc.cluster.local` | 5432 |
| MongoDB | `mongo-mongodb` | `mongo-mongodb.{K8S_NAMESPACE}.svc.cluster.local` | 27017 |
| Redis | `redis-master` | `redis-master.{K8S_NAMESPACE}.svc.cluster.local` | 6379 |
| RabbitMQ | `rabbitmq` | `rabbitmq.{K8S_NAMESPACE}.svc.cluster.local` | 5672 (AMQP), 15672 (Management) |
| Kafka | `kafka` | `kafka.{K8S_NAMESPACE}.svc.cluster.local` | 9092 |

> 예: 앱의 DB 접속 호스트는 `postgres-postgresql:5432`, Redis 접속 호스트는 `redis-master:6379`, RabbitMQ는 `rabbitmq:5672`.
> K8s Deployment 매니페스트에 위 접속 정보를 환경변수로 설정한다.

### 재구성 / 삭제 절차

**EKS/GKE: Helm 설치 서비스 (MongoDB, PostgreSQL, Redis, Kafka):**
```bash
# 재설치 (values.yaml 변경 시)
helm upgrade -i {릴리즈명} -f values.yaml bitnami/{차트명} --version {버전}

# 완전 삭제 (데이터 포함)
helm uninstall {릴리즈명}
kubectl delete pvc -l app.kubernetes.io/instance={릴리즈명}
```

> `helm uninstall` 시 PVC(데이터)는 자동 삭제되지 않는다. 데이터 초기화가 필요하면 위 PVC 삭제 명령을 함께 실행한다.

**EKS/GKE: Raw manifest 서비스 (RabbitMQ):**
```bash
# 재설치 (deploy.yaml 변경 시)
kubectl apply -f deploy.yaml

# 완전 삭제
kubectl delete -f deploy.yaml
```

**AKS: Raw manifest 서비스 (전체 — MongoDB, PostgreSQL, Redis, RabbitMQ, Kafka):**

> AKS에서는 Deployment Safeguards 정책으로 인해 모든 백킹서비스를 raw 매니페스트로 설치한다.

```bash
# 재설치 (deploy.yaml 변경 시)
kubectl apply -f deploy.yaml

# 완전 삭제 (데이터 포함)
kubectl delete -f deploy.yaml
kubectl delete pvc -l app={서비스명}   # 예: app=mongo, app=postgres, app=redis, app=kafka, app=rabbitmq
```

### 결과 보고서 작성

Health Check 완료 후 `docs/deploy/backing-service-k8s-result.md`를 작성한다.
아래 출력 형식 섹션의 템플릿을 사용한다.

## 출력 형식

`docs/deploy/backing-service-k8s-result.md` 결과 보고서 템플릿:

```markdown
# 백킹서비스 배포 결과서

## 구성 환경
- 환경: K8s Helm ({CLOUD} {K8S_CLUSTER})
- Namespace: {K8S_NAMESPACE}
- 기동 일시: YYYY-MM-DD

## 서비스 연결 정보

### PostgreSQL
| 항목 | 값 |
|------|---|
| Host (동일 네임스페이스) | postgres-postgresql |
| Host (외부 접근) | `kubectl port-forward svc/postgres-postgresql 5432:5432` → localhost:5432 |
| Port | 5432 |
| Database | {DB명} |
| User | postgres |
| Password | {values.yaml에 설정한 값} |
| JDBC URL | jdbc:postgresql://postgres-postgresql:5432/{DB명} |

### MongoDB
| 항목 | 값 |
|------|---|
| Host (동일 네임스페이스) | mongo-mongodb |
| Host (외부 접근) | `kubectl port-forward svc/mongo-mongodb 27017:27017` → localhost:27017 |
| Port | 27017 |
| Database | {DB명} |
| User | root |
| Password | {values.yaml에 설정한 값} |
| Connection URI | mongodb://root:{password}@mongo-mongodb:27017/{DB명}?authSource=admin |

### Redis
| 항목 | 값 |
|------|---|
| Host (동일 네임스페이스) | redis-master |
| Host (외부 접근) | `kubectl port-forward svc/redis-master 6379:6379` → localhost:6379 |
| Port | 6379 |
| Password | {values.yaml에 설정한 값} |

### RabbitMQ
| 항목 | 값 |
|------|---|
| Host (동일 네임스페이스) | rabbitmq |
| Host (외부 접근) | `kubectl port-forward svc/rabbitmq 5672:5672` → localhost:5672 |
| Management Console | `kubectl port-forward svc/rabbitmq 15672:15672` → http://localhost:15672 |
| Port | 5672 (AMQP), 15672 (Management) |
| User | {deploy.yaml에 설정한 값} |
| Password | {deploy.yaml에 설정한 값} |

### Kafka
| 항목 | 값 |
|------|---|
| Host (동일 네임스페이스) | kafka |
| Host (외부 접근) | `kubectl port-forward svc/kafka 9092:9092` → localhost:9092 |
| Port | 9092 |
| Bootstrap Servers | kafka:9092 |

## 릴리즈 정보

**EKS/GKE (Helm 설치):**

| 서비스 | 릴리즈명 | 설치 방식 | 버전 |
|--------|---------|----------|------|
| PostgreSQL | postgres | Helm bitnami/postgresql | {version} |
| MongoDB | mongo | Helm bitnami/mongodb | {version} |
| Redis | redis | Helm bitnami/redis | {version} |
| RabbitMQ | rabbitmq | Raw manifest (kubectl apply) | - |
| Kafka | kafka | Helm bitnami/kafka | {version} |

**AKS (Raw 매니페스트 설치):**

| 서비스 | StatefulSet명 | 설치 방식 | 이미지 태그 |
|--------|-------------|----------|-----------|
| PostgreSQL | postgres | Raw manifest (kubectl apply) | bitnamilegacy/postgresql:16 |
| MongoDB | mongo | Raw manifest (kubectl apply) | bitnamilegacy/mongodb:7.0 |
| Redis | redis | Raw manifest (kubectl apply) | bitnamilegacy/redis:7.2 |
| RabbitMQ | rabbitmq | Raw manifest (kubectl apply) | rabbitmq:3.13-management |
| Kafka | kafka | Raw manifest (kubectl apply) | bitnamilegacy/kafka:3.7 |

## Health Check 결과
- [ ] PostgreSQL: pg_isready 정상 (accepting connections)
- [ ] MongoDB: ping { ok: 1 } 확인
- [ ] Redis: PONG 확인
- [ ] RabbitMQ: rabbitmqctl status 정상
- [ ] Kafka: broker-api-versions 정상
- [ ] 서비스별 database 존재 확인
- [ ] EKS/GKE: `helm list`로 Helm 릴리즈 `deployed` 상태 확인
- [ ] AKS: `kubectl get sts`로 모든 StatefulSet READY 확인 (Helm 릴리즈 없음)
- [ ] `kubectl get sts`로 모든 StatefulSet Ready 확인
```

## 품질 기준

- [ ] `kubectl get po`로 모든 백킹서비스 Pod가 `Running` 상태
- [ ] 서비스별 health check 통과 (pg_isready, redis-cli ping, rabbitmqctl status, kafka-broker-api-versions 등)
- [ ] EKS/GKE: `helm list`로 Helm 릴리즈가 `deployed` 상태
- [ ] EKS/GKE: `kubectl get sts`로 RabbitMQ 등 raw manifest StatefulSet이 Ready 상태
- [ ] AKS: `kubectl get sts`로 모든 StatefulSet이 Ready 상태 (Helm 미사용, 전체 raw 매니페스트)
- [ ] AKS: 모든 이미지에 명시적 버전 태그 사용 확인 (`:latest` 금지)
- [ ] `docs/deploy/backing-service-k8s-result.md`가 작성됨
- [ ] values.yaml의 storageClass가 해당 클라우드에 맞게 설정됨
- [ ] Helm 차트의 values.yaml에 `bitnamilegacy` 이미지 오버라이드가 명시됨

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| Pod `Pending` 상태 지속 | PVC 바인딩 실패 (storageClass 불일치) | `kubectl get pvc`로 확인, storageClass 값을 클라우드에 맞게 변경 후 `helm upgrade -i` 재실행 |
| Pod `CrashLoopBackOff` | 리소스 부족 또는 설정 오류 | `kubectl logs {pod명}`으로 로그 확인, values.yaml 리소스 요청 축소 후 재설치 |
| `helm upgrade` 실패 | 이전 릴리즈 상태 이상 | `helm uninstall {릴리즈명}` 후 재설치, 필요 시 PVC 수동 삭제 |
| `port-forward` 연결 끊김 | 세션 타임아웃 또는 Pod 재시작 | `kubectl port-forward` 재실행, `kubectl get po`로 Pod 상태 확인 |
| `helm repo add` 실패 | 네트워크 또는 DNS 문제 | 프록시 설정 확인, `helm repo add bitnami https://charts.bitnami.com/bitnami` 재시도 |
| `ImagePullBackOff` | `docker.io/bitnami` 이미지 삭제됨 (2025.09) | values.yaml에 `image.repository: bitnamilegacy/{서비스명}` 오버라이드 추가 후 재설치 |
| `kubectl exec` 명령 실패 | 리소스 타입 오류 (`deploy/` 사용) | Bitnami는 StatefulSet이므로 `sts/{릴리즈명}-{서비스명}-0` 형식으로 변경 |
| `relation "xxx.yyy" does not exist` | 커스텀 스키마 미생성. `global.postgresql.auth.database`는 DB 1개만 생성하며, 스키마는 생성하지 않음. Spring JPA `DDL_AUTO=update`도 스키마는 자동 생성하지 않음 | values.yaml의 `primary.initdb.scripts`에 `CREATE SCHEMA IF NOT EXISTS` 추가 후 재설치, 또는 `kubectl exec`로 수동 생성 후 Pod 재시작 |
| AKS Helm 설치 시 `admission webhook denied` | Deployment Safeguards의 `UniqueServiceSelector` 정책이 Bitnami Helm 차트의 Headless + ClusterIP 이중 Service를 차단 | Helm 대신 raw 매니페스트(StatefulSet + 단일 ClusterIP Service)로 설치. "AKS 환경: Raw 매니페스트 설치" 섹션 참조 |
| AKS 이미지 Pull 실패 (`latest tag not allowed`) | AKS 이미지 태그 정책이 `:latest` 태그를 차단 | 모든 이미지에 명시적 버전 태그 지정 (예: `bitnamilegacy/mongodb:7.0`, `rabbitmq:3.13-management`) |
| AKS Health Check Pod 이름 불일치 | raw 매니페스트의 StatefulSet 이름이 Helm과 다름 (예: `mongo-0` vs `mongo-mongodb-0`) | "Health Check" 섹션의 AKS 전용 테이블 참조. AKS Pod 이름: `{StatefulSet명}-0` (예: `postgres-0`, `mongo-0`, `redis-0`) |

## 주의사항

- Helm 차트 버전을 명시적으로 지정한다 (`--version`). 미지정 시 최신 버전이 설치되어 예기치 않은 동작이 발생할 수 있다. 레퍼런스 검증 버전: MongoDB 14.3.2, PostgreSQL 14.3.2, Redis 18.4.0, Kafka 29.3.14.
- 교육/실습 환경에서는 `architecture: standalone`으로 설치하여 비용을 절감한다. 운영 환경에서는 `architecture: replicaset`(MongoDB) 또는 `architecture: replication`(PostgreSQL/Redis) 사용을 검토한다.
- `helm uninstall` 시 PVC(데이터)는 자동 삭제되지 않는다. 데이터 초기화가 필요하면 `kubectl delete pvc -l app.kubernetes.io/instance={릴리즈명}`으로 수동 삭제한다.
- 백킹서비스는 애플리케이션과 동일한 네임스페이스에 배포한다. 따라서 앱 Pod에서 서비스명만으로 접속 가능하다 (예: `postgres-postgresql:5432`).
- PostgreSQL의 `global.postgresql.auth.database`는 **1개 DB만 생성**한다. 여러 서비스가 각각 다른 DB(예: member, recommendation, payment)를 사용하는 경우 `primary.initdb.scripts`로 추가 DB를 생성해야 한다. 또한 앱이 커스텀 스키마(예: `lunchpick_member`)를 사용하는 경우, Spring JPA `DDL_AUTO=update`는 **테이블만 자동 생성**하며 스키마는 생성하지 않으므로, initdb 스크립트에 `CREATE SCHEMA IF NOT EXISTS`를 포함해야 한다.
- Cloud MQ(Azure Service Bus, AWS SQS, GCP Pub/Sub)는 Helm으로 설치하지 않는다. 클라우드 관리형 서비스를 프로비저닝한다. 프로비저닝 방법은 `{NPD_PLUGIN_DIR}/resources/guides/deploy/backing-service/backing-mq-container.md`의 Cloud MQ 섹션을 참조한다.
- values.yaml의 storageClass는 반드시 해당 클라우드에 맞는 값으로 설정한다 (위 StorageClass 테이블 참조). 잘못된 storageClass는 Pod `Pending` 상태의 주된 원인이다.
- Bitnami Helm 차트는 StatefulSet으로 배포된다. `kubectl exec` 시 리소스 타입을 `sts/`로 지정하고, Pod 인덱스(`-0`)를 붙인다 (예: `sts/postgres-postgresql-0`).
- RabbitMQ는 모든 클라우드에서 Helm 차트가 아닌 raw K8s manifest(StatefulSet + Service)로 설치한다. 삭제 시 `kubectl delete -f deploy.yaml`을 사용한다.
- AKS에서는 Deployment Safeguards(UniqueServiceSelector) 및 이미지 태그 정책(`latest` 차단)으로 인해 **모든 백킹서비스를 raw 매니페스트로 설치**한다. Helm 차트는 Headless Service + ClusterIP Service를 동시에 생성하여 정책에 위배된다.
- Kafka는 KRaft 모드(ZooKeeper 없음)로 설치한다. 교육/실습 환경에서는 controller 1, broker 1 replica로 비용을 절감한다.
- 2025년 9월 이후 `docker.io/bitnami/*` 이미지가 삭제되었다. Helm 차트의 values.yaml에 `image.repository: bitnamilegacy/{서비스명}`을 명시한다. `bitnamilegacy` 이미지는 보안 업데이트가 없으므로 교육/실습 용도로만 사용한다.
